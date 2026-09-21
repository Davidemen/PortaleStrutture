"""Small wrapper around `shared.rebar_catalog.bars_area` tolerant of the sheet's `n=0, Ø=0`
default (H18/H19, H24/H25 defaults on the `Mensola tozza` sheet): `bars_area` itself rejects a
zero diameter regardless of count, but "no bars of some placeholder diameter" is a legitimate
zero-area input here."""
from strutture.shared.rebar_catalog import bars_area


def bars_area_or_zero(n: int, diameter_mm: float) -> float:
    """Total steel area of `n` bars of `diameter_mm`, or 0 when `n == 0` (diameter ignored)."""
    if n == 0:
        return 0.0
    return bars_area(n, diameter_mm)
