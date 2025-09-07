from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Generator, Mapping, Sequence
from dataclasses import dataclass, fields
import enum
import itertools
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .characters import Character
    from .core import State
    from .events import Event

from . import characters
from . import events


PlayerID = int


class STBool(enum.Enum):
    """
    A Storytellers boolean can be TRUE, FALSE, or an arbitrary ST choice
    called MAYBE. MAYBEs are propogated through Information statements. E.g., 
    querying if the Recluse is a demon will return MAYBE.
    """
    FALSE = 0
    TRUE = 1
    MAYBE = float('inf')

    def __or__(self, other: STBool):
        if self is TRUE or other is TRUE:
            return TRUE
        if self is MAYBE or other is MAYBE:
            return MAYBE
        return FALSE

    def __and__(self, other: STBool):
        if self is FALSE or other is FALSE:
            return FALSE
        if self is MAYBE or other is MAYBE:
            return MAYBE
        return TRUE

    def __eq__(self, other: STBool):
        if self is MAYBE or other is MAYBE:
            return MAYBE
        return STBool(self is other)

    def __xor__(self, other: STBool):
        if self is MAYBE or other is MAYBE:
            return MAYBE
        return STBool(self is not other)

    def __invert__(self):
        if self is MAYBE:
            return MAYBE
        return STBool(1 - self.value)

    def __bool__(self):
        raise ValueError(
            "Implicitly converting a STBool to a bool is most likely to happen "
            "when erroneously using logical operators 'and', 'or' or 'not', "
            "instead of &, | or ~. Therefore this is disallowed."
        )

TRUE = STBool.TRUE
FALSE = STBool.FALSE
MAYBE = STBool.MAYBE


class Info(ABC):
    """
    An instance of Info (specialised by inheritence) stores a logical 
    statement, and provides a '__call__' method to see if that statement could
    hold in a given game state, from a given player's perspective (src).
    Statements that could return different values on a ST whim (e.g. Recluse 
    pinging FortuneTeller) will evaluate to MAYBE, allowing compound statements
    to reason over variability in sub-statements.
    """
    @abstractmethod
    def __call__(self, state: State, src: PlayerID) -> STBool:
        pass

    def __or__(self, other: Info):
        return InfoOp(self, other, 'or')
    def __and__(self, other: Info):
        return InfoOp(self, other, 'and')
    def __xor__(self, other: Info):
        return InfoOp(self, other, 'xor')
    def __eq__(self, other: Info):
        return InfoOp(self, other, 'eq')
    def __invert__(self):
        return InfoOp(self, None, 'invert')
    def __bool__(self):
        raise ValueError(
            "Implicitly converting an Info to a bool is most likely to happen "
            "when erroneously using logical operators 'and', 'or' or 'not', "
            "instead of &, | or ~. Therefore this is disallowed."
        )

@dataclass
class InfoOp(Info):
    a: Info
    b: Info | None
    op: str

    def __call__(self, state: State, src: PlayerID) -> STBool:
        return getattr(self, f'_eval_{self.op}')(state, src)

    def __repr__(self):
        return f'InfoOp(a={self.a}, b={self.b}, op={self.__call__.__name__})'

    def _eval_or(self, state: State, src: PlayerID):
        return self.a(state, src) | self.b(state, src)

    def _eval_and(self, state: State, src: PlayerID):
        return self.a(state, src) & self.b(state, src)

    def _eval_xor(self, state: State, src: PlayerID):
        return self.a(state, src) ^ self.b(state, src)

    def _eval_eq(self, state: State, src: PlayerID):
        return self.a(state, src) == self.b(state, src)

    def _eval_invert(self, state: State, src: PlayerID):
        return ~self.a(state, src)

    def __bool__(self):
        raise ValueError(
            "Implicitly converting an instance of Info to a bool is most"
            " likely to happen when erroneously using logical operators like "
            "'and', 'or' or 'not' instead of &, | or ~. Therefore this is "
            "disallowed."
        )

class NotInfo:
    def __call__(self, *args, **kwargs):
        raise ValueError(
            f"Looks like you're trying to treat a {type(self)} as Info, when "
            'it has in fact been explicitly marked as NotInfo :)'
        )

class ExternalInfo(ABC):
    """
    Info claimed by a player to have been cause by another player's ability 
    (e.g. NightWatchman ping, EvilTwin seen).
    """
    @abstractmethod
    def __call__(self, state: State, src: PlayerID) -> bool:
        pass

# ------------------- Info Objects -------------------- #

@dataclass
class IsEvil(Info):
    player: PlayerID
    def __call__(self, state: State, src: PlayerID = None):
        player = state.players[self.player]
        if (
            ((recluse := player.get_ability(characters.Recluse)) is not None)
            and not recluse.is_droisoned(state, player.id)
        ):
            return TRUE if player.is_evil else MAYBE

        if (
            ((spy := player.get_ability(characters.Spy)) is not None)
            and not spy.is_droisoned(state, player.id)
        ):
            return MAYBE if player.is_evil else FALSE

        return STBool(player.is_evil)

