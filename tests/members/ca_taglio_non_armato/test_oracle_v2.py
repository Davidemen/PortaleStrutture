"""Oracle tests for the v2 sheet (`1m`, per-metre strip: direct fck, N°/Ø instead of Asl)."""
import json
from pathlib import Path

import pytest

from strutture.members.ca_taglio_non_armato.compose import run
from strutture.members.ca_taglio_non_armato.models import TaglioNonArmatoInput

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_taglio_non_armato_v2_oracle.json").read_text(encoding="utf-8"))


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case_v2(case: dict):
    inputs = case["inputs"]
    outputs = case["outputs"]
    report = run(
        TaglioNonArmatoInput(
            rck_MPa=inputs["B2"],
            fck_MPa=inputs["B3"],
            h_mm=inputs["B7"],
            c_mm=inputs["B8"],
            bw_mm=inputs["B9"],
            n_barre=inputs["B11"],
            diametro_barre_mm=inputs["B12"],
            ned_kN=inputs.get("B14", 0),
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.materiali.fcd_MPa == pytest.approx(outputs["B4"], rel=1e-6)
    assert data.geometria.d_mm == pytest.approx(outputs["B10"], rel=1e-6)
    assert data.geometria.asl_mm2 == pytest.approx(outputs["B13"], rel=1e-6)
    assert data.taglio.sigma_cp_MPa == pytest.approx(outputs["B15"], rel=1e-6, abs=1e-9)
    assert data.taglio.k == pytest.approx(outputs["B17"], rel=1e-6)
    assert data.taglio.vmin_MPa == pytest.approx(outputs["B18"], rel=1e-6)
    assert data.taglio.rho_l == pytest.approx(outputs["B19"], rel=1e-6)
    assert data.taglio.vrd1_kN == pytest.approx(outputs["B21"], rel=1e-6)
    assert data.taglio.vrd2_kN == pytest.approx(outputs["B22"], rel=1e-6)
    assert data.taglio.vrd_kN == pytest.approx(outputs["B23"], rel=1e-6)
