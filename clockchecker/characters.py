
from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field
import enum
import itertools
from typing import ClassVar, TYPE_CHECKING

from clockchecker.info import PlayerID

if TYPE_CHECKING:
    from .core import State, StateGen, Player
    from .info import PlayerID, ExternalInfo, STBool

from . import core
from . import events
from . import info


"""
Implementing a Character Checklist:
 - Copy some other similar-ish character.
 - For basic info characters, just create a Ping class inheriting from 
   Info and implement the __call__ method.
 - For more complex characters or characters who have to make choices that are
   not evidenced by a Ping, override the relevant character methods such as
   [modify_category_counts, run_night/day/setup, killed, executed, etc.].
 - For characetrs that do things publicly in the day, consider implementing an
   Event instead of a Ping.
 - When overriding the default methods for complex characters, remember to 
   consider the desired behaviour of the new character if they are:
    - dead
    - droisoned
    - not their usual alignment
    - not the character who gets their claimed ping (Some TODO!)
    - spent
    - vortoxed
 - Remember to set or call the following as appropriately
    - set `character.spent` 
    - call `player.woke()` for Chambermaid if character uses using WakePattern.MANUAL
    - call `state.math_misregistration` for Mathematician counts
    - TODO: call `state.choose(target)` for Goon
   and curse these characters for forcing this mental burden onto the 
   implementation of other characters.
"""


class Categories(enum.Enum):
    Townsfolk = enum.auto()
    Outsider = enum.auto()
    Minion = enum.auto()
    Demon = enum.auto()
    Traveller = enum.auto()

TOWNSFOLK = Categories.Townsfolk
OUTSIDER = Categories.Outsider
MINION = Categories.Minion
DEMON = Categories.Demon
TRAVELLER = Categories.Traveller

CategoryBounds = tuple[
    tuple[int, int],  # Townsfolk count min / max
    tuple[int, int],  # Outsiders count min / max
    tuple[int, int],  # Minions count min / max
    tuple[int, int],  # Demons count min / max
]


DEFAULT_CATEGORY_COUNTS = {
    5: (3, 0, 1, 1),
    6: (3, 1, 1, 1),
    7: (5, 0, 1, 1),
    8: (5, 1, 1, 1),
    9: (5, 2, 1, 1),
    10: (7, 0, 2, 1),
    11: (7, 1, 2, 1),
    12: (7, 2, 2, 1),
    13: (9, 0, 3, 1),
    14: (9, 1, 3, 1),
    15: (9, 2, 3, 1),
}

# Rules for when a player can ping and what the Chambermaid should see.
# Characters using MANUAL are responsible for rejecting worlds where pings are 
# not on legal nights.
class WakePattern(enum.Enum):
    NEVER = enum.auto()
    FIRST_NIGHT = enum.auto()
    EACH_NIGHT = enum.auto()
    EACH_NIGHT_STAR = enum.auto()
    EACH_NIGHT_UNTIL_SPENT = enum.auto()
    MANUAL = enum.auto()


class Reason(enum.Enum):
    SETUP = enum.auto()
    DROISON = enum.auto()
    UNDROISON = enum.auto()
    DEATH = enum.auto()
    RESURRECTION = enum.auto()
    CHARACTER_CHANGE = enum.auto()


@dataclass
class Character:

    # Characters like Recluse and Spy override here
    misregister_categories: ClassVar[tuple[Categories, ...]] = ()

    effects_active: bool = False

    # Night the character was created, usually 1
    first_night: int = 1

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        """
        Modify bounds of acceptable character counts. E.g. the Baron should 
        override this method to increase the Outsider Min & Max and decrease
        the Townsfolk Min & Max. Meanwhile the Balloonist should increment only 
        the Outsider Max and decrement only the Townsfolk Min.
        """
        return bounds

    def run_setup(self, state: State, player: PlayerID) -> StateGen:
        """
        Create plausible worlds from the character's setup. E.g. the 
        Fortune Teller creates one world per choice of red herring. The 
        Marionette should just return (yield no candidate worlds) if it is not 
        sat next to the demon.
        This method is also called to set up a new instance of the character 
        if it is created mid game, so implementations should condition behaviour
        on the current game phase.
        """
        yield state

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:	
        """
        Take the character's night action. Most basic info roles can just 
        inherit this default implementation and implement their own Pings to go
        in night_info.
        """
        if self.default_info_check(state, me):
            yield state

    def run_day(self, state: State, day: int, me: PlayerID) -> StateGen:
        if self.default_info_check(state, me):
            yield state

    def end_day(self, state: State, day: int, me: PlayerID) -> bool:
            """
            Take dusk actions (e.g. poisoner stops poisoning).
            Can return False to invalidate the world, e.g., Vortox uses this to 
            reject worlds with no executions.
            """
            return True

    def default_info_check(
        self: Character, 
        state: State,
        me: PlayerID,
        even_if_dead: bool = False,
    ) -> bool:
        """Most info roles can inherit this pattern for their info check."""
        if state.night is not None:
            ping = state.get_night_info(type(self), me, state.night)
        elif state.day is not None:
            ping = state.get_day_info(me, state.day)
        else:
            raise ValueError('What time is it?')

        if ping is None or info.behaves_evil(state, me) or self.is_liar:
            return True

        player = state.players[me]
        if player.is_dead and not even_if_dead:
            return False

        if spent := getattr(player.character, 'spent', None):
            return False
        elif spent is not None:
            player.character.spent = True

        result = ping(state, me)
        if state.vortox and (self.category is TOWNSFOLK):
            state.math_misregistration()
            return result is not info.TRUE
        
        if player.droison_count:
            if not getattr(player.character, 'self_droison', False):
                state.math_misregistration(result)
            return True
        return result is not info.FALSE

    def maybe_activate_effects(
        self,
        state: State,
        me: PlayerID,
        reason: Reason | None = None,
    ) -> None:
        """
        Effects that this character is having on other players. Needs to be 
        triggerable under one method so that e.g. a poisoner dying at night can
        reactivate that poisoner's current victim.
        If a character doesn't want this wrapper logic, it can override this 
        method rather than the _impl method.
        """
        if (
            not self.effects_active
            and state.players[me].droison_count == 0
            and not state.players[me].is_dead
        ):
            self.effects_active = True
            self._activate_effects_impl(state, me)

    def maybe_deactivate_effects(
        self,
        state: State,
        me: PlayerID,
        reason: Reason | None = None,
    ) -> None:
        """
        Will be called on any character at the moment they are poisoned, killed,
        or changed into another character.
        """
        if self.effects_active:
            self.effects_active = False
            self._deactivate_effects_impl(state, me)

    def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
        """Individual character effect implementations override here."""
        pass
    def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
        """Individual character effect implementations override here."""
        pass

    def apply_death(
        self,
        state: State,
        me: PlayerID,
        src: PlayerID | None = None,
    ) -> StateGen:
        """Trigger consequences of a confirmed death."""
        state.players[me].is_dead = True
        self.maybe_deactivate_effects(state, me, Reason.DEATH)
        yield from state.death_in_town(me)

    def attacked_at_night(
        self: Character,
        state: State,
        me: PlayerID,
        src: PlayerID,
     ) -> StateGen:
        """
        Called when attacked at night, decides whether this causes death or not.
        This does not always imply 'me' was chosen by a player, e.g. see Gossip.
        Characters who die to their own ability will be 'attacked' by 
        themselves, i.e., me == src.
        Remember to re-read the attacker properties on the yielded state in the
        calling method, because e.g. the Goon will create a state where the
        attacker has become drunk.
        """
        if state.players[me].is_dead:
            yield state
        elif (
            self.cant_die(state, me)
            or (
                state.players[src].character.category is DEMON
                and getattr(state.players[me], 'safe_from_demon_count', 0)
            )
        ):
            state.math_misregistration()
            yield state
        else:
            self.death_explanation = f'killed by {state.players[src].name}'
            yield from self.apply_death(state, me, src)

    def executed(self, state: State, me: PlayerID, died: bool) -> StateGen:
        """Goblin, Psychopath, Saint etc override this method."""
        
        if died:
            self.death_explanation = 'executed'
            yield from self.killed(state, me)
        elif self.cant_die(state, me):
            yield state

    def killed(
        self,
        state: State,
        me: PlayerID,
        src: PlayerID | None = None,
    ) -> StateGen:
        """Check the death is logically valid, then apply it."""
        if not self.cant_die(state, me) and not state.players[me].is_dead:
            yield from self.apply_death(state, me, src)

    def cant_die(self, state: State, me: PlayerID) -> bool:
        """Things like checking for innkeeper protection will go here :)"""
        return False
    
    def run_night_external(
        self,
        state: State,
        external_info: ExternalInfo,
        me: PlayerID,
    ) -> bool:	
        """
        Check night info that this player claims was caused by another player's
        ability, e.g. being told your Evil Twin or that NightWatchman chose you.
        """
        if info.behaves_evil(state, me) or self.is_liar:
            return True
        # It is the responsibility of the ExternalInfo to account for Vortox.
        return external_info(state, me)

    def _world_str(self, state: State) -> str:
        """
        For printing nice output representations of worlds. E.g 
        E.g. see Posoiner or Fortune Teller.
        """
        ret = type(self).__name__
        if hasattr(self, 'death_explanation'):
            ret += f' ({self.death_explanation})'
        return ret

