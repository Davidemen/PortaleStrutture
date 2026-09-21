"""Fixed-behaviour tests for the `norma` dispatch (architecture-batch2.md §3): the rule-set table
in `regole.py`, and the norm-specific behaviour it drives through the (norm-agnostic) step
modules — see docs/specs/ca-pilastri-ntc2018.md / docs/specs/ca-pilastri-ec2.md."""
import pytest

from strutture.members.ca_pilastri.models import PilastroCircolareInput, PilastroRettangolareInput
from strutture.members.ca_pilastri.regole import resolve
from strutture.members.ca_pilastri.tool_rettangolare import run_pilastro_rettangolare
from strutture.shared.report import CalcError

BASE_RETT = {
    "l1_mm": 400.0, "l2_mm": 400.0, "h_mm": 3500.0, "acciaio": "B450C", "cls": "C25/30",
    "ned_kN": 1200.0, "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 8,
    "diametro_ferri_mm": 16.0, "diametro_staffe_mm": 10.0, "passo_staffe_mm": 150.0,
    "mrd_kNm": 160.0, "n_ferri_l1": 3,
}


@pytest.mark.unit
def test_default_norma_is_ntc2018():
    inputs = PilastroRettangolareInput(**BASE_RETT)
    assert inputs.norma == "NTC2018"


@pytest.mark.unit
def test_ntc2008_code_standard_is_rejected():
    """architecture-batch2.md §3: NTC2008 has no maintained code-standard branch — a superseded
    norm is only available as a spreadsheet reproduction."""
    inputs = PilastroRettangolareInput(**BASE_RETT, norma="NTC2008", legacy_compat=False)
    with pytest.raises(CalcError, match="NTC 2008"):
        run_pilastro_rettangolare(inputs)


@pytest.mark.unit
def test_ntc2008_legacy_is_accepted():
    inputs = PilastroRettangolareInput(**BASE_RETT, norma="NTC2008", legacy_compat=True)
    assert run_pilastro_rettangolare(inputs).ok


@pytest.mark.unit
def test_resolve_covers_every_norma_legacy_pair_except_ntc2008_codice():
    for norma in ("NTC2018", "EC2"):
        for legacy_compat in (True, False):
            resolve(norma, legacy_compat)  # must not raise
    resolve("NTC2008", True)  # must not raise
    with pytest.raises(CalcError):
        resolve("NTC2008", False)


@pytest.mark.unit
def test_ntc2018_legacy_drops_the_rs_minimum_comparison():
    """docs/specs/ca-pilastri-ntc2018.md §4: J24 = IF(H24<0.04,"OK","NO") — the NTC2008 sheet's
    rs>rs_min comparison is gone; only the 4% ceiling remains under legacy_compat=True."""
    report = run_pilastro_rettangolare(PilastroRettangolareInput(**BASE_RETT, norma="NTC2018", legacy_compat=True))
    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["percentuale_armatura"] is True  # rs=0.0100531 < 0.04, minimum not checked


@pytest.mark.unit
def test_ec2_uses_its_own_min_bar_diameter_and_area_ratio():
    """docs/specs/ca-pilastri-ec2.md §4: min bar Ø=8mm (not NTC's 12mm), min-As coefficient 0.002
    (not NTC's 0.003) combined with MAX (not MIN), no 4% ceiling clamp on As,min itself."""
    inputs = PilastroRettangolareInput(**{**BASE_RETT, "diametro_ferri_mm": 10.0}, norma="EC2", legacy_compat=True)
    report = run_pilastro_rettangolare(inputs)
    assert report.ok
    assert report.data.dettagli.diametro_long_min_mm == pytest.approx(8.0)
    assert report.data.armatura_minima.as_min_mm2 == pytest.approx(max(0.002 * 160000.0, 0.10 * 1200_000.0 / 391.304), rel=1e-5)


@pytest.mark.unit
def test_ec2_shear_uses_nu1_instead_of_fixed_half():
    """docs/specs/ca-pilastri-ec2.md §4.1/§4.2: VRdc gains a ν1=0.6*(1-fck/250) factor, replacing
    the NTC sheets' hardcoded 0.5; VRds (steel side, no ν1 term) is unaffected."""
    ntc = run_pilastro_rettangolare(PilastroRettangolareInput(**BASE_RETT, norma="NTC2018", legacy_compat=True))
    ec2 = run_pilastro_rettangolare(PilastroRettangolareInput(**BASE_RETT, norma="EC2", legacy_compat=True))
    assert ntc.data.regole.nu1 == pytest.approx(0.5)
    assert ec2.data.regole.nu1 == pytest.approx(0.54024, rel=1e-4)
    assert ec2.data.taglio.vrds_kN == pytest.approx(ntc.data.taglio.vrds_kN, rel=1e-6)
    assert ec2.data.taglio.vrdc_kN != pytest.approx(ntc.data.taglio.vrdc_kN, rel=1e-3)


