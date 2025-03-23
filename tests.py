from dataclasses import dataclass
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

        # This puzzle requires a custom method for one of the savant statements
        class DrunkBetweenTownsfolk(Info):
            def __call__(self, state: State, src: PlayerID) -> STBool:
                N = len(state.players)
                result = FALSE
                for player in range(len(state.players)):
                    found_drunk = IsCharacter(player, Drunk)(state, src)
                    if found_drunk is FALSE:  # Allow MAYBE
                        continue
                    tf_neighbours = (
                        IsCategory((player - 1) % N, TOWNSFOLK)(state, src) & 
                        IsCategory((player + 1) % N, TOWNSFOLK)(state, src)
                    )
                    result |= found_drunk & tf_neighbours
                return result

        You, Tim, Sula, Oscar, Matt, Anna = range(6)
        state = State([
            Player(name='You', claim=Savant, day_info={
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
            Player(name='Tim', claim=Knight, night_info={
                1: Knight.Ping(Sula, Anna)
            }),
            Player(name='Sula', claim=Steward, night_info={
                1: Steward.Ping(Matt)
            }),
            Player(name='Oscar', claim=Investigator, night_info={
                1: Investigator.Ping(Sula, Anna, Goblin)
            }),
            Player(name='Matt', claim=Noble, night_info={
                1: Noble.Ping(Tim, Sula, Oscar)
            }),
            Player(name='Anna', claim=Seamstress, night_info={
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
            Player(name='You', claim=Seamstress, night_info={
                1: Seamstress.Ping(Matthew, Sula, same=True)
            }),
            Player(name='Steph', claim=Knight, night_info={
                1: Knight.Ping(Tim, Sula)
            }),
            Player(name='Fraser', claim=FortuneTeller, night_info={
                1: FortuneTeller.Ping(Sarah, Anna, demon=False),
                2: FortuneTeller.Ping(You, Fraser, demon=False),
                3: FortuneTeller.Ping(Steph, Sarah, demon=False),
            }),
            Player(name='Tim', claim=Saint),
            Player(name='Sarah', claim=Investigator, night_info={
                1: Investigator.Ping(Matthew, Fraser, Goblin)
            }),
            Player(name='Matthew', claim=Juggler,
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
            Player(name='Anna', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(1)
            }),
            Player(name='Sula', claim=Balloonist, night_info={
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
                Player(name='You', claim=Slayer, day_info= {
                    1: Slayer.Shot(Tom, died=True),
                }),
                Player(name='Aoife', claim=Chef, night_info={
                    1: Chef.Ping(0)
                }),
                Player(name='Tom', claim=Recluse),
                Player(name='Sula', claim=Investigator, night_info={
                    1: Investigator.Ping(You, Aoife, Baron)
                }),
                Player(name='Matthew', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Aoife, Oscar, Librarian)
                }),
                Player(name='Oscar', claim=Librarian, night_info={
                    1: Librarian.Ping(None)
                }),
                Player(name='Josh', claim=Empath, night_info={
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
            Player(name='You', claim=Slayer, day_info={
                1: Slayer.Shot(Anna, died=True)
            }),
            Player(name='Tim', claim=Librarian, night_info={
                1: Librarian.Ping(You, Hannah, Drunk)
            }),
            Player(name='Sarah', claim=Investigator, night_info={
                1: Investigator.Ping(Tim, Fraser, ScarletWoman)
            }),
            Player(name='Hannah', claim=Saint),
            Player(name='Dan', claim=Chef, night_info={
                1: Chef.Ping(0)
            }),
            Player(name='Anna', claim=Recluse),
            Player(name='Matt', claim=Washerwoman, night_info={
                1: Washerwoman.Ping(Tim, Dan, Librarian)
            }),
            Player(name='Fraser', claim=Empath, night_info={
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
                Player(name='You', claim=Investigator, night_info={
                    1: Investigator.Ping(Matt, Hannah, Marionette)
                }),
                Player(name='Anna', claim=Empath, night_info={
                    1: Empath.Ping(2)
                }),
                Player(name='Dan', claim=Undertaker, night_info={
                    2: Undertaker.Ping(Anna, Empath)
                }),
                Player(name='Fraser', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Anna, Tim, demon=True),
                    2: FortuneTeller.Ping(You, Fraser, demon=False),
                    3: FortuneTeller.Ping(You, Sarah, demon=True),
                }),
                Player(name='Sarah', claim=Librarian, night_info={
                    1: Librarian.Ping(You, Hannah, Drunk)
                }),
                Player(name='Tim', claim=Recluse),
                Player(name='Matt', claim=Juggler,
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
                Player(name='Hannah', claim=Dreamer, night_info={
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
            Player(name='You', claim=Alsaahir),
            Player(name='Dan', claim=Noble, night_info={
                1: Noble.Ping(Tom, Anna, Hannah)
            }),
            Player(name='Tom', claim=Knight, night_info={
                1: Knight.Ping(Dan, Anna)
            }),
            Player(name='Matt', claim=Investigator, night_info={
                1: Investigator.Ping(Anna, Oscar, Goblin)
            }),
            Player(name='Anna', claim=Empath, night_info={
                1: Empath.Ping(Dan)
            }),
            Player(name='Hannah', claim=Steward, night_info={
                1: Steward.Ping(Tom)
            }),
            Player(name='Oscar', claim=Seamstress, night_info={
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
            Player(name='You', claim=Juggler),
            Player(name='Sarah', claim=Empath, night_info={
                1: Empath.Ping(You)
            }),
            Player(name='Tim', claim=Seamstress, night_info={
                1: Seamstress.Ping(You, Fraser, same=True)
            }),
            Player(name='Matthew', claim=Steward, night_info={
                1: Steward.Ping(You)
            }),
            Player(name='Steph', claim=Investigator, night_info={
                1: Investigator.Ping(Sarah, Fraser, Goblin)
            }),
            Player(name='Aoife', claim=Noble, night_info={
                1: Noble.Ping(Sarah, Tim, Matthew)
            }),
            Player(name='Fraser', claim=Knight, night_info={
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
                Player(name='You', claim=Librarian, night_info={
                    1: Librarian.Ping(Sula, Fraser, Drunk)
                }),
                Player(name='Sarah', claim=Saint),
                Player(name='Tim', claim=Noble, night_info={
                    1: Noble.Ping(Aoife, Sula, Fraser)
                }),
                Player(name='Dan', claim=Seamstress, night_info={
                    1: Seamstress.Ping(Aoife, Tim, same=False)
                }),
                Player(name='Aoife', claim=Investigator, night_info={
                    1: Investigator.Ping(Dan, Matthew, Marionette)
                }),
                Player(name='Sula', claim=Juggler,
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
                Player(name='Steph', claim=Knight, night_info={
                    1: Knight.Ping(Sarah, Dan)
                }),
                Player(name='Fraser', claim=Empath, night_info={
                    1: Empath.Ping(0)
                }),
                Player(name='Matthew', claim=Steward, night_info={
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
            Player(name='You', claim=Savant, day_info={
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
            Player(name='Fraser', claim=VillageIdiot, night_info={
                1: VillageIdiot.Ping(Sarah, is_evil=False),
                2: VillageIdiot.Ping(Aoife, is_evil=False),
                3: VillageIdiot.Ping(You, is_evil=False),
            }),
            Player(name='Sarah', claim=FortuneTeller, night_info={
                1: FortuneTeller.Ping(Oscar, Aoife, demon=False),
                2: FortuneTeller.Ping(You, Sarah, demon=True),
                3: FortuneTeller.Ping(Fraser, Tim, demon=False),
            }),
            Player(name='Oscar', claim=Investigator, night_info={
                1: Investigator.Ping(Fraser, Steph, Goblin),
            }),
            Player(name='Anna', claim=Juggler,
                day_info={1: Juggler.Juggle({You: Savant, Tim: VillageIdiot})},
                night_info={2: Juggler.Ping(1)}
            ),
            Player(name='Aoife', claim=Shugenja, night_info={
                1: Shugenja.Ping(clockwise=False)
            }),
            Player(name='Steph', claim=Dreamer, night_info={
                1: Dreamer.Ping(Sarah, FortuneTeller, Leviathan),
                2: Dreamer.Ping(You, Savant, Goblin),
                3: Dreamer.Ping(Fraser, Mutant, Goblin),
            }),
            Player(name='Tim', claim=VillageIdiot, night_info={
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
            Player(name='You', claim=Seamstress, night_info={
                1: Seamstress.Ping(Anna, Matthew, same=False)
            }),
            Player(name='Josh', claim=Seamstress, night_info={
                1: Seamstress.Ping(Anna, Tim, same=False)
            }),
            Player(name='Steph', claim=Seamstress, night_info={
                1: Seamstress.Ping(Tim, Matthew, same=False)
            }),
            Player(name='Anna', claim=Seamstress, night_info={
                1: Seamstress.Ping(Josh, Matthew, same=False)
            }),
            Player(name='Tim', claim=Seamstress, night_info={
                1: Seamstress.Ping(You, Josh, same=False)
            }),
            Player(name='Matthew', claim=Seamstress, night_info={
                1: Seamstress.Ping(Steph, Fraser, same=False)
            }),
            Player(name='Fraser', claim=Seamstress, night_info={
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
                Player(name='You', claim=Acrobat, night_info={
                    2: Acrobat.Choice(Fraser),
                    3: Acrobat.Choice(Josh),
                }),
                Player(name='Fraser', claim=Balloonist, night_info={
                    1: Balloonist.Ping(Oscar),
                    2: Balloonist.Ping(Anna),
                    3: Balloonist.Ping(You),
                }),
                Player(name='Oscar', claim=Gossip, day_info={
                    1: Gossip.Gossip(IsCategory(Fraser, DEMON)),
                    2: Gossip.Gossip(IsCategory(Anna, DEMON)),
                }),
                Player(name='Josh', claim=Knight, night_info={
                    1: Knight.Ping(Fraser, Oscar)
                }),
                Player(name='Anna', claim=Gambler, night_info={
                    2: Gambler.Gamble(Sula, Goblin),
                    3: Gambler.Gamble(You, Drunk),
                }),
                Player(name='Sula', claim=Juggler, day_info={
                    1: Juggler.Juggle({
                        You: Goblin,
                        Oscar: Gossip,
                        Josh: Knight,
                        Anna: Imp,
                    })
                }),
                Player(name='Hannah', claim=Steward, night_info={
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
                Player(name='You', claim=Slayer, day_info={
                    2: Slayer.Shot(Fraser, died=False)
                }),
                Player(name='Matthew', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Josh, Imp)
                }),
                Player(name='Dan', claim=Undertaker, night_info={
                    2: Undertaker.Ping(Josh, Poisoner)
                }),
                Player(name='Tom', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Tom, Sula, demon=False),
                    2: FortuneTeller.Ping(Tom, Josh, demon=True),
                }),
                Player(name='Sula', claim=Chef, night_info={
                    1: Chef.Ping(0)
                }),
                Player(name='Fraser', claim=Recluse),
                Player(name='Josh', claim=Washerwoman, night_info={
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
                Player(name='You', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Sarah, Lunatic, ScarletWoman)
                }),
                Player(name='Tim', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(2)
                }),
                Player(name='Fraser', claim=Empath, night_info={
                    1: Empath.Ping(0)
                }),
                Player(name='Hannah', claim=Slayer),
                Player(name='Sarah', claim=Courtier, night_info={
                    1: Courtier.Choice(Vortox)
                }),
                Player(name='Jasmine', claim=Mayor),
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
                Player(name='You', claim=Librarian, night_info={
                    1: Librarian.Ping(Fraser, Steph, Lunatic)
                }),
                Player(name='Oscar', claim=Investigator, night_info={
                    1: Investigator.Ping(Josh, Fraser, Spy)
                }),
                Player(name='Anna', claim=Empath, night_info={
                    1: Empath.Ping(1)
                }),
                Player(name='Josh', claim=Mayor),
                Player(name='Fraser', claim=Slayer),
                Player(name='Tom', claim=Dreamer, night_info={
                    1: Dreamer.Ping(Steph, Lunatic, Spy)
                }),
                Player(name='Aoife', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(3)
                }),
                Player(name='Steph', claim=Courtier, night_info={
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
                Player(name='You', claim=Investigator, night_info={
                    1: Investigator.Ping(Sarah, Aoife, ScarletWoman)
                }),
                Player(name='Jasmine', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(3)
                }),
                Player(name='Oscar', claim=Librarian, night_info={
                    1: Librarian.Ping(None)
                }),
                Player(name='Tim', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Oscar, Librarian)
                }),
                Player(name='Sarah', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(You, Oscar, demon=False),
                    2: FortuneTeller.Ping(You, Jasmine, demon=False),
                }),
                Player(name='Fraser', claim=Slayer, day_info={
                    2: Slayer.Shot(Oscar, died=False),
                }),
                Player(name='Aoife', claim=Recluse),
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
                Player(name='You', claim=Slayer),
                Player(name='Danielle', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Rob, Lav, Empath)
                }),
                Player(name='Gwilym', claim=Undertaker, night_info={
                    2: Undertaker.Ping(You, Slayer)
                }),
                Player(name='Brett', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Danielle, Gwilym, demon=False)
                }),
                Player(name='Rob', claim=Empath, night_info={
                    1: Empath.Ping(0),
                    2: Empath.Ping(0),
                }),
                Player(name='Lav', claim=Chef, night_info={
                    1: Chef.Ping(1)
                }),
                Player(name='Lydia', claim=Investigator, night_info={
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

        # This puzzle requires a custom method for one of the savant statements
        @dataclass
        class LongestRowOfTownsfolk(Info):
            """This puzzle (15) has no misregistration, so ommit that logic."""
            length: int
            def __call__(self, state: State, src: PlayerID) -> STBool:
                townsfolk = [
                    info.IsCategory(player, TOWNSFOLK)(state, src)
                    for player in range(len(state.players))
                ]
                assert not any(x is MAYBE for x in townsfolk), "Not Implemented"
                longest, prev_not_tf = 0, -1
                for player, is_tf in enumerate(townsfolk * 2):  # Wrap circle
                    if is_tf is FALSE:
                        longest = max(longest, player - prev_not_tf - 1)
                        prev_not_tf = player
                longest = min(longest, len(state.players))
                return STBool(longest == self.length)


        You, Oscar, Sarah, Hannah, Fraser, Aoife, Adam, Jasmine = range(8)
        state = State(
            players=[
                Player(name='You', claim=Savant, day_info={
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
                Player(name='Oscar', claim=Klutz),
                Player(name='Sarah', claim=Juggler, 
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
                Player(name='Hannah', claim=SnakeCharmer, night_info={
                    1: [
                        SnakeCharmer.Choice(Sarah),
                        EvilTwin.Is(Jasmine),
                    ],
                    2: SnakeCharmer.Choice(Oscar),
                    3: SnakeCharmer.Choice(Aoife),
                }),
                Player(name='Fraser', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(3)
                }),
                Player(name='Aoife', claim=Seamstress, night_info={
                    1: Seamstress.Ping(Oscar, Hannah, same=False)
                }),
                Player(name='Adam', claim=Artist, night_info={
                    1: Artist.Ping(
                        ~IsCharacter(You, Vortox)
                        & ~IsCharacter(Oscar, Vortox)
                        & ~IsCharacter(Sarah, Vortox) 
                    )
                }),
                Player(name='Jasmine', claim=SnakeCharmer, night_info={
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
                Player(name='You', claim=Saint),
                Player(name='Olivia', claim=Empath, night_info={
                    1: Empath.Ping(0),
                    2: Empath.Ping(1),
                }),
                Player(name='Jasmine', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Hannah, Tim, demon=False),
                    2: FortuneTeller.Ping(Olivia, Tim, demon=False),
                    3: FortuneTeller.Ping(Sarah, Jasmine, demon=False),
                }),
                Player(name='Fraser', claim=NightWatchman, night_info={
                    1: NightWatchman.Choice(Tim, confirmed=False)
                }),
                Player(name='Oscar', claim=Recluse),
                Player(name='Hannah', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Oscar, Tim, Chef)
                }),
                Player(name='Sarah', claim=Investigator, night_info={
                    1: Investigator.Ping(Olivia, Hannah, Poisoner)
                }),
                Player(name='Tim', claim=Chef, night_info={
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
                Player(name='You', claim=Puzzlemaster),
                Player(name='Adam', claim=Chef, night_info={
                    1: Chef.Ping(0),
                }),
                Player(name='Steph', claim=Empath, night_info={
                    1: Empath.Ping(0),
                }),
                Player(name='Fraser', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Hannah, Tom, demon=False),
                    2: FortuneTeller.Ping(Tom, Fraser, demon=True),
                    3: FortuneTeller.Ping(You, Sarah, demon=True),
                }),
                Player(name='Sarah', claim=Undertaker, night_info={
                    2: Undertaker.Ping(Steph, Empath),
                    3: Undertaker.Ping(Sula, Washerwoman),
                }),
                Player(name='Sula', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Sarah, Hannah, Undertaker)
                }),
                Player(name='Hannah', claim=Investigator, night_info={
                    1: Investigator.Ping(Sarah, Fraser, ScarletWoman)
                }),
                Player(name='Tom', claim=Slayer),
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
                Player(name='You', claim=Librarian, night_info={
                    1: Librarian.Ping(Fraser, Matt, Drunk)
                }),
                Player(name='Fraser', claim=Saint),
                Player(name='Oscar', claim=Recluse),
                Player(name='Jasmine', claim=Slayer),
                Player(name='Olivia', claim=Undertaker, night_info={
                    2: Undertaker.Ping(You, Baron),
                }),
                Player(name='Matt', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(Fraser, Saint)
                }),
                Player(name='Sula', claim=Washerwoman, night_info={
                    1: Washerwoman.Ping(Fraser, Olivia, Undertaker)
                }),
                Player(name='Aoife', claim=Empath, night_info={
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
                Player(name='You', claim=Investigator, night_info={
                    1: Investigator.Ping(Mary, Gabriel, Baron)
                }),
                Player(name='Caspar', claim=VillageIdiot, night_info={
                    1: VillageIdiot.Ping(Mary, is_evil=True),
                    2: VillageIdiot.Ping(Joseph, is_evil=True),
                }),
                Player(name='Joseph', claim=Saint),
                Player(name='Melchior', claim=VillageIdiot, night_info={
                    1: VillageIdiot.Ping(Balthazar, is_evil=True),
                    2: VillageIdiot.Ping(Mary, is_evil=True),
                }),
                Player(name='Mary', claim=Virgin, day_info={
                    1: Virgin.NominatedWithoutExecution(Balthazar)
                }),
                Player(name='Balthazar', claim=VillageIdiot, night_info={
                    1: VillageIdiot.Ping(Joseph, is_evil=True),
                    2: VillageIdiot.Ping(Caspar, is_evil=True),
                }),
                Player(name='Gabriel', claim=Ravenkeeper, night_info={
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
            Player(name='You', claim=Juggler,
                day_info={1: Juggler.Juggle({Matt: Goblin, Oscar: Goblin})},
                night_info={2: Juggler.Ping(0)},
            ),
            Player(name='Fraser', claim=Juggler,
                day_info={1: Juggler.Juggle({Olivia: Juggler, Oscar: Drunk})},
                night_info={2: Juggler.Ping(1)},
            ),
            Player(name='Aoife', claim=Juggler,
                day_info={1: Juggler.Juggle({Olivia: Leviathan, Oscar: Leviathan})},
                night_info={2: Juggler.Ping(0)},
            ),
            Player(name='Josh', claim=Juggler,
                day_info={1: Juggler.Juggle({Tim: Goblin, Oscar: Juggler})},
                night_info={2: Juggler.Ping(1)},
            ),
            Player(name='Tim', claim=Juggler,
                day_info={1: Juggler.Juggle({You: Leviathan, Josh: Juggler})},
                night_info={2: Juggler.Ping(0)},
            ),
            Player(name='Matt', claim=Juggler,
                day_info={1: Juggler.Juggle({Josh: Goblin, Tim: Juggler})},
                night_info={2: Juggler.Ping(0)},
            ),
            Player(name='Olivia', claim=Juggler,
                day_info={1: Juggler.Juggle({You: Juggler, Aoife: Drunk})},
                night_info={2: Juggler.Ping(2)},
            ),
            Player(name='Oscar', claim=Juggler,
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

        
    def test_puzzle_26(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1ihl8vs/weekly_puzzle_26_a_major_problem/

        You, Olivia, Dan, Tom, Matthew, Josh, Sula, Fraser = range(8)
        state = State(
            players=[
                Player(name='You', claim=Empath, night_info={
                    1: Empath.Ping(0)
                }),
                Player(name='Olivia', claim=Saint),
                Player(name='Dan', claim=Slayer, day_info={
                    2: Slayer.Shot(Matthew, died=False),
                }),
                Player(name='Tom', claim=Recluse),
                Player(name='Matthew', claim=Librarian, night_info={
                    1: Librarian.Ping(You, Josh, Drunk)
                }),
                Player(name='Josh', claim=Soldier),
                Player(name='Sula', claim=Undertaker, night_info={
                    2: Undertaker.Ping(You, Empath),
                    3: Undertaker.Ping(Dan, Slayer),
                }),
                Player(name='Fraser', claim=Chef, night_info={
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
                Player(name='You', claim=Chambermaid, night_info={
                    1: Chambermaid.Ping(Adam, Sarah, 1)
                }),
                Player(name='Matt', claim=Juggler,
                day_info={1: Juggler.Juggle({Fraser: Undertaker, Oscar: NoDashii})},
                night_info={2: Juggler.Ping(2)},
                ),
                Player(name='Fraser', claim=Undertaker, night_info={
                    2: Undertaker.Ping(Aoife, NoDashii)
                }),
                Player(name='Aoife', claim=Librarian, night_info={
                    1: Librarian.Ping(Matt, Adam, Drunk),
                }),
                Player(name='Adam', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(4)
                }),
                Player(name='Oscar', claim=Empath, night_info={
                    1: Empath.Ping(1),
                    2: Empath.Ping(2),
                    3: Empath.Ping(1),
                }),		
                Player(name='Olivia', claim=FortuneTeller, night_info={
                    1: FortuneTeller.Ping(Olivia, Sarah, demon=False),
                    2: FortuneTeller.Ping(Olivia, Aoife, demon=False),
                    3: FortuneTeller.Ping(Matt, Oscar, demon=False),
                }),
                Player(name='Sarah', claim=Oracle, night_info={
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

        
    def test_puzzle_30left(self):
        # https://www.reddit.com/r/BloodOnTheClocktower/comments/1j46gtl/weekly_puzzle_30_which_is_the_atheist_game/

        Finn, Louisa, Shan, Ben, Owen, Lydia = range(6)
        state = State(players=[
            Player(name='Finn', claim=Atheist),
            Player(name='Louisa', claim=Knight, night_info={
                1: Knight.Ping(Lydia, Shan)
            }),
            Player(name='Shan', claim=Artist, day_info={
                1: Artist.Ping(IsCharacter(Louisa, Drunk))
            }),
            Player(name='Ben', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(3),
            }),
            Player(name='Owen', claim=Noble, night_info={
                1: Noble.Ping(Lydia, Louisa, Shan),
            }),
            Player(name='Lydia', claim=Seamstress, night_info={
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
            Player(name='Lav', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(3),
            }),
            Player(name='Oli', claim=Atheist),
            Player(name='Callum', claim=Knight, night_info={
                1: Knight.Ping(Lav, Max)
            }),
            Player(name='Sarah', claim=Seamstress, night_info={
                1: Seamstress.Ping(Oli, Callum, same=True)
            }),
            Player(name='Max', claim=Artist, day_info={
                1: Artist.Ping(IsCharacter(Erika, Drunk))
            }),
            Player(name='Erika', claim=Noble, night_info={
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