"""Lookups shared by the `relazione.py` modules (docs/architecture-phase2.md §1/§6): finding the
raw `ReactionRow`/`RigaVerifica` behind a governing `(nodo, combo)` pair, and the row that governs
a per-`famiglia` envelope quantity across ALL famiglie (the same "global minimum" `tool.py::
_minimo` computes for `mu_scorrimento_minimo`/`mu_ribaltamento_minimo`). No calculation of its own:
every value returned here is already computed by the package's own step functions."""
from strutture.shared.load_table import ReactionRow

from .inviluppo import InviluppoRiga
from .riga_verifica import RigaVerifica


def trova_riga(righe: tuple[RigaVerifica, ...], nodo: int, combo: str) -> RigaVerifica:
    """The `RigaVerifica` of the given `(nodo, combo)` — always present, `reazioni` rows are
    unique on that pair (`validate_unique_nodo_combo`)."""
    return next(r for r in righe if r.nodo == nodo and r.combo == combo)


def trova_reazione(reazioni: tuple[ReactionRow, ...], nodo: int, combo: str) -> ReactionRow:
    """The raw `ReactionRow` of the given `(nodo, combo)` (the F/M values before self-weight and
    lever-arm transfer, not echoed by `RigaVerifica`)."""
    return next(r for r in reazioni if r.nodo == nodo and r.combo == combo)


def riga_governante_per(inviluppo: tuple[InviluppoRiga, ...], grandezza: str) -> InviluppoRiga | None:
    """The single `InviluppoRiga` achieving the GLOBAL minimum of `grandezza`, across every
    famiglia — the same row `strutture.foundations.plinti_isolati.tool._minimo` picks for the
    `mu_scorrimento_minimo`/`mu_ribaltamento_minimo` highlights. `None` when `grandezza` has no
    entry at all (no row of any famiglia had a defined value)."""
    candidati = [r for r in inviluppo if r.grandezza == grandezza]
    return min(candidati, key=lambda r: r.valore) if candidati else None
