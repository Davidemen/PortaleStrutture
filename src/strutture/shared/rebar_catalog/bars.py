"""Bar-group area/count/callout helpers shared by the CA member tools."""
import math

from .diameters import bar_area


def bars_area(n: int, diameter_mm: float) -> float:
    """Total steel area of n bars of the given diameter [mm^2]."""
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    return n * bar_area(diameter_mm)


def bars_needed(as_req_mm2: float, diameter_mm: float) -> int:
    """Minimum whole number of bars of `diameter_mm` covering the required area As_req [mm^2]."""
    if as_req_mm2 < 0:
        raise ValueError(f"as_req_mm2 must be >= 0, got {as_req_mm2}")
    if as_req_mm2 == 0:
        return 0
    return math.ceil(as_req_mm2 / bar_area(diameter_mm))


def bar_callout(n: int, diameter_mm: float) -> str:
    """Drafting callout string, e.g. bar_callout(4, 16) -> "4ø16"."""
    if n < 0:
        raise ValueError(f"n must be >= 0, got {n}")
    diam_str = str(int(diameter_mm)) if float(diameter_mm).is_integer() else str(diameter_mm)
    return f"{n}ø{diam_str}"
