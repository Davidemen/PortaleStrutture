"""In-process sliding-window rate limit middleware, keyed by client address."""
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..envelope import error_envelope

_WINDOW_SECONDS = 60.0
_RATE_LIMIT_MESSAGE_IT = "Troppe richieste. Riprova tra qualche istante."
# Static assets (`/js`, `/css`, `/fonts`, the favicon) never count against the budget -- with
# `cache-control: no-cache` a single page load already fires one request per module (~140 measured
# with this wave's ~40 new JS files), so a handful of reloads plus a live calculation could hit 429
# on an otherwise idle project page. Only `/api/...` traffic is meant to be limited.
_PERCORSI_ESCLUSI = ("/js/", "/css/", "/fonts/", "/favicon.ico")


class SlidingWindowRateLimitMiddleware(BaseHTTPMiddleware):
    """Rejects a client once it exceeds `limit_per_minute` requests in the trailing 60s, counting
    only `/api/...` requests -- static assets are served from `_PERCORSI_ESCLUSI` and skip the
    limiter entirely."""

    def __init__(self, app, limit_per_minute: int) -> None:
        super().__init__(app)
        self._limit_per_minute = limit_per_minute
        self._hits: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.url.path.startswith(_PERCORSI_ESCLUSI):
            return await call_next(request)
        client_key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - _WINDOW_SECONDS
        recent_hits = [hit for hit in self._hits.get(client_key, []) if hit >= window_start]

        if len(recent_hits) >= self._limit_per_minute:
            self._hits = {**self._hits, client_key: recent_hits}
            return error_envelope(_RATE_LIMIT_MESSAGE_IT, 429)

        self._hits = {**self._hits, client_key: [*recent_hits, now]}
        return await call_next(request)
