# Sudoku HTMX

A lightweight, session-backed Killer Sudoku game built with Django, HTMX, and vanilla CSS/JavaScript. It generates unique puzzles at three difficulty levels, renders connected sum cages, prevents illegal row/column/box/cage entries, and recognizes completed games.

## Run locally

Requires Python 3.10 or newer. The Python launcher is normally `py` on Windows and `python3` on Linux. After the virtual environment is activated, both platforms can use `python`.

### Windows (PowerShell)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cd src
python manage.py migrate
python manage.py runserver
```

If `py` is unavailable but `python --version` reports Python 3.10 or newer, use `python -m venv .venv` instead.

### Linux or macOS

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cd src
python manage.py migrate
python manage.py runserver
```

On Debian or Ubuntu, creating the environment may first require `sudo apt install python3-venv`.

Open http://127.0.0.1:8000/. Each browser session has its own board.

## Controls

- Choose Easy, Medium, or Hard and select **New game** to generate a puzzle.
- Click/tap a cell, then use the number pad. Numbers that violate the current row, column, box, or cage are disabled.
- Keyboard: `1`-`9`, arrow keys, `Backspace`, or `Delete`.
- Turn **Notes on** to toggle pencil marks. Entering a final number removes that note from every peer in its row, column, and 3x3 box.
- Enter the same final number twice to clear it, or use the clear button.
- Use **Restart** to clear entries without changing the puzzle.
- Use **Moonlit** for a persistent, muted brown-and-orange dark theme.

Each dotted cage has a total in its top-left corner. Digits cannot repeat in a cage, and the cage's values must add to that total. Every generated puzzle uses only multi-cell cages and is verified to have exactly one solution.

## Test

From the repository root, with the virtual environment activated:

```powershell
cd src
python manage.py test
python manage.py check
```

For deployment, set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and a comma-separated `DJANGO_ALLOWED_HOSTS` value. Serve behind a production WSGI/ASGI server rather than Django's development server.