@pytest.mark.unit
def test_ec2_stirrup_spacing_adds_column_dimension_candidate():
    """docs/specs/ca-pilastri-ec2.md §4 item 5: MIN(20*Ø, 400mm, min(L1,L2)) vs NTC's MIN(12*Ø, 250mm)."""
    overrides = {**BASE_RETT, "l1_mm": 300.0, "l2_mm": 600.0, "diametro_ferri_mm": 20.0, "n_ferri": 10}
    inputs = PilastroRettangolareInput(**overrides, norma="EC2", legacy_compat=True)
    report = run_pilastro_rettangolare(inputs)
    assert report.ok
    # candidates: 20*20=400, 400, min(300,600)=300 -> 300 governs
    assert report.data.dettagli.interasse_staffe_max_mm == pytest.approx(300.0)


@pytest.mark.unit
def test_ec2_phi_ef_changes_coefficient_a_under_code_standard():
    """docs/architecture-batch2.md §7 "pilastri EC2 A=C=0.7 hard-coded | F: ... A from φ_ef when
    given": legacy_compat=True always uses the sheet's hardcoded A=0.7, ignoring φef."""
    without_phi_ef = run_pilastro_rettangolare(PilastroRettangolareInput(**BASE_RETT, norma="EC2", legacy_compat=False))
    with_phi_ef = run_pilastro_rettangolare(PilastroRettangolareInput(**BASE_RETT, norma="EC2", legacy_compat=False, phi_ef=1.0))
    legacy_ignores_phi_ef = run_pilastro_rettangolare(PilastroRettangolareInput(**BASE_RETT, norma="EC2", legacy_compat=True, phi_ef=1.0))

    assert without_phi_ef.data.regole.a_snellezza == pytest.approx(0.7)
    assert with_phi_ef.data.regole.a_snellezza == pytest.approx(1.0 / 1.2, rel=1e-6)
    assert with_phi_ef.data.snellezza.lambda_lim != pytest.approx(without_phi_ef.data.snellezza.lambda_lim, rel=1e-3)
    assert legacy_ignores_phi_ef.data.regole.a_snellezza == pytest.approx(0.7)


@pytest.mark.unit
def test_ec2_code_standard_uses_gross_radius_of_gyration_like_ntc2018():
    """The EC2 sheet's own "Raggio d'inerzia" formula is byte-identical to the NTC2018 sheet's
    (gross section, confirmed against build/cellmaps/ca-pilastri-ec2/) — so both legacy_compat
    modes agree with the NTC2018 branch, not the superseded NTC2008 net-section formula."""
    ntc2018 = run_pilastro_rettangolare(PilastroRettangolareInput(**BASE_RETT, norma="NTC2018", legacy_compat=False))
    ec2 = run_pilastro_rettangolare(PilastroRettangolareInput(**BASE_RETT, norma="EC2", legacy_compat=False))
    assert ec2.data.snellezza.i_mm == pytest.approx(ntc2018.data.snellezza.i_mm, rel=1e-9)


@pytest.mark.unit
def test_norma_field_rejects_unknown_value():
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        PilastroRettangolareInput(**BASE_RETT, norma="EN1992")


@pytest.mark.unit
def test_circular_ec2_stirrup_spacing_uses_diameter_as_the_single_dimension():
    from strutture.members.ca_pilastri.tool_circolare import run_pilastro_circolare

    base_circ = {
        "d_mm": 400.0, "h_mm": 5000.0, "acciaio": "B450C", "cls": "C25/30", "ned_kN": 1200.0,
        "ved_kN": 150.0, "med_kNm": 80.0, "c_mm": 50.0, "n_ferri": 25, "diametro_ferri_mm": 10.0,
        "diametro_staffe_mm": 10.0, "passo_staffe_mm": 150.0, "mrd_kNm": 160.0,
    }
    report = run_pilastro_circolare(PilastroCircolareInput(**base_circ, norma="EC2", legacy_compat=True))
    assert report.ok
    # candidates: 20*10=200, 400, D=400 -> 200 governs
    assert report.data.dettagli.interasse_staffe_max_mm == pytest.approx(200.0)
