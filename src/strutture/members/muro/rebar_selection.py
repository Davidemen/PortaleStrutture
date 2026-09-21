"""As.nec (simplified flexure, jd=0.9d) and bar-callout selection shared by the three
reinforcement-design tools (armatura-paramento/fondazione-valle/fondazione-monte), muro-sostegno
rows 133-187. Pure functions; `tool.py` assembles the per-tool result models.

`legacy_compat=True` reproduces the sheet's own bar-diameter formula exactly (rows 151/169/187):
a *continuous* diameter rounded to a 0.2 mm step, not clamped to a commercially available
diameter. `legacy_compat=False` instead picks the smallest standard diameter (EN10080 series,
`shared.rebar_catalog.STANDARD_DIAMETERS_MM`) whose area covers As.nec over one bar spacing — see
docs/divergences/muro-sostegno.md (diverges numerically for Tool 5's golden case: 4 mm is not a
commercial diameter, the standard series starts at 6 mm).
"""
import math

from strutture.shared.rebar_catalog import STANDARD_DIAMETERS_MM, bar_area, bar_callout

LEVA_INTERNA_APPROSSIMATA = 0.9  # NTC 4.1.2 simplified flexure — jd/d assumed lever-arm ratio
KNM_TO_MM_UNITS = 1e4  # As.nec[cm2/m] = MEd[kNm]*1e4 / (0.9*d[m]*1000*fyd[MPa])
MM_PER_M = 1000.0
CEILING_STEP_MM = 0.2  # sheet's CEILING(...,0.2) drafting rounding step
MM2_PER_CM2 = 100.0
CM_PER_M = 100.0


def as_necessaria_cm2_m(*, m_ed_kNm: float, d_m: float, fyd_MPa: float) -> float:
    """As.nec [cm2/m], simplified flexure with assumed jd = 0.9·d (NTC2018 §4.1.2).

    Not floored at 0: a per-combination row can legitimately go negative (a favourable MEd), same
    as the sheet's own H143:H150/K161:K168/M179:M186 cells — see `governante_cm2_m` for the floor
    applied to the reported design value."""
    return m_ed_kNm * KNM_TO_MM_UNITS / (LEVA_INTERNA_APPROSSIMATA * d_m * MM_PER_M * fyd_MPa)


def governante_cm2_m(as_nec_valori_cm2_m: tuple[float, ...]) -> float:
    """Governing (max) As.nec across combinations, floored at 0: a negative governing value would
    mean every combination is favourable, i.e. no tension reinforcement is required by this check
    at all — reported as 0 rather than a negative "requirement" (both modes; the per-combination
    values above stay unclamped for oracle fidelity to the sheet)."""
    return max(0.0, max(as_nec_valori_cm2_m))


def diametro_sheet_mm(as_nec_cm2_m: float, passo_m: float) -> float:
    """Ø [mm], sheet formula: 10*CEILING(2*SQRT(As.nec·passo/pi), 0.2)."""
    grezzo = 2 * math.sqrt(as_nec_cm2_m * passo_m / math.pi)
    return 10 * math.ceil(grezzo / CEILING_STEP_MM) * CEILING_STEP_MM


def callout_sheet(as_nec_cm2_m: float, passo_m: float) -> str:
    """Sheet-exact callout string, e.g. "1φ8/20" (legacy_compat=True)."""
    diametro_mm = diametro_sheet_mm(as_nec_cm2_m, passo_m)
    return f"1φ{diametro_mm:g}/{passo_m * CM_PER_M:g}"


def diametro_standard_mm(as_nec_cm2_m: float, passo_m: float) -> float:
    """Smallest commercial diameter (EN10080 series) whose area covers As.nec over one spacing."""
    area_richiesta_mm2 = as_nec_cm2_m * MM2_PER_CM2 * passo_m
    candidati = tuple(d for d in STANDARD_DIAMETERS_MM if bar_area(d) >= area_richiesta_mm2)
    return min(candidati) if candidati else max(STANDARD_DIAMETERS_MM)


def callout_standard(as_nec_cm2_m: float, passo_m: float) -> str:
    """Code-standard callout via `shared.rebar_catalog.bar_callout`, e.g. "1ø6/20"."""
    diametro_mm = diametro_standard_mm(as_nec_cm2_m, passo_m)
    return f"{bar_callout(1, diametro_mm)}/{passo_m * CM_PER_M:g}"


def diametro_mm(as_nec_cm2_m: float, passo_m: float, *, legacy_compat: bool) -> float:
    return diametro_sheet_mm(as_nec_cm2_m, passo_m) if legacy_compat else diametro_standard_mm(as_nec_cm2_m, passo_m)


def callout(as_nec_cm2_m: float, passo_m: float, *, legacy_compat: bool) -> str:
    return callout_sheet(as_nec_cm2_m, passo_m) if legacy_compat else callout_standard(as_nec_cm2_m, passo_m)
