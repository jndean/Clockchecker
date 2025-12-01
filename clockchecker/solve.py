"""Functionality for generating all starting player configurations."""

from collections import Counter
from collections.abc import Iterator
from copy import copy
from dataclasses import dataclass
import itertools as it
import os
import traceback
from typing import Callable, Sequence, Sequence, TypeAlias

from . import core
from . import characters
from . import info
from .characters import Character
from .core import PlayerID, Puzzle, State, StateGen

try:
    from multiprocessing import Queue, Process
    MULTIPROCESSING_AVAILABLE = True
except ModuleNotFoundError:
    MULTIPROCESSING_AVAILABLE = False


ConfigGen: TypeAlias = Iterator['StartingConfiguration']

@dataclass
class StartingConfiguration:
    """
    Convenient container of everything you need (in addition to the puzzle)
    to describe the initial assignment of characters and behaviours to players
    (i.e. roughly the post-token-draw, pre-setup state) ready for solving.
    """
    liar_characters: tuple[type[Character], ...]
    liar_positions: tuple[PlayerID, ...]
    speculative_evil_positions: tuple[PlayerID, ...]
    speculative_good_positions: tuple[PlayerID, ...]
    speculative_ceremad_positions: tuple[PlayerID, ...]
    debug_key: tuple[int, ...]

    def get_characters(self, puzzle: Puzzle):
        # TODO: once speculation funcs have been factored out into one place,
        # this can just be computed once there
        chars = [p.claim for p in puzzle.players]
        for liar, position in zip(self.liar_characters, self.liar_positions):
            chars[position] = liar
        return chars

def _place_hidden_characters(puzzle: Puzzle) -> ConfigGen:
    """Generate all possible initial configurations of player roles."""
    _, _, num_minions, num_demons = puzzle.category_counts
    (
        max_speculative_evil,
        speculative_evil_characters,
        max_speculative_ceremad,
        speculative_ceremad_characters
    ) = _speculative_lying_starting_characters(puzzle)
    liar_combinations = it.product(
        it.chain(*[
            it.combinations(puzzle.demons, i)
            for i in range(
                max(0, num_demons - max_speculative_ceremad - max_speculative_evil),
                num_demons + 1,
            )
        ]),
        it.chain(*[
            it.combinations(puzzle.minions, i)
            for i in range(num_minions, len(puzzle.minions) + 1)
        ]),
        it.chain(*[
            it.combinations(puzzle.hidden_good, i)
            for i in range(len(puzzle.hidden_good) + 1)
        ]),
        it.chain(*[
            it.combinations(speculative_evil_characters, i)
            for i in range(max_speculative_evil + 1)
        ]),
        it.chain(*[
            it.combinations(speculative_ceremad_characters, i)
            for i in range(max_speculative_ceremad + 1)
        ])
    )
    player_ids = list(range(len(puzzle.players)))
    dbg_idx = 0
    for demons, minions, hidden_good, spec_evil, spec_mad in liar_combinations:
        liars = demons + minions + hidden_good + spec_evil + spec_mad
        l, e, m = len(liars), len(spec_evil), len(spec_mad)
        if e + m > puzzle.max_speculation:
            continue
        spec_evil_slice = slice(l - e - m, l - m)
        spec_mad_slice = slice(l - m, l)
        for liar_pos in it.permutations(player_ids, len(liars)):
            spec_evil_pos = liar_pos[spec_evil_slice]
            spec_mad_pos = liar_pos[spec_mad_slice]
            config = StartingConfiguration(
                liar_characters=liars,
                liar_positions=liar_pos,
                speculative_evil_positions=spec_evil_pos,
                speculative_ceremad_positions=spec_mad_pos,
                speculative_good_positions=(),
                debug_key=(dbg_idx,),
            )
            in_play = config.get_characters(puzzle)
            if _check_token_counts(puzzle, in_play):
                facts = _facts_for_speculation(puzzle, in_play)
                for subconf in _speculate_evil_good_evil(puzzle, config, facts):
                    if _check_speculation(puzzle, subconf, in_play, facts):
                        if core._PROFILING:
                            core.record_fork_caller((), 0)
                        yield subconf
                        dbg_idx += 1

