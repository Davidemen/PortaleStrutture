"""Lazy, cached loader and public lookup API for the merged Comuni database."""
import csv
import functools
from pathlib import Path

from .constants import DATA_CSV_PATH, DEFAULT_SEARCH_LIMIT
from .index import by_normalized_name, filter_prefix, resolve, sorted_by_normalized_name
from .label import ComuneOption, comune_label, split_label
from .models import Comune
from .normalize import normalize_name


def parse_csv(path: Path) -> tuple[Comune, ...]:
    """Parse an already-merged `comuni.csv` into validated, frozen Comune models. Not cached: used
    both by the (cached) public loader and directly by tests against small fixture files.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return tuple(
            Comune(
                regione=row["regione"],
                provincia=row["provincia"],
                istat=row["istat"],
                comune=row["comune"],
                zona_sismica=int(row["zona_sismica"]),
                zona_vento=int(row["zona_vento"]),
                zona_neve=row["zona_neve"],
            )
            for row in reader
        )


@functools.lru_cache(maxsize=1)
def load_comuni(path: Path = DATA_CSV_PATH) -> tuple[Comune, ...]:
    """Load and cache the full Comuni database (built by `strutture.shared.comuni.build`)."""
    if not path.exists():
        raise FileNotFoundError(f"{path} not found; run `uv run python -m strutture.shared.comuni.build` first")
    return parse_csv(path)


@functools.lru_cache(maxsize=1)
def _name_index() -> dict[str, tuple[Comune, ...]]:
    return by_normalized_name(load_comuni())


@functools.lru_cache(maxsize=1)
def _sorted_index() -> tuple[tuple[str, Comune], ...]:
    return sorted_by_normalized_name(load_comuni())


def lookup_comune(name: str, provincia: str | None = None) -> Comune:
    """Case/accent-insensitive lookup by comune name. Raises AmbiguousComuneError for a homonym
    across provinces unless `provincia` disambiguates it; raises KeyNotFound if nothing matches.
    """
    if not name or not name.strip():
        raise ValueError("name must not be blank")
    plain_name, label_provincia = split_label(name)  # accepts the dropdown label "Nome (Provincia)"
    matches = _name_index().get(normalize_name(plain_name), ())
    return resolve(plain_name, matches, provincia or label_provincia)


def search_comuni(prefix: str, limit: int = DEFAULT_SEARCH_LIMIT) -> tuple[Comune, ...]:
    """Prefix search over comune names (case/accent-insensitive), for autocomplete-style UIs."""
    if not prefix or not prefix.strip():
        raise ValueError("prefix must not be blank")
    if limit <= 0:
        raise ValueError("limit must be a positive integer")
    return filter_prefix(_sorted_index(), prefix, limit)


def search_options(prefix: str, limit: int = DEFAULT_SEARCH_LIMIT) -> tuple[ComuneOption, ...]:
    """Prefix search returning dropdown options whose label is unique (homonyms carry the provincia)."""
    index = _name_index()
    return tuple(
        ComuneOption(
            label=comune_label(c.comune, c.provincia, is_homonym=len(index[normalize_name(c.comune)]) > 1),
            comune=c,
        )
        for c in search_comuni(prefix, limit)
    )
