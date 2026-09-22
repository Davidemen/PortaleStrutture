"""Verified restatement (docs/architecture-phase2.md) of `giunti.py` (`pav-giunti`, geometric
rules-of-thumb for joint spacing — no code clause is stamped on the sheet, cited as CNR-DT211/2014
indicative practice per the tool's own `norm` field). Both checks compare an aspect ratio against
the SAME 1.5 threshold (`giunti.py`'s own docstring: the contraction-panel row's on-sheet label
reads "<1.2", a stale label, not a formula bug — the formula, 1.5 both rows, is kept). `Lmax`/
`t_iso`/`sp` are terminal outputs (nothing downstream depends on them) — cited in the checks' own
`nota`, not given a dedicated `Passo` (docs/architecture-phase2.md §6: only a coefficient/table
limit/intermediate that FEEDS a later formula needs its own step or named `Valore`)."""
from strutture.shared.relazione import Passo, Traccia, Valore

from .giunti import ASPECT_RATIO_LIMIT, GiuntiResult
from .models import PavimentoIndustrialeInput

CLAUSOLA = "CNR-DT211/2014 (regola pratica, nessuna clausola numerata sul foglio originale)"


def traccia_giunti(inputs: PavimentoIndustrialeInput, giunti: GiuntiResult) -> Traccia:
    """2 passi: verifica del pannello di contrazione, verifica del pannello di isolamento."""
    return Traccia(titolo="Giunti", passi=(_passo_contrazione(inputs, giunti), _passo_isolamento(inputs, giunti)))


def _passo_contrazione(inputs: PavimentoIndustrialeInput, giunti: GiuntiResult) -> Passo:
    soddisfatta = giunti.verifica_contrazione.passed
    l_max_mm = 10.0 * giunti.l_max_contrazione_cm
    return Passo(
        simbolo="a'/b'", formula=f"a' / b' < {ASPECT_RATIO_LIMIT:g}",
        valori=(
            Valore(simbolo="a'", valore=inputs.a_contrazione_m, unita="m", descrizione="dimensione del pannello di contrazione"),
            Valore(simbolo="b'", valore=inputs.b_contrazione_m, unita="m", descrizione="dimensione del pannello di contrazione"),
        ),
        risultato=giunti.rapporto_contrazione, unita="-", clausola=CLAUSOLA,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Rapporto di forma del pannello di contrazione. Dimensione massima ammessa del "
             f"pannello Lmax={giunti.l_max_contrazione_cm:.4g} cm ({l_max_mm:.4g} mm, 18·(h/10)+100), "
             "informativa, non confrontata da questo Check con le dimensioni effettive del pannello.",
    )


def _passo_isolamento(inputs: PavimentoIndustrialeInput, giunti: GiuntiResult) -> Passo:
    soddisfatta = giunti.verifica_isolamento.passed
    return Passo(
        simbolo="a/b", formula=f"a / b < {ASPECT_RATIO_LIMIT:g}",
        valori=(
            Valore(simbolo="a", valore=inputs.a_isolamento_m, unita="m", descrizione="dimensione del pannello di isolamento"),
            Valore(simbolo="b", valore=inputs.b_isolamento_m, unita="m", descrizione="dimensione del pannello di isolamento"),
        ),
        risultato=giunti.rapporto_isolamento, unita="-", clausola=CLAUSOLA,
        esito="soddisfatta" if soddisfatta else "non soddisfatta",
        nota=f"Rapporto di forma del pannello di isolamento. Spessore del giunto di isolamento "
             f"t_iso={giunti.spessore_isolamento_mm:.4g} mm (h/5) e apertura del giunto di dilatazione "
             f"sp={giunti.apertura_dilatazione_mm:.4g} mm (α·ΔT·max(a,b)), informativi, non legati a "
             "questo Check.",
    )
