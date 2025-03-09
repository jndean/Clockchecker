from core import *
from characters import *
from events import *
from info import *


# https://www.reddit.com/r/BloodOnTheClocktower/comments/1hlgh1w/weekly_puzzle_20_the_three_wise_men/

You, Caspar, Joseph, Melchior, Mary, Balthazar, Gabriel = range(7)
state = State(
    players=[
        Player(name='You', claim=Investigator, night_info={
            1: Investigator.Ping(Mary, Gabriel, Baron)
        }),
        Player(name='Caspar', claim=VillageIdiot, night_info={
            1: VillageIdiot.Ping(Mary, is_evil=True),
            2: VillageIdiot.Ping(Joseph, is_evil=True),
        }),
        Player(name='Joseph', claim=Saint),
        Player(name='Melchior', claim=VillageIdiot, night_info={
            1: VillageIdiot.Ping(Balthazar, is_evil=True),
            2: VillageIdiot.Ping(Mary, is_evil=True),
        }),
        Player(name='Mary', claim=Virgin, day_info={
            1: Virgin.NominatedWithoutExecution(Balthazar)
        }),
        Player(name='Balthazar', claim=VillageIdiot, night_info={
            1: VillageIdiot.Ping(Joseph, is_evil=True),
            2: VillageIdiot.Ping(Caspar, is_evil=True),
        }),
        Player(name='Gabriel', claim=Ravenkeeper, night_info={
            2: Ravenkeeper.Ping(Balthazar, Drunk)
        }),
    ],
    day_events={1: Execution(You)},
    night_deaths={2: Gabriel},
)

worlds = list(world_gen(
    state,
    possible_demons=[Imp],
    possible_minions=[Baron, Spy, Poisoner, ScarletWoman],
    possible_hidden_good=[Drunk],
    possible_hidden_self=[Drunk],
))

for world in worlds:
    print(world)
print(f'Found {len(worlds)} valid worlds')

