"""Generate the oracle fixture for `geo-cedimento-elastico-timoshenko-goodier` from
`Elastico_Timoshenko_Goodier_3` (the only complete draft -- `_2`/v1 are dead, see spec). Run once:
`uv run python tests/fixtures/gen_geo_cedimento_elastico_timoshenko_goodier.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: spec's own golden case (empty override).
    {},
    # Case 1: different mu and IF factors, lighter load.
    {"F5": 0.20, "U33": 0.55, "U36": 0.60, "C6": 0.75},
    # Case 2: bigger, deeper-embedded rectangle, higher load.
    {"C4": 150, "C5": 200, "F4": 80, "C6": 1.1, "U33": 0.70, "U36": 0.82},
    # Case 3: H significativo overridden smaller than the 5*B default.
    {"C7": 300},
    # Case 4: layer-1 modulus overridden.
    {"G11": 220, "C6": 0.5},
]

READ = ["H11", "N15", "P15", "N17", "P17", "F6", "N12", "P12", "C7"]

if __name__ == "__main__":
    generate(
        "geo-cedimenti",
        "Elastico_Timoshenko_Goodier_3",
        CASES,
        READ,
        Path(__file__).parent / "geo_cedimento_elastico_timoshenko_goodier_oracle.json",
    )
