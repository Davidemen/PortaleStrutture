"""materiale.py — grade lookup, gammaM0/gammaM1 resolution (docs/architecture.md §6, column-check H12/H13/H15)."""
import pytest

from strutture.members.acciaio_colonna_ec3.materiale import risolvi_materiale


@pytest.mark.unit
def test_legacy_defaults_gamma_to_one_like_the_sheet() -> None:
    materiali, warnings = risolvi_materiale("S235", None, None, legacy_compat=True)
    assert materiali.gamma_m0 == 1.0
    assert materiali.gamma_m1 == 1.0
    assert materiali.fyd_MPa == pytest.approx(235.0)
    assert warnings == ()


@pytest.mark.unit
def test_fixed_defaults_gamma_to_ec3_standard() -> None:
    materiali, warnings = risolvi_materiale("S235", None, None, legacy_compat=False)
    assert materiali.gamma_m0 == pytest.approx(1.05)
    assert materiali.gamma_m1 == pytest.approx(1.05)
    assert materiali.fyd_MPa == pytest.approx(235.0 / 1.05)
    assert warnings == ()


@pytest.mark.unit
def test_fixed_override_away_from_standard_warns() -> None:
    materiali, warnings = risolvi_materiale("S235", 1.2, None, legacy_compat=False)
    assert materiali.gamma_m0 == 1.2
    assert len(warnings) == 1
    assert "1.2" in warnings[0]


@pytest.mark.unit
def test_fixed_override_matching_standard_does_not_warn() -> None:
    _, warnings = risolvi_materiale("S235", 1.05, 1.05, legacy_compat=False)
    assert warnings == ()


@pytest.mark.unit
def test_fud_uses_gamma_m2_when_fixed_but_gamma_m0_when_legacy() -> None:
    """New divergence: H15 (fuk) divides by gammaM0 in the sheet; EC3 wants gammaM2 (unused elsewhere)."""
    legacy, _ = risolvi_materiale("S235", 2.0, None, legacy_compat=True)
    fixed, _ = risolvi_materiale("S235", None, None, legacy_compat=False)
    assert legacy.fud_MPa == pytest.approx(360.0 / 2.0)
    assert fixed.fud_MPa == pytest.approx(360.0 / 1.25)


@pytest.mark.unit
@pytest.mark.parametrize(
    "grado,fyk,fuk", [("S235", 235.0, 360.0), ("S275", 275.0, 430.0), ("S355", 355.0, 510.0), ("Q345", 345.0, 450.0), ("Q235", 235.0, 360.0)]
)
def test_grade_table_matches_materiali_sheet(grado: str, fyk: float, fuk: float) -> None:
    materiali, _ = risolvi_materiale(grado, 1.0, 1.0, legacy_compat=True)
    assert materiali.fyk_MPa == fyk
    assert materiali.fuk_MPa == fuk


@pytest.mark.unit
def test_unknown_grade_raises() -> None:
    from strutture.shared.tables import KeyNotFound

    with pytest.raises(KeyNotFound):
        risolvi_materiale("S460", None, None, legacy_compat=False)  # type: ignore[arg-type]
