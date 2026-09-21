"""Base contact pressure of a rigid rectangular footing (B x L) under N, Mx, My.

Public API:
- `eccentricities(n_kn, mx_knm, my_knm) -> (ex_m, ey_m)`, `in_kern_uniaxial`, `in_kern_biaxial`.
- `uniaxial(n_kn, m_knm, b_m, l_m) -> UniaxialPressure` — closed-form Navier / no-tension triangle.
- `biaxial(n_kn, mx_knm, my_knm, bx_m, by_m) -> BiaxialPressure` — exact method (Navier inside the
  kern, numeric no-tension plane solver outside it).
- `sovrapposizione(n_kn, mx_knm, my_knm, bx_m, by_m) -> BiaxialPressure` — the source spreadsheet's
  uniaxial-superposition approximation.
- `pressure(n_kn, mx_knm, my_knm, bx_m, by_m, metodo="esatto"|"sovrapposizione") -> BiaxialPressure`
  — single entry point dispatching to the two above (docs/architecture-batch2.md §9-D2).

Raises `strutture.shared.report.CalcError` whenever the resultant falls outside the footing
footprint (no no-tension equilibrium is possible).
"""
from .biaxial import biaxial
from .eccentricity import eccentricities, in_kern_biaxial, in_kern_uniaxial
from .models import BiaxialPressure, Metodo, NeutralAxis, UniaxialPressure
from .pressure import pressure
from .sovrapposizione import sovrapposizione
from .uniaxial import uniaxial

__all__ = [
    "BiaxialPressure",
    "Metodo",
    "NeutralAxis",
    "UniaxialPressure",
    "biaxial",
    "eccentricities",
    "in_kern_biaxial",
    "in_kern_uniaxial",
    "pressure",
    "sovrapposizione",
    "uniaxial",
]
