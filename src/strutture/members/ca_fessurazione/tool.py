"""Tool registration for the three `ca_fessurazione` sheets: `ca-sle-limitazione-tensioni`
(NTC2018 §4.1.2.2.5), `ca-apertura-fessure` (Circ. 2019 §C4.1.2.2.4.5) and
`ca-apertura-fessure-semplificata` (NTC2018 §4.1.2.2.4)."""
from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.rebar_catalog import bars_area, sigma_limit_by_diameter
from strutture.shared.report import CalcError, Check, Report, success
from strutture.shared.tables import KeyNotFound
from strutture.shared.tool import Tool

from .ampiezza_fessura import FATTORE_AMPIEZZA_FESSURA, apertura_fessure_wk_mm, utilizzo_apertura_fessure
from .classe_apertura_normativa import (
    CLASSE_FALLBACK_FRE,
    CLASSE_FALLBACK_QPE,
    classe_normativa_fre,
    classe_normativa_qpe,
)
from .coefficienti_fessurazione import (
    k1_per_tipo_barre,
    k2_per_sollecitazione,
    kt_per_durata_carico,
    wlim_mm_per_classe,
)
from .deformazione_media import deformazione_media_armatura
from .geometria_fessurazione import (
    altezza_efficace_mm,
    altezza_utile_mm,
    area_efficace_mm2,
    diametro_equivalente_mm,
    rapporto_armatura_efficace,
)
from .limitazione_tensioni import fck_da_rck, sigma_c_max_qpe_MPa, sigma_c_max_rar_MPa, sigma_s_max_rar_MPa
from .models import (
    AperturaFessureInput,
    AperturaFessureOutput,
    AperturaFessureSempInput,
    AperturaFessureSempOutput,
    CoefficientiFessurazioneOutput,
    GeometriaFessurazioneOutput,
    LimitazioneTensioniInput,
    LimitazioneTensioniOutput,
    MaterialeFessurazioneOutput,
    RisultatoFessurazioneOutput,
    VerificaSemplificataSezione,
    VerificaTensioneSezione,
)
from .sezioni import SEZIONI
from .spaziatura_fessure import (
    delta_sm_c4_1_7_mm,
    delta_sm_c4_1_10_mm,
    delta_sm_effettivo_mm,
    ramo_spaziatura,
    spaziatura_limite_mm,
)
from .verifica import utilizzo, verificato

CLAUSE_LIMITAZIONE_TENSIONI = "NTC2018 §4.1.2.2.5"
CLAUSE_APERTURA_FESSURE = "Circ. 2019 §C4.1.2.2.4.5"
CLAUSE_APERTURA_FESSURE_SEMP = "NTC2018 §4.1.2.2.4"

ESEMPIO_LIMITAZIONE_TENSIONI = {
    "rck_MPa": 45, "fyk_MPa": 450,
    "sigma_c_rar_1_MPa": 4.5, "sigma_c_qpe_1_MPa": 4.5, "sigma_s_rar_1_MPa": 255.8,
    "sigma_c_rar_2_MPa": 10, "sigma_c_qpe_2_MPa": 5.3, "sigma_s_rar_2_MPa": 274,
    "sigma_c_rar_3_MPa": 6, "sigma_c_qpe_3_MPa": 6, "sigma_s_rar_3_MPa": 237,
}
ESEMPIO_APERTURA_FESSURE = {
    "classe_calcestruzzo": "C28/35", "tipo_barre": "barre aderenza migliorata",
    "tipo_sollecitazione": "caso di flessione", "durata_carico": "lunga durata",
    "classe_fessurazione": "w3 (0.40 mm)", "interferro_mm": 200, "sigma_s_MPa": 286,
    "es_MPa": 210000, "h_mm": 250, "x_mm": 75.84, "b_mm": 1000,
    "n1": 5, "phi1_mm": 20, "n2": 0, "phi2_mm": 0, "copriferro_mm": 35,
    "k3": 3.4, "k4": 0.425,
}
ESEMPIO_APERTURA_FESSURE_SEMP = {
    "diametro_mm_1": 16, "sigma_fre_MPa_1": 231, "sigma_qpe_MPa_1": 218,
    "diametro_mm_2": 16, "sigma_fre_MPa_2": 206, "sigma_qpe_MPa_2": 233,
    "diametro_mm_3": 16, "sigma_fre_MPa_3": 180, "sigma_qpe_MPa_3": 171,
}

