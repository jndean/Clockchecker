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
    
    You, B, C, D = range(4)
    puzzle = Puzzle(
        players=[
            Player('You', claim=Artist, day_info={
                1: Artist.Ping(
                    IsCharacter(B, Leviathan)
                    & IsCharacter(C, PitHag)
                    & IsCharacter(D, Dreamer)
                )
            }),
            Player('B', claim=Empath, night_info={
                1: Empath.Ping(0),
            }),
            Player('C', claim=Empath, night_info={
                1: Empath.Ping(0),
            }),
            Player('D', claim=Dreamer, night_info={
                1: Dreamer.Ping(C, PitHag, Artist),
                2: Dreamer.Ping(B, Imp, Artist),
            }),
        ],
        day_events={},
        night_deaths={},
        hidden_characters=[Leviathan, PitHag, Baron, Imp],
        hidden_self=[],
        category_counts=(2, 0, 1, 1),
    )

    print(puzzle, '\n\nSolving...\n')
    count = 0
    for world in solve(puzzle):
        print(world)
        count += 1
    print(f'Found {count} worlds')