def _speculative_lying_starting_characters(puzzle: Puzzle) -> tuple[
    int, list[type[Character]], int, list[type[Character]],
]:
    """Determine which characters could lying be at the start of the game."""
    evil_liars = set()
    max_speculative_evil = 0
    pithag_on_script = characters.PitHag in puzzle.script
    fanggu_on_script = characters.FangGu in puzzle.script
    snakecharmer_on_script = characters.SnakeCharmer in puzzle.script
    cerenovus_on_script = characters.Cerenovus in puzzle.script
    philo_on_script = characters.Philosopher in puzzle.script
    good_on_script = [
        c for c in puzzle.script
        if not issubclass(c, (characters.Minion, characters.Demon))
    ]
    outsiders_on_script = [
        character for character in puzzle.script
        if issubclass(character, characters.Outsider)
    ]
    some_good_character_can_become_evil = (
        snakecharmer_on_script
        or (fanggu_on_script and outsiders_on_script)
    )
    if pithag_on_script and some_good_character_can_become_evil:
        evil_liars.update(good_on_script)
    if fanggu_on_script:
        max_speculative_evil += 1
        evil_liars.update(outsiders_on_script)
    if snakecharmer_on_script:
        max_speculative_evil += 1
        evil_liars.add(characters.SnakeCharmer)
        if philo_on_script:
            evil_liars.add(characters.Philosopher)

    ceremad_liars = puzzle.script if cerenovus_on_script else []
    # Sort for determinism
    evil_liars = list(sorted(list(evil_liars), key=lambda c: c.__name__))
    return (
        max_speculative_evil,
        evil_liars,
        int(cerenovus_on_script),
        ceremad_liars,
    )

def _speculate_evil_good_evil(
    puzzle: Puzzle,
    config: StartingConfiguration,
    facts: dict[str, int],
) -> ConfigGen:
    """
    Speculate on a case that will not be covered by regular hidden character
    placement and speculation: starting evils who turn good then turn evil again
    """
    existing_speculation = (
        config.speculative_evil_positions + config.speculative_ceremad_positions
    )
    max_extra_speculation = min(
        puzzle.max_speculation - len(existing_speculation),
        1,
    )
    evil_good_evil_possible = (
        facts['starting_evil_can_turn_good'] and facts['anyone_becomes_evil']
    )
    if max_extra_speculation <= 0 or not evil_good_evil_possible:
        # No extra speculation required
        yield config
        return

    starting_evils = [
        player for player in config.liar_positions
        if player not in existing_speculation
    ]
    dbg_idx = 0
    for extra_speculation in it.chain(*[
        it.combinations(starting_evils, i)
        for i in range(max_extra_speculation + 1)
    ]):
        if core._PROFILING:
            core.record_fork_caller(config.debug_key, 0)
        new_config = copy(config)
        new_config.speculative_evil_positions += extra_speculation
        new_config.debug_key += (dbg_idx, )
        if core._PROFILING:
            core.record_fork_caller(config.debug_key, 0)

        yield new_config
        dbg_idx += 1


def _check_token_counts(
    puzzle: Puzzle,
    in_play: Sequence[type[Character]],
) -> bool:
    """Check the list of starting characters is legal."""
    if (
        puzzle.player_zero_is_you
        and in_play[0] not in puzzle.hidden_self
        and in_play[0] is not puzzle.players[0].claim
    ):
        return False
    T, O, M, D = puzzle.category_counts
    bounds = ((T, T), (O, O), (M, M), (D, D))
    for character in in_play:
        bounds = character.modify_category_counts(bounds)
    actual_counts = Counter(c.get_category() for c in in_play)

    for (lo, hi), category in zip(bounds, characters.ALL_CATEGORIES):
        if not lo <= actual_counts[category] <= hi:
            return False
    if (
        not puzzle.allow_duplicate_tokens_in_bag
        and len(set(in_play)) != len(in_play)
    ):
        return False
    return True

