from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter
from collections.abc import Callable, Generator, Mapping, Sequence
from dataclasses import dataclass, fields
import enum
import itertools
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .characters import Category, Character
    from .core import State
    from .events import Event

from . import characters
from . import events


PlayerID = int


class STBool(enum.Enum):
    """
    Info statements, when evaluated, all return Storyteller Bools (STBools)
    which are like bools except when composed they propogate information such as
    whether the result is arbitrary base on a ST whim (is_maybe) and whether the
    value the ST must report differs from the real truth.
    """
    # Format: (truth, is_maybe, st_says), where
    #  - `truth` is the true value of the statement
    #  - `is_maybe` indicates the ST is free to give an arbitrary response
    #  - `st_says` is usually the same as `truth`, apart from in cases where
    #     the ST MUST LIE, e.g. checking if zombuul is dead or legion is minion

    FALSE = (False, False, False)
    FALSE_MAYBE = (False, True, False)
    FALSE_LYING = (True, False, False)
    TRUE = (True, False, True)
    TRUE_MAYBE = (True, True, True)
    TRUE_LYING = (False, False, True)

    @classmethod
    def _missing_(cls, value) -> STBool:
        assert isinstance(value, bool), f"{value} is not bool"
        return STBool((value, False, value))

    def truth(self) -> bool:
        return self.value[0]

    def is_maybe(self) -> bool:
        return self.value[1]

    def st_says(self) -> bool:
        return self.value[2]

    def is_true(self) -> bool:
        return self is STBool.TRUE or self is STBool.TRUE_LYING

    def not_true(self) -> bool:
        return not (self is STBool.TRUE or self is STBool.TRUE_LYING)

    def is_false(self) -> bool:
        return self is STBool.FALSE or self is STBool.FALSE_LYING

    def not_false(self) -> bool:
        return not (self is STBool.FALSE or self is STBool.FALSE_LYING)

    def st_lying(self) -> bool:
        truth, _, st_says = self.value
        return truth != st_says

    def __or__(self, other: STBool):
        (st, sm, ss), (ot, om, os) = self.value, other.value
        if self.is_true() or other.is_true():
            return STBool((st | ot, False, ss | os))
        return STBool((st | ot, sm | om, ss | os))

    def __and__(self, other: STBool):
        (st, sm, ss), (ot, om, os) = self.value, other.value
        if self.is_false() or other.is_false():
            return STBool((st & ot, False, ss & os))
        return STBool((st & ot, sm | om, ss & os))

    def __eq__(self, other: STBool):
        (st, sm, ss), (ot, om, os) = self.value, other.value
        return STBool((st == ot, sm | om, ss == os))

    def __xor__(self, other: STBool):
        (st, sm, ss), (ot, om, os) = self.value, other.value
        return STBool((st ^ ot, sm | om, ss ^ os))

    def __invert__(self):
        (st, sm, ss) = self.value
        return STBool(bool(1-st), sm, bool(1-ss))

    def __bool__(self):
        raise ValueError(
            "Implicitly converting a STBool to a bool is most likely to happen "
            "when erroneously using logical operators 'and', 'or' or 'not', "
            "instead of &, | or ~. Therefore this is disallowed."
        )


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
        raise NotImplementedError("Override this method when inheriting.")

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
            return STBool.TRUE if player.is_evil else STBool.FALSE_MAYBE

        if (
            ((spy := player.get_ability(characters.Spy)) is not None)
            and not spy.is_droisoned(state, player.id)
        ):
            return STBool.TRUE_MAYBE if player.is_evil else STBool.FALSE

        return STBool(player.is_evil)

@dataclass
class IsDroisoned(Info):
    player: PlayerID
    # by: int = None  # Unimplemented
    def __call__(self, state: State, src: PlayerID) -> STBool:
        return STBool(state.players[self.player].droison_count > 0)

@dataclass
class IsAlive(Info):
    player: PlayerID
    def __call__(self, state: State, src: PlayerID) -> STBool:
        player = state.players[self.player]
        if player.is_dead:  # Short-circuit the most common case
            return STBool.FALSE
        zombuul = player.get_ability(characters.Zombuul)
        if zombuul is not None and zombuul.registering_dead:
            return STBool.FALSE_LYING
        return STBool.TRUE

@dataclass
class IsCharacter(Info):
    player: PlayerID
    character: type[Character]
    def __call__(self, state: State, src: PlayerID) -> STBool:
        player = state.players[self.player]
        misreg_categories = player.get_misreg_categories(state)
        truth = isinstance(player.character, self.character)
        is_maybe = (
            issubclass(self.character, misreg_categories)
            or (truth and bool(misreg_categories))
        )
        # TODO: Legion logic will go here too.
        return STBool((truth, is_maybe, truth))

