"""Verified restatement (docs/architecture-phase2.md) of `steinbrenner_factors.py` (Steps 1-5,
`docs/specs/geo-cedimenti-elastico.md` Tool 2) — the aspect/depth ratios `a`, `b_centro`, `b_bordo`
and the Timoshenko & Goodier displacement-influence factor `IS = I1 + (1−2μ)/(1−μ)·I2`
(Timoshenko & Goodier, "Theory of Elasticity", 1970; Steinbrenner's I1/I2 sub-terms, as restated by
Bowles, "Foundation Analysis and Design"). Unlike the Newmark corner factor (`relazione_newmark_*`),
`I1`/`I2` ARE plain closed-form arithmetic — fully restated here, not cited as an identity.

`IS_bordo` uses `shared.soil_stress.steinbrenner_is(a/2, b_bordo, μ)` doubled (2 sub-rectangles
`B×(L/2)` sharing the loaded edge, Bowles), NOT the same single-rectangle call as `IS_centro`
(`steinbrenner_factors.py`'s own docstring: the sheet's single-rectangle corner factor for the edge
midpoint was a bug, fixed here) — the formula below reflects that: `m = a/2` throughout the bordo
term, restated (not folded into a bare literal `2`).

`B`/`H` are read through the package's own `boundary.to_m` (the input model stores them in
whichever `sistema_unita` the engineer chose, not always SI — `TimoshenkoGoodierOutput` does not
expose them, so they are read straight from the package's own conversion helper and the tool's own
default-H rule, exactly as the architecture brief allows for an intermediate not in the output)."""
import math

from strutture.shared.relazione import Passo, Traccia, Valore

from .boundary import to_m
from .models_tg import TimoshenkoGoodierInput, TimoshenkoGoodierOutput

# tool_timoshenko_goodier.H_SIGNIFICATIVO_DEFAULT_FACTOR, mirrored here (not imported) to avoid a
# circular import (that module imports this package's `relazione_timoshenko_goodier`).
H_SIGNIFICATIVO_DEFAULT_FACTOR = 5.0
PI_GRECO = math.pi
CLAUSOLA_IS = "Timoshenko & Goodier 1970 / Steinbrenner (Bowles, \"Foundation Analysis and Design\")"


def traccia_fattori(inputs: TimoshenkoGoodierInput, output: TimoshenkoGoodierOutput) -> Traccia:
    """5 passi: a, b_centro, b_bordo, IS_centro, IS_bordo."""
    b_m, h_m = b_m_da_inputs(inputs), h_m_da_inputs(inputs)
    return Traccia(
        titolo="Geometria e fattori di influenza allo spostamento (Timoshenko & Goodier)",
        passi=(
            _passo_a(inputs, output), _passo_b_centro(output, b_m, h_m), _passo_b_bordo(output, b_m, h_m),
            _passo_is_centro(inputs, output), _passo_is_bordo(inputs, output),
        ),
    )


def b_m_da_inputs(inputs: TimoshenkoGoodierInput) -> float:
    return to_m(inputs.b, inputs.sistema_unita)


def h_m_da_inputs(inputs: TimoshenkoGoodierInput) -> float:
    if inputs.h_significativo is not None:
        return to_m(inputs.h_significativo, inputs.sistema_unita)
    return H_SIGNIFICATIVO_DEFAULT_FACTOR * b_m_da_inputs(inputs)


def _passo_a(inputs: TimoshenkoGoodierInput, output: TimoshenkoGoodierOutput) -> Passo:
    unita = "m" if inputs.sistema_unita == "SI" else "cm"
    return Passo(
        simbolo="a", formula="L / B",
        valori=(
            Valore(simbolo="L", valore=inputs.l, unita=unita, descrizione="lunghezza della fondazione"),
            Valore(simbolo="B", valore=inputs.b, unita=unita, descrizione="larghezza della fondazione"),
        ),
        risultato=output.geometria.a, unita="-",
        nota="Rapporto di forma, riusato in entrambi i fattori IS (adimensionale: indipendente dal sistema di unità).",
    )


