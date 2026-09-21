"""Tests for the /api/divergences sign-off routes (roadmap Phase 1.2). The register is a fixed
tuple injected into the router factory; the repository is a tiny in-memory fake implementing
`SignoffRepository` -- never the real files, never the other agent's SQLite module."""
import pytest
from fastapi.testclient import TestClient

from strutture.shared.divergences.models import Divergence
from strutture.storage.models import MAX_NOTA, MAX_SIGLA, Signoff, Stato
from strutture.web import config
from strutture.web.app import create_app

D1 = Divergence(
    id="trave-ca/copriferro-minimo",
    titolo="Copriferro minimo fisso invece che da esposizione",
    tipo="errore_foglio",
    strumenti=("trave-ca",),
    cella="B12",
    foglio="Usa 20 mm fisso indipendentemente dalla classe di esposizione",
    corretto="Calcola il copriferro minimo da classe di esposizione e diametro (NTC2018 §4.1.6.1.3)",
    clausola="NTC2018 §4.1.6.1.3",
    impatto="copriferro 20 -> 25 mm",
)
D2 = Divergence(
    id="trave-ca/snellezza-lambda-lim",
    titolo="Snellezza limite calcolata con formula superata",
    tipo="aggiornamento_normativo",
    strumenti=("trave-ca", "pilastro-ca"),
    foglio="Usa la formula di NTC2008",
    corretto="Usa la formula di NTC2018 §4.1.2.3.9.2",
)
D3 = Divergence(
    id="muro-sostegno/capacita-portante",
    titolo="Capacità portante non calcolata dal foglio",
    tipo="da_verificare",
    strumenti=("muro-sostegno",),
    foglio="Il valore di resistenza è digitato a mano",
    corretto="Da verificare: nessuna formula di riferimento certa ancora individuata",
)
REGISTER: tuple[Divergence, ...] = (D1, D2, D3)


class FakeSignoffRepository:
    """Minimal in-memory `SignoffRepository`: append-only history per divergence id."""

    def __init__(self) -> None:
        self._history: dict[str, tuple[Signoff, ...]] = {}
        self._next_timestamp = 0

    def get(self, divergence_id: str) -> Signoff:
        history = self._history.get(divergence_id, ())
        return history[-1] if history else Signoff(divergence_id=divergence_id)

    def list_all(self) -> dict[str, Signoff]:
        return {key: value[-1] for key, value in self._history.items()}

    def set(self, divergence_id: str, stato: Stato, sigla: str, nota: str = "") -> Signoff:
        self._next_timestamp += 1
        record = Signoff(divergence_id=divergence_id, stato=stato, sigla=sigla, nota=nota, data=f"t{self._next_timestamp}")
        self._history = {**self._history, divergence_id: (*self._history.get(divergence_id, ()), record)}
        return record

    def history(self, divergence_id: str) -> tuple[Signoff, ...]:
        return self._history.get(divergence_id, ())


@pytest.fixture
def signoffs() -> FakeSignoffRepository:
    return FakeSignoffRepository()


@pytest.fixture
def settings() -> config.Settings:
    return config.Settings(rate_limit_per_minute=120, max_body_bytes=1_000_000, host="127.0.0.1", port=8000)


@pytest.fixture
def client(
    settings: config.Settings, signoffs: FakeSignoffRepository, monkeypatch: pytest.MonkeyPatch
) -> TestClient:
    """`create_app`'s signature is fixed (tools, settings, signoffs) so tests never import the real
    SQLite factory; the register injection point is `build_divergences_router`'s own `register`
    parameter, reached here by patching the loader `create_app` calls with no arguments -- the
    fixed REGISTER tuple above, never `strutture.shared.divergences.load_register`'s real files."""
    monkeypatch.setattr("strutture.web.routes.divergences.load_register", lambda: REGISTER)
    app = create_app(tools={}, settings=settings, signoffs=signoffs)
    return TestClient(app)


@pytest.mark.unit
def test_list_returns_merged_entries_and_totals(client: TestClient) -> None:
    response = client.get("/api/divergences")
    assert response.status_code == 200
    body = response.json()
    assert {e["id"] for e in body["divergenze"]} == {D1.id, D2.id, D3.id}
    entry = next(e for e in body["divergenze"] if e["id"] == D1.id)
    assert entry["titolo"] == D1.titolo
    assert entry["tipo"] == "errore_foglio"
    assert entry["clausola"] == D1.clausola
    assert entry["stato"] == "da_confermare"
    assert entry["sigla"] == ""
    assert entry["nota"] == ""
    assert entry["data"] == ""
    assert body["totali"] == {"da_confermare": 3, "approvato": 0, "respinto": 0}


