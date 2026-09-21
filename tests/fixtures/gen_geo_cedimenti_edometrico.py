"""Generate the oracle fixture for `geo-cedimento-edometrico` from
`workbooks/2xxxx_Cedimenti fondazioni_elastico+edo.xlsx`, sheet `Edometrico` (slug `geo-cedimenti`).

B/L/q/the 5-layer table are themselves formulas pulling from sheet `Elastico_centrale_Newmark`
(docs/specs/geo-cedimenti-edometrico.md "Geometry/loads are imported by formula"), so overrides for
those go through that sheet's cells, not `Edometrico`'s own (formula) cells.

Run once: `uv run python tests/fixtures/gen_geo_cedimenti_edometrico.py` (recalculation is slow,
hence only 5 cases).
"""
from pathlib import Path

from extract.fixtures import generate

CASES = [
    # Case 0: cached workbook defaults (spec's golden case: B=350, L=500, γ=1800, q=0.5, D=blank/0, Z,crit=10000).
    {},
    # Case 1: heavier soil (γ=2000 kg/mc) -- D=0 so q' is unaffected; exercises the Δσ'v/overburden branch only.
    {"B3": 2000},
    # Case 2: nonzero embedment D=1 m -- exercises q'=q-γ*D*0.0001 (the "unlabeled B8" cell, spec §7.3).
    {"B8": 1},
    # Case 3: manual finite Z,crit=770 cm (near the spec's own cross-check root ~769.5 cm) -- exercises
    # the cutoff/reset-idiom branch of B15=MAX(M3:M503), instead of the cached run's disabled (10000 cm) cutoff.
    {"B18": 770},
    # Case 4: different footing + soil altogether (B=400, L=450, q=0.6, γ=1900, one layer's Eed changed) --
    # exercises the general formula + layer-lookup path away from the cached numbers.
    {
        "Elastico_centrale_Newmark!D1": 400,
        "Elastico_centrale_Newmark!D2": 450,
        "Elastico_centrale_Newmark!D3": 0.6,
        "B3": 1900,
        "Elastico_centrale_Newmark!F8": 60,
    },
]

READ = [
    "B12", "B15",
    "H3", "I3", "J3", "K3", "L3",
    "H4", "I4", "J4", "K4", "L4",
    "H203", "I203", "J203", "K203", "L203",
    "H503", "I503", "J503", "K503", "L503",
]

if __name__ == "__main__":
    generate(
        "geo-cedimenti",
        "Edometrico",
        CASES,
        READ,
        Path(__file__).parent / "geo_cedimenti_edometrico_oracle.json",
    )
