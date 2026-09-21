"""Tool-level tests: dispatch by `norma`, the `example` golden case, and the UI hint contract
(DESIGN_SPEC §4: `group`/`unit`/`condition` on every relevant input field)."""
import pytest

from strutture.foundations.travi_collegamento.models import TraviCollegamentoInput
from strutture.foundations.travi_collegamento.tool import TOOLS


def _tool():
    return TOOLS[0]


@pytest.mark.unit
def test_single_tool_registered() -> None:
    assert len(TOOLS) == 1
    assert TOOLS[0].name == "fond-trave-collegamento"


@pytest.mark.unit
def test_example_validates_and_runs() -> None:
    tool = _tool()
    inputs = tool.input_model.model_validate(tool.example)
    report = tool.run(inputs)
    assert report.ok


@pytest.mark.unit
def test_dispatch_ntc_populates_ntc_groups_only() -> None:
    tool = _tool()
    inputs = TraviCollegamentoInput.model_validate(tool.example)
    report = tool.run(inputs)
    assert report.data.sismica_ntc is not None
    assert report.data.sismica_en is None
    assert report.data.minimi_ntc is not None
    assert report.data.minimi_en is None


@pytest.mark.unit
def test_dispatch_en_populates_en_groups_only() -> None:
    tool = _tool()
    en_inputs = {**tool.example, "norma": "EN1998", "f0": None, "categoria_topografica": None, "ms": 5.6, "n_piani": 3, "h_mm": 450, "n_barre": 8}
    inputs = TraviCollegamentoInput.model_validate(en_inputs)
    report = tool.run(inputs)
    assert report.data.sismica_en is not None
    assert report.data.sismica_ntc is None
    assert report.data.minimi_en is not None
    assert report.data.minimi_ntc is None


@pytest.mark.unit
def test_every_input_field_has_a_group() -> None:
    schema = TraviCollegamentoInput.model_json_schema()
    for name, prop in schema["properties"].items():
        assert "group" in prop, f"campo {name} senza 'group'"


@pytest.mark.unit
def test_norma_specific_fields_have_condition() -> None:
    schema = TraviCollegamentoInput.model_json_schema()
    for name in ("f0", "categoria_topografica", "ms", "n_piani", "alpha_staffa_deg"):
        assert "condition" in schema["properties"][name], f"campo {name} senza 'condition'"


@pytest.mark.unit
def test_dimensional_fields_carry_unit() -> None:
    schema = TraviCollegamentoInput.model_json_schema()
    for name in ("ag_g", "b_mm", "h_mm", "phi_mm", "n1_kN", "n2_kN", "l_mm", "cf_mm", "p_mm"):
        assert schema["properties"][name].get("unit"), f"campo {name} senza 'unit'"
