"""Registration of the composed tool `ca-trave-rettangolare` (rectangular RC beam, design +
verification). NTC2018 §4.1.6.1.1, §4.1.2.3.4.2, §4.1.2.3.5.2, §4.1.2.2.5, §4.1.2.2.4,
§7.4.4.1.1, §7.4.6.1.1, §7.4.6.2.1.

How to append a new step group to this same tool:
1. Add a new `<step>.py` module with pure functions + a new frozen `<Gruppo>Output` model in
   `models.py` (never edit the models already defined there).
2. Add the new FLAT input fields to `TraveRettangolareInput`, positioned where their row sits
   on the 'Travi sez. rettangolare' sheet (not appended at the end).
3. Add the matching nested field to `TraveRettangolareOutput`.
4. In `run()` below, call the new step in sheet order; add its `Check`(s) inside `_checks()`
   below (append to the returned tuple); add the group to the `TraveRettangolareOutput(...)` call.

SLS groups (Tool 4 `verifica-sle-tensioni`, Tool 5 `verifica-fessurazione`) were added following
exactly this recipe: see `sle_tensioni.py` / `fessurazione.py`. `_checks()` composes every group's
`Check`(s) into one tuple so `run()` itself stays pure composition (see `ca_pilastri/tool_*.py`
for the same run()-stays-small pattern).
"""
import logging

from strutture.shared.report import Check, Report, success
from strutture.shared.tool import Tool

from .armatura_limiti import armatura_minima_massima
from .capacity_design import dettagli_costruttivi
from .fessurazione import verifica_fessurazione
from .flessione_slu import verifica_flessione_slu
from .geometria import altezza_utile_mm, braccio_leva_mm
from .materiali import materiali_trave
from .models import (
    ArmaturaLimitiOutput,
    CapacityDesignOutput,
    FessurazioneOutput,
    FlessioneOutput,
    SleTensioniOutput,
    TaglioOutput,
    TraveRettangolareInput,
    TraveRettangolareOutput,
)
from .relazione import relazione as relazione_trave_rettangolare
from .schizzo import disegna as disegna_schizzo
from .sle_tensioni import verifica_sle_tensioni
from .taglio_slu import verifica_taglio_slu

logger = logging.getLogger(__name__)

ESEMPIO_AUREO = {
    "b_mm": 600, "h_mm": 400, "tipo_acciaio": "RB500W", "tipo_cls": "C35/45", "copriferro_mm": 70,
    "n_ferri1": 5, "diametro_ferri1_mm": 20, "n_ferri2": 0, "diametro_ferri2_mm": 0,
    "diametro_staffe1_mm": 12, "passo_staffe1_mm": 115, "n_bracci_staffe1": 2,
    "diametro_staffe2_mm": 0, "n_bracci_staffe2": 0, "alpha_staffe_deg": 90,
    "ved_kN": 138, "med_slu_kNm": 318, "med_rara_kNm": 239, "med_qp_kNm": 200,
    "condizioni_ambientali": "Ordinarie", "combinazione": "Frequente", "sensibilita_armatura": "Poco sensibile",
    "classe_apertura_fessura": "w3", "classe_duttilita": "CDB", "mrc_kNm": 350, "lt_m": 8,
}


def _checks_armatura_longitudinale(armatura: ArmaturaLimitiOutput) -> tuple[Check, ...]:
    return (
        Check(
            name="Armatura minima tesa",
            passed=armatura.as_o_mm2 >= armatura.as_min_mm2,
            detail=f"As,o={armatura.as_o_mm2:.1f} mm² >= As,min={armatura.as_min_mm2:.1f} mm²",
            clause="NTC2018 §4.1.6.1.1",
            value=armatura.as_min_mm2, limit=armatura.as_o_mm2, unit="mm²",
        ),
        Check(
            name="Armatura massima tesa",
            passed=armatura.as_o_mm2 <= armatura.as_max_mm2,
            detail=f"As,o={armatura.as_o_mm2:.1f} mm² <= As,max={armatura.as_max_mm2:.1f} mm²",
            clause="NTC2018 §4.1.6.1.1",
            value=armatura.as_o_mm2, limit=armatura.as_max_mm2, unit="mm²",
        ),
    )


