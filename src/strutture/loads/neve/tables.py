"""Lookup tables from `Tabelle!A3:C6` (NTC2018 §3.4.2 zonal qsk values — given in the clause body,
no table number) and the `ExposureTable` (`Neve!A16:I20` / `Neve accumulo!A16:I20`, duplicated
identically on both sheets; NTC2018 §3.4.3 Tab. 3.4.I, exposure coefficient CE).

Zona strings match `strutture.shared.comuni.Comune.zona_neve`'s normalized spelling
("I (mediterranea)", no stray parenthesis) rather than `Tabelle!A4`'s literal
"I (mediterranea))" typo — see `docs/divergences/neve.md`.
"""
from typing import Final

ZONE_NEVE: Final[tuple[str, ...]] = ("I (alpina)", "I (mediterranea)", "II", "III")

# Tabelle!B3:B6 — constant qsk (kN/m2), NTC2018 §3.4.2, applied at/below 200 m a.s.l.
ZONE_QSK1: Final[tuple[tuple[str, float], ...]] = (
    ("I (alpina)", 1.5),
    ("I (mediterranea)", 1.5),
    ("II", 1.0),
    ("III", 0.6),
)

# Tabelle!C3:C6 — qsk2(as) = coeff * (1 + (as/denom_m)**2), NTC2018 §3.4.2, applied above 200 m a.s.l.
ZONE_QSK2_PARAMS: Final[tuple[tuple[str, tuple[float, float]], ...]] = (
    ("I (alpina)", (1.39, 728.0)),
    ("I (mediterranea)", (1.35, 602.0)),
    ("II", (0.85, 481.0)),
    ("III", (0.51, 481.0)),
)

QSK_BRANCH_THRESHOLD_M: Final[float] = 200.0  # NTC2018 §3.4.2 — qsk1 at/below 200 m, qsk2 formula above

# Tabelle!A3:A6's own row order/text, *including* Bug 5's stray paren on the mediterranea row.
# `Neve!H10`/`Neve accumulo!H10` VLOOKUP this range with the TRUE (approximate) match flag, so a
# caller's normalized "I (mediterranea)" (one char shorter, sorts before the typo'd key) matches
# the *previous* row "I (alpina)" instead — legacy-mode-only, see `docs/divergences/neve.md`.
ZONA_TABELLE_KEYS_LEGACY: Final[tuple[str, ...]] = ("I (alpina)", "I (mediterranea))", "II", "III")
ZONA_TABELLE_KEY_TO_CANONICAL: Final[dict[str, str]] = dict(zip(ZONA_TABELLE_KEYS_LEGACY, ZONE_NEVE, strict=True))

# Neve!A16:I20 / Neve accumulo!A16:I20 — NTC2018 §3.4.3, Tab. 3.4.I exposure coefficient CE
EXPOSURE_TABLE: Final[tuple[tuple[str, float], ...]] = (
    ("Battuta dai venti", 0.9),
    ("Normale", 1.0),
    ("Riparata", 1.1),
)
