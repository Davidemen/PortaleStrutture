"""HIGH 1 (security review): CSRF via a CORS "simple" cross-origin request. A cross-origin page can
POST with Content-Type text/plain without a preflight; without this middleware `request.json()`
parses the body anyway and the request is processed as if it came from the engineer's own page.
`SameOriginMiddleware` protects every unsafe /api/* request globally, not just MIDAS."""
import pytest
from fastapi.testclient import TestClient

pytestmark = pytest.mark.unit


def test_text_plain_post_to_midas_is_rejected_with_415(client: TestClient) -> None:
    response = client.post("/api/midas/reactions", content=b'{"combinazioni": []}', headers={"content-type": "text/plain"})
    assert response.status_code == 415
    body = response.json()
    assert body["ok"] is False


def test_text_plain_post_to_tools_is_rejected_with_415(client: TestClient) -> None:
    response = client.post("/api/tools/fake-sum/run", content=b'{"a": 1, "b": 2}', headers={"content-type": "text/plain"})
    assert response.status_code == 415


def test_form_urlencoded_post_is_rejected_with_415(client: TestClient) -> None:
    """The other CORS-"simple" content type curl/browsers default to; also must be rejected."""
    response = client.post("/api/tools/fake-sum/run", data={"a": 1, "b": 2})
    assert response.status_code == 415


def test_cross_site_sec_fetch_site_is_rejected_with_403(client: TestClient) -> None:
    response = client.post("/api/tools/fake-sum/run", json={"a": 1, "b": 2}, headers={"sec-fetch-site": "cross-site"})
    assert response.status_code == 403
    assert response.json()["ok"] is False


def test_same_site_sec_fetch_site_is_also_rejected_with_403(client: TestClient) -> None:
    """Only same-origin/none are safe; "same-site" (different subdomain) is still rejected."""
    response = client.post("/api/tools/fake-sum/run", json={"a": 1, "b": 2}, headers={"sec-fetch-site": "same-site"})
    assert response.status_code == 403


def test_foreign_origin_is_rejected_with_403(client: TestClient) -> None:
    response = client.post("/api/tools/fake-sum/run", json={"a": 1, "b": 2}, headers={"origin": "https://evil.example.com"})
    assert response.status_code == 403


def test_foreign_origin_same_host_different_port_is_rejected_with_403(client: TestClient) -> None:
    response = client.post("/api/tools/fake-sum/run", json={"a": 1, "b": 2}, headers={"origin": "http://testserver:9999"})
    assert response.status_code == 403


def test_same_origin_sec_fetch_site_passes(client: TestClient) -> None:
    response = client.post("/api/tools/fake-sum/run", json={"a": 1, "b": 2}, headers={"sec-fetch-site": "same-origin"})
    assert response.status_code == 200


def test_none_sec_fetch_site_passes(client: TestClient) -> None:
    """"none" = user-typed/bookmarked navigation, not a script-driven cross-origin request."""
    response = client.post("/api/tools/fake-sum/run", json={"a": 1, "b": 2}, headers={"sec-fetch-site": "none"})
    assert response.status_code == 200


def test_matching_origin_passes(client: TestClient) -> None:
    response = client.post("/api/tools/fake-sum/run", json={"a": 1, "b": 2}, headers={"origin": "http://testserver"})
    assert response.status_code == 200


def test_header_less_post_passes(client: TestClient) -> None:
    """curl, the engineer's own scripts, and TestClient by default send neither header."""
    response = client.post("/api/tools/fake-sum/run", json={"a": 1, "b": 2})
    assert response.status_code == 200


def test_get_is_unaffected_by_cross_site_headers(client: TestClient) -> None:
    response = client.get("/api/tools", headers={"sec-fetch-site": "cross-site", "origin": "https://evil.example.com"})
    assert response.status_code == 200


def test_get_is_unaffected_by_content_type(client: TestClient) -> None:
    response = client.get("/api/tools", headers={"content-type": "text/plain"})
    assert response.status_code == 200


def test_non_api_path_is_unaffected(client: TestClient) -> None:
    """Static assets are served under "/"; the middleware only guards "/api/*"."""
    response = client.get("/", headers={"sec-fetch-site": "cross-site"})
    assert response.status_code == 200
