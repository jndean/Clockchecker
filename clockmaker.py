from collections import defaultdict
from copy import deepcopy
from dataclasses import dataclass, field
import random
from typing import Any, Iterator

import clockchecker as cc
from clockchecker import PlayerID


def defaultdict_field(default):
    def defaultdict_factory():
        return defaultdict(default)
    return field(default_factory=defaultdict_factory)


def to_cc(x: 'CharacterGenerator') -> type[cc.Character]:
    return getattr(cc, type(x).__name__)


class Constraint:
    def __init__(self, **values):
        self.values = values
    
    def __getattribute__(self, name: str) -> Any:
        return self.values.get(name, None)


@dataclass
class CharacterGenerator:
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: 'Puzzle',
    ) -> list[cc.Info]:
        return []
    
    def generate_day_info(
        self,
        me: PlayerID,
        day: int,
        puz: 'Puzzle',
    ) -> list[cc.Info | cc.Event]:
        return []


@dataclass
class Player:
    claim: CharacterGenerator
    constraints: list[Constraint] = field(default_factory=list)
    night_info: dict[int, list[cc.Info]] = defaultdict_field(list)
    day_info: dict[int, cc.Info] = defaultdict_field(list)
    state: dict[Any, Any] = field(default_factory=dict)

    is_alive: bool = True


@dataclass
class Puzzle:
    players: list[Player]
    day_events: defaultdict[int, list[cc.Event]]
    night_deaths: defaultdict[int, list]
    hidden: list[type[cc.Character]]
    hidden_self: list[type[cc.Character]]

    def __post_init__(self):
        self.minions = [x for x in self.hidden if x.category is cc.MINION]
        self.demons = [x for x in self.hidden if x.category is cc.DEMON]

    def random_player(
        self,
        n: int = 1,
        exclude: PlayerID | None = None,
    ) -> PlayerID | list[PlayerID]:
        options = list(range(len(self.players)))
        if exclude is not None:
            options.pop(exclude)
        choices = random.choices(options, k=n)
        return choices[0] if n == 1 else choices
    
    def get_constraints(self, player: PlayerID, **patterns):
        constraints = self.players[player].constraints
        if patterns:
            constraints = [
                constraint for constraint in constraints
                if all(getattr(constraint, k) == v for k, v in patterns.items())
            ]
        return constraints
    
    def to_cc_puzzle(self) -> cc.Puzzle:
        return cc.Puzzle(
            players=[
                cc.Player(
                    name=f'Player{i}',
                    claim=to_cc(player.claim),
                    night_info=deepcopy(player.night_info),
                    day_info=deepcopy(player.day_info),
                )
                for i, player in enumerate(puzzle.players)
            ],
            hidden_characters=self.hidden,
            hidden_self=self.hidden_self,
            day_events=puzzle.day_events,
            night_deaths=puzzle.night_deaths,
        )



def pick_characters(
    possible_claims: list[type[cc.Character]],
) -> Iterator[list[CharacterGenerator]]:
    while True:
        # TODO: randomise order
        yield possible_claims


def init_puzzles(
    characters_generator: Iterator[list[CharacterGenerator]],
    hidden: list[type[CharacterGenerator]],
    hidden_self: list[type[CharacterGenerator]],
) -> Iterator[Puzzle]:
    
    for claims in characters_generator:
        puzzle = Puzzle(
            players=[Player(claim=claim) for claim in claims],
            day_events={},
            night_deaths={},
            hidden=hidden,
            hidden_self=hidden_self,
        )
        yield puzzle


def generate_day(
    puzzles: Iterator[Puzzle],
    day: int,
) -> Iterator[Puzzle]:
    return puzzles


def generate_night(
    puzzles: Iterator[Puzzle],
    night: int,
    night_deaths: dict[int, list[PlayerID]],
) -> Iterator[Puzzle]:
    for puzzle in puzzles:

        if night in night_deaths:
            puzzle.night_deaths[night] = list(night_deaths[night])
            for pid in night_deaths[night]:
                puzzle.players[pid].is_alive = False
        elif night > 1:
            pid = puzzle.random_player()
            puzzle.night_deaths[night] = pid
            puzzle.players[pid].is_alive = False

        for player_id, player in enumerate(puzzle.players):
            if player.is_alive:
                night_info = player.claim.generate_night_info(
                    player_id,
                    night,
                    puzzle,
                )
                player.night_info[night].extend(night_info)


        

        yield puzzle



def generate_puzzles(
    claims: list[type[cc.Character]],
    hidden: list[type[cc.Character]],
    hidden_self: list[type[cc.Character]],
    night_deaths: dict[int, list[PlayerID]],
    nights: int,
) -> Iterator[Puzzle]:
    
    characters = pick_characters(claims)
    puzzles = init_puzzles(characters, hidden, hidden_self)

    for night in range(1, nights + 1):
        puzzles = generate_night(puzzles, night, night_deaths)
        if night != nights:
            puzzles = generate_day(puzzles, night)

    yield from puzzles


@dataclass
class Seamstress(CharacterGenerator):
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: Puzzle,
    ) -> list[cc.Info]:
        # constraints = puz.get_constraints(me)
        if night != 1:
            return []
        return [
            cc.Seamstress.Ping(
                *puz.random_player(2),
                same=bool(random.getrandbits(1)),
            )
        ]

@dataclass
class Knight(CharacterGenerator):
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: Puzzle,
    ) -> list[cc.Info]:
        if night != 1:
            return []
        return [cc.Knight.Ping(*puz.random_player(2, exclude=me))]
        
