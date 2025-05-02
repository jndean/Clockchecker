import multiprocessing

from clockchecker import *


if __name__ == '__main__':
	# In case your OS is whack.
	multiprocessing.freeze_support()
	multiprocessing.set_start_method('spawn')

	# https://www.reddit.com/r/BloodOnTheClocktower/comments/1kccbp9/weekly_puzzle_38_snakes_on_a_plane/
	You, Hannah, Dan, Adam, Tim, Fraser, Sula, Matt = range(8)
	puzzle = Puzzle(
        players=[
            Player('You', claim=Recluse),
            Player('Hannah', claim=Empath, night_info={
                1: Empath.Ping(0),
                2: Empath.Ping(1),
                3: Empath.Ping(1),
            }),
            Player('Dan', claim=Ravenkeeper, night_info={
                2: Ravenkeeper.Ping(Fraser, Poisoner),
            }),
            Player('Adam', claim=Investigator, night_info={
                1: Investigator.Ping(Tim, Sula, Baron),
            }),
            Player('Tim', claim=SnakeCharmer, night_info={
                1: SnakeCharmer.Choice(Matt),
                2: SnakeCharmer.Choice(Sula),
                3: SnakeCharmer.Choice(Hannah),
            }),
            Player('Fraser', claim=SnakeCharmer, night_info={
                1: SnakeCharmer.Choice(Sula),
                2: SnakeCharmer.Choice(Hannah),
                3: SnakeCharmer.Choice(Adam),
            }),
            Player('Sula', claim=FortuneTeller, night_info={
                1: FortuneTeller.Ping(You, Tim, False),
                2: FortuneTeller.Ping(Fraser, Matt, False),
            }),
			Player('Matt', claim=Saint),
        ],
        day_events={1: Execution(You), 2: Execution(Sula)},
        night_deaths={2: Dan, 3: Matt},
        demons=[Imp],
        minions=[Baron, Spy, Poisoner, ScarletWoman],
        hidden_good=[Drunk],
        hidden_self=[],
    )


	for world in Solver().generate_worlds(puzzle):
		print(world)

