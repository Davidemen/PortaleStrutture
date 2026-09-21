"""Serve the web UI:  python -m strutture.web [--host 127.0.0.1,100.112.1.85] [--port 8000] [--static-dir DIR]

Flags work identically in PowerShell, cmd and POSIX shells; the STRUTTURE_WEB_* environment
variables remain as defaults. --host accepts several comma-separated addresses (localhost + VPN).
"""
import argparse
import dataclasses
import sys
from pathlib import Path

import uvicorn

from . import config, serve
from .app import create_app

MAX_PORT = 65535


def _port(raw: str) -> int:
    value = int(raw)
    if not 0 < value <= MAX_PORT:
        raise argparse.ArgumentTypeError(f"port must be between 1 and {MAX_PORT}")
    return value


def _static_dir(raw: str) -> Path:
    path = Path(raw).expanduser().resolve()
    if not (path / "index.html").is_file():
        raise argparse.ArgumentTypeError(f"no index.html found in {path}")
    return path


def apply_cli(settings: config.Settings, argv: list[str]) -> config.Settings:
    """Settings with command-line overrides applied (a new object; the input is not modified)."""
    parser = argparse.ArgumentParser(prog="python -m strutture.web", description="StruttureMenni web UI")
    parser.add_argument("--host", help="bind address(es), comma-separated")
    parser.add_argument("--port", type=_port)
    parser.add_argument("--static-dir", type=_static_dir, dest="static_dir", help="serve a different UI directory")
    given = {key: value for key, value in vars(parser.parse_args(argv)).items() if value is not None}
    return dataclasses.replace(settings, **given)


def main(argv: list[str] | None = None) -> None:
    settings = apply_cli(config.from_env(), sys.argv[1:] if argv is None else argv)
    app = create_app(settings=settings)
    hosts = serve.parse_hosts(settings.host)
    if len(hosts) == 1:
        uvicorn.run(app, host=hosts[0], port=settings.port)
    else:
        serve.serve(app, hosts, settings.port)


if __name__ == "__main__":
    main()