@dataclass
class Acrobat(Character):
    """
    Each night*, choose a player:
    if they are or become drunk or poisoned tonight, you die.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    @dataclass
    class Choice(info.NotInfo):
        player: PlayerID

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Override Reason: Die on droisoned player choice"""
        acrobat = state.players[me]
        if acrobat.is_evil:
            raise NotImplementedError("Evil Acrobat")
        if (choice := state.get_night_info(Acrobat, me, night)) is None:
            yield state
        elif acrobat.is_dead:
            return
        elif acrobat.droison_count:
            yield state
        elif state.players[choice.player].droison_count:
            if acrobat.droison_count:
                state.math_misregistration()
                yield state
                return
            yield from self.attacked_at_night(state, me, me)
        else:
            yield state


@dataclass
class Alsaahir(Character):
    """Not yet implemented"""
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER


@dataclass
class Artist(Character):
    """
    Once per game, during the day, privately ask the Storyteller any yes/no
    question.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    spent: bool = False

    @dataclass
    class Ping(info.Info):
        statement: info.Info
        def __call__(self, state: State, src: PlayerID):
            return self.statement(state, src)

@dataclass
class Atheist(Character):
    """
    The Storyteller can break the game rules, and if executed, good wins,
    even if you are dead. [No evil characters].
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        """
        We find Atheist games by running the solver as normal and finding no
        valid worlds. As such, any game that hits this method at setup will have
        evil players plus an Atheist, and is therefore invalid and should yield
        no worlds.
        """
        if state.current_phase is core.Phase.SETUP:
            return
        yield state  # Allow Athiest to be created midgame ¯\_(ツ)_/¯

@dataclass
class Balloonist(Character):
    """
    Each night, you learn a player of a different character type than last night
    [+0 or +1 Outsider]
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    # Records the categories the last ping could have been registering as.
    prev_character: type[Character] = None 

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        (min_tf, max_tf), (min_out, max_out), mn, dm = bounds
        bounds = (min_tf - 1, max_tf), (min_out, max_out + 1), mn, dm
        return bounds

    @dataclass
    class Ping(info.NotInfo):
        player: PlayerID

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """
        Override Reason: even though we don't need to assert the balloonist 
        gets correct info when poisoned, we still need to take the action to 
        record that the following day the balloonist may see anything.

        NOTE: this implementation has only 1 day of memory, but technically the
        validity of balloonist pings can depend on all previous pings.
        E.g. a ping on 'Goblin, Legion, Imp' is not valid because legion must 
        have registered as one of minion or demon. I will fix this properly if 
        it ever actually comes up :)
        """
        balloonist = state.players[me]
        ping = state.get_night_info(Balloonist, me, night)
        if (
            balloonist.is_dead
            or balloonist.is_evil
            or ping is None
        ):
            self.prev_character = None
            yield state; return

        character = type(state.players[ping.player].character)
        prev_character = self.prev_character
        self.prev_character = character
        if prev_character is None:
            yield state; return

        if state.vortox:
            # Balloonist MUST get the same category every night in vortox worlds
            if character.category is prev_character.category:
                yield state
            return

        differ = ~info.SameCategory(character, prev_character)(state, me)
        if balloonist.droison_count:
            state.math_misregistration(differ)
            yield state
        elif differ is not info.FALSE:
            yield state


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

@dataclass
class Butler(Character):
    """
    Each night, choose a player (not yourself):
    tomorrow, you may only vote if they are voting too.
    """
    category: ClassVar[Categories] = OUTSIDER
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    # Will need to implement the Butler's choices if the Goon is added.

@dataclass
class Chambermaid(Character):
    """
    Each night, choose 2 alive players (not yourself):
    you learn how many woke tonight due to their ability.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            valid_choices = (
                self.player1 != src and self.player2 != src 
                and info.IsAlive(self.player1)(state, src) is not info.FALSE
                and info.IsAlive(self.player2)(state, src) is not info.FALSE
            )
            wake_count = sum(
                state.players[player].woke_tonight
                or (
                    # Handle Chambermaid-Mathematician Jinx,
                    # or multiple players having Chambermaid ability.
                    state.player_upcoming_in_night_order(player)
                    and Chambermaid.player_wakes_tonight(state, player)
                )
                for player in (self.player1, self.player2)
            )
            return info.STBool(valid_choices and wake_count == self.count)

    @staticmethod
    def player_wakes_tonight(
        state: State,
        player_id: PlayerID,
        character_override: type[Character] | None = None,
    ) -> bool:
        """
        Called on each player by State at the start of their turn in the night
        order, to decide whether or not that player will later register as
        having woken up. MANUAL wake patterns have to be implemented in the
        waking character's run_night method.
        """
        # Special cases not yet implemented:
        # - Chambermaid doesn't wake if there aren't valid choices
        # - Demon doesn't wake to their ability when exorcised
        # - Others, definitely.
        player = state.players[player_id]
        character = (
            player.character if character_override is None
            else character_override
        )
        match character.wake_pattern:
            case WakePattern.NEVER | WakePattern.MANUAL:
                woke = False
            case WakePattern.FIRST_NIGHT:
                woke = state.night == character.first_night
            case WakePattern.EACH_NIGHT:
                woke = True
            case WakePattern.EACH_NIGHT_STAR:
                woke = state.night != character.first_night
            case WakePattern.EACH_NIGHT_UNTIL_SPENT:
                woke = not character.spent
            case _:
                raise ValueError(
                    f'{type(character).__name__} has {character.wake_pattern=}'
                )
        return woke and not player.is_dead

@dataclass
class Chef(Character):
    """
    You start knowing how many pairs of evil players there are.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            N = len(state.players)
            evils = [info.IsEvil(i % N)(state, src) for i in range(N + 1)]
            evil_pairs = [a & b for a, b in zip(evils[:-1], evils[1:])]
            return info.ExactlyN(self.count, evil_pairs)(state, src)

@dataclass
class Clockmaker(Character):
    """
    You start knowing how many steps from the Demon to its nearest Minion.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        steps: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            """
            This implementation checks against the min distance over all 
            minion-demon pairs, giving info.MAYBEs as appropriate. The phrase 
            "The Demon" must give living demons priority over dead demons, so if 
            there are any living demons, all dead demons are ignored.
            """
            players = state.players
            N = len(players)
            minions, demons = (
                list(filter(
                    lambda x: x[1] is not info.FALSE,
                    [(i, info.IsCategory(i, cat)(state, src)) for i in range(N)]
                ))
                for cat in (MINION, DEMON)
            )
            ignore_dead_demons = any(not players[i].is_dead for i, _ in demons)

            correct_distance, too_close = info.FALSE, info.FALSE
            for demon_pos, is_demon in demons:
                if players[demon_pos].is_dead and ignore_dead_demons:
                    continue
                for minion_pos, is_minion in minions:
                    is_pair = is_demon & is_minion
                    distance = info.circle_distance(minion_pos, demon_pos, N)
                    if distance < self.steps:
                        too_close |= is_pair
                    elif distance == self.steps:
                        correct_distance |= is_pair

            return correct_distance & ~too_close

