"""STRUTTURE_WEB_STATIC_DIR lets a staging copy of the UI be served without touching the live one."""
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from strutture.web import config, create_app

pytestmark = pytest.mark.integration


def test_default_static_dir_is_the_packaged_ui() -> None:
    assert config.from_env({}).static_dir.name == "static"
    assert (config.from_env({}).static_dir / "index.html").is_file()


def test_custom_static_dir_is_served(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text("<!doctype html><title>staging</title>", encoding="utf-8")
    settings = config.from_env({"STRUTTURE_WEB_STATIC_DIR": str(tmp_path)})
    response = TestClient(create_app(tools={}, settings=settings)).get("/")
    assert response.status_code == 200 and "staging" in response.text


def test_missing_static_dir_fails_fast(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="STRUTTURE_WEB_STATIC_DIR"):
        config.from_env({"STRUTTURE_WEB_STATIC_DIR": str(tmp_path / "nope")})
