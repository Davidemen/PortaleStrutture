"""Generate the oracle fixture for `ca-sle-limitazione-tensioni` from
`Verifica fessurazione - SLEF (X).xlsx`, sheet `Limitazione delle tensioni`.
Run once: `uv run python tests/fixtures/gen_ca_fessurazione_limitazione_tensioni.py`.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: spec §8 golden values (all three sections "ok").
    {"C6": 45, "C8": 450, "D13": 4.5, "D14": 4.5, "D15": 255.8, "D21": 10, "D22": 5.3, "D23": 274, "D29": 6, "D30": 6, "D31": 237},
    # Case 1: mixed pass/fail within one recalculation — sezione 2 σc,RAR fails, sezione 3 σc,QPE fails.
    {"C6": 45, "C8": 450, "D13": 4.5, "D14": 4.5, "D15": 255.8, "D21": 25, "D22": 5.3, "D23": 274, "D29": 6, "D30": 20, "D31": 237},
    # Case 2: exact-equal boundaries on sezione 2 (all three checks at limite == agente -> "non verificato").
    {"C6": 25, "C8": 300, "D13": 12, "D14": 9, "D15": 239, "D21": 12.45, "D22": 9.3375, "D23": 240, "D29": 1, "D30": 1, "D31": 1},
    # Case 3: low Rck/fyk, widespread failures.
    {"C6": 16, "C8": 200, "D13": 10, "D14": 8, "D15": 200, "D21": 15, "D22": 10, "D23": 190, "D29": 12, "D30": 9, "D31": 175},
    # Case 4: high-grade materials, all sections pass.
    {"C6": 60, "C8": 500, "D13": 20, "D14": 15, "D15": 300, "D21": 18, "D22": 14, "D23": 280, "D29": 10, "D30": 8, "D31": 200},
    # Case 5: σs,RAR fails on sezione 1 only.
    {"C6": 45, "C8": 300, "D13": 4.5, "D14": 4.5, "D15": 250, "D21": 10, "D22": 5.3, "D23": 200, "D29": 6, "D30": 6, "D31": 180},
]

READ = [
    "C7",
    "C13", "C14", "C15", "E13", "E14", "E15", "F13", "F14", "F15",
    "C21", "C22", "C23", "E21", "E22", "E23", "F21", "F22", "F23",
    "C29", "C30", "C31", "E29", "E30", "E31", "F29", "F30", "F31",
]

if __name__ == "__main__":
    generate(
        "ca-fessurazione",
        "Limitazione delle tensioni",
        CASES,
        READ,
        Path(__file__).parent / "ca_fessurazione_limitazione_tensioni_oracle.json",
    )
