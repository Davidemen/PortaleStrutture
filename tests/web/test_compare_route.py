"""POST /api/tools/{name}/compare: one request, the tool run in both modes, the differences and the
register entries responsible for them."""
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict

from strutture.shared.divergences.models import Divergence
from strutture.shared.report import CalcError, Report, success
from strutture.shared.tool import Tool
from strutture.web.routes.tools import build_tools_router

pytestmark = pytest.mark.integration


class ModeInputs(BaseModel):
    model_config = ConfigDict(frozen=True)
    a: float
    legacy_compat: bool = False


class ModeOutputs(BaseModel):
    model_config = ConfigDict(frozen=True)
    totale: float


def _run_mode(inputs: ModeInputs) -> Report[ModeOutputs]:
    if inputs.a < 0 and inputs.legacy_compat:
        raise CalcError("il foglio non accetta valori negativi")
    return success(ModeOutputs(totale=inputs.a + (1.0 if inputs.legacy_compat else 0.0)), inputs)


class PlainInputs(BaseModel):
    model_config = ConfigDict(frozen=True)
    a: float


def _run_plain(inputs: PlainInputs) -> Report[ModeOutputs]:
    return success(ModeOutputs(totale=inputs.a), inputs)


MODE_TOOL = Tool("fake-mode", "Due modalità", "Prova", "TEST", ModeInputs, ModeOutputs, _run_mode)
PLAIN_TOOL = Tool("fake-plain", "Una modalità", "Prova", "TEST", PlainInputs, ModeOutputs, _run_plain)
REGISTER = (
    Divergence(id="demo/piu-uno", titolo="Il foglio aggiunge uno", tipo="errore_foglio", strumenti=("fake-mode",),
               foglio="somma 1 al totale", corretto="non somma nulla", uscite=("totale",)),
)


@pytest.fixture
def client() -> TestClient:
    app = FastAPI()
    app.include_router(build_tools_router({MODE_TOOL.name: MODE_TOOL, PLAIN_TOOL.name: PLAIN_TOOL}, register=REGISTER))
    return TestClient(app)


def test_compare_runs_both_modes_and_explains_the_difference(client: TestClient) -> None:
    body = client.post("/api/tools/fake-mode/compare", json={"a": 2.0}).json()
    assert body["ok"] is True and body["disponibile"] is True
    assert body["standard"]["data"]["totale"] == 2.0
    assert body["excel"]["data"]["totale"] == 3.0
    assert body["confronto"]["differenze"] == [
        {"percorso": "totale", "standard": 2.0, "excel": 3.0, "delta": -1.0, "delta_rel": pytest.approx(-1 / 3),
         "divergenze": ["demo/piu-uno"]}
    ]
    assert body["confronto"]["divergenze_coinvolte"] == ["demo/piu-uno"]


def test_the_mode_flag_in_the_request_is_ignored(client: TestClient) -> None:
    body = client.post("/api/tools/fake-mode/compare", json={"a": 2.0, "legacy_compat": True}).json()
    assert body["standard"]["data"]["totale"] == 2.0
    assert body["standard"]["inputs_echo"]["legacy_compat"] is False
    assert body["excel"]["inputs_echo"]["legacy_compat"] is True


def test_a_tool_without_an_excel_mode_says_so(client: TestClient) -> None:
    response = client.post("/api/tools/fake-plain/compare", json={"a": 2.0})
    assert response.status_code == 200
    body = response.json()
    assert body["disponibile"] is False and body["excel"] is None and body["confronto"] is None
    assert body["standard"]["data"]["totale"] == 2.0


def test_a_failure_in_one_mode_is_reported_not_raised(client: TestClient) -> None:
    body = client.post("/api/tools/fake-mode/compare", json={"a": -1.0}).json()
    assert body["ok"] is False
    assert body["standard"]["ok"] is True and body["excel"]["ok"] is False
    assert body["confronto"]["confrontabile"] is False


def test_validation_errors_come_back_in_both_reports(client: TestClient) -> None:
    body = client.post("/api/tools/fake-mode/compare", json={"a": "non un numero"}).json()
    assert body["ok"] is False and body["standard"]["ok"] is False and body["standard"]["errors"]


def test_unknown_tool_is_404_and_bad_json_is_400(client: TestClient) -> None:
    assert client.post("/api/tools/nope/compare", json={}).status_code == 404
    assert client.post("/api/tools/fake-mode/compare", content=b"{", headers={"Content-Type": "application/json"}).status_code == 400
    assert client.post("/api/tools/fake-mode/compare", json=[1, 2]).status_code == 400


# --- exact attribution: the Excel run records the corrections it used, each is then tried alone ---

class DueInputs(BaseModel):
    model_config = ConfigDict(frozen=True)
    a: float
    legacy_compat: bool = False


class DueOutputs(BaseModel):
    model_config = ConfigDict(frozen=True)
    x: float
    y: float
    somma: float


def _run_due(inputs: DueInputs) -> Report[DueOutputs]:
    from strutture.shared.divergences import legacy

    x = inputs.a + (1.0 if legacy("demo/x-piu-uno", inputs.legacy_compat) else 0.0)
    y = inputs.a * (2.0 if legacy("demo/y-doppio", inputs.legacy_compat) else 1.0)
    return success(DueOutputs(x=x, y=y, somma=x + y), inputs)


DUE_TOOL = Tool("fake-due", "Due correzioni", "Prova", "TEST", DueInputs, DueOutputs, _run_due)


def test_differences_are_attributed_by_trying_each_correction_alone() -> None:
    app = FastAPI()
    app.include_router(build_tools_router({DUE_TOOL.name: DUE_TOOL}, register=()))  # no `uscite` to lean on
    body = TestClient(app).post("/api/tools/fake-due/compare", json={"a": 3.0}).json()
    by_path = {d["percorso"]: d["divergenze"] for d in body["confronto"]["differenze"]}
    assert by_path == {"x": ["demo/x-piu-uno"], "y": ["demo/y-doppio"], "somma": ["demo/x-piu-uno", "demo/y-doppio"]}
    assert body["confronto"]["attribuzione"] == {"correzioni_valutate": 2, "completa": True, "non_valutabili": []}
    assert body["standard"]["data"] == {"x": 3.0, "y": 3.0, "somma": 6.0}  # the analysis runs never leak into the results


def test_no_attribution_runs_when_the_two_modes_agree(client: TestClient) -> None:
    body = client.post("/api/tools/fake-plain/compare", json={"a": 2.0}).json()
    assert body["confronto"] is None
