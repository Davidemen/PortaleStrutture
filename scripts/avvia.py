"""Office launcher: start the server and open the browser once it answers.

    uv run python scripts/avvia.py [--host 127.0.0.1] [--port 8000] [--no-browser] [...web flags]

Double-click wrappers: `Avvia StruttureMenni.bat` (Windows) and `Avvia StruttureMenni.command`
(macOS). Every flag of `python -m strutture.web` passes through unchanged. Portable: no shell
syntax, stdlib only. The browser is opened from a daemon thread AFTER the server answers — opening it
first shows a "connection refused" page the engineer then has to reload by hand.
"""
import sys
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from collections.abc import Callable

from strutture.web.__main__ import main as serve

HOST_PREDEFINITO = "127.0.0.1"
PORTA_PREDEFINITA = 8000
_TUTTE_LE_INTERFACCE = ("0.0.0.0", "::")


def url_locale(hosts: str, port: int) -> str:
    """The address to open in THIS machine's browser: loopback whenever the server listens on it
    (also via "all interfaces"), otherwise the first host given."""
    elenco = [h.strip() for h in hosts.split(",") if h.strip()]
    locale = any(h in (HOST_PREDEFINITO, "localhost", *_TUTTE_LE_INTERFACCE) for h in elenco)
    return f"http://{HOST_PREDEFINITO if locale or not elenco else elenco[0]}:{port}/"


def _risponde(url: str) -> bool:
    try:
        with urllib.request.urlopen(url, timeout=1):
            return True
    except (urllib.error.URLError, ConnectionError, OSError):
        return False


def attendi_e_apri(url: str, *, pronto: Callable[[str], bool] = _risponde, apri: Callable[[str], object] = webbrowser.open,
                   pausa: Callable[[float], None] = time.sleep, tentativi: int = 100) -> bool:
    """Poll `url` until it answers, then open it; False (and no browser) if it never does."""
    for _ in range(tentativi):
        if pronto(url):
            apri(url)
            return True
        pausa(0.2)
    return False


def _valore(argv: list[str], flag: str, predefinito: str) -> str:
    return argv[argv.index(flag) + 1] if flag in argv and argv.index(flag) + 1 < len(argv) else predefinito


def main() -> None:
    argv = sys.argv[1:]
    apri_browser = "--no-browser" not in argv
    sys.argv = [sys.argv[0], *(a for a in argv if a != "--no-browser")]
    if apri_browser:
        url = url_locale(_valore(argv, "--host", HOST_PREDEFINITO), int(_valore(argv, "--port", str(PORTA_PREDEFINITA))))
        threading.Thread(target=attendi_e_apri, args=(url,), daemon=True).start()
    serve()


if __name__ == "__main__":
    main()
