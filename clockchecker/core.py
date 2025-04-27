from __future__ import annotations

from collections.abc import Generator, Iterable, Mapping
from collections import Counter, defaultdict
from copy import copy, deepcopy
from dataclasses import dataclass, field
import enum
import itertools as it
import os
from multiprocessing import Queue, Process
from typing import Any, Callable, Generator, TYPE_CHECKING

if TYPE_CHECKING:
    from .characters import Character, CategoryBounds
    from .events import Event
    from .info import PlayerID, Info

from . import characters
from . import events
from . import info


# Set True to enable debug mode
_DEBUG = os.environ.get('DEBUG', False)
_DEBUG_STATE_FORK_COUNTS = {}
_DEBUG_WORLD_KEY = (106, 0, 0)


if TYPE_CHECKING:
    StateGen = Generator[State]


class Phase(enum.Enum):
    NIGHT = enum.auto()
    DAY = enum.auto()
    SETUP = enum.auto()
   
GLOBAL_PHASE_ORDERS = {
    Phase.NIGHT: characters.GLOBAL_NIGHT_ORDER,
    Phase.DAY: characters.GLOBAL_DAY_ORDER,
    Phase.SETUP: characters.GLOBAL_SETUP_ORDER,
}


@dataclass
class Player:
    """
    An instance of a player. 
    Character-specific info is stored in the character attribute, because
    characters can change, but players are forever.
    """
    name: str
    claim: type[Character]
    night_info: dict[int, Info | list] = field(default_factory=dict)
    day_info: dict[int, Info] = field(default_factory=dict)
    character: Character | None = None

    is_evil: bool = False
    is_dead: bool = False
    woke_tonight: bool = False
    droison_count: int = 0

    character_history: list[str] = field(default_factory=list)

    def __post_init__(self):
        self.character = self.claim()

        # Reorganise info so it can be easily used in night order
        self.external_night_info = defaultdict(list)
        for night in list(self.night_info):
            night_info = self.night_info[night]
            if not isinstance(night_info, list):
                night_info = [night_info]
            del self.night_info[night]
            for item in night_info:
                # Filter out info that comes from another player's ability
                char_name, _ = type(item).__qualname__.split('.')
                item_char = getattr(characters, char_name)
                if item_char is self.claim:
                    assert night not in self.night_info, (
                        "One info per night from own ability."
                    )
                    self.night_info[night] = item
                else:
                    self.external_night_info[(night, item_char)].append(item)
        self.external_night_info = dict(self.external_night_info)

    def droison(self, state: State, src: PlayerID) -> None:
        self.droison_count += 1
        self.character.maybe_deactivate_effects(
            state, self.id, characters.Reason.DROISON
        )

    def undroison(self, state: State, src: PlayerID) -> None:
        self.droison_count -= 1 
        self.character.maybe_activate_effects(
            state, self.id, characters.Reason.DROISON
        )

    def woke(self) -> None:
        self.woke_tonight = True

    def _world_str(self, state: State) -> str:
        """For printing nice output representations of worlds"""
        ret = ' '.join(
            self.character_history 
            + [self.character._world_str(state)]
        )
        if self.is_dead:
            ret += ' 💀'
        return ret