@dataclass
class Courtier(Character):
    """
    Once per game, at night, choose a character:
    they are drunk for 3 nights & 3 days.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_UNTIL_SPENT

    target: PlayerID = None
    choice_night: int | None = None
    spent: bool = False

    @dataclass
    class Choice(info.NotInfo):
        character: type[Character]

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        courtier = state.players[me]
        if courtier.is_evil:
            # Yield all choices like a poisoner, plus the non-choice
            raise NotImplementedError("Todo: Evil Courtier")

        choice = state.get_night_info(Courtier, me, night)
        if choice is None:
            yield state; return
        if courtier.is_dead or self.spent:
            return  # Drinking when spent or dead is a lie
        self.choice_night = night
        self.spent = True

        valid_targets = [
            target for target in range(len(state.players))
            if info.IsCharacter(target, choice.character)(state, me) 
            is not info.FALSE
        ]
        if courtier.droison_count:
            if valid_targets:
                state.math_misregistration()
            yield state; return  # Shame!
        
        for target in valid_targets:
            new_state = state.fork()
            new_courtier = new_state.players[me].character
            new_courtier.target = target
            new_courtier.maybe_activate_effects(new_state, me)
            yield new_state

    def end_day(self, state: State, day: int, me: PlayerID) -> bool:
        if self.target is not None and (day - self.choice_night) >= 2:
            self.maybe_deactivate_effects(state, me)
            self.target = None
        return True

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.target == me:
            state.players[me].droison_count += 1
        elif self.target is not None:
            state.players[self.target].droison(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.target == me:
            state.players[me].droison_count -= 1
        elif self.target is not None:
            state.players[self.target].undroison(state, me)

@dataclass
class Dreamer(Character):
    """
    Each night, choose a player (not yourself or Travellers): 
    you learn 1 good & 1 evil character, 1 of which is correct.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    @dataclass
    class Ping(info.Info):
        player: PlayerID
        character1: type[Character]
        character2: type[Character]

        def __call__(self, state: State, src: PlayerID) -> STBool:
            return (
                info.IsCharacter(self.player, self.character1)(state, src) |
                info.IsCharacter(self.player, self.character2)(state, src)
            )

@dataclass
class Drunk(Character):
    """
    You do not know you are the Drunk. 
    You think you are a Townsfolk character, but you are not.
    """
    category: ClassVar[Categories] = OUTSIDER
    is_liar: ClassVar[bool] = True
    # wake_pattern is decided during run_setup

    self_droison: bool = True

    # TODO: Drunk goes through the motions of the claimed character to determine
    # e.g. if it is spent and should no longer be waking.
    spent: bool = False

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        drunk = state.players[me]
        # Drunk can only 'lie' about being Townsfolk
        if drunk.claim.category is not TOWNSFOLK:
            return
        setup_reason = (
            Reason.SETUP if state.current_phase is core.Phase.SETUP 
            else Reason.CHARACTER_CHANGE
        )
        self.maybe_activate_effects(state, me, setup_reason)
        self.wake_pattern = drunk.claim.wake_pattern
        yield state

    # def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
    #     yield state

    def _activate_effects_impl(self, state: State, me: PlayerID):
        state.players[me].droison_count += 1

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        """Need to be able to undroison self on character change."""
        state.players[me].droison_count -= 1

@dataclass
class Empath(Character):
    """
    Each night, you learn how many of your 2 alive neighbors are evil.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            left, right = (info.get_next_player_who_is(
                state,
                lambda s, p: info.IsAlive(p)(s, src) is info.TRUE,
                src,
                clockwise,
            ) for clockwise in (True, False))
            evil_neighbours = [info.IsEvil(left)]
            if left != right:
                evil_neighbours.append(info.IsEvil(right))
            return info.ExactlyN(N=self.count, args=evil_neighbours)(state, src)

@dataclass
class EvilTwin(Character):
    """
    You & an opposing player know each other.
    If the good player is executed, evil wins. Good can't win if you both live.
    """
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    twin: PlayerID | None = None

    @dataclass
    class Is(info.ExternalInfo):
        """The 'good' twin reports an EvilTwin using EvilTwin.Is(player)."""
        eviltwin: PlayerID
        def __call__(self, state: State, src: PlayerID) -> bool:
            eviltwin = state.players[self.eviltwin].character
            return isinstance(eviltwin, EvilTwin) and eviltwin.twin == src

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        eviltwin = state.players[me]
        if eviltwin.droison_count:
            raise NotImplementedError('Poisoned EvilTwin')
        
        night_idx = (
            state.night if state.current_phase is core.Phase.NIGHT 
            else state.day + 1 if state.current_phase is core.Phase.DAY
            else 1
        )
        twin_alignment = ~info.IsEvil(me)(state, me)
        for player_id in range(len(state.players)):
            # Only players of opposing alignment can be twins
            if not (info.IsEvil(player_id)(state, me) is twin_alignment):
                continue
            claims_good_twin = any(
                (isinstance(ex_info, EvilTwin.Is) and ex_info.eviltwin == me)
                for ex_info in state.players[player_id].external_night_info.get(
                    (night_idx, EvilTwin), []
                )
            )
            if not (claims_good_twin or info.behaves_evil(state, player_id)):
                continue
            # This is a valid choice of twin
            new_state = state.fork()
            new_state.players[me].character.twin = player_id
            yield new_state

    def death_in_town(
        self,
        state: State,
        death: PlayerID,
        me: PlayerID
    ) -> StateGen:
        if (
            (death != self.twin and death != me)  # `me` could be good
            or info.IsEvil(death)(state, me) is not info.FALSE
        ):
            yield state
        elif state.players[me].droison_count:
            state.math_misregistration()
            yield state

@dataclass
class FangGu(Character):
    """Not yet implemented"""
    category: ClassVar[Categories] = DEMON
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        (min_tf, max_tf), (min_out, max_out), mn, dm = bounds
        bounds = (min_tf - 1, max_tf - 1), (min_out + 1, max_out + 1), mn, dm
        return bounds
    
    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        raise NotImplementedError("FangGu")

@dataclass
class FortuneTeller(Character):
    """
    Each night, choose 2 players: you learn if either is a Demon. 
    There is a good player that registers as a Demon to you.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    red_herring: PlayerID | None = None

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

    def _world_str(self, state: State) -> str:
        return (
            'FortuneTeller (Red Herring = '
            f'{state.players[self.red_herring].name})'
        )

@dataclass
class Gambler(Character):
    """
    Each night*, choose a player & guess their character:
    if you guess wrong, you die.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    @dataclass
    class Gamble(info.NotInfo):
        player: PlayerID
        character: type[Character]

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Override Reason: Die on error, fork on MAYBE, ignore vortox"""
        gambler = state.players[me]
        if gambler.is_evil:
            raise NotImplementedError("Evil Gambler")
        
        ping = state.get_night_info(Gambler, me, night)
        if gambler.is_dead or ping is None:
            yield state
            return

        result = info.IsCharacter(ping.player, ping.character)(state, me)
        if result is info.TRUE:
            yield state
        elif result is info.FALSE:
            # Gambler attacks themselves with their own ability
            if gambler.droison_count:
                state.math_misregistration()
                yield state; return
            yield from self.attacked_at_night(state, me, me)
        elif result is info.MAYBE:
            # Yield a world for both live and die case
            yield state.fork()
            die_state =state.fork()
            if gambler.droison_count:
                die_state.math_misregistration()
                yield die_state; return
            else:
                yield from self.attacked_at_night(die_state, me, me)

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
        if night == 1 or demon.is_dead:
            yield state
            return
        sunk_a_kill = False
        for target in range(len(state.players)):
            dead_target = state.players[target].is_dead
            if dead_target:
                if sunk_a_kill:
                    continue  # Dedupe sinking kill choice
                sunk_a_kill = True
            new_state = state.fork()
            if demon.droison_count:
                if not dead_target:
                    new_state.math_misregistration()
                yield new_state
                continue
            target_char = new_state.players[target].character
            yield from target_char.attacked_at_night(new_state, target, me)

@dataclass
class Goblin(Character):
    """TODO: Ability not yet implemented"""
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

@dataclass
class Gossip(Character):
    """
    Each day, you may make a public statement.
    Tonight, if it was true, a player dies.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    @dataclass
    class Gossip(events.Event):
        statement: info.Info
        player: PlayerID | None = None
        def __call__(self, state: State) -> StateGen:
            gossip = state.players[self.player]
            # Evaluate the gossip now during the day, act on it later at night
            gossip.prev_gossip = (self.statement(state, self.player), state.day)
            yield state

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Override Reason: On True gossip, create a world for every kill."""
        gossip = state.players[me]
        result, gossip_day = getattr(gossip, 'prev_gossip', (None, None))
        if (
            gossip.is_dead
            or result is None
            or result is info.FALSE
            or gossip_day != night - 1
        ):
            yield state; return
        
        dud_kill_done = False
        if result is info.MAYBE:
            yield state.fork()
            dud_kill_done = True

        if gossip.droison_count:
            state.math_misregistration()
            yield state; return

        for target in range(len(state.players)):
            if state.players[target].is_dead:
                # Dedupe worlds where nobody dies. I _think_ this is OK...
                if dud_kill_done:
                    continue
                dud_kill_done = True
            new_state = state.fork()

            target_char = new_state.players[target].character
            yield from target_char.attacked_at_night(new_state, target, me)

