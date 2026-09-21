"""Regenerate tests/fixtures/ca_travi_rettangolare_oracle.json from the workbook via LibreOffice.

Run with: uv run python tests/fixtures/gen_ca_travi_rettangolare.py
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {  # golden: spec §8 cached case (CD"B")
        "H6": 600, "H7": 400, "H8": "RB500W", "H9": "C35/45", "H10": 70,
        "H11": 5, "H12": 20, "H13": 0, "H14": 0,
        "H15": 12, "H16": 115, "H17": 2, "H18": 0, "H20": 0, "Z23": 90,
        "H23": 138, "H24": 318, "H25": 239, "H26": 200,
        "Y50": "Ordinarie", "Y51": "Frequente", "Y52": "Poco sensibile", "Z54": "w3",
        "J58": "CDB", "J77": "CDB", "K78": 350, "K80": 8,
    },
    {  # CD"A", both bar+stirrup types used (non-degenerate p,max), different materials;
        # combinazione="Quasi permanente" branch; classe_normativa=None (aggressive+sensibile+qp)
        "H6": 600, "H7": 400, "H8": "B450C", "H9": "C25/30", "H10": 40,
        "H11": 3, "H12": 16, "H13": 2, "H14": 16,
        "H15": 8, "H16": 150, "H17": 2, "H18": 8, "H20": 2, "Z23": 90,
        "H23": 100, "H24": 150, "H25": 80, "H26": 60,
        "Y50": "Aggressive", "Y51": "Quasi permanente", "Y52": "Sensibile", "Z54": "w1",
        "J58": "CDA", "J77": "CDA", "K78": 500, "K80": 6,
    },
    {  # As,min fail branch: single small bar
        "H6": 600, "H7": 400, "H8": "RB500W", "H9": "C35/45", "H10": 70,
        "H11": 1, "H12": 12, "H13": 0, "H14": 0,
        "H15": 12, "H16": 115, "H17": 2, "H18": 0, "H20": 0, "Z23": 90,
        "H23": 50, "H24": 30, "H25": 50, "H26": 40,
        "Y50": "Ordinarie", "Y51": "Frequente", "Y52": "Poco sensibile", "Z54": "w3",
        "J58": "CDB", "J77": "CDB", "K78": 350, "K80": 8,
    },
    {  # As,max fail branch: many large bars; classe w2, mismatch classe_normativa="w1"
        "H6": 600, "H7": 400, "H8": "RB500W", "H9": "C35/45", "H10": 70,
        "H11": 20, "H12": 25, "H13": 0, "H14": 0,
        "H15": 12, "H16": 115, "H17": 2, "H18": 0, "H20": 0, "Z23": 90,
        "H23": 138, "H24": 318, "H25": 200, "H26": 150,
        "Y50": "Molto aggressive", "Y51": "Frequente", "Y52": "Poco sensibile", "Z54": "w2",
        "J58": "CDB", "J77": "CDB", "K78": 350, "K80": 8,
    },
    {  # flessione OK branch: low MEd; combinazione="Quasi permanente"; classe w1, mismatch
        "H6": 600, "H7": 400, "H8": "RB500W", "H9": "C35/45", "H10": 70,
        "H11": 5, "H12": 20, "H13": 0, "H14": 0,
        "H15": 12, "H16": 115, "H17": 2, "H18": 0, "H20": 0, "Z23": 90,
        "H23": 138, "H24": 100, "H25": 50, "H26": 40,
        "Y50": "Ordinarie", "Y51": "Quasi permanente", "Y52": "Poco sensibile", "Z54": "w1",
        "J58": "CDB", "J77": "CDB", "K78": 350, "K80": 8,
    },
    {  # taglio fail branch: high VEd; non-B450C steel to exercise the Z42=360 hardcode divergence
        "H6": 600, "H7": 400, "H8": "FeB22k", "H9": "C35/45", "H10": 70,
        "H11": 5, "H12": 20, "H13": 0, "H14": 0,
        "H15": 12, "H16": 115, "H17": 2, "H18": 0, "H20": 0, "Z23": 90,
        "H23": 700, "H24": 318, "H25": 239, "H26": 200,
        "Y50": "Ordinarie", "Y51": "Frequente", "Y52": "Poco sensibile", "Z54": "w3",
        "J58": "CDB", "J77": "CDB", "K78": 350, "K80": 8,
    },
    {  # cotθ clamp at 1 lower bound: heavy stirrups (valid, sin²θ<1); classe w2 match
        "H6": 600, "H7": 400, "H8": "RB500W", "H9": "C35/45", "H10": 70,
        "H11": 5, "H12": 20, "H13": 0, "H14": 0,
        "H15": 16, "H16": 80, "H17": 4, "H18": 0, "H20": 0, "Z23": 90,
        "H23": 138, "H24": 318, "H25": 239, "H26": 200,
        "Y50": "Aggressive", "Y51": "Frequente", "Y52": "Poco sensibile", "Z54": "w2",
        "J58": "CDB", "J77": "CDB", "K78": 350, "K80": 8,
    },
    {  # capacity design MRc/MRb < 1 branch, CD"A"; classe_normativa=None (molto aggressive+sensibile+qp)
        "H6": 600, "H7": 400, "H8": "RB500W", "H9": "C35/45", "H10": 70,
        "H11": 5, "H12": 20, "H13": 0, "H14": 0,
        "H15": 12, "H16": 115, "H17": 2, "H18": 0, "H20": 0, "Z23": 90,
        "H23": 138, "H24": 318, "H25": 239, "H26": 200,
        "Y50": "Molto aggressive", "Y51": "Quasi permanente", "Y52": "Sensibile", "Z54": "w1",
        "J58": "CDA", "J77": "CDA", "K78": 100, "K80": 8,
    },
    {  # inclined stirrups (alpha != 90); classe w3, mismatch classe_normativa="w2"
        "H6": 600, "H7": 400, "H8": "RB500W", "H9": "C35/45", "H10": 70,
        "H11": 5, "H12": 20, "H13": 0, "H14": 0,
        "H15": 12, "H16": 115, "H17": 2, "H18": 0, "H20": 0, "Z23": 60,
        "H23": 138, "H24": 318, "H25": 239, "H26": 200,
        "Y50": "Ordinarie", "Y51": "Frequente", "Y52": "Sensibile", "Z54": "w3",
        "J58": "CDB", "J77": "CDB", "K78": 350, "K80": 8,
    },
]

READ = [
    "Z12", "Y13", "Z14", "Y15", "Z16", "Y17", "Z18", "Y19",
    "Z22", "Z24", "Z25", "Z26", "Y27",
    "Z31", "Z32", "Z33", "Y34", "Z35",
    "Z38", "Z39", "Y40", "Z41", "Y42", "Z46", "Y47", "Z53", "AI54", "Y55",
    "K59", "K60", "K62", "K81", "J82",
]

if __name__ == "__main__":
    generate("ca-travi", "Travi sez. rettangolare", CASES, READ, Path(__file__).parent / "ca_travi_rettangolare_oracle.json")
