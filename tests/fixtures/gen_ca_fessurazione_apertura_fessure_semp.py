"""Generate the oracle fixture for `ca-apertura-fessure-semplificata` from
`Verifica fessurazione - SLEF (X).xlsx`, sheet `Apertura delle fessure SEMP`.
Run once: `uv run python tests/fixtures/gen_ca_fessurazione_apertura_fessure_semp.py`.

The sheet's `D` columns (σs,lim) are free-typed numbers with no formula (see
docs/divergences/ca-fessurazione.md); each case below sets them to the exact Tab. C4.1.II value
for a chosen bar diameter (w3 curve for FRE, w2 curve for QPE), so the fixture also lets
`test_oracle_apertura_fessure_semplificata.py` check `sigma_limit_by_diameter` against the
sheet's own (matching, coincidental-by-construction) cached numbers.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: sheet's own cached example (ø=16 mm in all three sections).
    {"D21": 280, "D22": 240, "E21": 231, "E22": 218, "D43": 280, "D44": 240, "E43": 206, "E44": 233, "D66": 280, "D67": 240, "E66": 180, "E67": 171},
    # Case 1: distinct diameters per section, one failure per row.
    {"D21": 360, "D22": 320, "E21": 400, "E22": 300, "D43": 240, "D44": 222.22, "E43": 200, "E44": 250, "D66": 200, "D67": 160, "E66": 150, "E67": 170},
    # Case 2: boundary (limite == agente -> "non verificato") on several rows.
    {"D21": 320, "D22": 280, "E21": 320, "E22": 280, "D43": 300, "D44": 260, "E43": 100, "E44": 100, "D66": 260, "D67": 231.11, "E66": 260, "E67": 100},
    # Case 3: all rows comfortably pass.
    {"D21": 233.33, "D22": 213.33, "E21": 100, "E22": 100, "D43": 226.66, "D44": 204.4, "E43": 100, "E44": 100, "D66": 219.999, "D67": 196.36, "E66": 100, "E67": 100},
    # Case 4: large diameters, near-limit passes.
    {"D21": 213.333, "D22": 181.8, "E21": 213, "E22": 181, "D43": 206.6666, "D44": 167.24, "E43": 206, "E44": 167, "D66": 200, "D67": 160, "E66": 199, "E67": 159},
    # Case 5: mixed pass/fail, different diameter ordering.
    {"D21": 240, "D22": 222.22, "E21": 100, "E22": 250, "D43": 200, "D44": 160, "E43": 210, "E44": 100, "D66": 360, "D67": 320, "E66": 400, "E67": 100},
]

READ = [
    "D21", "D22", "F21", "G21", "F22", "G22",
    "D43", "D44", "F43", "G43", "F44", "G44",
    "D66", "D67", "F66", "G66", "F67", "G67",
]

if __name__ == "__main__":
    generate(
        "ca-fessurazione",
        "Apertura delle fessure SEMP",
        CASES,
        READ,
        Path(__file__).parent / "ca_fessurazione_apertura_fessure_semp_oracle.json",
    )