@dataclass
class Imp(GenericDemon):
    """
    Each night*, choose a player: they die. 
    If you kill yourself this way, a Minion becomes the Imp.
    """

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Override Reason: Add star pass to generic demon"""
        imp = state.players[me]
        if night == 1 or imp.is_dead:
            yield state; return
        
        # Kill other player
        sunk_a_kill = False
        for target in range(len(state.players)):
            if target == me:
                continue
            if state.players[target].is_dead:
                if sunk_a_kill:
                    continue  # Dedupe sinking kill choice
                sunk_a_kill = True
            new_state = state.fork()
            if imp.droison_count:
                new_state.math_misregistration()
                continue
            target_char = new_state.players[target].character
            yield from target_char.attacked_at_night(new_state, target, me)
        
        # Star pass
        if (
            imp.droison_count
            or self.cant_die(state, me) 
            or getattr(imp, 'safe_from_demon_count', 0)
        ):
            failed_starpass_state = state.fork()
            failed_starpass_state.math_misregistration()
            yield failed_starpass_state
            return
        self.death_explanation = f'Starpassed N{state.night}'
        # Decide who catches the star pass. SW must catch if able.
        scarletwomen, other_minions = [], []
        for player in state.players:
            character = player.character
            # BUG: technically this is a bug because SW.catches_death() can
            # incremement the Math number, so if there are 2 SW only one of whom
            # is poisoned, Math will incrememnt but SW won't have misfired.
            # Oh well.
            if character is ScarletWoman and character.catches_death(
                state, imp, player, True
            ):
                scarletwomen.append(player.id)
            elif character.category is MINION and not player.is_dead:
                other_minions.append(player.id)
        catchers = scarletwomen if scarletwomen else other_minions

        for minion in catchers:
            new_state = state.fork()
            # Note this slightly odd choice of if condition captures that the SW
            # only wakes if they caught the star pass _due to their ability_!
            if scarletwomen:
                new_state.players[minion].woke()
            for substate in new_state.character_change(minion, Imp):
                new_me = substate.players[me].character
                yield from new_me.apply_death(substate, me, src=me)

        if not catchers:
            new_state = state.fork()
            new_me = new_state.players[me].character
            yield from new_me.apply_death(new_state, me, src=me)

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

@dataclass
class Juggler(Character):
    """
    On your 1st day, publicly guess up to 5 players' characters. 
    That night, you learn how many you got correct.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    @dataclass
    class Juggle(events.Event):
        juggle: dict[PlayerID, type[Character]]
        player: PlayerID | None = None
        def __call__(self, state: State) -> StateGen:
            juggler = state.players[self.player]
            # Evaluate the juggles now, check the count later.
            juggler.correct_juggles = tuple(
                info.IsCharacter(player, character)(state, self.player)
                for player, character in self.juggle.items()
            )
            yield state

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, me: PlayerID) -> STBool:
            juggler = state.players[me]
            assert state.night == juggler.character.first_night + 1, (
                "Juggler.Ping only allowed on Juggler's second night"
            )
            correct_juggles = getattr(juggler, 'correct_juggles', None)
            assert correct_juggles is not None, (
                "No Juggler.Juggle happened before the Juggler.Ping"
            )
            juggler.woke()
            return info.ExactlyN(N=self.count, args=correct_juggles)(state, me)

@dataclass
class Klutz(Character):
    """
    When you learn that you died, publicly choose 1 alive player:
    if they are evil, your team loses.
    """
    category: ClassVar[Categories] = OUTSIDER
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    @dataclass
    class Choice(events.Event):
        choice: PlayerID
        player: PlayerID | None = None
        def __call__(self, state: State) -> StateGen:
            klutz = state.players[self.player]
            assert klutz.is_dead, "Unlikely the puzzle says that."
            if not info.has_ability_of(state, self.player, Klutz):
                if info.behaves_evil(state, self.player):
                    yield state
                return
            # Game is not over, so Klutz is claiming chosen player is good.
            is_good = ~info.IsEvil(self.choice)(state, self.player)
            if is_good is info.TRUE:
                yield state
            elif klutz.droison_count:
                state.math_misregistration(is_good)
                yield state
        
@dataclass
class Knight(Character):
    """
    You start knowing 2 players that are not the Demon.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID

        def __call__(self, state: State, src: PlayerID) -> STBool:
            return ~(
                info.IsCategory(self.player1, DEMON)(state, src) |
                info.IsCategory(self.player2, DEMON)(state, src)
            )

@dataclass
class Leviathan(Character):
    """
    If more than 1 good player is executed, evil wins.
    All players know you are in play. After day 5, evil wins.
    """
    category: ClassVar[Categories] = DEMON
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Game ends if S&H Leviathan reaches Night 6."""
        leviathan = state.players[me]
        if night < 6 or leviathan.is_dead:
            yield state
        elif leviathan.droison_count:
            state.math_misregistration()
            yield state

@dataclass
class Librarian(Character):
    """
    You start knowing that 1 of 2 players is a particular Outsider. 
    (Or that zero are in play.)
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        player1: PlayerID | None
        player2: PlayerID | None = None
        character: type[Character] | None = None

        def __call__(self, state: State, src: PlayerID) -> STBool:
            usage = (
                'Librarian.Ping usage: '
                'Librarian.Ping(player1, player2, character) or Ping(None)'
            )
            if self.player1 is None:
                assert self.player2 is None and self.character is None, usage
                return info.ExactlyN(N=0, args=[
                    info.IsCategory(player, OUTSIDER)
                    for player in range(len(state.players))
                ])(state, src)

            else:
                assert (self.player2 is not None 
                    and self.character is not None), usage
                return (
                    info.IsCharacter(self.player1, self.character)(state, src) |
                    info.IsCharacter(self.player2, self.character)(state, src)
                )

@dataclass
class LordOfTyphon(GenericDemon):
    """
    Each night*, choose a player: they die. [Evil characters are in a line. 
    You are in the middle. +1 Minion. -? to +? Outsiders]
    """
    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        tf, out, (min_lo, min_hi), dm = bounds
        return ((-99, 99), (-99, 99), (min_lo + 1, min_hi + 1), dm)

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Check evil in a row, Typhon in middle."""
        if state.current_phase is not core.Phase.SETUP:
            yield state; return
        evil = [player.is_evil for player in state.players]
        N = len(state.players)
        if not evil[(me - 1) % N] or not evil[(me + 1) % N]:
            return
        if 'e' * sum(evil) in ''.join('e' if e else 'g' for e in evil) * 2:
            yield state

@dataclass
class Lunatic(Character):
    """
    You think you are the Demon, but you are not.
    The demon knows who you are & who you chose at night.
    TODO: Not quite properly implemented yet - see todo.md
    """
    category: ClassVar[Categories] = OUTSIDER
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """
        Override Reason: Poisoned Lunatic doesn't tell the Demon their kill
        choice, so should tick Mathematician number up.
        TODO: Lunatic-Mathematician jinx, if the Lunatic's kill choice is not
        followed by the demon, the Math number increments. Currntly don't model
        Lunatic kill choices.
        """

@dataclass
class Marionette(Character):
    """
    You think you are a good character, but you are not. 
    The Demon knows who you are. [You neighbor the Demon]
    """
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    # wake_pattern is decided during run_setup

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        (tf_lo, tf_hi), (out_lo, out_hi), mn, dm = bounds
        return ((tf_lo, tf_hi + 1), (out_lo - 1, out_hi), mn, dm)

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Check neighbouring Demon"""
        if state.current_phase is core.Phase.SETUP:
            N = len(state.players)
            demon_neighbour = (
                info.IsCategory((me - 1) % N, DEMON)(state, me) 
                | info.IsCategory((me + 1) % N, DEMON)(state, me)
            )
            if demon_neighbour is info.FALSE:
                return
            if demon_neighbour is info.MAYBE:
                state.math_misregistration()  # e.g. Recluse-Mario triggers Math
        self.wake_pattern = state.players[me].claim.wake_pattern
        yield state

@dataclass
class Mathematician(Character):
    """
    Each night, you learn how many players' abilities worked abnormally
    (since dawn) due to another character's ability.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            lo, hi = state.math_misregistration_bounds
            return info.STBool(lo <= self.count <= hi)