def _checks_armatura_trasversale(inputs: TraveRettangolareInput, armatura: ArmaturaLimitiOutput) -> tuple[Check, ...]:
    return (
        Check(
            name="Armatura minima a taglio (staffe)",
            passed=armatura.asw_per_m_mm2 >= armatura.ast_min_per_m_mm2,
            clause="NTC2018 §4.1.6.1.1",
            value=armatura.ast_min_per_m_mm2, limit=armatura.asw_per_m_mm2, unit="mm²/m",
        ),
        Check(
            name="Passo massimo staffe",
            passed=inputs.passo_staffe1_mm <= armatura.passo_max_staffe_mm,
            clause="NTC2018 §4.1.6.1.1",
        ),
    )


def _checks_armatura_sismica(armatura: ArmaturaLimitiOutput) -> tuple[Check, ...]:
    return (
        Check(
            name="Percentuale di armatura tesa minima sismica",
            passed=armatura.rho_tesa >= armatura.rho_min_sismico,
            detail=f"ρ={armatura.rho_tesa:.5f} >= ρmin={armatura.rho_min_sismico:.5f}",
            clause="NTC2018 §7.4.6.2.1",
        ),
        Check(
            name="Percentuale di armatura tesa massima sismica",
            passed=armatura.rho_tesa <= armatura.rho_max_sismico,
            detail=f"ρ={armatura.rho_tesa:.5f} <= ρmax={armatura.rho_max_sismico:.5f}",
            clause="NTC2018 §7.4.6.2.1",
        ),
        Check(
            name="Armatura compressa minima sismica",
            passed=armatura.as_comp_mm2 >= armatura.as_comp_min_sismico_mm2,
            detail=f"As'={armatura.as_comp_mm2:.1f} mm² >= As',min={armatura.as_comp_min_sismico_mm2:.1f} mm²",
            clause="NTC2018 §7.4.6.2.1",
        ),
    )


def _checks_armatura(inputs: TraveRettangolareInput, armatura: ArmaturaLimitiOutput) -> tuple[Check, ...]:
    return (
        _checks_armatura_longitudinale(armatura)
        + _checks_armatura_trasversale(inputs, armatura)
        + _checks_armatura_sismica(armatura)
    )


def _checks_flessione_taglio(
    inputs: TraveRettangolareInput, flessione: FlessioneOutput, taglio: TaglioOutput, dettagli: CapacityDesignOutput
) -> tuple[Check, ...]:
    return (
        Check(
            name="Resistenza a flessione",
            passed=flessione.mrd_kNm > inputs.med_slu_kNm,
            detail=f"MRd={flessione.mrd_kNm:.2f} kNm, MEd={inputs.med_slu_kNm:.2f} kNm",
            clause="NTC2018 §4.1.2.3.4.2",
            value=inputs.med_slu_kNm, limit=flessione.mrd_kNm, unit="kNm",
        ),
        Check(
            name="Duttilità sezione (acciaio snervato)",
            passed=flessione.acciaio_snervato,
            detail=f"εs={flessione.eps_s_permille:.2f}‰",
            clause="NTC2018 §4.1.2.1.2.2",
        ),
        Check(
            name="Resistenza a taglio",
            passed=taglio.vrd_kN > inputs.ved_kN,
            detail=f"VRd={taglio.vrd_kN:.2f} kN, VEd={inputs.ved_kN:.2f} kN",
            clause="NTC2018 §4.1.2.3.5.2",
            value=inputs.ved_kN, limit=taglio.vrd_kN, unit="kN",
        ),
        Check(
            name="Capacity design a taglio",
            passed=dettagli.ved_max_kN < taglio.vrd_kN,
            detail=f"VEd,max={dettagli.ved_max_kN:.2f} kN, VRd={taglio.vrd_kN:.2f} kN",
            clause="NTC2018 §7.4.4.1.1",
            value=dettagli.ved_max_kN, limit=taglio.vrd_kN, unit="kN",
        ),
    )


