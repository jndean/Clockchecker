from __future__ import annotations

from collections import namedtuple
from dataclasses import dataclass, field
import enum
from typing import ClassVar, TYPE_CHECKING

if TYPE_CHECKING:
	from core import State, StateGen, Player
	from info import PlayerID, Info

import info
import events


class Categories(enum.Enum):
	Townsfolk = enum.auto()
	Outsider = enum.auto()
	Minion = enum.auto()
	Demon = enum.auto()
	Traveller = enum.auto()

TOWNSFOLK = Categories.Townsfolk
OUTSIDER = Categories.Outsider
MINION = Categories.Minion
DEMON = Categories.Demon

type CategoryBounds = tuple[
	tuple[int, int],  # Townsfolk count min / max
	tuple[int, int],  # Outsiders count min / max
	tuple[int, int],  # Minions count min / max
	tuple[int, int],  # Demons count min / max
]


@dataclass
class Character:

	# Characters like Recluse and Spy override here
	misregister_categories: ClassVar[tuple[Categories, ...]] = ()
	
	night_info: dict[int, Info] = field(default_factory=dict)
	day_info: dict[int, Info] = field(default_factory=dict)

	effects_active: bool = False

	@staticmethod
	def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
		"""
		Modify bounds of acceptable character counts. E.g. the Baron should 
		override this method to increase the Outsider Min & Max and decrease
		the Townsfolk Min & Max. Meanwhile the Balloonist should increment only 
		the Outsider Max and decrement only the Townsfolk Min.
		"""
		return bounds

	def run_setup(self, state: State, player: PlayerID) -> StateGen:
		"""
		Create plausible worlds from the character's setup. E.g. the 
		Fortune Teller creates one world per choice of red herring. The 
		Marionette should just return (yield no candidate worlds) if it is not 
		sat next to the demon.
		"""
		raise NotImplementedError()

	def run_night(self, state: State, night: int, src: PlayerID) -> StateGen:
			if self.default_info_check(state, self.night_info, night, src):
				yield state

	def run_day(self, state: State, day: int, src: PlayerID) -> StateGen:
			if self.default_info_check(state, self.day_info, day, src):
				yield state

	def end_day(self, state: State, day: int, src: PlayerID) -> None:
			pass

	def default_info_check(
		self: Character, 
		state: State,
		all_info: dict[int, Info],
		info_index: int, 
		src: PlayerID,
		even_if_dead: bool = False,
	) -> bool:
		"""
		Most info roles can reuse this pattern to run all their functions
		"""
		player = state.players[src]
		if info_index not in all_info or player.is_evil or self.is_liar:
			return True
		if player.is_dead and not even_if_dead:
			return False
		if player.droison_count and not state.vortox:
			return True
		result = all_info[info_index](state, src)
		if state.vortox and (self.category is TOWNSFOLK):
			return result is not info.TRUE
		return result is not info.FALSE

	def maybe_activate_effects(self, state: State, me: PlayerID) -> None:
		"""
		Effects that this character is having on other players. Needs to be 
		triggerable under in one method so that e.g. a poisoner dying at night 
		can reactivate that poisoner's current victim.
		If a character doesn't want thsi wrapper logic, it can override this 
		method rather than the _impl method.
		"""
		if (
			not self.effects_active
			and state.players[me].droison_count == 0
			and not state.players[me].is_dead
		):
			self.effects_active = True
			self._activate_effects_impl(state, me)

	def maybe_deactivate_effects(self, state: State, me: PlayerID) -> None:
		"""
		Will be called on any character at the moment they are poisoned, killed,
		or changed into another character.
		"""
		if self.effects_active:
			self.effects_active = False
			self._deactivate_effects_impl(state, me)

	def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
		pass
	def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
		pass

	def apply_death(self, state: State, me: PlayerID) -> StateGen:
		state.players[me].is_dead = True
		self.maybe_deactivate_effects(state, me)
		yield from state.death_in_town(me)

	def maybe_killed_at_night(
		self,
	 	state: State,
	 	me: PlayerID,
	 	src: PlayerID,
	 ) -> StateGen:
		"""Soldier etc override this method."""
		if not state.players[me].is_dead and not self.cant_die(state, me):
			yield from self.apply_death(state, me)
		else:
			yield state

	def executed(self, state: State, me: PlayerID, died: bool) -> StateGen:
		"""Goblin, psychopath etc override this method."""
		if died:
			if self.cant_die(state, me):
				return
			if not state.players[me].is_dead:
				yield from self.apply_death(state, me)
		elif self.cant_die(state, me):
			yield state

	def cant_die(self, state: State, me: PlayerID) -> bool:
		"""Things like checking for innkeeper protection will go here :)"""
		return False

	def _world_str(self, state: State) -> str:
		"""
		For printing nice output representations of worlds. E.g 
		E.g. see Posoiner or Fortune Teller.
		"""
		return ''


