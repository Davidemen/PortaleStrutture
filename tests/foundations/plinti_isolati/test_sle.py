import pytest

from strutture.foundations.plinti_isolati.flessione import flessione
from strutture.foundations.plinti_isolati.inviluppo import inviluppo
from strutture.foundations.plinti_isolati.riga_verifica import riga_verifica
from strutture.foundations.plinti_isolati.sle import sle, sle_checks


def _golden_flessione_e_inviluppo(golden_rows):
    righe = tuple(
        riga_verifica(row, 4.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0, 20.0, 30.0,
                      metodo_pressioni="sovrapposizione", legacy_compat=True)
        for row in golden_rows
    )
    inviluppo_righe = inviluppo(righe)
    flessione_result = flessione(inviluppo_righe, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0, 8.0, 12.2, 20.0, 20.0,
                                  434.783, 500.0, 3.35208, legacy_compat=True)
    return inviluppo_righe, flessione_result


@pytest.mark.golden
def test_sle_golden(golden_rows) -> None:
    """docs/specs/fond-plinti-isolati.md Tool-2 golden case: sigma_c,QP=3.35865, sigma_s,QP=138.361,
    sigma_c,CHA=3.59996, sigma_s,CHA=148.301, sigma_s,FREQ=139.873 N/mm2."""
    inviluppo_righe, flessione_result = _golden_flessione_e_inviluppo(golden_rows)
    result = sle(inviluppo_righe, flessione_result, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0,
                  copriferro_cm=8.0, legacy_compat=True)
    assert result.sigma_c_qp_MPa == pytest.approx(3.35865, rel=1e-3)
    assert result.sigma_s_qp_MPa == pytest.approx(138.361, rel=1e-3)
    assert result.sigma_c_rara_MPa == pytest.approx(3.59996, rel=1e-3)
    assert result.sigma_s_rara_MPa == pytest.approx(148.301, rel=1e-3)
    assert result.sigma_s_freq_MPa == pytest.approx(139.873, rel=1e-3)


@pytest.mark.golden
def test_sle_checks_golden(golden_rows) -> None:
    """docs/specs/fond-plinti-isolati.md golden case: every SLS stress check passes."""
    inviluppo_righe, flessione_result = _golden_flessione_e_inviluppo(golden_rows)
    result = sle(inviluppo_righe, flessione_result, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0,
                  copriferro_cm=8.0, legacy_compat=True)
    checks = sle_checks(result, fck_MPa=37.35, fyk_MPa=500.0)
    assert len(checks) == 5
    assert all(check.passed for check in checks)
    limiti = {check.name: check.limit for check in checks}
    assert limiti["Tensione calcestruzzo (quasi permanente)"] == pytest.approx(16.8075, rel=1e-4)
    assert limiti["Tensione acciaio (quasi permanente)"] == pytest.approx(220.0)
    assert limiti["Tensione calcestruzzo (caratteristica)"] == pytest.approx(22.41, rel=1e-4)
    assert limiti["Tensione acciaio (caratteristica)"] == pytest.approx(400.0)
    assert limiti["Tensione acciaio (frequente)"] == pytest.approx(240.0)


@pytest.mark.unit
def test_sle_checks_falliti() -> None:
    from strutture.foundations.plinti_isolati.models_sle import Sle

    result = Sle(sigma_c_qp_MPa=100.0, sigma_s_qp_MPa=1000.0, sigma_c_rara_MPa=100.0,
                 sigma_s_rara_MPa=1000.0, sigma_s_freq_MPa=1000.0)
    checks = sle_checks(result, fck_MPa=25.0, fyk_MPa=450.0)
    assert not any(check.passed for check in checks)


@pytest.mark.unit
def test_sle_effective_depth_fix(golden_rows) -> None:
    """Fix (CRITICAL, review finding sezione_parzializzata.py): `legacy_compat=False` uses the
    effective depth d=H-copriferro-margine (same margin as `flessione._as_required_cm2`), not the
    gross plinth height H, as the SLS lever arm -- this increases the reported stresses relative
    to the sheet's own (less precise) H-based idealisation."""
    inviluppo_righe, flessione_result = _golden_flessione_e_inviluppo(golden_rows)
    legacy = sle(inviluppo_righe, flessione_result, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0,
                 copriferro_cm=8.0, legacy_compat=True)
    fisso = sle(inviluppo_righe, flessione_result, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0,
                copriferro_cm=8.0, legacy_compat=False)
    assert fisso.sigma_c_qp_MPa > legacy.sigma_c_qp_MPa
    assert fisso.sigma_s_qp_MPa > legacy.sigma_s_qp_MPa


@pytest.mark.unit
def test_sle_famiglia_assente_omette_check() -> None:
    """Fix (HIGH, review finding): no rows of a given famiglia in the envelope -> `None` sigma
    fields (not the misleading 0.0-value PASS the sheet's own IFERROR-less formula produced)."""
    from strutture.foundations.plinti_isolati.models_flessione import Flessione

    flessione_vuota = Flessione(
        mx_slu_kNm=0.0, my_slu_kNm=0.0, as_x_cm2=0.0, as_y_cm2=0.0, as_x_min_cm2=0.0, as_y_min_cm2=0.0,
        n_x=1, n_y=1, phi_x_mm=12.0, phi_y_mm=12.0, phi_min_mm=8.0,
        as_prov_x_mm2=100.0, as_prov_y_mm2=100.0,
        callout_sup_x="1ø12", callout_inf_x="1ø12", callout_sup_y="1ø12", callout_inf_y="1ø12",
    )
    result = sle((), flessione_vuota, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0, copriferro_cm=8.0, legacy_compat=False)
    assert result.sigma_c_qp_MPa is None
    assert result.sigma_s_qp_MPa is None
    assert result.sigma_c_rara_MPa is None
    assert result.sigma_s_rara_MPa is None
    assert result.sigma_s_freq_MPa is None
    assert sle_checks(result, fck_MPa=35.0, fyk_MPa=450.0) == ()


@pytest.mark.unit
def test_sle_eccentricita_asse_corretto_no_legacy(golden_rows) -> None:
    """Same eX/eY fix as `flessione.py`, applied to the SLS moments."""
    inviluppo_righe, flessione_result = _golden_flessione_e_inviluppo(golden_rows)
    base = sle(inviluppo_righe, flessione_result, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0,
               copriferro_cm=8.0, legacy_compat=False)
    con_ex = sle(inviluppo_righe, flessione_result, 4.0, 4.0, 0.8, 0.0, 0.0, 0.1, 0.0,
                 copriferro_cm=8.0, legacy_compat=False)
    assert con_ex.sigma_s_qp_MPa != pytest.approx(base.sigma_s_qp_MPa)