def _facts_for_speculation(
    puzzle: Puzzle,
    in_play: list[type[Character]],
) -> dict[str, bool]:
    """
    Compute a set of facts about a game that are useful for speculating on what
    might happen in the game, particularly who might change role/alignment.
    """
    pithag_possible = characters.PitHag in in_play  # TODO: Alchemist
    outsiders_in_script = any(
        issubclass(c, characters.Outsider) for c in puzzle.script)
    outsiders_possible = (
        any(issubclass(c, characters.Outsider) for c in in_play)
        or (pithag_possible and outsiders_in_script)
    )
    fanggu_possible = (
        characters.FangGu in in_play
        or (pithag_possible and characters.FangGu in puzzle.script)
    )
    cerenovus_possible = (  # TODO: Alchemist
        characters.Cerenovus in in_play
        or (pithag_possible and characters.Cerenovus in puzzle.script)
    )
    philo_possible = (
        characters.Philosopher in in_play
        or (pithag_possible and characters.Philosopher in puzzle.script)
    )
    snakecharmer_possible = (
        characters.SnakeCharmer in in_play
        or (
            characters.SnakeCharmer in puzzle.script
            and (pithag_possible or philo_possible)
        )
    )
    minions_can_become_demons = pithag_possible
    starting_demons_can_turn_good = snakecharmer_possible
    starting_minions_can_turn_good = (
        minions_can_become_demons and snakecharmer_possible
    )
    starting_evil_can_turn_good = (
        starting_minions_can_turn_good or starting_demons_can_turn_good
    )
    # TODO: Barber
    # outsiders_in_play = any(issubclass(c, characters.Outsider) for c in play)
    # barber_possible = (
    #     characters.Barber in play
    #     or (
    #         characters.Barber in puzzle.script
    #         and (pithag_possible or evil_philosopher_possible)))
    anyone_becomes_outsider = (
        (pithag_possible and outsiders_in_script)
        # or (barber_possible and outsiders_in_play)
    )
    anyone_becomes_philo = (
        (pithag_possible and characters.Philosopher in puzzle.script)
        # or (barber_possible and characters.Philosopher in play)
    )
    anyone_becomes_snakecharmer = (
        (
            characters.SnakeCharmer in puzzle.script
            and (pithag_possible or anyone_becomes_philo)
        )
        # or (barber_possible and characters.SnakeCharmer in play)
    )
    anyone_becomes_evil = (
        (anyone_becomes_outsider and fanggu_possible)
        or anyone_becomes_snakecharmer
    )
    return {
        'cerenovus_possible': cerenovus_possible,
        'fanggu_possible': fanggu_possible,
        'snakecharmer_possible': snakecharmer_possible,
        'outsiders_possible':outsiders_possible,
        'anyone_becomes_outsider': anyone_becomes_outsider,
        'anyone_becomes_philo': anyone_becomes_philo,
        'anyone_becomes_snakecharmer': anyone_becomes_snakecharmer,
        'starting_minions_can_turn_good': starting_minions_can_turn_good,
        'starting_demons_can_turn_good': starting_demons_can_turn_good,
        'starting_evil_can_turn_good': starting_evil_can_turn_good,
        'anyone_becomes_evil': anyone_becomes_evil,
    }

def _check_speculation(
    puzzle: Puzzle,
    config: StartingConfiguration,
    in_play: list[type[Character]],
    facts: dict[str, int],
):
    """Reject worlds with invalid speculation, just for improved efficiency."""
    if puzzle.player_zero_is_you and (
            0 in config.speculative_ceremad_positions
            or 0 in config.speculative_evil_positions
    ):
        return False
    if (
        config.speculative_ceremad_positions
        and not facts['cerenovus_possible']
    ):
        return False
    fanggu_used = False
    for pid in config.speculative_evil_positions:
        character = in_play[pid]
        i_can_be_fanggu_jumped = (
            facts['fanggu_possible']
            and not fanggu_used
            and (
                issubclass(character, characters.Outsider)
                or facts['anyone_becomes_outsider']
        ))
        i_can_be_snakecharmer = (
            character is characters.SnakeCharmer
            or facts['anyone_becomes_snakecharmer']
            or (
                character is characters.Philosopher
                and characters.SnakeCharmer in puzzle.script
            )
        )
        fanggu_used |= i_can_be_fanggu_jumped and not i_can_be_snakecharmer
        if (
            not i_can_be_fanggu_jumped
            and not i_can_be_snakecharmer
        ):
            return False
    return True


