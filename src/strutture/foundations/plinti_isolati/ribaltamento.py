"""Step: overturning safety factor, per direction (docs/specs/fond-plinti-isolati.md Tool-1 step 11,
`CHECKS!AC:AH`).

Fix (docs/architecture-batch2.md §7 `plinti-isolati AE/AH`): the sheet's `IF(Mrib=0,">100",...)`
conflates "no overturning demand" with "very safe" under one text value. Here Mrib=0 reports
`None` (`senza_domanda`); `legacy_compat=True` keeps the sheet's stand-in."""
from dataclasses import dataclass

from strutture.shared.divergences import legacy

LEGACY_NO_DEMAND_RATIO = 100.0  # sheet's ">100" text, used both for Mrib=0 and ratio>100.


@dataclass(frozen=True)
class Ribaltamento:
    mu_x: float | None
    mu_y: float | None


def mu_ribaltamento(n_kN: float, ax_m: float, by_m: float, myy_kNm: float, mxx_kNm: float, *,
                     legacy_compat: bool) -> Ribaltamento:
    """Overturning ratio Mstab/Mrib for each direction: X uses Myy (bends about Y), Y uses Mxx."""
    return Ribaltamento(
        mu_x=_ratio(n_kN * ax_m / 2.0, myy_kNm, legacy_compat=legacy_compat),
        mu_y=_ratio(n_kN * by_m / 2.0, mxx_kNm, legacy_compat=legacy_compat),
    )


def _ratio(m_stab_kNm: float, m_rib_kNm: float, *, legacy_compat: bool) -> float | None:
    if m_rib_kNm == 0:
        return (LEGACY_NO_DEMAND_RATIO
                if legacy("plinti-isolati/ribaltamento-mrib-zero-valore-fittizio", legacy_compat)
                else None)
    ratio = m_stab_kNm / m_rib_kNm
    if (legacy("plinti-isolati/ribaltamento-mrib-zero-valore-fittizio", legacy_compat)
            and ratio > LEGACY_NO_DEMAND_RATIO):
        return LEGACY_NO_DEMAND_RATIO
    return ratio
