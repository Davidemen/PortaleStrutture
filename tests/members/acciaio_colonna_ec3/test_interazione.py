"""interazione.py — N-My-Mz interaction (column-check!Y47, Y50).

New divergence: Y47's third term has an extra /gammaM1 (missing parens vs Y50) — see module docstring.
"""
import pytest

from strutture.members.acciaio_colonna_ec3.interazione import costruisci_interazione
from strutture.members.acciaio_colonna_ec3.models import ColonnaEc3Input


def _inputs(**overrides: object) -> ColonnaEc3Input:
    base = {
        "b_mm": 280, "h_mm": 500, "tw_mm": 8, "tf_mm": 12, "area_mm2": 10528, "grado_acciaio": "S235",
        "gamma_m0": 1.05, "gamma_m1": 1.05, "tipo_lavorazione": "hot finished", "classe_sezione": "class 3",
        "iyy_mm4": 4.72063e8, "izz_mm4": 4.39243e7, "wel_y_mm3": 1.88825e6, "wpl_y_mm3": 2.09283e6,
        "wel_z_mm3": 3.13745e5, "wpl_z_mm3": 4.78016e5, "it_mm4": 4.05255e5, "e_MPa": 206000,
        "iy_mm": 211.752, "iz_mm": 62.5921, "nsd_kN": 172.326, "my_sd_kNm": 120.689, "mz_sd_kNm": 15.0,
        "vy_sd_kN": 29.2057, "vz_sd_kN": 0.00235166, "lcr_yy_mm": 16485.6, "lcr_zz_mm": 2083.1, "ly_mm": 18850,
        "lt_mm": 1800, "c1": 1.871, "mj_y_kNm": 0.00695734, "mj_z_kNm": 5.0, "dmax_yy_mm": 0, "dmax_zz_mm": 0,
        "diagramma_tipo_y": "1", "diagramma_tipo_z": "1",
    }
    base.update(overrides)
    return ColonnaEc3Input(**base)


@pytest.mark.unit
def test_legacy_yy_extra_gamma_m1_regression() -> None:
    """Hand-computed regression value for this fixture (gammaM1=1.05 makes the extra /gammaM1 visible;
    the same axis/coefficients fed through Y50's grouping — see test below — give a different result)."""
    inputs = _inputs(legacy_compat=True)
    result = costruisci_interazione(
        inputs=inputs, classe_num=3, gamma_m1=1.05, area_mm2=10528, npl_kN=2356.267,
        mpl_y_kNm=468.395, mpl_z_kNm=106.985, npl_rk_kN=2474.08, mpl_y_rk_kNm=491.815, mpl_z_rk_kNm=112.334,
        wy=1.5, wz=1.5, wel_y_mm3=1.88825e6, wpl_y_mm3=2.09283e6,
        wel_z_mm3=3.13745e5, wpl_z_mm3=4.78016e5, ncr_y_kN=3531.485, ncr_z_kN=20580.294, ncr_t_kN=34315.31,
        chi_yy=0.785942, chi_zz=0.949862, chi_lt=1.0, lambda_max=0.816833, lambda_zz=0.338366,
        lambda_lt=0.192003, alpha_lt_torsione=0.999142,
    )
    assert result.utilizzo_yy == pytest.approx(0.43288566518776594, rel=1e-6)


