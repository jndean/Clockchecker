import multiprocessing

from clockchecker import *


if __name__ == '__main__':
    # In case your OS is whack.
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')


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
    )

    print(puzzle, '\n\nSolving...\n')
    count = 0
    for world in solve(puzzle):
        print(world)
        count += 1
    print(f'Found {count} worlds')