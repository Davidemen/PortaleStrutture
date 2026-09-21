"""Fixed-behaviour tests (legacy_compat=False): divergences from docs/divergences/ca-fessurazione.md."""
import pytest
from pydantic import ValidationError

from strutture.members.ca_fessurazione.models import (
    AperturaFessureInput,
    AperturaFessureSempInput,
    LimitazioneTensioniInput,
)
from strutture.members.ca_fessurazione.tool import run_apertura_fessure, run_apertura_fessure_semplificata
from strutture.shared.report import CalcError

pytestmark = pytest.mark.unit

_APERTURA_FESSURE_BASE = {
    "classe_calcestruzzo": "C28/35",
    "tipo_barre": "barre aderenza migliorata",
    "tipo_sollecitazione": "caso di flessione",
    "durata_carico": "lunga durata",
    "classe_fessurazione": "w3 (0.40 mm)",
    "interferro_mm": 200,
    "sigma_s_MPa": 286,
    "h_mm": 250,
    "x_mm": 75.84,
    "b_mm": 1000,
    "n1": 5,
    "phi1_mm": 20,
    "n2": 0,
    "phi2_mm": 0,
    "copriferro_mm": 35,
}

_SEMP_BASE = {
    "diametro_mm_1": 16, "sigma_fre_MPa_1": 100, "sigma_qpe_MPa_1": 100,
    "diametro_mm_2": 16, "sigma_fre_MPa_2": 100, "sigma_qpe_MPa_2": 100,
    "diametro_mm_3": 16, "sigma_fre_MPa_3": 100, "sigma_qpe_MPa_3": 100,
}


def test_dropped_load_case_enum_rejected():
    """Divergence 1: 'caso di trazione eccentrica' (dead #DIV/0! branch, W7) is not ported."""
    with pytest.raises(ValidationError):
        AperturaFessureInput(**{**_APERTURA_FESSURE_BASE, "tipo_sollecitazione": "caso di trazione eccentrica (o per singole parti di sezione)"})


def test_apertura_fessure_ecm_fctm_from_shared_materials_by_class():
    """Divergence 2: E18/E19 (dead '[1]MATERIALE CLS' link) sourced from shared.materials.concrete."""
    legacy = run_apertura_fessure(AperturaFessureInput(**_APERTURA_FESSURE_BASE, legacy_compat=True))
    fixed = run_apertura_fessure(AperturaFessureInput(**_APERTURA_FESSURE_BASE, legacy_compat=False))
    assert legacy.data.materiale.ecm_MPa == pytest.approx(32588.1, rel=1e-5)
    assert legacy.data.materiale.fctm_MPa == pytest.approx(2.83499, rel=1e-5)
    # legacy_compat toggles the underlying concrete_properties() fck source, so the two modes
    # give different Ecm/fctm for the same class (see docs/divergences/materials.md).
    assert fixed.data.materiale.ecm_MPa != pytest.approx(legacy.data.materiale.ecm_MPa, rel=1e-6)
    assert fixed.data.materiale.fctm_MPa != pytest.approx(legacy.data.materiale.fctm_MPa, rel=1e-6)


def test_apertura_fessure_semp_off_table_diameter_legacy_raises():
    """Divergence 3, legacy side: exact-match VLOOKUP-equivalent raises for an untabulated diameter."""
    with pytest.raises(CalcError, match="Tab. C4.1.II"):
        run_apertura_fessure_semplificata(AperturaFessureSempInput(**{**_SEMP_BASE, "diametro_mm_1": 15}, legacy_compat=True))


def test_apertura_fessure_semp_off_table_diameter_fixed_interpolates():
    """Divergence 3, fixed side: legacy_compat=False interpolates instead of raising."""
    report = run_apertura_fessure_semplificata(
        AperturaFessureSempInput(**{**_SEMP_BASE, "diametro_mm_1": 15}, legacy_compat=False)
    )
    assert report.ok
    # w3 table has (14, 300) and (16, 280); 15mm interpolates to 290.
    assert report.data.sezioni[0].sigma_lim_fre_MPa == pytest.approx(290.0, rel=1e-9)
    # w2 table has (14, 260) and (16, 240); 15mm interpolates to 250.
    assert report.data.sezioni[0].sigma_lim_qpe_MPa == pytest.approx(250.0, rel=1e-9)


