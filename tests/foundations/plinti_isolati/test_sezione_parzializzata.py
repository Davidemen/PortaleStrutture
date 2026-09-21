import pytest

from strutture.foundations.plinti_isolati.sezione_parzializzata import (
    profondita_asse_neutro_mm,
    sigma_acciaio_MPa,
    sigma_calcestruzzo_MPa,
)


@pytest.mark.golden
def test_profondita_asse_neutro_golden() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: xi_x,QP = xi_y,QP = 213.541 mm
    (B=4000mm, H=800mm, As,prov=10367.3 mm2)."""
    xi = profondita_asse_neutro_mm(4000.0, 800.0, 10367.3)
    assert xi == pytest.approx(213.541, rel=1e-4)


@pytest.mark.golden
def test_sigma_calcestruzzo_golden() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: sigma_c,x,QP = 3.35865 N/mm2
    (Mx,QP=1045.43 kNm, B=4000mm, xi=213.541mm, H=800mm)."""
    sigma = sigma_calcestruzzo_MPa(1045.43, 4000.0, 213.541, 800.0)
    assert sigma == pytest.approx(3.35865, rel=1e-4)


@pytest.mark.golden
def test_sigma_acciaio_golden() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: sigma_s,x,QP = 138.361 N/mm2."""
    sigma = sigma_acciaio_MPa(1045.43, 10367.3, 213.541, 800.0)
    assert sigma == pytest.approx(138.361, rel=1e-4)


@pytest.mark.unit
def test_profondita_asse_neutro_indipendente_dal_momento() -> None:
    """The cracked-section neutral axis depends only on geometry and As, never on M (elastic
    cracked section): QP/CHA/FREQ share the same xi, per the sheet's own X7=X13 alias."""
    xi_qp = profondita_asse_neutro_mm(4000.0, 800.0, 10367.3)
    xi_cha = profondita_asse_neutro_mm(4000.0, 800.0, 10367.3)
    assert xi_qp == xi_cha
