document.body.addEventListener('htmx:beforeSwap', function(evt) {
  if (evt.detail.target && evt.detail.target.classList.contains('ks-cell')) {
    document.querySelectorAll('.ks-cell-selected').forEach(function(cell) {
      cell.classList.remove('ks-cell-selected');
    });
  }
});
