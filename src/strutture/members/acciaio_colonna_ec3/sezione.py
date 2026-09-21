"""Section-derived quantities (column-check!P9, P12, AI9, AI10, AI24, AI28, AN28, AV41, Q39-Q41).

Fixed divergence (docs/divergences/acciaio-colonna-ec3.md): "class 4" is an accepted
`ClasseSezione` value, but no effective-width calculation exists anywhere in this module (or the
sheet). Legacy mode reproduces the sheet's implicit treatment of class 4 as class 3 (gross
section); fixed mode refuses to silently understate the reduction and raises `CalcError` instead
of inventing an EN1993-1-5 §4.4 effective-width formula that was never specified.
"""
from strutture.shared.materials.structural_steel import modulo_taglio
from strutture.shared.report import CalcError
from strutture.shared.units import n_to_kn, nmm_to_knm

from .models import ClasseSezione
from .results import Sezione

LIMITE_WY_WZ = 1.5  # column-check!AI28/AN28 cap on Wpl/Wel.


def numero_classe(classe: ClasseSezione) -> int:
    """column-check!AQ26 — "class 1".."class 4" -> 1..4."""
    return int(classe.split()[-1])


def area_taglio_anima_mm2(h_mm: float, tf_mm: float, tw_mm: float) -> float:
    """column-check!P9 — Av,z, EN1993-1-1 §6.2.6(3)."""
    return 1.2 * (h_mm - 2.0 * tf_mm) * tw_mm


def area_taglio_ali_mm2(b_mm: float, tf_mm: float) -> float:
    """column-check!P12 — Av,y."""
    return 2.0 * b_mm * tf_mm


def costante_ingobbamento_mm6(izz_mm4: float, h_mm: float, tf_mm: float) -> float:
    """column-check!AI10 — Iw = Izz*(h-tf)^2/4."""
    return izz_mm4 * (h_mm - tf_mm) ** 2 / 4.0


def rapporto_moduli(wpl_mm3: float, wel_mm3: float) -> float:
    """column-check!AI28/AN28 — MIN(Wpl/Wel, 1.5)."""
    return min(wpl_mm3 / wel_mm3, LIMITE_WY_WZ)


def momento_plastico_resistente_kNm(
    classe: int, wel_mm3: float, wpl_mm3: float, fy_MPa: float
) -> float:
    """column-check!Q39/Q40 — Wpl*fy for class 1/2, Wel*fy for class 3/4 (fy = fyd or fyk, per caller)."""
    modulo = wel_mm3 if classe >= 3 else wpl_mm3
    return nmm_to_knm(modulo * fy_MPa)


def npl_kN(area_mm2: float, fy_MPa: float) -> float:
    """column-check!Q41 — Npl = A*fy (fy = fyd or fyk, per caller)."""
    return n_to_kn(area_mm2 * fy_MPa)


def verifica_classe_supportata(classe_num: int, *, legacy_compat: bool) -> None:
    """Class 4 has no effective-width implementation (§4.4) in this module — see module docstring."""
    if classe_num == 4 and not legacy_compat:
        raise CalcError(
            "Sezione di classe 4: nessun calcolo di area/moduli efficaci (EN1993-1-5 §4.4) "
            "implementato; la resistenza sulla sezione lorda non è conservativa."
        )


def alpha_lt_torsione(it_mm4: float, iyy_mm4: float) -> float:
    """column-check!AI24 — aLT = MAX(1-IT/Iyy, 0), a torsional-susceptibility factor."""
    return max(1.0 - it_mm4 / iyy_mm4, 0.0)


def raggio_polare_quadro_mm2(iy_mm: float, iz_mm: float) -> float:
    """column-check!AV41 — i0^2 = iy^2 + iz^2."""
    return iy_mm**2 + iz_mm**2


def costruisci_sezione(
    *,
    b_mm: float,
    h_mm: float,
    tw_mm: float,
    tf_mm: float,
    area_mm2: float,
    iyy_mm4: float,
    izz_mm4: float,
    it_mm4: float,
    e_MPa: float,
    iy_mm: float,
    iz_mm: float,
    wel_y_mm3: float,
    wpl_y_mm3: float,
    wel_z_mm3: float,
    wpl_z_mm3: float,
    fyd_MPa: float,
    fyk_MPa: float,
    classe: ClasseSezione,
    curva_instabilita_lt: str,
    curva_flessionale_yy: str,
    curva_flessionale_zz: str,
    alpha_yy: float,
    alpha_zz: float,
    alpha_lt: float,
    legacy_compat: bool,
) -> Sezione:
    classe_num = numero_classe(classe)
    verifica_classe_supportata(classe_num, legacy_compat=legacy_compat)
    return Sezione(
        av_z_mm2=area_taglio_anima_mm2(h_mm, tf_mm, tw_mm),
        av_y_mm2=area_taglio_ali_mm2(b_mm, tf_mm),
        iw_mm6=costante_ingobbamento_mm6(izz_mm4, h_mm, tf_mm),
        g_MPa=modulo_taglio(e_MPa),
        wy=rapporto_moduli(wpl_y_mm3, wel_y_mm3),
        wz=rapporto_moduli(wpl_z_mm3, wel_z_mm3),
        i0_quadro_mm2=raggio_polare_quadro_mm2(iy_mm, iz_mm),
        npl_kN=npl_kN(area_mm2, fyd_MPa),
        mpl_y_kNm=momento_plastico_resistente_kNm(classe_num, wel_y_mm3, wpl_y_mm3, fyd_MPa),
        mpl_z_kNm=momento_plastico_resistente_kNm(classe_num, wel_z_mm3, wpl_z_mm3, fyd_MPa),
        npl_rk_kN=npl_kN(area_mm2, fyk_MPa),
        mpl_y_rk_kNm=momento_plastico_resistente_kNm(classe_num, wel_y_mm3, wpl_y_mm3, fyk_MPa),
        mpl_z_rk_kNm=momento_plastico_resistente_kNm(classe_num, wel_z_mm3, wpl_z_mm3, fyk_MPa),
        alpha_lt_torsione=alpha_lt_torsione(it_mm4, iyy_mm4),
        curva_instabilita_lt=curva_instabilita_lt,
        curva_flessionale_yy=curva_flessionale_yy,
        curva_flessionale_zz=curva_flessionale_zz,
        alpha_yy=alpha_yy,
        alpha_zz=alpha_zz,
        alpha_lt=alpha_lt,
    )