# -----------------------------------------------------------------------------------------------
# Tool 1: ca-sle-limitazione-tensioni
# -----------------------------------------------------------------------------------------------


def _verifica_tensione_sezione(
    titolo: str, sottotitolo: str, fck_MPa: float, fyk_MPa: float, sigma_c_rar: float, sigma_c_qpe: float, sigma_s_rar: float
) -> VerificaTensioneSezione:
    limite_c_rar = sigma_c_max_rar_MPa(fck_MPa)
    limite_c_qpe = sigma_c_max_qpe_MPa(fck_MPa)
    limite_s_rar = sigma_s_max_rar_MPa(fyk_MPa)
    return VerificaTensioneSezione(
        titolo=titolo,
        sottotitolo=sottotitolo,
        sigma_c_max_rar_MPa=limite_c_rar,
        sigma_c_rar_MPa=sigma_c_rar,
        utilizzo_c_rar=utilizzo(sigma_c_rar, limite_c_rar),
        verificato_c_rar=verificato(sigma_c_rar, limite_c_rar),
        sigma_c_max_qpe_MPa=limite_c_qpe,
        sigma_c_qpe_MPa=sigma_c_qpe,
        utilizzo_c_qpe=utilizzo(sigma_c_qpe, limite_c_qpe),
        verificato_c_qpe=verificato(sigma_c_qpe, limite_c_qpe),
        sigma_s_max_rar_MPa=limite_s_rar,
        sigma_s_rar_MPa=sigma_s_rar,
        utilizzo_s_rar=utilizzo(sigma_s_rar, limite_s_rar),
        verificato_s_rar=verificato(sigma_s_rar, limite_s_rar),
    )


def _checks_sezione_tensioni(indice: int, sezione: VerificaTensioneSezione) -> tuple[Check, ...]:
    return tuple(
        Check(
            name=f"{nome_campo} sezione {indice + 1}",
            passed=getattr(sezione, f"verificato_{suffisso}"),
            detail=f"utilizzo {getattr(sezione, f'utilizzo_{suffisso}'):.3f}",
            clause=CLAUSE_LIMITAZIONE_TENSIONI,
            value=getattr(sezione, f"sigma_{agente}_MPa"), limit=getattr(sezione, f"{limite}_MPa"), unit="MPa",
        )
        for nome_campo, suffisso, agente, limite in (
            ("σc RAR", "c_rar", "c_rar", "sigma_c_max_rar"),
            ("σc QPE", "c_qpe", "c_qpe", "sigma_c_max_qpe"),
            ("σs RAR", "s_rar", "s_rar", "sigma_s_max_rar"),
        )
    )


def run_limitazione_tensioni(inputs: LimitazioneTensioniInput) -> Report[LimitazioneTensioniOutput]:
    fck_MPa = fck_da_rck(inputs.rck_MPa)
    valori_sezioni = (
        (inputs.sigma_c_rar_1_MPa, inputs.sigma_c_qpe_1_MPa, inputs.sigma_s_rar_1_MPa),
        (inputs.sigma_c_rar_2_MPa, inputs.sigma_c_qpe_2_MPa, inputs.sigma_s_rar_2_MPa),
        (inputs.sigma_c_rar_3_MPa, inputs.sigma_c_qpe_3_MPa, inputs.sigma_s_rar_3_MPa),
    )
    sezioni = tuple(
        _verifica_tensione_sezione(titolo, sottotitolo, fck_MPa, inputs.fyk_MPa, *valori)
        for (titolo, sottotitolo), valori in zip(SEZIONI, valori_sezioni, strict=True)
    )
    checks = tuple(check for indice, sezione in enumerate(sezioni) for check in _checks_sezione_tensioni(indice, sezione))
    data = LimitazioneTensioniOutput(fck_MPa=fck_MPa, sezioni=sezioni)
    return success(data, inputs, checks=checks)


