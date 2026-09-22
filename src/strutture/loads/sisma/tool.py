"""Tool registration: sisma-vita-riferimento, sisma-parametri-sito, sisma-fattori-struttura,
sisma-spettro. NTC2018 §3.2. Each `run` composes `strutture.shared.ntc_site_seismic` (the single
implementation of the site-hazard chain) with this package's own small steps; no formula is
reimplemented here.
"""
from strutture.shared.comuni import AmbiguousComuneError, KeyNotFound
from strutture.shared.ntc_site_seismic import (
    amplificazione,
    coefficiente_uso,
    periodi_ritorno,
    periodi_spettro,
    vita_riferimento,
)
from strutture.shared.report import CalcError, Report, success
from strutture.shared.tool import Tool

from .campionamento import campiona_periodi
from .completo import run_completo
from .comune_info import risolvi_comune
from .eta_verticale import eta_verticale
from .fattore_struttura_q import fattore_struttura_q
from .kr_regolarita import kr_regolare_altezza
from .models import (
    ComuneInfo,
    PuntoSpettro,
    SismaFattoriStrutturaInput,
    SismaFattoriStrutturaOutput,
    SismaParametriSitoInput,
    SismaParametriSitoOutput,
    SismaSpettroInput,
    SismaSpettroOutput,
    SismaVitaRiferimentoInput,
    SismaVitaRiferimentoOutput,
)
from .models_completo import SismaCompletoInput, SismaCompletoOutput
from .relazione import (
    relazione_completo,
    relazione_fattori_struttura,
    relazione_parametri_sito,
    relazione_spettro,
    relazione_vita_riferimento,
)
from .smorzamento import smorzamento_eta
from .spettro_elastico import se_elastico
from .spettro_progetto import valore_spettro
from .stato_limite import is_stato_limite_uls
from .validazione_sito import valida_parametri_sito


def run_vita_riferimento(inputs: SismaVitaRiferimentoInput) -> Report[SismaVitaRiferimentoOutput]:
    comune_info = None
    if inputs.comune:
        try:
            match = risolvi_comune(inputs.comune, inputs.provincia)
        except (KeyNotFound, AmbiguousComuneError) as error:
            raise CalcError(f"Comune non trovato: {error}") from error
        comune_info = ComuneInfo(provincia=match.provincia, regione=match.regione, zona_sismica=match.zona_sismica)

    cu = coefficiente_uso(inputs.classe_uso)
    vita = vita_riferimento(inputs.vn_anni, cu, legacy_compat=inputs.legacy_compat)
    periodi = periodi_ritorno(vita.vr)
    data = SismaVitaRiferimentoOutput(comune_info=comune_info, vita=vita, periodi_ritorno=periodi)
    return success(data, inputs)


def run_parametri_sito(inputs: SismaParametriSitoInput) -> Report[SismaParametriSitoOutput]:
    valida_parametri_sito(inputs.ag_g, inputs.f0, inputs.tc_star_s)
    amp = amplificazione(
        inputs.categoria_sottosuolo,
        inputs.categoria_topografica,
        inputs.tc_star_s,
        inputs.f0,
        inputs.ag_g,
        legacy_compat=inputs.legacy_compat,
    )
    periodi = periodi_spettro(amp.cc, inputs.tc_star_s, inputs.ag_g)
    data = SismaParametriSitoOutput(amplificazione=amp, periodi=periodi)
    return success(data, inputs)


def run_fattori_struttura(inputs: SismaFattoriStrutturaInput) -> Report[SismaFattoriStrutturaOutput]:
    is_uls = is_stato_limite_uls(inputs.stato_limite)
    eta = smorzamento_eta(inputs.xi_pct)
    kr = kr_regolare_altezza(inputs.regolare_altezza)
    q = fattore_struttura_q(inputs.q0, kr, is_uls=is_uls)
    eta_vert = eta_verticale(inputs.xi_pct, inputs.qv, legacy_compat=inputs.legacy_compat)
    data = SismaFattoriStrutturaOutput(eta=eta, q=q, eta_vert=eta_vert, q_vert=inputs.qv)
    return success(data, inputs)


def _punto_spettro(t_s: float, inputs: SismaSpettroInput, *, is_uls: bool) -> PuntoSpettro:
    se_g = se_elastico(
        t_s, inputs.tb_s, inputs.tc_s, inputs.td_s, inputs.ag_g, inputs.s, inputs.f0, inputs.eta, legacy_compat=inputs.legacy_compat
    )
    sd_g = valore_spettro(
        se_g,
        inputs.q,
        t_s,
        is_uls=is_uls,
        ag_g=inputs.ag_g,
        s=inputs.s,
        f0=inputs.f0,
        tb_s=inputs.tb_s,
        eta=inputs.eta,
        legacy_compat=inputs.legacy_compat,
    )
    return PuntoSpettro(t_s=t_s, se_g=se_g, sd_g=sd_g)


