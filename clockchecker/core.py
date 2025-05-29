from __future__ import annotations

from collections.abc import Iterator, Iterable, Mapping
from collections import Counter, defaultdict
from contextlib import nullcontext
from copy import copy, deepcopy
from dataclasses import dataclass, field, InitVar
import enum
import itertools as it
import os
from typing import Any, Callable, TypeAlias

try:
    from multiprocessing import Queue, Process
    MULTIPROCESSING_AVAILABLE = True
except ModuleNotFoundError:
    MULTIPROCESSING_AVAILABLE = False


from . import characters
from .characters import Character
from . import events
from .events import Event
from . import info
from .info import PlayerID, Info



# Set True to enable debug mode
_DEBUG = os.environ.get('DEBUG', False)
_DEBUG_STATE_FORK_COUNTS = {}
_DEBUG_WORLD_KEYS = [
    # (43519, 5, 8, 3, 11, 4, 8, 3, 3, 0, 3, 0, 4),
]


StateGen: TypeAlias = Iterator['State']
LiarPlacement: TypeAlias = tuple[list[type['Character']], tuple[int, ...], int]
LiarGen: TypeAlias = Iterator[LiarPlacement]


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
    night_info: dict[int, Info | list[Info]] = field(default_factory=dict)
    day_info: dict[int, Info] = field(default_factory=dict)
    character: Character | None = None

    is_evil: bool = False
    is_dead: bool = False
    woke_tonight: bool = False
    droison_count: int = 0
    character_history: list[str] = field(default_factory=list)

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

    def __post_init__(self):
        self.character = self.claim()

        # Reorganise info so it can be easily used in night order
        self.external_night_info = defaultdict(list)
        all_claims = set([self.claim])
        existing_night_info = list(self.night_info.items())
        self.night_info: Mapping[tuple[int, type[Character]], info.Info] = {}
        for night, night_info in existing_night_info:
            if not isinstance(night_info, list):
                night_info = [night_info]
            for item in night_info:
                # Because typing out puzzles is hard :)
                assert not isinstance(item, events.Event), f"{type(item)=}"

                if isinstance(item, characters.Philosopher.Choice):
                    all_claims.add(item.character)

                if (character := info.info_creator(item)) in all_claims:
                    assert (night, character) not in self.night_info, (
                        "One info per night from own ability (for now?)."
                    )
                    self.night_info[(night, character)] = item
                else:
                    self.external_night_info[(night, character)].append(item)

        self.external_night_info = dict(self.external_night_info)
    
    def _extract_info(self):
        night_info, day_info = self.night_info, self.day_info
        del self.night_info
        del self.day_info
        return night_info, day_info


