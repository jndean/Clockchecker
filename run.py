from core import *
from characters import *
from events import *
from info import *


# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gexyoq/weekly_puzzle_12a_12b_thunderstruck

You, Oscar, Anna, Josh, Fraser, Tom, Aoife, Steph = range(8)

state = State(
	players=[
		Player(name='You', claim=Librarian, night_info={
			1: Librarian.Ping(Fraser, Steph, Lunatic)
		}),
		Player(name='Oscar', claim=Investigator, night_info={
			1: Investigator.Ping(Josh, Fraser, Spy)
		}),
		Player(name='Anna', claim=Empath, night_info={
			1: Empath.Ping(1)
		}),
		Player(name='Josh', claim=Mayor),
		Player(name='Fraser', claim=Slayer),
		Player(name='Tom', claim=Dreamer, night_info={
			1: Dreamer.Ping(Steph, Lunatic, Spy)
		}),
		Player(name='Aoife', claim=Clockmaker, night_info={
			1: Clockmaker.Ping(3)
		}),
		Player(name='Steph', claim=Courtier, night_info={
			1: Courtier.Choice(Vortox)
		}),
	],
	day_events={
		1: [
			DoomsayerCall(caller=Tom, died=Josh),
			Slayer.Shot(src=Fraser, target=Steph, died=False),
			DoomsayerCall(caller=Steph, died=Oscar),
			DoomsayerCall(caller=Fraser, died=Aoife),
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


