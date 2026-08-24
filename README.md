# Saba Tour & Travels

A small travel-agency website for **sabatourtravels.com**, built with a static
frontend and an Express booking-inquiry API.

## Tech stack

- **Backend:** Node.js + [Express](https://expressjs.com/) (`server.js`)
- **Frontend:** static HTML/CSS/JS served from `public/`
- **Tests:** Node's built-in test runner (`node --test`)

## Getting started

```bash
npm install        # install dependencies
npm run dev        # start with auto-reload at http://localhost:3000
# or
npm start          # start without watch mode
```

Then open http://localhost:3000.

## API

| Method | Route              | Description                                  |
| ------ | ------------------ | -------------------------------------------- |
| GET    | `/api/health`      | Health check.                                |
| GET    | `/api/packages`    | List featured travel packages.               |
| POST   | `/api/inquiries`   | Submit a booking inquiry (`name`, `email`, `destination` required). |
| GET    | `/api/inquiries`   | List submitted inquiries (in-memory).        |

Example:

```bash
curl -s http://localhost:3000/api/health
curl -s -X POST http://localhost:3000/api/inquiries \
  -H 'Content-Type: application/json' \
  -d '{"name":"Jane","email":"jane@example.com","destination":"Kerala","travelers":2}'
```

## Tests

```bash
npm test
```

## Cloud Agent environment

Development environment configuration lives in
[`.cursor/environment.json`](.cursor/environment.json): it runs `npm install`
and starts the dev server (`npm run dev`) on port 3000.
