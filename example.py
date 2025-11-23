import multiprocessing

from clockchecker import *


if __name__ == '__main__':
    # In case your OS is whack.
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')


    # This game was played on a TPI stream. We write the puzzle from Amy's
    # perspective (i.e., player 0 (You) is actually Amy)
    You, Ethan, Barrow, Lyra, JC, Emerald, Sincerity, Eevee = range(8)
    puzzle = Puzzle(
        players=[
            Player('You', claim=Dreamer, night_info={
                1: Dreamer.Ping(Eevee, Seamstress, Vigormortis),
                2: Dreamer.Ping(JC, Oracle, NoDashii),
                3: Dreamer.Ping(Lyra, Sage, Vigormortis),
            }),
            Player('Ethan', claim=SnakeCharmer, night_info={
                1: SnakeCharmer.Choice(Barrow),
            }),
            Player('Barrow', claim=Artist, day_info={
                # Barrow didn't really claim to have asked a question
            }),
            Player('Lyra', claim=Sage, night_info={
                3: Sage.Ping(You, Eevee),
            }),
            Player('JC', claim=Oracle, night_info={
                2: Oracle.Ping(1),
                3: Oracle.Ping(1),
            }),
            Player('Emerald', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(2)
            }),
            Player('Sincerity', claim=Mathematician, night_info={
                1: Mathematician.Ping(0),
                2: Mathematician.Ping(0),
            }),
            Player('Eevee', claim=Seamstress, night_info={
                2: Seamstress.Ping(Emerald, You, same=False),
            }),
        ],
        day_events={
            1: Execution(Ethan),
            2: Execution(Sincerity),
            3: Dies(player=JC, after_nominating=True),
        },
        night_deaths={2: Barrow, 3: Lyra},
        hidden_characters=[Vigormortis, NoDashii, Vortox, Witch, Mutant],
        hidden_self=[],
    )

    You, Matthew, Fraser, Steph, Josh, Anna, Tim, Oscar = range(8)
    puzzle = Puzzle(
        players=[
            Player('You', claim=Savant, day_info={
                1: Savant.Ping(
                    LongestRowOfTownsfolk(3),
                    IsInPlay(NoDashii) & IsInPlay(Witch) & Clockmaker.Ping(3),
                ),
                2: Savant.Ping(
                    ExactlyN(N=2, args=[
                        IsCategory(Steph, Townsfolk),
                        IsCategory(Josh, Townsfolk),
                        IsCategory(Oscar, Townsfolk),
                    ]),
                    CharacterTypesAmongPlayers([Matthew, Steph, Josh, Tim], 2)
                ),
            }),
            Player('Matthew', claim=Seamstress, night_info={
                1: Seamstress.Ping(Fraser, Anna, same=True),
            }),
            Player('Fraser', claim=Mathematician, night_info={
                1: Mathematician.Ping(2),
                2: Mathematician.Ping(2),
                3: Mathematician.Ping(2),
            }),
            Player('Steph', claim=Sweetheart),
            Player('Josh', claim=Juggler,
                day_info={
                    1: Juggler.Juggle({
                        You: Savant,
                        Matthew: Vigormortis,
                        Fraser: Mathematician,
                        Steph: Witch,
                        Tim: FangGu,
                    })
                },
                night_info={2: Juggler.Ping(0)}
            ),
            Player('Anna', claim=Oracle, night_info={
                2: Oracle.Ping(0),
                3: Oracle.Ping(0),
            }),
            Player('Tim', claim=Dreamer, night_info={
                1: Dreamer.Ping(Fraser, Mathematician, Witch),
                2: Dreamer.Ping(Josh, Mutant, FangGu),
            }),
            Player('Oscar', claim=SnakeCharmer, night_info={
                1: SnakeCharmer.Choice(Fraser),
            }),
            
        ],
        day_events={
            1: [
                Dies(player=Oscar, after_nominating=True),
                Execution(Matthew),
            ],
            2: Execution(You),
        },
        night_deaths={2: Steph, 3: Tim},
        hidden_characters=[FangGu, Vigormortis, NoDashii, Vortox, Witch, Mutant],
        hidden_self=[],
    )


    print(puzzle, '\n\nSolving...\n')
    count = 0
    for world in solve(puzzle):
        print(world)
        count += 1
    print(f'Found {count} worlds')