def _checks_sle_tensioni(sle_tensioni: SleTensioniOutput) -> tuple[Check, ...]:
    return (
        Check(
            name="Tensione di compressione nel calcestruzzo, combinazione rara",
            passed=sle_tensioni.sigma_c_rara_MPa < sle_tensioni.limite_sigma_c_rara_MPa,
            detail=f"σc={sle_tensioni.sigma_c_rara_MPa:.2f} MPa < 0.60·fck={sle_tensioni.limite_sigma_c_rara_MPa:.2f} MPa",
            clause="NTC2018 §4.1.2.2.5",
            value=sle_tensioni.sigma_c_rara_MPa, limit=sle_tensioni.limite_sigma_c_rara_MPa, unit="MPa",
        ),
        Check(
            name="Tensione di trazione nell'acciaio, combinazione rara",
            passed=sle_tensioni.sigma_s_rara_MPa < sle_tensioni.limite_sigma_s_MPa,
            detail=f"σs={sle_tensioni.sigma_s_rara_MPa:.2f} MPa < {sle_tensioni.limite_sigma_s_MPa:.2f} MPa",
            clause="NTC2018 §4.1.2.2.5",
            value=sle_tensioni.sigma_s_rara_MPa, limit=sle_tensioni.limite_sigma_s_MPa, unit="MPa",
        ),
        Check(
            name="Tensione di compressione nel calcestruzzo, combinazione quasi permanente",
            passed=sle_tensioni.sigma_c_qp_MPa < sle_tensioni.limite_sigma_c_qp_MPa,
            detail=f"σc,qp={sle_tensioni.sigma_c_qp_MPa:.2f} MPa < 0.45·fck={sle_tensioni.limite_sigma_c_qp_MPa:.2f} MPa",
            clause="NTC2018 §4.1.2.2.5",
            value=sle_tensioni.sigma_c_qp_MPa, limit=sle_tensioni.limite_sigma_c_qp_MPa, unit="MPa",
        ),
    )


def _checks_sle_fessurazione(
    sle_tensioni: SleTensioniOutput, fessurazione: FessurazioneOutput, inputs: TraveRettangolareInput
) -> tuple[Check, ...]:
    checks = (
        Check(
            name="Controllo indiretto di fessurazione",
            passed=sle_tensioni.sigma_s_combinazione_MPa < fessurazione.sigma_limite_MPa,
            detail=f"σs={sle_tensioni.sigma_s_combinazione_MPa:.2f} MPa < σs,limite={fessurazione.sigma_limite_MPa:.2f} MPa",
            clause="NTC2018 §4.1.2.2.4 / Circ. C4.1.2.2.4.5",
            value=sle_tensioni.sigma_s_combinazione_MPa, limit=fessurazione.sigma_limite_MPa, unit="MPa",
        ),
    )
    if fessurazione.classe_normativa is None:
        return checks
    return (
        *checks,
        Check(
            name="Classe di apertura fessura conforme a Tab. 4.1.IV",
            passed=inputs.classe_apertura_fessura == fessurazione.classe_normativa,
            detail=f"scelta={inputs.classe_apertura_fessura}, richiesta da normativa={fessurazione.classe_normativa}",
            clause="NTC2018 Tab. 4.1.IV",
        ),
    )


def _checks_sle(sle_tensioni: SleTensioniOutput, fessurazione: FessurazioneOutput, inputs: TraveRettangolareInput) -> tuple[Check, ...]:
    return _checks_sle_tensioni(sle_tensioni) + _checks_sle_fessurazione(sle_tensioni, fessurazione, inputs)


