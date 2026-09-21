"""Unit tests for `profondita_critica` (the Δσv,q=0.1·Δσ'v criterion, closed-form root; the sheet
sets up a Cardano solver for the same equation but never uses it — docs/architecture-batch2.md §7
"edometrico B18/B24:B28")."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.profondita_critica import calcola_z_crit, profondita_critica
from strutture.shared.report import CalcError
from strutture.shared.soil_layers import effective_overburden
from strutture.shared.soil_stress import spread_2to1


@pytest.mark.unit
def test_calcola_z_crit_solves_the_0_1_criterion() -> None:
    """Verified numerically against docs/specs/geo-cedimenti-edometrico.md's own cross-check
    (u+v−(B+L)/3 ≈ 769.539 cm = 7.69539 m for these inputs)."""
    z_crit = calcola_z_crit(49.03325, 3.5, 5.0, 17.65197, metodo="approssimato")
    assert z_crit == pytest.approx(7.69539, rel=1e-4)
    delta_sigma = spread_2to1(49.03325, 3.5, 5.0, z_crit)
    assert delta_sigma == pytest.approx(0.1 * effective_overburden(17.65197, z_crit), rel=1e-6)


@pytest.mark.unit
def test_manual_override_always_wins() -> None:
    result = profondita_critica(49.03325, 3.5, 5.0, 17.65197, metodo="approssimato", z_crit_input_m=3.0, legacy_compat=False, z_max_m=50.0)
    assert result.z_crit_utilizzato_m == pytest.approx(3.0)
    assert result.z_crit_calcolato_m == pytest.approx(7.69539, rel=1e-4)  # still reported, not overwritten


@pytest.mark.unit
def test_manual_override_wins_in_legacy_mode_too() -> None:
    result = profondita_critica(49.03325, 3.5, 5.0, 17.65197, metodo="approssimato", z_crit_input_m=3.0, legacy_compat=True, z_max_m=50.0)
    assert result.z_crit_utilizzato_m == pytest.approx(3.0)


@pytest.mark.unit
def test_standard_mode_without_override_uses_the_computed_root() -> None:
    result = profondita_critica(49.03325, 3.5, 5.0, 17.65197, metodo="approssimato", z_crit_input_m=None, legacy_compat=False, z_max_m=50.0)
    assert result.z_crit_utilizzato_m == pytest.approx(result.z_crit_calcolato_m)


@pytest.mark.unit
def test_legacy_mode_without_override_disables_the_cutoff() -> None:
    """Reproduces the sheet's cached B18=10000 cm: a value past the depth table, so the cutoff
    never triggers within the computed rows (docs/specs "Suspected spreadsheet bugs" #1)."""
    result = profondita_critica(49.03325, 3.5, 5.0, 17.65197, metodo="approssimato", z_crit_input_m=None, legacy_compat=True, z_max_m=50.0)
    assert result.z_crit_utilizzato_m > 50.0


@pytest.mark.unit
def test_unrealistic_inputs_raise_calc_error_instead_of_a_bare_value_error() -> None:
    with pytest.raises(CalcError):
        calcola_z_crit(49.03325, 3.5, 5.0, gamma_kN_m3=1e-9, metodo="approssimato")


@pytest.mark.unit
def test_default_criterion_ignores_embedment_and_water_table_like_before() -> None:
    """No `d_m`/`water_table_m` given => the old formula (Δσ'v below the base, buoyant from
    z=0), so existing call sites are unaffected."""
    z_crit = calcola_z_crit(49.03325, 3.5, 5.0, 17.65197, metodo="approssimato")
    assert z_crit == pytest.approx(7.69539, rel=1e-4)


@pytest.mark.unit
def test_embedment_and_water_table_shift_the_criterion() -> None:
    """docs/architecture-batch2.md §7 review finding HIGH/`righe.py`: the criterion must compare
    against the total effective stress from ground level (γ·D + the increment below the base),
    not the increment alone — a dry embedded footing has a *larger* reference stress at every z,
    so the criterion is satisfied sooner (a shallower root) than the base-only formula."""
    z_crit_senza_incastro = calcola_z_crit(49.03325, 3.5, 5.0, 17.65197, metodo="approssimato", d_m=0.0, water_table_m=None)
    z_crit_con_incastro = calcola_z_crit(49.03325, 3.5, 5.0, 17.65197, metodo="approssimato", d_m=2.0, water_table_m=None)
    assert z_crit_con_incastro < z_crit_senza_incastro


@pytest.mark.unit
def test_profondita_critica_passes_embedment_and_water_table_through() -> None:
    result_senza = profondita_critica(
        49.03325, 3.5, 5.0, 17.65197, metodo="approssimato", z_crit_input_m=None,
        legacy_compat=False, z_max_m=50.0,
    )
    result_con = profondita_critica(
        49.03325, 3.5, 5.0, 17.65197, metodo="approssimato", z_crit_input_m=None,
        legacy_compat=False, z_max_m=50.0, d_m=2.0, water_table_m=None,
    )
    assert result_con.z_crit_calcolato_m < result_senza.z_crit_calcolato_m
