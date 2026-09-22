"""Tests for the /api/progetti and /api/elementi routes (`docs/architecture-phase3.md`). The
repository is a tiny in-memory fake implementing `ProjectRepository` -- never the real SQLite
module, which is written by another agent in parallel. Export/import are monkeypatched at the
route module's lazy-import wrappers so `strutture.storage.scambio` (also in progress) is never
touched."""
from typing import Any

import pytest
from fastapi.testclient import TestClient

from strutture.storage.interfaces import ConflictError, NotFoundError
from strutture.storage.models import Elemento, Progetto, RevisioneElemento
from strutture.web import config
from strutture.web.app import create_app
from tests.fixtures.web_fake_tools import FAKE_TOOLS


class FakeProjectRepository:
    """Minimal in-memory `ProjectRepository`: sequential ids/timestamps, optimistic locking,
    soft delete, append-only revision history."""

    def __init__(self) -> None:
        self._progetti: dict[str, Progetto] = {}
        self._elementi: dict[str, Elemento] = {}
        self._revisioni: dict[str, tuple[RevisioneElemento, ...]] = {}
        self._seq = 0

    def _next(self, prefix: str) -> str:
        self._seq += 1
        return f"{prefix}{self._seq}"

    def list_progetti(self, *, inclusi_eliminati: bool = False) -> tuple[Progetto, ...]:
        values = self._progetti.values()
        if not inclusi_eliminati:
            values = [p for p in values if not p.eliminato]
        return tuple(sorted(values, key=lambda p: p.id))

    def get_progetto(self, progetto_id: str) -> Progetto:
        progetto = self._progetti.get(progetto_id)
        if progetto is None:
            raise NotFoundError(progetto_id)
        return progetto

    def crea_progetto(self, progetto: Progetto) -> Progetto:
        new_id = self._next("p")
        ts = self._next("t")
        created = progetto.model_copy(update={"id": new_id, "revisione": 1, "creato": ts, "aggiornato": ts})
        self._progetti = {**self._progetti, new_id: created}
        return created

    def aggiorna_progetto(self, progetto: Progetto) -> Progetto:
        current = self._progetti.get(progetto.id)
        if current is None or current.eliminato:
            raise NotFoundError(progetto.id)
        if progetto.revisione != current.revisione:
            raise ConflictError(progetto.id)
        updated = current.model_copy(
            update={
                "codice": progetto.codice,
                "nome": progetto.nome,
                "committente": progetto.committente,
                "note": progetto.note,
                "revisione": current.revisione + 1,
                "aggiornato": self._next("t"),
            }
        )
        self._progetti = {**self._progetti, progetto.id: updated}
        return updated

    def elimina_progetto(self, progetto_id: str, revisione: int) -> None:
        current = self._progetti.get(progetto_id)
        if current is None:
            raise NotFoundError(progetto_id)
        if revisione != current.revisione:
            raise ConflictError(progetto_id)
        updated = current.model_copy(update={"eliminato": self._next("t"), "revisione": current.revisione + 1})
        self._progetti = {**self._progetti, progetto_id: updated}

    def ripristina_progetto(self, progetto_id: str) -> Progetto:
        current = self._progetti.get(progetto_id)
        if current is None:
            raise NotFoundError(progetto_id)
        updated = current.model_copy(
            update={"eliminato": "", "revisione": current.revisione + 1, "aggiornato": self._next("t")}
        )
        self._progetti = {**self._progetti, progetto_id: updated}
        return updated

    def list_elementi(self, progetto_id: str, *, inclusi_eliminati: bool = False) -> tuple[Elemento, ...]:
        if progetto_id not in self._progetti:
            raise NotFoundError(progetto_id)
        return tuple(e for e in self._elementi.values() if e.progetto_id == progetto_id and (inclusi_eliminati or not e.eliminato))

    def ripristina_elemento(self, elemento_id: str) -> Elemento:
        current = self._elementi.get(elemento_id)
        if current is None:
            raise NotFoundError(elemento_id)
        updated = current.model_copy(update={"eliminato": "", "revisione": current.revisione + 1, "aggiornato": self._next("t")})
        self._elementi[elemento_id] = updated
        return updated

    def get_elemento(self, elemento_id: str) -> Elemento:
        elemento = self._elementi.get(elemento_id)
        if elemento is None:
            raise NotFoundError(elemento_id)
        return elemento

    def crea_elemento(self, elemento: Elemento, *, sigla: str = "", nota: str = "") -> Elemento:
        if elemento.progetto_id not in self._progetti:
            raise NotFoundError(elemento.progetto_id)
        new_id = self._next("e")
        ts = self._next("t")
        created = elemento.model_copy(update={"id": new_id, "revisione": 1, "creato": ts, "aggiornato": ts})
        self._elementi = {**self._elementi, new_id: created}
        self._append_revisione(created, sigla, nota)
        return created

    def aggiorna_elemento(self, elemento: Elemento, *, sigla: str = "", nota: str = "") -> Elemento:
        current = self._elementi.get(elemento.id)
        if current is None:
            raise NotFoundError(elemento.id)
        if elemento.revisione != current.revisione:
            raise ConflictError(elemento.id)
        updated = current.model_copy(
            update={
                "strumento": elemento.strumento,
                "nome": elemento.nome,
                "inputs": elemento.inputs,
                "sintesi": elemento.sintesi,
                "stato": elemento.stato,
                "modalita": elemento.modalita,
                "provenienza": elemento.provenienza,
                "versione_app": elemento.versione_app,
                "revisione": current.revisione + 1,
                "aggiornato": self._next("t"),
            }
        )
        self._elementi = {**self._elementi, elemento.id: updated}
        self._append_revisione(updated, sigla, nota)
        return updated

    def duplica_elemento(self, elemento_id: str, nuovo_nome: str) -> Elemento:
        current = self._elementi.get(elemento_id)
        if current is None:
            raise NotFoundError(elemento_id)
        new_id = self._next("e")
        ts = self._next("t")
        duplicated = current.model_copy(
            update={"id": new_id, "nome": nuovo_nome, "revisione": 1, "creato": ts, "aggiornato": ts}
        )
        self._elementi = {**self._elementi, new_id: duplicated}
        self._append_revisione(duplicated, "", "")
        return duplicated

    def elimina_elemento(self, elemento_id: str, revisione: int) -> None:
        current = self._elementi.get(elemento_id)
        if current is None:
            raise NotFoundError(elemento_id)
        if revisione != current.revisione:
            raise ConflictError(elemento_id)
        updated = current.model_copy(update={"eliminato": self._next("t"), "revisione": current.revisione + 1})
        self._elementi = {**self._elementi, elemento_id: updated}

    def revisioni(self, elemento_id: str) -> tuple[RevisioneElemento, ...]:
        if elemento_id not in self._elementi:
            raise NotFoundError(elemento_id)
        return self._revisioni.get(elemento_id, ())

    def _append_revisione(self, elemento: Elemento, sigla: str, nota: str) -> None:
        record = RevisioneElemento(
            elemento_id=elemento.id,
            revisione=elemento.revisione,
            inputs=elemento.inputs,
            sintesi=elemento.sintesi,
            sigla=sigla,
            nota=nota,
            data=self._next("t"),
        )
        self._revisioni = {**self._revisioni, elemento.id: (*self._revisioni.get(elemento.id, ()), record)}