def _checks(
    inputs: TraveRettangolareInput,
    armatura: ArmaturaLimitiOutput,
    flessione: FlessioneOutput,
    taglio: TaglioOutput,
    sle_tensioni: SleTensioniOutput,
    fessurazione: FessurazioneOutput,
    dettagli: CapacityDesignOutput,
) -> tuple[Check, ...]:
    return (
        _checks_armatura(inputs, armatura)
        + _checks_flessione_taglio(inputs, flessione, taglio, dettagli)
        + _checks_sle(sle_tensioni, fessurazione, inputs)
    )


def _armatura(inputs: TraveRettangolareInput, d_mm: float, z_mm: float, fck_MPa: float, fctm_MPa: float, fyk_MPa: float, ftk_MPa: float) -> ArmaturaLimitiOutput:
    return armatura_minima_massima(
        b_mm=inputs.b_mm, h_mm=inputs.h_mm, d_mm=d_mm, z_mm=z_mm,
        n_ferri1=inputs.n_ferri1, diametro_ferri1_mm=inputs.diametro_ferri1_mm,
        n_ferri2=inputs.n_ferri2, diametro_ferri2_mm=inputs.diametro_ferri2_mm,
        diametro_staffe1_mm=inputs.diametro_staffe1_mm, n_bracci_staffe1=inputs.n_bracci_staffe1,
        passo_staffe1_mm=inputs.passo_staffe1_mm, diametro_staffe2_mm=inputs.diametro_staffe2_mm,
        n_bracci_staffe2=inputs.n_bracci_staffe2, fck_MPa=fck_MPa, fctm_MPa=fctm_MPa, fyk_MPa=fyk_MPa, ftk_MPa=ftk_MPa,
        classe_duttilita=inputs.classe_duttilita, legacy_compat=inputs.legacy_compat,
    )


def _sle(inputs: TraveRettangolareInput, d_mm: float, as_o_mm2: float, fck_MPa: float, fyk_MPa: float) -> tuple[SleTensioniOutput, FessurazioneOutput]:
    sle_tensioni = verifica_sle_tensioni(
        b_mm=inputs.b_mm, d_mm=d_mm, as_o_mm2=as_o_mm2, med_rara_kNm=inputs.med_rara_kNm, med_qp_kNm=inputs.med_qp_kNm,
        fck_MPa=fck_MPa, fyk_MPa=fyk_MPa, combinazione=inputs.combinazione, legacy_compat=inputs.legacy_compat,
    )
    fessurazione = verifica_fessurazione(
        sigma_s_MPa=sle_tensioni.sigma_s_combinazione_MPa,
        diametro_ferri1_mm=inputs.diametro_ferri1_mm, diametro_ferri2_mm=inputs.diametro_ferri2_mm,
        condizioni_ambientali=inputs.condizioni_ambientali, combinazione=inputs.combinazione,
        sensibilita_armatura=inputs.sensibilita_armatura, classe_apertura_fessura=inputs.classe_apertura_fessura,
        legacy_compat=inputs.legacy_compat,
    )
    return sle_tensioni, fessurazione


def _dettagli(inputs: TraveRettangolareInput, d_mm: float, mrb_kNm: float) -> CapacityDesignOutput:
    return dettagli_costruttivi(
        h_mm=inputs.h_mm, d_mm=d_mm, classe=inputs.classe_duttilita,
        diametro_staffe1_mm=inputs.diametro_staffe1_mm, diametro_staffe2_mm=inputs.diametro_staffe2_mm,
        n_bracci_staffe2=inputs.n_bracci_staffe2, diametro_ferri1_mm=inputs.diametro_ferri1_mm, n_ferri1=inputs.n_ferri1,
        diametro_ferri2_mm=inputs.diametro_ferri2_mm, n_ferri2=inputs.n_ferri2,
        mrb_kNm=mrb_kNm, mrc_kNm=inputs.mrc_kNm, lt_m=inputs.lt_m, v_gravita_kN=inputs.v_gravita_kN,
        legacy_compat=inputs.legacy_compat,
    )


