"""`POST /api/tools/{name}/run?relazione=1` (docs/architecture-phase2.md §1/§3): the trace is built
only on request, every `Passo` carries `formula_ast` next to `formula`, and `GET /api/tools` /
`/schema` expose `relazione: bool`."""
import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.relazione.modelli import Passo, Traccia, Valore
from strutture.shared.report import Report, success
from strutture.shared.tool import Tool
from strutture.web import create_app

pytestmark = pytest.mark.integration


class SpanIn(BaseModel):
    model_config = ConfigDict(frozen=True)
    luce_m: float = Field(gt=0, description="Luce", json_schema_extra={"unit": "m", "group": "Geometria", "symbol": "L"})
    legacy_compat: bool = False


class SpanOut(BaseModel):
    model_config = ConfigDict(frozen=True)
    freccia_mm: float = Field(description="Freccia", json_schema_extra={"unit": "mm", "highlight": True})


def _run(inputs: SpanIn) -> Report[SpanOut]:
    return success(SpanOut(freccia_mm=8.2), inputs)


def _relazione(inputs: SpanIn, output: SpanOut) -> tuple[Traccia, ...]:
    passo = Passo(
        simbolo="f", formula="L * 0.001",
        valori=(Valore(simbolo="L", valore=inputs.luce_m),),
        risultato=output.freccia_mm * 0.001, unita="m",
    )
    return (Traccia(titolo="Freccia", passi=(passo,)),)


WITH_RELAZIONE = Tool("span", "Freccia", "Test", "NTC2018 §4", SpanIn, SpanOut, _run, relazione=_relazione)
WITHOUT_RELAZIONE = Tool("bare", "Senza relazione", "Test", "-", SpanIn, SpanOut, _run)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(tools={"span": WITH_RELAZIONE, "bare": WITHOUT_RELAZIONE}))


def test_relazione_flag_defaults_off(client: TestClient) -> None:
    body = client.post("/api/tools/span/run", json={"luce_m": 5}).json()
    assert body["ok"] is True
    assert body["relazione"] == []


def test_relazione_flag_on_builds_the_trace(client: TestClient) -> None:
    body = client.post("/api/tools/span/run?relazione=1", json={"luce_m": 5}).json()
    assert body["ok"] is True
    assert len(body["relazione"]) == 1
    assert body["relazione"][0]["titolo"] == "Freccia"


def test_every_passo_carries_formula_ast_next_to_formula(client: TestClient) -> None:
    body = client.post("/api/tools/span/run?relazione=1", json={"luce_m": 5}).json()
    passo = body["relazione"][0]["passi"][0]
    assert passo["formula"] == "L * 0.001"
    assert passo["formula_ast"] == {
        "t": "op", "op": "*",
        "a": {"t": "id", "base": "L", "sub": ""},
        "b": {"t": "num", "v": 0.001},
    }


def test_relazione_flag_on_a_tool_without_relazione_stays_empty(client: TestClient) -> None:
    body = client.post("/api/tools/bare/run?relazione=1", json={"luce_m": 5}).json()
    assert body["ok"] is True
    assert body["relazione"] == []


def test_schema_and_list_expose_relazione_bool(client: TestClient) -> None:
    lista = {t["name"]: t for t in client.get("/api/tools").json()}
    assert lista["span"]["relazione"] is True
    assert lista["bare"]["relazione"] is False
    assert client.get("/api/tools/span/schema").json()["relazione"] is True
    assert client.get("/api/tools/bare/schema").json()["relazione"] is False
