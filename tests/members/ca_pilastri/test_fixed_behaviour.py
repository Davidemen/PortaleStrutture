"""Hand-computed expectations for every divergence (legacy_compat=False), plus boundary/validation
tests — see docs/divergences/ca-pilastri.md."""
import math

import pytest
from pydantic import ValidationError

from strutture.members.ca_pilastri.armatura_minima import armatura_minima
from strutture.members.ca_pilastri.confinamento import altezza_critica_mm, passo_massimo_confinato_mm
from strutture.members.ca_pilastri.dettagli import (
    diametro_staffe_minimo_mm,
    perimetro_circolare_mm,
    perimetro_rettangolare_mm,
)
from strutture.members.ca_pilastri.gerarchia import GAMMA_RD, domanda_taglio_capacity_design
from strutture.members.ca_pilastri.models import PilastroCircolareInput, PilastroRettangolareInput
from strutture.members.ca_pilastri.snellezza import (
    l0_effettivo_mm,
    lambda_limite,
    raggio_inerzia_netto_rettangolare_mm,
)
from strutture.members.ca_pilastri.taglio_puntoni import coefficiente_ac
from strutture.members.ca_pilastri.tool_rettangolare import run_pilastro_rettangolare
from strutture.shared.section_geometry import rect


@pytest.mark.unit
def test_lambda_lim_fix_removes_kn_to_n_bug():
    """Spec §7.1 / architecture.md §6: legacy overstates λlim ~31x by comparing Ned in kN
    directly against Ac*fcd in N. rm is explicitly given here (=0, C=1.7) so this test isolates
    the ×1000 unit fix from the rm/C default fix covered separately below."""
    ac_mm2, fcd_MPa, ned_kN = 160000.0, 14.11, 1200.0

    legacy = lambda_limite(ned_kN, ac_mm2, fcd_MPa, rm=0.0, legacy_compat=True)
    fixed = lambda_limite(ned_kN, ac_mm2, fcd_MPa, rm=0.0, legacy_compat=False)

    assert legacy == pytest.approx(1084.358, rel=1e-4)
    assert fixed == pytest.approx(35.908, rel=1e-3)
    assert legacy / fixed > 25  # ~31x overstatement


@pytest.mark.unit
def test_lambda_lim_end_moment_ratio_rm():
    ac_mm2, fcd_MPa, ned_kN = 160000.0, 14.11, 1200.0
    baseline = lambda_limite(ned_kN, ac_mm2, fcd_MPa, rm=0.0, legacy_compat=False)
    with_rm = lambda_limite(ned_kN, ac_mm2, fcd_MPa, rm=0.5, legacy_compat=False)
    assert with_rm < baseline  # C = 1.7 - rm decreases as rm grows


@pytest.mark.unit
def test_lambda_lim_rm_none_defaults_to_c_07_not_17():
    """Review finding (CRITICAL): rm=None ("non noto") must map to C=0.7 (NTC2018 §4.1.2.3.9.2 /
    EN 1992-1-1 §5.8.3.1(1) nota 3: "se rm non è noto, si può assumere C=0.7"), equivalent to
    rm=1 (singola curvatura) — NOT to rm=0 (which gives the wrong C=1.7, a 1.7/0.7=2.43x
    overstatement of λlim)."""
    ac_mm2, fcd_MPa, ned_kN = 160000.0, 14.11, 1200.0

    unknown = lambda_limite(ned_kN, ac_mm2, fcd_MPa, rm=None, legacy_compat=False)
    single_curvature = lambda_limite(ned_kN, ac_mm2, fcd_MPa, rm=1.0, legacy_compat=False)
    rm_zero = lambda_limite(ned_kN, ac_mm2, fcd_MPa, rm=0.0, legacy_compat=False)

    assert unknown == pytest.approx(single_curvature, rel=1e-9)
    assert unknown == pytest.approx(rm_zero * 0.7 / 1.7, rel=1e-6)
    assert unknown < rm_zero


