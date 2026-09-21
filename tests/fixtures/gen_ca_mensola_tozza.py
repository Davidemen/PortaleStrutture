"""Generate tests/fixtures/ca_mensola_tozza_oracle.json from `mensola-tozza.xls`, sheet
`Mensola tozza`. Run once: `uv run python tests/fixtures/gen_ca_mensola_tozza.py`.

Cases exercise: golden (§8, a<0.5h branch), a>=0.5h branch, staffe_verticali=SI (c=1.5),
inclined bars (dPR>0), HEd>0, gerarchia failure (PRS>PRC), ULS failure (PR<=PEd),
insufficient-stirrups note (A36), and the FeB22k/legacy #N/A bug (spec §7, divergence).
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    {  # golden §8: a=177 < 0.5*450=225 -> As,lnk = 0.25*As,hor branch; verdict soddisfatta
        "H5": 177, "H6": 450, "H7": 800, "H8": 50, "H9": 136, "H10": 0,
        "H14": "B450C", "H15": "C32/40",
        "H16": 8, "H17": 12, "H18": 0, "H19": 0, "H22": 0,
        "H24": 3, "H25": 12, "H29": "NO",
    },
    {  # a=300 >= 0.5*450=225 -> As,lnk = 0.5*PEd/fyd branch
        "H5": 300, "H6": 450, "H7": 800, "H8": 50, "H9": 100, "H10": 0,
        "H14": "FeB32k", "H15": "C25/30",
        "H16": 6, "H17": 14, "H18": 0, "H19": 0, "H22": 0,
        "H24": 2, "H25": 10, "H29": "NO",
    },
    {  # staffe_verticali=SI -> c coefficient 1.5 (H30 type-mismatch bug, spec §7)
        "H5": 177, "H6": 450, "H7": 800, "H8": 50, "H9": 136, "H10": 0,
        "H14": "B450C", "H15": "C32/40",
        "H16": 8, "H17": 12, "H18": 0, "H19": 0, "H22": 0,
        "H24": 3, "H25": 12, "H29": "SI",
    },
    {  # inclined bars: dPR > 0 contributes 0.8*dPR to PR
        "H5": 177, "H6": 450, "H7": 800, "H8": 50, "H9": 136, "H10": 0,
        "H14": "B450C", "H15": "C32/40",
        "H16": 8, "H17": 12, "H18": 4, "H19": 10, "H22": 45,
        "H24": 3, "H25": 12, "H29": "NO",
    },
    {  # HEd > 0 reduces PRS
        "H5": 177, "H6": 450, "H7": 800, "H8": 50, "H9": 136, "H10": 50,
        "H14": "B450C", "H15": "C32/40",
        "H16": 8, "H17": 12, "H18": 0, "H19": 0, "H22": 0,
        "H24": 3, "H25": 12, "H29": "NO",
    },
    {  # gerarchia failure: PRS >> PRC (small b/d, oversized tie steel) -> "non verificata"
        "H5": 50, "H6": 300, "H7": 100, "H8": 50, "H9": 50, "H10": 0,
        "H14": "B450C", "H15": "C20/25",
        "H16": 20, "H17": 20, "H18": 0, "H19": 0, "H22": 0,
        "H24": 2, "H25": 10, "H29": "NO",
    },
    {  # ULS failure: PRS <= PRC but PR <= PEd (PEd inflated far past PRS=495.937)
        "H5": 177, "H6": 450, "H7": 800, "H8": 50, "H9": 1000, "H10": 0,
        "H14": "B450C", "H15": "C32/40",
        "H16": 8, "H17": 12, "H18": 0, "H19": 0, "H22": 0,
        "H24": 3, "H25": 12, "H29": "NO",
    },
    {  # insufficient stirrups: n*2*bar_area(phi) < As,lnk -> A36 note fires
        "H5": 177, "H6": 450, "H7": 800, "H8": 50, "H9": 136, "H10": 0,
        "H14": "B450C", "H15": "C32/40",
        "H16": 8, "H17": 12, "H18": 0, "H19": 0, "H22": 0,
        "H24": 1, "H25": 6, "H29": "NO",
    },
    {  # FeB22k selectable via H14's dropdown but absent from Tabelle!M45:P49 -> sheet #N/A
        "H5": 177, "H6": 450, "H7": 800, "H8": 50, "H9": 136, "H10": 0,
        "H14": "FeB22k", "H15": "C32/40",
        "H16": 8, "H17": 12, "H18": 0, "H19": 0, "H22": 0,
        "H24": 3, "H25": 12, "H29": "NO",
    },
]

READ = ["Z5", "Z6", "Z8", "Z9", "H11", "H13", "H20", "H21", "H23", "H30", "H28", "H31", "H32", "H33", "C34", "A36"]

if __name__ == "__main__":
    generate(
        "ca-mensole",
        "Mensola tozza",
        CASES,
        READ,
        Path(__file__).parent / "ca_mensola_tozza_oracle.json",
    )