@dataclass
class Mayor(Character):
    """
    If only 3 player live & no execution occurs, your team wins. 
    If you die at night, another player might die instead.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

@dataclass
class Mutant(Character):
    """
    If you are "mad" about being an Outsider, you might be executed.
    """
    category: ClassVar[Categories] = OUTSIDER
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    def run_day(self, state: State, day: int, src: PlayerID) -> StateGen:
        # Mutants never break madness in these puzzles
        player = state.players[src]
        if player.is_dead or player.claim.category is not OUTSIDER:
            yield state
        elif player.droison_count:
            state.math_misregistration(info.MAYBE)  # Maybe ST is just nice :)
            yield state

@dataclass
class NightWatchman(Character):
    """
    Once per game, at night, choose a player:
    they learn you are the Nightwatchman.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_UNTIL_SPENT
    
    spent: bool = False

    @dataclass
    class Choice(info.NotInfo):
        """The Choice as reported by the NightWatchman."""
        player: PlayerID
        confirmed: bool
        
    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Override Reason: Poisoned NW must not be confirmed by good."""
        nightwatchman = state.players[me]
        if nightwatchman.is_evil or state.vortox:
            raise NotImplementedError(
                "When to spend if evil, or vortox giving incorrect ping source."
            )
        ping = state.get_night_info(NightWatchman, me, night)
        if ping is None:
            yield state; return
        if nightwatchman.is_dead or self.spent:
            return
        self.spent = True
        if ping.confirmed:
            if nightwatchman.droison_count == 0:
                yield state
        elif nightwatchman.droison_count:
            state.math_misregistration()
            yield state
            
@dataclass
class Noble(Character):
    """
    You start knowing 3 players, 1 and only 1 of which is evil.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID
        player3: PlayerID

        def __call__(self, state: State, src: PlayerID) -> STBool:
            return info.ExactlyN(N=1, args=(
                info.IsEvil(self.player1),
                info.IsEvil(self.player2),
                info.IsEvil(self.player3),
            ))(state, src)

@dataclass
class NoDashii(GenericDemon):
    """
    Each night*, choose a player: they die. 
    Your 2 Townsfolk neighbors are poisoned.
    """
    tf_neighbour1: PlayerID | None = None
    tf_neighbour2: PlayerID | None = None

    def run_setup(self, state: State, src: PlayerID) -> StateGen:
        # I allow the No Dashii to poison misregistering characters (e.g. Spy),
        # so there may be multiple possible combinations of neighbour pairs
        # depending on ST choices. Find them all and create a world for each.
        N = len(state.players)
        fwd_candidates, bkwd_candidates = [], []
        for candidates, direction in (
            (fwd_candidates, 1),
            (bkwd_candidates, -1),
        ):
            for step in range(1, N):
                player = (src + direction * step) % N
                is_tf = info.IsCategory(player, TOWNSFOLK)(state, src)
                if is_tf is not info.FALSE:
                    candidates.append(player)
                if is_tf is info.TRUE:
                    break
        # Create a world or each combination of left and right poisoned player
        for fwd in fwd_candidates:
            for bkwd in bkwd_candidates:
                new_state = state.fork()
                new_nodashii = new_state.players[src].character
                new_nodashii.tf_neighbour1 = fwd
                new_nodashii.tf_neighbour2 = bkwd
                new_nodashii.maybe_activate_effects(new_state, src)
                yield new_state

    def _activate_effects_impl(self, state: State, src: PlayerID):
        state.players[self.tf_neighbour1].droison(state, src)
        state.players[self.tf_neighbour2].droison(state, src)

    def _deactivate_effects_impl(self, state: State, src: PlayerID):
        state.players[self.tf_neighbour1].undroison(state, src)
        state.players[self.tf_neighbour2].undroison(state, src)

    def _world_str(self, state: State) -> str:
        return 'NoDashii (Poisoned {} & {})'.format(
            state.players[self.tf_neighbour1].name,
            state.players[self.tf_neighbour2].name,
        )

