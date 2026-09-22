"""Verified restatement (docs/architecture-phase2.md) of `sismica_ntc.py` (NTC2018 §7.2.5, Tab.
3.2.IV/3.2.V/C7.11.I) and `sismica_en.py` (EN1998-1 §3.2.2.2(2)P / EN1998-5 §5.4.1.2). `SS`
restates NTC2018 Tab. 3.2.IV's own piecewise formula (`shared.ntc_site_seismic.stratigrafia.
fattore_amplificazione_ss`) branched by `categoria_sottosuolo`, exactly as the source function
does; `ST` (Tab. 3.2.V) and `α`/`S`-by-spectrum-type (EN1998-5 Tab. §5.4.1.2) are pure table
lookups, cited by identity with a `nota` naming the table."""
from strutture.shared.ntc_site_seismic.stratigrafia import (
    SS_CLIP_INFERIORE_CATEGORIA_B_NTC as SS_B_MIN,
)
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import CategoriaSottosuoloTravi, TraviCollegamentoInput
from .sismica_en import MS_SOGLIA_TIPO_SPETTRO, SismicaEnResult
from .sismica_ntc import SismicaNtcResult

CLAUSOLA_SS = "NTC2018 Tab. 3.2.IV"
CLAUSOLA_ST = "NTC2018 Tab. 3.2.V"
CLAUSOLA_ALPHA_NTC = "NTC2018 §7.2.5 (Circolare 2019 Tab. C7.11.I)"
CLAUSOLA_EN_SITO = "EN1998-1 §3.2.2.2(2)P / EN1998-5 §5.4.1.2 (Tabelle!M131:P134)"

_FORMULE_SS: dict[CategoriaSottosuoloTravi, str] = {
    "A": "1",
    "B": f"min(max(1.40 - 0.40 * F_0 * a_g, {SS_B_MIN:g}), 1.20)",
    "C": "min(max(1.70 - 0.60 * F_0 * a_g, 1.00), 1.50)",
    "D": "min(max(2.40 - 1.50 * F_0 * a_g, 0.90), 1.80)",
}


def traccia_sismica_ntc(inputs: TraviCollegamentoInput, sismica: SismicaNtcResult) -> Traccia:
    """5 passi: SS, ST, S, α (lookup), amax. SS/α dipendono dalla categoria di sottosuolo (Tab.
    3.2.IV / Tab. C7.11.I): poiché `traccia_a_testo` non stampa mai `Passo.nota`, la categoria di
    sottosuolo e quella topografica vanno nel titolo (review finding MISSING_STEP, come in
    loads/sisma)."""
    assert inputs.f0 is not None and inputs.categoria_topografica is not None
    return Traccia(
        titolo=(
            f"Amplificazione sismica (NTC2018) — categoria di sottosuolo {inputs.categoria_sottosuolo}, "
            f"categoria topografica {inputs.categoria_topografica}"
        ),
        passi=(
            _passo_ss(inputs, sismica), _passo_st(inputs, sismica), _passo_s(sismica),
            _passo_alpha_ntc(inputs, sismica), _passo_amax(inputs, sismica),
        ),
    )


def _passo_ss(inputs: TraviCollegamentoInput, sismica: SismicaNtcResult) -> Passo:
    categoria = inputs.categoria_sottosuolo
    formula = _FORMULE_SS[categoria]
    valori = (
        (Valore(simbolo="F_0", valore=inputs.f0, descrizione="fattore di amplificazione dello spettro"),
         Valore(simbolo="a_g", valore=inputs.ag_g, unita="g", descrizione="accelerazione orizzontale massima al sito"))
        if categoria != "A" else ()
    )
    return Passo(
        simbolo="S_S", formula=formula, valori=valori,
        risultato=sismica.ss, unita="-", clausola=CLAUSOLA_SS,
        nota=f"Coefficiente di amplificazione stratigrafica, categoria di sottosuolo {categoria}.",
    )


def _passo_st(inputs: TraviCollegamentoInput, sismica: SismicaNtcResult) -> Passo:
    return Passo(
        simbolo="S_T", formula="S_T",
        valori=(Valore(simbolo="S_T", valore=sismica.st, descrizione=f"categoria topografica {inputs.categoria_topografica}"),),
        risultato=sismica.st, unita="-", clausola=CLAUSOLA_ST,
        nota="Coefficiente di amplificazione topografica, valore tabellare.",
    )


