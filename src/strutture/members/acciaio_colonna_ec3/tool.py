"""Tool registration: acciaio-colonna-h-ec3 — H/I-section steel column, EN1993-1-1.

One composed `Tool` for the whole sheet (acciaio-colonne-ec3!Column check): every step module is a
small pure function; `run` composes a few private helpers, each wiring a handful of step modules.
"""
from strutture.shared.report import Report, success
from strutture.shared.tool import Tool

from . import critica_elastica, flessione, materiale, sezione, taglio, taglio_instabilita
from .buckling_curve import alpha_flessionali, alpha_lt, curva_lt
from .instabilita_flessionale import costruisci_instabilita_flessionale
from .instabilita_flesso_torsionale import costruisci_ltb
from .interazione import costruisci_interazione
from .interazione_semplificata import costruisci_interazione_semplificata
from .models import ColonnaEc3Input
from .results import (
    ColonnaEc3Output,
    Flessione,
    InstabilitaFlessionale,
    InstabilitaTorsoFlessionale,
    Interazione,
    InterazioneSemplificata,
    Materiali,
    Sezione,
    Taglio,
    TaglioInstabilita,
)

ESEMPIO_AUREO = {
    "sezione_nome": "550x450x8x16 + plate 100x16", "b_mm": 280, "h_mm": 500, "tw_mm": 8, "tf_mm": 12,
    "area_mm2": 10528, "grado_acciaio": "Q345", "gamma_m0": 1, "gamma_m1": 1, "tipo_lavorazione": "hot finished",
    "classe_sezione": "class 3", "iyy_mm4": 4.72063e8, "izz_mm4": 4.39243e7, "wel_y_mm3": 1.88825e6,
    "wpl_y_mm3": 2.09283e6, "wel_z_mm3": 3.13745e5, "wpl_z_mm3": 4.78016e5, "it_mm4": 4.05255e5,
    "e_MPa": 206000, "iy_mm": 211.752, "iz_mm": 62.5921, "nsd_kN": 172.326, "my_sd_kNm": 120.689,
    "mz_sd_kNm": 0.00639699, "vy_sd_kN": 29.2057, "vz_sd_kN": 0.00235166, "lcr_yy_mm": 16485.6,
    "lcr_zz_mm": 2083.1, "ly_mm": 18850, "lt_mm": 1800, "c1": 1.871, "mj_y_kNm": 0.00695734,
    "mj_z_kNm": 0.0224413, "dmax_yy_mm": 0, "dmax_zz_mm": 0, "diagramma_tipo_y": "1", "diagramma_tipo_z": "1",
    "legacy_compat": True,
}


