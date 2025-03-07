from core import *
from characters import *
from events import *
from info import *

# https://www.reddit.com/r/BloodOnTheClocktower/comments/1hgdsmp/weekly_puzzle_19_he_could_be_you_he_could_be_me/

You, Fraser, Oscar, Jasmine, Olivia, Matt, Sula, Aoife = range(8)
state = State(
    players=[
        Player(name='You', claim=Librarian, night_info={
            1: Librarian.Ping(Fraser, Matt, Drunk)
        }),
        Player(name='Fraser', claim=Saint),
        Player(name='Oscar', claim=Recluse),
        Player(name='Jasmine', claim=Slayer),
        Player(name='Olivia', claim=Undertaker, night_info={
            2: Undertaker.Ping(You, Baron),
        }),
        Player(name='Matt', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Fraser, Saint)
        }),
        Player(name='Sula', claim=Washerwoman, night_info={
            1: Washerwoman.Ping(Fraser, Olivia, Undertaker)
        }),
        Player(name='Aoife', claim=Empath, night_info={
            1: Empath.Ping(0),
            2: Empath.Ping(1),
        }),
    ],
    day_events={
        1: Execution(You),
        2: Slayer.Shot(src=Jasmine, target=Oscar, died=True),
    },
    night_deaths={2: Matt},
)

worlds = list(world_gen(
    state,
    possible_demons=[Imp],
    possible_minions=[Poisoner, Spy, Baron, ScarletWoman],
    possible_hidden_good=[Drunk],
    possible_hidden_self=[Drunk],
))

for world in worlds:
    print(world)
print(f'Found {len(worlds)} valid worlds')
