const Townsfolk = [
    "Acrobat",
    "Alsaahir",
    "Artist",
    "Atheist",
    "Balloonist",
    "Chambermaid",
    "Chef",
    "Clockmaker",
    "Courtier",
    "Dreamer",
    "Empath",
    "Flowergirl",
    "FortuneTeller",
    "Gambler",
    "Gossip",
    "Investigator",
    "Juggler",
    "Knight",
    "Librarian",
    "Mathematician",
    "Mayor",
    "NightWatchman",
    "Noble",
    "Oracle",
    "Philosopher",
    "PoppyGrower",
    "Progidy",
    "Ravenkeeper",
    "Sage",
    "Savant",
    "Seamstress",
    "Shugenja",
    "Slayer",
    "SnakeCharmer",
    "Soldier",
    "Steward",
    "Undertaker",
    "VillageIdiot",
    "Virgin",
    "Washerwoman",
]
const Outsiders = [
    "Butler",
    "Drunk",
    "Klutz",
    "Lunatic",
    "Mutant",
    "Puzzlemaster",
    "Recluse",
    "Saint",
];
const Evils = [
    "Baron",
    "EvilTwin",
    "FangGu",
    "Goblin",
    "Imp",
    "Leviathan",
    "LordOfTyphon",
    "Marionette",
    "NoDashii",
    "Poisoner",
    "Po",
    "Pukka",
    "ScarletWoman",
    "Spy",
    "Vigormortis",
    "Vortox",
    "Widow",
    "Witch",
    "Xaan",
];

const InfoTokens = [
    "IsCharacter",
    "IsEvil",
    "IsDroisoned",
    "IsAlive",
    "IsCategory",
    "IsInPlay",
    "CharAttrEq",
    "ExactlyN",
    "SameCategory",
    "Dies",
    "Execution",
    "DrunkBetweenTownsfolk",
    "LongestRowOfTownsfolk",
];

const DataTokens = [
    "MINION",
    "DEMON",
    "TOWNSFOLK",
    "OUTSIDER",
];


const longSamples = {
    "NotQuiteTangible": [
{
name: "1: Can the sober Savant solve the puzzle?",
claims: ["Savant", "Knight", "Steward", "Investigator", "Noble", "Seamstress"],
hidden: ["Leviathan", "Goblin", "Drunk"],
value: `
# NQT 1: Can the sober Savant solve the puzzle?
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1erb5e2/can_the_sober_savant_solve_the_puzzle

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
)
`
}, {
name: "2: Come Fly With Me",
claims: ["Seamstress", "Knight", "FortuneTeller", "Saint", "Investigator", "Juggler", "Clockmaker", "Balloonist"],
hidden: ["Leviathan", "Goblin", "Drunk"],
value: `
# NQT 2: Come Fly With Me
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
)
`
}, {
name: "3a: Not Throwing Away My Shot (7-player)",
claims: ["Slayer", "Chef", "Recluse", "Investigator", "Washerwoman", "Librarian", "Empath"],
hidden: ["Imp", "Baron", "Spy", "Poisoner", "ScarletWoman", "Drunk"],
value: 
`# NQT 3a: Not Throwing Away My Shot (7-player)
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1f2jht3/weekly_puzzle_3a_3b_not_throwing_away_my_shot/

You, Aoife, Tom, Sula, Matthew, Oscar, Josh = range(7)
puzzle = Puzzle(
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
    hidden_characters=[Imp, Baron, Spy, Poisoner, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)
`
}, {
name: "3b: Not Throwing Away My Shot (8-player)",
claims: ["Slayer", "Librarian", "Investigator", "Saint", "Chef", "Recluse", "Washerwoman", "Empath"],
hidden: ["Imp", "Baron", "Spy", "Poisoner", "ScarletWoman", "Drunk"],
value:
`# NQT 3b: Not Throwing Away My Shot (8-player)
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
)
`
}, {
name: "4: The Many-Headed Monster",
claims: ["Investigator", "Empath", "Undertaker", "FortuneTeller", "Librarian", "Recluse", "Juggler", "Dreamer"],
hidden: ["LordOfTyphon", "Marionette", "Poisoner", "Drunk"],
value:
`# NQT 4: The Many-Headed Monster
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
)
`
}, {
name: "5a: You Only Guess Twice (Alsaahir)",
claims: ["Alsaahir", "Noble", "Knight", "Investigator", "Empath", "Steward", "Seamstress"],
hidden: ["Leviathan", "Goblin"],
value:
`# NQT 5a: You Only Guess Twice (Alsaahir)
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fcriex/weekly_puzzle_5a_5b_you_only_guess_twice/

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
)
`
}, {
name: "5b: You Only Guess Twice (Juggler)",
claims: ["Juggler", "Empath", "Seamstress", "Steward", "Investigator", "Noble", "Knight"],
hidden: ["Leviathan", "Goblin"],
value:
`# NQT 5b: You Only Guess Twice (Juggler)
# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fcriex/weekly_puzzle_5a_5b_you_only_guess_twice/

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
)
`
}
    ],

    "Riddles": [
        { name: "Voiceless It Cries", claims: [], hidden: [], value: "Voiceless it cries,\nWingless flutters,\nToothless bites,\nMouthless mutters." },
        { name: "What Has an Eye", claims: [], hidden: [],  value: "What has an eye, but cannot see?" },
        { name: "Tall When Young", claims: [], hidden: [],  value: "What is tall when it is young, and short when it is old?" },
        { name: "Cities, No Houses", claims: [], hidden: [],  value: "What has cities, but no houses; forests, but no trees; and water, but no fish?" }
    ],
};

