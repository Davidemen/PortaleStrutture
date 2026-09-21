"""Session-scoped app boot + per-test browser contexts for the e2e suite (DESIGN_SPEC §6.F, §7).

`pytest-playwright` is not a project dependency (spec §6.E), so importing it must not break
the default `pytest` run: `pytest_ignore_collect` below skips this whole package when it is
absent, and every Playwright type is only referenced in (unevaluated, PEP 563) annotations.
"""
from __future__ import annotations

import os
from collections.abc import Iterator
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from ._playwright_available import PLAYWRIGHT_AVAILABLE

if TYPE_CHECKING:
    from playwright.sync_api import Browser, BrowserContext, Page

    from ._collectors import PageCollectors
    from ._server import LiveServer

_DEFAULT_STATIC_DIR = Path(__file__).resolve().parents[2] / "src" / "strutture" / "web" / "static"
# Overridable so the same suite can be pointed at the static_next staging copy (UI_BRIEF.md
# "Staging") without touching this file per run; unset/empty -> unchanged default (live static/).
STATIC_DIR = Path(os.environ["STRUTTURE_E2E_STATIC_DIR"]) if os.environ.get("STRUTTURE_E2E_STATIC_DIR") else _DEFAULT_STATIC_DIR
DESKTOP_VIEWPORT = {"width": 1440, "height": 900}
MOBILE_VIEWPORT = {"width": 390, "height": 844}
TABLET_VIEWPORT = {"width": 900, "height": 1000}


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    """Skip this whole directory's test modules when Playwright is not installed."""
    if not PLAYWRIGHT_AVAILABLE and collection_path.resolve() != Path(__file__).resolve():
        return True
    return None


@pytest.fixture(scope="session")
def live_server() -> Iterator[LiveServer]:
    from ._server import start_live_server

    server = start_live_server(STATIC_DIR)
    yield server
    server.stop()


@pytest.fixture(scope="session")
def base_url(live_server: LiveServer) -> str:
    # Overrides pytest-base-url's own session-scoped `base_url` fixture (same name, same
    # scope) so Playwright's `_verify_url` autouse fixture checks our in-process server.
    return live_server.base_url


def _context(browser: Browser, viewport: dict[str, int]) -> Iterator[BrowserContext]:
    context = browser.new_context(viewport=viewport)
    yield context
    context.close()


@pytest.fixture
def desktop_context(browser: Browser) -> Iterator[BrowserContext]:
    yield from _context(browser, DESKTOP_VIEWPORT)


@pytest.fixture
def mobile_context(browser: Browser) -> Iterator[BrowserContext]:
    yield from _context(browser, MOBILE_VIEWPORT)


@pytest.fixture
def tablet_context(browser: Browser) -> Iterator[BrowserContext]:
    yield from _context(browser, TABLET_VIEWPORT)


def _page(context: BrowserContext) -> Iterator[tuple[Page, PageCollectors]]:
    from ._collectors import attach

    page = context.new_page()
    page.set_default_timeout(4_000)
    collectors = attach(page)
    yield page, collectors
    page.close()


@pytest.fixture
def desktop_page(desktop_context: BrowserContext) -> Iterator[tuple[Page, PageCollectors]]:
    yield from _page(desktop_context)


@pytest.fixture
def mobile_page(mobile_context: BrowserContext) -> Iterator[tuple[Page, PageCollectors]]:
    yield from _page(mobile_context)


@pytest.fixture
def tablet_page(tablet_context: BrowserContext) -> Iterator[tuple[Page, PageCollectors]]:
    yield from _page(tablet_context)


@pytest.fixture
def page(desktop_page: tuple[Page, PageCollectors]) -> Page:
    """Default page for flows that don't care about viewport: desktop, contract-typical size."""
    return desktop_page[0]
