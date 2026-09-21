"""Fixed-behaviour tests (legacy_compat=False): divergences from docs/divergences/ca-taglio-non-armato.md."""
import inspect

import pytest
from pydantic import ValidationError

from strutture.members.ca_taglio_non_armato import shear_resistance
from strutture.members.ca_taglio_non_armato.axial_stress import sigma_cp_MPa
from strutture.members.ca_taglio_non_armato.compose import run
from strutture.members.ca_taglio_non_armato.longitudinal_ratio import rho_l
from strutture.members.ca_taglio_non_armato.models import TaglioNonArmatoInput
from strutture.members.ca_taglio_non_armato.shear_resistance import vrd1_kN, vrd2_kN

pytestmark = pytest.mark.unit


def test_shear_resistance_uses_shared_n_to_kn_conversion():
    """The N->kN conversion must go through shared.units.n_to_kn, not a raw `/ 1000.0` literal."""
    source = inspect.getsource(shear_resistance)
    assert "1000.0" not in source
    assert "n_to_kn" in source


def test_vrd1_and_vrd2_values_unaffected_by_conversion_helper():
    v1 = vrd1_kN(k=1.5, rho_l=0.01, fck_MPa=25, sigma_cp_MPa=0.5, bw_mm=300, d_mm=450)
    v2 = vrd2_kN(vmin_MPa=0.4, sigma_cp_MPa=0.5, bw_mm=300, d_mm=450)
    assert v1 == pytest.approx((0.18 * 1.5 * (100 * 0.01 * 25) ** (1 / 3) / 1.5 + 0.15 * 0.5) * 300 * 450 / 1000.0, rel=1e-9)
    assert v2 == pytest.approx((0.4 + 0.15 * 0.5) * 300 * 450 / 1000.0, rel=1e-9)


def test_sigma_cp_uses_bw_h():
    """sigma_cp = NEd/Ac with Ac = bw*h (full concrete section, NTC2018 §4.1.2.3.5.1 / EN1992-1-1 §6.2.2(1)).

    Not a divergence: identical in both legacy_compat modes (sheet's bw*h formula is correct).
    """
    result = sigma_cp_MPa(ned_kN=500, bw_mm=1000, h_mm=500, fcd_MPa=16.4617)
    assert result == pytest.approx(500_000 / (1000 * 500), rel=1e-9)


def test_sigma_cp_capped_at_02_fcd():
    capped = sigma_cp_MPa(ned_kN=2000, bw_mm=300, h_mm=500, fcd_MPa=16.4617)
    assert capped == pytest.approx(0.2 * 16.4617, rel=1e-9)


def test_rho_l_sheet_uncapped():
    """Divergence 2: legacy_compat=True never caps rho_l at 0.02."""
    raw = rho_l(asl_mm2=25000, bw_mm=1500, d_mm=560, legacy_compat=True)
    assert raw == pytest.approx(25000 / (1500 * 560), rel=1e-9)
    assert raw > 0.02


def test_rho_l_fixed_capped_at_002():
    """Divergence 2 fix: legacy_compat=False clamps rho_l at 0.02 per §4.1.2.3.5.1."""
    capped = rho_l(asl_mm2=25000, bw_mm=1500, d_mm=560, legacy_compat=False)
    assert capped == pytest.approx(0.02, rel=1e-9)


def test_run_fixed_mode_caps_rho_l_and_changes_vrd():
    legacy_report = run(TaglioNonArmatoInput(rck_MPa=30, h_mm=600, c_mm=40, bw_mm=1500, asl_mm2=25000, ned_kN=0, legacy_compat=True))
    fixed_report = run(TaglioNonArmatoInput(rck_MPa=30, h_mm=600, c_mm=40, bw_mm=1500, asl_mm2=25000, ned_kN=0, legacy_compat=False))
    assert legacy_report.data.taglio.rho_l > 0.02
    assert fixed_report.data.taglio.rho_l == pytest.approx(0.02, rel=1e-9)
    assert fixed_report.data.taglio.vrd1_kN < legacy_report.data.taglio.vrd1_kN


@pytest.mark.parametrize(
    "overrides",
    [
        {"rck_MPa": 0},
        {"rck_MPa": -5},
        {"h_mm": 0},
        {"c_mm": -1},
        {"bw_mm": 0},
        {"asl_mm2": -1},
    ],
)
def test_invalid_inputs_rejected(overrides):
    base = {"rck_MPa": 35, "h_mm": 500, "c_mm": 50, "bw_mm": 1000, "asl_mm2": 1005, "ned_kN": 0}
    with pytest.raises(ValidationError):
        TaglioNonArmatoInput(**{**base, **overrides})


def test_k_capped_at_2_for_small_effective_depth():
    report = run(TaglioNonArmatoInput(rck_MPa=30, h_mm=150, c_mm=25, bw_mm=250, asl_mm2=226, ned_kN=0, legacy_compat=True))
    assert report.data.taglio.k == pytest.approx(2.0, rel=1e-9)


def test_asl_and_barre_both_given_rejected():
    """v2 delta #2: N°/Ø replace direct Asl, not alongside it."""
    with pytest.raises(ValidationError):
        TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, asl_mm2=1005, n_barre=5, diametro_barre_mm=12, ned_kN=0)


def test_neither_asl_nor_barre_given_rejected():
    with pytest.raises(ValidationError):
        TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, ned_kN=0)


