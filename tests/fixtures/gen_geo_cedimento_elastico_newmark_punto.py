"""Generate the oracle fixture for `geo-cedimento-elastico-newmark` (PUNTO) from sheet `500`
(cases 0-3), plus the free golden cases `400` and `350` (empty overrides, own built-in inputs) --
`docs/architecture-batch2.md` §6. Run once: `uv run python
tests/fixtures/gen_geo_cedimento_elastico_newmark_punto.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: spec's own golden case (500, empty override -> q=0.8, D=220, symmetric point).
    {},
    # Case 1: asymmetric point (e1 != e2) + a different embedment -- exercises the Fadum
    # superposition pairing bug the spec explicitly flags as untested at an asymmetric point.
    {"F7": 1000, "F8": 3000, "G1": 150},
    # Case 2: different comparison rectangle + a different point + lighter load.
    {"F5": 3000, "F6": 5000, "F7": 1500, "F8": 2500, "C1": 0.6, "G1": 100},
    # Case 3: deep embedment (base-relative layer boundaries shift into the 0-800cm integration
    # window) + a layer-2 modulus override -- exercises a second, different layer.
    {"G1": 800, "F16": 250},
    # Case 4: free golden case "400" (own built-in inputs, no override).
    {},
    # Case 5: free golden case "350" (own built-in inputs, no override).
    {},
]

READ = [
    "500!C2", "500!C3", "500!I3",
    "400!C2", "400!C3", "400!I3",
    "350!C2", "350!C3", "350!I3",
]

if __name__ == "__main__":
    generate(
        "geo-cedimenti",
        "500",
        CASES,
        READ,
        Path(__file__).parent / "geo_cedimento_elastico_newmark_punto_oracle.json",
    )
