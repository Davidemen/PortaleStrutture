"""Connection probe: version (`GET /config/ver`), current model units (`GET /db/UNIT`), and
regional-relay autodetection (docs/integrations/MIDAS.md §1 Base URL, §3 version.py)."""
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict

from .client import MidasClient
from .errors import MidasError
from .settings import Product

# midasit.cn (China relay) is a different TLD and not auto-tried; pass its base_url explicitly.
REGIONAL_SUFFIXES = ("", "-gb", "-in", "-kr", "-us")
_PRODUCT_PATH: dict[Product, str] = {"gen": "/gen", "civil": "/civil"}


class VersionInfo(BaseModel):
    model_config = ConfigDict(frozen=True)

    product: str
    name: str
    version: str


def probe(client: MidasClient) -> VersionInfo:
    """`GET /config/ver` -> `{"VER": {"NAME": "...GEN...", ...}}` (§1)."""
    body = client.get("/config/ver")
    ver = body.get("VER") if isinstance(body, dict) else None
    if not isinstance(ver, dict) or "NAME" not in ver:
        raise MidasError("bad_response", "Risposta inattesa da MIDAS per la verifica di connessione.")
    name = str(ver["NAME"])
    return VersionInfo(product=_product_from_name(name), name=name, version=str(ver.get("VERSION", "")))


def read_units(client: MidasClient) -> tuple[str, str]:
    """`GET /db/UNIT` -> `{"UNIT": {"1": {"FORCE": "KN", "DIST": "M", ...}}}` (§1); the fallback
    truth when a table response does not echo its own units (rule 4)."""
    body = client.get("/db/UNIT")
    unit = body.get("UNIT") if isinstance(body, dict) else None
    if not isinstance(unit, dict) or not unit:
        raise MidasError("bad_response", "Risposta inattesa da MIDAS per le unità del modello.")
    first = next(iter(unit.values()))
    force, dist = str(first.get("FORCE", "")), str(first.get("DIST", ""))
    if not force or not dist:
        raise MidasError("bad_response", "Unità del modello mancanti nella risposta di MIDAS.")
    return force, dist


def autodetect_base_url(
    client_factory: Callable[[str], MidasClient], product: Product
) -> tuple[str, MidasClient, VersionInfo]:
    """Try each regional relay in turn and return the first that answers `/config/ver` (§1)."""
    path = _PRODUCT_PATH[product]
    last_error: MidasError | None = None
    for suffix in REGIONAL_SUFFIXES:
        base_url = f"https://moa-engineers{suffix}.midasit.com:443{path}"
        client = client_factory(base_url)
        try:
            info = probe(client)
        except MidasError as error:
            last_error = error
            continue
        return base_url, client, info
    raise last_error or MidasError("not_connected", "Nessun relay MIDAS raggiungibile.")


def _product_from_name(name: str) -> str:
    return "civil" if "CIVIL" in name.upper() else "gen"
