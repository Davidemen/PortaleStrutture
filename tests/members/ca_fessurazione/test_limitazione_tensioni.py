import pytest

from strutture.members.ca_fessurazione.limitazione_tensioni import (
    fck_da_rck,
    sigma_c_max_qpe_MPa,
    sigma_c_max_rar_MPa,
    sigma_s_max_rar_MPa,
)

pytestmark = pytest.mark.unit


def test_fck_da_rck():
    assert fck_da_rck(45) == pytest.approx(37.35, rel=1e-9)


def test_sigma_c_max_rar():
    assert sigma_c_max_rar_MPa(37.35) == pytest.approx(22.41, rel=1e-9)


def test_sigma_c_max_qpe():
    assert sigma_c_max_qpe_MPa(37.35) == pytest.approx(16.8075, rel=1e-9)


def test_sigma_s_max_rar():
    assert sigma_s_max_rar_MPa(450) == pytest.approx(360, rel=1e-9)
