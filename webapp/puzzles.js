
// This file was auto-generated using clockchecker/webapp/update_content.py
const puzzleSamples = {
    "NotQuiteTangible": [{
name: 'NQT1',
claims: ['Savant', 'Knight', 'Steward', 'Investigator', 'Noble', 'Seamstress'],
hidden: ['Leviathan', 'Goblin', 'Drunk'],
value: 
`# NQT1: Can the sober Savant solve the puzzle?
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1erb5e2/can_the_sober_savant_solve_the_puzzle/
You, Tim, Sula, Oscar, Matt, Anna = range(6)
puzzle = Puzzle(
    players=[
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
    ],
    hidden_characters=[Leviathan, Goblin, Drunk],
    hidden_self=[],
)`
}, {
name: 'NQT2',
claims: ['Seamstress', 'Knight', 'FortuneTeller', 'Saint', 'Investigator', 'Juggler', 'Clockmaker', 'Balloonist'],
hidden: ['Leviathan', 'Goblin', 'Drunk'],
value: 
`# NQT2: Come Fly With Me
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1ewxu0r/weekly_puzzle_2_come_fly_with_me/
You, Steph, Fraser, Tim, Sarah, Matthew, Anna, Sula = range(8)
puzzle = Puzzle(
    players=[
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
    ],
    hidden_characters=[Leviathan, Goblin, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT3a',
claims: ['Slayer', 'Chef', 'Recluse', 'Investigator', 'Washerwoman', 'Librarian', 'Empath'],
hidden: ['Imp', 'Baron', 'Spy', 'Poisoner', 'ScarletWoman', 'Drunk'],
value: 
`# NQT3a: Not Throwing Away My Shot (7-player)
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1f2jht3/weekly_puzzle_3a_3b_not_throwing_away_my_shot/
You, Aoife, Tom, Sula, Matthew, Oscar, Josh = range(7)
puzzle = Puzzle(
    players=[
        Player('You', claim=Slayer, day_info={
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
    hidden_characters=[Imp, Baron, Spy, Poisoner, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT3b',
claims: ['Slayer', 'Librarian', 'Investigator', 'Saint', 'Chef', 'Recluse', 'Washerwoman', 'Empath'],
hidden: ['Imp', 'Baron', 'Spy', 'Poisoner', 'ScarletWoman', 'Drunk'],
value: 
`# NQT3b: Not Throwing Away My Shot (8-player)
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1f2jht3/weekly_puzzle_3a_3b_not_throwing_away_my_shot/
You, Tim, Sarah, Hannah, Dan, Anna, Matt, Fraser = range(8)
puzzle = Puzzle(
    players=[
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
    ],
    hidden_characters=[Imp, Baron, Spy, Poisoner, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT4',
claims: ['Investigator', 'Empath', 'Undertaker', 'FortuneTeller', 'Librarian', 'Recluse', 'Juggler', 'Dreamer'],
hidden: ['LordOfTyphon', 'Marionette', 'Poisoner', 'Drunk'],
value: 
`# NQT4: The Many-Headed Monster
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1f823s4/weekly_puzzle_4_the_manyheaded_monster/
You, Anna, Dan, Fraser, Sarah, Tim, Matt, Hannah = range(8)
puzzle = Puzzle(
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
    hidden_characters=[LordOfTyphon, Marionette, Poisoner, Drunk],
    hidden_self=[Drunk, Marionette],
)`
}, {
name: 'NQT5a',
claims: ['Alsaahir', 'Noble', 'Knight', 'Investigator', 'Empath', 'Steward', 'Seamstress'],
hidden: ['Leviathan', 'Goblin'],
value: 
`# NQT5a: You Only Guess Twice (Alsaahir)
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fcriex/weekly_puzzle_5a_5b_you_only_guess_twice/
# Notes: Find an Alsaahir guess to solve the puzzle
You, Dan, Tom, Matt, Anna, Hannah, Oscar = range(7)
puzzle = Puzzle(
    players=[
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
    ],
    hidden_characters=[Leviathan, Goblin],
    hidden_self=[],
)`
}, {
name: 'NQT5b',
claims: ['Juggler', 'Empath', 'Seamstress', 'Steward', 'Investigator', 'Noble', 'Knight'],
hidden: ['Leviathan', 'Goblin'],
value: 
`# NQT5b: You Only Guess Twice (Juggler)
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fcriex/weekly_puzzle_5a_5b_you_only_guess_twice/
# Notes: Find a Juggler guess to solve the puzzle
You, Sarah, Tim, Matthew, Steph, Aoife, Fraser = range(7)
puzzle = Puzzle(
    players=[
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
    ],
    hidden_characters=[Leviathan, Goblin],
    hidden_self=[],
)`
}, {
name: 'NQT6',
claims: ['Librarian', 'Saint', 'Noble', 'Seamstress', 'Investigator', 'Juggler', 'Knight', 'Empath', 'Steward'],
hidden: ['NoDashii', 'Vortox', 'Pukka', 'Marionette', 'Drunk'],
value: 
`# NQT6: Super Marionette Bros
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fj1h0c/weekly_puzzle_6_super_marionette_bros/
You, Sarah, Tim, Dan, Aoife, Sula, Steph, Fraser, Matthew = range(9)
puzzle = Puzzle(
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
    hidden_characters=[NoDashii, Vortox, Pukka, Marionette, Drunk],
    hidden_self=[Drunk, Marionette],
)`
}, {
name: 'NQT7',
claims: ['Savant', 'VillageIdiot', 'FortuneTeller', 'Investigator', 'Juggler', 'Shugenja', 'Dreamer', 'VillageIdiot'],
hidden: ['Leviathan', 'Goblin', 'Mutant'],
value: 
`# NQT7: The Savant Strikes Back
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1foeq4d/weekly_puzzle_7_the_savant_strikes_back/
You, Fraser, Sarah, Oscar, Anna, Aoife, Steph, Tim = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Savant, day_info={
            1: Savant.Ping(
                ExactlyN(N=1, args=[IsEvil(Fraser), IsEvil(Anna), IsEvil(Steph)]),
                Clockmaker.Ping(3),
            ),
            2: Savant.Ping(
                CharAttrEq(Sarah, 'red_herring', Sarah),
                (
                    IsCharacter(Fraser, VillageIdiot)
                    & CharAttrEq(Fraser, 'self_droison', True)
                ),
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
    ],
    hidden_characters=[Leviathan, Goblin, Mutant],
    hidden_self=[],
    allow_good_double_claims=True,
)`
}, {
name: 'NQT8',
claims: ['Seamstress', 'Seamstress', 'Seamstress', 'Seamstress', 'Seamstress', 'Seamstress', 'Seamstress'],
hidden: ['Imp', 'Poisoner'],
value: 
`# NQT8: The Stitch-Up
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1ftqc28/weekly_puzzle_8_the_stitchup/
# Notes: Every Townsfolk is a Seamstress
You, Josh, Steph, Anna, Tim, Matthew, Fraser = range(7)
puzzle = Puzzle(
    players=[
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
    ],
    hidden_characters=[Imp, Poisoner],
    hidden_self=[],
    allow_good_double_claims=True,
)`
}, {
name: 'NQT9',
claims: ['Acrobat', 'Balloonist', 'Gossip', 'Knight', 'Gambler', 'Juggler', 'Steward'],
hidden: ['Imp', 'Po', 'Goblin', 'Drunk'],
value: 
`# NQT9: The New Acrobat
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fz4jqe/weekly_puzzle_9_the_new_acrobat/
You, Fraser, Oscar, Josh, Anna, Sula, Hannah = range(7)
puzzle = Puzzle(
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
    hidden_characters=[Imp, Po, Goblin, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT10',
claims: ['Slayer', 'Ravenkeeper', 'Undertaker', 'FortuneTeller', 'Chef', 'Recluse', 'Washerwoman'],
hidden: ['Imp', 'Poisoner', 'Spy', 'Baron', 'ScarletWoman', 'Drunk'],
value: 
`# NQT10: Don't Overcook It
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1g49r8j/weekly_puzzle_10_dont_overcook_it/
You, Matthew, Dan, Tom, Sula, Fraser, Josh = range(7)
puzzle = Puzzle(
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
    hidden_characters=[Imp, Poisoner, Spy, Baron, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT12a',
claims: ['Dreamer', 'Clockmaker', 'Empath', 'Slayer', 'Courtier', 'Mayor'],
hidden: ['Vortox', 'Spy', 'ScarletWoman', 'Lunatic'],
value: 
`# NQT12a: Thunderstruck (6-player)
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gexyoq/weekly_puzzle_12a_12b_thunderstruck/
# Notes: Based on "<a href="https://bloodontheclocktower.com/custom-scripts/race-to-the-bottom">Race To The Bottom</a>"
You, Tim, Fraser, Hannah, Sarah, Jasmine = range(6)
puzzle = Puzzle(
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
    hidden_characters=[Vortox, Spy, ScarletWoman, Lunatic],
    hidden_self=[],
)`
}, {
name: 'NQT12b',
claims: ['Librarian', 'Investigator', 'Empath', 'Mayor', 'Slayer', 'Dreamer', 'Clockmaker', 'Courtier'],
hidden: ['Vortox', 'Spy', 'ScarletWoman', 'Lunatic'],
value: 
`# NQT12b: Thunderstruck (8-player)
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gexyoq/weekly_puzzle_12a_12b_thunderstruck/
# Notes: Based on "<a href="https://bloodontheclocktower.com/custom-scripts/race-to-the-bottom">Race To The Bottom</a>"
You, Oscar, Anna, Josh, Fraser, Tom, Aoife, Steph = range(8)
puzzle = Puzzle(
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
    hidden_characters=[Vortox, Spy, ScarletWoman, Lunatic],
    hidden_self=[],
)`
}, {
name: 'NQT13',
claims: ['Investigator', 'Clockmaker', 'Librarian', 'Ravenkeeper', 'FortuneTeller', 'Slayer', 'Recluse'],
hidden: ['Imp', 'Baron', 'Spy', 'ScarletWoman', 'Poisoner', 'Drunk'],
value: 
`# NQT13: Clockblocking
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gka3js/weekly_puzzle_13_clockblocking/
You, Jasmine, Oscar, Tim, Sarah, Fraser, Aoife = range(7)
puzzle = Puzzle(
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
    hidden_characters=[Imp, Baron, Spy, ScarletWoman, Poisoner, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT14',
claims: ['Slayer', 'Washerwoman', 'Undertaker', 'FortuneTeller', 'Empath', 'Chef', 'Investigator'],
hidden: ['Imp', 'Poisoner', 'Spy', 'ScarletWoman', 'Marionette'],
value: 
`# NQT14: New Super Marionette Bros
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gpo1xo/weekly_puzzle_14_new_super_marionette_bros/
You, Danielle, Gwilym, Brett, Rob, Lav, Lydia = range(7)
puzzle = Puzzle(
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
    hidden_characters=[Imp, Poisoner, Spy, ScarletWoman, Marionette],
    hidden_self=[Marionette],
)`
}, {
name: 'NQT15',
claims: ['Savant', 'Klutz', 'Juggler', 'SnakeCharmer', 'Clockmaker', 'Seamstress', 'Artist', 'SnakeCharmer'],
hidden: ['NoDashii', 'Vortox', 'EvilTwin', 'Mutant'],
value: 
`# NQT15: Wake Up and Choose Violets
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gv12ck/weekly_puzzle_15_wake_up_and_choose_violets/
You, Oscar, Sarah, Hannah, Fraser, Aoife, Adam, Jasmine = range(8)
puzzle = Puzzle(
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
        Player('Adam', claim=Artist, day_info={
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
    hidden_characters=[NoDashii, Vortox, EvilTwin, Mutant],
    hidden_self=[],
)`
}, {
name: 'NQT16',
claims: ['Saint', 'Empath', 'FortuneTeller', 'NightWatchman', 'Recluse', 'Washerwoman', 'Investigator', 'Chef'],
hidden: ['Imp', 'Poisoner', 'Spy', 'ScarletWoman', 'Baron', 'Drunk'],
value: 
`# NQT16: Who Watches the Watchmen?
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1h0f8se/weekly_puzzle_16_who_watches_the_watchmen/
You, Olivia, Jasmine, Fraser, Oscar, Hannah, Sarah, Tim = range(8)
puzzle = Puzzle(
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
    hidden_characters=[Imp, Poisoner, Spy, ScarletWoman, Baron, Drunk],
    hidden_self=[],
)`
}, {
name: 'NQT17',
claims: ['Puzzlemaster', 'Chef', 'Empath', 'FortuneTeller', 'Undertaker', 'Washerwoman', 'Investigator', 'Slayer'],
hidden: ['Imp', 'ScarletWoman'],
value: 
`# NQT17: The Missing Piece
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1h5sgc7/weekly_puzzle_17_the_missing_piece/
# Notes: Find a Puzzlemaster guess to solve the puzzle
You, Adam, Steph, Fraser, Sarah, Sula, Hannah, Tom = range(8)
puzzle = Puzzle(
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
    hidden_characters=[Imp, ScarletWoman],
    hidden_self=[],
)`
}, {
name: 'NQT18',
claims: ['Librarian', 'Juggler', 'SnakeCharmer', 'FortuneTeller', 'Balloonist', 'Saint', 'Investigator', 'Recluse'],
hidden: ['Leviathan', 'Xaan', 'Drunk'],
value: 
`# NQT18: X and the City
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1hb72qg/weekly_puzzle_18_starring_the_xaan/
You, Steph, Fraser, Dan, Aoife, Tim, Olivia, Sarah = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Librarian, night_info={
            1: Librarian.Ping(Aoife, Tim, Drunk),
        }),
        Player('Steph', claim=Juggler, 
            day_info={1: Juggler.Juggle({
                Fraser: Leviathan,
                Aoife: Balloonist,
                Tim: Xaan,
            })},
            night_info={2: Juggler.Ping(2)},
        ),
        Player('Fraser', claim=SnakeCharmer, night_info={
            1: SnakeCharmer.Choice(Olivia),
            2: SnakeCharmer.Choice(Steph),
            3: SnakeCharmer.Choice(Aoife),
        }),
        Player('Dan', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Tim, Sarah, demon=False),
            2: FortuneTeller.Ping(Steph, Aoife, demon=False),
            3: FortuneTeller.Ping(Fraser, Olivia, demon=False),
        }),
        Player('Aoife', claim=Balloonist, night_info={
            1: Balloonist.Ping(Olivia),
            2: Balloonist.Ping(Aoife),
            3: Balloonist.Ping(You),
        }),
        Player('Tim', claim=Saint),
        Player('Olivia', claim=Investigator, night_info={
            1: Investigator.Ping(Fraser, Aoife, Xaan),
        }),
        Player('Sarah', claim=Recluse),
    ],
    hidden_characters=[Leviathan, Xaan, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT19',
claims: ['Librarian', 'Saint', 'Recluse', 'Slayer', 'Undertaker', 'Ravenkeeper', 'Washerwoman', 'Empath'],
hidden: ['Imp', 'Poisoner', 'Spy', 'Baron', 'ScarletWoman', 'Drunk'],
value: 
`# NQT19: He Could Be You, He Could Be Me
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1hgdsmp/weekly_puzzle_19_he_could_be_you_he_could_be_me/
You, Fraser, Oscar, Jasmine, Olivia, Matt, Sula, Aoife = range(8)
puzzle = Puzzle(
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
    hidden_characters=[Imp, Poisoner, Spy, Baron, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT20',
claims: ['Investigator', 'VillageIdiot', 'Saint', 'VillageIdiot', 'Virgin', 'VillageIdiot', 'Ravenkeeper'],
hidden: ['Imp', 'Baron', 'Spy', 'Poisoner', 'ScarletWoman', 'Drunk'],
value: 
`# NQT20: The Three Wise Men
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1hlgh1w/weekly_puzzle_20_the_three_wise_men/
You, Caspar, Joseph, Melchior, Mary, Balthazar, Gabriel = range(7)
puzzle = Puzzle(
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
            1: UneventfulNomination(Balthazar)
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
    hidden_characters=[Imp, Baron, Spy, Poisoner, ScarletWoman, Drunk],
    hidden_self=[Drunk],
    allow_good_double_claims=True,
)`
}, {
name: 'NQT21',
claims: ['Juggler', 'Juggler', 'Juggler', 'Juggler', 'Juggler', 'Juggler', 'Juggler', 'Juggler'],
hidden: ['Leviathan', 'Goblin', 'Drunk'],
value: 
`# NQT21: Eight Jugglers Juggling
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1hpqhai/weekly_puzzle_21_eight_jugglers_juggling/
# Notes: Every Townsfolk is a Juggler
You, Fraser, Aoife, Josh, Tim, Matt, Olivia, Oscar = range(8)
puzzle = Puzzle(
    players=[
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
    ],
    hidden_characters=[Leviathan, Goblin, Drunk],
    hidden_self=[Drunk],
    allow_good_double_claims=True,
)`
}, {
name: 'NQT22',
claims: ['Chambermaid', 'Investigator', 'Slayer', 'Ravenkeeper', 'Saint', 'Recluse', 'Librarian', 'Washerwoman'],
hidden: ['Imp', 'Baron', 'Spy', 'Poisoner', 'ScarletWoman', 'Drunk'],
value: 
`# NQT22: One in the Chamber
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1hvum3b/weekly_puzzle_22_one_in_the_chamber/
You, Anna, Aoife, Sarah, Tim, Fraser, Oscar, Steph = range(8)
puzzle = Puzzle(
    players=[
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
    hidden_characters=[Imp, Baron, Spy, Poisoner, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT23',
claims: ['Chef', 'Washerwoman', 'Investigator', 'FortuneTeller', 'Ravenkeeper', 'Goblin', 'Librarian', 'Slayer'],
hidden: ['Imp', 'Goblin', 'Lunatic'],
value: 
`# NQT23: Goblincore
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1i199yv/weekly_puzzle_23_goblincore/
You, Hannah, Matt, Tim, Aoife, Fraser, Tom, Sula = range(8)
puzzle = Puzzle(
    players=[
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
    hidden_characters=[Imp, Goblin, Lunatic],
    hidden_self=[],
)`
}, {
name: 'NQT24',
claims: ['Investigator', 'Klutz', 'FortuneTeller', 'Washerwoman', 'Virgin', 'Librarian', 'Chef', 'Empath'],
hidden: ['Imp', 'Poisoner', 'Drunk'],
value: 
`# NQT24: The Ultimate Blunder
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1i6m0ww/weekly_puzzle_24_the_ultimate_blunder/
You, Olivia, Steph, Fraser, Sula, Oscar, Adam, Josh = range(8)
puzzle = Puzzle(
    players=[
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
    day_events={
        1: [
            UneventfulNomination(nominator=Adam, player=Sula),
            Execution(You),
        ]
    },
    night_deaths={2: Olivia},
    hidden_characters=[Imp, Poisoner, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT26',
claims: ['Empath', 'Saint', 'Slayer', 'Recluse', 'Librarian', 'Soldier', 'Undertaker', 'Chef'],
hidden: ['Imp', 'Poisoner', 'Spy', 'Baron', 'ScarletWoman', 'Drunk'],
value: 
`# NQT26: A Major Problem
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1ihl8vs/weekly_puzzle_26_a_major_problem/
You, Olivia, Dan, Tom, Matthew, Josh, Sula, Fraser = range(8)
puzzle = Puzzle(
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
    hidden_characters=[Imp, Poisoner, Spy, Baron, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT28',
claims: ['Chambermaid', 'Juggler', 'Undertaker', 'Librarian', 'Clockmaker', 'Empath', 'FortuneTeller', 'Oracle'],
hidden: ['Pukka', 'NoDashii', 'ScarletWoman', 'Drunk'],
value: 
`# NQT28: A Study in Scarlet
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1iu1vxo/weekly_puzzle_28_a_study_in_scarlet/
You, Matt, Fraser, Aoife, Adam, Oscar, Olivia, Sarah = range(8)
puzzle = Puzzle(
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
    hidden_characters=[Pukka, NoDashii, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT29',
claims: ['Dreamer', 'Dreamer', 'Dreamer', 'Dreamer', 'Dreamer', 'Dreamer', 'Dreamer', 'Dreamer'],
hidden: ['Imp', 'Poisoner', 'Drunk'],
value: 
`# NQT29: A Dreamer? I'm Not the Only One
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1ixykmz/weekly_puzzle_29_a_dreamer_im_not_the_only_one/
# Notes: Every Townsfolk is a Dreamer
You, Jasmine, Adam, Sarah, Sula, Steph, Hannah, Fraser = range(8)
puzzle = Puzzle(
    players=[
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
    hidden_characters=[Imp, Poisoner, Drunk],
    hidden_self=[Drunk],
    allow_good_double_claims=True,
)`
}, {
name: 'NQT30a',
claims: ['Atheist', 'Knight', 'Artist', 'Clockmaker', 'Noble', 'Seamstress'],
hidden: ['Imp', 'Spy', 'Drunk'],
value: 
`# NQT30a: The Babel Fish is a Dead Giveaway
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1j46gtl/weekly_puzzle_30_which_is_the_atheist_game/
# Notes: Two games, one of which has a genuine Atheist
Finn, Louisa, Shan, Ben, Owen, Lydia = range(6)
puzzle = Puzzle(
    players=[
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
    ],
    hidden_characters=[Imp, Spy, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT30b',
claims: ['Clockmaker', 'Atheist', 'Knight', 'Seamstress', 'Artist', 'Noble'],
hidden: ['Imp', 'Spy', 'Drunk'],
value: 
`# NQT30b: The Babel Fish is a Dead Giveaway
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1j46gtl/weekly_puzzle_30_which_is_the_atheist_game/
# Notes: Two games, one of which has a genuine Atheist
Lav, Oli, Callum, Sarah, Max, Erika = range(6)
puzzle = Puzzle(
    players=[
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
    ],
    hidden_characters=[Imp, Spy, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT31',
claims: ['Chef', 'Empath', 'Ravenkeeper', 'Investigator', 'Recluse', 'Undertaker', 'FortuneTeller'],
hidden: ['Imp', 'Poisoner', 'Spy', 'Baron', 'ScarletWoman', 'Drunk'],
value: 
`# NQT31: No, Your Other Left
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1j8ub5q/weekly_puzzle_31_no_your_other_left/
You, Aoife, Tim, Adam, Fraser, Sarah, Olivia = range(7)
puzzle = Puzzle(
    players=[
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
    hidden_characters=[Imp, Poisoner, Spy, Baron, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT32',
claims: ['Dreamer', 'Juggler', 'Recluse', 'Empath', 'Juggler', 'Saint', 'Undertaker', 'FortuneTeller'],
hidden: ['Imp', 'Poisoner', 'Baron', 'Drunk'],
value: 
`# NQT32: Prepare for Juggle, and Make it Double
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1je8z17/weekly_puzzle_32_prepare_for_juggle_and_make_it/
You, Matthew, Olivia, Sula, Dan, Fraser, Jasmine, Tim = range(8)
puzzle = Puzzle(
    players=[
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
    hidden_characters=[Imp, Poisoner, Baron, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT33',
claims: ['Empath', 'Recluse', 'Ravenkeeper', 'Washerwoman', 'Librarian', 'FortuneTeller', 'Saint', 'Investigator'],
hidden: ['Imp', 'Poisoner', 'Baron', 'Spy', 'ScarletWoman', 'Drunk'],
value: 
`# NQT33: Twice is Coincidence, Thrice is Proof
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1jl7cuv/weekly_puzzle_33_twice_is_coincidence_thrice_is/
You, Olivia, Jasmine, Hannah, Tom, Oscar, Sula, Fraser = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Empath, night_info={
            1: Empath.Ping(0),
        }),
        Player('Olivia', claim=Recluse),
        Player('Jasmine', claim=Ravenkeeper, night_info={
            3: Ravenkeeper.Ping(Hannah, Washerwoman),
        }),
        Player('Hannah', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Sula, Fraser, Investigator),
        }),
        Player('Tom', claim=Librarian, night_info={
            1: Librarian.Ping(Olivia, Sula, Saint),
        }),
        Player('Oscar', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Sula, Fraser, demon=False),
            2: FortuneTeller.Ping(Tom, Sula, demon=False),
            3: FortuneTeller.Ping(Hannah, Tom, demon=False),
        }),
        Player('Sula', claim=Saint),
        Player('Fraser', claim=Investigator, night_info={
            1: Investigator.Ping(You, Jasmine, Poisoner),
        }),
    ],
    day_events={1: Execution(You), 2: Execution(Fraser)},
    night_deaths={2: Olivia, 3: Jasmine},
    hidden_characters=[Imp, Poisoner, Baron, Spy, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT34',
claims: ['Mathematician', 'Sage', 'Artist', 'Clockmaker', 'Seamstress', 'Juggler', 'SnakeCharmer'],
hidden: ['NoDashii', 'Vortox', 'Witch'],
value: 
`# NQT34: The Vortox Conjecture
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1joxqgy/weekly_puzzle_34_the_vortox_conjecture/
You, Fraser, Steph, Sula, Sarah, Josh, Aoife = range(7)
puzzle = Puzzle(
    players=[
        Player('You', claim=Mathematician, night_info={
            1: Mathematician.Ping(1),
            2: Mathematician.Ping(0),
        }),
        Player('Fraser', claim=Sage, night_info={
            2: Sage.Ping(Sarah, Josh),
        }),
        Player('Steph', claim=Artist, day_info={
            1: Artist.Ping(IsCharacter(Aoife, NoDashii)),
        }),
        Player('Sula', claim=Clockmaker, night_info={
            1: Clockmaker.Ping(3),
        }),
        Player('Sarah', claim=Seamstress, night_info={
            1: Seamstress.Ping(Steph, Aoife, same=True),
        }),
        Player('Josh', claim=Juggler, 
            day_info={1: Juggler.Juggle({Steph: Artist, Sula: Clockmaker})},
            night_info={2: Juggler.Ping(0)},
        ),
        Player('Aoife', claim=SnakeCharmer, night_info={
            1: SnakeCharmer.Choice(Josh),
        }),
    ],
    day_events={
        1: [
            Dies(player=Steph, after_nominating=True), 
            Execution(Aoife),
        ]
    },
    night_deaths={2: Fraser},
    hidden_characters=[NoDashii, Vortox, Witch],
    hidden_self=[],
)`
}, {
name: 'NQT35',
claims: ['Librarian', 'Clockmaker', 'Undertaker', 'FortuneTeller', 'Ravenkeeper', 'Saint', 'Investigator', 'Empath'],
hidden: ['Imp', 'LordOfTyphon', 'Poisoner', 'Spy', 'Drunk'],
value: 
`# NQT35: Typhon Season
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1jv7zh2/weekly_puzzle_35_typhon_season/
You, Tim, Sula, Fraser, Oscar, Olivia, Sarah, Jasmine = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Librarian, night_info={
            1: Librarian.Ping(Sula, Oscar, Drunk),
        }),
        Player('Tim', claim=Clockmaker, night_info={
            1: Clockmaker.Ping(4),
        }),
        Player('Sula', claim=Undertaker, night_info={
            2: Undertaker.Ping(You, Spy),
        }),
        Player('Fraser', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Sula, Oscar, demon=False),
            2: FortuneTeller.Ping(Sarah, Jasmine, demon=False),
        }),
        Player('Oscar', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Sula, Imp),
        }),
        Player('Olivia', claim=Saint),
        Player('Sarah', claim=Investigator, night_info={
            1: Investigator.Ping(Olivia, Jasmine, Spy),
        }),
        Player('Jasmine', claim=Empath, night_info={
            1: Empath.Ping(2),
            2: Empath.Ping(2),
        }),

    ],
    day_events={1: Execution(You)},
    night_deaths={2: Oscar},
    hidden_characters=[Imp, LordOfTyphon, Poisoner, Spy, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT36',
claims: ['Empath', 'Saint', 'Slayer', 'Ravenkeeper', 'Investigator', 'FortuneTeller', 'Recluse', 'Slayer'],
hidden: ['Imp', 'Poisoner', 'Spy', 'Baron', 'ScarletWoman', 'Drunk'],
value: 
`# NQT36: What is Your Weapon of Choice?
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1k1exb7/weekly_puzzle_36_what_is_your_weapon_of_choice/
You, Steph, Adam, Josh, Sula, Olivia, Fraser, Oscar = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Empath, night_info={
            1: Empath.Ping(1),
        }),
        Player('Steph', claim=Saint),
        Player('Adam', claim=Slayer, day_info={
            3: Slayer.Shot(Sula, died=False),
        }),
        Player('Josh', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Adam, ScarletWoman),
        }),
        Player('Sula', claim=Investigator, night_info={
            1: Investigator.Ping(Steph, Josh, Spy),
        }),
        Player('Olivia', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Josh, Oscar, demon=False),
            2: FortuneTeller.Ping(Adam, Oscar, demon=False),
        }),
        Player('Fraser', claim=Recluse),
        Player('Oscar', claim=Slayer, day_info={
            2: Slayer.Shot(Steph, died=False),
        }),
    ],
    day_events={1: Execution(You), 2: Execution(Oscar)},
    night_deaths={2: Josh, 3: Olivia},
    hidden_characters=[Imp, Poisoner, Spy, Baron, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT37',
claims: ['Undertaker', 'Washerwoman', 'Chef', 'Ravenkeeper', 'Librarian', 'FortuneTeller', 'Empath', 'Imp'],
hidden: ['Imp', 'Poisoner', 'Spy', 'ScarletWoman', 'Marionette', 'Drunk'],
value: 
`# NQT37: New Super Marionette Bros&nbsp;U
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1k7n8hi/weekly_puzzle_37_new_super_marionette_bros_u/
You, Matt, Steph, Adam, Sula, Aoife, Fraser, Jasmine = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Undertaker, night_info={
            2: Undertaker.Ping(Matt, Spy),
            3: Undertaker.Ping(Aoife, Marionette),
        }),
        Player('Matt', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(You, Fraser, Undertaker),
        }),
        Player('Steph', claim=Chef, night_info={
            1: Chef.Ping(1),
        }),
        Player('Adam', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Fraser, Empath),
        }),
        Player('Sula', claim=Librarian, night_info={
            1: Librarian.Ping(Jasmine, Steph, Drunk),
        }),
        Player('Aoife', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(You, Jasmine, demon=True),
            2: FortuneTeller.Ping(Jasmine, Sula, demon=False),
        }),
        Player('Fraser', claim=Empath, night_info={
            1: Empath.Ping(1),
            2: Empath.Ping(1),
            3: Empath.Ping(1),
        }),
        Player('Jasmine', claim=Imp),
    ],
    day_events={1: Execution(Matt), 2: Execution(Aoife)},
    night_deaths={2: Adam, 3: Sula},
    hidden_characters=[Imp, Poisoner, Spy, ScarletWoman, Marionette, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT38',
claims: ['Recluse', 'Empath', 'Ravenkeeper', 'Investigator', 'SnakeCharmer', 'SnakeCharmer', 'FortuneTeller', 'Saint'],
hidden: ['Imp', 'Baron', 'Spy', 'Poisoner', 'ScarletWoman', 'Drunk'],
value: 
`# NQT38: Snakes on a Plane
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1kccbp9/weekly_puzzle_38_snakes_on_a_plane/
You, Hannah, Dan, Adam, Tim, Fraser, Sula, Matt = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Recluse),
        Player('Hannah', claim=Empath, night_info={
            1: Empath.Ping(0),
            2: Empath.Ping(1),
            3: Empath.Ping(1),
        }),
        Player('Dan', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Fraser, Poisoner),
        }),
        Player('Adam', claim=Investigator, night_info={
            1: Investigator.Ping(Tim, Sula, Baron),
        }),
        Player('Tim', claim=SnakeCharmer, night_info={
            1: SnakeCharmer.Choice(Matt),
            2: SnakeCharmer.Choice(Sula),
            3: SnakeCharmer.Choice(Hannah),
        }),
        Player('Fraser', claim=SnakeCharmer, night_info={
            1: SnakeCharmer.Choice(Sula),
            2: SnakeCharmer.Choice(Hannah),
            3: SnakeCharmer.Choice(Adam),
        }),
        Player('Sula', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(You, Tim, False),
            2: FortuneTeller.Ping(Fraser, Matt, False),
        }),
        Player('Matt', claim=Saint),
    ],
    day_events={1: Execution(You), 2: Execution(Sula)},
    night_deaths={2: Dan, 3: Matt},
    hidden_characters=[Imp, Baron, Spy, Poisoner, ScarletWoman, Drunk],
    hidden_self=[],
)`
}, {
name: 'NQT38_alt',
claims: ['Empath', 'Clockmaker', 'Philosopher', 'Juggler', 'Chef', 'Mathematician', 'Chambermaid', 'Oracle'],
hidden: ['NoDashii', 'Vortox', 'Witch', 'Drunk'],
value: 
`# Other: NQT38_alt
# This version of NQT Puzzle 38 was posted to the discord, but not Reddit
# once it was discovered that there is an unintended second solution that 
# relies on the Mathematician's counting of Philosophers waking to abilities
# they never gained due to being poisoned on the night they choose.
# https://discord.com/channels/569683781800296501/854891541969109033/1367073812063191081

You, Sarah, Hannah, Jasmine, Josh, Dan, Aoife, Fraser = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Empath, night_info={
            1: Empath.Ping(0),
        }),
        Player('Sarah', claim=Clockmaker, night_info={
            1: Clockmaker.Ping(3)
        }),
        Player('Hannah', claim=Philosopher, night_info={
            1: [
                Philosopher.Choice(Chambermaid),
                Chambermaid.Ping(Aoife, Fraser, 1),
            ],
            2: Chambermaid.Ping(Josh, Fraser, 2),
        }),
        Player('Jasmine', claim=Juggler,
            day_info={1: Juggler.Juggle({Hannah: Vortox, Josh: NoDashii})},
            night_info={2: Juggler.Ping(2)}
        ),
        Player('Josh', claim=Chef, night_info={
            1: Chef.Ping(1)
        }),
        Player('Dan', claim=Mathematician, night_info={
            1: Mathematician.Ping(2),
            2: Mathematician.Ping(1),
        }),
        Player('Aoife', claim=Chambermaid, night_info={
            1: Chambermaid.Ping(Hannah, Josh, 2),
        }),
        Player('Fraser', claim=Oracle, night_info={
            2: Oracle.Ping(2)
        }),
    ],
    day_events={1: [
        Dies(player=You, after_nominating=True),
        Execution(Aoife),
    ]},
    night_deaths={2: Sarah},
    hidden_characters=[NoDashii, Vortox, Witch, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT39',
claims: ['Oracle', 'Juggler', 'Philosopher', 'Seamstress', 'Sage', 'Artist', 'Mathematician', 'Klutz'],
hidden: ['NoDashii', 'Witch', 'Mutant'],
value: 
`# NQT39: Squid Game
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1kg6y94/weekly_puzzle_39_squid_game/
You, Jasmine, Matt, Aoife, Fraser, Tom, Sula, Hannah = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Oracle, night_info={
            2: Oracle.Ping(1),
        }),
        Player('Jasmine', claim=Juggler,
            day_info={
                1: Juggler.Juggle({
                    You: Witch,
                    Aoife: Witch,
                    Tom: Witch,
                    Fraser: Sage,
                    Hannah: Klutz,
                })
            },
            night_info={2: Juggler.Ping(3)}
        ),
        Player('Matt', claim=Philosopher, night_info={
            1: [
                Philosopher.Choice(Seamstress),
                Seamstress.Ping(Aoife, Tom, same=False),
            ]
        }),
        Player('Aoife', claim=Seamstress, night_info={
            1: Seamstress.Ping(Matt, Hannah, same=False)
        }),
        Player('Fraser', claim=Sage, night_info={
            2: Sage.Ping(Jasmine, Matt)
        }),
        Player('Tom', claim=Artist, day_info={
            1: Artist.Ping(
                IsCharacter(Jasmine, Mutant)
                | IsCharacter(Matt, Mutant)
                | IsCharacter(Aoife, Mutant)
            )
        }),
        Player('Sula', claim=Mathematician, night_info={
            1: Mathematician.Ping(0),
            2: Mathematician.Ping(1),
        }),
        Player('Hannah', claim=Klutz),
    ],
    day_events={
        1: [
            Dies(player=Tom, after_nominating=True),
            Execution(Aoife),
        ],
        2: Execution(Sula)
    },
    night_deaths={2: Fraser, 3: You},
    hidden_characters=[NoDashii, Witch, Mutant],
    hidden_self=[],
)`
}, {
name: 'NQT40',
claims: ['Investigator', 'FortuneTeller', 'Recluse', 'Washerwoman', 'Saint', 'Librarian', 'Empath', 'Butler', 'Slayer'],
hidden: ['Imp', 'Poisoner', 'Spy', 'ScarletWoman', 'Baron', 'Drunk'],
value: 
`# NQT40: Nine Lives
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1klqy8j/weekly_puzzle_40_nine_lives/
You, Matthew, Steph, Jasmine, Hannah, Fraser, Tim, Josh, Adam = range(9)
puzzle = Puzzle(
    players=[
        Player('You', claim=Investigator, night_info={
            1: Investigator.Ping(Steph, Fraser, ScarletWoman),
        }),
        Player('Matthew', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Tim, Josh, demon=False),
            2: FortuneTeller.Ping(Hannah, Tim, demon=False),
            3: FortuneTeller.Ping(You, Matthew, demon=True),
        }),
        Player('Steph', claim=Recluse),
        Player('Jasmine', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Tim, Adam, Empath),
        }),
        Player('Hannah', claim=Saint),
        Player('Fraser', claim=Librarian, night_info={
            1: Librarian.Ping(Jasmine, Hannah, Drunk),
        }),
        Player('Tim', claim=Empath, night_info={
            1: Empath.Ping(2),
            2: Empath.Ping(1),
        }),
        Player('Hannah', claim=Butler),
        Player('Adam', claim=Slayer, day_info={
            3: Slayer.Shot(Matthew, died=False),
        }),
    ],
    day_events={1: Execution(Josh), 2: Execution(Jasmine)},
    night_deaths={2: Fraser, 3: Tim},
    hidden_characters=[Imp, Poisoner, Spy, ScarletWoman, Baron, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT41',
claims: ['Imp', 'FortuneTeller', 'Seamstress', 'Slayer', 'Chef', 'Noble', 'PoppyGrower', 'Artist'],
hidden: ['Imp', 'Witch', 'Drunk', 'Lunatic'],
value: 
`# NQT41: No, John, You Are the Demons
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1kqfgch/weekly_puzzle_41_in_which_you_might_be_the_lunatic/
You, Amelia, Edd, Riley, Josef, Gina, Katharine, Chris = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Imp),
        Player('Amelia', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Edd, Josef, False),
            2: FortuneTeller.Ping(Josef, You, False),
            3: FortuneTeller.Ping(Amelia, You, False),
        }),
        Player('Edd', claim=Seamstress, night_info={
            1: Seamstress.Ping(Katharine, Chris, same=True),
        }),
        Player('Riley', claim=Slayer, day_info={
            1: Slayer.Shot(Katharine, died=False),
        }),
        Player('Josef', claim=Chef, night_info={
            1: Chef.Ping(1),
        }),
        Player('Gina', claim=Noble, night_info={
            1: Noble.Ping(Edd, Riley, Chris),
        }),
        Player('Katharine', claim=PoppyGrower),
        Player('Chris', claim=Artist, day_info={
            1: Artist.Ping(~IsCategory(Riley, TOWNSFOLK)),
        }),
    ],
    day_events={
        1: [
            Dies(after_nominating=True, player=Gina),
            Execution(Riley),
        ],
        2: Execution(Edd)
    },
    night_deaths={2: Chris, 3: Josef},
    hidden_characters=[Imp, Witch, Drunk, Lunatic],
    hidden_self=[Imp, Lunatic],
)`
}, {
name: 'NQT43',
claims: ['Ravenkeeper', 'Investigator', 'Chef', 'Chef', 'Recluse', 'FortuneTeller', 'Empath', 'Saint'],
hidden: ['Imp', 'Poisoner', 'Spy', 'ScarletWoman', 'Baron', 'Drunk'],
value: 
`# NQT43: Two Many Cooks
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1kz0kf2/weekly_puzzle_43_too_many_cooks/
You, Anna, Josh, Tom, Sarah, Matthew, Fraser, Steph = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Steph, Drunk),
        }),
        Player('Anna', claim=Investigator, night_info={
            1: Investigator.Ping(Josh, Sarah, ScarletWoman),
        }),
        Player('Josh', claim=Chef, night_info={
            1: Chef.Ping(2),
        }),
        Player('Tom', claim=Chef, night_info={
            1: Chef.Ping(1),
        }),
        Player('Sarah', claim=Recluse),
        Player('Matthew', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Tom, Fraser, demon=False),
            2: FortuneTeller.Ping(Josh, Matthew, demon=False),
        }),
        Player('Fraser', claim=Empath, night_info={
            1: Empath.Ping(0),
        }),
        Player('Steph', claim=Saint),
    ],
    day_events={1: Execution(Fraser), 2: Execution(Matthew)},
    night_deaths={2: You, 3: Steph},
    hidden_characters=[Imp, Poisoner, Spy, ScarletWoman, Baron, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT44',
claims: ['Juggler', 'Chef', 'FortuneTeller', 'Noble', 'Shugenja', 'Investigator', 'Progidy', 'Progidy'],
hidden: ['Leviathan', 'ScarletWoman', 'Drunk'],
value: 
`# NQT44: Trouble Homebrewing
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1lamap3/weekly_puzzle_44_trouble_homebrewing/
# Notes: Uses homebrew Townsfolk
You, Olivia, Sarah, Tim, Fraser, Steph, Matt, Dan = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Juggler,
            day_info={
                1: Juggler.Juggle({
                    Matt: Leviathan,
                    Olivia: ScarletWoman,
                }
            )},
            night_info={2: Juggler.Ping(0)},
        ),
        Player('Olivia', claim=Chef, night_info={
            1: Chef.Ping(0),
        }),
        Player('Sarah', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Tim, Dan, demon=False),
            2: FortuneTeller.Ping(Tim, Fraser, demon=False),
            3: FortuneTeller.Ping(You, Steph, demon=True),
        }),
        Player('Tim', claim=Noble, night_info={
            1: Noble.Ping(You, Olivia, Fraser),
        }),
        Player('Fraser', claim=Shugenja, night_info={
            1: Shugenja.Ping(clockwise=False),
        }),
        Player('Steph', claim=Investigator, night_info={
            1: Investigator.Ping(Fraser, Matt, ScarletWoman),
        }),
        Player('Matt', claim=Progidy, night_info={
            1: Progidy.Ping(Dan, Tim),
            2: Progidy.Ping(Sarah, Dan),
            3: Progidy.Ping(Sarah, Steph),
        }),
        Player('Dan', claim=Progidy, night_info={
            1: Progidy.Ping(Steph, Olivia),
            2: Progidy.Ping(Fraser, Matt),
            3: Progidy.Ping(Steph, Fraser),
        }),
    ],
    hidden_characters=[Leviathan, ScarletWoman, Drunk],
    hidden_self=[Drunk],
    allow_good_double_claims=True,
)`
}, {
name: 'NQT44_alt',
claims: ['Washerwoman', 'Progidy', 'Progidy', 'Knight', 'Shugenja', 'Clockmaker', 'Noble', 'Juggler'],
hidden: ['Leviathan', 'ScarletWoman', 'Drunk'],
value: 
`# Other: NQT44_alt
# Unreleased Solar/Lunar Prodigy puzzle, because it has unintended solutions

You, Fraser, Sula, Adam, Oscar, Jasmine, Anna, Steph = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Oscar, Steph, Shugenja),
        }),
        Player('Fraser', claim=Progidy, night_info={
            1: Progidy.Ping(Adam, Anna),
            2: Progidy.Ping(Anna, You),
        }),
        Player('Sula', claim=Progidy, night_info={
            1: Progidy.Ping(Steph, You),
            2: Progidy.Ping(Fraser, Steph),
        }),
        Player('Adam', claim=Knight, night_info={
            1: Knight.Ping(Sula, Steph),
        }),
        Player('Oscar', claim=Shugenja, night_info={
            1: Shugenja.Ping(clockwise=False),
        }),
        Player('Jasmine', claim=Clockmaker, night_info={
            1: Clockmaker.Ping(3),
        }),
        Player('Anna', claim=Noble, night_info={
            1: Noble.Ping(Fraser, Adam, Jasmine),
        }),
        Player('Step', claim=Juggler,
            day_info={
                1: Juggler.Juggle({
                    You: Leviathan,
                    Fraser: Leviathan,
                    Oscar: Leviathan,
                    Sula: Drunk,
                }
            )},
            night_info={2: Juggler.Ping(0)},
        ),
    ],
    hidden_characters=[Leviathan, ScarletWoman, Drunk],
    hidden_self=[Drunk],
    allow_good_double_claims=True,
)`
}, {
name: 'NQT45a',
claims: ['Ravenkeeper', 'Empath', 'FortuneTeller', 'Investigator', 'Chef', 'Investigator', 'Washerwoman', 'Slayer'],
hidden: ['Imp', 'ScarletWoman', 'Spy', 'Drunk', 'Hermit'],
value: 
`# NQT45a: Don't Try This at Home
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1lgua6n/weekly_puzzle_45_featuring_a_cursed_hermit_combo/
Hermit.set_outsiders(Saint, Recluse, Drunk)

