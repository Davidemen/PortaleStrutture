import pytest

from strutture.members.ca_fessurazione.models import (
    AperturaFessureInput,
    AperturaFessureSempInput,
    LimitazioneTensioniInput,
)
from strutture.members.ca_fessurazione.tool import (
    run_apertura_fessure,
    run_apertura_fessure_semplificata,
    run_limitazione_tensioni,
)


@pytest.mark.golden
def test_golden_limitazione_tensioni():
    """Spec §8: Rck=45, fyk=450, sezione 1 (h=30cm bordo)."""
    report = run_limitazione_tensioni(
        LimitazioneTensioniInput(
            rck_MPa=45,
            fyk_MPa=450,
            sigma_c_rar_1_MPa=4.5,
            sigma_c_qpe_1_MPa=4.5,
            sigma_s_rar_1_MPa=255.8,
            sigma_c_rar_2_MPa=10,
            sigma_c_qpe_2_MPa=5.3,
            sigma_s_rar_2_MPa=274,
            sigma_c_rar_3_MPa=6,
            sigma_c_qpe_3_MPa=6,
            sigma_s_rar_3_MPa=237,
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.fck_MPa == pytest.approx(37.35, rel=1e-6)
    sezione1 = data.sezioni[0]
    assert sezione1.sigma_c_max_rar_MPa == pytest.approx(22.41, rel=1e-6)
    assert sezione1.utilizzo_c_rar == pytest.approx(0.200803, rel=1e-5)
    assert sezione1.verificato_c_rar is True
    assert sezione1.sigma_c_max_qpe_MPa == pytest.approx(16.8075, rel=1e-6)
    assert sezione1.utilizzo_c_qpe == pytest.approx(0.267738, rel=1e-5)
    assert sezione1.verificato_c_qpe is True
    assert sezione1.sigma_s_max_rar_MPa == pytest.approx(360, rel=1e-6)
    assert sezione1.utilizzo_s_rar == pytest.approx(0.710556, rel=1e-5)
    assert sezione1.verificato_s_rar is True


@pytest.mark.golden
def test_golden_apertura_fessure():
    """Spec §8 full case."""
    report = run_apertura_fessure(
        AperturaFessureInput(
            classe_calcestruzzo="C28/35",
            tipo_barre="barre aderenza migliorata",
            tipo_sollecitazione="caso di flessione",
            durata_carico="lunga durata",
            classe_fessurazione="w3 (0.40 mm)",
            interferro_mm=200,
            sigma_s_MPa=286,
            es_MPa=210000,
            h_mm=250,
            x_mm=75.84,
            b_mm=1000,
            n1=5,
            phi1_mm=20,
            n2=0,
            phi2_mm=0,
            copriferro_mm=35,
            k3=3.4,
            k4=0.425,
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.materiale.ecm_MPa == pytest.approx(32588.1, rel=1e-5)
    assert data.materiale.fctm_MPa == pytest.approx(2.83499, rel=1e-5)
    assert data.materiale.alpha_e == pytest.approx(6.44407, rel=1e-5)
    assert data.geometria.d_mm == pytest.approx(205, rel=1e-6)
    assert data.geometria.hc_eff_mm == pytest.approx(58.0533, rel=1e-5)
    assert data.geometria.ac_eff_mm2 == pytest.approx(58053.3, rel=1e-5)
    assert data.geometria.as_mm2 == pytest.approx(1570.8, rel=1e-4)
    assert data.geometria.phi_eq_mm == pytest.approx(20, rel=1e-6)
    assert data.geometria.rho_eff == pytest.approx(0.0270578, rel=1e-5)
    assert data.coefficienti.k1 == pytest.approx(0.8, rel=1e-9)
    assert data.coefficienti.k2 == pytest.approx(0.5, rel=1e-9)
    assert data.coefficienti.kt == pytest.approx(0.4, rel=1e-9)
    assert data.fessurazione.slim_mm == pytest.approx(225, rel=1e-6)
    assert data.fessurazione.ramo == "C4.1.7"
    assert data.fessurazione.delta_sm_mm == pytest.approx(143.916, rel=1e-5)
    assert data.fessurazione.epsilon_sm == pytest.approx(0.00112753, rel=1e-5)
    assert data.fessurazione.wk_mm == pytest.approx(0.275859, rel=1e-5)
    assert data.fessurazione.wlim_mm == pytest.approx(0.4, rel=1e-9)
    assert data.fessurazione.utilizzo == pytest.approx(0.69, rel=1e-9)
    assert data.fessurazione.verificato is True


@pytest.mark.golden
def test_golden_apertura_fessure_semplificata():
    """Sheet's own cached example (cellmap `apertura-delle-fessure-semp.txt`), ø=16mm."""
    report = run_apertura_fessure_semplificata(
        AperturaFessureSempInput(
            diametro_mm_1=16,
            sigma_fre_MPa_1=231,
            sigma_qpe_MPa_1=218,
            diametro_mm_2=16,
            sigma_fre_MPa_2=206,
            sigma_qpe_MPa_2=233,
            diametro_mm_3=16,
            sigma_fre_MPa_3=180,
            sigma_qpe_MPa_3=171,
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    attesi = (
        (0.825, True, 0.908333, True),
        (0.735714, True, 0.970833, True),
        (0.642857, True, 0.7125, True),
    )
    for sezione, (util_fre, ok_fre, util_qpe, ok_qpe) in zip(data.sezioni, attesi, strict=True):
        assert sezione.sigma_lim_fre_MPa == pytest.approx(280, rel=1e-6)
        assert sezione.sigma_lim_qpe_MPa == pytest.approx(240, rel=1e-6)
        assert sezione.utilizzo_fre == pytest.approx(util_fre, rel=1e-5)
        assert sezione.verificato_fre is ok_fre
        assert sezione.utilizzo_qpe == pytest.approx(util_qpe, rel=1e-5)
        assert sezione.verificato_qpe is ok_qpe
