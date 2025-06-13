# TODO:
 - Why are there Categories, why do Characters not instead inherit from 4 subclasses of Character? Then Category checks are performed by isinstance?
 	- Would be a good time to switch to proper ABCs?

 - Recent rule change means there can no longer be misregistration during setup actions, so Marionette can't sit next to Recluse, Recluse can't be in Typhon line, Spy can't increase Xaan number. This ruling is not completely stable /adopted by the community, so I will not change the implementation to rule out worlds using these mechanics just yet. 

 - Seperately track night number and a character's personal night number
   e.g. so that a Chef created on night 3 will register as waking up. Partially done this, but need to go through each character to check they respect the correct night number. I think in general "each night*" refers to true game night number, whereas "you start knowing" means your personal first night.

 - Could easily(?) filter out worlds where a player has a ping not in line with their wake_pattern

 - Allow claiming mid-game character changes. I think they need to be in the player's night info lists so the puzzle can specify when the change happened relative to the player's normal info... Right now, the SnakeCharmer has a wonderfully satisfying implementation that successfully swaps with demons, and triggeres abilities in the correct order, but there is no way for a player to claim to have changed role, so it can not yet be a utilised by a puzzle :( .

 - If no solutions are found and Atheist is in Puzzle statement, return the Atheist world

 - The EvilTwin ExternalInfo system is _awful_, it was supposed to account for night order but it really doesn't, because if an EvilTwin is claimed to be created mid game the claimed Ping just won't be checked at the moment the twin is created. Feels like ExternalInfo should be scrapped since that's all it does now, and all logic could be put into the EvilTwin... or perhaps ExternalInfo needs to be a stateful thing, state tracks what claims have been made and EvilTwin ticks off the ones it has fulfilled at the moment it does it...

 - Characters that would like to listen for character_changed events:
   - NoDashii to update poisoned neighbours
   - Vigormortis to update poisoned neighbours of killed minions
   - Xaan to poison new townsfolk
   - Philo to drunk new players with the same role
 - Characters that would like to listen for alignment_changed events:
   - Fortune Teller to change red herring
   - Widow to update player who knows
   - Evil twin to update good twin
   - Etc

 - I think one day I might need a GLOBAL_FIRST_NIGHT_ORDER and a GLOBAL_OTHER_NIGHT_ORDER.

# Active Bugs To Fix:

	- If the NoDashii's poisoned neighbours are changed to non-townsfolk, currently nothing prompts the NoDashii to update who it is poisoning

	- Not respecting the jinx on cannibal/juggler. What a ridiculous jinx!

	- EvilTwin is doesn't pick a new twin if they change alignment

	- Not respecting Lunatic-Mathematician jinx.

	- The Mathematician implementation can't handle the possibiliy of an evil Townsolk learning incorrect info.

	- FangGu jump will also be caught by a ScarletWoman

	- In general, Mathematician is implemented badly. Currently only "first-degree" math numbers are counted, e.g. during run_night, an ability doesn't work on the spot. However, a drunk Poisoner, Xaan, No Dashii etc who is failing to poison their target should increment the count, but only at the moment that their target's ability _does_ work. This happens at an arbitrary point later, and is not implemented. Also, the No Dashii failing to kill ticks up the Math number, and this would need to be deduplicated with the them failing to poison their neighbour (since Math counts players who misfired tonight, not number of misfires). Similarly, a droisoned Monk or Soldier failing to protect from the demon won't Math right...
	The Spy misregistering as good is detected fine by Mathematician, but a drunk Spy _not_ misregistering as good when they would normally is _not_ picked up by Math.

	- EASY FIX: IsCategory(Spy, TOWNSFOLK) returns MAYBE but IsCategory(Spy, MINION) 
	returns TRUE, should be able to misregister!

	- Nobody f***ing knows the exact ruling on how Vortox affects 
	mis-registering characters, but I'm not happy with what is currently implemented. STBool.Maybe doesn't contain info about whether misinfo would be True or False, so it is not possible to infer which way the Vortox should push ST choices (if you believe the ST doesn't have misregistration choices in a vortox world).
	A solution would be to make STBool have True, False True-That-Can-Misregister-As-False, and False-That-Can-Misregister-As-True. Maybe called TRUE, FALSE, SURE, NAH?
	Having said that, the current system can correctly solve all the available vortox puzzles, so perhaps I'm ok leaving it for now...
	- The 3-value bool is also slightly lacking for e.g. a FangGu to increment the Math number correctly. If a Fang Gu kills a Recluse or a Spy, they both register as Outsider with identical value MAYBE. But the Math number is incremented when the Spy is jumped to, whereas it is incremented when the Recluse is _not_ jumped to, and a single MAYBE requires us to add some slightly inelegant extra checks to detect which case we're in.

	- For external info (Like Nightwatchman pings or Evil Twin sightings), if there are multuple instances of an external-info generating character then the first one will trigger the check for all such character info, possibly before the second instance of the character gets to make their choice so the world will be incorrectly rejects. This will be relevant if the Philosopher is ever implemented and chooses in-play abilities.


# Things we don't and won't handle:

 - Order not specified by night order. E.g. if there are two poisoners in town then either could go first, but we only try one ordering.