@pytest.mark.unit
def test_rm_field_defaults_to_none_not_zero():
    """Review finding (CRITICAL): the input model must not silently default to rm=0 (C=1.7); the
    "not known" state is represented by rm=None (C=0.7)."""
    base = {
        "l1_mm": 400.0, "l2_mm": 400.0, "h_mm": 3500.0, "acciaio": "B450C", "cls": "C25/30",
        "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 8,
        "diametro_ferri_mm": 16.0, "diametro_staffe_mm": 10.0, "passo_staffe_mm": 150.0,
        "mrd_kNm": 160.0, "n_ferri_l1": 3,
    }
    inputs = PilastroRettangolareInput(**base)
    assert inputs.rm is None

    from strutture.members.ca_pilastri.snellezza import coefficiente_c
    assert coefficiente_c(inputs.rm) == pytest.approx(0.7)


@pytest.mark.unit
def test_l0_becomes_a_real_input_defaulting_to_clear_height():
    """Spec §7.7: l0 was hardcoded to 3000mm regardless of H; now a real input defaulting to H
    under legacy_compat=False, and reproducing the hardcoded 3000mm only under legacy_compat=True."""
    assert l0_effettivo_mm(None, h_mm=4000.0, legacy_compat=True) == pytest.approx(3000.0)
    assert l0_effettivo_mm(None, h_mm=4000.0, legacy_compat=False) == pytest.approx(4000.0)
    assert l0_effettivo_mm(2500.0, h_mm=4000.0, legacy_compat=True) == pytest.approx(2500.0)
    assert l0_effettivo_mm(2500.0, h_mm=4000.0, legacy_compat=False) == pytest.approx(2500.0)


@pytest.mark.unit
def test_radius_of_gyration_gross_vs_net_section():
    """Spec §7.6 / architecture.md §7 decision D3: legacy uses the net (cover-reduced) section;
    code-standard uses the gross section via shared.section_geometry."""
    l1_mm, l2_mm, c_mm = 400.0, 600.0, 50.0
    net = raggio_inerzia_netto_rettangolare_mm(l1_mm, l2_mm, c_mm)
    gross = rect(l1_mm, l2_mm).radius_of_gyration_mm
    assert net == pytest.approx(86.603, rel=1e-4)
    assert gross == pytest.approx(173.205, rel=1e-4)
    assert gross != pytest.approx(net, rel=1e-2)


@pytest.mark.unit
def test_capacity_design_shear_doubles_under_code_standard():
    """Spec §7.5 / architecture.md §7 decision D3: the sheet demand is MRd/H (single hinge, no
    overstrength factor); code-standard sums both column-end resisting moments (2*MRd/H) AND
    applies gamma_Rd=1.10 (CD"B", NTC2018 §7.4.4.2.1 — see also GAMMA_RD test below)."""
    mrd_kNm, h_mm = 160.0, 3500.0
    legacy = domanda_taglio_capacity_design(mrd_kNm, h_mm, legacy_compat=True)
    fixed = domanda_taglio_capacity_design(mrd_kNm, h_mm, legacy_compat=False)
    assert legacy == pytest.approx(45.714, rel=1e-4)
    assert fixed == pytest.approx(100.571, rel=1e-4)
    assert fixed == pytest.approx(2 * 1.10 * legacy)


@pytest.mark.unit
def test_ac_selector_dead_branch_fix():
    """Spec §7.3: the sheet tests `H7<0` (column height, always > 0) instead of `σcp<0`. Direct
    call to the pure step function with a negative σcp (tension) — unreachable through the Tool
    input schema since ned_kN is constrained > 0 (pilastro semplicemente compresso)."""
    sigma_cp_MPa, fcd_MPa = -5.0, 14.11

    legacy = coefficiente_ac(sigma_cp_MPa, fcd_MPa, legacy_compat=True)
    fixed = coefficiente_ac(sigma_cp_MPa, fcd_MPa, legacy_compat=False)

    assert legacy == pytest.approx(1.0 + sigma_cp_MPa / fcd_MPa)  # falls through to the σcp<0.25fcd branch
    assert fixed == pytest.approx(1.0)  # correctly hits the "tension" branch


@pytest.mark.unit
def test_bar_spacing_rectangular_perimeter_fix():
    """Spec §7.2 / architecture.md §6: the sheet reuses the circular-column bar-spacing formula
    (2π·((L1/2)-c)), which ignores L2 entirely, on the rectangular sheet."""
    l1_mm, l2_mm, c_mm = 400.0, 600.0, 50.0
    legacy = perimetro_circolare_mm(l1_mm, c_mm)
    fixed = perimetro_rettangolare_mm(l1_mm, l2_mm, c_mm)
    assert legacy == pytest.approx(2 * math.pi * 150.0)
    assert fixed == pytest.approx(1600.0)
    assert legacy != pytest.approx(fixed, rel=1e-2)


