"""Foundation bearing-pressure distribution + eccentricity check, EC7 Annex D / NTC2018 §6.4.2.1
(muro-sostegno rows 66-72 static, 92-95 seismic). Pure functions; `tool.py` assembles the
`PressioniCombo` result."""
from typing import NamedTuple


def eccentricita_termine(peso_kN: float, x_m: float, b_fond_m: float) -> tuple[float, float]:
    """(e, M) of one vertical-load term about the footing centre (cols D/E, G/H, J/K)."""
    e_m = b_fond_m / 2 - x_m
    return e_m, peso_kN * e_m


def eccentricita_risultante(
    *, m_rib_kNm: float, m_muro_ecc_kNm: float, m_terr_ecc_kNm: float, m_sv_ecc_kNm: float, n_tot_kN: float
) -> tuple[float, float]:
    """(Mtot, e) — Mtot (col M) = MRIB(Tool2, moment of the thrust about the toe) + the three
    eccentricity moments of the vertical loads about the footing centre; e (col O) = Mtot/Ntot."""
    m_tot_kNm = m_rib_kNm + m_muro_ecc_kNm + m_terr_ecc_kNm + m_sv_ecc_kNm
    return m_tot_kNm, m_tot_kNm / n_tot_kN


def larghezza_efficace(*, eccentricita_m: float, b_fond_m: float) -> float:
    """B* (col Q) = 0 se |e| ≤ B/6 (sezione interamente compressa), altrimenti 3·(B/2 − |e|)."""
    if abs(eccentricita_m) <= b_fond_m / 6:
        return 0.0
    return 3 * (b_fond_m / 2 - abs(eccentricita_m))


class PressioniValleMonte(NamedTuple):
    p_valle_kPa: float
    p_monte_kPa: float


def pressioni_valle_monte(*, n_tot_kN: float, m_tot_kNm: float, b_fond_m: float, b_star_m: float) -> PressioniValleMonte:
    """pvalle/pmonte (cols R/S): trapezio se B*=0, triangolo (uplift parziale) altrimenti."""
    if b_star_m == 0:
        return PressioniValleMonte(
            p_valle_kPa=n_tot_kN / b_fond_m + 6 * m_tot_kNm / b_fond_m**2,
            p_monte_kPa=n_tot_kN / b_fond_m - 6 * m_tot_kNm / b_fond_m**2,
        )
    if m_tot_kNm < 0:
        return PressioniValleMonte(p_valle_kPa=0.0, p_monte_kPa=2 * n_tot_kN / b_star_m)
    return PressioniValleMonte(p_valle_kPa=2 * n_tot_kN / b_star_m, p_monte_kPa=0.0)