@pytest.mark.unit
def test_list_filters_by_strumento(client: TestClient) -> None:
    response = client.get("/api/divergences", params={"strumento": "pilastro-ca"})
    assert response.status_code == 200
    assert {e["id"] for e in response.json()["divergenze"]} == {D2.id}


@pytest.mark.unit
def test_list_filters_by_tipo(client: TestClient) -> None:
    response = client.get("/api/divergences", params={"tipo": "da_verificare"})
    assert {e["id"] for e in response.json()["divergenze"]} == {D3.id}


@pytest.mark.unit
def test_list_filters_by_stato(client: TestClient) -> None:
    client.put(f"/api/divergences/{D1.id}/signoff", json={"stato": "approvato", "sigla": "ab"})
    response = client.get("/api/divergences", params={"stato": "approvato"})
    body = response.json()
    assert {e["id"] for e in body["divergenze"]} == {D1.id}
    assert body["totali"] == {"da_confermare": 0, "approvato": 1, "respinto": 0}


@pytest.mark.unit
def test_list_filters_by_free_text_query(client: TestClient) -> None:
    response = client.get("/api/divergences", params={"q": "copriferro"})
    assert {e["id"] for e in response.json()["divergenze"]} == {D1.id}


@pytest.mark.unit
def test_riepilogo_counts_per_tool_including_multi_tool_divergences(client: TestClient) -> None:
    response = client.get("/api/divergences/riepilogo")
    assert response.status_code == 200
    per_strumento = response.json()["per_strumento"]
    assert per_strumento["trave-ca"] == {"da_confermare": 2, "approvato": 0, "respinto": 0}
    assert per_strumento["pilastro-ca"] == {"da_confermare": 1, "approvato": 0, "respinto": 0}
    assert per_strumento["muro-sostegno"] == {"da_confermare": 1, "approvato": 0, "respinto": 0}


@pytest.mark.unit
def test_riepilogo_reflects_signoffs(client: TestClient) -> None:
    client.put(f"/api/divergences/{D2.id}/signoff", json={"stato": "respinto", "sigla": "mr", "nota": "no"})
    per_strumento = client.get("/api/divergences/riepilogo").json()["per_strumento"]
    assert per_strumento["trave-ca"] == {"da_confermare": 1, "approvato": 0, "respinto": 1}
    assert per_strumento["pilastro-ca"] == {"da_confermare": 0, "approvato": 0, "respinto": 1}


