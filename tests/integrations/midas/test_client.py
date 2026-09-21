"""Rule 1 (read-only allow-list), rule 5 (timeouts/retry), error mapping and key redaction —
docs/integrations/MIDAS.md §2, §3 client.py."""
import logging

import httpx
import pytest

from strutture.integrations.midas import MidasClient, MidasError

from .conftest import make_transport

BASE_URL = "https://moa-engineers.midasit.com:443/gen"
FAKE_KEY = "MAPI-FAKEKEY-DO-NOT-LEAK-1234"


def _client(routes: dict, key: str | None = FAKE_KEY) -> MidasClient:
    return MidasClient(BASE_URL, key, transport=make_transport(routes))


@pytest.mark.unit
def test_get_is_allowed() -> None:
    client = _client({"/config/ver": {"VER": {"NAME": "midas Gen NX", "VERSION": "1.0"}}})
    assert client.get("/config/ver")["VER"]["NAME"] == "midas Gen NX"


@pytest.mark.unit
def test_post_table_is_allowed() -> None:
    client = _client({"/post/table": {"SS_Table": {"HEAD": [], "DATA": []}}})
    assert client.post_table({"TABLE_NAME": "SS_Table"}) == {"SS_Table": {"HEAD": [], "DATA": []}}


@pytest.mark.unit
@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("PUT", "/db/node"),
        ("DELETE", "/db/node"),
        ("POST", "/db/node"),
        ("GET", "/doc/open"),
        ("GET", "/doc"),
        ("POST", "/doc/save"),
        ("PUT", "/post/table"),
    ],
)
def test_write_and_doc_operations_raise_before_any_request_is_made(method: str, path: str) -> None:
    def never_called(request: httpx.Request) -> httpx.Response:
        raise AssertionError("transport must never be reached for a forbidden method/path")

    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(never_called))
    with pytest.raises(MidasError) as exc_info:
        client.request(method, path)
    assert exc_info.value.kind == "forbidden_url"
    assert exc_info.value.status_code == 400


@pytest.mark.unit
def test_missing_key_raises_auth_before_any_request() -> None:
    def never_called(request: httpx.Request) -> httpx.Response:
        raise AssertionError("transport must never be reached without a key")

    client = MidasClient(BASE_URL, None, transport=httpx.MockTransport(never_called))
    with pytest.raises(MidasError) as exc_info:
        client.get("/config/ver")
    assert exc_info.value.kind == "auth"


@pytest.mark.unit
def test_401_maps_to_auth_error() -> None:
    client = _client({"/config/ver": lambda r: httpx.Response(401, json={"message": "invalid key"})})
    with pytest.raises(MidasError) as exc_info:
        client.get("/config/ver")
    assert exc_info.value.kind == "auth"
    assert exc_info.value.status_code == 401


@pytest.mark.unit
def test_message_error_body_maps_to_bad_response() -> None:
    client = _client({"/config/ver": lambda r: httpx.Response(200, json={"message": "Please connect API first."})})
    with pytest.raises(MidasError) as exc_info:
        client.get("/config/ver")
    assert exc_info.value.kind == "bad_response"
    assert exc_info.value.status_code == 502


@pytest.mark.unit
def test_timeout_maps_to_timeout_error_with_one_retry() -> None:
    attempts = {"n": 0}

    def flaky(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        raise httpx.ReadTimeout("simulated timeout", request=request)

    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(flaky))
    with pytest.raises(MidasError) as exc_info:
        client.get("/config/ver")
    assert exc_info.value.kind == "timeout"
    assert exc_info.value.status_code == 504
    assert attempts["n"] == 2  # one retry, no more


@pytest.mark.unit
def test_connect_error_maps_to_not_connected() -> None:
    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated connection failure", request=request)

    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(unreachable))
    with pytest.raises(MidasError) as exc_info:
        client.get("/config/ver")
    assert exc_info.value.kind == "not_connected"
    assert exc_info.value.status_code == 502


@pytest.mark.unit
def test_retry_recovers_on_second_attempt() -> None:
    attempts = {"n": 0}

    def flaky_then_ok(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] == 1:
            raise httpx.ConnectError("simulated blip", request=request)
        return httpx.Response(200, json={"VER": {"NAME": "midas Gen NX", "VERSION": "1.0"}})

    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(flaky_then_ok))
    body = client.get("/config/ver")
    assert body["VER"]["NAME"] == "midas Gen NX"
    assert attempts["n"] == 2


@pytest.mark.unit
def test_malformed_json_maps_to_bad_response() -> None:
    def not_json(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, content=b"not json at all")

    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(not_json))
    with pytest.raises(MidasError) as exc_info:
        client.get("/config/ver")
    assert exc_info.value.kind == "bad_response"


@pytest.mark.unit
def test_key_never_appears_in_any_exception_message(caplog: pytest.LogCaptureFixture) -> None:
    """The key must never leak: not in the raised message, and not in any log record we emit."""

    def echoes_key(request: httpx.Request) -> httpx.Response:
        # Simulate a pathological MIDAS error that echoes request data back, including headers.
        sent_key = request.headers.get("MAPI-Key", "")
        return httpx.Response(500, json={"message": f"forbidden for key {sent_key}"})

    caplog.set_level(logging.DEBUG)
    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(echoes_key))
    with pytest.raises(MidasError) as exc_info:
        client.get("/config/ver")
    assert FAKE_KEY not in str(exc_info.value)
    assert FAKE_KEY not in exc_info.value.message_it
    for record in caplog.records:
        assert FAKE_KEY not in record.getMessage()


@pytest.mark.unit
def test_key_never_appears_in_logs_on_retry(caplog: pytest.LogCaptureFixture) -> None:
    def unreachable(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("simulated failure", request=request)

    caplog.set_level(logging.DEBUG)
    client = MidasClient(BASE_URL, FAKE_KEY, transport=httpx.MockTransport(unreachable))
    with pytest.raises(MidasError):
        client.get("/config/ver")
    for record in caplog.records:
        assert FAKE_KEY not in record.getMessage()


@pytest.mark.unit
def test_generic_http_error_status_maps_to_bad_response() -> None:
    client = _client({"/config/ver": lambda r: httpx.Response(500, json={"detail": "boom"})})
    with pytest.raises(MidasError) as exc_info:
        client.get("/config/ver")
    assert exc_info.value.kind == "bad_response"
    assert "500" in exc_info.value.message_it


@pytest.mark.unit
def test_non_dict_json_body_maps_to_bad_response() -> None:
    client = _client({"/config/ver": lambda r: httpx.Response(200, json=[1, 2, 3])})
    with pytest.raises(MidasError) as exc_info:
        client.get("/config/ver")
    assert exc_info.value.kind == "bad_response"


@pytest.mark.unit
def test_base_url_is_validated_at_construction() -> None:
    with pytest.raises(MidasError) as exc_info:
        MidasClient("http://evil.example.com/gen", FAKE_KEY)
    assert exc_info.value.kind == "forbidden_url"
