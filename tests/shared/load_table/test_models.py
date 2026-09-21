import pytest
from pydantic import ValidationError

from strutture.shared.load_table import ReactionRow


def _row(**overrides: object) -> ReactionRow:
    base = {"nodo": 1832, "combo": "ULS_CR1", "famiglia": "SLU_STR", "fx_kN": 0.13, "fy_kN": 5.37, "fz_kN": 220.9, "mx_kNm": -36.4, "my_kNm": 1.3, "mz_kNm": -0.06}
    return ReactionRow(**{**base, **overrides})


def test_row_is_frozen():
    row = _row()
    with pytest.raises(ValidationError):
        row.fx_kN = 1.0  # type: ignore[misc]


def test_famiglia_optional_for_pile_caps():
    row = _row(famiglia=None)
    assert row.famiglia is None


def test_famiglia_rejects_unknown_value():
    with pytest.raises(ValidationError):
        _row(famiglia="NOT_A_FAMILY")


def test_aliases_are_exposed_in_json_schema():
    schema = ReactionRow.model_json_schema()
    assert schema["properties"]["fx_kN"]["aliases"] == ["Fx", "FX", "Fx (kN)"]
    assert "Node" in schema["properties"]["nodo"]["aliases"]