def run(inputs: TraveRettangolareInput) -> Report[TraveRettangolareOutput]:
    materiali = materiali_trave(inputs.tipo_cls, inputs.tipo_acciaio, legacy_compat=inputs.legacy_compat)
    cls, acciaio = materiali.calcestruzzo, materiali.acciaio
    d_mm = altezza_utile_mm(inputs.h_mm, inputs.copriferro_mm)
    z_mm = braccio_leva_mm(d_mm)

    armatura = _armatura(inputs, d_mm, z_mm, cls.fck_MPa, cls.fctm_MPa, acciaio.fyk_MPa, acciaio.ftk_MPa)
    flessione = verifica_flessione_slu(
        as_o_mm2=armatura.as_o_mm2, fyd_MPa=acciaio.fyd_MPa, fcd_MPa=cls.fcd_MPa, b_mm=inputs.b_mm, d_mm=d_mm,
        med_slu_kNm=inputs.med_slu_kNm, es_MPa=acciaio.es_MPa, legacy_compat=inputs.legacy_compat,
    )
    taglio = verifica_taglio_slu(
        b_mm=inputs.b_mm, z_mm=z_mm, asw_per_m_mm2=armatura.asw_per_m_mm2, fyd_MPa=acciaio.fyd_MPa, fcd_MPa=cls.fcd_MPa,
        alpha_staffe_deg=inputs.alpha_staffe_deg,
    )
    sle_tensioni, fessurazione = _sle(inputs, d_mm, armatura.as_o_mm2, cls.fck_MPa, acciaio.fyk_MPa)
    dettagli = _dettagli(inputs, d_mm, flessione.mrd_kNm)

    try:
        schizzo = disegna_schizzo(inputs, flessione)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per ca-trave-rettangolare")
        schizzo = None

    data = TraveRettangolareOutput(
        materiali=materiali, armatura=armatura, flessione=flessione, taglio=taglio,
        sle_tensioni=sle_tensioni, fessurazione=fessurazione, dettagli_costruttivi=dettagli,
        schizzo=schizzo,
    )
    checks = _checks(inputs, armatura, flessione, taglio, sle_tensioni, fessurazione, dettagli)
    return success(data, inputs, checks=checks, warnings=_avvisi(inputs), avvisi_campi={AVVISO_TAGLIO_GRAVITAZIONALE: "v_gravita_kN"})


AVVISO_TAGLIO_GRAVITAZIONALE = (
    "Gerarchia delle resistenze a taglio: il contributo dei carichi gravitazionali (V_g, NTC2018 §7.4.4.1.1) "
    "non è stato inserito; il taglio di progetto considera i soli momenti resistenti di estremità."
)


def _avvisi(inputs: TraveRettangolareInput) -> tuple[str, ...]:
    if inputs.legacy_compat or inputs.v_gravita_kN > 0.0:
        return ()
    return (AVVISO_TAGLIO_GRAVITAZIONALE,)


TOOLS = (
    Tool(
        name="ca-trave-rettangolare",
        title="Trave in c.a. a sezione rettangolare — progetto e verifica",
        group="Calcestruzzo armato / Travi",
        norm="NTC2018 §4.1.6.1.1, §4.1.2.3.4.2, §4.1.2.3.5.2, §4.1.2.2.5, §4.1.2.2.4, §7.4.4.1.1, §7.4.6",
        input_model=TraveRettangolareInput,
        output_model=TraveRettangolareOutput,
        run=run,
        example=ESEMPIO_AUREO,
        summary="Progetta e verifica una trave in c.a. a sezione rettangolare a flessione, taglio e stato limite di esercizio.",
        relazione=relazione_trave_rettangolare,
    ),
)
