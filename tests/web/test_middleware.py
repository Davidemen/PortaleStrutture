import pytest
from fastapi.testclient import TestClient

from strutture.web import config
from strutture.web.app import create_app
from tests.fixtures.web_fake_tools import FAKE_TOOLS


@pytest.mark.unit
def test_security_headers_present_on_every_response(client: TestClient) -> None:
    response = client.get("/api/tools")
    assert response.headers["content-security-policy"] == "default-src 'self'; base-uri 'self'; frame-ancestors 'none'"
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert "access-control-allow-origin" not in response.headers


@pytest.mark.unit
def test_security_headers_present_even_on_rate_limited_response() -> None:
    settings = config.Settings(rate_limit_per_minute=1, max_body_bytes=1_000_000, host="127.0.0.1", port=8000)
    app = create_app(tools=FAKE_TOOLS, settings=settings)
    limited_client = TestClient(app)

    limited_client.get("/api/tools")
    response = limited_client.get("/api/tools")

    assert response.status_code == 429
    assert response.headers["x-content-type-options"] == "nosniff"


@pytest.mark.unit
def test_rate_limit_returns_429_after_limit_exceeded() -> None:
    settings = config.Settings(rate_limit_per_minute=2, max_body_bytes=1_000_000, host="127.0.0.1", port=8000)
    app = create_app(tools=FAKE_TOOLS, settings=settings)
    limited_client = TestClient(app)

    first = limited_client.get("/api/tools")
    second = limited_client.get("/api/tools")
    third = limited_client.get("/api/tools")

    assert first.status_code == 200
    assert second.status_code == 200
    assert third.status_code == 429
    body = third.json()
    assert body["ok"] is False


@pytest.mark.unit
def test_static_assets_never_count_against_the_rate_limit() -> None:
    """Static paths (`/js`, `/css`, `/fonts`) must not exhaust the budget on their own -- a page
    reload's own module fetches (~140 measured with this wave's ~40 new JS files) are not `/api`
    traffic and must never trigger a 429 that then also blocks the real calculation."""
    settings = config.Settings(rate_limit_per_minute=1, max_body_bytes=1_000_000, host="127.0.0.1", port=8000)
    app = create_app(tools=FAKE_TOOLS, settings=settings)
    limited_client = TestClient(app)

    for _ in range(5):
        limited_client.get("/js/main.js")

    assert limited_client.get("/api/tools").status_code == 200


@pytest.mark.unit
def test_body_size_cap_returns_413() -> None:
    settings = config.Settings(rate_limit_per_minute=120, max_body_bytes=10, host="127.0.0.1", port=8000)
    app = create_app(tools=FAKE_TOOLS, settings=settings)
    capped_client = TestClient(app)

    response = capped_client.post("/api/tools/fake-sum/run", json={"a": 1, "b": 2, "extra": "x" * 100})

    assert response.status_code == 413
    body = response.json()
    assert body["ok"] is False


@pytest.mark.unit
def test_static_index_is_served(client: TestClient) -> None:
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "StruttureMenni" in response.text
