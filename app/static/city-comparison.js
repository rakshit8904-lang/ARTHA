(() => {
  const cards = [...document.querySelectorAll('.locality-card')];
  if (!cards.length) return;
  const fmt = n => '₹' + Math.round(n).toLocaleString('en-IN');

  function update() {
    const rows = cards.map(card => {
      const fields = [...card.querySelectorAll('[data-cost]')];
      const values = fields.map(field => field.value.trim() === '' ? null : Number(field.value));
      const known = values.filter(value => value !== null && Number.isFinite(value) && value >= 0);
      const total = known.reduce((sum, value) => sum + value, 0);
      card.querySelector('.tier-total').textContent = known.length ? fmt(total) : '—';
      card.querySelector('.tier-completeness').textContent =
        `${known.length} of ${fields.length} categories entered`;
      return {
        name: card.querySelector('.locality-name').value.trim() ||
          card.querySelector('.tier-label').textContent,
        total,
        count: known.length
      };
    });

    const output = document.getElementById('city-comparison-results');
    const valid = rows.filter(row => row.count);
    if (!valid.length) {
      output.textContent = 'Enter costs above to compare localities.';
      return;
    }

    const max = Math.max(...valid.map(row => row.total), 1);
    output.replaceChildren();
    valid.forEach(row => {
      const line = document.createElement('div');
      line.className = 'compare-row';
      const name = document.createElement('span');
      name.textContent = row.name;
      const track = document.createElement('div');
      track.className = 'compare-track';
      const bar = document.createElement('i');
      bar.style.width = `${Math.max(2, row.total / max * 100)}%`;
      track.appendChild(bar);
      const amount = document.createElement('strong');
      amount.textContent = fmt(row.total);
      const coverage = document.createElement('small');
      coverage.textContent = `${row.count}/9 categories`;
      line.append(name, track, amount, coverage);
      output.appendChild(line);
    });
  }

  document.querySelectorAll('.locality-card input').forEach(input => {
    input.addEventListener('input', update);
  });
  update();
})();
