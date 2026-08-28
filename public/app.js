'use strict';

document.getElementById('year').textContent = new Date().getFullYear();

async function loadPackages() {
  const grid = document.getElementById('package-grid');
  try {
    const res = await fetch('/api/packages');
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { packages } = await res.json();

    grid.innerHTML = packages
      .map(
        (p) => `
        <article class="package-card">
          <h3>${escapeHtml(p.title)}</h3>
          <p class="summary">${escapeHtml(p.summary)}</p>
          <div class="package-meta">
            <span class="price">$${p.priceUsd}</span>
            <span class="nights">${p.nights} nights</span>
          </div>
        </article>`
      )
      .join('');
  } catch (err) {
    grid.innerHTML = `<p class="error">Could not load packages: ${escapeHtml(err.message)}</p>`;
  }
}

const form = document.getElementById('inquiry-form');
const result = document.getElementById('inquiry-result');

form.addEventListener('input', () => {
  if (result.textContent) {
    result.className = 'inquiry-result';
    result.textContent = '';
  }
});

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  result.className = 'inquiry-result';
  result.textContent = 'Sending…';

  const payload = Object.fromEntries(new FormData(form).entries());

  try {
    const res = await fetch('/api/inquiries', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();

    if (!res.ok) throw new Error(data.error || `HTTP ${res.status}`);

    result.className = 'inquiry-result success';
    result.textContent = `Thanks, ${payload.name}! Your inquiry for ${payload.destination} is confirmed. Reference: ${data.reference}.`;
    form.reset();
  } catch (err) {
    result.className = 'inquiry-result error';
    result.textContent = `Something went wrong: ${err.message}`;
  }
});

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

loadPackages();
