"""Verified restatement (docs/architecture-phase2.md) of `punto.py` (PUNTO mode, `docs/specs/
geo-cedimenti-elastico.md` Tool 1 steps 1-7) — settlement at an arbitrary point O of the
O'-rectangle, `w_O = Σ Δz·Δσz(z)/E(z)` with `Δσz = under_point(...).total` (Fadum superposition of
4 signed sub-rectangle corners sharing O, `shared.soil_stress.point` docstring — fixes the sheet's
same-side pairing bug), plus the independent single-rectangle corner settlement `w_O'` at the
comparison point O' (`newmark_corner(side_p, side_q, ...)` directly, no superposition).

Both `under_point` and `newmark_corner` are exact Newmark closed forms with the same arctangent
branch correction as the CENTRO path (`relazione_newmark_centro.py` docstring) — not restatable as
one expression in the notation grammar; each traced slice's `Δσz` cites the already-computed value
directly."""
from strutture.shared.relazione import Traccia, Valore

from .models_newmark import NewmarkInput, NewmarkOutput, RigaNewmark
from .relazione_newmark_righe import traccia_fette

CLAUSOLA_NEWMARK = "Newmark 1942 (integrazione numerica, Poulos & Davis)"


def tracce_punto(inputs: NewmarkInput, output: NewmarkOutput) -> tuple[Traccia, ...]:
    assert output.punto is not None and output.righe_o_prime is not None
    traccia_o = traccia_fette(
        "Tensione e cedimento per fette di profondità (punto O)",
        output.righe, "w_O", output.punto.w_o_mm, _formula_sigma_o, CLAUSOLA_NEWMARK,
    )
    traccia_o_prime = traccia_fette(
        "Cedimento di riferimento nel vertice O' del rettangolo di confronto",
        output.righe_o_prime, "w_O'", output.punto.w_o_prime_mm, _formula_sigma_o_prime, CLAUSOLA_NEWMARK,
    )
    return (traccia_o, traccia_o_prime)


def _formula_sigma_o(riga: RigaNewmark, z_prec: float, etichetta: str) -> tuple[str, tuple[Valore, ...], str]:
    formula = f"Δσz_{etichetta}"
    valori = (
        Valore(
            simbolo=formula, valore=riga.delta_sigma_kPa, unita="kPa",
            descrizione="superposizione di Fadum, 4 sotto-rettangoli con vertice comune in O (Poulos & Davis)",
        ),
    )
    nota = _nota_mezzeria(riga, z_prec) + (
        " Calcolato da soil_stress.under_point: la correzione di ramo dell'arcotangente non è "
        "restituita qui in forma chiusa (vedi il modulo)."
    )
    return formula, valori, nota


def _formula_sigma_o_prime(riga: RigaNewmark, z_prec: float, etichetta: str) -> tuple[str, tuple[Valore, ...], str]:
    formula = f"Δσz_{etichetta}"
    valori = (
        Valore(
            simbolo=formula, valore=riga.delta_sigma_kPa, unita="kPa",
            descrizione="integrale di Newmark allo spigolo del rettangolo di confronto O'gbd, lati O'd e O'g interi",
        ),
    )
    nota = _nota_mezzeria(riga, z_prec) + (
        " Calcolato da soil_stress.newmark_corner: la correzione di ramo dell'arcotangente non è "
        "restituita qui in forma chiusa (vedi il modulo)."
    )
    return formula, valori, nota


def _nota_mezzeria(riga: RigaNewmark, z_prec: float) -> str:
    z_metà = (z_prec + riga.z_m) / 2
    return f"Valutato alla mezzeria della fetta, z_metà=(z_prec+z)/2={_testo(z_metà)} m (z={_testo(riga.z_m)} m resta il fondo della fetta)."


def _testo(valore_m: float) -> str:
    return f"{valore_m:.4g}".replace(".", ",")
