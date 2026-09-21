"""suggest_famiglia — name patterns first, then ACTIVE — docs/integrations/MIDAS.md §3 famiglia.py."""
import pytest

from strutture.integrations.midas import Combination, suggest_famiglia


def _combo(name: str, active: str = "ACTIVE") -> Combination:
    return Combination(name=name, table_name=f"{name}(CB)", classification="GEN", active=active, description="", n_terms=1)


@pytest.mark.unit
@pytest.mark.parametrize(
    ("name", "expected"),
    [
        ("SLU1", "SLU_STR"),
        ("SLU-EQU1", "SLU_EQU"),
        ("STR1", "SLU_STR"),
        ("SLV1", "SLV_STR"),
        ("SLV-EQU1", "SLV_EQU"),
        ("SISMA1", "SLV_STR"),
        ("SLE_RARA1", "SLE_RARA"),
        ("CAR1", "SLE_RARA"),
        ("FREQ1", "SLE_FREQ"),
        ("QP1", "SLE_QP"),
        ("PERM1", "SLE_QP"),
    ],
)
def test_name_pattern_rules(name: str, expected: str) -> None:
    assert suggest_famiglia(_combo(name)) == expected


@pytest.mark.unit
def test_falls_back_to_active_strength() -> None:
    assert suggest_famiglia(_combo("COMBO1", active="STRENGTH")) == "SLU_STR"


@pytest.mark.unit
def test_falls_back_to_active_service() -> None:
    assert suggest_famiglia(_combo("COMBO1", active="SERVICE")) == "SLE_RARA"


@pytest.mark.unit
def test_returns_none_when_nothing_matches() -> None:
    assert suggest_famiglia(_combo("COMBO1", active="INACTIVE")) is None
