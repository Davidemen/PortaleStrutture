"""Step 2: bottom + top flexural design of the pile cap slab, as a 1-meter-wide beam spanning
between pile rows (docs/specs/fond-plinti-pali.md Tool-2). Governing `Mu` is picked from two
envelope cases (max total column N with its own moment, and the extreme moment with its own N,
`Footing check!AU7:AY22`); the beam term is halved when the load is shared by two pile rows
(`schema_pali` "2x2"), full when only one row carries it ("2x1"/"1x2"), absent when the design
direction itself has a single pile position ("1x2"/"2x1"/"1x1", direct moment transfer only).

The top ("sup") block mirrors §"AU33:BA51": same beam-span logic, but the design axial force is the
table's minimum total column load (uplift-governed, `Footing check!AV36=MIN(F)`) taken with the
opposite sign, no self-weight, and `legacy_compat=True` reproduces the sheet's own use of the
literal `3.14` instead of `PI()` (docs/architecture-batch2.md §7 `plinti-pali AV51/AZ51`) — the
only numeric divergence in this step; both branches otherwise agree with the golden case."""
import math

from strutture.shared.materials.concrete import fcd as concrete_fcd
from strutture.shared.numeric import clamp
from strutture.shared.rebar_catalog import bar_area
from strutture.shared.report import CalcError

from .inviluppo import Inviluppo
from .models_flessione import DesignFlessione, Flessione
from .rows import RigaCarico

AS_MIN_RATIO_INF = 0.0018  # sheet's 0.18% (bottom), NTC2018 §4.1.6.1.1-style minimum, 1m design strip.
AS_MIN_RATIO_SUP = 0.0009  # sheet's 0.09% (top).
STRIP_WIDTH_MM = 1000.0  # the sheet designs this slab as a 1m-wide strip regardless of AX/BY.
MARGIN_LEVER_ARM = 1.5  # sheet's `1.5*ø` margin subtracted from H for the effective depth.
LEGACY_PI = 3.14  # sheet's top-reinforcement literal (bug: `AV51`/`AZ51` use 3.14, not PI()).
MU_ADIMENSIONALE_MAX = 0.25  # balanced-section limit of mu = M/(b*d^2*fcd) for z = d*(0.5+sqrt(0.25-mu)).


def flessione(
    righe: tuple[RigaCarico, ...], env: Inviluppo, count_x: int, count_y: int, lx_m: float, ly_m: float,
    h_plinto_m: float, peso_proprio_kN: float, copriferro_mm: float,
    diametro_inf_x_mm: float, diametro_inf_y_mm: float, passo_inf_x_mm: float, passo_inf_y_mm: float,
    diametro_sup_x_mm: float, diametro_sup_y_mm: float, passo_sup_x_mm: float, passo_sup_y_mm: float,
    fyd_MPa: float, fck_MPa: float, gamma_c: float, *, legacy_compat: bool,
) -> Flessione:
    """Bottom + top flexural design, X-X and Y-Y."""
    h_mm = h_plinto_m * 1000.0
    fcd_MPa = concrete_fcd(fck_MPa, gamma_c=gamma_c)

    mu_a_x, mu_b_x = _mu_inferiore(righe, env, count_x, count_y, lx_m, peso_proprio_kN, asse="x")
    mu_a_y, mu_b_y = _mu_inferiore(righe, env, count_y, count_x, ly_m, peso_proprio_kN, asse="y")

    inf_x = _progetta(max(mu_a_x, mu_b_x), h_mm, copriferro_mm, diametro_inf_x_mm, passo_inf_x_mm, fyd_MPa,
                       fcd_MPa, as_min_ratio=AS_MIN_RATIO_INF, usa_pi_letterale=False, legacy_compat=legacy_compat)
    inf_y = _progetta(max(mu_a_y, mu_b_y), h_mm, copriferro_mm, diametro_inf_y_mm, passo_inf_y_mm, fyd_MPa,
                       fcd_MPa, as_min_ratio=AS_MIN_RATIO_INF, usa_pi_letterale=False, legacy_compat=legacy_compat)

    mu_sup_x = _mu_superiore(righe, env, count_x, count_y, lx_m, colonna_associata="my_finale_kNm")
    mu_sup_y = _mu_superiore(righe, env, count_y, count_x, ly_m, colonna_associata="mx_finale_kNm")

    sup_x = _progetta(mu_sup_x, h_mm, copriferro_mm, diametro_sup_x_mm, passo_sup_x_mm, fyd_MPa, fcd_MPa,
                       as_min_ratio=AS_MIN_RATIO_SUP, usa_pi_letterale=legacy_compat, legacy_compat=legacy_compat)
    sup_y = _progetta(mu_sup_y, h_mm, copriferro_mm, diametro_sup_y_mm, passo_sup_y_mm, fyd_MPa, fcd_MPa,
                       as_min_ratio=AS_MIN_RATIO_SUP, usa_pi_letterale=legacy_compat, legacy_compat=legacy_compat)

    return Flessione(inf_x=inf_x, inf_y=inf_y, sup_x=sup_x, sup_y=sup_y)


