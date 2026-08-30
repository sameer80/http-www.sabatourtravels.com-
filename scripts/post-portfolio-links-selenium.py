#!/usr/bin/env python3
"""
Post cross-portfolio backlinks on YOUR WordPress sites using Selenium WebDriver.

IMPORTANT:
- Only use on websites you own (onewaydrop.cab, sabacabs.com, punetomumbaicabservice.com).
- Copy scripts/link-post-config.example.json to scripts/link-post-config.json
- Set WordPress credentials in environment variables (see config file).
- Start with dry_run=true, then set dry_run=false to publish.

Install:
  pip install -r scripts/requirements-selenium.txt

Run (Windows / Linux):
  python scripts/post-portfolio-links-selenium.py
"""

from __future__ import annotations

import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "scripts" / "link-post-config.json"
EXAMPLE_PATH = ROOT / "scripts" / "link-post-config.example.json"


def load_config() -> dict:
    path = CONFIG_PATH if CONFIG_PATH.exists() else EXAMPLE_PATH
    with open(path, encoding="utf-8") as fh:
        config = json.load(fh)
    if path == EXAMPLE_PATH:
        print(f"Using example config: {EXAMPLE_PATH}")
        print("Copy to scripts/link-post-config.json and add your WordPress credentials.")
    return config


def fetch_cross_link_plan(config: dict) -> list[dict]:
    api_url = config.get("api_url", "http://localhost:8000").rstrip("/")
    email = config.get("login_email", "demo@example.com")
    password = config.get("login_password", "demo1234")
    form = urllib.parse.urlencode({"username": email, "password": password}).encode()
    login_req = urllib.request.Request(
        f"{api_url}/api/auth/login",
        data=form,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(login_req, timeout=30) as resp:
        token = json.loads(resp.read().decode())["access_token"]
    plan_req = urllib.request.Request(
        f"{api_url}/api/portfolio/cross-links/plan",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urllib.request.urlopen(plan_req, timeout=30) as resp:
        payload = json.loads(resp.read().decode())
    return payload.get("plan", [])


def group_plan_by_source(plan: list[dict]) -> dict[str, list[dict]]:
    grouped: dict[str, list[dict]] = {}
    for item in plan:
        grouped.setdefault(item["source_domain"], []).append(item)
    return grouped


def build_partners_html(links: list[dict]) -> str:
    lines = ['<h2>Our travel websites</h2>', '<ul>']
    for link in links:
        lines.append(
            f'  <li><a href="{link["target_url"]}" rel="noopener">{link["anchor_text"]}</a></li>'
        )
    lines.append("</ul>")
    return "\n".join(lines)


def wp_login(driver, login_url: str, username: str, password: str) -> None:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.webdriver.support.ui import WebDriverWait

    driver.get(login_url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "user_login")))
    driver.find_element(By.ID, "user_login").clear()
    driver.find_element(By.ID, "user_login").send_keys(username)
    driver.find_element(By.ID, "user_pass").clear()
    driver.find_element(By.ID, "user_pass").send_keys(password)
    driver.find_element(By.ID, "wp-submit").click()
    WebDriverWait(driver, 20).until(lambda d: "wp-admin" in d.current_url)


def upsert_partners_page(driver, base_url: str, slug: str, title: str, html: str) -> str:
    """Create or update a WordPress page using REST API with authenticated browser session."""
    driver.get(f"{base_url.rstrip('/')}/wp-admin/")
    time.sleep(2)
    nonce = driver.execute_script(
        "return (window.wpApiSettings && window.wpApiSettings.nonce) || '';"
    )
    if not nonce:
        raise RuntimeError("Could not read WordPress REST nonce. Check admin login.")

    script = """
    const slug = arguments[0];
    const title = arguments[1];
    const html = arguments[2];
    const nonce = arguments[3];
    const root = window.wpApiSettings.root;
    async function run() {
      let pageRes = await fetch(root + 'pages?slug=' + encodeURIComponent(slug), {
        headers: { 'X-WP-Nonce': nonce }
      });
      let pages = await pageRes.json();
      let payload = { title, status: 'publish', content: html };
      if (pages.length) {
        const id = pages[0].id;
        const upd = await fetch(root + 'pages/' + id, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'X-WP-Nonce': nonce },
          body: JSON.stringify(payload)
        });
        return await upd.json();
      }
      const crt = await fetch(root + 'pages', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-WP-Nonce': nonce },
        body: JSON.stringify({ ...payload, slug })
      });
      return await crt.json();
    }
    return run();
    """
    result = driver.execute_script(script, slug, title, html, nonce)
    if isinstance(result, dict) and result.get("link"):
        return result["link"]
    if isinstance(result, dict) and result.get("message"):
        raise RuntimeError(result["message"])
    return f"{base_url.rstrip('/')}/{slug}/"


def main() -> int:
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
    except ImportError:
        print("Install Selenium first: pip install -r scripts/requirements-selenium.txt")
        return 1

    config = load_config()
    dry_run = bool(config.get("dry_run", True))
    headless = bool(config.get("headless", False))
    sites_cfg = config.get("sites", {})

    print("Fetching cross-link plan from API ...")
    plan = fetch_cross_link_plan(config)
    grouped = group_plan_by_source(plan)
    print(f"Plan: {len(plan)} cross-links across {len(grouped)} source sites")

    if dry_run:
        print("\nDRY RUN - no WordPress changes will be made\n")
        for domain, links in grouped.items():
            print(f"[{domain}] would publish {len(links)} link(s):")
            for link in links:
                print(f"  -> {link['target_url']}  anchor={link['anchor_text']!r}")
        print("\nSet dry_run=false in link-post-config.json to publish.")
        return 0

    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1400,900")
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        for domain, links in grouped.items():
            site = sites_cfg.get(domain)
            if not site:
                print(f"Skip {domain}: not configured in link-post-config.json")
                continue
            username = os.environ.get(site["username_env"], "")
            password = os.environ.get(site["password_env"], "")
            if not username or not password:
                print(f"Skip {domain}: set {site['username_env']} and {site['password_env']} env vars")
                continue

            slug = site.get("partners_page_slug", "our-travel-websites")
            title = site.get("partners_page_title", "Our Travel Websites")
            base_url = links[0]["source_base_url"]
            html = build_partners_html(links)

            print(f"\nPosting on {domain} ...")
            wp_login(driver, site["wp_login_url"], username, password)
            page_url = upsert_partners_page(driver, base_url, slug, title, html)
            print(f"  Published/updated: {page_url}")
    finally:
        driver.quit()

    print("\nCross-portfolio links posted on your WordPress sites.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