def _costruisci_sezione_e_stabilita(
    inputs: ColonnaEc3Input, materiali: Materiali
) -> tuple[Sezione, int, float, float, float, InstabilitaFlessionale, InstabilitaTorsoFlessionale]:
    """Sezione + instabilità flessionale/flesso-torsionale (§5.5, §6.3.1, §6.3.2)."""
    curva_instabilita_lt = curva_lt(inputs.h_mm, inputs.b_mm, inputs.tipo_lavorazione)
    a_lt = alpha_lt(curva_instabilita_lt)
    alpha_yy, alpha_zz, curva_yy, curva_zz = alpha_flessionali(
        inputs.h_mm, inputs.b_mm, inputs.tf_mm, inputs.tipo_lavorazione, legacy_compat=inputs.legacy_compat
    )
    sez = sezione.costruisci_sezione(
        b_mm=inputs.b_mm, h_mm=inputs.h_mm, tw_mm=inputs.tw_mm, tf_mm=inputs.tf_mm, area_mm2=inputs.area_mm2,
        iyy_mm4=inputs.iyy_mm4, izz_mm4=inputs.izz_mm4, it_mm4=inputs.it_mm4, e_MPa=inputs.e_MPa,
        iy_mm=inputs.iy_mm, iz_mm=inputs.iz_mm, wel_y_mm3=inputs.wel_y_mm3, wpl_y_mm3=inputs.wpl_y_mm3,
        wel_z_mm3=inputs.wel_z_mm3, wpl_z_mm3=inputs.wpl_z_mm3, fyd_MPa=materiali.fyd_MPa, fyk_MPa=materiali.fyk_MPa,
        classe=inputs.classe_sezione, curva_instabilita_lt=curva_instabilita_lt,
        curva_flessionale_yy=curva_yy, curva_flessionale_zz=curva_zz, alpha_yy=alpha_yy, alpha_zz=alpha_zz,
        alpha_lt=a_lt, legacy_compat=inputs.legacy_compat,
    )
    classe_num = sezione.numero_classe(inputs.classe_sezione)
    ncr_y = critica_elastica.ncr_flessionale_kN(inputs.e_MPa, inputs.iyy_mm4, inputs.lcr_yy_mm)
    ncr_z = critica_elastica.ncr_flessionale_kN(inputs.e_MPa, inputs.izz_mm4, inputs.lcr_zz_mm)
    ncr_t = critica_elastica.ncr_torsionale_kN(sez.g_MPa, inputs.it_mm4, inputs.e_MPa, sez.iw_mm6, inputs.lt_mm, sez.i0_quadro_mm2)
    instab_fless = costruisci_instabilita_flessionale(
        area_mm2=inputs.area_mm2, fyd_MPa=materiali.fyd_MPa, fyk_MPa=materiali.fyk_MPa,
        ncr_y_kN=ncr_y, ncr_z_kN=ncr_z, ncr_t_kN=ncr_t, alpha_yy=alpha_yy, alpha_zz=alpha_zz,
        legacy_compat=inputs.legacy_compat,
    )
    ltb = costruisci_ltb(
        c1=inputs.c1, e_MPa=inputs.e_MPa, izz_mm4=inputs.izz_mm4, lt_mm=inputs.lt_mm, iw_mm6=sez.iw_mm6,
        g_MPa=sez.g_MPa, it_mm4=inputs.it_mm4, classe_num=classe_num, wel_y_mm3=inputs.wel_y_mm3,
        wpl_y_mm3=inputs.wpl_y_mm3, fyd_MPa=materiali.fyd_MPa, fyk_MPa=materiali.fyk_MPa, alpha_lt=a_lt,
        my_sd_kNm=inputs.my_sd_kNm, mz_sd_kNm=inputs.mz_sd_kNm, legacy_compat=inputs.legacy_compat,
    )
    return sez, classe_num, ncr_y, ncr_z, ncr_t, instab_fless, ltb


def _costruisci_resistenze_sezione(
    inputs: ColonnaEc3Input, materiali: Materiali, sez: Sezione, classe_num: int
) -> tuple[Taglio, Flessione, TaglioInstabilita]:
    """Taglio, flessione e instabilità a taglio dell'anima (§6.2.5, §6.2.6, §6.2.8, EN1993-1-5 §5)."""
    tgl = taglio.costruisci_taglio(
        av_z_mm2=sez.av_z_mm2, av_y_mm2=sez.av_y_mm2, fyd_MPa=materiali.fyd_MPa,
        vy_sd_kN=inputs.vy_sd_kN, vz_sd_kN=inputs.vz_sd_kN, legacy_compat=inputs.legacy_compat,
    )
    fless = flessione.costruisci_flessione(
        classe_num=classe_num, wel_y_mm3=inputs.wel_y_mm3, wpl_y_mm3=inputs.wpl_y_mm3,
        wel_z_mm3=inputs.wel_z_mm3, wpl_z_mm3=inputs.wpl_z_mm3, fyd_MPa=materiali.fyd_MPa,
        gamma_m0=materiali.gamma_m0, vy_sd_kN=inputs.vy_sd_kN, vz_sd_kN=inputs.vz_sd_kN,
        vpl_rd_anima_kN=tgl.vpl_rd_anima_kN, vpl_rd_ali_kN=tgl.vpl_rd_ali_kN,
        my_sd_kNm=inputs.my_sd_kNm, mz_sd_kNm=inputs.mz_sd_kNm, legacy_compat=inputs.legacy_compat,
    )
    tgl_instab = taglio_instabilita.costruisci_taglio_instabilita(
        b_mm=inputs.b_mm, h_mm=inputs.h_mm, tw_mm=inputs.tw_mm, tf_mm=inputs.tf_mm, ly_mm=inputs.ly_mm,
        fyd_MPa=materiali.fyd_MPa, fyk_MPa=materiali.fyk_MPa, gamma_m0=materiali.gamma_m0, gamma_m1=materiali.gamma_m1,
        nsd_kN=inputs.nsd_kN, my_sd_kNm=inputs.my_sd_kNm, vy_sd_kN=inputs.vy_sd_kN, legacy_compat=inputs.legacy_compat,
    )
    return tgl, fless, tgl_instab