def _mu_beam(n_own: int, n_perp: int, spacing_m: float, n_eff_kN: float, m_assoc_kNm: float) -> float:
    """Mu = 0.5 or 1.0 * n_eff * spacing/4 + |M|, or |M| alone when this axis has a single pile
    position (no beam action possible): the 0.5 factor applies when the load is shared by two pile
    rows along the perpendicular axis (`n_perp>=2`), the full factor when carried by a single row."""
    if n_own == 1:
        return abs(m_assoc_kNm)
    fattore = 0.5 if n_perp >= 2 else 1.0
    return fattore * n_eff_kN * spacing_m / 4.0 + abs(m_assoc_kNm)


def _mu_inferiore(
    righe: tuple[RigaCarico, ...], env: Inviluppo, n_own: int, n_perp: int, spacing_m: float,
    peso_proprio_kN: float, *, asse: str,
) -> tuple[float, float]:
    """(Mu_A, Mu_B): case A uses the max total column N and its own moment; case B uses the extreme
    moment of this axis and the N of whichever combo produced it."""
    m_assoc_attr = "my_finale_kNm" if asse == "x" else "mx_finale_kNm"
    m_massimo, m_minimo = (env.my_max, env.my_min) if asse == "x" else (env.mx_max, env.mx_min)

    n_a = env.n_totale_max.valore
    m_a = getattr(righe[env.n_totale_max.indice], m_assoc_attr)
    mu_a = _mu_beam(n_own, n_perp, spacing_m, n_a + peso_proprio_kN, m_a)

    usa_massimo = m_massimo.valore > abs(m_minimo.valore)
    n_b = righe[m_massimo.indice if usa_massimo else m_minimo.indice].n_kN
    m_b = max(m_massimo.valore, abs(m_minimo.valore))
    mu_b = _mu_beam(n_own, n_perp, spacing_m, n_b + peso_proprio_kN, m_b)

    return mu_a, mu_b


def _mu_superiore(
    righe: tuple[RigaCarico, ...], env: Inviluppo, n_own: int, n_perp: int, spacing_m: float, *, colonna_associata: str,
) -> float:
    """Top-slab Mu: driven by the minimum total column N (uplift), negated, no self-weight."""
    n_top = -env.n_totale_min.valore
    m_assoc = getattr(righe[env.n_totale_min.indice], colonna_associata)
    return abs(_mu_beam(n_own, n_perp, spacing_m, n_top, m_assoc))


def _braccio_leva_mm(mu_kNm: float, d_mm: float, fcd_MPa: float, *, legacy_compat: bool) -> float:
    """Internal lever arm `z`: the sheet uses the full effective depth `d` (no lever-arm reduction);
    the fix solves the rectangular-section equilibrium `z = d*(0.5 + sqrt(0.25 - mu))` with
    `mu = M/(b*d^2*fcd)` (`b` = the 1m design strip), capped at the balanced-section limit so `As`
    is never understated (docs/architecture-batch2.md code-review finding, flessione.py:106)."""
    if legacy_compat or mu_kNm <= 0.0:
        return d_mm
    mu_adim = mu_kNm * 1.0e6 / (STRIP_WIDTH_MM * d_mm**2 * fcd_MPa)
    mu_adim = clamp(mu_adim, 0.0, MU_ADIMENSIONALE_MAX)
    return d_mm * (0.5 + math.sqrt(0.25 - mu_adim))


def _progetta(
    mu_kNm: float, h_mm: float, copriferro_mm: float, diametro_mm: float, passo_mm: float, fyd_MPa: float,
    fcd_MPa: float, *, as_min_ratio: float, usa_pi_letterale: bool, legacy_compat: bool,
) -> DesignFlessione:
    """As required from `Mu*1e6/(z*fyd)` with the internal lever arm `z` (see `_braccio_leva_mm`),
    user-chosen diameter/spacing checked against it. `usa_pi_letterale` reproduces the sheet's
    `3.14` literal for the top-bar area."""
    d_mm = h_mm - copriferro_mm - MARGIN_LEVER_ARM * diametro_mm
    if d_mm <= 0:
        raise CalcError(f"copriferro/diametro troppo grandi: altezza utile d={d_mm} mm non positiva")
    z_mm = _braccio_leva_mm(mu_kNm, d_mm, fcd_MPa, legacy_compat=legacy_compat)
    as_req_flexural = mu_kNm * 1.0e6 / (z_mm * fyd_MPa)
    as_min = STRIP_WIDTH_MM * h_mm * as_min_ratio
    as_req = max(as_req_flexural, as_min)
    n_barre = math.ceil(STRIP_WIDTH_MM / passo_mm)
    area_barra = LEGACY_PI / 4.0 * diametro_mm**2 if usa_pi_letterale else bar_area(diametro_mm)
    as_prov = n_barre * area_barra
    return DesignFlessione(
        mu_kNm=mu_kNm, as_min_mm2=as_min, as_req_flexural_mm2=as_req_flexural, as_req_mm2=as_req,
        diametro_mm=diametro_mm, passo_mm=passo_mm, n_barre_per_m=n_barre, as_prov_mm2=as_prov,
        verificato=as_prov >= as_req,
    )
