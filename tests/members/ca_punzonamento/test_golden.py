import pytest

from strutture.members.ca_punzonamento.compose import run
from strutture.members.ca_punzonamento.models import PunzonamentoInput

GOLDEN_INPUTS = {
    "ved_kN": 225, "pterreno_MPa": 0, "lato_a_mm": 400, "lato_b_mm": 400, "h_mm": 500, "diametro_mm": 0,
    "fck_MPa": 35, "copriferro_mm": 50, "posizione": "interno", "px_mm": 200, "py_mm": 200, "phix_mm": 20,
    "phiy_mm": 20, "a1eff_mm": 400, "bu_mm": 380, "st_mm": 200, "phi_staffa_mm": 12, "n_staffe": 8,
    "legacy_compat": True,
}


@pytest.mark.golden
def test_golden_case():
    """Spec §8: Shotblast_225N, dx=440/dy=420/d=430mm, a governing = 2d = 860mm."""
    report = run(PunzonamentoInput(**GOLDEN_INPUTS))
    assert report.ok
    data = report.data

    assert data.geometria.dx_mm == pytest.approx(440, rel=1e-6)
    assert data.geometria.dy_mm == pytest.approx(420, rel=1e-6)
    assert data.geometria.d_mm == pytest.approx(430, rel=1e-6)
    assert data.geometria.u0_mm == pytest.approx(1600, rel=1e-6)

    assert data.faccia_pilastro.v_rd_max_MPa == pytest.approx(3.96667, rel=1e-5)
    assert data.faccia_pilastro.v_ed_0_MPa == pytest.approx(0.37609, rel=1e-4)

    pc = data.perimetro_critico
    assert pc.a_governante_su_d == pytest.approx(2.0, rel=1e-6)
    assert pc.a_governante_mm == pytest.approx(860, rel=1e-6)
    assert pc.ui_mm == pytest.approx(7003.54, rel=1e-5)
    assert pc.area_mm2 == pytest.approx(3.85952e6, rel=1e-5)
    assert pc.v_rd_i_MPa == pytest.approx(0.471968, rel=1e-5)
    assert pc.v_ed_i_MPa == pytest.approx(0.08592, rel=1e-4)
    assert pc.rapporto == pytest.approx(0.182046, rel=1e-5)
    assert pc.armatura_necessaria is False

    # spec sample rows of the scan table (a/d = 0.5, 1.25, 2.0)
    riga_050 = pc.righe[0]
    assert riga_050.a_su_d == pytest.approx(0.5)
    assert riga_050.ui_mm == pytest.approx(2950.88, rel=1e-5)
    assert riga_050.area_mm2 == pytest.approx(649220.12, rel=1e-5)
    assert riga_050.v_rd_i_MPa == pytest.approx(1.88787, rel=1e-5)
    assert riga_050.v_ed_i_MPa == pytest.approx(0.20392, rel=1e-4)
    assert riga_050.rapporto == pytest.approx(0.108016, rel=1e-5)

    riga_125 = pc.righe[75]
    assert riga_125.a_su_d == pytest.approx(1.25)
    assert riga_125.ui_mm == pytest.approx(4977.21, rel=1e-5)
    assert riga_125.rapporto == pytest.approx(0.160101, rel=1e-5)

    riga_200 = pc.righe[-1]
    assert riga_200.a_su_d == pytest.approx(2.0)
    assert riga_200.ui_mm == pytest.approx(7003.54, rel=1e-5)
    assert riga_200.rapporto == pytest.approx(0.182046, rel=1e-5)

    assert data.messaggio == "Progetto delle armature verticali non necessario."

    armatura = data.armatura
    assert armatura is not None  # legacy_compat=True: ungated block always present (spec bug #5)
    assert armatura.u0_out_mm == pytest.approx(1274.97, rel=1e-5)
    assert armatura.asw_min_mm2 == pytest.approx(58.318, rel=1e-4)
    assert armatura.v_rd_cs1_kN == pytest.approx(62.7098, rel=1e-5)
    assert armatura.v_rd_c_primo_kN == pytest.approx(1066.01, rel=1e-5)
    assert armatura.v_rd_s_kN == pytest.approx(501.679, rel=1e-5)
    assert armatura.v_rrd_kN == pytest.approx(1567.68, rel=1e-5)
    assert armatura.ved_su_vrd == pytest.approx(0.165052, rel=1e-5)


@pytest.mark.golden
def test_golden_case_checks():
    report = run(PunzonamentoInput(**GOLDEN_INPUTS))
    by_name = {c.name: c for c in report.checks}
    assert by_name["punzonamento_faccia_pilastro"].passed is True
    assert by_name["punzonamento_perimetro_critico"].passed is True
    assert by_name["resistenza_con_armatura"].passed is True
    # sheet F46: a1,eff=400mm is above a1,max=215mm — the sheet itself flags this ("<di a1max!")
    assert by_name["a1_eff_nel_range"].passed is False