@dataclass
class State:
    puzzle: Puzzle
    players: list[Player]
    day_events: dict[int, list[Event]]
    night_deaths: dict[int, list[PlayerID]]

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

        for player in self.players:
            # Events can be entered in Player.day_info or in State.day_events,
            # b/c that feels nice. Move them all to one place before solving.
            for day, maybe_event in list(player.day_info.items()):
                if isinstance(maybe_event, events.Event):
                    del player.day_info[day]
                    maybe_event.player = player.id
                    if day in self.day_events:
                        self.day_events[day].insert(0, maybe_event)
                    else:
                        self.day_events[day] = [maybe_event]

        if _DEBUG:
            self.debug_key = ()  # The root debug key

    def begin_game(self, allow_good_double_claims: bool) -> bool:
        """Called after player positions and characters have been chosen"""
        self.current_phase = Phase.SETUP
        self.phase_order_index = 0
        self.update_character_callbacks()
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

    def fork(self, fork_id: int | None = None) -> State:
        """
        Create a unique key for each set of possible branches in the state space
        so that (mainly for debugging) we can trace an output world back through
        the branches that created it. Thankfully the solver is deterministic.
        """
        # deepcopy everything except the puzzle definition, which is shared
        puzzle, self.puzzle = self.puzzle, None
        ret = deepcopy(self)
        self.puzzle, ret.puzzle = puzzle, puzzle
        if _DEBUG:
            if fork_id is None:
                fork_id = _DEBUG_STATE_FORK_COUNTS[self.debug_key]
                _DEBUG_STATE_FORK_COUNTS[self.debug_key] += 1
            else:
                _DEBUG_STATE_FORK_COUNTS.clear()
            ret.debug_key = self.debug_key + (fork_id,)
            _DEBUG_STATE_FORK_COUNTS[ret.debug_key] = 0
            if _DEBUG_WORLD_KEYS and not ret._is_world():
                ret.debug_cull = True
        return ret
    
    def get_night_info(
        self,
        character: type[Character],
        player: PlayerID,
        night: int,
    ):
        return self.puzzle._night_info[player].get((night, character), None)
    
    def get_day_info(self, player: PlayerID, day: int):
        return self.puzzle._day_info[player].get(day, None)

    def _is_world(self, key: tuple[int] | None = None) -> bool:
        """
        Use debug keys generated during forks to determine if this state is an
        upstream choice that leads to the keyed world.
        """
        if not _DEBUG:
            return False
        keys = [key] if key is not None else _DEBUG_WORLD_KEYS
        return any(
            all(a == b for a, b in zip(self.debug_key, _key))
            for _key in keys
        )

    def run_next_character(self) -> StateGen:
        """Run all players who have the ability of the next character."""
        order = (
            self.puzzle.night_order if self.current_phase is Phase.NIGHT
            else self.puzzle.day_order if self.current_phase is Phase.DAY
            else self.puzzle.setup_order
        )

        if self.phase_order_index >= len(order):
            yield self
            return

        character_t = order[self.phase_order_index]
        self.currently_acting_character = character_t
        self.players_still_to_act = [
            pid for pid in range(len(self.players))
            if info.acts_like(self, pid, character_t)
        ]
        for state in self.run_all_players_with_currently_acting_character():
            state.phase_order_index += 1
            yield state

    def run_all_players_with_currently_acting_character(self) -> StateGen:
        """
        Multiple characters might have the ability of the character acting in
        the current night/day/setup order step, run them all.
        """
        if not self.players_still_to_act:
            yield self
            return

        pid = self.players_still_to_act.pop()
        player = self.players[pid]
        
        if self._is_world():
            print(f'Running {self.current_phase.name} ? for '
                  f'{player.name} ({type(player.character).__name__})')

        match self.current_phase:
            case Phase.NIGHT:
                if characters.Chambermaid.player_wakes_tonight(self, pid):
                    player.woke()
                states = player.character.run_night(self, self.night, pid)
                states = State.run_external_night_info(
                    states, self.currently_acting_character, self.night
                )
            case Phase.DAY:
                states = player.character.run_day(self, self.day, pid)
            case Phase.SETUP:
                states = player.character.run_setup(self, pid)

        for state in states:
            if hasattr(states, 'debug_cull'):
                continue
            # Recursive tail-calls can set up a variable-depth generator stack
            # corresponding to how many players have the active ability, and
            # handle players changing character mid-turn.
            yield from state.run_all_players_with_currently_acting_character()
    
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
            if self._is_world():
                names = {p: plyr.name for p, plyr in enumerate(self.players)}
                print(f'Running {info.pretty_print(events[event], names)}')
            yield from events[event](self)

    def end_setup(self) -> StateGen:
        self.current_phase = Phase.NIGHT
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
        if player_id in self.players_still_to_act:
            self.players_still_to_act.remove(player_id)

        next_night = self.night if self.night is not None else self.day + 1
        player.character = character(first_night=next_night)
        self.update_character_callbacks()

        for substate in player.character.run_setup(self, player_id):
            if not substate.check_game_over():
                yield substate

    def update_character_callbacks(self):
        """Re-gather callbacks after character changes"""

        # Death_in_town callback registration
        self.pre_death_in_town_callback_players = []
        for player_id, player in enumerate(self.players):
            if hasattr(player.character, "pre_death_in_town"):
                self.pre_death_in_town_callback_players.append(player_id)
        
        # External info retrieval 
        self.external_info_registry = defaultdict(list)
        for player in self.players:
            for (night, character), items in player.external_night_info.items():
                for item in items:
                    self.external_info_registry[(character, night)].append(
                        (item, player.id)
                    )
        self.external_info_registry = dict(self.external_info_registry)
    
    def player_upcoming_in_night_order(self, player: PlayerID) -> bool:
        assert self.current_phase is Phase.NIGHT
        char = type(self.players[player].character)
        remaining_chars = self.puzzle.night_order[self.phase_order_index + 1:]
        return player in self.players_still_to_act or char in remaining_chars
    
    def pre_death_in_town(self, dying_player_id: PlayerID) -> StateGen:
        """Trigger things that require global checks, e.g. Minstrel or SW."""
        if not self.pre_death_in_town_callback_players:
            yield self; return
        def do_death_callback(states: StateGen, caller: PlayerID) -> StateGen:
            for state in states:
                callback = state.players[caller].character.pre_death_in_town
                yield from callback(state, dying_player_id, caller)
        for caller in self.pre_death_in_town_callback_players:
            yield from do_death_callback([self], caller)

    def post_death_in_town(self, dead_player_id: PlayerID) -> StateGen:
        """Called immediately after a player died."""
        dead_character = self.players[dead_player_id].character
        if (
            dead_character.category is characters.DEMON
            and self.check_game_over()
        ):
            return
        yield self

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
            if char.is_liar or player.is_evil:
                colour = '31' if player.is_evil else '34'
            ret.append(
                f'\033[{colour};1m{player.name: >{pad}}: {rhs}\033[0m'
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
    players: list[Player]
    hidden_characters: InitVar[list[type[Character]]]
    hidden_self: list[type[Character]]
    day_events: dict[int, list[Event]] = field(default_factory=dict)
    night_deaths: dict[int, list[PlayerID]] = field(default_factory=dict)
    category_counts: tuple[int, int, int, int] | None = None
    allow_good_double_claims: bool = True
    deduplicate_initial_characters: bool = True
    finish_final_day: bool = False

    def __post_init__(self, hidden_characters):
        if self.category_counts is None:
            self.category_counts = characters.DEFAULT_CATEGORY_COUNTS[
                len(self.players)
            ]
        self.demons, self.minions, self.hidden_good = [], [], []
        for character in hidden_characters:
            if character.category is characters.DEMON:
                self.demons.append(character)
            elif character.category is characters.MINION:
                self.minions.append(character)
            else:
                self.hidden_good.append(character)
        self._validate_inputs()

        self._max_day = max(
            max((max(p.day_info, default=0) for p in self.players)),
            max(self.day_events, default=0),
        )
        self._max_night = max(
            self._max_day,
            max((
                max((n for n, _ in p.night_info), default=0)
                for p in self.players
            )),
            max(self.night_deaths, default=0),
        )
        self._max_day = max(self._max_day, self._max_night - 1)
        self.finish_final_day |= (self._max_day < self._max_night)

        self._state = State(self, self.players, self.day_events, self.night_deaths)
        self._night_info, self._day_info = zip(*(
            player._extract_info() for player in self.players
        ))

        script = set(
            [p.claim for p in self.players]
            + hidden_characters
            + self.hidden_self
        )
        self.setup_order = [
            character for character in characters.GLOBAL_SETUP_ORDER
            if character in script
        ]
        self.night_order = [
            character for character in characters.GLOBAL_NIGHT_ORDER
            if character in script
        ]
        self.day_order = [
            character for character in characters.GLOBAL_DAY_ORDER
            if character in script
        ]

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
            [type(p.character) for p in self.players]
            + self.demons + self.minions
            + self.hidden_good + self.hidden_self
        )
        registered_characters = (
            characters.GLOBAL_NIGHT_ORDER
            + characters.GLOBAL_DAY_ORDER 
            + characters.INACTIVE_CHARACTERS
        )
        for character in used_characters:
            if character not in registered_characters:
                raise ValueError(
                    f'Character {character.__name__} has not been placed in the'
                    ' night order. Did you forget?'
                )
        
        # Check valid choices of hidden good characters
        for character in self.hidden_good:
            if not character.is_liar:
                raise ValueError(
                    f"{character.__name__} can't be in hidden_good"
                )
        for character in self.demons:
            if character.category is not characters.DEMON:
                raise ValueError(f'{character.__name__} is not a Demon')
        for character in self.minions:
            if character.category is not characters.MINION:
                raise ValueError(f'{character.__name__} is not a Minion')
    
    def __str__(self) -> str:
        ret = ['Puzzle(\n  \033[0;4mPlayers\033[0m']
        names = [player.name for player in self.players]
        for player_id, player in enumerate(self.players):
            ret.append(f'    \033[33;1m{player.name} claims '
                       f'{player.claim.__name__}\033[0m')
            for c, all_info in (('N', self._night_info), ('D', self._day_info)):
                for day, info_item in all_info[player_id].items():
                    if isinstance(day, tuple):
                        day = day[0]
                    info_str = info.pretty_print(info_item, names)
                    ret.append(f'      {c}{day}: {info_str}')
        ret.extend([
            '\n  \033[0;4mPossible Hidden Characters\033[0m',
            '    Other Players: [{}]'.format(", ".join(
                character.__name__ for character in 
                self.demons + self.minions + self.hidden_good
            )),
            f'    You: [{", ".join(c.__name__ for c in self.hidden_self)}]',
        ])
        if self.day_events:
            ret.append('\n  \033[0;4mDay Events\033[0m')
            for d, evs in self.day_events.items():
                for ev in evs:
                    ret.append(f'    D{d}: {info.pretty_print(ev, names)}')
        if self.night_deaths:
            ret.append('\n  \033[0;4mNight Deaths\033[0m')
            for d, deaths in self.night_deaths.items():
                for death in deaths:
                    ret.append(f'    N{d}: {info.pretty_print(death, names)}')
        ret.append(')')
        return '\n'.join(ret)


