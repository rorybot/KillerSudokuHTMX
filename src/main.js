import './style.css'

let noteMode = false;
let selected = { row: null, col: null };
// Store cell state: {final: number|null, notes: Set<number>}
const gridState = Array.from({length:9},()=>Array.from({length:9},()=>({final:null,notes:new Set()})));

function renderGrid() {
  let html = `<div class="ks-container">
      <div class="ks-controls">
        <button id="toggle-mode" aria-pressed="${noteMode}" aria-label="Toggle note mode">
          ${noteMode ? 'Note Mode ✏️' : 'Number Mode 1️⃣'}
        </button>
      </div>
      <div class="ks-grid" role="grid" aria-label="Killer Sudoku Grid">
`;
  for (let r = 0; r < 9; r++) {
    html += '<div class="ks-row" role="row">';
    for (let c = 0; c < 9; c++) {
      const cell = gridState[r][c];
      const isSelected = selected.row === r && selected.col === c;
      html += `<div class="ks-cell${isSelected ? ' ks-cell-selected' : ''}" role="gridcell" tabindex="0" data-row="${r}" data-col="${c}">
        <div class="ks-final">${cell.final ? cell.final : ''}</div>
        <div class="ks-notes">
          ${Array.from({length:9}, (_,i) => `<span class="ks-note n${i+1}">${cell.notes.has(i+1) ? i+1 : ''}</span>`).join('')}
        </div>
      </div>`;
    }
    html += '</div>';
  }
  html += '</div></div>';
  document.querySelector('#app').innerHTML = html;
}

function selectCell(r, c) {
  selected = { row: r, col: c };
  renderGrid();
}

function handleCellInput(num) {
  if (selected.row === null || selected.col === null) return;
  const cell = gridState[selected.row][selected.col];
  if (noteMode) {
    cell.final = null; // Clear final if adding a note
    if (cell.notes.has(num)) cell.notes.delete(num);
    else cell.notes.add(num);
  } else {
    cell.final = num;
    cell.notes.clear();
  }
  renderGrid();
}

function handleCellClear() {
  if (selected.row === null || selected.col === null) return;
  const cell = gridState[selected.row][selected.col];
  cell.final = null;
  cell.notes.clear();
  renderGrid();
}

renderGrid();

document.addEventListener('click', (e) => {
  if (e.target.id === 'toggle-mode') {
    noteMode = !noteMode;
    renderGrid();
    return;
  }
  const cell = e.target.closest('.ks-cell');
  if (cell) {
    const r = +cell.dataset.row, c = +cell.dataset.col;
    selectCell(r, c);
  }
});

document.addEventListener('keydown', (e) => {
  if (selected.row === null || selected.col === null) return;
  if (e.key >= '1' && e.key <= '9') {
    handleCellInput(Number(e.key));
    e.preventDefault();
  } else if (e.key === 'Backspace' || e.key === 'Delete' || e.key === '0') {
    handleCellClear();
    e.preventDefault();
  } else if (e.key === 'ArrowUp' && selected.row > 0) {
    selectCell(selected.row - 1, selected.col);
    e.preventDefault();
  } else if (e.key === 'ArrowDown' && selected.row < 8) {
    selectCell(selected.row + 1, selected.col);
    e.preventDefault();
  } else if (e.key === 'ArrowLeft' && selected.col > 0) {
    selectCell(selected.row, selected.col - 1);
    e.preventDefault();
  } else if (e.key === 'ArrowRight' && selected.col < 8) {
    selectCell(selected.row, selected.col + 1);
    e.preventDefault();
  }
});
