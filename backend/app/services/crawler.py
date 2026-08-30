from __future__ import annotations

import re
import asyncio
from collections import deque
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import settings


@dataclass
class CrawledPage:
    url: str
    path: str
    status_code: int
    title: str | None = None
    meta_description: str | None = None
    h1: str | None = None
    headings: dict[str, list[str]] = field(default_factory=dict)
    word_count: int = 0
    canonical: str | None = None
    robots: str | None = None
    has_schema: bool = False
    images_missing_alt: int = 0
    internal_links: list[tuple[str, str]] = field(default_factory=list)
    redirect_chain: list[str] = field(default_factory=list)
    content_text: str = ""


def build_crawl_headers() -> dict[str, str]:
    return {
        "User-Agent": settings.crawl_user_agent,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
    }


class WebsiteCrawler:
    def __init__(self, base_url: str, max_pages: int | None = None):
        self.base_url = base_url.rstrip("/")
        parsed = urlparse(self.base_url)
        self.domain = parsed.netloc
        self.max_pages = max_pages or settings.max_crawl_pages
        self.visited: set[str] = set()
        self.pages: list[CrawledPage] = []
        self.robots_txt: str | None = None
        self.sitemap_urls: list[str] = []

    def _normalize_url(self, url: str) -> str:
        parsed = urlparse(url)
        path = parsed.path or "/"
        return f"{parsed.scheme}://{parsed.netloc}{path}".rstrip("/") or f"{parsed.scheme}://{parsed.netloc}/"

    def _is_internal(self, url: str) -> bool:
        parsed = urlparse(url)
        return parsed.netloc == self.domain or parsed.netloc == ""

    def _extract_sitemap_locs(self, xml_text: str) -> tuple[list[str], list[str]]:
        page_urls = re.findall(r"<loc>(.*?)</loc>", xml_text)
        if "<sitemapindex" in xml_text.lower():
            return [], page_urls
        return page_urls, []

    async def _get_with_retry(self, client: httpx.AsyncClient, url: str) -> httpx.Response | None:
        last_response: httpx.Response | None = None
        for attempt in range(settings.crawl_max_retries):
            try:
                response = await client.get(url, follow_redirects=True)
                last_response = response
                if response.status_code == 429:
                    retry_after = response.headers.get("Retry-After")
                    wait_seconds = int(retry_after) if retry_after and retry_after.isdigit() else min(60, 5 * (attempt + 1))
                    await asyncio.sleep(wait_seconds)
                    continue
                return response
            except httpx.HTTPError:
                if attempt + 1 >= settings.crawl_max_retries:
                    return last_response
                await asyncio.sleep(2 ** attempt)
        return last_response

    async def _load_sitemap_urls(self, client: httpx.AsyncClient, sitemap_url: str, depth: int = 0) -> None:
        if depth > 2 or sitemap_url in self.sitemap_urls:
            return
        self.sitemap_urls.append(sitemap_url)
        resp = await self._get_with_retry(client, sitemap_url)
        if not resp or resp.status_code != 200:
            return
        page_urls, child_sitemaps = self._extract_sitemap_locs(resp.text)
        for child in child_sitemaps[:5]:
            await asyncio.sleep(settings.crawl_delay_seconds)
            await self._load_sitemap_urls(client, child, depth + 1)
        for loc in page_urls:
            if len(self.visited) >= self.max_pages:
                break
            if self._is_internal(loc):
                self.visited.add(self._normalize_url(loc))

    async def fetch_robots_and_sitemap(self, client: httpx.AsyncClient) -> None:
        resp = await self._get_with_retry(client, f"{self.base_url}/robots.txt")
        if resp and resp.status_code == 200 and "user-agent" in resp.text.lower():
            self.robots_txt = resp.text
            for line in self.robots_txt.splitlines():
                if line.lower().startswith("sitemap:"):
                    sitemap_url = line.split(":", 1)[1].strip()
                    await self._load_sitemap_urls(client, sitemap_url)

        if not self.sitemap_urls:
            for candidate in (
                f"{self.base_url}/sitemap.xml",
                f"{self.base_url}/sitemap_index.xml",
            ):
                await self._load_sitemap_urls(client, candidate)
                if self.visited:
                    break

    def _extract_page(self, url: str, response: httpx.Response, redirect_chain: list[str]) -> CrawledPage:
        soup = BeautifulSoup(response.text, "lxml")
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None
        meta_desc_tag = soup.find("meta", attrs={"name": re.compile("^description$", re.I)})
        meta_description = meta_desc_tag.get("content", "").strip() if meta_desc_tag else None
        h1_tag = soup.find("h1")
        h1 = h1_tag.get_text(strip=True) if h1_tag else None
        headings: dict[str, list[str]] = {}
        for level in ("h1", "h2", "h3"):
            headings[level] = [tag.get_text(strip=True) for tag in soup.find_all(level)]
        canonical_tag = soup.find("link", rel="canonical")
        canonical = canonical_tag.get("href") if canonical_tag else None
        robots_tag = soup.find("meta", attrs={"name": "robots"})
        robots = robots_tag.get("content") if robots_tag else None
        has_schema = bool(soup.find("script", attrs={"type": "application/ld+json"}))
        images_missing_alt = sum(1 for img in soup.find_all("img") if not img.get("alt", "").strip())
        text = soup.get_text(" ", strip=True)
        word_count = len(re.findall(r"\w+", text))
        internal_links: list[tuple[str, str]] = []
        for anchor in soup.find_all("a", href=True):
            href = urljoin(url, anchor["href"])
            if self._is_internal(href) and not href.startswith(("mailto:", "tel:", "javascript:", "#")):
                internal_links.append((self._normalize_url(href), anchor.get_text(strip=True)[:200]))
        path = urlparse(url).path or "/"
        return CrawledPage(
            url=url,
            path=path,
            status_code=response.status_code,
            title=title,
            meta_description=meta_description,
            h1=h1,
            headings=headings,
            word_count=word_count,
            canonical=canonical,
            robots=robots,
            has_schema=has_schema,
            images_missing_alt=images_missing_alt,
            internal_links=internal_links,
            redirect_chain=redirect_chain,
            content_text=text[:5000],
        )

    async def crawl(self) -> list[CrawledPage]:
        queue: deque[str] = deque([self.base_url])
        self.visited.add(self._normalize_url(self.base_url))

        async with httpx.AsyncClient(
            timeout=settings.crawl_timeout_seconds,
            follow_redirects=True,
            headers=build_crawl_headers(),
        ) as client:
            await self.fetch_robots_and_sitemap(client)
            for url in list(self.visited):
                if url not in queue:
                    queue.append(url)

            while queue and len(self.pages) < self.max_pages:
                current_url = queue.popleft()
                redirect_chain: list[str] = []
                response = await self._get_with_retry(client, current_url)
                if response is None:
                    parsed = urlparse(current_url)
                    self.pages.append(
                        CrawledPage(
                            url=current_url,
                            path=parsed.path or "/",
                            status_code=0,
                            redirect_chain=redirect_chain,
                        )
                    )
                    continue

                if response.status_code == 429 and current_url == self.base_url:
                    await asyncio.sleep(45)
                    response = await self._get_with_retry(client, current_url)
                    if response is None:
                        parsed = urlparse(current_url)
                        self.pages.append(
                            CrawledPage(
                                url=current_url,
                                path=parsed.path or "/",
                                status_code=429,
                                redirect_chain=redirect_chain,
                            )
                        )
                        continue

                if response.status_code == 429:
                    parsed = urlparse(current_url)
                    self.pages.append(
                        CrawledPage(
                            url=current_url,
                            path=parsed.path or "/",
                            status_code=429,
                            redirect_chain=redirect_chain,
                        )
                    )
                    await asyncio.sleep(settings.crawl_delay_seconds)
                    continue

                redirect_chain = [str(r.url) for r in response.history] + [str(response.url)]
                if response.status_code >= 400 or not response.text.strip():
                    parsed = urlparse(str(response.url))
                    self.pages.append(
                        CrawledPage(
                            url=str(response.url),
                            path=parsed.path or "/",
                            status_code=response.status_code,
                            redirect_chain=redirect_chain,
                        )
                    )
                    await asyncio.sleep(settings.crawl_delay_seconds)
                    continue

                page = self._extract_page(str(response.url), response, redirect_chain)
                self.pages.append(page)

                for link_url, _ in page.internal_links:
                    normalized = self._normalize_url(link_url)
                    if normalized not in self.visited and len(self.visited) < self.max_pages:
                        self.visited.add(normalized)
                        queue.append(normalized)

                await asyncio.sleep(settings.crawl_delay_seconds)
        return self.pages