def _check_valid_character_counts(
    puzzle: Puzzle,
    liar_characters: Iterable[type[Character]],
    liar_positions: Iterable[int],
) -> bool:
    """Check that the starting player category counts are legal."""
    setup = [p.claim for p in puzzle.players]
    for liar, position in zip(liar_characters, liar_positions):
        setup[position] = liar
        if position == 0 and liar not in puzzle.hidden_self:
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


def _liar_placement_gen(puzzle: Puzzle) -> LiarGen:
    """Generate all possible initial placements of the hidden roles."""
    n_townsfolk, n_outsiders, n_minions, n_demons = puzzle.category_counts
    liar_combinations = it.product(
        it.combinations(puzzle.demons, n_demons),
        it.chain(*[
            it.combinations(puzzle.minions, i)
            for i in range(n_minions, len(puzzle.minions) + 1)
        ]),
        it.chain(*[
            it.combinations(puzzle.hidden_good, i)
            for i in range(len(puzzle.hidden_good) + 1)
        ])
    )
    player_ids = list(range(len(puzzle.players)))
    dbg_idx = 0
    for demons, minions, hidden_good in liar_combinations:
        liars = demons + minions + hidden_good
        for liar_positions in it.permutations(player_ids, len(liars)):
            yield (liars, liar_positions, dbg_idx)
            dbg_idx += 1