@pytest.mark.unit
def test_get_divergence_includes_history(client: TestClient) -> None:
    client.put(f"/api/divergences/{D1.id}/signoff", json={"stato": "approvato", "sigla": "ab", "nota": "ok"})
    client.put(f"/api/divergences/{D1.id}/signoff", json={"stato": "respinto", "sigla": "cd", "nota": "no"})
    response = client.get(f"/api/divergences/{D1.id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == D1.id
    assert body["stato"] == "respinto"
    assert [s["stato"] for s in body["storia"]] == ["approvato", "respinto"]


@pytest.mark.unit
def test_get_unknown_divergence_returns_404_with_italian_message(client: TestClient) -> None:
    response = client.get("/api/divergences/non-esiste/qualcosa")
    assert response.status_code == 404
    assert response.json()["ok"] is False
    assert "non-esiste/qualcosa" in response.json()["errors"][0]


@pytest.mark.unit
def test_signoff_stores_and_returns_the_record(client: TestClient) -> None:
    response = client.put(f"/api/divergences/{D1.id}/signoff", json={"stato": "approvato", "sigla": "gb", "nota": "verificato"})
    assert response.status_code == 200
    body = response.json()
    assert body["divergence_id"] == D1.id
    assert body["stato"] == "approvato"
    assert body["sigla"] == "gb"
    assert body["nota"] == "verificato"


@pytest.mark.unit
def test_signoff_allows_da_confermare_without_sigla(client: TestClient) -> None:
    response = client.put(f"/api/divergences/{D1.id}/signoff", json={"stato": "da_confermare"})
    assert response.status_code == 200
    assert response.json()["sigla"] == ""


@pytest.mark.unit
def test_signoff_requires_sigla_when_approving(client: TestClient) -> None:
    response = client.put(f"/api/divergences/{D1.id}/signoff", json={"stato": "approvato"})
    assert response.status_code == 400
    body = response.json()
    assert body["ok"] is False
    assert "sigla" in body["errors"][0]


@pytest.mark.unit
def test_signoff_rejects_sigla_over_max_length(client: TestClient) -> None:
    response = client.put(f"/api/divergences/{D1.id}/signoff", json={"stato": "approvato", "sigla": "x" * (MAX_SIGLA + 1)})
    assert response.status_code == 400


@pytest.mark.unit
def test_signoff_rejects_nota_over_max_length(client: TestClient) -> None:
    response = client.put(
        f"/api/divergences/{D1.id}/signoff", json={"stato": "approvato", "sigla": "gb", "nota": "x" * (MAX_NOTA + 1)}
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_signoff_rejects_invalid_stato(client: TestClient) -> None:
    response = client.put(f"/api/divergences/{D1.id}/signoff", json={"stato": "boh", "sigla": "gb"})
    assert response.status_code == 400


@pytest.mark.unit
def test_signoff_unknown_divergence_returns_404(client: TestClient) -> None:
    response = client.put("/api/divergences/non-esiste/qualcosa/signoff", json={"stato": "approvato", "sigla": "gb"})
    assert response.status_code == 404
    assert response.json()["ok"] is False


@pytest.mark.unit
def test_signoff_multiplo_updates_all_given_ids(client: TestClient) -> None:
    response = client.post(
        "/api/divergences/signoff-multiplo",
        json={"ids": [D1.id, D2.id], "stato": "approvato", "sigla": "gb", "nota": "bulk"},
    )
    assert response.status_code == 200
    assert response.json() == {"aggiornati": 2}
    assert client.get(f"/api/divergences/{D1.id}").json()["stato"] == "approvato"
    assert client.get(f"/api/divergences/{D2.id}").json()["stato"] == "approvato"
    assert client.get(f"/api/divergences/{D3.id}").json()["stato"] == "da_confermare"


@pytest.mark.unit
def test_signoff_multiplo_skips_unknown_ids(client: TestClient) -> None:
    response = client.post(
        "/api/divergences/signoff-multiplo",
        json={"ids": [D1.id, "non-esiste/qualcosa"], "stato": "approvato", "sigla": "gb"},
    )
    assert response.status_code == 200
    assert response.json() == {"aggiornati": 1}


@pytest.mark.unit
def test_signoff_multiplo_rejects_more_than_200_ids(client: TestClient) -> None:
    ids = [D1.id] * 201
    response = client.post("/api/divergences/signoff-multiplo", json={"ids": ids, "stato": "approvato", "sigla": "gb"})
    assert response.status_code == 400


@pytest.mark.unit
def test_signoff_multiplo_requires_sigla_when_approving(client: TestClient) -> None:
    response = client.post("/api/divergences/signoff-multiplo", json={"ids": [D1.id], "stato": "approvato"})
    assert response.status_code == 400


@pytest.mark.unit
def test_same_origin_guard_still_applies_to_put(client: TestClient) -> None:
    response = client.put(
        f"/api/divergences/{D1.id}/signoff",
        content=b'{"stato": "approvato", "sigla": "gb"}',
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 415


@pytest.mark.unit
def test_same_origin_guard_still_applies_to_bulk_post(client: TestClient) -> None:
    response = client.post(
        "/api/divergences/signoff-multiplo",
        content=b'{"ids": [], "stato": "approvato", "sigla": "gb"}',
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 415


@pytest.mark.unit
def test_unicode_notes_round_trip(client: TestClient) -> None:
    nota = "φ ≤ 30° verificato — città più àèìòù, 中文测试"
    response = client.put(f"/api/divergences/{D1.id}/signoff", json={"stato": "approvato", "sigla": "gb", "nota": nota})
    assert response.status_code == 200
    assert response.json()["nota"] == nota
    fetched = client.get(f"/api/divergences/{D1.id}")
    assert fetched.json()["nota"] == nota
