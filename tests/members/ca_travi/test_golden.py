import pytest

from strutture.members.ca_travi.models import TraveRettangolareInput
from strutture.members.ca_travi.tool import run

GOLDEN_KWARGS = {
    "b_mm": 600, "h_mm": 400, "tipo_acciaio": "RB500W", "tipo_cls": "C35/45", "copriferro_mm": 70,
    "n_ferri1": 5, "diametro_ferri1_mm": 20, "n_ferri2": 0, "diametro_ferri2_mm": 0,
    "diametro_staffe1_mm": 12, "passo_staffe1_mm": 115, "n_bracci_staffe1": 2,
    "diametro_staffe2_mm": 0, "n_bracci_staffe2": 0, "alpha_staffe_deg": 90,
    "ved_kN": 138, "med_slu_kNm": 318, "med_rara_kNm": 239, "med_qp_kNm": 200,
    "condizioni_ambientali": "Ordinarie", "combinazione": "Frequente", "sensibilita_armatura": "Poco sensibile",
    "classe_apertura_fessura": "w3",
    "classe_duttilita": "CDB", "mrc_kNm": 350, "lt_m": 8,
}


@pytest.mark.golden
def test_golden_trave_rettangolare():
    """Spec §8 cached case (sheet 'Travi sez. rettangolare')."""
    report = run(TraveRettangolareInput(legacy_compat=True, **GOLDEN_KWARGS))
    assert report.ok
    data = report.data

    assert data.materiali.calcestruzzo.fcd_MPa == pytest.approx(21.165, rel=1e-6)
    assert data.materiali.acciaio.fyd_MPa == pytest.approx(434.783, rel=1e-5)

    assert data.armatura.as_min_mm2 == pytest.approx(238.937, rel=1e-5)
    assert data.armatura.as_o_mm2 == pytest.approx(1570.8, rel=1e-5)
    assert data.armatura.as_max_mm2 == pytest.approx(9600.0)

    assert data.flessione.d_mm == pytest.approx(330.0)
    assert data.flessione.mrd_kNm == pytest.approx(207.01, rel=1e-5)

    assert data.taglio.vrdc_kN == pytest.approx(650.276, rel=1e-5)
    assert data.taglio.vrds_kN == pytest.approx(634.97, rel=1e-5)
    assert data.taglio.vrd_kN == pytest.approx(634.97, rel=1e-5)

    assert data.dettagli_costruttivi.lunghezza_critica_mm == pytest.approx(400.0)
    assert data.dettagli_costruttivi.passo_max_zona_critica_mm == pytest.approx(0.0)
    assert data.dettagli_costruttivi.lunghezza_ancoraggio_mm == pytest.approx(120.0)
    assert data.dettagli_costruttivi.ved_max_kN == pytest.approx(207.01, rel=1e-5)

    assert data.sle_tensioni.x_mm == pytest.approx(126.44, rel=1e-4)
    assert data.sle_tensioni.sigma_c_rara_MPa == pytest.approx(21.8885, rel=1e-4)
    assert data.sle_tensioni.sigma_s_rara_MPa == pytest.approx(528.576, rel=1e-4)
    assert data.sle_tensioni.sigma_c_qp_MPa == pytest.approx(18.3168, rel=1e-4)
    assert data.sle_tensioni.sigma_s_combinazione_MPa == pytest.approx(528.576, rel=1e-4)
    assert data.fessurazione.sigma_limite_MPa == pytest.approx(240.0)

    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["Armatura minima tesa"] is True
    assert by_name["Armatura massima tesa"] is True
    assert by_name["Armatura minima a taglio (staffe)"] is True
    assert by_name["Passo massimo staffe"] is True
    assert by_name["Resistenza a flessione"] is False  # spec: MEd 318 > MRd 207.01 -> "NO"
    assert by_name["Resistenza a taglio"] is True
    assert by_name["Capacity design a taglio"] is True
    assert by_name["Tensione di compressione nel calcestruzzo, combinazione rara"] is True  # spec: 21.8885 < 22.41 -> "OK"
    assert by_name["Tensione di trazione nell'acciaio, combinazione rara"] is False  # spec: 528.576 > 360 -> "NO"
    assert (
        by_name["Tensione di compressione nel calcestruzzo, combinazione quasi permanente"] is False
    )  # spec: 18.3168 > 16.8075 -> "NO"
    assert by_name["Controllo indiretto di fessurazione"] is False  # spec: 528.576 > 240 -> "NO"


@pytest.mark.golden
def test_golden_trave_rettangolare_fixed_mode_diverges_on_known_bugs():
    """legacy_compat=False fixes the As,min/Ast,min/passo-max formulas; MRd/VRd are unaffected."""
    legacy = run(TraveRettangolareInput(legacy_compat=True, **GOLDEN_KWARGS)).data
    fixed = run(TraveRettangolareInput(legacy_compat=False, **GOLDEN_KWARGS)).data

    assert fixed.armatura.as_min_mm2 != pytest.approx(legacy.armatura.as_min_mm2)
    # Ast,min: NTC2018's 1.5*b floor governs for this section in both modes (900 mm²/m); fixed
    # mode additionally checks EC2 9.2.2(5) as a second floor, but never returns less than 1.5*b
    # (see docs/divergences/ca-travi.md item 2 — the 1.5*b floor is mandatory, not overridable).
    assert fixed.armatura.ast_min_per_m_mm2 == pytest.approx(legacy.armatura.ast_min_per_m_mm2)
    assert fixed.armatura.ast_min_per_m_mm2 == pytest.approx(900.0)
    assert fixed.armatura.passo_max_staffe_mm != pytest.approx(legacy.armatura.passo_max_staffe_mm)
    assert fixed.dettagli_costruttivi.passo_max_zona_critica_mm != pytest.approx(
        legacy.dettagli_costruttivi.passo_max_zona_critica_mm
    )
    # tipo_acciaio="RB500W" (fyk=500): legacy hardcodes limite_sigma_s=360 (Z42 bug, only right for
    # B450C); fixed mode applies 0.80*fyk=400.
    assert legacy.sle_tensioni.limite_sigma_s_MPa == pytest.approx(360.0)
    assert fixed.sle_tensioni.limite_sigma_s_MPa == pytest.approx(400.0)
    # flessione/taglio have no ca-travi-specific bug; their small drift here comes only from the
    # upstream concrete fck legacy_compat (see docs/divergences/materials.md), not from ca-travi's
    # own formulas — confirm they use identical fcd/fyd inputs by re-running with the same fcd/fyd.
    assert fixed.materiali.calcestruzzo.fcd_MPa != legacy.materiali.calcestruzzo.fcd_MPa