def _world_check_gen(puzzle: Puzzle, liars_generator: LiarGen) -> StateGen:
    """Accepts starting configurations and finds all possible solutions."""

    def apply_all(substates: StateGen, method: str, args: tuple[Any] = ()):
        return (s for S in substates for s in getattr(S, method)(*args))

    event_counts = defaultdict(int, {
        day: len(events) for day, events in puzzle.day_events.items()
    })

    for liar_characters, liar_positions, debug_idx in liars_generator:
        # Sanity check character counts before creating a new world
        if not _check_valid_character_counts(
            puzzle, liar_characters, liar_positions,
        ):
            continue
        # Create the world and place the hidden characters
        world = puzzle._state.fork(debug_idx)
        for liar, position in zip(liar_characters, liar_positions):
            world.players[position].character = liar()
            world.players[position].is_evil = liar.category in (
                characters.MINION, characters.DEMON
            )
        if not world.begin_game(puzzle.allow_good_double_claims):
            continue
    
        # Chains together a big ol' stack of generators corresponding to each
        # possible action of each player, forming a pipeline through which
        # possible world states flow. Only valid worlds are able to reach the
        # end of the pipe.
        worlds = [world]
        for player in range(len(puzzle.setup_order)):
            worlds = apply_all(worlds, 'run_next_character')
        worlds = apply_all(worlds, 'end_setup')
        for round_ in range(1, puzzle._max_night + 1):
            for player in range(len(puzzle.night_order)):
                worlds = apply_all(worlds, 'run_next_character')
            worlds = apply_all(worlds, 'end_night')
            if round_ <= puzzle._max_day:
                for player in range(len(puzzle.day_order)):
                    worlds = apply_all(worlds, 'run_next_character')
                for event in range(event_counts[round_]):
                    worlds = apply_all(worlds, 'run_event', (round_, event))
                if round_ < puzzle._max_day or puzzle.finish_final_day:
                    worlds = apply_all(worlds, 'end_day')
        yield from worlds


