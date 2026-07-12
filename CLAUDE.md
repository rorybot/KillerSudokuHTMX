# CLAUDE.md

This file provides guidance to coding agents working in this repository.

## Commands

All Django commands run from `src/` with the virtual environment activated (`.venv` at repo root; on Windows: `.\.venv\Scripts\Activate.ps1`).

```powershell
python -m pip install -r requirements.txt
cd src
python manage.py migrate
python manage.py runserver
python manage.py test
python manage.py check
```

## Architecture

Django + HTMX Killer Sudoku with no models and no client-side game state beyond the persisted visual theme. The solution, cages, difficulty, entries, selected cell, note mode, and completion status live in the Django session. SQLite backs sessions. Each browser session gets its own game.

Every user action is an HTMX POST that mutates the session and re-renders `board.html`, replacing `<section id="sudoku-app">`. CSRF is passed through its `hx-headers` attribute. Template nesting is `grid.html` → `board.html` → `grid_inner.html`.

`generator.py` transforms pre-verified cage topologies through digit permutations and board symmetries. Easy, Medium, and Hard use progressively fewer and larger cages; every cage has at least two cells and each topology has exactly one solution.

`views.py` owns the game rules. `enter_number` rejects values that violate row, column, 3×3 box, cage uniqueness, or cage sum feasibility. Grid cells are `{"final": int|None, "notes": [int]}`; always copy the module-level `EMPTY_GRID` before use.

`static/js/sudoku.js` maps keyboard input to the POST endpoints. Its promise queue prevents rapid keypresses from racing HTMX board replacements. It also persists the light/muted-dark visual theme in `localStorage` and restores focus after swaps.

Tests are in `src/sudoku/tests.py` and cover generation, rules, sessions, security, rendering, and endpoint behavior.
