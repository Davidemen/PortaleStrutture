"""API surface for the MIDAS integration (docs/integrations/MIDAS.md §4): status, verify,
combinations, supports, reactions, and the `{ok: false, errors, kind}` error envelope."""
import json

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from strutture.integrations.midas import MidasClient
from strutture.web.routes.midas import build_midas_router
from tests.integrations.midas.conftest import load_fixture, make_transport

pytestmark = pytest.mark.integration

BASE_URL = "https://moa-engineers.midasit.com:443/gen"
FAKE_KEY = "TESTKEY-DO-NOT-LEAK-9F3A"
_STANDARD_HEAD = ["Index", "Node", "Load", "FX", "FY", "FZ", "MX", "MY", "MZ"]


@pytest.fixture(autouse=True)
def clean_midas_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("MIDAS_MAPI_KEY", "MIDAS_BASE_URL", "MIDAS_PRODUCT", "MIDAS_ALLOWED_HOSTS"):
        monkeypatch.delenv(name, raising=False)


def _client(routes: dict) -> TestClient:
    def factory(base_url: str, key: str) -> MidasClient:
        return MidasClient(base_url, key, transport=make_transport(routes))

    app = FastAPI()
    app.include_router(build_midas_router(client_factory=factory))
    return TestClient(app)


# ---- /api/midas/status ------------------------------------------------------------------------


def test_status_reports_no_server_key_by_default() -> None:
    client = _client({})
    response = client.get("/api/midas/status")
    assert response.status_code == 200
    assert response.json() == {"server_key": False, "base_url": None, "product": None}