def test_only_n_barre_without_diametro_rejected():
    with pytest.raises(ValidationError):
        TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, n_barre=5, ned_kN=0)


def test_asl_from_n_barre_e_diametro():
    """v2 delta #2: Asl = N° * pi*diametro^2/4 (sheet `1m` B13)."""
    report = run(TaglioNonArmatoInput(rck_MPa=40, fck_MPa=32, h_mm=250, c_mm=68, bw_mm=1000, n_barre=5, diametro_barre_mm=12, ned_kN=0, legacy_compat=True))
    assert report.data.geometria.asl_mm2 == pytest.approx(5 * 3.14159265358979 * 12**2 / 4, rel=1e-9)


def test_fck_direct_overrides_rck_derived_value():
    """v2 delta #1: a direct fck (sheet `1m` B3) is used as-is, Rck becomes informational."""
    report = run(TaglioNonArmatoInput(rck_MPa=40, fck_MPa=32, h_mm=250, c_mm=68, bw_mm=1000, n_barre=5, diametro_barre_mm=12, ned_kN=0, legacy_compat=True))
    assert report.data.materiali.fck_MPa == pytest.approx(32, rel=1e-9)


def test_fck_omitted_falls_back_to_rck_derived_value():
    report = run(TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, asl_mm2=1005, ned_kN=0, legacy_compat=True))
    assert report.data.materiali.fck_MPa == pytest.approx(0.83 * 35, rel=1e-9)


def test_fck_incoherent_with_rck_raises_a_warning():
    """v2 'Suspected bugs': the sheet accepts fck/Rck inconsistent pairs silently; the port warns instead."""
    report = run(TaglioNonArmatoInput(rck_MPa=40, fck_MPa=45, h_mm=250, c_mm=68, bw_mm=1000, n_barre=5, diametro_barre_mm=12, ned_kN=0, legacy_compat=True))
    assert report.ok
    assert report.warnings
    assert "incoerente" in report.warnings[0]


def test_fck_coherent_with_rck_no_warning():
    report = run(TaglioNonArmatoInput(rck_MPa=40, fck_MPa=32, h_mm=250, c_mm=68, bw_mm=1000, n_barre=5, diametro_barre_mm=12, ned_kN=0, legacy_compat=True))
    assert report.ok
    assert report.warnings == ()


def test_gamma_c_default_matches_v1_constant():
    with_default = run(TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, asl_mm2=1005, ned_kN=0, legacy_compat=True))
    with_explicit = run(TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, asl_mm2=1005, ned_kN=0, gamma_c=1.5, legacy_compat=True))
    assert with_default.data.taglio.vrd_kN == pytest.approx(with_explicit.data.taglio.vrd_kN, rel=1e-12)


def test_gamma_c_changes_fcd_and_vrd1():
    baseline = run(TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, asl_mm2=1005, ned_kN=0, legacy_compat=True))
    higher_gamma_c = run(TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, asl_mm2=1005, ned_kN=0, gamma_c=1.6, legacy_compat=True))
    assert higher_gamma_c.data.materiali.fcd_MPa < baseline.data.materiali.fcd_MPa
    assert higher_gamma_c.data.taglio.vrd1_kN < baseline.data.taglio.vrd1_kN


def test_check_ratio_flags_uncapped_rho_l_in_legacy_mode():
    report = run(TaglioNonArmatoInput(rck_MPa=30, h_mm=600, c_mm=40, bw_mm=1500, asl_mm2=25000, ned_kN=0, legacy_compat=True))
    check = next(c for c in report.checks if "armatura longitudinale" in c.name.lower())
    assert not check.passed
    assert check.value == pytest.approx(report.data.taglio.rho_l, rel=1e-9)
    assert check.limit == pytest.approx(0.02, rel=1e-9)
    assert check.unit == "-"


def test_check_ratio_flags_uncapped_rho_l_in_code_standard_mode_too():
    """Reviewed finding: the check must compare the RAW (uncapped) ratio, not the value already
    clamped to 0.02 by rho_l() under legacy_compat=False — otherwise it can never fail."""
    report = run(TaglioNonArmatoInput(rck_MPa=30, h_mm=600, c_mm=40, bw_mm=1500, asl_mm2=25000, ned_kN=0, legacy_compat=False))
    check = next(c for c in report.checks if "armatura longitudinale" in c.name.lower())
    raw = 25000 / (1500 * 560)
    assert raw > 0.02
    assert report.data.taglio.rho_l == pytest.approx(0.02, rel=1e-9)  # capped value still feeds VRd,1
    assert not check.passed
    assert check.value == pytest.approx(raw, rel=1e-9)
    assert check.limit == pytest.approx(0.02, rel=1e-9)


def test_run_fixed_mode_warns_when_rho_l_cap_bites():
    report = run(TaglioNonArmatoInput(rck_MPa=30, h_mm=600, c_mm=40, bw_mm=1500, asl_mm2=25000, ned_kN=0, legacy_compat=False))
    assert any("armatura longitudinale" in w.lower() or "ρl" in w for w in report.warnings)


def test_run_fixed_mode_no_warning_when_rho_l_within_limit():
    report = run(TaglioNonArmatoInput(rck_MPa=35, h_mm=500, c_mm=50, bw_mm=1000, asl_mm2=1005, ned_kN=0, legacy_compat=False))
    assert report.warnings == ()
