"""Functionality for generating all starting player configurations."""

from collections import Counter
from collections.abc import Iterator
from copy import copy
from dataclasses import dataclass
import itertools as it
import os
import traceback
from typing import Callable, Sequence, Sequence

from . import core
from . import characters
from . import info
from .characters import Character
from .core import Puzzle, State, StateGen

try:
    from multiprocessing import Queue, Process
    MULTIPROCESSING_AVAILABLE = True
except ModuleNotFoundError:
    MULTIPROCESSING_AVAILABLE = False


@dataclass
class StartingConfiguration:
    """
    Convenient container of everything you need (in addition to the puzzle)
    to describe the initial assignment of characters and behaviours to players
    (i.e. roughly the post-token-draw, pre-setup state) ready for solving.
    """
    liar_characters: tuple[type[Character]]
    liar_positions: tuple[int, ...]
    speculative_evil_positions: tuple[int, ...]
    speculative_good_positions: tuple[int, ...]
    debug_key: tuple[int, ...]


def _starting_config_gen(puzzle: Puzzle) -> Iterator[StartingConfiguration]:
    """Generate all possible initial configurations of player roles."""
    max_speculative_liars = min(
        _max_speculative_evil_from_script(puzzle.script),
        puzzle.max_speculation,
    )
    _, _, n_minions, n_demons = puzzle.category_counts
    liar_combinations = it.product(
        it.combinations(puzzle.demons, n_demons),
        it.chain(*[
            it.combinations(puzzle.minions, i)
            for i in range(n_minions, len(puzzle.minions) + 1)
        ]),
        it.chain(*[
            it.combinations(puzzle.hidden_good, i)
            for i in range(len(puzzle.hidden_good) + 1)
        ]),
        it.chain(*[
            it.combinations(puzzle.speculative_liars, i)
            for i in range(
                min(max_speculative_liars, len(puzzle.speculative_liars)) + 1
            )
        ])
    )
    player_ids = list(range(len(puzzle.players)))
    dbg_idx = 0
    for demons, minions, hidden_good, speculations in liar_combinations:
        liars = demons + minions + hidden_good + speculations
        for liar_positions in it.permutations(player_ids, len(liars)):
            existing_spec_pos = liar_positions[len(liars)-len(speculations):]
            for other_spec_pos in it.chain(*[
                it.permutations(player_ids, i)
                for i in range(max_speculative_liars + 1 - len(speculations))
            ]):
                if any(i in existing_spec_pos for i in other_spec_pos):
                    continue
                spec_pos = existing_spec_pos + other_spec_pos
                config = StartingConfiguration(
                    liar_characters=liars,
                    liar_positions=liar_positions,
                    speculative_evil_positions=spec_pos,
                    speculative_good_positions=(),
                    debug_key=(dbg_idx,),
                )
                if _check_valid_character_counts(puzzle, config):
                    yield config
                    dbg_idx += 1


def _max_speculative_evil_from_script(script: Sequence[type[Character]]) -> int:
    """
    Compute the maximum number of players who might need to be
    'speculativly evil', i.e., they lie from the begining of the game because
    they end up as evil.
    """
    total = 0
    total += characters.FangGu in script  # FangGu jumps to a good player
    total += characters.SnakeCharmer in script  # SC charms a demon
    # TODO: Mezepheles
    return total

def _max_speculative_evil_from_config(
    play: Sequence[type[Character]],
    puzzle: Puzzle,
) -> int:
    """Max speculative evils for a given set of in-play characters"""
    total = 0

    pithag_possible = characters.PitHag in play  # No alchemist yet
    fanggu_possible = (
        characters.FangGu in play
        or (pithag_possible and characters.FangGu in puzzle.script)
    )
    outsiders_possible = (
        any(issubclass(c, characters.Outsider) for c in play)
        or (
            pithag_possible
            and any(issubclass(c, characters.Outsider) for c in puzzle.script)
        )
    )
    snakecharmer_possible = (
        characters.SnakeCharmer in play
        or (pithag_possible and characters.SnakeCharmer in puzzle.script)
    )
    total += fanggu_possible and outsiders_possible
    total += snakecharmer_possible
    # TODO: Mezepheles, mid-game BountyHunter etc.
    return total


