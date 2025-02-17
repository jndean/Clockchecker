from enum import Enum

from core import *
from characters import *
from info import *
from events import *

if __name__ == '__main__':

	# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fj1h0c/weekly_puzzle_6_super_marionette_bros/

	You, Sarah, Tim, Dan, Aoife, Sula, Steph, Fraser, Matthew = range(9)

	state = State(
		players=[
			Player(name='You', character=Librarian(night_info={
				1: Librarian.Ping(Sula, Fraser, Drunk)
			})),
			Player(name='Sarah', character=Saint()),
			Player(name='Tim', character=Noble(night_info={
				1: Noble.Ping(Aoife, Sula, Fraser)
			})),
			Player(name='Dan', character=Seamstress(night_info={
				1: Seamstress.Ping(Aoife, Tim, same=False)
			})),
			Player(name='Aoife', character=Investigator(night_info={
				1: Investigator.Ping(Dan, Matthew, Marionette)
			})),
			Player(name='Sula', character=Juggler(
				day_info={1: Juggler.Juggle({
					You: Librarian,
					Tim: Marionette,
					Dan: Vortox,
					Fraser: Drunk,
					Matthew: Pukka,
				})},
				night_info={2: Juggler.Ping(2)}
			)),
			Player(name='Steph', character=Knight(night_info={
				1: Knight.Ping(Sarah, Dan)
			})),
			Player(name='Fraser', character=Empath(night_info={
				1: Empath.Ping(0)
			})),
			Player(name='Matthew', character=Steward(night_info={
				1: Steward.Ping(Dan)
			})),
		],
		day_events={1: Execution(Fraser, died=True)},
		night_deaths={2: Steph},
	)

	worlds = world_gen(
		state,
		possible_demons=[NoDashii, Vortox, Pukka],
		possible_minions=[Marionette],
		possible_hidden_good=[Drunk],
		possible_hidden_self=[Drunk, Marionette],
		category_counts=(5, 2, 1, 1), # townsfolk, outsiders, minions, demons
	)

	for world in worlds:
		print(world)

