"""Unit tests for `fattori_combo` — combination partial factors (muro rows 45-50/80-81) against
the values read directly from the workbook (openpyxl, Tratto A) via `fattori_azioni`/`fattori_geotecnici`."""
import pytest

from strutture.members.muro.combinazioni import ALL_COMBOS, fattori_combo

pytestmark = pytest.mark.unit


@pytest.mark.parametrize(
    ("nome", "gamma_g_muro", "gamma_phi_terr", "gamma_g_terr", "gamma_q"),
    [
        ("STR_1", 1.3, 1.0, 1.3, 1.5),
        ("STR_2", 1.0, 1.0, 1.0, 0.0),
        ("GEO_1", 1.0, 1.25, 1.0, 1.3),
        ("GEO_2", 1.0, 1.25, 1.0, 0.0),
        ("EQU_1", 0.9, 1.25, 1.1, 1.5),
        ("EQU_2", 0.9, 1.25, 1.1, 0.0),
        ("SISMA_1", 1.0, 1.25, 1.0, 0.6),
        ("SISMA_2", 1.0, 1.25, 1.0, 0.6),
    ],
)
def test_fattori_combo_matches_workbook_cells(nome, gamma_g_muro, gamma_phi_terr, gamma_g_terr, gamma_q):
    """Values cross-checked directly against Muro!D45:N50/D80:N81 and C56:C61/C87:C88 with openpyxl
    (data_only=True): D/J/N per row 45=(1.3,1,1.3) 46=(1,1,1) 47=48=(1,1.25,1) 49=50=(0.9,1.25,1.1)
    80=81=(1,1.25,1); C (γQ) per row 56=1.5 57=0 58=1.3 59=0 60=1.5 61=0 87=88=0.6."""
    for legacy_compat in (True, False):
        fattori = fattori_combo(nome, legacy_compat=legacy_compat)
        assert fattori.gamma_g_muro == pytest.approx(gamma_g_muro)
        assert fattori.gamma_phi_terr == pytest.approx(gamma_phi_terr)
        assert fattori.gamma_g_terr == pytest.approx(gamma_g_terr)
        assert fattori.gamma_q == pytest.approx(gamma_q)


def test_all_combos_has_eight_entries_in_sheet_order():
    assert ALL_COMBOS == ("STR_1", "STR_2", "GEO_1", "GEO_2", "EQU_1", "EQU_2", "SISMA_1", "SISMA_2")
