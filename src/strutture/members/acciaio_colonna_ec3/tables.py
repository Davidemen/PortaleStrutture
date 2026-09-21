"""Lookup tables and hardcoded constants (acciaio-colonne-ec3!Materiali!H19:J23; EN1993-1-1 Tab. 6.1).

The `Materiali` grade table is specific to this workbook (it mixes EN grades S235/S275/S355 with
two non-EN tubular-micropile grades Q235/Q345); it is intentionally NOT the same as
`strutture.shared.materials.structural_steel` (which only covers S235..S460), so it is kept local
to this tool.
"""
from .models import GradoAcciaioColonna

# Materiali!H19:J23 — VLOOKUP(grado, ..., col) table. (fyk, fuk), MPa.
TABELLA_ACCIAIO_MPA: tuple[tuple[GradoAcciaioColonna, tuple[float, float]], ...] = (
    ("S235", (235.0, 360.0)),
    ("S275", (275.0, 430.0)),
    ("S355", (355.0, 510.0)),
    ("Q345", (345.0, 450.0)),
    ("Q235", (235.0, 360.0)),
)

# EN1993-1-1 Tab. 6.1 — imperfection factor alpha by buckling curve letter.
ALPHA_PER_CURVA: dict[str, float] = {"a": 0.21, "b": 0.34, "c": 0.49, "d": 0.76}

# EC3-EN Annex A / general case (§6.3.2.2) recommended values, column-check!AF43/AF44.
LAMBDA_LT_0 = 0.4
BETA_LT = 0.75

# EN1993-1-1 Tab. 6.2 — flexural buckling curve selection thresholds for rolled I/H sections.
LIMITE_HB_TAB_6_2 = 1.2
LIMITE_TF_SOTTILE_MM = 40.0
LIMITE_TF_SPESSA_MM = 100.0

# column-check!AC27 vs AD27 — shear buckling slenderness check, EN1993-1-5 §5.1(2).
FATTORE_LIMITE_HW_T = 72.0

ESPONENTE_INTERAZIONE_YY = 2.0  # column-check!B52 — sezioni a I/H, §6.2.9.1 Tab. 6.7-like exponent.
