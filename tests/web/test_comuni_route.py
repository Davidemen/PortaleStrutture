"""GET /api/comuni powers the searchable comune dropdown."""
import pytest
from fastapi.testclient import TestClient

from strutture.web import create_app

pytestmark = pytest.mark.integration


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(tools={}))


def test_search_returns_labelled_options(client: TestClient) -> None:
    response = client.get("/api/comuni", params={"q": "berg"})
    assert response.status_code == 200
    first = response.json()[0]
    assert set(first) == {"label", "comune", "provincia", "regione"}
    assert any(option["label"] == "Bergamo" for option in response.json())


def test_search_disambiguates_homonyms_and_honours_limit(client: TestClient) -> None:
    labels = [o["label"] for o in client.get("/api/comuni", params={"q": "castro", "limit": 50}).json()]
    assert "Castro (Bergamo)" in labels and "Castro (Lecce)" in labels
    assert len(client.get("/api/comuni", params={"q": "san", "limit": 5}).json()) == 5


@pytest.mark.parametrize("params", [{"q": "b"}, {"q": "x" * 61}, {"q": "berg", "limit": 0}, {"q": "berg", "limit": 51}, {}])
def test_search_validates_query(client: TestClient, params: dict) -> None:
    assert client.get("/api/comuni", params=params).status_code == 422


def test_unknown_prefix_returns_empty_list(client: TestClient) -> None:
    assert client.get("/api/comuni", params={"q": "zzzz"}).json() == []
