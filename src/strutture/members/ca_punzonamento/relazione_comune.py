"""Constants and shape-dependent formula fragments shared by `relazione.py`/`relazione_*.py`
(docs/architecture-phase2.md §6). Grammar-illegal UI symbols ("(a/d)*", "V_Rd,cs(1)", "n(f)") get a
grammar-legal internal identifier where a formula needs to reuse them, with the real symbol kept as
the defining `Passo.simbolo` (never parsed) — the same trick the ca-taglio-non-armato demo uses for
"N°"/"⌀" (see its own `relazione.py` docstring).
"""
from strutture.shared.relazione import Valore

from .effective_depth import column_shape
from .models import PunzonamentoInput

PI_GRECO = 3.141592653589793
GAMMA_C = 1.5  # EC2 Tab. 2.1N — fixed for this tool (not a user input): column_face/governing_capacity/
# perimeter_scan/shear_reinf_layout all hardcode the same 1.5, persistent/transient design situations.
KN_TO_N = 1000.0  # kN -> N, embedded as a visible formula literal (never hidden inside an opaque constant)
SCALA_N_A_KN = 0.001  # display factor for terms whose formula is naturally computed in N
RIDUZIONE_TERRENO_CLAUSE = "EN 1992-1-1 §6.4.4(2) eq. (6.48)"  # detrazione della reazione del terreno dal
# taglio (review finding, WRONG_FORMULA): NOT §6.4.5(3), che è v_Rd,max al filo del pilastro.


def valori_colonna(inputs: PunzonamentoInput) -> tuple[Valore, ...]:
    """The column/pile cross-section identifiers a formula needs: `D` alone (circular) or `a`/`b`
    (rectangular) — `effective_depth.column_shape`'s own convention (`lato_a_mm == 0` = circular)."""
    if column_shape(inputs.lato_a_mm) == "circ":
        return (Valore(simbolo="D", valore=inputs.diametro_mm, unita="mm", descrizione="diametro del pilastro/palo circolare"),)
    return (
        Valore(simbolo="a", valore=inputs.lato_a_mm, unita="mm", descrizione="lato 1 del pilastro"),
        Valore(simbolo="b", valore=inputs.lato_b_mm, unita="mm", descrizione="lato 2 del pilastro"),
    )


def formula_perimetro(lato_a_mm: float, *, distanza: str = "") -> str:
    """u(a) (EC2§6.4.2 rounded-rectangle/circle perimeter) at distance `distanza` (an identifier
    name) from the column face; `distanza=""` is the column face itself (dist=0, the `2*pi*dist`
    term vanishes and is omitted rather than written as `+ 2*pi*0`)."""
    if column_shape(lato_a_mm) == "circ":
        return f"π * (D + 2 * {distanza})" if distanza else "π * D"
    return f"2 * (a + b) + 2 * π * {distanza}" if distanza else "2 * (a + b)"


def formula_area(lato_a_mm: float, *, distanza: str) -> str:
    """A_a(a) (EC2§6.4.2 rounded-rectangle/circle enclosed area) at distance `distanza` (an
    identifier name, always given: unlike `formula_perimetro` this is never evaluated at dist=0)."""
    if column_shape(lato_a_mm) == "circ":
        return f"π * (D/2 + {distanza})^2"
    return f"a * b + 2 * (a + b) * {distanza} + π * {distanza}^2"


def formula_area_colonna(lato_a_mm: float) -> str:
    """A0, the column/pile footprint area itself (dist=0): `a*b` or `π*(D/2)^2`."""
    if column_shape(lato_a_mm) == "circ":
        return "π * (D/2)^2"
    return "a * b"


def valori_pi_se_circolare(lato_a_mm: float) -> tuple[Valore, ...]:
    """`π` is only an identifier of `formula_perimetro`/`formula_area_colonna` at distance 0 for a
    circular column (the rectangular branch has no `π` term there); at a non-zero distance BOTH
    branches use `π` (the `2*pi*dist` / `pi*dist^2` term), so callers add it unconditionally instead."""
    return (Valore(simbolo="π", valore=PI_GRECO),) if column_shape(lato_a_mm) == "circ" else ()
