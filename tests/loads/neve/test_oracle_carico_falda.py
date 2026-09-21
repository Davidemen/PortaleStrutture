import json
from pathlib import Path

import pytest

from strutture.loads.neve.models import CaricoFaldaInput
from strutture.loads.neve.tool import run_carico_falda

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "neve_carico_falda_oracle.json").read_text())


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs, outputs = case["inputs"], case["outputs"]
    report = run_carico_falda(
        CaricoFaldaInput(
            comune=inputs["H5"],
            as_m=inputs["H9"],
            topografia=inputs["H13"],
            ct=inputs["H26"],
            tipo_copertura="Copertura a due falde",  # both branches always computed in legacy mode
            a=inputs["H30"],
            parapetto=inputs["H31"],
            a1=inputs["H52"],
            parapetto1=inputs["H53"],
            a2=inputs["H56"],
            parapetto2=inputs["H57"],
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.provincia == outputs["H6"]
    assert data.regione == outputs["H7"]
    assert data.zona == outputs["H8"]
    assert data.qsk == pytest.approx(outputs["H10"], rel=1e-6)
    assert data.ce == pytest.approx(outputs["H14"], rel=1e-6)
    assert data.mu == pytest.approx(outputs["H32"], abs=1e-9)
    assert data.qs == pytest.approx(outputs["D34"], rel=1e-6, abs=1e-9)
    assert data.mu1 == pytest.approx(outputs["H54"], abs=1e-9)
    assert data.qs1 == pytest.approx(outputs["D60"], rel=1e-6, abs=1e-9)
    assert data.mu2 == pytest.approx(outputs["H58"], abs=1e-9)
    assert data.qs2 == pytest.approx(outputs["H61"], rel=1e-6, abs=1e-9)
