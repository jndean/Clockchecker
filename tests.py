from copy import deepcopy
import unittest

from clockchecker import *
import puzzles


def assert_solutions(
    testcase: unittest.TestCase,
    puzzle: Puzzle,
    solutions: tuple[tuple[Character, ...]],
    conditions: Info| None = None,
):
    predictions = list(solve(puzzle))
    prediction_chars = tuple(
        tuple(x.__name__ for x in world.initial_characters)
        for world in predictions
    )
    solutions_chars = tuple(
        tuple(x.__name__ for x in solution)
        for solution in solutions
    )
    testcase.assertEqual(sorted(prediction_chars), sorted(solutions_chars))
    if conditions is not None:
        for prediction in predictions:
            testcase.assertIsNot(conditions(prediction, 0), FALSE)


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

                test_def = all_puzzles[puzzle_name]()
                worlds = list(
                    test_def.solve_override
                    if test_def.solve_override is not None
                    else solve(test_def.puzzle)
                )

                prediction_str = sorted(tuple(
                    ', '.join(x.__name__ for x in world.initial_characters)
                    for world in worlds
                ))
                solution_str = sorted(tuple(
                    ', '.join(x.__name__ for x in solution)
                    for solution in test_def.solutions
                ))
                self.assertEqual(prediction_str, solution_str)

                if test_def.solution_condition is not None:
                    for world in worlds:
                        self.assertTrue(test_def.solution_condition(world))
                
                print('\033[32;1m\b✓', end='')
        print('\033[0m')


class TestRiot(unittest.TestCase):
    def test_minions_become_riot(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Riot) & IsCharacter(D, Goblin)),
                }),
                Player('B', claim=Undertaker),
                Player('C', claim=Investigator, night_info={
                    1: Investigator.Ping(D, You, Goblin)
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
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(D, Riot) & IsCharacter(C, Goblin)),
                }),
                Player('B', claim=Slayer, day_info={
                    2: Slayer.Shot(C, died=True),
                }),
                Player('C', claim=Investigator, night_info={
                    1: Investigator.Ping(D, You, Goblin)
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
        You, B, C, D, E = range(5)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Riot) & IsCharacter(D, Goblin)),
                }),
                Player('B', claim=Slayer, day_info={
                    3: Slayer.Shot(C, died=True),
                }),
                Player('C', claim=Investigator, night_info={
                    1: Investigator.Ping(D, You, Goblin)
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


class TestWidow(unittest.TestCase):
    def test_widow_creates_ping(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Imp) & IsCharacter(D, Widow))
                }),
                Player('B', claim=Investigator, night_info={
                    1: [
                        Investigator.Ping(You, B, Widow),
                        Widow.InPlay(),
                    ],
                }),
                Player('C', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(1)
                }),
                Player('D', claim=Saint, night_info={
                    1: Widow.InPlay(),
                }),
            ],
            day_events={},
            night_deaths={2: B},
            hidden_characters=[Imp, Widow],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(
            self,
            puzzle,
            solutions=((Artist, Investigator, Imp, Widow),),
            conditions=CharAttrEq(D, 'target', B),
        )

    def test_widow_self_poisones_with_no_ping(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Imp) & IsCharacter(D, Widow))
                }),
                Player('B', claim=Investigator, night_info={
                    1: Investigator.Ping(D, You, Widow),
                }),
                Player('C', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(1)
                }),
                Player('D', claim=Balloonist, night_info={
                    1: Balloonist.Ping(You),
                    2: Balloonist.Ping(B),
                }),
            ],
            day_events={},
            night_deaths={2: B},
            hidden_characters=[Imp, Widow],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(
            self,
            puzzle,
            solutions=((Artist, Investigator, Imp, Widow),),
            conditions=CharAttrEq(D, 'target', D),
        )

    def test_widow_goo_pings_not_allowed_if_widow_not_in_play(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(
                        IsCharacter(C, Leviathan)
                        & IsCharacter(D, Goblin)
                    )
                }),
                Player('B', claim=Investigator, night_info={
                    1: [
                        Investigator.Ping(D, You, Goblin),
                        Widow.InPlay(),
                    ],
                }),
                Player('C', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(1),
                }),
                Player('D', claim=Balloonist, night_info={
                    1: Balloonist.Ping(You),
                    2: Balloonist.Ping(B),
                }),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Leviathan, Widow, Goblin],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=())

    def test_widow_evil_pings_allowed(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(
                        IsCharacter(C, Leviathan)
                        & IsCharacter(D, Goblin)
                    )
                }),
                Player('B', claim=Investigator, night_info={
                    1: Investigator.Ping(D, You, Goblin),
                }),
                Player('C', claim=Clockmaker, night_info={
                    1: Clockmaker.Ping(1)
                }),
                Player('D', claim=Balloonist, night_info={
                    1: [Balloonist.Ping(You), Widow.InPlay()],
                    2: Balloonist.Ping(You),
                }),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Leviathan, Widow, Goblin],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Investigator, Leviathan, Goblin),
        ))

    def test_widow_pings_when_unpoisoned(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist,
                    day_info={
                        1: Artist.Ping(
                            IsCharacter(B, Poisoner)
                            & IsCharacter(C, Widow)
                            & IsCharacter(D, Leviathan)
                        ),
                    },
                    night_info={2: Widow.InPlay()},
                ),
                Player('B', claim=Poisoner),
                Player('C', claim=Widow),
                Player('D', claim=Leviathan),
            ],
            day_events={1: Execution(B)},
            night_deaths={},
            hidden_characters=[Leviathan, Widow, Poisoner],
            hidden_self=[],
            category_counts=(1, 0, 2, 1),
        )
        assert_solutions(
            self,
            puzzle,
            solutions=((Artist, Poisoner, Widow, Leviathan),),
            conditions=~CharAttrEq(C, 'target', C),
        )