@pytest.mark.unit
def test_stirrup_min_diameter_aggregation_fix():
    """Both sheets' summary row (J63/J70) aggregates the two minimum-diameter candidates with
    MIN; the 'live' warning cell (K16) correctly uses MAX (must satisfy both independent minima,
    NTC2018 §7.4.6.2.2)."""
    diametro_ferri_mm = 28.0  # candidates: 6 (fixed), 28/4=7
    legacy = diametro_staffe_minimo_mm(diametro_ferri_mm, legacy_compat=True)
    fixed = diametro_staffe_minimo_mm(diametro_ferri_mm, legacy_compat=False)
    assert legacy == pytest.approx(6.0)
    assert fixed == pytest.approx(7.0)


@pytest.mark.unit
def test_rectangular_stirrup_diameter_check_h9_vs_h16_bug():
    """The rectangular sheet's row 63 compares the diameter threshold against H9 (a concrete-class
    text cell) instead of H16 (the actual stirrup diameter): Excel treats any number as less than
    any text, so the check is always 'OK' regardless of the stirrup diameter — legacy_compat
    reproduces that; code-standard performs the real (and here failing) comparison."""
    base = {
        "l1_mm": 400.0, "l2_mm": 400.0, "h_mm": 3500.0, "acciaio": "B450C", "cls": "C25/30",
        "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 8,
        "diametro_ferri_mm": 28.0, "diametro_staffe_mm": 6.0, "passo_staffe_mm": 150.0,
        "mrd_kNm": 160.0, "n_ferri_l1": 3,
    }
    legacy_report = run_pilastro_rettangolare(PilastroRettangolareInput(**base, legacy_compat=True))
    fixed_report = run_pilastro_rettangolare(PilastroRettangolareInput(**base, legacy_compat=False))

    legacy_checks = {c.name: c.passed for c in legacy_report.checks}
    fixed_checks = {c.name: c.passed for c in fixed_report.checks}
    assert legacy_checks["Diametro minimo delle staffe"] is True  # 6mm staffe, 7mm richiesti: il foglio non se ne accorge
    assert fixed_checks["Diametro minimo delle staffe"] is False  # la verifica corretta lo cattura


@pytest.mark.unit
def test_armatura_minima_envelope_max_vs_min():
    """Review finding (CRITICAL): NTC2018 §4.1.6.1.2 states As,min = max(0.10*Ned/fyd, 0.003*Ac),
    an envelope (MAX), not the sheet's MIN. legacy_compat=True keeps the sheet's non-conservative
    MIN; legacy_compat=False uses the correct MAX (capped at 0.04*Ac)."""
    ac_mm2, ned_kN, fyd_MPa = 160000.0, 1200.0, 391.304  # golden case
    candidato_area = 0.003 * ac_mm2  # 480
    candidato_assiale = 0.10 * 1200.0 * 1000.0 / 391.304  # ~306.67

    as_min_legacy, _ = armatura_minima(ac_mm2, ned_kN, fyd_MPa, legacy_compat=True)
    as_min_fixed, _ = armatura_minima(ac_mm2, ned_kN, fyd_MPa, legacy_compat=False)

    assert as_min_legacy == pytest.approx(min(candidato_area, candidato_assiale), rel=1e-5)
    assert as_min_fixed == pytest.approx(max(candidato_area, candidato_assiale), rel=1e-5)
    assert as_min_fixed == pytest.approx(480.0, rel=1e-5)


@pytest.mark.unit
def test_armatura_minima_envelope_capped_at_area_ceiling():
    """The As,min envelope (NTC2018 §4.1.6.1.2) must never exceed the 4% maximum reinforcement
    ratio (§7.4.6.2.2), even for extreme Ned/fyd combinations."""
    ac_mm2, ned_kN, fyd_MPa = 10000.0, 100000.0, 100.0  # candidato_assiale huge: 100 GN.../fyd
    as_min_fixed, _ = armatura_minima(ac_mm2, ned_kN, fyd_MPa, legacy_compat=False)
    assert as_min_fixed == pytest.approx(0.04 * ac_mm2)


