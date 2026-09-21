"""Backend -> UI hint contract (docs/ui/DESIGN_SPEC.md §4): one schema request boots a deep link."""
import pytest
from fastapi.testclient import TestClient
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check, success
from strutture.shared.tool import Tool
from strutture.web import create_app

pytestmark = pytest.mark.integration


class SpanIn(BaseModel):
    model_config = ConfigDict(frozen=True)
    luce_m: float = Field(gt=0, description="Luce", json_schema_extra={"unit": "m", "group": "Geometria", "symbol": "L"})


class SpanOut(BaseModel):
    model_config = ConfigDict(frozen=True)
    freccia_mm: float = Field(description="Freccia", json_schema_extra={"unit": "mm", "highlight": True})


def _run(inputs: SpanIn):
    check = Check(name="freccia", passed=True, clause="§4.1", value=8.2, limit=10.0, unit="mm")
    return success(SpanOut(freccia_mm=8.2), inputs, checks=(check,))


WITH_EXAMPLE = Tool("span", "Freccia", "Test", "NTC2018 §4", SpanIn, SpanOut, _run, example={"luce_m": 5.0})
WITHOUT_EXAMPLE = Tool("bare", "Senza esempio", "Test", "-", SpanIn, SpanOut, _run)


@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app(tools={"span": WITH_EXAMPLE, "bare": WITHOUT_EXAMPLE}))


def test_schema_endpoint_carries_identity_example_and_hints(client: TestClient) -> None:
    body = client.get("/api/tools/span/schema").json()
    assert set(body) == {"name", "title", "group", "norm", "example", "input", "output"}
    assert (body["name"], body["title"], body["norm"], body["example"]) == ("span", "Freccia", "NTC2018 §4", {"luce_m": 5.0})
    assert body["input"]["properties"]["luce_m"]["group"] == "Geometria"
    assert body["output"]["properties"]["freccia_mm"]["highlight"] is True


def test_example_defaults_to_null(client: TestClient) -> None:
    assert client.get("/api/tools/bare/schema").json()["example"] is None


def test_checks_expose_value_limit_and_unit_for_utilisation_bars(client: TestClient) -> None:
    check = client.post("/api/tools/span/run", json={"luce_m": 5}).json()["checks"][0]
    assert (check["value"], check["limit"], check["unit"]) == (8.2, 10.0, "mm")


def test_check_numeric_fields_are_optional() -> None:
    plain = Check(name="x", passed=False)
    assert plain.value is None and plain.limit is None and plain.unit == ""


def test_example_never_switches_the_tool_into_excel_mode() -> None:
    """Golden inputs are recorded with legacy_compat=True; "Carica esempio" must load them in the default mode."""
    legacy_example = Tool("leg", "Legacy", "Test", "-", SpanIn, SpanOut, _run, example={"luce_m": 5.0, "legacy_compat": True})
    body = TestClient(create_app(tools={"leg": legacy_example})).get("/api/tools/leg/schema").json()
    assert body["example"] == {"luce_m": 5.0}


def test_every_registered_example_runs_in_the_default_mode() -> None:
    from strutture.shared.tool import discover, execute

    broken = [
        name for name, tool in discover().items()
        if tool.example and not execute(tool, {**tool.example, "legacy_compat": False}).ok
    ]
    assert broken == []
