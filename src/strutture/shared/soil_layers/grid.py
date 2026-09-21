"""Depth-slicing helper replacing the sheets' hardcoded fill-down (10 cm step, fixed row count)."""
import math


def depth_grid(z_max_m: float, dz_m: float) -> tuple[float, ...]:
    """`(0, dz_m, 2*dz_m, ..., z_max_m)`: the depth slices from the surface/base down to
    `z_max_m` in steps of `dz_m` (last step may be shorter than `dz_m` if `z_max_m` is not an
    exact multiple). Stress functions need `z_m > 0`, so callers that skip the surface slice
    should use `depth_grid(...)[1:]`."""
    if dz_m <= 0:
        raise ValueError(f"depth_grid: dz_m must be > 0, got {dz_m}")
    if z_max_m <= 0:
        raise ValueError(f"depth_grid: z_max_m must be > 0, got {z_max_m}")
    ratio = z_max_m / dz_m
    rounded = round(ratio)
    steps = rounded if math.isclose(ratio, rounded, rel_tol=1e-9, abs_tol=1e-9) else math.floor(ratio)
    grid = tuple(step * dz_m for step in range(steps + 1))
    return grid if math.isclose(grid[-1], z_max_m, rel_tol=1e-9, abs_tol=1e-9) else (*grid, z_max_m)
