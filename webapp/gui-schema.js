/**
 * GUI Schema for ClockChecker Puzzle Builder
 * 
 * This schema defines all the elements available in the puzzle builder GUI,
 * including characters, info types, events, and their field definitions.
 * 
 * Future: This could be auto-generated from the Python source files.
 */

const GuiSchema = {

    // Character categories
    characters: {
        Townsfolk: [
            'Acrobat', 'Alsaahir', 'Artist', 'Atheist', 'Balloonist', 'Chambermaid',
            'Chef', 'Clockmaker', 'Courtier', 'Dreamer', 'Empath', 'Exorcist',
            'Flowergirl', 'FortuneTeller', 'Gambler', 'Gossip', 'Investigator',
            'Juggler', 'Knight', 'Librarian', 'Mathematician', 'Mayor', 'Monk',
            'NightWatchman', 'Noble', 'Oracle', 'Philosopher', 'PoppyGrower',
            'Princess', 'Ravenkeeper', 'Sage', 'Savant', 'Seamstress', 'Shugenja',
            'Slayer', 'SnakeCharmer', 'Soldier', 'Steward', 'Undertaker',
            'VillageIdiot', 'Virgin', 'Washerwoman'
        ],
        Outsiders: [
            'Butler', 'Drunk', 'Golem', 'Hermit', 'Klutz', 'Lunatic', 'Mutant',
            'Politician', 'Puzzlemaster', 'Recluse', 'Saint', 'Sweetheart'
        ],
        Minions: [
            'Baron', 'Boffin', 'Cerenovus', 'EvilTwin', 'Goblin', 'Marionette',
            'PitHag', 'Poisoner', 'ScarletWoman', 'Spy', 'Widow', 'Witch', 'Xaan'
        ],
        Demons: [
            'FangGu', 'Imp', 'Kazali', 'Leviathan', 'LordOfTyphon', 'NoDashii',
            'Po', 'Pukka', 'Riot', 'Vigormortis', 'Vortox'
        ],
        Homebrews: [
            'Progidy'
        ]
    },

    // Flatten characters for easy lookup
    get allCharacters() {
        return [
            ...this.characters.Townsfolk,
            ...this.characters.Outsiders,
            ...this.characters.Minions,
            ...this.characters.Demons,
            ...this.characters.Homebrews
        ];
    },

    // Category classifications
    categories: ['Townsfolk', 'Outsider', 'Minion', 'Demon'],

    // Info types that can be added to night_info or day_info
    // Grouped by the character that provides them
    infoTypes: {
        // Night info types (character abilities)
        night: {
            // Format: 'CharacterName': { fields: [...], template: '...' }
            'Acrobat.Choice': {
                fields: [{ name: 'player', type: 'player', label: 'Chose Player' }],
                template: 'Acrobat.Choice({player})'
            },
            'Balloonist.Ping': {
                fields: [{ name: 'player', type: 'player', label: 'Saw Player' }],
                template: 'Balloonist.Ping({player})'
            },
            'Chambermaid.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Player 1' },
                    { name: 'player2', type: 'player', label: 'Player 2' },
                    { name: 'count', type: 'number', label: 'Count', min: 0, max: 2 }
                ],
                template: 'Chambermaid.Ping({player1}, {player2}, {count})'
            },
            'Chef.Ping': {
                fields: [{ name: 'count', type: 'number', label: 'Evil Pairs', min: 0, max: 10 }],
                template: 'Chef.Ping({count})'
            },
            'Clockmaker.Ping': {
                fields: [{ name: 'distance', type: 'number', label: 'Distance', min: 1, max: 10 }],
                template: 'Clockmaker.Ping({distance})'
            },
            'Courtier.Choice': {
                fields: [{ name: 'character', type: 'character', label: 'Chose Character' }],
                template: 'Courtier.Choice({character})'
            },
            'Dreamer.Ping': {
                fields: [
                    { name: 'player', type: 'player', label: 'About Player' },
                    { name: 'char1', type: 'character', label: 'Character 1' },
                    { name: 'char2', type: 'character', label: 'Character 2' }
                ],
                template: 'Dreamer.Ping({player}, {char1}, {char2})'
            },
            'Empath.Ping': {
                fields: [{ name: 'count', type: 'number', label: 'Evil Neighbours', min: 0, max: 2 }],
                template: 'Empath.Ping({count})'
            },
            'Exorcist.Choice': {
                fields: [{ name: 'player', type: 'player', label: 'Chose Player' }],
                template: 'Exorcist.Choice({player})'
            },
            'Flowergirl.Ping': {
                fields: [{ name: 'voted', type: 'bool', label: 'Demon Voted' }],
                template: 'Flowergirl.Ping({voted})'
            },
            'FortuneTeller.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Player 1' },
                    { name: 'player2', type: 'player', label: 'Player 2' },
                    { name: 'demon', type: 'bool', label: 'Saw Demon' }
                ],
                template: 'FortuneTeller.Ping({player1}, {player2}, demon={demon})'
            },
            'Gambler.Gamble': {
                fields: [
                    { name: 'player', type: 'player', label: 'Guessed Player' },
                    { name: 'character', type: 'character', label: 'Guessed As' }
                ],
                template: 'Gambler.Gamble({player}, {character})'
            },
            'Investigator.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Player 1' },
                    { name: 'player2', type: 'player', label: 'Player 2' },
                    { name: 'minion', type: 'character', label: 'Minion Type', category: 'Minions' }
                ],
                template: 'Investigator.Ping({player1}, {player2}, {minion})'
            },
            'Juggler.Ping': {
                fields: [{ name: 'count', type: 'number', label: 'Correct Juggles', min: 0, max: 5 }],
                template: 'Juggler.Ping({count})'
            },
            'Knight.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Good Player 1' },
                    { name: 'player2', type: 'player', label: 'Good Player 2' }
                ],
                template: 'Knight.Ping({player1}, {player2})'
            },
            'Librarian.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Player 1', nullable: true },
                    { name: 'player2', type: 'player', label: 'Player 2', nullable: true },
                    { name: 'outsider', type: 'character', label: 'Outsider Type', category: 'Outsiders', nullable: true }
                ],
                template: 'Librarian.Ping({player1}, {player2}, {outsider})',
                nullTemplate: 'Librarian.Ping(None)'
            },
            'Mathematician.Ping': {
                fields: [{ name: 'count', type: 'number', label: 'Malfunctions', min: 0, max: 10 }],
                template: 'Mathematician.Ping({count})'
            },
            'Monk.Choice': {
                fields: [{ name: 'player', type: 'player', label: 'Protected Player' }],
                template: 'Monk.Choice({player})'
            },
            'NightWatchman.Choice': {
                fields: [{ name: 'player', type: 'player', label: 'Chose Player' }],
                template: 'NightWatchman.Choice({player})'
            },
            'NightWatchman.Ping': {
                fields: [{ name: 'player', type: 'player', label: 'Pinged By' }],
                template: 'NightWatchman.Ping({player})'
            },
            'Noble.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Player 1' },
                    { name: 'player2', type: 'player', label: 'Player 2' },
                    { name: 'player3', type: 'player', label: 'Player 3' }
                ],
                template: 'Noble.Ping({player1}, {player2}, {player3})'
            },
            'Oracle.Ping': {
                fields: [{ name: 'count', type: 'number', label: 'Dead Evil', min: 0, max: 10 }],
                template: 'Oracle.Ping({count})'
            },
            'Philosopher.Choice': {
                fields: [{ name: 'character', type: 'character', label: 'Became Character' }],
                template: 'Philosopher.Choice({character})'
            },
            'Ravenkeeper.Ping': {
                fields: [
                    { name: 'player', type: 'player', label: 'Chose Player' },
                    { name: 'character', type: 'character', label: 'Saw Character' }
                ],
                template: 'Ravenkeeper.Ping({player}, {character})'
            },
            'Sage.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Player 1' },
                    { name: 'player2', type: 'player', label: 'Player 2' }
                ],
                template: 'Sage.Ping({player1}, {player2})'
            },
            'Seamstress.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Player 1' },
                    { name: 'player2', type: 'player', label: 'Player 2' },
                    { name: 'same', type: 'bool', label: 'Same Alignment' }
                ],
                template: 'Seamstress.Ping({player1}, {player2}, same={same})'
            },
            'Shugenja.Ping': {
                fields: [{ name: 'clockwise', type: 'bool', label: 'Clockwise' }],
                template: 'Shugenja.Ping(clockwise={clockwise})'
            },
            'SnakeCharmer.Choice': {
                fields: [{ name: 'player', type: 'player', label: 'Chose Player' }],
                template: 'SnakeCharmer.Choice({player})'
            },
            'Steward.Ping': {
                fields: [{ name: 'player', type: 'player', label: 'Good Player' }],
                template: 'Steward.Ping({player})'
            },
            'Undertaker.Ping': {
                fields: [
                    { name: 'player', type: 'player', label: 'Executed Player' },
                    { name: 'character', type: 'character', label: 'Saw Character' }
                ],
                template: 'Undertaker.Ping({player}, {character})'
            },
            'VillageIdiot.Ping': {
                fields: [
                    { name: 'player', type: 'player', label: 'About Player' },
                    { name: 'is_evil', type: 'bool', label: 'Is Evil' }
                ],
                template: 'VillageIdiot.Ping({player}, is_evil={is_evil})'
            },
            'Washerwoman.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Player 1' },
                    { name: 'player2', type: 'player', label: 'Player 2' },
                    { name: 'townsfolk', type: 'character', label: 'Townsfolk Type', category: 'Townsfolk' }
                ],
                template: 'Washerwoman.Ping({player1}, {player2}, {townsfolk})'
            },
            // Evil info
            'EvilTwin.Is': {
                fields: [{ name: 'player', type: 'player', label: 'Twin Player' }],
                template: 'EvilTwin.Is({player})'
            },
            'Cerenovus.Mad': {
                fields: [{ name: 'character', type: 'character', label: 'Mad As Character' }],
                template: 'Cerenovus.Mad({character})'
            },
            'CharacterChange': {
                fields: [{ name: 'character', type: 'character', label: 'New Character' }],
                template: 'CharacterChange({character})'
            },
            'Widow.InPlay': {
                fields: [],
                template: 'Widow.InPlay()'
            },
            'PoppyGrower.InPlay': {
                fields: [],
                template: 'PoppyGrower.InPlay()'
            },
            'Progidy.Ping': {
                fields: [
                    { name: 'player1', type: 'player', label: 'Player 1' },
                    { name: 'player2', type: 'player', label: 'Player 2' }
                ],
                template: 'Progidy.Ping({player1}, {player2})'
            }
        },

        // Day info types
        day: {
            'Artist.Ping': {
                fields: [{ name: 'infoExpr', type: 'info', label: 'Question Answer' }],
                template: 'Artist.Ping({infoExpr})'
            },
            'Slayer.Shot': {
                fields: [
                    { name: 'target', type: 'player', label: 'Target' },
                    { name: 'died', type: 'bool', label: 'Target Died' }
                ],
                template: 'Slayer.Shot({target}, died={died})'
            },
            'Savant.Ping': {
                fields: [
                    { name: 'statement1', type: 'info', label: 'Statement 1' },
                    { name: 'statement2', type: 'info', label: 'Statement 2' }
                ],
                template: 'Savant.Ping(\n    {statement1},\n    {statement2}\n)'
            },
            'Juggler.Juggle': {
                fields: [{ name: 'juggle', type: 'juggle', label: 'Juggles' }],
                template: 'Juggler.Juggle({juggle})'
            },
            'Flowergirl.Voters': {
                fields: [{ name: 'voters', type: 'playerList', label: 'Voters' }],
                template: 'Flowergirl.Voters([{voters}])'
            },
            'Gossip.Gossip': {
                fields: [{ name: 'statement', type: 'info', label: 'Statement' }],
                template: 'Gossip.Gossip({statement})'
            },
            'Klutz.Choice': {
                fields: [
                    { name: 'player', type: 'player', label: 'Klutz Player' },
                    { name: 'choice', type: 'player', label: 'Chosen Player' }
                ],
                template: 'Klutz.Choice(player={player}, choice={choice})'
            },
            'Puzzlemaster.Ping': {
                fields: [
                    { name: 'guess', type: 'player', label: 'Guessed Drunk' },
                    { name: 'demon', type: 'player', label: 'Demon Learned' }
                ],
                template: 'Puzzlemaster.Ping(guess={guess}, demon={demon})'
            },
            'UneventfulNomination': {
                fields: [{ name: 'player', type: 'player', label: 'Nominated By' }],
                template: 'UneventfulNomination({player})'
            },
            'ExecutionByST': {
                fields: [
                    { name: 'player', type: 'player', label: 'Player Executed' },
                    { name: 'after_nominating', type: 'player', label: 'After Nominating', optional: true }
                ],
                template: 'ExecutionByST({player})'
            },
            'Dies': {
                fields: [{ name: 'after_nominating', type: 'bool', label: 'After Nominating' }],
                template: 'Dies(after_nominating={after_nominating})'
            }
        }
    },

    // Day events (puzzle-level, not player-level)
    dayEvents: {
        'Execution': {
            fields: [
                { name: 'player', type: 'player', label: 'Player' },
                { name: 'died', type: 'bool', label: 'Died', default: true }
            ],
            template: 'Execution({player}, died={died})',
            simpleTemplate: 'Execution({player})'
        },
        'Slayer.Shot': {
            fields: [
                { name: 'player', type: 'player', label: 'Slayer' },
                { name: 'target', type: 'player', label: 'Target' },
                { name: 'died', type: 'bool', label: 'Target Died' }
            ],
            template: 'Slayer.Shot(player={player}, target={target}, died={died})'
        },
        'Doomsayer.Call': {
            fields: [
                { name: 'player', type: 'player', label: 'Called By' },
                { name: 'died', type: 'player', label: 'Who Died' }
            ],
            template: 'Doomsayer.Call(player={player}, died={died})'
        },
        'Dies': {
            fields: [
                { name: 'player', type: 'player', label: 'Player', optional: true },
                { name: 'after_nominating', type: 'bool', label: 'After Nominating', optional: true },
                { name: 'after_nominated_by', type: 'player', label: 'After Nominated By', optional: true }
            ],
            template: 'Dies(player={player}, after_nominating={after_nominating}, after_nominated_by={after_nominated_by})'
        },
        'ExecutionByST': {
            fields: [
                { name: 'player', type: 'player', label: 'Player' },
                { name: 'after_nominating', type: 'player', label: 'After Nominating', optional: true },
                { name: 'died', type: 'bool', label: 'Died', default: true }
            ],
            template: 'ExecutionByST({player}, after_nominating={after_nominating}, died={died})',
            simpleTemplate: 'ExecutionByST({player}, after_nominating={after_nominating})'
        }
    },

    // Info expression types (for Savant, Artist, Gossip)
    infoExpressions: {
        'IsEvil': {
            fields: [{ name: 'player', type: 'player', label: 'Player' }],
            template: 'IsEvil({player})'
        },
        'IsCharacter': {
            fields: [
                { name: 'player', type: 'player', label: 'Player' },
                { name: 'character', type: 'character', label: 'Character' }
            ],
            template: 'IsCharacter({player}, {character})'
        },
        'IsCategory': {
            fields: [
                { name: 'player', type: 'player', label: 'Player' },
                { name: 'category', type: 'category', label: 'Category' }
            ],
            template: 'IsCategory({player}, {category})'
        },
        'IsInPlay': {
            fields: [{ name: 'character', type: 'character', label: 'Character' }],
            template: 'IsInPlay({character})'
        },
        'Chef.Ping': {
            fields: [{ name: 'count', type: 'number', label: 'Count' }],
            template: 'Chef.Ping({count})'
        },
        'Clockmaker.Ping': {
            fields: [{ name: 'distance', type: 'number', label: 'Distance' }],
            template: 'Clockmaker.Ping({distance})'
        },
        'DrunkBetweenTownsfolk': {
            fields: [],
            template: 'DrunkBetweenTownsfolk()'
        },
        'LongestRowOfTownsfolk': {
            fields: [{ name: 'length', type: 'number', label: 'Length' }],
            template: 'LongestRowOfTownsfolk({length})'
        },
        'ExactlyN': {
            fields: [
                { name: 'N', type: 'number', label: 'N' },
                { name: 'args', type: 'infoList', label: 'Statements' }
            ],
            template: 'ExactlyN(N={N}, args=[{args}])'
        }
    },

    // Helper to get character color class
    getCharacterColorClass(char) {
        if (this.characters.Minions.includes(char) || this.characters.Demons.includes(char)) {
            return 'evil-character';
        }
        if (this.characters.Outsiders.includes(char)) {
            return 'outsider-character';
        }
        return 'townsfolk-character';
    },

    // Helper to get relevant info types for a character
    getInfoTypesForCharacter(character, phase) {
        const types = phase === 'night' ? this.infoTypes.night : this.infoTypes.day;
        const relevant = [];
        for (const [key, value] of Object.entries(types)) {
            // Include character-specific info types
            if (key.startsWith(character + '.')) {
                relevant.push({ key, ...value });
            }
        }
        return relevant;
    },

    // Helper to get all info types for a phase
    getAllInfoTypes(phase) {
        const types = phase === 'night' ? this.infoTypes.night : this.infoTypes.day;
        return Object.entries(types).map(([key, value]) => ({ key, ...value }));
    }
};

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = GuiSchema;
}
