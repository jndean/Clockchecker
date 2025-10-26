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
    speculative_evil_positions: tuple[PlayerID, ...] | None
    speculative_good_positions: tuple[PlayerID, ...]
    debug_key: tuple[int, ...]

    def get_characters(self, puzzle: Puzzle):
        chars = [p.claim for p in puzzle.players]
        for liar, position in zip(self.liar_characters, self.liar_positions):
            chars[position] = liar
        return chars



def _place_hidden_characters(puzzle: Puzzle) -> ConfigGen:
    """Generate all possible initial configurations of player roles."""
    _, _, num_minions, num_demons = puzzle.category_counts
    num_speculative_liars =_max_speculative_evil_from_puzzle(puzzle)
    liar_combinations = it.product(
        it.combinations(puzzle.demons, num_demons),
        it.chain(*[
            it.combinations(puzzle.minions, i)
            for i in range(num_minions, len(puzzle.minions) + 1)
        ]),
        it.chain(*[
            it.combinations(puzzle.hidden_good, i)
            for i in range(len(puzzle.hidden_good) + 1)
        ]),
        it.chain(*[
            it.combinations(puzzle.speculative_liars, i)
            for i in range(
                1 + min(num_speculative_liars, len(puzzle.speculative_liars))
            )
        ])
    )
    player_ids = list(range(len(puzzle.players)))
    dbg_idx = 0
    for demons, minions, hidden_good, speculative_evil in liar_combinations:
        liars = demons + minions + hidden_good + speculative_evil
        for liar_pos in it.permutations(player_ids, len(liars)):
            spec_evil_pos = liar_pos[len(liars) - len(speculative_evil):]
            config = StartingConfiguration(
                liar_characters=liars,
                liar_positions=liar_pos,
                speculative_evil_positions=spec_evil_pos,
                speculative_good_positions=(),
                debug_key=(dbg_idx,),
            )
            if _check_token_counts(puzzle, config.get_characters(puzzle)):
                if core._PROFILING:
                    core.record_fork_caller((), 0)
                yield from _speculate_evil_players(puzzle, config)
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

def _speculate_evil_players(
    puzzle: Puzzle,
    config: StartingConfiguration,
) -> ConfigGen:
    """
    While `_hidden_character_placement` will place hidden characters that might
    become evil (like outsiders in a FangGu game) and mark them as speculatively
    evil, we may still need to generate possibilities of players being
    speculatively evil because of a character type they didn't start as (e.g.
    they might get Pit-Hag'd into an outsider later). This function is a lot
    more individual-character-aware than the approach taken elsewere in the
    solver, because naive speculation of evils can make even simple puzzles slow
    so it is worth hard-coding some game-knowledge into generating as few
    possibilities as we can.
    """
    play = config.get_characters(puzzle)
    max_spec = _max_speculative_evil_from_config(play, puzzle)
    remaining_spec = max_spec - len(config.speculative_evil_positions)
    if not remaining_spec:
        yield config; return

    outsiders_in_script = any(issubclass(c, characters.Outsider) for c in puzzle.script)
    pithag_possible = characters.PitHag in play  # TODO: Alchemist
    fanggu_possible = (
        characters.FangGu in play
        or (pithag_possible and characters.FangGu in puzzle.script)
    )
    # TODO: Barber
    # outsider_in_play = any(issubclass(c, characters.Outsider) for c in play)
    # barber_possible = (
    #     characters.Barber in play
    #     or (
    #         characters.Barber in puzzle.script and (
    #             pithag_possible or evil_philosopher_possible
    #         )
    #     )
    # )
    anyone_becomes_outsider = (
        (pithag_possible and outsiders_in_script)
        # or (barber_possible and outsider_in_play)
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

    speculation_candidates = []
    for pid, character in enumerate(play):
        if pid in config.speculative_evil_positions:
            continue
        i_can_be_fanggu_jumped = fanggu_possible and (
            anyone_becomes_outsider
            or issubclass(character, characters.Outsider)
        )
        i_can_be_snakecharmer = (
            anyone_becomes_snakecharmer
            or issubclass(character, characters.SnakeCharmer)
            or (
                issubclass(character, characters.Philosopher)
                and characters.SnakeCharmer in puzzle.script
            )
        )
        if i_can_be_fanggu_jumped or i_can_be_snakecharmer:
            speculation_candidates.append(pid)

    dbg_idx = 0
    for speculation_pos in it.chain(*[
        it.combinations(speculation_candidates, i)
        for i in range(remaining_spec + 1)
    ]):
        if core._PROFILING:
            core.record_fork_caller(config.debug_key, 0)
        new_config = copy(config)
        new_config.speculative_evil_positions += speculation_pos
        new_config.debug_key += (dbg_idx,)
        yield new_config
        dbg_idx += 1


def _max_speculative_evil_from_puzzle(puzzle: Puzzle) -> int:
    """
    Compute the maximum number of players who might need to be
    'speculativly evil', i.e., they lie from the begining of the game because
    they end up as evil.
    """
    total = 0
    total += characters.FangGu in puzzle.script  # FangGu jumps to a good player
    total += characters.SnakeCharmer in puzzle.script  # SC charms a demon
    # TODO: Mezepheles
    total = min(total, puzzle.max_speculation)
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

    total = min(total, puzzle.max_speculation)
    return total


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
    for config in  _place_hidden_characters(puzzle):
        liars_q.put(config)
    for _ in range(num_procs):
        liars_q.put(None)  # Finished Sentinel
    if core._PROFILING:
        liars_q.put(core._PROFILING_FORK_LOCATIONS)

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

        if core._PROFILING:
            core._PROFILING_FORK_LOCATIONS += liars_queue.get()

    core.summarise_fork_profiling()


def _apply_all(states: StateGen, fn: Callable[[State], StateGen]) -> StateGen:
    """
    Utility for calling a state-generating function on all states in a StateGen.
    """
    for state in states:
        if hasattr(state, 'cull_branch'):
            continue
        yield from fn(state)