def _filter_solutions(puzzle: Puzzle, solutions: StateGen) -> StateGen:
    if not puzzle.deduplicate_initial_characters:
        yield from solutions
    else:
        seen_solutions = set()
        for solution in solutions:
            if solution.initial_characters not in seen_solutions:
                seen_solutions.add(solution.initial_characters)
                yield solution

    
def _world_checking_worker(puzzle: Puzzle, liars_q: Queue, solutions_q: Queue):
    def liars_gen():
        while (liars := liars_q.get()) is not None:
            yield liars
    for solution in _world_check_gen(puzzle, liars_gen()):
        solutions_q.put(solution)
    solutions_q.put(None)  # Finished Sentinel

def _liar_placement_worker(puzzle: Puzzle, liars_q: Queue, num_procs: int):
    for placement in _liar_placement_gen(puzzle):
        liars_q.put(placement)
    for _ in range(num_procs):
        liars_q.put(None)  # Finished Sentinel

def _solution_collecting_worker(solutions_q: Queue, num_procs: int) -> StateGen:
    finish_count = 0
    while True:
        solution = solutions_q.get()
        if solution is None:  # Finished Sentinel
            finish_count += 1
            if finish_count == num_procs:
                return
        else:
            yield solution


def solve(puzzle: Puzzle, num_processes=None) -> StateGen:
    """Top level solver method, accepts a puzzle and generates solutions."""

    if num_processes is None:
        num_processes = os.cpu_count()

    if num_processes == 1 or not MULTIPROCESSING_AVAILABLE:
        # Non-parallel version just runs everything in one process.
        liars = _liar_placement_gen(puzzle)
        solutions = _world_check_gen(puzzle, liars)
        solutions = _filter_solutions(puzzle, solutions)
        yield from solutions
        return

    # Parallel version
    liars_queue = Queue(maxsize=num_processes)
    solutions_queue = Queue(maxsize=num_processes)

    all_workers = [
        Process(
            target=_world_checking_worker,
            daemon=True,
            args=(puzzle, liars_queue, solutions_queue)
        )
        for _ in range(num_processes)
    ]
    all_workers.append(
        Process(
            target=_liar_placement_worker,
            daemon=True,
            args=(puzzle, liars_queue, num_processes)
        )
    )

    for worker in all_workers:
        worker.start()

    solutions = _solution_collecting_worker(solutions_queue, num_processes)
    solutions = _filter_solutions(puzzle, solutions)
    yield from _filter_solutions(puzzle, solutions)
        
    for worker in all_workers:
        worker.join()