@dataclass
class Alsaahir(Character):
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

@dataclass
class Balloonist(Character):
	"""
	Each night, you learn a player of a different character type than last night
	[+0 or +1 Outsider]
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	# Records the categories the last ping could have been registering as.
	prev_character: type[Character] = None 

	@staticmethod
	def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
		(min_tf, max_tf), (min_out, max_out), mn, dm = bounds
		bounds = (min_tf - 1, max_tf), (min_out, max_out + 1), mn, dm
		return bounds

	@dataclass
	class Ping:
		player: PlayerID

	def run_night(self, state: State, night: int, src: PlayerID) -> StateGen:
		"""
		Override Reason: even though we don't need to assert the balloonist 
		gets correct info when poisoned, we still need to take the action to 
		record that the following day the balloonist may see anything.

		NOTE: THIS IMPLEMENTATION ONLY HAS 1 DAY OF MEMORY, BUT TECHNICALLY THE 
		VALIDITY OF BALLOONIST PINGS CAN DEPEND ON ALL PREVIOUS PINGS. 
		E.g. a ping on 'Goblin, Legion, Imp' is not valid because legion must 
		have registered as one of minion or demon. I will fix this is it ever 
		actually comes up :)
		"""
		balloonist = state.players[src]
		ping = self.night_info.get(night, None)
		if (balloonist.is_dead
			or balloonist.is_evil
			or ping is None
		):
			self.prev_character = None
			yield state; return

		character = type(state.players[ping.player].character)

		prev_character = self.prev_character
		self.prev_character = character
		if prev_character is None or balloonist.droison_count:
			# Just record todays ping to check tomorrow's validity
			yield state; return

		if state.vortox:
			# Balloonist MUST get the same category every night in vortox worlds
			if character.category is prev_character.category:
				yield state
			return

		same = info.SameCategory(character, prev_character)(state, src)
		if same is not info.TRUE:
			yield state


@dataclass
class Baron(Character):
	"""
	There are extra Outsiders in play. [+2 Outsiders]
	"""
	category: ClassVar[Categories] = MINION
	is_liar: ClassVar[bool] = True

	@staticmethod
	def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
		(min_tf, max_tf), (min_out, max_out), mn, dm = bounds
		bounds = (min_tf - 2, max_tf - 2), (min_out + 2, max_out + 2), mn, dm
		return bounds

@dataclass
class Chef(Character):
	"""
	You start knowing how many pairs of evil players there are.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping:
		count: int
		def __call__(self, state: State, src: PlayerID) -> STBool:
			N = len(state.players)
			trues, maybes = 0, 0
			evils = [info.IsEvil(i)(state, src) for i in range(N)]
			evils += [evils[0]]  # So that the following zip wraps the circle
			for a, b in zip(evils[:-1], evils[1:]):
				pair = a & b
				maybes += pair is info.MAYBE
				trues += pair is info.TRUE
			return info.STBool(trues <= self.count <= trues + maybes)

@dataclass
class Clockmaker(Character):
	"""
	You start knowing how many steps from the Demon to its nearest Minion.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping:
		steps: int
		def __call__(self, state: State, src: PlayerID) -> STBool:
			"""
			This implementation checks against the min distance over all 
			minion-demon pairs, giving MAYBEs as appropriate. The phrase 
			"The Demon" must give living demons priority over dead demons, so if 
			there are any living demons, all dead demons are ignored.
			"""
			players = state.players
			N = len(players)
			minions, demons = (
				list(filter(
					lambda x: x[1] is not info.FALSE,
					[(i, info.IsCategory(i, cat)(state, src)) for i in range(N)]
				))
				for cat in (MINION, DEMON)
			)
			ignore_dead_demons = any(not players[i].is_dead for i, _ in demons)

			correct_distance, too_close = info.FALSE, info.FALSE
			for demon_pos, is_demon in demons:
				if players[demon_pos].is_dead and ignore_dead_demons:
					continue
				for minion_pos, is_minion in minions:
					is_pair = is_demon & is_minion
					distance = info.circle_distance(minion_pos, demon_pos, N)
					if distance < self.steps:
						too_close |= is_pair
					elif distance == self.steps:
						correct_distance |= is_pair

			return correct_distance & ~too_close

@dataclass
class Dreamer(Character):
	"""
	Each night, choose a player (not yourself or Travellers): 
	you learn 1 good & 1 evil character, 1 of which is correct.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping:
		player: PlayerID
		character1: type[Character]
		character2: type[Character]

		def __call__(self, state: State, src: PlayerID) -> STBool:
			return (
				info.IsCharacter(self.player, self.character1)(state, src) |
				info.IsCharacter(self.player, self.character2)(state, src)
			)

