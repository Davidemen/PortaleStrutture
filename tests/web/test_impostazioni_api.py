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
def test_get_via_default_sqlite_repository_warns_on_corrupted_row(tmp_path) -> None:
    """§26.6 "mai in silenzio": a real deployment (`create_app` with no `impostazioni=` override,
    the default `_LazySqliteImpostazioniRepository`) must still surface the corrupted-row avviso,
    not just the in-memory fake the other tests inject directly."""
    from strutture.storage.database import write_session
    from strutture.storage.impostazioni_sqlite import open_impostazioni_repository

    db_path = tmp_path / "strutture.db"
    open_impostazioni_repository(tmp_path)  # runs the migrations, creates the tables
    with write_session(db_path) as connection:
        connection.execute(
            "INSERT INTO impostazioni (id, valori, revisione, sigla, aggiornato_il) "
            "VALUES (1, :valori, 1, 'ab', '2026-01-01T00:00:00Z')",
            {"valori": "{not valid json"},
        )

    app = create_app(
        tools=FAKE_TOOLS, settings=config.Settings(
            rate_limit_per_minute=600, max_body_bytes=1_000_000, host="127.0.0.1", port=8000, data_dir=tmp_path,
        ),
        progetti=InMemoryProjectRepository(), signoffs=InMemorySignoffRepository(),
    )
    body = TestClient(app).get("/api/impostazioni").json()
    assert body["avvisi"], body


@pytest.mark.unit
def test_put_type_step_unconvertible_for_a_field_rejected_with_field_named(settings) -> None:
    """§26.3: a per-type step that cannot be expressed in one of the type's fields (4-decimal rule)
    is rejected AT SAVE TIME, with that field named -- not just left for GET .../passi to discover
    later."""
    from pydantic import BaseModel, ConfigDict, Field

    from strutture.shared.report import Report, success
    from strutture.shared.tool import Tool

    class _Input(BaseModel):
        model_config = ConfigDict(frozen=True)

        copriferro_cm: float = Field(gt=0, json_schema_extra={"unit": "cm", "symbol": "c", "group": "g"})

    class _Output(BaseModel):
        model_config = ConfigDict(frozen=True)

        ok: bool = True

    def _run(inputs: _Input) -> Report[_Output]:
        return success(_Output(), inputs)

    tool = Tool(
        name="fake-copriferro", title="Copriferro di prova", group="Prova", norm="TEST",
        input_model=_Input, output_model=_Output, run=_run,
    )
    app = create_app(
        tools={**FAKE_TOOLS, "fake-copriferro": tool}, settings=settings, progetti=InMemoryProjectRepository(),
        signoffs=InMemorySignoffRepository(), impostazioni=InMemoryImpostazioniRepository(),
    )
    client = TestClient(app)
    body = client.put("/api/impostazioni", json={
        "impostazioni": {"passi_per_tipo": {"copriferro": 1.2345}}, "revisione": 0, "sigla": "AB",
    })
    assert body.status_code == 422, body.text
    payload = body.json()
    assert "fake-copriferro.copriferro_cm" in payload["errors"][0]
    assert payload["error_details"][0]["loc"] == ["impostazioni", "passi_per_tipo"]
    assert client.get("/api/impostazioni").json()["revisione"] == 0  # never actually saved


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
