from django.shortcuts import render
from django.http import HttpResponse

# Helper to initialize session state
EMPTY_GRID = [[{'final': None, 'notes': []} for _ in range(9)] for _ in range(9)]

def get_state(request):
    if 'grid' not in request.session:
        request.session['grid'] = [[{'final': None, 'notes': []} for _ in range(9)] for _ in range(9)]
        request.session['selected'] = [0, 0]
        request.session['note_mode'] = False
    return request.session['grid'], request.session['selected'], request.session['note_mode']

def sudoku_grid(request):
    grid, selected, note_mode = get_state(request)
    notes_range = range(1, 10)
    return render(request, 'sudoku/grid.html', {
        'grid': grid,
        'selected': selected,
        'notes_range': notes_range,
    })

def select_cell(request, row, col):
    grid, selected, note_mode = get_state(request)
    request.session['selected'] = [int(row), int(col)]
    request.session.modified = True
    notes_range = range(1, 10)
    return render(request, 'sudoku/grid_inner.html', {
        'grid': grid,
        'selected': [int(row), int(col)],
        'notes_range': notes_range,
    })

def enter_number(request):
    grid, selected, note_mode = get_state(request)
    num = request.GET.get('num')
    try:
        num = int(num)
        row, col = selected if selected else (-1, -1)
        if (
            selected is not None and
            0 <= row < 9 and 0 <= col < 9 and 1 <= num <= 9
        ):
            if note_mode:
                notes = grid[row][col]['notes']
                if num in notes:
                    notes.remove(num)
                else:
                    notes.append(num)
                notes.sort()
            else:
                grid[row][col]['final'] = num
                grid[row][col]['notes'] = []  # Clear notes when entering a final number
            request.session['grid'] = grid
            request.session.modified = True
    except Exception:
        pass  # Ignore invalid input
    notes_range = range(1, 10)
    return render(request, 'sudoku/grid_inner.html', {
        'grid': grid,
        'selected': selected,
        'notes_range': notes_range,
        'note_mode': note_mode,
    })

def move_selection(request, direction):
    grid, selected, note_mode = get_state(request)
    row, col = selected
    if direction == 'up':
        row = (row - 1) % 9
    elif direction == 'down':
        row = (row + 1) % 9
    elif direction == 'left':
        col = (col - 1) % 9
    elif direction == 'right':
        col = (col + 1) % 9
    request.session['selected'] = [row, col]
    request.session.modified = True
    notes_range = range(1, 10)
    return render(request, 'sudoku/grid_inner.html', {
        'grid': grid,
        'selected': [row, col],
        'notes_range': notes_range,
    })

def clear_cell(request):
    grid, selected, note_mode = get_state(request)
    row, col = selected if selected else (-1, -1)
    if selected is not None and 0 <= row < 9 and 0 <= col < 9:
        grid[row][col]['final'] = None
        grid[row][col]['notes'] = []
        request.session['grid'] = grid
        request.session.modified = True
    notes_range = range(1, 10)
    return render(request, 'sudoku/grid_inner.html', {
        'grid': grid,
        'selected': selected,
        'notes_range': notes_range,
    })

def toggle_note_mode(request):
    grid, selected, note_mode = get_state(request)
    note_mode = not note_mode
    request.session['note_mode'] = note_mode
    request.session.modified = True
    notes_range = range(1, 10)
    # Render the full grid.html so the button label updates
    return render(request, 'sudoku/grid.html', {
        'grid': grid,
        'selected': selected,
        'notes_range': notes_range,
        'note_mode': note_mode,
    })