@dataclass
class Drunk(Character):
	"""
	You do not know you are the Drunk. 
	You think you are a Townsfolk character, but you are not.
	"""
	category: ClassVar[Categories] = OUTSIDER
	is_liar: ClassVar[bool] = True

@dataclass
class Empath(Character):
	"""
	Each night, you learn how many of your 2 alive neighbors are evil.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping:
		count: int
		def __call__(self, state: State, src: PlayerID) -> STBool:
			left, right = (info.get_next_player_who_is(
				state,
				lambda s, p: info.IsAlive(p)(s, src) is info.TRUE,
				src,
				clockwise,
			) for clockwise in (True, False))
			evil_neighbours = [info.IsEvil(left)]
			if left != right:
				evil_neighbours.append(info.IsEvil(right))
			return info.ExactlyN(N=self.count, args=evil_neighbours)(state, src)

@dataclass
class FangGu(Character):
	category: ClassVar[Categories] = DEMON
	is_liar: ClassVar[bool] = True

	@staticmethod
	def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
		(min_tf, max_tf), (min_out, max_out), mn, dm = bounds
		bounds = (min_tf - 1, max_tf - 1), (min_out + 1, max_out + 1), mn, dm
		return bounds

@dataclass
class FortuneTeller(Character):
	"""
	Each night, choose 2 players: you learn if either is a Demon. 
	There is a good player that registers as a Demon to you.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping:
		player1: PlayerID
		player2: PlayerID
		demon: bool

		def __call__(self, state: State, src: PlayerID) -> STBool:
			real_result = (
				info.IsCategory(self.player2, DEMON)(state, src) |
				info.IsCategory(self.player1, DEMON)(state, src) |
				info.CharAttrEq(src, 'red_herring', self.player1)(state, src) |
				info.CharAttrEq(src, 'red_herring', self.player2)(state, src)
			)
			return real_result == info.STBool(self.demon)

	def run_setup(self, state: State, src: PlayerID) -> StateGen:
		# Any player could be chosen as the red herring
		for red_herring in range(len(state.players)):
			new_state = state.fork()
			new_state.players[src].character.red_herring = red_herring
			yield new_state

	def _world_str(self, state: State) -> str:
		"""For printing nice output representations of worlds"""
		return f' (Red Herring = {state.players[self.red_herring].name})'


@dataclass
class GenericDemon(Character):
	"""
	Many demons just do one kill each night*, so implment that once here.
	"""
	category: ClassVar[Categories] = DEMON
	is_liar: ClassVar[bool] = True

	def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
		"""Override Reason: Create a world for every kill choice."""
		demon = state.players[me]
		if night == 1 or demon.is_dead or demon.droison_count:
			yield state; return
		for target in range(len(state.players)):
			new_state = state.fork()
			new_demon = new_state.players[me].character
			target_char = new_state.players[target].character
			yield from target_char.maybe_killed_at_night(new_state, target, me)

@dataclass
class Goblin(Character):
	category: ClassVar[Categories] = MINION
	is_liar: ClassVar[bool] = True

@dataclass
class Imp(GenericDemon):
	"""
	Each night*, choose a player: they die. 
	If you kill yourself this way, a Minion becomes the Imp.
	"""

	def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
		"""Override Reason: Add star pass to generic demon"""
		demon = state.players[me]
		if night == 1 or demon.is_dead or demon.droison_count:
			yield state; return
		for target in range(len(state.players)):
			if target == me:
				import sys  # TMP
				if 'unittest' not in sys.modules:
					print("Star pass not implemented yet")
			new_state = state.fork()
			new_demon = new_state.players[me].character
			target_char = new_state.players[target].character
			yield from target_char.maybe_killed_at_night(new_state, target, me)