class TestVirgin(unittest.TestCase):
    def test_virgin_procs_on_tf(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Goblin) & IsCharacter(D, Imp)),
                }),
                Player('B', claim=Virgin),
                Player('C', claim=ScarletWoman),
                Player('D', claim=Imp),
            ],
            day_events={1: ExecutionByST(You, after_nominating=B)},
            night_deaths={},
            hidden_characters=[Imp, Goblin],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Virgin, Goblin, Imp),
        ))

    def test_virgin_procs_on_spy(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(D, Imp)),
                }),
                Player('B', claim=Virgin),
                Player('C', claim=Soldier),
                Player('D', claim=Imp),
            ],
            day_events={1: ExecutionByST(C, after_nominating=B)},
            night_deaths={},
            hidden_characters=[Imp, Spy, Poisoner],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Virgin, Spy, Imp),
        ))

    def test_virgin_spent(self):
        You, B, C, D = range(4)
        puzzle_base = dict(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Spy) & IsCharacter(D, Leviathan)),
                }),
                Player('B', claim=Virgin),
                Player('C', claim=Soldier),
                Player('D', claim=Leviathan),
            ],
            night_deaths={},
            hidden_characters=[Leviathan, Spy],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(
            self,
            puzzle=Puzzle(
                **deepcopy(puzzle_base),
                day_events={
                    1: UneventfulNomination(player=B, nominator=C),
                    2: UneventfulNomination(player=B, nominator=C),
                },
            ),
            solutions=((Artist, Virgin, Spy, Leviathan),),
        )
        assert_solutions(
            self,
            puzzle=Puzzle(
                **deepcopy(puzzle_base),
                day_events={
                    1: UneventfulNomination(player=B, nominator=C),
                    2: UneventfulNomination(player=B, nominator=You),
                },
            ),
            solutions=((Artist, Virgin, Spy, Leviathan),),
        )
        assert_solutions(
            self,
            puzzle=Puzzle(
                **deepcopy(puzzle_base),
                day_events={
                    1: UneventfulNomination(player=B, nominator=C),
                    2: ExecutionByST(You, after_nominating=B),
                },
            ),
            solutions=(),
        )

    def test_virgin_poisoned(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Poisoner) & IsCharacter(D, Imp)),
                }),
                Player('B', claim=Virgin),
                Player('C', claim=Poisoner),
                Player('D', claim=Imp),
            ],
            day_events={1: UneventfulNomination(player=B, nominator=You)},
            night_deaths={},
            hidden_characters=[Imp, Poisoner],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(
            self,
            puzzle,
            solutions=((Artist, Virgin, Poisoner, Imp),),
            conditions=CharAttrEq(C, 'target', B),
        )
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Poisoner) & IsCharacter(D, Imp)),
                }),
                Player('B', claim=Virgin),
                Player('C', claim=Poisoner),
                Player('D', claim=Imp),
            ],
            day_events={
                1: UneventfulNomination(player=B, nominator=You),
                2: UneventfulNomination(player=B, nominator=You),
            },
            night_deaths={2: C},
            hidden_characters=[Imp, Poisoner],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Virgin, Poisoner, Imp),
        ))

    def test_virgin_dead(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(C, Goblin) & IsCharacter(D, Imp)),
                }),
                Player('B', claim=Virgin),
                Player('C', claim=Virgin),
                Player('D', claim=Imp),
            ],
            day_events={2: UneventfulNomination(player=B, nominator=You)},
            night_deaths={2: B},
            hidden_characters=[Imp, Goblin],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Virgin, Goblin, Imp),
        ))

    def test_philo_virgin(self):
        You, B, C, D, E = range(5)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(D, Goblin) & IsCharacter(E, Imp)),
                }),
                Player('B', claim=Philosopher, night_info={
                    1: Philosopher.Choice(Virgin),
                }),
                Player('C', claim=Virgin),
                Player('D', claim=Goblin),
                Player('E', claim=Imp),
            ],
            day_events={
                1: [
                    UneventfulNomination(player=C, nominator=You),
                    ExecutionByST(player=C, after_nominating=B),
                ],
            },
            night_deaths={},
            hidden_characters=[Imp, Goblin],
            hidden_self=[],
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Philosopher, Virgin, Goblin, Imp),
        ))


