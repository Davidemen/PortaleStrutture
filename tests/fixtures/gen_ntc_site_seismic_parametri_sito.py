"""Generate the oracle fixture for `amplificazione` from `sisma.xls[x]`, sheet `Sisma`.
Run once: `uv run python tests/fixtures/gen_ntc_site_seismic_parametri_sito.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"I26": "A", "I27": "T1", "I28": 0.272, "I29": 2.436, "I30": 0.098},
    {"I26": "B", "I27": "T1", "I28": 0.272, "I29": 2.436, "I30": 0.098},
    {"I26": "C", "I27": "T2", "I28": 0.35, "I29": 2.0, "I30": 0.15},
    {"I26": "D", "I27": "T3", "I28": 0.4, "I29": 2.2, "I30": 0.2},
    {"I26": "E", "I27": "T4", "I28": 0.3, "I29": 2.1, "I30": 0.12},
    # High F0*ag pushes the raw Ss(B) formula below the sheet's (buggy) 0.40 clip: 1.40-0.40*2.5*1.1=0.30.
    {"I26": "B", "I27": "T1", "I28": 0.272, "I29": 2.5, "I30": 1.1},
    # Low F0*ag pushes each category to its upper clip.
    {"I26": "C", "I27": "T1", "I28": 0.272, "I29": 1.0, "I30": 0.01},
]

READ = ["I31", "I32", "I33", "I34"]

if __name__ == "__main__":
    generate(
        "sisma",
        "Sisma",
        CASES,
        READ,
        Path(__file__).parent / "ntc_site_seismic_parametri_sito_oracle.json",
    )
