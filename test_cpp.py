import ctypes
import time
import unittest

import puzzles
from clockchecker import solve, solve_cpp
from clockchecker.cpp_solve import (
    _get_lib,
    serialize_puzzle,
    CSerializedSolution,
    MAX_SOLUTIONS,
)


class TestCppPoC(unittest.TestCase):
    def test_all_puzzles(self):
        puzzle_names = [
            "puzzle_NQT1",
            "puzzle_NQT2",
            "puzzle_NQT3a",
            "puzzle_NQT3b",
            "puzzle_NQT4",
            "puzzle_NQT5a",
            "puzzle_NQT5b",
            "puzzle_NQT6",
            "puzzle_NQT7",
            "puzzle_NQT8",
            "puzzle_NQT9",
            "puzzle_NQT10",
            "puzzle_NQT12a",
            "puzzle_NQT12b",
            "puzzle_NQT13",
            "puzzle_NQT14",
            "puzzle_NQT15",
            "puzzle_NQT16",
            "puzzle_NQT17",
            "puzzle_NQT18",
            "puzzle_NQT19",
            "puzzle_NQT20",
            "puzzle_NQT21",
            "puzzle_NQT22",
            "puzzle_NQT23",
            "puzzle_NQT24",
            "puzzle_NQT26",
            "puzzle_NQT28",
            "puzzle_NQT29",
            "puzzle_NQT30a",
            "puzzle_NQT30b",
            "puzzle_NQT31",
            "puzzle_NQT32",
            "puzzle_NQT33",
            "puzzle_NQT34",
            "puzzle_NQT35",
            "puzzle_NQT36",
            "puzzle_NQT37",
            "puzzle_NQT38",
            "puzzle_NQT38_alt",
            "puzzle_NQT39",
            "puzzle_NQT40",
            "puzzle_NQT41",
            "puzzle_NQT42",
            "puzzle_NQT43",
            "puzzle_NQT44",
            "puzzle_NQT44_alt",
            "puzzle_NQT45a",
            "puzzle_NQT45b",
            "puzzle_NQT46",
            "puzzle_NQT47",
            "puzzle_NQT48",
            "puzzle_NQT49",
            "puzzle_NQT50",
            "puzzle_NQT51",
            "puzzle_NQT53",
            "puzzle_NQT54",
            "puzzle_NQT55",
            "puzzle_NQT57",
            "puzzle_NQT58",
            "puzzle_NQT59",
            "puzzle_NQT60",
            "puzzle_NQT61",
            "puzzle_NQT63",
            "puzzle_NQT65",
            "puzzle_NQT66",
            "puzzle_NQT67",
            "puzzle_NQT68",
            "puzzle_NQT69_alt",
            "puzzle_NQT69",
            "puzzle_NQT70",
            "puzzle_NQT71_alt2",
            "puzzle_NQT73",
            "puzzle_NQT74",
            "puzzle_NQT75",
            "puzzle_NQT77",
            "puzzle_NQT78",
            "puzzle_NQT79",
            "puzzle_NQT80",
            "puzzle_NQT90",
            "puzzle_josef_yes_but_dont",
            "puzzle_josef_lunatic",
            "puzzle_nikhilvyas27",
            "puzzle_nikhilvyas28",
            "puzzle_ali_adversarial1",
            "puzzle_ali_adversarial2",
            "puzzle_nqt_sw_test",
            "puzzle_nqt_snv_test1",
            "puzzle_nqt_snv_test2",
            "puzzle_nqt_snv_test3",
            "puzzle_nqt_snv_test4",
            "puzzle_nqt_uncommon_vig_solution",
            "puzzle_emerald_snv",
        ]
        lib = _get_lib()
        print(
            f"\n{'Puzzle':<13} | {'Py (1 proc)':>11} | {'C++ 1T core':>11} | {'C++ MT core':>11} | {'C++ MT e2e':>11} | {'Speedup (1T/MT)':>17} | Status"
        )
        print("-" * 105)

        total_py = 0.0
        total_cpp_1t = 0.0
        total_cpp_mt = 0.0
        total_cpp_e2e = 0.0

        for name in puzzle_names:
            pdef_py = getattr(puzzles, name)()
            pdef_cpp = getattr(puzzles, name)()

            # Run Python solver (single-process for fair 1-to-1 algorithmic comparison)
            t0 = time.perf_counter()
            if pdef_py.solve_override is not None:
                orig_solve = puzzles.solve
                puzzles.solve = lambda p, **kw: orig_solve(p, num_processes=1)
                try:
                    py_worlds = list(pdef_py.solve_override)
                finally:
                    puzzles.solve = orig_solve
            else:
                py_worlds = list(solve(pdef_py.puzzle, num_processes=1))
            t_py = time.perf_counter() - t0

            # End-to-end C++ solve from Python Puzzle -> Python State objects
            t0 = time.perf_counter()
            if pdef_cpp.solve_override is not None:
                orig_solve = puzzles.solve
                puzzles.solve = solve_cpp
                try:
                    cpp_worlds = list(pdef_cpp.solve_override)
                finally:
                    puzzles.solve = orig_solve
            else:
                cpp_worlds = list(solve_cpp(pdef_cpp.puzzle))
            t_cpp_e2e = time.perf_counter() - t0

            # Pure C++ solver kernel time (1T vs MT work-stealing)
            sub_puzzles = pdef_cpp.puzzle if isinstance(pdef_cpp.puzzle, tuple) else (pdef_cpp.puzzle,)
            cpuzzles = [serialize_puzzle(sp) for sp in sub_puzzles]
            out_solutions = (CSerializedSolution * MAX_SOLUTIONS)()
            t0 = time.perf_counter()
            for cpuzzle in cpuzzles:
                lib.solve_puzzle_cpp_mt(ctypes.byref(cpuzzle), out_solutions, MAX_SOLUTIONS, 1)
            t_cpp_1t = time.perf_counter() - t0

            t0 = time.perf_counter()
            for cpuzzle in cpuzzles:
                lib.solve_puzzle_cpp_mt(ctypes.byref(cpuzzle), out_solutions, MAX_SOLUTIONS, 0)
            t_cpp_mt = time.perf_counter() - t0

            total_py += t_py
            total_cpp_1t += t_cpp_1t
            total_cpp_mt += t_cpp_mt
            total_cpp_e2e += t_cpp_e2e

            target_strs = sorted(
                ", ".join(x.__name__ for x in sol)
                for sol in pdef_cpp.solutions
            )
            py_strs = sorted(
                ", ".join(x.__name__ for x in w.initial_characters)
                for w in py_worlds
            )
            cpp_strs = sorted(
                ", ".join(x.__name__ for x in w.initial_characters)
                for w in cpp_worlds
            )

            self.assertEqual(py_strs, target_strs, f"{name}: Python mismatch")
            self.assertEqual(cpp_strs, target_strs, f"{name}: C++ mismatch: got {cpp_strs} vs {target_strs}")
            if pdef_cpp.solution_endchars is not None:
                target_end_strs = sorted(
                    ", ".join(x.__name__ for x in sol)
                    for sol in pdef_cpp.solution_endchars
                )
                cpp_end_strs = sorted(
                    ", ".join(type(p.character).__name__ for p in w.players)
                    for w in cpp_worlds
                )
                self.assertEqual(
                    cpp_end_strs,
                    target_end_strs,
                    f"{name}: C++ endchars mismatch: got {cpp_end_strs} vs {target_end_strs}",
                )
            if pdef_cpp.solution_condition is not None:
                for w in cpp_worlds:
                    self.assertTrue(
                        pdef_cpp.solution_condition(w),
                        f"{name}: C++ solution_condition failed on {w}",
                    )

            sp_1t = t_py / t_cpp_1t if t_cpp_1t > 0 else float("inf")
            sp_mt = t_py / t_cpp_mt if t_cpp_mt > 0 else float("inf")
            print(
                f"{name:<13} | {t_py*1000:8.2f} ms | {t_cpp_1t*1000:8.3f} ms | {t_cpp_mt*1000:8.3f} ms | {t_cpp_e2e*1000:8.3f} ms | "
                f"{sp_1t:6.1f}x / {sp_mt:7.1f}x | OK ({len(cpp_worlds)} sol)"
            )

        print("-" * 105)
        sp_1t = total_py / total_cpp_1t if total_cpp_1t > 0 else float("inf")
        sp_mt = total_py / total_cpp_mt if total_cpp_mt > 0 else float("inf")
        sp_e2e = total_py / total_cpp_e2e if total_cpp_e2e > 0 else float("inf")
        print(
            f"{'TOTAL':<13} | {total_py*1000:8.2f} ms | {total_cpp_1t*1000:8.3f} ms | {total_cpp_mt*1000:8.3f} ms | {total_cpp_e2e*1000:8.3f} ms | "
            f"{sp_1t:6.1f}x / {sp_mt:7.1f}x | (e2e: {sp_e2e:.1f}x)"
        )


if __name__ == "__main__":
    unittest.main()
