"""Verified restatement of `sisma-parametri-sito` (NTC2018 §3.2.2/§3.2.3.2.1, Tab. 3.2.IV/3.2.V;
docs/architecture-phase2.md §6, wave 3 adoption). Pure function of the tool's own validated inputs
and already-computed output; `strutture.shared.ntc_site_seismic` (the single implementation of
`C_c`/`S_s`/`S_T`/`S`/`T_B`/`T_C`/`T_D`, also used by `muro-sostegno`) is never touched, not one
number. Standard mode only: the relazione is never built with `legacy_compat=True` (§1), so the
categoria B lower clip bound of `S_s` is always the NTC-correct 1,00 here, never the sheet's 0,40
(see `docs/divergences/sisma.md`) — no `legacy()` branch of `fattore_amplificazione_ss` ever fires.

`T_B`/`T_C`/`T_D` use the SAME identifiers as `SismaSpettroInput`'s own `symbol` hints
(`relazione_spettro.py` cites them again unchanged): `sisma-completo` chains this tool's `T_C`
straight into that one (`relazione_completo.py`), so one symbol keeps one meaning across the whole
package, not just within a single Traccia. `T*_C` (`tc_star_s`) uses the grammar-legal identifier
`T'_C` — an asterisk is not a letter the notation tokenizer accepts (docs/architecture-phase2.md
§2) — the same apostrophe-for-star substitution the grammar's own docstring gives as an example
(`c'_k`); every `Valore` built from it carries a `descrizione` naming the original input symbol.

`S_T` is a pure table lookup (NTC2018 Tab. 3.2.V, no formula an engineer would write): its Passo
uses the "formula = the identifier itself" pattern, naming the table in `nota`, mirroring `C_u` in
`relazione_vita_riferimento.py`. `C_c`/`S_s` DO have real formulas for categories B-E (branch by
`categoria_sottosuolo`, a categorical input exactly like `classe_uso` drives `C_u`'s table row) —
category A is the one trivial constant (`C_c=S_s=1`, no clip, Tab. 3.2.IV). `S_s` additionally
gets its own pre-clip `S_s,0` step for B-E: the clip bounds are the actual NTC limits, not the
sheet's (wrong, for category B) ones, so showing the raw value first makes the clip's effect
explicit.
"""
from strutture.shared.ntc_site_seismic import AmplificazioneResult, CategoriaSottosuolo
from strutture.shared.ntc_site_seismic.periodi_spettro import TD_COSTANTE_S
from strutture.shared.ntc_site_seismic.stratigrafia import SS_CLIP_INFERIORE_CATEGORIA_B_NTC
from strutture.shared.ntc_site_seismic.tables import FATTORE_TOPOGRAFICO_ST
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import SismaParametriSitoInput, SismaParametriSitoOutput

CLAUSOLA_TAB_3_2_IV = "NTC2018 §3.2.2 Tab. 3.2.IV"
CLAUSOLA_TAB_3_2_V = "NTC2018 §3.2.2 Tab. 3.2.V"
CLAUSOLA_PERIODI = "NTC2018 §3.2.3.2.1"

# Tab. 3.2.IV, categorie B-E: Cc = coeff * T*_C^-esponente.
_CC_COEFF: dict[CategoriaSottosuolo, tuple[float, float]] = {
    "B": (1.10, 0.20), "C": (1.05, 0.33), "D": (1.25, 0.50), "E": (1.15, 0.40),
}
# Tab. 3.2.IV, categorie B-E: Ss,0 = a - b*F0*ag, clipped a [minimo, massimo].
_SS_COEFF: dict[CategoriaSottosuolo, tuple[float, float, float, float]] = {
    "B": (1.40, 0.40, SS_CLIP_INFERIORE_CATEGORIA_B_NTC, 1.20),
    "C": (1.70, 0.60, 1.00, 1.50),
    "D": (2.40, 1.50, 0.90, 1.80),
    "E": (2.00, 1.10, 1.00, 1.60),
}


def relazione_parametri_sito(inputs: SismaParametriSitoInput, output: SismaParametriSitoOutput) -> tuple[Traccia, ...]:
    """8 (categoria A: 6) passi in due Traccia: amplificazione (C_c, S_s,0 se B-E, S_s, S_T, S) e
    periodi caratteristici (T_C, T_B, T_D). Le formule di C_c/S_s/S_T dipendono dalla categoria di
    sottosuolo/topografica (branch per `categoria_sottosuolo`/`categoria_topografica`): poiché
    `traccia_a_testo` non stampa mai `Passo.nota` (dove le categorie erano finora nominate), le
    categorie vanno nel titolo della Traccia, non solo nella nota (review finding MISSING_STEP)."""
    amp = output.amplificazione
    passi_amp = (_passo_cc(inputs, amp), *_passi_ss(inputs, amp), _passo_st(inputs, amp), _passo_s(amp))
    passi_periodi = (_passo_tc(inputs, amp, output), _passo_tb(output), _passo_td(inputs, output))
    titolo_amp = (
        f"Amplificazione stratigrafica e topografica — categoria di sottosuolo "
        f"{inputs.categoria_sottosuolo}, categoria topografica {inputs.categoria_topografica}"
    )
    return (
        Traccia(titolo=titolo_amp, passi=passi_amp),
        Traccia(titolo="Periodi caratteristici dello spettro di risposta elastico", passi=passi_periodi),
    )


def _valore_tc_star(inputs: SismaParametriSitoInput) -> Valore:
    return Valore(simbolo="T'_C", valore=inputs.tc_star_s, unita="s", descrizione="periodo T*_C in input")


