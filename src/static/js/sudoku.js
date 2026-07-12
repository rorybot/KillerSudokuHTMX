document.addEventListener('keydown', (event) => {
  if (event.ctrlKey || event.metaKey || event.altKey) return;
  const directions = {ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right'};
  let path, values;
  if (/^[1-9]$/.test(event.key)) { path = '/enter/'; values = {num: event.key}; }
  else if (event.key === 'Backspace' || event.key === 'Delete') path = '/clear/';
  else if (directions[event.key]) path = `/move/${directions[event.key]}/`;
  else return;
  event.preventDefault();
  htmx.ajax('POST', path, {target: '#sudoku-app', swap: 'outerHTML', values});
});

document.addEventListener('htmx:afterSwap', (event) => {
  if (event.detail.target.id === 'sudoku-app') document.querySelector('.ks-cell-selected')?.focus({preventScroll: true});
});
