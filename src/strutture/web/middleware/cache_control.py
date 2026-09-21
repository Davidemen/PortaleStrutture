"""Cache policy: static assets revalidate on every load (ETag -> cheap 304); API responses are never stored."""
from collections.abc import Awaitable, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

API_PREFIX = "/api/"
STATIC_POLICY = "no-cache"
API_POLICY = "no-store"


class CacheControlMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        response = await call_next(request)
        response.headers["Cache-Control"] = API_POLICY if request.url.path.startswith(API_PREFIX) else STATIC_POLICY
        return response
