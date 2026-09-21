"""Generate the oracle fixture for `fond-trave-collegamento` (norma=NTC2018) from
`50_Calcolo travi di collegamento NTC 2018.xlsx`, sheet `Travi collegamento NTC2018`.
Run once: `uv run python tests/fixtures/gen_fond_trave_collegamento_ntc2018.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: spec golden case, soil B / topo T1.
    {},
    # Case 1: soil A, topo T2 -- SS/ST=1, small non-zero alpha (0.2).
    {"C6": "A", "C7": "T2"},
    # Case 2: soil C, topo T3.
    {"C6": "C", "C7": "T3"},
    # Case 3: soil D, topo T4 -- max stratigraphic/topographic amplification.
    {"C6": "D", "C7": "T4"},
    # Case 4: small section + large forces + max amplification -> compression check fails.
    {"C4": 0.35, "C5": 3.0, "C6": "D", "C7": "T4", "C11": 200, "C12": 200, "C22": 8000, "C23": 9000},
    # Case 5: few longitudinal bars, small diameter -> tension check fails (fixed mode; sheet bug keeps it OK).
    {"C13": 8, "C14": 2, "C22": 6000, "C23": 6500},
    # Case 6: wide spacing -> stirrup areal density check fails.
    {"C53": 400},
    # Case 7: long span, beta>1 -> high slenderness, check fails.
    {"C38": 9000, "C39": 2},
]

READ = [
    "C8", "C9", "C10", "C15", "C16", "C19", "C20", "C21", "C24",
    "C27", "C28", "C29", "C30", "C31", "C32", "C33", "C34",
    "C40", "C41", "C42", "C43", "C44", "C45",
    "C51", "C52", "C54", "C55", "C56",
]

if __name__ == "__main__":
    generate(
        "fond-travi-collegamento",
        "Travi collegamento NTC2018",
        CASES,
        READ,
        Path(__file__).parent / "fond_trave_collegamento_ntc2018_oracle.json",
    )
