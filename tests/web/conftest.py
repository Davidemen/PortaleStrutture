import pytest
from fastapi.testclient import TestClient

from strutture.web import config
from strutture.web.app import create_app
from tests.fixtures.web_fake_tools import FAKE_TOOLS


@pytest.fixture
def settings() -> config.Settings:
    return config.Settings(rate_limit_per_minute=120, max_body_bytes=1_000_000, host="127.0.0.1", port=8000)


@pytest.fixture
def client(settings: config.Settings) -> TestClient:
    app = create_app(tools=FAKE_TOOLS, settings=settings)
    return TestClient(app)
