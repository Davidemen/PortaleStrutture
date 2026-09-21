"""Static assets must revalidate on every load so UI updates land without a hard refresh."""
import pytest
from fastapi.testclient import TestClient

from strutture.web import create_app

pytestmark = pytest.mark.integration


@pytest.mark.parametrize("path", ["/", "/js/forms.js", "/css/tokens.css"])
def test_static_files_are_served_with_no_cache(path: str) -> None:
    response = TestClient(create_app(tools={})).get(path)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-cache"


def test_api_responses_are_never_stored() -> None:
    response = TestClient(create_app(tools={})).get("/api/tools")
    assert response.headers["cache-control"] == "no-store"