@pytest.fixture
def progetti() -> FakeProjectRepository:
    return FakeProjectRepository()


@pytest.fixture
def settings() -> config.Settings:
    return config.Settings(rate_limit_per_minute=120, max_body_bytes=1_000_000, host="127.0.0.1", port=8000)


@pytest.fixture
def client(settings: config.Settings, progetti: FakeProjectRepository) -> TestClient:
    app = create_app(tools=FAKE_TOOLS, settings=settings, progetti=progetti)
    return TestClient(app)


def _crea_progetto(client: TestClient, nome: str = "Palazzina A") -> dict[str, Any]:
    response = client.post("/api/progetti", json={"nome": nome, "codice": "J-001"})
    assert response.status_code == 201
    return response.json()


def _crea_elemento(client: TestClient, progetto_id: str, nome: str = "Plinto P1") -> dict[str, Any]:
    response = client.post(
        f"/api/progetti/{progetto_id}/elementi",
        json={"strumento": "fake-sum", "nome": nome, "inputs": {"a": 1, "b": 2}},
    )
    assert response.status_code == 201
    return response.json()


# ---- progetti CRUD ----


@pytest.mark.unit
def test_create_and_get_progetto(client: TestClient) -> None:
    created = _crea_progetto(client)
    assert created["nome"] == "Palazzina A"
    assert created["revisione"] == 1
    assert created["id"]

    response = client.get(f"/api/progetti/{created['id']}")
    assert response.status_code == 200
    assert response.json() == created


