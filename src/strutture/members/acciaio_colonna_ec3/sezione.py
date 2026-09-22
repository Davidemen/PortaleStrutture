"""Section-derived quantities (column-check!P9, P12, AI9, AI10, AI24, AI28, AN28, AV41, Q39-Q41).

Fixed divergence (docs/divergences/acciaio-colonna-ec3.md): "class 4" is an accepted
`ClasseSezione` value, but no effective-width calculation exists anywhere in this module (or the
sheet). Legacy mode reproduces the sheet's implicit treatment of class 4 as class 3 (gross
section); fixed mode refuses to silently understate the reduction and raises `CalcError` instead
of inventing an EN1993-1-5 §4.4 effective-width formula that was never specified.
"""
from strutture.shared.materials.structural_steel import modulo_taglio

from .models import ClasseSezione
from .results import Sezione
from .sezione_resistenza import campi_resistenza, momento_plastico_resistente_kNm, npl_kN, verifica_classe_supportata

__all__ = [
    "alpha_lt_torsione",
    "area_taglio_ali_mm2",
    "area_taglio_anima_mm2",
    "costante_ingobbamento_mm6",
    "costruisci_sezione",
    "momento_plastico_resistente_kNm",
    "npl_kN",
    "numero_classe",
    "raggio_polare_quadro_mm2",
    "rapporto_moduli",
    "verifica_classe_supportata",
]

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


def alpha_lt_torsione(it_mm4: float, iyy_mm4: float) -> float:
    """column-check!AI24 — aLT = MAX(1-IT/Iyy, 0), a torsional-susceptibility factor."""
    return max(1.0 - it_mm4 / iyy_mm4, 0.0)


def raggio_polare_quadro_mm2(iy_mm: float, iz_mm: float) -> float:
    """column-check!AV41 — i0^2 = iy^2 + iz^2."""
    return iy_mm**2 + iz_mm**2


def _campi_geometrici(
    *, b_mm: float, h_mm: float, tw_mm: float, tf_mm: float, izz_mm4: float, it_mm4: float, iyy_mm4: float,
    e_MPa: float, iy_mm: float, iz_mm: float, wel_y_mm3: float, wpl_y_mm3: float, wel_z_mm3: float, wpl_z_mm3: float,
) -> dict[str, float]:
    """Grandezze derivate dalla geometria della sezione (P9, P12, AI9, AI10, AI24, AI28, AN28, AV41)."""
    return {
        "av_z_mm2": area_taglio_anima_mm2(h_mm, tf_mm, tw_mm),
        "av_y_mm2": area_taglio_ali_mm2(b_mm, tf_mm),
        "iw_mm6": costante_ingobbamento_mm6(izz_mm4, h_mm, tf_mm),
        "g_MPa": modulo_taglio(e_MPa),
        "wy": rapporto_moduli(wpl_y_mm3, wel_y_mm3),
        "wz": rapporto_moduli(wpl_z_mm3, wel_z_mm3),
        "i0_quadro_mm2": raggio_polare_quadro_mm2(iy_mm, iz_mm),
        "alpha_lt_torsione": alpha_lt_torsione(it_mm4, iyy_mm4),
    }


def costruisci_sezione(
    *,
    b_mm: float, h_mm: float, tw_mm: float, tf_mm: float, area_mm2: float,
    iyy_mm4: float, izz_mm4: float, it_mm4: float, e_MPa: float, iy_mm: float, iz_mm: float,
    wel_y_mm3: float, wpl_y_mm3: float, wel_z_mm3: float, wpl_z_mm3: float,
    fyd_MPa: float, fyk_MPa: float, classe: ClasseSezione,
    curva_instabilita_lt: str, curva_flessionale_yy: str, curva_flessionale_zz: str,
    alpha_yy: float, alpha_zz: float, alpha_lt: float, legacy_compat: bool,
) -> Sezione:
    classe_num = numero_classe(classe)
    verifica_classe_supportata(classe_num, legacy_compat=legacy_compat)
    campi_geometrici = _campi_geometrici(
        b_mm=b_mm, h_mm=h_mm, tw_mm=tw_mm, tf_mm=tf_mm, izz_mm4=izz_mm4, it_mm4=it_mm4, iyy_mm4=iyy_mm4,
        e_MPa=e_MPa, iy_mm=iy_mm, iz_mm=iz_mm, wel_y_mm3=wel_y_mm3, wpl_y_mm3=wpl_y_mm3,
        wel_z_mm3=wel_z_mm3, wpl_z_mm3=wpl_z_mm3,
    )
    resistenza = campi_resistenza(
        classe_num=classe_num, area_mm2=area_mm2, wel_y_mm3=wel_y_mm3, wpl_y_mm3=wpl_y_mm3,
        wel_z_mm3=wel_z_mm3, wpl_z_mm3=wpl_z_mm3, fyd_MPa=fyd_MPa, fyk_MPa=fyk_MPa,
    )
    return Sezione(
        **campi_geometrici,
        **resistenza,
        curva_instabilita_lt=curva_instabilita_lt,
        curva_flessionale_yy=curva_flessionale_yy,
        curva_flessionale_zz=curva_flessionale_zz,
        alpha_yy=alpha_yy,
        alpha_zz=alpha_zz,
        alpha_lt=alpha_lt,
    )
