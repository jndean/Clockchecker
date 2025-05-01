import multiprocessing

from clockchecker import *


if __name__ == '__main__':
	# In case your OS is whack.
	multiprocessing.freeze_support()
	multiprocessing.set_start_method('spawn')

	# https://www.reddit.com/r/BloodOnTheClocktower/comments/1joxqgy/weekly_puzzle_34_the_vortox_conjecture/
	You, Fraser, Steph, Sula, Sarah, Josh, Aoife = range(7)
	puzzle = Puzzle(
        players=[
            Player('You', claim=Mathematician, night_info={
                1: Mathematician.Ping(1),
                2: Mathematician.Ping(0),
            }),
            Player('Fraser', claim=Sage, night_info={
                2: Sage.Ping(Sarah, Josh),
            }),
            Player('Steph', claim=Artist, day_info={
                1: Artist.Ping(IsCharacter(Aoife, NoDashii)),
            }),
            Player('Sula', claim=Clockmaker, night_info={
                1: Clockmaker.Ping(3),
            }),
            Player('Sarah', claim=Seamstress, night_info={
                1: Seamstress.Ping(Steph, Aoife, same=True),
            }),
            Player('Josh', claim=Juggler, 
                day_info={1: Juggler.Juggle({Steph: Artist, Sula: Clockmaker})},
                night_info={2: Juggler.Ping(0)},
            ),
            Player('Aoife', claim=SnakeCharmer, night_info={
                1: SnakeCharmer.Choice(Josh),
            }),
        ],
        day_events={
            1: [
                Dies(player=Steph, after_nominating=True), 
                Execution(Aoife),
            ]
        },
        night_deaths={2: Fraser},
        demons=[NoDashii, Vortox],
        minions=[Witch],
        hidden_good=[],
        hidden_self=[],
    )


	for world in Solver().generate_worlds(puzzle):
		print(world)