@dataclass
class Investigator(Character):
	"""
	You start knowing that 1 of 2 players is a particular Minion.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping:
		player1: PlayerID
		player2: PlayerID
		character: type[Character]

		def __call__(self, state: State, src: PlayerID) -> STBool:
			return (
				info.IsCharacter(self.player1, self.character)(state, src) |
				info.IsCharacter(self.player2, self.character)(state, src)
			)

@dataclass
class Juggler(Character):
	"""
	On your 1st day, publicly guess up to 5 players' characters. 
	That night, you learn how many you got correct.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Juggle(events.Event):
		juggle: dict[PlayerID, Character]
		def __call__(self, state: State) -> StateGen:
			pass

	@dataclass
	class Ping(info.Info):
		count: int
		def __call__(self, state: State, src: PlayerID) -> STBool:
			assert state.night > 1, "Jugglers don't ping on night 1"
			juggle = getattr(state.players[src].character, 'juggle', None)
			assert juggle is not None, (
				"No Juggler.Juggle happened before the Juggler.Ping")
			return info.ExactlyN(
				N=self.count, 
				args=(
					info.IsCharacter(player, character)
					for player, character in juggle.items()
				)
			)(state, src)

	def run_day(self, state: State, day: int, player: PlayerID) -> StateGen:
		"""
		Overridden because: No vortox inversion, and the Juggler can make their
		guess even if droisoned or dead during the day.
		TODO!: juggle should be evaluated during the day, not the night!
		"""
		character = state.players[player].character
		if state.day in character.day_info:
			character.juggle = character.day_info[state.day].juggle
		yield state

@dataclass
class Knight(Character):
	"""
	You start knowing 2 players that are not the Demon.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping(info.Info):
		player1: PlayerID
		player2: PlayerID

		def __call__(self, state: State, src: PlayerID) -> STBool:
			return ~(
				info.IsCategory(self.player1, DEMON)(state, src) |
				info.IsCategory(self.player2, DEMON)(state, src)
			)

@dataclass
class Leviathan(Character):
	category: ClassVar[Categories] = DEMON
	is_liar: ClassVar[bool] = True

@dataclass
class Librarian(Character):
	"""
	You start knowing that 1 of 2 players is a particular Outsider. 
	(Or that zero are in play.)
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping:
		player1: PlayerID | None
		player2: PlayerID | None = None
		character: type[Character] | None = None

		def __call__(self, state: State, src: PlayerID) -> STBool:
			usage = (
				'Librarian.Ping usage: '
				'Librarian.Ping(player1, player2, character) or Ping(None)'
			)
			if self.player1 is None:
				assert self.player2 is None and self.character is None, usage
				return info.ExactlyN(N=0, args=[
					info.IsCategory(player, OUTSIDER)
					for player in range(len(state.players))
				])(state, src)

			else:
				assert (self.player2 is not None 
					and self.character is not None), usage
				return (
					info.IsCharacter(self.player1, self.character)(state, src) |
					info.IsCharacter(self.player2, self.character)(state, src)
				)


@dataclass
class Mutant(Character):
	"""
	If you are "mad" about being an Outsider, you might be executed.
	"""
	category: ClassVar[Categories] = OUTSIDER
	is_liar: ClassVar[bool] = True

	def run_night(self, state: State, night: int, src: PlayerID) -> StateGen:
		# Mutants never break madness in these puzzles
		player = state.players[src]
		if (
			player.droison_count 
			or player.is_dead
			or player.bluff.category is not OUTSIDER
		):
			yield state

