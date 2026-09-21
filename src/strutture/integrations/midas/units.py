"""Force/length unit conversion (docs/integrations/MIDAS.md §1 UNIT, §2 rule 4): never guess —
explicit factor tables only, unknown units are an error."""
from typing import Final

_FORCE_TO_KN: Final[dict[str, float]] = {
    "N": 0.001,
    "KN": 1.0,
    "KGF": 0.00980665,
    "TONF": 9.80665,
    "LBF": 0.0044482216152605,
    "KIPS": 4.4482216152605,
}
_LENGTH_TO_M: Final[dict[str, float]] = {
    "M": 1.0,
    "CM": 0.01,
    "MM": 0.001,
    "FT": 0.3048,
    "IN": 0.0254,
}


def to_kn(value: float, unit: str) -> float:
    factor = _FORCE_TO_KN.get(unit.upper())
    if factor is None:
        raise ValueError(f"Unità di forza sconosciuta: {unit!r}.")
    return value * factor


def to_m(value: float, unit: str) -> float:
    factor = _LENGTH_TO_M.get(unit.upper())
    if factor is None:
        raise ValueError(f"Unità di lunghezza sconosciuta: {unit!r}.")
    return value * factor


def moment_factor(force_unit: str, length_unit: str) -> float:
    """kN·m per one (force_unit · length_unit), for converting MX/MY/MZ."""
    force_factor = _FORCE_TO_KN.get(force_unit.upper())
    length_factor = _LENGTH_TO_M.get(length_unit.upper())
    if force_factor is None or length_factor is None:
        raise ValueError(f"Unità sconosciuta: forza={force_unit!r}, lunghezza={length_unit!r}.")
    return force_factor * length_factor
