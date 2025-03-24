from clockchecker import *

# https://www.reddit.com/r/BloodOnTheClocktower/comments/1je8z17/weekly_puzzle_32_prepare_for_juggle_and_make_it/

You, Matthew, Olivia, Sula, Dan, Fraser, Jasmine, Tim = range(8)
state = State(
    players= [
        Player('You', claim=Dreamer, night_info={
            1: Dreamer.Ping(Sula, Drunk, Imp),
        }),
        Player('Matthew', claim=Juggler, 
            day_info={
                1: Juggler.Juggle({
                    You: Imp,
                    Dan: Drunk,
                    Jasmine: Baron,
                    Tim: FortuneTeller,
                })
            },
            night_info={2: Juggler.Ping(0)},
        ),
        Player('Olivia', claim=Recluse),
        Player('Sula', claim=Empath, night_info={
            1: Empath.Ping(1),
            2: Empath.Ping(1),
            3: Empath.Ping(0),
        }),
        Player('Dan', claim=Juggler, 
            day_info={
                1: Juggler.Juggle({
                    You: Dreamer,
                    Fraser: Poisoner,
                    Tim: Baron,
                })
            },
            night_info={2: Juggler.Ping(0)},
        ),
        Player('Fraser', claim=Saint),
        Player('Jasmine', claim=Undertaker, night_info={
            2: Undertaker.Ping(You, Dreamer),
            3: Undertaker.Ping(Dan, Juggler),
        }),
        Player('Tim', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Matthew, Fraser, demon=False),
        }),
    ],
    day_events={1: Execution(You), 2: Execution(Dan)},
    night_deaths={2: Tim, 3: Fraser},
)

worlds = world_gen(
    state,
    possible_demons=[Imp],
    possible_minions=[Poisoner, Baron],
    possible_hidden_good=[Drunk],
    possible_hidden_self=[Drunk],
)

worlds = list(worlds)
for world in worlds:
    print(world)
print(f'Found {len(worlds)} valid worlds')
