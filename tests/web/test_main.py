import pytest

import strutture.web.__main__ as web_main


@pytest.mark.unit
def test_main_starts_uvicorn_with_configured_host_and_port(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    def fake_run(app, host, port):
        captured["host"] = host
        captured["port"] = port

    monkeypatch.setenv("STRUTTURE_WEB_HOST", "0.0.0.0")
    monkeypatch.setenv("STRUTTURE_WEB_PORT", "9001")
    monkeypatch.setattr(web_main.uvicorn, "run", fake_run)

    web_main.main([])

    assert captured == {"host": "0.0.0.0", "port": 9001}
