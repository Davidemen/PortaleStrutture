"""Errors raised by the Comuni lookup API. `KeyNotFound` is reused from `shared.tables` for
consistency with every other VLOOKUP-style lookup in the codebase.
"""
from ..tables import KeyNotFound

__all__ = ["AmbiguousComuneError", "KeyNotFound"]


class AmbiguousComuneError(LookupError):
    """Multiple comuni share a name across different province; caller must pass `provincia`."""