@dataclass
class IsDroisoned(Info):
    player: PlayerID
    by: int = None
    def __call__(self, state: State, src: PlayerID) -> STBool:
        return STBool(state.players[self.player].is_droisoned)

@dataclass
class IsAlive(Info):
    player: PlayerID
    def __call__(self, state: State, src: PlayerID) -> STBool:
        player = state.players[self.player]
        if (
            (z := player.get_ability(characters.Zombuul)) is not None
            and z.registering_dead
        ):
            return FALSE
        return STBool(not player.is_dead)

@dataclass
class IsCharacter(Info):
    player: PlayerID
    character: type[Character]
    def __call__(self, state: State, src: PlayerID) -> STBool:
        player = state.players[self.player]
        if self.character.category in player.get_misreg_categories(state):
            return MAYBE
        return STBool(type(player.character) is self.character)

@dataclass
class IsCategory(Info): 
    player: PlayerID
    category: characters.Categories
    def __call__(self, state: State, src: PlayerID) -> STBool:
        player = state.players[self.player]
        if self.category in player.get_misreg_categories(state):
            return MAYBE
        return STBool(player.character.category is self.category)

@dataclass
class CharAttrEq(Info):
    player: PlayerID
    attr: str
    value: Any
    def __call__(self, state: State, src: PlayerID) -> STBool:
        missing = []  # A unique object for pointer comparison using `is` 
        val = getattr(state.players[self.player].character, self.attr, missing)
        return STBool(val is not missing and val == self.value)

@dataclass
class ExactlyN(Info):
    N: int
    args: Sequence[Info] | Sequence[STBool]
    def __call__(self, state: State, src: PlayerID) -> STBool:
        if isinstance(self.args[0], Info):
            # Args not yet evaluated against the state
            results = [arg(state, src) for arg in self.args]
        else:
            results = self.args
        true_count = sum(r is TRUE for r in results)
        maybe_count = sum(r is MAYBE for r in results)
        if maybe_count == 0:
            return STBool(true_count == self.N)
        if true_count <= self.N <= true_count + maybe_count:
            return MAYBE
        return FALSE

@dataclass
class IsInPlay(Info):
    character: type[Character]
    def __call__(self, state: State, src: PlayerID) -> STBool:
        result = FALSE
        test = IsCharacter(player=0, character=self.character)
        for player in range(len(state.players)):
            test.player = player
            result |= test(state, src)
            if result is TRUE:
                return TRUE  # Early exit on TRUE not MAYBE
        return result


@dataclass
class CustomInfo(Info):
    method: Callable[[State], STBool]
    def __call__(self, state: State, src: PlayerID) -> STBool:
        return self.method(state)



# ------------------- Some helper utilities -------------------- #

def get_next_player_who_is(
    state: State, 
    condition: Callable[[State, PlayerID], bool],
    you: PlayerID = 0,
    clockwise: bool = True,
) -> PlayerID | None:
    """
    Scans town for a player matching the condition, checking 'you' last.
    This functions deals in bools not STBools, otherwise it is not well posed.
    """
    step = 1 if clockwise else -1
    n_players = len(state.players)
    for i in range(1, n_players + 1):
        player = (you + step * i) % n_players
        if condition(state, player):
            return player
    return None

def circle_distance(a: PlayerID, b: PlayerID, n_players: int) -> int:
    """If a sits next to b, they have distance 1."""
    if b < a:
        return min(a - b, n_players + b - a)
    return min(b - a, n_players + a - b)

def all_registration_combinations(
    registrations: Sequence[STBool]
) -> Generator[list[int]]:
    """
    Given a list of registrations, return every possible combination of indices
    into that list such that the index of a TRUE is always included and the
    index of a MAYBE may be included.
    """
    trues = [i for i, reg in enumerate(registrations) if reg is TRUE]
    maybes = [i for i, reg in enumerate(registrations) if reg is MAYBE]
    for maybe_combination in itertools.chain.from_iterable(
        itertools.combinations(maybes, r)
        for r in range(len(maybes)+1)
    ):
        yield trues + list(maybe_combination)

def tf_candidates_in_direction(
    state: State,
    src: PlayerID,
    direction: int,
) -> list[PlayerID]:
    """
    Find all players that could register as the closest Townsfolk in a given
    direction from a src player. Used by e.g. NoDashii and Vigormortis.
    Direction 1 = clockwise, -1 = anticlockwise.
    """
    N = len(state.players)
    candidates = []
    for step in range(1, N):
        player = (src + direction * step) % N
        is_tf = IsCategory(player, characters.TOWNSFOLK)(state, src)
        if is_tf is not FALSE:
            candidates.append(player)
        if is_tf is TRUE:
            break
    return candidates

