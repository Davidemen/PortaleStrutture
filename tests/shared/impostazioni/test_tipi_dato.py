"""tipo_dato: each rule 0-7 of WORKBENCH_SPEC.md §26.4 on synthetic field schemas."""
import pytest

from strutture.shared.impostazioni.tipi_dato import tipo_dato


@pytest.mark.unit
def test_hint_wins_over_every_other_rule():
    campo = {"unit": "MPa", "type": "number", "tipo_dato": "lunghezza_mm"}
    assert tipo_dato("qualunque", campo) == "lunghezza_mm"


@pytest.mark.unit
def test_integer_field_is_intero():
    assert tipo_dato("n_barre", {"type": "integer"}) == "intero"
    assert tipo_dato("n_barre", {"anyOf": [{"type": "integer"}, {"type": "null"}]}) == "intero"


@pytest.mark.unit
def test_non_length_unit_has_no_type():
    assert tipo_dato("ned_kN", {"unit": "kN", "type": "number"}) is None
    assert tipo_dato("gamma_c", {"type": "number"}) is None


@pytest.mark.unit
def test_copriferro_by_name():
    assert tipo_dato("copriferro_cm", {"unit": "cm", "type": "number", "symbol": "c"}) == "copriferro"
    assert tipo_dato("c_mm", {"unit": "mm", "type": "number", "symbol": "c"}) == "copriferro"
    assert tipo_dato("cf_mm", {"unit": "mm", "type": "number"}) == "copriferro"


@pytest.mark.unit
def test_diameter_by_symbol_or_name():
    assert tipo_dato("diametro_barre_mm", {"unit": "mm", "type": "number", "symbol": "⌀"}) == "diametro_armatura"
    assert tipo_dato("diametro_pila_mm", {"unit": "mm", "type": "number", "symbol": "Ø_palo"}) == "lunghezza_mm"
    assert tipo_dato("diametro_x_mm", {"unit": "mm", "type": "number"}) == "diametro_armatura"


@pytest.mark.unit
def test_diameter_stays_length_for_section_and_pile():
    # ca-punzonamento.diametro_mm "D" and fond-plinto-su-pali.diametro_pila_mm "Ø_palo": symbol present, not a
    # diameter-of-rebar symbol, so they fall through to the length rule.
    assert tipo_dato("diametro_mm", {"unit": "mm", "type": "number", "symbol": "D"}) == "lunghezza_mm"


@pytest.mark.unit
def test_passo_armatura_by_name():
    assert tipo_dato("passo_staffe_mm", {"unit": "mm", "type": "number"}) == "passo_armatura"
    assert tipo_dato("interferro_mm", {"unit": "mm", "type": "number"}) == "passo_armatura"


@pytest.mark.unit
def test_spessore_by_symbol_or_name():
    assert tipo_dato("t_soletta_mm", {"unit": "mm", "type": "number", "symbol": "t_s"}) == "spessore"
    assert tipo_dato("h_f", {"unit": "mm", "type": "number", "symbol": "h_f"}) == "spessore"
    assert tipo_dato("spessore_mm", {"unit": "mm", "type": "number"}) == "spessore"


@pytest.mark.unit
def test_lengths_by_unit_fallback():
    assert tipo_dato("b_mm", {"unit": "mm", "type": "number"}) == "lunghezza_mm"
    assert tipo_dato("l_m", {"unit": "m", "type": "number"}) == "lunghezza_m"
    assert tipo_dato("s_cm", {"unit": "cm", "type": "number"}) == "lunghezza_cm"
