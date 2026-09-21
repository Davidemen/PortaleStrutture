"""Generate the oracle fixture for `vita_riferimento`/`periodo_ritorno` from `sisma.xls[x]`, sheet `Sisma`.
Run once: `uv run python tests/fixtures/gen_ntc_site_seismic_vita_riferimento.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"I7": 50, "I8": "I"},
    {"I7": 50, "I8": "II"},
    {"I7": 50, "I8": "III"},
    {"I7": 50, "I8": "IV"},
    {"I7": 10, "I8": "II"},
    {"I7": 100, "I8": "IV"},
]

READ = ["I9", "I10", "E13", "E14", "E15", "E16"]

if __name__ == "__main__":
    generate(
        "sisma",
        "Sisma",
        CASES,
        READ,
        Path(__file__).parent / "ntc_site_seismic_vita_riferimento_oracle.json",
    )
