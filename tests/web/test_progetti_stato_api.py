"""Tests for `GET /api/progetti/{id}/stato` (WORKBENCH_SPEC.md §25.3/§25.5). In-memory project and
signoff repositories, a fixed register injected into `routes.progetti_stato.load_register`."""
import pytest
from fastapi.testclient import TestClient

from strutture.shared.divergences.models import Divergence
from strutture.storage.impostazioni_memory import InMemoryImpostazioniRepository
from strutture.storage.memory import InMemorySignoffRepository
from strutture.storage.progetti_memory import InMemoryProjectRepository
from strutture.web import config
from strutture.web.app import create_app
from tests.fixtures.web_fake_tools import FAKE_TOOLS

REGISTER: tuple[Divergence, ...] = (
    Divergence(
        id="fake-sum/coefficiente", titolo="Coefficiente da confermare", tipo="scelta_ingegneristica",
        strumenti=("fake-sum",), foglio="Valore digitato a mano", corretto="Valore proposto dal programma",
    ),
)


@pytest.fixture
def settings() -> config.Settings:
    return config.Settings(rate_limit_per_minute=600, max_body_bytes=1_000_000, host="127.0.0.1", port=8000)


@pytest.fixture
def progetti() -> InMemoryProjectRepository:
    return InMemoryProjectRepository()


@pytest.fixture
def signoffs() -> InMemorySignoffRepository:
    return InMemorySignoffRepository()


