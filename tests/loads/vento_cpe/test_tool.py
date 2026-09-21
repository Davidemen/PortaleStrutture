import pytest

from strutture.loads.vento_cpe.models import VentoCpeOutput
from strutture.loads.vento_cpe.tool import TOOLS


@pytest.mark.unit
def test_tool_registered_with_expected_shape():
    assert len(TOOLS) == 1
    tool = TOOLS[0]
    assert tool.name == "vento-cpe-rettangolare"
    assert tool.output_model is VentoCpeOutput


@pytest.mark.unit
def test_tool_run_returns_ok_report():
    tool = TOOLS[0]
    report = tool.run(tool.input_model(b=15, d=12, h=9))
    assert report.ok
    assert report.data.classification
