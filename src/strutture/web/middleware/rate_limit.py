"""In-process sliding-window rate limit middleware, keyed by client address."""
import time
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..envelope import error_envelope

_WINDOW_SECONDS = 60.0
_RATE_LIMIT_MESSAGE_IT = "Troppe richieste. Riprova tra qualche istante."


class SlidingWindowRateLimitMiddleware(BaseHTTPMiddleware):
    """Rejects a client once it exceeds `limit_per_minute` requests in the trailing 60s."""

    def __init__(self, app, limit_per_minute: int) -> None:
        super().__init__(app)
        self._limit_per_minute = limit_per_minute
        self._hits: dict[str, list[float]] = {}

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        client_key = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window_start = now - _WINDOW_SECONDS
        recent_hits = [hit for hit in self._hits.get(client_key, []) if hit >= window_start]

        if len(recent_hits) >= self._limit_per_minute:
            self._hits = {**self._hits, client_key: recent_hits}
            return error_envelope(_RATE_LIMIT_MESSAGE_IT, 429)

        self._hits = {**self._hits, client_key: [*recent_hits, now]}
        return await call_next(request)
