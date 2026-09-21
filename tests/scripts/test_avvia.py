"""The office launcher (double-click on Windows/macOS): waits for the server, THEN opens the browser."""
import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

_PATH = Path(__file__).resolve().parents[2] / "scripts" / "avvia.py"
_SPEC = importlib.util.spec_from_file_location("avvia", _PATH)
avvia = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(avvia)


def test_browser_opens_only_once_the_server_answers() -> None:
    answers = iter([False, False, True])
    opened: list[str] = []
    ok = avvia.attendi_e_apri("http://127.0.0.1:8000/", pronto=lambda url: next(answers), apri=opened.append,
                              pausa=lambda s: None, tentativi=10)
    assert ok is True and opened == ["http://127.0.0.1:8000/"]


def test_browser_is_not_opened_when_the_server_never_answers() -> None:
    opened: list[str] = []
    ok = avvia.attendi_e_apri("http://127.0.0.1:8000/", pronto=lambda url: False, apri=opened.append,
                              pausa=lambda s: None, tentativi=3)
    assert ok is False and opened == []


def test_the_browser_url_is_always_local_even_when_listening_on_the_vpn_too() -> None:
    assert avvia.url_locale("127.0.0.1,100.112.1.85", 8000) == "http://127.0.0.1:8000/"
    assert avvia.url_locale("0.0.0.0", 8123) == "http://127.0.0.1:8123/"
    assert avvia.url_locale("192.168.1.20", 8000) == "http://192.168.1.20:8000/"
