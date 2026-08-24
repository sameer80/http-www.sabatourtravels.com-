'use strict';

const path = require('path');
const express = require('express');

const app = express();
const PORT = process.env.PORT || 3000;

// In-memory store for booking inquiries. This is a starter app, so persistence
// is intentionally kept simple; swap for a database when one is introduced.
const inquiries = [];

app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

app.get('/api/health', (req, res) => {
  res.json({ status: 'ok', service: 'saba-tour-travels', uptime: process.uptime() });
});

app.get('/api/packages', (req, res) => {
  res.json({ packages });
});

app.post('/api/inquiries', (req, res) => {
  const { name, email, destination, travelers, message } = req.body || {};

  if (!name || !email || !destination) {
    return res.status(400).json({
      error: 'name, email and destination are required',
    });
  }

  const inquiry = {
    id: inquiries.length + 1,
    name,
    email,
    destination,
    travelers: Number(travelers) || 1,
    message: message || '',
    createdAt: new Date().toISOString(),
  };
  inquiries.push(inquiry);

  res.status(201).json({
    ok: true,
    reference: `SABA-${String(inquiry.id).padStart(4, '0')}`,
    inquiry,
  });
});

app.get('/api/inquiries', (req, res) => {
  res.json({ count: inquiries.length, inquiries });
});

const packages = [
  {
    id: 'goa-getaway',
    title: 'Goa Beach Getaway',
    nights: 4,
    priceUsd: 420,
    summary: 'Sun, sand and sunsets on India’s favourite coastline.',
  },
  {
    id: 'kerala-backwaters',
    title: 'Kerala Backwaters',
    nights: 5,
    priceUsd: 560,
    summary: 'Cruise the palm-fringed backwaters on a private houseboat.',
  },
  {
    id: 'rajasthan-heritage',
    title: 'Rajasthan Heritage Trail',
    nights: 7,
    priceUsd: 890,
    summary: 'Palaces, forts and desert nights across the royal state.',
  },
];

if (require.main === module) {
  app.listen(PORT, () => {
    console.log(`Saba Tour & Travels running at http://localhost:${PORT}`);
  });
}

module.exports = app;
