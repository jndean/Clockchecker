from __future__ import annotations

from collections.abc import Iterator, Iterable, Mapping
from collections import Counter, defaultdict
from copy import copy, deepcopy
from dataclasses import dataclass, field, InitVar
import enum
import inspect
import os
from typing import Callable, TypeAlias


from . import characters
from .characters import Character
from . import events
from .events import Event
from . import info
from .info import PlayerID, Info



# Flags to enable features for development
_PROFILING = os.environ.get('PROFILING', False)
_DEBUG = os.environ.get('DEBUG', False) or _PROFILING

_PROFILING_FORK_LOCATIONS = Counter()
_DEBUG_STATE_FORK_COUNTS = {}
_DEBUG_LOG_RECENT = None
_DEBUG_WORLD_KEYS = [
    # (45, 0, 0, 3, 1, 3, 3),
]


StateGen: TypeAlias = Iterator['State']

class Phase(enum.Enum):
    NIGHT = enum.auto()
    DAY = enum.auto()
    SETUP = enum.auto()


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
    ever_behaved_evil: bool = False

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

    def get_ability(
        self,
        character_t: type[Character] | None,
    ) -> Character | None:
        """
        Retrieve ability implementation from a player. If the character_t
        is None, returns the player's root character. Otherwise, recursively
        searches for any wrapped character of the given type. E.g., if
        called on the Philo-Alchemist-Goblin, you would want to specify
        whether you were accessing the Philosopher, Alchemist or Goblin
        instance stored on the player.
        """
        if character_t is None:
            return self.character
        if (ability := self.character.get_ability(character_t)) is not None:
            return ability
        if (b_ability := getattr(self, 'boffin_ability', None)) is not None:
            return b_ability.get_ability(character_t)
        return None

    def has_ability(self, character_t: type[Character]) -> bool:
        """
        Only concerned with whether it is legal for this player to use
        the specified ability, does not consider droisoning, which
        should be handled by the ability implementation.
        """
        return self.character.get_ability(character_t) is not None

    def get_ability_that_acts_like(
        self,
        character_t: type[Character],
    ) -> Character | None:
        """
        Retrieve ability implementation from a player, which acts_like the
        specified character. (E.g., for running the Drunk at the night-order
        slot of their simulated ability).
        """
        if (ability := self.get_ability(character_t)) is not None:
            return ability
        if self.character.acts_like(character_t):
            return self.character
        boffin_ability = getattr(self, 'boffin_ability', None)
        if boffin_ability is not None and boffin_ability.acts_like(character_t):
            return boffin_ability
        return None

    def acts_like(self, character_t: type[Character]) -> bool:
        return self.get_ability_that_acts_like(character_t) is not None

    def get_misreg_categories(
        self,
        state: State,
    ) -> tuple[characters.Category]:
        """
        Get the Categories this Player can misregister as. Recurses into wrapped
        characters, and handles droisoning, including awkward droisoned
        Boffin abilities.
        """
        categories = (
            () if self.droison_count
            else self.character.misregister_categories
        )
        # boffin_ability is only present when the Boffin is sober-and-healthy
        if hasattr(self, 'boffin_ability'):
            categories = tuple(set(
                categories + self.boffin_ability.misregister_categories
            ))
        return categories

    @property
    def vigormortised(self):
        return getattr(self.character, 'vigormortised', False)

    @property
    def lies_about_self(self):
        return (
            self.character.lies_about_self
            or getattr(self, 'speculative_ceremad', False)
        )

    def _world_str(self, state: State) -> str:
        """For printing nice output representations of worlds"""
        items = self.character_history + [self.character._world_str(state)]
        if hasattr(self, 'boffin_ability'):
            boffin_repr = self.boffin_ability._world_str(state)
            items.append(f'with Boffin[{boffin_repr}]')
        if self.is_dead:
            items.append('💀')
        if self.droison_count:
            items.append('🧪')
        if hasattr(self, 'speculative_evil'):
            items.append('(behaves evil)')
        return ' '.join(items)

    def __post_init__(self):
        self.character = self.claim()

        # Reorganise info so it can be easily used in night order
        self.external_night_info = defaultdict(list)
        existing_night_info = list(self.night_info.items())
        self.night_info: Mapping[tuple[int, type[Character]], info.Info] = {}
        for night, night_info in existing_night_info:
            if not isinstance(night_info, list):
                night_info = [night_info]
            for item in night_info:
                # Because typing out puzzles is hard :)
                assert not isinstance(item, events.Event), f"{type(item)=}"

                character = info.info_creator(item)
                if isinstance(item, (info.Info, info.NotInfo)):
                    assert (night, character) not in self.night_info, (
                        "One info per night from own ability (for now?)."
                    )
                    self.night_info[(night, character)] = item
                else:
                    assert isinstance(item, info.ExternalInfo)
                    self.external_night_info[(night, character)].append(item)

        self.external_night_info = dict(self.external_night_info)

    def _extract_info(self):
        # TODO: These should be created in Puzzle, not State, obviously.
        night_info, day_info = self.night_info, self.day_info
        ext_night_info = self.external_night_info
        del self.night_info
        del self.day_info
        del self.external_night_info
        return night_info, day_info, ext_night_info