@dataclass
class Oracle(Character):
    """
    Each night*, you learn how many dead players are evil.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            return info.ExactlyN(
                N=self.count, 
                args=[
                    info.IsEvil(player) & ~info.IsAlive(player)
                    for player in range(len(state.players))
                ]
            )(state, src)

@dataclass
class Philosopher(Character):
    """
    Once per game, at night, choose a good character: gain that ability.
    If this character is in play, they are drunk.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    # Wake pattern is replaced upon Character choice
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    droisoned_choice: type[Character] | None = None
    active_ability: Character | None = None
    drunk_targets: list[PlayerID] | None = None

    @dataclass
    class Choice(info.NotInfo):
        character: type[Character]

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        philo = state.players[me]
        if philo.is_evil:
            raise NotImplementedError('Evil Philosopher')

        if self.active_ability is not None:
            yield from self.active_ability.run_night(state, night, me)
            return
        if philo.is_dead:
            yield state; return  # I miss GOTOs, and I'm not ashamed to say it.

        if self.droisoned_choice is not None:
            ping = state.get_night_info(self.droisoned_choice, me, night)
            if (
                ping is not None
                or Chambermaid.player_wakes_tonight(
                    state, me, character_override=self.droisoned_choice
                )
            ):
                state.math_misregistration()
            yield state; return

        choice = state.get_night_info(Philosopher, me, night)
        if choice is None:
            yield state; return

        if philo.droison_count:
            self.droisoned_choice = choice.character
            state.math_misregistration()
            yield state; return

        # Updating the phase order index is very specifically done before
        # setting the active ability or updating the night order
        state.update_phase_order_index_before_character_change(
            Philosopher, choice.character
        )
        self.active_ability = choice.character(first_night=state.night)
        state.update_character_orders()  # Night order changes
        self.wake_pattern = choice.character.wake_pattern
        self.is_liar = choice.character.is_liar  # Philo-Mutant...?

        for substate in self.active_ability.run_setup(state, me):
            drunk_combinations = list(
                info.all_registration_combinations([
                    info.IsCharacter(player, choice.character)(substate, me)
                    for player in range(len(state.players))
                ])
            )
            for drunk_targets in drunk_combinations:
                new_state = (
                    substate if len(drunk_combinations) == 1
                    else state.fork()
                )
                new_philo = new_state.players[me].character
                new_philo.drunk_targets = drunk_targets
                new_philo.maybe_activate_effects(new_state, me)
                yield new_state

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        if self.active_ability is None:
            return super().run_setup(state, me)
        return self.active_ability.run_setup(state, me)

    def run_day(self, state: State, day: int, me: PlayerID) -> StateGen:
        if self.active_ability is None:
            return super().run_day(state, day, me)
        return self.active_ability.run_day(state, day, me)

    def end_day(self, state: State, day: int, me: PlayerID) -> bool:
        if self.active_ability is None:
            return True
        return self.active_ability.end_day(state, day, me)

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.active_ability is None:
            return
        for player in self.drunk_targets:
            state.players[player].droison(state, me)
        self.active_ability._activate_effects_impl(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.active_ability is None:
            return
        for player in self.drunk_targets:
            state.players[player].undroison(state, me)
        self.active_ability._deactivate_effects_impl(state, me)

    def apply_death(self, *args, **kwargs) -> StateGen:
        if self.active_ability is None:
            return super().apply_death(*args, **kwargs)
        return self.active_ability.apply_death(*args, **kwargs)

    def executed(self, state: State, me: PlayerID, died: bool) -> StateGen:
        if self.active_ability is None:
            return super().executed(state, me, died)
        return self.active_ability.executed(state, me, died)

    def killed(self, *args, **kwargs) -> StateGen:
        if self.active_ability is None:
            return super().killed(*args, **kwargs)
        return self.active_ability.killed(*args, **kwargs)

    def cant_die(self, state: State, me: PlayerID) -> bool:
        if self.active_ability is None:
            return super().cant_die(state, me)
        return self.active_ability.cant_die(state, me)

@dataclass
class Po(GenericDemon):
    """
    Each night*, you may choose a player: they die.
    If your last choice was no-one, choose 3 players tonight.
    """

    charged: bool = False

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        po = state.players[me]
        if night == 1 or po.is_dead:
            yield state; return
        
        if not self.charged:
            # Charge World
            new_state = state.fork()
            new_state.players[me].character.charged = True
            yield new_state

            # 1 Kill World
            sunk_a_kill = False
            for target in range(len(state.players)):
                dead_target = state.players[target].is_dead
                if dead_target:
                    if sunk_a_kill:
                        continue  # Dedupe sinking kill choice
                    sunk_a_kill = True
                new_state = state.fork()
                if po.droison_count:
                    if not dead_target:
                        new_state.math_misregistration()
                    yield new_state
                    continue
                target_char = new_state.players[target].character
                yield from target_char.attacked_at_night(new_state, target, me)
        else:
            # 3 Kill World
            print('Untested code')
            self.charged = False
            if po.droison_count:
                state.math_misregistration()
                yield state
                return
            
            def kill_gen(states: StateGen, kill: PlayerID) -> StateGen:
                for state_ in states:
                    target = state_.players[kill].character
                    yield from target.attacked_at_night(state_, target, me)
            for kills in itertools.combinations(range(len(state.players)), r=3):
                new_states = [state.fork()]
                for kill in kills:
                    new_states = kill_gen(new_states, kill)
                yield from new_states

@dataclass
class Poisoner(Character):
    """
    Each night, choose a player: they are poisoned tonight and tomorrow day.
    """
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    target: PlayerID = None

    # Keep history just for pretty printing the history of a game.
    target_history: list[PlayerID] = field(default_factory=list)

    def run_night(self, state: State, night: int, src: PlayerID) -> StateGen:
        """Override Reason: Create a world for every poisoning choice."""
        poisoner = state.players[src]
        if poisoner.is_dead:
            yield state; return
        for target in range(len(state.players)):
            new_state = state.fork()
            new_poisoner = new_state.players[src].character
            # Even droisoned poisoners make a choice, because they might be 
            # undroisoned before dusk.
            new_poisoner.target = target
            new_poisoner.target_history.append(target)
            new_poisoner.maybe_activate_effects(new_state, src)
            yield new_state

    def end_day(self, state: State, day: int, me: PlayerID) -> bool:
        self.maybe_deactivate_effects(state, me)
        self.target = None
        return True

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.target == me:
            state.players[me].droison_count += 1
        elif self.target is not None:
            state.players[self.target].droison(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.target == me:
            state.players[me].droison_count -= 1
        elif self.target is not None:
            state.players[self.target].undroison(state, me)

    def _world_str(self, state: State) -> str:
        return (
            f'{type(self).__name__} (Poisoned '
            f'{", ".join(state.players[p].name for p in self.target_history)})'
        )


@dataclass
class Pukka(Character):
    """
    Each night, choose a player: they are poisoned.
    The previously poisoned player dies then becomes healthy.
    """
    category: ClassVar[Categories] = DEMON
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    target: PlayerID | None = None

    # For pretty-printing the history of a game.
    target_history: list[PlayerID] = field(default_factory=list)

    def run_night(self, state: State, day: int, me: PlayerID) -> StateGen:
        """TODO: This wouldn't handle picking a Goon"""
        pukka = state.players[me]
        if pukka.is_dead:
            yield state; return
        if pukka.droison_count:
            if (
                self.target is not None
                and not state.players[self.target].is_dead
            ):
                state.math_misregistration()
            yield state; return

        # A Pukka's new target is poisoned, then the previous target dies, and
        # _then_ the previous target becomes sober. For that reason we can't use
        # `maybe_deactivate_effects` because target will have changed, so we
        # manually handle the unpoisoning of the killed player.
        self.effects_active = False
        for new_target in range(len(state.players)):
            new_state = state.fork()
            new_pukka = new_state.players[me].character
            new_pukka.target = new_target
            new_pukka.target_history.append(new_target)
            new_pukka.maybe_activate_effects(new_state, me)
            if self.target is None:
                yield new_state
            else:
                target_char = new_state.players[self.target].character
                for substate in target_char.attacked_at_night(
                    new_state, self.target, me
                ):
                    substate.players[self.target].undroison(substate, me)
                    yield substate

    def end_day(self, state: State, day: int, me: PlayerID) -> bool:
        self.maybe_deactivate_effects(state, me)
        return True

    def _activate_effects_impl(self, state: State, me: PlayerID):
        state.players[self.target].droison(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        # Break a self-poisoning infinite recursion, whilst still leaving the 
        # Pukka marked as droisoned.
        if self.target != me:
            state.players[self.target].undroison(state, me)

@dataclass
class Puzzlemaster(Character):
    """
    1 player is drunk, even if you die. If you guess (once) who it is, learn the
    Demon player, but guess wrong & get false info.
    """
    category: ClassVar[Categories] = OUTSIDER
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    puzzle_drunk: PlayerID | None = None
    spent: bool = False

    @dataclass
    class Ping(info.Info):
        guess: PlayerID
        demon: PlayerID
        def __call__(self, state: State, me: PlayerID) -> STBool:
            correct_demon = info.IsCategory(self.demon, DEMON)(state, me)
            puzzlemaster = state.players[me].character
            if self.guess == puzzlemaster.puzzle_drunk:
                return correct_demon
            return ~correct_demon

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Choose puzzle_drunk."""
        for player in range(len(state.players)):
            new_state = state.fork()
            new_puzzlemaster = new_state.players[me].character
            new_puzzlemaster.puzzle_drunk = player
            new_puzzlemaster.maybe_activate_effects(new_state, me, Reason.SETUP)
            yield new_state

    def maybe_activate_effects(
        self,
        state: State,
        me: PlayerID,
        reason: Reason,
    ) -> None:
        """Override Reason: Even when dead."""
        if (
            not self.effects_active 
            and state.players[me].droison_count == 0
            and reason is not Reason.RESURRECTION
        ):
            self.effects_active = True
            state.players[self.puzzle_drunk].droison(state, me)

    def maybe_deactivate_effects(
        self,
        state: State,
        me: PlayerID,
        reason: Reason,
    ) -> None:
        """Override Reason: Even when dead."""
        if (
            self.effects_active 
            and reason is not Reason.DEATH
            and self.puzzle_drunk != me  # Break recursion
        ):
            self.effects_active = False
            state.players[self.puzzle_drunk].undroison(state, me)

    def _world_str(self, state: State) -> str:
        return (
            f'Puzzlemaster ({state.players[self.puzzle_drunk].name} is '
            'puzzle-drunk)'
        )

@dataclass
class Ravenkeeper(Character):
    """
    If you die at night, you are woken to choose a player:
    you learn their character.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    death_night: int | None = None

    @dataclass
    class Ping(info.Info):
        player: PlayerID
        character: type[Character]

        def __call__(self, state: State, src: PlayerID) -> STBool:
            assert state.night > 1, "Ravenkeepers don't die night 1!"
            ravenkeeper = state.players[src].character
            death_night = ravenkeeper.death_night
            if death_night is None or death_night != state.night:
                return info.FALSE
            return info.IsCharacter(self.player, self.character)(state, src)

    def apply_death(
        self,
        state: State,
        me: PlayerID,
        src: PlayerID | None = None,
    ) -> StateGen:
        """Override Reason: Record when death happened."""
        if state.night is not None:
            self.death_night = state.night
            state.players[me].woke()
        yield from super().apply_death(state, me, src)

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Override Reason: Even if dead."""
        # The Ping checks the death was on the same night.
        if self.default_info_check(state, me, even_if_dead=True):
            yield state

@dataclass
class Recluse(Character):
    """
    You might register as evil & as a Minion or Demon, even if dead.
    """
    category: ClassVar[Categories] = OUTSIDER
    is_liar: ClassVar[bool] = False
    misregister_categories: ClassVar[tuple[Categories, ...]] = (MINION, DEMON)
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

@dataclass
class Sage(Character):
    """
    If the Demon kills you, you learn that it is 1 of 2 players.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    death_night: int | None = None

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID

        def __call__(self, state: State, src: PlayerID) -> STBool:
            assert state.night > 1, "Sages don't die night 1!"
            sage = state.players[src].character
            death_night = sage.death_night
            if death_night is None or death_night != state.night:
                return info.FALSE
            return (
                info.IsCategory(self.player1, DEMON)(state, src)
                | info.IsCategory(self.player2, DEMON)(state, src)
            )

    def apply_death(
        self,
        state: State,
        me: PlayerID,
        src: PlayerID | None = None,
    ) -> StateGen:
        """Override Reason: Record when death happened."""
        killed_by_demon = info.IsCategory(src, DEMON)(state, me)
        if state.night is not None and killed_by_demon is not info.FALSE:
            self.death_night = state.night
            state.players[me].woke()
        yield from super().apply_death(state, me, src)

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Override Reason: Even if dead."""
        # The Ping checks the death was on the same night.
        if self.default_info_check(state, me, even_if_dead=True):
            yield state

@dataclass
class Savant(Character):
    """
    Each day, you may visit the Storyteller to learn 2 things in private: 
    one is true & one is false.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    @dataclass
    class Ping(info.Info):
        a: info.Info
        b: info.Info
        def __call__(self, state: State, src: PlayerID):
            a, b = self.a(state, src), self.b(state, src)
            if state.vortox:
                return ~(a | b)
            return a ^ b

    def run_day(self, state: State, day: int, me: PlayerID) -> StateGen:
        """ Override Reason: Novel Vortox effect on Savant, see Savant.Ping."""
        savant = state.players[me]
        ping = state.get_day_info(me, day)
        if (
            savant.is_dead
            or savant.is_evil
            or ping is None
        ):
            yield state
            return
        result = ping(state, me)
        if savant.droison_count:
            state.math_misregistration(result)
            yield state
        elif result is not info.FALSE:
            yield state

@dataclass
class ScarletWoman(Character):
    """
    If there are 5 or more players alive & the Demon dies, you become the Demon.
    (Travellers don't count).
    """
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    def death_in_town(
        self,
        state: State,
        death: PlayerID,
        me: PlayerID
    ) -> StateGen:
        """Catch a Demon death. I don't allow catching Recluse deaths."""
        scarletwoman = state.players[me]
        dead_player = state.players[death]
        if self.catches_death(state, dead_player, scarletwoman):
            if state.night is not None:
                scarletwoman.woke()
            yield from state.character_change(me, type(dead_player.character))
        else:
            yield state

    def catches_death(
        self,
        state: State,
        dead: Player,
        scarletwoman: Player,
        death_not_yet_applied: bool = False,
    ) -> bool:
        """
        Trigger condition is also checked by Imp, so has its own method.
        WARNING: This method may mutate `state` by incremening the Math number.
        """
        living_players = sum(
            not p.is_dead and not p.character.category is TRAVELLER
            for p in state.players
        )
        living_player_threshold = 4 + death_not_yet_applied
        would_catch = (
            not scarletwoman.is_dead
            and dead.character.category is DEMON
            and living_players >= living_player_threshold
        )
        if would_catch and scarletwoman.droison_count:
            state.math_misregistration()
            return False
        return would_catch

@dataclass
class Seamstress(Character):
    """
    Once per game, at night, choose 2 players (not yourself):
    you learn if they are the same alignment.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID
        same: bool
        def __call__(self, state: State, src: PlayerID) -> STBool:
            a = info.IsEvil(self.player1)(state, src)
            b = info.IsEvil(self.player2)(state, src)
            enemies = a ^ b
            if self.same:
                return ~enemies
            return enemies

@dataclass
class Shugenja(Character):
    """
    You start knowing if your closest evil player is clockwise or 
    anti-clockwise. If equidistant, this info is arbitrary.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        clockwise: bool
        def __call__(self, state: State, src: PlayerID) -> STBool:
            N = len(state.players)
            direction = 1 if self.clockwise else - 1
            evils = [None] + [
                info.IsEvil((src + direction * step) % N)(state, src)
                for step in range(1, N)
            ]
            fwd_maybe, bwd_maybe, fwd_true, bwd_true = N, N, N, N
            for step in range(N // 2, 0, -1):
                if evils[step] is info.TRUE:
                    fwd_true, fwd_maybe = step, step
                elif evils[step] is info.MAYBE:
                    fwd_maybe = step
                if evils[-step] is info.TRUE:
                    bwd_true, bwd_maybe = step, step
                elif evils[-step] is info.MAYBE:
                    bwd_maybe = step

            if bwd_true < fwd_maybe:
                return info.FALSE
            if fwd_true < bwd_maybe:
                return info.TRUE
            return info.MAYBE

@dataclass
class SnakeCharmer(Character):
    """
    Each night, choose an alive player:
    a chosen Demon swaps characters & alignments with you & is then poisoned.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    self_droison: bool = False

    @dataclass
    class Choice(info.NotInfo):
        player: PlayerID

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """Override Reason: Charming!"""
        snakecharmer = state.players[me]
        if snakecharmer.is_evil:
            raise NotImplementedError('Evil Snakecharmer!')
        choice = state.get_night_info(SnakeCharmer, me, night)
        if choice is None:
            yield state; return
        if not isinstance(choice, SnakeCharmer.Choice):
            return

        is_demon = info.IsCategory(choice.player, DEMON)(state, me)
        if is_demon is info.FALSE:
            yield state; return
        if is_demon is info.MAYBE:
            # Yield world where the jump happens plus one were it doesn't
            yield state.fork()
            jump_state = state.fork()
        else:
            jump_state = state

        if snakecharmer.droison_count:
            if not self.self_droison:
                jump_state.math_misregistration()
            yield jump_state; return

        # Do the jump
        snakecharmer = jump_state.players[me]
        demon_player = jump_state.players[choice.player]
        demon_is_evil = demon_player.is_evil
        demon_character = type(demon_player.character)
        demon_player.is_evil = snakecharmer.is_evil
        snakecharmer.is_evil = demon_is_evil
        for ss1 in jump_state.character_change(me, demon_character):
            for ss2 in ss1.character_change(choice.player, SnakeCharmer):
                new_snakecharmer = ss2.players[choice.player].character
                new_snakecharmer.self_droison = True
                new_snakecharmer.maybe_activate_effects(state, me)
                yield ss2

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.self_droison:
            state.players[me].droison_count += 1

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.self_droison:
            state.players[me].undroison(state, me)

 
@dataclass
class Soldier(Character):
    """
    You are safe from the Demon.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Activate safe_from_demon."""
        self.maybe_activate_effects(state, me)
        yield state

    def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
        soldier = state.players[me]
        # Characetrs like monk might delete the attr if it hits 0, so recreate
        # it if neccessary.
        if hasattr(soldier, 'safe_from_demon_count'):
            soldier.safe_from_demon_count += 1
        else:
            soldier.safe_from_demon_count = 1

    def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
        state.players[me].safe_from_demon_count -= 1

@dataclass
class Steward(Character):
    """
    You start knowing 1 good player.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        player: PlayerID
        def __call__(self, state: State, src: PlayerID) -> STBool:
            return ~info.IsEvil(self.player)(state, src)

@dataclass
class Saint(Character):
    """
    If you die by execution, your team loses.
    """
    category: ClassVar[Categories] = OUTSIDER
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    def executed(self, state: State, me: PlayerID, died: bool) -> StateGen:
        """
        Override Reason: Game is not over, execution is not a valid world.
        We let the super method handle any non-Saint-related execution details.
        """
        droisoned = state.players[me].droison_count
        if droisoned:
            state.math_misregistration()
        if droisoned or not died:
            return super().executed(self, state, me, died)


@dataclass
class Slayer(Character):
    """
    Once per game, during the day, publicly choose a player: 
    if they are the Demon, they die.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    spent: bool = False

    @dataclass
    class Shot(events.Event):
        target: PlayerID
        died: bool
        player: PlayerID | None = None

        def __call__(self, state: State) -> StateGen:
            shooter = state.players[self.player]
            if not info.has_ability_of(state, self.player, Slayer):
                if info.behaves_evil(state, self.player):
                    yield state
                return
            target = state.players[self.target]
            if (
                shooter.is_dead
                or target.is_dead
                or not isinstance(shooter.character, Slayer)
                or shooter.character.spent
            ):
                should_die = info.FALSE
            else:
                should_die = info.IsCategory(self.target, DEMON)(
                    state, self.player
                )
            if shooter.droison_count:
                if should_die is not info.FALSE and not self.died:
                    state.math_misregistration(~should_die)
                should_die = info.FALSE

            if isinstance(shooter.character, Slayer):
                shooter.character.spent = True

            if self.died and should_die is not info.FALSE:
                state.math_misregistration(should_die)
                yield from target.character.killed(
                    state, self.target, src=shooter.id
                )
            elif not self.died and should_die is not info.TRUE:
                yield state

@dataclass
class Spy(Character):
    """
    Each night, you see the Grimoire. You might register as good & as a 
    Townsfolk or Outsider, even if dead.
    """
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    misregister_categories: ClassVar[tuple[Categories, ...]] = (
        TOWNSFOLK, OUTSIDER
    )
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

@dataclass
class Undertaker(Character):
    """
    Each night*, you learn which character died by execution today.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    @dataclass
    class Ping(info.Info):
        player: PlayerID | None
        character: type[Character] | None

        def __call__(self, state: State, src: PlayerID) -> STBool:
            assert state.night > 1, "Undertaker acts from second night."
            assert (self.character is None) == (self.player is None)

            previous_day_events = state.day_events.get(state.night - 1, [])
            if self.player is None:
                return STBool(
                    not any(
                        isinstance(e, events.Execution) and e.died 
                        for e in previous_day_events
                    )
                )
            elif any(
                isinstance(event, events.Execution)
                and event.player == self.player
                and event.died
                for event in previous_day_events
            ):
                return info.IsCharacter(self.player, self.character)(state, src)
            return info.FALSE

@dataclass
class Washerwoman(Character):
    """
    You start knowing that 1 of 2 players is a particular Townsfolk.
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

@dataclass
class Witch(Character):
    """
    Each night, choose a player: if they nominate tomorrow, they die.
    If just 3 players live, you lose this ability.
    """
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    target: PlayerID | None = None    

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        witch = state.players[me]

        if self.target is not None:
            del state.players[self.target].witch_cursed
            self.target = None

        if witch.is_dead or sum(not p.is_dead for p in state.players) <= 3:
            yield state; return
       
        if witch.droison_count:
            state.math_misregistration()
            yield state; return
        
        for target in range(len(state.players)):
            if state.players[target].is_dead:
                # There are enough ways for curse not to trigger, don't need
                # this one too (until we implement the Goon...)
                continue
            new_state = state.fork()
            new_state.players[me].character.target = target
            new_state.players[target].witch_cursed = witch.name
            yield new_state
            
    def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
        if self.target is not None:
            state.players[self.target].witch_cursed = state.players[me].name

    def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
        if self.target is not None:
            del state.players[self.target].witch_cursed



@dataclass
class VillageIdiot(Character):
    """
    Each night, choose a player: you learn their alignment. 
    [+0 to +2 Village Idiots. 1 of the extras is drunk]
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    self_droison: bool = False

    @dataclass
    class Ping(info.Info):
        player: PlayerID
        is_evil: bool
        def __call__(self, state: State, src: PlayerID) -> STBool:
            registers_evil = info.IsEvil(self.player)(state, src)
            return registers_evil == info.STBool(self.is_evil)

    def run_setup(self, state: State, src: PlayerID) -> StateGen:
        # If there is more than one Village Idiot, choose one to be the drunk VI
        VIs = [i for i, player in enumerate(state.players)
                if isinstance(player.character, VillageIdiot)]
        already_done = any(state.players[p].character.self_droison for p in VIs)
        if len(VIs) == 1 or already_done:
            yield state
            return

        for vi in VIs:
            new_state = state.fork()
            new_state.players[vi].droison_count += 1
            new_state.players[vi].character.self_droison = True
            yield new_state

    def _world_str(self, state: State) -> str:
        """For printing nice output representations of worlds"""
        return f'VillageIdiot ({"Drunk" if self.self_droison else "Sober"})'

@dataclass
class Virgin(Character):
    """
    The 1st time you are nominated, if the nominator is a Townsfolk, 
    they are executed immediately.
    """
    category: ClassVar[Categories] = TOWNSFOLK
    is_liar: ClassVar[bool] = False
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    spent: bool = False

    # Virgin nominations are checked in the ExecutedByST and 
    # UneventfulExecution events

@dataclass
class Vortox(GenericDemon):
    """
    Each night*, choose a player: they die. 
    Townsfolk abilities yield false info.
    Each day, if no-one was executed, evil wins.
    """

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        self.maybe_activate_effects(state, me)
        yield state

    def end_day(self, state: State, day: int, me: PlayerID) -> bool:
        events_ = state.day_events.get(day, [])
        return any(isinstance(ev, events.Execution) for ev in events_)

    def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
        state.vortox = True

    def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
        state.vortox = False

@dataclass
class Xaan(Character):
    """
    On night X, all Townsfolk are poisoned until dusk. [X Outsiders]
    """
    category: ClassVar[Categories] = MINION
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    X: int = 0
    targets: list[PlayerID] | None = None

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        tf, out, mn, dm = bounds
        return ((-99, 99), (-99, 99), mn, dm)

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        if state.current_phase != core.Phase.SETUP:
            raise NotImplementedError(
                "Xaan created mid-game, X wasn't calculated at setup"
            )
        # Despite the recent ruling, I still allow misregistration during setup,
        # and so create a world for each possible value of X. Can remove this
        # later if the ruling survives the test of time.
        outsiders = [
            info.IsCategory(player, OUTSIDER)(state, me)
            for player in range(len(state.players))
        ]
        X_lo = sum(outsider is info.TRUE for outsider in outsiders)
        X_hi = sum(outsider is not info.FALSE for outsider in outsiders)
        for X in range(X_lo, X_hi + 1):
            new_state = state.fork()
            new_state.players[me].character.X = X
            yield new_state

    def run_night(self, state: State, night: int, me: PlayerID) -> StateGen:
        """
        On night X, create a world for every possible combination of poison
        targets (i.e., handle a Spy misregistering as a TF or not).
        """
        xaan = state.players[me]
        if xaan.is_dead or night != self.X:
            self.targets = None
            yield state
            return

        townsfolk = [
            info.IsCategory(player, TOWNSFOLK)(state, me)
            for player in range(len(state.players))
        ]
        maybes = [i for i, is_tf in enumerate(townsfolk) if is_tf is info.MAYBE]
        trues = [i for i, is_tf in enumerate(townsfolk) if is_tf is info.TRUE]
        if xaan.droison_count and trues:
            # This is a best-effort at maintining Mathematician count, but
            # technically should only really trigger if one of the targets
            # doesn't misfire tonight. See TODO.
            state.math_misregistration()

        for maybe_subset in itertools.chain.from_iterable(
            itertools.combinations(maybes, r)
            for r in range(1, len(maybes) + 1)
        ):
            new_state = state.fork()
            new_xaan = new_state.players[me].character
            new_xaan.targets = trues + maybe_subset
            new_xaan.maybe_activate_effects(new_state, me)
            yield new_state

        # No fork for most common case
        xaan.character.targets = trues
        xaan.character.maybe_activate_effects(state, me)
        yield state

    def end_day(self, state: State, day: int, me: PlayerID) -> bool:
        xaan = state.players[me].character
        if xaan.targets is not None:
            xaan.maybe_deactivate_effects(state, me)
            xaan.targets = None
        return True

    def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
        xaan = state.players[me].character
        if xaan.targets is not None:
            for target in xaan.targets:
                state.players[target].droison(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
        xaan = state.players[me].character
        if xaan.targets is not None:
            for target in xaan.targets:
                state.players[target].undroison(state, me)

    def _world_str(self, state: State) -> str:
        return f'Xaan (X={self.X})'

@dataclass
class Zombuul(Character):
    """TODO: Not implemented properly yet"""
    category: ClassVar[Categories] = DEMON
    is_liar: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    registering_dead: bool = False



GLOBAL_SETUP_ORDER = [
    Atheist,
    Vortox,
    Marionette,
    NoDashii,
    Puzzlemaster,
    FortuneTeller,
    VillageIdiot,
    Drunk,
    Soldier,
    Xaan,
    EvilTwin,  # Must go after any alignment changes
    LordOfTyphon,  # Goes last to check evils created by setup are in a line
]

GLOBAL_NIGHT_ORDER = [
    Philosopher,
    Xaan,
    Leviathan,
    Poisoner,
    Courtier,
    Gambler,
    Acrobat,
    SnakeCharmer,
    EvilTwin,  # Nasty hack - see todo.md
    Witch,
    ScarletWoman,
    Imp,
    Pukka,
    Po,
    FangGu,
    NoDashii,
    Vortox,
    LordOfTyphon,
    Gossip,
    Sage,
    Ravenkeeper,
    Washerwoman,
    Librarian,
    Investigator,
    Chef,
    Empath,
    FortuneTeller,
    Undertaker,
    Clockmaker,
    Dreamer,
    Oracle,
    Seamstress,
    Juggler,
    Steward,
    Knight,
    Noble,
    Balloonist,
    Shugenja,
    VillageIdiot,
    NightWatchman,
    Chambermaid,
    Mathematician,
]

GLOBAL_DAY_ORDER = [
    Alsaahir,
    Artist,
    Savant,
    Mutant,
    Puzzlemaster,
    Klutz,
]

INACTIVE_CHARACTERS = [
    Atheist,
    Baron,
    Butler,
    Drunk,
    Goblin,
    Lunatic,
    Marionette,
    Mayor,
    Recluse,
    Saint,
    Slayer,
    Soldier,
    Spy,
    Virgin,
]


def get_character_phase_order_idx(
    global_order: Sequence[type[Character]],
    character: type[Character],
) -> int:
    try:
        return global_order.index(character)
    except ValueError:
        return 999999

def get_player_phase_order_idx(
    global_order: Sequence[type[Character]],
    state: State,
    player: PlayerID,
) -> int:
    for i, character in enumerate(global_order):
        if info.acts_like(state, player, character):
            return i
    return 999999
