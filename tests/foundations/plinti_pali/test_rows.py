import pytest

from strutture.foundations.plinti_pali.rows import riga_carico
from strutture.shared.load_table import ReactionRow
from strutture.shared.pile_group import pile_coordinates

PILES_2X2 = pile_coordinates("2x2", 2.0, 2.0)


@pytest.mark.unit
def test_riga_carico_legacy_golden_row_slu4() -> None:
    row = ReactionRow(nodo=18000, combo="SLU4", fx_kN=-15.9477, fy_kN=-0.93033, fz_kN=1899.9593,
                       mx_kNm=9.91203, my_kNm=-169.805, mz_kNm=2.7315)
    riga = riga_carico(row, PILES_2X2, 2, 2, 2.0, 2.0, 1.2, 0.0, 0.0, legacy_compat=True)
    assert riga.n_min_pila_kN == pytest.approx(424.997, rel=1e-5)  # Footing check!AB9
    assert riga.n_max_pila_kN == pytest.approx(524.982, rel=1e-5)  # AC9


@pytest.mark.unit
def test_riga_carico_fixed_ordina_i_pali_come_lo_schema() -> None:
    row = ReactionRow(nodo=1, combo="C1", fx_kN=0.0, fy_kN=0.0, fz_kN=400.0, mx_kNm=0.0, my_kNm=0.0, mz_kNm=0.0)
    riga = riga_carico(row, PILES_2X2, 2, 2, 2.0, 2.0, 1.2, 0.0, 0.0, legacy_compat=False)
    assert riga.n_pali_kN == pytest.approx((100.0,) * 4, rel=1e-9)
    assert riga.n_min_pila_kN == pytest.approx(100.0, rel=1e-9)
    assert riga.n_max_pila_kN == pytest.approx(100.0, rel=1e-9)


@pytest.mark.unit
def test_riga_carico_schema_1x1_nessuna_divisione_per_zero() -> None:
    """Single pile: legacy `Lx`/`Ly` are both 0 (no spacing) — must not raise ZeroDivisionError."""
    piles_1x1 = pile_coordinates("1x1", 0.0, 0.0)
    row = ReactionRow(nodo=1, combo="C1", fx_kN=0.0, fy_kN=0.0, fz_kN=500.0, mx_kNm=10.0, my_kNm=5.0, mz_kNm=0.0)
    riga = riga_carico(row, piles_1x1, 1, 1, 0.0, 0.0, 1.0, 0.0, 0.0, legacy_compat=True)
    assert riga.n_min_pila_kN == pytest.approx(500.0, rel=1e-9)
    assert riga.n_max_pila_kN == pytest.approx(500.0, rel=1e-9)