@pytest.mark.unit
def test_gerarchia_applies_gamma_rd_cdb_only_under_code_standard():
    """Review finding (CRITICAL): NTC2018 §7.4.4.2.1 requires VEd = gamma_Rd * sum(MRd) / lp with
    gamma_Rd=1.10 for CD"B" (this tool's declared ductility class); the sheet applies no
    overstrength factor at all. legacy_compat=True must stay identical (no gamma_Rd)."""
    mrd_kNm, h_mm = 160.0, 3500.0
    legacy = domanda_taglio_capacity_design(mrd_kNm, h_mm, legacy_compat=True)
    fixed = domanda_taglio_capacity_design(mrd_kNm, h_mm, legacy_compat=False)
    assert GAMMA_RD == pytest.approx(1.10)
    assert legacy == pytest.approx(45.714, rel=1e-4)  # unchanged sheet behaviour
    assert fixed == pytest.approx(2 * GAMMA_RD * mrd_kNm / (h_mm / 1000.0), rel=1e-6)
    assert fixed == pytest.approx(100.571, rel=1e-4)


@pytest.mark.unit
def test_detailing_checks_use_inclusive_limits_under_code_standard():
    """Review finding (MEDIUM): the NTC2018 limits are stated inclusively ("non deve essere minore
    di 12 mm", "Ø >= max(6, Ø_long/4)"); a bar/stirrup exactly at the limit must pass under
    legacy_compat=False. legacy_compat=True keeps the sheet's own strict comparisons."""
    base = {
        "l1_mm": 400.0, "l2_mm": 400.0, "h_mm": 3500.0, "acciaio": "B450C", "cls": "C25/30",
        "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 8,
        "diametro_ferri_mm": 12.0, "diametro_staffe_mm": 6.0, "passo_staffe_mm": 150.0,
        "mrd_kNm": 160.0, "n_ferri_l1": 3,
    }
    legacy_report = run_pilastro_rettangolare(PilastroRettangolareInput(**base, legacy_compat=True))
    fixed_report = run_pilastro_rettangolare(PilastroRettangolareInput(**base, legacy_compat=False))
    legacy_checks = {c.name: c.passed for c in legacy_report.checks}
    fixed_checks = {c.name: c.passed for c in fixed_report.checks}

    # phi_long = 12mm exactly at the limit: sheet (strict >) fails it, code-standard (>=) passes it.
    assert legacy_checks["Diametro minimo delle barre longitudinali"] is False
    assert fixed_checks["Diametro minimo delle barre longitudinali"] is True

    # phi_staffe = 6mm, threshold = max(6, 12/4=3) = 6mm exactly: sheet's real (non-H9-bugged)
    # comparison would fail it (strict <); code-standard (<=) passes it. The rect sheet's own
    # L63 bug (H9-vs-H16) still makes legacy_compat report True regardless (documented divergence).
    assert legacy_checks["Diametro minimo delle staffe"] is True  # unchanged H9-vs-H16 sheet bug
    assert fixed_checks["Diametro minimo delle staffe"] is True  # 6 <= 6 now passes


@pytest.mark.unit
def test_area_minima_longitudinale_inclusive_under_code_standard():
    """as_min == as exactly must pass under legacy_compat=False (`<=`); the sheet's own strict `<`
    is kept under legacy_compat=True."""
    base = {
        "l1_mm": 400.0, "l2_mm": 400.0, "h_mm": 3500.0, "acciaio": "B450C", "cls": "C25/30",
        "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 8,
        "diametro_ferri_mm": 16.0, "diametro_staffe_mm": 10.0, "passo_staffe_mm": 150.0,
        "mrd_kNm": 160.0, "n_ferri_l1": 3,
    }
    fixed_report = run_pilastro_rettangolare(PilastroRettangolareInput(**base, legacy_compat=False))
    as_min_mm2 = fixed_report.data.armatura_minima.as_min_mm2
    as_mm2 = fixed_report.data.geometria.as_mm2
    ac_mm2 = fixed_report.data.geometria.ac_mm2
    # Independently confirm the operator is inclusive using the step function directly.
    from strutture.members.ca_pilastri.regole import resolve
    from strutture.members.ca_pilastri.tool_rettangolare import _dettagli

    fixed_inputs = PilastroRettangolareInput(**base, legacy_compat=False)
    rules = resolve(fixed_inputs.norma, fixed_inputs.legacy_compat)
    _, checks = _dettagli(fixed_inputs, rules, ac_mm2, as_min_mm2, as_min_mm2)
    by_name = {c.name: c.passed for c in checks}
    assert by_name["Area minima di armatura longitudinale"] is True  # as == as_min exactly: must pass (<=)
    assert as_min_mm2 != pytest.approx(as_mm2)  # sanity: golden inputs aren't naturally at the boundary


