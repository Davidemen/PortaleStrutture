"""EN1993-1-2 Table 3.1 — reduction factors for structural steel at elevated temperature, verbatim
(acciaio-incendio!resistenza!B35:D47 carries only the θ/ky/kE columns; kp,θ is the standard's own
third column, added here so the shared table is complete for any future consumer)."""

# (θ °C, ky,θ, kp,θ, kE,θ), ascending, exact tabulated rows (no pre-interpolation).
TABLE_3_1: tuple[tuple[float, float, float, float], ...] = (
    (20.0, 1.000, 1.000, 1.0000),
    (100.0, 1.000, 1.000, 1.0000),
    (200.0, 1.000, 0.807, 0.9000),
    (300.0, 1.000, 0.613, 0.8000),
    (400.0, 1.000, 0.420, 0.7000),
    (500.0, 0.780, 0.360, 0.6000),
    (600.0, 0.470, 0.180, 0.3100),
    (700.0, 0.230, 0.075, 0.1300),
    (800.0, 0.110, 0.050, 0.0900),
    (900.0, 0.060, 0.0375, 0.0675),
    (1000.0, 0.040, 0.0250, 0.0450),
    (1100.0, 0.020, 0.0125, 0.0225),
    (1200.0, 0.000, 0.0000, 0.0000),
)