const shortSamples = {
    "Townsfolk": [
        { name: "Washerwoman", value: "Player('Jasmine', claim=Washerwoman, night_info={\n    1: Washerwoman.Ping(Tim, Adam, Empath),\n}),\n" },
        { name: "Empath", value: "Player('Tim', claim=Empath, night_info={\n    1: Empath.Ping(2),\n    2: Empath.Ping(1),\n}),\n" },
        { name: "Slayer", value: "Player('Adam', claim=Slayer, day_info={\n    3: Slayer.Shot(Matthew, died=False),\n}),\n" },
    ],
    "Punctuation": [
        { name: "Period", value: "." }, { name: "Comma", value: "," }, { name: "Exclamation", value: "!" }, { name: "Question Mark", value: "?" }, 
        { name: "Semicolon", value: ";" }, { name: "Colon", value: ":" }, { name: "Apostrophe", value: "'" }, { name: "Quote", value: "\"" }
    ],
    "Brackets & Symbols": [
        { name: "Parentheses", value: "()" }, { name: "Square Brackets", value: "[]" }, { name: "Curly Braces", value: "{}" }, { name: "Angle Brackets", value: "<>" },
        { name: "Ampersand", value: "&" }, { name: "Asterisk", value: "*" }, { name: "Hashtag", value: "#" }, { name: "At Sign", value: "@" }, { name: "Percent", value: "%" }
    ],
    "Emoji Glyphs": [
        { name: "Arrow Right", value: "➡️" }, { name: "Arrow Left", value: "⬅️" }, { name: "Arrow Up", value: "⬆️" }, { name: "Arrow Down", value: "⬇️" },
        { name: "Check Mark", value: "✅" }, { name: "Cross Mark", value: "❌" }, { name: "Plus Sign", value: "➕" }, { name: "Minus Sign", value: "➖" },
        { name: "Sun", value: "☀️" }, { name: "Moon", value: "🌙" }, { name: "Star", value: "⭐" }, { name: "Fire", value: "🔥" },
        { name: "Thumbs Up", value: "👍" }, { name: "Thumbs Down", value: "👎" }, { name: "Red Heart", value: "❤️" }, { name: "Broken Heart", value: "💔" }
    ],
    "Common Glyphs": [
        { name: "Check", value: "✓" }, { name: "X", value: "✗" }, { name: "Right Arrow", value: "→" }, { name: "Left Arrow", value: "←" },
        { name: "Up Arrow", value: "↑" }, { name: "Down Arrow", value: "↓" }, { name: "Left-Right Arrow", value: "↔" }, { name: "Up-Down Arrow", value: "↕" }
    ]
};