You, Ben, Louisa, Marc, Julia, Eliz, Shan, Laura = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Ben, Empath)
        }),
        Player('Ben', claim=Empath, night_info={
            1: Empath.Ping(0),
            2: Empath.Ping(0),
            3: Empath.Ping(0),
        }),
        Player('Louisa', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(You, Julia, demon=False),
            2: FortuneTeller.Ping(Ben, Shan, demon=False),
        }),
        Player('Marc', claim=Investigator, night_info={
            1: Investigator.Ping(Julia, Eliz, ScarletWoman)
        }),
        Player('Julia', claim=Chef, night_info={
            1: Chef.Ping(1)
        }),
        Player('Eliz', claim=Investigator, night_info={
            1: Investigator.Ping(Marc, Julia, ScarletWoman)
        }),
        Player('Shan', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Julia, Laura, Chef)
        }),
        Player('Laura', claim=Slayer, day_info={
            3: Slayer.Shot(Ben, died=False),
        }),
    ],
    day_events={1: Execution(Eliz), 2: Execution(Louisa)},
    night_deaths={2: You, 3: Julia},
    hidden_characters=[Imp, ScarletWoman, Spy, Drunk, Hermit],
    hidden_self=[Drunk, Hermit],
)`
}, {
name: 'NQT45b',
claims: ['Slayer', 'Undertaker', 'Investigator', 'Empath', 'Ravenkeeper', 'Washerwoman', 'Investigator', 'Chef'],
hidden: ['Imp', 'ScarletWoman', 'Spy', 'Drunk', 'Hermit'],
value: 
`# NQT45b: Don't Try This at Home
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1lgua6n/weekly_puzzle_45_featuring_a_cursed_hermit_combo/
Hermit.set_outsiders(Saint, Recluse, Drunk)

