# Sudoku HTMX

A lightweight, session-backed Sudoku board built with Django, HTMX, and vanilla CSS/JavaScript. It supports keyboard and touch input, final numbers, 3×3 pencil notes, wraparound arrow navigation, clearing/resetting, and automatic note removal from row, column, and box peers.

## Run locally

Requires Python 3.10 or newer.

```sh
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cd src
python manage.py migrate
python manage.py runserver
```

Open http://127.0.0.1:8000/. Each browser session has its own board.

## Controls

- Click/tap a cell, then use the number pad.
- Keyboard: `1`–`9`, arrow keys, `Backspace`, or `Delete`.
- Turn **Notes on** to toggle pencil marks. Entering a final number removes that note from every peer in its row, column, and 3×3 box.
- Enter the same final number twice to clear it, or use the clear button.

## Test

```sh
cd src
python manage.py test
python manage.py check
```

For deployment, set `DJANGO_SECRET_KEY`, `DJANGO_DEBUG=false`, and a comma-separated `DJANGO_ALLOWED_HOSTS` value. Serve behind a production WSGI/ASGI server rather than Django's development server.
