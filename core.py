from __future__ import annotations

from collections.abc import Iterable
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass, field
import enum
import itertools as it
from multiprocessing import Pool
from typing import Any, Callable, ClassVar, Generator, TYPE_CHECKING

if TYPE_CHECKING:
	from characters import Character
	from info import PlayerID, Info

import characters
import info


type StateGen = Generator[State]


@dataclass
class Player:
	"""
	An instance of a player. 
	Character-specific info is stored in the character attribute, because
	characters can change, but players are forever.
	"""
	name: str
	character: Character
	bluff: type[Character] | None = None
	is_evil: bool = False
	is_dead: bool = False
	droison_count: int = 0

	def droison(self, state: State, src: PlayerID) -> None:
		self.droison_count += 1 
		self.character.maybe_deactivate_effects(state, self.id)

	def undroison(self, state: State, src: PlayerID) -> None:
		self.droison_count -= 1 
		self.character.maybe_activate_effects(state, self.id)

	def _world_str(self, state: State) -> str:
		"""For printing nice output representations of worlds"""
		ret = type(self.character).__name__
		ret += self.character._world_str(state)
		return ret


@dataclass
class State:
	# The list of players starts with You as player 0 and proceeds clockwise
	players: list[Player]

	def __post_init__(self):
		"""Called before worlds are posited by overriding these characters"""
		for i, player in enumerate(self.players):
			player.id = i
			player.bluff = type(player.character)

	def begin_game(self, default_counts: tuple[int, ...]) -> bool:
		"""Called after player positions and characters have been chosen"""

		# Check that the starting player type counts are legal
		T, O, M, D = default_counts
		bounds = ((T, T), (O, O), (M, M), (D, D))
		for player in self.players:
			bounds = player.character.modify_category_counts(bounds)
		counts = Counter(p.character.category for p in self.players)
		for (lo, hi), cat in zip(bounds, characters.Categories):
			if not (lo <= counts[cat] <= hi):
				return False
		self.category_counts = counts

		# Initialise data structures for game
		self.update_character_index()
		self.initial_characters = tuple(type(p.character) for p in self.players)
		self.night, self.day = 0, None
		self.order_position = 0
		return True

	def run_action_for_next_player(self, round_: int, phase: str) -> StateGen:
		match phase:
			case 'night':
				order = self.night_order
			case 'day':
				order = self.day_order
			case 'setup':
				order = self.setup_order
		if self.order_position >= len(order):
			yield self  # Move this check to caller to reduce generator stack?
			return
		player = self.players[order[self.order_position]]
		match phase:
			case 'night':
				substates = player.character.run_night(self, round_, player.id)
			case 'day':
				substates = player.character.run_day(self, round_, player.id)
			case 'setup':
				substates = player.character.run_setup(self, player.id)
		for substate in substates:
			substate.order_position += 1
			yield substate

	def end_setup(self):
		self.order_position = 0
		return self

	def end_night(self):
		for player in self.players:
			player.done_action = False
		self.order_position = 0
		self.night, self.day = None, self.night
		return self

	def end_day(self):
		for player in self.players:
			player.done_action = False
			player.character.end_day(self, self.day, player.id)
		self.order_position = 0
		self.night, self.day = self.day + 1, None
		return self

	def character_change(self, player: PlayerID, character: Character):
		self.players[player].character = character
		self.update_character_index()

	def update_character_index(self):
		# TODO: This fn should modify self.order_position to compensate for change?
		self.vortox = False
		self.setup_order, self.night_order, self.day_order = [], [], []
		for character in characters.GLOBAL_SETUP_ORDER:
			for i, player in enumerate(self.players):
				if type(player.character) is character:
					self.setup_order.append(i)
					if character is characters.Vortox:
						self.vortox = True
		for character in characters.GLOBAL_NIGHT_ORDER:
			for i, player in enumerate(self.players):
				if type(player.character) is character:
					self.night_order.append(i)
		for character in characters.GLOBAL_DAY_ORDER:
			for i, player in enumerate(self.players):
				if type(player.character) is character:
					self.day_order.append(i)

	def __str__(self) -> str:
		ret = ['World(']
		pad = max(len(player.name) for player in self.players) + 1
		for player in self.players:
			char = type(player.character)
			rhs = player._world_str(self)
			colour = 0
			if char.is_liar:
				colour = '31' if player.is_evil else '34'
			ret.append(
				f'\033[{colour};1m{player.name: >{pad}} : {rhs}\033[0m'
			)
		ret.append(')')
		return '\n'.join(ret)


