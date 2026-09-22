"""`/api/tools/{name}/dimensiona` and `/api/tools/{name}/sensibilita` (WORKBENCH_SPEC §23.4, §24.1)."""
import pytest
from fastapi.testclient import TestClient

from strutture.web.routes.dimensiona import StatoDimensiona

pytestmark = pytest.mark.integration

_BASE = {"domanda": 50.0, "capacita": 200.0}


def _corpo(**over):
    body = {"inputs": _BASE, "campo": "capacita", "da": 10.0, "a": 100.0, "passo": 5.0, "obiettivo": 1.0}
    return {**body, **over}


def test_404_strumento_sconosciuto(client: TestClient) -> None:
    response = client.post("/api/tools/non-esiste/dimensiona", json=_corpo())
    assert response.status_code == 404
    assert response.json()["ok"] is False


def test_422_campo_non_numerico(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo(campo="legacy_compat"))
    assert response.status_code == 422
    assert "non è numerico" in response.json()["errors"][0]


def test_422_campo_inesistente(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo(campo="non_esiste"))
    assert response.status_code == 422


def test_422_passo_non_positivo(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo(passo=0))
    assert response.status_code == 422
    assert "passo" in response.json()["errors"][0].lower()


def test_422_obiettivo_fuori_range(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo(obiettivo=1.5))
    assert response.status_code == 422


def test_422_da_maggiore_uguale_a(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo(da=100.0, a=10.0))
    assert response.status_code == 422


def test_422_griglia_vuota(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo(da=10.1, a=10.4, passo=1.0))
    assert response.status_code == 422
    assert "Nessun multiplo" in response.json()["errors"][0]


def test_422_passo_non_intero_su_campo_intero(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-verifica/dimensiona", json=_corpo(campo="n_barre", da=1, a=10, passo=1.5),
    )
    assert response.status_code == 422
    assert "intero" in response.json()["errors"][0]


def test_429_con_semaforo_occupato(client: TestClient) -> None:
    stato = StatoDimensiona()
    for _ in range(2):  # MAX_RICERCHE_CONTEMPORANEE
        stato.semaforo.acquire()
    client.app.state.dimensiona = stato
    try:
        response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo())
        assert response.status_code == 429
    finally:
        for _ in range(2):
            stato.semaforo.release()
        client.app.state.dimensiona = StatoDimensiona()


def test_trovato_forma_della_risposta(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo())
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["esito"] == "trovato"
    assert body["verso"] == "minimo"
    assert body["valore"] == pytest.approx(50.0)
    assert body["affidabile"] is True
    assert body["modalita"] == "standard"
    assert body["correzioni"] == {"da_confermare": 0, "respinto": 0}
    assert body["governante"]["nome"] == "Resistenza"
    assert body["report"] is not None
    assert body["campioni"]


def test_sensibilita_forma_della_risposta(client: TestClient) -> None:
    body = {"inputs": _BASE, "campo": "capacita", "da": 10.0, "a": 100.0, "punti": 10}
    response = client.post("/api/tools/fake-verifica/sensibilita", json=body)
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert len(data["valori"]) == 10
    voce = next(v for v in data["verifiche"] if v["nome"] == "Resistenza")
    assert len(voce["eta"]) == 10
    assert voce["eta"][0] == pytest.approx(50.0 / 10.0)
    assert data["errori"] == []
    assert data["completa"] is True


def test_sensibilita_404(client: TestClient) -> None:
    response = client.post(
        "/api/tools/non-esiste/sensibilita", json={"inputs": _BASE, "campo": "capacita", "da": 1, "a": 2, "punti": 3},
    )
    assert response.status_code == 404


def test_sensibilita_422_punti_fuori_range(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-verifica/sensibilita", json={"inputs": _BASE, "campo": "capacita", "da": 1, "a": 2, "punti": 1},
    )
    assert response.status_code == 422
