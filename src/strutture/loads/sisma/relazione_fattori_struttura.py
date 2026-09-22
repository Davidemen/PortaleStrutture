"""Verified restatement of `sisma-fattori-struttura` (NTC2018 §3.2.3.2.1 eq. 3.2.6, §7.3.1,
§7.3.3.2; docs/architecture-phase2.md §6, wave 3 adoption). Pure function of the tool's own
validated inputs and already-computed output; the calculation code is never touched, not one
number. `K_R` and `q_max = q_0·K_R` are intermediates `SismaFattoriStrutturaOutput` does not
expose (only the FINAL `q`, gated by stato limite, is a field): both are read straight from the
package's own step functions (`kr_regolarita.kr_regolare_altezza`, a plain multiplication of
already-known values), exactly as the architecture brief allows.

`η_v` is restated with its OWN raw/floor derivation, not as "η_v = η": `eta_verticale.py`'s fixed
branch genuinely calls `smorzamento_eta(xi_pct)` a second, independent time (not a reference to
the already-computed `η`), matching NTC2018's assumption that ξ=5% governs both components unless
stated otherwise — the two are equal here only because they share the same ξ, not by definition;
the `nota` says so.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .fattore_struttura_q import fattore_struttura_q
from .kr_regolarita import KR_NON_REGOLARE, KR_REGOLARE, kr_regolare_altezza
from .models import SismaFattoriStrutturaInput, SismaFattoriStrutturaOutput
from .smorzamento import ETA_MIN
from .stato_limite import is_stato_limite_uls


def relazione_fattori_struttura(
    inputs: SismaFattoriStrutturaInput, output: SismaFattoriStrutturaOutput
) -> tuple[Traccia, ...]:
    """8 passi in due Traccia: smorzamento e struttura orizzontale (η, K_R, q_max, q) e struttura
    verticale (η_v, q_v)."""
    kr = kr_regolare_altezza(inputs.regolare_altezza)
    q_max = fattore_struttura_q(inputs.q0, kr, is_uls=True)
    is_uls = is_stato_limite_uls(inputs.stato_limite)
    passi_orizzontale = (
        *_passi_eta(inputs.xi_pct, output.eta, simbolo="η", simbolo_grezzo="η_0", clausola="NTC2018 §3.2.3.2.1 eq. 3.2.6"),
        _passo_kr(inputs, kr),
        _passo_q_max(inputs, kr, q_max),
        _passo_q(inputs, output, q_max, is_uls=is_uls),
    )
    passi_verticale = (
        *_passi_eta(
            inputs.xi_pct, output.eta_vert, simbolo="η_v", simbolo_grezzo="η_v,0",
            clausola="NTC2018 §7.3.3.2 + §3.2.3.2.1 eq. 3.2.6",
            nota_extra="Stessa formula di η: NTC2018 assume ξ=5% anche per la componente verticale, salvo diversa indicazione.",
        ),
        _passo_q_vert(output),
    )
    return (
        Traccia(titolo="Fattore di smorzamento e fattore di struttura orizzontale", passi=passi_orizzontale),
        Traccia(titolo="Fattori di struttura per la componente verticale", passi=passi_verticale),
    )


def _passi_eta(xi_pct: float, eta: float, *, simbolo: str, simbolo_grezzo: str, clausola: str, nota_extra: str = "") -> tuple[Passo, Passo]:
    eta_grezzo = (10.0 / (5.0 + xi_pct)) ** 0.5
    passo_grezzo = Passo(
        simbolo=simbolo_grezzo, formula="sqrt(10 / (5 + ξ))",
        valori=(Valore(simbolo="ξ", valore=xi_pct, unita="%", descrizione="smorzamento viscoso equivalente"),),
        risultato=eta_grezzo, unita="-", clausola=clausola,
        nota="Correzione per smorzamento, prima del limite inferiore." + (f" {nota_extra}" if nota_extra else ""),
    )
    passo_finale = Passo(
        simbolo=simbolo, formula=f"max({simbolo_grezzo}, {ETA_MIN:g})",
        valori=(Valore(simbolo=simbolo_grezzo, valore=eta_grezzo, descrizione="valore grezzo, calcolato sopra"),),
        risultato=eta, unita="-", clausola=clausola,
        nota=f"Limite inferiore {ETA_MIN:g} della formula stessa, indipendente dallo smorzamento nominale.",
    )
    return (passo_grezzo, passo_finale)


def _passo_kr(inputs: SismaFattoriStrutturaInput, kr: float) -> Passo:
    return Passo(
        simbolo="K_R", formula="K_R",
        valori=(Valore(simbolo="K_R", valore=kr, descrizione=f"regolare in altezza: {inputs.regolare_altezza}"),),
        risultato=kr, unita="-", clausola="NTC2018 §7.3.1",
        nota=f"K_R={KR_REGOLARE:g} se la struttura è regolare in altezza (SI), {KR_NON_REGOLARE:g} altrimenti (NO).",
    )


def _passo_q_max(inputs: SismaFattoriStrutturaInput, kr: float, q_max: float) -> Passo:
    return Passo(
        simbolo="q_max", formula="q_0 * K_R",
        valori=(
            Valore(simbolo="q_0", valore=inputs.q0, descrizione="fattore di struttura massimo, dipende dalla tipologia strutturale"),
            Valore(simbolo="K_R", valore=kr, descrizione="fattore di riduzione per irregolarità in altezza, calcolato sopra"),
        ),
        risultato=q_max, unita="-", clausola="NTC2018 §7.3.1",
        nota="Fattore di struttura massimo raggiungibile, prima del vincolo dello stato limite considerato.",
    )


def _passo_q(inputs: SismaFattoriStrutturaInput, output: SismaFattoriStrutturaOutput, q_max: float, *, is_uls: bool) -> Passo:
    if is_uls:
        return Passo(
            simbolo="q", formula="q_max",
            valori=(Valore(simbolo="q_max", valore=q_max, descrizione="fattore di struttura massimo, calcolato sopra"),),
            risultato=output.q, unita="-", clausola="NTC2018 §7.3.1",
            nota=f"Stato limite {inputs.stato_limite}: stato limite ultimo, si assume q=q_max.",
        )
    return Passo(
        simbolo="q", formula="1", valori=(),
        risultato=output.q, unita="-", clausola="NTC2018 §7.3.1",
        nota=f"Stato limite {inputs.stato_limite}: stato limite di esercizio, si assume q=1 "
             "(lo spettro elastico non è ridotto).",
    )


def _passo_q_vert(output: SismaFattoriStrutturaOutput) -> Passo:
    return Passo(
        simbolo="q_v", formula="q_v",
        valori=(Valore(simbolo="q_v", valore=output.q_vert, descrizione="dato di ingresso, fissato dalla normativa (NTC2018 tipicamente q_v ≈ 1,5)"),),
        risultato=output.q_vert, unita="-", clausola="NTC2018 §7.3.3.2",
        nota="Fattore di struttura per la componente verticale: dato di ingresso, non derivato in questo foglio.",
    )
