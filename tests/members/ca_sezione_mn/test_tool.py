"""`TOOLS` registration + UI-hint contract (docs/BUILD_CONTRACT.md "Batch 2", docs/ui/DESIGN_SPEC.md
§4): example validates and runs in the only (default) mode, every input carries group/description,
dimensional fields carry unit/symbol, conditional fields carry `condition`, domains carry `chart`,
and the tool stays fast (< 500 ms, best of 5, for the example, < 5 s for 500 combinations)."""
import time

import pytest

from strutture.members.ca_sezione_mn.models_input import SezioneMnInput
from strutture.members.ca_sezione_mn.models_output import SezioneMnOutput
from strutture.members.ca_sezione_mn.tool import TOOLS
from strutture.shared.tool import execute

pytestmark = pytest.mark.unit

TOOL = TOOLS[0]
_RIPETIZIONI_TEMPO = 5
_SOGLIA_ESEMPIO_S = 0.5


def test_tool_registered():
    assert len(TOOLS) == 1
    assert TOOL.name == "ca-sezione-dominio-mn"
    assert TOOL.input_model is SezioneMnInput
    assert TOOL.output_model is SezioneMnOutput
    assert TOOL.group == "Calcestruzzo armato / Pilastri"


def test_example_has_no_legacy_compat():
    assert TOOL.example is not None
    assert "legacy_compat" not in TOOL.example


def test_example_validates_and_runs():
    inputs = TOOL.input_model.model_validate(TOOL.example)
    report = TOOL.run(inputs)
    assert report.ok, report.errors
    assert report.data.governante is not None
    assert report.checks and report.checks[0].name == "Verifica a pressoflessione"


def test_example_runs_via_execute_without_legacy_compat_key():
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors


def test_example_runs_fast():
    durate = []
    for _ in range(_RIPETIZIONI_TEMPO):  # il minimo scarta i picchi di carico del runner
        inizio = time.perf_counter()
        report = execute(TOOL, TOOL.example)
        durate.append(time.perf_counter() - inizio)
        assert report.ok, report.errors
    assert min(durate) < _SOGLIA_ESEMPIO_S, f"esempio in {min(durate):.3f}s"
    assert TOOL.live is True  # < 120 ms in practice: safe to leave live recalculation on


def test_cinquecento_combinazioni_sotto_5_secondi():
    azioni = [
        {"nome": f"C{i}", "n_ed_kN": 200.0 + (i % 20) * 60.0, "m_ed_x_kNm": (i % 7) * 30.0, "m_ed_y_kNm": (i % 5) * 15.0}
        for i in range(500)
    ]
    inputs = {**TOOL.example, "azioni": azioni}
    inizio = time.perf_counter()
    report = execute(TOOL, inputs)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert len(report.data.righe) == 500
    assert durata < 5.0, f"500 combinazioni in {durata:.3f}s"


def test_every_input_field_has_group_and_description():
    schema = SezioneMnInput.model_json_schema()
    for name, prop in schema["properties"].items():
        assert prop.get("description"), f"{name}: missing Italian description"
        assert prop.get("group"), f"{name}: missing UI group hint"


def test_dimensional_fields_carry_unit_and_symbol():
    schema = SezioneMnInput.model_json_schema()
    dimensional = {
        "b_mm", "h_mm", "diametro_mm", "bf_mm", "hf_mm", "bw_mm", "lw_mm", "tw_mm", "le_mm", "te_mm",
        "layout_copriferro_mm", "layout_diametro_mm",
    }
    for name in dimensional:
        prop = schema["properties"][name]
        assert prop.get("unit"), f"{name}: missing unit"
        assert prop.get("symbol"), f"{name}: missing symbol"


def test_geometry_fields_are_conditional_on_forma():
    schema = SezioneMnInput.model_json_schema()
    assert schema["properties"]["b_mm"]["condition"] == {"field": "forma", "equals": ["rettangolare"]}
    assert schema["properties"]["diametro_mm"]["condition"] == {"field": "forma", "equals": ["circolare"]}
    assert schema["properties"]["vertici"]["condition"] == {"field": "forma", "equals": ["poligono_libero"]}


def test_advanced_fields_are_flagged():
    schema = SezioneMnInput.model_json_schema()
    for name in ("legge_calcestruzzo", "legge_acciaio"):
        assert schema["properties"][name].get("advanced") is True


