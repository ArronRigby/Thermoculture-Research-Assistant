"""
Web scrapers for UK news sources.

Implements :class:`BBCNewsCollector` and :class:`GuardianCollector`, both
subclasses of :class:`BaseCollector`.  They use **httpx** for async HTTP and
**BeautifulSoup4** for HTML parsing.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional
from urllib.parse import quote_plus, urljoin

import httpx
from bs4 import BeautifulSoup, Tag

from collectors.base import BaseCollector, CollectedItem
from collectors.locations import find_locations


# ---------------------------------------------------------------------------
# BBC News Collector
# ---------------------------------------------------------------------------

class BBCNewsCollector(BaseCollector):
    """
    Scrape climate-related articles from the BBC News website.

    Strategy
    --------
    1. Hit the BBC search endpoint for each climate keyword.
    2. Parse the search-results page for article links.
    3. Fetch each article page, extract headline, body, author, date.
    4. Scan the article body for UK location mentions.
    """

    BASE_URL = "https://www.bbc.co.uk"
    SEARCH_URL = "https://www.bbc.co.uk/search"

    def __init__(self, rate_limit_seconds: float = 2.0):
        super().__init__(source_name="bbc_news", rate_limit_seconds=rate_limit_seconds)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def collect(
        self,
        *,
        keywords: list[str] | None = None,
        max_results_per_keyword: int = 30,
        **kwargs,
    ) -> list[CollectedItem]:
        """
        Run the BBC News collection process.

        Parameters
        ----------
        keywords:
            Override the default climate keywords.
        max_results_per_keyword:
            Maximum number of articles to fetch per keyword.
        """
        search_terms = keywords or self.CLIMATE_KEYWORDS
        collected: list[CollectedItem] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(
            headers=self.DEFAULT_HEADERS,
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        ) as client:
            for term in search_terms:
                self.logger.info("BBC: searching for %r", term)
                keyword_items_collected = 0  # Track items for THIS keyword only
                try:
                    page = 1
                    while keyword_items_collected < max_results_per_keyword:
                        found_urls = await self._search(client, term, max_results_per_keyword, page=page)
                        if not found_urls:
                            break

                        new_urls_on_page = 0
                        for url in found_urls:
                            if url in seen_urls:
                                continue
                            seen_urls.add(url)
                            new_urls_on_page += 1

                            await self._rate_limit()

                            try:
                                item = await self._fetch_article(client, url)
                                if item is not None:
                                    collected.append(item)
                                    self.items_collected += 1
                                    keyword_items_collected += 1  # Increment per-keyword counter
                                    if keyword_items_collected >= max_results_per_keyword:
                                        break  # Stop collecting for this keyword
                            except Exception:
                                self.logger.exception("BBC: failed to fetch %s", url)

                        if new_urls_on_page == 0:
                            # If we didn't find any unique articles on this page, stop digging deeper for this term
                            break

                        page += 1
                        if page > 10: # Safety cap: don't go past 10 pages for one keyword
                            break

                except Exception:
                    self.logger.exception("BBC: search failed for %r", term)
                    continue

        self.logger.info("BBC: collected %d articles", len(collected))
        return collected

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _search(
        self,
        client: httpx.AsyncClient,
        query: str,
        max_results: int,
        page: int = 1,
    ) -> list[str]:
        """Return a list of article URLs from the BBC search page."""
        params = {"q": query, "d": "news_gnl", "page": str(page)}
        response = await client.get(self.SEARCH_URL, params=params)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        urls: list[str] = []

        # BBC search results contain links with data-testid or class-based selectors.
        # We look for anchor tags that point to /news/ article pages.
        for link in soup.find_all("a", href=True):
            href: str = link["href"]
            # Normalise relative URLs.
            if href.startswith("/"):
                href = urljoin(self.BASE_URL, href)

            # Only keep BBC News article pages.
            if "/news/" not in href and "/news/articles/" not in href:
                continue
            # Skip live pages / topic indexes.
            if "/live/" in href or "/topics/" in href:
                continue

            if href not in urls:
                urls.append(href)

            if len(urls) >= max_results:
                break

        self.logger.debug("BBC: found %d result URLs for %r", len(urls), query)
        return urls

    async def _fetch_article(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> Optional[CollectedItem]:
        """Fetch and parse a single BBC News article."""
        response = await client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title = self._extract_title(soup)
        if not title:
            self.logger.debug("BBC: no title found at %s -- skipping", url)
            return None

        body = self._extract_body(soup)
        if not body or len(body) < 100:
            self.logger.debug("BBC: article body too short at %s -- skipping", url)
            return None

        author = self._extract_author(soup)
        published_at = self._extract_date(soup)
        location_hints = [loc["name"] for loc in find_locations(body)]

        return CollectedItem(
            title=title,
            content=body,
            source_url=url,
            author=author,
            published_at=published_at,
            location_hints=location_hints,
            raw_metadata={
                "source": "bbc_news",
                "word_count": len(body.split()),
            },
        )

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> Optional[str]:
        # Try the main headline tag first.
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)
        # Fallback: <meta property="og:title">
        og = soup.find("meta", property="og:title")
        if og and isinstance(og, Tag):
            return og.get("content", "").strip() or None  # type: ignore[return-value]
        return None

    @staticmethod
    def _extract_body(soup: BeautifulSoup) -> Optional[str]:
        """Extract the main article text from a BBC article page."""
        # BBC uses <article> containing <p> tags for the body.
        article_tag = soup.find("article")
        container = article_tag if article_tag else soup

        paragraphs: list[str] = []
        for p in container.find_all("p"):  # type: ignore[union-attr]
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

        return "\n\n".join(paragraphs) if paragraphs else None

    @staticmethod
    def _extract_author(soup: BeautifulSoup) -> Optional[str]:
        # Try "author" meta tag.
        meta = soup.find("meta", attrs={"name": "author"})
        if meta and isinstance(meta, Tag):
            val = meta.get("content", "").strip()  # type: ignore[assignment]
            if val:
                return str(val)

        # Fallback: look for contributor/byline elements.
        byline = soup.find(attrs={"class": re.compile(r"byline|author", re.I)})
        if byline:
            return byline.get_text(strip=True) or None

        return None

    @staticmethod
    def _extract_date(soup: BeautifulSoup) -> Optional[datetime]:
        # Try <time datetime="...">
        time_tag = soup.find("time", attrs={"datetime": True})
        if time_tag and isinstance(time_tag, Tag):
            raw = time_tag["datetime"]
            return _parse_iso_datetime(str(raw))

        # Fallback: article:published_time meta.
        meta = soup.find("meta", property="article:published_time")
        if meta and isinstance(meta, Tag):
            raw = meta.get("content", "")
            return _parse_iso_datetime(str(raw))

        return None


# ---------------------------------------------------------------------------
# Guardian Collector
# ---------------------------------------------------------------------------

class GuardianCollector(BaseCollector):
    """
    Scrape climate-related articles from The Guardian website.

    Strategy
    --------
    1. Hit the Guardian search endpoint for each climate keyword.
    2. Parse the search-results page for article links.
    3. Fetch each article, extract headline, body, author, date.
    4. Scan the article body for UK location mentions.
    """

    BASE_URL = "https://www.theguardian.com"
    RSS_FEEDS = [
        "https://www.theguardian.com/uk/environment/rss",
        "https://www.theguardian.com/environment/climate-crisis/rss",
        "https://www.theguardian.com/environment/energy/rss",
    ]

    def __init__(self, rate_limit_seconds: float = 2.0):
        super().__init__(source_name="guardian", rate_limit_seconds=rate_limit_seconds)

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    async def collect(
        self,
        *,
        keywords: list[str] | None = None,
        max_results_per_feed: int = 50,
        **kwargs,
    ) -> list[CollectedItem]:
        """
        Run the Guardian collection process using RSS feeds.
        """
        collected: list[CollectedItem] = []
        seen_urls: set[str] = set()

        async with httpx.AsyncClient(
            headers=self.DEFAULT_HEADERS,
            timeout=httpx.Timeout(30.0),
            follow_redirects=True,
        ) as client:
            for feed_url in self.RSS_FEEDS:
                self.logger.info("Guardian: fetching RSS feed %s", feed_url)
                try:
                    article_urls = await self._parse_rss(client, feed_url, max_results_per_feed)
                except Exception:
                    self.logger.exception("Guardian: RSS fetch failed for %s", feed_url)
                    continue

                for url in article_urls:
                    if url in seen_urls:
                        continue
                    seen_urls.add(url)

                    await self._rate_limit()

                    try:
                        item = await self._fetch_article(client, url)
                        if item is not None:
                            collected.append(item)
                            self.items_collected += 1
                    except Exception:
                        self.logger.exception("Guardian: failed to fetch %s", url)

        self.logger.info("Guardian: collected %d articles from RSS", len(collected))
        return collected

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _parse_rss(
        self,
        client: httpx.AsyncClient,
        feed_url: str,
        max_results: int,
    ) -> list[str]:
        """Return a list of article URLs from the Guardian RSS feed."""
        response = await client.get(feed_url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "xml")
        urls: list[str] = []

        # RSS items have <link> elements.
        for item in soup.find_all("item"):
            link_tag = item.find("link")
            if link_tag:
                href = link_tag.get_text(strip=True)
                if href and href not in urls:
                    urls.append(href)

            if len(urls) >= max_results:
                break

        self.logger.debug("Guardian: found %d article URLs in feed %s", len(urls), feed_url)
        return urls

    async def _fetch_article(
        self,
        client: httpx.AsyncClient,
        url: str,
    ) -> Optional[CollectedItem]:
        """Fetch and parse a single Guardian article."""
        response = await client.get(url)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        title = self._extract_title(soup)
        if not title:
            self.logger.debug("Guardian: no title found at %s -- skipping", url)
            return None

        body = self._extract_body(soup)
        if not body or len(body) < 100:
            self.logger.debug("Guardian: article body too short at %s -- skipping", url)
            return None

        author = self._extract_author(soup)
        published_at = self._extract_date(soup)
        location_hints = [loc["name"] for loc in find_locations(body)]

        return CollectedItem(
            title=title,
            content=body,
            source_url=url,
            author=author,
            published_at=published_at,
            location_hints=location_hints,
            raw_metadata={
                "source": "guardian",
                "word_count": len(body.split()),
            },
        )

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> Optional[str]:
        # Guardian articles: <h1> inside <div data-gu-name="headline">.
        headline_div = soup.find("div", attrs={"data-gu-name": "headline"})
        if headline_div:
            h1 = headline_div.find("h1")
            if h1:
                return h1.get_text(strip=True)

        # Fallback: first <h1>.
        h1 = soup.find("h1")
        if h1:
            return h1.get_text(strip=True)

        og = soup.find("meta", property="og:title")
        if og and isinstance(og, Tag):
            return og.get("content", "").strip() or None  # type: ignore[return-value]
        return None

    @staticmethod
    def _extract_body(soup: BeautifulSoup) -> Optional[str]:
        """Extract the main article text from a Guardian article page."""
        # Guardian wraps article body in <div id="maincontent"> or
        # <div data-gu-name="body">.
        body_div = soup.find("div", attrs={"data-gu-name": "body"})
        if not body_div:
            body_div = soup.find("div", id="maincontent")
        if not body_div:
            body_div = soup.find("article")
        container = body_div if body_div else soup

        paragraphs: list[str] = []
        for p in container.find_all("p"):  # type: ignore[union-attr]
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

        return "\n\n".join(paragraphs) if paragraphs else None

    @staticmethod
    def _extract_author(soup: BeautifulSoup) -> Optional[str]:
        # Guardian uses <a rel="author">.
        author_tag = soup.find("a", attrs={"rel": "author"})
        if author_tag:
            return author_tag.get_text(strip=True) or None

        # Fallback: meta author tag.
        meta = soup.find("meta", attrs={"name": "author"})
        if meta and isinstance(meta, Tag):
            val = meta.get("content", "").strip()  # type: ignore[assignment]
            if val:
                return str(val)

        # Fallback: byline element.
        byline = soup.find(attrs={"class": re.compile(r"byline|contributor", re.I)})
        if byline:
            return byline.get_text(strip=True) or None

        return None

    @staticmethod
    def _extract_date(soup: BeautifulSoup) -> Optional[datetime]:
        # Try <time datetime="...">.
        time_tag = soup.find("time", attrs={"datetime": True})
        if time_tag and isinstance(time_tag, Tag):
            raw = time_tag["datetime"]
            return _parse_iso_datetime(str(raw))

        # Fallback: article:published_time meta.
        meta = soup.find("meta", property="article:published_time")
        if meta and isinstance(meta, Tag):
            raw = meta.get("content", "")
            return _parse_iso_datetime(str(raw))

        return None


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _parse_iso_datetime(raw: str) -> Optional[datetime]:
    """
    Best-effort parse of an ISO-8601 datetime string.

    Returns a timezone-aware datetime or ``None`` on failure.
    """
    if not raw:
        return None

    raw = raw.strip()

    # Try a few common formats.
    for fmt in (
        "%Y-%m-%dT%H:%M:%S.%fZ",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%S.%f%z",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(raw, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return None
