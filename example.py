from clockchecker import *


# https://www.reddit.com/r/BloodOnTheClocktower/comments/1fz4jqe/weekly_puzzle_9_the_new_acrobat/

You, Fraser, Oscar, Josh, Anna, Sula, Hannah = range(7)

state = State(
    players=[
        Player(name='You', claim=Acrobat, night_info={
            2: Acrobat.Choice(Fraser),
            3: Acrobat.Choice(Josh),
        }),
        Player(name='Fraser', claim=Balloonist, night_info={
            1: Balloonist.Ping(Oscar),
            2: Balloonist.Ping(Anna),
            3: Balloonist.Ping(You),
        }),
        Player(name='Oscar', claim=Gossip, day_info={
            1: Gossip.Gossip(IsCategory(Fraser, DEMON)),
            2: Gossip.Gossip(IsCategory(Anna, DEMON)),
        }),
        Player(name='Josh', claim=Knight, night_info={
            1: Knight.Ping(Fraser, Oscar)
        }),
        Player(name='Anna', claim=Gambler, night_info={
            2: Gambler.Gamble(Sula, Goblin),
            3: Gambler.Gamble(You, Drunk),
        }),
        Player(name='Sula', claim=Juggler, day_info={
            1: Juggler.Juggle({
                You: Goblin,
                Oscar: Gossip,
                Josh: Knight,
                Anna: Imp,
            })
        }),
        Player(name='Hannah', claim=Steward, night_info={
            1: Steward.Ping(Oscar)
        }),
    ],
    night_deaths={
        2: Sula, 
        3: [You, Josh, Anna]
    },
)


worlds = list(world_gen(
    state,
    possible_demons=[Imp, Po],
    possible_minions=[Goblin],
    possible_hidden_good=[Drunk],
    possible_hidden_self=[Drunk],
))


for world in worlds:
    print(world)
print(f'Found {len(worlds)} valid worlds')
