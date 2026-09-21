"""Unit tests for `genera_righe` — grid shape, degenerate first row, cumulative monotonicity,
and the "never a silent 0" contract for coverage gaps."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.righe import genera_righe
from strutture.shared.soil_layers import SoilLayer
from strutture.shared.tables import KeyNotFound

_LAYERS_FULL_COVERAGE = (
    SoilLayer(z_top_m=0.0, z_bot_m=3.7, modulo_MPa=5.5),
    SoilLayer(z_top_m=3.7, z_bot_m=50.0, modulo_MPa=7.0),
)
_LAYERS_PARTIAL_COVERAGE = (SoilLayer(z_top_m=0.0, z_bot_m=2.0, modulo_MPa=5.5),)


def _generate(layers, *, metodo="approssimato", legacy_compat=False, z_max_m=5.0, dz_m=1.0):
    return genera_righe(49.03325, 3.5, 5.0, 17.65197, layers, metodo=metodo, dz_m=dz_m, z_max_m=z_max_m, legacy_compat=legacy_compat)


@pytest.mark.unit
def test_row_count_matches_depth_grid() -> None:
    righe = _generate(_LAYERS_FULL_COVERAGE, z_max_m=5.0, dz_m=1.0)
    assert len(righe) == 6  # 0,1,2,3,4,5


@pytest.mark.unit
def test_first_row_is_degenerate() -> None:
    righe = _generate(_LAYERS_FULL_COVERAGE)
    assert righe[0].z_m == pytest.approx(0.0)
    assert righe[0].delta_h_cm == pytest.approx(0.0)
    assert righe[0].cumulativo_cm == pytest.approx(0.0)


@pytest.mark.unit
def test_cumulative_is_non_decreasing() -> None:
    righe = _generate(_LAYERS_FULL_COVERAGE)
    cumulativi = [riga.cumulativo_cm for riga in righe]
    assert cumulativi == sorted(cumulativi)


@pytest.mark.unit
def test_raises_key_not_found_when_layers_do_not_cover_z_max_and_not_legacy() -> None:
    with pytest.raises(KeyNotFound, match="non copre"):
        _generate(_LAYERS_PARTIAL_COVERAGE, z_max_m=5.0, legacy_compat=False)


@pytest.mark.unit
def test_legacy_mode_zeroes_the_increment_past_coverage_instead_of_raising() -> None:
    righe = _generate(_LAYERS_PARTIAL_COVERAGE, z_max_m=5.0, legacy_compat=True)
    oltre_copertura = [riga for riga in righe if riga.z_m > 2.0]
    assert oltre_copertura
    assert all(riga.eed_kPa is None for riga in oltre_copertura)
    assert all(riga.delta_h_cm == pytest.approx(0.0) for riga in oltre_copertura)


@pytest.mark.unit
def test_both_delta_sigma_methods_are_reported() -> None:
    righe = _generate(_LAYERS_FULL_COVERAGE, metodo="newmark")
    riga_a_profondita = righe[2]
    assert riga_a_profondita.delta_sigma_approssimato_kPa is not None
    assert riga_a_profondita.delta_sigma_newmark_kPa is not None
    assert riga_a_profondita.delta_sigma_kPa == pytest.approx(riga_a_profondita.delta_sigma_newmark_kPa)


@pytest.mark.unit
def test_default_sigma_v0_ignores_embedment_and_water_table_like_before() -> None:
    """No `d_m`/`water_table_m` given => unchanged legacy formula (Δσ'v below the base, buoyant
    from z=0), so old call sites keep working untouched."""
    righe = _generate(_LAYERS_FULL_COVERAGE, z_max_m=5.0, dz_m=1.0)
    riga_5m = righe[-1]
    assert riga_5m.sigma_v0_kPa == pytest.approx(17.65197 * 5.0 - 9.80665 * 5.0, rel=1e-6)


@pytest.mark.unit
def test_standard_mode_sigma_v0_is_the_total_stress_from_ground_level_dry_site() -> None:
    """docs/architecture-batch2.md §7 review finding HIGH/`righe.py`: for a dry site (no water
    table) σ'v0 must include the embedment overburden γ·D and use the total (not buoyant) weight."""
    righe = genera_righe(
        49.03325, 3.5, 5.0, 18.0, _LAYERS_FULL_COVERAGE,
        metodo="approssimato", dz_m=1.0, z_max_m=5.0, legacy_compat=False,
        d_m=2.0, water_table_m=None,
    )
    riga_5m = righe[-1]
    assert riga_5m.sigma_v0_kPa == pytest.approx(18.0 * (2.0 + 5.0))


@pytest.mark.unit
def test_standard_mode_sigma_v0_applies_buoyant_weight_below_the_water_table() -> None:
    righe = genera_righe(
        49.03325, 3.5, 5.0, 18.0, _LAYERS_FULL_COVERAGE,
        metodo="approssimato", dz_m=1.0, z_max_m=5.0, legacy_compat=False,
        d_m=2.0, water_table_m=1.0,
    )
    riga_5m = righe[-1]
    # z=5 m below the base = 7 m from ground level; water table 1 m below ground level.
    atteso = 18.0 * 1.0 + (18.0 - 9.80665) * (7.0 - 1.0)
    assert riga_5m.sigma_v0_kPa == pytest.approx(atteso, rel=1e-6)


@pytest.mark.unit
def test_legacy_mode_ignores_embedment_and_water_table_even_when_given() -> None:
    """`legacy_compat=True` must stay frozen: `d_m`/`water_table_m` are ignored."""
    righe = genera_righe(
        49.03325, 3.5, 5.0, 18.0, _LAYERS_FULL_COVERAGE,
        metodo="approssimato", dz_m=1.0, z_max_m=5.0, legacy_compat=True,
        d_m=2.0, water_table_m=1.0,
    )
    riga_5m = righe[-1]
    assert riga_5m.sigma_v0_kPa == pytest.approx(18.0 * 5.0 - 9.80665 * 5.0, rel=1e-6)
