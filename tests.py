import unittest

from core import *
from characters import *
from events import *
from info import *


def assert_solutions(
	testcase: unittest.TestCase, 
	worlds: Generator[State],
	solutions: tuple[tuple[Character, ...]],
):
	"""
	Checks that a given list of world states has character placements that 
	exactly match the allowed solutions
	"""
	def to_string(answer: Iterable[Character]) -> str:
		return ', '.join(x.__name__ for x in answer)
	predictions = tuple(
		to_string(world.initial_characters)
		for world in worlds
	)
	testcase.assertEqual(sorted(predictions), sorted(map(to_string, solutions)))


class Puzzles(unittest.TestCase):
	def test_puzzle_1(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1erb5e2/can_the_sober_savant_solve_the_puzzle

		You, Tim, Sula, Oscar, Matt, Anna = range(6)
		class DrunkBetweenTownsfolk(Info):
			def __call__(self, state: State, src: PlayerID):
				N = len(state.players)
				result = FALSE
				for i, player in enumerate(state.players):
					found_drunk = IsCharacter(i, Drunk)(state, src)
					if found_drunk is FALSE:
						continue
					tf_neighbours = (
						IsCategory((i - 1) % N, TOWNSFOLK)(state, src) & 
						IsCategory((i + 1) % N, TOWNSFOLK)(state, src)
					)
					result |= found_drunk & tf_neighbours
				return result

		state = State([
			Player(name='You', character=Savant(day_info={
				1: Savant.Ping(
					IsInPlay(Investigator), 
					IsEvil(Tim) | IsEvil(Anna)
				),
				2: Savant.Ping(
					Chef.Ping(1), 
					DrunkBetweenTownsfolk()
				),
				3: Savant.Ping(
					IsCategory(Tim, MINION) | IsCategory(Sula, MINION),
					~IsInPlay(Noble)
				),
			})),
			Player(name='Tim', character=Knight(night_info={
				1: Knight.Ping(Sula, Anna)
			})),
			Player(name='Sula', character=Steward(night_info={
				1: Steward.Ping(Matt)
			})),
			Player(name='Oscar', character=Investigator(night_info={
				1: Investigator.Ping(Sula, Anna, Goblin)
			})),
			Player(name='Matt', character=Noble(night_info={
				1: Noble.Ping(Tim, Sula, Oscar)
			})),
			Player(name='Anna', character=Seamstress(night_info={
				1: Seamstress.Ping(Sula, Oscar, same=False)
			}))
		])

		worlds = world_gen(
			state,
			possible_demons=[Leviathan],
			possible_minions=[Goblin],
			possible_hidden_good=[Drunk],
			possible_hidden_self=[],
		)

		assert_solutions(self, worlds, solutions=(
			(Savant, Goblin, Steward, Drunk, Noble, Leviathan),
		))


	def test_puzzle_2(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1ewxu0r/weekly_puzzle_2_come_fly_with_me/

		You, Steph, Fraser, Tim, Sarah, Matthew, Anna, Sula = range(8)
		state = State([
			Player(name='You', character=Seamstress(night_info={
				1: Seamstress.Ping(Matthew, Sula, same=True)
			})),
			Player(name='Steph', character=Knight(night_info={
				1: Knight.Ping(Tim, Sula)
			})),
			Player(name='Fraser', character=FortuneTeller(night_info={
				1: FortuneTeller.Ping(Sarah, Anna, demon=False),
				2: FortuneTeller.Ping(You, Fraser, demon=False),
				3: FortuneTeller.Ping(Steph, Sarah, demon=False),
			})),
			Player(name='Tim', character=Saint()),
			Player(name='Sarah', character=Investigator(night_info={
				1: Investigator.Ping(Matthew, Fraser, Goblin)
			})),
			Player(name='Matthew', character=Juggler(
				day_info={
					1: Juggler.Juggle({
						Steph: Knight,
						Sarah: Leviathan,
						Anna: Goblin,
						Sula: Goblin,
						You: Seamstress,
					})
				},
				night_info={2: Juggler.Ping(2)}
			)),
			Player(name='Anna', character=Clockmaker(night_info={
				1: Clockmaker.Ping(1)
			})),
			Player(name='Sula', character=Balloonist(night_info={
				1: Balloonist.Ping(Tim),
				2: Balloonist.Ping(Matthew),
				3: Balloonist.Ping(Steph),
			})),
		])

		worlds = world_gen(
			state,
			possible_demons=[Leviathan],
			possible_minions=[Goblin],
			possible_hidden_good=[Drunk],
			possible_hidden_self=[Drunk],
		)

		assert_solutions(self, worlds, solutions=(
			(Drunk, Knight, FortuneTeller, Saint, Goblin, 
				Leviathan, Clockmaker, Balloonist),
		))


	def test_puzzle_3a(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1f2jht3/weekly_puzzle_3a_3b_not_throwing_away_my_shot/

		You, Aoife, Tom, Sula, Matthew, Oscar, Josh = range(7)
		state = State(
			players=[
				Player(name='You', character=Slayer()),
				Player(name='Aoife', character=Chef(night_info={
					1: Chef.Ping(0)
				})),
				Player(name='Tom', character=Recluse()),
				Player(name='Sula', character=Investigator(night_info={
					1: Investigator.Ping(You, Aoife, Baron)
				})),
				Player(name='Matthew', character=WasherWoman(night_info={
					1: WasherWoman.Ping(Aoife, Oscar, Librarian)
				})),
				Player(name='Oscar', character=Librarian(night_info={
					1: Librarian.Ping(None)
				})),
				Player(name='Josh', character=Empath(night_info={
					1: Empath.Ping(0)
				})),
			],
			day_events={
				1: Slayer.Shot(src=You, target=Tom, died=True),
			},
		)

		worlds = world_gen(
			state,
			possible_demons=[Imp],
			possible_minions=[Baron, Spy, Poisoner, ScarletWoman],
			possible_hidden_good=[Drunk],
			possible_hidden_self=[Drunk],
		)
		assert_solutions(self, worlds, solutions=(
			(Slayer, Baron, Recluse, Investigator, Imp, Drunk, Empath),
		))


	def test_puzzle_3b(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1f2jht3/weekly_puzzle_3a_3b_not_throwing_away_my_shot/

		You, Tim, Sarah, Hannah, Dan, Anna, Matt, Fraser = range(8)
		state = State(
			players=[
				Player(name='You', character=Slayer()),
				Player(name='Tim', character=Librarian(night_info={
					1: Librarian.Ping(You, Hannah, Drunk)
				})),
				Player(name='Sarah', character=Investigator(night_info={
					1: Investigator.Ping(Tim, Fraser, ScarletWoman)
				})),
				Player(name='Hannah', character=Saint()),
				Player(name='Dan', character=Chef(night_info={
					1: Chef.Ping(0)
				})),
				Player(name='Anna', character=Recluse()),
				Player(name='Matt', character=WasherWoman(night_info={
					1: WasherWoman.Ping(Tim, Dan, Librarian)
				})),
				Player(name='Fraser', character=Empath(night_info={
					1: Empath.Ping(0)
				})),
			],
			day_events={1: Slayer.Shot(src=You, target=Anna, died=True)},
		)

		worlds = world_gen(
			state,
			possible_demons=[Imp],
			possible_minions=[Baron, Spy, Poisoner, ScarletWoman],
			possible_hidden_good=[Drunk],
			possible_hidden_self=[Drunk],
		)
		assert_solutions(self, worlds, solutions=(
			(Slayer, Librarian, Imp, Spy, Chef, Recluse, WasherWoman, Empath),
		))

	def test_puzzle_4(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1f823s4/weekly_puzzle_4_the_manyheaded_monster/

		You, Anna, Dan, Fraser, Sarah, Tim, Matt, Hannah = range(8)
		state = State(
			players=[
				Player(name='You', character=Investigator(night_info={
					1: Investigator.Ping(Matt, Hannah, Marionette)
				})),
				Player(name='Anna', character=Empath(night_info={
					1: Empath.Ping(2)
				})),
				Player(name='Dan', character=Undertaker(night_info={
					2: Undertaker.Ping(Anna, Empath)
				})),
				Player(name='Fraser', character=FortuneTeller(night_info={
					1: FortuneTeller.Ping(Anna, Tim, demon=True),
					2: FortuneTeller.Ping(You, Fraser, demon=False),
					3: FortuneTeller.Ping(You, Sarah, demon=True),
				})),
				Player(name='Sarah', character=Librarian(night_info={
					1: Librarian.Ping(You, Hannah, Drunk)
				})),
				Player(name='Tim', character=Recluse()),
				Player(name='Matt', character=Juggler(
					day_info={
						1: Juggler.Juggle({
							You: Investigator,
							Dan: LordOfTyphon,
							Tim: Recluse,
							Hannah: Dreamer,
						}
					)},
					night_info={2: Juggler.Ping(1)}
				)),
				Player(name='Hannah', character=Dreamer(night_info={
					1: Dreamer.Ping(You, Investigator, LordOfTyphon)
				})),
			],
			day_events={
				1: Execution(Anna, died=True),
				2: Execution(Dan, died=True),
			},
			night_deaths={2: Hannah, 3: Tim},
		)

		worlds = world_gen(
			state,
			possible_demons=[LordOfTyphon],
			possible_minions=[Marionette, Poisoner],
			possible_hidden_good=[Drunk],
			possible_hidden_self=[Drunk, Marionette],
		)
		assert_solutions(self, worlds, solutions=(
			(Investigator, Drunk, Marionette, LordOfTyphon, Poisoner, Recluse, 
				Juggler, Dreamer),
			(Investigator, Drunk, Poisoner, LordOfTyphon, Marionette, Recluse, 
				Juggler, Dreamer),
		))


	def test_puzzle_5a(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fcriex/weekly_puzzle_5a_5b_you_only_guess_twice/

		You, Dan, Tom, Matt, Anna, Hannah, Oscar = range(7)
		state = State([
			Player(name='You', character=Alsaahir()),
			Player(name='Dan', character=Noble(night_info={
				1: Noble.Ping(Tom, Anna, Hannah)
			})),
			Player(name='Tom', character=Knight(night_info={
				1: Knight.Ping(Dan, Anna)
			})),
			Player(name='Matt', character=Investigator(night_info={
				1: Investigator.Ping(Anna, Oscar, Goblin)
			})),
			Player(name='Anna', character=Empath(night_info={
				1: Empath.Ping(Dan)
			})),
			Player(name='Hannah', character=Steward(night_info={
				1: Steward.Ping(Tom)
			})),
			Player(name='Oscar', character=Seamstress(night_info={
				1: Seamstress.Ping(Tom, Hannah, same=False)
			})),
		])

		worlds = world_gen(
			state,
			possible_demons=[Leviathan],
			possible_minions=[Goblin],
			possible_hidden_good=[],
			possible_hidden_self=[],
		)

		assert_solutions(self, worlds, solutions=(
			(Alsaahir, Noble, Knight, Investigator, Empath, Leviathan, Goblin),
			(Alsaahir, Noble, Knight, Investigator, Goblin, Steward, Leviathan),
		))


	def test_puzzle_5b(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fcriex/weekly_puzzle_5a_5b_you_only_guess_twice/

		You, Sarah, Tim, Matthew, Steph, Aoife, Fraser = range(7)
		state = State([
			Player(name='You', character=Juggler()),
			Player(name='Sarah', character=Empath(night_info={
				1: Empath.Ping(You)
			})),
			Player(name='Tim', character=Seamstress(night_info={
				1: Seamstress.Ping(You, Fraser, same=True)
			})),
			Player(name='Matthew', character=Steward(night_info={
				1: Steward.Ping(You)
			})),
			Player(name='Steph', character=Investigator(night_info={
				1: Investigator.Ping(Sarah, Fraser, Goblin)
			})),
			Player(name='Aoife', character=Noble(night_info={
				1: Noble.Ping(Sarah, Tim, Matthew)
			})),
			Player(name='Fraser', character=Knight(night_info={
				1: Knight.Ping(You, Steph)
			})),
		])

		worlds = world_gen(
			state,
			possible_demons=[Leviathan],
			possible_minions=[Goblin],
			possible_hidden_good=[],
			possible_hidden_self=[],
		)

		assert_solutions(self, worlds, solutions=(
			(Juggler, Leviathan, Seamstress, Steward, Goblin, Noble, Knight),
			(Juggler, Empath, Seamstress, Leviathan, Goblin, Noble, Knight),
			(Juggler, Goblin, Seamstress, Steward, Investigator, Leviathan, Knight),
			(Juggler, Empath, Seamstress, Steward, Goblin, Leviathan, Knight),
		))


	def test_puzzle_6(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fj1h0c/weekly_puzzle_6_super_marionette_bros/

		You, Sarah, Tim, Dan, Aoife, Sula, Steph, Fraser, Matthew = range(9)
		state = State(
			players=[
				Player(name='You', character=Librarian(night_info={
					1: Librarian.Ping(Sula, Fraser, Drunk)
				})),
				Player(name='Sarah', character=Saint()),
				Player(name='Tim', character=Noble(night_info={
					1: Noble.Ping(Aoife, Sula, Fraser)
				})),
				Player(name='Dan', character=Seamstress(night_info={
					1: Seamstress.Ping(Aoife, Tim, same=False)
				})),
				Player(name='Aoife', character=Investigator(night_info={
					1: Investigator.Ping(Dan, Matthew, Marionette)
				})),
				Player(name='Sula', character=Juggler(
					day_info={1: Juggler.Juggle({
						You: Librarian,
						Tim: Marionette,
						Dan: Vortox,
						Fraser: Drunk,
						Matthew: Pukka,
					})},
					night_info={2: Juggler.Ping(2)}
				)),
				Player(name='Steph', character=Knight(night_info={
					1: Knight.Ping(Sarah, Dan)
				})),
				Player(name='Fraser', character=Empath(night_info={
					1: Empath.Ping(0)
				})),
				Player(name='Matthew', character=Steward(night_info={
					1: Steward.Ping(Dan)
				})),
			],
			day_events={1: Execution(Fraser, died=True)},
			night_deaths={2: Steph},
		)
		worlds = world_gen(
			state,
			possible_demons=[NoDashii, Vortox, Pukka],
			possible_minions=[Marionette],
			possible_hidden_good=[Drunk],
			possible_hidden_self=[Drunk, Marionette],
		)
		assert_solutions(self, worlds, solutions=(
			(Marionette, Saint, Noble, Seamstress, Investigator, Juggler, Drunk,
			 Empath, Vortox),
		))


	def test_puzzle_7(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1foeq4d/weekly_puzzle_7_the_savant_strikes_back/

		You, Fraser, Sarah, Oscar, Anna, Aoife, Steph, Tim = range(8)
		state = State([
			Player(name='You', character=Savant(day_info={
				1: Savant.Ping(
					ExactlyN(N=1, args=[IsEvil(Fraser), IsEvil(Anna), IsEvil(Steph)]),
					Clockmaker.Ping(3),
				),
				2: Savant.Ping(
					CharAttrEq(Sarah, 'red_herring', Sarah),
					CharAttrEq(Fraser, 'is_drunk_VI', True),
				),
				3: Savant.Ping(
					ExactlyN(N=2, args=[
						IsInPlay(Juggler),
						IsInPlay(Shugenja),
						IsInPlay(VillageIdiot)
					]),
					ExactlyN(N=2, args=[
						IsCategory(Oscar, TOWNSFOLK),
						IsCategory(Anna, TOWNSFOLK),
						IsCategory(Tim, TOWNSFOLK)
					]),
				),
			})),
			Player(name='Fraser', character=VillageIdiot(night_info={
				1: VillageIdiot.Ping(Sarah, is_evil=False),
				2: VillageIdiot.Ping(Aoife, is_evil=False),
				3: VillageIdiot.Ping(You, is_evil=False),
			})),
			Player(name='Sarah', character=FortuneTeller(night_info={
				1: FortuneTeller.Ping(Oscar, Aoife, demon=False),
				2: FortuneTeller.Ping(You, Sarah, demon=True),
				3: FortuneTeller.Ping(Fraser, Tim, demon=False),
			})),
			Player(name='Oscar', character=Investigator(night_info={
				1: Investigator.Ping(Fraser, Steph, Goblin),
			})),
			Player(name='Anna', character=Juggler(
				day_info={1: Juggler.Juggle({You: Savant, Tim: VillageIdiot})},
				night_info={2: Juggler.Ping(1)}
			)),
			Player(name='Aoife', character=Shugenja(night_info={
				1: Shugenja.Ping(clockwise=False)
			})),
			Player(name='Steph', character=Dreamer(night_info={
				1: Dreamer.Ping(Sarah, FortuneTeller, Leviathan),
				2: Dreamer.Ping(You, Savant, Goblin),
				3: Dreamer.Ping(Fraser, Mutant, Goblin),
			})),
			Player(name='Tim', character=VillageIdiot(night_info={
				1: VillageIdiot.Ping(Anna, is_evil=False),
				2: VillageIdiot.Ping(Sarah, is_evil=False),
				3: VillageIdiot.Ping(You, is_evil=False),
			})),
		])

		worlds = world_gen(
			state,
			possible_demons=[Leviathan],
			possible_minions=[Goblin],
			possible_hidden_good=[Mutant],
			possible_hidden_self=[],
		)

		assert_solutions(self, worlds, solutions=(
			(Savant, VillageIdiot, FortuneTeller, Goblin, 
				Leviathan, Shugenja, Mutant, VillageIdiot),
		))


	def test_puzzle_12a(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gexyoq/weekly_puzzle_12a_12b_thunderstruck

		You, Tim, Fraser, Hannah, Sarah, Jasmine = range(6)
		state = State(
			players=[
				Player(name='You', character=Dreamer(night_info={
					1: Dreamer.Ping(Sarah, Lunatic, ScarletWoman)
				})),
				Player(name='Tim', character=Clockmaker(night_info={
					1: Clockmaker.Ping(2)
				})),
				Player(name='Fraser', character=Empath(night_info={
					1: Empath.Ping(0)
				})),
				Player(name='Hannah', character=Slayer()),
				Player(name='Sarah', character=Courtier(night_info={
					1: Courtier.Choice(Vortox)
				})),
				Player(name='Jasmine', character=Mayor()),
			],
			day_events={
				1: [
					DoomsayerCall(caller=Hannah, died=Tim),
					Slayer.Shot(src=Hannah, target=Fraser, died=False),
					DoomsayerCall(caller=You, died=Sarah),
				]
			},
		)

		worlds = world_gen(
			state,
			possible_demons=[Vortox],
			possible_minions=[Spy, ScarletWoman],
			possible_hidden_good=[Lunatic],
			possible_hidden_self=[],
		)

		assert_solutions(self, worlds, solutions=(
			(Dreamer, Clockmaker, Lunatic, Slayer, Spy, Vortox),
		))


	def test_puzzle_13(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gka3js/weekly_puzzle_13_clockblocking/

		You, Jasmine, Oscar, Tim, Sarah, Fraser, Aoife = range(7)

		state = State(
			players=[
				Player(name='You', character=Investigator(night_info={
					1: Investigator.Ping(Sarah, Aoife, ScarletWoman)
				})),
				Player(name='Jasmine', character=Clockmaker(night_info={
					1: Clockmaker.Ping(3)
				})),
				Player(name='Oscar', character=Librarian(night_info={
					1: Librarian.Ping(None)
				})),
				Player(name='Tim', character=Ravenkeeper(night_info={
					2: Ravenkeeper.Ping(Oscar, Librarian)
				})),
				Player(name='Sarah', character=FortuneTeller(night_info={
					1: FortuneTeller.Ping(You, Oscar, demon=False),
					2: FortuneTeller.Ping(You, Jasmine, demon=False),
				})),
				Player(name='Fraser', character=Slayer()),
				Player(name='Aoife', character=Recluse()),
			],
			day_events={
				1: [
					Slayer.Shot(src=Fraser, target=Oscar, died=False),
					Execution(Aoife, died=True)
				],
			},
			night_deaths={
				2: Tim,
			},
		)

		worlds = world_gen(
			state,
			possible_demons=[Imp],
			possible_minions=[Baron, Spy, ScarletWoman, Poisoner],
			possible_hidden_good=[Drunk],
			possible_hidden_self=[Drunk],
		)
		assert_solutions(self, worlds, solutions=((
			Investigator, Clockmaker, Baron, Drunk, FortuneTeller, Imp, Recluse
		),))


	def test_puzzle_21(self):
		# https://www.reddit.com/r/BloodOnTheClocktower/comments/1hpqhai/weekly_puzzle_21_eight_jugglers_juggling/

		You, Fraser, Aoife, Josh, Tim, Matt, Olivia, Oscar = range(8)
		state = State([
			Player(name='You', character=Juggler(
				day_info={1: Juggler.Juggle({Matt: Goblin, Oscar: Goblin})},
				night_info={2: Juggler.Ping(0)},
			)),
			Player(name='Fraser', character=Juggler(
				day_info={1: Juggler.Juggle({Olivia: Juggler, Oscar: Drunk})},
				night_info={2: Juggler.Ping(1)},
			)),
			Player(name='Aoife', character=Juggler(
				day_info={1: Juggler.Juggle({Olivia: Leviathan, Oscar: Leviathan})},
				night_info={2: Juggler.Ping(0)},
			)),
			Player(name='Josh', character=Juggler(
				day_info={1: Juggler.Juggle({Tim: Goblin, Oscar: Juggler})},
				night_info={2: Juggler.Ping(1)},
			)),
			Player(name='Tim', character=Juggler(
				day_info={1: Juggler.Juggle({You: Leviathan, Josh: Juggler})},
				night_info={2: Juggler.Ping(0)},
			)),
			Player(name='Matt', character=Juggler(
				day_info={1: Juggler.Juggle({Josh: Goblin, Tim: Juggler})},
				night_info={2: Juggler.Ping(0)},
			)),
			Player(name='Olivia', character=Juggler(
				day_info={1: Juggler.Juggle({You: Juggler, Aoife: Drunk})},
				night_info={2: Juggler.Ping(2)},
			)),
			Player(name='Oscar', character=Juggler(
				day_info={1: Juggler.Juggle({Josh: Goblin, Matt: Juggler})},
				night_info={2: Juggler.Ping(0)},
			)),
		])

		worlds = world_gen(
			state,
			possible_demons=[Leviathan],
			possible_minions=[Goblin],
			possible_hidden_good=[Drunk],
			possible_hidden_self=[Drunk],
		)

		assert_solutions(self, worlds, solutions=(
			(Juggler, Juggler, Drunk, Juggler, Goblin, 
				Juggler, Juggler, Leviathan),
		))
