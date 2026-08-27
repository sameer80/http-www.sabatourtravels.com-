"""Selenium-based web page scanner."""

from __future__ import annotations

import time
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager


@dataclass
class ScanResult:
    url: str
    success: bool
    title: str = ""
    page_source_length: int = 0
    load_time_ms: int = 0
    meta_tags: list[dict[str, str]] = field(default_factory=list)
    headings: dict[str, list[str]] = field(default_factory=dict)
    links: list[dict[str, str]] = field(default_factory=list)
    images: list[dict[str, str]] = field(default_factory=list)
    forms: list[dict[str, Any]] = field(default_factory=list)
    modals: list[dict[str, str]] = field(default_factory=list)
    scripts: list[str] = field(default_factory=list)
    iframes: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _create_driver(headless: bool = True) -> webdriver.Chrome:
    options = Options()
    if headless:
        options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(30)
    return driver


def _normalize_url(url: str) -> str:
    url = url.strip()
    if not url:
        raise ValueError("URL cannot be empty")
    parsed = urlparse(url)
    if not parsed.scheme:
        url = f"https://{url}"
    return url


def _text_or_empty(element) -> str:
    try:
        return (element.text or "").strip()
    except WebDriverException:
        return ""


def _attr(element, name: str) -> str:
    try:
        return element.get_attribute(name) or ""
    except WebDriverException:
        return ""


def scan_url(url: str, headless: bool = True, wait_seconds: int = 3) -> ScanResult:
    """Scan a web page and collect structural information."""
    normalized = _normalize_url(url)
    result = ScanResult(url=normalized, success=False)
    driver = None

    try:
        driver = _create_driver(headless=headless)
        start = time.time()
        driver.get(normalized)

        try:
            WebDriverWait(driver, wait_seconds).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            result.errors.append("Page body did not load within timeout")

        # Allow dynamic content / modals to render
        time.sleep(1)

        result.load_time_ms = int((time.time() - start) * 1000)
        result.title = driver.title or ""
        result.page_source_length = len(driver.page_source or "")

        # Meta tags
        for meta in driver.find_elements(By.TAG_NAME, "meta"):
            name = _attr(meta, "name") or _attr(meta, "property") or _attr(meta, "http-equiv")
            content = _attr(meta, "content")
            if name and content:
                result.meta_tags.append({"name": name, "content": content})

        # Headings h1-h6
        for level in range(1, 7):
            tag = f"h{level}"
            texts = [
                t for t in (_text_or_empty(h) for h in driver.find_elements(By.TAG_NAME, tag)) if t
            ]
            if texts:
                result.headings[tag] = texts

        # Links
        seen_links: set[str] = set()
        for link in driver.find_elements(By.TAG_NAME, "a"):
            href = _attr(link, "href")
            if not href or href in seen_links:
                continue
            seen_links.add(href)
            result.links.append(
                {
                    "text": _text_or_empty(link)[:200],
                    "href": href,
                    "target": _attr(link, "target"),
                }
            )

        # Images
        for img in driver.find_elements(By.TAG_NAME, "img"):
            src = _attr(img, "src")
            if not src:
                continue
            result.images.append(
                {
                    "src": urljoin(normalized, src),
                    "alt": _attr(img, "alt"),
                    "title": _attr(img, "title"),
                }
            )

        # Forms and inputs
        for form in driver.find_elements(By.TAG_NAME, "form"):
            inputs = []
            for inp in form.find_elements(By.CSS_SELECTOR, "input, select, textarea, button"):
                inputs.append(
                    {
                        "tag": inp.tag_name,
                        "type": _attr(inp, "type"),
                        "name": _attr(inp, "name"),
                        "id": _attr(inp, "id"),
                        "placeholder": _attr(inp, "placeholder"),
                    }
                )
            result.forms.append(
                {
                    "action": _attr(form, "action") or normalized,
                    "method": (_attr(form, "method") or "get").lower(),
                    "id": _attr(form, "id"),
                    "inputs": inputs,
                }
            )

        # Modals (common patterns)
        modal_selectors = [
            "[role='dialog']",
            ".modal",
            ".modal-dialog",
            "[aria-modal='true']",
            "[class*='modal']",
            "[id*='modal']",
        ]
        seen_modals: set[str] = set()
        for selector in modal_selectors:
            for modal in driver.find_elements(By.CSS_SELECTOR, selector):
                key = _attr(modal, "id") or _attr(modal, "class") or _text_or_empty(modal)[:80]
                if not key or key in seen_modals:
                    continue
                seen_modals.add(key)
                result.modals.append(
                    {
                        "selector": selector,
                        "id": _attr(modal, "id"),
                        "class": _attr(modal, "class"),
                        "visible": modal.is_displayed(),
                        "text_preview": _text_or_empty(modal)[:300],
                    }
                )

        # External scripts
        for script in driver.find_elements(By.TAG_NAME, "script"):
            src = _attr(script, "src")
            if src:
                result.scripts.append(urljoin(normalized, src))

        # Iframes
        for iframe in driver.find_elements(By.TAG_NAME, "iframe"):
            src = _attr(iframe, "src")
            if src:
                result.iframes.append(urljoin(normalized, src))

        result.success = True

    except ValueError as exc:
        result.errors.append(str(exc))
    except WebDriverException as exc:
        result.errors.append(f"Selenium error: {exc.msg if hasattr(exc, 'msg') else str(exc)}")
    except Exception as exc:  # noqa: BLE001
        result.errors.append(f"Unexpected error: {exc}")
    finally:
        if driver:
            driver.quit()

    return result
