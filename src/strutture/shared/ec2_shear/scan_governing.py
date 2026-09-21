"""Generic exhaustive scan replacing the spreadsheet fill-down + MAX/VLOOKUP idiom used to find a governing
control-perimeter distance (docs/specs/ca-punzonamento.md step 5: 151 samples of a/d in [0.5, 2.0])."""
from collections.abc import Callable

from .models import GoverningScan


def scan_governing(f: Callable[[float], float], lo: float, hi: float, step: float) -> GoverningScan:
    """Evaluate f at lo, lo+step, ..., hi (inclusive) and return the sample maximizing f(x)."""
    if step <= 0:
        raise ValueError(f"step must be positive, got {step}")
    if hi < lo:
        raise ValueError(f"hi must be >= lo, got hi={hi} < lo={lo}")

    n_samples = round((hi - lo) / step) + 1
    samples = tuple(lo + i * step for i in range(n_samples))

    best_index = 0
    best_x = samples[0]
    best_value = f(samples[0])
    for index, x in enumerate(samples[1:], start=1):
        value = f(x)
        if value > best_value:
            best_index, best_x, best_value = index, x, value

    return GoverningScan(x=best_x, value=best_value, index=best_index)
