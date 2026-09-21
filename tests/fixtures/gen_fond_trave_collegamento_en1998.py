"""Generate the oracle fixture for `fond-trave-collegamento` (norma=EN1998) from
`50_Calcolo travi di collegamento NTC 2018.xlsx`, sheet `Travi colleg. EN 1998-1 e 5`.
Run once: `uv run python tests/fixtures/gen_fond_trave_collegamento_en1998.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: spec golden case, soil B, Ms=5.6 (TIPO2, exercises the S-column-selection bug).
    {},
    # Case 1: soil A, Ms=5.0 (TIPO1) -- alpha=0 -> NEd should be 0.
    {"C5": "A", "C6": 5.0},
    # Case 2: soil C, Ms=5.5 (boundary, still TIPO1).
    {"C5": "C", "C6": 5.5},
    # Case 3: soil D, Ms=6.5 (TIPO2, far past threshold).
    {"C5": "D", "C6": 6.5},
    # Case 4: N.floors > 3 -> hw,min=500, likely fails the C10 default 450mm height check.
    {"C49": 5},
    # Case 5: narrow section -> bw,min check fails.
    {"C9": 200},
    # Case 6: few longitudinal bars -> min longitudinal reinforcement check fails.
    {"C11": 8, "C12": 2},
    # Case 7: inclined stirrups (45 deg) + wide spacing -> min stirrup ratio check fails.
    {"C58": 45, "C62": 500},
]

READ = [
    "C7", "C8", "C13", "C14", "C17", "C18", "C19", "C22",
    "C25", "C26", "C27", "C28", "C29", "C30", "C31", "C32",
    "C38", "C39", "C40", "C41", "C42", "C43", "C44",
    "C47", "C48", "C50", "C51", "C52", "C53",
    "C60", "C61", "C63", "C64", "C65",
]

if __name__ == "__main__":
    generate(
        "fond-travi-collegamento",
        "Travi colleg. EN 1998-1 e 5",
        CASES,
        READ,
        Path(__file__).parent / "fond_trave_collegamento_en1998_oracle.json",
    )
