import unittest

from clockchecker import *
import puzzles


def assert_solutions(
    testcase: unittest.TestCase,
    puzzle: Puzzle,
    solutions: tuple[tuple[Character, ...]],
):
    predictions = tuple(
        tuple(x.__name__ for x in world.initial_characters)
        for world in solve(puzzle)
    )
    solutions = tuple(
        tuple(x.__name__ for x in solution)
        for solution in solutions
    )
    testcase.assertEqual(sorted(predictions), sorted(solutions))



class NQTPuzzles(unittest.TestCase):
    """Solve all the NQT puzzles as integration tests."""

    def test_puzzles(self):
        all_puzzles = {
            puzzle_name: getattr(puzzles, puzzle_name)
            for puzzle_name in dir(puzzles)
            if puzzle_name.startswith('puzzle_')
        }
        print(f'Testing all {len(all_puzzles)} puzzles')

        for puzzle_name in all_puzzles:
            with self.subTest(msg=puzzle_name):
                print(f'\033[31;1m.', end='', flush=True)
                # print(puzzle_name)

                puzzle, solutions, condition = all_puzzles[puzzle_name]()
                worlds = list(solve(puzzle))

                prediction_str = sorted(tuple(
                    ', '.join(x.__name__ for x in world.initial_characters)
                    for world in worlds
                ))
                solution_str = sorted(tuple(
                    ', '.join(x.__name__ for x in solution)
                    for solution in solutions
                ))
                self.assertEqual(prediction_str, solution_str)

                if condition is not None:
                    for world in worlds:
                        self.assertTrue(condition(world))
                
                print('\033[32;1m\b✓', end='')
        print('\033[0m')


class TestRiot(unittest.TestCase):
    def test_minions_become_riot(self):
        A, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('A', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Riot) & IsCharacter(D, Goblin)),
                }),
                Player('B', claim=Undertaker),
                Player('C', claim=Investigator, night_info={
                    1: Investigator.Ping(D, A, Goblin)
                }),
                Player('D', claim=Empath, night_info={
                    1: Empath.Ping(1),
                    1: Empath.Ping(1),
                }),
            ],
            day_events={3: Dies(player=C, after_nominated_by=B)},
            night_deaths={},
            hidden_characters=[Riot, Goblin],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Undertaker, Riot, Goblin),
        ))

    def test_minions_not_riot_day_2(self):
        A, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('A', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(D, Riot) & IsCharacter(C, Goblin)),
                }),
                Player('B', claim=Slayer, day_info={
                    2: Slayer.Shot(C, died=True),
                }),
                Player('C', claim=Investigator, night_info={
                    1: Investigator.Ping(D, A, Goblin)
                }),
                Player('D', claim=Empath, night_info={
                    1: Empath.Ping(1),
                    1: Empath.Ping(1),
                }),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Riot, Goblin],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=())

    def test_recluse_can_become_riot(self):
        A, B, C, D, E = range(5)
        puzzle = Puzzle(
            players=[
                Player('A', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Riot) & IsCharacter(D, Goblin)),
                }),
                Player('B', claim=Slayer, day_info={
                    3: Slayer.Shot(C, died=True),
                }),
                Player('C', claim=Investigator, night_info={
                    1: Investigator.Ping(D, A, Goblin)
                }),
                Player('D', claim=Empath, night_info={
                    1: Empath.Ping(1),
                    1: Empath.Ping(1),
                }),
                Player('E', claim=Recluse),
            ],
            day_events={1: Execution(D)},
            night_deaths={},
            hidden_characters=[Riot, Goblin],
            hidden_self=[],
            category_counts=(2, 1, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Slayer, Riot, Goblin, Recluse),
        ))
