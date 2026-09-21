"""UI-hint contract tests for `PavimentoIndustrialeInput` (DESIGN_SPEC §4/§4b, BUILD_CONTRACT
"UI hints are part of the job")."""
import pytest
from pydantic import ValidationError

from strutture.foundations.pavimento_industriale.models import PavimentoIndustrialeInput

_BASE = {
    "classe_calcestruzzo": "C25/30", "h_mm": 200, "c_mm": 30, "phi_rete_mm": 8, "passo_rete_mm": 200,
    "q_daN_m2": 2600, "a_contrazione_m": 20, "b_contrazione_m": 18, "a_isolamento_m": 30.9, "b_isolamento_m": 21.2,
    "delta_t_C": 30,
    "carichi": [{"caso": "A", "posizione": "centro", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9}],
}


@pytest.mark.unit
def test_every_field_has_a_group() -> None:
    """`carichi` is exempt: `shared.tabular.table_field` doesn't accept a `group` hint (the table
    widget is its own visual container, architecture-batch2.md §2)."""
    schema = PavimentoIndustrialeInput.model_json_schema()
    for name, prop in schema["properties"].items():
        if name == "carichi":
            continue
        assert "group" in prop, f"campo {name} senza 'group'"


@pytest.mark.unit
def test_dimensional_fields_carry_unit() -> None:
    schema = PavimentoIndustrialeInput.model_json_schema()
    for name in ("h_mm", "c_mm", "phi_rete_mm", "passo_rete_mm", "g_daN_m2", "q_daN_m2", "a_contrazione_m", "delta_t_C"):
        assert schema["properties"][name].get("unit"), f"campo {name} senza 'unit'"


@pytest.mark.unit
def test_carichi_table_hints() -> None:
    schema = PavimentoIndustrialeInput.model_json_schema()
    prop = schema["properties"]["carichi"]
    assert prop["widget"] == "table"
    assert prop["table"]["key"] == "caso"
    assert prop["maxItems"] == 12


@pytest.mark.unit
def test_advanced_fields_are_marked() -> None:
    schema = PavimentoIndustrialeInput.model_json_schema()
    for name in ("legacy_compat", "gamma_c", "gamma_s", "kt_manuale_N_mm3", "coeff_vrd_max"):
        assert schema["properties"][name].get("advanced") is True, f"campo {name} senza 'advanced'"


@pytest.mark.unit
def test_coeff_vrd_max_is_a_named_dropdown_defaulting_to_04() -> None:
    schema = PavimentoIndustrialeInput.model_json_schema()
    prop = schema["properties"]["coeff_vrd_max"]
    assert prop["enum"] == [0.4, 0.5]
    assert prop["default"] == 0.4


@pytest.mark.unit
def test_requires_sottofondo_or_manual_kt() -> None:
    with pytest.raises(ValidationError, match="sottofondo"):
        PavimentoIndustrialeInput(**_BASE, sottofondo_tipo=None, kt_manuale_N_mm3=None)
    with pytest.raises(ValidationError, match="sottofondo"):
        PavimentoIndustrialeInput(**_BASE, sottofondo_tipo="soffice", kt_manuale_N_mm3=0.05)


@pytest.mark.unit
def test_accepts_exactly_one_sottofondo_source() -> None:
    via_lookup = PavimentoIndustrialeInput(**_BASE, sottofondo_tipo="soffice", kt_manuale_N_mm3=None)
    via_manual = PavimentoIndustrialeInput(**_BASE, sottofondo_tipo=None, kt_manuale_N_mm3=0.05)
    assert via_lookup.sottofondo_tipo == "soffice"
    assert via_manual.kt_manuale_N_mm3 == pytest.approx(0.05)


@pytest.mark.unit
def test_max_twelve_carichi_rows() -> None:
    riga = _BASE["carichi"][0]
    with pytest.raises(ValidationError):
        PavimentoIndustrialeInput(**{**_BASE, "carichi": [riga] * 13}, sottofondo_tipo="soffice")
