"""Research service (P5D): agricultural web search via SearXNG with official-
source prioritization and verifiable citations.

Security model:
- The ONLY outbound web fetch is to the configured SearXNG instance (server
  config, never user input) — SSRF by user-supplied URL is impossible by
  construction; the service never fetches result URLs itself.
- SearXNG runs loopback-only by default (Phase 0 containment).
- Result snippets are returned as data to the client; they are never
  interpolated into system prompts. A `?site:`-style re-query is out of scope.
- Citations are the provider's URLs verbatim (scheme-filtered to http/https);
  the service never fabricates or rewrites them.
"""

from datetime import UTC, datetime
from urllib.parse import urlsplit

import httpx

from app.core.config import Settings

# Official agricultural sources are ranked first (stable ordering, no score games).
OFFICIAL_DOMAIN_SUFFIXES = (
    "gov.in",
    "nic.in",
    "icar.gov.in",
    "icar.org.in",
    "kisan.gov.in",
    "agricoop.gov.in",
    "edu.in",
    "ac.in",
)


class ResearchServiceError(Exception):
    """SearXNG unavailable or failed (mapped to 503 by the router)."""


class ResearchResult:
    __slots__ = ("title", "url", "snippet", "source_domain", "official_source", "rank")

    def __init__(self, title: str, url: str, snippet: str, official_source: bool, rank: int):
        self.title = title
        self.url = url
        self.snippet = snippet
        self.source_domain = urlsplit(url).hostname or ""
        self.official_source = official_source
        self.rank = rank

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "url": self.url,
            "snippet": self.snippet,
            "source_domain": self.source_domain,
            "official_source": self.official_source,
            "rank": self.rank,
        }


def _is_official(url: str) -> bool:
    host = urlsplit(url).hostname or ""
    return any(host == s or host.endswith("." + s) for s in OFFICIAL_DOMAIN_SUFFIXES)


def _safe_url(url: str) -> str | None:
    """Only http(s) result URLs are citable; anything else is dropped."""
    scheme = urlsplit(url).scheme.lower()
    return url if scheme in ("http", "https") else None


class ResearchService:
    def __init__(self, settings: Settings):
        self._settings = settings

    async def search(self, query: str, *, limit: int = 8) -> list[ResearchResult]:
        """Query SearXNG and return officially-prioritized, citation-safe results.

        Raises ResearchServiceError on any provider failure (timeout, connect,
        HTTP error, malformed body) — the router maps this to 503.
        """
        async with httpx.AsyncClient(
            base_url=self._settings.searxng_base_url,
            timeout=httpx.Timeout(self._settings.searxng_timeout_seconds),
        ) as client:
            try:
                resp = await client.get("/search", params={"q": query, "format": "json"})
                resp.raise_for_status()
                data = resp.json()
            except (httpx.HTTPError, ValueError) as e:
                raise ResearchServiceError(
                    f"search provider unavailable: {type(e).__name__}"
                ) from e

        raw = data.get("results") or [] if isinstance(data, dict) else []
        results: list[ResearchResult] = []
        for i, item in enumerate(raw):
            url = _safe_url(item.get("url") or "")
            if not url or len(results) >= limit:
                break
            results.append(
                ResearchResult(
                    title=(item.get("title") or "")[:300],
                    url=url,
                    snippet=(item.get("content") or "")[:500],
                    official_source=_is_official(url),
                    rank=i + 1,
                )
            )
        # Official sources first (stable within tiers by provider rank).
        results.sort(key=lambda r: (not r.official_source, r.rank))
        for new_rank, r in enumerate(results, 1):
            r.rank = new_rank
        return results


def retrieved_at() -> str:
    """Freshness stamp (UTC ISO-8601) attached to every response."""
    return datetime.now(UTC).isoformat()