@dataclass
class FortuneTeller(CharacterGenerator):
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: Puzzle,
    ) -> list[cc.Info]:
        return [
            cc.FortuneTeller.Ping(
                *puz.random_player(2),
                demon=(random.getrandbits(1)),
            )
        ]

@dataclass
class Saint(CharacterGenerator):
    pass
@dataclass
class Recluse(CharacterGenerator):
    pass
@dataclass
class Soldier(CharacterGenerator):
    pass

@dataclass
class Investigator(CharacterGenerator):
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: Puzzle,
    ) -> list[cc.Info]:
        if night != 1:
            return []
        return [
            cc.Investigator.Ping(
                *puz.random_player(2),
                random.choice(puz.minions)
            )
        ]

@dataclass
class Washerwoman(CharacterGenerator):
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: Puzzle,
    ) -> list[cc.Info]:
        if night != 1:
            return []
        player1 = random.choice([
            i for i, player in enumerate(puz.players)
            if i != me and to_cc(player.claim).category is cc.TOWNSFOLK
        ])
        return [
            cc.Washerwoman.Ping(
                player1,
                puz.random_player(exclued=me),
                to_cc(puz.players[player1].claim),
            )
        ]

@dataclass
class Juggler(CharacterGenerator):
    pass
    # def generate_night_info(
    #     self,
    #     me: PlayerID,
    #     night: int,
    #     puz: Puzzle,
    # ) -> list[cc.Info]:
    #     raise NotImplementedError()

@dataclass
class Clockmaker(CharacterGenerator):
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: Puzzle,
    ) -> list[cc.Info]:
        if night != 1:
            return []
        return [cc.Clockmaker.Ping(random.randint(1, len(puz.players) // 2))]
    
@dataclass
class Empath(CharacterGenerator):
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: Puzzle,
    ) -> list[cc.Info]:
        return [cc.Empath.Ping(random.randint(0, 2))]

@dataclass
class Balloonist(CharacterGenerator):
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: Puzzle,
    ) -> list[cc.Info]:
        return [cc.Balloonist.Ping(puz.random_player())]
    
@dataclass
class Undertaker(CharacterGenerator):
    def generate_night_info(
        self,
        me: PlayerID,
        night: int,
        puz: Puzzle,
    ) -> list[cc.Info]:
        if night == 1:
            return []
        return [
            cc.Investigator.Ping(
                *puz.random_player(2),
                random.choice(puz.minions)
            )
        ]


def average_info_strength(puzzle: Puzzle, nights: int) -> float:
    deltas = []
    base_count = len(list(cc.Solver().generate_worlds(puzzle.to_cc_puzzle())))
    for pid1, player1 in enumerate(puzzle.players):
        for n1 in range(1, nights + 1):
            for iid1 in range(len(player1.night_info[n1])):
                ablated = deepcopy(puzzle)
                ablated.players[pid1].night_info[n1].pop(iid1)
                
                for pid2, player2 in enumerate(ablated.players):
                    for n2 in range(1, nights + 1):
                        for iid2 in range(len(player2.night_info[n2])):
                            ablated2 = deepcopy(ablated)
                            ablated2.players[pid2].night_info[n2].pop(iid2)
                            
                            new_count = len(list(cc.Solver().generate_worlds(ablated2.to_cc_puzzle())))
                            deltas.append(new_count - base_count)
    print(deltas)
    return (sum(deltas) / len(deltas)) if deltas else 0


if __name__ == '__main__':

    SEARCH_LENGTH = 20000

    nights = 1
    claims=[
        Empath(),
        Slayer(),
        Imp(),
        Investigator(),
        FortuneTeller(),
        Recluse(),
        Undertaker(),
        Spy(),
        Soldier(),
        ScaletWoman(),
    ]
    hidden = [cc.Leviathan, cc.Goblin]
    hidden_self = [cc.Drunk]

    puzzle_generator = generate_puzzles(
        claims=claims,
        hidden=hidden,
        hidden_self=hidden_self,
        nights=nights,
        night_deaths={2: 2},
        day_events={1: cc.Execution(5), 2: cc.Execution(9)}
    )

    for i in range(SEARCH_LENGTH):
        puzzle = next(puzzle_generator)
        cc_puzzle = puzzle.to_cc_puzzle()
        solutions = list(cc.Solver().generate_worlds(cc_puzzle))
        print(f'{len(solutions)=}')
        if len(solutions) == 1:
            print(puzzle.to_cc_puzzle())
            for solution in solutions:
                print(solution)
            if (info_strength := average_info_strength(puzzle, nights)) > 0:
                # print(puzzle)
                # for solution in solutions:
                #     print(solution)
                print(f'{info_strength=}')


    You, Dan, Tim, Sula, Matt, Steph = range(6)

    # constraints = Constraints(
    #     num_players=6,
    #     claims=[Washerwoman, Chef]
    #     players=[
    #         Player(
    #             name=You,
    #             character=Baron,
    #             claim=Imp,
    #             neighbours=None,

    #         )
    #     ]
    # )

    # puzzles = generate_puzzles(
    #     possible_claims=[
    #         Seamstress(),
    #         Knight(),
    #         FortuneTeller(),
    #         Saint(),
    #         Juggler(),
    #         Clockmaker(),
    #         Balloonist(),
    #     ],
    #     possible_hidden=[cc.Leviathan, cc.Goblin, cc.Drunk],
    #     possible_hidden_self=[cc.Drunk],
    #     nights=1,
    # )

    