@pytest.mark.unit
def test_rectangular_input_rejects_out_of_range_and_invalid_enum():
    base = {
        "l1_mm": 400.0, "l2_mm": 400.0, "h_mm": 3500.0, "acciaio": "B450C", "cls": "C25/30",
        "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 8,
        "diametro_ferri_mm": 16.0, "diametro_staffe_mm": 10.0, "passo_staffe_mm": 150.0,
        "mrd_kNm": 160.0, "n_ferri_l1": 3,
    }
    with pytest.raises(ValidationError):
        PilastroRettangolareInput(**{**base, "ned_kN": -1.0})  # must be > 0 (pilastro compresso)
    with pytest.raises(ValidationError):
        PilastroRettangolareInput(**{**base, "acciaio": "S355"})  # not a valid AcciaioGrado
    with pytest.raises(ValidationError):
        PilastroRettangolareInput(**{**base, "cls": "C16/20"})  # not in this sheet's dropdown
    with pytest.raises(ValidationError):
        PilastroRettangolareInput(**{**base, "rm": 1.5})  # out of [-1, 1]


@pytest.mark.unit
def test_circular_input_rejects_out_of_range_and_invalid_enum():
    base = {
        "d_mm": 400.0, "h_mm": 5000.0, "acciaio": "B450C", "cls": "C25/30",
        "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 25,
        "diametro_ferri_mm": 16.0, "diametro_staffe_mm": 10.0, "passo_staffe_mm": 150.0, "mrd_kNm": 160.0,
    }
    with pytest.raises(ValidationError):
        PilastroCircolareInput(**{**base, "mrd_kNm": 0.0})  # must be > 0
    with pytest.raises(ValidationError):
        PilastroCircolareInput(**{**base, "n_ferri": 3})  # below ge=4


@pytest.mark.unit
def test_long_bar_spacing_uses_seismic_250mm_under_code_standard():
    """Review finding (MEDIUM): the "Interasse massimo delle barre longitudinali" check is labelled NTC2018
    §7.4.6.2.2 (CD"B" seismic detailing: bar spacing <=250mm over the whole column), but used the
    non-seismic §4.1.6.1.2 300mm limit. legacy_compat=True keeps the sheet's own 300mm value."""
    base = {
        "l1_mm": 400.0, "l2_mm": 400.0, "h_mm": 3500.0, "acciaio": "B450C", "cls": "C25/30",
        "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0,
        "diametro_ferri_mm": 16.0, "diametro_staffe_mm": 10.0, "passo_staffe_mm": 150.0,
        "mrd_kNm": 160.0, "n_ferri_l1": 3, "n_ferri": 4,
    }
    # perimetro netto rettangolare = 2*((400-100)+(400-100)) = 1200mm; /4 ferri = 300mm esatti,
    # oltre il limite sismico (250mm) ma entro quello non-sismico del foglio (300mm).
    fixed_report = run_pilastro_rettangolare(PilastroRettangolareInput(**base, legacy_compat=False))
    legacy_report = run_pilastro_rettangolare(PilastroRettangolareInput(**base, legacy_compat=True))

    legacy_checks = {c.name: c.passed for c in legacy_report.checks}
    fixed_checks = {c.name: c.passed for c in fixed_report.checks}
    assert fixed_report.data.dettagli.interasse_long_calcolato_mm == pytest.approx(300.0)
    assert fixed_checks["Interasse massimo delle barre longitudinali"] is False  # 300 > 250mm (seismic limit)
    assert legacy_checks["Interasse massimo delle barre longitudinali"] is True  # sheet's own (non-seismic) 300mm limit, unaffected
    assert fixed_report.data.dettagli.interasse_long_max_mm == pytest.approx(250.0)
    assert legacy_report.data.dettagli.interasse_long_max_mm == pytest.approx(300.0)


