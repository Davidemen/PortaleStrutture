"""Step: bar diameter/count selection for flexural reinforcement, factored out of `flessione.py`
to keep both modules within the size limits (docs/BUILD_CONTRACT.md, regola 12). Same formulas,
same `legacy_compat` branches; see `flessione.py` module docstring for the fix rationale."""
import math
from typing import NamedTuple

from strutture.shared.divergences import legacy
from strutture.shared.rebar_catalog import STANDARD_DIAMETERS_MM, bars_area

MARGIN_PHI_MIN_CM = 3.0  # sheet's `1.5*2` margin (cm) in the Phi_min formula.
FYK_REFERENCE_LEGACY_MPA = 500.0  # sheet's literal `500` in the Phi_min formula (should be the real fyk).


class ArmaturaProgetto(NamedTuple):
    """Selected bar diameters/counts and provided steel area, both directions."""

    phi_min_mm: float
    diam_x_mm: float
    diam_y_mm: float
    n_x_dispari: int
    n_y_dispari: int
    as_prov_x_mm2: float
    as_prov_y_mm2: float


def progetta_armatura(
    as_x_cm2: float, as_y_cm2: float, as_x_min_cm2: float, as_y_min_cm2: float, n_x: int, n_y: int,
    diametro_manuale_x_mm: float, diametro_manuale_y_mm: float, fctm_MPa: float, fyk_riferimento_MPa: float,
    h_mm: float, copriferro_cm: float, passo_armatura_cm: float, *, legacy_compat: bool,
) -> ArmaturaProgetto:
    """Governing diameter (crack-control minimum vs required) and odd bar count, both directions."""
    phi_min_mm = _phi_min_mm(fctm_MPa, fyk_riferimento_MPa, h_mm, copriferro_cm, passo_armatura_cm,
                              legacy_compat=legacy_compat)
    phi_x_mm = _phi_richiesto_mm(as_x_cm2, as_x_min_cm2, n_x, diametro_manuale_x_mm, legacy_compat=legacy_compat)
    phi_y_mm = _phi_richiesto_mm(as_y_cm2, as_y_min_cm2, n_y, diametro_manuale_y_mm, legacy_compat=legacy_compat)
    diam_x_mm = max(phi_min_mm, phi_x_mm)
    diam_y_mm = max(phi_min_mm, phi_y_mm)
    n_x_dispari = _prossimo_dispari(n_x)
    n_y_dispari = _prossimo_dispari(n_y)
    return ArmaturaProgetto(
        phi_min_mm=phi_min_mm, diam_x_mm=diam_x_mm, diam_y_mm=diam_y_mm,
        n_x_dispari=n_x_dispari, n_y_dispari=n_y_dispari,
        as_prov_x_mm2=bars_area(n_x_dispari, diam_x_mm), as_prov_y_mm2=bars_area(n_y_dispari, diam_y_mm),
    )


def _phi_richiesto_mm(as_cm2: float, as_min_cm2: float, n_bars: int, diametro_manuale_mm: float, *,
                       legacy_compat: bool) -> float:
    as_governante_mm2 = max(as_cm2, as_min_cm2) * 100.0
    diametro_calcolato_mm = math.sqrt(4.0 * as_governante_mm2 / n_bars / math.pi)
    diametro_mm = _arrotonda_diametro(diametro_calcolato_mm, legacy_compat=legacy_compat)
    return max(diametro_mm, diametro_manuale_mm)


def _phi_min_mm(fctm_MPa: float, fyk_riferimento_MPa: float, h_mm: float, copriferro_cm: float,
                passo_cm: float, *, legacy_compat: bool) -> float:
    """Minimum bar diameter for crack control at spacing `passo_cm` (NTC2018 §4.1.6.1.1 As,min ratio
    0.26*fctm/fyk, solved for the diameter of one bar spaced every `passo_cm`)."""
    d_cm = h_mm / 10.0 - copriferro_cm - MARGIN_PHI_MIN_CM
    striscia_cm = 100.0  # 1 m wide reference strip, matching the 0.26*fctm/fyk*b*d As,min formula.
    area_per_bar_cm2 = 0.26 * (fctm_MPa / fyk_riferimento_MPa) * striscia_cm * d_cm * (passo_cm / 100.0)
    diametro_calcolato_mm = 10.0 * math.sqrt(4.0 * area_per_bar_cm2 / math.pi)
    return _arrotonda_diametro(diametro_calcolato_mm, legacy_compat=legacy_compat)


def _arrotonda_diametro(diametro_mm: float, *, legacy_compat: bool) -> float:
    """Sheet: round up to the next even millimetre. Fix: round up to the next standard commercial
    diameter (`shared.rebar_catalog.STANDARD_DIAMETERS_MM`)."""
    if legacy("plinti-isolati/diametro-armatura-arrotondato-a-pari-non-commerciale", legacy_compat):
        return math.ceil(diametro_mm / 2.0) * 2.0
    candidati = [d for d in STANDARD_DIAMETERS_MM if d >= diametro_mm]
    if not candidati:
        raise ValueError(f"diametro richiesto {diametro_mm:.1f} mm oltre il massimo commerciale disponibile")
    return min(candidati)


def _prossimo_dispari(n: int) -> int:
    return n if n % 2 == 1 else n + 1


def meta_arrotondata_per_eccesso(n_dispari: int) -> int:
    return (n_dispari + 1) // 2
