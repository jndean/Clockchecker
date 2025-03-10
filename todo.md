# TODO:
 - Why are there Categories, why do Characters not instead inherit from 4 subclasses of Character? Then Category checks are performed by isinstance?
 	- Would be a good time to switch to proper ABCs?

 - Multithread the evaluator gen. Nothing fancy, just the initial character generator.

 - Could really do with a refactor that separates State into two things: a class for the initial immutable Puzzle definition (all the public info) and a class for the current mutable state of a World which is run out (like State currently is, with forking) and checked against the Puzzle.

 - Seperately track night number and a character's personal night number
   e.g. so that a Chef created on night 3 will register as waking up. Partially done this, but need to go through each character to check they respect the correct night number.

 - Could easily(?) filter out worlds where a player has a ping not in line with their wake_pattern

 - During setup, move all events in Player.day_info into State.day_info, and automatically set src=player. That way users can specify events under the relevant player, and only need to list them in the State.day_events list directly if order is important.

 - If no solutions are found and Atheist is in Puzzle statement, return Atheist world


# Active Bugs To Fix:

	- RN, Pings don't generally check that their callers are actually the
	corresponding character. Will become more relevant when TF can become evil?

	- Pukka shouldn't stop poisoning on end_day

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


# Things we don't and won't handle:

 - Order not specified by night order. E.g. if there are two poisoners in town then either could go first, but we only try one ordering.