@pytest.mark.unit
def test_ec2_cot_theta_uses_the_same_nu1_as_vrdmax_under_code_standard():
    """Review finding (MEDIUM): cot_theta hardcoded the strut-efficiency factor at the NTC value
    (0.5) even for the EC2 code-standard branch, where VRd,max uses ν1=0.6*(1-fck/250)
    (`limiti_ec2.nu1`, echoed in RegoleResult.nu1) — so the reported cotθ used to be inconsistent
    with the ν1 used everywhere else. legacy_compat=True reproduces the EC2 sheet's own CX42
    formula, which hardcodes 0.5 regardless of norma (confirmed in build/cellmaps), so it must be
    unaffected."""
    ntc_codice = run_pilastro_rettangolare(PilastroRettangolareInput(l1_mm=400.0, l2_mm=400.0, h_mm=3500.0, acciaio="B450C", cls="C25/30", ned_kN=1200.0, ved_kN=150.0, med_kNm=80.0, c_mm=50.0, n_ferri=8, diametro_ferri_mm=16.0, diametro_staffe_mm=10.0, passo_staffe_mm=100.0, mrd_kNm=160.0, n_ferri_l1=3, norma="NTC2018", legacy_compat=False))
    ec2_codice = run_pilastro_rettangolare(PilastroRettangolareInput(l1_mm=400.0, l2_mm=400.0, h_mm=3500.0, acciaio="B450C", cls="C25/30", ned_kN=1200.0, ved_kN=150.0, med_kNm=80.0, c_mm=50.0, n_ferri=8, diametro_ferri_mm=16.0, diametro_staffe_mm=10.0, passo_staffe_mm=100.0, mrd_kNm=160.0, n_ferri_l1=3, norma="EC2", legacy_compat=False))
    ec2_legacy = run_pilastro_rettangolare(PilastroRettangolareInput(l1_mm=400.0, l2_mm=400.0, h_mm=3500.0, acciaio="B450C", cls="C25/30", ned_kN=1200.0, ved_kN=150.0, med_kNm=80.0, c_mm=50.0, n_ferri=8, diametro_ferri_mm=16.0, diametro_staffe_mm=10.0, passo_staffe_mm=150.0, mrd_kNm=160.0, n_ferri_l1=3, norma="EC2", legacy_compat=True))
    assert ec2_codice.data.regole.nu1 != pytest.approx(0.5, rel=1e-6)  # EC2's own ν1 formula, not the NTC fixed value
    assert ec2_codice.data.taglio.cot_theta != pytest.approx(ntc_codice.data.taglio.cot_theta, rel=1e-6)
    # cross-check: recompute cotθ by hand with the EC2 nu1 and compare
    from strutture.members.ca_pilastri.taglio_theta import cot_theta as _cot_theta
    fcd_MPa = ec2_codice.data.materiali.fcd_MPa
    fyd_MPa = ec2_codice.data.materiali.fyd_MPa
    ac_coef = ec2_codice.data.taglio.ac
    expected = _cot_theta(10.0, fyd_MPa, 400.0, 100.0, ac_coef, fcd_MPa, nu1=ec2_codice.data.regole.nu1)
    assert ec2_codice.data.taglio.cot_theta == pytest.approx(expected, rel=1e-9)
    # legacy_compat=True must stay identical to the sheet's own hardcoded-0.5 formula, raw
    # cotθ=2.65809 (build/cellmaps/ca-pilastri-ec2 CX43) clamped to 2.5 by Z13/EC2 §6.2.3(2)
    assert ec2_legacy.data.taglio.cot_theta == pytest.approx(2.5, rel=1e-6)


@pytest.mark.unit
def test_ec2_code_standard_uses_italian_na_as_min_area_ratio():
    """Review finding (HIGH): the tool declares EC2 WITH the Italian National Annex (α_cc=0.85);
    the NA raises the column As,min area coefficient from the EN 1992-1-1 §9.5.2(2) recommended
    0.002 to 0.003 (aligned with NTC2018 §4.1.6.1.2). legacy_compat=True keeps the sheet's own
    0.002 (its own oracle/golden values)."""
    from strutture.members.ca_pilastri.regole import resolve

    codice = resolve("EC2", False)
    legacy = resolve("EC2", True)
    assert codice.as_min_area_ratio == pytest.approx(0.003)
    assert legacy.as_min_area_ratio == pytest.approx(0.002)

    ac_mm2, ned_kN, fyd_MPa = 160000.0, 1200.0, 391.304
    as_min_codice, _ = armatura_minima(
        ac_mm2, ned_kN, fyd_MPa, legacy_compat=False,
        area_ratio=codice.as_min_area_ratio, combinatore=codice.as_min_combinatore,
    )
    assert as_min_codice == pytest.approx(max(0.003 * ac_mm2, 0.10 * ned_kN * 1000.0 / fyd_MPa), rel=1e-5)
    assert as_min_codice == pytest.approx(480.0, rel=1e-5)


