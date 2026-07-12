from copy import deepcopy
from itertools import combinations

from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from .generator import DIFFICULTIES, generate_puzzle

SIZE = 9
DEFAULT_DIFFICULTY = "medium"
EMPTY_GRID = [[{"final": None, "notes": []} for _ in range(SIZE)] for _ in range(SIZE)]


def start_game(request, difficulty=DEFAULT_DIFFICULTY):
    puzzle = generate_puzzle(difficulty)
    request.session["grid"] = deepcopy(EMPTY_GRID)
    request.session["selected"] = [0, 0]
    request.session["note_mode"] = False
    request.session["difficulty"] = difficulty
    request.session["solution"] = puzzle["solution"]
    request.session["cages"] = puzzle["cages"]
    request.session["game_status"] = "playing"
    request.session.modified = True


def get_state(request):
    required = ("grid", "solution", "cages")
    if any(key not in request.session for key in required):
        start_game(request)
    return (
        request.session["grid"],
        request.session.get("selected", [0, 0]),
        request.session.get("note_mode", False),
        request.session["cages"],
        request.session.get("difficulty", DEFAULT_DIFFICULTY),
        request.session.get("game_status", "playing"),
        request.session["solution"],
    )


def cage_layout(cages):
    cage_at = [[None] * SIZE for _ in range(SIZE)]
    for index, cage in enumerate(cages):
        for row, col in cage["cells"]:
            cage_at[row][col] = index

    layout = [[None] * SIZE for _ in range(SIZE)]
    for row in range(SIZE):
        for col in range(SIZE):
            index = cage_at[row][col]
            cage = cages[index]
            first = min(tuple(cell) for cell in cage["cells"])
            classes = []
            # Draw each shared cage edge once, on the lower/right-hand cell.
            for name, dr, dc in (("top", -1, 0), ("left", 0, -1)):
                other_row, other_col = row + dr, col + dc
                if (
                    0 <= other_row < SIZE
                    and 0 <= other_col < SIZE
                    and cage_at[other_row][other_col] != index
                ):
                    classes.append(f"cage-{name}")
            layout[row][col] = {
                "classes": " ".join(classes),
                "cage_index": index,
                "sum": cage["sum"] if (row, col) == first else None,
            }
    return layout


def find_cage(cages, row, col):
    return next(cage for cage in cages if [row, col] in cage["cells"])


def legal_numbers(grid, selected, cages):
    row, col = selected
    used = {
        grid[peer_row][peer_col]["final"]
        for peer_row, peer_col in peers(row, col)
        if grid[peer_row][peer_col]["final"] is not None
    }
    cage = find_cage(cages, row, col)
    other_cells = [(r, c) for r, c in cage["cells"] if (r, c) != (row, col)]
    cage_values = {
        grid[r][c]["final"]
        for r, c in other_cells
        if grid[r][c]["final"] is not None
    }
    empty_count = sum(grid[r][c]["final"] is None for r, c in other_cells)
    placed_sum = sum(cage_values)
    legal = set()
    for num in range(1, 10):
        if num in used or num in cage_values:
            continue
        remainder = cage["sum"] - placed_sum - num
        if empty_count == 0:
            possible = remainder == 0
        else:
            remaining_digits = [
                digit
                for digit in range(1, 10)
                if digit not in cage_values and digit != num
            ]
            possible = any(
                sum(choice) == remainder
                for choice in combinations(remaining_digits, empty_count)
            )
        if possible:
            legal.add(num)
    return legal


def context(grid, selected, note_mode, cages, difficulty, game_status, solution):
    layout = cage_layout(cages)
    selected_cage = layout[selected[0]][selected[1]]["cage_index"]
    rows = []
    for row in range(SIZE):
        rendered_row = []
        for col in range(SIZE):
            active_boundaries = []
            cell_layout = layout[row][col]
            if "cage-top" in cell_layout["classes"] and (
                cell_layout["cage_index"] == selected_cage
                or layout[row - 1][col]["cage_index"] == selected_cage
            ):
                active_boundaries.append("cage-top-active")
            if "cage-left" in cell_layout["classes"] and (
                cell_layout["cage_index"] == selected_cage
                or layout[row][col - 1]["cage_index"] == selected_cage
            ):
                active_boundaries.append("cage-left-active")
            rendered_row.append(
                {
                    **grid[row][col],
                    **cell_layout,
                    "row": row,
                    "col": col,
                    "active_cage": layout[row][col]["cage_index"] == selected_cage,
                    "active_boundaries": " ".join(active_boundaries),
                }
            )
        rows.append(rendered_row)
    available = legal_numbers(grid, selected, cages)
    selected_cell = grid[selected[0]][selected[1]]
    available.update(selected_cell["notes"])
    if selected_cell["final"]:
        available.add(selected_cell["final"])
    return {
        "grid": grid,
        "grid_rows": rows,
        "selected": selected,
        "note_mode": note_mode,
        "notes_range": range(1, 10),
        "available_numbers": available,
        "difficulties": DIFFICULTIES,
        "difficulty": difficulty,
        "game_status": game_status,
    }


