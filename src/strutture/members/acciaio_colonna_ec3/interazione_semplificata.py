"""Simplified fallback interaction checks (column-check!H46-H52, J53/J54, V54, I56 — EN1993-1-1 §6.2.9.1).

New divergence (found by direct cell-formula inspection): `V54`'s axial term is `Nsd/(A*fyd)`
(column-check cells `H10*H14`, i.e. Npl **in Newtons, without the /1000 of `Q41`/`H46`**), making
it ~1000x smaller than the intended `n = Nsd/Npl,Rd` — effectively dropping the axial-load
contribution from this particular linear check. `H46` (used everywhere else, including `I56`)
computes the same ratio correctly. Fixed behaviour uses `H46`'s `n`; legacy reproduces the
mis-scaled term. See docs/divergences/acciaio-colonna-ec3.md.

Fixed divergence: `I56` (eq. 6.41) divides by the UNREDUCED `Mpl,Rd` instead of the axial-reduced
`MN,Rd` the same function already computes (`J53`/`J54`) — EN1993-1-1 §6.2.9.1(6) eq. (6.41) is
`[My,Ed/MN,y,Rd]^2 + [Mz,Ed/MN,z,Rd]^(5n)`. Fixed mode divides by MN,Rd; legacy reproduces Mpl,Rd.

Fixed divergence: `H50` (`a_zz`, feeding `J54`'s MN,z,Rd) uses a flange-area-style ratio
`(A-2*h*tw)/A` instead of EN1993-1-1 §6.2.9.1(5)'s single `a = MIN((A-2*b*tf)/A, 0.5)` used for
BOTH axes, and then applies the y-y interpolation formula to z-z as well — not the clause's actual
z-z expression (`Mpl,z,Rd` for `n<=a`, `Mpl,z,Rd*[1-((n-a)/(1-a))^2]` for `n>a`). Fixed mode
implements §6.2.9.1(5) literally for MN,z,Rd; legacy reproduces the sheet's substitute formula.
"""
from strutture.shared.divergences import legacy
from strutture.shared.report import Check
from strutture.shared.units import kn_to_n

from .results import InterazioneSemplificata
from .tables import ESPONENTE_INTERAZIONE_YY


def rapporto_assiale(nsd_kN: float, area_mm2: float, fyd_MPa: float) -> float:
    """column-check!H46 — n = Nsd*1000/(A*fyd)."""
    return kn_to_n(nsd_kN) / (area_mm2 * fyd_MPa)


def fattore_area_ali(area_mm2: float, b_mm: float, tf_mm: float) -> float:
    """column-check!H48 — a_yy = MIN((A-2*b*tf)/A, 0.5); EN1993-1-1 §6.2.9.1(5), used for both axes
    in fixed mode (see module docstring)."""
    return min((area_mm2 - 2.0 * b_mm * tf_mm) / area_mm2, 0.5)


def fattore_area_anima(area_mm2: float, h_mm: float, tw_mm: float) -> float:
    """column-check!H50 — a_zz = MIN((A-2*h*tw)/A, 0.5); reproduced in legacy mode only (see module
    docstring — §6.2.9.1(5) uses the single flange-based `a` for both axes)."""
    return min((area_mm2 - 2.0 * h_mm * tw_mm) / area_mm2, 0.5)


def mn_rd_y_kNm(mpl_y_kNm: float, n: float, a: float) -> float:
    """column-check!J53 — MN,y,Rd = MIN(Mpl,y*(1-n)/(1-0.5*a), Mpl,y), EN1993-1-1 §6.2.9.1(5)."""
    return min(mpl_y_kNm * (1.0 - n) / (1.0 - 0.5 * a), mpl_y_kNm)


def mn_rd_kNm(mpl_kNm: float, n: float, a: float) -> float:
    """column-check!J53/J54 — legacy MN,Rd = MIN(Mpl*(1-n)/(1-0.5*a), Mpl), applied to both axes."""
    return min(mpl_kNm * (1.0 - n) / (1.0 - 0.5 * a), mpl_kNm)


def mn_rd_z_kNm_fixed(mpl_z_kNm: float, n: float, a: float) -> float:
    """EN1993-1-1 §6.2.9.1(5) — MN,z,Rd = Mpl,z for n<=a, else Mpl,z*(1-((n-a)/(1-a))^2)."""
    if n <= a:
        return mpl_z_kNm
    return mpl_z_kNm * (1.0 - ((n - a) / (1.0 - a)) ** 2)


