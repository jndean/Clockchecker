# TODO:
 - Why are there Categories, why do Characters not instead inherit from 4 subclasses of Character? Then Category checks are performed by isinstance?
 	- Would be a good time to switch to proper ABCs?

 - EASY: Check vigormortis unpoisoned rule (see note in \_activate_effects_impl)

 - EASY: Could add a puzzle flag: disallow_killing_dead_players, which NQT adds as a rule in #46. Potentially this could be added just as a world rejection inside the 'attacked_at_night' default method.

- Easy: Make wrapper characters (Philosopher, Hermit, Drunklike) passthrough global_end_night method, e.g. for Widow.

- GOOD: Make Player.character private (Player._character?) and any time something wants to access player's character it should call player.get_character(CharacterType) with the expected character type. (Maybe it can call with None explicitly to get the root character?). This can then recurse into wrapped characters and return the instance of the ability that is expected.

 - Recent rule change means there can no longer be misregistration during setup actions, so Marionette can't sit next to Recluse, Recluse can't be in Typhon line, Spy can't increase Xaan number. This ruling is not completely stable /adopted by the community, so I will not change the implementation to rule out worlds using these mechanics just yet. 

 - Seperately track night number and a character's personal night number
   e.g. so that a Chef created on night 3 will register as waking up. Partially done this, but need to go through each character to check they respect the correct night number. I think in general "each night*" refers to true game night number, whereas "you start knowing" means your personal first night.

 - Could easily(?) filter out worlds where a player has a ping not in line with their wake_pattern

 - Several characters directly access attributes on a player's character (e.g., FortuneTeller.Ping accessed state.players[me].character.redherring) which doesn't play nicely when wrapped by other characters (such as Philo wrapping their chosen ability, or, in the extreme, a Hermit wrapping a Drunk wrapping a Philosopher wrapping a Drunklike wrapping their chosen ability :D). Possibly these need to go through a more serious API that can be passed through to wrapped abilities. I have implemented a one-off passthrough for some common attributes like `character.spent`, see Philo. 

 - Get rid of player.woke_tonight. Rather than characters recording if they woke during run_night, make every WakePattern.MANUAL character override the .wakes_tonight() method so that this can always be checked statically? [This is made hard by characters such as SW who can't be determined statically in advance..., so right now we awkwards have both `character.wakes_tonight()` (which makes a best effort in advance), and `player..woke_tonight` (which records the truth after the fact)]

 - Allow claiming mid-game character changes. I think they need to be in the player's night info lists so the puzzle can specify when the change happened relative to the player's normal info... Right now, the SnakeCharmer has a wonderfully satisfying implementation that successfully swaps with demons, and triggeres abilities in the correct order, but there is no way for a player to claim to have changed role, so it can not yet be a utilised by a puzzle :( .

 - If no solutions are found and Atheist is in Puzzle statement, return the Atheist world

 - The EvilTwin ExternalInfo system is _awful_, it was supposed to account for night order but it really doesn't, because if an EvilTwin is claimed to be created mid game the claimed Ping just won't be checked at the moment the twin is created. Feels like ExternalInfo should be scrapped since that's all it does now, and all logic could be put into the EvilTwin... or perhaps ExternalInfo needs to be a stateful thing, state tracks what claims have been made and EvilTwin ticks off the ones it has fulfilled at the moment it does it...

 - Implement the events system! (Some of the below could be callbcaks, not events...)
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
 - Characters thta would like to listen to droison_changed events:
   - Acrobat, who can die if their chosen player become droisoned later that night...
     Possibly this could equally be a callback attached to the chosen player...

 - I think one day I might need a GLOBAL_FIRST_NIGHT_ORDER and a GLOBAL_OTHER_NIGHT_ORDER.


# Active Bugs To Fix:

	- If the NoDashii's poisoned neighbours are changed to non-townsfolk, currently nothing prompts the NoDashii to update who it is poisoning

	- Not respecting the jinx on cannibal/juggler. What a ridiculous jinx!

	- EvilTwin is doesn't pick a new twin if they change alignment

	- Not respecting Lunatic-Mathematician jinx.

	- The Mathematician implementation can't handle the possibiliy of an evil Townsolk learning incorrect info.

	- FangGu jump will also be caught by a ScarletWoman

	- Currently 'safe_from_demon' doesn't protect from demon poisoning. It's easy to implement this if the poisoning is applied after safe_from_demon, but we don't track where droison count comes from so it is not currently possible to implement this if the poisoning happens first.

	- I think poisoned witch is incrementing math wrong and also not picking a target, which it should.

	- In general, Mathematician is implemented badly. Currently only "first-degree" math numbers are counted, e.g. during run_night, an ability doesn't work on the spot. However, a drunk Poisoner, Xaan, No Dashii etc who is failing to poison their target should increment the count, but only at the moment that their target's ability _does_ work. This happens at an arbitrary point later, and is not implemented. Also, the No Dashii failing to kill ticks up the Math number, and this would need to be deduplicated with the them failing to poison their neighbour (since Math counts players who misfired tonight, not number of misfires). Similarly, a droisoned Monk or Soldier failing to protect from the demon won't Math right, poisoned Princess etc...
	The Spy misregistering as good is detected fine by Mathematician, but a drunk Spy _not_ misregistering as good when they would normally is _not_ picked up by Math.

	- IsCategory(Spy, TOWNSFOLK) returns MAYBE but IsCategory(Spy, MINION) 
	returns TRUE, should be able to misregister! This is easy to fix, but if fixed it exposes the holes in the vortox misinfo calcs, described herafter.

	- Nobody f***ing knows the exact ruling on how Vortox affects 
	mis-registering characters, but I'm not happy with what is currently implemented. STBool.Maybe doesn't contain info about whether misinfo would be True or False, so it is not possible to infer which way the Vortox should push ST choices (if you believe the ST doesn't have misregistration choices in a vortox world).
	A solution would be to make STBool have True, False True-That-Can-Misregister-As-False, and False-That-Can-Misregister-As-True. Maybe called TRUE, FALSE, SURE, NAH?
	Having said that, the current system can correctly solve all the available vortox puzzles, so perhaps I'm ok leaving it for now...
	- The 3-value bool is also slightly lacking for e.g. a FangGu to increment the Math number correctly. If a Fang Gu kills a Recluse or a Spy, they both register as Outsider with identical value MAYBE. But the Math number is incremented when the Spy is jumped to, whereas it is incremented when the Recluse is _not_ jumped to, and a single MAYBE requires us to add some slightly inelegant extra checks to detect which case we're in.

	- For external info (Like Nightwatchman pings or Evil Twin sightings), if there are multuple instances of an external-info generating character then the first one will trigger the check for all such character info, possibly before the second instance of the character gets to make their choice so the world will be incorrectly rejects. This will be relevant if the Philosopher is ever implemented and chooses in-play abilities.


# Things we don't and won't handle:

 - Order not specified by night order. E.g. if there are two poisoners in town then either could go first, but we only try one ordering.

 - Currently, a Vig killed Recluse can register as Minion and poison one of their neighbours for the rest of the game, however there is no mechanism for them to stop registering as Minion at an arbitrary subsequent time to stop the poisoning. I don't think I will ever address this. To be completely correct it would technically have to spawn a non-poisoning world after every other action in the game.