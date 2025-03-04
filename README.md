# ClockChecker 🕰️
Reddit user u\Not_Quite_Vertical posts [weekly Blood on the Clocktower puzzles](https://notquitetangible.blogspot.com/2024/11/clocktower-puzzle-archive.html). ClockChecker is a naïve solver of specifically these puzzles, which generates and checks all possible worlds. A driving motivation is for implementing new characters to be as easy as possible.
 
## Puzzle Examples
<table>
 <tr><th>*Solver Script*</th><th>*Puzzle*</th></tr>
<tr> 
<td rowspan="3">
 
 ```python3
from clockchecker import *

You, Olivia, Dan, Tom, Matthew, Josh, Sula, Fraser = range(8)
state = State(
  players=[
    Player(name='You', claim=Empath, night_info={
      1: Empath.Ping(0)
    }),
    Player(name='Olivia', claim=Saint),
    Player(name='Dan', claim=Slayer),
    Player(name='Tom', claim=Recluse),
    Player(name='Matthew', claim=Librarian, night_info={
      1: Librarian.Ping(You, Josh, Drunk)
    }),
    Player(name='Josh', claim=Soldier),
    Player(name='Sula', claim=Undertaker, night_info={
      2: Undertaker.Ping(You, Empath),
      3: Undertaker.Ping(Dan, Slayer),
    }),
    Player(name='Fraser', claim=Chef, night_info={
      1: Chef.Ping(2)
    }),
  ],
  day_events={
    1: Execution(You),
    2: [Slayer.Shot(src=Dan, target=Matthew, died=False),
        Execution(Dan)]
  },
  night_deaths={2: Josh, 3: Olivia},
)

for world in world_gen(
    state,
    possible_demons=[Imp],
    possible_minions=[Poisoner, Spy, Baron, ScarletWoman],
    possible_hidden_good=[Drunk],
    possible_hidden_self=[Drunk],
):
    print(world)
 ```
</td>

<td><img src="https://i.redd.it/9h3598yc75he1.png"> </td>
</tr>
<tr><th>*Output*</th></tr>
<tr>
<td>
 
```
World(
     You : Empath 💀
  Olivia : Saint 💀
     Dan : Slayer 💀
     Tom : Imp
 Matthew : Poisoner (Poisoned Fraser, Josh, You)
    Josh : Soldier 💀
    Sula : Undertaker
  Fraser : Chef
) 
```
</td>
</tr>
</table>

<table>
 <tr><th>Puzzle</th><th>Solver Script</th></tr>

<tr> 
 <td><img src="https://preview.redd.it/weekly-puzzle-thunderstruck-v0-lev8yps3wpxd1.png?width=1356&format=png&auto=webp&s=e6c0d4e266f69c38e24db79066841a622bb33a13"> </td>
<td rowspan="3">
 
 ```python3
from clockchecker import *

You, Oscar, Anna, Josh, Fraser, Tom, Aoife, Steph = range(8)
state = State(
  players=[
    Player(name='You', claim=Librarian, night_info={
      1: Librarian.Ping(Fraser, Steph, Lunatic)
    }),
    Player(name='Oscar', claim=Investigator, night_info={
      1: Investigator.Ping(Josh, Fraser, Spy)
    }),
    Player(name='Anna', claim=Empath, night_info={
      1: Empath.Ping(1)
    }),
    Player(name='Josh', claim=Mayor),
    Player(name='Fraser', claim=Slayer),
    Player(name='Tom', claim=Dreamer, night_info={
      1: Dreamer.Ping(Steph, Lunatic, Spy)
    }),
    Player(name='Aoife', claim=Clockmaker, night_info={
      1: Clockmaker.Ping(3)
    }),
    Player(name='Steph', claim=Courtier, night_info={
      1: Courtier.Choice(Vortox)
    }),
  ],
  day_events={
    1: [
      DoomsayerCall(caller=Tom, died=Josh),
      Slayer.Shot(src=Fraser, target=Steph, died=False),
      DoomsayerCall(caller=Steph, died=Oscar),
      DoomsayerCall(caller=Fraser, died=Aoife),
    ]
  },
)

for world in  world_gen(
    state,
    possible_demons=[Vortox],
    possible_minions=[Spy, ScarletWoman],
    possible_hidden_good=[Lunatic],
    possible_hidden_self=[],
):
    print(world)
 ```
</td>
</tr>
<tr><th>Output</th></tr>
<tr>
<td>
 
```
World(
    You : Librarian
  Oscar : Vortox 💀
   Anna : Lunatic
   Josh : Mayor 💀
 Fraser : Slayer
    Tom : Dreamer
  Aoife : Clockmaker 💀
  Steph : ScarletWoman -> Vortox
)
```
</td>
</tr>
</table>

## Example Character Implementations
The hope is for implementing new characters easy, and for those implementations to be easy to read and easy to reason over. TPI is determined to make this goal unattainable, however _most_ characters fit well in the Clockchecker framework. Some examples lifted directly from the `characters.py` file are below.

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

		def __call__(self, state: State, src: PlayerID) -> STBool:
			return (
				info.IsCharacter(self.player1, self.character)(state, src) |
				info.IsCharacter(self.player2, self.character)(state, src)
			)
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
		self.wake_pattern = drunk.claim.wake_pattern
		"""Drunk can only 'lie' about being Townsfolk"""
		if drunk.claim.category is TOWNSFOLK:
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

	def death_in_town(self, state: State, death: PlayerID, me: PlayerID):
		"""Catch a Demon death. I don't allow catching Recluse deaths."""
		scarletwoman = state.players[me]
		dead_player = state.players[death]
		living_players = sum(not p.is_dead for p in state.players)
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