def v54_lineare(nsd_kN: float, area_mm2: float, fyd_MPa: float, my_sd_kNm: float, mn_rd_y_kNm: float,
                 mz_sd_kNm: float, mn_rd_z_kNm: float, *, legacy_compat: bool) -> float:
    """column-check!V54 — sum of linear utilisation ratios; legacy reproduces the mis-scaled n term."""
    termine_n = (
        nsd_kN / (area_mm2 * fyd_MPa)
        if legacy("acciaio-colonna-ec3/v54-termine-assiale-mille-volte-piccolo", legacy_compat)
        else rapporto_assiale(nsd_kN, area_mm2, fyd_MPa)
    )
    return termine_n + my_sd_kNm / mn_rd_y_kNm + mz_sd_kNm / mn_rd_z_kNm


def i56_potenza(my_sd_kNm: float, mn_o_mpl_y_kNm: float, mz_sd_kNm: float, mn_o_mpl_z_kNm: float, n: float) -> float:
    """column-check!I56 — (My/M*,y)^2 + (Mz/M*,z)^MAX(5n,1); caller passes MN,Rd (fixed, eq. 6.41)
    or Mpl,Rd (legacy) as M*."""
    esponente_h = max(5.0 * n, 1.0)
    return (my_sd_kNm / mn_o_mpl_y_kNm) ** ESPONENTE_INTERAZIONE_YY + (mz_sd_kNm / mn_o_mpl_z_kNm) ** esponente_h


def costruisci_interazione_semplificata(
    *, nsd_kN: float, area_mm2: float, fyd_MPa: float, b_mm: float, h_mm: float, tw_mm: float, tf_mm: float,
    mpl_y_kNm: float, mpl_z_kNm: float, my_sd_kNm: float, mz_sd_kNm: float, legacy_compat: bool,
) -> InterazioneSemplificata:
    n = rapporto_assiale(nsd_kN, area_mm2, fyd_MPa)
    a_yy = fattore_area_ali(area_mm2, b_mm, tf_mm)
    if legacy("acciaio-colonna-ec3/mn-rd-z-formula-sbagliata", legacy_compat):
        a_zz = fattore_area_anima(area_mm2, h_mm, tw_mm)
        mn_rd_y = mn_rd_kNm(mpl_y_kNm, n, a_yy)
        mn_rd_z = mn_rd_kNm(mpl_z_kNm, n, a_zz)
    else:
        mn_rd_y = mn_rd_y_kNm(mpl_y_kNm, n, a_yy)
        mn_rd_z = mn_rd_z_kNm_fixed(mpl_z_kNm, n, a_yy)
    v54 = v54_lineare(nsd_kN, area_mm2, fyd_MPa, my_sd_kNm, mn_rd_y, mz_sd_kNm, mn_rd_z, legacy_compat=legacy_compat)
    i56_denom_y, i56_denom_z = (
        (mpl_y_kNm, mpl_z_kNm) if legacy("acciaio-colonna-ec3/i56-usa-mpl-invece-di-mn-rd", legacy_compat)
        else (mn_rd_y, mn_rd_z)
    )
    i56 = i56_potenza(my_sd_kNm, i56_denom_y, mz_sd_kNm, i56_denom_z, n)
    return InterazioneSemplificata(
        n_ratio=n,
        mn_rd_y_kNm=mn_rd_y,
        mn_rd_z_kNm=mn_rd_z,
        verifica_yy=Check(name="MN,Rd,y (semplificata)", passed=mn_rd_y > my_sd_kNm, clause="EN1993-1-1 §6.2.9.1", value=my_sd_kNm, limit=mn_rd_y, unit="kNm"),
        verifica_zz=Check(name="MN,Rd,z (semplificata)", passed=mn_rd_z > mz_sd_kNm, clause="EN1993-1-1 §6.2.9.1", value=mz_sd_kNm, limit=mn_rd_z, unit="kNm"),
        v54=v54,
        verifica_lineare=Check(name="Interazione lineare (V54)", passed=v54 < 1.0, clause="EN1993-1-1 §6.2.9.1", value=v54, limit=1.0, unit="-"),
        i56=i56,
        verifica_potenza=Check(name="Interazione a potenza (I56)", passed=i56 < 1.0, clause="EN1993-1-1 §6.2.1(7)", value=i56, limit=1.0, unit="-"),
    )
