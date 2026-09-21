"""Golden test: `docs/specs/ca-mensole.md` §8 cached case, `legacy_compat=True`."""
import pytest

from strutture.members.ca_mensole.models import MensolaTozzaInput
from strutture.members.ca_mensole.tool import run


@pytest.mark.golden
def test_golden_mensola_tozza() -> None:
    inputs = MensolaTozzaInput(
        a_mm=177, h_mm=450, b_mm=800, c_mm=50, ped_kN=136, hed_kN=0,
        acciaio="B450C", calcestruzzo="C32/40",
        n_hor=8, phi_hor_mm=12, n_incl=0, phi_incl_mm=0, angolo_incl_deg=0,
        n_staffe=3, phi_staffe_mm=12, staffe_verticali="NO",
        legacy_compat=True,
    )
    report = run(inputs)
    assert report.ok
    data = report.data

    assert data.materiali.gamma_s == pytest.approx(1.15, rel=1e-6)
    assert data.materiali.gamma_c == pytest.approx(1.5, rel=1e-6)
    assert data.materiali.fyd_MPa == pytest.approx(391.304, rel=1e-5)
    assert data.materiali.fcd_MPa == pytest.approx(18.8133, rel=1e-5)

    assert data.geometria.d_mm == pytest.approx(400, rel=1e-6)
    assert data.geometria.l_mm == pytest.approx(257, rel=1e-6)

    assert data.armature.as_hor_mm2 == pytest.approx(904.779, rel=1e-5)
    assert data.armature.as_incl_mm2 == pytest.approx(0, abs=1e-9)
    assert data.armature.as_lnk_min_mm2 == pytest.approx(226.195, rel=1e-5)

    assert data.capacita.c_coeff == pytest.approx(1, rel=1e-9)
    assert data.capacita.prs_kN == pytest.approx(495.937, rel=1e-5)
    assert data.capacita.prc_kN == pytest.approx(1595.16, rel=1e-5)
    assert data.capacita.dpr_kN == pytest.approx(0, abs=1e-9)
    assert data.capacita.pr_kN == pytest.approx(495.937, rel=1e-5)

    checks_by_name = {check.name: check for check in report.checks}
    assert checks_by_name["Gerarchia delle resistenze (rottura duttile lato acciaio)"].passed
    assert checks_by_name["Verifica PR > PEd"].passed
    assert checks_by_name["Area staffe orizzontali >= As,lnk minima"].passed
