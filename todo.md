# TODO:

 - EASY: Check vigormortis unpoisoned rule (see note in \_activate_effects_impl)

 - EASY: Vig isn't checking if exorcised.

 - EASY: Could add a puzzle flag: disallow_killing_dead_players, which NQT adds as a rule in #46. Potentially this could be added just as a world rejection inside the 'attacked_at_night' default method.

- Easy: Make wrapper characters (Philosopher, Hermit, Drunklike) passthrough global_end_night method, e.g. for Widow.

- EASY: Update descriptions of STBools in docstrings/README

- Current creation of speculative liars is wasteful, could create less setups rather than creating then rejecting them for having too many liars or having You speculatively lie in liar_gen.

- GOOD: Make Player.character private (Player.\_character?) and any time something wants to access player's character it should call player.get_character(CharacterType) with the expected character type. (Maybe it can call with None explicitly to get the root character?). This can then recurse into wrapped characters and return the instance of the ability that is expected

- Go though each character and check that they hav an implementation (or NotImplementedError) for being a speculative_liar if it has an effect, _not_ just being evil.

- There can no longer be misregistration during setup actions, so Marionette can't sit next to Recluse, Recluse can't be in Typhon line, Spy can't increase Xaan number. This ruling is not completely stable /adopted by the community, so I will not change the implementation to rule out worlds using these mechanics just yet. 

- Seperately track night number and a character's personal night number
  e.g. so that a Chef created on night 3 will register as waking up. Partially donethis, but need to go through each character to check they respect the correctnight number. I think in general "each night*" refers to true game night number,whereas "you start knowing" means your personal first night.

 - Could easily(?) filter out worlds where a player has a ping not in line with their wake_pattern

 - Several characters directly access attributes on a player's character (e.g., FortuneTeller.Ping accessed state.players[me].character.redherring) which doesn't play nicely when wrapped by other characters (such as Philo wrapping their chosen ability, or, in the extreme, a Hermit wrapping a Drunk wrapping a Philosopher wrapping a Drunklike wrapping their chosen ability :D). Possibly these need to go through a more serious API that can be passed through to wrapped abilities. I have implemented a one-off passthrough for some common attributes like `character.spent`, see Philo. 

 - Get rid of player.woke_tonight. Rather than characters recording if they woke during run_night, make every WakePattern.MANUAL character override the .wakes_tonight() method so that this can always be checked statically? [This is made hard by characters such as SW who can't be determined statically in advance..., so right now we awkwards have both `character.wakes_tonight()` (which makes a best effort in advance), and `player.woke_tonight` (which records the truth after the fact)]

 - Allow claiming mid-game character changes. I think they need to be in the player's night info lists so the puzzle can specify when the change happened relative to the player's normal info... Right now, the SnakeCharmer has a wonderfully satisfying implementation that successfully swaps with demons, and triggeres abilities in the correct order, but there is no way for a player to claim to have changed role, so it can not yet be a utilised by a puzzle :( .

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

	- Now that we have a 6-valued STBool we can fix up some of the missing features caused by the previous 3-valued STBool. E.g. a FangGu jumping + Math number. If a Fang Gu kills a Recluse or a Spy, they both used to register as Outsider with identical value MAYBE. But the Math number is incremented when the Spy is jumped to, whereas it is incremented when the Recluse is _not_ jumped to, and a single MAYBE required us to add some slightly inelegant extra checks to detect which case we're in. These days we have TRUE_MAYBE and FALSE_MAYBE so we can simplify.

	- For external info (Like Nightwatchman pings or Evil Twin sightings), if there are multuple instances of an external-info generating character then the first one will trigger the check for all such character info, possibly before the second instance of the character gets to make their choice so the world will be incorrectly rejects. This will be relevant if the Philosopher is ever implemented and chooses in-play abilities.


# Things we don't and won't handle:

 - Order not specified by night order. E.g. if there are two poisoners in town then either could go first, but we only try one ordering. Or if two things are supposed to happen 'simultaneously', the engine will do them one after the other (like a Soldier and a NoDashii sitting next to each other both become undrunked after a Minstrel day simultaneously, but the engine will undrunk them in an order depending on where they sit, so sometimes the Soldier will become immune from NoDashii poisoning before it the NoDashii is undrunked, and sometimes the Soldier will become NoDashii poisoned before they regain demon immunity).


 - Currently, a Vig killed Recluse can register as Minion and poison one of their neighbours for the rest of the game, however there is no mechanism for them to stop registering as Minion at an arbitrary subsequent time to stop the poisoning. I don't think I will ever address this. To be completely correct it would technically have to spawn a non-poisoning world after every subsequent action in the game.


## Problems with the STBool:
 - While the STBool can record that the ST may give an arbitrary answer to a query on the game state, it makes the assumption that there is only one true underlying answer to the statement. This is not always correct, e.g. the Shugenja query "closest evil is clockwise", if equidistant we want to return TRUE_MAYBE. But if the result of this query gets negated we'll have a FALSE_MAYBE, whilst really the result of the negation of the statement (i.e. "closest evil is anticlockwise") should still be TRUE_MAYBE.

  - STBool is used to uptick math in the deafult_info_check by recording when a Ping is only True due to misregistration, however, it doesn't encode that the misregistration may be a "part of your own ability", e.g. Red Herring, so it doesn't represent this well.
