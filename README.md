# Killer Sudoku HTMX App

I play a lot of Killer Sudoku when I'm bored, to pass the time. There's one good iOS app, but it bombards you with annoyings ads. I just wanted one of my own that I can customize and use as I like, hopefully importing some harder puzzles too. 

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

1. Install dependencies:
   ```sh
   npm install
   ```
2. Start the development server:
   ```sh
   npm run dev
   ```

## Features
- Enter final numbers or notes in each cell
- Notes are shown as small numbers in a 3x3 grid
- Only one final number per cell; entering it clears notes
- Killer Sudoku cage and grid styling

## Tech Stack
- Vite
- HTMX
- Vanilla JavaScript

---
Replace this README with more details as you build your app.
