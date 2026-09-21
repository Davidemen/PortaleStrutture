"""Step 4: base contact pressure, dispatching to the exact or superposition method (docs/architecture-batch2.md
§9-D2). Thin wrapper over `shared.footing_pressure`: `legacy_compat=True` forces the sheet's
superposition method regardless of the user's `metodo_pressioni` choice."""
from strutture.shared.footing_pressure import BiaxialPressure, Metodo, pressure


def pressione_contatto(n_kN: float, mxx_kNm: float, myy_kNm: float, ax_m: float, by_m: float, *,
                        metodo_pressioni: Metodo, legacy_compat: bool) -> BiaxialPressure:
    """Contact pressure of the ax_m * by_m footing under N, Mxx (bends about X), Myy (bends about Y)."""
    metodo: Metodo = "sovrapposizione" if legacy_compat else metodo_pressioni
    return pressure(n_kN, mxx_kNm, myy_kNm, ax_m, by_m, metodo=metodo)
