from enum import Enum

from core import *
from characters import *
from info import *
from events import *

if __name__ == '__main__':

	# https://www.reddit.com/r/BloodOnTheClocktower/comments/1f823s4/weekly_puzzle_4_the_manyheaded_monster/

	You, Anna, Dan, Fraser, Sarah, Tim, Matt, Hannah = range(8)

	state = State(
		players=[
			Player(name='You', character=Investigator(night_info={
				1: Investigator.Ping(Matt, Hannah, Marionette)
			})),
			Player(name='Anna', character=Empath(night_info={
				1: Empath.Ping(2)
			})),
			Player(name='Dan', character=Undertaker(night_info={
				2: Undertaker.Ping(Anna, Empath)
			})),
			Player(name='Fraser', character=FortuneTeller(night_info={
				1: FortuneTeller.Ping(Anna, Tim, demon=True),
				2: FortuneTeller.Ping(You, Fraser, demon=False),
				3: FortuneTeller.Ping(You, Sarah, demon=True),
			})),
			Player(name='Sarah', character=Librarian(night_info={
				1: Librarian.Ping(You, Hannah, Drunk)
			})),
			Player(name='Tim', character=Recluse()),
			Player(name='Matt', character=Juggler(
				day_info={
					1: Juggler.Juggle({
						You: Investigator,
						Dan: LordOfTyphon,
						Tim: Recluse,
						Hannah: Dreamer,
					}
				)},
				night_info={2: Juggler.Ping(1)}
			)),
			Player(name='Hannah', character=Dreamer(night_info={
				1: Dreamer.Ping(You, Investigator, LordOfTyphon)
			})),
		],
		day_events={
			1: Execution(Anna, died=True),
			2: Execution(Dan, died=True),
		},
		night_deaths={2: Hannah, 3: Tim},
	)

	worlds = world_gen(
		state,
		possible_demons=[LordOfTyphon],
		possible_minions=[Marionette, Poisoner],
		possible_hidden_good=[Drunk],
		possible_hidden_self=[Drunk, Marionette],
		category_counts=(5, 1, 1, 1), # townsfolk, outsiders, minions, demons
	)

	valid_worlds = list(worlds)
	for world in valid_worlds:
		print(world)
	print(f'Found {len(valid_worlds)} valid worlds')

