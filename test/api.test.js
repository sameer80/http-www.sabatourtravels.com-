'use strict';

const { test, after } = require('node:test');
const assert = require('node:assert');
const app = require('../server');

const server = app.listen(0);
const base = () => `http://localhost:${server.address().port}`;

after(() => server.close());

test('GET /api/health returns ok', async () => {
  const res = await fetch(`${base()}/api/health`);
  assert.strictEqual(res.status, 200);
  const body = await res.json();
  assert.strictEqual(body.status, 'ok');
});

test('GET /api/packages returns packages', async () => {
  const res = await fetch(`${base()}/api/packages`);
  assert.strictEqual(res.status, 200);
  const body = await res.json();
  assert.ok(Array.isArray(body.packages));
  assert.ok(body.packages.length >= 1);
});

test('POST /api/inquiries creates an inquiry', async () => {
  const res = await fetch(`${base()}/api/inquiries`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'Test', email: 't@example.com', destination: 'Goa' }),
  });
  assert.strictEqual(res.status, 201);
  const body = await res.json();
  assert.strictEqual(body.ok, true);
  assert.match(body.reference, /^SABA-\d{4}$/);
});

test('POST /api/inquiries validates required fields', async () => {
  const res = await fetch(`${base()}/api/inquiries`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ name: 'No Destination' }),
  });
  assert.strictEqual(res.status, 400);
});