@dataclass
class Noble(Character):
	"""
	You start knowing 3 players, 1 and only 1 of which is evil.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping(info.Info):
		player1: PlayerID
		player2: PlayerID
		player3: PlayerID

		def __call__(self, state: State, src: PlayerID) -> STBool:
			return info.ExactlyN(N=1, args=(
				info.IsEvil(self.player1),
				info.IsEvil(self.player2),
				info.IsEvil(self.player3),
			))(state, src)

@dataclass
class NoDashii(Character):
	"""
	Each night*, choose a player: they die. 
	Your 2 Townsfolk neighbors are poisoned.
	"""
	category: ClassVar[Categories] = DEMON
	is_liar: ClassVar[bool] = True
	tf_neighbour1: PlayerID | None = None
	tf_neighbour2: PlayerID | None = None

	def run_setup(self, state: State, src: PlayerID) -> StateGen:
		N = len(state.players)
		townsfolk = [
			info.IsCategory((src + step) % N, TOWNSFOLK)(state, src) 
			for step in range(1, N)
		]
		# I allow the No Dashii to poison misregistering characters (e.g. Spy),
		# so there may be multiple possible combinations of neighbour pairs
		# depending on ST choices. Find them alland create a world for each.
		fwd_candidates, bkwd_candidates = [], []
		for candidates, direction in (
			(fwd_candidates, 1),
			(bkwd_candidates, -1),
		):
			for step in range(1, N):
				player = (src + direction * step) % N
				is_tf = info.IsCategory(player, TOWNSFOLK)(state, src)
				if is_tf is not info.FALSE:
					candidates.append(player)
				if is_tf is info.TRUE:
					break
		# Create a world or each combination of left and right poisoned player
		for fwd in fwd_candidates:
			for bkwd in bkwd_candidates:
				new_state = state.fork()
				new_nodashii = new_state.players[src].character
				new_nodashii.tf_neighbour1 = fwd
				new_nodashii.tf_neighbour2 = bkwd
				new_nodashii.maybe_activate_effects(new_state, src)
				yield new_state

	def _activate_effects_impl(self, state: State, src: PlayerID):
		state.players[self.tf_neighbour1].droison(state, src)
		state.players[self.tf_neighbour2].droison(state, src)

	def _deactivate_effects_impl(self, state: State, src: PlayerID):
		state.players[self.tf_neighbour1].undroison(state, src)
		state.players[self.tf_neighbour2].undroison(state, src)


@dataclass
class Poisoner(Character):
	"""
	Each night, choose a player: they are poisoned tonight and tomorrow day.
	"""
	category: ClassVar[Categories] = MINION
	is_liar: ClassVar[bool] = True
	target: PlayerID = None

	# Keep history just for debug and pretty printing the history of a game.
	target_history: list[PlayerID] = field(default_factory=list)

	def run_night(self, state: State, night: int, src: PlayerID) -> StateGen:
		"""Override Reason: Create a world for every poisoning choice."""
		poisoner = state.players[src]
		if poisoner.is_dead:
			yield state; return
		for target in range(len(state.players)):
			new_state = state.fork()
			new_poisoner = new_state.players[src].character
			# Even droisoned poisoners make a choice, because they might be 
			# undroisoned before dusk.
			new_poisoner.target = target
			new_poisoner.target_history.append(target)
			new_poisoner.maybe_activate_effects(new_state, src)
			yield new_state

	def end_day(self, state: State, day: int, src: PlayerID) -> None:
		self.maybe_deactivate_effects(state, src)
		self.target = None

	def _activate_effects_impl(self, state: State, src: PlayerID):
		state.players[self.target].droison(state, src)

	def _deactivate_effects_impl(self, state: State, src: PlayerID):
		# Break a self-poisoning infinite recursion, whilst still leaving the 
		# Poisoner marked as droisoned.
		if self.target != src:
			state.players[self.target].undroison(state, src)

	def _world_str(self, state: State) -> str:
		return f' (Poisoned {", ".join(
			state.players[p].name for p in self.target_history
		)})'


@dataclass
class Pukka(Character):
	"""
	Each night, choose a player: they are poisoned.
	The previously poisoned player dies then becomes healthy.
	"""
	category: ClassVar[Categories] = DEMON
	is_liar: ClassVar[bool] = True
	target: PlayerID | None = None

	def run_night(self, state: State, day: int, src: PlayerID) -> StateGen:
		"""
		Override Reason: Create a world for every poisoning choice. Even 
		a droisoned pukka must make a choice.
		"""
		pukka = state.players[src]
		if pukka.is_dead:
			yield state; return
		if self.target is not None and pukka.droison_count == 0:
			# Kill the previously poisoned player
			print("Pukka kills not implemented")
		for target in range(len(state.players)):
			new_state = state.fork()
			new_pukka = new_state.players[src].character
			new_pukka.target = target
			new_pukka.target_history.append(target)
			new_pukka.maybe_activate_effects(new_state, src)
			yield new_state

	def end_day(self, state: State, day: int, src: PlayerID) -> None:
		self.maybe_deactivate_effects(state, src)

	def _activate_effects_impl(self, state: State, src: PlayerID):
		state.players[self.target].droison(state, src)

	def _deactivate_effects_impl(self, state: State, src: PlayerID):
		# Break a self-poisoning infinite recursion, whilst still leaving the 
		# Pukka marked as droisoned.
		if self.target != src:
			state.players[self.target].undroison(state, src)

@dataclass
class Ravenkeeper(Character):
	"""
	If you die at night, you are woken to choose a player:
	you learn their character.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	death_night: int | None = None

	@dataclass
	class Ping:
		player: PlayerID
		character: type[Character]

		def __call__(self, state: State, src: PlayerID) -> STBool:
			ravenkeeper = state.players[src].character
			death_night = ravenkeeper.death_night
			if death_night is None or death_night != state.night:
				return info.FALSE
			return info.IsCharacter(self.player, self.character)(state, src)

	def apply_death(self, state: State, me: PlayerID) -> StateGen:
		"""Override Reason: Record when death happened."""
		if state.night is not None:
			self.death_night = state.night
		yield from super().apply_death(state, me)

	def run_night(self, state: State, night: int, src: PlayerID) -> StateGen:
		"""
		Override Reason: Even if dead.
		The Ping checks the death was on the same night.
		"""
		if self.default_info_check(
			state, self.night_info, night, src, even_if_dead=True
		):
			yield state



