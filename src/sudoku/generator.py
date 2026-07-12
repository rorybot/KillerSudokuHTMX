"""Fast generation of verified-unique Killer Sudoku puzzles."""

import random

SIZE = 9
ALL_DIGITS = tuple(range(1, 10))
DIFFICULTIES = ("easy", "medium", "hard")

# This solved grid and the cage templates below were verified together by
# ``count_solutions``. New games apply Sudoku-preserving digit permutations and
# board symmetries, so every variant retains the same uniqueness proof.
BASE_SOLUTION = (
    (1, 4, 7, 9, 6, 2, 8, 5, 3),
    (6, 9, 2, 5, 3, 8, 7, 4, 1),
    (3, 5, 8, 4, 1, 7, 2, 9, 6),
    (5, 2, 6, 8, 4, 3, 1, 7, 9),
    (9, 7, 1, 2, 5, 6, 3, 8, 4),
    (4, 8, 3, 7, 9, 1, 6, 2, 5),
    (2, 1, 9, 6, 8, 5, 4, 3, 7),
    (7, 3, 4, 1, 2, 9, 5, 6, 8),
    (8, 6, 5, 3, 7, 4, 9, 1, 2),
)

MEDIUM_CELLS = (
    ((4, 3), (5, 3)), ((2, 4), (2, 5)),
    ((0, 0), (0, 1), (1, 0), (1, 1)), ((0, 7), (0, 8)),
    ((5, 7), (6, 7)), ((2, 2), (3, 2)), ((6, 1), (7, 1)),
    ((0, 4), (1, 4)), ((4, 0), (5, 0)),
    ((3, 6), (4, 6), (5, 6)), ((4, 1), (4, 2)),
    ((4, 5), (5, 5)), ((6, 5), (6, 6)), ((7, 6), (7, 7)),
    ((5, 8), (6, 8)), ((7, 2), (7, 3), (8, 2)),
    ((8, 0), (8, 1)), ((0, 6), (1, 6), (1, 7), (1, 8)),
    ((0, 5), (1, 5)), ((2, 6), (2, 7), (3, 7)),
    ((8, 3), (8, 4)), ((6, 2), (6, 3)), ((2, 3), (3, 3)),
    ((7, 8), (8, 8)), ((4, 7), (4, 8)),
    ((3, 4), (3, 5), (4, 4)), ((8, 6), (8, 7)),
    ((2, 0), (2, 1)), ((1, 2), (1, 3)), ((5, 4), (6, 4)),
    ((5, 1), (5, 2)), ((2, 8), (3, 8)),
    ((7, 4), (7, 5), (8, 5)), ((6, 0), (7, 0)),
    ((3, 0), (3, 1)), ((0, 2), (0, 3)),
)

_EASY_SPLIT_CAGES = {
    ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 6), (1, 6), (1, 7), (1, 8)),
}
EASY_CELLS = tuple(cage for cage in MEDIUM_CELLS if cage not in _EASY_SPLIT_CAGES) + (
    ((0, 0), (0, 1)), ((1, 0), (1, 1)),
    ((0, 6), (1, 6)), ((1, 7), (1, 8)),
)

HARD_CELLS = (
    ((2, 4), (2, 5)), ((0, 0), (0, 1), (1, 0), (1, 1)),
    ((0, 7), (0, 8)), ((2, 2), (3, 2)), ((0, 4), (1, 4)),
    ((4, 0), (5, 0)), ((4, 1), (4, 2)), ((4, 5), (5, 5)),
    ((5, 8), (6, 8)), ((0, 6), (1, 6), (1, 7), (1, 8)),
    ((0, 5), (1, 5)), ((2, 6), (2, 7), (3, 7)),
    ((6, 2), (6, 3)), ((2, 3), (3, 3)), ((7, 8), (8, 8)),
    ((3, 4), (3, 5), (4, 4)), ((8, 6), (8, 7)),
    ((2, 0), (2, 1)), ((1, 2), (1, 3)), ((5, 4), (6, 4)),
    ((7, 4), (7, 5), (8, 5)), ((6, 0), (7, 0)),
    ((3, 0), (3, 1)), ((0, 2), (0, 3)),
    ((4, 3), (5, 1), (5, 2), (5, 3)),
    ((6, 1), (7, 1), (8, 0), (8, 1)),
    ((2, 8), (3, 8), (4, 7), (4, 8)),
    ((5, 7), (6, 7), (7, 6), (7, 7)),
    ((3, 6), (4, 6), (5, 6), (6, 5), (6, 6)),
    ((7, 2), (7, 3), (8, 2), (8, 3), (8, 4)),
)

CAGE_TEMPLATES = {
    "easy": EASY_CELLS,
    "medium": MEDIUM_CELLS,
    "hard": HARD_CELLS,
}


