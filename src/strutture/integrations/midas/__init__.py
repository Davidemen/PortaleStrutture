"""MIDAS NX (Gen NX / Civil NX) integration: pure package, no FastAPI imports
(docs/integrations/MIDAS.md §3). `strutture.web.routes.midas` is the only caller outside this
package's own tests."""
from .client import MidasClient
from .combinations import Combination, read_combinations
from .errors import ErrorKind, MidasError, redact
from .famiglia import suggest_famiglia
from .reactions import CHUNK_SIZE, MAX_CHUNKS, read_reactions
from .settings import MidasSettings, Product, has_server_key, resolve_key, validate_base_url
from .supports import SupportNode, read_supports
from .units import moment_factor, to_kn, to_m
from .version import VersionInfo, autodetect_base_url, probe, read_units

__all__ = [
    "CHUNK_SIZE",
    "MAX_CHUNKS",
    "Combination",
    "ErrorKind",
    "MidasClient",
    "MidasError",
    "MidasSettings",
    "Product",
    "SupportNode",
    "VersionInfo",
    "autodetect_base_url",
    "has_server_key",
    "moment_factor",
    "probe",
    "read_combinations",
    "read_reactions",
    "read_supports",
    "read_units",
    "redact",
    "resolve_key",
    "suggest_famiglia",
    "to_kn",
    "to_m",
    "validate_base_url",
]
