# Web URL Scanner (Selenium)

A localhost web app where you enter any website URL and Selenium scans the page for:

- Page title, meta tags, and headings
- All links and images
- Forms and input fields
- Modals (dialog elements)
- External scripts and iframes

## Requirements

- Python 3.10+
- Google Chrome (for Selenium headless browser)

## Setup

```bash
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open **http://127.0.0.1:5000** in your browser, enter a URL (e.g. `https://example.com`), and click **Scan Page**.

## API

**POST** `/api/scan`

```json
{ "url": "https://example.com" }
```

Returns a JSON object with scan results.

## Project Structure

```
app.py              # Flask web server
scanner.py          # Selenium scanning logic
templates/index.html
static/style.css
requirements.txt
```
