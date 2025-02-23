from core import *
from characters import *
from events import *
from info import *

# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gexyoq/weekly_puzzle_12a_12b_thunderstruck

You, Tim, Fraser, Hannah, Sarah, Jasmine = range(6)
state = State(
	players=[
		Player(name='You', character=Dreamer(night_info={
			1: Dreamer.Ping(Sarah, Lunatic, ScarletWoman)
		})),
		Player(name='Tim', character=Clockmaker(night_info={
			1: Clockmaker.Ping(2)
		})),
		Player(name='Fraser', character=Empath(night_info={
			1: Empath.Ping(0)
		})),
		Player(name='Hannah', character=Slayer()),
		Player(name='Sarah', character=Courtier(night_info={
			1: Courtier.Choice(Vortox)
		})),
		Player(name='Jasmine', character=Mayor()),
	],
	day_events={
		1: [
			DoomsayerCall(caller=Hannah, died=Tim),
			Slayer.Shot(src=Hannah, target=Fraser, died=False),
			DoomsayerCall(caller=You, died=Sarah),
		]
	},
)

worlds = world_gen(
	state,
	possible_demons=[Vortox],
	possible_minions=[Spy, ScarletWoman],
	possible_hidden_good=[Lunatic],
	possible_hidden_self=[],
)

valid_worlds = list(worlds)
for world in valid_worlds:
	print(world)
print(f'Found {len(valid_worlds)} valid worlds')


# # https://www.reddit.com/r/BloodOnTheClocktower/comments/1gexyoq/weekly_puzzle_12a_12b_thunderstruck

# You, Oscar, Anna, Josh, Fraser, Tom, Aoife, Steph = range(8)

# state = State(
# 	players=[
# 		Player(name='You', character=Librarian(), night_info={
# 			1: Librarian.Ping(Fraser, Steph, Lunatic)
# 		}),
# 		Player(name='Oscar', character=Investigator(), night_info={
# 			1: Investigator.Ping(Josh, Fraser, Spy)
# 		}),
# 		Player(name='Anna', character=Empath(), night_info={
# 			1: Empath.Ping(1)
# 		}),
# 		Player(name='Josh', character=Mayor()),
# 		Player(name='Fraser', character=Slayer()),
# 		Player(name='Tom', character=Dreamer(), night_info={
# 			1: Dreamer.Ping(Steph, Lunatic, Spy)
# 		}),
# 		Player(name='Aoife', character=Clockmaker(), night_info={
# 			1: Clockmaker.Ping(3)
# 		}),
# 		Player(name='Steph', character=Courtier(), night_info={
# 			1: Courtier.Choice(Vortox)
# 		}),
# 	],
# 	day_events={
# 		1: [
# 			DoomsayerCall(caller=Tom, died=Josh),
# 			Slayer.Shot(src=Fraser, target=Steph, died=False),
# 			# DoomsayerCall(caller=Steph, died=Oscar),
# 			DoomsayerCall(caller=Fraser, died=Aoife),
# 		]
# 	},
# )

# worlds = world_gen(
# 	state,
# 	possible_demons=[Vortox],
# 	possible_minions=[Spy, ScarletWoman],
# 	possible_hidden_good=[Lunatic],
# 	possible_hidden_self=[],
# )


# valid_worlds = list(worlds)
# for world in valid_worlds:
# 	print(world)
# print(f'Found {len(valid_worlds)} valid worlds')