def _check_valid_character_counts(
    puzzle: Puzzle,
    config: StartingConfiguration,
) -> bool:
    """Check that the starting player token counts are legal."""
    setup = [p.claim for p in puzzle.players]
    for liar, position in zip(config.liar_characters, config.liar_positions):
        setup[position] = liar
        if (
            position == 0 and puzzle.player_zero_is_you
            and liar not in puzzle.hidden_self
        ):
            return False
    # TODO: Clean up speculative liar generation, it is rubbish.
    if puzzle.player_zero_is_you and 0 in config.speculative_evil_positions:
        return False
    max_speculation = _max_speculative_evil_from_config(setup, puzzle)
    if len(config.speculative_evil_positions) > max_speculation:
        return False

    T, O, M, D = puzzle.category_counts
    bounds = ((T, T), (O, O), (M, M), (D, D))
    for character in setup:
        bounds = character.modify_category_counts(bounds)
    actual_counts = Counter(character.get_category() for character in setup)

    for (lo, hi), category in zip(bounds, characters.ALL_CATEGORIES):
        if not lo <= actual_counts[category] <= hi:
            return False
    if (
        not puzzle.allow_duplicate_tokens_in_bag
        and len(set(setup)) != len(setup)
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
    for round_ in range(1, puzzle._max_night + 1):
        # NIGHT
        for _ in range(len(puzzle.night_order)):
            worlds = _apply_all(worlds, lambda w: w.run_next_character())
        worlds = _apply_all(worlds, lambda w: w.end_night())
        if round_ <= puzzle._max_day:
            # DAY
            for _ in range(len(puzzle.day_order)):
                worlds = _apply_all(worlds, lambda w: w.run_next_character())
            for event in range(puzzle.event_counts[round_]):
                worlds = _apply_all(
                    worlds, lambda w, r=round_, e=event: w.run_event(r, e))
            if round_ < puzzle._max_day or puzzle.finish_final_day:
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
    for player in state.players:
        if hasattr(player, 'speculative_evil'):
            del player.speculative_evil
            if not info.behaves_evil(state, player.id):
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
                redo_config.debug_key = state.debug_key
                core._DEBUG_STATE_FORK_COUNTS[redo_config.debug_key] = 0
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

    if core._PROFILING:
        core.summarise_profiling()

# ------------------------------ THREADING ------------------------------ #

def _world_checking_worker(puzzle: Puzzle, liars_q: Queue, solutions_q: Queue):
    puzzle.unserialise_extra_state()
    def liars_gen():
        while (liars := liars_q.get()) is not None:
            yield liars
    try:
        for solution in _world_check_gen(puzzle, liars_gen()):
            solutions_q.put(solution)
    except Exception as e:
        solutions_q.put(traceback.format_exc())
    if core._PROFILING:
        solutions_q.put(core._PROFILING_FORK_LOCATIONS)
    solutions_q.put(None)  # Finished Sentinel

def _starting_config_worker(puzzle: Puzzle, liars_q: Queue, num_procs: int):
    for config in _starting_config_gen(puzzle):
        liars_q.put(config)
    for _ in range(num_procs):
        liars_q.put(None)  # Finished Sentinel

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
        configs = _starting_config_gen(puzzle)
        solutions = _world_check_gen(puzzle, configs)
        solutions = _filter_solutions(puzzle, solutions)
        yield from solutions
        return

    # Parallel version
    liars_queue = Queue(maxsize=num_processes)
    solutions_queue = Queue(maxsize=num_processes)

    all_workers = [
        Process(
            target=_world_checking_worker,
            daemon=True,
            args=(puzzle, liars_queue, solutions_queue)
        )
        for _ in range(num_processes)
    ]
    all_workers.append(
        Process(
            target=_starting_config_worker,
            daemon=True,
            args=(puzzle, liars_queue, num_processes)
        )
    )

    for worker in all_workers:
        worker.start()

    solutions = _solution_collecting_worker(solutions_queue, num_processes)
    yield from _filter_solutions(puzzle, solutions)

    for worker in all_workers:
        worker.join()


def _apply_all(states: StateGen, fn: Callable[[State], StateGen]) -> StateGen:
    """
    Utility for calling a state-generating function on all states in a StateGen.
    """
    for state in states:
        if hasattr(state, 'cull_branch'):
            continue
        yield from fn(state)