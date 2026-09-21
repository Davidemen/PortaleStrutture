"""Fixed-behaviour tests (legacy_compat=False): divergences from docs/divergences/ca-punzonamento.md."""
import pytest
from pydantic import ValidationError

from strutture.members.ca_punzonamento import shear_reinf_design as design
from strutture.members.ca_punzonamento.compose import run
from strutture.members.ca_punzonamento.models import PunzonamentoInput
from strutture.members.ca_punzonamento.perimeter_area import area_within_perimeter_mm2
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit

BASE = {
    "ved_kN": 225, "pterreno_MPa": 0, "lato_a_mm": 400, "lato_b_mm": 400, "h_mm": 500, "diametro_mm": 0,
    "fck_MPa": 35, "copriferro_mm": 50, "posizione": "interno", "px_mm": 200, "py_mm": 200, "phix_mm": 20,
    "phiy_mm": 20, "a1eff_mm": 400, "bu_mm": 380, "st_mm": 200, "phi_staffa_mm": 12, "n_staffe": 8,
}


def test_phi_staffa_28_accepted_only_under_legacy_compat():
    PunzonamentoInput(**{**BASE, "phi_staffa_mm": 28, "legacy_compat": True})
    with pytest.raises(ValidationError, match="non commerciale"):
        PunzonamentoInput(**{**BASE, "phi_staffa_mm": 28, "legacy_compat": False})


def test_phi_staffa_18_is_the_code_standard_replacement_for_the_typo():
    PunzonamentoInput(**{**BASE, "phi_staffa_mm": 18, "legacy_compat": False})


def test_fywd_ef_uncapped_in_legacy_mode():
    """Divergence: H56=250+0.25d, no cap, for a thick slab (d>560mm) where fywd,ef would exceed fyd."""
    d_mm = 600  # 250+0.25*600 = 400 MPa > fyd(B450C) = 391.3 MPa
    legacy = design.fywd_ef_MPa(d_mm, legacy_compat=True)
    fixed = design.fywd_ef_MPa(d_mm, legacy_compat=False)
    assert legacy == pytest.approx(400.0, rel=1e-9)
    assert fixed == pytest.approx(391.304, rel=1e-4)
    assert fixed < legacy


def test_fywd_ef_not_capped_when_below_fyd():
    """No divergence at the golden case's d=430mm: 250+0.25*430=357.5 < fyd=391.3."""
    legacy = design.fywd_ef_MPa(430.0, legacy_compat=True)
    fixed = design.fywd_ef_MPa(430.0, legacy_compat=False)
    assert legacy == pytest.approx(fixed, rel=1e-9)


def test_armatura_group_present_in_legacy_mode_even_when_not_needed():
    report = run(PunzonamentoInput(**BASE, legacy_compat=True))
    assert report.data.perimetro_critico.armatura_necessaria is False
    assert report.data.armatura is not None
    assert report.data.armatura.n_file < 0  # spec's own cached "-1", meaningless but reproduced


def test_armatura_group_absent_in_code_standard_mode_when_not_needed():
    report = run(PunzonamentoInput(**BASE, legacy_compat=False))
    assert report.data.perimetro_critico.armatura_necessaria is False
    assert report.data.armatura is None


def test_armatura_group_present_in_both_modes_when_actually_needed():
    overrides = {**BASE, "ved_kN": 1300, "phi_staffa_mm": 18}
    for legacy_compat in (True, False):
        report = run(PunzonamentoInput(**overrides, legacy_compat=legacy_compat))
        assert report.data.perimetro_critico.armatura_necessaria is True
        assert report.data.armatura is not None
        assert report.data.armatura.n_file >= 2


def test_area_within_perimeter_ignores_circular_shape_in_legacy_mode():
    """Divergence: the sheet's A_a formula never branches for a circular column (A=lato_a_mm=0),
    silently missing the pi*(D/2)*a + pi*(D/2)^2 terms."""
    legacy = area_within_perimeter_mm2(0.0, 0.0, 500.0, 200.0, legacy_compat=True)
    fixed = area_within_perimeter_mm2(0.0, 0.0, 500.0, 200.0, legacy_compat=False)
    assert legacy == pytest.approx(3.14159265 * 200.0**2, rel=1e-6)  # only the pi*a^2 term survives
    assert fixed > legacy  # correct circular area also includes the column's own footprint


def test_area_within_perimeter_matches_when_column_is_square():
    """No divergence when A=B: both formulas reduce to the same rounded-rectangle area."""
    legacy = area_within_perimeter_mm2(400.0, 400.0, 0.0, 215.0, legacy_compat=True)
    fixed = area_within_perimeter_mm2(400.0, 400.0, 0.0, 215.0, legacy_compat=False)
    assert legacy == pytest.approx(fixed, rel=1e-9)


def test_rho_capped_at_2_percent_via_shared_v_rd_c_in_both_modes():
    """Divergence: shared.ec2_shear.v_rd_c always caps rho_l at 2% (EC2 §6.4.4(1)); the sheet's own
    D37 formula does not, so this tool cannot literally reproduce an out-of-clause rho even under
    legacy_compat=True (docs/divergences/ca-punzonamento.md)."""
    overrides = {**BASE, "px_mm": 50, "py_mm": 50, "phix_mm": 25, "phiy_mm": 25}
    legacy = run(PunzonamentoInput(**overrides, legacy_compat=True))
    fixed = run(PunzonamentoInput(**overrides, legacy_compat=False))
    assert legacy.data.perimetro_critico.rho > 0.02
    assert legacy.data.perimetro_critico.v_rd_i_MPa == pytest.approx(fixed.data.perimetro_critico.v_rd_i_MPa, rel=1e-9)