class TestSlayer(unittest.TestCase):
    def test_slayer_kills_demon(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Slayer, day_info={
                    1: Slayer.Shot(D, died=True)
                }),
                Player('B', claim=Soldier),
                Player('C', claim=Imp),
                Player('D', claim=Imp),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Imp, Imp],
            hidden_self=[],
            category_counts=(2, 0, 0, 2),
        )
        assert_solutions(self, puzzle, solutions=(
            (Slayer, Soldier, Imp, Imp),
        ))

    def test_slayer_misses_minion(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Slayer, day_info={
                    1: Slayer.Shot(D, died=False)
                }),
                Player('B', claim=Soldier),
                Player('C', claim=Imp),
                Player('D', claim=Goblin),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Imp, Goblin],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Slayer, Soldier, Imp, Goblin),
        ))

    def test_slayer_may_kill_recluse(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Slayer, day_info={
                    1: Slayer.Shot(D, died=False)  # Recluse survives
                }),
                Player('B', claim=Soldier),
                Player('C', claim=Imp),
                Player('D', claim=Recluse),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Imp],
            hidden_self=[],
            category_counts=(2, 1, 0, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Slayer, Soldier, Imp, Recluse),
        ))
        puzzle = Puzzle(
            players=[
                Player('You', claim=Slayer, day_info={
                    1: Slayer.Shot(D, died=True)  # Recluse dies
                }),
                Player('B', claim=Soldier),
                Player('C', claim=Imp),
                Player('D', claim=Recluse),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Imp],
            hidden_self=[],
            category_counts=(2, 1, 0, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Slayer, Soldier, Imp, Recluse),
        ))

    def test_slayer_poisoned(self):
        You, B, C = range(3)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Slayer, day_info={
                    1: Slayer.Shot(C, died=False)
                }),
                Player('B', claim=Soldier),
                Player('C', claim=Pukka),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Pukka],
            hidden_self=[],
            category_counts=(2, 0, 0, 1),
        )
        assert_solutions(
            self,
            puzzle,
            solutions=((Slayer, Soldier, Pukka),),
            conditions=CharAttrEq(C, 'target', You),
        )

    def test_slayer_spent(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Slayer, day_info={
                    1: [
                        Slayer.Shot(B, died=False),
                        Slayer.Shot(C, died=False),
                    ],
                }),
                Player('B', claim=Soldier),
                Player('C', claim=Imp),
                Player('D', claim=Imp),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Imp, Imp],
            hidden_self=[],
            category_counts=(2, 0, 0, 2),
        )
        assert_solutions(self, puzzle, solutions=(
            (Slayer, Soldier, Imp, Imp),
        ))

    def test_others_cant_slay(self):
        You, B, C = range(3)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(IsCharacter(B, Goblin) & IsCharacter(C, Imp))
                }),
                Player('B', claim=Slayer, day_info={
                    1: Slayer.Shot(C, died=False)
                }),
                Player('C', claim=Imp, day_info={
                    1: Slayer.Shot(C, died=False)
                }),
            ],
            day_events={},
            night_deaths={},
            hidden_characters=[Imp, Goblin],
            hidden_self=[],
            category_counts=(1, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Goblin, Imp),
        ))

    def test_philo_slayer(self):
        You, B, C, D,= range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Philosopher,
                    night_info={1: Philosopher.Choice(Slayer)},
                ),
                Player('B', claim=Imp),
                Player('C', claim=Imp),
                Player('D', claim=Soldier),
            ],
            day_events={
                1: [
                    Slayer.Shot(B, died=True, player=You),
                    Slayer.Shot(C, died=False, player=You),
                ]
            },
            night_deaths={},
            hidden_characters=[Imp, Imp],
            hidden_self=[],
            category_counts=(2, 0, 0, 2),
        )
        assert_solutions(self, puzzle, solutions=(
            (Philosopher, Imp, Imp, Soldier),
        ))

