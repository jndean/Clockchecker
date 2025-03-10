from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core import State, StateGen, Player
    from .info import PlayerID, Info

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


@dataclass
class ExecutionByST(Execution):
    """
    A player is executed by the ST during the day. They might not die.
    The reason for execution is not certain (e.g. breaing madness or nominating
    the virgin).
    Inheriting from Execution lets things like Vortox easily check Executions.
    """
    # E.g. like nominating virgin
    nominating: PlayerID | None = None
    def __call__(self, state: State) -> StateGen:
        raise NotImplementedError()