def _world_check(puzzle: Puzzle, config: StartingConfiguration) -> StateGen:
    """
    Given a description of an initial game configuration, simulate all choices
    and yield those worlds that fit the puzzle constraints.
    """
    # Create the world and place the hidden characters
    world = puzzle.state_template.fork(config.debug_key)
    for liar, position in zip(config.liar_characters, config.liar_positions):
        world.players[position].character = liar()
        world.players[position].is_evil = issubclass(
            liar, (characters.Minion, characters.Demon)
        )
        world.players[position].ever_behaved_evil = info.behaves_evil(
            world, position
        )
    for position in config.speculative_evil_positions:
        world.players[position].speculative_evil = True
    for position in config.speculative_good_positions:
        world.players[position].speculative_good = True
    for position in config.speculative_ceremad_positions:
        world.players[position].speculative_ceremad = True
    if not world.begin_game(puzzle.allow_duplicate_tokens_in_bag):
        return

    # Chains together a big ol' stack of generators corresponding to each
    # possible action of each player, forming a pipeline through which
    # possible world states flow. Only valid worlds are able to reach the
    # end of the pipe.

    # SETUP
    worlds = [world]
    for _ in range(len(puzzle.setup_order)):
        worlds = _apply_all(worlds, lambda w: w.run_next_character())
    worlds = _apply_all(worlds, lambda w: w.end_setup())
    for round_ in range(1, puzzle.max_night + 1):
        # NIGHT
        for _ in range(len(puzzle.night_order)):
            worlds = _apply_all(worlds, lambda w: w.run_next_character())
        worlds = _apply_all(worlds, lambda w: w.end_night())
        if round_ <= puzzle.max_day:
            # DAY
            for _ in range(len(puzzle.day_order)):
                worlds = _apply_all(worlds, lambda w: w.run_next_character())
            for event in range(puzzle.event_counts[round_]):
                worlds = _apply_all(
                    worlds, lambda w, r=round_, e=event: w.run_event(r, e))
            if round_ < puzzle.max_day or puzzle.finish_final_day:
                worlds = _apply_all(worlds, lambda w: w.end_day())

    # ROUND ROBIN
    worlds = _apply_all(worlds, lambda w: _round_robin(w, config))
    yield from worlds


def _round_robin(state: State, config: StartingConfiguration) -> StateGen:
    """
    Called once simulating of nights and days has finished, i.e., when the
    players do their final round robin. At this point, any speculative evils
    must have become 'concrete' evils, otherwise the speculation was
    incorrect. Moreover, for any player who is now good but ever had the
    capacity to lie, we must resimulate the world with the extra condition
    that they must never have taken the opportunity to lie.
    """
    state.log('[ROUND ROBIN]')

    for player in state.players:
        if hasattr(player, 'speculative_evil'):
            del player.speculative_evil
            if not info.behaves_evil(state, player.id):
                return
        if hasattr(player, 'speculative_ceremad'):
            if not getattr(player, 'ceremad', 0):
                return

    if not any(hasattr(p, 'speculative_good') for p in state.players):
        speculative_good = [
            pid
            for pid, player in enumerate(state.players)
            if player.ever_behaved_evil and not info.behaves_evil(state, pid)
        ]
        if speculative_good:
            redo_config = copy(config)
            redo_config.speculative_good_positions = speculative_good
            if core._DEBUG:
                redo_config.debug_key = state.debug_key + (
                    core._DEBUG_STATE_FORK_COUNTS[state.debug_key],)
                core._DEBUG_STATE_FORK_COUNTS[state.debug_key] += 1
            if core._PROFILING:
                core.record_fork_caller(state.debug_key, 0)
            yield from _world_check(state.puzzle, redo_config)
            return
    yield state


def _world_check_gen(
    puzzle: Puzzle,
    config_gen: Iterator[StartingConfiguration]
) -> StateGen:
    """Run _world_check on all starting configurations."""
    if core._DEBUG:
        core._DEBUG_STATE_FORK_COUNTS.clear()
    if core._PROFILING:
        core._PROFILING_FORK_LOCATIONS.clear()

    for config in config_gen:
        yield from _world_check(puzzle, config)