@dataclass
class IsCategory(Info):
    player: PlayerID
    category: Category
    def __call__(self, state: State, src: PlayerID) -> STBool:
        player = state.players[self.player]
        misreg_categories = player.get_misreg_categories(state)
        truth = isinstance(player.character, self.category)
        is_maybe = (
            self.category in misreg_categories
            or (truth and bool(misreg_categories))
        )
        # TODO: Legion logic will go here too.
        return STBool((truth, is_maybe, truth))

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
        truth = (self.N == sum(r.truth() for r in results))
        st_says = (self.N == sum(r.st_says() for r in results))
        num_looks_true = sum(r.is_true() for r in results)
        num_maybes = sum(r.is_maybe() for r in results)
        is_maybe = (
            num_looks_true <= self.N <= num_looks_true + num_maybes
            if num_maybes else False
        )
        return STBool((truth, is_maybe, st_says))


@dataclass
class IsInPlay(Info):
    character: type[Character]
    def __call__(self, state: State, src: PlayerID) -> STBool:
        result = STBool.FALSE
        query = IsCharacter(player=0, character=self.character)
        for player in range(len(state.players)):
            query.player = player
            result |= query(state, src)
            if result is STBool.TRUE:
                return STBool.TRUE  # Early exit on TRUE
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
    trues = [i for i, reg in enumerate(registrations) if reg.is_true()]
    maybes = [i for i, reg in enumerate(registrations) if reg.is_maybe()]
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
        is_tf = IsCategory(player, characters.Townsfolk)(state, src)
        if is_tf.not_false():
            candidates.append(player)
        if is_tf.is_true():
            break
    return candidates

def behaves_evil(state: State, player_id: PlayerID) -> bool:
    """
    Characters have the lies_about_self ClassVar which determines if they lie
    about their own role and info. However, some good characters also lie about
    other character's info. E.g. the lunatic is good but may lie about receiving
    a Nightwatchman ping, whilst the drunk lies about their character and info
    but would truthfully report a Nightwatchman ping.
    """
    if player_id == 0 and state.puzzle.player_zero_is_you:
        return False  # You can't lie to yourself, Josef
    player = state.players[player_id]
    if hasattr(player, 'speculative_good'):
        return False
    if player.is_evil or hasattr(player, 'speculative_evil'):
        return True
    return type(player.character) in (
        characters.Lunatic,
        characters.Politician,
    )

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
        elif type_ == 'info.Info':
            ret.append(pretty_print(value, names))
        elif type_ in ('type[Character]', 'Category'):
            ret.append(value.__name__)
        elif type_ == 'int':
            ret.append(str(value))
        elif type_.startswith('Sequence'):
            ret.append(f'[{", ".join([pretty_print(x, names) for x in value])}]')
        else:
            ret.append(f'{field.name}={str(value)}')

    return f'{type(info).__qualname__}({", ".join(ret)})'


def info_creator(info: Info) -> type[Character]:
    return getattr(characters, type(info).__qualname__.split('.')[0])


def retracted(info: Info) -> Info:
    """
    A `retracted(Empath.Ping(0))` is one claimed at the time but retracted by
    the final game state displayed in the Puzzle.
    """
    info.is_retracted = True
    return info


# ------------------ Custom Info For Specific Puzzles -------------------- #


# Required for a Savant statement in Puzzle #1
@dataclass
class DrunkBetweenTownsfolk(Info):
    def __call__(self, state: State, src: PlayerID) -> STBool:
        N = len(state.players)
        result = STBool.FALSE
        for player in range(N):
            found_drunk = IsCharacter(player, characters.Drunk)(state, src)
            if found_drunk.is_false():  # Allow MAYBE
                continue
            tf_neighbours = (
                IsCategory((player - 1) % N, characters.Townsfolk)(state, src) &
                IsCategory((player + 1) % N, characters.Townsfolk)(state, src)
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
            IsCategory(player, characters.Townsfolk)(state, src)
            for player in range(len(state.players))
        ]
        assert not any(x.is_maybe() for x in townsfolk), (
            "Puzzle 15 has no misregistration, so ommit that logic for now."
        )
        longest, prev_not_tf = 0, -1
        for player, is_tf in enumerate(townsfolk * 2):  # Wrap circle
            if is_tf.is_false():
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
            return STBool.FALSE  # Early Exit
        return STBool(any(
            (
                not player.is_dead
                and not player.droison_count
                and (widow := player.get_ability(characters.Widow)) is not None
                and widow.target == target.id
            )
            for player in state.players
        ))