# -----------------------------------------------------------------------------------------------
# Tool 2: ca-apertura-fessure
# -----------------------------------------------------------------------------------------------


def _geometria_apertura_fessure(inputs: AperturaFessureInput) -> GeometriaFessurazioneOutput:
    d_mm = altezza_utile_mm(inputs.h_mm, inputs.phi1_mm, inputs.copriferro_mm)
    hc_eff_mm = altezza_efficace_mm(inputs.h_mm, d_mm, inputs.x_mm)
    ac_eff_mm2 = area_efficace_mm2(hc_eff_mm, inputs.b_mm)
    as_mm2 = bars_area(inputs.n1, inputs.phi1_mm) + (bars_area(inputs.n2, inputs.phi2_mm) if inputs.n2 > 0 else 0.0)
    phi_eq_mm = diametro_equivalente_mm(inputs.n1, inputs.phi1_mm, inputs.n2, inputs.phi2_mm)
    rho_eff = rapporto_armatura_efficace(as_mm2, ac_eff_mm2)
    return GeometriaFessurazioneOutput(
        d_mm=d_mm, hc_eff_mm=hc_eff_mm, ac_eff_mm2=ac_eff_mm2, as_mm2=as_mm2, phi_eq_mm=phi_eq_mm, rho_eff=rho_eff
    )


def _coefficienti_apertura_fessure(inputs: AperturaFessureInput) -> CoefficientiFessurazioneOutput:
    return CoefficientiFessurazioneOutput(
        k1=k1_per_tipo_barre(inputs.tipo_barre),
        k2=k2_per_sollecitazione(inputs.tipo_sollecitazione),
        kt=kt_per_durata_carico(inputs.durata_carico),
    )


def _fessurazione_apertura_fessure(
    inputs: AperturaFessureInput,
    geometria: GeometriaFessurazioneOutput,
    coefficienti: CoefficientiFessurazioneOutput,
    fctm_MPa: float,
    alpha_e: float,
) -> RisultatoFessurazioneOutput:
    slim_mm = spaziatura_limite_mm(inputs.copriferro_mm, geometria.phi_eq_mm)
    delta_c4_1_7_mm = delta_sm_c4_1_7_mm(
        inputs.k3, inputs.copriferro_mm, coefficienti.k1, coefficienti.k2, inputs.k4, geometria.phi_eq_mm, geometria.rho_eff
    )
    delta_c4_1_10_mm = delta_sm_c4_1_10_mm(inputs.h_mm, inputs.x_mm, legacy_compat=inputs.legacy_compat)
    ramo = ramo_spaziatura(inputs.interferro_mm, slim_mm)
    delta_sm_mm = delta_sm_effettivo_mm(ramo, delta_c4_1_7_mm, delta_c4_1_10_mm)

    epsilon_sm = deformazione_media_armatura(
        inputs.sigma_s_MPa, coefficienti.kt, fctm_MPa, geometria.rho_eff, alpha_e, inputs.es_MPa
    )
    wk_mm = apertura_fessure_wk_mm(FATTORE_AMPIEZZA_FESSURA, epsilon_sm, delta_sm_mm)
    wlim_mm = wlim_mm_per_classe(inputs.classe_fessurazione)

    return RisultatoFessurazioneOutput(
        slim_mm=slim_mm,
        ramo=ramo,
        delta_sm_mm=delta_sm_mm,
        epsilon_sm=epsilon_sm,
        wk_mm=wk_mm,
        wlim_mm=wlim_mm,
        utilizzo=utilizzo_apertura_fessure(wk_mm, wlim_mm),
        verificato=verificato(wk_mm, wlim_mm),
    )


