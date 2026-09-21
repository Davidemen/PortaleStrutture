"""Step: cantilever bending moment at the critical section, from a family's governing bearing
pressure (docs/specs/fond-plinti-isolati.md Tool-2 steps 3/8, `INPUT!W3:X4`, `T13:T14`, `AB20:AB21`
— one formula reused for every pressure level QP/CHA/FREQ/SLU).

Fix: the sheet always measures the cantilever from the footing CENTRE (never subtracting the
pedestal half-width), overestimating M when a pedestal is present; the code-standard path measures
it from the column/pedestal FACE per the task's "bending at the column face". Zero numeric impact
on the golden case (no pedestal, aX=aY=0). `legacy_compat=True` also reproduces the sheet's own
kgf*cm -> kN*m conversion shortcut (exact: 1 kgf*cm = 9.80665e-5 kN*m); see
docs/divergences/plinti-isolati.md."""
from .legacy_units import kpa_to_kgcm2

LEGACY_KGF_CM_TO_KNM_DIVISOR = 1.0e4  # sheet's `/10^4` (exact would be ~9806.65).
CM_PER_M = 100.0


def momento_cantilever_kNm(sigma_kpa: float, larghezza_m: float, luce_totale_m: float,
                            semi_pedestal_m: float, eccentricita_extra_m: float, *, legacy_compat: bool) -> float:
    """M = sigma * larghezza * cantilever_len^2 / 2, for a strip of width `larghezza_m` spanning
    `luce_totale_m` (the plinth side perpendicular to the strip) plus `eccentricita_extra_m`.
    `semi_pedestal_m` (half the column/pedestal width along the span) is subtracted from the
    cantilever length, unless `legacy_compat` (sheet ignores the pedestal)."""
    if legacy_compat:
        cantilever_m = luce_totale_m / 2.0 + eccentricita_extra_m
        sigma_kgcm2 = kpa_to_kgcm2(sigma_kpa, legacy_compat=True)
        return (sigma_kgcm2 * (larghezza_m * CM_PER_M) * 0.5 * (cantilever_m * CM_PER_M) ** 2
                / LEGACY_KGF_CM_TO_KNM_DIVISOR)
    cantilever_m = max(luce_totale_m / 2.0 - semi_pedestal_m, 0.0) + eccentricita_extra_m
    return sigma_kpa * larghezza_m * cantilever_m**2 / 2.0
