"""Unit tests for `tensioni`/`sigma_westergaard`/`carico_concentrato` (spec steps 3-6, "ruota
motrice" cached example: P=15.5kN, bx=500mm, by=100mm, h=200mm, l=776.901mm, b=120.861mm)."""
import pytest

from strutture.foundations.pavimento_industriale.concentrati_tensioni import (
    carico_concentrato,
    sigma_westergaard,
    tensioni,
)

_H_MM = 200
_L_MM = 776.901
_B_MM = 120.861
_RR_MM = 126.157


@pytest.mark.unit
def test_carico_concentrato_applies_gamma_and_psi1() -> None:
    p_slu, p_sle_freq = carico_concentrato(15.5, 1.5, 0.9)
    assert p_slu == pytest.approx(23.25)
    assert p_sle_freq == pytest.approx(13.95)


@pytest.mark.unit
def test_sigma_westergaard_centro_matches_golden_case() -> None:
    sigma = sigma_westergaard("centro", 23.25, _H_MM, _L_MM, _B_MM, _RR_MM)
    assert sigma == pytest.approx(0.789861, rel=1e-5)


@pytest.mark.unit
def test_sigma_westergaard_bordo_matches_golden_case() -> None:
    sigma = sigma_westergaard("bordo", 23.25, _H_MM, _L_MM, _B_MM, _RR_MM)
    assert sigma == pytest.approx(1.19436, rel=1e-5)


@pytest.mark.unit
def test_sigma_westergaard_spigolo_matches_golden_case() -> None:
    sigma = sigma_westergaard("spigolo", 23.25, _H_MM, _L_MM, _B_MM, _RR_MM)
    assert sigma == pytest.approx(1.02311, rel=1e-5)


@pytest.mark.unit
def test_spigolo_is_the_most_severe_position_for_this_geometry() -> None:
    """Matches spec cached ordering: bordo > spigolo > centro for this footprint."""
    centro = sigma_westergaard("centro", 23.25, _H_MM, _L_MM, _B_MM, _RR_MM)
    bordo = sigma_westergaard("bordo", 23.25, _H_MM, _L_MM, _B_MM, _RR_MM)
    spigolo = sigma_westergaard("spigolo", 23.25, _H_MM, _L_MM, _B_MM, _RR_MM)
    assert bordo > spigolo > centro


@pytest.mark.unit
def test_spigolo_can_turn_negative_for_a_large_footprint() -> None:
    """Not a bug: a corner load with rr comparable to l pushes `1-1.23*(rr/l)^0.6` negative (oracle
    case bx=by=1000mm, h=200mm, l=776.9mm -- see `tests/fixtures/gen_pavimento_industriale.py`).
    `TensioniResult.sigma_c_max_MPa` therefore has no lower bound."""
    sigma = sigma_westergaard("spigolo", 23.25, 200.0, 776.901, 564.19, 564.19)
    assert sigma < 0


@pytest.mark.unit
def test_tensioni_matches_golden_case() -> None:
    result = tensioni("centro", 15.5, 1.5, 0.9, _H_MM, _L_MM, _B_MM, _RR_MM)
    assert result.p_slu_kN == pytest.approx(23.25)
    assert result.p_sle_freq_kN == pytest.approx(13.95)
    assert result.sigma_c_max_MPa == pytest.approx(0.789861, rel=1e-5)
    assert result.m_slu_Nmm_m == pytest.approx(5265.74, rel=1e-5)
