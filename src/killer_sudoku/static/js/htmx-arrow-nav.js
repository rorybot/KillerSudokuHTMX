console.log('htmx-arrow-nav.js loaded');
document.addEventListener('keydown', function(e) {
  if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
    let direction = e.key.replace('Arrow', '').toLowerCase();
    htmx.ajax('GET', `/move/${direction}/`, {target: '.ks-grid', swap: 'outerHTML'});
    e.preventDefault();
  }
});