class TestBoffin(unittest.TestCase):
    def test_boffin_slayer(self):
        You, B, C, D,= range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(
                        IsCharacter(B, Leviathan) & IsCharacter(C, Boffin)
                    )},
                ),
                Player('B', claim=Slayer),
                Player('C', claim=Boffin),
                Player('D', claim=Recluse),
            ],
            day_events={
                1: Slayer.Shot(D, died=True, player=B),
            },
            night_deaths={},
            hidden_characters=[Leviathan, Boffin],
            hidden_self=[],
            category_counts=(1, 1, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Leviathan, Boffin, Recluse),
        ))

    def test_boffin_spent_slayer(self):
        You, B, C, D,= range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(
                        IsCharacter(B, Leviathan) & IsCharacter(C, Boffin)
                    )},
                ),
                Player('B', claim=Slayer),
                Player('C', claim=Boffin),
                Player('D', claim=Recluse),
            ],
            day_events={
                1: [
                    Slayer.Shot(C, died=False, player=B),
                    Slayer.Shot(D, died=True, player=B),
                ]
            },
            night_deaths={},
            hidden_characters=[Leviathan, Boffin],
            hidden_self=[],
            category_counts=(1, 1, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=())

    def test_boffin_recluse(self):
        You, B, C, D,= range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(
                        IsCharacter(B, Leviathan)
                        & IsCharacter(C, Boffin)
                        & IsCharacter(D, Ravenkeeper)
                    )},
                ),
                Player('B', claim=Slayer),
                Player('C', claim=Butler),
                Player('D', claim=Ravenkeeper, night_info={
                    2: Ravenkeeper.Ping(B, Goblin)
                }),
            ],
            day_events={},
            night_deaths={2: D},
            hidden_characters=[Imp, Boffin, Goblin],
            hidden_self=[],
            also_on_script=[Recluse],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Imp, Boffin, Ravenkeeper),
        ))

    def test_boffin_virgin(self):
        You, B, C, D,= range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(
                        IsCharacter(B, Leviathan)
                        & IsCharacter(C, Boffin)
                        & IsCharacter(D, Ravenkeeper)
                    )},
                ),
                Player('B', claim=Slayer),
                Player('C', claim=Butler),
                Player('D', claim=Ravenkeeper),
            ],
            day_events={
                1: ExecutionByST(player=D, after_nominating=B)
            },
            night_deaths={},
            hidden_characters=[Leviathan, Boffin],
            hidden_self=[],
            also_on_script=[Virgin],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Leviathan, Boffin, Ravenkeeper),
        ))

    def test_boffin_golem(self):
        You, B, C, D,= range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(
                        IsCharacter(B, Leviathan)
                        & IsCharacter(C, Boffin)
                        & IsCharacter(D, Ravenkeeper)
                    )},
                ),
                Player('B', claim=Golem),
                Player('C', claim=Butler),
                Player('D', claim=Ravenkeeper),
            ],
            day_events={1: Dies(player=C, after_nominated_by=B)},
            night_deaths={},
            hidden_characters=[Leviathan, Boffin],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Leviathan, Boffin, Ravenkeeper),
        ))

    # def boffin_philo_philo_empath_wakes(self):
    def test_boffin_droisoned(self):
        You, B, C, D, E = range(5)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(
                        IsCharacter(B, Imp)
                        & IsCharacter(C, Boffin)
                        & IsCharacter(D, Courtier)
                        & IsCharacter(E, Butler)
                    )},
                ),
                Player('B', claim=Golem),
                Player('C', claim=Butler),
                Player('D', claim=Courtier, night_info={
                    1: Courtier.Choice(Boffin),
                }),
                Player('E', claim=Butler),
            ],
            day_events={
                1: UneventfulNomination(player=D, nominator=B),
                2: Dies(player=E, after_nominated_by=B),
            },
            night_deaths={2: D},
            hidden_characters=[Imp, Boffin],
            hidden_self=[],
            category_counts=(2, 1, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Imp, Boffin, Courtier, Butler),
        ))

    def test_boffin_on_drunk_demon(self):
        You, B, C, D = range(4)
        puzzle = Puzzle(
            players=[
                Player('You', claim=Artist, day_info={
                    1: Artist.Ping(
                        IsCharacter(B, Imp)
                        & IsCharacter(C, Boffin)
                        & IsCharacter(D, Courtier)
                    )},
                ),
                Player('B', claim=Golem),
                Player('C', claim=Butler),
                Player('D', claim=Courtier, night_info={
                    1: Courtier.Choice(Imp),
                }),
            ],
            day_events={
                1: Dies(player=D, after_nominated_by=B),
            },
            night_deaths={},
            hidden_characters=[Imp, Boffin],
            hidden_self=[],
            category_counts=(2, 0, 1, 1),
        )
        assert_solutions(self, puzzle, solutions=(
            (Artist, Imp, Boffin, Courtier),
        ))