def _run_game_gen(states: StateGen, n_players: int, n_rounds: int) -> StateGen:

	def run_phase_for_next_player(substates, phase, round_):
		for ss in substates:
			yield from ss.run_action_for_next_player(round_, phase)

	for player in range(n_players):
		states = run_phase_for_next_player(states, 'setup', None)
	states = map(lambda state: state.end_setup(), states)
	for round_ in range(n_rounds):
		for player in range(n_players):
			states = run_phase_for_next_player(states, 'night', round_)
		states = map(lambda state: state.end_night(), states)
		for player in range(n_players):
			states = run_phase_for_next_player(states, 'day', round_)
		states = map(lambda state: state.end_day(), states)
	yield from states


def _deduplicate_by_initial_characters(states: StateGen) -> StateGen:
	"""
	Deduplicate worlds that have the same starting characters if you're only
	interested in what characters people started as, and don't care to 
	distinguish two worlds that only differ in e.g. the choice of the 
	red_herring.
	"""
	seen = set()
	for state in states:
		if state.initial_characters not in seen:
			seen.add(state.initial_characters)
			yield state


def world_gen(
	public_state: State,
	possible_demons: list[Character],
	possible_minions: list[Character],
	possible_hidden_good: list[Character],
	possible_hidden_self: list[Character],
	category_counts: tuple[int, int, int, int] = (7, 0, 2, 1),
	world_init_check: Callable[State, bool] | None = None,
	deduplicate_initial_characters: bool = True,
) -> StateGen:
	"""Generate worlds from the perspective of player 0"""

	check_characters_registered(
		[type(p.character) for p in public_state.players] + possible_demons + 
		possible_minions + possible_hidden_good + possible_hidden_self
	)

	num_players = len(public_state.players)
	num_rounds = 1 + max(
		max(it.chain(
			player.character.night_actions.keys(),
			player.character.day_actions.keys(),
		), default=0)
		for player in public_state.players
	)

	n_townsfolk, n_outsiders, n_minions, n_demons = category_counts
	liar_combinations = it.product(
		it.combinations(possible_demons, n_demons),
		it.combinations(possible_minions, n_minions),
		it.chain(*[
			it.combinations(possible_hidden_good, i)
			for i in range(len(possible_hidden_good) + 1)
		])
	)

	def _createWorld(
		liars: list[Character],
		positions: list[int]
	) -> State | None:
		"""Given a list of """
		world = deepcopy(public_state)
		for liar, position in zip(liars, positions):
			if position == 0 and liar not in possible_hidden_self:
				return None
			world.players[position].character = liar()
			world.players[position].is_evil = liar.category in (
				characters.MINION, characters.DEMON
			)
		if not world.begin_game(category_counts):
			return None
		if world_init_check is not None and not world_init_check(world):
			return None
		return world

	def _initial_characters_gen() -> StateGen:
		player_ids = list(range(len(public_state.players)))
		for demons, minions, hidden_good in liar_combinations:
			liars = demons + minions + hidden_good
			for liar_positions in it.permutations(player_ids, len(liars)):
				world = _createWorld(liars, liar_positions)
				if world is not None:
					yield world

	gen = _initial_characters_gen()
	gen = _run_game_gen(gen, num_players, num_rounds)
	if deduplicate_initial_characters:
		gen = _deduplicate_by_initial_characters(gen)

	yield from gen


def check_characters_registered(check_list: Iterable[type[Character]]):
	"""
	Whenever I implement a new character I forget to register it in the night 
	order and lose time trying to figure out why it isn't working. This test 
	funciton just catches when I've done that, to save me some debugging time.
	"""
	registered = (characters.GLOBAL_NIGHT_ORDER
	 			   + characters.GLOBAL_DAY_ORDER 
	 			   + characters.INACTIVE_CHARACTERS)
	for character in check_list:
		if character not in registered:
			raise ValueError(
				f'Character {character.__name__} has not been placed in the '
				'night order. Did you forget?'
			)