"""Regenerate tests/fixtures/muro_sostegno_oracle.json from `Muro di sostegno DM2018.xlsx`,
sheet "Tratto A". Run with: uv run python tests/fixtures/gen_muro_sostegno_oracle.py

`categoria_sottosuolo`/`categoria_topografica` are kept fixed at Tratto A's own values (C/T1) in
every case: I18 (Ss) is a hardcoded, non-live input in Tratto A (see docs/specs/muro-sostegno.md
"Tratto A vs B"), so overriding ag/F0 without also overriding I18 would desync the sheet from the
tool's live Ss(category, ag, F0). The live Ss/ST formula itself is oracle-tested independently in
tests/shared/ntc_site_seismic/test_oracle_parametri_sito.py; this fixture instead exercises the
downstream physics (Coulomb/Mononobe-Okabe, ribaltamento/scorrimento, pressioni) that IS specific
to muro-sostegno.
"""
from pathlib import Path

from extract.fixtures import generate

BASE = {
    "I4": 19.7, "I5": 15.6, "I6": 30.69, "I7": 0, "I8": 0, "I9": 90, "I10": 0,
    "I15": 0.136, "I16": 2.419, "I18": 1.5, "I19": 1, "I21": 0.24, "I22": 1,
    "I25": 25, "I26": 0.49, "I27": 0.25, "I28": 0.3, "I29": 2.4, "I31": 0.26, "I32": 1.15, "I38": 2,
    "I135": 0.06, "I136": 450, "I139": 0.2, "I156": 0.06, "I157": 0.2,
}

CASES = [
    {},  # Tratto A as cached (spec §8 golden case, recomputed as a LibreOffice regression check)
    {"I6": 25.0, "I8": 22.0},  # beta > phi_d for GEO/EQU (phi_d=20) but not STR (phi_d=25): both Ka branches
    {"I7": 15.0},  # delta > 0 -> nonzero SV.q/SV.terr components
    {"I10": 12.0},  # omega != 0 -> full OS numerator/denominator
    {"I9": 75.0},  # psi != 90 deg -> inclined internal face
    {"I38": 5.0, "I32": 0.85},  # surcharge + smaller heel -> eccentricity beyond B/6, still e < B/2 (static)
    {"I21": 0.35, "I22": 1.15},  # different beta_m/gamma_e -> seismic kh/thrust scaling
    {"I26": 0.4, "I31": 0.4, "I32": 0.9},  # different overall geometry (still e < B/2 for every combo)
]

# Tool 1 (rows 45/46/47/80/81), Tool 2 (rows 56/57/58/87/88), Tool 3 (rows 67/68/69/94/95),
# Tool 4 (rows 143/144/145/149/150), Tool 5 (rows 161/162/163/167/168), Tool 6 (179/180/181/185/186).
_TOOL1_COLS = ["G", "I", "K", "M", "Q", "S"]
_TOOL1_SISMA_EXTRA = ["Y", "Z", "AA"]
_TOOL2_COLS = ["B", "M", "N", "O", "Q", "R", "S"]
_TOOL3_COLS = ["D", "E", "G", "H", "M", "N", "O", "Q", "R", "S"]
_TOOL4_COLS = ["C", "D", "E", "F", "G", "H"]
_TOOL5_COLS = ["C", "D", "E", "F", "G", "H", "I", "J", "K"]
_TOOL6_COLS = ["C", "D", "E", "F", "G", "H", "I", "J", "K", "M"]

READ = ["I18", "I19", "I20", "H151", "I151", "K169", "M169", "M187", "N187"]
_COMBO_ROWS = [
    (45, 56, 67, 143, 161, 179, False),
    (46, 57, 68, 144, 162, 180, False),
    (47, 58, 69, 145, 163, 181, False),
    (80, 87, 94, 149, 167, 185, True),
    (81, 88, 95, 150, 168, 186, True),
]
for tool1_row, tool2_row, tool3_row, tool4_row, tool5_row, tool6_row, sismica in _COMBO_ROWS:
    READ += [f"{col}{tool1_row}" for col in _TOOL1_COLS]
    if sismica:
        READ += [f"{col}{tool1_row}" for col in _TOOL1_SISMA_EXTRA]
    READ += [f"{col}{tool2_row}" for col in _TOOL2_COLS]
    READ += [f"{col}{tool3_row}" for col in _TOOL3_COLS]
    READ += [f"{col}{tool4_row}" for col in _TOOL4_COLS]
    READ += [f"{col}{tool5_row}" for col in _TOOL5_COLS]
    READ += [f"{col}{tool6_row}" for col in _TOOL6_COLS]

if __name__ == "__main__":
    generate("muro-sostegno", "Tratto A", [{**BASE, **case} for case in CASES], READ, Path(__file__).parent / "muro_sostegno_oracle.json")
