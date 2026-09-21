import json
from pathlib import Path

import pytest

from strutture.members.ca_taglio_non_armato.compose import run
from strutture.members.ca_taglio_non_armato.models import TaglioNonArmatoInput

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_taglio_non_armato_oracle.json").read_text())


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs = case["inputs"]
    outputs = case["outputs"]
    report = run(
        TaglioNonArmatoInput(
            rck_MPa=inputs["B2"],
            h_mm=inputs["B7"],
            c_mm=inputs["B8"],
            bw_mm=inputs["B9"],
            asl_mm2=inputs["B11"],
            ned_kN=inputs["B12"],
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.materiali.fck_MPa == pytest.approx(outputs["B3"], rel=1e-6)
    assert data.materiali.fcd_MPa == pytest.approx(outputs["B4"], rel=1e-6)
    assert data.geometria.d_mm == pytest.approx(outputs["B10"], rel=1e-6)
    assert data.taglio.sigma_cp_MPa == pytest.approx(outputs["B13"], rel=1e-6, abs=1e-9)
    assert data.taglio.k == pytest.approx(outputs["B15"], rel=1e-6)
    assert data.taglio.vmin_MPa == pytest.approx(outputs["B16"], rel=1e-6)
    assert data.taglio.rho_l == pytest.approx(outputs["B17"], rel=1e-6)
    assert data.taglio.vrd1_kN == pytest.approx(outputs["B19"], rel=1e-6)
    assert data.taglio.vrd2_kN == pytest.approx(outputs["B20"], rel=1e-6)
    assert data.taglio.vrd_kN == pytest.approx(outputs["B21"], rel=1e-6)
