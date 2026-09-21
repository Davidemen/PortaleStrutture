import pytest

from strutture.foundations.plinti_pali.azioni_pila import momenti_pila


@pytest.mark.unit
def test_momenti_pila_golden_row_slu4() -> None:
    # Footing check! row 9 (SLU4): Fx=-15.9477 Fy=-0.93033 Fz=1899.9593 Mx=9.91203 My=-169.805, H=1.2m.
    m = momenti_pila(-15.9477, -0.93033, 1899.9593, 9.91203, -169.805, 1.2, 0.0, 0.0)
    assert m.mx_finale_kNm == pytest.approx(11.0284, rel=1e-4)  # W9
    assert m.my_finale_kNm == pytest.approx(-188.942, rel=1e-4)  # X9


@pytest.mark.unit
def test_momenti_pila_nessuna_azione() -> None:
    m = momenti_pila(0.0, 0.0, 847.1593, 0.0, 0.0, 1.2, 0.0, 0.0)
    assert m.mx_finale_kNm == pytest.approx(0.0, abs=1e-9)
    assert m.my_finale_kNm == pytest.approx(0.0, abs=1e-9)


@pytest.mark.unit
def test_momenti_pila_eccentricita_trasferisce_n() -> None:
    m = momenti_pila(0.0, 0.0, 1000.0, 0.0, 0.0, 1.0, 0.1, -0.2)
    assert m.mx_finale_kNm == pytest.approx(1000.0 * -0.2, rel=1e-9)
    assert m.my_finale_kNm == pytest.approx(-1000.0 * 0.1, rel=1e-9)
