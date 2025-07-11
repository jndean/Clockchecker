# Clockchecker 🕰️
Reddit user u/Not_Quite_Vertical posts [weekly Blood on the Clocktower puzzles](https://notquitetangible.blogspot.com/2024/11/clocktower-puzzle-archive.html). Clockchecker is a naïve solver of specifically these puzzles, which generates and checks all possible worlds. A driving motivation behind the design of clockchecker is for implementing new characters to be as easy as possible, because hobbies are supposed to be fun.

*Try it now, interactively [in your browser](https://josefdean.co.uk/clockchecker/).*
 
## Puzzle Solving Examples
<p align="center">


<details open>
<summary><b>Puzzle 26 - A Basic Example</b></summary>
 
<table>
<tr><th>Puzzle 26</th></tr>
<tr><td><p align="center"><img src="README_imgs/puzzle26.png" width=600px></p></td></tr>
<tr><th>Solver Script</th></tr>
<tr><td>
 
 ```python3
from clockchecker import *

You, Olivia, Dan, Tom, Matthew, Josh, Sula, Fraser = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Empath, night_info={
            1: Empath.Ping(0)
        }),
        Player('Olivia', claim=Saint),
        Player('Dan', claim=Slayer, day_info={
            2: Slayer.Shot(Matthew, died=False),
        }),
        Player('Tom', claim=Recluse),
        Player('Matthew', claim=Librarian, night_info={
            1: Librarian.Ping(You, Josh, Drunk)
        }),
        Player('Josh', claim=Soldier),
        Player('Sula', claim=Undertaker, night_info={
            2: Undertaker.Ping(You, Empath),
            3: Undertaker.Ping(Dan, Slayer),
        }),
        Player('Fraser', claim=Chef, night_info={
            1: Chef.Ping(2)
        }),
    ],
    day_events={1: Execution(You), 2: Execution(Dan)},
    night_deaths={2: Josh, 3: Olivia},
    hidden_characters=[Imp, Poisoner, Spy, Baron, ScarletWoman, Drunk],
    hidden_self=[Drunk],
)
for world in Solver().generate_worlds(puzzle):
    print(world)
 ```
</td></tr>
<tr><th>Output</th></tr>
<tr><td><img src="README_imgs/solution26.png"></td></tr>
</table>

</details>
<details>
<summary><b>Puzzle 12b - Example of interesting Day Events, and role changes.</b></summary>

<table>
<tr><th>Puzzle 12b</th></tr>
<tr><td><p align="center"><img src="README_imgs/puzzle12b.webp" width=600px></p></td></tr>
<tr><th>Solver Script</th></tr>
<tr><td>
 
 ```python3
from clockchecker import *

You, Oscar, Anna, Josh, Fraser, Tom, Aoife, Steph = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Librarian, night_info={
            1: Librarian.Ping(Fraser, Steph, Lunatic)
        }),
        Player('Oscar', claim=Investigator, night_info={
            1: Investigator.Ping(Josh, Fraser, Spy)
        }),
        Player('Anna', claim=Empath, night_info={
            1: Empath.Ping(1)
        }),
        Player('Josh', claim=Mayor),
        Player('Fraser', claim=Slayer),
        Player('Tom', claim=Dreamer, night_info={
            1: Dreamer.Ping(Steph, Lunatic, Spy)
        }),
        Player('Aoife', claim=Clockmaker, night_info={
            1: Clockmaker.Ping(3)
        }),
        Player('Steph', claim=Courtier, night_info={
            1: Courtier.Choice(Vortox)
        }),
    ],
    day_events={
        1: [
            Doomsayer.Call(player=Tom, died=Josh),
            Slayer.Shot(player=Fraser, target=Steph, died=False),
            Doomsayer.Call(player=Steph, died=Oscar),
            Doomsayer.Call(player=Fraser, died=Aoife),
        ]
    },
    hidden_characters=[Vortox, Spy, ScarletWoman, Lunatic],
    hidden_self=[],
)

for world in Solver().generate_worlds(puzzle):
    print(world)
 ```
</td></tr>
<tr><th>Output</th></tr>
<tr><td><img src="README_imgs/solution12b.png"></td></tr>
</table>
</details>
<details>
<summary><b>Puzzle 1 - Using composable Info objects to build arbitrary Savant statements.</b></summary>

<table>
<tr><th>Puzzle 1</th></tr>
<tr><td><p align="center"><img src="README_imgs/puzzle1.webp" width=600px></p></td></tr>
<tr><th>Solver Script</th></tr>
<tr><td>
 
 ```python3
from clockchecker import *

# 5 of the 6 Savant statements we can handle by composing existing Info primitives, however
# for one of them it's easier to create this custom object implementing the Info interface.
@dataclass
class DrunkBetweenTownsfolk(Info):
    def __call__(self, state: State, src: PlayerID) -> STBool:
        N = len(state.players)
        result = FALSE
        for player in range(N):
            found_drunk = IsCharacter(player, characters.Drunk)(state, src)
            if found_drunk is FALSE:  # Allows MAYBE
                continue
            tf_neighbours = (
                IsCategory((player - 1) % N, TOWNSFOLK)(state, src) &
                IsCategory((player + 1) % N, TOWNSFOLK)(state, src)
            )
            result |= found_drunk & tf_neighbours
        return result

# Now solve the puzzle
You, Tim, Sula, Oscar, Matt, Anna = range(6)
puzzle = Puzzle(
    players=[
        Player('You', claim=Savant, day_info={
            1: Savant.Ping(
                IsInPlay(Investigator), 
                IsEvil(Tim) | IsEvil(Anna)
            ),
            2: Savant.Ping(
                Chef.Ping(1), 
                DrunkBetweenTownsfolk()
            ),
            3: Savant.Ping(
                IsCategory(Tim, MINION) | IsCategory(Sula, MINION),
                ~IsInPlay(Noble)
            ),
        }),
        Player('Tim', claim=Knight, night_info={
            1: Knight.Ping(Sula, Anna)
        }),
        Player('Sula', claim=Steward, night_info={
            1: Steward.Ping(Matt)
        }),
        Player('Oscar', claim=Investigator, night_info={
            1: Investigator.Ping(Sula, Anna, Goblin)
        }),
        Player('Matt', claim=Noble, night_info={
            1: Noble.Ping(Tim, Sula, Oscar)
        }),
        Player('Anna', claim=Seamstress, night_info={
            1: Seamstress.Ping(Sula, Oscar, same=False)
        }),
    ],
    hidden_characters=[Leviathan, Goblin, Drunk],
    hidden_self=[],
)

for world in Solver().generate_worlds(puzzle):
    print(world)
 ```
</td></tr>
<tr><th>Output</th></tr>
<tr><td><img src="README_imgs/solution1.png"></td></tr>
</table>
</details>
<details>
<summary><b>Puzzle 41 - Katharine's favourite 🧙‍♀️ (an evil perspective puzzle) </b></summary>

<table>
<tr><th>Puzzle 41</th></tr>
<tr><td><p align="center"><img src="README_imgs/puzzle41.webp" width=600px></p></td></tr>
<tr><th>Solver Script</th></tr>
<tr><td>
 
 ```python3
from clockchecker import *

You, Amelia, Edd, Riley, Josef, Gina, Katharine, Chris = range(8)
puzzle = Puzzle(
    players=[
        Player('You', claim=Imp),
        Player('Amelia', claim=FortuneTeller, night_info={
            1: FortuneTeller.Ping(Edd, Josef, False),
            2: FortuneTeller.Ping(Josef, You, False),
            3: FortuneTeller.Ping(Amelia, You, False),
        }),
        Player('Edd', claim=Seamstress, night_info={
            1: Seamstress.Ping(Katharine, Chris, same=True),
        }),
        Player('Riley', claim=Slayer, day_info={
            1: Slayer.Shot(Katharine, died=False),
        }),
        Player('Josef', claim=Chef, night_info={
            1: Chef.Ping(1),
        }),
        Player('Gina', claim=Noble, night_info={
            1: Noble.Ping(Edd, Riley, Chris),
        }),
        Player('Katharine', claim=PoppyGrower),
        Player('Chris', claim=Artist, day_info={
            1: Artist.Ping(~IsCategory(Riley, TOWNSFOLK)),
        }),
    ],
    day_events={
        1: [
            Dies(after_nominating=True, player=Gina),
            Execution(Riley),
        ],
        2: Execution(Edd)
    },
    night_deaths={2: Chris, 3: Josef},
    hidden_characters=[Imp, Witch, Drunk, Lunatic],
    hidden_self=[Lunatic],
)

for world in Solver().generate_worlds(puzzle):
    print(world)
 ```
</td></tr>
<tr><th>Output</th></tr>
<tr><td><img src="README_imgs/solution41.png"></td></tr>
</table>
</details>
 
</p>

## Usage
The example script demonstrates the way the solver is intended to be used for solving a new puzzle. It usually just contains whatever puzzle I was implementing most recently, since that's how I test them. Run the example with:
```bash
python example.py
```
Solved puzzles are recorded in the `puzzles.py` file, you can choose to print and solve one by name, e.g.:
```bash
python puzzles.py NQT24
python puzzles.py josef_yes_but_dont
```
I record most previously solved puzzles so that they can be run as unit tests during development. You can run these tests and solve all puzzles using
```bash
python -m unittest
```
Clockchecker is written purely in Python (3.13), because it is supposed to be fun to work on rather than efficient to run. At time of writing the above unittest command solves 54 puzzles in 18.2 seconds.

## Example Character Implementations
The hope is for characters to be easy to write, easy to read, and easy to reason over. TPI is determined to make this goal unattainable. That said, at least _some_ characters fit quite well in the clockchecker framework; some example characters taken from the `characters.py` file are below.

Reasoning over the output of character information is done using `STBool`s (StoryTeller bools) which can have value `TRUE`, `FALSE` or `MAYBE`. For example, `info.IsCharacter(Josef, Imp)` will evaluate to `MAYBE` if Josef is the Recluse. Logical operator overloads are implemented on STBools (e.g., `(TRUE | MAYBE) := TRUE`, `(TRUE & MAYBE) := MAYBE`, `(FALSE == MAYBE) := MAYBE`, etc), allowing the propogation of uncertainty due to Storyteller decisions using fairly legible code.

<details open>
<summary><b>Investigator</b></summary>
 
```python
@dataclass
class Investigator(Character):
    """
    You start knowing that 1 of 2 players is a particular Minion.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID
        character: type[Character]

        def __call__(self, state: State, me: PlayerID) -> STBool:
            return (
                info.IsCharacter(self.player1, self.character)(state, me) |
                info.IsCharacter(self.player2, self.character)(state, me)
            )
```
</details>
<details>
<summary><b>Fortune Teller</b></summary>

```python
@dataclass
class FortuneTeller(Character):
    """
    Each night, choose 2 players: you learn if either is a Demon. 
    There is a good player that registers as a Demon to you.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID
        demon: bool
        def __call__(self, state: State, me: PlayerID) -> STBool:
            red_herring = state.players[me].character.red_herring
            real_result = (
                info.IsCategory(self.player1, DEMON)(state, me)
                | info.IsCategory(self.player2, DEMON)(state, me)
                | info.STBool(red_herring in (self.player1, self.player2))
            )
            return real_result == info.STBool(self.demon)

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        # Any good player could be chosen as the red herring
        for player in range(len(state.players)):
            if info.IsEvil(player)(state, me) is not info.TRUE:
                new_state = state.fork()
                new_state.players[me].character.red_herring = player
                yield new_state
```
</details>
<details>
<summary><b>Baron</b></summary>
 
```python
@dataclass
class Baron(Character):
    """
    There are extra Outsiders in play. [+2 Outsiders]
    """
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        (min_tf, max_tf), (min_out, max_out), mn, dm = bounds
        bounds = (min_tf - 2, max_tf - 2), (min_out + 2, max_out + 2), mn, dm
        return bounds
```
</details>
<details>
<summary><b>Drunk</b></summary>
 
```python
@dataclass
class Drunk(Character):
    """
    You do not know you are the Drunk. 
    You think you are a Townsfolk character, but you are not.
    """
    category: ClassVar[Categories] = OUTSIDER
    is_liar: ClassVar[bool] = True

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        drunk = state.players[me]
        # Drunk can only 'lie' about being Townsfolk
        if drunk.claim.category is not TOWNSFOLK:
            return
        self.wake_pattern = drunk.claim.wake_pattern
        yield state
```
</details>
<details>
<summary><b>Scarlet Woman</b></summary>
 
```python
@dataclass
class ScarletWoman(Character):
    """
    If there are 5 or more players alive & the Demon dies, you become the Demon.
    (Travellers don't count).
    """
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    def death_in_town(self, state: State, death: PlayerID, me: PlayerID) -> None:
        """Catch a Demon death. I don't allow catching Recluse deaths."""
        scarletwoman = state.players[me]
        dead_player = state.players[death]
        living_players = sum(
            not p.is_dead and p.character.category is not TRAVELLER
            for p in state.players
        )
        if (
            not scarletwoman.is_dead
            and scarletwoman.droison_count == 0
            and dead_player.character.category is DEMON
            and living_players >= 4
        ):
            if state.night is not None:
                scarletwoman.woke()
            state.character_change(me, type(dead_player.character))
```
</details>
<details>
<summary><b>Generic Demon</b></summary>

 ```python
@dataclass
class GenericDemon(Character):
    """
    Many demons just kill once each night*, so implment that once here.
    """
    category: ClassVar[Categories] = DEMON
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Override Reason: Create a world for every kill choice."""
        demon = state.players[me]
        if night == 1 or demon.is_dead or demon.droison_count:
            yield state
            return
        for target in range(len(state.players)):
            new_state = state.fork()
            target_char = new_state.players[target].character
            yield from target_char.attacked_at_night(new_state, target, me)
```
</details>

<details>
<summary><b>No Dashii</b></summary>

```python
@dataclass
class NoDashii(GenericDemon):
    """
    Each night*, choose a player: they die. 
    Your 2 Townsfolk neighbors are poisoned.
    """
    tf_neighbour1: PlayerID | None = None
    tf_neighbour2: PlayerID | None = None

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        # I allow the No Dashii to poison misregistering characters (e.g. Spy),
        # so there may be multiple possible combinations of neighbour pairs
        # depending on ST choices. Find them all and create a world for each.
        N = len(state.players)
        clockwise_candidates, anticlockwise_candidates = [], []
        for candidates, direction in (
            (clockwise_candidates, 1),
            (anticlockwise_candidates, -1),
        ):
            for step in range(1, N):
                player = (me + direction * step) % N
                is_tf = info.IsCategory(player, TOWNSFOLK)(state, me)
                if is_tf is not info.FALSE:
                    candidates.append(player)
                if is_tf is info.TRUE:
                    break
        # Create a world or each combination of cw and acw poisoned player
        for clockwise_neighbour in clockwise_candidates:
            for anticlockwise_neighbour in anticlockwise_candidates:
                new_state = state.fork()
                new_nodashii = new_state.players[me].character
                new_nodashii.tf_neighbour1 = clockwise_neighbour
                new_nodashii.tf_neighbour2 = anticlockwise_neighbour
                new_nodashii.maybe_activate_effects(new_state, me)
                yield new_state

    def _activate_effects_impl(self, state: State, me: PlayerID):
        state.players[self.tf_neighbour1].droison(state, me)
        state.players[self.tf_neighbour2].droison(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        state.players[self.tf_neighbour1].undroison(state, me)
        state.players[self.tf_neighbour2].undroison(state, me)
```
</details>
