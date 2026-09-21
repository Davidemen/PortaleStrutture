"""Lookup tables specific to the tie-beam sheets (`Tabelle!M117:P134`), not shared with other
tools: the α coefficient of the `NEd = amax·Nsd·α` formula (NTC and EN differ) and the EN1998-1
soil-category spectral table (its S values differ from the NTC `ntc_site_seismic` ones)."""
from .models import CategoriaSottosuoloTravi

# Tabelle!M118:P121 col P — coefficiente α, NTC2018 §7.2.5 (Circolare 2019 Tab. C7.11.I).
ALPHA_NTC: tuple[tuple[CategoriaSottosuoloTravi, float], ...] = (
    ("A", 0.2), ("B", 0.3), ("C", 0.4), ("D", 0.6),
)

# Tabelle!M131:P134 — EN1998-1 soil table: N=S tipo 1, O=S tipo 2, P=α (EN1998-5 §5.4.1.2).
EN1998_SOIL_TABLE: tuple[tuple[CategoriaSottosuoloTravi, tuple[float, float, float]], ...] = (
    ("A", (1.0, 1.0, 0.0)),
    ("B", (1.2, 1.35, 0.3)),
    ("C", (1.15, 1.5, 0.4)),
    ("D", (1.35, 1.8, 0.6)),
)
