"""`/api/tools/{name}/dimensiona` and `/api/tools/{name}/sensibilita` (WORKBENCH_SPEC §23.4, §24.1)."""
import pytest
from fastapi.testclient import TestClient

from strutture.web.routes.dimensiona import StatoDimensiona, _etichetta_campo

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


def test_etichetta_campo_uses_description_and_symbol_never_the_internal_name() -> None:
    """The engineer never sees a raw pydantic field name (e.g. `categoria_sottosuolo`) -- the
    field's own `symbol`/`description` come first, the internal name is only a last resort."""
    assert _etichetta_campo({"symbol": "ag", "description": "Accelerazione al suolo"}, "ag_g") == "ag (Accelerazione al suolo)"
    assert _etichetta_campo({"description": "Categoria di sottosuolo"}, "categoria_sottosuolo") == "Categoria di sottosuolo"
    assert _etichetta_campo({}, "categoria_sottosuolo") == "categoria_sottosuolo"


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
    assert "punti" in response.json()["errors"][0].lower()


# -- §23.3 point 7: an optional numeric field (`anyOf`, no top-level `type`) -----------------------


def test_campo_opzionale_anyof_e_accettato(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-verifica/dimensiona",
        json=_corpo(campo="margine", da=1.0, a=40.0, passo=1.0, inputs={**_BASE, "margine": 10.0}),
    )
    assert response.status_code == 200, response.text
    assert response.json()["ok"] is True


def test_sensibilita_campo_opzionale_anyof_e_accettato(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-verifica/sensibilita",
        json={"inputs": {**_BASE, "margine": 10.0}, "campo": "margine", "da": 1.0, "a": 40.0, "punti": 5},
    )
    assert response.status_code == 200, response.text


# -- §23.3 point 7 / §23.4: da/a outside the field's own schema limits ------------------------------


def test_422_a_fuori_dal_limite_dello_schema(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo(a=2000.0))
    assert response.status_code == 422
    assert "1000" in response.json()["errors"][0]


def test_sensibilita_422_da_fuori_dal_limite_dello_schema(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-verifica/sensibilita",
        json={"inputs": _BASE, "campo": "capacita", "da": -5.0, "a": 100.0, "punti": 5},
    )
    assert response.status_code == 422


def test_sensibilita_422_da_maggiore_uguale_a(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-verifica/sensibilita",
        json={"inputs": _BASE, "campo": "capacita", "da": 100.0, "a": 10.0, "punti": 5},
    )
    assert response.status_code == 422


# -- §23.3 point 7 / §24.1: the base inputs themselves must be valid before any grid point runs ----


def test_422_inputs_di_base_non_validi_da_errore_dello_strumento(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-verifica/dimensiona", json=_corpo(inputs={"domanda": -5.0, "capacita": 200.0}),
    )
    assert response.status_code == 422
    assert response.json()["errors"]


def test_sensibilita_422_inputs_di_base_non_validi(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-verifica/sensibilita",
        json={"inputs": {"domanda": -5.0, "capacita": 200.0}, "campo": "capacita", "da": 1, "a": 2, "punti": 3},
    )
    assert response.status_code == 422


# -- §23.2/§24.1: affidabilità composed from more than the search algorithm's own verdict -----------


def test_obiettivo_su_minimi_falso_e_obiettivo_sotto_uno_rende_inaffidabile(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo(obiettivo=0.5))
    body = response.json()
    assert body["affidabile"] is False
    assert any("limiti massimi di dettaglio" in m for m in body["motivi"])


def test_obiettivo_pieno_resta_affidabile(client: TestClient) -> None:
    response = client.post("/api/tools/fake-verifica/dimensiona", json=_corpo(obiettivo=1.0))
    body = response.json()
    assert body["affidabile"] is True


def test_modalita_excel_rende_sempre_inaffidabile(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-verifica/dimensiona", json=_corpo(inputs={**_BASE, "legacy_compat": True}),
    )
    body = response.json()
    assert body["modalita"] == "excel"
    assert body["affidabile"] is False
    assert any("Excel" in m for m in body["motivi"])


def test_avvisi_nuovi_confrontati_con_gli_inputs_inviati_non_con_griglia_0(settings) -> None:
    """§23.3 point 2: "nuovi" avvisi are measured against the engineer's OWN submitted `inputs`,
    not whatever the grid's first sample happens to be. Tool: a warning appears at x >= 50. Grid
    (multiples of 49 in [1, 199]: 49, 98, 147, 196) starts BELOW the threshold (49, no warning) but
    the submitted `inputs` (x=100) are ABOVE it (has the warning already) -- the old code compared
    every sample to griglia[0]=49's run (no warning), wrongly flagging 98/147/196 as "new"."""
    from pydantic import BaseModel, ConfigDict, Field

    from strutture.shared.report import Check, Report, success
    from strutture.shared.tool import Tool
    from strutture.storage.memory import InMemorySignoffRepository
    from strutture.storage.progetti_memory import InMemoryProjectRepository
    from strutture.web.app import create_app

    class _In(BaseModel):
        model_config = ConfigDict(frozen=True)

        x: float = Field(gt=0, lt=1000)

    class _Out(BaseModel):
        model_config = ConfigDict(frozen=True)

        ok: bool = True

    def _run(inputs: _In) -> Report[_Out]:
        avvisi = ("Oltre soglia",) if inputs.x >= 50 else ()
        checks = (Check(name="Sempre ok", passed=True, clause="TEST"),)
        return success(_Out(), inputs, checks=checks, warnings=avvisi)

    tool = Tool(name="fake-avviso", title="Prova", group="g", norm="n", input_model=_In, output_model=_Out, run=_run)
    app = create_app(
        tools={"fake-avviso": tool}, settings=settings, progetti=InMemoryProjectRepository(),
        signoffs=InMemorySignoffRepository(),
    )
    client = TestClient(app)
    response = client.post(
        "/api/tools/fake-avviso/dimensiona",
        json={"inputs": {"x": 100.0}, "campo": "x", "da": 1.0, "a": 199.0, "passo": 49.0, "obiettivo": 1.0},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert {float(c["valore"]) for c in body["campioni"]} >= {98.0, 147.0, 196.0}
    assert all(c["avvisi_nuovi"] == [] for c in body["campioni"])