@pytest.mark.unit
def test_confinamento_rectangular_uses_larger_side_for_hcr_and_smaller_for_passo():
    """Review finding (HIGH): NTC2018 §7.4.6.1.2 defines lcr from the LARGER section dimension;
    §7.4.6.2.2's CD"B" spacing limit s<=b0/2 is governed by the SMALLER confined-core dimension.
    Passing the wrong side to either function gives a different, wrong number when l1 != l2."""
    h_mm, l1_mm, l2_mm, diametro_ferri_mm = 3500.0, 300.0, 600.0, 20.0

    hcr_from_smaller = altezza_critica_mm(h_mm, min(l1_mm, l2_mm))  # bug: base side instead of the governing (larger) one
    hcr_from_larger = altezza_critica_mm(h_mm, max(l1_mm, l2_mm))
    passo_from_larger = passo_massimo_confinato_mm(max(l1_mm, l2_mm), diametro_ferri_mm)  # bug: base side instead of the governing (smaller) one
    passo_from_smaller = passo_massimo_confinato_mm(min(l1_mm, l2_mm), diametro_ferri_mm)

    assert hcr_from_larger != pytest.approx(hcr_from_smaller)
    assert hcr_from_larger == pytest.approx(max(600.0, 3500.0 / 6.0, 450.0))
    assert passo_from_smaller != pytest.approx(passo_from_larger)
    assert passo_from_smaller == pytest.approx(min(150.0, 175.0, 160.0))


@pytest.mark.unit
def test_run_pilastro_rettangolare_confinement_geometry_uses_governing_sides():
    """End-to-end: the composed tool must pass max(l1,l2) to hcr and min(l1,l2) to the confined
    spacing limit, not l1_mm unconditionally (review finding, HIGH)."""
    base = {
        "l1_mm": 300.0, "l2_mm": 600.0, "h_mm": 3500.0, "acciaio": "B450C", "cls": "C25/30",
        "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 8,
        "diametro_ferri_mm": 20.0, "diametro_staffe_mm": 10.0, "passo_staffe_mm": 100.0,
        "mrd_kNm": 160.0, "n_ferri_l1": 3,
    }
    report = run_pilastro_rettangolare(PilastroRettangolareInput(**base, legacy_compat=False))
    assert report.ok
    confinamento = report.data.confinamento
    assert confinamento.hcr_mm == pytest.approx(altezza_critica_mm(3500.0, 600.0))
    assert confinamento.passo_max_confinato_mm == pytest.approx(passo_massimo_confinato_mm(300.0, 20.0))
    # sanity: using l1 for both (the bug) would give different, wrong numbers
    assert confinamento.hcr_mm != pytest.approx(altezza_critica_mm(3500.0, 300.0))


@pytest.mark.unit
def test_passo_staffe_zona_critica_check_is_reported():
    """Review finding (HIGH): passo_max_confinato_mm was computed but never turned into a Check —
    a column whose stirrup pitch violates the CD"B" confinement rule was reported as fully
    compliant. NTC2018 §7.4.6.2.2: s <= min(b0/2, 175mm, 8*Ø_long)."""
    base = {
        "l1_mm": 400.0, "l2_mm": 400.0, "h_mm": 3500.0, "acciaio": "B450C", "cls": "C25/30",
        "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 8,
        "diametro_ferri_mm": 16.0, "diametro_staffe_mm": 10.0, "mrd_kNm": 160.0, "n_ferri_l1": 3,
    }
    # candidates: 400/2=200, 175, 8*16=128 -> passo_max_confinato = 128mm
    violating = run_pilastro_rettangolare(PilastroRettangolareInput(**base, passo_staffe_mm=150.0, legacy_compat=False))
    compliant = run_pilastro_rettangolare(PilastroRettangolareInput(**base, passo_staffe_mm=100.0, legacy_compat=False))

    violating_checks = {c.name: c.passed for c in violating.checks}
    compliant_checks = {c.name: c.passed for c in compliant.checks}
    assert "Passo delle staffe in zona critica" in violating_checks
    assert violating_checks["Passo delle staffe in zona critica"] is False
    assert compliant_checks["Passo delle staffe in zona critica"] is True