def test_apertura_fessure_c4_1_10_branch_uses_1_3_over_1_7_when_fixed():
    """Divergence: with interferro >= slim (C4.1.10 branch) legacy_compat=True keeps the sheet's
    Delta_sm = 0.75*(h-x); legacy_compat=False uses 1.3/1.7*(h-x) (EN1992-1-1 eq. 7.14 / Circ.
    2019 §C4.1.10, ~2% larger, non-conservative sheet value corrected)."""
    base = {**_APERTURA_FESSURE_BASE, "interferro_mm": 300}  # > slim=225mm -> ramo C4.1.10
    legacy = run_apertura_fessure(AperturaFessureInput(**base, legacy_compat=True))
    fixed = run_apertura_fessure(AperturaFessureInput(**base, legacy_compat=False))
    assert legacy.data.fessurazione.ramo == "C4.1.10"
    assert fixed.data.fessurazione.ramo == "C4.1.10"
    assert legacy.data.fessurazione.delta_sm_mm == pytest.approx(0.75 * (250 - 75.84), rel=1e-9)
    assert fixed.data.fessurazione.delta_sm_mm == pytest.approx((1.3 / 1.7) * (250 - 75.84), rel=1e-9)
    assert fixed.data.fessurazione.wk_mm > legacy.data.fessurazione.wk_mm


@pytest.mark.parametrize("overrides", [{"rck_MPa": 0}, {"rck_MPa": -1}, {"fyk_MPa": 0}])
def test_limitazione_tensioni_invalid_inputs_rejected(overrides):
    base = {
        "rck_MPa": 45, "fyk_MPa": 450,
        "sigma_c_rar_1_MPa": 4.5, "sigma_c_qpe_1_MPa": 4.5, "sigma_s_rar_1_MPa": 255.8,
        "sigma_c_rar_2_MPa": 10, "sigma_c_qpe_2_MPa": 5.3, "sigma_s_rar_2_MPa": 274,
        "sigma_c_rar_3_MPa": 6, "sigma_c_qpe_3_MPa": 6, "sigma_s_rar_3_MPa": 237,
    }
    with pytest.raises(ValidationError):
        LimitazioneTensioniInput(**{**base, **overrides})


@pytest.mark.parametrize("overrides", [{"diametro_mm_1": 0}, {"diametro_mm_1": -5}])
def test_apertura_fessure_semp_invalid_diameter_rejected(overrides):
    with pytest.raises(ValidationError):
        AperturaFessureSempInput(**{**_SEMP_BASE, **overrides})


def test_apertura_fessure_semp_default_exposure_matches_sheet_hardcoded_w3_w2():
    """Divergence: default 'ordinarie'/'poco sensibile' is the Tab. 4.1.IV row the sheet
    hardcodes (w3 FRE / w2 QPE), so legacy_compat=False reproduces the sheet's classes here."""
    report = run_apertura_fessure_semplificata(AperturaFessureSempInput(**_SEMP_BASE, legacy_compat=False))
    assert report.ok
    assert report.data.sezioni[0].classe_fre == "w3"
    assert report.data.sezioni[0].classe_qpe == "w2"


def test_apertura_fessure_semp_aggressive_exposure_lowers_the_limit_when_fixed():
    """Divergence 4: hardcoded w3/w2 (NTC2018 Tab. 4.1.IV 'ordinarie + poco sensibile') is only
    correct for that exposure/sensitivity; 'molto aggressive' + 'sensibile' requires w1/decompressione,
    lowering sigma_s,lim for phi=16mm well below the hardcoded 280/240 MPa curve."""
    aggressive = {
        **_SEMP_BASE,
        "condizioni_ambientali": "molto aggressive",
        "sensibilita_armatura": "poco sensibile",
        "legacy_compat": False,
    }
    legacy = run_apertura_fessure_semplificata(AperturaFessureSempInput(**_SEMP_BASE, legacy_compat=True))
    fixed = run_apertura_fessure_semplificata(AperturaFessureSempInput(**aggressive))
    assert legacy.data.sezioni[0].classe_fre == "w3"
    assert fixed.ok
    assert fixed.data.sezioni[0].classe_fre == "w1"
    assert fixed.data.sezioni[0].sigma_lim_fre_MPa < legacy.data.sezioni[0].sigma_lim_fre_MPa


def test_apertura_fessure_semp_decompression_case_raises_calc_error():
    """Tab. 4.1.IV leaves 'aggressive + quasi permanente + sensibile' blank: NTC2018 requires a
    decompression check instead of a crack-width limit, which this tool does not compute."""
    decompressione = {
        **_SEMP_BASE,
        "condizioni_ambientali": "aggressive",
        "sensibilita_armatura": "sensibile",
        "legacy_compat": False,
    }
    with pytest.raises(CalcError, match="decompressione"):
        run_apertura_fessure_semplificata(AperturaFessureSempInput(**decompressione))


def test_apertura_fessure_semp_legacy_ignores_exposure_inputs():
    """legacy_compat=True must reproduce the sheet's hardcoded w3/w2 regardless of the new
    exposure/sensitivity inputs — engineering fix only touches the code-standard branch."""
    aggressive_legacy = {
        **_SEMP_BASE,
        "condizioni_ambientali": "molto aggressive",
        "sensibilita_armatura": "sensibile",
        "legacy_compat": True,
    }
    report = run_apertura_fessure_semplificata(AperturaFessureSempInput(**aggressive_legacy))
    assert report.ok
    assert report.data.sezioni[0].classe_fre == "w3"
    assert report.data.sezioni[0].classe_qpe == "w2"
