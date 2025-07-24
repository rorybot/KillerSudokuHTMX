document.addEventListener('DOMContentLoaded', function() {
  document.body.addEventListener('htmx:afterSwap', function(evt) {
    // Only run after a grid swap
    if (evt.detail.target && evt.detail.target.classList.contains('ks-grid')) {
      const selected = document.querySelector('.ks-cell-selected');
      if (selected) selected.focus();
    }
  });
});
