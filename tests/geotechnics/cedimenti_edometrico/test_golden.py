"""Golden test: docs/specs/geo-cedimenti-edometrico.md "Golden test case", `legacy_compat=True`."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.models import EdometricoInput
from strutture.geotechnics.cedimenti_edometrico.tool import run

_STRATI = [
    {"z_top_m": 0.00, "z_bot_m": 3.70, "modulo_MPa": 5.500000812600001},
    {"z_top_m": 3.70, "z_bot_m": 4.70, "modulo_MPa": 6.99999657665},
    {"z_top_m": 4.70, "z_bot_m": 5.50, "modulo_MPa": 9.00000400425},
    {"z_top_m": 5.50, "z_bot_m": 31.50, "modulo_MPa": 6.99999657665},
    {"z_top_m": 31.50, "z_bot_m": 118.90, "modulo_MPa": 6.99999657665},
]

_INPUTS = {
    "sistema_unita": "tecnico",
    "b": 350, "l": 500, "d": 0, "gamma": 1800, "q": 0.5,
    "strati": _STRATI,
    "metodo_tensioni": "approssimato",
    "z_crit_input": 10000,  # sheet's cached B18: past the 5000 cm table, cutoff disabled
    "dz": 10, "z_max": 5000,
    "legacy_compat": True,
}


def _row_near(righe, z_m: float):
    return min(righe, key=lambda riga: abs(riga.z_m - z_m))


@pytest.mark.golden
def test_golden_edometrico() -> None:
    report = run(EdometricoInput(**_INPUTS))
    assert report.ok
    data = report.data

    assert data.carico.q_prime_kPa == pytest.approx(49.03325, rel=1e-6)

    riga_0 = _row_near(data.righe, 0.0)
    assert riga_0.delta_sigma_kPa == pytest.approx(49.03325, rel=1e-5)
    assert riga_0.sigma_v0_kPa == pytest.approx(0.0)
    assert riga_0.delta_h_cm == pytest.approx(0.0)
    assert riga_0.cumulativo_cm == pytest.approx(0.0)

    riga_10cm = _row_near(data.righe, 0.10)
    assert riga_10cm.delta_h_cm == pytest.approx(0.0849754, rel=1e-5)
    assert riga_10cm.cumulativo_cm == pytest.approx(0.0849754, rel=1e-5)

    riga_1970cm = _row_near(data.righe, 19.70)
    assert riga_1970cm.delta_sigma_kPa == pytest.approx(0.0152694 * 98.0665, rel=1e-4)
    assert riga_1970cm.delta_h_cm == pytest.approx(0.00213917, rel=1e-4)
    assert riga_1970cm.cumulativo_cm == pytest.approx(2.71064, rel=1e-5)

    riga_ultima = _row_near(data.righe, 50.0)
    assert riga_ultima.delta_sigma_kPa == pytest.approx(0.00297366 * 98.0665, rel=1e-4)
    assert riga_ultima.delta_h_cm == pytest.approx(0.000416595, rel=1e-4)

    assert data.cedimento.w_ed_cm == pytest.approx(2.9958, rel=1e-4)
    assert data.cedimento.w_ed_mm == pytest.approx(29.958, rel=1e-4)