def behaves_evil(state: State, player_id: PlayerID) -> bool:
    """
    Characters have the is_liar ClassVar which determines if they lie about
    their own role and info. However, some good characters also lie about other
    character's info. E.g. the lunatic is good but may lie about receiving a 
    Nightwatchman ping, whilst the drunk lies about their character and info but
    would truthfully report a Nightwatchman ping.
    This puzzle state is defined from the perspective of Player 0, so Player 0
    never lies to themselves.
    """
    if player_id == 0 and state.puzzle.player_zero_is_you:
        return False
    player = state.players[player_id]
    character = type(player.character)
    if character in (
        characters.Lunatic,
        # characters.Politician, (TODO)
    ):
        return True
    return player.is_evil

def pretty_print(info: Info | Event, names: Mapping[PlayerID, str]) -> str:
    """For printing human-readable str representations of Info."""

    if isinstance(info, InfoOp):
        if info.b is None:
            return f'~{pretty_print(info.a, names)}'
        op_symbols = {'and': '&', 'or': '|', 'xor': '^', 'eq': '=='}
        return '{} {} {}'.format(
            pretty_print(info.a, names),
            op_symbols[info.op],
            pretty_print(info.b, names)
        )
    
    elif isinstance(info, characters.Savant.Ping):
        return ('Savant.Ping:\n'
                f'            {pretty_print(info.a, names)}\n'
                f'            {pretty_print(info.b, names)}')

    elif isinstance(info, characters.Juggler.Juggle):
        items = [
            f'{names[pid]:}: {character.__name__}'
            for pid, character in info.juggle.items()
        ]
        if len(items) > 3:
            return (f'Juggler.Juggle({names[info.player]}, {{\n' + 
                    ',\n'.join(f'      {item}' for item in items)
                    + '\n    })')
        return f'Juggler.Juggle({names[info.player]}, {{{", ".join(items)}}})'
    elif isinstance(info, events.NightDeath):
        return names[info.player]

    ret = []
    for field in fields(info):
        value = getattr(info, field.name)

        type_, *or_none = field.type.split(' | ')
        if or_none and or_none != ['None']:
            type_ = field.type

        if value is None:
            ret.append(f'{field.name}={str(value)}')
        elif type_ == 'PlayerID':
            ret.append(names[value])
        elif type_ in 'info.Info':
            ret.append(pretty_print(value, names))
        elif type_ == 'type[Character]':
            ret.append(value.__name__)
        elif type_ == 'characters.Categories':
            ret.append(value.name)
        elif type_ == 'int':
            ret.append(str(value))
        elif type_.startswith('Sequence'):
            ret.append(f'[{", ".join([pretty_print(x, names) for x in value])}]')
        else:
            ret.append(f'{field.name}={str(value)}')

    return f'{type(info).__qualname__}({", ".join(ret)})'


def info_creator(info: Info) -> type[Character]:
    return getattr(characters, type(info).__qualname__.split('.')[0])


# ------------------ Custom Info For Specific Puzzles -------------------- #


# Required for a Savant statement in Puzzle #1
@dataclass
class DrunkBetweenTownsfolk(Info):
    def __call__(self, state: State, src: PlayerID) -> STBool:
        N = len(state.players)
        result = FALSE
        for player in range(N):
            found_drunk = IsCharacter(player, characters.Drunk)(state, src)
            if found_drunk is FALSE:  # Allow MAYBE
                continue
            tf_neighbours = (
                IsCategory((player - 1) % N, characters.TOWNSFOLK)(state, src) &
                IsCategory((player + 1) % N, characters.TOWNSFOLK)(state, src)
            )
            result |= found_drunk & tf_neighbours
        return result


# Required for a Savant statement in Puzzle #15
@dataclass
class LongestRowOfTownsfolk(Info):
    length: int | None = None
    minimum: int = -999
    maximum: int = 999
    def __call__(self, state: State, src: PlayerID) -> STBool:
        townsfolk = [
            IsCategory(player, characters.TOWNSFOLK)(state, src)
            for player in range(len(state.players))
        ]
        assert not any(x is MAYBE for x in townsfolk), (
            "Puzzle 15 has no misregistration, so ommit that logic for now."
        )
        longest, prev_not_tf = 0, -1
        for player, is_tf in enumerate(townsfolk * 2):  # Wrap circle
            if is_tf is FALSE:
                longest = max(longest, player - prev_not_tf - 1)
                prev_not_tf = player
        longest = min(longest, len(state.players))
        if self.length is not None:
            return STBool(longest == self.length)
        else:
            return STBool(self.minimum <= longest <= self.maximum)


# Required for a Artist statement in Puzzle #42
@dataclass
class WidowPoisoned(Info):
    player: PlayerID
    def __call__(self, state: State, src: PlayerID) -> STBool:
        target = state.players[self.player]
        if not target.droison_count:
            return FALSE  # Early Exit
        return STBool(any(
            (
                not player.is_dead
                and not player.droison_count
                and (widow := player.get_ability(characters.Widow)) is not None
                and widow.target == target.id
            )
            for player in state.players
        ))
