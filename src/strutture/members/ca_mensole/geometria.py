"""Effective depth and equivalent shear span (`Mensola tozza!H11,H13`, spec §4 steps 6-8).

`H12` (z = h - 2c) is computed on the sheet but never referenced by any downstream formula
(spec §7) and is intentionally not reproduced here.
"""
from strutture.shared.report import CalcError

from .models import GeometriaResult

SHEAR_SPAN_OFFSET_COEFF = 0.2  # l = a + 0.2*d — clause "?" (spec §6, not independently verified)


def geometria(a_mm: float, h_mm: float, c_mm: float) -> GeometriaResult:
    """d = h - c (altezza utile); l = a + 0.2d (braccio di taglio equivalente)."""
    d_mm = h_mm - c_mm
    if d_mm <= 0:
        raise CalcError(f"copriferro c={c_mm} deve essere minore dell'altezza h={h_mm} (d = h - c deve essere > 0)")
    l_mm = a_mm + SHEAR_SPAN_OFFSET_COEFF * d_mm
    return GeometriaResult(d_mm=d_mm, l_mm=l_mm)
