"""HIGH 2 (security review): MIDAS calls are synchronous httpx; if a route handler ran them
directly inside `async def`, one slow/large MIDAS request would block the single event loop and
every other concurrent API request with it. Route handlers must off-load that work to a thread."""
import time
from concurrent.futures import ThreadPoolExecutor

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from strutture.integrations.midas import MidasClient
from strutture.web.routes.midas import build_midas_router
from strutture.web.routes.tools import build_tools_router
from tests.fixtures.web_fake_tools import FAKE_TOOLS

pytestmark = pytest.mark.unit

BASE_URL = "https://moa-engineers.midasit.com:443/gen"
FAKE_KEY = "FAKEKEY"
_SLOW_SECONDS = 1.5  # long enough that runner jitter (~0.1 s) cannot reach the half-way threshold


def _slow_handler(request: httpx.Request) -> httpx.Response:
    if request.url.path.endswith("/config/ver"):
        time.sleep(_SLOW_SECONDS)  # simulate a slow MIDAS relay, synchronously (real httpx blocks)
        return httpx.Response(200, json={"VER": {"NAME": "midas Gen NX", "VERSION": "1.0"}})
    return httpx.Response(200, json={"UNIT": {"1": {"FORCE": "KN", "DIST": "M"}}})


def _slow_factory(base_url: str, key: str) -> MidasClient:
    return MidasClient(base_url, key, transport=httpx.MockTransport(_slow_handler))


@pytest.fixture
def app() -> FastAPI:
    fastapi_app = FastAPI()
    fastapi_app.include_router(build_midas_router(client_factory=_slow_factory))
    fastapi_app.include_router(build_tools_router(FAKE_TOOLS))
    return fastapi_app


def test_a_slow_midas_call_does_not_block_a_concurrent_api_request(app: FastAPI) -> None:
    # Outside a `with` block, TestClient spins up a brand-new event loop per call (no shared
    # state to block). Only inside `with TestClient(...)` does every request share ONE portal/event
    # loop -- which is exactly the scenario a real server has, and the one this test must exercise.
    with TestClient(app) as client, ThreadPoolExecutor(max_workers=2) as pool:
        slow_future = pool.submit(
            client.post, "/api/midas/verify", json={"base_url": BASE_URL}, headers={"X-Midas-Key": FAKE_KEY}
        )
        time.sleep(0.05)  # let the slow request start first
        fast_start = time.monotonic()
        fast_response = client.get("/api/tools")
        fast_elapsed = time.monotonic() - fast_start
        slow_response = slow_future.result()

    assert slow_response.status_code == 200
    assert fast_response.status_code == 200
    # if the MIDAS call blocked the event loop, this would take ~_SLOW_SECONDS too
    assert fast_elapsed < _SLOW_SECONDS / 2
