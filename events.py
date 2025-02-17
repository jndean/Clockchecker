from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from core import State, StateGen, Player
	from info import PlayerID, Info

import core
import characters
import info



class Event(ABC):
	"""
	Any publically visible event used in describing the puzzle.
	E.g. Executions, Nominations, Juggles, Slayer Shots etc.
	Night deaths are not publically visible, so are not Events.
	ST consults are not public, so are instead character day_info
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



class Death:
	"""
	Doesn't extend the Event interface, because not all deaths are publically 
	visible event.
	"""
	pass

@dataclass
class NightDeath(Death):
	player: PlayerID

@dataclass
class NightResurrection(Death):
	player: PlayerID


# @dataclass
# class ExecutionByST(Execution):
# 	"""
# 	A player is executed by the ST during the day. They might not die.
# 	The reason for execution is not certain (e.g. broken madness, witch curse,
#   nominated virgin).
# 	"""
# 	when_nominating: bool = False	
# 	def __call__(self, state: State) -> StateGen:
# 		raise NotImplementedError()