@dataclass
class State:
    # The list of players starts with You as player 0 and proceeds clockwise
    players: list[Player]
    day_events: dict[int, list[Event]] = field(default_factory=dict)
    night_deaths: dict[int, list[PlayerID]] = field(default_factory=dict)
    finish_final_day: bool = False

    def __post_init__(self):
        """
        Post-process the human-entered state representation for the machine.
        Called before worlds are posited by overriding these characters.
        """
        for i, player in enumerate(self.players):
            player.id = i
        assert 1 not in self.night_deaths, "Can there be deaths on night 1?"
        # Make entering night deaths neater by accepting bare ints 
        for night, deaths in self.night_deaths.items():
            if not isinstance(deaths, Iterable):
                deaths = [deaths]
            for i, death in enumerate(deaths):
                if not isinstance(death, events.NightEvent):
                    assert isinstance(death, int), "Bad night_deaths value."
                    deaths[i] = events.NightDeath(death)
            self.night_deaths[night] = deaths
        for day, events_ in self.day_events.items():
            if isinstance(events_, events.Event):
                self.day_events[day] = [events_]

        # Events can be entered in Player.day_info or in State.day_events, b/c
        # that feels nice. Move them all to one place before the solve starts.
        for player in self.players:
            for day, maybe_event in list(player.day_info.items()):
                if isinstance(maybe_event, events.Event):
                    del player.day_info[day]
                    maybe_event.player = player.id
                    if day in self.day_events:
                        self.day_events[day].insert(0, maybe_event)
                    else:
                        self.day_events[day] = [maybe_event]
            # # Also, because typing out puzzles is hard :)
            for item in player.night_info.values():
                assert not isinstance(item, events.Event), f"{type(item)=}"

        self.max_day = max(
            max((max(p.day_info, default=0) for p in self.players)),
            max(self.day_events, default=0),
        )
        self.max_night = max(
            self.max_day,
            max((max(p.night_info, default=0) for p in self.players)),
            max(self.night_deaths, default=0),
        )
        self.max_day = max(self.max_day, self.max_night - 1)
        self.finish_final_day |= (self.max_day < self.max_night)

    def begin_game(self, allow_good_double_claims: bool) -> bool:
        """Called after player positions and characters have been chosen"""
        # Initialise data structures for game
        self.current_phase = Phase.SETUP
        self.phase_order_index = 0
        self.setup_order, self.night_order, self.day_order = [], [], []
        self.current_phase_order = self.setup_order
        self.update_character_index()
        self.initial_characters = tuple(type(p.character) for p in self.players)
        self.night, self.day = None, None
        self.previously_alive = [True] * len(self.players)

        self.math_misregistration_bounds = [0, 0]  # Setup pings incl. in N1.
        self.vortox = False  # The vortox will set this during setup

        if not allow_good_double_claims:
            good_claims = set()
            for player in self.players:
                if info.behaves_evil(self, player.id):
                    continue
                if player.claim in good_claims:
                    return False
                good_claims.add(player.claim)
        
        return True

    def fork(self) -> State:
        """
        Create a unique key for each set of possible branches in the state space
        so that (mainly for debugging) we can trace an output world back through
        the branches that created it. Thankfully the solver is deterministic.
        """
        ret = deepcopy(self)
        if _DEBUG:
            fork_count = _DEBUG_STATE_FORK_COUNTS[self.debug_key]
            ret.debug_key = self.debug_key + (fork_count,)
            _DEBUG_STATE_FORK_COUNTS[ret.debug_key] = 0
            _DEBUG_STATE_FORK_COUNTS[self.debug_key] += 1
        return ret
    
    def root_fork(self, fork_id) -> State:
        """
        Fork the root puzzle state. Due to multiprocessing, this method can't be
        aware of all other forks that have been created, so an explicit fork_id
        is required for deterministic debug keys.
        """
        ret = deepcopy(self)
        if _DEBUG:
            ret.debug_key = (fork_id,)
            _DEBUG_STATE_FORK_COUNTS.clear()
            _DEBUG_STATE_FORK_COUNTS[ret.debug_key] = 0
        return ret

    def _is_world(self, key: tuple[int] = _DEBUG_WORLD_KEY) -> bool:
        """
        Use debug keys generated during forks to determine if this state is an
        upstream choice that leads to the keyed world.
        """
        return _DEBUG and (
            len(self.debug_key) <= len(key)
            and all(a == b for a, b in zip(self.debug_key, key))
        )

    def run_next_player(self, round_: int | None) -> Generator[State]:
        if self.phase_order_index >= len(self.current_phase_order):
            yield self
            return
        player_id = self.current_phase_order[self.phase_order_index]
        character = self.players[player_id].character

        match self.current_phase:
            case Phase.SETUP:
                substates = character.run_setup(self, player_id)
            case Phase.NIGHT:
                characters.record_if_player_woke_tonight(self, player_id)
                substates = character.run_night(self, round_, player_id)                    
                substates = State.run_external_night_info(
                    substates, type(character), round_
                )
            case Phase.DAY:
                substates = character.run_day(self, round_, player_id)

        for substate in substates:
            substate.phase_order_index += 1
            yield substate
    
    @staticmethod
    def run_external_night_info(
        states: StateGen,
        character: type[Character],
        night: int,
    ) -> StateGen:
        """
        Check all information caused by this player's ability but reported by
        another player (e.g. Nightwatchman, Evil Twin).
        """
        for state in states:
            externals = state.external_info_registry.get((character, night), [])
            for external_info, player_id in externals:
                if not state.players[player_id].character.run_night_external(
                    state, external_info, player_id
                ):
                    break
            else:
                yield state

    def run_event(self, round_: int, event: int) -> StateGen:
        events = self.day_events.get(round_, None)
        if events is None:
            yield self
        else:
            yield from events[event](self)

    def end_setup(self) -> StateGen:
        self.current_phase = Phase.NIGHT
        self.current_phase_order = self.night_order
        self.phase_order_index = 0
        self.night = 1
        self.day = None
        yield self

    def end_night(self) -> StateGen:
        for player in self.players:
            player.woke_tonight = False

        # Check the right people have Died / Resurrected in the night
        currently_alive = [
            info.IsAlive(player)(self, None) is info.TRUE
            for player in range(len(self.players))
        ]
        currently_alive_gt = copy(self.previously_alive)
        if self.night in self.night_deaths:
            for death in self.night_deaths[self.night]:
                # `death` can either be a NightDeath or a NightResurrection
                # Deaths/Resurrections require players to be alive/dead resp.
                previously_alive_gt = isinstance(death, events.NightDeath)
                if self.previously_alive[death.player] != previously_alive_gt:
                    return
                currently_alive_gt[death.player] = not previously_alive_gt
        if currently_alive != currently_alive_gt:
            return
        del self.previously_alive

        # Check good players are what they claim to be
        for player in self.players:
            if not (
                player.character.is_liar 
                or player.is_evil
                or isinstance(player.character, player.claim)
            ):
                return

        self.math_misregistration_bounds = [0, 0]

        self.current_phase = Phase.DAY
        self.current_phase_order = self.day_order
        self.phase_order_index = 0
        self.day = self.night
        self.night = None
        yield self

    def end_day(self) -> StateGen:
        for player in self.players:
            if not player.character.end_day(self, self.day, player.id):
                return
        self.previously_alive = [
            info.IsAlive(player)(self, None) is info.TRUE
            for player in range(len(self.players))
        ]
        self.current_phase = Phase.NIGHT
        self.current_phase_order = self.night_order
        self.phase_order_index = 0
        self.night = self.day + 1
        self.day = None
        yield self

    def character_change(
        self,
        player_id: PlayerID,
        character: type[Character]
    ) -> StateGen:
        player = self.players[player_id]

        player.character_history.append(player.character._world_str(self))
        player.character_history.append(self._change_str())
        player.character.maybe_deactivate_effects(
            self, player_id, characters.Reason.CHARACTER_CHANGE
        )
        
        # Ammend night(/day/setup) order position
        if self.phase_order_index < len(self.current_phase_order):  # In phase
            active_player_id = self.current_phase_order[self.phase_order_index]
            active_character = type(self.players[active_player_id].character)
            global_order = GLOBAL_PHASE_ORDERS[self.current_phase]
            active_idx = global_order.index(active_character)
            old_idx = list_find(global_order, type(player.character), 9999)
            new_idx = list_find(global_order, character, 9999)
            self.phase_order_index += (
                (new_idx <= active_idx) - (old_idx <= active_idx)
            )
        
        player.character = character(
            first_night=self.night if self.night is not None else self.day + 1
        )
        self.update_character_index()

        for substate in player.character.run_setup(self, player_id):
            if not substate.check_game_over():
                yield substate

    def update_character_index(self):
        # Night/day/setup order
        self.setup_order.clear()
        self.night_order.clear()
        self.day_order.clear()
        for global_order, order in (
            (characters.GLOBAL_SETUP_ORDER, self.setup_order),
            (characters.GLOBAL_NIGHT_ORDER, self.night_order),
            (characters.GLOBAL_DAY_ORDER, self.day_order),
        ):
            for character in global_order:
                for player_id in range(len(self.players)):
                    if info.has_ability_of(self, player_id, character):
                        order.append(player_id)

        # Death_in_town callback registration
        self.death_in_town_callback_players = []
        for player_id, player in enumerate(self.players):
            if hasattr(player.character, "death_in_town"):
                self.death_in_town_callback_players.append(player_id)
        
        # External info retrieval 
        self.external_info_registry = defaultdict(list)
        for player in self.players:
            for (night, character), items in player.external_night_info.items():
                for item in items:
                    self.external_info_registry[(character, night)].append(
                        (item, player.id)
                    )
        self.external_info_registry = dict(self.external_info_registry)

    def death_in_town(self, dead_player_id: PlayerID) -> StateGen:
        """Trigger things that require global checks, e.g. Minstrel or SW."""
        dead_player = self.players[dead_player_id]

        def do_death_callback(states: StateGen, caller: PlayerID) -> StateGen:
            for state in states:
                callback = state.players[caller].character.death_in_town
                yield from callback(state, dead_player_id, caller)
        substates = [self]
        for caller in self.death_in_town_callback_players:
            substates = do_death_callback(substates, caller)

        if dead_player.character.category is not characters.DEMON:
            yield from substates
        else:
            # Game might end on Demon death
            for substate in substates:
                if not substate.check_game_over():
                    yield substate

    def check_game_over(self) -> bool:
        # TODO: evil win condition. Doesn't actually come up much when solving.
        all_demons_dead = not any(
            p.character.category is characters.DEMON and not p.is_dead
            for p in self.players
        )
        # TODO: Add Evil Twin / Mastermind check here.
        game_over = all_demons_dead  
        return game_over
    
    def math_misregistration(self, result: info.STBool | None = None):
        """
        Modify bounds on possible Mathematician pings this night.
        If misregistration is certain, no argument is needed. If it depends on
        an STBool being FALSE (e.g. a Ping from a character ability), that can
        be provided in `result`.
        """
        if result is info.TRUE:
            return
        self.math_misregistration_bounds[1] += 1
        if result is None or result is info.FALSE:
            self.math_misregistration_bounds[0] += 1

    def __str__(self) -> str:
        ret = [f'World{self.debug_key if _DEBUG else ""}(']
        pad = max(len(player.name) for player in self.players) + 1
        for player in self.players:
            char = type(player.character)
            rhs = player._world_str(self)
            colour = 0
            if char.is_liar:
                colour = '31' if player.is_evil else '34'
            ret.append(
                f'\033[{colour};1m{player.name: >{pad}} : {rhs}\033[0m'
            )
        ret.append(')')
        return '\n'.join(ret)
    
    def _change_str(self) -> str:
        match self.current_phase:
            case Phase.DAY:
                return f'-[D{self.day}]->'
            case Phase.NIGHT:
                return f'-[N{self.night}]->'
            case Phase.SETUP:
                return '-->'


