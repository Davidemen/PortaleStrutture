"""Code marker linking a legacy branch to its register entry.

    if legacy("ca-pilastri/lambda-lim-unita", legacy_compat):
        ... spreadsheet behaviour ...
    else:
        ... code-standard behaviour ...

It returns the flag unchanged; its value is the greppable, testable link: a test collects every
string literal passed to `legacy(` and compares it with the register in both directions.

Two analysis contexts exist for the Excel comparison (`strutture.web.confronto`), both scoped by a
`ContextVar` — per thread / per task, restored on exit, inert for every normal run:
- `traccia()` records which ids a run consulted with the flag on (the corrections its inputs reach);
- `solo(ids)` makes exactly those ids take the spreadsheet path, whatever the flag says — one
  correction at a time, to see which outputs THAT correction changes for THESE inputs.
Neither changes what `legacy()` means for a calculation: outside them it is the identity on the flag."""
from collections.abc import Callable, Iterable, Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_SOLO: ContextVar[frozenset[str] | None] = ContextVar("strutture_legacy_solo", default=None)
_TRACCIA: ContextVar[set[str] | None] = ContextVar("strutture_legacy_traccia", default=None)


def legacy(divergence_id: str, legacy_compat: bool) -> bool:
    """True when the spreadsheet behaviour of `divergence_id` must be reproduced."""
    forzati = _SOLO.get()
    attivo = legacy_compat if forzati is None else divergence_id in forzati
    visti = _TRACCIA.get()
    if attivo and visti is not None:
        visti.add(divergence_id)
    return attivo


@contextmanager
def traccia() -> Iterator[Callable[[], frozenset[str]]]:
    """Collect the ids for which `legacy()` answered True inside the block; yields a getter."""
    visti: set[str] = set()
    token = _TRACCIA.set(visti)
    try:
        yield lambda: frozenset(visti)
    finally:
        _TRACCIA.reset(token)


@contextmanager
def solo(ids: Iterable[str]) -> Iterator[None]:
    """Inside the block only `ids` take the spreadsheet path, regardless of the flag passed."""
    token = _SOLO.set(frozenset(ids))
    try:
        yield
    finally:
        _SOLO.reset(token)
