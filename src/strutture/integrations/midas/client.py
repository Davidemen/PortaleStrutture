"""Read-only httpx client for the MIDAS relay API (docs/integrations/MIDAS.md §1, §2 rules 1/2/5,
§3 client.py).

Only `get` and `post_table` exist; `request` enforces the method/path allow-list even when called
directly, so no code path in this package can ever mutate, save or re-unit the engineer's model."""
import logging

import httpx

from .errors import MidasError, redact
from .settings import validate_base_url

logger = logging.getLogger(__name__)

CONNECT_TIMEOUT_S = 5.0
READ_TIMEOUT_S = 60.0
_KEY_HEADER = "MAPI-Key"
_ALLOWED_POST_PATHS = ("/post/table",)
_FORBIDDEN_MSG_IT = "Operazione non consentita: il client MIDAS è di sola lettura (solo GET e POST /post/table)."
_NO_KEY_MSG_IT = "Nessuna chiave MAPI disponibile."


class MidasClient:
    def __init__(
        self,
        base_url: str,
        key: str | None,
        *,
        transport: httpx.BaseTransport | None = None,
        allowed_hosts: tuple[str, ...] = (),
    ) -> None:
        try:
            canonical = validate_base_url(base_url, allowed_hosts)
        except ValueError as error:
            raise MidasError("forbidden_url", str(error)) from None
        self._key = key
        timeout = httpx.Timeout(connect=CONNECT_TIMEOUT_S, read=READ_TIMEOUT_S, write=READ_TIMEOUT_S, pool=READ_TIMEOUT_S)
        # httpx appends a relative request path to base_url's path verbatim (no "/" insertion), so
        # the base itself must end in one for "/config/ver" to land under ".../gen/config/ver".
        self._http = httpx.Client(base_url=f"{canonical}/", timeout=timeout, transport=transport)

    def get(self, path: str) -> dict:
        return self.request("GET", path)

    def post_table(self, argument: dict) -> dict:
        return self.request("POST", "/post/table", json={"Argument": argument})

    def request(self, method: str, path: str, json: dict | None = None) -> dict:
        """Low-level call, guarded by the read-only allow-list. Exposed (not `_request`) so the
        allow-list is directly testable: a forbidden call raises before any transport is touched."""
        _ensure_allowed(method, path)
        if not self._key:
            raise MidasError("auth", _NO_KEY_MSG_IT)
        response = self._send(method, path, json)
        return _parse_response(response, self._key)

    def _send(self, method: str, path: str, json: dict | None) -> httpx.Response:
        headers = {_KEY_HEADER: self._key} if self._key else {}
        try:
            return self._http.request(method, path, json=json, headers=headers)
        except httpx.TransportError:
            logger.info("MIDAS %s %s failed, retrying once", method, path)  # never log headers/body
            return self._retry(method, path, json, headers)

    def _retry(self, method: str, path: str, json: dict | None, headers: dict[str, str]) -> httpx.Response:
        try:
            return self._http.request(method, path, json=json, headers=headers)
        except httpx.TimeoutException:
            raise MidasError("timeout", "Timeout nella comunicazione con MIDAS. Riprova più tardi.") from None
        except httpx.TransportError:
            raise MidasError(
                "not_connected",
                "Impossibile raggiungere MIDAS. Verifica che l'app sia aperta e connessa (Apps > API Settings > Connect).",
            ) from None


def _ensure_allowed(method: str, path: str) -> None:
    normalized = path if path.startswith("/") else f"/{path}"
    if normalized == "/doc" or normalized.startswith("/doc/"):
        raise MidasError("forbidden_url", _FORBIDDEN_MSG_IT)
    if method == "GET":
        return
    if method == "POST" and normalized in _ALLOWED_POST_PATHS:
        return
    raise MidasError("forbidden_url", _FORBIDDEN_MSG_IT)


def _parse_response(response: httpx.Response, key: str) -> dict:
    if response.status_code == 401:
        raise MidasError("auth", "Chiave MAPI non valida o scaduta. Aggiorna la chiave in MIDAS (Apps > API Settings).")
    try:
        body = response.json()
    except ValueError:
        message = redact(f"Risposta di MIDAS non valida (JSON malformato): {response.text[:200]}", key)
        raise MidasError("bad_response", message) from None
    if isinstance(body, dict) and set(body.keys()) == {"message"}:
        raise MidasError("bad_response", redact(f"MIDAS ha restituito un errore: {body['message']}", key))
    if response.status_code >= 400:
        raise MidasError("bad_response", f"MIDAS ha risposto con errore HTTP {response.status_code}.")
    if not isinstance(body, dict):
        raise MidasError("bad_response", "Risposta di MIDAS non valida (atteso un oggetto JSON).")
    return body
