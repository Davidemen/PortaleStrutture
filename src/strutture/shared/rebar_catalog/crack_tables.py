"""Crack-control steel-stress limit tables, NTC2018 Tab. C4.1.II (sigma_s max vs bar diameter,
per crack-width class w1/w2/w3) and Tab. C4.1.III (sigma_s max vs bar spacing).

Source of the diameter table: `ca-travi`/`ca-mensole` sheet 'Tabelle'!N67:R93 (two stacked
blocks per column — a coarse 6-row block at N67:Q72 plus a fine-grained extension at
N73:R93 — merged here into one ascending-by-diameter table per w-class). The sheet looks
these up with an exact-match VLOOKUP against the bar diameter (fragile: any diameter not in
the table raises #N/A); `legacy_compat=True` reproduces that. Code-standard mode
(`legacy_compat=False`) interpolates linearly between the two bracketing diameters, per
`shared.tables.interp_lookup`.

The spacing table (Tab. C4.1.III / EN1992-1-1 Table 7.3N) is not present in the sheets
checked for this package (ca-travi/ca-mensole/ca-pilastri `Tabelle` — see
docs/divergences/shared-ca.md); values below are the standard EC2/NTC2018 Table 7.3N figures,
one column per crack-width class, keyed spacing [mm] -> sigma_s limit [MPa] (i.e. inverted
from the norm's native sigma_s -> max-spacing direction, so lookup takes the spacing actually
used and returns the steel-stress limit it satisfies). The w2 (wk=0.3mm) column is the one
explicitly checked cell-by-cell; w1 (wk=0.2mm) and w3 (wk=0.4mm) are the same published table
inverted the same way (see docs/divergences/shared-ca.md).
"""
from typing import Literal

from strutture.shared.tables import exact_lookup, interp_lookup

CrackWidthClass = Literal["w1", "w2", "w3"]

# Tabelle!N67:R93 merged per w-class, ascending by bar diameter [mm] -> sigma_s limit [MPa].
_DIAMETER_LIMITS: dict[CrackWidthClass, tuple[tuple[float, float], ...]] = {
    "w3": (
        (10.0, 360.0), (12.0, 320.0), (14.0, 300.0), (16.0, 280.0), (18.0, 260.0),
        (20.0, 240.0), (22.0, 233.33), (24.0, 226.66), (26.0, 219.999), (28.0, 213.333),
        (30.0, 206.6666), (32.0, 200.0), (40.0, 160.0),
    ),
    "w2": (
        (8.0, 360.0), (10.0, 320.0), (12.0, 280.0), (14.0, 260.0), (16.0, 240.0),
        (18.0, 231.11), (20.0, 222.22), (22.0, 213.33), (24.0, 204.4), (25.0, 200.0),
        (26.0, 196.36), (28.0, 181.8), (30.0, 167.24), (32.0, 160.0),
    ),
    "w1": (
        (6.0, 320.0), (8.0, 280.0), (10.0, 260.0), (12.0, 240.0), (14.0, 220.0),
        (16.0, 200.0), (18.0, 191.12), (20.0, 182.24), (22.0, 173.36), (24.0, 164.48),
        (25.0, 160.0),
    ),
}

# EN1992-1-1 Table 7.3N / NTC2018 Tab. C4.1.III, inverted per w-class: bar spacing [mm] ->
# max sigma_s [MPa]. w2 (wk=0.3mm) verified against the finding's worked example; w1/w3 are the
# same published table's other two columns, inverted the same way.
_SPACING_LIMITS: dict[CrackWidthClass, tuple[tuple[float, float], ...]] = {
    "w3": ((100.0, 360.0), (150.0, 320.0), (200.0, 280.0), (250.0, 240.0), (300.0, 200.0)),
    "w2": ((50.0, 360.0), (100.0, 320.0), (150.0, 280.0), (200.0, 240.0), (250.0, 200.0), (300.0, 160.0)),
    "w1": ((50.0, 280.0), (100.0, 240.0), (150.0, 200.0), (200.0, 160.0)),
}


def sigma_limit_by_diameter(diameter_mm: float, w_class: CrackWidthClass, *, legacy_compat: bool = False) -> float:
    """Max steel stress sigma_s [MPa] for crack-width class `w_class` given the bar diameter.

    `legacy_compat=True` reproduces the sheet's exact-match VLOOKUP (raises KeyNotFound for any
    diameter not in Tab. C4.1.II); `legacy_compat=False` interpolates between bracketing rows.
    """
    if diameter_mm <= 0:
        raise ValueError(f"diameter_mm must be > 0, got {diameter_mm}")
    table = _DIAMETER_LIMITS[w_class]
    return exact_lookup(table, diameter_mm) if legacy_compat else interp_lookup(table, diameter_mm)


def sigma_limit_by_spacing(spacing_mm: float, w_class: CrackWidthClass, *, legacy_compat: bool = False) -> float:
    """Max steel stress sigma_s [MPa] for crack-width class `w_class` given bar spacing
    (interferro), Tab. C4.1.III.

    `legacy_compat=True` reproduces exact-match lookup behaviour; `legacy_compat=False`
    interpolates. See module docstring for the table's per-w-class source.
    """
    if spacing_mm <= 0:
        raise ValueError(f"spacing_mm must be > 0, got {spacing_mm}")
    table = _SPACING_LIMITS[w_class]
    return exact_lookup(table, spacing_mm) if legacy_compat else interp_lookup(table, spacing_mm)
