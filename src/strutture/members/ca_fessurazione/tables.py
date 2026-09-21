"""Local lookup tables for `ca_fessurazione` (Circ. 2019 §C4.1.6-C4.1.9), sheet `Apertura delle
fessure` S5:T6 / V5:W6 / P5:Q6 / Y5:Z7.

`K2_PER_SOLLECITAZIONE` deliberately has only the two entries the sheet's own `VLOOKUP(E6,
V5:W6, 2, FALSE)` [E40] actually ranges over. A third dropdown option exists in the sheet
("caso di trazione eccentrica (o per singole parti di sezione)", `V7`) whose formula
`W7=(W9+W10)/2/W9` divides by two empty cells (`#DIV/0!`) and sits outside the `V5:W6` lookup
range the working formula uses — a dead, unreachable branch. Per `docs/architecture.md` §6
("Dead cells across units ... ca-fessurazione `W7` ... DROP — do not port") it is not exposed
as an enum value at all; see `docs/divergences/ca-fessurazione.md`.
"""
from typing import Literal

TipoBarre = Literal["barre aderenza migliorata", "barre lisce"]
TipoSollecitazione = Literal["caso di flessione", "caso di trazione semplice"]
DurataCarico = Literal["breve durata", "lunga durata"]
ClasseFessurazione = Literal["w1 (0.20 mm)", "w2 (0.30 mm)", "w3 (0.40 mm)"]

# S5:T6 — k1 (coefficiente di aderenza), §C4.1.7.
K1_PER_TIPO_BARRE: tuple[tuple[TipoBarre, float], ...] = (
    ("barre aderenza migliorata", 0.8),
    ("barre lisce", 1.6),
)

# V5:W6 — k2 (tipo di sollecitazione), §C4.1.9. See module docstring for the dropped 3rd row.
K2_PER_SOLLECITAZIONE: tuple[tuple[TipoSollecitazione, float], ...] = (
    ("caso di flessione", 0.5),
    ("caso di trazione semplice", 1.0),
)

# P5:Q6 — kt (durata del carico), §C4.1.6.
KT_PER_DURATA_CARICO: tuple[tuple[DurataCarico, float], ...] = (
    ("breve durata", 0.6),
    ("lunga durata", 0.4),
)

# Y5:Z7 — wlim [mm] per classe di fessurazione, §4.1.2.2.4.5 / Tab. 4.1.IV.
WLIM_MM_PER_CLASSE: tuple[tuple[ClasseFessurazione, float], ...] = (
    ("w1 (0.20 mm)", 0.2),
    ("w2 (0.30 mm)", 0.3),
    ("w3 (0.40 mm)", 0.4),
)
