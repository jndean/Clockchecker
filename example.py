import multiprocessing

from clockchecker import *


if __name__ == '__main__':
    # In case your OS is whack.
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')

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
    )

    print(puzzle, '\n\nSolving...\n')

    for world in Solver().generate_worlds(puzzle):
        print('Found', world)
