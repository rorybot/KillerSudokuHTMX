let keyboardRequestQueue = Promise.resolve();

function setTheme(theme) {
  const dark = theme === 'dark';
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  const toggle = document.querySelector('#theme-toggle');
  if (toggle) {
    toggle.setAttribute('aria-pressed', String(dark));
    toggle.setAttribute('aria-label', dark ? 'Use light theme' : 'Use muted dark theme');
    toggle.textContent = dark ? 'Daylight' : 'Moonlit';
  }
}

let savedTheme = 'light';
try { savedTheme = localStorage.getItem('killer-sudoku-theme') || 'light'; } catch (_) {}
setTheme(savedTheme);

document.querySelector('#theme-toggle')?.addEventListener('click', () => {
  const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
  setTheme(nextTheme);
  try { localStorage.setItem('killer-sudoku-theme', nextTheme); } catch (_) {}
});

function queueKeyboardRequest(path, values) {
  keyboardRequestQueue = keyboardRequestQueue
    .then(() => {
      const board = document.querySelector('#sudoku-app');
      if (!board) return;
      const headers = JSON.parse(board.getAttribute('hx-headers') || '{}');
      return htmx.ajax('POST', path, {
        target: '#sudoku-app',
        swap: 'outerHTML',
        values,
        headers,
      });
    })
    .catch((error) => {
      console.error('Keyboard action failed', error);
    });
}

function moveFocusImmediately(direction) {
  const selected = document.querySelector('.ks-cell-selected');
  if (!selected) return;
  const offsets = {up: [-1, 0], down: [1, 0], left: [0, -1], right: [0, 1]};
  const [dr, dc] = offsets[direction];
  const row = (Number(selected.dataset.row) + dr + 9) % 9;
  const col = (Number(selected.dataset.col) + dc + 9) % 9;
  const next = document.querySelector(`[data-row="${row}"][data-col="${col}"]`);
  if (!next) return;

  const cage = next.dataset.cage;
  document.querySelectorAll('.ks-cell-selected').forEach((cell) => {
    cell.classList.remove('ks-cell-selected');
    cell.setAttribute('aria-selected', 'false');
  });
  document.querySelectorAll('.ks-cage-active').forEach((cell) => cell.classList.remove('ks-cage-active'));
  document.querySelectorAll(`[data-cage="${cage}"]`).forEach((cell) => cell.classList.add('ks-cage-active'));
  document.querySelectorAll('.cage-top-active, .cage-left-active').forEach((cell) => {
    cell.classList.remove('cage-top-active', 'cage-left-active');
  });
  document.querySelectorAll('.cage-top').forEach((cell) => {
    const above = document.querySelector(`[data-row="${Number(cell.dataset.row) - 1}"][data-col="${cell.dataset.col}"]`);
    if (cell.dataset.cage === cage || above?.dataset.cage === cage) cell.classList.add('cage-top-active');
  });
  document.querySelectorAll('.cage-left').forEach((cell) => {
    const left = document.querySelector(`[data-row="${cell.dataset.row}"][data-col="${Number(cell.dataset.col) - 1}"]`);
    if (cell.dataset.cage === cage || left?.dataset.cage === cage) cell.classList.add('cage-left-active');
  });
  next.classList.add('ks-cell-selected');
  next.setAttribute('aria-selected', 'true');
  next.focus({preventScroll: true});
}

document.addEventListener('keydown', (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  const directions = {ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right'};
  let path, values;
  if (/^[1-9]$/.test(event.key)) { path = '/enter/'; values = {num: event.key}; }
  else if (event.key === 'Backspace' || event.key === 'Delete') path = '/clear/';
  else if (event.key.toLowerCase() === 'n') path = '/toggle_note_mode/';
  else if (directions[event.key]) {
    moveFocusImmediately(directions[event.key]);
    path = `/move/${directions[event.key]}/`;
  }
  else return;
  event.preventDefault();
  queueKeyboardRequest(path, values);
});

document.addEventListener('htmx:afterSwap', (event) => {
  if (event.detail.target.id === 'sudoku-app') document.querySelector('.ks-cell-selected')?.focus({preventScroll: true});
});
