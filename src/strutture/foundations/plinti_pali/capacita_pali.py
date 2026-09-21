"""Step: pile axial capacity check against the user-given pile resistance (task addition, no sheet
cell — the source workbook computes the tension-pile strut/tie block unconditionally but never
reports it, docs/architecture-batch2.md §7 `plinti-pali BP:BX`; fix: gate on `Nmin<0` and report it,
here as a compression + an optional tension capacity check)."""
from .models_taglio import CapacitaPalo


def capacita_compressione(n_max_env_kN: float, resistenza_kN: float) -> CapacitaPalo:
    return CapacitaPalo(domanda_kN=n_max_env_kN, resistenza_kN=resistenza_kN,
                         utilizzo=n_max_env_kN / resistenza_kN, verificato=n_max_env_kN <= resistenza_kN)


def capacita_trazione(n_min_env_kN: float, resistenza_kN: float) -> CapacitaPalo:
    """Only meaningful (and only called by `tool.py`) when `n_min_env_kN < 0` (pile in tension)."""
    domanda_kN = abs(n_min_env_kN)
    return CapacitaPalo(domanda_kN=domanda_kN, resistenza_kN=resistenza_kN,
                         utilizzo=domanda_kN / resistenza_kN, verificato=domanda_kN <= resistenza_kN)
