# TODO:
 - Why are there Categories, why do Characters not instead inherit from 4 subclasses of Character? Then Category checks are performed by isinstance?
 	- Would be a good time to switch to proper ABCs?

 - Could really do with a refactor that separates State into two things: a class for the initial immutable Puzzle definition (all the public info) and a class for the current mutable state of a World which is run out (like State currently is, with forking) and checked against the Puzzle.

 - Seperately track night number and a character's personal night number
   e.g. so that a Chef created on night 3 will register as waking up. Partially done this, but need to go through each character to check they respect the correct night number. I think in general "each night*" refers to true night number, whereas "you start knowing" means your personal first night.

 - Could easily(?) filter out worlds where a player has a ping not in line with their wake_pattern

 - Allow claiming mid-game character changes. I think they need to be in the player's night info lists so the puzzle can specify when the change happened relative to the player's normal info... Right now, the SnakeCharmer has a wonderfully satisfying implementation that successfully swaps with demons, and triggeres abilities in the correct order, but there is no way for a player to claim to have changed role so it can not yet be a utilised by a puzzle :( .

 - During setup, move all events in Player.day_info into State.day_info, and automatically set src=player. That way users can specify events under the relevant player, and only need to list them in the State.day_events list directly if order is important.

 - If no solutions are found and Atheist is in Puzzle statement, return Atheist world

 - The EvilTwin ExternalInfo system is _awful_, it was supposed to account for night order but it really doesn't, because if an EvilTwin is claimed to be created mid game the claimed Ping just won't be checked at the moment the twin is created. Feels like ExternalInfo should be scrapped since that's all it does now, and all logic could be put into the Twin... or perhaps ExternalInfo needs to be a stateful thing, state tracks what claims have been made and EvilTwin ticks off the ones it has fulfilled at the moment it does it...


# Active Bugs To Fix:

	- When a player's character changes, the new character doesn't activate any 
	effects or do any setup.

	- If the NoDashii's poisoned neighbours are changed to non-townsfolk, currently
	nothing prompts the NoDashii to update who it is

	- RN, Pings don't generally check that their callers are actually the
	corresponding character. This will become more relevant when TF can become evil?

	- Pukka shouldn't stop poisoning on end_day

	- Not respecting the jinx on cannibal/juggler. What a ridiculous jinx!

	- EvilTwin is doesn't pick a new twin if they change alignment

	- Should implement run_night for Lunatic so it can call decide_if_woke_tonight for the demon they think they are (make decide_if_woke_tonight accept a 
	character, rather than a player). This should also be respected in `info.behaves_like`.
	Perhaps Lunatic.run_setup should generate a world for each choice of demon? May require separation of Puzzle and State.

	- IsCategory(Spy, TOWNSFOLK) returns MAYBE but IsCategory(Spy, MINION) 
	returns TRUE, should be able to misregister!

	- Nobody f***ing knows the exact ruling on how Vortox affects 
	mis-registering characters, but the ruling *I* have started to settle on is 
	not what is currently implemented. STBool.Maybe doesn't contain info about 
	whether misinfo would be True or False, so it is not possible to infer 
	which way the Vortox should push ST choices (if you believe the ST doesn't 
	have misregistration choices in a vortox world). A solution would be to make
	STBool have True, False, True-That-Can-Misregister-As-False, and False-That-Can-Misregister-As-True. Maybe called TRUE, FALSE, SURE, NAH?
	Having said that, the current system can correctly solve all the available vortox puzzles, so perhaps I'm ok leaving it for now.

	- For external info (Like Nightwatchman pings or Evil Twin sightings), if there are multuple instances of an external-info generating character then the first one will trigger the check for all such character info, possibly before the second instance of the character gets to make their choice so the world will be incorrectly rejects. This will be relevant if the Philosopher is ever implemented and chooses in-play abilities.


# Things we don't and won't handle:

 - Order not specified by night order. E.g. if there are two poisoners in town then either could go first, but we only try one ordering. Or if there are two Scarlet Women, we only generate a world where one of them caught the demon.