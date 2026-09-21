"""CSRF protection for every unsafe /api/* request (security review HIGH 1; docs/integrations/
MIDAS.md §2 rule 2).

A cross-origin page can send a POST with `Content-Type: text/plain` (or
`application/x-www-form-urlencoded`) without a CORS preflight — a "simple request" in browser
terms. `request.json()` parses such a body anyway, so without this check a malicious page could
drive any state-changing /api/* call through an authenticated engineer's browser session. This
middleware is global (not MIDAS-specific): every unsafe method on /api/* must declare
`Content-Type: application/json`, and must not carry evidence of being cross-origin."""
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from ..envelope import error_envelope

API_PREFIX = "/api/"
_UNSAFE_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})
_REQUIRED_CONTENT_TYPE = "application/json"
_SAFE_FETCH_SITES = frozenset({"same-origin", "none"})
_UNSUPPORTED_CONTENT_TYPE_IT = "Content-Type non supportato: usare application/json."
_CROSS_ORIGIN_IT = "Richiesta rifiutata: origine non consentita."


class SameOriginMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable[[Request], Awaitable[Response]]) -> Response:
        if request.method in _UNSAFE_METHODS and request.url.path.startswith(API_PREFIX):
            rejection = _reject(request)
            if rejection is not None:
                return rejection
        return await call_next(request)


def _reject(request: Request) -> Response | None:
    if _media_type(request.headers.get("content-type", "")) != _REQUIRED_CONTENT_TYPE:
        return error_envelope(_UNSUPPORTED_CONTENT_TYPE_IT, 415)

    fetch_site = request.headers.get("sec-fetch-site")
    if fetch_site is not None and fetch_site not in _SAFE_FETCH_SITES:
        return error_envelope(_CROSS_ORIGIN_IT, 403)

    origin = request.headers.get("origin")
    if origin is not None and not _same_origin(origin, request):
        return error_envelope(_CROSS_ORIGIN_IT, 403)

    return None


def _media_type(content_type: str) -> str:
    return content_type.split(";", 1)[0].strip().lower()


def _same_origin(origin: str, request: Request) -> bool:
    parts = urlsplit(origin)
    origin_tuple = (parts.scheme, (parts.hostname or "").lower(), parts.port or _default_port(parts.scheme))
    request_tuple = (request.url.scheme, request.url.hostname, request.url.port or _default_port(request.url.scheme))
    return origin_tuple == request_tuple


def _default_port(scheme: str) -> int | None:
    return {"http": 80, "https": 443}.get(scheme)