You, Tim, Adam, Dan, Oscar, Sula, Sarah, Fraser = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Slayer, day_info={
            2: Slayer.Shot(Adam, died=False),
        }),
        Player('Tim', claim=Undertaker, night_info={
            2: Undertaker.Ping(Dan, Drunk),
            3: Undertaker.Ping(Fraser, Chef),
        }),
        Player('Adam', claim=Investigator, night_info={
            1: Investigator.Ping(Tim, Dan, ScarletWoman)
        }),
        Player('Dan', claim=Empath, night_info={
            1: Empath.Ping(1),
        }),
        Player('Oscar', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Adam, Investigator),
        }),
        Player('Sula', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Tim, Fraser, Undertaker)
        }),
        Player('Sarah', claim=Investigator, night_info={
            1: Investigator.Ping(Tim, Fraser, Spy)
        }),
        Player('Fraser', claim=Chef, night_info={
            1: Chef.Ping(1)
        }),
    ],
    day_events={1: Execution(Dan), 2: Execution(Fraser)},
    night_deaths={2: Oscar, 3: You},
    hidden_characters=[Imp, ScarletWoman, Spy, Drunk, Hermit],
    hidden_self=[Drunk, Hermit],
)`
}, {
name: 'NQT46',
claims: ['Clockmaker', 'Exorcist', 'Investigator', 'Chambermaid', 'Gossip', 'Princess', 'Gambler'],
hidden: ['Imp', 'Poisoner'],
value: 
`# NQT46: The Princess Diaries
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1lk83yb/weekly_puzzle_46_the_princess_diaries/
You, Matthew, Fraser, Adam, Aoife, Jasmine, Josh = range(7)
puzzle = Puzzle(
    players=[
        Player('You', claim=Clockmaker, night_info={
            1: Clockmaker.Ping(3),
        }),
        Player('Matthew', claim=Exorcist, night_info={
            2: Exorcist.Choice(Jasmine),
            3: Exorcist.Choice(Aoife),
        }),
        Player('Fraser', claim=Investigator, night_info={
            1: Investigator.Ping(Aoife, Jasmine, Poisoner),
        }),
        Player('Adam', claim=Chambermaid, night_info={
            1: Chambermaid.Ping(Fraser, Josh, 2),
            2: Chambermaid.Ping(Matthew, Aoife, 2),
        }),
        Player('Aoife', claim=Gossip, day_info={
            1: Gossip.Gossip(IsCategory(Adam, TOWNSFOLK)),
            2: Gossip.Gossip(IsCategory(Matthew, DEMON)),
        }),
        Player('Jasmine', claim=Princess),
        Player('Josh', claim=Gambler, night_info={
            2: Gambler.Gamble(Aoife, Gossip),
            3: Gambler.Gamble(Matthew, Imp),
        }),
    ],
    day_events={
        1: [
            UneventfulNomination(player=You, nominator=Jasmine),
            Execution(You),
        ],
        2: Execution(Adam),
    },
    night_deaths={2: Fraser, 3: Jasmine},
    hidden_characters=[Imp, Poisoner],
    hidden_self=[],
    allow_killing_dead_players=False,
)`
}, {
name: 'NQT47',
claims: ['Recluse', 'Investigator', 'Undertaker', 'Saint', 'Saint', 'Butler', 'Washerwoman', 'Chef', 'Ravenkeeper'],
hidden: ['Imp', 'Poisoner', 'Spy', 'Baron', 'ScarletWoman', 'Drunk'],
value: 
`# Other: NQT47
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1lq1bt7/weekly_puzzle_47_we_have_evil_twin_at_home/

