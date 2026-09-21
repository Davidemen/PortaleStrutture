"""Generate the oracle fixture for `geo-cedimento-elastico-newmark` (CENTRO) from
`Elastico_centrale_Newmark`. Run once: `uv run python
tests/fixtures/gen_geo_cedimento_elastico_newmark_centro.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: spec's own golden case (empty override -> B=350,L=500,q=0.5,D=110).
    {},
    # Case 1: bigger, shallower, lighter-loaded footing, L<B.
    {"D1": 500, "D2": 300, "D3": 0.35, "G1": 90},
    # Case 2: square footing, deep embedment, high pressure.
    {"D1": 250, "D2": 250, "D3": 0.65, "G1": 180},
    # Case 3: layer-1 modulus overridden directly (literal, not the baked "=kPa/(10*9.80665)" formula).
    {"D1": 400, "D2": 600, "D3": 0.4, "G1": 110, "F7": 60},
]

READ = ["U6", "Z6"]

if __name__ == "__main__":
    generate(
        "geo-cedimenti",
        "Elastico_centrale_Newmark",
        CASES,
        READ,
        Path(__file__).parent / "geo_cedimento_elastico_newmark_centro_oracle.json",
    )