def box_index(row, col):
    return row // 3 * 3 + col // 3


def generate_solution(rng):
    """Return a randomized solved grid using Sudoku-preserving shuffles."""

    def shuffled_groups():
        groups = list(range(3))
        rng.shuffle(groups)
        result = []
        for group in groups:
            members = list(range(group * 3, group * 3 + 3))
            rng.shuffle(members)
            result.extend(members)
        return result

    rows = shuffled_groups()
    cols = shuffled_groups()
    digits = list(ALL_DIGITS)
    rng.shuffle(digits)
    return [
        [digits[(row * 3 + row // 3 + col) % SIZE] for col in cols]
        for row in rows
    ]


def transform_cell(row, col, symmetry):
    """Apply one of the square's eight adjacency-preserving symmetries."""
    if symmetry >= 4:
        col = SIZE - 1 - col
        symmetry -= 4
    for _ in range(symmetry):
        row, col = col, SIZE - 1 - row
    return row, col


def generate_puzzle(difficulty, rng=None):
    """Return a fast randomized, verified-unique Killer Sudoku puzzle."""
    if difficulty not in DIFFICULTIES:
        raise ValueError(f"Unknown difficulty: {difficulty!r}")
    rng = rng or random.Random()
    shuffled_digits = list(ALL_DIGITS)
    rng.shuffle(shuffled_digits)
    digit_map = dict(zip(ALL_DIGITS, shuffled_digits))
    symmetry = rng.randrange(8)

    solution = [[0] * SIZE for _ in range(SIZE)]
    for row in range(SIZE):
        for col in range(SIZE):
            new_row, new_col = transform_cell(row, col, symmetry)
            solution[new_row][new_col] = digit_map[BASE_SOLUTION[row][col]]

    cages = []
    for template in CAGE_TEMPLATES[difficulty]:
        cells = sorted(transform_cell(row, col, symmetry) for row, col in template)
        cages.append(
            {
                "cells": [[row, col] for row, col in cells],
                "sum": sum(solution[row][col] for row, col in cells),
            }
        )
    rng.shuffle(cages)
    return {"solution": solution, "cages": cages}


def count_solutions(cages, limit=2, node_cap=100_000):
    """Count solutions of a cage layout, up to ``limit``."""
    cage_sum = [cage["sum"] for cage in cages]
    cage_size = [len(cage["cells"]) for cage in cages]
    cage_of = {}
    for index, cage in enumerate(cages):
        for row, col in cage["cells"]:
            cage_of[(row, col)] = index

    grid = [[0] * SIZE for _ in range(SIZE)]
    rows = [0] * SIZE
    cols = [0] * SIZE
    boxes = [0] * SIZE
    cage_used = [0] * len(cages)
    cage_placed = [0] * len(cages)
    cage_left = list(cage_size)
    state = {"count": 0, "nodes": 0, "aborted": False}

    def candidates(row, col):
        index = cage_of[(row, col)]
        used = rows[row] | cols[col] | boxes[box_index(row, col)] | cage_used[index]
        need = cage_sum[index] - cage_placed[index]
        others = cage_left[index] - 1
        free = [digit for digit in ALL_DIGITS if not cage_used[index] >> digit & 1]
        result = []
        for num in ALL_DIGITS:
            if used >> num & 1:
                continue
            remainder = need - num
            if others == 0:
                if remainder != 0:
                    continue
            else:
                available = [digit for digit in free if digit != num]
                if others > len(available):
                    continue
                if remainder < sum(available[:others]) or remainder > sum(available[-others:]):
                    continue
            result.append(num)
        return result

    def solve():
        if state["aborted"] or state["count"] >= limit:
            return
        state["nodes"] += 1
        if state["nodes"] > node_cap:
            state["aborted"] = True
            return
        best = None
        best_digits = None
        for row in range(SIZE):
            for col in range(SIZE):
                if grid[row][col]:
                    continue
                digits = candidates(row, col)
                if not digits:
                    return
                if best_digits is None or len(digits) < len(best_digits):
                    best, best_digits = (row, col), digits
        if best is None:
            state["count"] += 1
            return
        row, col = best
        box = box_index(row, col)
        index = cage_of[(row, col)]
        for num in best_digits:
            bit = 1 << num
            grid[row][col] = num
            rows[row] |= bit
            cols[col] |= bit
            boxes[box] |= bit
            cage_used[index] |= bit
            cage_placed[index] += num
            cage_left[index] -= 1
            solve()
            grid[row][col] = 0
            rows[row] &= ~bit
            cols[col] &= ~bit
            boxes[box] &= ~bit
            cage_used[index] &= ~bit
            cage_placed[index] -= num
            cage_left[index] += 1
            if state["aborted"] or state["count"] >= limit:
                return

    solve()
    return None if state["aborted"] else state["count"]
