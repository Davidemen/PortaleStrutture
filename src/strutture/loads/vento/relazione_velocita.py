"""Verified restatement (docs/architecture-phase2.md §6) of the reference-velocity chain:
altitude-corrected coefficient c_a and v_b (`vref.py`, NTC2018 §3.3.1 — the same paragraph that
introduces v_b,0/a_0/k_s and Tab. 3.3.I, restated in `relazione_zona.py`; the review lesson "cite
the clause that actually gives THAT formula" applies here too: v_b=v_b,0·c_a is a §3.3.1 formula,
not §3.3.2, review finding WRONG_CLAUSE), the return-period factor c_r
(`periodo_ritorno.py::coefficiente_periodo_ritorno`, NTC2018 §3.3.2 eq. (3.3.3) — the module's own
docstring already says "NTC2018 eq. 3.3.3"; citing a Circolare paragraph number for an NTC equation
number is unverifiable in either document, review finding WRONG_CLAUSE) and the design reference
velocity v_r (NTC2018 §3.3.2 eq. 3.3.2). The calculation code is never touched:
`vref.coefficiente_altitudine`'s own `as<=a0` branch is restated with its own formula text (a
constant "1", no interpolation) rather than forced through the `a_s>a_0` formula, matching
`docs/architecture-phase2.md`'s "restate what the code does" rule."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import VentoPressioneInput, VentoPressioneOutput

CLAUSOLA_VREF = "NTC2018 §3.3.1 Tab. 3.3.I"
CLAUSOLA_CR = "NTC2018 §3.3.2 eq. (3.3.3)"
CLAUSOLA_VR = "NTC2018 §3.3.2 eq. (3.3.2)"


def traccia_velocita_di_riferimento(inputs: VentoPressioneInput, output: VentoPressioneOutput) -> Traccia:
    """4 passi: c_a, v_b (=v_ref), c_r(T_R), v_r."""
    return Traccia(
        titolo="Velocità di riferimento",
        passi=(_passo_ca(inputs, output), _passo_vb(output), _passo_cr(inputs, output), _passo_vr(output)),
    )


def _passo_ca(inputs: VentoPressioneInput, output: VentoPressioneOutput) -> Passo:
    # `traccia_a_testo` non stampa mai `Passo.nota` (review finding MISSING_STEP): la condizione
    # che seleziona il ramo va quindi nel simbolo stampato, non solo nella nota.
    if inputs.altitudine_m <= output.a0:
        return Passo(
            simbolo="c_a  (a_s ≤ a_0)", formula="1", valori=(),
            risultato=output.ca, unita="-", clausola=CLAUSOLA_VREF,
            nota=f"Altitudine a_s={inputs.altitudine_m:g} m ≤ a_0={output.a0:g} m: nessuna correzione di altitudine.",
        )
    return Passo(
        simbolo="c_a  (a_s > a_0)",
        formula="1 + k_s * (a_s / a_0 - 1)",
        valori=(
            Valore(simbolo="k_s", valore=output.ks, descrizione="coefficiente di zona, calcolato sopra"),
            Valore(simbolo="a_s", valore=inputs.altitudine_m, unita="m", descrizione="altitudine del sito"),
            Valore(simbolo="a_0", valore=output.a0, unita="m", descrizione="altitudine di riferimento della zona, calcolata sopra"),
        ),
        risultato=output.ca, unita="-", clausola=CLAUSOLA_VREF,
        nota=f"Altitudine a_s={inputs.altitudine_m:g} m > a_0={output.a0:g} m: correzione lineare di altitudine.",
    )


def _passo_vb(output: VentoPressioneOutput) -> Passo:
    return Passo(
        simbolo="v_b",
        formula="v_b,0 * c_a",
        valori=(
            Valore(simbolo="v_b,0", valore=output.vb0, unita="m/s", descrizione="velocità base di riferimento della zona, calcolata sopra"),
            Valore(simbolo="c_a", valore=output.ca, descrizione="coefficiente di altitudine, calcolato sopra"),
        ),
        risultato=output.vref, unita="m/s", clausola=CLAUSOLA_VREF,
        nota="Velocità di riferimento al suolo per un periodo di ritorno di 50 anni.",
    )


def _passo_cr(inputs: VentoPressioneInput, output: VentoPressioneOutput) -> Passo:
    return Passo(
        simbolo="c_r",
        formula="0.75 * sqrt(1 - 0.2 * ln(-ln(1 - 1 / T_R)))",
        valori=(Valore(simbolo="T_R", valore=inputs.periodo_ritorno_anni, unita="anni", descrizione="periodo di ritorno di progetto"),),
        risultato=output.a_r, unita="-", clausola=CLAUSOLA_CR,
        nota="Fattore di correzione di Gumbel per il periodo di ritorno di progetto.",
    )


def _passo_vr(output: VentoPressioneOutput) -> Passo:
    return Passo(
        simbolo="v_r",
        formula="v_b * c_r",
        valori=(
            Valore(simbolo="v_b", valore=output.vref, unita="m/s", descrizione="velocità di riferimento al suolo, calcolata sopra"),
            Valore(simbolo="c_r", valore=output.a_r, descrizione="fattore di correzione per il periodo di ritorno, calcolato sopra"),
        ),
        risultato=output.vr, unita="m/s", clausola=CLAUSOLA_VR,
        nota="Velocità di riferimento per il periodo di ritorno di progetto.",
    )
