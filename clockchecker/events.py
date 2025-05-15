from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import State, StateGen
    from .info import PlayerID

from . import core
from . import characters
from . import info



class Event(ABC):
    """
    Any publically visible event used in describing the puzzle.
    E.g. Executions, Nominations, Juggles, Slayer Shots etc.
    Night deaths are not publically visible, so are not Events.
    ST consults are not public, so are instead character day_info.

    Events can be placed either in `State.day_events` or in `Player.day_info`.
    When the State is initialised, all events from each `Player.day_info` get
    moved into `State.day_events` *in arbitrary order*. So while defining the
    events in `Player.day_info` is nice for storing a player's actions within
    that player's definition, putting the actions directly into
    `State.day_events` is beter for specifying the exact order of events, when
    it matters. As such, Events that can be placed in `Player.day_info` should
    have a `player: PlayerID | None = None` attribute, which is automatically
    populated when the event is moved to `State.day_events`, and can be manually
    set if defining events there directly.
    """
    @abstractmethod
    def __call__(self, state: State) -> StateGen:
        pass

    def deaths(self, state: State) -> Iterable[PlayerID]:
        return ()


@dataclass
class Execution(Event):
    """
    A player is executed during the day by popular vote. They might not die.
    Executions not triggered by popular vote should use an appropriate subclass
    of Execution (e.g. executions triggered by Witches, Virgin).
    """
    player: PlayerID
    died: bool = True

    def __call__(self, state: State) -> StateGen:
        player = state.players[self.player].character
        yield from player.executed(state, self.player, self.died)


class Doomsayer:
    """
    If 4 or more players live, each living player may publically choose (once
    per game) that a player of their own alignment dies.
    """
    @dataclass
    class Call(Event):
        died: PlayerID
        player: PlayerID | None = None
        def __call__(self, state: State) -> StateGen:
            a = info.IsEvil(self.player)(state, self.player)
            b = info.IsEvil(self.died)(state, self.player)
            if a ^ b is not info.TRUE:
                yield from state.players[self.died].character.killed(
                    state, self.died
                )

@dataclass
class ExecutionByST(Execution):
    """
    A player is executed by the ST during the day. They might not die.
    The reason for execution is not certain (e.g. breaking madness or nominating
    the Virgin).
    Inheriting from Execution lets things like Vortox easily check Executions.
    """
    # E.g. like nominating virgin
    nominating: PlayerID | None = None
    def __call__(self, state: State) -> StateGen:
        raise NotImplementedError()

@dataclass
class UneventfulNomination(Event):
    """
    A player is nominated, and nothing extraordinary happens. 
    I.e., no execution triggered by the Virgin, no death to a Witch curse etc.
    A nomination that does trigger some ability should instead be represented by
    an ExecutionByST or Dies event as appropriate.
    """
    nominator: PlayerID
    player: PlayerID | None = None
    def __call__(self, state: State) -> StateGen:
        if info.has_ability_of(state, self.player, characters.Virgin):
            yield from self._virgin_check(state)
        else:
            yield state

    def _virgin_check(self, state: State) -> StateGen:
        virgin = state.players[self.player]
        if not isinstance(virgin.character, characters.Virgin):
            raise NotImplementedError('Recording a Philo Virgin is spent.')
        townsfolk_nominator = info.IsCategory(
            self.nominator, characters.TOWNSFOLK
        )(state, self.player)
        if (
            virgin.is_dead
            or virgin.character.spent
            or townsfolk_nominator is not info.TRUE
        ):
            virgin.character.spent = True
            yield state
        elif virgin.droison_count:
            state.math_misregistration()
            virgin.character.spent = True
            yield state

@dataclass
class Dies(Event):
    """
    A player dies during the day without execution, e.g. Witch-cursed or Tinker.
    """
    after_nominating: bool
    player: PlayerID | None = None
    def __call__(self, state: State) -> StateGen:
        dead_player = state.players[self.player]
        if self.after_nominating:
            if (witch := getattr(dead_player, 'witch_cursed', None)) is not None:
                dead_player.character.death_explanation = f"cursed by {witch}"
                yield from dead_player.character.killed(state, self.player)
            return

class NightEvent:
    """
    Doesn't extend the Event interface, because deaths are not publically 
    visible events. We only learn who is dead or alive come dawn.
    """
    pass

@dataclass
class NightDeath(NightEvent):
    player: PlayerID

@dataclass
class NightResurrection(NightEvent):
    player: PlayerID