@dataclass
class State:
    puzzle: Puzzle
    players: list[Player]

    def __post_init__(self):
        if _DEBUG:
            self.debug_key = ()  # The root debug key

    @property
    def player_ids(self):
        return range(len(self.players))

    def begin_game(self, allow_duplicate_tokens_in_bag: bool) -> bool:
        """Called after player positions and characters have been chosen"""
        self.current_phase = Phase.SETUP
        self.phase_order_index = 0
        self.update_character_callbacks()
        self.initial_characters = tuple(type(p.character) for p in self.players)
        self.night, self.day = None, None
        self.previously_alive = [True] * len(self.players)

        self._math_misregistration_bounds = [0, 0]  # Setup pings incl. in N1.
        self._math_misregisterers = set()
        self.vortox = False  # The vortox will set this during setup

        if not allow_duplicate_tokens_in_bag:
            # Reject good double claims
            good_claims = set()
            for player in self.players:
                if (
                    info.behaves_evil(self, player.id)
                    or (
                        # E.g. The Mutant may double claim but not the Drunk
                        player.lies_about_self
                        and not player.character.draws_wrong_token()
                    )
                ):
                    continue
                if player.claim in good_claims:
                    return False
                good_claims.add(player.claim)

        return True

    def fork(self, fork_id: tuple[int, ...] | None = None) -> State:
        """
        Create a unique key for each set of possible branches in the state space
        so that (mainly for debugging) we can trace an output world back through
        the branches that created it. For this reason we keep the solver
        deterministic.
        """
        if _PROFILING and fork_id is None:
            record_fork_caller(self.debug_key, 1)

        # deepcopy everything except the puzzle definition, which is shared
        puzzle, self.puzzle = self.puzzle, None
        ret = deepcopy(self)
        self.puzzle, ret.puzzle = puzzle, puzzle

        if _DEBUG:
            if fork_id is None:
                fork_id = (_DEBUG_STATE_FORK_COUNTS[self.debug_key],)
                _DEBUG_STATE_FORK_COUNTS[self.debug_key] += 1
            ret.debug_key = self.debug_key + fork_id
            _DEBUG_STATE_FORK_COUNTS[ret.debug_key] = 0
            if _DEBUG_WORLD_KEYS and not ret._is_world():
                ret.cull_branch = True

        if puzzle.user_interrupt is not None and puzzle.user_interrupt():
            raise InterruptedError('User requested solve stops')
        return ret

    def get_night_info(
        self,
        character: type[Character],
        player: PlayerID,
        night: int,
    ):
        return self.puzzle._night_info[player].get((night, character), None)

    def get_day_info(self, player: PlayerID):
        return self.puzzle._day_info[player].get(self.day, None)

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

    def log(self, message: str | Callable[[], str]):
        """
        When _DEBUG is enabled, log a trace of actions in a tree-like format
        that make it slightly easier to follow what's happening in the
        depth-first search of the possibility space.
        """
        if self._is_world():
            if not isinstance(message, str):
                message = message()
            global _DEBUG_LOG_RECENT
            underhang = '↝' if self.debug_key == _DEBUG_LOG_RECENT else ''
            print(f'S{self.debug_key}{underhang} {message}')
            _DEBUG_LOG_RECENT = self.debug_key

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
            if self.players[pid].acts_like(character_t)
        ]
        states = self.run_all_players_with_currently_acting_character()
        if self.current_phase is Phase.NIGHT:
            states = State.run_external_night_info(
                states, self.currently_acting_character, self.night
            )
        for state in states:
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
        ability = player.get_ability_that_acts_like(
            self.currently_acting_character
        )
        if ability is None:
            raise RuntimeError(
                "Player appears to have lost an ability within that ability's "
                "slot in the night order. Is that really possible? If so, "
                "feel free to remove this error and continue recursing."
            )

        # Some telemetry that is nice to see when debug mode is enabled
        round_ = self.night if self.night else self.day if self.day else ''
        claim = (
            '' if player.claim is self.currently_acting_character
            else f' claiming {player.claim.__name__}'
        )
        self.log(
            f'[{self.current_phase.name} {round_} '
            f'{type(ability).__name__}] for {player.name} (the '
            f'{type(player.character).__name__}{claim})'
        )

        match self.current_phase:
            case Phase.NIGHT:
                if ability.wakes_tonight(self, pid):
                    player.woke()
                states = ability.run_night(self, pid)
            case Phase.DAY:
                states = ability.run_day(self, pid)
            case Phase.SETUP:
                states = ability.run_setup(self, pid)

        # Recursive tail-calls can set up a variable-depth generator stack
        # corresponding to how many players have the active ability, and
        # handle players changing character mid-turn.
        yield from apply_all(
            states,
            lambda s: s.run_all_players_with_currently_acting_character()
        )

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
            externals = state.puzzle.external_info_registry.get(
                (character, night), []
            )
            for external_info, player_id in externals:
                if not state.players[player_id].character.run_night_external(
                    state, external_info, player_id
                ):
                    break
            else:
                yield state

    def run_event(self, round_: int, event: int) -> StateGen:
        events = self.puzzle.day_events.get(round_, None)
        if events is None:
            yield self
        else:
            self.log(lambda: info.pretty_print(
                events[event],
                {p: player.name for p, player in enumerate(self.players)}
            ))
            yield from events[event](self)

    def end_setup(self) -> StateGen:
        # Check good players are what they claim to be
        for player in self.players:
            if not (
                isinstance(player.character, player.claim)
                or info.behaves_evil(self, player.id)
                or player.lies_about_self
            ):
                return
        self.current_phase = Phase.NIGHT
        self.phase_order_index = 0
        self.night = 1
        self.day = None
        yield self

    def end_night(self) -> StateGen:
        # Split into this func, which handles generating all the possible night
        # end scenarios using each character's end_night function, and the
        # _end_night function, which handles actually applying the end-of-night
        # book-keeping to each of those generated states.
        self.log(f'[NIGHT {self.night} END]')

        def end_character_nights(state, pid):
            character = state.players[pid].character
            yield from character.end_night(state, pid)

        states = [self]
        for pid in self.player_ids:
            states = apply_all(states, end_character_nights, pid=pid)
        states = apply_all(states, lambda state: state._end_night())
        yield from states

    def _end_night(self) -> StateGen:
        for char_t in self.puzzle.script:
            if not char_t.global_end_night(self):
                return
        for player in self.players:
            player.woke_tonight = False

        # Check the right people have Died / Resurrected in the night
        currently_alive = [
            info.IsAlive(player)(self, None).is_true()
            for player in range(len(self.players))
        ]
        currently_alive_gt = copy(self.previously_alive)
        if self.night in self.puzzle.night_deaths:
            for death in self.puzzle.night_deaths[self.night]:
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
                isinstance(player.character, player.claim)
                or info.behaves_evil(self, player.id)
                or player.lies_about_self
            ):
                return

        self._math_misregistration_bounds = [0, 0]
        self._math_misregisterers = set()

        self.current_phase = Phase.DAY
        self.phase_order_index = 0
        self.day = self.night
        self.night = None
        yield self

    def end_day(self) -> StateGen:
        def end_character_days(state, pid):
            character = state.players[pid].character
            yield from character.end_day(state, pid)
        states = [self]
        for pid in self.player_ids:
            states = apply_all(states, end_character_days, pid=pid)
        states = apply_all(states, lambda state: state._end_day())
        yield from states

    def _end_day(self) -> StateGen:
        self.previously_alive = [
            info.IsAlive(player)(self, None).is_true()
            for player in range(len(self.players))
        ]
        self.current_phase = Phase.NIGHT
        self.phase_order_index = 0
        self.night = self.day + 1
        self.day = None
        yield self

    def change_alignment(self, pid: PlayerID, is_evil: bool) -> StateGen:
        # Returns a StateGen because one day I will implement alignment-change
        # event callbacks that other characters may respond to (e.g. FT, ET).
        player = self.players[pid]
        player.is_evil = is_evil
        player.ever_behaved_evil |= info.behaves_evil(self, pid)
        yield self

    def change_character(
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
                behaves_evil = info.behaves_evil(substate, player_id)
                substate.players[player_id].ever_behaved_evil |= behaves_evil
                yield substate

    def update_character_callbacks(self):
        """Re-gather callbacks after character changes"""
        self.pre_death_in_town_callback_players = []
        for player_id, player in enumerate(self.players):
            if hasattr(player.character, "pre_death_in_town"):
                self.pre_death_in_town_callback_players.append(player_id)

    def player_upcoming_in_night_order(self, player: PlayerID) -> bool:
        assert self.current_phase is Phase.NIGHT
        char = type(self.players[player].character)
        remaining_chars = self.puzzle.night_order[self.phase_order_index + 1:]
        return player in self.players_still_to_act or char in remaining_chars

    def pre_death_in_town(self, dying_player_id: PlayerID) -> StateGen:
        """Trigger things that require global checks, e.g. Minstrel or SW."""
        states = [self]
        for caller in self.pre_death_in_town_callback_players:
            states = apply_all(states, lambda state, caller=caller: (
                state.players[caller].character.pre_death_in_town(
                    state, dying_player_id, caller
                )
            ))
        yield from states

    def post_death_in_town(self, dead_player_id: PlayerID) -> StateGen:
        """Called immediately after a player died."""
        dead_character = self.players[dead_player_id].character
        if (
            isinstance(dead_character, characters.Demon)
            and self.check_game_over()
        ):
            return
        yield self

    def check_game_over(self) -> bool:
        """The game is never over, so reject games where a team has won."""
        all_demons_dead = not any(
            isinstance(p.character, characters.Demon) and not p.is_dead
            for p in self.players
        )
        no_evil_twin = not any(
            (
                isinstance(p.character, characters.EvilTwin)
                and (not p.is_dead or p.vigormortised)
                and p.droison_count == 0
            )
            for p in self.players
        )
        # TODO: Mastermind day.
        # TODO: Evil win condition, will become relevant in Zombuul puzzles
        game_over = all_demons_dead and no_evil_twin
        return game_over

    def math_misregistration(
        self,
        player: PlayerID,
        result: info.STBool | None = None
    ) -> None:
        """
        Modify bounds on possible Mathematician pings this night.
        If misregistration is certain, no argument is needed. If it depends on
        an STBool being FALSE (e.g. a Ping from a character ability), that can
        be provided in `result`.
        """
        if result is info.STBool.TRUE or player in self._math_misregisterers:
            return
        self._math_misregistration_bounds[1] += 1
        self._math_misregisterers.add(player)
        if result is None or not result.is_maybe():
            self._math_misregistration_bounds[0] += 1

    def exclude_player_from_math_tonight(self, player: PlayerID):
        self._math_misregisterers.add(player)

    def __str__(self) -> str:
        ret = [f'World{self.debug_key if _DEBUG else ""}(']
        pad = max(len(player.name) for player in self.players) + 1
        for player in self.players:
            rhs = player._world_str(self)
            colour = 0
            if player.lies_about_self or info.behaves_evil(self, player.id):
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
    also_on_script: list[type[Character]] = field(default_factory=list)

    user_interrupt: Callable[[], bool] | None = None

    # --------- SOLVER OPTIONS --------- #
    # Deduplicate solutions if they share the same starting characters
    deduplicate_initial_characters: bool = True
    # Generally puzzles are posed towards the end of the day, before executions
    finish_final_day: bool = False
    # Enable for e.g. oops all seamstresses
    allow_duplicate_tokens_in_bag: bool = False
    # You cannot lie to yourself, so player 0 gets special treatment
    player_zero_is_you: bool = True
    # Some BMR-style puzzles set this False # TODO: NotImplementedYet?
    allow_killing_dead_players: bool = True
    # Cap the number of speculative good liars considered
    max_speculation: int = 2


    def __post_init__(self, hidden_characters: list[type[Character]]):
        """Finish building Puzzle representation from user inputs."""
        if self.category_counts is None:
            self.category_counts = characters.DEFAULT_CATEGORY_COUNTS[
                len(self.players)
            ]
        self.demons, self.minions, self.hidden_good = (
            [], [], []
        )
        for character in hidden_characters:
            collection = (
                self.demons if issubclass(character, characters.Demon) else
                self.minions if issubclass(character, characters.Minion) else
                self.hidden_good
            )
            collection.append(character)
        self._validate_inputs()

        self.max_day = max(
            max((max(p.day_info, default=0) for p in self.players)),
            max(self.day_events, default=0),
        )
        self.max_night = max(
            self.max_day,
            max((
                max((n for n, _ in p.night_info), default=0)
                for p in self.players
            )),
            max((
                max((n for n, _ in p.external_night_info), default=0)
                for p in self.players
            )),
            max(self.night_deaths, default=0),
        )
        self.max_day = max(self.max_day, self.max_night - 1)
        self.finish_final_day |= (self.max_day < self.max_night)

        for i, player in enumerate(self.players):
            player.id = i

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

        # Events can be entered in Player.day_info or in State.day_events,
        # b/c that feels nice. Move them all to one place before solving.
        for player in self.players:
            for day, maybe_event in list(player.day_info.items()):
                if isinstance(maybe_event, events.Event):
                    del player.day_info[day]
                    maybe_event.player = player.id
                    if day in self.day_events:
                        self.day_events[day].insert(0, maybe_event)
                    else:
                        self.day_events[day] = [maybe_event]
        self._night_info, self._day_info, _external_night_info = zip(*(
            player._extract_info() for player in self.players
        ))
        self.event_counts = defaultdict(int, {
            day: len(events) for day, events in self.day_events.items()
        })

        # External info retrieval
        self.external_info_registry = defaultdict(list)
        for pid, ext_info in enumerate(_external_night_info):
            for (night, character), items in ext_info.items():
                for item in items:
                    self.external_info_registry[(character, night)].append(
                        (item, pid)
                    )
        self.external_info_registry: dict[
            tuple[type[Character], int],
            tuple[info.ExternalInfo, PlayerID],
        ] = dict(self.external_info_registry)

        assert self.player_zero_is_you ^ (self.players[0].name != 'You'), (
            "Player 0 must be called 'You' iff puzzle.player_zero_is_you=True"
        )

        # Compute script and character orderings. Sort script for determinism.
        self.script = list(set(
            [p.claim for p in self.players]
            + hidden_characters
            + self.hidden_self
            + self.also_on_script
        ))
        self.script.sort(key=lambda character: character.__name__)

        self.setup_order = [
            character for character in characters.GLOBAL_SETUP_ORDER
            if character in self.script
        ]
        self.night_order = [
            character for character in characters.GLOBAL_NIGHT_ORDER
            if character in self.script
        ]
        self.day_order = [
            character for character in characters.GLOBAL_DAY_ORDER
            if character in self.script
        ]
        self.state_template = State(self, self.players)

        for character, _ in self.external_info_registry:
            assert character in self.script, (
                f"Consider adding {character.__name__} to Puzzle.also_on_script"
            )

        # Annoyingly, the pickle module doesn't store modified class attributes,
        # so when a puzzle is sent between processes, such classes (like the
        # Hermit) lose their state. Therefore, we get the Puzzle to record state
        # manually and reapply it when the puzzle is unserialised.
        self._extra_serialised_state = {
            'hermit_outsiders': characters.Hermit.outsiders
        }

    def unserialise_extra_state(self):
        if hermit_outsiders := self._extra_serialised_state['hermit_outsiders']:
            characters.Hermit.set_outsiders(*hermit_outsiders)
        del self._extra_serialised_state


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
            if not any(issubclass(character, reg) for reg in registered_characters):
                raise ValueError(
                    f'Character {character.__name__} has not been placed in the'
                    ' night order. Did you forget?'
                )
        for character in self.hidden_good:
            if not character.lies_about_self:
                raise ValueError(f"{character.__name__} can't be in hidden?")

        assert 1 not in self.night_deaths, "Can there be deaths on night 1?"

    def __str__(self) -> str:
        ret = ['Puzzle(\n  \033[0;4mPlayers\033[0m']
        names = [player.name for player in self.players]
        for player_id, player in enumerate(self.players):
            ret.append(f'    \033[33;1m{player.name} claims '
                       f'{player.claim.__name__}\033[0m')
            for (_, night), info_items in self.external_info_registry.items():
                for info_item, pid in info_items:
                    if pid == player_id:
                        info_str = info.pretty_print(info_item, names)
                        ret.append(f'      N{night}: {info_str}')
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
                self.demons + self.minions +
                self.hidden_good
            )),
            f'    You: [{", ".join(c.__name__ for c in self.hidden_self)}]',
        ])
        if self.also_on_script:
            ret.append(
                '    On script but not claimed: ['
                f'{", ".join(c.__name__ for c in self.also_on_script)}]'
            )
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

    def __repr__(self) -> str:
        return str(self)