def test_perimeter_rows_singularity_raises_calc_error():
    """A degenerate a1eff/bu/H layout that yields exactly one radial row makes sr undefined
    (division by zero in the sheet's own D51 formula, #DIV/0! there too)."""
    overrides = {**BASE, "ved_kN": 800, "phi_staffa_mm": 18}
    with pytest.raises(CalcError, match="una sola fila"):
        run(PunzonamentoInput(**overrides, legacy_compat=True))


@pytest.mark.parametrize(
    "overrides",
    [
        {"ved_kN": 0},
        {"lato_a_mm": -1},
        {"h_mm": 0},
        {"fck_MPa": 0},
        {"copriferro_mm": 0},
        {"px_mm": 0},
        {"phi_staffa_mm": 11},
        {"n_staffe": 0},
    ],
)
def test_invalid_inputs_rejected(overrides):
    with pytest.raises(ValidationError):
        PunzonamentoInput(**{**BASE, **overrides})


def test_circular_column_requires_diametro():
    with pytest.raises(ValidationError, match="diametro"):
        PunzonamentoInput(**{**BASE, "lato_a_mm": 0, "lato_b_mm": 0, "diametro_mm": 0})


def test_rectangular_column_requires_lato_b():
    with pytest.raises(ValidationError, match="lato_b_mm"):
        PunzonamentoInput(**{**BASE, "lato_a_mm": 400, "lato_b_mm": 0})


def test_circular_column_accepts_zero_lato_b():
    PunzonamentoInput(**{**BASE, "lato_a_mm": 0, "lato_b_mm": 0, "diametro_mm": 500})


def test_asw_min_check_present_and_passing_with_adequate_stirrups():
    """EN 1992-1-1 §9.4.3(2) eq. (9.11): the minimum shear-reinforcement area must actually be checked
    against the area provided, not just computed and left unused."""
    overrides = {**BASE, "ved_kN": 1300, "phi_staffa_mm": 8}
    report = run(PunzonamentoInput(**overrides, legacy_compat=False))
    check = next(c for c in report.checks if c.name == "Area minima delle cuciture verticali")
    assert check.clause == "EN 1992-1-1 §9.4.3(2) eq. (9.11)"
    assert check.unit == "mm2"
    assert check.value == pytest.approx(report.data.armatura.area_staffa_mm2, rel=1e-9)
    assert check.limit == pytest.approx(report.data.armatura.asw_min_mm2, rel=1e-9)
    assert check.passed is True


def test_asw_min_check_fails_when_stirrup_area_below_minimum():
    """Larger tangential spacing `st_mm` raises Asw,min (eq. 9.11) past the fixed φ8 stirrup area,
    so the check must actually fail instead of being reported as verified."""
    overrides = {**BASE, "ved_kN": 1300, "phi_staffa_mm": 8, "st_mm": 600}
    report = run(PunzonamentoInput(**overrides, legacy_compat=False))
    check = next(c for c in report.checks if c.name == "Area minima delle cuciture verticali")
    assert check.value < check.limit
    assert check.passed is False


def test_coeff_vrd_max_defaults_to_04_a1_2014_in_code_standard_mode():
    """docs/divergences/ec2-shared.md: the tool's own explicit `coeff_vrd_max` choice, not a silent
    shared default; the un-overridden run must match `V_RD_MAX_COEFF_A1_2014` (0.4)."""
    report = run(PunzonamentoInput(**BASE, legacy_compat=False))
    with_default = report.data.faccia_pilastro.v_rd_max_MPa
    report_explicit = run(PunzonamentoInput(**BASE, legacy_compat=False, coeff_vrd_max=0.4))
    assert with_default == pytest.approx(report_explicit.data.faccia_pilastro.v_rd_max_MPa, rel=1e-12)


def test_coeff_vrd_max_04_vs_05_give_resistances_in_ratio_08_in_code_standard_mode():
    a1_2014 = run(PunzonamentoInput(**BASE, legacy_compat=False, coeff_vrd_max=0.4))
    na_it = run(PunzonamentoInput(**BASE, legacy_compat=False, coeff_vrd_max=0.5))
    assert a1_2014.data.faccia_pilastro.v_rd_max_MPa == pytest.approx(
        na_it.data.faccia_pilastro.v_rd_max_MPa * 0.8, rel=1e-9,
    )


def test_coeff_vrd_max_ignored_in_legacy_mode():
    """legacy_compat=True must keep reproducing the sheet's own `0.2*0.85/1.5` coefficient regardless
    of `coeff_vrd_max` (docs/divergences/ca-punzonamento.md)."""
    legacy_04 = run(PunzonamentoInput(**BASE, legacy_compat=True, coeff_vrd_max=0.4))
    legacy_05 = run(PunzonamentoInput(**BASE, legacy_compat=True, coeff_vrd_max=0.5))
    assert legacy_04.data.faccia_pilastro.v_rd_max_MPa == pytest.approx(
        legacy_05.data.faccia_pilastro.v_rd_max_MPa, rel=1e-12,
    )


def test_non_positive_effective_depth_raises_calc_error_instead_of_crashing():
    """h_mm/copriferro_mm/phix_mm/phiy_mm are only bounded individually (gt=0), so a valid combination
    can still yield d_mm<=0 (h=50, copriferro=40, phix=20). Must surface as a CalcError, not a bare
    ValueError leaking out of shared.ec2_shear.k_factor.k_size."""
    overrides = {**BASE, "h_mm": 50, "copriferro_mm": 40, "phix_mm": 20, "phiy_mm": 12}
    for legacy_compat in (True, False):
        with pytest.raises(CalcError, match="altezza utile"):
            run(PunzonamentoInput(**overrides, legacy_compat=legacy_compat))