def render_board(request, *state):
    return render(request, "sudoku/board.html", context(*state))


def update_completion(request, grid, solution):
    complete = all(
        grid[row][col]["final"] == solution[row][col]
        for row in range(SIZE)
        for col in range(SIZE)
    )
    request.session["game_status"] = "won" if complete else "playing"


@require_GET
def sudoku_grid(request):
    return render(request, "sudoku/grid.html", context(*get_state(request)))


@require_POST
def select_cell(request, row, col):
    if not 0 <= row < SIZE or not 0 <= col < SIZE:
        return HttpResponseBadRequest("Cell is outside the grid")
    grid, _, note_mode, cages, difficulty, game_status, solution = get_state(request)
    selected = [row, col]
    request.session["selected"] = selected
    request.session.modified = True
    return render_board(request, grid, selected, note_mode, cages, difficulty, game_status, solution)


def peers(row, col):
    result = {(row, i) for i in range(SIZE)} | {(i, col) for i in range(SIZE)}
    box_row, box_col = row // 3 * 3, col // 3 * 3
    result |= {(r, c) for r in range(box_row, box_row + 3) for c in range(box_col, box_col + 3)}
    result.discard((row, col))
    return result


@require_POST
def enter_number(request):
    grid, selected, note_mode, cages, difficulty, game_status, solution = get_state(request)
    try:
        num = int(request.POST.get("num", ""))
    except (TypeError, ValueError):
        num = 0
    row, col = selected
    cell = grid[row][col]
    legal = legal_numbers(grid, selected, cages)
    removing_existing = cell["final"] == num or (note_mode and num in cell["notes"])
    if 1 <= num <= 9 and (num in legal or removing_existing):
        if note_mode and cell["final"] is None:
            if num in cell["notes"]:
                cell["notes"].remove(num)
            else:
                cell["notes"].append(num)
                cell["notes"].sort()
        else:
            cell["final"] = None if cell["final"] == num else num
            cell["notes"] = []
            if cell["final"]:
                for peer_row, peer_col in peers(row, col):
                    notes = grid[peer_row][peer_col]["notes"]
                    if num in notes:
                        notes.remove(num)
        request.session["grid"] = grid
        update_completion(request, grid, solution)
        request.session.modified = True
        game_status = request.session["game_status"]
    return render_board(request, grid, selected, note_mode, cages, difficulty, game_status, solution)


@require_POST
def move_selection(request, direction):
    grid, selected, note_mode, cages, difficulty, game_status, solution = get_state(request)
    deltas = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
    if direction not in deltas:
        return HttpResponseBadRequest("Unknown direction")
    dr, dc = deltas[direction]
    selected = [(selected[0] + dr) % SIZE, (selected[1] + dc) % SIZE]
    request.session["selected"] = selected
    request.session.modified = True
    return render_board(request, grid, selected, note_mode, cages, difficulty, game_status, solution)


@require_POST
def clear_cell(request):
    grid, selected, note_mode, cages, difficulty, game_status, solution = get_state(request)
    grid[selected[0]][selected[1]] = {"final": None, "notes": []}
    request.session["grid"] = grid
    update_completion(request, grid, solution)
    request.session.modified = True
    return render_board(request, grid, selected, note_mode, cages, difficulty, request.session["game_status"], solution)


@require_POST
def toggle_note_mode(request):
    grid, selected, note_mode, cages, difficulty, game_status, solution = get_state(request)
    note_mode = not note_mode
    request.session["note_mode"] = note_mode
    request.session.modified = True
    return render_board(request, grid, selected, note_mode, cages, difficulty, game_status, solution)


@require_POST
def reset_grid(request):
    _, _, _, cages, difficulty, _, solution = get_state(request)
    request.session["grid"] = deepcopy(EMPTY_GRID)
    request.session["selected"] = [0, 0]
    request.session["note_mode"] = False
    request.session["game_status"] = "playing"
    request.session.modified = True
    return render_board(
        request,
        request.session["grid"],
        [0, 0],
        False,
        cages,
        difficulty,
        "playing",
        solution,
    )


@require_POST
def new_game(request):
    difficulty = request.POST.get("difficulty", DEFAULT_DIFFICULTY)
    if difficulty not in DIFFICULTIES:
        return HttpResponseBadRequest("Unknown difficulty")
    start_game(request, difficulty)
    return render_board(request, *get_state(request))
