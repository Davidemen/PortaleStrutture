"""Multi-address serving: STRUTTURE_WEB_HOST may list several bind addresses (e.g. localhost + VPN)."""
import pytest

from strutture.web import __main__ as entrypoint
from strutture.web import serve

pytestmark = pytest.mark.unit


def test_parse_hosts_splits_trims_and_dedupes() -> None:
    assert serve.parse_hosts("127.0.0.1, 100.112.1.85,127.0.0.1") == ("127.0.0.1", "100.112.1.85")


@pytest.mark.parametrize("raw", ["", " , ", "127.0.0.1,not an address"])
def test_parse_hosts_rejects_blank_or_invalid(raw: str) -> None:
    with pytest.raises(ValueError):
        serve.parse_hosts(raw)


def test_bind_sockets_listens_on_every_host() -> None:
    sockets = serve.bind_sockets(("127.0.0.1",), port=0)
    try:
        assert [s.getsockname()[0] for s in sockets] == ["127.0.0.1"]
        assert sockets[0].getsockname()[1] > 0
    finally:
        for sock in sockets:
            sock.close()


def test_bind_sockets_closes_earlier_sockets_when_a_later_bind_fails() -> None:
    with pytest.raises(OSError):
        serve.bind_sockets(("127.0.0.1", "203.0.113.1"), port=0)  # TEST-NET-3: never a local address


def test_main_serves_all_hosts_through_one_server(monkeypatch: pytest.MonkeyPatch) -> None:
    served: dict[str, object] = {}
    monkeypatch.setenv("STRUTTURE_WEB_HOST", "127.0.0.1,100.112.1.85")
    monkeypatch.setenv("STRUTTURE_WEB_PORT", "9002")
    monkeypatch.setattr(serve, "bind_sockets", lambda hosts, port: served.update(hosts=hosts, port=port) or ["sock"])

    class FakeServer:
        def __init__(self, config: object) -> None:
            served["config"] = config

        def run(self, sockets: list[object]) -> None:
            served["sockets"] = sockets

    monkeypatch.setattr(serve.uvicorn, "Server", FakeServer)
    entrypoint.main([])
    assert served["hosts"] == ("127.0.0.1", "100.112.1.85") and served["port"] == 9002 and served["sockets"] == ["sock"]
