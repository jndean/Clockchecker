import multiprocessing
from time import time

from clockchecker import *


if __name__ == '__main__':
    # In case your OS is whack.
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')

    You, Tesso, Beardy, Emerald, Alanna, Aero, Sam, Theo, Karen= range(9)
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
                # day_info={
                #     1: Flowergirl.Voters([Tesso, Beardy, Emerald, Alanna, Aero, Sam]),
                #     2: Flowergirl.Voters([Emerald, Alanna, Sam, Theo, Karen]),
                #     3: Flowergirl.Voters([Beardy, Karen, Tesso]),
                # },
                # night_info={
                #     2: Flowergirl.Ping(True),
                #     3: Flowergirl.Ping(False),
                #     4: Flowergirl.Ping(True),
                # }
            ),
            Player('Alanna', claim=Oracle, night_info={
                2: Oracle.Ping(0),
                3: Oracle.Ping(1),
            }),
            Player('Aero', claim=Artist, night_info={
                # 1: Artist.Ping(IsInPlay(NoDashii))
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
                    IsInPlay(Po),  # TODO: Don't support Vigormortis
                    IsCharacter(Aero, Artist),
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
        hidden_characters=[NoDashii, Vortox, FangGu, Witch, Mutant, Drunk],
        hidden_self=[],
        deduplicate_initial_characters=True,
    )


    print(puzzle, '\n\nSolving...\n')
    start = time()

    count = 0
    for world in solve(puzzle):
        print(world)
        count += 1
    print(f'Found {count} worlds in {time() - start:0.2f}s')