def test_status_reports_server_key_present_but_never_the_key_itself(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIDAS_MAPI_KEY", FAKE_KEY)
    client = _client({})
    response = client.get("/api/midas/status")
    assert response.json()["server_key"] is True
    assert FAKE_KEY not in response.text


def test_status_reflects_configured_base_url_and_product(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MIDAS_BASE_URL", BASE_URL)
    monkeypatch.setenv("MIDAS_PRODUCT", "civil")
    client = _client({})
    assert client.get("/api/midas/status").json() == {"server_key": False, "base_url": BASE_URL, "product": "civil"}


# ---- /api/midas/verify -------------------------------------------------------------------------


def test_verify_with_explicit_base_url() -> None:
    routes = {"/config/ver": load_fixture("midas_version.json"), "/db/UNIT": load_fixture("midas_unit.json")}
    client = _client(routes)
    response = client.post(
        "/api/midas/verify", json={"base_url": BASE_URL}, headers={"X-Midas-Key": FAKE_KEY}
    )
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "ok": True,
        "product": "gen",
        "name": "midas Gen NX",
        "version": "1.6.6",
        "base_url": BASE_URL,
        "units": {"force": "KN", "dist": "M"},
    }


def test_verify_without_base_url_autodetects() -> None:
    routes = {"/config/ver": load_fixture("midas_version.json"), "/db/UNIT": load_fixture("midas_unit.json")}
    client = _client(routes)
    response = client.post("/api/midas/verify", json={}, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert response.json()["base_url"].startswith("https://moa-engineers")


def test_verify_without_key_returns_401() -> None:
    client = _client({})
    response = client.post("/api/midas/verify", json={"base_url": BASE_URL})
    assert response.status_code == 401
    body = response.json()
    assert body["ok"] is False
    assert body["kind"] == "auth"


def test_verify_rejects_forbidden_base_url_with_400() -> None:
    client = _client({})
    response = client.post(
        "/api/midas/verify", json={"base_url": "http://evil.example.com/gen"}, headers={"X-Midas-Key": FAKE_KEY}
    )
    assert response.status_code == 400
    assert response.json()["kind"] == "forbidden_url"


def test_verify_maps_401_from_midas() -> None:
    routes = {"/config/ver": lambda r: httpx.Response(401, json={"message": "bad key"})}
    client = _client(routes)
    response = client.post("/api/midas/verify", json={"base_url": BASE_URL}, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 401
    assert response.json()["kind"] == "auth"


def test_verify_maps_timeout_to_504() -> None:
    def timeout(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("simulated timeout", request=request)

    client = _client({"/config/ver": timeout})
    response = client.post("/api/midas/verify", json={"base_url": BASE_URL}, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 504
    assert response.json()["kind"] == "timeout"


def test_verify_maps_connection_failure_to_502() -> None:
    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated failure", request=request)

    client = _client({"/config/ver": unreachable})
    response = client.post("/api/midas/verify", json={"base_url": BASE_URL}, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 502
    assert response.json()["kind"] == "not_connected"


def test_verify_maps_midas_message_error_to_502() -> None:
    routes = {"/config/ver": load_fixture("midas_error.json")}
    client = _client(routes)
    response = client.post("/api/midas/verify", json={"base_url": BASE_URL}, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 502
    assert response.json()["kind"] == "bad_response"


def test_verify_rejects_non_object_body_with_400() -> None:
    client = _client({})
    response = client.post("/api/midas/verify", content=b"[1, 2, 3]", headers={"content-type": "application/json", "X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_verify_rejects_malformed_json_with_400() -> None:
    client = _client({})
    response = client.post("/api/midas/verify", content=b"{not json", headers={"content-type": "application/json", "X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_key_never_appears_in_any_error_response() -> None:
    def echoes(request: httpx.Request) -> httpx.Response:
        sent = request.headers.get("MAPI-Key", "")
        return httpx.Response(500, json={"message": f"denied for {sent}"})

    client = _client({"/config/ver": echoes})
    response = client.post("/api/midas/verify", json={"base_url": BASE_URL}, headers={"X-Midas-Key": FAKE_KEY})
    assert FAKE_KEY not in response.text


# ---- /api/midas/combinations --------------------------------------------------------------------


def test_combinations_returns_famiglia_suggestion() -> None:
    empty = {f"/db/LCOM-{c}": {f"LCOM-{c}": {}} for c in ("CONC", "STEEL", "SRC", "STLCOMP", "SEISMIC")}
    routes = {"/db/LCOM-GEN": load_fixture("midas_lcom_gen.json"), **empty}
    client = _client(routes)
    response = client.post("/api/midas/combinations", json={"base_url": BASE_URL}, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 200
    combos = response.json()["combinations"]
    slu1 = next(c for c in combos if c["name"] == "SLU1")
    assert slu1["table_name"] == "SLU1(CB)"
    assert slu1["famiglia_suggerita"] == "SLU_STR"


def test_combinations_without_base_url_and_no_server_default_returns_400() -> None:
    client = _client({})
    response = client.post("/api/midas/combinations", json={}, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400
    assert response.json()["kind"] == "forbidden_url"


# ---- /api/midas/supports ------------------------------------------------------------------------


def test_supports_lists_constrained_nodes() -> None:
    routes = {"/db/cons": load_fixture("midas_cons.json"), "/db/node": load_fixture("midas_node.json")}
    client = _client(routes)
    response = client.post("/api/midas/supports", json={"base_url": BASE_URL}, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 200
    supports = response.json()["supports"]
    assert {s["nodo"] for s in supports} == {12, 13}
    assert {"nodo", "x_m", "y_m", "z_m"} == set(supports[0])


# ---- /api/midas/reactions -----------------------------------------------------------------------


def test_reactions_returns_righe_and_avvisi() -> None:
    client = _client({"/post/table": load_fixture("midas_reactions.json")})
    body = {
        "base_url": BASE_URL,
        "combinazioni": [{"table_name": "SLU1(CB)", "famiglia": "SLU_STR"}, {"table_name": "SLE1(CB)", "famiglia": "SLE_RARA"}],
    }
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 200
    payload = response.json()
    assert payload["n_righe"] == 2
    assert payload["avvisi"] == []
    row = next(r for r in payload["righe"] if r["combo"] == "SLU1")
    assert row["famiglia"] == "SLU_STR"
    assert row["fz_kN"] == pytest.approx(847.1593)


def test_reactions_requires_at_least_one_combinazione() -> None:
    client = _client({})
    response = client.post("/api/midas/reactions", json={"base_url": BASE_URL, "combinazioni": []}, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_reactions_reports_group_and_node_filters() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        argument = json.loads(request.content)["Argument"]
        assert argument["NODE_ELEMS"] == {"STRUCTURE_GROUP_NAME": "Plinti"}
        return httpx.Response(200, json={"SS_Table": {"HEAD": _STANDARD_HEAD, "DATA": [], "FORCE": "KN", "DIST": "M"}})

    client = _client({"/post/table": handler})
    body = {"base_url": BASE_URL, "gruppo": "Plinti", "combinazioni": [{"table_name": "SLU1(CB)"}]}
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 200
    assert response.json()["n_righe"] == 0


# ---- HIGH 2: request bounds (no unbounded lists/strings reach the MIDAS client) -----------------


def test_reactions_rejects_more_than_500_combinazioni() -> None:
    client = _client({})
    combinazioni = [{"table_name": f"C{i}(CB)"} for i in range(501)]
    body = {"base_url": BASE_URL, "combinazioni": combinazioni}
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400
    assert response.json()["kind"] == "forbidden_url"


def test_reactions_accepts_exactly_500_combinazioni() -> None:
    combinazioni = [{"table_name": f"C{i}(CB)"} for i in range(500)]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"SS_Table": {"HEAD": _STANDARD_HEAD, "DATA": [], "FORCE": "KN", "DIST": "M"}})

    client = _client({"/post/table": handler})
    body = {"base_url": BASE_URL, "combinazioni": combinazioni}
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 200


def test_reactions_rejects_more_than_5000_nodi() -> None:
    client = _client({})
    body = {"base_url": BASE_URL, "nodi": list(range(1, 5002)), "combinazioni": [{"table_name": "C1(CB)"}]}
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_reactions_rejects_a_non_positive_node_id() -> None:
    client = _client({})
    body = {"base_url": BASE_URL, "nodi": [0], "combinazioni": [{"table_name": "C1(CB)"}]}
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_reactions_rejects_an_oversized_table_name() -> None:
    client = _client({})
    body = {"base_url": BASE_URL, "combinazioni": [{"table_name": "C" * 300}]}
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_reactions_rejects_an_oversized_gruppo() -> None:
    client = _client({})
    body = {"base_url": BASE_URL, "gruppo": "x" * 300, "combinazioni": [{"table_name": "C1(CB)"}]}
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_reactions_rejects_an_oversized_base_url() -> None:
    client = _client({})
    body = {"base_url": "https://moa-engineers.midasit.com/" + "g" * 300, "combinazioni": [{"table_name": "C1(CB)"}]}
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_reactions_rejects_an_invalid_famiglia() -> None:
    client = _client({})
    body = {"base_url": BASE_URL, "combinazioni": [{"table_name": "C1(CB)", "famiglia": "NOT_A_FAMIGLIA"}]}
    response = client.post("/api/midas/reactions", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_verify_rejects_an_oversized_base_url() -> None:
    client = _client({})
    body = {"base_url": "https://moa-engineers.midasit.com/" + "g" * 300}
    response = client.post("/api/midas/verify", json=body, headers={"X-Midas-Key": FAKE_KEY})
    assert response.status_code == 400


def test_base_url_field_itself_is_bounded_to_200_chars() -> None:
    """White-box check that the 200-char bound is the pydantic `Field`, independent of the fact
    that an over-long MIDAS URL would also fail the host/path check downstream."""
    from pydantic import ValidationError

    from strutture.web.routes.midas import _BaseUrlBody

    _BaseUrlBody.model_validate({"base_url": "x" * 200})  # exactly at the limit: fine
    with pytest.raises(ValidationError):
        _BaseUrlBody.model_validate({"base_url": "x" * 201})
