"""P5D tests: research service + API — citations verbatim, official-source
prioritization, provider-failure mapping, SSRF-safe URL filtering."""

import httpx
import pytest
from httpx import AsyncClient

from app.core.security import hash_password
from app.db.models.user import User
from app.db.session import db_manager
from app.services.research import OFFICIAL_DOMAIN_SUFFIXES, ResearchService, ResearchServiceError

pytestmark = pytest.mark.usefixtures("async_initialized_db")

SEARX_RESPONSE = {
    "results": [
        {
            "title": "Blog post",
            "url": "https://farming-blog.example.com/pest",
            "content": "unofficial snippet",
        },
        {
            "title": "ICAR advisory",
            "url": "https://icar.org.in/advisory/pest",
            "content": "official snippet",
        },
        {
            "title": "Bad scheme",
            "url": "javascript:alert(1)",
            "content": "should be dropped",
        },
    ]
}


def _svc() -> ResearchService:
    from app.core.config import Settings

    return ResearchService(Settings())


async def _mock_search(monkeypatch, payload, error=None):
    class _Resp:
        def raise_for_status(self):
            pass

        def json(self):
            if error:
                raise error
            return payload

    async def fake_get(self, url, params=None):
        if error == "http":
            raise httpx.ConnectError("down")
        return _Resp()

    monkeypatch.setattr(httpx.AsyncClient, "get", fake_get)


async def test_official_sources_prioritized_and_urls_verbatim(monkeypatch) -> None:
    await _mock_search(monkeypatch, SEARX_RESPONSE)
    results = await _svc().search("pest control cotton")
    assert [r.official_source for r in results][0] is True  # icar.org.in first
    assert results[0].url == "https://icar.org.in/advisory/pest"  # verbatim
    assert results[0].source_domain == "icar.org.in"
    assert all(r.source_domain not in ("", None) for r in results)


async def test_non_http_urls_dropped(monkeypatch) -> None:
    await _mock_search(monkeypatch, SEARX_RESPONSE)
    results = await _svc().search("pest control cotton")
    assert all(r.url.startswith(("http://", "https://")) for r in results)
    assert len(results) == 2


async def test_no_results_empty_not_error(monkeypatch) -> None:
    await _mock_search(monkeypatch, {"results": []})
    assert await _svc().search("xyzzy unknown") == []


async def test_provider_failure_raises_service_error(monkeypatch) -> None:
    await _mock_search(monkeypatch, {}, error="http")
    with pytest.raises(ResearchServiceError):
        await _svc().search("anything")


async def test_research_endpoint_requires_auth(async_client: AsyncClient) -> None:
    resp = await async_client.get("/api/v1/research", params={"q": "rice"})
    assert resp.status_code == 401


async def test_research_endpoint_provider_down_503(async_client: AsyncClient, monkeypatch) -> None:
    user = User(email="p5d-a@verifytest.com", password_hash=hash_password("Pass-2026!x"))
    async with db_manager.session() as session:
        session.add(user)
    login = await async_client.post(
        "/api/v1/auth/login",
        json={"email": "p5d-a@verifytest.com", "password": "Pass-2026!x"},
    )
    assert login.status_code == 200

    svc = ResearchService

    async def fail(self, query, *, limit=8):
        raise ResearchServiceError("search provider unavailable: ConnectError")

    monkeypatch.setattr(svc, "search", fail)
    resp = await async_client.get("/api/v1/research", params={"q": "rice blast"})
    assert resp.status_code == 503
    assert resp.json()["error_code"] == "RESEARCH_UNAVAILABLE"


def test_official_suffix_list_sane() -> None:
    assert any(s.endswith("gov.in") for s in OFFICIAL_DOMAIN_SUFFIXES)
