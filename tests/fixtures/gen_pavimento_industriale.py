"""Generate the oracle fixture for `fond-pavimento-industriale` from
`10x_Pavimento industriale CNR_DT211-2014.xlsx`, sheet `carichi_distribuiti_concentrati`.
Reads only the "ruota motrice" (K:O) concentrated-load block -- the "ruote anteriori" (Q:U) block
uses identical formulas on different cells and is not needed to exercise every branch.
Run once: `uv run python tests/fixtures/gen_pavimento_industriale.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: spec golden case (defaults).
    {},
    # Case 1: different sottofondo lookup + slab geometry -> shifts kT, d, lambda, l, W.
    {"C24": "soffice", "C27": 250, "C28": 25},
    # Case 2: different concrete class -> shifts the whole materiali chain (fck/fcd/fctm/fcfk/fcfd).
    {"C4": "C35/45"},
    # Case 3: large contact patch (rr/h >= 1.724) -> no Westergaard radius correction (b = rr).
    {"L10": 1000, "M10": 1000, "N10": 1000, "L11": 1000, "M11": 1000, "N11": 1000},
    # Case 4: thick slab -> k = 1+sqrt(200/d) stays below the 2.0 clamp (unclamped branch).
    {"C27": 300, "C28": 35},
]

READ = [
    # materiali
    "C5", "C6", "C8", "C9", "C10", "C11", "C12", "C13", "C14", "C19", "C21",
    # sottofondo
    "C26", "C29", "C30", "C31", "C32", "C33", "C34", "C35",
    # distribuiti
    "G9", "G10", "G11", "G12", "G16", "H16", "G17", "H17",
    "G21", "H21", "G22", "H22", "G26", "H26", "G27", "H27", "G33", "H33", "G34", "H34", "G35", "H35",
]
for col in ("L", "M", "N"):  # concentrated loads, "ruota motrice" block: centro/bordo/spigolo
    READ += [
        f"{col}12", f"{col}13", f"{col}14", f"{col}17", f"{col}22", f"{col}23",
        f"{col}28", f"{col}29", f"{col}30", f"{col}31", f"{col}32",
        f"{col}33", f"{col}34", f"{col}35", f"{col}36", f"{col}40", f"{col}41",
        f"{col}47", f"{col}48", f"{col}49",
    ]
READ += ["G39", "I39", "G40", "G41", "G47", "I47", "G50"]

if __name__ == "__main__":
    generate(
        "pavimento-industriale",
        "carichi_distribuiti_concentrati",
        CASES,
        READ,
        Path(__file__).parent / "pavimento_industriale_oracle.json",
    )