def run_apertura_fessure(inputs: AperturaFessureInput) -> Report[AperturaFessureOutput]:
    concrete = concrete_properties(inputs.classe_calcestruzzo, legacy_compat=inputs.legacy_compat)
    alpha_e = inputs.es_MPa / concrete.ecm_MPa

    geometria = _geometria_apertura_fessure(inputs)
    materiale = MaterialeFessurazioneOutput(ecm_MPa=concrete.ecm_MPa, fctm_MPa=concrete.fctm_MPa, alpha_e=alpha_e)
    coefficienti = _coefficienti_apertura_fessure(inputs)
    fessurazione = _fessurazione_apertura_fessure(inputs, geometria, coefficienti, concrete.fctm_MPa, alpha_e)

    data = AperturaFessureOutput(geometria=geometria, materiale=materiale, coefficienti=coefficienti, fessurazione=fessurazione)
    check = Check(
        name="apertura fessure",
        passed=fessurazione.verificato,
        detail=f"wk={fessurazione.wk_mm:.4f} mm / wlim={fessurazione.wlim_mm} mm",
        clause=CLAUSE_APERTURA_FESSURE,
        value=fessurazione.wk_mm, limit=fessurazione.wlim_mm, unit="mm",
    )
    return success(data, inputs, checks=(check,))


# -----------------------------------------------------------------------------------------------
# Tool 3: ca-apertura-fessure-semplificata
# -----------------------------------------------------------------------------------------------


def _classi_apertura_semplificata(
    condizioni_ambientali: str, sensibilita_armatura: str, *, legacy_compat: bool
) -> tuple[str, str]:
    """Classe (w1/w2/w3) applicata per FRE/QPE: fissa (w3/w2) sotto `legacy_compat=True`,
    risolta da Tab. 4.1.IV altrimenti — vedi `classe_apertura_normativa`."""
    if legacy_compat:
        return CLASSE_FALLBACK_FRE, CLASSE_FALLBACK_QPE
    classe_fre = classe_normativa_fre(condizioni_ambientali, sensibilita_armatura)
    classe_qpe = classe_normativa_qpe(condizioni_ambientali, sensibilita_armatura)
    if classe_fre is None or classe_qpe is None:
        raise CalcError(
            "per l'esposizione/sensibilità dell'armatura scelte la normativa richiede una "
            "verifica a decompressione anziché un limite di ampiezza di fessura (Tab. 4.1.IV): "
            "non supportata da questo strumento"
        )
    return classe_fre, classe_qpe


def _verifica_semplificata_sezione(
    titolo: str,
    sottotitolo: str,
    diametro_mm: float,
    sigma_fre_MPa: float,
    sigma_qpe_MPa: float,
    *,
    condizioni_ambientali: str,
    sensibilita_armatura: str,
    legacy_compat: bool,
) -> VerificaSemplificataSezione:
    classe_fre, classe_qpe = _classi_apertura_semplificata(condizioni_ambientali, sensibilita_armatura, legacy_compat=legacy_compat)
    limite_fre = sigma_limit_by_diameter(diametro_mm, classe_fre, legacy_compat=legacy_compat)
    limite_qpe = sigma_limit_by_diameter(diametro_mm, classe_qpe, legacy_compat=legacy_compat)
    return VerificaSemplificataSezione(
        titolo=titolo,
        sottotitolo=sottotitolo,
        diametro_mm=diametro_mm,
        classe_fre=classe_fre,
        sigma_lim_fre_MPa=limite_fre,
        sigma_fre_MPa=sigma_fre_MPa,
        utilizzo_fre=utilizzo(sigma_fre_MPa, limite_fre),
        verificato_fre=verificato(sigma_fre_MPa, limite_fre),
        classe_qpe=classe_qpe,
        sigma_lim_qpe_MPa=limite_qpe,
        sigma_qpe_MPa=sigma_qpe_MPa,
        utilizzo_qpe=utilizzo(sigma_qpe_MPa, limite_qpe),
        verificato_qpe=verificato(sigma_qpe_MPa, limite_qpe),
    )


