"""Verified restatement (docs/architecture-phase2.md) of `centro.py` (CENTRO mode, `docs/specs/
geo-cedimenti-elastico.md` Tool 1 steps 2-6) — settlement at the geometric centre of the loaded
rectangle, `w = Σ Δz·Δσz(z)/E(z)` with `Δσz = under_center(q,B,L,z)` (Newmark 1942, 4-quadrant
superposition), plus the closed-form QA cross-check `w_QA` (`ic_center`).

`under_center` is algebraically `4·newmark_corner(q,B/2,L/2,z)` — the exact Newmark corner-of-
rectangle closed form needs a branch correction on the arctangent term
(`shared.soil_stress.newmark.newmark_corner` docstring) not restatable as one expression in the
notation grammar's whitelist (docs/architecture-phase2.md §2): each traced slice's `Δσz` cites the
already-computed value directly, the identity form the architecture brief allows for a value the
trace does not itself derive.

In STANDARD mode `w_QA` is algebraically identical to `w` (`centro.py`'s own docstring: both paths
use the same closed form, on the same depth grid) — the QA discrepancy is a legacy-only artefact
(two different hard-coded integration depths); the informative step below states this and is
explicitly NOT a normative check."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .models_newmark import CentroCedimento, NewmarkInput, NewmarkOutput, RigaNewmark
from .relazione_newmark_righe import traccia_fette

CLAUSOLA_NEWMARK = "Newmark 1942 (integrazione numerica, Poulos & Davis)"


def tracce_centro(inputs: NewmarkInput, output: NewmarkOutput) -> tuple[Traccia, ...]:
    assert output.centro is not None and output.righe_qa is not None
    traccia_principale = traccia_fette(
        "Tensione e cedimento per fette di profondità (centro fondazione)",
        output.righe, "w", output.centro.w_centro_mm, _formula_sigma_centro, CLAUSOLA_NEWMARK,
    )
    return (traccia_principale, _traccia_qa(output.centro))


def _formula_sigma_centro(riga: RigaNewmark, z_prec: float, etichetta: str) -> tuple[str, tuple[Valore, ...], str]:
    formula = f"Δσz_{etichetta}"
    valori = (
        Valore(
            simbolo=formula, valore=riga.delta_sigma_kPa, unita="kPa",
            descrizione="integrale di Newmark sotto il centro dell'area caricata, 4 quadranti uguali (Poulos & Davis)",
        ),
    )
    nota = (
        f"Valutato alla mezzeria della fetta, z_metà=(z_prec+z)/2={_testo((z_prec + riga.z_m) / 2)} m "
        f"(z={_testo(riga.z_m)} m resta il fondo della fetta). Calcolato da soil_stress.under_center: la "
        "correzione di ramo dell'arcotangente non è restituita qui in forma chiusa (vedi il modulo)."
    )
    return formula, valori, nota


def _traccia_qa(centro: CentroCedimento) -> Traccia:
    """Nessun `esito`: per costruzione (vedi docstring del modulo) non è una verifica normativa,
    solo un controllo interno di coerenza fra due formulazioni algebricamente equivalenti."""
    return Traccia(
        titolo="Controllo di coerenza (QA) — non è una verifica normativa",
        passi=(
            Passo(
                simbolo="w_QA", formula="w_QA",
                valori=(
                    Valore(
                        simbolo="w_QA", valore=centro.w_qa_cm, unita="cm",
                        descrizione="cedimento di controllo, stesso integrale con Ic di Boussinesq in forma chiusa (centro.py)",
                    ),
                ),
                risultato=centro.w_qa_cm, unita="cm",
                nota="In modalità standard w_QA usa la stessa formula chiusa e la stessa griglia di profondità "
                     "di w: è un controllo di coerenza interno, non una verifica normativa.",
            ),
            Passo(
                # `w_cm`, non il nudo `w`: la Traccia principale già stampa "w = ... = 31,2 mm" —
                # riusare "w" qui per lo stesso cedimento espresso in cm (3,12) metterebbe lo
                # stesso simbolo con due unità diverse in righe adiacenti (review finding
                # MISLEADING).
                simbolo="Δ%", formula="(w_cm - w_QA) / w_cm * 100",
                valori=(
                    Valore(simbolo="w_cm", valore=centro.w_centro_cm, unita="cm", descrizione="cedimento principale al centro fondazione (w della traccia precedente, qui in cm), calcolato sopra"),
                    Valore(simbolo="w_QA", valore=centro.w_qa_cm, unita="cm", descrizione="calcolato sopra"),
                ),
                risultato=centro.scarto_qa_pct, unita="%",
                nota="Scarto percentuale fra il percorso principale e il controllo QA; atteso 0% in modalità "
                     "standard (percorsi algebricamente identici).",
            ),
        ),
    )


def _testo(valore_m: float) -> str:
    return f"{valore_m:.4g}".replace(".", ",")
