# Killer Sudoku HTMX App

<details>
  <summary>I play a lot of Killer Sudoku when I'm bored, to pass the time. There's one good iOS app, but it bombards you with annoyings ads...</summary>
  
<img width="2880" height="1694" alt="image" src="https://github.com/user-attachments/assets/cd6fbaa0-93fd-41ff-97c5-af0d68913a1a" />
  
</details>


 I just wanted one of my own that I can customize and use as I like, hopefully importing some harder puzzles too. 

I've been curious about HTMX for a while, been following the horse-headed man on Twitter and wanted to shake up my thinking. I'm a React dev, and I wanted to try throwing that all out the window and going with their [Hypermedia-first approach](https://htmx.org/essays/hypermedia-friendly-scripting/#prime_directive)

Goal is that this has to work as well as or better than the iOS app that I use, so I can just fire this up in the browser (served from my little lenovo home server).

- HTMX-powered interactive grid
- Toggle between entering final numbers and notes
  -- "Final" just terminology for non-notational; they can be deleted 
- Notes displayed in a 3x3 grid per cell
- Standard grid and cage styling
- Automatic note deletion
  - If you finalize a cell as '2', then all orthagonal cells with '2' noted in them have that '2' deleted
  - Same thing for relations in cages: finalizing one cell as '2' deletes the '2' note from other cells in the cage

## Getting Started

This project is now a Django + HTMX web app with a standard python build process.

### Prerequisites
- Python 3.10+
- pip
- (Recommended) virtualenv

### Installation

1. Clone the repository:
   ```sh
   git clone <your-repo-url>
   cd <repo-folder>
   ```
2. Create and activate a virtual environment:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install Python dependencies:
   ```sh
   pip install -r requirements.txt
   ```
   (If `requirements.txt` is missing, install Django and django-htmx:)
   ```sh
   pip install django django-htmx
   ```
4. Run database migrations:
   ```sh
   cd src/backend
   python manage.py migrate
   ```
5. Start the development server:
   ```sh
   python manage.py runserver
   ```
6. Open your browser to [http://localhost:8000/](http://localhost:8000/)

### Tech Stack
- Django (backend, session, templates, static files)
- HTMX (frontend interactivity)
- SQLite (default Django DB)
- Vanilla CSS
- Vanilla JS (no package.json to be found here)