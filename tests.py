import unittest

from clockchecker import *


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
        state = State([
            Player('You', claim=Savant, day_info={
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
            }),
            Player('Tim', claim=Knight, night_info={
                1: Knight.Ping(Sula, Anna)
            }),
            Player('Sula', claim=Steward, night_info={
                1: Steward.Ping(Matt)
            }),
            Player('Oscar', claim=Investigator, night_info={
                1: Investigator.Ping(Sula, Anna, Goblin)
            }),
            Player('Matt', claim=Noble, night_info={
                1: Noble.Ping(Tim, Sula, Oscar)
            }),
            Player('Anna', claim=Seamstress, night_info={
                1: Seamstress.Ping(Sula, Oscar, same=False)
            }),
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
            Player('You', claim=Seamstress, night_info={
                1: Seamstress.Ping(Matthew, Sula, same=True)
            }),
            Player('Steph', claim=Knight, night_info={
                1: Knight.Ping(Tim, Sula)
            }),
            Player('Fraser', claim=FortuneTeller, night_info={
                1: FortuneTeller.Ping(Sarah, Anna, demon=False),
                2: FortuneTeller.Ping(You, Fraser, demon=False),
                3: FortuneTeller.Ping(Steph, Sarah, demon=False),
            }),
            Player('Tim', claim=Saint),
            Player('Sarah', claim=Investigator, night_info={
                1: Investigator.Ping(Matthew, Fraser, Goblin)
            }),
            Player('Matthew', claim=Juggler,
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
            ),
            Player('Anna', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(1)
            }),
            Player('Sula', claim=Balloonist, night_info={
                1: Balloonist.Ping(Tim),
                2: Balloonist.Ping(Matthew),
                3: Balloonist.Ping(Steph),
            }),
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
                Player('You', claim=Slayer, day_info= {
                    1: Slayer.Shot(Tom, died=True),
                }),
                Player('Aoife', claim=Chef, night_info={
                    1: Chef.Ping(0)
                }),
                Player('Tom', claim=Recluse),
                Player('Sula', claim=Investigator, night_info={
                    1: Investigator.Ping(You, Aoife, Baron)
                }),
                Player('Matthew', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Aoife, Oscar, Librarian)
                }),
                Player('Oscar', claim=Librarian, night_info={
                    1: Librarian.Ping(None)
                }),
                Player('Josh', claim=Empath, night_info={
                    1: Empath.Ping(0)
                }),
            ],
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
        state = State(players=[
            Player('You', claim=Slayer, day_info={
                1: Slayer.Shot(Anna, died=True)
            }),
            Player('Tim', claim=Librarian, night_info={
                1: Librarian.Ping(You, Hannah, Drunk)
            }),
            Player('Sarah', claim=Investigator, night_info={
                1: Investigator.Ping(Tim, Fraser, ScarletWoman)
            }),
            Player('Hannah', claim=Saint),
            Player('Dan', claim=Chef, night_info={
                1: Chef.Ping(0)
            }),
            Player('Anna', claim=Recluse),
            Player('Matt', claim=Washerwoman, night_info={
                1: Washerwoman.Ping(Tim, Dan, Librarian)
            }),
            Player('Fraser', claim=Empath, night_info={
                1: Empath.Ping(0)
            }),
        ])

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Baron, Spy, Poisoner, ScarletWoman],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )
        assert_solutions(self, worlds, solutions=(
            (Slayer, Librarian, Imp, Spy, Chef, Recluse, Washerwoman, Empath),
        ))

    def test_puzzle_4(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1f823s4/weekly_puzzle_4_the_manyheaded_monster/

        You, Anna, Dan, Fraser, Sarah, Tim, Matt, Hannah = range(8)
        state = State(
            players=[
                Player('You', claim=Investigator, night_info={
                    1: Investigator.Ping(Matt, Hannah, Marionette)
                }),
                Player('Anna', claim=Empath, night_info={
                    1: Empath.Ping(2)
                }),
                Player('Dan', claim=Undertaker, night_info={
                    2: Undertaker.Ping(Anna, Empath)
                }),
                Player('Fraser', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Anna, Tim, demon=True),
                    2: FortuneTeller.Ping(You, Fraser, demon=False),
                    3: FortuneTeller.Ping(You, Sarah, demon=True),
                }),
                Player('Sarah', claim=Librarian, night_info={
                    1: Librarian.Ping(You, Hannah, Drunk)
                }),
                Player('Tim', claim=Recluse),
                Player('Matt', claim=Juggler,
                    day_info={
                        1: Juggler.Juggle({
                            You: Investigator,
                            Dan: LordOfTyphon,
                            Tim: Recluse,
                            Hannah: Dreamer,
                        }
                    )},
                    night_info={2: Juggler.Ping(1)}
                ),
                Player('Hannah', claim=Dreamer, night_info={
                    1: Dreamer.Ping(You, Investigator, LordOfTyphon)
                }),
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
            Player('You', claim=Alsaahir),
            Player('Dan', claim=Noble, night_info={
                1: Noble.Ping(Tom, Anna, Hannah)
            }),
            Player('Tom', claim=Knight, night_info={
                1: Knight.Ping(Dan, Anna)
            }),
            Player('Matt', claim=Investigator, night_info={
                1: Investigator.Ping(Anna, Oscar, Goblin)
            }),
            Player('Anna', claim=Empath, night_info={
                1: Empath.Ping(Dan)
            }),
            Player('Hannah', claim=Steward, night_info={
                1: Steward.Ping(Tom)
            }),
            Player('Oscar', claim=Seamstress, night_info={
                1: Seamstress.Ping(Tom, Hannah, same=False)
            }),
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
            Player('You', claim=Juggler),
            Player('Sarah', claim=Empath, night_info={
                1: Empath.Ping(You)
            }),
            Player('Tim', claim=Seamstress, night_info={
                1: Seamstress.Ping(You, Fraser, same=True)
            }),
            Player('Matthew', claim=Steward, night_info={
                1: Steward.Ping(You)
            }),
            Player('Steph', claim=Investigator, night_info={
                1: Investigator.Ping(Sarah, Fraser, Goblin)
            }),
            Player('Aoife', claim=Noble, night_info={
                1: Noble.Ping(Sarah, Tim, Matthew)
            }),
            Player('Fraser', claim=Knight, night_info={
                1: Knight.Ping(You, Steph)
            }),
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
                Player('You', claim=Librarian, night_info={
                    1: Librarian.Ping(Sula, Fraser, Drunk)
                }),
                Player('Sarah', claim=Saint),
                Player('Tim', claim=Noble, night_info={
                    1: Noble.Ping(Aoife, Sula, Fraser)
                }),
                Player('Dan', claim=Seamstress, night_info={
                    1: Seamstress.Ping(Aoife, Tim, same=False)
                }),
                Player('Aoife', claim=Investigator, night_info={
                    1: Investigator.Ping(Dan, Matthew, Marionette)
                }),
                Player('Sula', claim=Juggler,
                    day_info={
                        1: Juggler.Juggle({
                            You: Librarian,
                            Tim: Marionette,
                            Dan: Vortox,
                            Fraser: Drunk,
                            Matthew: Pukka,
                        })
                    },
                    night_info={2: Juggler.Ping(2)}
                ),
                Player('Steph', claim=Knight, night_info={
                    1: Knight.Ping(Sarah, Dan)
                }),
                Player('Fraser', claim=Empath, night_info={
                    1: Empath.Ping(0)
                }),
                Player('Matthew', claim=Steward, night_info={
                    1: Steward.Ping(Dan)
                }),
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
            Player('You', claim=Savant, day_info={
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
            }),
            Player('Fraser', claim=VillageIdiot, night_info={
                1: VillageIdiot.Ping(Sarah, is_evil=False),
                2: VillageIdiot.Ping(Aoife, is_evil=False),
                3: VillageIdiot.Ping(You, is_evil=False),
            }),
            Player('Sarah', claim=FortuneTeller, night_info={
                1: FortuneTeller.Ping(Oscar, Aoife, demon=False),
                2: FortuneTeller.Ping(You, Sarah, demon=True),
                3: FortuneTeller.Ping(Fraser, Tim, demon=False),
            }),
            Player('Oscar', claim=Investigator, night_info={
                1: Investigator.Ping(Fraser, Steph, Goblin),
            }),
            Player('Anna', claim=Juggler,
                day_info={1: Juggler.Juggle({You: Savant, Tim: VillageIdiot})},
                night_info={2: Juggler.Ping(1)}
            ),
            Player('Aoife', claim=Shugenja, night_info={
                1: Shugenja.Ping(clockwise=False)
            }),
            Player('Steph', claim=Dreamer, night_info={
                1: Dreamer.Ping(Sarah, FortuneTeller, Leviathan),
                2: Dreamer.Ping(You, Savant, Goblin),
                3: Dreamer.Ping(Fraser, Mutant, Goblin),
            }),
            Player('Tim', claim=VillageIdiot, night_info={
                1: VillageIdiot.Ping(Anna, is_evil=False),
                2: VillageIdiot.Ping(Sarah, is_evil=False),
                3: VillageIdiot.Ping(You, is_evil=False),
            }),
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

    def test_puzzle_8(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1ftqc28/weekly_puzzle_8_the_stitchup/

        You, Josh, Steph, Anna, Tim, Matthew, Fraser = range(7)
        state = State([
            Player('You', claim=Seamstress, night_info={
                1: Seamstress.Ping(Anna, Matthew, same=False)
            }),
            Player('Josh', claim=Seamstress, night_info={
                1: Seamstress.Ping(Anna, Tim, same=False)
            }),
            Player('Steph', claim=Seamstress, night_info={
                1: Seamstress.Ping(Tim, Matthew, same=False)
            }),
            Player('Anna', claim=Seamstress, night_info={
                1: Seamstress.Ping(Josh, Matthew, same=False)
            }),
            Player('Tim', claim=Seamstress, night_info={
                1: Seamstress.Ping(You, Josh, same=False)
            }),
            Player('Matthew', claim=Seamstress, night_info={
                1: Seamstress.Ping(Steph, Fraser, same=False)
            }),
            Player('Fraser', claim=Seamstress, night_info={
                1: Seamstress.Ping(Steph, Anna, same=False)
            }),
        ])

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner],
            possible_hidden_good=[],
            possible_hidden_self=[],
        )

        assert_solutions(self, worlds, solutions=(
            (Seamstress, Imp, Poisoner) +  (Seamstress,) * 4,
            (Seamstress, Poisoner, Imp) +  (Seamstress,) * 4,
        ))

    def test_puzzle_9(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1fz4jqe/weekly_puzzle_9_the_new_acrobat/

        You, Fraser, Oscar, Josh, Anna, Sula, Hannah = range(7)
        state = State(
            players=[
                Player('You', claim=Acrobat, night_info={
                    2: Acrobat.Choice(Fraser),
                    3: Acrobat.Choice(Josh),
                }),
                Player('Fraser', claim=Balloonist, night_info={
                    1: Balloonist.Ping(Oscar),
                    2: Balloonist.Ping(Anna),
                    3: Balloonist.Ping(You),
                }),
                Player('Oscar', claim=Gossip, day_info={
                    1: Gossip.Gossip(IsCategory(Fraser, DEMON)),
                    2: Gossip.Gossip(IsCategory(Anna, DEMON)),
                }),
                Player('Josh', claim=Knight, night_info={
                    1: Knight.Ping(Fraser, Oscar)
                }),
                Player('Anna', claim=Gambler, night_info={
                    2: Gambler.Gamble(Sula, Goblin),
                    3: Gambler.Gamble(You, Drunk),
                }),
                Player('Sula', claim=Juggler, day_info={
                    1: Juggler.Juggle({
                        You: Goblin,
                        Oscar: Gossip,
                        Josh: Knight,
                        Anna: Imp,
                    })
                }),
                Player('Hannah', claim=Steward, night_info={
                    1: Steward.Ping(Oscar)
                }),
            ],
            night_deaths={
                2: Sula,
                3: [You, Josh, Anna]
            },
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp, Po],
            possible_minions=[Goblin],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )
        
        assert_solutions(self, worlds, solutions=(
           (Acrobat, Balloonist, Gossip, Drunk, Imp, Juggler, Goblin),
        ))

        
    def test_puzzle_10(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1g49r8j/weekly_puzzle_10_dont_overcook_it

        You, Matthew, Dan, Tom, Sula, Fraser, Josh = range(7)
        state = State(
            players=[
                Player('You', claim=Slayer, day_info={
                    2: Slayer.Shot(Fraser, died=False)
                }),
                Player('Matthew', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Josh, Imp)
                }),
                Player('Dan', claim=Undertaker, night_info={
                    2: Undertaker.Ping(Josh, Poisoner)
                }),
                Player('Tom', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Tom, Sula, demon=False),
                    2: FortuneTeller.Ping(Tom, Josh, demon=True),
                }),
                Player('Sula', claim=Chef, night_info={
                    1: Chef.Ping(0)
                }),
                Player('Fraser', claim=Recluse),
                Player('Josh', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Dan, Sula, Undertaker)
                }),
            ],
            day_events={1: Execution(Josh)},
            night_deaths={2: Matthew},
        )
        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner, Spy, Baron, ScarletWoman],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )

        assert_solutions(self, worlds, solutions=(
            (Slayer, Ravenkeeper, Imp, FortuneTeller, Chef, Poisoner, 
                Washerwoman),
        ))


    def test_puzzle_12a(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1gexyoq/weekly_puzzle_12a_12b_thunderstruck

        You, Tim, Fraser, Hannah, Sarah, Jasmine = range(6)
        state = State(
            players=[
                Player('You', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Sarah, Lunatic, ScarletWoman)
                }),
                Player('Tim', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(2)
                }),
                Player('Fraser', claim=Empath, night_info={
                    1: Empath.Ping(0)
                }),
                Player('Hannah', claim=Slayer),
                Player('Sarah', claim=Courtier, night_info={
                    1: Courtier.Choice(Vortox)
                }),
                Player('Jasmine', claim=Mayor),
            ],
            day_events={
                1: [
                    Doomsayer.Call(player=Hannah, died=Tim),
                    Slayer.Shot(player=Hannah, target=Fraser, died=False),
                    Doomsayer.Call(player=You, died=Sarah),
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


    def test_puzzle_12b(self):
        You, Oscar, Anna, Josh, Fraser, Tom, Aoife, Steph = range(8)

        state = State(
            players=[
                Player('You', claim=Librarian, night_info={
                    1: Librarian.Ping(Fraser, Steph, Lunatic)
                }),
                Player('Oscar', claim=Investigator, night_info={
                    1: Investigator.Ping(Josh, Fraser, Spy)
                }),
                Player('Anna', claim=Empath, night_info={
                    1: Empath.Ping(1)
                }),
                Player('Josh', claim=Mayor),
                Player('Fraser', claim=Slayer),
                Player('Tom', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Steph, Lunatic, Spy)
                }),
                Player('Aoife', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(3)
                }),
                Player('Steph', claim=Courtier, night_info={
                    1: Courtier.Choice(Vortox)
                }),
            ],
            day_events={
                1: [
                    Doomsayer.Call(player=Tom, died=Josh),
                    Slayer.Shot(player=Fraser, target=Steph, died=False),
                    Doomsayer.Call(player=Steph, died=Oscar),
                    Doomsayer.Call(player=Fraser, died=Aoife),
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
            (Librarian, Vortox, Lunatic, Mayor, Slayer, Dreamer, Clockmaker, 
                ScarletWoman),
        ))


    def test_puzzle_13(self):
        You, Jasmine, Oscar, Tim, Sarah, Fraser, Aoife = range(7)
        state = State(
            players=[
                Player('You', claim=Investigator, night_info={
                    1: Investigator.Ping(Sarah, Aoife, ScarletWoman)
                }),
                Player('Jasmine', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(3)
                }),
                Player('Oscar', claim=Librarian, night_info={
                    1: Librarian.Ping(None)
                }),
                Player('Tim', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Oscar, Librarian)
                }),
                Player('Sarah', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(You, Oscar, demon=False),
                    2: FortuneTeller.Ping(You, Jasmine, demon=False),
                }),
                Player('Fraser', claim=Slayer, day_info={
                    2: Slayer.Shot(Oscar, died=False),
                }),
                Player('Aoife', claim=Recluse),
            ],
            day_events={1: Execution(Aoife, died=True)},
            night_deaths={2: Tim,},
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

    def test_puzzle_14(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1gpo1xo/weekly_puzzle_14_new_super_marionette_bros/

        You, Danielle, Gwilym, Brett, Rob, Lav, Lydia = range(7)
        state = State(
            players=[
                Player('You', claim=Slayer),
                Player('Danielle', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Rob, Lav, Empath)
                }),
                Player('Gwilym', claim=Undertaker, night_info={
                    2: Undertaker.Ping(You, Slayer)
                }),
                Player('Brett', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Danielle, Gwilym, demon=False)
                }),
                Player('Rob', claim=Empath, night_info={
                    1: Empath.Ping(0),
                    2: Empath.Ping(0),
                }),
                Player('Lav', claim=Chef, night_info={
                    1: Chef.Ping(1)
                }),
                Player('Lydia', claim=Investigator, night_info={
                    1: Investigator.Ping(You, Danielle, Marionette)
                }),
            ],
            day_events={
                1: [
                    Slayer.Shot(player=You, target=Lydia, died=False),
                    Execution(You),
                ]
            },
            night_deaths={2: Brett},
        )
        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner, Spy, ScarletWoman, Marionette],
            possible_hidden_good=[],
            possible_hidden_self=[Marionette],
        )
        assert_solutions(self, worlds, solutions=((
            Slayer, Washerwoman, Undertaker, 
            FortuneTeller, Empath, Imp, Poisoner
        ),))

    def test_puzzle_15(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1gv12ck/weekly_puzzle_15_wake_up_and_choose_violets

        You, Oscar, Sarah, Hannah, Fraser, Aoife, Adam, Jasmine = range(8)
        state = State(
            players=[
                Player('You', claim=Savant, day_info={
                    1: Savant.Ping(
                        ExactlyN(N=3, args=[
                            IsInPlay(Clockmaker),
                            IsInPlay(Klutz),
                            IsInPlay(Juggler),
                            IsInPlay(Vortox),
                        ]),
                        LongestRowOfTownsfolk(5),
                    )
                }),
                Player('Oscar', claim=Klutz),
                Player('Sarah', claim=Juggler, 
                    day_info={
                        1: Juggler.Juggle({
                            You: Savant,
                            Hannah: SnakeCharmer,
                            Fraser: Clockmaker,
                            Aoife: Seamstress,
                            Jasmine: SnakeCharmer,
                        })
                    },
                    night_info={2: Juggler.Ping(3)},
                ),
                Player('Hannah', claim=SnakeCharmer, night_info={
                    1: [
                        SnakeCharmer.Choice(Sarah),
                        EvilTwin.Is(Jasmine),
                    ],
                    2: SnakeCharmer.Choice(Oscar),
                    3: SnakeCharmer.Choice(Aoife),
                }),
                Player('Fraser', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(3)
                }),
                Player('Aoife', claim=Seamstress, night_info={
                    1: Seamstress.Ping(Oscar, Hannah, same=False)
                }),
                Player('Adam', claim=Artist, night_info={
                    1: Artist.Ping(
                        ~IsCharacter(You, Vortox)
                        & ~IsCharacter(Oscar, Vortox)
                        & ~IsCharacter(Sarah, Vortox) 
                    )
                }),
                Player('Jasmine', claim=SnakeCharmer, night_info={
                    1: [
                        SnakeCharmer.Choice(Fraser),
                        EvilTwin.Is(Hannah),
                    ],
                    2: SnakeCharmer.Choice(Aoife),
                    3: SnakeCharmer.Choice(Adam),
                }),
            ],
            day_events={
                1: Execution(You),
                2: [
                    Execution(Oscar),
                    Klutz.Choice(player=Oscar, choice=Sarah),
                ],
            },
        )

        worlds = world_gen(
            state,
            possible_demons=[NoDashii, Vortox],
            possible_minions=[EvilTwin],
            possible_hidden_good=[Mutant],
            possible_hidden_self=[],
        )
        
        assert_solutions(self, worlds, solutions=((
            Savant, Klutz, Juggler, SnakeCharmer, Clockmaker,
            Seamstress, Vortox, EvilTwin
        ),))

    def test_puzzle_16(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1h0f8se/weekly_puzzle_16_who_watches_the_watchmen/

        You, Olivia, Jasmine, Fraser, Oscar, Hannah, Sarah, Tim = range(8)
        state = State(
            players=[
                Player('You', claim=Saint),
                Player('Olivia', claim=Empath, night_info={
                    1: Empath.Ping(0),
                    2: Empath.Ping(1),
                }),
                Player('Jasmine', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Hannah, Tim, demon=False),
                    2: FortuneTeller.Ping(Olivia, Tim, demon=False),
                    3: FortuneTeller.Ping(Sarah, Jasmine, demon=False),
                }),
                Player('Fraser', claim=NightWatchman, night_info={
                    1: NightWatchman.Choice(Tim, confirmed=False)
                }),
                Player('Oscar', claim=Recluse),
                Player('Hannah', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Oscar, Tim, Chef)
                }),
                Player('Sarah', claim=Investigator, night_info={
                    1: Investigator.Ping(Olivia, Hannah, Poisoner)
                }),
                Player('Tim', claim=Chef, night_info={
                    1: Chef.Ping(1)
                }),
            ],
            day_events={1: Execution(Hannah),  2: Execution(Fraser)},
            night_deaths={2: You, 3: Olivia},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner, Spy, ScarletWoman, Baron],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[],
        )

        assert_solutions(self, worlds, solutions=((
            Saint, Empath, FortuneTeller, Poisoner, Imp, Washerwoman, 
            Investigator, Chef
        ),))

    def test_puzzle_17(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1h5sgc7/weekly_puzzle_17_the_missing_piece/

        You, Adam, Steph, Fraser, Sarah, Sula, Hannah, Tom = range(8)
        state = State(
            players=[
                Player('You', claim=Puzzlemaster),
                Player('Adam', claim=Chef, night_info={
                    1: Chef.Ping(0),
                }),
                Player('Steph', claim=Empath, night_info={
                    1: Empath.Ping(0),
                }),
                Player('Fraser', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Hannah, Tom, demon=False),
                    2: FortuneTeller.Ping(Tom, Fraser, demon=True),
                    3: FortuneTeller.Ping(You, Sarah, demon=True),
                }),
                Player('Sarah', claim=Undertaker, night_info={
                    2: Undertaker.Ping(Steph, Empath),
                    3: Undertaker.Ping(Sula, Washerwoman),
                }),
                Player('Sula', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Sarah, Hannah, Undertaker)
                }),
                Player('Hannah', claim=Investigator, night_info={
                    1: Investigator.Ping(Sarah, Fraser, ScarletWoman)
                }),
                Player('Tom', claim=Slayer),
            ],
            day_events={
                1: Execution(Steph),
                2: Execution(Sula),
                3: Execution(Sarah),
            },
            night_deaths={2: Adam, 3: Hannah},
        )

        worlds = list(world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[ScarletWoman],
            possible_hidden_good=[],
            possible_hidden_self=[],
        ))

        assert_solutions(self, worlds, solutions=(
            (Puzzlemaster, Imp, Empath, ScarletWoman, Undertaker, Washerwoman,
                 Investigator, Slayer),
            (Puzzlemaster, Chef, Empath, Imp, Undertaker, Washerwoman,
                 ScarletWoman, Slayer),
            (Puzzlemaster, Chef, Empath, ScarletWoman, Undertaker, Washerwoman,
                 Imp, Slayer),
            (Puzzlemaster, Chef, Empath, ScarletWoman, Undertaker, Washerwoman,
                 Investigator, Imp),
        ))
        for world in worlds:
            self.assertEqual(world.players[You].character.puzzle_drunk, Steph)

    def test_puzzle_19(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1hgdsmp/weekly_puzzle_19_he_could_be_you_he_could_be_me/

        You, Fraser, Oscar, Jasmine, Olivia, Matt, Sula, Aoife = range(8)
        state = State(
            players=[
                Player('You', claim=Librarian, night_info={
                    1: Librarian.Ping(Fraser, Matt, Drunk)
                }),
                Player('Fraser', claim=Saint),
                Player('Oscar', claim=Recluse),
                Player('Jasmine', claim=Slayer),
                Player('Olivia', claim=Undertaker, night_info={
                    2: Undertaker.Ping(You, Baron),
                }),
                Player('Matt', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Fraser, Saint)
                }),
                Player('Sula', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Fraser, Olivia, Undertaker)
                }),
                Player('Aoife', claim=Empath, night_info={
                    1: Empath.Ping(0),
                    2: Empath.Ping(1),
                }),
            ],
            day_events={
                1: Execution(You),
                2: Slayer.Shot(player=Jasmine, target=Oscar, died=True),
            },
            night_deaths={2: Matt},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner, Spy, Baron, ScarletWoman],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )

        assert_solutions(self, worlds, solutions=(
            (Librarian, Spy, Recluse, Slayer, Imp, 
                Ravenkeeper, Washerwoman, Empath),
        ))
        
    def test_puzzle_20(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1hlgh1w/weekly_puzzle_20_the_three_wise_men/

        You, Caspar, Joseph, Melchior, Mary, Balthazar, Gabriel = range(7)
        state = State(
            players=[
                Player('You', claim=Investigator, night_info={
                    1: Investigator.Ping(Mary, Gabriel, Baron)
                }),
                Player('Caspar', claim=VillageIdiot, night_info={
                    1: VillageIdiot.Ping(Mary, is_evil=True),
                    2: VillageIdiot.Ping(Joseph, is_evil=True),
                }),
                Player('Joseph', claim=Saint),
                Player('Melchior', claim=VillageIdiot, night_info={
                    1: VillageIdiot.Ping(Balthazar, is_evil=True),
                    2: VillageIdiot.Ping(Mary, is_evil=True),
                }),
                Player('Mary', claim=Virgin, day_info={
                    1: Virgin.NominatedWithoutExecution(Balthazar)
                }),
                Player('Balthazar', claim=VillageIdiot, night_info={
                    1: VillageIdiot.Ping(Joseph, is_evil=True),
                    2: VillageIdiot.Ping(Caspar, is_evil=True),
                }),
                Player('Gabriel', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Balthazar, Drunk)
                }),
            ],
            day_events={1: Execution(You)},
            night_deaths={2: Gabriel},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Baron, Spy, Poisoner, ScarletWoman],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )

        assert_solutions(self, worlds, solutions=((
            Investigator, VillageIdiot, Saint, VillageIdiot, Baron, Imp, Drunk,
        ),))

    def test_puzzle_21(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1hpqhai/weekly_puzzle_21_eight_jugglers_juggling/

        You, Fraser, Aoife, Josh, Tim, Matt, Olivia, Oscar = range(8)
        state = State([
            Player('You', claim=Juggler,
                day_info={1: Juggler.Juggle({Matt: Goblin, Oscar: Goblin})},
                night_info={2: Juggler.Ping(0)},
            ),
            Player('Fraser', claim=Juggler,
                day_info={1: Juggler.Juggle({Olivia: Juggler, Oscar: Drunk})},
                night_info={2: Juggler.Ping(1)},
            ),
            Player('Aoife', claim=Juggler,
                day_info={1: Juggler.Juggle({Olivia: Leviathan, Oscar: Leviathan})},
                night_info={2: Juggler.Ping(0)},
            ),
            Player('Josh', claim=Juggler,
                day_info={1: Juggler.Juggle({Tim: Goblin, Oscar: Juggler})},
                night_info={2: Juggler.Ping(1)},
            ),
            Player('Tim', claim=Juggler,
                day_info={1: Juggler.Juggle({You: Leviathan, Josh: Juggler})},
                night_info={2: Juggler.Ping(0)},
            ),
            Player('Matt', claim=Juggler,
                day_info={1: Juggler.Juggle({Josh: Goblin, Tim: Juggler})},
                night_info={2: Juggler.Ping(0)},
            ),
            Player('Olivia', claim=Juggler,
                day_info={1: Juggler.Juggle({You: Juggler, Aoife: Drunk})},
                night_info={2: Juggler.Ping(2)},
            ),
            Player('Oscar', claim=Juggler,
                day_info={1: Juggler.Juggle({Josh: Goblin, Matt: Juggler})},
                night_info={2: Juggler.Ping(0)},
            ),
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

    def test_puzzle_22(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1hvum3b/weekly_puzzle_22_one_in_the_chamber/

        You, Anna, Aoife, Sarah, Tim, Fraser, Oscar, Steph = range(8)
        state = State(
            players= [
                Player('You', claim=Chambermaid, night_info={
                    1: Chambermaid.Ping(Anna, Steph, 2),
                    2: Chambermaid.Ping(Tim, Steph, 0),
                    3: Chambermaid.Ping(Tim, Steph, 1),
                }),
                Player('Anna', claim=Investigator, night_info={
                    1: Investigator.Ping(Aoife, Steph, Baron),
                }),
                Player('Aoife', claim=Slayer, day_info={
                    3: Slayer.Shot(Tim, died=False),
                }),
                Player('Sarah', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Steph, Washerwoman),
                }),
                Player('Tim', claim=Saint),
                Player('Fraser', claim=Recluse),
                Player('Oscar', claim=Librarian, night_info={
                    1: Librarian.Ping(You, Sarah, Drunk),
                }),
                Player('Steph', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(You, Aoife, Chambermaid),
                }),
            ],
            day_events={1: Execution(Oscar), 2: Execution(Fraser)},
            night_deaths={2: Sarah, 3: Anna},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Baron, Spy, Poisoner, ScarletWoman],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )

        assert_solutions(self, worlds, solutions=((
            Drunk, Investigator, Slayer, Imp, Saint, Recluse, Librarian, Baron
        ),))

    def test_puzzle_23(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1i199yv/weekly_puzzle_23_goblincore/

        You, Hannah, Matt, Tim, Aoife, Fraser, Tom, Sula = range(8)
        state = State(
            players= [
                Player('You', claim=Chef, night_info={
                    1: Chef.Ping(0),
                }),
                Player('Hannah', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Tom, Sula, Librarian),
                }),
                Player('Matt', claim=Investigator, night_info={
                    1: Investigator.Ping(Aoife, Fraser, Goblin),
                }),
                Player('Tim', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Hannah, Tim, demon=False),
                    2: FortuneTeller.Ping(Fraser, Sula, demon=True),
                }),
                Player('Aoife', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Matt, Investigator),
                }),
                Player('Fraser', claim=Goblin),
                Player('Tom', claim=Librarian, night_info={
                    1: Librarian.Ping(Matt, Fraser, Lunatic),
                }),
                Player('Sula', claim=Slayer, day_info={
                    2: Slayer.Shot(Matt, died=False),
                }),
            ],
            night_deaths={2: Aoife},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Goblin],
            possible_hidden_good=[Lunatic],
            possible_hidden_self=[],
        )

        assert_solutions(self, worlds, solutions=(
            (Chef, Washerwoman, Investigator, FortuneTeller,
             Goblin, Lunatic, Librarian, Imp),
        ))

    def test_puzzle_24(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1i6m0ww/weekly_puzzle_24_the_ultimate_blunder/

        You, Olivia, Steph, Fraser, Sula, Oscar, Adam, Josh = range(8)
        state = State(
            players= [
                Player('You', claim=Investigator, night_info={
                    1: Investigator.Ping(Olivia, Josh, Poisoner),
                }),
                Player('Olivia', claim=Klutz, day_info={
                    2: Klutz.Choice(Adam),
                }),
                Player('Steph', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Steph, Adam, demon=False),
                    2: FortuneTeller.Ping(Steph, Adam, demon=True),
                }),
                Player('Fraser', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Olivia, Sula, Virgin),
                }),
                Player('Sula', claim=Virgin),
                Player('Oscar', claim=Librarian, night_info={
                    1: Librarian.Ping(You, Olivia, Klutz),
                }),
                Player('Adam', claim=Chef, night_info={
                    1: Chef.Ping(1),
                }),
                Player('Josh', claim=Empath, night_info={
                    1: Empath.Ping(1),
                    2: Empath.Ping(0),
                }),
            ],
            day_events={1: [
                Virgin.NominatedWithoutExecution(player=Sula, nominator=Adam),
                Execution(You),
            ]},
            night_deaths={2: Olivia},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )

        assert_solutions(self, worlds, solutions=(
            (Investigator, Klutz, FortuneTeller, Washerwoman, Virgin,
             Librarian, Imp, Poisoner),
        ))


    def test_puzzle_26(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1ihl8vs/weekly_puzzle_26_a_major_problem/

        You, Olivia, Dan, Tom, Matthew, Josh, Sula, Fraser = range(8)
        state = State(
            players=[
                Player('You', claim=Empath, night_info={
                    1: Empath.Ping(0)
                }),
                Player('Olivia', claim=Saint),
                Player('Dan', claim=Slayer, day_info={
                    2: Slayer.Shot(Matthew, died=False),
                }),
                Player('Tom', claim=Recluse),
                Player('Matthew', claim=Librarian, night_info={
                    1: Librarian.Ping(You, Josh, Drunk)
                }),
                Player('Josh', claim=Soldier),
                Player('Sula', claim=Undertaker, night_info={
                    2: Undertaker.Ping(You, Empath),
                    3: Undertaker.Ping(Dan, Slayer),
                }),
                Player('Fraser', claim=Chef, night_info={
                    1: Chef.Ping(2)
                }),
            ],
            day_events={1: Execution(You), 2: Execution(Dan)},
            night_deaths={2: Josh, 3: Olivia},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner, Spy, Baron, ScarletWoman],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )

        assert_solutions(self, worlds, solutions=(
            (Empath, Saint, Slayer, Imp, Poisoner, Soldier, Undertaker, Chef),
        ))

    def test_puzzle_28(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1iu1vxo/weekly_puzzle_28_a_study_in_scarlet/

        You, Matt, Fraser, Aoife, Adam, Oscar, Olivia, Sarah = range(8)
        state = State(
            players=[
                Player('You', claim=Chambermaid, night_info={
                    1: Chambermaid.Ping(Adam, Sarah, 1)
                }),
                Player('Matt', claim=Juggler,
                day_info={1: Juggler.Juggle({Fraser: Undertaker, Oscar: NoDashii})},
                night_info={2: Juggler.Ping(2)},
                ),
                Player('Fraser', claim=Undertaker, night_info={
                    2: Undertaker.Ping(Aoife, NoDashii)
                }),
                Player('Aoife', claim=Librarian, night_info={
                    1: Librarian.Ping(Matt, Adam, Drunk),
                }),
                Player('Adam', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(4)
                }),
                Player('Oscar', claim=Empath, night_info={
                    1: Empath.Ping(1),
                    2: Empath.Ping(2),
                    3: Empath.Ping(1),
                }),		
                Player('Olivia', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Olivia, Sarah, demon=False),
                    2: FortuneTeller.Ping(Olivia, Aoife, demon=False),
                    3: FortuneTeller.Ping(Matt, Oscar, demon=False),
                }),
                Player('Sarah', claim=Oracle, night_info={
                    2: Oracle.Ping(1)
                }),
            ],
            day_events={1: Execution(Adam), 2: Execution(Aoife)},
            night_deaths={2: You, 3: Sarah},
        )

        worlds = world_gen(
            state,
            possible_demons=[Pukka, NoDashii],
            possible_minions=[ScarletWoman],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )
        
        assert_solutions(self, worlds, solutions=(
            (Chambermaid, Drunk, ScarletWoman, Librarian, Clockmaker,
                Empath, NoDashii, Oracle),
        ))

    def test_puzzle_29(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1ixykmz/weekly_puzzle_29_a_dreamer_im_not_the_only_one/

        You, Jasmine, Adam, Sarah, Sula, Steph, Hannah, Fraser = range(8)
        state = State(
            players= [
                Player('You', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Jasmine, Dreamer, Poisoner),
                }),
                Player('Jasmine', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Sula, Drunk, Imp),
                }),
                Player('Adam', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Jasmine, Dreamer, Imp),
                    2: Dreamer.Ping(Fraser, Dreamer, Imp),
                }),
                Player('Sarah', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Jasmine, Drunk, Poisoner),
                    2: Dreamer.Ping(Adam, Drunk, Imp),
                }),
                Player('Sula', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Jasmine, Drunk, Poisoner),
                    2: Dreamer.Ping(Hannah, Drunk, Poisoner),
                }),
                Player('Steph', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Jasmine, Drunk, Imp),
                    2: Dreamer.Ping(Sula, Dreamer, Poisoner),
                }),
                Player('Hannah', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Adam, Drunk, Poisoner),
                    2: Dreamer.Ping(Sula, Drunk, Imp),
                }),
                Player('Fraser', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Hannah, Drunk, Imp),
                    2: Dreamer.Ping(Jasmine, Drunk, Poisoner),
                }),

            ],
            day_events={1: Execution(Jasmine)},
            night_deaths={2: You},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )
        
        assert_solutions(self, worlds, solutions=(
            (Dreamer, Poisoner, Imp, Dreamer, Dreamer, Dreamer, Drunk, Dreamer),
        ))
        
    def test_puzzle_30left(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1j46gtl/weekly_puzzle_30_which_is_the_atheist_game/

        Finn, Louisa, Shan, Ben, Owen, Lydia = range(6)
        state = State(players=[
            Player('Finn', claim=Atheist),
            Player('Louisa', claim=Knight, night_info={
                1: Knight.Ping(Lydia, Shan)
            }),
            Player('Shan', claim=Artist, day_info={
                1: Artist.Ping(IsCharacter(Louisa, Drunk))
            }),
            Player('Ben', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(3),
            }),
            Player('Owen', claim=Noble, night_info={
                1: Noble.Ping(Lydia, Louisa, Shan),
            }),
            Player('Lydia', claim=Seamstress, night_info={
                1: Seamstress.Ping(Finn, Ben, same=True)
            }),
        ])

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Spy],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )
        
        assert_solutions(self, worlds, solutions=(
            (Drunk, Spy, Artist, Clockmaker, Imp, Seamstress),
        ))
  
    def test_puzzle_30right(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1j46gtl/weekly_puzzle_30_which_is_the_atheist_game/

        Lav, Oli, Callum, Sarah, Max, Erika = range(6)
        state = State(players=[
            Player('Lav', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(3),
            }),
            Player('Oli', claim=Atheist),
            Player('Callum', claim=Knight, night_info={
                1: Knight.Ping(Lav, Max)
            }),
            Player('Sarah', claim=Seamstress, night_info={
                1: Seamstress.Ping(Oli, Callum, same=True)
            }),
            Player('Max', claim=Artist, day_info={
                1: Artist.Ping(IsCharacter(Erika, Drunk))
            }),
            Player('Erika', claim=Noble, night_info={
                1: Noble.Ping(Lav, Callum, Sarah),
            }),
        ])

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Spy],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )
        self.assertEqual(len(list(worlds)), 0)  # Atheist game! TODO: return the Atheist world

        
    def test_puzzle_31(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1j8ub5q/weekly_puzzle_31_no_your_other_left/

        You, Aoife, Tim, Adam, Fraser, Sarah, Olivia = range(7)
        state = State(
            players= [
                Player('You', claim=Chef, night_info={
                    1: Chef.Ping(1),
                }),
                Player('Aoife', claim=Empath, night_info={
                    1: Empath.Ping(0),
                    2: Empath.Ping(1),
                    3: Empath.Ping(1),
                }),
                Player('Tim', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Olivia, Imp),
                }),
                Player('Adam', claim=Investigator, night_info={
                    1: Investigator.Ping(Aoife, Fraser, Spy),
                }),
                Player('Fraser', claim=Recluse),
                Player('Sarah', claim=Undertaker, night_info={
                    2: Undertaker.Ping(You, Spy),
                }),
                Player('Olivia', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Aoife, Tim, demon=False),
                    2: FortuneTeller.Ping(Aoife, Olivia, demon=False),
                }),
            ],
            day_events={1: Execution(You), 2: Execution(Sarah)},
            night_deaths={2: Tim, 3: Olivia},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner, Spy, Baron, ScarletWoman],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )

        assert_solutions(self, worlds, solutions=(
            (Chef, Empath, Drunk, Imp, Recluse, Baron, FortuneTeller),
        ))


    def test_puzzle_32(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1je8z17/weekly_puzzle_32_prepare_for_juggle_and_make_it/

        You, Matthew, Olivia, Sula, Dan, Fraser, Jasmine, Tim = range(8)
        state = State(
            players= [
                Player('You', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Sula, Drunk, Imp),
                }),
                Player('Matthew', claim=Juggler, 
                    day_info={
                        1: Juggler.Juggle({
                            You: Imp,
                            Dan: Drunk,
                            Jasmine: Baron,
                            Tim: FortuneTeller,
                        })
                    },
                    night_info={2: Juggler.Ping(0)},
                ),
                Player('Olivia', claim=Recluse),
                Player('Sula', claim=Empath, night_info={
                    1: Empath.Ping(1),
                    2: Empath.Ping(1),
                    3: Empath.Ping(0),
                }),
                Player('Dan', claim=Juggler,
                    day_info={
                        1: Juggler.Juggle({
                            You: Dreamer,
                            Fraser: Poisoner,
                            Tim: Baron,
                        })
                    },
                    night_info={2: Juggler.Ping(0)},
                ),
                Player('Fraser', claim=Saint),
                Player('Jasmine', claim=Undertaker, night_info={
                    2: Undertaker.Ping(You, Dreamer),
                    3: Undertaker.Ping(Dan, Juggler),
                }),
                Player('Tim', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Matthew, Fraser, demon=False),
                }),
            ],
            day_events={1: Execution(You), 2: Execution(Dan)},
            night_deaths={2: Tim, 3: Fraser},
        )

        worlds = world_gen(
            state,
            possible_demons=[Imp],
            possible_minions=[Poisoner, Baron],
            possible_hidden_good=[Drunk],
            possible_hidden_self=[Drunk],
        )

        assert_solutions(self, worlds, solutions=(
            (Dreamer, Poisoner, Imp, Empath, Juggler, Saint, Undertaker, 
             FortuneTeller),
        ))