You, Olivia, Steph, Josh, Sula, Oscar, Jasmine, Tom, Fraser = range(9)
puzzle = Puzzle(
    players=[
        Player('You', claim=Recluse),
        Player('Olivia', claim=Investigator, night_info={
            1: Investigator.Ping(Josh, Tom, Baron)
        }),
        Player('Steph', claim=Undertaker, night_info={
            2: Undertaker.Ping(You, Recluse),
            3: Undertaker.Ping(Jasmine, Washerwoman),
            4: Undertaker.Ping(Tom, Drunk),
        }),
        Player('Josh', claim=Saint),
        Player('Sula', claim=Saint),
        Player('Oscar', claim=Butler),
        Player('Jasmine', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Josh, Tom, Chef)
        }),
        Player('Tom', claim=Chef, night_info={
            1: Chef.Ping(0)
        }),
        Player('Fraser', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Olivia, Investigator)
        }),
    ],
    day_events={1: Execution(You), 2: Execution(Jasmine), 3: Execution(Tom)},
    night_deaths={2: Fraser, 3: Oscar, 4: Olivia},
    hidden_characters=[Imp, Poisoner, Spy, Baron, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'NQT48',
claims: ['Mathematician', 'Chambermaid', 'VillageIdiot', 'VillageIdiot', 'Juggler', 'Golem', 'Puzzlemaster', 'Artist'],
hidden: ['Leviathan', 'Xaan', 'Poisoner'],
value: 
`# Other: NQT48
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1ltxd8a/weekly_puzzle_48_solving_for_x/

You, Matthew, Olivia, Jasmine, Fraser, Sula, Dan, Tom = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Mathematician, night_info={
            1: Mathematician.Ping(1),
            2: Mathematician.Ping(0),
            3: Mathematician.Ping(1),
        }),
        Player('Matthew', claim=Chambermaid, night_info={
            1: Chambermaid.Ping(Olivia, Jasmine, 2),
            2: Chambermaid.Ping(Olivia, Dan, 2),
            3: Chambermaid.Ping(Olivia, Fraser, 0),
        }),
        Player('Olivia', claim=VillageIdiot, night_info={
            1: VillageIdiot.Ping(Tom, is_evil=True),
            2: VillageIdiot.Ping(Matthew, is_evil=True),
            3: VillageIdiot.Ping(Dan, is_evil=False),
        }),
        Player('Jasmine', claim=VillageIdiot, night_info={
            1: VillageIdiot.Ping(Tom, is_evil=False),
            2: VillageIdiot.Ping(Fraser, is_evil=False),
            3: VillageIdiot.Ping(Matthew, is_evil=True),
        }),
        Player('Fraser', claim=Juggler,
            day_info={1: Juggler.Juggle({Olivia: VillageIdiot, Sula: Golem})},
            night_info={2: Juggler.Ping(0)}
        ),
        Player('Sula', claim=Golem),
        Player('Dan', claim=Puzzlemaster, day_info={
            3: Puzzlemaster.Ping(guess=Tom, demon=Matthew),
        }),
        Player('Tom', claim=Artist, day_info={
            3: Artist.Ping(
                IsCharacter(Jasmine, Poisoner)
                | IsCharacter(Fraser, Poisoner)
                | IsCharacter(Dan, Poisoner)
            )
        }),
        
    ],
    day_events={3: Dies(player=Tom, after_nominated_by=Sula)},
    night_deaths={},
    hidden_characters=[Leviathan, Xaan, Poisoner],
    hidden_self=[],
    allow_good_double_claims=True,
)`
}
], "Other": [{
name: 'josef_yes_but_dont',
claims: ['Ravenkeeper', 'Slayer', 'Saint', 'Investigator', 'FortuneTeller', 'Recluse', 'Empath', 'Undertaker', 'Soldier', 'Chef', 'Washerwoman'],
hidden: ['Imp', 'Spy', 'ScarletWoman'],
value: 
`# Other: josef_yes_but_dont
# A puzzle that relies on the ScarletWoman catching a Recluse death
You, Ali, Edd, Riley, Adam, Gina, Katharine, Tom, Zak, Jodie, _ = range(11)
puzzle = Puzzle(
    players=[
        Player('You', claim=Ravenkeeper, night_info={
            3: Ravenkeeper.Ping(Zak, Soldier),
        }),
        Player('Ali', claim=Slayer, day_info={
            1: Slayer.Shot(Riley, died=False),
        }),
        Player('Edd', claim=Saint),
        Player('Riley', claim=Investigator, night_info={
            1: Investigator.Ping(Katharine, Jodie, ScarletWoman),
        }),
        Player('Adam', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(You, Ali, True),
            2: FortuneTeller.Ping(Jodie, Katharine, True),
            3: FortuneTeller.Ping(Tom, Zak, True),
        }),
        Player('Gina', claim=Recluse),
        Player('Katharine', claim=Empath, night_info={
            1: Empath.Ping(0),
            2: Empath.Ping(1),
            3: Empath.Ping(1),
        }),
        Player('Tom', claim=Undertaker, night_info={
            2: Undertaker.Ping(Gina, Imp),
            3: Undertaker.Ping(Jodie, Slayer),
        }),
        Player('Zak', claim=Soldier),
        Player('Jodie', claim=Chef, night_info={
            1: Chef.Ping(0),
        }),
        Player('Jesal', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Katharine, Zak, Empath),
        })
    ],
    day_events={
        1: Execution(Gina),
        2: Execution(Jodie),
    },
    night_deaths={2: Edd, 3: You},
    hidden_characters=[Imp, Spy, ScarletWoman],
    hidden_self=[],
    deduplicate_initial_characters=True,
)`
}, {
name: 'ali_adversarial1',
claims: ['Shugenja', 'Noble', 'Seamstress', 'Investigator', 'Washerwoman', 'Knight', 'Seamstress', 'Chambermaid'],
hidden: ['Imp', 'Goblin', 'Drunk'],
value: 
`# Other: ali_adversarial1
# A puzzle made by a hater.
You, Edd, Riley, Gina, Adam, Katharine, Chris, Josef = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Shugenja, night_info={
            1: Shugenja.Ping(clockwise=False)
        }),
        Player('Edd', claim=Noble, night_info={
            1: Noble.Ping(You, Riley, Katharine),
        }),
        Player('Riley', claim=Seamstress, night_info={
            2: Seamstress.Ping(Adam, Chris, same=False),
        }),
        Player('Gina', claim=Investigator, night_info={
            1: Investigator.Ping(Adam, Josef, Goblin),
        }),
        Player('Adam', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(You, Riley, Seamstress),
        }),
        Player('Katharine', claim=Knight, night_info={
            1: Knight.Ping(Chris, Josef),
        }),
        Player('Chris', claim=Seamstress, night_info={
            2: Seamstress.Ping(Riley, Josef, same=True),
        }),
        Player('Josef', claim=Chambermaid, night_info={
            1: Chambermaid.Ping(Riley, Chris, 2),
            2: Chambermaid.Ping(Riley, Chris, 2),
            3: Chambermaid.Ping(Riley, Chris, 0),
        }),
    ],
    day_events={
        1: Execution(Edd),
        2: Execution(Gina)
    },
    night_deaths={2: Adam, 3: Katharine},
    hidden_characters=[Imp, Goblin, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'ali_adversarial2',
claims: ['Juggler', 'Seamstress', 'Shugenja', 'Seamstress', 'Knight', 'Washerwoman', 'Noble', 'Chambermaid'],
hidden: ['Imp', 'Goblin', 'Drunk'],
value: 
`# Other: ali_adversarial2
# A puzzle made by a hater.
You, Gina, Chris, Adam, Riley, Edd, Josef, Katharine = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Juggler,
            day_info={
                1: Juggler.Juggle({
                    Gina: Imp,
                    Adam: Seamstress,
                    Edd: Washerwoman,
                    Josef: Goblin,
                    Katharine:Goblin,
                })
            },
            night_info={2: Juggler.Ping(1)}
        ),
        Player('Gina', claim=Seamstress, night_info={
            2: Seamstress.Ping(Chris, Josef, same=False),
        }),
        Player('Chris', claim=Shugenja, night_info={
            1: Shugenja.Ping(clockwise=False)
        }),
        Player('Adam', claim=Seamstress, night_info={
            2: Seamstress.Ping(Edd, Josef, same=False),
        }),
        Player('Riley', claim=Knight, night_info={
            1: Knight.Ping(Chris, Josef),
        }),
        Player('Edd', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Gina, Adam, Seamstress),
        }),
        Player('Josef', claim=Noble, night_info={
            1: Noble.Ping(Chris, Riley, Katharine),
        }),
        Player('Katharine', claim=Chambermaid, night_info={
            1: Chambermaid.Ping(Adam, Edd, 1),
            2: Chambermaid.Ping(Adam, Edd, 2),
            3: Chambermaid.Ping(Gina, Josef, 0),
        }),
    ],
    day_events={
        1: Execution(Chris),
        2: Execution(Adam)
    },
    night_deaths={2: Riley, 3: You},
    hidden_characters=[Imp, Goblin, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'emerald_snv',
claims: ['Klutz', 'Clockmaker', 'Seamstress', 'Flowergirl', 'Oracle', 'Artist', 'Juggler', 'Savant', 'Mathematician'],
hidden: ['NoDashii', 'Vortox', 'FangGu', 'Vigormortis', 'Witch', 'Mutant'],
value: 
`# Other: emerald_snv
# Puzzle set during Aus Clocktower Con 2025
You, Tesso, Beardy, Emerald, Alanna, Aero, Sam, Theo, Karen = range(9)
puzzle = Puzzle(
    players=[
        Player('You', claim=Klutz),
        Player('Tesso', claim=Clockmaker, night_info={
            1: Clockmaker.Ping(2)
        }),
        Player('Beardy', claim=Seamstress, night_info={
            1: Seamstress.Ping(Sam, Emerald, same=True)
        }),
        Player('Emerald', claim=Flowergirl,
            day_info={
                1: Flowergirl.Voters([Tesso, Beardy, Emerald, Alanna, Aero, Sam]),
                2: Flowergirl.Voters([Emerald, Alanna, Sam, Theo, Karen]),
                3: Flowergirl.Voters([Beardy, Karen, Tesso]),
            },
            night_info={
                2: Flowergirl.Ping(True),
                3: Flowergirl.Ping(False),
                4: Flowergirl.Ping(True),
            }
        ),
        Player('Alanna', claim=Oracle, night_info={
            2: Oracle.Ping(0),
            3: Oracle.Ping(1),
        }),
        Player('Aero', claim=Artist, day_info={
            1: Artist.Ping(
                IsCharacter(You, NoDashii)
                | IsCharacter(Tesso, NoDashii)
                | IsCharacter(Beardy, NoDashii)
                | IsCharacter(Emerald, NoDashii)
                | IsCharacter(Alanna, NoDashii)
            )
        }),
        Player('Sam', claim=Juggler,
            day_info={
                1: Juggler.Juggle({
                    You: Klutz,
                    Alanna: Witch,
                    Beardy: Witch,
                    Theo: Savant,
                    Alanna: Mutant,
                })
            },
            night_info={2: Juggler.Ping(3)},
        ),
        Player('Theo', claim=Savant, day_info={
            1: Savant.Ping(
                IsCategory(Karen, OUTSIDER) ^ IsCategory(Sam, OUTSIDER),
                IsInPlay(Lunatic),  # TODO: Don't support Cerenovus
            ),
            2: Savant.Ping(
                IsInPlay(Vigormortis),
                LongestRowOfTownsfolk(minimum=4),
            )
        }),
        Player('Karen', claim=Mathematician, night_info={
            1: Mathematician.Ping(0),
            2: Mathematician.Ping(1),
            3: Mathematician.Ping(1),
            4: Mathematician.Ping(0),
        }),
    ],
    day_events={
        1: [
            Dies(player=You, after_nominating=True),
            Klutz.Choice(player=You, choice=Alanna),
            Execution(Aero),
        ],
        2: Execution(Sam),
        3: Execution(You),
    },
    night_deaths={2: Tesso, 3: Theo, 4: Alanna},
    hidden_characters=[NoDashii, Vortox, FangGu, Vigormortis, Witch, Mutant],
    hidden_self=[],
    deduplicate_initial_characters=True,
)`
}, {
name: 'emerald_tb',
claims: ['Librarian', 'FortuneTeller', 'Virgin', 'Undertaker', 'Empath', 'Washerwoman', 'Butler', 'Soldier', 'Chef', 'Virgin', 'Investigator', 'Ravenkeeper'],
hidden: ['Imp', 'Poisoner', 'Baron', 'Spy', 'ScarletWoman', 'Drunk'],
value: 
`# Other: emerald_tb
# Puzzle set during Aus Clocktower Con 2025
# Too slow to run in unittests, so start with underscore.
(
    You, Reggie, Evin, Steve, BenB, Claire, Lachlan, Amy, Steffen,
    BenD, Jamie, Andy
) = range(12)

puzzle = Puzzle(
    players=[
        Player('You', claim=Librarian, night_info={
            1: Librarian.Ping(BenD, Jamie, Drunk),
        }),
        Player('Reggie', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Evin, BenD, demon=True),
            2: FortuneTeller.Ping(Lachlan, Steffen, demon=True),
            3: FortuneTeller.Ping(Steve, Jamie, demon=False),
            4: FortuneTeller.Ping(Amy, Reggie, demon=True),
        }),
        Player('Evin', claim=Virgin, day_info={
            1: UneventfulNomination(You)
        }),
        Player('Steve', claim=Undertaker, night_info={
            2: Undertaker.Ping(Steffen, Poisoner),
            3: Undertaker.Ping(You, Poisoner),
            4: Undertaker.Ping(BenD, Imp),
            5: Undertaker.Ping(Reggie, FortuneTeller),
        }),
        Player('BenB', claim=Empath, night_info={
            1: Empath.Ping(0),
            2: Empath.Ping(0),
            3: Empath.Ping(1),
        }),
        Player('Claire', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Reggie, Andy, FortuneTeller),
        }),
        Player('Lachlan', claim=Butler),
        Player('Amy', claim=Soldier),
        Player('Steffen', claim=Chef, night_info={
            1: Chef.Ping(2),
        }),
        Player('BenD', claim=Virgin, day_info={
            3: UneventfulNomination(Jamie)
        }),
        Player('Jamie', claim=Investigator, night_info={
            1: Investigator.Ping(Andy, Steffen, Poisoner),
        }),
        Player('Andy', claim=Ravenkeeper, night_info={
            3: Ravenkeeper.Ping(Amy, Imp)
        }),

    ],
    day_events={
        1: Execution(Steffen),
        2: Execution(You),
        3: Execution(BenD),
        4: Execution(Reggie),
    },
    night_deaths={2: Evin, 3: Andy, 4: BenB, 5: Lachlan, 6: Amy},
    hidden_characters=[Imp, Poisoner, Baron, Spy, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)`
}, {
name: 'empty_template',
claims: [],
hidden: [''],
value: 
`# Other: empty_template
# An empty puzzle template for you to populate

You,  = range(1)
puzzle = Puzzle(
    players=[
    ],
    day_events={},
    night_deaths={},
    hidden_characters=[],
    hidden_self=[],
)`
}
],
};
