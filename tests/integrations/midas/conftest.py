"""Shared fixtures for the MIDAS integration tests: fixture JSON loader + a MockTransport builder
that dispatches on request path, so each test only lists the endpoints it cares about."""
import json
from collections.abc import Callable
from pathlib import Path

import httpx
import pytest

FIXTURES_DIR = Path(__file__).resolve().parents[2] / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES_DIR / name).read_text(encoding="utf-8"))


def make_transport(routes: dict[str, dict | Callable[[httpx.Request], httpx.Response]], *, default_status: int = 200) -> httpx.MockTransport:
    """`routes` maps a path suffix (e.g. "/config/ver") to a JSON body, or to a callable that
    receives the request and returns a full `httpx.Response` (for custom status codes/errors)."""

    def handler(request: httpx.Request) -> httpx.Response:
        for suffix, value in routes.items():
            if request.url.path.endswith(suffix):
                if callable(value):
                    return value(request)
                return httpx.Response(default_status, json=value)
        return httpx.Response(404, json={"message": f"no route for {request.url.path}"})

    return httpx.MockTransport(handler)


@pytest.fixture
def fixture() -> Callable[[str], dict]:
    return load_fixture
