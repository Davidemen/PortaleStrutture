"""Pure query logic over pre-built Comuni indices (no I/O, no caching — the loader owns caching)."""
from ..tables import KeyNotFound
from .errors import AmbiguousComuneError
from .models import Comune
from .normalize import normalize_name


def by_normalized_name(comuni: tuple[Comune, ...]) -> dict[str, tuple[Comune, ...]]:
    """Group comuni by case/accent-folded name; homonyms across province end up in the same bucket."""
    index: dict[str, tuple[Comune, ...]] = {}
    for comune in comuni:
        key = normalize_name(comune.comune)
        index[key] = (*index.get(key, ()), comune)
    return index


def sorted_by_normalized_name(comuni: tuple[Comune, ...]) -> tuple[tuple[str, Comune], ...]:
    """(normalized name, Comune) pairs sorted for prefix search."""
    return tuple(sorted(((normalize_name(c.comune), c) for c in comuni), key=lambda pair: pair[0]))


def resolve(name: str, matches: tuple[Comune, ...], provincia: str | None) -> Comune:
    """Pick the single Comune a name resolves to, disambiguating homonyms by provincia."""
    if not matches:
        raise KeyNotFound(f"comune non trovato: {name!r}")
    if len(matches) == 1:
        return matches[0]
    if provincia is None:
        province = sorted({c.provincia for c in matches})
        raise AmbiguousComuneError(f"comune {name!r} è ambiguo tra le province {province}; specificare provincia")
    provincia_key = normalize_name(provincia)
    for candidate in matches:
        if normalize_name(candidate.provincia) == provincia_key:
            return candidate
    raise KeyNotFound(f"comune {name!r} non trovato in provincia {provincia!r}")


def filter_prefix(sorted_pairs: tuple[tuple[str, Comune], ...], prefix: str, limit: int) -> tuple[Comune, ...]:
    """First `limit` comuni (in sorted-name order) whose normalized name starts with `prefix`."""
    key = normalize_name(prefix)
    matches = [comune for norm_name, comune in sorted_pairs if norm_name.startswith(key)]
    return tuple(matches[:limit])