@pytest.fixture
def client(settings, progetti, signoffs, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    monkeypatch.setattr("strutture.web.routes.progetti_stato.load_register", lambda: REGISTER)
    app = create_app(
        tools=FAKE_TOOLS, settings=settings, progetti=progetti, signoffs=signoffs,
        impostazioni=InMemoryImpostazioniRepository(),
    )
    return TestClient(app)


def _crea_progetto(client: TestClient) -> str:
    return client.post("/api/progetti", json={"nome": "Prova"}).json()["id"]


def _crea_elemento(client: TestClient, progetto_id: str, *, a: float, b: float = 0.0, provenienza=None) -> dict:
    body = {
        "strumento": "fake-sum", "nome": "E", "inputs": {"a": a, "b": b},
        "provenienza": provenienza or {},
    }
    response = client.post(f"/api/progetti/{progetto_id}/elementi", json=body)
    assert response.status_code == 201, response.text
    return response.json()


def _collegamento(fornitore_id: str, valore: float) -> dict:
    return {"collegamenti": [
        {"chiave": "prova.a", "strumento": "fake-sum", "percorso": "total", "ingresso": False,
         "valore": valore, "elemento_id": fornitore_id}
    ]}


@pytest.mark.unit
def test_unknown_project_404(client: TestClient) -> None:
    response = client.get("/api/progetti/mai-esistito/stato")
    assert response.status_code == 404


@pytest.mark.unit
def test_empty_project_shape(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    body = client.get(f"/api/progetti/{progetto_id}/stato").json()
    assert body["elementi"] == {}
    assert body["conteggi"]["elementi"] == 0


@pytest.mark.unit
def test_unchanged_value_not_marked(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    fornitore = _crea_elemento(client, progetto_id, a=1, b=2)  # total = 3
    consumatore = _crea_elemento(client, progetto_id, a=0, provenienza=_collegamento(fornitore["id"], 3))
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    assert stato["elementi"][consumatore["id"]]["da_ricalcolare"] is False


@pytest.mark.unit
def test_new_revision_same_value_not_marked(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    fornitore = _crea_elemento(client, progetto_id, a=1, b=2)
    consumatore = _crea_elemento(client, progetto_id, a=0, provenienza=_collegamento(fornitore["id"], 3))
    client.put(f"/api/elementi/{fornitore['id']}", json={
        "strumento": "fake-sum", "nome": "rinominato", "inputs": {"a": 1, "b": 2}, "revisione": fornitore["revisione"],
    })
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    assert stato["elementi"][consumatore["id"]]["da_ricalcolare"] is False


@pytest.mark.unit
def test_changed_output_at_same_or_new_revision_marks_valore_cambiato(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    fornitore = _crea_elemento(client, progetto_id, a=1, b=2)
    consumatore = _crea_elemento(client, progetto_id, a=0, provenienza=_collegamento(fornitore["id"], 3))
    client.put(f"/api/elementi/{fornitore['id']}", json={
        "strumento": "fake-sum", "nome": "E", "inputs": {"a": 5, "b": 2}, "revisione": fornitore["revisione"],
    })
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    voce = stato["elementi"][consumatore["id"]]
    assert voce["da_ricalcolare"] is True
    assert voce["motivi"][0]["causa"] == "valore_cambiato"
    assert stato["conteggi"]["da_ricalcolare"] == 1


@pytest.mark.unit
def test_deleted_provider_marks_origine_eliminata(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    fornitore = _crea_elemento(client, progetto_id, a=1, b=2)
    consumatore = _crea_elemento(client, progetto_id, a=0, provenienza=_collegamento(fornitore["id"], 3))
    client.request("DELETE", f"/api/elementi/{fornitore['id']}", json={"revisione": fornitore["revisione"]})
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    assert stato["elementi"][consumatore["id"]]["motivi"][0]["causa"] == "origine_eliminata"


@pytest.mark.unit
def test_failing_provider_marks_origine_non_calcolabile(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    fornitore = _crea_elemento(client, progetto_id, a=1, b=2)
    consumatore = _crea_elemento(client, progetto_id, a=0, provenienza=_collegamento(fornitore["id"], 3))
    # push the provider's stored inputs outside the tool's validity range -> the run fails.
    client.put(f"/api/elementi/{fornitore['id']}", json={
        "strumento": "fake-sum", "nome": "E", "inputs": {"a": 1000, "b": 2}, "revisione": fornitore["revisione"],
    })
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    assert stato["elementi"][consumatore["id"]]["motivi"][0]["causa"] == "origine_non_calcolabile"


@pytest.mark.unit
def test_old_shape_provenienza_never_marks(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto_id, a=1, provenienza={"fonte": "MIDAS", "modello": "x"})
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    assert stato["elementi"][elemento["id"]]["da_ricalcolare"] is False


@pytest.mark.unit
def test_item_without_elemento_id_never_marks_origine_non_salvata(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    provenienza = {"collegamenti": [
        {"chiave": "prova.a", "strumento": "fake-sum", "percorso": "total", "ingresso": False, "valore": 3}
    ]}
    elemento = _crea_elemento(client, progetto_id, a=0, provenienza=provenienza)
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    assert stato["elementi"][elemento["id"]]["da_ricalcolare"] is False


@pytest.mark.unit
def test_chain_propagation_a_to_b_to_c(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    a = _crea_elemento(client, progetto_id, a=1, b=2)  # total 3
    b = _crea_elemento(client, progetto_id, a=0, provenienza=_collegamento(a["id"], 3))
    c = _crea_elemento(client, progetto_id, a=0, provenienza=_collegamento(b["id"], 0))
    client.put(f"/api/elementi/{a['id']}", json={
        "strumento": "fake-sum", "nome": "E", "inputs": {"a": 9, "b": 2}, "revisione": a["revisione"],
    })
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    assert stato["elementi"][b["id"]]["motivi"][0]["causa"] == "valore_cambiato"
    assert any(m["causa"] == "origine_da_ricalcolare" for m in stato["elementi"][c["id"]]["motivi"])


@pytest.mark.unit
def test_provvisorio_standard_mode_da_confermare(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto_id, a=1)
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    voce = stato["elementi"][elemento["id"]]
    assert voce["provvisorio"] is True
    assert voce["correzioni"]["da_confermare"] == 1


@pytest.mark.unit
def test_conteggi_present_in_response(client: TestClient) -> None:
    progetto_id = _crea_progetto(client)
    _crea_elemento(client, progetto_id, a=1)
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    for chiave in ("elementi", "verificati", "non_verificati", "dati_modificati", "da_ricalcolare",
                    "provvisori", "provvisori_per_origine", "controllo_rinviato", "cicli_origini"):
        assert chiave in stato["conteggi"]


@pytest.mark.unit
def test_max_ricalcoli_origini_gives_controllo_rinviato(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("strutture.web.routes.progetti_stato.MAX_RICALCOLI_ORIGINI", 1)
    progetto_id = _crea_progetto(client)
    fornitore = _crea_elemento(client, progetto_id, a=1, b=2)
    provenienza = {"collegamenti": [
        {"chiave": "prova.a", "strumento": "fake-sum", "percorso": "total", "ingresso": False,
         "valore": 3, "elemento_id": fornitore["id"]},
        {"chiave": "prova.b", "strumento": "fake-sum", "percorso": "total", "ingresso": False,
         "valore": 3, "elemento_id": fornitore["id"]},
    ]}
    consumatore = _crea_elemento(client, progetto_id, a=0, provenienza=provenienza)
    stato = client.get(f"/api/progetti/{progetto_id}/stato").json()
    cause = {m["causa"] for m in stato["elementi"][consumatore["id"]]["motivi"]}
    assert "controllo_rinviato" in cause
