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
from typing import NamedTuple

from strutture.shared.divergences import legacy
from strutture.shared.load_table import Famiglia
from strutture.shared.rebar_catalog import bar_callout

from .flessione_armatura import FYK_REFERENCE_LEGACY_MPA, meta_arrotondata_per_eccesso, progetta_armatura
from .inviluppo import InviluppoRiga
from .models_flessione import Flessione
from .momento_cantilever import momento_cantilever_kNm

MARGIN_EFFECTIVE_DEPTH_MM = 30.0  # sheet's `1.5*20`: assumed half-diameter margin for the As calc.
MINIMUM_REINFORCEMENT_RATIO = 0.001  # NTC2018 minimo armature a piastra/soletta bidirezionale, entrambe le facce.
TWO_FACES = 2.0

ULS_FAMILIES_FIXED: tuple[Famiglia, ...] = ("SLU_STR", "SLU_EQU", "SLV_STR", "SLV_EQU")
ULS_FAMILIES_LEGACY: tuple[Famiglia, ...] = ("SLU_STR", "SLE_QP", "SLU_EQU", "SLV_EQU")


def mead_families(*, legacy_compat: bool) -> tuple[Famiglia, ...]:
    """Families entering the MEd envelope (fix D4: ULS-type only; sheet also includes `SLE_QP`)."""
    return (ULS_FAMILIES_LEGACY
            if legacy("plinti-isolati/inviluppo-momento-slu-include-famiglia-sle", legacy_compat)
            else ULS_FAMILIES_FIXED)


def max_pressione_kpa(inviluppo: tuple[InviluppoRiga, ...], famiglie: tuple[Famiglia, ...]) -> float:
    """MAX of the family envelope `pressione_max_kpa` over the given families (0 if none present)."""
    valori = [r.valore for r in inviluppo if r.grandezza == "pressione_max_kpa" and r.famiglia in famiglie]
    return max(valori, default=0.0)


def _eccentricita_cantilever(ex_m: float, ey_m: float, *, legacy_compat: bool) -> tuple[float, float]:
    """Which user eccentricity lengthens which cantilever: `(extra_x_m, extra_y_m)`. `legacy_compat=True`
    reproduces the sheet's own swap (X cantilever gets eY, Y cantilever gets eX, see module docstring);
    `legacy_compat=False` pairs each eccentricity with its own axis (eX -> X cantilever)."""
    if legacy("plinti-isolati/eccentricita-cantilever-x-y-scambiate", legacy_compat):
        return ey_m, ex_m
    return ex_m, ey_m


class _SollecitazioniSlu(NamedTuple):
    """Governing ULS moment + required/minimum steel + bar count, both directions (private helper:
    keeps `flessione()` under the function size limit, regola 12)."""

    mx_slu_kNm: float
    my_slu_kNm: float
    as_x_cm2: float
    as_y_cm2: float
    as_x_min_cm2: float
    as_y_min_cm2: float
    n_x: int
    n_y: int
    h_mm: float


def _sollecitazioni_slu(
    sigma_slu_kpa: float, ax_m: float, by_m: float, h_plinto_m: float, a_pedestal_m: float, b_pedestal_m: float,
    ex_m: float, ey_m: float, copriferro_cm: float, passo_armatura_cm: float, fyd_MPa: float, *,
    legacy_compat: bool,
) -> _SollecitazioniSlu:
    h_mm = h_plinto_m * 1000.0
    d_mm = h_mm - copriferro_cm * 10.0 - MARGIN_EFFECTIVE_DEPTH_MM

    extra_x_m, extra_y_m = _eccentricita_cantilever(ex_m, ey_m, legacy_compat=legacy_compat)
    mx_slu_kNm = momento_cantilever_kNm(sigma_slu_kpa, by_m, ax_m, a_pedestal_m / 2.0, extra_x_m, legacy_compat=legacy_compat)
    my_slu_kNm = momento_cantilever_kNm(sigma_slu_kpa, ax_m, by_m, b_pedestal_m / 2.0, extra_y_m, legacy_compat=legacy_compat)

    return _SollecitazioniSlu(
        mx_slu_kNm=mx_slu_kNm, my_slu_kNm=my_slu_kNm,
        as_x_cm2=_as_required_cm2(mx_slu_kNm, d_mm, fyd_MPa), as_y_cm2=_as_required_cm2(my_slu_kNm, d_mm, fyd_MPa),
        as_x_min_cm2=_as_min_cm2(by_m * 1000.0, h_mm), as_y_min_cm2=_as_min_cm2(ax_m * 1000.0, h_mm),
        n_x=_bar_count(by_m * 100.0, copriferro_cm, passo_armatura_cm),
        n_y=_bar_count(ax_m * 100.0, copriferro_cm, passo_armatura_cm),
        h_mm=h_mm,
    )


def flessione(
    inviluppo: tuple[InviluppoRiga, ...], ax_m: float, by_m: float, h_plinto_m: float,
    a_pedestal_m: float, b_pedestal_m: float, ex_m: float, ey_m: float,
    copriferro_cm: float, passo_armatura_cm: float, diametro_manuale_x_mm: float, diametro_manuale_y_mm: float,
    fyd_MPa: float, fyk_MPa: float, fctm_MPa: float, *, legacy_compat: bool,
) -> Flessione:
    """Bending moment at the column face + required/provided flexural reinforcement, both directions."""
    sigma_slu_kpa = max_pressione_kpa(inviluppo, mead_families(legacy_compat=legacy_compat))
    soll = _sollecitazioni_slu(
        sigma_slu_kpa, ax_m, by_m, h_plinto_m, a_pedestal_m, b_pedestal_m, ex_m, ey_m,
        copriferro_cm, passo_armatura_cm, fyd_MPa, legacy_compat=legacy_compat,
    )
    fyk_riferimento = (FYK_REFERENCE_LEGACY_MPA
                       if legacy("plinti-isolati/phi-min-divisore-500-invece-di-fyk", legacy_compat)
                       else fyk_MPa)
    armatura = progetta_armatura(
        soll.as_x_cm2, soll.as_y_cm2, soll.as_x_min_cm2, soll.as_y_min_cm2, soll.n_x, soll.n_y,
        diametro_manuale_x_mm, diametro_manuale_y_mm, fctm_MPa, fyk_riferimento, soll.h_mm,
        copriferro_cm, passo_armatura_cm, legacy_compat=legacy_compat,
    )

    return Flessione(
        mx_slu_kNm=soll.mx_slu_kNm, my_slu_kNm=soll.my_slu_kNm,
        as_x_cm2=soll.as_x_cm2, as_y_cm2=soll.as_y_cm2, as_x_min_cm2=soll.as_x_min_cm2, as_y_min_cm2=soll.as_y_min_cm2,
        n_x=armatura.n_x_dispari, n_y=armatura.n_y_dispari,
        phi_x_mm=armatura.diam_x_mm, phi_y_mm=armatura.diam_y_mm, phi_min_mm=armatura.phi_min_mm,
        as_prov_x_mm2=armatura.as_prov_x_mm2, as_prov_y_mm2=armatura.as_prov_y_mm2,
        callout_sup_x=bar_callout(meta_arrotondata_per_eccesso(armatura.n_x_dispari), armatura.diam_x_mm),
        callout_inf_x=bar_callout(armatura.n_x_dispari, armatura.diam_x_mm),
        callout_sup_y=bar_callout(meta_arrotondata_per_eccesso(armatura.n_y_dispari), armatura.diam_y_mm),
        callout_inf_y=bar_callout(armatura.n_y_dispari, armatura.diam_y_mm),
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
