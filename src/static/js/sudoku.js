let keyboardRequestQueue = Promise.resolve();

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
