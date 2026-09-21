"""Generate the oracle fixture for `ca-apertura-fessure` from
`Verifica fessurazione - SLEF (X).xlsx`, sheet `Apertura delle fessure`.
Run once: `uv run python tests/fixtures/gen_ca_fessurazione_apertura_fessure.py`.

Concrete classes `C30/37`/`C35/45` are deliberately avoided: they are the two rows where the
`MATERIALE CLS` fill-down bug lives (docs/divergences/materials.md), and `ca-fessurazione`'s own
local sheet pre-corrects `C35/45` differently from the generic `shared.materials.concrete`
legacy reproduction (see this unit's Author notes / docs/divergences/ca-fessurazione.md) — so
those two classes would not agree between this sheet's oracle and our shared module.
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: spec §8 golden values (barre aderenza migliorata, flessione, lunga durata, w3, C4.1.7 branch).
    {
        "E4": "C28/35", "E5": "barre aderenza migliorata", "E6": "caso di flessione", "E7": "lunga durata",
        "E8": "w3 (0.40 mm)", "E9": 200, "E10": 286, "E23": 250, "E25": 75.84, "E26": 1000,
        "E29": 5, "E30": 20, "E31": 0, "E32": 0, "E38": 35,
    },
    # Case 1: barre lisce, breve durata, w1, C4.1.7 branch.
    {
        "E4": "C20/25", "E5": "barre lisce", "E6": "caso di flessione", "E7": "breve durata",
        "E8": "w1 (0.20 mm)", "E9": 150, "E10": 200, "E23": 300, "E25": 100, "E26": 1200,
        "E29": 6, "E30": 18, "E31": 0, "E32": 0, "E38": 30,
    },
    # Case 2: "caso di trazione smplice" (sheet's literal dropdown string), w2, C4.1.7 branch.
    {
        "E4": "C40/50", "E5": "barre aderenza migliorata", "E6": "caso di trazione smplice", "E7": "lunga durata",
        "E8": "w2 (0.30 mm)", "E9": 180, "E10": 250, "E23": 280, "E25": 85, "E26": 900,
        "E29": 4, "E30": 22, "E31": 0, "E32": 0, "E38": 32,
    },
    # Case 3: two rebar groups (n2/ø2 > 0), s >= slim -> C4.1.10 branch.
    {
        "E4": "C25/30", "E5": "barre lisce", "E6": "caso di flessione", "E7": "lunga durata",
        "E8": "w1 (0.20 mm)", "E9": 500, "E10": 200, "E23": 300, "E25": 90, "E26": 800,
        "E29": 3, "E30": 16, "E31": 2, "E32": 12, "E38": 30,
    },
    # Case 4: small section, C4.1.7 branch, w2.
    {
        "E4": "C16/20", "E5": "barre aderenza migliorata", "E6": "caso di flessione", "E7": "lunga durata",
        "E8": "w2 (0.30 mm)", "E9": 120, "E10": 220, "E23": 220, "E25": 60, "E26": 600,
        "E29": 4, "E30": 14, "E31": 0, "E32": 0, "E38": 25,
    },
    # Case 5: highest concrete class, two rebar groups, s >= slim -> C4.1.10 branch.
    {
        "E4": "C50/60", "E5": "barre lisce", "E6": "caso di trazione smplice", "E7": "breve durata",
        "E8": "w3 (0.40 mm)", "E9": 300, "E10": 310, "E23": 400, "E25": 140, "E26": 1000,
        "E29": 6, "E30": 25, "E31": 4, "E32": 16, "E38": 40,
    },
]

READ = [
    "E24", "E22", "E27", "E35", "E33", "E36",  # geometria: d, hc,ef, Ac,eff, As, øeq, ρreff
    "E18", "E19", "E20",  # materiale: Ecm, fctm, αe
    "E39", "E40", "E43",  # coefficienti: k1, k2, kt
    "E12", "H12", "E15",  # spaziatura: slim, ramo, Δsm,eff
    "E45", "E46", "E47",  # εsm, wlim, wk
]

if __name__ == "__main__":
    generate(
        "ca-fessurazione",
        "Apertura delle fessure",
        CASES,
        READ,
        Path(__file__).parent / "ca_fessurazione_apertura_fessure_oracle.json",
    )
