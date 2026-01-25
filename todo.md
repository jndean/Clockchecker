# TODO:

 - EASY: Check vigormortis unpoisoned rule (see note in \_activate_effects_impl)

 - EASY: Create a method that selects "The Demon" based on living precedence rules etc, returns generator of demkns. use tbis in Scarlwt woman. Boffin should use this. 

 - EASY: Could add a puzzle flag: disallow_killing_dead_players, which NQT adds as a rule in #46. Potentially this could be added just as a world rejection inside the 'attacked_at_night' default method.

- Easy: Make wrapper characters (Philosopher, Hermit, Drunklike) passthrough global_end_night method, e.g. for Widow.

- EASY: Update descriptions of STBools in docstrings/README

- EASY: Puzzle.allow_duplicate_tokens_in_bag is being used to allow multiple VIs, but
  VIs should have their own mechanism for this so that we can specify no OTHER
  duplicate tokens (otherwise we're going to have e.g. speculatively-lying duplicate snakecharmers popping up in VI puzzles).

- GOOD: Make Player.character private (Player.\_character?) and any time something wants to access player's character it should call player.get_character(CharacterType) with the expected character type. (Maybe it can call with None explicitly to get the root character?). This can then recurse into wrapped characters and return the instance of the ability that is expected

- Go though each character and check that they have an implementation for
behaving evil (or NotImplementedError) _not_ just being evil.

- There can no longer be misregistration during setup actions, so Marionette can't sit next to Recluse, Recluse can't be in Typhon line, Spy can't increase Xaan number. This ruling is not completely stable /adopted by the community, so I will not change the implementation to rule out worlds using these mechanics just yet.

- Seperately track night number and a character's personal night number
  e.g. so that a Chef created on night 3 will register as waking up. Partially done this, but need to go through each character to check they respect the correct night number. I think in general "each night*" refers to true game night number,whereas "you start knowing" means your personal first night.

 - Get rid of player.woke_tonight. Rather than characters recording if they woke during run_night, make every WakePattern.MANUAL character override the .wakes_tonight() method so that this can always be checked statically? [This is made hard by characters such as SW who can't be determined statically in advance..., so right now we awkwards have both `character.wakes_tonight()` (which makes a best effort in advance), and `player.woke_tonight` (which records the truth after the fact)]

 - The EvilTwin ExternalInfo system is _awful_, it was supposed to account for night order but it really doesn't, because if an EvilTwin is claimed to be created mid game the claimed Ping just won't be checked at the moment the twin is created. Feels like ExternalInfo should be scrapped since that's all it does now, and all logic could be put into the EvilTwin... or perhaps ExternalInfo needs to be a stateful thing, state tracks what claims have been made and EvilTwin ticks off the ones it has fulfilled at the moment it does it...

  - Currently the 'safe_from_demon_count' attribute actually only saves from death, not from poisoning (or Vortox). Making the Vortox work will be only a few lines of code, but making safe from poisoning work will be much more involved. Suppose a NoDashii poisons a neighbour from N1, then the neighbour is Monk protected N3. The Monk should be able to deactivate one of the NoDashii's poisonings, and the NoDashii code should probably not need to know about it. Similarly at the end of the night the Monk ability needs to trigger the re-poisoning of the TF.
  THIS MAY BE THE TIME to introduce status effect 'reminder' tokens, in this case one that lives on the poisoned player, so that the Monk ability can check for statuses on the target and de/reactivate them individually, and the placed token should know how to de/reactivate itself. E.g. the NoDashii can define a reminder token called `PoisonedNeighbour` (which probably inheits from the token `Poisoned`) which knows how to unpoison just one NoDashii neighbour, then the `NoDashii._deactvate_efects_impl()` just calls deactivate on each of the poisoned neighbour reminder tokens it has in play.
  The base ReminderToken class probably has a `src` attribute :)

 - Implement the events system! (Some of the below could be token callbcaks, not events...)
 - Characters that would like to listen for character_changed events:
   - NoDashii to update poisoned neighbours - DONE
   - Vigormortis to update poisoned neighbours of killed minions and unvigormortise killed minions
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

  - Currently players can be ceremad as evil characters. Would need to add a final day check on mad player claims.

	- Not respecting the jinx on cannibal/juggler. What a ridiculous jinx!

	- Not respecting Lunatic-Mathematician jinx.

	- FangGu jump will also be caught by a ScarletWoman

	- The Mathematician implementation can't handle the possibiliy of an evil Townsolk learning incorrect info.

	- In general, Mathematician is implemented badly. Currently only "first-degree" math numbers are counted, e.g. during run_night, an ability doesn't work on the spot. However, a drunk Poisoner, Xaan, No Dashii etc who is failing to poison their target should increment the count, but only at the moment that their target's ability _does_ work. This happens at an arbitrary point later, and is not implemented. E.g., a droisoned Monk or Soldier failing to protect from the demon won't Math right, poisoned Princess etc...
	The Spy misregistering as good is detected fine by Mathematician, but a drunk Spy _not_ misregistering as good when they would normally is _not_ picked up by Math.

	- Now that we have a 6-valued STBool we can fix up some of the missing features caused by the previous 3-valued STBool. E.g. a FangGu jumping + Math number. If a Fang Gu kills a Recluse or a Spy, they both used to register as Outsider with identical value MAYBE. But the Math number is incremented when the Spy is jumped to, whereas it is incremented when the Recluse is _not_ jumped to, and a single MAYBE required us to add some slightly inelegant extra checks to detect which case we're in. These days we have TRUE_MAYBE and FALSE_MAYBE so we can simplify.

	- For external info (Like Nightwatchman pings or Evil Twin sightings), if there are multuple instances of an external-info generating character then the first one will trigger the check for all such character info, possibly before the second instance of the character gets to make their choice so the world will be incorrectly rejects. This will be relevant if the Philosopher is ever implemented and chooses in-play abilities.


# Things we don't and won't handle:

 - Order not specified by night order. E.g. if there are two poisoners in town then either could go first, but we only try one ordering. (Similar if there is a SnakeCharmer and a Philo-SnakeCharmer, which could have a mechanical difference if the Philo goes first and hits the demon, undrunking the real SC). Or if two things are supposed to happen 'simultaneously', the engine will generally do them one after the other unless I write a special case (like a Soldier and a NoDashii sitting next to each other both become undrunked simultaneously after a Minstrel day, but the engine will undrunk them in an order depending on where they sit, so sometimes the Soldier will become immune from NoDashii poisoning before the NoDashii is undrunked, and sometimes the Soldier will become NoDashii poisoned before they regain demon immunity).


 - Currently, a Vig killed Recluse can register as Minion and poison one of their neighbours for the rest of the game, however there is no mechanism for them to stop registering as Minion at an arbitrary subsequent time to stop the poisoning. I don't think I will ever address this. To be completely correct it might technically have to spawn a non-poisoning world after every subsequent action in the game.


## Problems with the STBool:
 - While the STBool can record that the ST may give an arbitrary answer to a query on the game state, it makes the assumption that there is only one true underlying answer to the statement. This is not always correct, e.g. the Shugenja query "closest evil is clockwise", if equidistant we want to return TRUE_MAYBE. But if the result of this query gets negated we'll have a FALSE_MAYBE, whilst really the result of the negation of the statement (i.e. "closest evil is anticlockwise") should still be TRUE_MAYBE.

  - STBool is used to uptick math in the deafult_info_check by recording when a Ping is only True due to misregistration, however, it doesn't encode that the misregistration may be a "part of your own ability", e.g. Red Herring, so it doesn't represent this well.