def _passo_b_centro(output: TimoshenkoGoodierOutput, b_m: float, h_m: float) -> Passo:
    return Passo(
        simbolo="b_centro", formula="2 * H / B",
        valori=(
            Valore(simbolo="H", valore=h_m, unita="m", descrizione="profondità significativa"),
            Valore(simbolo="B", valore=b_m, unita="m"),
        ),
        risultato=output.geometria.b_centro, unita="-",
        nota="Rapporto di profondità per il punto centrale (superposizione a 4 quadranti).",
    )


def _passo_b_bordo(output: TimoshenkoGoodierOutput, b_m: float, h_m: float) -> Passo:
    return Passo(
        simbolo="b_bordo", formula="H / B",
        valori=(
            Valore(simbolo="H", valore=h_m, unita="m"),
            Valore(simbolo="B", valore=b_m, unita="m"),
        ),
        risultato=output.geometria.b_bordo, unita="-",
        nota="Rapporto di profondità per il punto medio del bordo.",
    )


def _passo_is_centro(inputs: TimoshenkoGoodierInput, output: TimoshenkoGoodierOutput) -> Passo:
    geometria, fattori = output.geometria, output.fattori
    return Passo(
        simbolo="IS_centro", formula=_formula_is("a", "b_centro"),
        valori=(
            Valore(simbolo="a", valore=geometria.a, descrizione="rapporto di forma, calcolato sopra"),
            Valore(simbolo="b_centro", valore=geometria.b_centro, descrizione="rapporto di profondità al centro, calcolato sopra"),
            Valore(simbolo="μ", valore=inputs.mu, descrizione="coefficiente di Poisson del terreno"),
            Valore(simbolo="π", valore=PI_GRECO),
        ),
        risultato=fattori.is_centro, unita="-", clausola=CLAUSOLA_IS,
        nota="Fattore di influenza allo spostamento, superposizione a 4 quadranti uguali per raggiungere il centro.",
    )


def _passo_is_bordo(inputs: TimoshenkoGoodierInput, output: TimoshenkoGoodierOutput) -> Passo:
    geometria, fattori = output.geometria, output.fattori
    formula = f"2 * ({_formula_is('(a / 2)', 'b_bordo')})"
    return Passo(
        simbolo="IS_bordo", formula=formula,
        valori=(
            Valore(simbolo="a", valore=geometria.a, descrizione="rapporto di forma, calcolato sopra"),
            Valore(simbolo="b_bordo", valore=geometria.b_bordo, descrizione="rapporto di profondità al bordo, calcolato sopra"),
            Valore(simbolo="μ", valore=inputs.mu, descrizione="coefficiente di Poisson del terreno"),
            Valore(simbolo="π", valore=PI_GRECO),
        ),
        risultato=fattori.is_bordo, unita="-", clausola=CLAUSOLA_IS,
        nota="Punto medio del bordo: 2 sotto-rettangoli B×(L/2) affiancati lungo il bordo caricato "
             "(Bowles), non il fattore di spigolo del rettangolo intero — a dimezzato nel termine, non "
             "un fattore 2 applicato a un risultato diverso.",
    )


def _formula_i1(m: str, n: str) -> str:
    return (
        f"({m} * ln((1 + sqrt({m}^2 + 1)) * sqrt({m}^2 + {n}^2) / {m} / (1 + sqrt({m}^2 + {n}^2 + 1))) "
        f"+ ln(({m} + sqrt({m}^2 + 1)) * sqrt(1 + {n}^2) / ({m} + sqrt({m}^2 + {n}^2 + 1)))) / π"
    )


def _formula_i2(m: str, n: str) -> str:
    return f"({n} / (2 * π) * atan({m} / {n} / sqrt({m}^2 + {n}^2 + 1)))"


def _formula_is(m: str, n: str) -> str:
    return f"{_formula_i1(m, n)} + (1 - 2 * μ) / (1 - μ) * {_formula_i2(m, n)}"