def run_spettro(inputs: SismaSpettroInput) -> Report[SismaSpettroOutput]:
    if inputs.t_end_s <= inputs.t_start_s:
        raise CalcError(f"il periodo finale ({inputs.t_end_s} s) deve essere maggiore di quello iniziale ({inputs.t_start_s} s)")
    if not (inputs.tb_s < inputs.tc_s < inputs.td_s):
        raise CalcError(f"i periodi caratteristici devono rispettare TB < TC < TD (ricevuto TB={inputs.tb_s}, TC={inputs.tc_s}, TD={inputs.td_s})")

    is_uls = is_stato_limite_uls(inputs.stato_limite)
    t_values = campiona_periodi(inputs.t_start_s, inputs.t_end_s, inputs.step_s)
    punti = tuple(_punto_spettro(t_s, inputs, is_uls=is_uls) for t_s in t_values)
    data = SismaSpettroOutput(punti=punti)
    return success(data, inputs)


TOOLS = (
    Tool(
        name="sisma-vita-riferimento",
        title="Sisma — vita di riferimento e periodi di ritorno",
        group="Carichi / Sisma",
        norm="NTC2018 §3.2.1, §2.4.3",
        input_model=SismaVitaRiferimentoInput,
        output_model=SismaVitaRiferimentoOutput,
        run=run_vita_riferimento,
        example={"comune": "Brembate", "vn_anni": 50, "classe_uso": "II"},
        summary="Calcola la vita di riferimento e i periodi di ritorno dell'azione sismica a partire da vita nominale e classe d'uso, individuando opzionalmente comune e zona sismica.",
        relazione=relazione_vita_riferimento,
    ),
    Tool(
        name="sisma-parametri-sito",
        title="Sisma — parametri di sito e amplificazione",
        group="Carichi / Sisma",
        norm="NTC2018 §3.2.2, §3.2.3.2.1",
        input_model=SismaParametriSitoInput,
        output_model=SismaParametriSitoOutput,
        run=run_parametri_sito,
        example={
            "categoria_sottosuolo": "B",
            "categoria_topografica": "T1",
            "tc_star_s": 0.272,
            "f0": 2.436,
            "ag_g": 0.098,
        },
        summary="Determina i coefficienti di amplificazione stratigrafica e topografica del sito e i periodi caratteristici dello spettro di risposta a partire dalla categoria di sottosuolo, dalla categoria topografica e dai parametri di pericolosità sismica di base.",
        relazione=relazione_parametri_sito,
    ),
    Tool(
        name="sisma-fattori-struttura",
        title="Sisma — fattori di struttura",
        group="Carichi / Sisma",
        norm="NTC2018 §3.2.3.5, §7.3.1, §7.3.3.2",
        input_model=SismaFattoriStrutturaInput,
        output_model=SismaFattoriStrutturaOutput,
        run=run_fattori_struttura,
        example={"xi_pct": 5, "q0": 1.5, "regolare_altezza": "SI", "stato_limite": "SLV", "qv": 1.5},
        summary="Calcola il fattore di smorzamento e i fattori di struttura orizzontale e verticale dell'edificio a partire da smorzamento viscoso, regolarità in altezza e fattori di struttura di base.",
        relazione=relazione_fattori_struttura,
    ),
    Tool(
        name="sisma-spettro",
        title="Sisma — spettro di risposta",
        group="Carichi / Sisma",
        norm="NTC2018 §3.2.3.2.1",
        input_model=SismaSpettroInput,
        output_model=SismaSpettroOutput,
        run=run_spettro,
        example={
            "s": 1.2,
            "eta": 1.0,
            "q": 1.5,
            "ag_g": 0.098,
            "f0": 2.436,
            "tb_s": 0.129398,
            "tc_s": 0.388193,
            "td_s": 1.992,
            "stato_limite": "SLV",
        },
        summary="Genera lo spettro di risposta elastico e di progetto, in termini di accelerazioni campionate su un intervallo di periodi, a partire dai parametri di sito e dai fattori di struttura già determinati.",
        relazione=relazione_spettro,
    ),
    Tool(
        name="sisma-completo",
        title="Sisma — analisi completa (vita, sito, struttura, spettro)",
        group="Carichi / Sisma",
        norm="NTC2018 §3.2",
        input_model=SismaCompletoInput,
        output_model=SismaCompletoOutput,
        run=run_completo,
        example={
            "comune": "Brembate",
            "vn_anni": 50,
            "classe_uso": "II",
            "stato_limite": "SLV",
            "categoria_sottosuolo": "B",
            "categoria_topografica": "T1",
            "tc_star_s": 0.272,
            "f0": 2.436,
            "ag_g": 0.098,
            "xi_pct": 5,
            "q0": 1.5,
            "regolare_altezza": "SI",
            "qv": 1.5,
        },
        summary="Esegue in un unico calcolo l'intera catena sismica, dalla vita di riferimento ai parametri di sito e ai fattori di struttura, fino allo spettro di risposta di progetto.",
        relazione=relazione_completo,
    ),
)
