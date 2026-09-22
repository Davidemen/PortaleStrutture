"""Verified restatement (docs/architecture-phase2.md) of `righe.py`/`steel_base.py`
(`acciaio-resistenza-incendio` — EN1993-1-2 §3.2.1 Tab. 3.1 + Annex A eq. (A.1)). `f_y,20°C`/
`f_u,20°C` are an EN10025 grade-table lookup (`steel_base.materiale_base`); k_y,θ/k_E,θ a
piecewise-linear interpolation of Tab. 3.1 — both restated with `formula` the identifier itself,
`nota` naming the table (docs/architecture-phase2.md §6's "lookup only" fallback). This tool has no
`Check` (`tool.run` calls `success(data, inputs, warnings=...)` with no `checks=`).

Many rows (one per requested exposure time, `RigaResistenzaIncendio` is a `tuple` field never
recursed into by the harness, docs/architecture-phase2.md §4): the trace restates the GOVERNING row
only — the LONGEST requested exposure time, the most severe one (§5) — and says so in the title.
`f_y,20°C`/`f_u,20°C` are not grammar-legal identifiers (a degree sign is not a letter, same
constraint `ca_travi.relazione_taglio` documents for "cotg θ"): `f_y20`/`f_u20` are used in
`formula`/`valori` instead, `Passo.simbolo` keeps the readable UI hint (free text, never parsed).
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import ResistenzaIncendioInput, ResistenzaIncendioOutput, RigaResistenzaIncendio


def relazione_resistenza(inputs: ResistenzaIncendioInput, output: ResistenzaIncendioOutput) -> tuple[Traccia, ...]:
    """8 passi: f_y,20°C, f_u,20°C (lookup EN10025), θ, k_y,θ, k_E,θ (lookup Tab. 3.1), f_y,θ,
    f_u,θ, E_θ."""
    riga_governante = max(output.righe, key=lambda r: r.t_min)
    return (
        Traccia(
            titolo=f"Riduzione di resistenza e rigidezza in condizioni di incendio — riga governante: "
                   f"t={riga_governante.t_min:g} min (esposizione più severa fra quelle richieste)",
            passi=(
                _passo_base(output, "f_y,20°C", "f_y20", output.materiale.fy_20_MPa),
                _passo_base(output, "f_u,20°C", "f_u20", output.materiale.fu_20_MPa),
                _passo_theta(riga_governante),
                _passo_fattore(riga_governante, "k_y,θ", riga_governante.ky_theta),
                _passo_fattore(riga_governante, "k_E,θ", riga_governante.kE_theta),
                _passo_fy_theta(output, riga_governante),
                _passo_fu_theta(output, riga_governante),
                _passo_e_theta(inputs, riga_governante),
            ),
        ),
    )


def _passo_base(output: ResistenzaIncendioOutput, simbolo: str, identificatore: str, valore: float) -> Passo:
    return Passo(
        simbolo=simbolo, formula=identificatore,
        valori=(Valore(simbolo=identificatore, valore=valore, descrizione="valore nominale EN10025 per il grado dichiarato"),),
        risultato=valore, unita="MPa", clausola="EN10025 (tabella nominale)",
    )


def _passo_theta(riga: RigaResistenzaIncendio) -> Passo:
    # Θg=20+345·log10(8t+1) è la curva NOMINALE ISO 834, EN1991-1-2 §3.2.1 eq. (3.4) — non l'Annex
    # A eq. (A.1), che è la curva PARAMETRICA (un modello diverso): la didascalia "curva nominale
    # ISO 834" contraddiceva la clausola citata finora (review finding WRONG_CLAUSE).
    return Passo(
        simbolo="θ", formula="20 + 345 * log10(8 * t + 1)",
        valori=(Valore(simbolo="t", valore=riga.t_min, unita="min", descrizione="durata di esposizione"),),
        risultato=riga.theta_C, unita="°C", clausola="EN1991-1-2 §3.2.1 eq. (3.4) (curva nominale ISO 834)",
        nota="Temperatura del gas; il foglio assume acciaio non protetto e la considera uguale alla "
             "temperatura dell'acciaio (nessuna inerzia termica).",
    )


def _passo_fattore(riga: RigaResistenzaIncendio, simbolo: str, valore: float) -> Passo:
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=valore, descrizione="lettura tabellare, EN1993-1-2 Tab. 3.1, interpolazione lineare"),),
        risultato=valore, unita="-", clausola="EN1993-1-2 Tab. 3.1",
    )


def _passo_fy_theta(output: ResistenzaIncendioOutput, riga: RigaResistenzaIncendio) -> Passo:
    return Passo(
        simbolo="f_y,θ", formula="f_y20 * k_y,θ",
        valori=(
            Valore(simbolo="f_y20", valore=output.materiale.fy_20_MPa, unita="MPa", descrizione="calcolato sopra"),
            Valore(simbolo="k_y,θ", valore=riga.ky_theta, descrizione="calcolato sopra"),
        ),
        risultato=riga.fy_theta_MPa, unita="MPa", clausola="EN1993-1-2 §3.2.1",
    )


def _passo_fu_theta(output: ResistenzaIncendioOutput, riga: RigaResistenzaIncendio) -> Passo:
    # EN1993-1-2 §3.2.1/Tab. 3.1 definiscono solo k_y,θ/k_p,θ/k_E,θ: nessun fattore di riduzione
    # per f_u dei profili (bulloni/saldature sono nell'Annex D). Riusare k_y,θ è un'ipotesi di
    # calcolo, non una clausola — la `clausola` lo dichiara in chiaro (review finding WRONG_CLAUSE:
    # `nota` non è mai stampata da `traccia_a_testo`, quindi l'ipotesi va resa visibile altrove).
    return Passo(
        simbolo="f_u,θ", formula="f_u20 * k_y,θ",
        valori=(
            Valore(simbolo="f_u20", valore=output.materiale.fu_20_MPa, unita="MPa", descrizione="calcolato sopra"),
            Valore(simbolo="k_y,θ", valore=riga.ky_theta, descrizione="calcolato sopra"),
        ),
        risultato=riga.fu_theta_MPa, unita="MPa",
        clausola="ipotesi: f_u ridotto con k_y,θ (EN1993-1-2 non fornisce k_u,θ per i profili)",
        nota="La normativa non tabula una riduzione separata per f_u: il foglio riutilizza k_y,θ.",
    )


def _passo_e_theta(inputs: ResistenzaIncendioInput, riga: RigaResistenzaIncendio) -> Passo:
    return Passo(
        simbolo="E_θ", formula="E * k_E,θ",
        valori=(
            Valore(simbolo="E", valore=inputs.e_20_MPa, unita="MPa", descrizione="modulo elastico di riferimento a 20°C"),
            Valore(simbolo="k_E,θ", valore=riga.kE_theta, descrizione="calcolato sopra"),
        ),
        risultato=riga.e_theta_MPa, unita="MPa", clausola="EN1993-1-2 §3.2.1",
    )
