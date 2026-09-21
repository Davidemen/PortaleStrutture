"""MidasError: the single exception type raised by the integration, carrying an Italian
user-facing message and an HTTP-status-mapped `kind` (docs/integrations/MIDAS.md §2 rules 1/3,
§3 client.py, §4)."""
from typing import Literal

ErrorKind = Literal["auth", "not_connected", "timeout", "bad_response", "forbidden_url"]

_STATUS_BY_KIND: dict[ErrorKind, int] = {
    "forbidden_url": 400,
    "auth": 401,
    "bad_response": 502,
    "not_connected": 502,
    "timeout": 504,
}


class MidasError(Exception):
    """`message_it` is safe to show the user or log: it must never contain the MAPI key."""

    def __init__(self, kind: ErrorKind, message_it: str) -> None:
        super().__init__(message_it)
        self.kind = kind
        self.message_it = message_it

    @property
    def status_code(self) -> int:
        return _STATUS_BY_KIND[self.kind]


def redact(text: str, key: str | None) -> str:
    """Replace every occurrence of `key` in `text` with a placeholder. Defence in depth: the key
    should never reach a message in the first place, but MIDAS' own error text could echo it back."""
    if not key:
        return text
    return text.replace(key, "***")
