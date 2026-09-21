"""`checks.py`: the single "Verifica a pressoflessione" check on the envelope, with a clear Italian
detail even when `N_Ed` falls outside the section's resistance domain (never a crash, never a
silent clamp — docs/architecture-phase4.md §B)."""
import pytest

from strutture.members.ca_sezione_mn.checks import CLAUSOLA_PRESSOFLESSIONE, check_pressoflessione
from strutture.members.ca_sezione_mn.models_output import RigaAzione

pytestmark = pytest.mark.unit


def test_verifica_passata() -> None:
    governante = RigaAzione(
        nome="SLU1", n_ed_kN=500.0, m_ed_x_kNm=50.0, m_ed_y_kNm=0.0, tipo="uniassiale x",
        mx_rd_kNm=100.0, my_rd_kNm=None, rapporto=0.5, dentro=True,
    )
    check = check_pressoflessione(governante)
    assert check.name == "Verifica a pressoflessione"
    assert check.passed is True
    assert check.clause == CLAUSOLA_PRESSOFLESSIONE
    assert check.value == pytest.approx(0.5)
    assert check.limit == pytest.approx(1.0)
    assert "SLU1" in check.detail


def test_verifica_fallita_per_rapporto_superiore_a_1() -> None:
    governante = RigaAzione(
        nome="SLU2", n_ed_kN=500.0, m_ed_x_kNm=150.0, m_ed_y_kNm=0.0, tipo="uniassiale x",
        mx_rd_kNm=100.0, my_rd_kNm=None, rapporto=1.5, dentro=False,
    )
    check = check_pressoflessione(governante)
    assert check.passed is False
    assert check.value == pytest.approx(1.5)


def test_verifica_fallita_n_ed_fuori_dal_dominio_ha_dettaglio_chiaro() -> None:
    governante = RigaAzione(
        nome="SLU3", n_ed_kN=9000.0, m_ed_x_kNm=10.0, m_ed_y_kNm=0.0, tipo="uniassiale x",
        mx_rd_kNm=None, my_rd_kNm=None, rapporto=None, dentro=False,
    )
    check = check_pressoflessione(governante)
    assert check.passed is False
    assert check.value is None
    assert "fuori dal campo di resistenza" in check.detail
    assert "SLU3" in check.detail
    assert "9000" in check.detail
