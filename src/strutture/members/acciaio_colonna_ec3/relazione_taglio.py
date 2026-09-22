"""Verified restatement (docs/architecture-phase2.md) of `taglio.py` (V_pl,Rd,w / V_pl,Rd,f —
EN1993-1-1 §6.2.6(2)/(3)). Each `Passo` combines the resistance's own formula with the `Check` it
drives (mirroring `ca_travi.relazione_armatura`'s limit+check pattern), since the demand (a plain
input) needs no separate derivation of its own.

`ColonnaEc3Output.taglio` gives BOTH `vpl_rd_anima_kN` and `vpl_rd_ali_kN` the SAME UI symbol hint
`"V_pl,Rd"` — reusing it here for both would collide (one symbol, two different meanings within the
trace, lesson of docs/architecture-phase2.md §6's wave-1 proof-read); the identifiers below are
`V_pl,Rd,w` (web/anima) and `V_pl,Rd,f` (flange/ali) instead, each with a single meaning.

Fixed-mode demand pairing (`taglio.costruisci_taglio`, non-legacy branch): the web check compares
against `inputs.vy_sd_kN` and the flange check against `inputs.vz_sd_kN` — the legacy sheet swaps
them (a documented, unfixed-here divergence in `taglio.py`'s own docstring); `relazione` only ever
describes standard mode (`strutture.shared.tool._con_relazione`), so this is the only pairing ever
printed. The demand is printed as `V_Ed,w`/`V_Ed,f` (web-plane/flange-plane shear), NOT as
`V_y,sd`/`V_z,sd`: `models.py` documents `vy_sd_kN` as "Taglio di progetto sull'anima" (the WEB), the
reverse of EN1993-1-1's own axis convention (V_z,Ed is the web shear, V_y,Ed the flange shear) — a
naming inconsistency baked into the calculation code's field names, which this relazione module
cannot change (review finding MISLEADING). Printing the misleading EC3-look-alike symbols here would
let a reader believe the wrong axis is being checked; `V_Ed,w`/`V_Ed,f` names the demand by the plane
it acts in instead, matching the `V_pl,Rd,w`/`V_pl,Rd,f` capacities it is compared against.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models import ColonnaEc3Input
from .relazione_comune import N_A_KN
from .results import ColonnaEc3Output


def traccia_taglio(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Traccia:
    """2 passi: V_pl,Rd,w (Check "Vpl,Rd anima"), V_pl,Rd,f (Check "Vpl,Rd ali")."""
    return Traccia(titolo="Resistenza a taglio", passi=(_passo_anima(inputs, output), _passo_ali(inputs, output)))


def _passo_anima(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    taglio = output.taglio
    return Passo(
        simbolo="V_pl,Rd,w",
        formula=f"1.2 * (h - 2*t_f) * t_w * f_yd / sqrt(3) * {N_A_KN:g} >= V_Ed,w",
        valori=(
            Valore(simbolo="h", valore=inputs.h_mm, unita="mm"),
            Valore(simbolo="t_f", valore=inputs.tf_mm, unita="mm"),
            Valore(simbolo="t_w", valore=inputs.tw_mm, unita="mm"),
            Valore(simbolo="f_yd", valore=output.materiali.fyd_MPa, unita="MPa", descrizione="calcolato sopra"),
            Valore(simbolo="V_Ed,w", valore=inputs.vy_sd_kN, unita="kN", descrizione="taglio di progetto nel piano dell'anima"),
        ),
        risultato=taglio.vpl_rd_anima_kN, unita="kN", clausola="EN1993-1-1 §6.2.6(2)/(3)",
        esito="soddisfatta" if taglio.verifica_anima.passed else "non soddisfatta",
        nota="Area resistente a taglio dell'anima A_v,z=1,2·(h−2t_f)·t_w, §6.2.6(3).",
    )


def _passo_ali(inputs: ColonnaEc3Input, output: ColonnaEc3Output) -> Passo:
    taglio = output.taglio
    return Passo(
        simbolo="V_pl,Rd,f",
        formula=f"2 * b * t_f * f_yd / sqrt(3) * {N_A_KN:g} >= V_Ed,f",
        valori=(
            Valore(simbolo="b", valore=inputs.b_mm, unita="mm"),
            Valore(simbolo="t_f", valore=inputs.tf_mm, unita="mm"),
            Valore(simbolo="f_yd", valore=output.materiali.fyd_MPa, unita="MPa", descrizione="calcolato sopra"),
            Valore(simbolo="V_Ed,f", valore=inputs.vz_sd_kN, unita="kN", descrizione="taglio di progetto nel piano delle ali"),
        ),
        risultato=taglio.vpl_rd_ali_kN, unita="kN", clausola="EN1993-1-1 §6.2.6(2)",
        esito="soddisfatta" if taglio.verifica_ali.passed else "non soddisfatta",
        nota="Area resistente a taglio delle ali A_v,y=2·b·t_f.",
    )
