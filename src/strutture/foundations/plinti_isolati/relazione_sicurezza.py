"""`relazione.py` (docs/architecture-phase2.md §6): sliding and overturning safety factors, EACH
on ITS OWN governing row — `mu_scorrimento_minimo`/`mu_ribaltamento_minimo` (`tool.py::_minimo`)
are the GLOBAL minimum across every famiglia, which is often a different `(nodo, combo)` than the
sigma-governing row traced by `relazione_azioni.py` (confirmed on the package's own 537-row golden
table: the sliding minimum shares the sigma-governing combo there, the overturning one does not).
Restating each highlight from ITS OWN row (found via `relazione_helpers.riga_governante_per`,
never re-derived) keeps every `Passo.risultato` exactly equal to the output it explains.

Sliding ("Scorrimento") is checked for every famiglia present (`checks_inviluppo.py` has no
gating), so its Passo is always a genuine comparison. Overturning ("Ribaltamento") is a valid
NTC2018 check only for the EQU-type famiglie (`checks_inviluppo.py` Fix 2: an STR-type gammaW
would inflate the stabilising moment); `_passo_mu_ribaltamento` restates the SAME ratio either way,
but only turns it into a comparison (`esito`/`clausola`) when a real Check exists for it."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .checks_inviluppo import EQU_FAMIGLIE, SAFETY_RATIO_LIMIT
from .input import PlintoIsolatoInput
from .models import PlintoIsolatoOutput
from .relazione_helpers import riga_governante_per, trova_riga
from .riga_verifica import RigaVerifica
from .scorrimento import GAMMA_R_SCORRIMENTO

# Review finding (WRONG_CLAUSE): entrambe le verifiche riusavano `checks_inviluppo.OVERTURNING_CLAUSE`
# ("NTC2018 §6.4.3.1", che è "Fondazioni su pali", non pertinente a un plinto superficiale). Costanti
# separate e corrette, locali a questo modulo di relazione (il Check reale resta invariato).
SCORRIMENTO_CLAUSE = "NTC2018 §6.4.2.1, Tab. 6.4.I (R3)"
RIBALTAMENTO_CLAUSE = "NTC2018 §6.4.2.1 con Tab. 2.6.I/6.2.I (EQU)"


def traccia_scorrimento(inputs: PlintoIsolatoInput, output: PlintoIsolatoOutput) -> Traccia | None:
    """`None` when no `reazioni` row has a defined sliding ratio (no horizontal demand anywhere,
    `mu_scorrimento_minimo` is `None`)."""
    entry = riga_governante_per(output.inviluppo, "scorrimento_min")
    if entry is None:
        return None
    riga = trova_riga(output.righe, entry.nodo, entry.combo)
    titolo = f"Scorrimento — combinazione governante {riga.combo} ({riga.famiglia})"
    return Traccia(titolo=titolo, passi=(_passo_mu_scorrimento(inputs, riga),))


def _passo_mu_scorrimento(inputs: PlintoIsolatoInput, riga: RigaVerifica) -> Passo:
    if riga.mu_scorrimento is None:
        raise ValueError(f"riga governante allo scorrimento senza rapporto mu (nodo {riga.nodo})")
    soddisfatta = riga.mu_scorrimento >= SAFETY_RATIO_LIMIT
    return Passo(
        simbolo="μ_scorr", formula=f"N * tan(φ) / (γ_R * sqrt(V_x^2 + V_y^2)) >= {SAFETY_RATIO_LIMIT:g}",
        valori=(
            Valore(simbolo="N", valore=riga.n_kN, unita="kN"),
            Valore(simbolo="φ", valore=inputs.phi_terreno_deg, unita="°", descrizione="angolo di attrito terreno-fondazione"),
            Valore(simbolo="γ_R", valore=GAMMA_R_SCORRIMENTO, descrizione="NTC2018 Tab. 6.4.I, R3 (scorrimento, approccio 2)"),
            Valore(simbolo="V_x", valore=riga.vx_kN, unita="kN"),
            Valore(simbolo="V_y", valore=riga.vy_kN, unita="kN"),
        ),
        risultato=riga.mu_scorrimento, unita="-", clausola=SCORRIMENTO_CLAUSE,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Coefficiente di sicurezza allo scorrimento sul piano di posa; N è il valore della "
             f"combinazione governante e include il γ_G della sua famiglia ({riga.famiglia}), anche "
             f"quando il peso proprio agisce a favore di sicurezza (aumenta l'attrito resistente).",
    )


def traccia_ribaltamento(inputs: PlintoIsolatoInput, output: PlintoIsolatoOutput) -> Traccia | None:
    """`None` when neither direction has a defined overturning ratio anywhere (both `Myy` and
    `Mxx` demand are zero on every row, `mu_ribaltamento_minimo` is `None`)."""
    candidati = [
        (entry, direzione)
        for direzione, grandezza in (("X", "ribaltamento_x_min"), ("Y", "ribaltamento_y_min"))
        for entry in (riga_governante_per(output.inviluppo, grandezza),)
        if entry is not None
    ]
    if not candidati:
        return None
    entry, direzione = min(candidati, key=lambda coppia: coppia[0].valore)
    riga = trova_riga(output.righe, entry.nodo, entry.combo)
    e_verifica_equ = riga.famiglia in EQU_FAMIGLIE
    # Review finding (MISLEADING): il titolo — sempre reso, a differenza di `nota` — si presentava
    # come "combinazione governante" anche quando la famiglia non è EQU e il rapporto è solo
    # informativo (γ_G della famiglia, non γ_G,stab=0,9 dell'equilibrio EQU).
    suffisso_informativo = "" if e_verifica_equ else " — valore informativo, non verifica EQU"
    titolo = f"Ribaltamento — combinazione governante {riga.combo} ({riga.famiglia}, direzione {direzione}){suffisso_informativo}"
    return Traccia(titolo=titolo, passi=(_passo_mu_ribaltamento(inputs, riga, direzione, e_verifica_equ),))


def _passo_mu_ribaltamento(inputs: PlintoIsolatoInput, riga: RigaVerifica, direzione: str, e_verifica_equ: bool) -> Passo:
    if direzione == "X":
        formula_base, risultato = "N * A_X / 2 / M_yy", riga.mu_ribaltamento_x
        valori = (
            Valore(simbolo="N", valore=riga.n_kN, unita="kN"),
            Valore(simbolo="A_X", valore=inputs.ax_m, unita="m"),
            Valore(simbolo="M_yy", valore=riga.myy_kNm, unita="kNm"),
        )
    else:
        formula_base, risultato = "N * B_Y / 2 / M_xx", riga.mu_ribaltamento_y
        valori = (
            Valore(simbolo="N", valore=riga.n_kN, unita="kN"),
            Valore(simbolo="B_Y", valore=inputs.by_m, unita="m"),
            Valore(simbolo="M_xx", valore=riga.mxx_kNm, unita="kNm"),
        )
    if risultato is None:
        raise ValueError(f"riga governante al ribaltamento {direzione} senza rapporto mu (nodo {riga.nodo})")
    formula = f"{formula_base} >= {SAFETY_RATIO_LIMIT:g}" if e_verifica_equ else formula_base
    esito = ("soddisfatta" if risultato >= SAFETY_RATIO_LIMIT else "non soddisfatta") if e_verifica_equ else ""
    clausola = RIBALTAMENTO_CLAUSE if e_verifica_equ else ""
    nota = ("Coefficiente di sicurezza al ribaltamento, momento stabilizzante su momento ribaltante."
            if e_verifica_equ else
            f"Valore informativo, non una verifica EQU: {RIBALTAMENTO_CLAUSE} richiede γ_G,stab=0,9 "
            f"sull'azione stabilizzante, mentre N qui include il γ_G della famiglia {riga.famiglia}.")
    return Passo(
        simbolo="μ_rib", formula=formula, valori=valori, risultato=risultato, unita="-",
        clausola=clausola, esito=esito, nota=nota,
    )
