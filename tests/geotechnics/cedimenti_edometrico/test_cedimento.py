"""Unit tests for `cedimento_totale` (the settlement at the Z,crit cutoff)."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.cedimento import cedimento_totale
from strutture.geotechnics.cedimenti_edometrico.righe import RigaResult


def _riga(z_m: float, cumulativo_cm: float) -> RigaResult:
    return RigaResult(
        z_m=z_m, delta_sigma_approssimato_kPa=1.0, delta_sigma_newmark_kPa=1.0, delta_sigma_kPa=1.0,
        sigma_v0_kPa=1.0, eed_kPa=1000.0, delta_h_cm=0.0, cumulativo_cm=cumulativo_cm,
    )


_RIGHE = (_riga(0.0, 0.0), _riga(1.0, 1.0), _riga(2.0, 2.5), _riga(3.0, 3.2))


@pytest.mark.unit
def test_settlement_is_the_cumulative_just_below_the_cutoff() -> None:
    result = cedimento_totale(_RIGHE, z_crit_utilizzato_m=2.5)
    assert result.w_ed_cm == pytest.approx(2.5)


@pytest.mark.unit
def test_cutoff_beyond_the_last_row_gives_the_full_sum() -> None:
    result = cedimento_totale(_RIGHE, z_crit_utilizzato_m=100.0)
    assert result.w_ed_cm == pytest.approx(3.2)


@pytest.mark.unit
def test_cutoff_at_or_below_the_first_row_gives_zero() -> None:
    result = cedimento_totale(_RIGHE, z_crit_utilizzato_m=0.0)
    assert result.w_ed_cm == pytest.approx(0.0)


@pytest.mark.unit
def test_result_is_reported_in_both_cm_and_mm() -> None:
    result = cedimento_totale(_RIGHE, z_crit_utilizzato_m=2.5)
    assert result.w_ed_mm == pytest.approx(result.w_ed_cm * 10.0)
