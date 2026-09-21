"""Small numeric helpers replacing spreadsheet idioms."""
from collections.abc import Callable

DEFAULT_TOLERANCE = 1e-9
MAX_ITERATIONS = 200


def clamp(value: float, low: float, high: float) -> float:
    if low > high:
        raise ValueError(f"clamp bounds inverted: {low} > {high}")
    return max(low, min(high, value))


def lerp(x: float, x0: float, y0: float, x1: float, y1: float) -> float:
    """Linear interpolation of y at x between (x0, y0) and (x1, y1)."""
    if x1 == x0:
        raise ValueError("lerp needs two distinct abscissae")
    return y0 + (y1 - y0) * (x - x0) / (x1 - x0)


def bisect(f: Callable[[float], float], low: float, high: float, tol: float = DEFAULT_TOLERANCE) -> float:
    """Root of f in [low, high] (replaces Excel goal-seek). f(low) and f(high) must have opposite signs."""
    f_low, f_high = f(low), f(high)
    if f_low == 0:
        return low
    if f_high == 0:
        return high
    if f_low * f_high > 0:
        raise ValueError(f"bisect: no sign change in [{low}, {high}]")
    for _ in range(MAX_ITERATIONS):
        mid = (low + high) / 2
        f_mid = f(mid)
        if f_mid == 0 or (high - low) / 2 < tol:
            return mid
        low, high, f_low = (mid, high, f_mid) if f_low * f_mid > 0 else (low, mid, f_low)
    raise ValueError("bisect: did not converge")


def fixpoint(f: Callable[[float], float], x0: float, tol: float = DEFAULT_TOLERANCE) -> float:
    """x such that x = f(x), by direct iteration (replaces Excel iterative circular references)."""
    x = x0
    for _ in range(MAX_ITERATIONS):
        x_next = f(x)
        if abs(x_next - x) <= tol * max(1.0, abs(x_next)):
            return x_next
        x = x_next
    raise ValueError("fixpoint: did not converge")
