"""taglio.py — shear resistance (column-check!G26, G36).

New divergence: J26/J36 compare each capacity against the wrong axis's demand — see module docstring.
"""
import pytest

from strutture.members.acciaio_colonna_ec3.taglio import costruisci_taglio, vpl_rd_kN


@pytest.mark.unit
def test_vpl_rd() -> None:
    import math

    assert vpl_rd_kN(4569.6, 345) == pytest.approx(4569.6 * 345 / math.sqrt(3.0) / 1000.0)


@pytest.mark.unit
def test_legacy_swaps_the_demand_axis() -> None:
    result = costruisci_taglio(av_z_mm2=4569.6, av_y_mm2=6720, fyd_MPa=345, vy_sd_kN=29.2057, vz_sd_kN=0.00235166, legacy_compat=True)
    assert result.verifica_anima.value == pytest.approx(0.00235166)  # anima check actually used vz_sd (bug)
    assert result.verifica_ali.value == pytest.approx(29.2057)  # ali check actually used vy_sd (bug)


@pytest.mark.unit
def test_fixed_uses_the_matching_axis() -> None:
    result = costruisci_taglio(av_z_mm2=4569.6, av_y_mm2=6720, fyd_MPa=345, vy_sd_kN=29.2057, vz_sd_kN=0.00235166, legacy_compat=False)
    assert result.verifica_anima.value == pytest.approx(29.2057)
    assert result.verifica_ali.value == pytest.approx(0.00235166)


@pytest.mark.unit
def test_fails_when_demand_exceeds_capacity() -> None:
    result = costruisci_taglio(av_z_mm2=10, av_y_mm2=10, fyd_MPa=345, vy_sd_kN=1000, vz_sd_kN=1000, legacy_compat=False)
    assert result.verifica_anima.passed is False
    assert result.verifica_ali.passed is False
