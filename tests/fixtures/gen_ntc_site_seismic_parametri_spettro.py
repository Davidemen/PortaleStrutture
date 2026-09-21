"""Generate the oracle fixture for `periodi_spettro` from `sisma.xls[x]`, sheet `Sisma`.
Run once: `uv run python tests/fixtures/gen_ntc_site_seismic_parametri_spettro.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {"I26": "A", "I27": "T1", "I28": 0.272, "I29": 2.436, "I30": 0.098},
    {"I26": "B", "I27": "T1", "I28": 0.272, "I29": 2.436, "I30": 0.098},
    {"I26": "C", "I27": "T2", "I28": 0.35, "I29": 2.0, "I30": 0.15},
    {"I26": "D", "I27": "T3", "I28": 0.4, "I29": 2.2, "I30": 0.2},
    {"I26": "E", "I27": "T4", "I28": 0.3, "I29": 2.1, "I30": 0.12},
    {"I26": "B", "I27": "T1", "I28": 0.15, "I29": 2.0, "I30": 0.3},
]

READ = ["I31", "I48", "I49", "I50"]

if __name__ == "__main__":
    generate(
        "sisma",
        "Sisma",
        CASES,
        READ,
        Path(__file__).parent / "ntc_site_seismic_parametri_spettro_oracle.json",
    )
