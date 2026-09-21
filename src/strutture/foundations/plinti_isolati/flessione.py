"""Step: flexural reinforcement design from the governing envelope (docs/specs/fond-plinti-isolati.md
Tool-2 steps 8-13, `INPUT!T13:T31`).

Fix D4 (docs/architecture-batch2.md §9): MEd is enveloped from the ULS-type families only
(`SLU_STR`, `SLU_EQU`, `SLV_STR`, `SLV_EQU`); the sheet's own set swaps `SLV_STR` for the
serviceability `SLE_QP` family, `legacy_compat=True` reproduces that. Two more sheet magic numbers
are fixed here (see docs/divergences/plinti-isolati.md): `Φmin` divides by a literal 500 N/mm²
reference yield strength instead of the actual `fyk`, and diameters round to the next even
millimetre instead of the next standard commercial diameter.

Fix `eX`/`eY` swap (HIGH, review finding): `docs/specs/fond-plinti-isolati.md` step 8 transcribes
the sheet's own formula `Mx,SLU = ...*(AX/20+eY/10)^2` (`My,SLU` mirrors with `eX`) — i.e. the sheet
lengthens the X cantilever (which spans `ax_m`, the X plinth dimension) with `eY`, not `eX`. But
`azioni_base.py`/`input.py` define `ex_m` as the eccentricity feeding `MYY` (X-direction load
asymmetry); pairing it with the Y cantilever instead is a bug, invisible on the golden case
(`ex_m=ey_m=0`). `_eccentricita_cantilever` keeps the sheet's swap under `legacy_compat=True` and
pairs `ex_m` with the X cantilever (and `ey_m` with the Y one) otherwise."""
import math

from strutture.shared.load_table import Famiglia
from strutture.shared.rebar_catalog import STANDARD_DIAMETERS_MM, bar_callout, bars_area

from .inviluppo import InviluppoRiga
from .models_flessione import Flessione
from .momento_cantilever import momento_cantilever_kNm

MARGIN_EFFECTIVE_DEPTH_MM = 30.0  # sheet's `1.5*20`: assumed half-diameter margin for the As calc.
MARGIN_PHI_MIN_CM = 3.0  # sheet's `1.5*2` margin (cm) in the Phi_min formula.
FYK_REFERENCE_LEGACY_MPA = 500.0  # sheet's literal `500` in the Phi_min formula (should be the real fyk).
MINIMUM_REINFORCEMENT_RATIO = 0.001  # NTC2018 minimo armature a piastra/soletta bidirezionale, entrambe le facce.
TWO_FACES = 2.0

ULS_FAMILIES_FIXED: tuple[Famiglia, ...] = ("SLU_STR", "SLU_EQU", "SLV_STR", "SLV_EQU")
ULS_FAMILIES_LEGACY: tuple[Famiglia, ...] = ("SLU_STR", "SLE_QP", "SLU_EQU", "SLV_EQU")


def mead_families(*, legacy_compat: bool) -> tuple[Famiglia, ...]:
    """Families entering the MEd envelope (fix D4: ULS-type only; sheet also includes `SLE_QP`)."""
    return ULS_FAMILIES_LEGACY if legacy_compat else ULS_FAMILIES_FIXED


def max_pressione_kpa(inviluppo: tuple[InviluppoRiga, ...], famiglie: tuple[Famiglia, ...]) -> float:
    """MAX of the family envelope `pressione_max_kpa` over the given families (0 if none present)."""
    valori = [r.valore for r in inviluppo if r.grandezza == "pressione_max_kpa" and r.famiglia in famiglie]
    return max(valori, default=0.0)


def _eccentricita_cantilever(ex_m: float, ey_m: float, *, legacy_compat: bool) -> tuple[float, float]:
    """Which user eccentricity lengthens which cantilever: `(extra_x_m, extra_y_m)`. `legacy_compat=True`
    reproduces the sheet's own swap (X cantilever gets eY, Y cantilever gets eX, see module docstring);
    `legacy_compat=False` pairs each eccentricity with its own axis (eX -> X cantilever)."""
    if legacy_compat:
        return ey_m, ex_m
    return ex_m, ey_m


