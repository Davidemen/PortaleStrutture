"""`python -m strutture.web --host … --port …` works the same in PowerShell, cmd and POSIX shells."""
import socket
from pathlib import Path

import pytest

from strutture.web import __main__ as entrypoint
from strutture.web import config, serve

pytestmark = pytest.mark.unit


def test_flags_override_environment(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<!doctype html>", encoding="utf-8")
    base = config.from_env({"STRUTTURE_WEB_HOST": "127.0.0.1", "STRUTTURE_WEB_PORT": "8000"})
    settings = entrypoint.apply_cli(base, ["--host", "127.0.0.1,100.112.1.85", "--port", "9100", "--static-dir", str(tmp_path)])
    assert (settings.host, settings.port, settings.static_dir) == ("127.0.0.1,100.112.1.85", 9100, tmp_path.resolve())


def test_no_flags_keeps_environment_settings() -> None:
    base = config.from_env({"STRUTTURE_WEB_PORT": "8123"})
    assert entrypoint.apply_cli(base, []) == base


@pytest.mark.parametrize("argv", [["--port", "0"], ["--port", "70000"], ["--static-dir", "does-not-exist"]])
def test_invalid_flags_exit_with_usage_error(argv: list[str]) -> None:
    with pytest.raises(SystemExit):
        entrypoint.apply_cli(config.from_env({}), argv)


def test_windows_gets_exclusive_address_use_instead_of_reuseaddr(monkeypatch: pytest.MonkeyPatch) -> None:
    # On Windows SO_REUSEADDR lets another process hijack the port; SO_EXCLUSIVEADDRUSE is the safe option.
    monkeypatch.setattr(serve.sys, "platform", "win32")
    monkeypatch.setattr(serve.socket, "SO_EXCLUSIVEADDRUSE", 0xFFFB, raising=False)
    assert serve.listen_options() == ((socket.SOL_SOCKET, 0xFFFB, 1),)
    monkeypatch.setattr(serve.sys, "platform", "darwin")
    assert serve.listen_options() == ((socket.SOL_SOCKET, socket.SO_REUSEADDR, 1),)