def _filter_solutions(puzzle: Puzzle, solutions: StateGen) -> StateGen:
    """
    Filter solutions, e.g., deduplicating by identical starting characters.
    """
    any_solution_found = False

    if puzzle.deduplicate_initial_characters:
        seen_solutions = set()
        for solution in solutions:
            key = solution.initial_characters + tuple(
                type(p.character) for p in solution.players
            )
            if key not in seen_solutions:
                seen_solutions.add(key)
                yield solution
        any_solution_found = bool(seen_solutions)
    else:
        for solution in solutions:
            yield solution
            any_solution_found = True

    if not any_solution_found:
        atheist_state = puzzle.state_template.fork(fork_id=(-1,))
        atheist_state.begin_game(True)
        if any(p.has_ability(characters.Atheist) for p in atheist_state.players):
            yield atheist_state


# ------------------------------ THREADING ------------------------------ #

def _world_checking_worker(puzzle: Puzzle, config_q: Queue, solutions_q: Queue):
    puzzle.unserialise_extra_state()
    def liars_gen():
        while (liars := config_q.get()) is not None:
            yield liars
    try:
        for solution in _world_check_gen(puzzle, liars_gen()):
            solutions_q.put(solution)
    except Exception as e:
        solutions_q.put(traceback.format_exc())
    if core._PROFILING:
        solutions_q.put(core._PROFILING_FORK_LOCATIONS)
    solutions_q.put(None)  # Finished Sentinel

def _starting_config_worker(puzzle: Puzzle, config_q: Queue, num_procs: int):
    for config in  _place_hidden_characters(puzzle):
        config_q.put(config)
    for _ in range(num_procs):
        config_q.put(None)  # Finished Sentinel
    if core._PROFILING:
        config_q.put(core._PROFILING_FORK_LOCATIONS)

def _solution_collecting_worker(solutions_q: Queue, num_procs: int) -> StateGen:
    finish_count = 0
    err_str = None
    while True:
        recvd = solutions_q.get()
        if isinstance(recvd, State):
            yield recvd
        elif isinstance(recvd, Counter) and core._PROFILING:
            core._PROFILING_FORK_LOCATIONS += recvd
        else:  # Finished. Maybe sentinel, maybe error
            if recvd is not None:
                err_str = recvd
            finish_count += 1
            if finish_count == num_procs:
                break
    if err_str is not None:
        exc = RuntimeError('Exception during solve, see below')
        exc.add_note(f'\n{err_str}')
        raise exc


def solve(puzzle: Puzzle, num_processes=None) -> StateGen:
    """Top level solver method, accepts a puzzle and generates solutions."""

    if num_processes is None:
        num_processes = int(os.environ.get('NUM_PROC', os.cpu_count()))

    if num_processes == 1 or not MULTIPROCESSING_AVAILABLE:
        # Non-parallel version just runs everything in one process.
        configs = _place_hidden_characters(puzzle)
        solutions = _world_check_gen(puzzle, configs)
        solutions = _filter_solutions(puzzle, solutions)
        yield from solutions
    else:
        # Parallel version
        config_queue = Queue(maxsize=num_processes)
        solutions_queue = Queue(maxsize=num_processes)

        all_workers = [
            Process(
                target=_world_checking_worker,
                daemon=True,
                args=(puzzle, config_queue, solutions_queue)
            )
            for _ in range(num_processes)
        ]
        all_workers.append(
            Process(
                target=_starting_config_worker,
                daemon=True,
                args=(puzzle, config_queue, num_processes)
            )
        )

        for worker in all_workers:
            worker.start()

        solutions = _solution_collecting_worker(solutions_queue, num_processes)
        yield from _filter_solutions(puzzle, solutions)

        for worker in all_workers:
            worker.join()

        if core._PROFILING:
            core._PROFILING_FORK_LOCATIONS += config_queue.get()

    core.summarise_fork_profiling()


def solve_and_print(puzzle: Puzzle, num_processes=None) -> None:
    # Convenience function, because I often find myself wanting to quickly
    # insert a loop like this in the middle of a test.
    for solution in solve(puzzle, num_processes=num_processes):
        print(solution)


def _apply_all(states: StateGen, fn: Callable[[State], StateGen]) -> StateGen:
    """
    Utility for calling a state-generating function on all states in a StateGen.
    """
    for state in states:
        if hasattr(state, 'cull_branch'):
            continue
        yield from fn(state)
