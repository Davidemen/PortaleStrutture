import json
from pathlib import Path

import pytest

from strutture.loads.vento_cpe.models import VentoCpeInput
from strutture.loads.vento_cpe.tool import run

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "vento_cpe_oracle.json").read_text())


def _assert_cpe(actual: float | None, expected: object) -> None:
    if expected == "ND":
        assert actual is None
    else:
        assert actual == pytest.approx(expected, rel=1e-6)


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs = case["inputs"]
    outputs = case["outputs"]
    report = run(VentoCpeInput(b=inputs["D6"], d=inputs["D7"], h=inputs["D8"], legacy_compat=True))
    assert report.ok
    data = report.data

    assert data.classification == outputs["B10"]

    assert data.dir1.h_d == pytest.approx(outputs["D9"], rel=1e-6)
    _assert_cpe(data.dir1.cpe_windward, outputs["D13"])
    _assert_cpe(data.dir1.cpe_side, outputs["D14"])
    _assert_cpe(data.dir1.cpe_leeward, outputs["D15"])

    assert data.dir2.h_d == pytest.approx(outputs["E9"], rel=1e-6)
    _assert_cpe(data.dir2.cpe_windward, outputs["E13"])
    _assert_cpe(data.dir2.cpe_side, outputs["E14"])
    _assert_cpe(data.dir2.cpe_leeward, outputs["E15"])
