from core import *
from characters import *
from events import *
from info import *


# https://www.reddit.com/r/BloodOnTheClocktower/comments/1g49r8j/weekly_puzzle_10_dont_overcook_it

You, Matthew, Dan, Tom, Sula, Fraser, Josh = range(7)

state = State(
	players=[
		Player(name='You', claim=Slayer),
		Player(name='Matthew', claim=Ravenkeeper, night_info={
			2: Ravenkeeper.Ping(Josh, Imp)
		}),
		Player(name='Dan', claim=Undertaker, night_info={
			2: Undertaker.Ping(Josh, Poisoner)
		}),
		Player(name='Tom', claim=FortuneTeller, night_info={
			1: FortuneTeller.Ping(Tom, Sula, demon=False),
			2: FortuneTeller.Ping(Tom, Josh, demon=True),
		}),
		Player(name='Sula', claim=Chef, night_info={
			1: Chef.Ping(0)
		}),
		Player(name='Fraser', claim=Recluse),
		Player(name='Josh', claim=WasherWoman, night_info={
			1: WasherWoman.Ping(Dan, Sula, Undertaker)
		}),
	],
	day_events={
		1: Execution(Josh),
		2: Slayer.Shot(src=You, target=Fraser, died=False),
	},
	night_deaths={2: Matthew},
)

worlds = world_gen(
	state,
	possible_demons=[Imp],
	possible_minions=[Poisoner, Spy, Baron, ScarletWoman],
	possible_hidden_good=[Drunk],
	possible_hidden_self=[Drunk],
)

valid_worlds = list(worlds)
for world in valid_worlds:
	print(world)
print(f'Found {len(valid_worlds)} valid worlds')
