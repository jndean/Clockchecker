import multiprocessing

from clockchecker import *


if __name__ == '__main__':
    # In case your OS is whack.
    multiprocessing.freeze_support()
    multiprocessing.set_start_method('spawn')

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
        hidden_self=[Lunatic],
    )

    print(puzzle, '\n\nSolving...\n')

    for world in Solver(num_processes=4).generate_worlds(puzzle):
        print(world)