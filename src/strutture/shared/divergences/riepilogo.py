"""Per-tool summary of the register (WORKBENCH_SPEC.md §25.2): reused by `GET /api/divergences/riepilogo`
(unchanged behaviour: per-`stato` counts including every entry) and by `shared/stato_progetto/provvisorio.py`
(which also needs the counts restricted to `ramo == "nessuno"` and the `da_verificare` doubts, separately)."""
from typing import Protocol

from .models import Divergence

STATI = ("da_confermare", "approvato", "respinto")


class _StatoLookup(Protocol):
    """Whatever `signoffs.get(id).stato` needs to be — avoids importing the storage layer from
    `shared`, which never depends on it."""

    def get(self, divergence_id: str) -> object: ...  # returns something with a `.stato` attribute


def riepilogo_per_strumento(
    divergences: tuple[Divergence, ...], signoffs: _StatoLookup
) -> dict[str, dict[str, int | dict[str, int]]]:
    """`{strumento: {da_confermare, approvato, respinto, ramo_nessuno: {...}, da_verificare,
    correzioni: {...}, correzioni_ramo_nessuno: {...}}}`.

    `da_confermare`/`approvato`/`respinto`/`ramo_nessuno` count EVERY entry regardless of `tipo`
    (GET /api/divergences/riepilogo's own per-stato tally, unchanged). `correzioni`/
    `correzioni_ramo_nessuno` are the same two tallies but with `tipo == "da_verificare"` entries
    excluded: a dubbio never counts as a correction pending/approved/rejected (WORKBENCH_SPEC §25.2
    -- `shared/stato_progetto/provvisorio.py` reads THESE, not the unfiltered ones, so a tool with
    only doubts pending a decision is never "provvisorio")."""
    per_strumento: dict[str, dict] = {}
    for divergence in divergences:
        stato = signoffs.get(divergence.id).stato
        for strumento in divergence.strumenti:
            voce = per_strumento.setdefault(strumento, _voce_vuota())
            voce[stato] += 1
            if divergence.ramo == "nessuno":
                voce["ramo_nessuno"][stato] += 1
            if divergence.tipo == "da_verificare":
                voce["da_verificare"] += 1
                continue
            voce["correzioni"][stato] += 1
            if divergence.ramo == "nessuno":
                voce["correzioni_ramo_nessuno"][stato] += 1
    return per_strumento


def _voce_vuota() -> dict:
    return {
        **dict.fromkeys(STATI, 0),
        "ramo_nessuno": dict.fromkeys(STATI, 0),
        "da_verificare": 0,
        "correzioni": dict.fromkeys(STATI, 0),
        "correzioni_ramo_nessuno": dict.fromkeys(STATI, 0),
    }