@pytest.mark.unit
def test_list_progetti_excludes_deleted_by_default(client: TestClient) -> None:
    created = _crea_progetto(client)
    client.request("DELETE", f"/api/progetti/{created['id']}", json={"revisione": created["revisione"]})

    active = client.get("/api/progetti").json()
    assert active == []

    everything = client.get("/api/progetti", params={"inclusi_eliminati": True}).json()
    assert {p["id"] for p in everything} == {created["id"]}


@pytest.mark.unit
def test_get_progetto_unknown_returns_404(client: TestClient) -> None:
    response = client.get("/api/progetti/does-not-exist")
    assert response.status_code == 404
    assert response.json()["ok"] is False


@pytest.mark.unit
def test_create_progetto_validation_error_returns_400(client: TestClient) -> None:
    response = client.post("/api/progetti", json={"nome": ""})
    assert response.status_code == 400
    assert response.json()["ok"] is False


@pytest.mark.unit
def test_update_progetto_success(client: TestClient) -> None:
    created = _crea_progetto(client)
    response = client.put(
        f"/api/progetti/{created['id']}",
        json={"nome": "Palazzina B", "codice": "J-002", "revisione": created["revisione"]},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["nome"] == "Palazzina B"
    assert body["revisione"] == 2


@pytest.mark.unit
def test_update_progetto_stale_revisione_returns_409_with_current_record(client: TestClient) -> None:
    created = _crea_progetto(client)
    client.put(f"/api/progetti/{created['id']}", json={"nome": "Palazzina B", "revisione": created["revisione"]})

    stale = client.put(f"/api/progetti/{created['id']}", json={"nome": "Palazzina C", "revisione": created["revisione"]})
    assert stale.status_code == 409
    body = stale.json()
    assert body["ok"] is False
    assert "Modificato da un altro utente" in body["errors"][0]
    assert body["attuale"]["nome"] == "Palazzina B"


@pytest.mark.unit
def test_update_progetto_unknown_returns_404(client: TestClient) -> None:
    response = client.put("/api/progetti/does-not-exist", json={"nome": "X", "revisione": 1})
    assert response.status_code == 404


@pytest.mark.unit
def test_soft_delete_and_restore_progetto(client: TestClient) -> None:
    created = _crea_progetto(client)

    deleted = client.request("DELETE", f"/api/progetti/{created['id']}", json={"revisione": created["revisione"]})
    assert deleted.status_code == 200

    missing = client.get(f"/api/progetti/{created['id']}")
    assert missing.json()["eliminato"] != ""

    restored = client.post(f"/api/progetti/{created['id']}/ripristina", json={})
    assert restored.status_code == 200
    assert restored.json()["eliminato"] == ""


@pytest.mark.unit
def test_delete_progetto_conflict_returns_409(client: TestClient) -> None:
    created = _crea_progetto(client)
    response = client.request("DELETE", f"/api/progetti/{created['id']}", json={"revisione": 999})
    assert response.status_code == 409
    assert response.json()["attuale"]["id"] == created["id"]


@pytest.mark.unit
def test_delete_progetto_unknown_returns_404(client: TestClient) -> None:
    response = client.request("DELETE", "/api/progetti/does-not-exist", json={"revisione": 1})
    assert response.status_code == 404


@pytest.mark.unit
def test_delete_progetto_invalid_body_returns_400(client: TestClient) -> None:
    created = _crea_progetto(client)
    response = client.request("DELETE", f"/api/progetti/{created['id']}", json={"revisione": -1})
    assert response.status_code == 400


@pytest.mark.unit
def test_update_progetto_invalid_body_returns_400(client: TestClient) -> None:
    created = _crea_progetto(client)
    response = client.put(f"/api/progetti/{created['id']}", json={"nome": "", "revisione": created["revisione"]})
    assert response.status_code == 400


@pytest.mark.unit
def test_ripristina_progetto_unknown_returns_404(client: TestClient) -> None:
    response = client.post("/api/progetti/does-not-exist/ripristina", json={})
    assert response.status_code == 404


@pytest.mark.unit
def test_list_elementi_unknown_progetto_returns_404(client: TestClient) -> None:
    response = client.get("/api/progetti/does-not-exist/elementi")
    assert response.status_code == 404


@pytest.mark.unit
def test_create_elemento_invalid_body_returns_400(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    response = client.post(f"/api/progetti/{progetto['id']}/elementi", json={"strumento": "fake-sum", "nome": ""})
    assert response.status_code == 400


# ---- elementi CRUD ----


@pytest.mark.unit
def test_create_and_get_elemento(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    assert elemento["strumento"] == "fake-sum"
    assert elemento["inputs"] == {"a": 1, "b": 2}

    response = client.get(f"/api/elementi/{elemento['id']}")
    assert response.status_code == 200
    assert response.json() == elemento


@pytest.mark.unit
def test_create_elemento_unknown_strumento_returns_400(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    response = client.post(
        f"/api/progetti/{progetto['id']}/elementi",
        json={"strumento": "does-not-exist", "nome": "X", "inputs": {}},
    )
    assert response.status_code == 400
    assert "does-not-exist" in response.json()["errors"][0]


@pytest.mark.unit
def test_create_elemento_unknown_progetto_returns_404(client: TestClient) -> None:
    response = client.post(
        "/api/progetti/does-not-exist/elementi",
        json={"strumento": "fake-sum", "nome": "X", "inputs": {}},
    )
    assert response.status_code == 404


@pytest.mark.unit
def test_list_elementi_of_progetto(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    response = client.get(f"/api/progetti/{progetto['id']}/elementi")
    assert response.status_code == 200
    assert {e["id"] for e in response.json()} == {elemento["id"]}


@pytest.mark.unit
def test_update_elemento_success(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    response = client.put(
        f"/api/elementi/{elemento['id']}",
        json={"strumento": "fake-sum", "nome": "Plinto P2", "inputs": {"a": 5}, "revisione": elemento["revisione"]},
    )
    assert response.status_code == 200
    assert response.json()["nome"] == "Plinto P2"
    assert response.json()["revisione"] == 2


@pytest.mark.unit
def test_update_elemento_conflict_returns_409(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    response = client.put(
        f"/api/elementi/{elemento['id']}",
        json={"strumento": "fake-sum", "nome": "X", "inputs": {}, "revisione": 999},
    )
    assert response.status_code == 409
    assert response.json()["attuale"]["id"] == elemento["id"]


@pytest.mark.unit
def test_update_elemento_unknown_returns_404(client: TestClient) -> None:
    response = client.put(
        "/api/elementi/does-not-exist",
        json={"strumento": "fake-sum", "nome": "X", "inputs": {}, "revisione": 1},
    )
    assert response.status_code == 404


@pytest.mark.unit
def test_update_elemento_unknown_strumento_returns_400(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    response = client.put(
        f"/api/elementi/{elemento['id']}",
        json={"strumento": "does-not-exist", "nome": "X", "inputs": {}, "revisione": elemento["revisione"]},
    )
    assert response.status_code == 400


@pytest.mark.unit
def test_get_elemento_unknown_returns_404(client: TestClient) -> None:
    response = client.get("/api/elementi/does-not-exist")
    assert response.status_code == 404


@pytest.mark.unit
def test_delete_elemento_conflict_returns_409(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    response = client.request("DELETE", f"/api/elementi/{elemento['id']}", json={"revisione": 999})
    assert response.status_code == 409
    assert response.json()["attuale"]["id"] == elemento["id"]


@pytest.mark.unit
def test_delete_elemento_unknown_returns_404(client: TestClient) -> None:
    response = client.request("DELETE", "/api/elementi/does-not-exist", json={"revisione": 1})
    assert response.status_code == 404


@pytest.mark.unit
def test_duplicate_elemento_invalid_body_returns_400(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    response = client.post(f"/api/elementi/{elemento['id']}/duplica", json={"nome": ""})
    assert response.status_code == 400


@pytest.mark.unit
def test_delete_and_soft_delete_elemento(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    response = client.request("DELETE", f"/api/elementi/{elemento['id']}", json={"revisione": elemento["revisione"]})
    assert response.status_code == 200

    listed = client.get(f"/api/progetti/{progetto['id']}/elementi").json()
    assert listed == []

    still_gettable = client.get(f"/api/elementi/{elemento['id']}")
    assert still_gettable.json()["eliminato"] != ""


@pytest.mark.unit
def test_duplicate_elemento(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    response = client.post(f"/api/elementi/{elemento['id']}/duplica", json={"nome": "Plinto P1 (copia)"})
    assert response.status_code == 201
    duplicated = response.json()
    assert duplicated["id"] != elemento["id"]
    assert duplicated["nome"] == "Plinto P1 (copia)"
    assert duplicated["inputs"] == elemento["inputs"]


@pytest.mark.unit
def test_duplicate_elemento_unknown_returns_404(client: TestClient) -> None:
    response = client.post("/api/elementi/does-not-exist/duplica", json={"nome": "X"})
    assert response.status_code == 404


@pytest.mark.unit
def test_revisions_list(client: TestClient) -> None:
    progetto = _crea_progetto(client)
    elemento = _crea_elemento(client, progetto["id"])
    client.put(
        f"/api/elementi/{elemento['id']}",
        json={
            "strumento": "fake-sum",
            "nome": "Plinto P1",
            "inputs": {"a": 9},
            "revisione": elemento["revisione"],
            "sigla": "MB",
            "nota": "Aggiornato spessore",
        },
    )
    response = client.get(f"/api/elementi/{elemento['id']}/revisioni")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 2
    assert body[0]["revisione"] == 1
    assert body[1]["revisione"] == 2
    assert body[1]["sigla"] == "MB"
    assert body[1]["nota"] == "Aggiornato spessore"


@pytest.mark.unit
def test_revisions_unknown_elemento_returns_404(client: TestClient) -> None:
    response = client.get("/api/elementi/does-not-exist/revisioni")
    assert response.status_code == 404


# ---- export / import ----


@pytest.mark.unit
def test_export_shape(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    progetto = _crea_progetto(client)
    _crea_elemento(client, progetto["id"])

    captured: dict[str, Any] = {}

    def fake_esporta(progetto_obj: Progetto, elementi_con_revisioni: Any, versione_app: str) -> dict[str, Any]:
        captured["progetto"] = progetto_obj
        captured["elementi_con_revisioni"] = elementi_con_revisioni
        captured["versione_app"] = versione_app
        return {
            "formato": "strutture-progetto",
            "versione": 1,
            "esportato": "2026-01-01T00:00:00Z",
            "app": versione_app,
            "progetto": progetto_obj.model_dump(mode="json"),
            "elementi": [],
        }

    monkeypatch.setattr("strutture.web.routes.progetti._scambio_esporta", fake_esporta)

    response = client.get(f"/api/progetti/{progetto['id']}/esporta")
    assert response.status_code == 200
    body = response.json()
    assert body["formato"] == "strutture-progetto"
    assert body["versione"] == 1
    assert body["progetto"]["id"] == progetto["id"]
    assert captured["progetto"].id == progetto["id"]
    assert len(captured["elementi_con_revisioni"]) == 1
    assert captured["versione_app"] == "0.1.0"


@pytest.mark.unit
def test_export_unknown_progetto_returns_404(client: TestClient) -> None:
    response = client.get("/api/progetti/does-not-exist/esporta")
    assert response.status_code == 404


@pytest.mark.unit
def test_import_returns_warnings(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    imported_progetto = Progetto(id="p-new", nome="Importato", revisione=1)

    def fake_importa(payload: dict[str, Any], repository: Any, strumenti_noti: frozenset[str]) -> tuple[Progetto, tuple[str, ...]]:
        assert payload["formato"] == "strutture-progetto"
        assert "fake-sum" in strumenti_noti
        return imported_progetto, ("Strumento sconosciuto 'vecchio-tool' importato senza verifica",)

    monkeypatch.setattr("strutture.web.routes.progetti._scambio_importa", fake_importa)

    response = client.post(
        "/api/progetti/importa",
        json={"formato": "strutture-progetto", "versione": 1, "progetto": {}, "elementi": []},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["progetto"]["id"] == "p-new"
    assert body["avvisi"] == ["Strumento sconosciuto 'vecchio-tool' importato senza verifica"]


@pytest.mark.unit
def test_import_validation_error_returns_400(client: TestClient, monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_importa(payload: dict[str, Any], repository: Any, strumenti_noti: frozenset[str]) -> Any:
        raise ValueError("Formato di importazione non riconosciuto")

    monkeypatch.setattr("strutture.web.routes.progetti._scambio_importa", fake_importa)

    response = client.post("/api/progetti/importa", json={"formato": "qualcosa-altro"})
    assert response.status_code == 400
    assert "non riconosciuto" in response.json()["errors"][0]


# ---- same-origin guard still applies ----


@pytest.mark.unit
def test_post_with_text_plain_content_type_is_rejected(client: TestClient) -> None:
    response = client.post(
        "/api/progetti",
        content=b'{"nome": "X"}',
        headers={"Content-Type": "text/plain"},
    )
    assert response.status_code == 415


def test_elemento_can_be_listed_deleted_and_restored(client: TestClient) -> None:
    progetto = client.post("/api/progetti", json={"nome": "P"}).json()
    elemento = client.post(f"/api/progetti/{progetto['id']}/elementi", json={"strumento": "fake-sum", "nome": "E", "inputs": {"a": 1}}).json()
    assert client.request("DELETE", f"/api/elementi/{elemento['id']}", json={"revisione": elemento["revisione"]}).json() == {"eliminato": True}
    assert client.get(f"/api/progetti/{progetto['id']}/elementi").json() == []
    eliminati = client.get(f"/api/progetti/{progetto['id']}/elementi", params={"inclusi_eliminati": "true"}).json()
    assert [e["id"] for e in eliminati] == [elemento["id"]] and eliminati[0]["eliminato"]
    restored = client.post(f"/api/elementi/{elemento['id']}/ripristina", json={}).json()  # same-origin guard wants JSON
    assert restored["eliminato"] == "" and restored["revisione"] == elemento["revisione"] + 2
    assert client.post("/api/elementi/nope/ripristina", json={}).status_code == 404
