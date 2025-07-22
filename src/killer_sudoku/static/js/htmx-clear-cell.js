console.log('htmx-clear-cell.js loaded');
document.addEventListener('keydown', function(e) {
  if (e.key === 'Backspace' || e.key === 'Delete') {
    htmx.ajax('POST', '/clear/', {target: '.ks-grid', swap: 'outerHTML'});
    e.preventDefault();
  }
});
