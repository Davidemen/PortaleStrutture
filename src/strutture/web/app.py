"""Generic, schema-driven web app factory. No per-tool code lives here."""
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from strutture.shared.tool import Tool, discover
from strutture.storage.interfaces import SignoffRepository
from strutture.storage.models import Signoff, Stato

from . import config
from .middleware.body_limit import BodySizeLimitMiddleware
from .middleware.cache_control import CacheControlMiddleware
from .middleware.rate_limit import SlidingWindowRateLimitMiddleware
from .middleware.same_origin import SameOriginMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware
from .routes.comuni import build_comuni_router
from .routes.divergences import build_divergences_router
from .routes.midas import build_midas_router
from .routes.tools import build_tools_router


def create_app(
    tools: dict[str, Tool] | None = None,
    settings: config.Settings | None = None,
    signoffs: SignoffRepository | None = None,
) -> FastAPI:
    """Build the FastAPI app. `tools` defaults to `discover()`; inject a fake registry for tests.
    `signoffs` defaults to the real SQLite repository, imported lazily so tests never need it
    (they inject a small in-test fake implementing `SignoffRepository` instead)."""
    resolved_tools = tools if tools is not None else discover()
    resolved_settings = settings if settings is not None else config.from_env()
    resolved_signoffs = signoffs if signoffs is not None else _default_signoff_repository(resolved_settings.data_dir)

    app = FastAPI(title="StruttureMenni", docs_url=None, redoc_url=None)

    # Starlette runs the *last*-added middleware outermost, so SecurityHeaders (added last)
    # wraps every response -- including the ones RateLimit/BodySizeLimit/SameOrigin short-circuit.
    # SameOrigin is added right before it, so a CSRF attempt is rejected before it can consume rate
    # limit budget or have its body read.
    app.add_middleware(SlidingWindowRateLimitMiddleware, limit_per_minute=resolved_settings.rate_limit_per_minute)
    app.add_middleware(BodySizeLimitMiddleware, max_bytes=resolved_settings.max_body_bytes)
    app.add_middleware(CacheControlMiddleware)
    app.add_middleware(SameOriginMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)

    app.include_router(build_tools_router(resolved_tools))
    app.include_router(build_comuni_router())
    app.include_router(build_midas_router())
    app.include_router(build_divergences_router(resolved_signoffs))
    app.mount("/", StaticFiles(directory=resolved_settings.static_dir, html=True), name="static")

    return app


def _default_signoff_repository(data_dir: Path) -> SignoffRepository:
    """Deferred to `_LazySqliteSignoffRepository`: the SQLite module is written by another agent
    in parallel, so it must not be imported before the first real call reaches it — otherwise every
    test that builds an app without passing `signoffs` (unrelated tool/comuni/midas tests) would
    fail while that module does not exist yet."""
    return _LazySqliteSignoffRepository(data_dir)


class _LazySqliteSignoffRepository:
    """Implements `SignoffRepository`, importing and opening the real repository on first use."""

    def __init__(self, data_dir: Path) -> None:
        self._data_dir = data_dir
        self._repository: SignoffRepository | None = None

    def _resolved(self) -> SignoffRepository:
        if self._repository is None:
            from strutture.storage.signoff_sqlite import open_signoff_repository

            self._repository = open_signoff_repository(self._data_dir)
        return self._repository

    def get(self, divergence_id: str) -> Signoff:
        return self._resolved().get(divergence_id)

    def list_all(self) -> dict[str, Signoff]:
        return self._resolved().list_all()

    def set(self, divergence_id: str, stato: Stato, sigla: str, nota: str = "") -> Signoff:
        return self._resolved().set(divergence_id, stato, sigla, nota)

    def history(self, divergence_id: str) -> tuple[Signoff, ...]:
        return self._resolved().history(divergence_id)
