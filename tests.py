import unittest

import clockchecker
import puzzles



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

                puzzle, solutions, condition = all_puzzles[puzzle_name]()
                with clockchecker.Solver() as solver:
                    worlds = list(solver.generate_worlds(puzzle))

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
