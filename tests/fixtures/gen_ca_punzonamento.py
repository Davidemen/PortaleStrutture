"""Regenerate tests/fixtures/ca_punzonamento_oracle.json from the workbook via LibreOffice.

Run with: uv run python -m tests.fixtures.gen_ca_punzonamento
"""
from pathlib import Path

from extract.fixtures import generate

# Every case gives the full set of sheet inputs (not deltas), "x" reproducing the sheet's own
# "no override" text for D21/D24. See docs/specs/ca-punzonamento.md "Inputs" for the cell map.
CASES = [
    {  # A: golden case as-is (spec §8) — regression parity check
        "D2": 225, "D3": 0, "D4": 400, "D5": 400, "D6": 500, "D7": 0, "D8": 35, "D9": 50, "D13": 1.15,
        "D21": "x", "D24": "x", "D27": 200, "D28": 200, "D29": 20, "D30": 20, "D31": 0, "D32": 0,
        "D33": 0, "D34": 0, "D46": 400, "D47": 380, "D52": 200, "D55": 12, "D58": 8,
    },
    {  # B: circular column + pterreno>0 (non-shape-aware A_a bug) + beta=1 (centrato); a/d* != 2.0
        "D2": 225, "D3": 0.02, "D4": 0, "D5": 0, "D6": 500, "D7": 500, "D8": 35, "D9": 50, "D13": 1,
        "D21": "x", "D24": "x", "D27": 200, "D28": 200, "D29": 20, "D30": 20, "D31": 0, "D32": 0,
        "D33": 0, "D34": 0, "D46": 400, "D47": 380, "D52": 200, "D55": 12, "D58": 8,
    },
    {  # C: bordo (beta=1.4) + manual perimeter override (umanuale, MIN clamp branch)
        "D2": 225, "D3": 0, "D4": 400, "D5": 400, "D6": 500, "D7": 0, "D8": 35, "D9": 50, "D13": 1.4,
        "D21": 3000, "D24": "x", "D27": 200, "D28": 200, "D29": 20, "D30": 20, "D31": 0, "D32": 0,
        "D33": 0, "D34": 0, "D46": 400, "D47": 380, "D52": 200, "D55": 12, "D58": 8,
    },
    {  # D: angolo (beta=1.5) + manual area override (A_amanuale, MIN clamp in Ved,Red,ui) + pterreno>0
        "D2": 225, "D3": 0.01, "D4": 400, "D5": 400, "D6": 500, "D7": 0, "D8": 35, "D9": 50, "D13": 1.5,
        "D21": "x", "D24": 3000000, "D27": 200, "D28": 200, "D29": 20, "D30": 20, "D31": 0, "D32": 0,
        "D33": 0, "D34": 0, "D46": 400, "D47": 380, "D52": 200, "D55": 12, "D58": 8,
    },
    {  # E: D55=28 typo diameter + Ved raised until reinforcement is genuinely required (F38 fails)
        "D2": 1300, "D3": 0, "D4": 400, "D5": 400, "D6": 500, "D7": 0, "D8": 35, "D9": 50, "D13": 1.15,
        "D21": "x", "D24": "x", "D27": 200, "D28": 200, "D29": 20, "D30": 20, "D31": 0, "D32": 0,
        "D33": 0, "D34": 0, "D46": 400, "D47": 380, "D52": 200, "D55": 28, "D58": 8,
    },
    {  # F: tight tension-rebar spacing -> rho_l > 2% (EC2 §6.4.4(1) cap, uncapped in the sheet)
        "D2": 225, "D3": 0, "D4": 400, "D5": 400, "D6": 500, "D7": 0, "D8": 35, "D9": 50, "D13": 1.15,
        "D21": "x", "D24": "x", "D27": 50, "D28": 50, "D29": 25, "D30": 25, "D31": 0, "D32": 0,
        "D33": 0, "D34": 0, "D46": 400, "D47": 380, "D52": 200, "D55": 12, "D58": 8,
    },
]

OUTPUT_CELLS = [
    "D10", "D11", "D12", "D16", "D17", "D18", "F18", "D20", "D22", "D23", "D25", "D26", "D35", "D36",
    "D37", "D38", "F38", "C40", "D41", "D42", "D43", "D44", "D45", "F46", "D47", "F47", "D48", "D49",
    "D50", "D51", "F52", "D53", "D54", "H55", "H56", "D56", "D57", "D58", "D59", "D60", "D61", "F61", "D62",
    # scan-table samples (step 5): i=2 (x=0.50), i=77 (x=1.25), i=152 (x=2.00), and the winning row/index
    "AQ2", "AR2", "AS2", "AU2", "AV2", "AW2",
    "AQ77", "AR77", "AS77", "AU77", "AV77", "AW77",
    "AQ152", "AR152", "AS152", "AU152", "AV152", "AW152",
    "AW154", "AX154",
]
READ = OUTPUT_CELLS

# Full input cell map (docs/specs/ca-punzonamento.md "Inputs"), used to read Shotblast_375N's own
# defaults for the free-golden case below (no case override -> "inputs" would otherwise be empty).
INPUT_CELLS = [
    "D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9", "D13", "D21", "D24", "D27", "D28", "D29", "D30",
    "D31", "D32", "D33", "D34", "D46", "D47", "D52", "D55", "D58",
]
READ_WITH_INPUTS = sorted(set(OUTPUT_CELLS) | set(INPUT_CELLS))

if __name__ == "__main__":
    generate("ca-punzonamento", "Shotblast_225N", CASES, READ, Path(__file__).parent / "ca_punzonamento_oracle.json")
    # Free golden case (docs/BUILD_CONTRACT.md "Member tools"): Shotblast_375N is a byte-identical
    # clone of the same formulas with different inputs, read with no overrides at all; the input
    # cells are read too (as "outputs") since there is no override dict to recover them from.
    generate(
        "ca-punzonamento", "Shotblast_375N", [{}], READ_WITH_INPUTS,
        Path(__file__).parent / "ca_punzonamento_375n_oracle.json",
    )
