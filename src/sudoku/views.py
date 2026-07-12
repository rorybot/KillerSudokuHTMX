from copy import deepcopy

from django.http import HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

SIZE = 9
EMPTY_GRID = [[{"final": None, "notes": []} for _ in range(SIZE)] for _ in range(SIZE)]


def get_state(request):
    if "grid" not in request.session:
        request.session["grid"] = deepcopy(EMPTY_GRID)
        request.session["selected"] = [0, 0]
        request.session["note_mode"] = False
    return request.session["grid"], request.session.get("selected", [0, 0]), request.session.get("note_mode", False)


def context(grid, selected, note_mode):
    return {"grid": grid, "selected": selected, "note_mode": note_mode, "notes_range": range(1, 10)}


def render_board(request, grid, selected, note_mode):
    return render(request, "sudoku/board.html", context(grid, selected, note_mode))


@require_GET
def sudoku_grid(request):
    return render(request, "sudoku/grid.html", context(*get_state(request)))


@require_POST
def select_cell(request, row, col):
    grid, _, note_mode = get_state(request)
    request.session["selected"] = [row, col]
    request.session.modified = True
    return render_board(request, grid, [row, col], note_mode)


def peers(row, col):
    result = {(row, i) for i in range(SIZE)} | {(i, col) for i in range(SIZE)}
    box_row, box_col = row // 3 * 3, col // 3 * 3
    result |= {(r, c) for r in range(box_row, box_row + 3) for c in range(box_col, box_col + 3)}
    result.discard((row, col))
    return result


@require_POST
def enter_number(request):
    grid, selected, note_mode = get_state(request)
    try:
        num = int(request.POST.get("num", ""))
    except (TypeError, ValueError):
        num = 0
    row, col = selected
    if 1 <= num <= 9:
        cell = grid[row][col]
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
        request.session.modified = True
    return render_board(request, grid, selected, note_mode)


@require_POST
def move_selection(request, direction):
    grid, selected, note_mode = get_state(request)
    deltas = {"up": (-1, 0), "down": (1, 0), "left": (0, -1), "right": (0, 1)}
    if direction not in deltas:
        return HttpResponseBadRequest("Unknown direction")
    dr, dc = deltas[direction]
    selected = [(selected[0] + dr) % SIZE, (selected[1] + dc) % SIZE]
    request.session["selected"] = selected
    request.session.modified = True
    return render_board(request, grid, selected, note_mode)


@require_POST
def clear_cell(request):
    grid, selected, note_mode = get_state(request)
    grid[selected[0]][selected[1]] = {"final": None, "notes": []}
    request.session["grid"] = grid
    request.session.modified = True
    return render_board(request, grid, selected, note_mode)


@require_POST
def toggle_note_mode(request):
    grid, selected, note_mode = get_state(request)
    note_mode = not note_mode
    request.session["note_mode"] = note_mode
    request.session.modified = True
    return render_board(request, grid, selected, note_mode)


@require_POST
def reset_grid(request):
    request.session["grid"] = deepcopy(EMPTY_GRID)
    request.session["selected"] = [0, 0]
    request.session["note_mode"] = False
    request.session.modified = True
    return render_board(request, request.session["grid"], [0, 0], False)
