"""Top-level entry point: dispatches to the exact or superposition biaxial pressure method."""
from .biaxial import biaxial
from .models import BiaxialPressure, Metodo
from .sovrapposizione import sovrapposizione


def pressure(n_kn: float, mx_knm: float, my_knm: float, bx_m: float, by_m: float,
             metodo: Metodo = "esatto") -> BiaxialPressure:
    """Contact pressure of a bx_m * by_m rigid footing under N, Mx, My.

    metodo="esatto" (default): Navier inside the kern, no-tension plane solver outside it.
    metodo="sovrapposizione": the source spreadsheet's uniaxial-superposition approximation
    (docs/architecture-batch2.md §9-D2); a Tool with legacy_compat=True must force this metodo.
    """
    if metodo == "esatto":
        return biaxial(n_kn, mx_knm, my_knm, bx_m, by_m)
    if metodo == "sovrapposizione":
        return sovrapposizione(n_kn, mx_knm, my_knm, bx_m, by_m)
    raise ValueError(f"metodo sconosciuto: {metodo!r}")
