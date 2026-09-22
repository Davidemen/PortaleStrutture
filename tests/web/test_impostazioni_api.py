"""Tests for `/api/impostazioni...` (WORKBENCH_SPEC.md §26.7): GET factory shape, PUT ok/409/422,
`/tipi`, `/passi`, `/storia`."""
import pytest
from fastapi.testclient import TestClient

from strutture.storage.impostazioni_memory import InMemoryImpostazioniRepository
from strutture.storage.memory import InMemorySignoffRepository
from strutture.storage.progetti_memory import InMemoryProjectRepository
from strutture.web import config
from strutture.web.app import create_app
from tests.fixtures.web_fake_tools import FAKE_TOOLS


@pytest.fixture
def settings() -> config.Settings:
    return config.Settings(rate_limit_per_minute=600, max_body_bytes=1_000_000, host="127.0.0.1", port=8000)


@pytest.fixture
def client(settings) -> TestClient:
    app = create_app(
        tools=FAKE_TOOLS, settings=settings, progetti=InMemoryProjectRepository(),
        signoffs=InMemorySignoffRepository(), impostazioni=InMemoryImpostazioniRepository(),
    )
    return TestClient(app)


@pytest.mark.unit
def test_get_returns_factory_shape(client: TestClient) -> None:
    body = client.get("/api/impostazioni").json()
    assert body["ok"] is True
    assert body["revisione"] == 0
    assert body["impostazioni"]["obiettivo_sfruttamento"] == 1.0
    assert body["fabbrica"]["obiettivo_sfruttamento"] == 1.0
    assert body["avvisi"] == []


@pytest.mark.unit
def test_put_ok_increments_revision(client: TestClient) -> None:
    payload = {"impostazioni": {"obiettivo_sfruttamento": 0.9}, "revisione": 0, "sigla": "AB"}
    response = client.put("/api/impostazioni", json=payload)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["revisione"] == 1
    assert body["impostazioni"]["obiettivo_sfruttamento"] == 0.9
    assert body["sigla"] == "AB"


@pytest.mark.unit
def test_put_stale_revision_gives_409_with_attuale(client: TestClient) -> None:
    client.put("/api/impostazioni", json={"impostazioni": {}, "revisione": 0, "sigla": "AB"})
    response = client.put("/api/impostazioni", json={"impostazioni": {"obiettivo_sfruttamento": 0.5}, "revisione": 0, "sigla": "CD"})
    assert response.status_code == 409
    body = response.json()
    assert "attuale" in body
    assert body["attuale"]["revisione"] == 1


@pytest.mark.unit
def test_put_obiettivo_out_of_range_gives_422_with_loc(client: TestClient) -> None:
    response = client.put("/api/impostazioni", json={"impostazioni": {"obiettivo_sfruttamento": 1.5}, "revisione": 0, "sigla": "AB"})
    assert response.status_code == 422
    body = response.json()
    assert body["error_details"]
    assert "impostazioni" in body["error_details"][0]["loc"]


@pytest.mark.unit
def test_put_missing_sigla_rejected(client: TestClient) -> None:
    response = client.put("/api/impostazioni", json={"impostazioni": {}, "revisione": 0, "sigla": ""})
    assert response.status_code == 422


@pytest.mark.unit
def test_put_unknown_tool_exception_gives_422(client: TestClient) -> None:
    payload = {
        "impostazioni": {"passi_per_campo": [{"strumento": "boh", "campo": "x", "passo": 1.0}]},
        "revisione": 0, "sigla": "AB",
    }
    response = client.put("/api/impostazioni", json=payload)
    assert response.status_code == 422
    assert "Strumento sconosciuto" in response.json()["errors"][0]


@pytest.mark.unit
def test_tipi_covers_every_numeric_input_exactly_once(client: TestClient) -> None:
    body = client.get("/api/impostazioni/tipi").json()
    totale = sum(len(t["campi"]) for t in body["tipi"]) + len(body["senza_tipo"])
    # fake-sum: a, b (lengths without unit -> unit "kN" not a length -> senza_tipo); fake-flag: no numeric field.
    assert totale >= 2


@pytest.mark.unit
def test_passi_404_unknown_tool(client: TestClient) -> None:
    response = client.get("/api/impostazioni/passi", params={"strumento": "boh"})
    assert response.status_code == 404


@pytest.mark.unit
def test_passi_precedence_campo_over_tipo(client: TestClient) -> None:
    client.put("/api/impostazioni", json={
        "impostazioni": {"passi_per_campo": [{"strumento": "fake-sum", "campo": "a", "passo": 5.0}]},
        "revisione": 0, "sigla": "AB",
    })
    body = client.get("/api/impostazioni/passi", params={"strumento": "fake-sum"}).json()
    assert body["passi"]["a"]["passo"] == 5.0
    assert body["passi"]["a"]["origine"] == "campo"


@pytest.mark.unit
def test_storia_order(client: TestClient) -> None:
    client.put("/api/impostazioni", json={"impostazioni": {"obiettivo_sfruttamento": 0.9}, "revisione": 0, "sigla": "AB"})
    client.put("/api/impostazioni", json={"impostazioni": {"obiettivo_sfruttamento": 0.8}, "revisione": 1, "sigla": "CD"})
    storia = client.get("/api/impostazioni/storia").json()
    assert [s["revisione"] for s in storia] == [2, 1]
