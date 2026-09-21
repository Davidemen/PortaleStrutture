"""EN1993-1-1 Table 3.1 — nominal fy/fu by grade and thickness band (t<=40mm, 40<t<=80mm).
acciaio-colonne-ec3!Materiali!H19:J23 only carries the t<=40mm value per grade (S235/S275/S355)
and never reads element thickness — `legacy_compat=True` reproduces that (see
docs/divergences/materials.md)."""
from .models import SteelGrade

SPESSORE_LIMITE_SOTTILE_MM = 40.0
SPESSORE_LIMITE_MASSIMO_MM = 80.0

# grade -> ((fyk, fuk) for t<=40mm, (fyk, fuk) for 40<t<=80mm), MPa.
STEEL_TABLE_MPA: tuple[tuple[SteelGrade, tuple[tuple[float, float], tuple[float, float]]], ...] = (
    ("S235", ((235.0, 360.0), (215.0, 360.0))),
    ("S275", ((275.0, 430.0), (255.0, 410.0))),
    ("S355", ((355.0, 510.0), (335.0, 470.0))),
    ("S420", ((420.0, 520.0), (390.0, 520.0))),
    ("S460", ((460.0, 540.0), (430.0, 540.0))),
)

E_MPA = 210000.0  # EN1993-1-1 §3.2.6 — modulo elastico E.
POISSON_RATIO = 0.3  # EN1993-1-1 §3.2.6 — coefficiente di Poisson ν.

# acciaio-colonne-ec3!Materiali!E4:E6 — coefficienti di sicurezza (caso non da ponte).
GAMMA_M0 = 1.05
GAMMA_M1_NON_PONTE = 1.05
GAMMA_M1_PONTE = 1.1
GAMMA_M2 = 1.25
