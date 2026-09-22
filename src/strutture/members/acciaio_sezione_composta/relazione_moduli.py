"""Verified restatement (docs/architecture-phase2.md) of `moduli_elastici.py` (W_el, plain
mechanics: I / distance to the outer fibre), `raggi.py` (i = sqrt(I/A)) and `plastico.py` (W_pl,
the true equal-area plastic modulus, code-standard mode). Outer-fibre distances (y_max/y_min/x_max/
x_min, `moduli_elastici._estremi`) are each used only once (feeding a single `Wel` `Passo`), so they
are cited as a `Valore` with a `descrizione`, never given their own `Passo`, mirroring
`relazione_instabilita_flessionale.py`'s Φ.

W_pl has NO closed-form formula an engineer would write by hand: `plastico.asse_neutro_plastico`
finds the equal-area axis by BISECTION (a numerical goal-seek, replacing Excel's own), then W_pl
sums the static moments of the two half-areas about it, splitting any element that straddles the
axis. Both z_pl and W_pl are restated the way docs/architecture-phase2.md §6 treats a lookup-only
value: `formula` is the identifier itself, `nota` names the method. `plastico._strisce_asse_x/_y`
are imported directly (leading underscore): `ElementoRisultato` does not expose each element's own
b_mm/h_mm, so z_pl can only be reproduced by rebuilding the INTERNAL `Elemento` geometry through
`elementi.costruisci_elementi` (same inputs `run()` uses) and feeding it through the exact same
private helper — anything else would risk silently drifting from what the tool actually computed.
"""
from strutture.shared.relazione import Passo, Traccia, Valore

from .elementi import costruisci_elementi
from .models import SezioneHRimpiattataInput
from .moduli_elastici import _estremi
from .plastico import _strisce_asse_x, _strisce_asse_y, asse_neutro_plastico
from .risultati import ElementoRisultato, Sezione

MM_PER_CM = 10.0
MM4_PER_CM4 = MM_PER_CM**4


def traccia_moduli(inputs: SezioneHRimpiattataInput, elementi: tuple[ElementoRisultato, ...], sezione: Sezione) -> Traccia:
    """10 passi: 4 W_el, 2 raggi d'inerzia, 2 z_pl (assi a aree uguali), 2 W_pl."""
    y_min, y_max, x_min, x_max = _estremi_da_elementi(inputs)
    return Traccia(
        titolo="Moduli di resistenza e raggi d'inerzia",
        passi=(
            _passo_wel(sezione, "x", "superiore", "I_x", sezione.ix_cm4, "y_max", y_max, "y_N", sezione.y_n_mm, sezione.wel_x_superiore_cm3),
            _passo_wel(sezione, "x", "inferiore", "I_x", sezione.ix_cm4, "y_N", sezione.y_n_mm, "y_min", y_min, sezione.wel_x_inferiore_cm3),
            _passo_wel(sezione, "y", "+x", "I_y", sezione.iy_cm4, "x_max", x_max, "x_N", sezione.x_n_mm, sezione.wel_y_destro_cm3),
            _passo_wel(sezione, "y", "-x", "I_y", sezione.iy_cm4, "x_N", sezione.x_n_mm, "x_min", x_min, sezione.wel_y_sinistro_cm3),
            _passo_raggio(sezione, "x"), _passo_raggio(sezione, "y"),
            _passo_z_pl(inputs, "x"), _passo_wpl(sezione, "x"),
            _passo_z_pl(inputs, "y"), _passo_wpl(sezione, "y"),
        ),
    )


def _estremi_da_elementi(inputs: SezioneHRimpiattataInput) -> tuple[float, float, float, float]:
    elementi = costruisci_elementi(inputs.h_profilo_mm, inputs.b_profilo_mm, inputs.tf_mm, inputs.tw_mm,
                                    inputs.piatti, legacy_compat=inputs.legacy_compat)
    return _estremi(elementi)


def _passo_wel(
    sezione: Sezione, asse: str, lato: str, simbolo_i: str, valore_i: float,
    simbolo_a: str, valore_a: float, simbolo_b: str, valore_b: float, risultato: float,
) -> Passo:
    return Passo(
        simbolo=f"Wel,{asse},{lato}", formula=f"{simbolo_i} / ({simbolo_a} / {MM_PER_CM:g} - {simbolo_b} / {MM_PER_CM:g})",
        valori=(
            Valore(simbolo=simbolo_i, valore=valore_i, unita="cm4", descrizione="calcolato sopra"),
            Valore(simbolo=simbolo_a, valore=valore_a, unita="mm", descrizione="quota della fibra più esterna" if "max" in simbolo_a or "min" in simbolo_a else "calcolato sopra"),
            Valore(simbolo=simbolo_b, valore=valore_b, unita="mm", descrizione="quota della fibra più esterna" if "max" in simbolo_b or "min" in simbolo_b else "calcolato sopra"),
        ),
        risultato=risultato, unita="cm3", clausola="Statica — Wel = I / distanza dalla fibra estrema",
        nota=f"Modulo di resistenza elastico, asse {'forte' if asse == 'x' else 'debole'}, lato {lato}.",
    )


def _passo_raggio(sezione: Sezione, asse: str) -> Passo:
    simbolo_i = "I_x" if asse == "x" else "I_y"
    valore_i = sezione.ix_cm4 if asse == "x" else sezione.iy_cm4
    risultato = sezione.raggio_x_mm if asse == "x" else sezione.raggio_y_mm
    return Passo(
        simbolo=f"i_{asse}", formula=f"sqrt({simbolo_i} * {MM4_PER_CM4:g} / A)",
        valori=(
            Valore(simbolo=simbolo_i, valore=valore_i, unita="cm4", descrizione="calcolato sopra"),
            Valore(simbolo="A", valore=sezione.area_mm2, unita="mm2", descrizione="calcolato sopra"),
        ),
        risultato=risultato, unita="mm", clausola="Statica — i = sqrt(I/A)",
        nota=f"Raggio d'inerzia, asse {'forte' if asse == 'x' else 'debole'}.",
    )


def _passo_z_pl(inputs: SezioneHRimpiattataInput, asse: str) -> Passo:
    elementi = costruisci_elementi(inputs.h_profilo_mm, inputs.b_profilo_mm, inputs.tf_mm, inputs.tw_mm,
                                    inputs.piatti, legacy_compat=inputs.legacy_compat)
    strisce = _strisce_asse_x(elementi) if asse == "x" else _strisce_asse_y(elementi)
    z_pl = asse_neutro_plastico(strisce)
    simbolo = f"z_pl,{asse}"
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=z_pl, unita="mm", descrizione="calcolato per bisezione"),),
        risultato=z_pl, unita="mm",
        nota="Posizione dell'asse a AREE UGUALI (A/2 per parte), trovata per bisezione: nessuna "
             "formula chiusa la esprime direttamente.",
    )


def _passo_wpl(sezione: Sezione, asse: str) -> Passo:
    risultato = sezione.wpl_x_cm3 if asse == "x" else sezione.wpl_y_cm3
    simbolo = f"W_pl,{asse}"
    return Passo(
        simbolo=simbolo, formula=simbolo,
        valori=(Valore(simbolo=simbolo, valore=risultato, unita="cm3"),),
        risultato=risultato, unita="cm3",
        nota="Somma dei momenti statici delle due semi-aree (A/2 ciascuna) rispetto all'asse a aree "
             "uguali z_pl, spezzando l'elemento che lo attraversa (qui in generale l'anima).",
    )
