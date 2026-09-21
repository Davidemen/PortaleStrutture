"""Golden case: acciaio.md spec §8, legacy_compat=True (acciaio-colonne-ec3!Column check)."""
import pytest

from strutture.members.acciaio_colonna_ec3.models import ColonnaEc3Input
from strutture.members.acciaio_colonna_ec3.tool import ESEMPIO_AUREO, run


@pytest.mark.golden
def test_golden_column_check() -> None:
    inputs = ColonnaEc3Input(**ESEMPIO_AUREO)
    report = run(inputs)

    assert report.ok
    d = report.data

    assert d.materiali.fyd_MPa == pytest.approx(345.0, rel=1e-6)
    assert d.materiali.fud_MPa == pytest.approx(450.0, rel=1e-6)
    assert d.sezione.curva_instabilita_lt == "b"

    assert d.instabilita_flessionale.ncr_y_kN == pytest.approx(3531.51, rel=1e-4)
    assert d.instabilita_flessionale.ncr_z_kN == pytest.approx(20580.2, rel=1e-4)
    assert d.instabilita_flessionale.lambda_yy == pytest.approx(1.01415, rel=1e-5)
    assert d.instabilita_flessionale.lambda_zz == pytest.approx(0.420105, rel=1e-5)
    assert d.instabilita_flessionale.chi_yy == pytest.approx(0.588068, rel=1e-5)
    assert d.instabilita_flessionale.chi_zz == pytest.approx(0.886636, rel=1e-5)

    assert d.instabilita_torso_flessionale.mcr_Nmm == pytest.approx(1.27057e10, rel=1e-5)
    assert d.instabilita_torso_flessionale.lambda_lt == pytest.approx(0.226433, rel=1e-5)
    assert d.instabilita_torso_flessionale.verifica_non_necessaria is True

    assert d.flessione.mrd_y_kNm == pytest.approx(651.446, rel=1e-5)
    assert d.flessione.mrd_z_kNm == pytest.approx(108.242, rel=1e-5)
    assert d.taglio.vpl_rd_anima_kN == pytest.approx(910.2, rel=1e-4)
    assert d.taglio.vpl_rd_ali_kN == pytest.approx(1338.53, rel=1e-4)

    assert d.taglio_instabilita.vb_rd_kN == pytest.approx(757.091, rel=1e-5)

    assert d.interazione.kyy == pytest.approx(0.807385, rel=1e-5)
    assert d.interazione.kyz == pytest.approx(0.839168, rel=1e-5)
    assert d.interazione.kzy == pytest.approx(0.823658, rel=1e-5)
    assert d.interazione.kzz == pytest.approx(0.856082, rel=1e-5)
    assert d.interazione.utilizzo_yy == pytest.approx(0.230307, rel=1e-5)
    assert d.interazione.utilizzo_zz == pytest.approx(0.206155, rel=1e-5)

    assert d.interazione_semplificata.i56 == pytest.approx(0.0343815, rel=1e-5)

    assert all(check.passed for check in report.checks)
    assert report.warnings == ()