def _checks_sezione_semp(indice: int, sezione: VerificaSemplificataSezione) -> tuple[Check, ...]:
    return tuple(
        Check(
            name=f"σs {combinazione} sezione {indice + 1}",
            passed=getattr(sezione, f"verificato_{suffisso}"),
            detail=f"utilizzo {getattr(sezione, f'utilizzo_{suffisso}'):.3f}",
            clause=CLAUSE_APERTURA_FESSURE_SEMP,
            value=getattr(sezione, f"sigma_{suffisso}_MPa"), limit=getattr(sezione, f"sigma_lim_{suffisso}_MPa"), unit="MPa",
        )
        for combinazione, suffisso in (("frequente", "fre"), ("quasi-permanente", "qpe"))
    )


def run_apertura_fessure_semplificata(inputs: AperturaFessureSempInput) -> Report[AperturaFessureSempOutput]:
    valori_sezioni = (
        (inputs.diametro_mm_1, inputs.sigma_fre_MPa_1, inputs.sigma_qpe_MPa_1),
        (inputs.diametro_mm_2, inputs.sigma_fre_MPa_2, inputs.sigma_qpe_MPa_2),
        (inputs.diametro_mm_3, inputs.sigma_fre_MPa_3, inputs.sigma_qpe_MPa_3),
    )
    try:
        sezioni = tuple(
            _verifica_semplificata_sezione(
                titolo,
                sottotitolo,
                *valori,
                condizioni_ambientali=inputs.condizioni_ambientali,
                sensibilita_armatura=inputs.sensibilita_armatura,
                legacy_compat=inputs.legacy_compat,
            )
            for (titolo, sottotitolo), valori in zip(SEZIONI, valori_sezioni, strict=True)
        )
    except KeyNotFound as error:
        raise CalcError(f"diametro non presente in Tab. C4.1.II: {error}") from error
    checks = tuple(check for indice, sezione in enumerate(sezioni) for check in _checks_sezione_semp(indice, sezione))
    return success(AperturaFessureSempOutput(sezioni=sezioni), inputs, checks=checks)


TOOLS = (
    Tool(
        name="ca-sle-limitazione-tensioni",
        title="Verifica SLE — limitazione delle tensioni",
        group="Calcestruzzo armato / Fessurazione",
        norm=CLAUSE_LIMITAZIONE_TENSIONI,
        input_model=LimitazioneTensioniInput,
        output_model=LimitazioneTensioniOutput,
        run=run_limitazione_tensioni,
        example=ESEMPIO_LIMITAZIONE_TENSIONI,
        summary="Verifica, per tre sezioni, che le tensioni di esercizio nel calcestruzzo e nell'acciaio nelle combinazioni rara e quasi permanente rispettino i limiti di normativa in funzione delle resistenze caratteristiche dei materiali.",
    ),
    Tool(
        name="ca-apertura-fessure",
        title="Verifica SLE — apertura delle fessure",
        group="Calcestruzzo armato / Fessurazione",
        norm=CLAUSE_APERTURA_FESSURE,
        input_model=AperturaFessureInput,
        output_model=AperturaFessureOutput,
        run=run_apertura_fessure,
        example=ESEMPIO_APERTURA_FESSURE,
        summary="Calcola l'ampiezza caratteristica delle fessure di una sezione in cemento armato a partire da geometria, armatura e tensione nell'acciaio, verificandola rispetto al limite della classe di esposizione scelta.",
    ),
    Tool(
        name="ca-apertura-fessure-semplificata",
        title="Verifica SLE — apertura delle fessure (semplificata)",
        group="Calcestruzzo armato / Fessurazione",
        norm=CLAUSE_APERTURA_FESSURE_SEMP,
        input_model=AperturaFessureSempInput,
        output_model=AperturaFessureSempOutput,
        run=run_apertura_fessure_semplificata,
        example=ESEMPIO_APERTURA_FESSURE_SEMP,
        summary="Verifica in forma semplificata, per tre sezioni e in funzione del diametro delle barre, che le tensioni nell'acciaio nelle combinazioni frequente e quasi permanente rispettino i limiti tabellari di apertura delle fessure.",
    ),
)