def _passo_s(sismica: SismicaNtcResult) -> Passo:
    return Passo(
        simbolo="S", formula="S_S * S_T",
        valori=(
            Valore(simbolo="S_S", valore=sismica.ss, descrizione="calcolato sopra"),
            Valore(simbolo="S_T", valore=sismica.st, descrizione="calcolato sopra"),
        ),
        risultato=sismica.s, unita="-",
        nota="Coefficiente che tiene conto della categoria di sottosuolo e delle condizioni topografiche.",
    )


def _passo_alpha_ntc(inputs: TraviCollegamentoInput, sismica: SismicaNtcResult) -> Passo:
    return Passo(
        simbolo="α", formula="α",
        valori=(Valore(simbolo="α", valore=sismica.alpha, descrizione=f"categoria di sottosuolo {inputs.categoria_sottosuolo}"),),
        risultato=sismica.alpha, unita="-", clausola=CLAUSOLA_ALPHA_NTC,
        nota="Coefficiente della forza assiale di progetto, valore tabellare per categoria di sottosuolo.",
    )


def _passo_amax(inputs: TraviCollegamentoInput, sismica: SismicaNtcResult) -> Passo:
    return Passo(
        simbolo="a_max", formula="a_g * S",
        valori=(
            Valore(simbolo="a_g", valore=inputs.ag_g, unita="g", descrizione="accelerazione orizzontale massima al sito"),
            Valore(simbolo="S", valore=sismica.s, descrizione="calcolato sopra"),
        ),
        risultato=sismica.amax_g, unita="g",
        nota="Accelerazione orizzontale massima attesa al sito.",
    )


def traccia_sismica_en(inputs: TraviCollegamentoInput, sismica: SismicaEnResult) -> Traccia:
    """3 passi: S (lookup + criterio tipo spettro), α (lookup), amax. Titolo con la categoria di
    sottosuolo per lo stesso motivo di `traccia_sismica_ntc` (review finding MISSING_STEP)."""
    assert inputs.ms is not None
    titolo = f"Amplificazione sismica (EN1998) — categoria di sottosuolo {inputs.categoria_sottosuolo}"
    return Traccia(titolo=titolo, passi=(_passo_s_en(inputs, sismica), _passo_alpha_en(sismica), _passo_amax_en(inputs, sismica)))


def _passo_s_en(inputs: TraviCollegamentoInput, sismica: SismicaEnResult) -> Passo:
    tipo_corretto = "Tipo 2" if inputs.ms <= MS_SOGLIA_TIPO_SPETTRO else "Tipo 1"
    return Passo(
        simbolo="S", formula="S",
        valori=(
            Valore(
                simbolo="S", valore=sismica.s,
                descrizione=f"categoria di sottosuolo {inputs.categoria_sottosuolo}, spettro {tipo_corretto} "
                            f"(Ms={inputs.ms:g} {'≤' if inputs.ms <= MS_SOGLIA_TIPO_SPETTRO else '>'} {MS_SOGLIA_TIPO_SPETTRO:g}, EN1998-1 §3.2.2.2(2)P)",
            ),
        ),
        risultato=sismica.s, unita="-", clausola=CLAUSOLA_EN_SITO,
        nota="Coefficiente di sito, valore tabellare per categoria di sottosuolo e tipo di spettro.",
    )


def _passo_alpha_en(sismica: SismicaEnResult) -> Passo:
    return Passo(
        simbolo="α", formula="α",
        valori=(Valore(simbolo="α", valore=sismica.alpha, descrizione="categoria di sottosuolo"),),
        risultato=sismica.alpha, unita="-", clausola=CLAUSOLA_EN_SITO,
        nota="Coefficiente della forza assiale di progetto, valore tabellare per categoria di sottosuolo.",
    )


def _passo_amax_en(inputs: TraviCollegamentoInput, sismica: SismicaEnResult) -> Passo:
    return Passo(
        simbolo="a_max", formula="a_g * S",
        valori=(
            Valore(simbolo="a_g", valore=inputs.ag_g, unita="g", descrizione="accelerazione orizzontale massima al sito"),
            Valore(simbolo="S", valore=sismica.s, descrizione="calcolato sopra"),
        ),
        risultato=sismica.amax_g, unita="g",
        nota="Accelerazione orizzontale massima attesa al sito.",
    )