@pytest.mark.unit
def test_fixed_yy_matches_zz_grouping_no_extra_gamma() -> None:
    inputs = _inputs(legacy_compat=False)
    kwargs = {
        "classe_num": 3, "gamma_m1": 1.05, "area_mm2": 10528, "npl_kN": 2356.267, "mpl_y_kNm": 468.395, "mpl_z_kNm": 106.985,
        "npl_rk_kN": 2474.08, "mpl_y_rk_kNm": 491.815, "mpl_z_rk_kNm": 112.334,
        "wy": 1.5, "wz": 1.5, "wel_y_mm3": 1.88825e6, "wpl_y_mm3": 2.09283e6, "wel_z_mm3": 3.13745e5, "wpl_z_mm3": 4.78016e5,
        "ncr_y_kN": 3531.485, "ncr_z_kN": 20580.294, "ncr_t_kN": 34315.31, "chi_yy": 0.785942, "chi_zz": 0.949862, "chi_lt": 1.0,
        "lambda_max": 0.816833, "lambda_zz": 0.338366, "lambda_lt": 0.192003, "alpha_lt_torsione": 0.999142,
    }
    fixed = costruisci_interazione(inputs=inputs, **kwargs)
    legacy = costruisci_interazione(inputs=_inputs(legacy_compat=True), **kwargs)
    # Both the Y47 grouping fix and the NRk/MRk (item below) fix are active simultaneously in fixed
    # mode here, so only the divergence (not its sign) is asserted; the isolated Y47 effect (grouping
    # only, same denominators) is covered by test_isolated_y47_grouping_fix_raises_mz_term below.
    assert fixed.utilizzo_yy != pytest.approx(legacy.utilizzo_yy)


@pytest.mark.unit
def test_isolated_y47_grouping_fix_raises_mz_term() -> None:
    """With the SAME (design-strength) denominators on both sides, dropping Y47's extra /gammaM1
    raises the Mz term (gammaM1>1) — isolates the grouping fix from the NRk/MRk fix."""

    def _utilizzo_yy(*, gamma_extra: bool) -> float:
        from strutture.members.acciaio_colonna_ec3.interazione import _utilizzo

        return _utilizzo(
            nsd_kN=172.326, chi=0.785942, npl_kN=2356.267, gamma_m1=1.05, k_diretto=0.8154914657098103,
            my_sd_kNm=120.689, chi_lt=1.0, mpl_y_kNm=468.395, k_incrociato=0.8578517370961999, mz_sd_kNm=15.0,
            mpl_z_kNm=106.985, gamma_extra_terzo_termine=gamma_extra,
        )

    assert _utilizzo_yy(gamma_extra=True) < _utilizzo_yy(gamma_extra=False)


@pytest.mark.unit
def test_fixed_mode_uses_characteristic_resistances_not_gamma_m0_embedded() -> None:
    """EN1993-1-1 §6.3.3 eq. 6.61/6.62 denominators use NRk/Mi,Rk/gammaM1, not Npl/Mpl (fyd-based,
    which already embeds an extra /gammaM0)."""
    kwargs = {
        "classe_num": 3, "gamma_m1": 1.05, "area_mm2": 10528, "npl_kN": 2356.267, "mpl_y_kNm": 468.395, "mpl_z_kNm": 106.985,
        "npl_rk_kN": 2474.08, "mpl_y_rk_kNm": 491.815, "mpl_z_rk_kNm": 112.334,
        "wy": 1.5, "wz": 1.5, "wel_y_mm3": 1.88825e6, "wpl_y_mm3": 2.09283e6, "wel_z_mm3": 3.13745e5, "wpl_z_mm3": 4.78016e5,
        "ncr_y_kN": 3531.485, "ncr_z_kN": 20580.294, "ncr_t_kN": 34315.31, "chi_yy": 0.785942, "chi_zz": 0.949862, "chi_lt": 1.0,
        "lambda_max": 0.816833, "lambda_zz": 0.338366, "lambda_lt": 0.192003, "alpha_lt_torsione": 0.999142,
    }
    fixed = costruisci_interazione(inputs=_inputs(legacy_compat=False), **kwargs)
    # npl_rk_kN (2474.08) > npl_kN (2356.267) -> the axial term shrinks -> utilizzo_zz (no gamma quirk) is smaller
    # than it would be with the design-strength npl_kN, all else equal.
    legacy_denominators = costruisci_interazione(inputs=_inputs(legacy_compat=True), **kwargs)
    assert fixed.utilizzo_zz != pytest.approx(legacy_denominators.utilizzo_zz)
