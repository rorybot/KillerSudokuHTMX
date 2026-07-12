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

document.addEventListener('keydown', (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  const directions = {ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right'};
  let path, values;
  if (/^[1-9]$/.test(event.key)) { path = '/enter/'; values = {num: event.key}; }
  else if (event.key === 'Backspace' || event.key === 'Delete') path = '/clear/';
  else if (directions[event.key]) path = `/move/${directions[event.key]}/`;
  else return;
  event.preventDefault();
  queueKeyboardRequest(path, values);
});

document.addEventListener('htmx:afterSwap', (event) => {
  if (event.detail.target.id === 'sudoku-app') document.querySelector('.ks-cell-selected')?.focus({preventScroll: true});
});
