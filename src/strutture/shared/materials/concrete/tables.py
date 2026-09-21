"""Lookup tables for the concrete class chain (NTC2018 Tab. 4.1.I; ca-fessurazione!MATERIALE CLS
A3:B14, ca-travi/ca-mensole/ca-pilastri!Tabelle M34:N41).

Merge C4/C5 (docs/architecture.md §3): the sheets fill fck down as `0.83*Rck` for every class —
`legacy_compat=True` reproduces that. The NTC2018 Tab. 4.1.I literal fck (the number in the class
name) is the code-standard source of truth; ca-fessurazione!C11 already carries this literal value
(35, not the fill-down's 37.35) for C35/45, which is how the bug was found (see divergence C1)."""
from .models import ConcreteClass

# NTC2018 Tab. 4.1.I — Rck (cube strength) per concrete class.
CONCRETE_RCK_MPA: tuple[tuple[ConcreteClass, float], ...] = (
    ("C8/10", 10.0), ("C12/15", 15.0), ("C16/20", 20.0), ("C20/25", 25.0),
    ("C25/30", 30.0), ("C28/35", 35.0), ("C30/37", 37.0), ("C32/40", 40.0),
    ("C35/45", 45.0), ("C40/50", 50.0), ("C45/55", 55.0), ("C50/60", 60.0),
)

# NTC2018 Tab. 4.1.I — literal fck (cylinder strength), the number in "C<fck>/<Rck>".
CONCRETE_FCK_LITERAL_MPA: tuple[tuple[ConcreteClass, float], ...] = (
    ("C8/10", 8.0), ("C12/15", 12.0), ("C16/20", 16.0), ("C20/25", 20.0),
    ("C25/30", 25.0), ("C28/35", 28.0), ("C30/37", 30.0), ("C32/40", 32.0),
    ("C35/45", 35.0), ("C40/50", 40.0), ("C45/55", 45.0), ("C50/60", 50.0),
)

# NTC2018 §4.1.2.1.1.1 — coefficiente riduttivo per resistenza di calcolo a lungo termine.
ALPHA_CC = 0.85
# NTC2018 Tab. 4.1.II (ca-travi!E3) — coefficiente di sicurezza del calcestruzzo.
GAMMA_C = 1.5
# ca-fessurazione!MATERIALE CLS C3 (=0.83*B3) — fill-down ratio fck = k * Rck (sheet bug, see above).
K_RCK_TO_FCK_LEGACY = 0.83
