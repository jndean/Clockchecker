from dataclasses import dataclass

from clockchecker import *


# https://www.reddit.com/r/BloodOnTheClocktower/comments/1gv12ck/weekly_puzzle_15_wake_up_and_choose_violets

# This puzzle requires a custom method for one of the savant statements
@dataclass
class LongestRowOfTownsfolk(Info):
    """This puzzle (15) has no misregistration, so ommit that logic for now."""
    length: int
    def __call__(self, state: State, src: PlayerID) -> STBool:
        N = len(state.players)
        townsfolk = [
            info.IsCategory(player % N, TOWNSFOLK)(state, src)
            for player in range(N * 2)  # Wrap around circle
        ]
        longest, current = 0, 0
        for is_tf in townsfolk:
            if is_tf is TRUE:
                current += 1
            elif is_tf is FALSE:
                longest = max(longest, current)
                current = 0
            else:
                raise NotImplementedError("Misregistration")
        if longest > N:
            longest = N
        return STBool(longest == self.length)


You, Oscar, Sarah, Hannah, Fraser, Aoife, Adam, Jasmine = range(8)

state = State(
    players=[
        Player(name='You', claim=Savant, day_info={
            1: Savant.Ping(
                ExactlyN(N=3, args=[
                    IsInPlay(Clockmaker),
                    IsInPlay(Klutz),
                    IsInPlay(Juggler),
                    IsInPlay(Vortox),
                ]),
                LongestRowOfTownsfolk(5),
            )
        }),
        Player(name='Oscar', claim=Klutz),
        Player(name='Sarah', claim=Juggler, 
            day_info={
                1: Juggler.Juggle({
                    You: Savant,
                    Hannah: SnakeCharmer,
                    Fraser: Clockmaker,
                    Aoife: Seamstress,
                    Jasmine: SnakeCharmer,
                })
            },
            night_info={2: Juggler.Ping(3)},
        ),
        Player(name='Hannah', claim=SnakeCharmer, night_info={
            1: [
                SnakeCharmer.Choice(Sarah),
                EvilTwin.Is(Jasmine),
            ],
            2: SnakeCharmer.Choice(Oscar),
            3: SnakeCharmer.Choice(Aoife),
        }),
        Player(name='Fraser', claim=Clockmaker, night_info={
            1: Clockmaker.Ping(3)
        }),
        Player(name='Aoife', claim=Seamstress, night_info={
            1: Seamstress.Ping(Oscar, Hannah, same=False)
        }),
        Player(name='Adam', claim=Artist, night_info={
            1: Artist.Ping(
                ~IsCharacter(You, Vortox)
                & ~IsCharacter(Oscar, Vortox)
                & ~IsCharacter(Sarah, Vortox) 
            )
        }),
        Player(name='Jasmine', claim=SnakeCharmer, night_info={
            1: [
                SnakeCharmer.Choice(Fraser),
                EvilTwin.Is(Hannah),
            ],
            2: SnakeCharmer.Choice(Aoife),
            3: SnakeCharmer.Choice(Adam),
        }),
    ],
    day_events={
        1: Execution(You),
        2: [
            Execution(Oscar),
            Klutz.Choice(player=Oscar, choice=Sarah),
        ],
    },
)


worlds = list(world_gen(
    state,
    possible_demons=[NoDashii, Vortox],
    possible_minions=[EvilTwin],
    possible_hidden_good=[Mutant],
    possible_hidden_self=[],
))


for world in worlds:
    print(world)
print(f'Found {len(worlds)} valid worlds')
