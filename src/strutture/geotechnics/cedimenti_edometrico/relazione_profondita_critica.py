"""Verified restatement (docs/architecture-phase2.md) of `profondita_critica.py` (Step 6) — the
"significant depth" Z,crit past which the oedometric sum is cut off, criterion Δσv,q(z) = 0,1·σ'v0(z)
(a classical geotechnical significant-depth criterion, NOT an NTC2018 formula: §6.2.2 prescribes
WHICH checks must be performed, not this criterion — same lesson `relazione_cedimento.py` applies
to Δσ/ΔH, review finding WRONG_CLAUSE). The root is found by bisection (`shared.numeric.bisect`),
not a closed-form arithmetic expression the notation grammar can restate
(docs/architecture-phase2.md §2 is a whitelist of arithmetic operators and functions, no
root-finding): `Z_crit,calc` is cited directly from `ProfonditaCriticaResult`, the identity form
the architecture brief allows for a value the trace does not itself derive, with a `nota` naming
the defining criterion — the same convention as a table lookup.

`Z_crit,calc` is ALWAYS computed by `profondita_critica.py` regardless of a manual override
(`EdometricoInput.z_crit_input`), so it is always shown; `Z_crit` (the highlighted, actually-used
value, `ProfonditaCriticaResult.z_crit_utilizzato_m`) is either that same root or the manual
override, whichever the tool actually used — the two-branch step below states which."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .ingresso import converti_in_si
from .models import EdometricoInput
from .output import EdometricoOutput

CRITERIO_FRAZIONE = 0.1  # profondita_critica._CRITERIO_FRAZIONE, Δσv,q = 0.1·σ'v0
CLAUSOLA_Z_CRIT = "criterio della profondità significativa (classico, Δσv,q = 0,1·σ'v0)"


def traccia_profondita_critica(inputs: EdometricoInput, output: EdometricoOutput) -> Traccia:
    """2 passi: la radice calcolata Z,crit,calc e la profondità critica effettivamente utilizzata
    Z,crit (manuale se impostata, altrimenti la radice)."""
    return Traccia(
        titolo="Profondità critica (criterio Δσv,q = 0,1·σ'v0)",
        passi=(_passo_z_crit_calcolato(output), _passo_z_crit_utilizzato(inputs, output)),
    )


def _passo_z_crit_calcolato(output: EdometricoOutput) -> Passo:
    profondita = output.profondita_critica
    return Passo(
        simbolo="Z_crit,calc", formula="Z_crit,calc",
        valori=(
            Valore(
                simbolo="Z_crit,calc", valore=profondita.z_crit_calcolato_m, unita="m",
                descrizione="radice, calcolata per bisezione, di Δσv,q(z) = 0,1·σ'v0(z)",
            ),
        ),
        risultato=profondita.z_crit_calcolato_m, unita="m", clausola=CLAUSOLA_Z_CRIT,
        nota="Profondità significativa classica: sotto Z,crit l'incremento di tensione indotto dal "
             f"carico scende sotto il {CRITERIO_FRAZIONE:g}0·100=10% della tensione litostatica "
             "efficace. Radice trovata numericamente (bisezione), non una formula chiusa.",
    )


def _passo_z_crit_utilizzato(inputs: EdometricoInput, output: EdometricoOutput) -> Passo:
    profondita = output.profondita_critica
    si = converti_in_si(inputs)
    manuale = si.z_crit_input_m is not None
    identificatore = "Z_crit,input" if manuale else "Z_crit,calc"
    descrizione = (
        "profondità critica manuale d'ingresso, sovrascrive il criterio automatico"
        if manuale else "radice calcolata sopra"
    )
    nota = (
        "Valore impostato manualmente dall'ingegnere (qui più profondo della griglia di calcolo: "
        "il taglio della somma dei cedimenti è di fatto disattivato)."
        if manuale and profondita.z_crit_utilizzato_m >= si.z_max_m
        else "Valore impostato manualmente dall'ingegnere." if manuale
        else "Valore calcolato automaticamente (nessun Z,crit manuale impostato)."
    )
    return Passo(
        simbolo="Z_crit", formula=identificatore,
        valori=(Valore(simbolo=identificatore, valore=profondita.z_crit_utilizzato_m, unita="m", descrizione=descrizione),),
        risultato=profondita.z_crit_utilizzato_m, unita="m", clausola=CLAUSOLA_Z_CRIT,
        nota=f"Profondità critica utilizzata per il taglio della somma dei cedimenti. {nota}",
    )
