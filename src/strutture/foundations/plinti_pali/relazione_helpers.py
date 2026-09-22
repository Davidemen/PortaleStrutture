"""Lookups shared by the `relazione_*.py` modules (docs/architecture-phase2.md §1/§6): finding the
`RigaCarico` behind a governing `(nodo, combo)` pair (mirrors `plinti_isolati.relazione_helpers.
trova_riga`) and the pile that achieves a row's own `n_max_pila_kN`/`n_min_pila_kN`. No calculation
of its own: every value returned here is already computed by the package's own step functions."""
from .inviluppo import InviluppoRiga
from .rows import RigaCarico


def trova_riga(righe: tuple[RigaCarico, ...], nodo: int, combo: str) -> RigaCarico:
    """The `RigaCarico` of the given `(nodo, combo)` — always present, `reazioni` rows are unique
    on that pair (`validate_unique_nodo_combo`)."""
    return next(r for r in righe if r.nodo == nodo and r.combo == combo)


def riga_di(righe: tuple[RigaCarico, ...], riga: InviluppoRiga) -> RigaCarico:
    """The full `RigaCarico` behind one `InviluppoRiga` envelope cell."""
    return trova_riga(righe, riga.nodo, riga.combo)


def indice_palo_governante(n_pali_kN: tuple[float, ...], *, minimo: bool = False) -> int:
    """0-based index of the pile achieving `min`/`max` of `n_pali_kN` (same order as `piles`)."""
    chiave = (lambda i: n_pali_kN[i]) if not minimo else (lambda i: -n_pali_kN[i])
    return max(range(len(n_pali_kN)), key=chiave)


def mu_beam(n_own: int, n_perp: int, spacing_m: float, n_eff_kN: float, m_assoc_kNm: float) -> float:
    """Mirrors `flessione._mu_beam` exactly, restated inline rather than importing the package's
    private helper (same convention `plinti_isolati.relazione_azioni` documents for its own
    inlined closed-form restatements) — shared by `relazione_flessione.py` (bottom reinforcement)
    and `relazione_armatura_superiore.py` (top reinforcement), both built on this same beam term."""
    if n_own == 1:
        return abs(m_assoc_kNm)
    fattore = 0.5 if n_perp >= 2 else 1.0
    return fattore * n_eff_kN * spacing_m / 4.0 + abs(m_assoc_kNm)
