from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Sequence
from dataclasses import dataclass
import enum
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .characters import Character
    from .core import State

from . import characters


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
    pass
    def __call__(self, *args, **kwargs):
        raise ValueError(
            f"Looks like you're trying to treat a {type(self)} as Info, when "
            'it has in fact been explicitly marked as NotInfo :)'
        )

# ------------------- Info Objects -------------------- #

@dataclass
class IsEvil(Info):
    player: PlayerID
    def __call__(self, state: State, src: PlayerID = None):
        player = state.players[self.player]
        if not player.droison_count:  # Misregistrations are part of ability
            if isinstance(player.character, characters.Recluse):
                return TRUE if player.is_evil else MAYBE
            if isinstance(player.character, characters.Spy):
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
        character = player.character
        if type(character) is characters.Zombuul and character.registering_dead:
            return FALSE
        return STBool(not player.is_dead)

@dataclass
class IsCharacter(Info):
    player: int
    character: type[Character]
    def __call__(self, state: State, src: PlayerID) -> STBool:
        player = state.players[self.player]
        actual_character = type(player.character)
        if (
            self.character.category in actual_character.misregister_categories
            and not player.droison_count  # Misregistrations are part of ability
        ):
            return MAYBE
        return STBool(actual_character is self.character)

@dataclass
class IsCategory(Info): 
    player: PlayerID
    category: characters.Categories
    def __call__(self, state: State, src: PlayerID) -> STBool:
        player = state.players[self.player]
        character = type(player.character)
        if (
            self.category in character.misregister_categories
            and not player.droison_count  # Misregistrations are part of ability
        ):
            return MAYBE
        return STBool(character.category is self.category)

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
    args: Sequence[Info | STBool]
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
class SameCategory(Info): 
    a: type[Character]
    b: type[Character]
    def __call__(self, state: State, src: PlayerID) -> STBool:
        # TODO: This is not correct. Doesn't account for poisoning of 
        # misregistration, and doesn't account for both a & b misregistering as
        # the same category.
        if self.a.category in self.b.misregister_categories:
            return MAYBE
        if self.b.category in self.a.misregister_categories:
            return MAYBE
        return STBool(self.a.category is self.b.category)

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


def behaves_evil(state: State, player_id: PlayerID) -> bool:
    """
    Characters have the is_liar ClassVar which determines if they lie about
    their own role and info. However, some good characters also lie about other
    character's info. E.g. the lunatic is good but may lie about receiving a 
    Nightwatchman ping, whilst the drunk lies about their character and info but
    would truthfully report a Nightwatchman ping.
    """
    player = state.players[player_id]
    character = type(player.character)
    if character in (
        characters.Lunatic,
        # characters.Politician, (TODO)
    ):
        return True
    if character is characters.Marionette:
        return False
    return player.is_evil


def has_ability_of(
    state: State,
    player_id: PlayerID,
    character: type[Character]
) -> bool:
    """For checking if it is legal for a player to use a character's ability."""
    # TODO: Philospoher and Boffin'd Demon logic go here.
    return isinstance(state.players[player_id].character, character)


def acts_like(
    state: State,
    player_id: PlayerID,
    character: type[Character]
) -> bool:
    """
    Like `has_ability_of` but also includes characters that think they have
    another character's ability.
    """
    if has_ability_of(state, player_id, character):
        return True
    player = state.players[player_id]
    if type(player.character) in (
        characters.Drunk,
        characters.Marionette,
    ):
        return isinstance(player.claim, character)
    # TODO: Lunatic currently doesn't decide what demon they think they are.
    return False