def apply_all(
    states: StateGen,
    fn: Callable[[State], StateGen],
    **kwargs,
) -> StateGen:
    """Yields from a state-generating function on all states in a StateGen."""
    for state in states:
        yield from fn(state, **kwargs)


def record_fork_caller(debug_key: tuple[int, ...], offset: int):
    """
    Record which (character) method just forked a world during the solve, this
    can be aggregated into stats that are useful for profiling the combinatorial
    complexity introduced by each character's implementation.
    """
    caller_frame = inspect.currentframe().f_back
    for _ in range(offset):
        caller_frame = caller_frame.f_back
    _, _, fn_name, _, _ = inspect.getframeinfo(caller_frame)
    cls = caller_frame.f_locals.get('self')
    cls_prefix = f'{cls.__class__.__name__}.' if cls is not None else ''
    caller = f'{cls_prefix}{fn_name}'
    _PROFILING_FORK_LOCATIONS[(caller, debug_key)] += 1


def summarise_fork_profiling():
    """Aggregate stats about the combinatorial complexity of each character."""
    # Produces tables like the following:
    # ┌───────────────────────────────────────────────────┐
    # │                     Function │  Factor  │  Total  │
    # ├───────────────────────────────────────────────────┤
    # │     _place_hidden_characters │ 1032.00x │    1032 │
    # │           NoDashii.run_night │    8.00x │   68096 │
    # │             FangGu.run_night │    7.86x │  286672 │
    # │             Vortox.run_night │    7.66x │   51776 │
    # │              Witch.run_night │    7.18x │   72480 │
    # │        Vigormortis.run_night │    5.00x │    4480 │
    # │      _speculate_evil_players │    3.13x │    1660 │
    # │ SnakeCharmer._run_night_evil │    1.04x │    2486 │
    # │           NoDashii.run_setup │    1.00x │     703 │
    # └───────────────────────────────────────────────────┤
    #                                           │  489385 │
    #                                           └─────────┘
    if not _PROFILING:
        return
    groups = defaultdict(list)
    for (caller, _), count in _PROFILING_FORK_LOCATIONS.items():
        groups[caller].append(count)
    rows = [
        (caller, (total := sum(counts)), total / len(counts))
        for caller, counts in groups.items()
    ]
    rows.sort(reverse=True, key=lambda row: row[2])
    name_len = max((len(name) for name in groups), default=0)
    print('Profiling returned the following stats about forking worlds')
    title = f'│ {'Function': >{name_len}} │  Factor  │  Total  │'
    print(f'┌{'─' * (len(title)-2)}┐\n{title}\n├{'─' * (len(title)-2)}┤')
    for name, total, avg in rows:
        print(f'│ {name: >{name_len}} │ {avg:7.2f}x │ {total: >7} │ ')
    print(f'└{'─' * (len(title)-2)}┤')
    print(f'{' ' * (len(title)-11)}│ {sum(r[1] for r in rows): >7} │')
    print(f'{' ' * (len(title)-11)}└{'─' * 9}┘')


def _debug_keys_from_DEBUG() -> list[tuple[int, ...]]:
    if not isinstance(_DEBUG, str):
        return []
    s = _DEBUG.strip()
    if s[0] != '(' or s[-1] != ')':
        return []
    return [tuple(int(x.strip()) for x in s[1:-1].split(','))]

_DEBUG_WORLD_KEYS.extend(_debug_keys_from_DEBUG())