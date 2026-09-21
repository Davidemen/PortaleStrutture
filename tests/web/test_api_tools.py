import pytest
from fastapi.testclient import TestClient


@pytest.mark.unit
def test_list_tools_returns_summaries(client: TestClient) -> None:
    response = client.get("/api/tools")
    assert response.status_code == 200
    names = {item["name"] for item in response.json()}
    assert names == {"fake-sum", "fake-flag"}
    sum_summary = next(item for item in response.json() if item["name"] == "fake-sum")
    assert sum_summary == {
        "name": "fake-sum",
        "title": "Somma di prova",
        "group": "Prova",
        "norm": "TEST §1",
    }


@pytest.mark.unit
def test_schema_returns_input_and_output_json_schema(client: TestClient) -> None:
    response = client.get("/api/tools/fake-sum/schema")
    assert response.status_code == 200
    body = response.json()
    assert "input" in body and "output" in body
    assert body["input"]["properties"]["a"]["description"] == "Primo addendo"
    assert body["input"]["properties"]["a"]["unit"] == "kN"
    assert body["output"]["properties"]["total"]["type"] == "number"


@pytest.mark.unit
def test_schema_unknown_tool_returns_404(client: TestClient) -> None:
    response = client.get("/api/tools/does-not-exist/schema")
    assert response.status_code == 404
    body = response.json()
    assert body["ok"] is False
    assert "does-not-exist" in body["errors"][0]


@pytest.mark.unit
def test_run_happy_path(client: TestClient) -> None:
    response = client.post("/api/tools/fake-sum/run", json={"a": 5, "b": 7})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["data"]["total"] == pytest.approx(12.0)
    assert body["checks"][0]["passed"] is True
    assert body["checks"][0]["clause"] == "TEST §1"


@pytest.mark.unit
def test_run_validation_error_envelope(client: TestClient) -> None:
    response = client.post("/api/tools/fake-sum/run", json={"a": 500, "b": 7})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["data"] is None
    assert any("a" in message for message in body["errors"])


@pytest.mark.unit
def test_run_calc_error_envelope(client: TestClient) -> None:
    response = client.post("/api/tools/fake-flag/run", json={"mode": "boom"})
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is False
    assert body["errors"] == ["modalità 'boom' non è valida per questo strumento"]


@pytest.mark.unit
def test_run_unexpected_error_returns_generic_500(client: TestClient) -> None:
    response = client.post("/api/tools/fake-flag/run", json={"mode": "crash"})
    assert response.status_code == 500
    body = response.json()
    assert body["ok"] is False
    assert "interno" in body["errors"][0]
    assert "RuntimeError" not in body["errors"][0]
    assert "bug simulato" not in body["errors"][0]


@pytest.mark.unit
def test_run_unknown_tool_returns_404(client: TestClient) -> None:
    response = client.post("/api/tools/does-not-exist/run", json={})
    assert response.status_code == 404


@pytest.mark.unit
def test_run_non_object_body_returns_error_envelope(client: TestClient) -> None:
    response = client.post("/api/tools/fake-sum/run", json=[1, 2, 3])
    assert response.status_code == 400
    body = response.json()
    assert body["ok"] is False


@pytest.mark.unit
def test_run_malformed_json_returns_error_envelope(client: TestClient) -> None:
    response = client.post(
        "/api/tools/fake-sum/run", content=b"{not json", headers={"content-type": "application/json"}
    )
    assert response.status_code == 400
    body = response.json()
    assert body["ok"] is False