@dataclass
class Recluse(Character):
	"""
	You might register as evil & as a Minion or Demon, even if dead.
	"""
	category: ClassVar[Categories] = OUTSIDER
	is_liar: ClassVar[bool] = False
	misregister_categories: ClassVar[tuple[Categories, ...]] = (MINION, DEMON)


@dataclass
class Savant(Character):
	"""
	Each day, you may visit the Storyteller to learn 2 things in private: 
	one is true & one is false.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping(info.Info):
		a: info.Info
		b: info.Info
		def __call__(self, state: State, src: PlayerID):
			a, b = self.a(state, src), self.b(state, src)
			if state.vortox:
				return not (a | b)
			return a ^ b

	def run_day(self, state: State, day: int, src: PlayerID) -> StateGen:
		""" Override Reason: Novel Vortox effect on Savant, see Savant.Ping."""
		savant = state.players[src]
		if (
			savant.is_dead
			or savant.is_evil
			or savant.droison_count
			or day not in savant.character.day_info
		):
			yield state; return
		ping = savant.character.day_info[day]
		result = ping(state, src)
		if result is not info.FALSE:
			yield state


@dataclass
class Seamstress(Character):
	"""
	Once per game, at night, choose 2 players (not yourself):
	you learn if they are the same alignment.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping(info.Info):
		player1: PlayerID
		player2: PlayerID
		same: bool
		def __call__(self, state: State, src: PlayerID):
			a = info.IsEvil(self.player1)(state, src)
			b = info.IsEvil(self.player2)(state, src)
			enemies = a ^ b
			if self.same:
				return ~enemies
			return enemies

@dataclass
class ScarletWoman(Character):
	category: ClassVar[Categories] = MINION
	is_liar: ClassVar[bool] = True


@dataclass
class Shugenja(Character):
	"""
	You start knowing if your closest evil player is clockwise or 
	anti-clockwise. If equidistant, this info is arbitrary.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping(info.Info):
		clockwise: bool
		def __call__(self, state: State, src: PlayerID):
			N = len(state.players)
			direction = 1 if self.clockwise else - 1
			evils = [None] + [
				info.IsEvil((src + direction * step) % N)(state, src)
				for step in range(1, N)
			]
			fwd_maybe, bwd_maybe, fwd_true, bwd_true = N, N, N, N
			for step in range(N // 2, 0, -1):
				if evils[step] is info.TRUE:
					fwd_true, fwd_maybe = step, step
				elif evils[step] is info.MAYBE:
					fwd_maybe = step
				if evils[-step] is info.TRUE:
					bwd_true, bwd_maybe = step, step
				elif evils[-step] is info.MAYBE:
					bwd_maybe = step

			if bwd_true < fwd_maybe:
				return info.FALSE
			if fwd_true < bwd_maybe:
				return info.TRUE
			return info.MAYBE	

@dataclass
class Steward(Character):
	"""
	You start knowing 1 good player.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping(info.Info):
		player: PlayerID
		def __call__(self, state: State, src: PlayerID):
			return ~info.IsEvil(self.player)(state, src)

@dataclass
class Saint(Character):
	"""
	If you die by execution, your team loses.
	"""
	category: ClassVar[Categories] = OUTSIDER
	is_liar: ClassVar[bool] = False