def _costruisci_interazioni(
    inputs: ColonnaEc3Input, materiali: Materiali, sez: Sezione, classe_num: int,
    ncr_y: float, ncr_z: float, ncr_t: float,
    instab_fless: InstabilitaFlessionale, ltb: InstabilitaTorsoFlessionale,
) -> tuple[Interazione, InterazioneSemplificata]:
    """Interazione N-My-Mz, Annex A (§6.3.3) e verifiche semplificate di riscontro (§6.2.9.1)."""
    interaz = costruisci_interazione(
        inputs=inputs, classe_num=classe_num, gamma_m1=materiali.gamma_m1, area_mm2=inputs.area_mm2,
        npl_kN=sez.npl_kN, mpl_y_kNm=sez.mpl_y_kNm, mpl_z_kNm=sez.mpl_z_kNm,
        npl_rk_kN=sez.npl_rk_kN, mpl_y_rk_kNm=sez.mpl_y_rk_kNm, mpl_z_rk_kNm=sez.mpl_z_rk_kNm,
        wy=sez.wy, wz=sez.wz,
        wel_y_mm3=inputs.wel_y_mm3, wpl_y_mm3=inputs.wpl_y_mm3, wel_z_mm3=inputs.wel_z_mm3, wpl_z_mm3=inputs.wpl_z_mm3,
        ncr_y_kN=ncr_y, ncr_z_kN=ncr_z, ncr_t_kN=ncr_t, chi_yy=instab_fless.chi_yy, chi_zz=instab_fless.chi_zz,
        chi_lt=ltb.chi_lt, lambda_max=instab_fless.lambda_max, lambda_zz=instab_fless.lambda_zz,
        lambda_lt=ltb.lambda_lt, alpha_lt_torsione=sez.alpha_lt_torsione,
    )
    interaz_semp = costruisci_interazione_semplificata(
        nsd_kN=inputs.nsd_kN, area_mm2=inputs.area_mm2, fyd_MPa=materiali.fyd_MPa, b_mm=inputs.b_mm,
        h_mm=inputs.h_mm, tw_mm=inputs.tw_mm, tf_mm=inputs.tf_mm, mpl_y_kNm=sez.mpl_y_kNm, mpl_z_kNm=sez.mpl_z_kNm,
        my_sd_kNm=inputs.my_sd_kNm, mz_sd_kNm=inputs.mz_sd_kNm, legacy_compat=inputs.legacy_compat,
    )
    return interaz, interaz_semp


def run(inputs: ColonnaEc3Input) -> Report[ColonnaEc3Output]:
    materiali, warnings = materiale.risolvi_materiale(
        inputs.grado_acciaio, inputs.gamma_m0, inputs.gamma_m1, legacy_compat=inputs.legacy_compat
    )
    sez, classe_num, ncr_y, ncr_z, ncr_t, instab_fless, ltb = _costruisci_sezione_e_stabilita(inputs, materiali)
    tgl, fless, tgl_instab = _costruisci_resistenze_sezione(inputs, materiali, sez, classe_num)
    interaz, interaz_semp = _costruisci_interazioni(
        inputs, materiali, sez, classe_num, ncr_y, ncr_z, ncr_t, instab_fless, ltb
    )
    data = ColonnaEc3Output(
        materiali=materiali, sezione=sez, instabilita_flessionale=instab_fless, instabilita_torso_flessionale=ltb,
        flessione=fless, taglio=tgl, taglio_instabilita=tgl_instab, interazione=interaz, interazione_semplificata=interaz_semp,
    )
    checks = (
        tgl.verifica_anima, tgl.verifica_ali, fless.verifica_y, fless.verifica_z, tgl_instab.verifica,
        interaz.verifica_yy, interaz.verifica_zz, interaz_semp.verifica_yy, interaz_semp.verifica_zz,
        interaz_semp.verifica_lineare, interaz_semp.verifica_potenza,
    )
    return success(data, inputs, checks=checks, warnings=warnings)


TOOLS = (
    Tool(
        name="acciaio-colonna-h-ec3",
        title="Verifica di instabilità e resistenza colonne ad H/I — EC3",
        group="Acciaio / Colonne",
        norm="EN1993-1-1 §5.5, §6.2, §6.3",
        input_model=ColonnaEc3Input,
        output_model=ColonnaEc3Output,
        run=run,
        example={k: v for k, v in ESEMPIO_AUREO.items() if k != "legacy_compat"},
    ),
)
