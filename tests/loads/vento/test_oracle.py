"""Oracle test against LibreOffice-recalculated fixtures (tests/fixtures/gen_vento_pressione.py).

`legacy_compat=True` is compared against the sheet's `Vento` scalars and, for the pressure profile,
a handful of `Tabelle!K4:Q1004` rows (below zmin / mid-height / top), read by section index so the
tool's own parametric profile (n_sezioni=1000) lands on the exact same height grid as the sheet.
"""
import json
from pathlib import Path

import pytest

from strutture.loads.vento.models import VentoPressioneInput
from strutture.loads.vento.tool import run

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "vento_pressione_oracle.json").read_text())


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=[c["inputs"]["H4"] for c in FIXTURE])
def test_oracle_case(case: dict):
    inputs, vento, tabelle = case["inputs"], case["vento"], case["tabelle"]
    report = run(
        VentoPressioneInput(
            comune=inputs["H4"],
            altitudine_m=inputs["H8"],
            periodo_ritorno_anni=inputs["H13"],
            categoria_esposizione=inputs["H29"],
            ct=inputs["H33"],
            altezza_edificio_m=inputs["H34"],
            n_sezioni=1000,
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    # .strip(): the raw Comuni sheet has a stray trailing space on a handful of regione labels
    # (e.g. "Abruzzo ") that the curated strutture.shared.comuni build normalises away -- a data
    # hygiene artifact, not a calculation divergence (see docs/divergences/vento.md).
    assert data.provincia == vento["H5"].strip()
    assert data.regione == vento["H6"].strip()
    assert data.zona == vento["H7"]
    assert data.vb0 == pytest.approx(vento["B10"], rel=1e-6)
    assert data.a0 == pytest.approx(vento["E10"], rel=1e-6)
    assert data.ka == pytest.approx(vento["H10"], rel=1e-6)
    assert data.vref == pytest.approx(vento["H12"], rel=1e-6)
    assert data.a_r == pytest.approx(vento["H14"], rel=1e-6)
    assert data.vr == pytest.approx(vento["H15"], rel=1e-6)
    assert data.kr == pytest.approx(vento["B31"], rel=1e-6)
    assert data.z0 == pytest.approx(vento["E31"], rel=1e-6)
    assert data.zmin == pytest.approx(vento["H31"], rel=1e-6)
    assert data.qb == pytest.approx(vento["H36"], rel=1e-6)
    assert data.ce_h == pytest.approx(vento["H37"], rel=1e-6)

    for row in tabelle:
        riga = data.profilo[row["n"]]
        assert riga.z_m == pytest.approx(row["L"], rel=1e-6, abs=1e-9)
        assert riga.ce == pytest.approx(row["O"] ** 2, rel=1e-6)  # Tabelle!O stores sqrt(ce), spec §8
        assert riga.p_kNm2 == pytest.approx(row["P"], rel=1e-6)