def _passo_cc(inputs: SismaParametriSitoInput, amp: AmplificazioneResult) -> Passo:
    categoria = inputs.categoria_sottosuolo
    if categoria == "A":
        return Passo(
            simbolo="C_c", formula="1", valori=(), risultato=amp.cc, unita="-", clausola=CLAUSOLA_TAB_3_2_IV,
            nota="Categoria A: nessuna correzione del periodo, Cc=1.",
        )
    coeff, esponente = _CC_COEFF[categoria]
    return Passo(
        simbolo="C_c", formula=f"{coeff:g} * T'_C^-{esponente:g}",
        valori=(_valore_tc_star(inputs),),
        risultato=amp.cc, unita="-", clausola=CLAUSOLA_TAB_3_2_IV,
        nota=f"Coefficiente di correzione del periodo per categoria di sottosuolo {categoria}.",
    )


def _passi_ss(inputs: SismaParametriSitoInput, amp: AmplificazioneResult) -> tuple[Passo, ...]:
    categoria = inputs.categoria_sottosuolo
    if categoria == "A":
        return (
            Passo(
                simbolo="S_s", formula="1", valori=(), risultato=amp.ss, unita="-", clausola=CLAUSOLA_TAB_3_2_IV,
                nota="Categoria A: nessuna amplificazione stratigrafica, Ss=1.",
            ),
        )
    a, b, minimo, massimo = _SS_COEFF[categoria]
    valori = (
        Valore(simbolo="F_0", valore=inputs.f0, descrizione="fattore di amplificazione massima dello spettro"),
        Valore(simbolo="a_g", valore=inputs.ag_g, unita="g", descrizione="accelerazione orizzontale massima al sito"),
    )
    ss_raw = a - b * inputs.f0 * inputs.ag_g
    passo_raw = Passo(
        simbolo="S_s,0", formula=f"{a:g} - {b:g} * F_0 * a_g", valori=valori,
        risultato=ss_raw, unita="-", clausola=CLAUSOLA_TAB_3_2_IV,
        nota=f"Valore prima del limite di Tab. 3.2.IV per categoria di sottosuolo {categoria}.",
    )
    passo_clip = Passo(
        simbolo="S_s", formula=f"min(max(S_s,0, {minimo:g}), {massimo:g})",
        valori=(Valore(simbolo="S_s,0", valore=ss_raw, descrizione="valore grezzo, calcolato sopra"),),
        risultato=amp.ss, unita="-", clausola=CLAUSOLA_TAB_3_2_IV,
        nota=f"Limite [{minimo:g}; {massimo:g}] di Tab. 3.2.IV per categoria {categoria}"
             + (" (in modalità standard: 1,00, non lo 0,40 del foglio originale)." if categoria == "B" else "."),
    )
    return (passo_raw, passo_clip)


def _passo_st(inputs: SismaParametriSitoInput, amp: AmplificazioneResult) -> Passo:
    valori_st = "; ".join(f"{cat}={valore:g}" for cat, valore in FATTORE_TOPOGRAFICO_ST)
    return Passo(
        simbolo="S_T", formula="S_T",
        valori=(Valore(simbolo="S_T", valore=amp.st, descrizione=f"per categoria topografica {inputs.categoria_topografica}"),),
        risultato=amp.st, unita="-", clausola=CLAUSOLA_TAB_3_2_V,
        nota=f"Tabelle!A7:B10 (NTC2018 Tab. 3.2.V): {valori_st}.",
    )


def _passo_s(amp: AmplificazioneResult) -> Passo:
    return Passo(
        simbolo="S", formula="S_T * S_s",
        valori=(
            Valore(simbolo="S_T", valore=amp.st, descrizione="coefficiente di amplificazione topografica, calcolato sopra"),
            Valore(simbolo="S_s", valore=amp.ss, descrizione="coefficiente di amplificazione stratigrafica, calcolato sopra"),
        ),
        risultato=amp.s, unita="-", clausola="NTC2018 §3.2.2",
        nota="Coefficiente di amplificazione del suolo.",
    )


def _passo_tc(inputs: SismaParametriSitoInput, amp: AmplificazioneResult, output: SismaParametriSitoOutput) -> Passo:
    return Passo(
        simbolo="T_C", formula="C_c * T'_C",
        valori=(
            Valore(simbolo="C_c", valore=amp.cc, descrizione="coefficiente di correzione del periodo, calcolato sopra"),
            _valore_tc_star(inputs),
        ),
        risultato=output.periodi.tc, unita="s", clausola=CLAUSOLA_PERIODI,
        nota="Periodo di inizio del tratto a velocità costante.",
    )


def _passo_tb(output: SismaParametriSitoOutput) -> Passo:
    return Passo(
        simbolo="T_B", formula="T_C / 3",
        valori=(Valore(simbolo="T_C", valore=output.periodi.tc, unita="s", descrizione="calcolato sopra"),),
        risultato=output.periodi.tb, unita="s", clausola=CLAUSOLA_PERIODI,
        nota="Periodo di inizio del tratto ad accelerazione costante.",
    )


def _passo_td(inputs: SismaParametriSitoInput, output: SismaParametriSitoOutput) -> Passo:
    return Passo(
        simbolo="T_D", formula=f"4 * a_g + {TD_COSTANTE_S:g}",
        valori=(Valore(simbolo="a_g", valore=inputs.ag_g, unita="g"),),
        risultato=output.periodi.td, unita="s", clausola=CLAUSOLA_PERIODI,
        nota="Periodo di inizio del tratto a spostamento costante (ag in g).",
    )
