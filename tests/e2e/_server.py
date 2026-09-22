"""Boot the app on a free localhost port, in-process, on a background thread.

Portable to Windows: no shell syntax, no subprocess, sockets only. A dataclass-free
plain object is fine here since this is test-only harness code, not app state.
"""
import socket
import threading
import time
import urllib.error
import urllib.request

import uvicorn

from strutture.shared.tool import discover
from strutture.storage.impostazioni_memory import InMemoryImpostazioniRepository
from strutture.storage.memory import InMemorySignoffRepository
from strutture.storage.progetti_memory import InMemoryProjectRepository
from strutture.web import config as web_config
from strutture.web.app import create_app

from ._demo_tool import DEMO_RELAZIONE, DEMO_TABELLA, DEMO_TABELLA_MIDAS

_READY_TIMEOUT_S = 15.0
_READY_POLL_S = 0.05


class LiveServer:
    """A running uvicorn server plus the means to stop it. Immutable after construction."""

    def __init__(self, base_url: str, server: uvicorn.Server, thread: threading.Thread) -> None:
        self.base_url = base_url
        self._server = server
        self._thread = thread

    def stop(self) -> None:
        self._server.should_exit = True
        self._thread.join(timeout=5)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def _wait_until_ready(url: str) -> None:
    deadline = time.monotonic() + _READY_TIMEOUT_S
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            urllib.request.urlopen(url, timeout=1)
            return
        except (urllib.error.URLError, ConnectionError, OSError) as error:
            last_error = error
            time.sleep(_READY_POLL_S)
    raise RuntimeError(f"e2e dev server at {url} never became ready") from last_error


def start_live_server(static_dir) -> LiveServer:
    """Serve `static_dir` with the real tool registry plus the e2e demo table tool."""
    port = _free_port()
    tools = {
        **discover(),
        DEMO_TABELLA.name: DEMO_TABELLA,
        DEMO_TABELLA_MIDAS.name: DEMO_TABELLA_MIDAS,
        DEMO_RELAZIONE.name: DEMO_RELAZIONE,
    }
    settings = web_config.Settings(
        rate_limit_per_minute=100_000,
        max_body_bytes=8_000_000,
        host="127.0.0.1",
        port=port,
        static_dir=static_dir,
    )
    # In-memory stores: a browser test that signs off a correction or saves a project must never
    # write into the office's real `var/` database.
    app = create_app(tools=tools, settings=settings, signoffs=InMemorySignoffRepository(),
                     progetti=InMemoryProjectRepository(), impostazioni=InMemoryImpostazioniRepository())
    uv_config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(uv_config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{port}"
    _wait_until_ready(base_url + "/")
    return LiveServer(base_url, server, thread)