def flessione(
    inviluppo: tuple[InviluppoRiga, ...], ax_m: float, by_m: float, h_plinto_m: float,
    a_pedestal_m: float, b_pedestal_m: float, ex_m: float, ey_m: float,
    copriferro_cm: float, passo_armatura_cm: float, diametro_manuale_x_mm: float, diametro_manuale_y_mm: float,
    fyd_MPa: float, fyk_MPa: float, fctm_MPa: float, *, legacy_compat: bool,
) -> Flessione:
    """Bending moment at the column face + required/provided flexural reinforcement, both directions."""
    famiglie = mead_families(legacy_compat=legacy_compat)
    sigma_slu_kpa = max_pressione_kpa(inviluppo, famiglie)

    h_mm = h_plinto_m * 1000.0
    d_mm = h_mm - copriferro_cm * 10.0 - MARGIN_EFFECTIVE_DEPTH_MM

    extra_x_m, extra_y_m = _eccentricita_cantilever(ex_m, ey_m, legacy_compat=legacy_compat)
    mx_slu_kNm = momento_cantilever_kNm(sigma_slu_kpa, by_m, ax_m, a_pedestal_m / 2.0, extra_x_m, legacy_compat=legacy_compat)
    my_slu_kNm = momento_cantilever_kNm(sigma_slu_kpa, ax_m, by_m, b_pedestal_m / 2.0, extra_y_m, legacy_compat=legacy_compat)

    as_x_cm2 = _as_required_cm2(mx_slu_kNm, d_mm, fyd_MPa)
    as_y_cm2 = _as_required_cm2(my_slu_kNm, d_mm, fyd_MPa)
    as_x_min_cm2 = _as_min_cm2(by_m * 1000.0, h_mm)
    as_y_min_cm2 = _as_min_cm2(ax_m * 1000.0, h_mm)

    n_x = _bar_count(by_m * 100.0, copriferro_cm, passo_armatura_cm)
    n_y = _bar_count(ax_m * 100.0, copriferro_cm, passo_armatura_cm)

    fyk_riferimento = FYK_REFERENCE_LEGACY_MPA if legacy_compat else fyk_MPa
    phi_min_mm = _phi_min_mm(fctm_MPa, fyk_riferimento, h_mm, copriferro_cm, passo_armatura_cm, legacy_compat=legacy_compat)

    phi_x_mm = _phi_richiesto_mm(as_x_cm2, as_x_min_cm2, n_x, diametro_manuale_x_mm, legacy_compat=legacy_compat)
    phi_y_mm = _phi_richiesto_mm(as_y_cm2, as_y_min_cm2, n_y, diametro_manuale_y_mm, legacy_compat=legacy_compat)

    diam_x_mm = max(phi_min_mm, phi_x_mm)
    diam_y_mm = max(phi_min_mm, phi_y_mm)
    n_x_dispari = _prossimo_dispari(n_x)
    n_y_dispari = _prossimo_dispari(n_y)
    as_prov_x_mm2 = bars_area(n_x_dispari, diam_x_mm)
    as_prov_y_mm2 = bars_area(n_y_dispari, diam_y_mm)

    return Flessione(
        mx_slu_kNm=mx_slu_kNm, my_slu_kNm=my_slu_kNm,
        as_x_cm2=as_x_cm2, as_y_cm2=as_y_cm2, as_x_min_cm2=as_x_min_cm2, as_y_min_cm2=as_y_min_cm2,
        n_x=n_x_dispari, n_y=n_y_dispari, phi_x_mm=diam_x_mm, phi_y_mm=diam_y_mm, phi_min_mm=phi_min_mm,
        as_prov_x_mm2=as_prov_x_mm2, as_prov_y_mm2=as_prov_y_mm2,
        callout_sup_x=bar_callout(_meta_arrotondata_per_eccesso(n_x_dispari), diam_x_mm),
        callout_inf_x=bar_callout(n_x_dispari, diam_x_mm),
        callout_sup_y=bar_callout(_meta_arrotondata_per_eccesso(n_y_dispari), diam_y_mm),
        callout_inf_y=bar_callout(n_y_dispari, diam_y_mm),
    )


def _as_required_cm2(m_slu_kNm: float, d_mm: float, fyd_MPa: float) -> float:
    """As = M / (0.9*d*fyd), M in N*mm (1 kN*m = 1e6 N*mm), result in cm2."""
    if d_mm <= 0:
        raise ValueError(f"copriferro troppo grande: altezza utile d={d_mm} mm non positiva")
    as_mm2 = (m_slu_kNm * 1.0e6) / (0.9 * d_mm * fyd_MPa)
    return as_mm2 / 100.0


def _as_min_cm2(larghezza_mm: float, h_mm: float) -> float:
    """As,min = 2 * 0.1% * larghezza * H (both faces), result in cm2 (mm2 -> cm2: /100)."""
    return TWO_FACES * MINIMUM_REINFORCEMENT_RATIO * larghezza_mm * h_mm / 100.0


def _bar_count(luce_cm: float, copriferro_cm: float, passo_cm: float) -> int:
    return math.ceil((luce_cm - 2.0 * copriferro_cm) / passo_cm + 1.0)


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
    if legacy_compat:
        return math.ceil(diametro_mm / 2.0) * 2.0
    candidati = [d for d in STANDARD_DIAMETERS_MM if d >= diametro_mm]
    if not candidati:
        raise ValueError(f"diametro richiesto {diametro_mm:.1f} mm oltre il massimo commerciale disponibile")
    return min(candidati)


def _prossimo_dispari(n: int) -> int:
    return n if n % 2 == 1 else n + 1


def _meta_arrotondata_per_eccesso(n_dispari: int) -> int:
    return (n_dispari + 1) // 2
