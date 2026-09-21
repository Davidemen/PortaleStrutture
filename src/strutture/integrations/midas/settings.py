"""Server-side MIDAS configuration: base URL / product defaults, the SSRF allow-list escape hatch
for tests, and MAPI-key resolution (docs/integrations/MIDAS.md §1 Base URL, §2 rules 2-3)."""
import os
import re
from typing import Literal
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict

Product = Literal["gen", "civil"]

_HOST_RE = re.compile(r"^moa-engineers(-[a-z]{2})?\.midasit\.(com|cn)$")
_ALLOWED_PATHS = ("/gen", "/civil")
_KEY_ENV_VAR = "MIDAS_MAPI_KEY"


class MidasSettings(BaseModel):
    """Server defaults; read fresh from the environment, never cached across requests."""

    model_config = ConfigDict(frozen=True)

    base_url: str | None = None
    product: Product | None = None
    allowed_hosts: tuple[str, ...] = ()

    @classmethod
    def from_env(cls, env: dict[str, str] | None = None) -> "MidasSettings":
        source = env if env is not None else os.environ
        product = source.get("MIDAS_PRODUCT")
        allowed = tuple(h.strip() for h in source.get("MIDAS_ALLOWED_HOSTS", "").split(",") if h.strip())
        return cls(
            base_url=source.get("MIDAS_BASE_URL") or None,
            product=product if product in ("gen", "civil") else None,
            allowed_hosts=allowed,
        )


def resolve_key(header_key: str | None, env: dict[str, str] | None = None) -> str | None:
    """Rule 2: header `X-Midas-Key` first, then server env `MIDAS_MAPI_KEY`."""
    if header_key and header_key.strip():
        return header_key.strip()
    source = env if env is not None else os.environ
    return source.get(_KEY_ENV_VAR) or None


def has_server_key(env: dict[str, str] | None = None) -> bool:
    """`GET /api/midas/status` needs this without ever revealing the key itself."""
    source = env if env is not None else os.environ
    return bool(source.get(_KEY_ENV_VAR))


def validate_base_url(base_url: str, allowed_hosts: tuple[str, ...] = ()) -> str:
    """Rule 3 (no SSRF): https, port 443 (or none), host matching the MIDAS relay pattern, path
    `/gen` or `/civil`. `allowed_hosts` (`host:port` strings, from `MIDAS_ALLOWED_HOSTS`) is the
    only escape hatch, used by tests to point at a fake in-process relay."""
    parts = urlsplit(base_url)
    if parts.username or parts.password:
        raise ValueError("URL non valido: non sono ammesse credenziali nell'URL.")
    try:
        port = parts.port  # raises its own (English) ValueError for a port outside 0-65535
    except ValueError:
        raise ValueError("URL non valido: porta non consentita.") from None
    host = parts.hostname or ""  # urlsplit() already lower-cases this
    host_port = f"{host}:{port if port is not None else 443}"
    if host_port not in allowed_hosts:
        if parts.scheme != "https":
            raise ValueError("URL non valido: lo schema deve essere https.")
        if port not in (443, None):
            raise ValueError("URL non valido: porta non consentita.")
        if not _HOST_RE.match(host):
            raise ValueError("URL non valido: host non consentito.")
    if parts.path not in _ALLOWED_PATHS:
        raise ValueError("URL non valido: il percorso deve essere /gen o /civil.")
    netloc = host if port is None else f"{host}:{port}"
    return f"{parts.scheme}://{netloc}{parts.path}"