def test_domains_carry_chart_hints():
    schema = SezioneMnOutput.model_json_schema()
    for field in ("dominio_x", "dominio_y"):
        chart = schema["properties"][field]["chart"]
        assert chart["x"] == "n_kN"
        assert chart["y"] == ["m_kNm"]


def test_righe_field_has_rows_page_hint():
    schema = SezioneMnOutput.model_json_schema()
    assert schema["properties"]["righe"]["rows_page"] == 200


def test_at_most_three_highlighted_outputs():
    schema = SezioneMnOutput.model_json_schema()
    highlighted = [
        (model_name, field_name)
        for model_name, model_schema in schema["$defs"].items()
        for field_name, prop in model_schema.get("properties", {}).items()
        if prop.get("highlight") is True
    ]
    assert 1 <= len(highlighted) <= 3
    # never on the ROW model (every combination + the governing one share it): the Sintesi shows the
    # governing utilisation as η_max already, and a row-level highlight printed the same symbol twice
    assert ("RigaAzione", "rapporto") not in highlighted
    assert ("GeometriaOutput", "as_mm2") in highlighted


def test_check_name_has_no_underscore():
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    for check in report.checks:
        assert "_" not in check.name


@pytest.mark.parametrize(
    "overrides",
    [
        {"forma": "circolare", "b_mm": None, "h_mm": None, "diametro_mm": 450,
         "armatura_modo": "layout", "layout_tipo": "circolare", "layout_n_barre": 8,
         "layout_copriferro_mm": 30, "layout_diametro_mm": 18},
        {"forma": "a_l", "b_mm": None, "bf_mm": 400, "hf_mm": 150, "bw_mm": 250, "h_mm": 500,
         "armatura_modo": "tabella",
         "barre": [{"x_mm": 30, "y_mm": 30, "diametro_mm": 20}, {"x_mm": 370, "y_mm": 30, "diametro_mm": 20}]},
        {"forma": "parete", "b_mm": None, "h_mm": None, "lw_mm": 3000, "tw_mm": 200, "le_mm": 400, "te_mm": 300,
         "armatura_modo": "tabella",
         "barre": [{"x_mm": -1300, "y_mm": 0, "diametro_mm": 16}, {"x_mm": 1300, "y_mm": 0, "diametro_mm": 16}]},
        {"forma": "poligono_libero", "b_mm": None, "h_mm": None,
         "vertici": [{"x_mm": 0, "y_mm": 0}, {"x_mm": 400, "y_mm": 0}, {"x_mm": 400, "y_mm": 400}, {"x_mm": 0, "y_mm": 400}],
         "armatura_modo": "tabella",
         "barre": [{"x_mm": 40, "y_mm": 40, "diametro_mm": 20}, {"x_mm": 360, "y_mm": 360, "diametro_mm": 20}]},
    ],
)
def test_ogni_forma_gira_correttamente(overrides: dict) -> None:
    inputs = {**TOOL.example, **overrides}
    report = execute(TOOL, inputs)
    assert report.ok, report.errors
    assert report.data.geometria.ac_mm2 > 0.0


def test_barra_esterna_al_contorno_fallisce_con_messaggio_chiaro() -> None:
    inputs = {**TOOL.example, "armatura_modo": "tabella", "barre": [{"x_mm": 0, "y_mm": 5000, "diametro_mm": 20}]}
    report = execute(TOOL, inputs)
    assert report.ok is False
    assert any("esterna al contorno" in e for e in report.errors)


def test_governing_resistances_are_exposed_positive_for_the_column_tools():
    """Phase 5 link: the column tools take a typed M_Rd; the M-N tool provides the exact M_Rd+ about
    x at the governing N_Ed (`sezione.mrd_x_kNm`), a positive number whatever the sign of M_Ed."""
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    res = report.data.resistenze_governante
    assert res is not None
    assert res.n_ed_kN == report.data.governante.n_ed_kN
    assert res.mrd_x_pos_kNm > 0 and res.mrd_x_neg_kNm < 0
    assert res.mrd_y_pos_kNm > 0 and res.mrd_y_neg_kNm < 0
    assert res.mrd_x_pos_kNm == pytest.approx(abs(report.data.governante.mx_rd_kNm), rel=1e-6)


def test_governing_resistances_are_absent_when_n_ed_is_outside_the_domain():
    report = execute(TOOL, {**TOOL.example, "azioni": [{"nome": "X", "n_ed_kN": 50000.0, "m_ed_x_kNm": 10.0, "m_ed_y_kNm": 0.0}]})
    assert report.ok, report.errors
    assert report.data.resistenze_governante is None
