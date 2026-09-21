"""Registration test for the `ca-taglio-non-armato` Tool."""
import pytest

from strutture.members.ca_taglio_non_armato.models import TaglioNonArmatoInput, TaglioNonArmatoOutput
from strutture.members.ca_taglio_non_armato.tool import TOOLS

pytestmark = pytest.mark.unit


def test_tool_registered_once():
    assert len(TOOLS) == 1
    tool = TOOLS[0]
    assert tool.name == "ca-taglio-non-armato"
    assert tool.group == "Calcestruzzo armato / Travi"
    assert tool.input_model is TaglioNonArmatoInput
    assert tool.output_model is TaglioNonArmatoOutput


def test_example_has_no_legacy_compat_and_no_legacy_compat_string():
    tool = TOOLS[0]
    assert "legacy_compat" not in tool.example
    assert "legacy_compat" not in str(tool.example)
