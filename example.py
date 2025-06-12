import multiprocessing
from time import time

from clockchecker import *


if __name__ == '__main__':
    # In case your OS is whack.
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')

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
    )


    print(puzzle, '\n\nSolving...\n')
    start = time()

    count = 0
    for world in solve(puzzle):
        print(world)
        count += 1
    print(f'Found {count} worlds in {time() - start:0.2f}s')