@dataclass
class Puzzle:
    state: State
    possible_demons: list[Character]
    possible_minions: list[Character]
    possible_hidden_good: list[Character]
    possible_hidden_self: list[Character]
    category_counts: tuple[int, int, int, int] | None = None
    world_init_check: Callable[[State], bool] | None = None
    allow_good_double_claims: bool = True
    deduplicate_initial_characters: bool = True

    def __post_init__(self):
        if self.category_counts is None:
            self.category_counts = characters.DEFAULT_CATEGORY_COUNTS[
                len(self.state.players)
            ]
        self._validate_inputs()

    def _validate_inputs(self):
        """
        When I enter a new puzzle and it is not solved correctly, half the time
        it's because I have mis-entered the puzzle or forgotten to register
        newly implemented characters in the night order or other such repeated
        mistakes. This fn does a half-hearted job of catching such mistakes to
        reduce debugging time during development.
        """

        # Check all used characters are registered in the night order
        used_characters = (
            [type(p.character) for p in self.state.players]
            + self.possible_demons + self.possible_minions
            + self.possible_hidden_good + self.possible_hidden_self
        )
        registered_characters = (
            characters.GLOBAL_NIGHT_ORDER
            + characters.GLOBAL_DAY_ORDER 
            + characters.INACTIVE_CHARACTERS
        )
        for character in used_characters:
            if character not in registered_characters:
                raise ValueError(
                    f'Character {character.__name__} has not been placed in the '
                    'night order. Did you forget?'
                )
        
        # Check valid choices of hidden good characters
        for character in self.possible_hidden_good:
            if not character.is_liar:
                raise ValueError(
                    f"{character.__name__} can't be in possible_hidden_good"
                )
        for character in self.possible_demons:
            if character.category is not characters.DEMON:
                raise ValueError(f'{character.__name__} is not a Demon')
        for character in self.possible_minions:
            if character.category is not characters.MINION:
                raise ValueError(f'{character.__name__} is not a Minion')


