"""UI hints are part of the job (docs/BUILD_CONTRACT.md "Batch 2"): every input has a `group`,
`Tool.example` must validate and run, and at most 3 output fields are `highlight`ed."""
from strutture.foundations.plinti_pali.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


def test_ogni_input_ha_un_group() -> None:
    schema = TOOL.input_model.model_json_schema()
    for name, prop in schema["properties"].items():
        assert "group" in prop, f"campo {name!r} senza group"


def test_al_massimo_tre_highlight() -> None:
    schema = TOOL.output_model.model_json_schema()
    highlighted = [name for name, prop in schema["properties"].items() if prop.get("highlight") is True]
    assert len(highlighted) <= 3


def test_reazioni_ha_widget_tabella() -> None:
    schema = TOOL.input_model.model_json_schema()
    assert schema["properties"]["reazioni"]["widget"] == "table"
    assert schema["properties"]["reazioni"]["table"]["key"] == "combo"


def test_legacy_compat_e_avanzato() -> None:
    schema = TOOL.input_model.model_json_schema()
    assert schema["properties"]["legacy_compat"]["advanced"] is True


def test_coeff_vrd_max_e_avanzato_con_default_04() -> None:
    schema = TOOL.input_model.model_json_schema()
    prop = schema["properties"]["coeff_vrd_max"]
    assert prop["advanced"] is True
    assert prop["enum"] == [0.4, 0.5]
    assert prop["default"] == 0.4


def test_righe_ha_paginazione_e_grafico() -> None:
    schema = TOOL.output_model.model_json_schema()
    assert schema["properties"]["righe"]["rows_page"] == 200
    assert "chart" in schema["properties"]["righe"]


def test_esempio_valida_e_gira() -> None:
    assert TOOL.example is not None
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data is not None
    assert len(report.data.righe) == len(TOOL.example["reazioni"])
