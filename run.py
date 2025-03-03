from core import *
from characters import *
from events import *
from info import *


# https://www.reddit.com/r/BloodOnTheClocktower/comments/1iu1vxo/weekly_puzzle_28_a_study_in_scarlet/

You, Matt, Fraser, Aoife, Adam, Oscar, Olivia, Sarah = range(8)
state = State(
	players=[
		Player(name='You', claim=Chambermaid, night_info={
			1: Chambermaid.Ping(Adam, Sarah, 1)
		}),
		Player(name='Matt', claim=Juggler,
		  day_info={1: Juggler.Juggle({Fraser: Undertaker, Oscar: NoDashii})},
		  night_info={2: Juggler.Ping(2)},
		),
		Player(name='Fraser', claim=Undertaker, night_info={
			2: Undertaker.Ping(Aoife, NoDashii)
		}),
		Player(name='Aoife', claim=Librarian, night_info={
			1: Librarian.Ping(Matt, Adam, Drunk),
		}),
		Player(name='Adam', claim=Clockmaker, night_info={
			1: Clockmaker.Ping(4)
		}),
		Player(name='Oscar', claim=Empath, night_info={
			1: Empath.Ping(1),
			2: Empath.Ping(2),
			3: Empath.Ping(1),
		}),		
		Player(name='Olivia', claim=FortuneTeller, night_info={
			1: FortuneTeller.Ping(Olivia, Sarah, demon=False),
			2: FortuneTeller.Ping(Olivia, Aoife, demon=False),
			3: FortuneTeller.Ping(Matt, Oscar, demon=False),
		}),
		Player(name='Sarah', claim=Oracle, night_info={
			2: Oracle.Ping(1)
		}),
	],
	day_events={1: Execution(Adam), 2: Execution(Aoife)},
	night_deaths={2: You, 3: Sarah},
)
worlds = world_gen(
	state,
	possible_demons=[Pukka, NoDashii],
	possible_minions=[ScarletWoman],
	possible_hidden_good=[Drunk],
	possible_hidden_self=[Drunk],
)

valid_worlds = list(worlds)
for world in valid_worlds:
	print(world)
print(f'Found {len(valid_worlds)} valid worlds')
