import multiprocessing

from clockchecker import *


if __name__ == '__main__':
    # In case your OS is whack.
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')


    You, Ali, Edd, Riley, Adam, Gina, Katharine, Tom, Zak, Jodie, Jesal = range(11)
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
    )

    print(puzzle, '\n\nSolving...\n')
    count = 0
    for world in Solver().generate_worlds(puzzle):
        print(world)
        count += 1
    print(f'Found {count} worlds')
