
from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
import enum
import itertools
from typing import ClassVar, Sequence, TypeAlias, TYPE_CHECKING

from clockchecker.info import PlayerID

if TYPE_CHECKING:
    from .core import Player, State, StateGen
    from .events import Event
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
    - vigormortised, exorcised
 - Remember to set or call the following as appropriately
    - set `character.spent`
    - call `player.woke()` for Chambermaid if character uses using WakePattern.MANUAL
    - call `state.math_misregistration` for Mathematician counts
    - TODO: call `state.choose(target)` for Goon
   - If you use maybe_activate_effects, check if you should maybe_deactivate_effects
     before the next night.
"""

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
    misregister_categories: ClassVar[tuple['Category', ...]] = ()

    # Good characters who lie about themselves and their info (e.g., Drunk)
    lies_about_self: ClassVar[bool] = False

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

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """
        Take the character's night action. Most basic info roles can just
        inherit this default implementation and implement their own Pings to go
        in night_info.
        """
        if self.default_info_check(state, me):
            yield state

    def run_day(self, state: State, me: PlayerID) -> StateGen:
        if self.default_info_check(state, me):
            yield state

    def end_night(self, state: State, me: PlayerID) -> StateGen:
        """
        Take dawn actions (e.g. PitHag cleans up unexplained kills on arbitrary
        death nights).
        """
        yield state

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        """Take dusk actions (e.g. poisoner stops poisoning)."""
        yield state

    @staticmethod
    def global_end_night(state: State) -> bool:
        """
        Do accounting at end of night. Runs for every character on the script,
        regardless of what is in play. This is useful for asserting that a
        character's effects are invalid when that character is not in play, e.g.
        reject worlds with Widow pings if there is no Widow.
        """
        return True

    def default_info_check(
        self: Character,
        state: State,
        me: PlayerID,
        even_if_dead: bool = False,
        even_if_droisoned: bool = False,
    ) -> bool:
        """Most info roles can inherit this pattern for their info check."""
        if state.current_phase is core.Phase.NIGHT:
            ping = state.get_night_info(type(self), me, state.night)
        elif state.current_phase is core.Phase.DAY:
            ping = state.get_day_info(type(self), me)

        player = state.players[me]
        if (
                ping is None
                or info.behaves_evil(state, me)
                or (
                    player.lies_about_self
                    # Can only lie about ping if lying about character. E.g., Mad.
                    and not isinstance(player.character, player.claim)
                )
        ):
            return True

        if player.is_dead and not even_if_dead:
            return False

        if spent := getattr(self, 'spent', None):
            return False
        elif spent is not None:
            self.spent = True

        result = ping(state, me)

        if result.st_lying():
            state.math_misregistration(me)

        if state.vortox and isinstance(self, Townsfolk):
            state.math_misregistration(me)
            return not result.truth()

        if not even_if_droisoned and self.is_droisoned(state, me):
            if not getattr(self, 'self_droison', False):
                state.math_misregistration(me, result)
            return True

        return result.not_false()

    def maybe_activate_effects(
        self,
        state: State,
        me: PlayerID,
        reason: Reason | None = None,
    ) -> None:
        """
        Effects that this character is having on other players. Needs to be
        triggerable under one method so that e.g. a Poisoner dying at night can
        reactivate that Poisoner's current victim.
        If a character doesn't want this wrapper logic, it can override this
        method rather than the _impl method.
        """
        player = state.players[me]
        if (
            not self.effects_active
            and not self.is_droisoned(state, me)
            and (not player.is_dead or player.vigormortised)
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
        if reason is Reason.DEATH and state.players[me].vigormortised:
            return
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
        for substate in state.pre_death_in_town(me):
            player = substate.players[me]
            player.is_dead = True
            player.character.maybe_deactivate_effects(substate, me, Reason.DEATH)
            yield from substate.post_death_in_town(me)

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
            if state.puzzle.allow_killing_dead_players:
                yield state
        elif self.safe_from_attacker(state, me, src):
            state.math_misregistration(src)
            yield state
        else:
            self.death_explanation = f'killed by {state.players[src].name}'
            yield from self.apply_death(state, me, src)

    def executed(self, state: State, me: PlayerID, died: bool) -> StateGen:
        """Goblin, Psychopath, Saint etc override this method."""
        if state.players[me].is_dead:  # and not died: ?
            yield state
        if died:
            self.death_explanation = 'executed'
            yield from self.killed(state, me, src=None)
        elif self.cant_die(state, me):
            yield state

    def killed(
        self,
        state: State,
        me: PlayerID,
        src: PlayerID | None,
    ) -> StateGen:
        """Check the death is logically valid, then apply it."""
        if not self.cant_die(state, me) and not state.players[me].is_dead:
            yield from self.apply_death(state, me, src)

    def safe_from_attacker(
        self,
        state: State,
        me: PlayerID,
        attacker: PlayerID
    ) -> bool:
        """
        Queried when player is attacked. Exists separately from the
        `attacked_at_night` method because things like FangGu need to be able to
        check "would they die" without effecting the death.
        """
        return (
            self.cant_die(state, me)
            or (
                isinstance(state.players[attacker].character, Demon)
                and (
                    getattr(state.players[me], 'safe_from_demon_count', 0)
                    or getattr(state, 'active_princesses', 0)
                )
            )
        )

    def cant_die(self, state: State, me: PlayerID) -> bool:
        """
        TODO: Innkeeper should be checked here. Sailor or Lleech should extend
        this method. Things like Soldier and Monk live in `safe_from_attacker`.
        """
        return hasattr(state, 'pithag_preventing_kills')

    def is_droisoned(self, state: State, me: PlayerID) -> bool:
        """
        Droisoning is an attribute stored on a Player, but Characters should
        not access it directly when deciding if their ability works. Instead,
        they should use this method to handle cases of indirection where the
        ability is given to the current player by another player (i.e. Boffin).
        """
        # TODO: If the boffin-granted ability wraps another ability, that sub-
        # ability will not have the `ability_src` attribute.
        pid = me if (src := getattr(self, 'ability_src', None)) is None else src
        return state.players[pid].droison_count > 0

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
        if info.behaves_evil(state, me):
            return True
        # It is the responsibility of the ExternalInfo to account for Vortox.
        return external_info(state, me)

    def get_ability(
        self,
        character_t: type[Character],
    ) -> Character | None:
        """
        Recursive ability finder handling characters that wrap other characters,
        so that you can query the
        Psychopath[holding LilMonsta[with Boffin[Philo[Alchemist[Witch]]]
        and extract the Witch character instance.
        """
        if isinstance(self, character_t):
            return self

        if (
            isinstance(self, Philosopher)
            and self.active_ability is not None
            and (ret := self.active_ability.get_ability(character_t)) is not None
        ):
            return ret
        if isinstance(self, Hermit):
            for subability in self.active_abilities:
                if (ret := subability.get_ability(character_t)) is not None:
                    return ret

        # TODO: Alchemist
        return None

    def acts_like(self, character: type[Character]) -> bool:
        """
        Checks if this character is treated like the query character by the ST.
        Like 'has_ability', but also returns True on characters that think they
        have the queried ability.
        """
        if self.get_ability(character) is not None:
            return True
        if (sim := getattr(self, 'drunklike_character', None)) is not None:
            return sim.acts_like(character)
        return False

    def wakes_tonight(self, state: State, me: PlayerID) -> bool:
        """
        Evaluated at the point the character is about to be woken according to
        night-order. Most wake patterns can be handle by this default method,
        characters with MANUAL wake patterns should override this method.
        This won't capture abilities that activate out-of-night-order, e.g., SW.
        """
        # Special cases not yet implemented:
        # - Chambermaid doesn't wake if there aren't valid choices
        # - Others, definitely.
        player = state.players[me]
        if (
            player.is_dead or
            (isinstance(self, Demon) and getattr(player, 'exorcised_count', 0))
        ):
            return False

        match self.wake_pattern:
            case WakePattern.NEVER:
                return False
            case WakePattern.FIRST_NIGHT:
                return state.night == self.first_night
            case WakePattern.EACH_NIGHT:
                return True
            case WakePattern.EACH_NIGHT_STAR:
                return state.night != self.first_night
            case WakePattern.EACH_NIGHT_UNTIL_SPENT:
                return not self.spent
        raise ValueError(f'{type(self).__name__} has {self.wake_pattern=}')

    @classmethod
    def draws_wrong_token(cls) -> bool:
        return (
            issubclass(cls, Drunklike)
            or cls is Hermit and any(
                issubclass(x, Drunklike) for x in cls.outsiders
            )
        )

    @classmethod
    def get_category(cls) -> Category:
        for cat in ALL_CATEGORIES:
            if issubclass(cls, cat):
                return cat
        raise ValueError(f'Character {cls.__name__} has no Category!')

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
class Townsfolk(Character): pass
@dataclass
class Outsider(Character): pass
@dataclass
class Minion(Character): pass
@dataclass
class Demon(Character): pass
@dataclass
class Traveller(Character):pass

class _Category(ABC): pass
_Category.register(Townsfolk)
_Category.register(Outsider)
_Category.register(Minion)
_Category.register(Demon)
_Category.register(Traveller)
Category : TypeAlias = type[_Category]
ALL_CATEGORIES = (Townsfolk, Outsider, Minion, Demon, Traveller)


@dataclass
class Acrobat(Townsfolk):
    """
    Each night*, choose a player:
    if they are or become drunk or poisoned tonight, you die.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    @dataclass
    class Choice(info.NotInfo):
        player: PlayerID
    
        def display(self, names: list[str]) -> str:
            return f'Chose {names[self.player]}'

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Die on droisoned player choice"""
        if info.behaves_evil(state, me):
            raise NotImplementedError("Evil Acrobat")
        acrobat = state.players[me]
        if (choice := state.get_night_info(Acrobat, me, state.night)) is None:
            yield state
        elif acrobat.is_dead:
            return
        elif self.is_droisoned(state, me):
            yield state
        elif (
            (chosen := state.players[choice.player]).droison_count
            or chosen.has_ability(Drunk)  # See Acrobat Almanac
        ):
            if self.is_droisoned(state, me):
                state.math_misregistration(me)
                yield state
                return
            yield from self.attacked_at_night(state, me, me)
        else:
            yield state


@dataclass
class Alsaahir(Townsfolk):
    """Not yet implemented"""
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER


@dataclass
class Artist(Townsfolk):
    """
    Once per game, during the day, privately ask the Storyteller any yes/no
    question.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    spent: bool = False

    @dataclass
    class Ping(info.Info):
        statement: info.Info
        def __call__(self, state: State, src: PlayerID):
            return self.statement(state, src)
        
        def display(self, names: list[str]) -> str:
            return self.statement.display(names)

@dataclass
class Atheist(Townsfolk):
    """
    The Storyteller can break the game rules, and if executed, good wins,
    even if you are dead. [No evil characters].
    """
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
class Balloonist(Townsfolk):
    """
    Each night, you learn a player of a different character type than last night
    [+0 or +1 Outsider]
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    # Records the last ping's true category.
    prev_category: Category | None = None
    # Records all categories the last ping could have been registering as.
    prev_regs: tuple[Category] | None = None

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        (min_tf, max_tf), (min_out, max_out), mn, dm = bounds
        bounds = (min_tf - 1, max_tf), (min_out, max_out + 1), mn, dm
        return bounds

    @dataclass
    class Ping(info.NotInfo):
        player: PlayerID

        def display(self, names: list[str]) -> str:
            return f'Balloonist saw {names[self.player]}'

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """
        Override Reason: even though we don't need to assert the balloonist
        gets correct info when poisoned, we still need to take the action to
        record that the following day the balloonist may see anything.

        NOTE: this implementation has only 1 day of memory. I think it's ok?
        """
        balloonist = state.players[me]
        ping = state.get_night_info(Balloonist, me, state.night)
        if (
            balloonist.is_dead
            or ping is None
            or info.behaves_evil(state, me)
        ):
            self.prev_category = None
            yield state; return

        ping_player = state.players[ping.player]
        current_category = ping_player.character.get_category()
        possible_regs = set(
            (current_category,) + ping_player.get_misreg_categories(state)
        )
        # Anything the previous ping must have been is disallowed for this ping
        if self.prev_category is not None and len(self.prev_regs) == 1:
            possible_regs.discard(self.prev_regs[0])
        possible_regs = tuple(possible_regs)
        actually_same = current_category is self.prev_category
        prev_category = self.prev_category

        self.prev_category = current_category
        self.prev_regs = possible_regs

        if prev_category is None:
            yield state; return

        if state.vortox:
            # Balloonist MUST get the same category every night in vortox worlds
            if actually_same:
                yield state
            return

        valid_ping = bool(possible_regs)
        if valid_ping:
            if actually_same:
                state.math_misregistration(me)
            yield state; return
        elif self.is_droisoned(state, me):
            state.math_misregistration(me)
            yield state; return

@dataclass
class Baron(Minion):
    """
    There are extra Outsiders in play. [+2 Outsiders]
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        (min_tf, max_tf), (min_out, max_out), mn, dm = bounds
        bounds = (min_tf - 2, max_tf - 2), (min_out + 2, max_out + 2), mn, dm
        return bounds

@dataclass
class Boffin(Minion):
    """
    The Demon (even if drunk or poisoned) has a not-in-play good character's
    ability. You both know which.
    """
    # TODO: Wake pattern is actually whenever the ability changes.
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    target_demon: PlayerID  | None = None
    inactive_ability: Character | None = None

    # TODO: In `death_in_town``, if demon dies boffin should reassign ability

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        if state.current_phase is not core.Phase.SETUP:
            raise NotImplementedError("TODO: Mid-game Boffin creation.")

        demon_ids = [
            player.id for player in state.players
            if info.IsCategory(player.id, Demon)(state, me).not_false()
            # and player.is_alive  # Not relevant during SETUP...
        ]
        abilities = [
            character for character in state.puzzle.script
            if issubclass(character, (Townsfolk, Outsider))
            and info.IsInPlay(character)(state, me).not_true()
        ]
        assert len(abilities) and len(demon_ids)
        for demon_id, ability_t in itertools.product(demon_ids, abilities):
            new_state = state.fork()
            boffin = new_state.players[me].get_ability(Boffin)
            boffin.target_demon = demon_id
            boffin.effects_active = True
            ability = ability_t()
            ability.ability_src = me
            demon = new_state.players[demon_id]
            assert not hasattr(demon, 'boffin_ability'), "Multiple Boffins? :O"
            demon.boffin_ability = ability
            yield from ability.run_setup(new_state, demon_id)

    def _activate_effects_impl(self, state: State, me: PlayerID):
        demon = state.players[self.target_demon]
        assert not hasattr(demon, 'boffin_ability'), "Multiple Boffins? :O"
        demon.boffin_ability = self.inactive_ability
        self.inactive_ability = None
        demon.boffin_ability.maybe_activate_effects(state, self.target_demon)

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        """Remove the ability, store on the Boffin until reactivation."""
        demon = state.players[self.target_demon]
        demon.boffin_ability.maybe_deactivate_effects(state, self.target_demon)
        self.inactive_ability = demon.boffin_ability
        del demon.boffin_ability

    def _world_str(self, state: State) -> str:
        demon = state.players[self.target_demon]
        ability = type(
            demon.boffin_ability if self.inactive_ability is None
            else self.inactive_ability
        )
        return f'Boffin ({demon.name} += {ability.__name__})'

@dataclass
class Butler(Outsider):
    """
    Each night, choose a player (not yourself):
    tomorrow, you may only vote if they are voting too.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    # Will need to implement the Butler's choices if the Goon is added.

@dataclass
class Cerenovus(Minion):
    """
    Each night, choose a player & a good character:
    they are "mad" they are this character tomorrow, or might be executed.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    target: PlayerID = None
    target_history: list[PlayerID] = field(default_factory=list)

    @dataclass
    class Mad(info.ExternalInfo):
        # Other players use this to claim they were ceremad one night
        character: type[Character] | None = None
        def __call__(self, state: State, src: PlayerID) -> bool:
            return (
                getattr(state.players[src], 'ceremad', 0)
                and any(
                    (ability := player.get_ability(Cerenovus)) is not None
                    and ability.target == src
                    for player in state.players
                )
            )
            
        def display(self, names: list[str]) -> str:
            if self.character is not None:
                return f'Made Mad as {self.character.__name__}'
            return 'Made Mad'

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        cerenovus = state.players[me]
        if cerenovus.is_dead and not cerenovus.vigormortised:
            yield state; return
        if self.is_droisoned(state, me):
            state.math_misregistration(me)
            self.target = None
            yield state; return

        # As an optimisation we can target just the following:
        # - good players who are retro-actively claiming ceremadness tonight
        # - speculatively ceremad players
        # - players executed by ST tomorrow (which might be a madness break)
        # - plus one choice of player who would never admit it
        evil_behaving_players = set(
            pid for pid in state.player_ids if info.behaves_evil(state, pid)
        )
        good_behaving_players_claiming_mad = (
            Cerenovus._players_claiming_ceremad_tonight(state)
            - evil_behaving_players
        )
        speculatively_mad_players = set(
            player.id for player in state.players
            if getattr(player, 'speculative_ceremad', 0)
        )
        players_executed_by_ST_tomorrow = set(
            ev.player for ev in state.puzzle.day_events.get(state.night + 1, [])
        )
        targets = (
            good_behaving_players_claiming_mad
            .union(speculatively_mad_players)
            .union(players_executed_by_ST_tomorrow)
        )
        if evil_behaving_players:
            targets.add(evil_behaving_players.pop())

        for target in targets:
            new_state = state.fork()
            new_cerenovus = new_state.players[me].get_ability(Cerenovus)
            new_cerenovus.target = target
            new_cerenovus.target_history.append(target)
            new_cerenovus.maybe_activate_effects(new_state, me)
            yield new_state

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        self.maybe_deactivate_effects(state, me)
        self.target = None
        yield state

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.target is not None:
            player = state.players[self.target]
            player.ceremad = getattr(player, 'ceremad', 0) + 1

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.target is not None:
            player = state.players[self.target]
            player.ceremad -= 1
            if not player.ceremad:
                del player.ceremad

    @staticmethod
    def _players_claiming_ceremad_tonight(state: State) -> set[PlayerID]:
        ext_info = state.puzzle.external_info_registry.get(
            (Cerenovus, state.night), []
        )
        return set(pid for _, pid in ext_info)

    @staticmethod
    def global_end_night(state: State) -> bool:
        """Check truthful mad players report their madness on subsequent nights"""
        if state.night == state.puzzle.max_night:
            return True
        claiming_madness = Cerenovus._players_claiming_ceremad_tonight(state)
        return not any(
            getattr(player, 'ceremad', 0)
            and player.id not in claiming_madness
            and not getattr(player, 'speculative_ceremad', False)  # Still mad in round robin
            and not info.behaves_evil(state, player.id)
            for player in state.players
        )

    def _world_str(self, state: State) -> str:
        return (
            f'{type(self).__name__} (Chose '
            f'{", ".join(state.players[p].name for p in self.target_history)})'
        )

@dataclass
class Chambermaid(Townsfolk):
    """
    Each night, choose 2 alive players (not yourself):
    you learn how many woke tonight due to their ability.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            valid_choices = (
                self.player1 != src and self.player2 != src
                and info.IsAlive(self.player1)(state, src).not_false()
                and info.IsAlive(self.player2)(state, src).not_false()
            )
            wake_count = sum(
                player.woke_tonight
                or (
                    # Handle Chambermaid-Mathematician Jinx,
                    # or multiple players having Chambermaid ability.
                    state.player_upcoming_in_night_order(player.id)
                    and player.character.wakes_tonight(state, player.id)
                )
                for player in (
                    state.players[self.player1],
                    state.players[self.player2],
                )
            )
            return info.STBool(valid_choices and wake_count == self.count)

        def display(self, names: list[str]) -> str:
            return (
                f'{self.count} of {names[self.player1]} and '
                f'{names[self.player2]} woke'
            )

@dataclass
class Chef(Townsfolk):
    """
    You start knowing how many pairs of evil players there are.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            N = len(state.players)
            evils = [info.IsEvil(i % N)(state, src) for i in range(N + 1)]
            evil_pairs = [a & b for a, b in zip(evils[:-1], evils[1:])]
            return info.ExactlyN(self.count, evil_pairs)(state, src)

        def display(self, names: list[str]) -> str:
            return f'{self.count} evil pairs'

@dataclass
class Clockmaker(Townsfolk):
    """
    You start knowing how many steps from the Demon to its nearest Minion.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        steps: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            """
            This implementation checks against the min distance over all
            minion-demon pairs, giving MAYBEs as appropriate. The phrase
            "The Demon" must give living demons priority over dead demons, so if
            there are any living demons, all dead demons are ignored.
            """
            players = state.players
            N = len(players)
            minions, demons = (
                list(filter(
                    lambda x: x[1].not_false(),
                    [(i, info.IsCategory(i, cat)(state, src)) for i in range(N)]
                ))
                for cat in (Minion, Demon)
            )
            ignore_dead_demons = any(
                info.IsAlive(pid)(state, src).is_true()
                for pid, _ in demons
            )
            # TODO: This is not correct because ignore_dead_demons should depend
            # on whether a misregistration has happened. E.g., consider the case
            # where there is a living Recluse and dead-looking Zombuul.

            correct_distance, too_close = info.STBool.FALSE, info.STBool.FALSE
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

        def display(self, names: list[str]) -> str:
            return f'Clockmaker {self.steps}'

@dataclass
class Courtier(Townsfolk):
    """
    Once per game, at night, choose a character:
    they are drunk for 3 nights & 3 days.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_UNTIL_SPENT

    target: PlayerID | None = None
    choice_night: int | None = None
    spent: bool = False

    @dataclass
    class Choice(info.NotInfo):
        character: type[Character]
        
        def display(self, names: list[str]) -> str:
            return f'Drank with {self.character.__name__}'

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        if info.behaves_evil(state, me):
            # Yield all choices like a poisoner, plus the non-choice
            raise NotImplementedError("Todo: Evil Courtier")

        courtier = state.players[me]

        choice = state.get_night_info(Courtier, me, state.night)
        if choice is None:
            yield state; return
        if courtier.is_dead or self.spent:
            return  # Drinking when spent or dead is a lie
        self.choice_night = state.night
        self.spent = True

        valid_targets = [
            target for target in state.player_ids
            if info.IsCharacter(target, choice.character)(state, me).not_false()
        ]
        if self.is_droisoned(state, me):
            if valid_targets:
                state.math_misregistration(me)
            yield state; return  # Shame!

        for target in valid_targets:
            self.target = target
            new_state = state.fork()
            new_courtier = new_state.players[me].get_ability(Courtier)
            new_courtier.maybe_activate_effects(new_state, me)
            yield new_state

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        if self.target is not None and (state.day - self.choice_night) >= 2:
            self.maybe_deactivate_effects(state, me)
            self.target = None
        yield state

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
class Dreamer(Townsfolk):
    """
    Each night, choose a player (not yourself or Travellers):
    you learn 1 good & 1 evil character, 1 of which is correct.
    """
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
        
        def display(self, names: list[str]) -> str:
            return (
                f'{names[self.player]} is '
                f'{self.character1.__name__} or {self.character2.__name__}'
            )

@dataclass
class Drunklike(Character):
    """
    A base class for characters that think they have the behaviour of another
    character but don't (Drunk, Marionette, Lunatic). Upon any action, forks the
    current world state and simulates the character's assumed behaviour in a
    fake world, thus computing correct wake patterns/picks without mutating the
    real world state or requiring other character implementations to implement
    Drunk-specific behaviour.
    """
    lies_about_self: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    drunklike_character: Character | None = None

    def wakes_tonight(self, state: State, me: PlayerID) -> bool:
        return self.drunklike_character.wakes_tonight(state, me)

    def _create_simulation(
        self,
        state: State,
        me: PlayerID,
    ) -> tuple[State, Character]:
        """Create a parallel world where the Drunklike really has the ability"""
        sim_state = state.fork()
        sim_player = sim_state.players[me]
        sim_player.character = sim_player.character.drunklike_character
        return sim_state, sim_player.character

    def _extract_from_simulation(
        self,
        state: State,
        simulation: State,
        me: PlayerID
    ):
        """Copy useful info from simulation back to real state."""
        real_player = state.players[me]
        sim_player = simulation.players[me]
        if hasattr(sim_player.character, 'spent'):
            self.spent = sim_player.character.spent
        real_player.woke_tonight |= sim_player.woke_tonight
        self.drunklike_character = sim_player.character

    def _worth_simulating(self, state: State):
        """
        The simulations require expensive deepcopys, and are only relevant for
        a few character interactions. So it's worth filtering out some basic
        cases where the output is obviously irrelevant.
        """
        return self.drunklike_character.wake_pattern in (
            WakePattern.MANUAL,
            WakePattern.EACH_NIGHT_UNTIL_SPENT,
        )

    def _run_simulation(self, state: State, me: PlayerID) -> StateGen:
        """Run fake ability in simulated world, extract real-world effects."""
        if not self._worth_simulating(state):
            self.spent = False
            yield state
            return

        sim_state, sim_character = self._create_simulation(state, me)
        match state.current_phase:
            case core.Phase.SETUP:
                simulation = sim_character.run_setup(sim_state, me)
            case core.Phase.NIGHT:
                simulation = sim_character.run_night(sim_state, me)

        no_substates = True
        for sim_substate in simulation:
            substate = state if sim_substate is sim_state else state.fork()
            self._extract_from_simulation(substate, sim_substate, me)
            yield substate
            no_substates = False
        if no_substates:
            self._extract_from_simulation(state, sim_state, me)
            yield state

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        yield from self._run_simulation(state, me)

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        yield from self._run_simulation(state, me)

@dataclass
class Drunk(Drunklike, Outsider):
    """
    You do not know you are the Drunk.
    You think you are a Townsfolk character, but you are not.
    """
    self_droison: bool = True

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        drunk = state.players[me]
        if not issubclass(drunk.claim, Townsfolk):
            # Drunk can only 'lie' about being Townsfolk
            return
        self.drunklike_character = drunk.claim()
        yield from super().run_setup(state, me)

@dataclass
class Empath(Townsfolk):
    """
    Each night, you learn how many of your 2 alive neighbors are evil.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            left, right = (info.get_next_player_who_is(
                state,
                lambda s, p: info.IsAlive(p)(s, src).is_true(),
                src,
                clockwise,
            ) for clockwise in (True, False))
            evil_neighbours = [info.IsEvil(left)]
            if left != right:
                evil_neighbours.append(info.IsEvil(right))
            return info.ExactlyN(N=self.count, args=evil_neighbours)(state, src)

        def display(self, names: list[str]) -> str:
            return f'{self.count} evil neighbours'

@dataclass
class Exorcist(Townsfolk):
    """
    Each night*, choose a player (different to last night):
    the Demon, if chosen, learns who you are then doesn't wake tonight.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    target: PlayerID | None = None

    @dataclass
    class Choice(info.NotInfo):
        player: PlayerID
    
        def display(self, names: list[str]) -> str:
            return f'Exorcised {names[self.player]}'

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        if info.behaves_evil(state, me):
            raise NotImplementedError('Evil Exorcist!')

        exorcist = state.players[me]
        if exorcist.is_dead:
            yield state; return

        choice = state.get_night_info(Exorcist, me, state.night)
        if choice is None:
            yield state; return

        self.maybe_deactivate_effects(state, me)
        self.target = choice.player
        target_character = state.players[choice.player].character
        # Check if would_wake before activating exorcist effects
        would_wake = target_character.wakes_tonight(state, choice.player)
        self.maybe_activate_effects(state, me)

        is_demon = info.IsCategory(choice.player, Demon)(state, me)
        if is_demon.is_false():
            yield state; return
        if is_demon.is_maybe():
            yield state.fork()

        if self.is_droisoned(state, me):
            # Demon should be told they were picked, so any time the exorcist
            # chooses a demon while poisoned, this fails and Math triggers.
            state.math_misregistration(me)
        elif would_wake:
            state.math_misregistration(choice.player)
        yield state

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.target is not None:
            target = state.players[self.target]
            target.exorcised_count = getattr(target, 'exorcised_count', 0) + 1

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.target is not None:
            target = state.players[self.target]
            target.exorcised_count -= 1
            if target.exorcised_count == 0:
                del target.exorcised_count

@dataclass
class EvilTwin(Minion):
    """
    You & an opposing player know each other.
    If the good player is executed, evil wins. Good can't win if you both live.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    twin: PlayerID | None = None

    @dataclass
    class Is(info.ExternalInfo):
        """The 'good' twin reports an EvilTwin using EvilTwin.Is(player)."""
        eviltwin: PlayerID
        def __call__(self, state: State, src: PlayerID) -> bool:
            eviltwin = state.players[self.eviltwin].get_ability(EvilTwin)
            return eviltwin is not None and eviltwin.twin == src
        
        def display(self, names: list[str]) -> str:
            return f'{names[self.eviltwin]} is the EvilTwin'

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        eviltwin = state.players[me].get_ability(EvilTwin)
        if eviltwin.is_droisoned(state, me):
            raise NotImplementedError('Poisoned EvilTwin')

        night_idx = (
            state.night if state.current_phase is core.Phase.NIGHT
            else state.day + 1 if state.current_phase is core.Phase.DAY
            else 1
        )
        i_am_evil = info.IsEvil(me)(state, me)
        all_good_twin_claims = state.puzzle.external_info_registry.get(
            (EvilTwin, night_idx), []
        )
        for player_id in state.player_ids:
            # Only players of opposing alignment can be twins
            if (info.IsEvil(player_id)(state, me) == i_am_evil).is_true():
                continue
            claims_good_twin = any(
                (_pid == player_id and claim.eviltwin == me)
                for claim, _pid in all_good_twin_claims
            )
            if not (claims_good_twin or info.behaves_evil(state, player_id)):
                continue
            # This is a valid choice of twin
            new_state = state.fork()
            new_state.players[me].get_ability(EvilTwin).twin = player_id
            yield new_state

    def pre_death_in_town(
        self,
        state: State,
        death: PlayerID,
        me: PlayerID
    ) -> StateGen:
        eviltwin = state.players[me]
        if (
            (eviltwin.is_dead and not eviltwin.vigormortised)
            or (death != self.twin and death != me)  # `me` could be good
            or info.IsEvil(death)(state, me).not_false()
        ):
            yield state
        elif self.is_droisoned(state, me):
            state.math_misregistration(me)
            yield state

@dataclass
class GenericDemon(Demon):
    """
    Many demons just kill once each night*, so implment that once here.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Create a world for every kill choice."""
        demon = state.players[me]
        if (
            state.night == 1
            or demon.is_dead
            or getattr(demon, 'exorcised_count', 0)
        ):
            yield state; return

        sunk_a_kill = False
        for target in state.player_ids:
            dead_target = state.players[target].is_dead
            if dead_target:
                if sunk_a_kill:
                    continue  # Dedupe kill sinking forks
                sunk_a_kill = True
            new_state = state.fork()
            if self.is_droisoned(state, me):
                if not dead_target:
                    new_state.math_misregistration(me)
                yield new_state
                continue
            target_char = new_state.players[target].character
            yield from target_char.attacked_at_night(new_state, target, me)

@dataclass
class FangGu(GenericDemon):
    """
    Each night*, choose a player: they die. The 1st Outsider this kills becomes
    an evil Fang Gu & you die instead. [+1 Outsider]
    """

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        (min_tf, max_tf), (min_out, max_out), mn, dm = bounds
        bounds = (min_tf - 1, max_tf - 1), (min_out + 1, max_out + 1), mn, dm
        return bounds

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        fanggu = state.players[me]
        if (
            state.night == 1
            or fanggu.is_dead
            or getattr(fanggu, 'exorcised_count', 0)
        ):
            yield state; return

        sunk_a_kill = False
        for target in state.player_ids:
            target_player = state.players[target]

            # 1. The kill sink world
            if target_player.is_dead:
                if sunk_a_kill:
                    continue  # Dedupe identical kill sink worlds
                yield state.fork()
                sunk_a_kill = True
                continue

            # 2. The droison world
            if self.is_droisoned(state, me):
                droison_state = state.fork()
                droison_state.math_misregistration(me)
                yield droison_state
                continue

            is_outsider = info.IsCategory(target, Outsider)(state, me)

            already_jumped = getattr(state, 'fanggu_already_jumped', False)
            wouldnt_jump = already_jumped or (is_outsider.not_true())
            fails_jump = (
                fanggu.character.safe_from_attacker(state, me, me)  # Wouldn't catch Boffin Soldier...
                or target_player.character.safe_from_attacker(state, target, me)
            )
            # 3. The normal kill world. This includes the case where they can't
            # jump due to other player's abilities.
            if wouldnt_jump or fails_jump:
                kill_state = state.fork()
                if (
                    (fails_jump and not wouldnt_jump)
                    or (
                        is_outsider.is_maybe()
                        and isinstance(target_player.character, Outsider)
                    )
                ):
                    kill_state.math_misregistration(me)
                kill_target = kill_state.players[target].character
                kill_state.log(f'FangGu attacks {state.players[target].name}')
                yield from kill_target.attacked_at_night(kill_state, target, me)
                # Let MAYBE through to also create a jump world
                if already_jumped or fails_jump or is_outsider.is_false():
                    continue

            # 4. The world where the Fang Gu jumps.
            jump_state = state.fork()
            jump_state.fanggu_already_jumped = True
            if (
                is_outsider.is_maybe()
                and not isinstance(target_player.character, Outsider)
            ):
                jump_state.math_misregistration(me)
            for ss in jump_state.change_character(target, FangGu):
                for jump_substate in ss.change_alignment(target, is_evil=True):
                    new_me = jump_substate.players[me].get_ability(FangGu)
                    new_me.death_explanation = f'Jumped N{jump_substate.night}'
                    yield from new_me.apply_death(jump_substate, me, src=me)

@dataclass
class Flowergirl(Townsfolk):
    """
    Each night*, you learn if a Demon voted today.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    demon_voted_on_day: tuple[STBool, int] = (None, None)

    @dataclass
    class Voters(events.Event):
        voters: list[PlayerID]
        player: PlayerID | None = None
        def __call__(self, state: State) -> StateGen:
            # Evaluate Demon-ness as an Event at the time of the votes, since it
            # might change before the Flowergirl received their Ping
            demon_voted = info.STBool.FALSE
            for voter in self.voters:
                demon_voted |= info.IsCategory(voter, Demon)(state, self.player)
            flowergirl = state.players[self.player]
            flowergirl.demon_voted_on_day = (demon_voted, state.day)
            yield state
        
        def display(self, names: list[str]) -> str:
            return f"Voters: {', '.join([names[v] for v in self.voters])}"

    @dataclass
    class Ping(info.Info):
        demon_voted: bool
        def __call__(self, state: State, me: PlayerID) -> STBool:
            flowergirl = state.players[me]
            demon_voted, day = flowergirl.demon_voted_on_day
            assert day == state.night - 1, (
                "Flowergirl Ping without recording votes the previous day."
            )
            return info.STBool(self.demon_voted) == demon_voted

        def display(self, names: list[str]) -> str:
            return 'Demon voted' if self.demon_voted else 'Demon did not vote'

@dataclass
class FortuneTeller(Townsfolk):
    """
    Each night, choose 2 players: you learn if either is a Demon.
    There is a good player that registers as a Demon to you.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    red_herring: PlayerID | None = None

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID
        demon: bool
        def __call__(self, state: State, me: PlayerID) -> STBool:
            fortuneteller = state.players[me].get_ability(FortuneTeller)
            real_result = (
                info.IsCategory(self.player1, Demon)(state, me)
                | info.IsCategory(self.player2, Demon)(state, me)
            )
            if fortuneteller.red_herring in (self.player1, self.player2):
                real_result |= info.STBool.TRUE_LYING
                if real_result is info.STBool.TRUE_LYING:
                    state.exclude_player_from_math_tonight(me)
            claimed_result = info.STBool(self.demon)
            return real_result == claimed_result
            
        def display(self, names: list[str]) -> str:
            return (
                f'{names[self.player1]} | {names[self.player2]}'
                f' -> {"yes" if self.demon else "no"}'  
             )

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        # Simulate all worlds where the red herring is chosen, plus just one
        # where is some random other person
        redherrings = set()
        good_team = set(
            pid for pid in state.player_ids
            if info.IsEvil(pid)(state, me).not_true()
        )
        for night in range(1, state.puzzle.max_night + 1):
            if (ping := state.get_night_info(FortuneTeller, me, night)) is None:
                continue
            if ping.player1 in good_team:
                redherrings.add(ping.player1)
            if ping.player2 in good_team:
                redherrings.add(ping.player2)
        unchosen_good = good_team - redherrings
        if unchosen_good:
            redherrings.add(unchosen_good.pop())
        for player in redherrings:
            new_state = state.fork()
            new_ft = new_state.players[me].get_ability(FortuneTeller)
            new_ft.red_herring = player
            yield new_state

    def _world_str(self, state: State) -> str:
        return (
            'FortuneTeller (Red Herring = '
            f'{state.players[self.red_herring].name})'
        )

@dataclass
class Gambler(Townsfolk):
    """
    Each night*, choose a player & guess their character:
    if you guess wrong, you die.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    @dataclass
    class Gamble(info.NotInfo):
        player: PlayerID
        character: type[Character]
            
        def display(self, names: list[str]) -> str:
            return f'Gambled {names[self.player]} as {self.character.__name__}'

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Die on error, fork on MAYBE, ignore vortox."""
        if info.behaves_evil(state, me):
            raise NotImplementedError("Evil Gambler")

        gambler = state.players[me]

        ping = state.get_night_info(Gambler, me, state.night)
        if gambler.is_dead or ping is None:
            yield state
            return

        result = info.IsCharacter(ping.player, ping.character)(state, me)
        if result.is_true():
            yield state
        elif result.is_false():
            # Gambler attacks themselves with their own ability
            if self.is_droisoned(state, me):
                state.math_misregistration(me)
                yield state; return
            yield from self.attacked_at_night(state, me, me)
        elif result.is_maybe():
            # Yield a world for both live and die case
            yield state.fork()
            die_state = state.fork()
            if self.is_droisoned(state, me):
                die_state.math_misregistration(me)
                yield die_state; return
            else:
                yield from self.attacked_at_night(die_state, me, me)

@dataclass
class Goblin(Minion):
    """TODO: Ability not yet implemented"""
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

@dataclass
class Golem(Outsider):
    """
    You may only nominate once per game.
    When you do, if the nominee is not the Demon, they die.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    spent: bool = False

    # Golem abilities are checked by this method if there is an
    # "UneventfulNomination" or "Dies" event in the day events.
    def nominates(self, state: State, nomination: Event) -> StateGen:

        if isinstance(nomination, events.UneventfulNomination):
            golem = state.players[nomination.nominator]
        elif isinstance(nomination, events.Dies):
            golem = state.players[nomination.after_nominated_by]
        else:
            raise ValueError(f'Unknown event type {type(nomination)=}')

        if self.spent and not self.is_droisoned(state, golem.id):
            raise ValueError("Golem nominated twice. Likely a puzzle typo?")
        self.spent = True
        nominee = state.players[nomination.player]
        is_demon = info.IsCategory(nominee.id, Demon)(state, golem.id)

        if isinstance(nomination, events.UneventfulNomination):
            if is_demon.is_false() and self.is_droisoned(state, golem.id):
                state.math_misregistration(golem.id)
                yield state
            elif is_demon.is_maybe():
                if isinstance(nominee.character, Demon):
                    state.math_misregistration(golem.id)
                yield state
            elif is_demon.is_true():
                yield state
            return

        # isinstance(nomination, events.Dies)
        if not self.is_droisoned(state, golem.id) and is_demon.not_true():
            if isinstance(nominee.character, Demon):
                state.math_misregistration(golem.id)  # ...Boffin-Alchemist-Spy?
            yield from nominee.character.killed(state, nominee.id, golem.id)

    def uneventful_nomination(
        self,
        state: State,
        nomination: events.UneventfulNomination,
        me: PlayerID,
    ) -> StateGen:
        return self.nominates(state, nomination)

@dataclass
class Gossip(Townsfolk):
    """
    Each day, you may make a public statement.
    Tonight, if it was true, a player dies.
    """
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
        
        def display(self, names: list[str]) -> str:
            return (
                f'{names[self.player]} gossiped {self.statement.display(names)}'
            )

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: On True gossip, create a world for every kill."""
        gossip = state.players[me]
        result, gossip_day = getattr(gossip, 'prev_gossip', (None, None))
        if (
            gossip.is_dead
            or result is None
            or result.is_false()
            or gossip_day != state.night - 1
        ):
            yield state; return

        dud_kill_done = False
        if result.is_maybe():
            yield state.fork()
            dud_kill_done = True

        if self.is_droisoned(state, me):
            state.math_misregistration(me)
            yield state; return

        for target in state.player_ids:
            if state.players[target].is_dead:
                # Dedupe worlds where nobody dies. I think this is OK...
                if dud_kill_done:
                    continue
                dud_kill_done = True
            new_state = state.fork()
            target_char = new_state.players[target].character
            yield from target_char.attacked_at_night(new_state, target, me)

@dataclass
class Hermit(Outsider):
    """
    You have all Outsider abilities. [-0 or -1 Outsider]
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    outsiders: ClassVar[list[type[Character]]] | None = None
    active_abilities: list[Character] | None = None

    @classmethod
    def set_outsiders(cls, *outsiders: Sequence[type[Character]]) -> None:
        """
        Each puzzle should use call this method to globally set what abilities
        the Hermit has. This is necessary to allow the core puzzle engine to
        treat all character classes equally, with zero-argument constructors. I
        really wanted this method to be a class factory that built a
        puzzle-specific class, but this didn't play nicely with multiprocessing
        since the user-built classes weren't serialisable by pickle.

        We do not support outsider compbinations where more than one overrides
        the same method and that method mutates common player state like is_dead
        If this becomes a problem, we could modify apply_death etc to have a
        'soft_death' flag, that doesn't truly kill.
        """
        assert len(outsiders) > 0
        override_registry = {}
        misreg_categories = set()
        for i, outsider in enumerate(outsiders):
            misreg_categories.update(outsider.misregister_categories)
            for fname in ('apply_death', 'attacked_at_night', 'executed', 'killed'):
                if getattr(outsider, fname) is not getattr(Character, fname):
                    if fname in override_registry:
                        raise ValueError(
                            f'Hermit has two conflicting overrides for {fname}'
                        )
                    override_registry[fname] = i
        misreg_categories.discard(Outsider)

        cls.lies_about_self = any(x.lies_about_self for x in outsiders)
        cls.misregister_categories = tuple(misreg_categories)
        cls.override_registry = override_registry
        cls.outsiders = tuple(outsiders)

    def __post_init__(self):
        if self.outsiders is None:
            raise ValueError(
                "You must call `Hermit.set_outsiders(...)` before using the "
                "Hermit in a puzzle."
            )
        self.active_abilities = [x() for x in self.outsiders]

    def _run_all_abilities(
        self,
        state: State,
        me: PlayerID,
        funcname: str,
        *args,
    ) -> StateGen:
        states = [state]
        for ability in range(len(self.active_abilities)):
            states = core.apply_all(states, lambda s, ability=ability: getattr(
                s.players[me].get_ability(Hermit).active_abilities[ability],
                funcname,
            )(s, me))
        yield from states

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        return self._run_all_abilities(state, me, 'run_setup', me)

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        for ability in self.active_abilities:
            # This catches Drunklike acts_like current character, so run sim.
            if ability.acts_like(state.currently_acting_character):
                yield from ability.run_night(state, me)
                break
        else:
            raise ValueError('Hermit tried to run_night but no ability fired?')

    def run_day(self, state: State, me: PlayerID) -> StateGen:
        return self._run_all_abilities(state, me, 'run_day', me)

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        return self._run_all_abilities(state, me, 'end_day', me)

    def end_night(self, state: State, me: PlayerID) -> StateGen:
        return self._run_all_abilities(state, me, 'end_night', me)

    def _activate_effects_impl(self, state: State, me: PlayerID):
        for ability in self.active_abilities:
            ability._activate_effects_impl(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        for ability in self.active_abilities:
            ability._deactivate_effects_impl(state, me)

    # Todo: auto-generate the below overrides in the build_func?
    def apply_death(self, state: State, me: PlayerID, src: PlayerID) -> StateGen:
        method_idx = self.override_registry.get('apply_death', 0)
        method = getattr(self.active_abilities[method_idx], 'apply_death')
        return method(state, me, src)

    def executed(self, state: State, me: PlayerID, died: bool) -> StateGen:
        method_idx = self.override_registry.get('executed', 0)
        method = getattr(self.active_abilities[method_idx], 'executed')
        return method(state, me, died)

    def killed(self, state, *args, **kwargs) -> StateGen:
        method_idx = self.override_registry.get('killed', 0)
        method = getattr(self.active_abilities[method_idx], 'killed')
        return method(state, *args, **kwargs)

    def cant_die(self, state: State, me: PlayerID) -> bool:
        return any(x.cant_die(state, me) for x in self.active_abilities)

    def wakes_tonight(self, state: State, me: PlayerID) -> bool:
        return any(x.wakes_tonight(state, me) for x in self.active_abilities)

    @property
    def drunklike_character(self):
        return_val = None
        for ability in self.active_abilities:
            sim_char = getattr(ability, 'drunklike_character', None)
            if sim_char is not None:
                assert return_val is None
                return_val = sim_char
        return return_val

@dataclass
class Imp(GenericDemon):
    """
    Each night*, choose a player: they die.
    If you kill yourself this way, a Minion becomes the Imp.
    """

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Add star pass to generic demon"""
        imp = state.players[me]
        if (
            state.night == 1
            or imp.is_dead
            or getattr(imp, 'exorcised_count', 0)
        ):
            yield state; return

        # Kill other player
        sunk_a_kill = False
        for target in state.player_ids:
            if target == me:
                continue
            if state.players[target].is_dead:
                if sunk_a_kill:
                    continue  # Dedupe sinking kill choice
                sunk_a_kill = True
            new_state = state.fork()
            if self.is_droisoned(state, me):
                if not new_state.players[target].is_dead:
                    new_state.math_misregistration(me)
                yield new_state
                continue
            target_char = new_state.players[target].character
            yield from target_char.attacked_at_night(new_state, target, me)

        # Star pass
        if (
            self.is_droisoned(state, me)
            or self.cant_die(state, me)
            or getattr(imp, 'safe_from_demon_count', 0)
        ):
            failed_starpass_state = state.fork()
            failed_starpass_state.math_misregistration(me)
            yield failed_starpass_state
            return
        self.death_explanation = f'Starpassed N{state.night}'
        # Decide who catches the star pass. SW must catch if able.

        scarletwomen, other_minions = [], []
        for player in state.players:
            character = player.character
            sw_catch, sw_misreg = ScarletWoman.catches_death(state, imp, player)
            if sw_misreg.not_false():
                raise NotImplementedError('SW inc Math or not inc Math')
            if sw_catch.is_true():
                scarletwomen.append(player.id)
            elif isinstance(character, Minion) and not player.is_dead:
                other_minions.append(player.id)

        catchers = scarletwomen if scarletwomen else other_minions

        for minion in catchers:
            new_state = state.fork()
            # Note this slightly odd choice of if condition captures that the SW
            # only wakes if they caught the star pass _due to their ability_!
            if scarletwomen:
                new_state.players[minion].woke()
            for substate in new_state.change_character(minion, Imp):
                new_me = substate.players[me].character
                yield from new_me.apply_death(substate, me, src=me)

        if not catchers:
            new_state = state.fork()
            new_me = new_state.players[me].character
            yield from new_me.apply_death(new_state, me, src=me)

@dataclass
class Investigator(Townsfolk):
    """
    You start knowing that 1 of 2 players is a particular Minion.
    """
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
            
        def display(self, names: list[str]) -> str:
            return (
                f'{names[self.player1]} or {names[self.player2]}'
                f' is the {self.character.__name__}'
            )

@dataclass
class Juggler(Townsfolk):
    """
    On your 1st day, publicly guess up to 5 players' characters.
    That night, you learn how many you got correct.
    """
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
        
        def display(self, names: list[str]) -> str:
            return f"{names[self.player]} juggled {', '.join([
                f'{names[player]}={character.__name__}'
                for player, character in self.juggle.items()
            ])}"

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, me: PlayerID) -> STBool:
            juggler_player = state.players[me]
            juggler_ability = juggler_player.get_ability(Juggler)
            assert state.night == juggler_ability.first_night + 1, (
                "Juggler.Ping only allowed on Juggler's second night"
            )
            correct_juggles = getattr(juggler_player, 'correct_juggles', None)
            assert correct_juggles is not None, (
                "No Juggler.Juggle happened before the Juggler.Ping"
            )
            juggler_player.woke()
            return info.ExactlyN(N=self.count, args=correct_juggles)(state, me)
            
        def display(self, names: list[str]) -> str:
            return f"Juggled {self.count} correctly"

    def wakes_tonight(self, state: State, me: PlayerID) -> bool:
        juggler = state.players[me]
        return (
            not juggler.is_dead
            and state.night == self.first_night + 1
            and state.get_night_info(Juggler, me, state.night) is not None
        )

@dataclass
class Kazali(GenericDemon):
    """
    Each night*, choose a player: they die.
    [You choose which players are which Minions. -? to +? Outsiders]
    """

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        tf, os, mn, dm = bounds
        return(-99, 99), (-99, 99), mn, dm


@dataclass
class Klutz(Outsider):
    """
    When you learn that you died, publicly choose 1 alive player:
    if they are evil, your team loses.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    @dataclass
    class Choice(events.Event):
        choice: PlayerID
        player: PlayerID | None = None
        def __call__(self, state: State) -> StateGen:
            klutz_player = state.players[self.player]
            klutz_ability = klutz_player.get_ability(Klutz)
            assert klutz_player.is_dead, "Unlikely the puzzle says Klutz alive."
            if klutz_ability is None:
                if info.behaves_evil(state, self.player):
                    yield state
                return
            # Game is not over, so Klutz is claiming chosen player is good.
            is_good = ~info.IsEvil(self.choice)(state, self.player)
            if is_good.is_true():
                yield state
            elif klutz_ability.is_droisoned(state, self.player):
                state.math_misregistration(self.player, is_good)
                yield state
    
    def display(self, names: list[str]) -> str:
        return f"{names[self.player]} Klutz-picks {names[self.choice]}"

@dataclass
class Knight(Townsfolk):
    """
    You start knowing 2 players that are not the Demon.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID

        def __call__(self, state: State, src: PlayerID) -> STBool:
            return ~(
                info.IsCategory(self.player1, Demon)(state, src) |
                info.IsCategory(self.player2, Demon)(state, src)
            )
            
        def display(self, names: list[str]) -> str:
            return (
                f'{names[self.player1]} and {names[self.player2]}'
                f' are not the Demon'
            )

@dataclass
class Leviathan(Demon):
    """
    If more than 1 good player is executed, evil wins.
    All players know you are in play. After day 5, evil wins.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """Game ends if S&H Leviathan reaches Night 6."""
        leviathan = state.players[me]
        if state.night < 6 or leviathan.is_dead:
            yield state
        elif self.is_droisoned(state, me):
            state.math_misregistration(me)
            yield state

@dataclass
class Librarian(Townsfolk):
    """
    You start knowing that 1 of 2 players is a particular Outsider.
    (Or that zero are in play.)
    """
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
                    info.IsCategory(player, Outsider)
                    for player in state.player_ids
                ])(state, src)

            else:
                assert (self.player2 is not None
                    and self.character is not None), usage
                return (
                    info.IsCharacter(self.player1, self.character)(state, src) |
                    info.IsCharacter(self.player2, self.character)(state, src)
                )
            
        def display(self, names: list[str]) -> str:
            return (
                f'{names[self.player1]} or {names[self.player2]}'
                f' is the {self.character.__name__}'
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
        evil = [player.is_evil for player in state.players]  # Misreg can't affect setup
        N = len(state.players)
        if not evil[(me - 1) % N] or not evil[(me + 1) % N]:
            return
        if 'e' * sum(evil) in ''.join('e' if e else 'g' for e in evil) * 2:
            yield state

@dataclass
class Lunatic(Drunklike, Outsider):
    """
    You think you are the Demon, but you are not.
    The demon knows who you are & who you chose at night.
    """

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        """Create world for each choice of claimed demon."""
        for demon in state.puzzle.demons:
            substate = state.fork()
            new_lunatic = substate.players[me].get_ability(Lunatic)
            new_lunatic.drunklike_character = demon()
            yield from Drunklike.run_setup(new_lunatic, substate, me)

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """
        TODO: Poisoned Lunatic doesn't tell the Demon their kill
        choice, so should tick Mathematician number up.
        TODO: Lunatic-Mathematician jinx, if the Lunatic's kill choice is not
        followed by the demon, the Math number increments. Currently there are
        no puzzles where the Lunatic claims Lunatic and reveals their kill
        choices, so this is not modelled.
        """
        if self.is_droisoned(state, me) and state.night == self.first_night:
            # Demon doesn't learn who the droisoned Lunatic is, increment math.
            # Really this should be checked on subsequent nights too, but that
            #  will (usually) be covered OK by the rest of the math logic below.
            state.math_misregistration(me)
        for substate in Drunklike.run_night(self, state, me):
            lunatic = substate.players[me]
            if (
                lunatic.woke_tonight
                and lunatic.get_ability(Lunatic).is_droisoned(substate, me)
            ):
                # MAYBE inc math, because Lunatic could have chosen whoever.
                # This is only approximately correct, most of the time.
                substate.math_misregistration(me, info.STBool.TRUE_MAYBE)
            yield substate

@dataclass
class Marionette(Drunklike, Minion):
    """
    You think you are a good character, but you are not.
    The Demon knows who you are. [You neighbor the Demon]
    """

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        (tf_lo, tf_hi), (out_lo, out_hi), mn, dm = bounds
        return ((tf_lo, tf_hi + 1), (out_lo - 1, out_hi), mn, dm)

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Check neighbouring Demon"""
        if state.current_phase is core.Phase.SETUP:
            N = len(state.players)
            demon_neighbour = (
                info.IsCategory((me - 1) % N, Demon)(state, me)
                | info.IsCategory((me + 1) % N, Demon)(state, me)
            )
            if demon_neighbour.is_false():
                return
            if demon_neighbour.is_maybe():
                state.math_misregistration(me)  # e.g. Recluse-Mario ticks Math

        self.drunklike_character = state.players[me].claim()
        yield from super().run_setup(state, me)

@dataclass
class Mathematician(Townsfolk):
    """
    Each night, you learn how many players' abilities worked abnormally
    (since dawn) due to another character's ability.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            lo, hi = state._math_misregistration_bounds
            return info.STBool(lo <= self.count <= hi)
            
        def display(self, names: list[str]) -> str:
            return f"Math {self.count}"

@dataclass
class Mayor(Townsfolk):
    """
    If only 3 player live & no execution occurs, your team wins.
    If you die at night, another player might die instead.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

@dataclass
class Monk(Townsfolk):
    """
    Each night*, choose a player (not yourself):
    they are safe from the Demon tonight.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    target: PlayerID = None
    target_history: list[PlayerID] = field(default_factory=list)

    @dataclass
    class Choice(info.NotInfo):
        player: PlayerID
    
        def display(self, names: list[str]) -> str:
            return f'Protected {names[self.player]}'

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        if info.behaves_evil(state, me):
            raise NotImplementedError("Todo: Evil Monk")

        monk = state.players[me]
        choice = state.get_night_info(Monk, me, state.night)
        if choice is None:
            yield state; return
        if monk.is_dead:
            return

        self.maybe_deactivate_effects(state, me)
        self.target = choice.player
        self.target_history.append(choice.player)
        self.maybe_activate_effects(state, me)
        yield state

    def end_night(self, state: State, me: PlayerID) -> StateGen:
        self.maybe_deactivate_effects(state, me)
        self.target = None
        yield state

    def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
        if self.target is not None:
            p = state.players[self.target]
            p.safe_from_demon_count = getattr(p, 'safe_from_demon_count', 0) + 1

    def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
        if self.target is not None:
            p = state.players[self.target]
            p.safe_from_demon_count -= 1
            if not p.safe_from_demon_count:
                del p.safe_from_demon_count

    def _world_str(self, state: State) -> str:
        return (
            f'{type(self).__name__} (Protected '
            f'{", ".join(state.players[p].name for p in self.target_history)})'
        )

@dataclass
class Mutant(Outsider):
    """
    If you are "mad" about being an Outsider, you might be executed.
    """
    lies_about_self: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    def run_day(self, state: State, me: PlayerID) -> StateGen:
        # This impl considers all information to be delivered on the final day,
        # therefore it is only a problem for the Mutant to retroactively claim
        # Outsider if it is still a sober and healthy Mutant on the final day.

        player = state.players[me]
        if player.is_dead or state.day != state.puzzle.max_day:
            yield state
        elif not issubclass(player.claim, Outsider):
            yield state
        elif self.is_droisoned(state, me):
            state.math_misregistration(me, info.STBool.FALSE_MAYBE)  # Maybe ST is just nice?
            yield state

        # TODO: Currently we can only tick up Math on a poisoned mutant on final
        # day, because we can't record what they were claiming in the past, only
        # what they're claiming retroactively at endgame. Once we have a way of
        # placing speculative_liars, fork a lying good version of the Mutant
        # who must still be alive at the end (rather than must be dead or
        # changed) so then a non-lying Mutant claiming Outsider in the past can
        # MAYBE uptick math when poisoned midgame.

    def apply_death(
        self,
        state: State,
        me: PlayerID,
        src: PlayerID | None = None,
    ) -> StateGen:
        for substate in super().apply_death(state, me, src):
            # Good dead Mutants claim Mutant
            mutant = substate.players[me]
            if mutant.claim is Mutant or info.behaves_evil(substate, me):
                yield substate

@dataclass
class NightWatchman(Townsfolk):
    """
    Once per game, at night, choose a player:
    they learn you are the Nightwatchman.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_UNTIL_SPENT

    spent: bool = False

    @dataclass
    class Choice(info.NotInfo):
        """The Choice as reported by the NightWatchman."""
        player: PlayerID
            
        def display(self, names: list[str]) -> str:
            return f"Chose {names[self.player]}"

    @dataclass
    class Ping(info.ExternalInfo):
        """The wakeup received by the target of a NightWatchman.Choice."""
        player: PlayerID
        def __call__(self, state: State, src: PlayerID) -> bool:
            nwm = state.players[self.player]
            choice = state.get_night_info(NightWatchman, nwm.id, state.night)
            nwm_truthful = not info.behaves_evil(state, nwm.id)
            ability = nwm.get_ability(NightWatchman)
            return not (
                ability is None
                or ability.is_droisoned(state, nwm.id)
                or (choice is None and nwm_truthful)
            )
            
        def display(self, names: list[str]) -> str:
            return f"{names[self.player]} is the NightWatchman"

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        nightwatchman = state.players[me]
        if state.vortox:
            raise NotImplementedError('TODO: Vortox + NightWatchman')

        if info.behaves_evil(state, me):
            yield from self._run_evil_night(state, me)
            return

        choice = state.get_night_info(NightWatchman, me, state.night)
        if choice is None:
            yield state; return
        if nightwatchman.is_dead or self.spent:
            return
        self.spent = True

        if info.behaves_evil(state, choice.player):
            if self.is_droisoned(state, me):
                state.math_misregistration(me)
            yield state; return

        all_pings = state.puzzle.external_info_registry.get(
            (NightWatchman, state.night), []
        )
        confirmed_by_good = any(
            True for ping, pid in all_pings
            if choice.player == pid and ping.player == me
        )
        if self.is_droisoned(state, me):
            state.math_misregistration(me)
            if not confirmed_by_good:
                yield state
        elif confirmed_by_good:
            yield state

    def _run_evil_night(self, state: State, me: PlayerID) -> StateGen:
        """run_night when an evil player hold the NightWatchman ability."""
        # Check if a good player received the Ping
        all_pings = state.puzzle.external_info_registry.get(
            (NightWatchman, state.night), []
        )
        good_pings = [pid for ping, pid in all_pings if ping.player == me]
        if len(good_pings) > 1:
            return
        if good_pings:
            if not self.spent:
                # The world where they used it on a truthful player tonight
                self.spent = True
                yield state
            return
        if not self.spent:
            # The world where they use it on someone who needn't report it
            spent_world = state.fork()
            spent_nwm = spent_world.players[me].get_ability(NightWatchman)
            spent_nwm.spent = True
            yield spent_world
        # The world where they don't use it
        yield state

    @staticmethod
    def global_end_night(state: State) -> bool:
        """
        Run global check that nobody without the NightWatchman ability claimed
        to make a Choice (since `run_night` only executes on true NighWatchman
        instances).
        """
        return not any(
            state.get_night_info(NightWatchman, pid, state.night) is not None
            and not player.has_ability(NightWatchman)
            and not info.behaves_evil(state, pid)
            and not player.lies_about_self
            for pid, player in enumerate(state.players)
        )

@dataclass
class Noble(Townsfolk):
    """
    You start knowing 3 players, 1 and only 1 of which is evil.
    """
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
            
        def display(self, names: list[str]) -> str:
            return (
                f'One of {names[self.player1]}, {names[self.player2]} and '
                f'{names[self.player3]} is evil'
            )

@dataclass
class NoDashii(GenericDemon):
    """
    Each night*, choose a player: they die.
    Your 2 Townsfolk neighbors are poisoned.
    """
    tf_neighbour1: PlayerID | None = None
    tf_neighbour2: PlayerID | None = None

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        # TODO: This implementation allows the No Dashii to poison
        # misregistering characters (e.g. Spy), so there may be multiple
        # possible combinations of neighbour pairs depending on ST choices.
        # However this is wrong and should be simplified.
        # In order to do it truly properly, we need to be able to check if the
        # neighbour misreg is from that player's ability, i.e., we need to know
        # if a neighbouring demon is holding the Boffin[Alchemist[Spy]] ability
        # and could misregister as a Townsfolk to catch the poison.
        N = len(state.players)
        fwd_candidates, bkwd_candidates = [], []
        for candidates, direction in (
            (fwd_candidates, 1),
            (bkwd_candidates, -1),
        ):
            for step in range(1, N):
                player = (me + direction * step) % N
                is_tf = info.IsCategory(player, Townsfolk)(state, me)
                if is_tf.not_false():
                    candidates.append(player)
                if is_tf.is_true():
                    break
        # Create a world or each combination of left and right poisoned player
        for fwd in fwd_candidates:
            for bkwd in bkwd_candidates:
                new_state = state.fork()
                new_nodashii = new_state.players[me].get_ability(NoDashii)
                new_nodashii.tf_neighbour1 = fwd
                new_nodashii.tf_neighbour2 = bkwd
                new_nodashii.maybe_activate_effects(new_state, me)
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
class Oracle(Townsfolk):
    """
    Each night*, you learn how many dead players are evil.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    @dataclass
    class Ping(info.Info):
        count: int
        def __call__(self, state: State, src: PlayerID) -> STBool:
            return info.ExactlyN(
                N=self.count,
                args=[
                    info.IsEvil(player) & ~info.IsAlive(player)
                    for player in state.player_ids
                ]
            )(state, src)
            
        def display(self, names: list[str]) -> str:
            return f"{self.count} dead evils"

@dataclass
class Philosopher(Townsfolk):
    """
    Once per game, at night, choose a good character: gain that ability.
    If this character is in play, they are drunk.
    """
    # Wake pattern is replaced upon Character choice
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    active_ability: Character | None = None
    drunk_target: PlayerID | None = None
    droisoned_philo_choice: bool = False

    @dataclass
    class Choice(info.NotInfo):
        character: type[Character]
            
        def display(self, names: list[str]) -> str:
            return f"Chose {self.character.name} ability"

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        if info.behaves_evil(state, me):
            # raise NotImplementedError('Evil Philosopher')
            print('TMP ', end='')

        philo = state.players[me]

        if self.active_ability is not None:
            if self.droisoned_philo_choice:
                # If waking to an ability you don't have, increment Math
                ability_t = type(self.active_ability.drunklike_character)
                if (
                    state.get_night_info(ability_t, me, state.night) is not None
                    or self.active_ability.wakes_tonight(state, me)
                ):
                    state.math_misregistration(me)
            yield from self.active_ability.run_night(state, me)
            return
        if philo.is_dead:
            yield state; return  # I miss GOTOs, and I'm not ashamed to say it.

        choice = state.get_night_info(Philosopher, me, state.night)
        if choice is None:
            yield state; return
        new_character = choice.character(first_night=state.night)
        if self.is_droisoned(state, me):
            # If Philo is is droisoned when they make their choice, they become
            # a Drunk-like player who thinks they have an ability thereafter.
            self.active_ability = Drunklike(
                drunklike_character=new_character
            )
            self.drunk_target = None
            self.droisoned_philo_choice = True
            state.math_misregistration(me)
            yield state; return

        self.active_ability = new_character
        self.lies_about_self = choice.character.lies_about_self  # Philo-Mutant...?

        for substate in self.active_ability.run_setup(state, me):
            drunk_targets = [
                player for player in state.player_ids
                if info.IsCharacter(
                    player, choice.character
                )(substate, me).not_false()
            ]
            if not drunk_targets:
                drunk_targets.append(None)

            for drunk_target in drunk_targets:
                new_state = (
                    substate if len(drunk_targets) == 1
                    else substate.fork()
                )
                new_philo = new_state.players[me].get_ability(Philosopher)
                new_philo.drunk_target = drunk_target
                new_philo.maybe_activate_effects(new_state, me)
                yield new_state

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        if self.active_ability is None:
            return super().run_setup(state, me)
        return self.active_ability.run_setup(state, me)

    def run_day(self, state: State, me: PlayerID) -> StateGen:
        if self.active_ability is None:
            return super().run_day(state, me)
        return self.active_ability.run_day(state, me)

    def end_night(self, state: State, me: PlayerID) -> StateGen:
        if self.active_ability is None:
            yield state
        else:
            yield from self.active_ability.end_night(state, me)

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        if self.active_ability is None:
            yield state; return
        yield from self.active_ability.end_day(state, me)

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.active_ability is None:
            return
        if self.drunk_target is not None:
            state.players[self.drunk_target].droison(state, me)
        self.active_ability.maybe_activate_effects(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.active_ability is None:
            return
        if self.drunk_target is not None:
            state.players[self.drunk_target].undroison(state, me)
        self.active_ability.maybe_deactivate_effects(state, me)

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

    def wakes_tonight(self, state: State, me: PlayerID) -> bool:
        if self.active_ability is None:
            return super().wakes_tonight(state, me)
        return self.active_ability.wakes_tonight(state, me)

    @property
    def spent(self):
        if self.active_ability is None:
            return None
        return getattr(self.active_ability, 'spent', None)

    @spent.setter
    def spent(self, value):
        if self.active_ability is None:
            return
        self.active_ability.spent = value

    @property
    def drunklike_character(self):
        return getattr(self.active_ability, 'drunklike_character', None)

    @property
    def misregister_categories(self) -> tuple[Category, ...]:
        return (
            () if self.active_ability is None
            else self.active_ability.misregister_categories
        )


@dataclass
class PitHag(Minion):
    """
    Each night*, choose a player & a character they become (if not in play).
    If a Demon is made, deaths tonight are arbitrary.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    target_history: list[tuple[PlayerID, type[Character]]] = field(
        default_factory=list
    )

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        # PitHag arbitrary deaths can prevent deaths backwards in time, so we
        # must speculatively create a parallel world where there are arbitrary
        # deaths from the start of the night, and and filter out the incorrect
        # choices later.
        if (
            # Next night is not coming.
            state.day == state.puzzle.max_night
            # Can't make demon because they're all in play
            or not any (
                info.IsInPlay(character)(state, me).not_true()
                for character in state.puzzle.script
                if PitHag._can_register_as_demon(character)
            )
        ):
            yield state; return
        assert not hasattr(state, 'pithag_preventing_kills'), 'Todo: 2 PitHags'
        arbitrary_death_state = state.fork()
        arbitrary_death_state.pithag_preventing_kills = me
        yield arbitrary_death_state
        yield state

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        pithag = state.players[me]
        if state.night == 1 or (pithag.is_dead and not pithag.vigormortised):
            yield state; return
        if self.is_droisoned(state, me):
            # Cover both cases where would have failed or not
            state.math_misregistration(me, info.STBool.FALSE_MAYBE)
            yield state; return

        candidate_characters = PitHag._get_valid_changes(state, me)
        for target, characters in enumerate(candidate_characters):
            for char_t in characters:
                new_state = state.fork()
                new_state.log(f'PitHag changes {state.players[target].name}'
                              f' into {char_t.__name__}')
                new_pithag = new_state.players[me].get_ability(PitHag)
                new_pithag.target_history.append((target, char_t))
                for substate in new_state.change_character(target, char_t):
                    if PitHag._can_register_as_demon(char_t):
                        yield from PitHag._arbitrary_deaths(substate, me)
                    else:
                        yield substate
        # No-change world
        if getattr(state, 'pithag_preventing_kills', None) != me:
            self.target_history.append((None, None))
            state.log('PitHag picks in-play character')
            yield state

    @staticmethod
    def _get_valid_changes(
        state: State,
        me: PlayerID,
    ) -> list[list[type[Character]]]:
        """
        Selects which characters each player can be changed into, with the
        following logic/optimisations:
        1. In speculative arbitrary death nights, it was already pre-ordained
           at the start of the night that a Demon will be made tonight.
        2. Only investigate changing good players if they report the same
           change the following day or have a reason not to.
        """
        characters = [
            character for character in state.puzzle.script
            if info.IsInPlay(character)(state, me).not_true()
        ]
        if getattr(state, 'pithag_preventing_kills', None) == me:
            # PitHag must create demon to match speculative arbitrary kill night
            characters = list(filter(PitHag._can_register_as_demon, characters))
        lying_characters = [c for c in characters if c.lies_about_self]
        ret = []
        for player in state.players:
            if (
                info.behaves_evil(state, player.id)
                or player.lies_about_self
            ):
                ret.append(characters)
                continue
            player_chars = set(lying_characters)
            claim_change = state.get_night_info(
                info.CharacterChange, player.id, state.night
            )
            if claim_change is not None:
                player_chars.add(claim_change.character)
            ret.append(player_chars)
        return ret


    @staticmethod
    def _arbitrary_deaths(state: State, me: PlayerID) -> StateGen:
        # The PitHag causes deaths at arbitrary times in the night order, but
        # generating a world for all possible deaths at all possible points in
        # the night order, every night, along with all combinations of allowing
        # real kills to succeed or fail is pretty infeasible.
        # Instead I generate two worlds:
        # (1) The PitHag prevents deaths for the whole night, then enacts
        #     all required deaths at the end of the night.
        # (2) The PitHag allows the night to play out, then kills remaining
        #     unexplained deaths at the end of the night.
        # (3) The PitHag causes all deaths right now, and prevents any other
        #     character from killing tonight.
        # This will cover the vast majority of cases, but may miss some very
        # timing-plus-character-sensitive cases. E.g., the PitHag kills the
        # Philo-Sage right now, next the demon kills the real (now-sober) Sage.
        # But that's quite whacky. Better coverage of cases can be added later
        # if needed...

        # World 1: Let the night continue, come back later to do remaining kills
        # Added wrinkle: PitHag has already decided if we are in World 1 at the
        # end of the previous day (see PitHag.end_day()), so detect that here
        if getattr(state, 'pithag_preventing_kills', None) == me:
            state.pithag_kills_at_night_end = me
            state.log(f'PitHag prevents all deaths until night end')
            yield state
            return

        # World 2: Let the night continue, come back later to do remaining kills
        remaining_kills_later_state = state.fork()
        remaining_kills_later_state.pithag_kills_at_night_end = me
        yield remaining_kills_later_state

        # World 3: kill all right now, prevent any further deaths.
        for substate in PitHag._kill_all_remaining_deaths(state, me):
            substate.pithag_preventing_kills = me
            yield substate

    @staticmethod
    def _kill_all_remaining_deaths(state: State, me: PlayerID) -> StateGen:
        deaths = [
            death.player
            for death in state.puzzle.night_deaths.get(state.night, ())
            if info.IsAlive(death.player)(state, me).is_true()
            and isinstance(death, events.NightDeath)
        ]
        state.log(f'PitHag kills {[state.players[d].name for d in deaths]}')
        states = [state]
        for pid in deaths:
            states = core.apply_all(states, lambda state, pid=pid: (
                state.players[pid].character.attacked_at_night(state, pid, me)
            ))
        yield from states

    def end_night(self, state: State, me: PlayerID) -> StateGen:
        if hasattr(state, 'pithag_preventing_kills'):
            del state.pithag_preventing_kills
        if hasattr(state, 'pithag_kills_at_night_end'):
            del state.pithag_kills_at_night_end
            yield from PitHag._kill_all_remaining_deaths(state, me)
        else:
            yield state

    @staticmethod
    def _can_register_as_demon(character: type[Character]):
        return (
            issubclass(character, Demon)
            or (
                isinstance(character.misregister_categories, tuple)
                and Demon in character.misregister_categories
            )
        )

    def _world_str(self, state: State) -> str:
        history_strs = [
            f'{state.players[p].name} into {c.__name__}'
            if p is not None else 'None'
            for p, c in self.target_history
        ]
        return f"{type(self).__name__} (Changed {', '.join(history_strs)})"

@dataclass
class Po(GenericDemon):
    """
    Each night*, you may choose a player: they die.
    If your last choice was no-one, choose 3 players tonight.
    """

    charged: bool = False

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        po = state.players[me]
        if state.night == 1 or po.is_dead or getattr(po, 'exorcised_count', 0):
            yield state; return

        if not self.charged:
            # Charge World
            new_state = state.fork()
            new_state.players[me].get_ability(Po).charged = True
            yield new_state

            # 1 Kill World
            sunk_a_kill = False
            for target in state.player_ids:
                dead_target = state.players[target].is_dead
                if dead_target:
                    if sunk_a_kill:
                        continue  # Dedupe sinking kill choice
                    sunk_a_kill = True
                new_state = state.fork()
                if self.is_droisoned(state, me):
                    if not dead_target:
                        new_state.math_misregistration(me)
                    yield new_state
                    continue
                target_char = new_state.players[target].character
                yield from target_char.attacked_at_night(new_state, target, me)
        else:
            # 3 Kill World
            print('Untested code')
            self.charged = False
            if self.is_droisoned(state, me):
                state.math_misregistration(me)
                yield state
                return

            for kills in itertools.combinations(state.player_ids, r=3):
                new_states = [state.fork()]
                for kill in kills:
                    new_states = core.apply_all(
                        new_states,
                        lambda substate, kill=kill:
                        substate.players[kill].character.attacked_at_night(
                            substate, kill, me
                        )
                    )
                yield from new_states

@dataclass
class Poisoner(Minion):
    """
    Each night, choose a player: they are poisoned tonight and tomorrow day.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    target: PlayerID = None

    # Keep history just for pretty printing the history of a game.
    target_history: list[PlayerID] = field(default_factory=list)

    def run_night(self, state: State, src: PlayerID) -> StateGen:
        """Override Reason: Create a world for every poisoning choice."""
        poisoner = state.players[src]
        if poisoner.is_dead and not poisoner.vigormortised:
            yield state; return
        for target in state.player_ids:
            new_state = state.fork()
            new_poisoner = new_state.players[src].get_ability(Poisoner)
            # Even droisoned poisoners make a choice, because they might be
            # undroisoned before dusk.
            new_poisoner.target = target
            new_poisoner.target_history.append(target)
            new_poisoner.maybe_activate_effects(new_state, src)
            yield new_state

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        self.maybe_deactivate_effects(state, me)
        self.target = None
        yield state

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
class Politician(Outsider):
    """
    If you were the player most responsible for your team losing,
    you change alignment & win, even if dead.
    """
    lies_about_self: ClassVar[bool] = True
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

@dataclass
class PoppyGrower(Townsfolk):
    """
    Each night, choose a player (not yourself):
    tomorrow, you may only vote if they are voting too.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    @dataclass
    class InPlay(info.ExternalInfo):
        """A player who was evil can claim they know a PoppyGrower was play."""
        def __call__(self, state: State, src: PlayerID) -> bool:
            for player in state.players:
                pg = player.get_ability(PoppyGrower)
                if not (pg is None or pg.is_droisoned(state, player.id)):
                    return True
            return False
            
        def display(self, names: list[str]) -> str:
            return "A PoppyGrower was in play"

@dataclass
class Princess(Townsfolk):
    """
    On your 1st day, if you nominated & executed a player,
    the Demon doesn’t kill tonight.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    activated: bool = False

    def _nominates(self, state: State, me: PlayerID, nominee: PlayerID) -> None:
        if self.first_night != state.day:
            return
        if any(
            isinstance(ev, events.Execution)
            for ev in state.puzzle.day_events.get(state.day, [])
        ):
            self.activated = True
            self.maybe_activate_effects(state, me)

    def uneventful_nomination(
        self,
        state: State,
        nomination: events.UneventfulNomination,
        me: PlayerID,
    ) -> StateGen:
        self._nominates(state, nomination.nominator, nomination.player)
        yield state

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.activated:
            state.active_princesses = getattr(state, 'active_princesses', 0) + 1

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.activated:
            state.active_princesses -= 1
            if state.active_princesses == 0:
                del state.active_princesses

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        if self.first_night < state.day:
            self.maybe_deactivate_effects(state, me)
            self.activated = False
        yield state

@dataclass
class Progidy(Townsfolk):
    """
    HOMEBREW: NQT
    You draw the Prodigy token. Each night, choose a player:
    you learn a player of the same(solar)/opposite(lunar) alignment.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    is_solar: bool | None = None

    @dataclass
    class Ping(info.Info):
        chose: PlayerID
        shown: PlayerID
        def __call__(self, state: State, src: PlayerID) -> STBool:
            chose_evil = info.IsEvil(self.chose)(state, src)
            shown_evil = info.IsEvil(self.shown)(state, src)
            if state.players[src].get_ability(Progidy).is_solar:
                return chose_evil == shown_evil
            else:
                return chose_evil ^ shown_evil

        def display(self, names: list[str]) -> str:
            return f"Chose {names[self.chose]}, shown {names[self.shown]}"

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        if state.current_phase is not core.Phase.SETUP:
            raise NotImplementedError('Prodigy created mid-game')

        # Check if another prodigy hase already set our polarity
        if self.is_solar is not None:
            yield state
            return

        other_prodigies = [
            i for i, player in enumerate(state.players)
            if i != me and player.has_ability(Progidy)
        ]
        if len(other_prodigies) > 1:
            return

        # I am Solar
        solar_state = state.fork()
        solar_state.players[me].get_ability(Progidy).is_solar = True
        if other_prodigies:
            lunar = other_prodigies[0]
            solar_state.players[lunar].get_ability(Progidy).is_solar = False
        yield solar_state

        # I am Lunar
        state.players[me].get_ability(Progidy).is_solar = False
        if other_prodigies:
            solar = other_prodigies[0]
            state.players[solar].get_ability(Progidy).is_solar = True
        yield state

    def _world_str(self, state: State) -> str:
        return f"{'Solar' if self.is_solar else 'Lunar'}Prodigy"


@dataclass
class Pukka(Demon):
    """
    Each night, choose a player: they are poisoned.
    The previously poisoned player dies then becomes healthy.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    target: PlayerID | None = None

    # For pretty-printing the history of a game.
    target_history: list[PlayerID] = field(default_factory=list)

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """TODO: This wouldn't handle picking a Goon"""
        pukka = state.players[me]
        if pukka.is_dead:
            yield state; return
        if self.is_droisoned(state, me):
            if (
                self.target is not None
                and not state.players[self.target].is_dead
            ):
                state.math_misregistration(me)
            yield state; return

        if getattr(pukka, 'exorcised_count', 0):
            self.target, target = None, self.target
            yield from pukka._do_kill(state, me, target)
            return

        # A Pukka's new target is poisoned, then the previous target dies, and
        # _then_ the previous target becomes sober. For that reason we can't use
        # `maybe_deactivate_effects` because target will have changed, so we
        # manually handle the unpoisoning of the killed player.
        self.effects_active = False
        for new_target in state.player_ids:
            new_state = state.fork()
            new_pukka = new_state.players[me].get_ability(Pukka)
            new_pukka.target = new_target
            new_pukka.target_history.append(new_target)
            new_pukka.maybe_activate_effects(new_state, me)
            yield from new_pukka._do_kill(new_state, me, self.target)

    def _do_kill(_, state: State, me: PlayerID, target: PlayerID) -> StateGen:
        """The kill-and-make-healthy part of the Pukka's night ability."""
        # Do not refer to self.target, bc it has already been set to the new
        # poison target.
        if target is None:
            yield state
            return
        target_char = state.players[target].character
        for substate in target_char.attacked_at_night(state, target, me):
            substate.players[target].undroison(substate, me)
            yield substate

    def _activate_effects_impl(self, state: State, me: PlayerID):
        state.players[self.target].droison(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        # Break a self-poisoning infinite recursion, whilst still leaving the
        # Pukka marked as droisoned.
        if self.target != me:
            state.players[self.target].undroison(state, me)

@dataclass
class Puzzlemaster(Outsider):
    """
    1 player is drunk, even if you die. If you guess (once) who it is, learn the
    Demon player, but guess wrong & get false info.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    puzzle_drunk: PlayerID | None = None
    spent: bool = False

    @dataclass
    class Ping(info.Info):
        guess: PlayerID
        demon: PlayerID
        def __call__(self, state: State, me: PlayerID) -> STBool:
            correct_demon = info.IsCategory(self.demon, Demon)(state, me)
            puzzlemaster = state.players[me].get_ability(Puzzlemaster)
            if self.guess == puzzlemaster.puzzle_drunk:
                return correct_demon
            return ~correct_demon
            
        def display(self, names: list[str]) -> str:
            return (
                f'Guessed {names[self.guess]}, told '
                f'{names[self.demon]} is the Demon'
            )

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Choose puzzle_drunk."""
        for player in state.player_ids:
            new_state = state.fork()
            new_puzzlemaster = new_state.players[me].get_ability(Puzzlemaster)
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
        if not (
            self.effects_active
            or self.is_droisoned(state, me)
            or reason is Reason.RESURRECTION
        ):
            # TODO: Should effects be marked active even on RESURRECTION?
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
class Ravenkeeper(Townsfolk):
    """
    If you die at night, you are woken to choose a player:
    you learn their character.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    death_night: int | None = None

    @dataclass
    class Ping(info.Info):
        player: PlayerID
        character: type[Character]

        def __call__(self, state: State, src: PlayerID) -> STBool:
            assert state.night > 1, "Ravenkeepers don't die night 1!"
            ravenkeeper = state.players[src].get_ability(Ravenkeeper)
            death_night = ravenkeeper.death_night
            if death_night is None or death_night != state.night:
                return info.STBool.FALSE
            result = info.IsCharacter(self.player, self.character)(state, src)
            if ravenkeeper.died_droisoned:
                state.math_misregistration(src, result)
                return result ^ info.STBool.FALSE_MAYBE
            return result
            
        def display(self, names: list[str]) -> str:
            return f"{names[self.player]} is the {self.character.__name__}"

    def apply_death(
        self,
        state: State,
        me: PlayerID,
        src: PlayerID | None = None,
    ) -> StateGen:
        """Override Reason: Record when death happened."""
        if state.night is not None:
            self.death_night = state.night
            self.died_droisoned = self.is_droisoned(state, me)
            state.players[me].woke()
        yield from super().apply_death(state, me, src)

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Even if dead & droisoned."""
        # The Ping checks the death was on the same night.
        # We escape the droison check performed by default_info_check and
        # manually check inside the ping, because e.g. a Pukka would undroison
        # the RK before it's position in the night order.
        if self.default_info_check(
            state, me, even_if_dead=True, even_if_droisoned=True
        ):
            yield state

    def wakes_tonight(self, state: State, me: PlayerID) -> bool:
        return state.get_night_info(Ravenkeeper, me, state.night) is not None

@dataclass
class Recluse(Outsider):
    """
    You might register as evil & as a Minion or Demon, even if dead.
    """
    misregister_categories: ClassVar[tuple[Category, ...]] = (Minion, Demon)
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

@dataclass
class Riot(Demon):
    """
    On day 3, Minions become Riot & nominees die but nominate an alive player
    immediately. This must happen.
    """
    # This doesn't implement (m)any of the NUMEROUS Riot jinxes, since they tend
    # to completely change the way characters work. We can add them if they
    # become relevant I guess.

    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    currently_causing_riot: bool = False

    def run_day(self, state: State, me: PlayerID) -> StateGen:
        riot = state.players[me]
        if state.day != 3 or riot.is_dead:
            yield state; return
        if self.is_droisoned(state, me):
            state.math_misregistration(me)
            yield state; return

        self.maybe_deactivate_effects(state, me)
        self.maybe_activate_effects(state, me)

        # Riot-Exorcist jinx
        if getattr(riot, 'exorcised_count', 0):
            yield state; return

        # Turn minions into Riot. Include Recluse :D
        def _make_riot(states: StateGen, pid: PlayerID) -> StateGen:
            for substate in states:
                for subsubstate in substate.change_character(pid, Riot):
                    subsubstate.players[pid].character.maybe_activate_effects(
                        subsubstate, pid, Reason.CHARACTER_CHANGE
                    )
                    yield subsubstate

        minion_combinations = list(info.all_registration_combinations(
            [info.IsCategory(p.id, Minion)(state, me) for p in state.players]
        ))
        for minions in minion_combinations:
            states = [state if len(minion_combinations) == 1 else state.fork()]
            for minion in minions:
                states = _make_riot(states, minion)
            yield from states

    def _activate_effects_impl(self, state: State, me: PlayerID):
        riot = state.players[me]
        if (
            state.day == 3
            and not riot.is_dead
            and not getattr(self, 'exorcised_count', 0)
        ):
            state.rioting_count = getattr(state, 'rioting_count', 0) + 1
            self.currently_causing_riot = True

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.currently_causing_riot:
            self.currently_causing_riot = False
            state.rioting_count -= 1

    @staticmethod
    def day_three_nomination(state: State, nomination: Event) -> StateGen:
        riot_id = None
        for player in state.players:
            if (
                not player.is_dead
                and (riot := player.get_ability(Riot)) is not None
                and not riot.is_droisoned(state, player.id)
            ):
                riot_id = player.id
                break
        assert riot_id is not None

        if isinstance(nomination, events.UneventfulNomination):
            raise NotImplementedError('TODO: Riot nomination without death')

        assert isinstance(nomination, events.Dies)
        nominee = state.players[nomination.player]
        if nominee.is_dead:
            yield state
        else:
            yield from nominee.character.killed(state, nominee.id, riot_id)

@dataclass
class Sage(Townsfolk):
    """
    If the Demon kills you, you learn that it is 1 of 2 players.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    death_night: int | None = None

    @dataclass
    class Ping(info.Info):
        player1: PlayerID
        player2: PlayerID

        def __call__(self, state: State, src: PlayerID) -> STBool:
            assert state.night > 1, "Sages don't die night 1!"
            sage = state.players[src].get_ability(Sage)
            death_night = sage.death_night
            if death_night is None or death_night != state.night:
                return info.STBool.FALSE
            result = (
                info.IsCategory(self.player1, Demon)(state, src)
                | info.IsCategory(self.player2, Demon)(state, src)
            )
            if sage.died_droisoned:
                state.math_misregistration(src, result)
                return result ^ info.STBool.FALSE_MAYBE
            return result
            
        def display(self, names: list[str]) -> str:
            return f'{names[self.player1]} or {names[self.player2]} is the Demon'

    def apply_death(
        self,
        state: State,
        me: PlayerID,
        src: PlayerID | None,
    ) -> StateGen:
        """Override Reason: Record when death happened."""
        killed_by_demon = (
            info.IsCategory(src, Demon)(state, me)
            if src is not None
            else info.STBool.FALSE
        )
        if state.night is not None and killed_by_demon.not_false():
            self.death_night = state.night
            self.died_droisoned = self.is_droisoned(state, me)
            state.players[me].woke()
        yield from super().apply_death(state, me, src)

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """Override Reason: Even if dead."""
        # The Ping checks the death was on the same night.
        if self.default_info_check(
            state, me, even_if_dead=True, even_if_droisoned=True
        ):
            yield state

    def wakes_tonight(self, state: State, me: PlayerID) -> bool:
        return state.get_night_info(Sage, me, state.night) is not None

@dataclass
class Savant(Townsfolk):
    """
    Each day, you may visit the Storyteller to learn 2 things in private:
    one is true & one is false.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    @dataclass
    class Ping(info.Info):
        a: info.Info
        b: info.Info
        def __call__(self, state: State, src: PlayerID):
            a, b = self.a(state, src), self.b(state, src)
            if state.vortox:
                return a | b  # This is post-processed in Savant.run_day()
            return a ^ b
            
        def display(self, names: list[str]) -> str:
            return (
                f'Either ({self.a.display(names)}) or ({self.b.display(names)})'
            )

    def run_day(self, state: State, me: PlayerID) -> StateGen:
        """ Override Reason: Novel Vortox effect on Savant, see Savant.Ping."""
        savant = state.players[me]
        ping = state.get_day_info(Savant, me)
        if (
            savant.is_dead
            or ping is None
            or info.behaves_evil(state, me)
        ):
            yield state
            return
        result = ping(state, me)
        if state.vortox:
            if not result.truth():
                state.math_misregistration(me)
                yield state
            return
        if self.is_droisoned(state, me):
            state.math_misregistration(me, result)
            yield state
        elif result.not_false():
            yield state

@dataclass
class ScarletWoman(Minion):
    """
    If there are 5 or more players alive & the Demon dies, you become the Demon.
    (Travellers don't count).
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    def pre_death_in_town(
        self,
        state: State,
        about_to_die: PlayerID,
        me: PlayerID
    ) -> StateGen:
        """Catch a Demon death."""
        scarletwoman = state.players[me]
        dying_player = state.players[about_to_die]
        catches, droison = self.catches_death(state, dying_player, scarletwoman)

        if catches.not_false():

            # On MAYBE, spawn an extra world where no catch happened
            if catches.is_maybe():
                substate = state.fork()
                if dying_player.has_ability(ScarletWoman):  # TODO: What is this line doing?!?! Pls test me.
                    substate.math_misregistration(me, ~droison)
                yield substate

            possible_demons = set()
            if isinstance(dying_player.character, Demon):
                possible_demons.add(type(dying_player.character))
            # Recluse could have registered as any Demon on the script
            if dying_player.has_ability(Recluse):
                possible_demons.update(state.puzzle.demons)
            possible_demons.discard(Recluse)  # This ruling feels best to me.

            # Yield worlds where the SW catches the death
            for demon in possible_demons:
                substate = state.fork()
                if substate.night is not None:
                    substate.players[me].woke()
                yield from substate.change_character(me, demon)

        else:
            yield state

    @staticmethod
    def catches_death(
        state: State,
        dying: Player,
        scarletwoman: Player,
    ) -> tuple[STBool, STBool]:
        """
        Trigger condition is also checked by Imp, so has its own method.
        Returns:
            - STBool specifying if SW will catch
            - STBool specifying if a fumble would be due to poison. This is so
              the caller can increment Math number appropriately.
        """
        sw_ability = scarletwoman.get_ability(ScarletWoman)
        if sw_ability is None:
            return info.STBool.FALSE, info.STBool.FALSE

        living_player_count = sum(
            not p.is_dead and not isinstance(p.character, Traveller)
            for p in state.players
        )
        ability_active = info.STBool(
            living_player_count >= 5
            and (not scarletwoman.is_dead or scarletwoman.vigormortised)  # ?
        )
        demon_dying = info.IsCategory(dying.id, Demon)(state, scarletwoman.id)

        would_catch = demon_dying & ability_active
        sw_droisoned = sw_ability.is_droisoned(state, scarletwoman.id)
        if would_catch.not_false() and sw_droisoned:
            return info.STBool.FALSE, ~would_catch
        return would_catch, info.STBool.FALSE

    def wakes_tonight(self, state: State, me: PlayerID) -> bool:
        return False  # Not triggered by night order, so can't comput this here.


@dataclass
class Seamstress(Townsfolk):
    """
    Once per game, at night, choose 2 players (not yourself):
    you learn if they are the same alignment.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_UNTIL_SPENT

    spent: bool = False

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
            
        def display(self, names: list[str]) -> str:
            return (
                f'{names[self.player1]} and {names[self.player2]} are'
                f'{"" if self.same else " not"} the same alignment'
            )

@dataclass
class Shugenja(Townsfolk):
    """
    You start knowing if your closest evil player is clockwise or
    anti-clockwise. If equidistant, this info is arbitrary.
    """
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
            fwd_true, fwd_maybe, fwd_says = N, N, N
            bkwd_true, bkwd_maybe, bkwd_says = N, N, N
            for step in range(N // 2, 0, -1):
                if evils[step].truth():
                    fwd_true, fwd_maybe = step, step
                elif evils[step].is_maybe():
                    fwd_maybe = step
                if evils[step].st_says():
                    fwd_says = step
                if evils[-step].truth():
                    bkwd_true, bkwd_maybe = step, step
                elif evils[-step].is_maybe():
                    bkwd_maybe = step
                if evils[-step].st_says():
                    bkwd_says = step

            truth = fwd_true <= bkwd_true
            is_maybe = (
                bkwd_maybe <= fwd_true
                if truth else
                fwd_maybe <= bkwd_true
            )
            st_says = fwd_says <= bkwd_says
            return info.STBool((truth, is_maybe, st_says))
            
        def display(self, names: list[str]) -> str:
            return (
                f'Closest evil is {"" if self.clockwise else "anti-"}clockwise'
            )

@dataclass
class SnakeCharmer(Townsfolk):
    """
    Each night, choose an alive player:
    a chosen Demon swaps characters & alignments with you & is then poisoned.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    self_droison: bool = False
    target_history: list[PlayerID] = field(default_factory=list)

    @dataclass
    class Choice(info.NotInfo):
        player: PlayerID
    
        def display(self, names: list[str]) -> str:
            return f'Chose {names[self.player]}'

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        if state.players[me].is_dead:
            yield state; return

        if info.behaves_evil(state, me):
            yield from self._run_night_evil(state, me)
            return

        choice = state.get_night_info(SnakeCharmer, me, state.night)
        if choice is None:
            yield state; return
        if not isinstance(choice, SnakeCharmer.Choice): # Why is this here?
            return

        is_demon = info.IsCategory(choice.player, Demon)(state, me)
        if is_demon.is_false():
            yield state; return
        if is_demon.is_maybe():
            # Yield world where the jump happens plus one were it doesn't
            yield state.fork()
            jump_state = state.fork()
        else:
            jump_state = state

        if self.is_droisoned(jump_state, me):
            if not self.self_droison:
                jump_state.math_misregistration(me)
            yield jump_state; return

        yield from self._jump(jump_state, choice.player, me)

    def _run_night_evil(self, state: State, me: PlayerID) -> StateGen:
        demon_queries = [
            info.IsCategory(target, Demon)(state, me)
            for target in state.player_ids
        ]
        maybe_demons = [i for i, q in enumerate(demon_queries) if q.not_false()]

        # World class 1: tried to jump but poisoned
        if self.is_droisoned(state, me) and any(maybe_demons):
            poisoned_state = state.fork()
            if not self.self_droison:
                poisoned_state.math_misregistration(me)
            yield poisoned_state; return
        # World class 2: all the possible jumps
        for target in maybe_demons:
            jump_state = state.fork()
            jump_state.log(f'SnakeCharmer jumps {state.players[target].name}')
            new_sc = jump_state.players[me].get_ability(SnakeCharmer)
            yield from new_sc._jump(jump_state, target, me)
        # World class 3: jump not triggered
        if any(q.not_true() for q in demon_queries):
            state.log(f'SnakeCharmer misses')
            yield state

    def _jump(self, state: State, target: PlayerID, me: PlayerID) -> StateGen:
        i_am_evil = state.players[me].is_evil
        target_is_evil = state.players[target].is_evil
        demon_character = type(state.players[target].character)

        states = core.apply_all(
            [state], lambda s: s.change_alignment(target, i_am_evil))
        states = core.apply_all(
            states, lambda s: s.change_alignment(me, target_is_evil))
        states = core.apply_all(
            states, lambda s: s.change_character(me, demon_character))
        states = core.apply_all(
            states, lambda s: s.change_character(target, SnakeCharmer))

        for substate in states:
            new_sc = substate.players[target].get_ability(SnakeCharmer)
            new_sc.self_droison = True
            new_sc.maybe_activate_effects(substate, target)
            yield substate

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.self_droison:
            state.players[me].droison_count += 1

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.self_droison:
            state.players[me].undroison(state, me)

@dataclass
class Soldier(Townsfolk):
    """
    You are safe from the Demon.
    """
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
class Steward(Townsfolk):
    """
    You start knowing 1 good player.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    @dataclass
    class Ping(info.Info):
        player: PlayerID
        def __call__(self, state: State, src: PlayerID) -> STBool:
            return ~info.IsEvil(self.player)(state, src)
            
        def display(self, names: list[str]) -> str:
            return f'{names[self.player]} is good'

@dataclass
class Saint(Outsider):
    """
    If you die by execution, your team loses.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    def executed(self, state: State, me: PlayerID, died: bool) -> StateGen:
        """
        Override Reason: Game is not over, execution is not a valid world.
        We let the super method handle any non-Saint-related execution details.
        """
        droisoned = self.is_droisoned(state, me)
        if droisoned:
            state.math_misregistration(me)
        if droisoned or not died:
            yield from super().executed(state, me, died)


@dataclass
class Slayer(Townsfolk):
    """
    Once per game, during the day, publicly choose a player:
    if they are the Demon, they die.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    spent: bool = False

    @dataclass
    class Shot(events.Event):
        target: PlayerID
        died: bool
        player: PlayerID | None = None

        def __call__(self, state: State) -> StateGen:
            shooter = state.players[self.player]
            ability = shooter.get_ability(Slayer)
            if ability is None:
                if info.behaves_evil(state, self.player) and not self.died:
                    yield state
                return
            target = state.players[self.target]
            if (
                shooter.is_dead
                or target.is_dead
                or ability.spent
            ):
                should_die = info.STBool.FALSE
            else:
                should_die = info.IsCategory(self.target, Demon)(
                    state, self.player
                )
            if ability.is_droisoned(state, shooter.id):
                if should_die.not_false() and not self.died:
                    state.math_misregistration(self.player, ~should_die)
                should_die = info.STBool.FALSE

            ability.spent = True

            if self.died and should_die.not_false():
                state.math_misregistration(self.player, should_die)
                yield from target.character.killed(
                    state, self.target, src=shooter.id
                )
            elif not self.died and should_die.not_true():
                yield state
        
        def display(self, names: list[str]) -> str:
            return (
                f"{names[self.player]} shot {names[self.target]}"
                f"{' ' if self.died else ' with no effect'}"
            )

@dataclass
class Spy(Minion):
    """
    Each night, you see the Grimoire. You might register as good & as a
    Townsfolk or Outsider, even if dead.
    """
    misregister_categories: ClassVar[tuple[Category, ...]] = (
        Townsfolk, Outsider
    )
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT


@dataclass
class Sweetheart(Outsider):
    """
    When you die, 1 player is drunk from now on.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    target: PlayerID | None = None

    def apply_death(
        self,
        state: State,
        me: PlayerID,
        src: PlayerID | None = None,
    ) -> StateGen:
        if self.is_droisoned(state, me):
            yield from super().apply_death(state, me, src)
            return
        for player in state.player_ids:
            new_state = state.fork()
            new_sweetheart = new_state.players[me].get_ability(Sweetheart)
            new_sweetheart.target = player
            new_sweetheart.maybe_activate_effects(new_state, me, Reason.DEATH)
            new_state.log(f'Sweetheart drunking {state.players[player].name}')
            yield from super().apply_death(new_state, me, src)

    def maybe_activate_effects(
        self,
        state: State,
        me: PlayerID,
        reason: Reason,
    ) -> None:
        """Override Reason: Even when dead."""
        if reason is Reason.RESURRECTION:
            raise NotImplementedError('Resurrecting Sweetheart')
        if (
            not self.effects_active
            and not self.is_droisoned(state, me)
            and self.target is not None
        ):
            self.effects_active = True
            state.players[self.target].droison(state, me)

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
            and self.target != me  # Break recursion
        ):
            self.effects_active = False
            state.players[self.target].undroison(state, me)

    def _world_str(self, state: State) -> str:
        if self.effects_active and self.target is not None:
            return f'Sweetheart ({state.players[self.target].name} is drunk)'
        return 'Sweetheart'

@dataclass
class Undertaker(Townsfolk):
    """
    Each night*, you learn which character died by execution today.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT_STAR

    @dataclass
    class Ping(info.Info):
        player: PlayerID | None
        character: type[Character] | None

        def __call__(self, state: State, src: PlayerID) -> STBool:
            assert state.night > 1, "Undertaker acts from second night."
            assert (self.character is None) == (self.player is None)

            yesterday = state.night - 1
            yesterdays_events = state.puzzle.day_events.get(yesterday, [])
            if self.player is None:
                return STBool(
                    not any(
                        isinstance(e, events.Execution) and e.died
                        for e in yesterdays_events
                    )
                )
            elif any(
                isinstance(event, events.Execution)
                and event.player == self.player
                and event.died
                for event in yesterdays_events
            ):
                return info.IsCharacter(self.player, self.character)(state, src)
            return info.STBool.FALSE
            
        def display(self, names: list[str]) -> str:
            return f'{names[self.player]} is the {self.character.__name__}'

@dataclass
class VillageIdiot(Townsfolk):
    """
    Each night, choose a player: you learn their alignment.
    [+0 to +2 Village Idiots. 1 of the extras is drunk]
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    self_droison: bool = False

    @dataclass
    class Ping(info.Info):
        player: PlayerID
        is_evil: bool
        def __call__(self, state: State, src: PlayerID) -> STBool:
            registers_evil = info.IsEvil(self.player)(state, src)
            return registers_evil == info.STBool(self.is_evil)
            
        def display(self, names: list[str]) -> str:
            return (
                f'{names[self.player]} is {"evil" if self.is_evil else "good"}'
            )

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        # If there is more than one Village Idiot, choose one to be the drunk VI
        VIs = [i for i, player in enumerate(state.players)
                if player.get_ability(VillageIdiot) is not None]
        already_done = any(
            state.players[v].get_ability(VillageIdiot).self_droison for v in VIs
        )
        if len(VIs) == 1 or already_done:
            yield state
            return

        for vi in VIs:
            new_state = state.fork()
            drunk_vi = new_state.players[vi]
            drunk_vi.droison_count += 1
            drunk_vi.get_ability(VillageIdiot).self_droison = True
            yield new_state

    def _world_str(self, state: State) -> str:
        """For printing nice output representations of worlds"""
        return f'VillageIdiot ({"Drunk" if self.self_droison else "Sober"})'

@dataclass
class Washerwoman(Townsfolk):
    """
    You start knowing that 1 of 2 players is a particular Townsfolk.
    """
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
            
        def display(self, names: list[str]) -> str:
            return (
                f'{names[self.player1]} or {names[self.player2]} '
                f'is the {self.character.__name__}'
            )

@dataclass
class Widow(Minion):
    """
    On your 1st night, look at the Grimoire & choose a player:
    they are poisoned. 1 good player knows a Widow is in play.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.FIRST_NIGHT

    target: PlayerID | None = None

    @dataclass
    class InPlay(info.ExternalInfo):
        def __call__(self, state: State, src: PlayerID) -> bool:
            return True
            
        def display(self, names: list[str]) -> str:
            return 'A Widow is in play'

    def run_setup(self, state: State, me: PlayerID) -> StateGen:
        if state.current_phase is not core.Phase.SETUP and self.target is None:
            yield from self._run_first_night(state, me, Reason.CHARACTER_CHANGE)
        else:
            yield state

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        if state.night == 1 and self.target is None:
            yield from self._run_first_night(state, me, None)
        else:
            yield state

    @staticmethod
    def _good_pings_heard_tonight(state: State) -> list[PlayerID]:
        all_pings = state.puzzle.external_info_registry.get(
            (Widow, state.night), []
        )
        return [pid for _, pid in all_pings if not info.behaves_evil(state, pid)]

    def _run_first_night(
        self,
        state: State,
        me: PlayerID,
        reason: Reason,
    ) -> StateGen:
        """
        Run the Widow's first night. On the first night of the game this
        happens just after the Poisoner (according to night order), but if
        created mid-game (as far as I can see) it always happens at the
        moment of creation, ignoring night-order.
        """
        good_pings_heard_tonight = Widow._good_pings_heard_tonight(state)
        maybe_heard_by_liar = any(
            info.behaves_evil(state, player.id) and not player.is_evil
            for player in state.players
        )
        # TODO: Once we have alignment change callbacks, record who heard the
        # Widow.Ping so it can be moved if they become evil.

        for target in state.player_ids:
            substate = state.fork()
            widow = substate.players[me].get_ability(Widow)
            widow.target = target
            widow.maybe_activate_effects(substate, me, reason)
            if widow.is_droisoned(substate, me):
                if target != me:
                    substate.math_misregistration(me)
                yield substate
            elif good_pings_heard_tonight or maybe_heard_by_liar:
                substate.widow_pinged_night = substate.night
                yield substate

    @staticmethod
    def global_end_night(state: State) -> bool:
        """
        Validate Pings this night made sense. Called at the end of the night
        if Widow is on the script, regardless of whether it's in play.
        """
        good_pings_heard_tonight = Widow._good_pings_heard_tonight(state)
        if len(good_pings_heard_tonight) > 1:
            # I read the rules as only one good player will ever be informed
            # Not yet handled case of alignment change within the same night...
            return False
        if getattr(state, 'widow_pinged_night', None) != state.night:
            return not good_pings_heard_tonight
        maybe_heard_by_liar = any(
            info.behaves_evil(state, player.id) and not player.is_evil
            for player in state.players
        )
        return good_pings_heard_tonight or maybe_heard_by_liar

    def _activate_effects_impl(self, state: State, me: PlayerID):
        if self.target == me:
            state.players[me].droison_count += 1
        elif self.target is not None:
            state.players[self.target].droison(state, me)
            if not hasattr(state, 'widow_pinged_night'):
                state.widow_pinged_night = (
                    state.night if state.night is not None else state.day + 1
                )

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        if self.target == me:
            state.players[me].droison_count -= 1
        elif self.target is not None:
            state.players[self.target].undroison(state, me)

    def _world_str(self, state: State) -> str:
        return f'Widow (Poisoned {state.players[self.target].name})'

@dataclass
class Witch(Minion):
    """
    Each night, choose a player: if they nominate tomorrow, they die.
    If just 3 players live, you lose this ability.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.EACH_NIGHT

    target: PlayerID | None = None

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        self.maybe_deactivate_effects(state, me)
        self.target = None

        witch = state.players[me]

        if (
            (witch.is_dead and not witch.vigormortised)
            or sum(not p.is_dead for p in state.players) <= 3
        ):
            yield state; return

        if self.is_droisoned(state, me):
            # Uninteresting to distinguish worlds where curse misfired or didn't
            # handle both with a single MAYBE math misregistration.
            state.math_misregistration(me, info.STBool.TRUE_MAYBE)
            yield state; return

        # Only spawn worlds cursing people who nominate tomorrow (plus one more)
        # TODO: If goon ability in play, consider cursing them (even droisoned)
        def nominator_from_event(e):
            return (
                e.player if (isinstance(e, events.Dies) and e.after_nominating)
                else e.nominator if isinstance(e, events.UneventfulNomination)
                else None
            )
        nominators = [
            nominator
            for ev in state.puzzle.day_events.get(state.night, [])
            if (nominator := nominator_from_event(ev)) is not None
        ]
        for target in nominators:
            new_state = state.fork()
            new_witch = new_state.players[me].get_ability(Witch)
            new_witch.target = target
            new_witch.maybe_activate_effects(new_state, me)
            yield new_state

        for target in state.player_ids:
            if target not in nominators:
                # The world without a successful curse
                self.target = target
                self.maybe_activate_effects(state, me)
                yield state
                return

    def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
        if self.target is not None:
            state.players[self.target].witch_cursed = me

    def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
        if self.target is not None:
            del state.players[self.target].witch_cursed

    def uneventful_nomination(
        self,
        state: State,
        nomination: events.UneventfulNomination,
        me: PlayerID,
    ) -> StateGen:
        nominator = state.players[nomination.nominator]
        if self.target is not nominator.id:
            yield state
        elif nominator.character.cant_die(state, nominator.id):
            state.math_misregistration(me)
            yield state

@dataclass
class Vigormortis(GenericDemon):
    """
    Each night*, choose a player: they die. Minions you kill keep their ability
    & poison 1 Townsfolk neighbor. [-1 Outsider]
    """
    poisoned_tf: list[PlayerID] = field(default_factory=list)
    killed_minions: list[PlayerID] = field(default_factory=list)

    @staticmethod
    def modify_category_counts(bounds: CategoryBounds) -> CategoryBounds:
        (min_tf, max_tf), (min_out, max_out), mn, dm = bounds
        bounds = (min_tf + 1, max_tf + 1), (min_out - 1, max_out - 1), mn, dm
        return bounds

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        vig = state.players[me]
        if (
            state.night == 1
            or vig.is_dead
            or getattr(vig, 'exorcised_count', 0)
        ):
            yield state; return

        N = len(state.players)
        sunk_a_kill = False
        for target in range(N):
            target_player = state.players[target]

            # 1. The kill sink world
            if target_player.is_dead:
                if sunk_a_kill:
                    continue  # Dedupe identical kill_sink worlds
                yield state.fork()
                sunk_a_kill = True
                continue

            # 2. The droison world
            if self.is_droisoned(state, me):
                droison_state = state.fork()
                droison_state.math_misregistration(me)
                yield droison_state
                continue

            is_minion = info.IsCategory(target, Minion)(state, me)

            # 3. The normal kill world
            if is_minion.not_true():
                kill_state = state.fork()
                kill_target = kill_state.players[target].character
                yield from kill_target.attacked_at_night(kill_state, target, me)
                if is_minion.is_false():
                    continue

            # 4. The killed minion world
            minion_state = state.fork()
            minion = minion_state.players[target].character
            minion.vigormortised = True
            # TODO: ALL of the player's abilities should be marked vigormortised
            # not just the root ability/character. Do this by maing an ability
            # generator on a player, which `get_ability` and `has_ability` call.
            poison_candidates = (
                info.tf_candidates_in_direction(minion_state, target, -1)
                + info.tf_candidates_in_direction(minion_state, target, 1)
            )
            for ss1 in minion.attacked_at_night(minion_state, target, me):
                for poison_candidate in poison_candidates:
                    ss2 = ss1.fork()
                    new_vig = ss2.players[me].get_ability(Vigormortis)
                    # Don't use deactivate_effects because that would kill
                    # existing dead minions. So manually add targets and effects
                    new_vig.maybe_activate_effects(ss2, me)
                    new_vig.killed_minions.append(target)
                    new_vig.poisoned_tf.append(poison_candidate)
                    if new_vig.effects_active:
                        ss2.players[poison_candidate].droison(ss2, me)
                    yield ss2

    def _activate_effects_impl(self, state: State, me: PlayerID):
        # TODO: Possibly remove both these things. I think maybe a reactivated
        # vigormortis doesn't reanimate dead minions (or repoison their
        # neighbours?) but I'm on a plane with no wifi right now so can't check.
        for target in self.poisoned_tf:
            state.players[target].droison(state, me)
        for minion in self.killed_minions:
            state.players[minion].character.vigormortised = True

    def _deactivate_effects_impl(self, state: State, me: PlayerID):
        # TODO: Clear self.poison_targets and self.killed_minions here too?
        for target in self.poisoned_tf:
            state.players[target].droison(state, me)
        for minion in self.killed_minions:
            minion_char = state.players[minion].character
            if hasattr(minion_char, 'vigormortised'):
                del minion_char.vigormortised
                # TODO: minion character change event should notify vigormortis.

    def _world_str(self, state: State) -> str:
        names = [state.players[target].name for target in self.poisoned_tf]
        return f'Vigormortis (Poisoning {" & ".join(names)})'

@dataclass
class Virgin(Townsfolk):
    """
    The 1st time you are nominated, if the nominator is a Townsfolk,
    they are executed immediately.
    """
    wake_pattern: ClassVar[WakePattern] = WakePattern.NEVER

    spent: bool = False

    def uneventful_nomination(
        self,
        state: State,
        nomination: events.UneventfulNomination,
        me: PlayerID,
    ) -> StateGen:
        virgin = state.players[nomination.player]
        nominator_is_tf = info.IsCategory(nomination.nominator, Townsfolk)(
            state, virgin.id
        )
        if (
            virgin.is_dead
            or self.spent
            or nominator_is_tf.not_true()
        ):
            self.spent = True
            if not nominator_is_tf.truth():
                state.math_misregistration(virgin.id)
            yield state
        elif self.is_droisoned(state, virgin.id):
            state.math_misregistration(virgin.id)
            self.spent = True
            yield state

    def execution_on_nomination(
        self,
        state: State,
        execution: events.ExecutionByST,
    ) -> StateGen:
        nominee = state.players[execution.after_nominating]
        virgin_ability = nominee.get_ability(Virgin)
        tf_nom = info.IsCategory(execution.player, Townsfolk)(state, nominee.id)

        if (
            nominee.is_dead
            or virgin_ability.is_droisoned(state, nominee.id)
            or virgin_ability.spent
            or tf_nom.is_false()
        ):
            return
        virgin_ability.spent = True
        if not tf_nom.truth():
            state.math_misregistration(nominee.id)

        executee = state.players[execution.player].character
        for ss in executee.executed(state, execution.player, execution.died):
            ss.players[execution.player].character.death_explanation = (
                'nominated Virgin'
            )
            yield ss

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

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        events_ = state.puzzle.day_events.get(state.day, [])
        if any(isinstance(ev, events.Execution) for ev in events_):
            yield state

    def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
        state.vortox = True

    def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
        state.vortox = False

@dataclass
class Xaan(Minion):
    """
    On night X, all Townsfolk are poisoned until dusk. [X Outsiders]
    """
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
        # The current ruling is that misregistration doesn't affect setup, so
        # the Xaan counts the real number of outsiders
        self.X = sum(
            isinstance(player.character, Outsider)
            for player in state.players
        )
        yield state

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        """
        On night X, create a world for every possible combination of poison
        targets (i.e., handle a Spy misregistering as a TF or not).
        """
        xaan = state.players[me]
        if (xaan.is_dead and not xaan.vigormortised) or state.night != self.X:
            self.targets = None
            yield state
            return

        townsfolk = [
            info.IsCategory(player, Townsfolk)(state, me)
            for player in state.player_ids
        ]
        maybes = [i for i, is_tf in enumerate(townsfolk) if is_tf.is_maybe()]
        trues = [i for i, is_tf in enumerate(townsfolk) if is_tf.is_true()]
        if self.is_droisoned(state, me) and trues:
            # This is a best-effort at maintining Mathematician count, but
            # technically should only really trigger if one of the targets
            # doesn't misfire tonight. See todo.md.
            state.math_misregistration(me)

        for maybe_subset in itertools.chain.from_iterable(
            itertools.combinations(maybes, r)
            for r in range(1, len(maybes) + 1)
        ):
            new_state = state.fork()
            new_xaan = new_state.players[me].get_ability(Xaan)
            new_xaan.targets = trues + maybe_subset
            new_xaan.maybe_activate_effects(new_state, me)
            yield new_state

        # No fork for most common case
        self.targets = trues
        self.maybe_activate_effects(state, me)
        yield state

    def end_day(self, state: State, me: PlayerID) -> StateGen:
        if self.targets is not None:
            self.maybe_deactivate_effects(state, me)
            self.targets = None
        yield state

    def _activate_effects_impl(self, state: State, me: PlayerID) -> None:
        if self.targets is not None:
            for target in self.targets:
                state.players[target].droison(state, me)

    def _deactivate_effects_impl(self, state: State, me: PlayerID) -> None:
        if self.targets is not None:
            for target in self.targets:
                state.players[target].undroison(state, me)

    def _world_str(self, state: State) -> str:
        return f'Xaan (X={self.X})'

@dataclass
class Zombuul(Demon):
    """TODO: Not implemented properly yet"""
    wake_pattern: ClassVar[WakePattern] = WakePattern.MANUAL

    registering_dead: bool = False

    def run_night(self, state: State, me: PlayerID) -> StateGen:
        raise NotImplementedError("TODO: Zombuul")


# https://script.bloodontheclocktower.com/data/nightsheet.json

GLOBAL_SETUP_ORDER = [
    Boffin,
    Atheist,
    Vortox,
    Marionette,
    NoDashii,
    Puzzlemaster,
    FortuneTeller,
    VillageIdiot,
    Lunatic,
    Progidy,
    Drunk,
    Soldier,
    Xaan,
    EvilTwin,  # Must go after any alignment changes
    LordOfTyphon,  # Goes last to check evils created by setup are in a line
]

GLOBAL_NIGHT_ORDER = [
    PoppyGrower,
    Philosopher,
    Xaan,
    Leviathan,
    Poisoner,
    Widow,
    Courtier,
    Gambler,
    Acrobat,
    SnakeCharmer,
    Monk,
    EvilTwin,  # Nasty hack - see todo.md
    Witch,
    Cerenovus,
    PitHag,
    ScarletWoman,
    Exorcist,
    Imp,
    Pukka,
    Po,
    FangGu,
    NoDashii,
    Vortox,
    LordOfTyphon,
    Vigormortis,
    Kazali,
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
    Flowergirl,
    Oracle,
    Seamstress,
    Juggler,
    Steward,
    Knight,
    Noble,
    Balloonist,
    Shugenja,
    VillageIdiot,
    Progidy,
    NightWatchman,
    Butler,  # OTHER_NIGHT position, on FIRST_NIGHT it's actually much earlier?
    Chambermaid,
    Mathematician,
]

GLOBAL_DAY_ORDER = [
    Riot,
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
    Boffin,
    Drunk,
    Goblin,
    Golem,
    Hermit,
    Lunatic,
    Marionette,
    Mayor,
    Politician,
    Princess,
    Recluse,
    Saint,
    Slayer,
    Soldier,
    Spy,
    Sweetheart,
    Virgin,
]
