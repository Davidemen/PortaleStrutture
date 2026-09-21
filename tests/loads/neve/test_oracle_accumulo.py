import json
from pathlib import Path

import pytest

from strutture.loads.neve.models import AccumuloInput
from strutture.loads.neve.tool import run_accumulo

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "neve_accumulo_oracle.json").read_text())


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs, outputs = case["inputs"], case["outputs"]
    report = run_accumulo(
        AccumuloInput(
            comune=inputs["H5"],
            as_m=inputs["H9"],
            topografia=inputs["H13"],
            ct=inputs["H26"],
            b1=inputs["H29"],
            b2=inputs["H30"],
            h=inputs["H31"],
            gamma=inputs["H32"],
            a=inputs["H34"],
            m1_input=inputs["H35"],
            msup=inputs["H37"],
            neve_sheet_as_m=inputs["neve_h9"],
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.zona == outputs["H8"]
    assert data.qsk == pytest.approx(outputs["H10"], rel=1e-6)
    assert data.ce == pytest.approx(outputs["H14"], rel=1e-6)
    assert data.ls == pytest.approx(outputs["H33"], rel=1e-6)
    assert data.mw == pytest.approx(outputs["H36"], rel=1e-6)
    assert data.ms == pytest.approx(outputs["H38"], abs=1e-9)
    assert data.m2 == pytest.approx(outputs["H39"], rel=1e-6)
    assert data.m1_final == pytest.approx(outputs["H43"], rel=1e-6)
    assert data.m2_final == pytest.approx(outputs["H44"], rel=1e-6)
    assert data.ls_final == pytest.approx(outputs["H45"], rel=1e-6)
