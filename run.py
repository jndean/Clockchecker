from enum import Enum

from core import *
from characters import *
from info import *
from events import *

if __name__ == '__main__':


	# # https://www.reddit.com/r/BloodOnTheClocktower/comments/1f2jht3/weekly_puzzle_3a_3b_not_throwing_away_my_shot/
	# You, Aoife, Tom, Sula, Matthew, Oscar, Josh = range(7)

	# state = State([
	# 	Player(name='You', character=Slayer(day_actions={
	# 		0: Slayer.Shot(Tom, died=True)
	# 	})),
	# 	Player(name='Aoife', character=Chef(night_info={
	# 		0: Chef.Ping(0)
	# 	})),
	# 	Player(name='Tom', character=Recluse()),
	# 	Player(name='Sula', character=Investigator(night_info={
	# 		0: Investigator.Ping(You, Aoife, Baron)
	# 	})),
	# 	Player(name='Matthew', character=WasherWoman(night_info={
	# 		0: WasherWoman.Ping(Aoife, Oscar, Librarian),
	# 	})),
	# 	Player(name='Oscar', character=Librarian(night_info={
	# 		0: Librarian.Ping(None)
	# 	})),
	# 	Player(name='Josh', character=Empath(night_info={
	# 		0: Empath.Ping(0)
	# 	})),
	# ])

	# worlds = list(world_gen(
	# 	state,
	# 	possible_demons=[Imp],
	# 	possible_minions=[Baron, Spy, Poisoner, ScarletWoman],
	# 	possible_hidden_good=[Drunk],
	# 	possible_hidden_self=[Drunk],
	# 	category_counts=(5, 0, 1, 1), # townsfolk, outsiders, minions, demons
	# ))

	# for world in worlds:
	# 	print(world)
	# print(f'\nTotal Candidate Worlds: {len(worlds)}\n')

	# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gka3js/weekly_puzzle_13_clockblocking/?rdt=47879
	You, Jasmine, Oscar, Tim, Sarah, Fraser, Aoife = range(7)

	state = State(
		players=[
			Player(name='You', character=Investigator(night_info={
				1: Investigator.Ping(Sarah, Aoife, ScarletWoman)
			})),
			Player(name='Jasmine', character=Clockmaker(night_info={
				1: Clockmaker.Ping(3)
			})),
			Player(name='Oscar', character=Librarian(night_info={
				1: Librarian.Ping(None)
			})),
			Player(name='Tim', character=Ravenkeeper(night_info={
				2: Ravenkeeper.Ping(Oscar, Librarian)
			})),
			Player(name='Sarah', character=FortuneTeller(night_info={
				1: FortuneTeller.Ping(You, Oscar, demon=False),
				2: FortuneTeller.Ping(You, Jasmine, demon=False),
			})),
			Player(name='Fraser', character=Slayer()),
			Player(name='Aoife', character=Recluse()),
		],
		day_events={
			1: [
				Slayer.Shot(src=Fraser, target=Oscar, died=False),
				Execution(Aoife, died=True)
			],
		},
		night_deaths={
			2: Tim,
		},
	)

	worlds = list(world_gen(
		state,
		possible_demons=[Imp],
		possible_minions=[Baron, Spy, ScarletWoman, Poisoner],
		possible_hidden_good=[Drunk],
		possible_hidden_self=[Drunk],
		category_counts=(5, 0, 1, 1), # townsfolk, outsiders, minions, demons
	))

	for world in worlds:
		print(world)
	print(f'\nTotal Candidate Worlds: {len(worlds)}\n')

