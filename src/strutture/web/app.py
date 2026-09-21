"""Generic, schema-driven web app factory. No per-tool code lives here."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from strutture.shared.tool import Tool, discover

from . import config
from .middleware.body_limit import BodySizeLimitMiddleware
from .middleware.cache_control import CacheControlMiddleware
from .middleware.rate_limit import SlidingWindowRateLimitMiddleware
from .middleware.same_origin import SameOriginMiddleware
from .middleware.security_headers import SecurityHeadersMiddleware
from .routes.comuni import build_comuni_router
from .routes.midas import build_midas_router
from .routes.tools import build_tools_router


def create_app(tools: dict[str, Tool] | None = None, settings: config.Settings | None = None) -> FastAPI:
    """Build the FastAPI app. `tools` defaults to `discover()`; inject a fake registry for tests."""
    resolved_tools = tools if tools is not None else discover()
    resolved_settings = settings if settings is not None else config.from_env()

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
    app.mount("/", StaticFiles(directory=resolved_settings.static_dir, html=True), name="static")

    return app
