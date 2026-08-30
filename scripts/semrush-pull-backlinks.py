#!/usr/bin/env python3
"""
Pull backlinks from SEMrush into the AI SEO Manager dashboard.

Usage (from repo root):
  export SEMRUSH_API_KEY=your_key
  python scripts/semrush-pull-backlinks.py

Requires backend running on http://localhost:8000 (or set API_URL).
"""

from __future__ import annotations

import json
import os
import sys
import urllib.parse
import urllib.request

API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")
EMAIL = os.environ.get("SEO_LOGIN_EMAIL", "demo@example.com")
PASSWORD = os.environ.get("SEO_LOGIN_PASSWORD", "demo1234")


def api_request(path: str, method: str = "GET", data: dict | None = None, token: str | None = None):
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = json.dumps(data).encode() if data is not None else None
    req = urllib.request.Request(f"{API_URL}{path}", data=body, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode())


def login() -> str:
    form = urllib.parse.urlencode({"username": EMAIL, "password": PASSWORD}).encode()
    req = urllib.request.Request(
        f"{API_URL}/api/auth/login",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())["access_token"]


def main() -> int:
    if not os.environ.get("SEMRUSH_API_KEY"):
        print("Warning: SEMRUSH_API_KEY is not set in this shell.")
        print("Set it in backend .env too, then restart the backend.")

    print(f"Logging in to {API_URL} ...")
    token = login()
    websites = api_request("/api/websites", token=token)
    if not websites:
        print("No websites found. Run portfolio bootstrap in the dashboard first.")
        return 1

    for site in websites:
        domain = site["domain"]
        print(f"\nPulling SEMrush backlinks for {domain} (id={site['id']}) ...")
        try:
            result = api_request(
                f"/api/websites/{site['id']}/backlinks/pull-semrush",
                method="POST",
                data={},
                token=token,
            )
            print(f"  OK  synced={result.get('synced', 0)} total={result.get('total_backlinks', 0)}")
            print(f"  {result.get('message', '')}")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode()
            print(f"  FAIL HTTP {exc.code}: {detail[:300]}")

    print("\nDone. Open Dashboard > Backlinks to review imported links.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
