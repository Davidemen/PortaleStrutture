"""annex_a_kij.py — interaction factors kyy/kyz/kzy/kzz (EN1993-1-1 Annex A, Table A.1;
column-check!AI30-AI83). The Cij correction terms divide by lambda_zz, not chi_zz — see module docstring.
"""
import pytest

from strutture.members.acciaio_colonna_ec3.annex_a_kij import cyy, cyz, czy, czz, fattore_mu, kyy, kyz, kzy, kzz


@pytest.mark.unit
def test_fattore_mu() -> None:
    assert fattore_mu(172.326, 3531.51, 0.588068) == pytest.approx((1 - 172.326 / 3531.51) / (1 - 0.588068 * 172.326 / 3531.51))


@pytest.mark.unit
def test_cyy_golden_case() -> None:
    valore = cyy(
        wy=1.10834, cmy=0.784216, lambda_max=1.01415, n_pl=0.0474445, alpha_lt=0.999142, lambda_lt=0.226433,
        chi_lt=1.0, my_sd_kNm=120.689, mz_sd_kNm=0.00639699, mpl_y_kNm=651.446, mpl_z_kNm=108.242,
        wel_y_mm3=1.88825e6, wpl_y_mm3=2.09283e6,
    )
    assert valore == pytest.approx(1.00096, rel=1e-3)


@pytest.mark.unit
def test_cyz_czy_czz_golden_case() -> None:
    kwargs = {
        "wy": 1.10834, "wz": 1.5, "cmy": 0.784216, "cmz": 0.849726, "chi_lt": 1.0, "lambda_max": 1.01415, "lambda_lt": 0.226433,
        "lambda_zz": 0.420104, "n_pl": 0.0474445, "alpha_lt": 0.999142, "my_sd_kNm": 120.689,
    }
    assert cyz(**kwargs, mpl_y_kNm=651.446, wel_z_mm3=3.13745e5, wpl_z_mm3=4.78016e5) == pytest.approx(1.00294, rel=1e-3)
    kwargs_czz = {k: v for k, v in kwargs.items() if k != "wy"}
    assert czz(**kwargs_czz, mpl_y_kNm=651.446, wel_z_mm3=3.13745e5, wpl_z_mm3=4.78016e5) == pytest.approx(0.663725, rel=1e-3)
    czy_kwargs = {
        "wy": 1.10834, "wz": 1.5, "cmy": 0.784216, "cmz": 0.849726, "chi_lt": 1.0, "lambda_max": 1.01415, "lambda_lt": 0.226433,
        "lambda_zz": 0.420104, "n_pl": 0.0474445, "alpha_lt": 0.999142, "my_sd_kNm": 120.689, "mz_sd_kNm": 0.00639699,
        "mpl_y_kNm": 651.446, "mpl_z_kNm": 108.242, "wel_y_mm3": 1.88825e6, "wpl_y_mm3": 2.09283e6,
    }
    czy_val = czy(**czy_kwargs, legacy_compat=True)
    assert czy_val == pytest.approx(1.00428, rel=1e-3)


@pytest.mark.unit
def test_czy_fixed_mode_uses_wy_power_5_not_wz() -> None:
    """EN1993-1-1 Annex A Table A.1: Czy's bracket pairs Cmy/lambda_max with wy**5, not wz**5."""
    kwargs = {
        "wy": 1.10834, "wz": 1.5, "cmy": 0.784216, "cmz": 0.849726, "chi_lt": 1.0, "lambda_max": 1.01415, "lambda_lt": 0.226433,
        "lambda_zz": 0.420104, "n_pl": 0.0474445, "alpha_lt": 0.999142, "my_sd_kNm": 120.689, "mz_sd_kNm": 0.00639699,
        "mpl_y_kNm": 651.446, "mpl_z_kNm": 108.242, "wel_y_mm3": 1.88825e6, "wpl_y_mm3": 2.09283e6,
    }
    legacy = czy(**kwargs, legacy_compat=True)
    fixed = czy(**kwargs, legacy_compat=False)
    assert fixed != pytest.approx(legacy)
    # wy < wz here -> wy**5 is a smaller divisor -> the subtracted d_lt/n_pl term is larger -> Czy smaller
    assert fixed < legacy


@pytest.mark.unit
def test_kyy_class_1_2_divides_by_cyy() -> None:
    assert kyy(2, cmy=0.784216, cm_lt=1.0, mu_y=0.979305, n_y=0.0488, cyy=1.00096) == pytest.approx(
        1.0 * 0.784216 * (0.979305 / (1 - 0.0488)) / 1.00096
    )


@pytest.mark.unit
def test_kzz_class_3_4_skips_czz() -> None:
    base = 0.85 * (0.99 / (1 - 0.05))
    assert kzz(3, cmz=0.85, mu_z=0.99, n_z=0.05, czz=123.0) == pytest.approx(base)


@pytest.mark.unit
def test_kyz_and_kzy_golden_case() -> None:
    assert kyz(3, cmz=0.849726, mu_y=0.979305, n_z=0.00837, cyz=1.0, wy=1.10834, wz=1.5) == pytest.approx(
        0.849726 * (0.979305 / (1 - 0.00837))
    )
    assert kzy(2, cmy=0.784216, cm_lt=1.0, mu_z=0.999044, n_y=0.0488, czy=1.00428, wy=1.10834, wz=1.5) == pytest.approx(
        1.0 * 0.784216 * (0.999044 / (1 - 0.0488)) / 1.00428 * 0.6 * (1.10834 / 1.5) ** 0.5
    )