def _check_valid_character_counts(
    puzzle: Puzzle,
    liar_characters: Iterable[type[Character]],
    liar_positions: Iterable[int],
) -> bool:
    """Check that the starting player category counts are legal."""
    setup = [p.claim for p in puzzle.state.players]
    for liar, position in zip(liar_characters, liar_positions):
        setup[position] = liar
        if position == 0 and liar not in puzzle.possible_hidden_self:
            return False
    T, O, M, D = puzzle.category_counts
    bounds = ((T, T), (O, O), (M, M), (D, D))
    for character in setup:
        bounds = character.modify_category_counts(bounds)
    actual_counts = Counter(character.category for character in setup)

    for (lo, hi), category in zip(bounds, characters.Categories):
        if not lo <= actual_counts[category] <= hi:
            return False
    return True
    

def _run_game_gen(
    states: StateGen,
    n_players: int,
    max_night: int,
    max_day: int,
    finish_final_day: bool,
    event_counts: Mapping[int, int],
) -> StateGen:
    """
    Chains together a big ol' stack of generators corresponding to each possible
    action of each player, forming a pipeline through which possible world 
    states flow. Only valid worlds are able to reach the end of the pipe.
    """	
    def apply_all(substates: StateGen, method: str, args: tuple[Any]):
        return (s for S in substates for s in getattr(S, method)(*args))

    for player in range(n_players):
        states = apply_all(states, 'run_next_player', (None, ))
    states = apply_all(states, 'end_setup', ())
    for round_ in range(1, max_night + 1):
        for player in range(n_players):
            states = apply_all(states, 'run_next_player', (round_, ))
        states = apply_all(states, 'end_night', ())
        if round_ <= max_day:
            for player in range(n_players):
                states = apply_all(states, 'run_next_player', (round_, ))
            for event in range(event_counts[round_]):
                states = apply_all(states, 'run_event', (round_, event))
            if round_ < max_day or finish_final_day:
                states = apply_all(states, 'end_day', ())

    yield from states


