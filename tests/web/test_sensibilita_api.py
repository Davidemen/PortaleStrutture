"""`/api/tools/{name}/sensibilita` behaviour shared with `/dimensiona` but not exercised in
test_dimensiona_api.py's own smoke tests: the semaphore, the forced standard mode for an approved
tool, and the injected `tempo_max_s` (WORKBENCH_SPEC §24.1)."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from strutture.shared.divergences.models import Divergence
from strutture.storage.memory import InMemorySignoffRepository
from strutture.web.routes.dimensiona import StatoDimensiona, build_dimensiona_router
from tests.fixtures.web_fake_tools import FAKE_TOOLS

pytestmark = pytest.mark.integration

_BASE = {"domanda": 50.0, "capacita": 200.0}
_CORPO = {"inputs": _BASE, "campo": "capacita", "da": 10.0, "a": 100.0, "punti": 10}
REGISTER = (
    Divergence(
        id="fake-verifica/qualcosa", titolo="Qualcosa da correggere", tipo="errore_foglio",
        strumenti=("fake-verifica",), foglio="Sbagliato", corretto="Giusto",
    ),
)


def _app(signoffs, *, register=None) -> FastAPI:
    app = FastAPI()
    app.state.dimensiona = StatoDimensiona()
    app.include_router(build_dimensiona_router(FAKE_TOOLS, signoffs, register=register))
    return app


@pytest.fixture
def client() -> TestClient:
    return TestClient(_app(InMemorySignoffRepository()))


def test_429_con_semaforo_occupato(client: TestClient) -> None:
    stato = StatoDimensiona()
    for _ in range(2):  # MAX_RICERCHE_CONTEMPORANEE
        stato.semaforo.acquire()
    client.app.state.dimensiona = stato
    try:
        response = client.post("/api/tools/fake-verifica/sensibilita", json=_CORPO)
        assert response.status_code == 429
    finally:
        for _ in range(2):
            stato.semaforo.release()


def test_tempo_max_s_e_iniettato_da_stato_dimensiona(client: TestClient) -> None:
    """`calcola_serie` must receive `app.state.dimensiona.tempo_max_s`, not always the module's own
    default -- a deadline already in the past gives a `completa=False`, empty series."""
    client.app.state.dimensiona = StatoDimensiona(tempo_max_s=-1.0)
    response = client.post("/api/tools/fake-verifica/sensibilita", json=_CORPO)
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["completa"] is False
    assert body["valori"] == []


def test_modalita_excel_forzata_a_standard_per_uno_strumento_approvato() -> None:
    """§24.1: an approved tool never studies its Excel branch by accident, even if the request's
    own `inputs` ask for `legacy_compat=True` -- the same forcing `/dimensiona` already applies."""
    signoffs = InMemorySignoffRepository()
    signoffs.set("fake-verifica/qualcosa", "approvato", "ab", "ok")
    client = TestClient(_app(signoffs, register=REGISTER))
    body = {"inputs": {**_BASE, "legacy_compat": True}, "campo": "capacita", "da": 10.0, "a": 100.0, "punti": 5}
    response = client.post("/api/tools/fake-verifica/sensibilita", json=body)
    assert response.status_code == 200, response.text
    assert response.json()["modalita"] == "standard"


def test_modalita_excel_quando_non_approvato() -> None:
    signoffs = InMemorySignoffRepository()  # left "da_confermare": not approved
    client = TestClient(_app(signoffs, register=REGISTER))
    body = {"inputs": {**_BASE, "legacy_compat": True}, "campo": "capacita", "da": 10.0, "a": 100.0, "punti": 5}
    response = client.post("/api/tools/fake-verifica/sensibilita", json=body)
    assert response.status_code == 200, response.text
    assert response.json()["modalita"] == "excel"
