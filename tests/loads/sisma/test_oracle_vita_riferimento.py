import json
from pathlib import Path

import pytest

from strutture.loads.sisma.models import SismaVitaRiferimentoInput
from strutture.loads.sisma.tool import TOOLS

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "sisma_vita_riferimento_oracle.json").read_text())
TOOL = next(t for t in TOOLS if t.name == "sisma-vita-riferimento")


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs = case["inputs"]
    outputs = case["outputs"]
    report = TOOL.run(
        SismaVitaRiferimentoInput(
            comune=inputs.get("I4"), vn_anni=inputs["I7"], classe_uso=inputs["I8"], legacy_compat=True
        )
    )
    assert report.ok
    data = report.data

    assert data.vita.cu == pytest.approx(outputs["I9"], rel=1e-6)
    assert data.vita.vr == pytest.approx(outputs["I10"], rel=1e-6)
    assert data.periodi_ritorno.slo == pytest.approx(outputs["E13"], rel=1e-6)
    assert data.periodi_ritorno.sld == pytest.approx(outputs["E14"], rel=1e-6)
    assert data.periodi_ritorno.slv == pytest.approx(outputs["E15"], rel=1e-6)
    assert data.periodi_ritorno.slc == pytest.approx(outputs["E16"], rel=1e-6)

    if "I4" in inputs:
        assert data.comune_info.provincia == outputs["I5"]
        assert data.comune_info.regione == outputs["I6"]