def _liar_placement_worker(
    puzzle_queue: Queue,
    liar_queue: Queue,
    num_processes: int,
):
    """Generate all possible initial placements of the hidden roles."""
    while (puzzle := puzzle_queue.get()) is not None:
        n_townsfolk, n_outsiders, n_minions, n_demons = puzzle.category_counts
        liar_combinations = it.product(
            it.combinations(puzzle.possible_demons, n_demons),
            it.chain(*[
                it.combinations(puzzle.possible_minions, i)
                for i in range(n_minions, len(puzzle.possible_minions) + 1)
            ]),
            it.chain(*[
                it.combinations(puzzle.possible_hidden_good, i)
                for i in range(len(puzzle.possible_hidden_good) + 1)
            ])
        )
        player_ids = list(range(len(puzzle.state.players)))
        dbg_idx = 0
        for demons, minions, hidden_good in liar_combinations:
            liars = demons + minions + hidden_good
            for liar_positions in it.permutations(player_ids, len(liars)):
                liar_queue.put((liars, liar_positions, dbg_idx))
                dbg_idx += 1

        # Work Done sentinel per process
        for _ in range(num_processes):
            liar_queue.put(None)


def _world_checking_worker(puzzle_q: Queue, liars_q: Queue, solutions_q: Queue):
    """Accepts starting configurations and finds all possible solutions."""

    while (puzzle := puzzle_q.get()) is not None:
        event_counts = defaultdict(int, {
            day: len(events) for day, events in puzzle.state.day_events.items()
        })

        while (liars := liars_q.get()) is not None:
            # Sanity check character counts before creating a new world
            liar_characters, liar_positions, debug_idx = liars
            if not _check_valid_character_counts(
                puzzle, liar_characters, liar_positions,
                # puzzle.category_counts, puzzle.possible_hidden_self,
            ):
                continue
            # Create the world and place the hidden characters
            world = puzzle.state.root_fork(debug_idx)
            for liar, position in zip(liar_characters, liar_positions):
                world.players[position].character = liar()
                world.players[position].is_evil = liar.category in (
                    characters.MINION, characters.DEMON
                )
            if not world.begin_game(puzzle.allow_good_double_claims):
                continue
            if (
                puzzle.world_init_check is not None
                and not puzzle.world_init_check(world)
            ):
                continue
            # Run the solver on the world
            for solution in _run_game_gen(
                [world],
                len(puzzle.state.players),
                puzzle.state.max_night,
                puzzle.state.max_day,
                puzzle.state.finish_final_day,
                event_counts,
            ):
                solutions_q.put(solution)
        solutions_q.put(None)


