"""Unique display labels for comuni: homonyms across provinces become 'Nome (Provincia)'."""
import re
from dataclasses import dataclass

from .models import Comune

_LABEL_PATTERN = re.compile(r"^(?P<name>.+?)\s*\((?P<provincia>[^()]+)\)$")


@dataclass(frozen=True)
class ComuneOption:
    """One dropdown entry: `label` round-trips through `lookup_comune`."""

    label: str
    comune: Comune


def comune_label(name: str, provincia: str, *, is_homonym: bool) -> str:
    return f"{name} ({provincia})" if is_homonym else name


def split_label(text: str) -> tuple[str, str | None]:
    """'Castro (Lecce)' -> ('Castro', 'Lecce'); a plain name -> (name, None)."""
    stripped = text.strip()
    match = _LABEL_PATTERN.match(stripped)
    if not match or not match.group("provincia").strip():
        return stripped, None
    return match.group("name").strip(), match.group("provincia").strip()