@dataclass
class Slayer(Character):
	"""
	Once per game, during the day, publicly choose a player: 
	if they are the Demon, they die.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False
	spent: bool = False

	@dataclass
	class Shot(events.Event):
		src: PlayerID
		target: PlayerID
		died: bool

		def __call__(self, state: State) -> StateGen:
			shooter = state.players[self.src]
			target = state.players[self.target]
			if (
				shooter.is_dead
				or target.is_dead
				or not isinstance(shooter.character, Slayer)
				or shooter.droison_count
				or shooter.character.spent
			):
				should_die = info.FALSE
			else:
				should_die = info.IsCategory(self.target, DEMON)

			if isinstance(shooter.character, Slayer):
				shooter.character.spent = True

			if self.died and should_die is not info.FALSE:
				yield from target.character.apply_death(state, self.target)
			elif not self.died and should_die is not info.TRUE:
				yield state

@dataclass
class Spy(Character):
	"""
	Each night, you see the Grimoire. You might register as good & as a 
	Townsfolk or Outsider, even if dead.
	"""
	category: ClassVar[Categories] = MINION
	is_liar: ClassVar[bool] = True
	misregister_categories: ClassVar[tuple[Categories, ...]] = (
		TOWNSFOLK, OUTSIDER
	)

@dataclass
class WasherWoman(Character):
	"""
	You start knowing that 1 of 2 players is a particular Townsfolk.
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False

	@dataclass
	class Ping(info.Info):
		player1: PlayerID
		player2: PlayerID
		character: Character
		def __call__(self, state: State, src: PlayerID) -> STBool:
			return (
				info.IsCharacter(self.player1, self.character)(state, src) |
				info.IsCharacter(self.player2, self.character)(state, src)
			)


@dataclass
class VillageIdiot(Character):
	"""
	Each night, choose a player: you learn their alignment. 
	[+0 to +2 Village Idiots. 1 of the extras is drunk]
	"""
	category: ClassVar[Categories] = TOWNSFOLK
	is_liar: ClassVar[bool] = False
	is_drunk_VI: bool = False

	@dataclass
	class Ping:
		player: PlayerID
		is_evil: bool
		def __call__(self, state: State, src: PlayerID) -> STBool:
			registers_evil = info.IsEvil(self.player)(state, src)
			return registers_evil == info.STBool(self.is_evil)

	def run_setup(self, state: State, src: PlayerID) -> StateGen:
		# If there is more than one Village Idiot, choose one to be the drunk VI
		VIs = [i for i, player in enumerate(state.players)
				if isinstance(player.character, VillageIdiot)]
		already_done = any(state.players[p].character.is_drunk_VI for p in VIs)
		if len(VIs) == 1 or already_done:
			yield state
			return

		for vi in VIs:
			new_state = state.fork()
			new_state.players[vi].droison_count += 1
			new_state.players[vi].character.is_drunk_VI = True
			yield new_state

	def _world_str(self, state: State) -> str:
		"""For printing nice output representations of worlds"""
		if self.is_drunk_VI:
			return f' (Drunk)'
		return ''


@dataclass
class Vortox(Character):
	category: ClassVar[Categories] = DEMON
	is_liar: ClassVar[bool] = True

@dataclass
class Zombuul(Character):
	category: ClassVar[Categories] = DEMON
	is_liar: ClassVar[bool] = True

	registering_dead: bool = False



GLOBAL_SETUP_ORDER = [
	NoDashii,
	FortuneTeller,
	VillageIdiot,
]

GLOBAL_NIGHT_ORDER = [
	Poisoner,
	ScarletWoman,
	Imp,
	Pukka,
	FangGu,
	NoDashii,
	Vortox,
	Ravenkeeper,
	WasherWoman,
	Librarian,
	Investigator,
	Chef,
	Empath,
	FortuneTeller,
	Clockmaker,
	Dreamer,
	Seamstress,
	Juggler,
	Steward,
	Knight,
	Noble,
	Balloonist,
	Shugenja,
	VillageIdiot,
]

GLOBAL_DAY_ORDER = [
	Alsaahir,
	Juggler,
	Savant,
	Slayer,
	Saint,
	Mutant,
]

INACTIVE_CHARACTERS = [
	Leviathan,
	Goblin,
	Drunk,
	Recluse,
	Spy,
	Baron,
]
