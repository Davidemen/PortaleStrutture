"""Equivalent uniform moment factors Cmy, Cmz, CmLT (EN1993-1-1 Annex A/Table B.3;
column-check!AI35-AN59, AM64-AM66). Reproduced literally from the cellmap in both modes — no bug
flagged for this block. Cmy alone gets the torsional-susceptibility correction (per the moment
diagram along the strong axis, which governs LTB); Cmz never does, matching the sheet.

New divergence (found by direct cell-formula inspection): the diagram-type-2 branch of Cmz
(`AN53`) reuses `P5` (Iyy, the y-y axis inertia used by the analogous `AI53` for Cmy) instead of
`P6` (Izz) — a copy-paste slip when the y-y formula was mirrored for the z-z axis. Fixed behaviour
uses Izz; legacy reproduces the Iyy reuse. See docs/divergences/acciaio-colonna-ec3.md.
"""
import math

from strutture.shared.units import kn_to_n, knm_to_nmm

from .models import DiagrammaMomento


def rapporto_estremi(m_sd_kNm: float, m_j_kNm: float) -> float:
    """column-check!AI46/AN46 — psi = MIN(Msd,Mj)/MAX(Msd,Mj)."""
    return min(m_sd_kNm, m_j_kNm) / max(m_sd_kNm, m_j_kNm)


def epsilon_y(my_sd_kNm: float, area_mm2: float, nsd_kN: float, wel_y_mm3: float) -> float:
    """column-check!AV35 — epsilon_y = My,sd[N*mm]*A/(Nsd[N]*Wel,y)."""
    return knm_to_nmm(my_sd_kNm) * area_mm2 / (kn_to_n(nsd_kN) * wel_y_mm3)


def cm0_tipo1(psi: float, nsd_kN: float, ncr_kN: float) -> float:
    """column-check!AI47/AN47 — end moments only, EN1993-1-1 Table B.3."""
    return 0.79 + 0.21 * psi + 0.36 * (psi - 0.33) * nsd_kN / ncr_kN


def cm0_tipo2(e_MPa: float, inerzia_mm4: float, dmax_mm: float, lcr_mm: float, m_sd_kNm: float, nsd_kN: float, ncr_kN: float) -> float:
    """column-check!AI53/AN53 — transverse load, deflection-based factor."""
    base = 1.0 + ((math.pi**2 * e_MPa * inerzia_mm4 * dmax_mm) / (lcr_mm**2 * knm_to_nmm(m_sd_kNm)) - 1.0) * (nsd_kN / ncr_kN)
    return base


def cm0_tipo3a(nsd_kN: float, ncr_kN: float) -> float:
    """column-check!AI56/AN56."""
    return 1.0 - 0.18 * nsd_kN / ncr_kN


def cm0_tipo3b(nsd_kN: float, ncr_kN: float) -> float:
    """column-check!AI59/AN59."""
    return 1.0 + 0.03 * nsd_kN / ncr_kN


def cmz(
    tipo: DiagrammaMomento, mz_sd_kNm: float, mj_z_kNm: float, e_MPa: float, iyy_mm4: float, izz_mm4: float,
    dmax_zz_mm: float, lcr_zz_mm: float, nsd_kN: float, ncr_z_kN: float, *, legacy_compat: bool,
) -> float:
    """column-check!AM65 — Cmz, never torsion-corrected; type-2 branch — see module docstring."""
    if tipo == "1":
        return cm0_tipo1(rapporto_estremi(mz_sd_kNm, mj_z_kNm), nsd_kN, ncr_z_kN)
    if tipo == "2":
        inerzia = iyy_mm4 if legacy_compat else izz_mm4
        return cm0_tipo2(e_MPa, inerzia, dmax_zz_mm, lcr_zz_mm, mz_sd_kNm, nsd_kN, ncr_z_kN)
    if tipo == "3a":
        return cm0_tipo3a(nsd_kN, ncr_z_kN)
    return cm0_tipo3b(nsd_kN, ncr_z_kN)


def cmy(
    tipo: DiagrammaMomento, lambda_lt: float, soglia_lambda0: float, my_sd_kNm: float, mj_y_kNm: float,
    e_MPa: float, iyy_mm4: float, dmax_yy_mm: float, lcr_yy_mm: float, nsd_kN: float, ncr_y_kN: float,
    alpha_lt_torsione: float, eps_y: float,
) -> float:
    """column-check!AM64 — Cmy, torsion-corrected when lambda_LT exceeds the Annex A threshold.

    Diagram type "3a" (AI56/AJ56) squares the (1-Cmy0) term in its correction; the others (1/2/3b,
    AI47/AI53/AI59 vs AJ47/AJ53/AJ59) share the same linear correction — reproduced as-is.
    """
    if tipo == "1":
        base = cm0_tipo1(rapporto_estremi(my_sd_kNm, mj_y_kNm), nsd_kN, ncr_y_kN)
    elif tipo == "2":
        base = cm0_tipo2(e_MPa, iyy_mm4, dmax_yy_mm, lcr_yy_mm, my_sd_kNm, nsd_kN, ncr_y_kN)
    elif tipo == "3a":
        base = cm0_tipo3a(nsd_kN, ncr_y_kN)
    else:
        base = cm0_tipo3b(nsd_kN, ncr_y_kN)
    if lambda_lt <= soglia_lambda0:
        return base
    fattore = alpha_lt_torsione * math.sqrt(eps_y)
    correzione = fattore / (1.0 + fattore)
    if tipo == "3a":
        return base + (1.0 - base) * (1.0 - base) * correzione
    return base + (1.0 - base) * correzione


def soglia_lambda0(c1: float, nsd_kN: float, ncr_z_kN: float, ncr_t_kN: float) -> float:
    """column-check!AV43 — threshold selecting the torsion-corrected Cmy branch."""
    return 0.2 * math.sqrt(c1) * ((1.0 - nsd_kN / ncr_z_kN) * (1.0 - nsd_kN / ncr_t_kN)) ** 0.25


def cm_lt(lambda_lt: float, soglia: float, cmy_valore: float, alpha_lt_torsione: float, nsd_kN: float, ncr_z_kN: float, ncr_t_kN: float) -> float:
    """column-check!AM66 — CmLT."""
    if lambda_lt < soglia:
        return 1.0
    return max((cmy_valore**2 * alpha_lt_torsione) / math.sqrt((1.0 - nsd_kN / ncr_z_kN) * (1.0 - nsd_kN / ncr_t_kN)), 1.0)
