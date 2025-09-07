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


@dataclass
class ExecutionByST(Execution):
    """
    A player is executed by the ST during the day. They might not die.
    The reason for execution is not certain (e.g. breaking madness or nominating
    the Virgin).
    Inheriting from Execution lets things like Vortox easily check Executions.
    """
    # E.g. like nominating virgin
    after_nominating: PlayerID | None = None
    def __call__(self, state: State) -> StateGen:
        if self.after_nominating is not None:
            nominee = state.players[self.after_nominating]
            if (virgin := nominee.get_ability(characters.Virgin)) is not None:
                yield from virgin.execution_on_nomination(state, self)
        else:
            raise NotImplementedError("TODO: Madness breaks etc.")


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
        nominator = state.players[self.nominator]
        nominee = state.players[self.player]
        if (princess := nominator.get_ability(characters.Princess)) is not None:
            princess.nominates(state, self.nominator, self.player)
        states = [state]
        if (virgin := nominee.get_ability(characters.Virgin)) is not None:
            states = virgin.uneventful_nomination(state, self)
        if (golem := nominator.get_ability(characters.Golem)) is not None:
            raise NotImplementedError("Need to put a generator stack here")
            # yield from golem.nominates(state, self)
        if getattr(state, "rioting_count", 0):
            raise NotImplementedError("Riot nomination doesn't kill, gen stack")
            # yielf from characters.Riot.day_three_nomination(state, self)
        yield from states

@dataclass
class Dies(Event):
    """
    A player dies during the day without execution, e.g. Witch-cursed or Tinker.
    """
    after_nominating: bool = False
    after_nominated_by: PlayerID | None = None
    player: PlayerID | None = None
    def __call__(self, state: State) -> StateGen:
        dying = state.players[self.player]
        if self.after_nominating:
            if (witch := getattr(dying, 'witch_cursed', None)) is not None:
                dying.character.death_explanation = f"cursed by {witch}"
                yield from dying.character.killed(state, self.player)
        elif self.after_nominated_by is not None:
            nominator = state.players[self.after_nominated_by]
            if getattr(state, "rioting_count", 0):
                yield from characters.Riot.day_three_nomination(state, self)
            elif (golem := nominator.get_ability(characters.Golem)) is not None:
                yield from golem.nominates(state, self)

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
