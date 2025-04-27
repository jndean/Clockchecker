import multiprocessing

from clockchecker import *


if __name__ == '__main__':
	# In case your OS is whack.
	multiprocessing.freeze_support()
	multiprocessing.set_start_method('spawn')


	# https://www.reddit.com/r/BloodOnTheClocktower/comments/1hb72qg/weekly_puzzle_18_starring_the_xaan/
	You, Steph, Fraser, Dan, Aoife, Tim, Olivia, Sarah = range(8)
	state = State(
		players= [
			Player('You', claim=Librarian, night_info={
				1: Librarian.Ping(Aoife, Tim, Drunk),
			}),
			Player('Steph', claim=Juggler, 
				day_info={1: Juggler.Juggle({
					Fraser: Leviathan,
					Aoife: Balloonist,
					Tim: Xaan,
				})},
				night_info={2: Juggler.Ping(2)},
			),
			Player('Fraser', claim=SnakeCharmer, night_info={
				1: SnakeCharmer.Choice(Olivia),
				2: SnakeCharmer.Choice(Steph),
				3: SnakeCharmer.Choice(Aoife),
			}),
			Player('Dan', claim=FortuneTeller, night_info={
				1: FortuneTeller.Ping(Tim, Sarah, demon=False),
				2: FortuneTeller.Ping(Steph, Aoife, demon=False),
				3: FortuneTeller.Ping(Fraser, Olivia, demon=False),
			}),
            Player('Aoife', claim=Balloonist, night_info={
                1: Balloonist.Ping(Olivia),
                2: Balloonist.Ping(Aoife),
                3: Balloonist.Ping(You),
            }),
			Player('Tim', claim=Saint),
			Player('Olivia', claim=Investigator, night_info={
				1: Investigator.Ping(Fraser, Aoife, Xaan),
			}),
			Player('Sarah', claim=Recluse),
		],
	)
	puzzle = Puzzle(
		state,
		possible_demons=[Leviathan],
		possible_minions=[Xaan],
		possible_hidden_good=[Drunk],
		possible_hidden_self=[Drunk],
	)


	with Solver() as solver:
		count = 0
		for world in solver.generate_worlds(puzzle):
			print(world)
			count += 1
		print(f'Found {count} worlds')
