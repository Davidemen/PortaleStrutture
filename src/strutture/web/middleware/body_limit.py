"""Rejects requests whose body exceeds a configured byte cap."""
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..envelope import error_envelope

_BODY_TOO_LARGE_MESSAGE_IT = "Il corpo della richiesta supera la dimensione massima consentita."


class BodySizeLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_bytes: int) -> None:
        super().__init__(app)
        self._max_bytes = max_bytes

    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        content_length = request.headers.get("content-length")
        if content_length is not None and content_length.isdigit() and int(content_length) > self._max_bytes:
            return error_envelope(_BODY_TOO_LARGE_MESSAGE_IT, 413)

        body = await request.body()
        if len(body) > self._max_bytes:
            return error_envelope(_BODY_TOO_LARGE_MESSAGE_IT, 413)

        return await call_next(request)
