"""Localhost web app for Selenium URL scanning."""

from __future__ import annotations

import json

from flask import Flask, jsonify, render_template, request

from scanner import scan_url

app = Flask(__name__)


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/api/scan")
def api_scan():
    data = request.get_json(silent=True) or {}
    url = (data.get("url") or request.form.get("url") or "").strip()

    if not url:
        return jsonify({"success": False, "errors": ["Please enter a URL"]}), 400

    result = scan_url(url)
    return jsonify(result.to_dict())


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
