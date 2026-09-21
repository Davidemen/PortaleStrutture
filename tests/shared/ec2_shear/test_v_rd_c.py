"""§6.2.2 eq. 6.2.a (beam shear) and §6.4.4 eq. 6.47 (punching, 2d/a enhancement).
Punching numbers cross-checked against docs/specs/ca-punzonamento.md Shotblast_225N golden case
(d=430mm, rho=sqrt(rho_x*rho_y) with phix=phiy=20mm, px=py=200mm, fck=35MPa)."""
import pytest

from strutture.shared.ec2_shear import k_size, v_rd_c

D_MM = 430.0
FCK_MPA = 35.0
K = k_size(D_MM)
RHO_X = (3.14159265358979 * 20.0**2 / 4.0) / (200.0 * D_MM)
RHO = RHO_X  # rho_x == rho_y in the golden case


def test_punching_enhancement_matches_governing_perimeter_sample():
    """i=152 (a=2d): 2d/a=1.0 -> uRd,i=0.471968 MPa."""
    result = v_rd_c(K, RHO, FCK_MPA, sigma_cp_MPa=0.0, av_over_2d=1.0)
    assert result.v_rd_c_MPa == pytest.approx(0.471968, rel=2e-3)
    assert result.v_min_MPa is not None  # populated (enhanced by 2d/a), just not governing here
    assert result.enhancement_factor == 1.0


def test_punching_enhancement_matches_scan_sample_i2():
    """i=2 (a=215mm=0.5d): 2d/a=4.0 -> uRd,i=1.88787 MPa."""
    result = v_rd_c(K, RHO, FCK_MPA, sigma_cp_MPa=0.0, av_over_2d=4.0)
    assert result.v_rd_c_MPa == pytest.approx(1.88787, rel=2e-3)


def test_punching_enhancement_applies_v_min_floor_scaled_by_enhancement():
    """EN 1992-1-1 §6.4.4(2) eq. (6.50): vRd >= vmin*2d/a — the floor is enhanced too, not dropped."""
    from strutture.shared.ec2_shear import v_min as v_min_fn

    k, rho, fck_MPa, av_over_2d = 1.5, 0.0001, 20.0, 3.0
    result = v_rd_c(k, rho, fck_MPa, sigma_cp_MPa=0.0, av_over_2d=av_over_2d)
    v_min_MPa = v_min_fn(k, fck_MPa)
    assert result.concrete_term_MPa < v_min_MPa  # low rho: the floor must bind
    assert result.v_rd_c_MPa == pytest.approx(v_min_MPa * av_over_2d)
    assert result.v_min_MPa == pytest.approx(v_min_MPa)
    assert result.enhancement_factor == av_over_2d


def test_punching_enhancement_keeps_concrete_term_when_it_governs():
    """Unchanged behaviour when the concrete term already exceeds vmin (golden-case regression)."""
    result = v_rd_c(K, RHO, FCK_MPA, sigma_cp_MPa=0.0, av_over_2d=1.0)
    assert result.concrete_term_MPa > result.v_min_MPa
    assert result.v_rd_c_MPa == pytest.approx(result.concrete_term_MPa)


def test_punching_enhancement_adds_k1_sigma_cp_unscaled():
    baseline = v_rd_c(K, RHO, FCK_MPA, sigma_cp_MPa=0.0, av_over_2d=2.0)
    with_axial = v_rd_c(K, RHO, FCK_MPA, sigma_cp_MPa=1.0, av_over_2d=2.0)
    assert with_axial.k1_sigma_cp_MPa == pytest.approx(0.15 * 1.0)
    assert with_axial.v_rd_c_MPa == pytest.approx(baseline.v_rd_c_MPa + 0.15 * 1.0)


def test_beam_shear_without_enhancement_applies_v_min_floor():
    """Low reinforcement ratio: vmin governs over the concrete term."""
    result = v_rd_c(k=2.0, rho=0.0001, fck_MPa=20.0, sigma_cp_MPa=0.0)
    assert result.v_min_MPa is not None
    assert result.v_rd_c_MPa == pytest.approx(result.v_min_MPa)
    assert result.enhancement_factor is None


def test_beam_shear_axial_compression_adds_k1_sigma_cp():
    baseline = v_rd_c(k=1.5, rho=0.01, fck_MPa=30.0, sigma_cp_MPa=0.0)
    with_axial = v_rd_c(k=1.5, rho=0.01, fck_MPa=30.0, sigma_cp_MPa=2.0)
    assert with_axial.k1_sigma_cp_MPa == pytest.approx(0.15 * 2.0)
    assert with_axial.v_rd_c_MPa == pytest.approx(baseline.v_rd_c_MPa + 0.15 * 2.0)


def test_rho_is_capped_at_0_02():
    high_rho = v_rd_c(k=1.5, rho=0.05, fck_MPa=30.0, sigma_cp_MPa=0.0)
    capped = v_rd_c(k=1.5, rho=0.02, fck_MPa=30.0, sigma_cp_MPa=0.0)
    assert high_rho.v_rd_c_MPa == pytest.approx(capped.v_rd_c_MPa)


def test_national_annex_coefficients_are_overridable():
    default = v_rd_c(k=1.5, rho=0.01, fck_MPa=30.0, sigma_cp_MPa=0.0)
    custom = v_rd_c(k=1.5, rho=0.01, fck_MPa=30.0, sigma_cp_MPa=0.0, c_rd_c_coefficient=0.20, k1=0.10)
    assert custom.concrete_term_MPa != pytest.approx(default.concrete_term_MPa)


@pytest.mark.parametrize(
    ("k", "rho", "fck_MPa", "gamma_c"),
    [(1.0, 0.01, 0.0, 1.5), (1.0, 0.01, -1.0, 1.5), (1.0, -0.01, 30.0, 1.5), (1.0, 0.01, 30.0, 0.0)],
)
def test_invalid_inputs_raise(k, rho, fck_MPa, gamma_c):
    with pytest.raises(ValueError):
        v_rd_c(k, rho, fck_MPa, sigma_cp_MPa=0.0, gamma_c=gamma_c)