class Solver:
    """Manages the worker threads"""
    def __init__(self, num_processes=6):
        self.puzzle_queue = Queue(maxsize=num_processes + 1)
        self.liars_queue = Queue(maxsize=num_processes)
        self.solutions_queue = Queue(maxsize=num_processes)
        self.num_processes = num_processes

        self.all_workers = [
            Process(
                target=_world_checking_worker,
                daemon=True,
                args=(self.puzzle_queue, self.liars_queue, self.solutions_queue)
            )
            for _ in range(num_processes)
        ]
        self.all_workers.append(
            Process(
                target=_liar_placement_worker,
                daemon=True,
                args=(self.puzzle_queue, self.liars_queue, num_processes)
            )
        )
    
    def __enter__(self):
        for process in self.all_workers:
            process.start()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for _ in range(self.num_processes + 1):
            self.puzzle_queue.put(None)
        for process in self.all_workers:
            process.join()

    def generate_worlds(self, puzzle: Puzzle) -> StateGen:
        for _ in range(self.num_processes + 1):
            self.puzzle_queue.put(puzzle)
        
        seen_solutions = set()
        finish_count = 0
        while True:
            solution = self.solutions_queue.get()
            if solution is None:  # Done sentinel
                finish_count += 1
                if finish_count == self.num_processes:
                    break
            elif (
                not puzzle.deduplicate_initial_characters
                or solution.initial_characters not in seen_solutions
            ):
                seen_solutions.add(solution.initial_characters)
                yield solution


def list_find(X: list, item: Any, sentinel: int) -> int:
    try:
        return X.index(item)
    except ValueError:
        return sentinel