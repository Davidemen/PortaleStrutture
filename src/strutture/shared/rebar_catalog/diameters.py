"""Standard reinforcement bar diameters used across the CA (cemento armato) tool group.

Source: UNI EN 10080 / NTC2018 §11.3.2.1 commercial diameter series, as used throughout
`ca-travi`, `ca-mensole`, `ca-pilastri` (e.g. Tabelle!H12/H14 dropdowns for Ø_barre).
"""
import math

STANDARD_DIAMETERS_MM: tuple[float, ...] = (
    6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 25.0, 26.0, 28.0, 30.0, 32.0, 40.0,
)


def bar_area(diameter_mm: float) -> float:
    """Cross-sectional area of a single round bar, A = pi/4 * d^2 [mm^2]."""
    if diameter_mm <= 0:
        raise ValueError(f"diameter_mm must be > 0, got {diameter_mm}")
    return math.pi / 4.0 * diameter_mm**2
