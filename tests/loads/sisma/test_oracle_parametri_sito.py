import json
from pathlib import Path

import pytest

from strutture.loads.sisma.models import SismaParametriSitoInput
from strutture.loads.sisma.tool import TOOLS

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "sisma_parametri_sito_oracle.json").read_text())
TOOL = next(t for t in TOOLS if t.name == "sisma-parametri-sito")


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs = case["inputs"]
    outputs = case["outputs"]
    report = TOOL.run(
        SismaParametriSitoInput(
            categoria_sottosuolo=inputs["I26"],
            categoria_topografica=inputs["I27"],
            tc_star_s=inputs["I28"],
            f0=inputs["I29"],
            ag_g=inputs["I30"],
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.amplificazione.cc == pytest.approx(outputs["I31"], rel=1e-6)
    assert data.amplificazione.ss == pytest.approx(outputs["I32"], rel=1e-6)
    assert data.amplificazione.st == pytest.approx(outputs["I33"], rel=1e-6)
    assert data.amplificazione.s == pytest.approx(outputs["I34"], rel=1e-6)
    assert data.periodi.tb == pytest.approx(outputs["I48"], rel=1e-5)
    assert data.periodi.tc == pytest.approx(outputs["I49"], rel=1e-5)
    assert data.periodi.td == pytest.approx(outputs["I50"], rel=1e-6)
