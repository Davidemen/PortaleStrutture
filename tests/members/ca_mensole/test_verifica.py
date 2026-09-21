"""Unit tests for `strutture.members.ca_mensole.verifica` (C34, A36)."""
import pytest

from strutture.members.ca_mensole.verifica import verifica_gerarchia, verifica_staffe, verifica_uls


@pytest.mark.unit
def test_verifica_gerarchia_passes() -> None:
    assert verifica_gerarchia(prs_kN=495.937, prc_kN=1595.156).passed


@pytest.mark.unit
def test_verifica_gerarchia_fails_on_brittle_strut() -> None:
    assert not verifica_gerarchia(prs_kN=5531.935, prc_kN=98.188).passed


@pytest.mark.unit
def test_verifica_gerarchia_boundary_equal_is_ductile() -> None:
    """PRS == PRC is the boundary (`<=`), not a strut failure."""
    assert verifica_gerarchia(prs_kN=100.0, prc_kN=100.0).passed


@pytest.mark.unit
def test_verifica_uls_passes() -> None:
    assert verifica_uls(pr_kN=495.937, ped_kN=136).passed


@pytest.mark.unit
def test_verifica_uls_fails() -> None:
    assert not verifica_uls(pr_kN=495.937, ped_kN=1000).passed


@pytest.mark.unit
def test_verifica_uls_boundary_equal_fails() -> None:
    """PR == PEd is not `PR > PEd` (strict inequality)."""
    assert not verifica_uls(pr_kN=100.0, ped_kN=100.0).passed


@pytest.mark.unit
def test_verifica_staffe_sufficient() -> None:
    check = verifica_staffe(n_staffe=3, phi_staffe_mm=12, as_lnk_min_mm2=226.195)
    assert check.passed
    assert check.detail == ""


@pytest.mark.unit
def test_verifica_staffe_insufficient_note() -> None:
    check = verifica_staffe(n_staffe=1, phi_staffe_mm=6, as_lnk_min_mm2=226.195)
    assert not check.passed
    assert check.detail == "NOTA: As > di As,lnk"


@pytest.mark.unit
def test_verifica_staffe_zero_stirrups_no_diameter_error() -> None:
    check = verifica_staffe(n_staffe=0, phi_staffe_mm=0, as_lnk_min_mm2=10.0)
    assert not check.passed
