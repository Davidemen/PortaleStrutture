import json
from pathlib import Path

import pytest

from strutture.loads.sisma.models import SismaFattoriStrutturaInput
from strutture.loads.sisma.tool import TOOLS

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "sisma_fattori_struttura_oracle.json").read_text())
TOOL = next(t for t in TOOLS if t.name == "sisma-fattori-struttura")


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs = case["inputs"]
    outputs = case["outputs"]
    report = TOOL.run(
        SismaFattoriStrutturaInput(
            xi_pct=inputs["I37"],
            q0=inputs["I39"],
            regolare_altezza=inputs["I40"].upper(),
            stato_limite=inputs["I25"].upper(),
            qv=inputs["I44"],
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.eta == pytest.approx(outputs["I38"], rel=1e-6)
    assert data.q == pytest.approx(outputs["I41"], rel=1e-6)
