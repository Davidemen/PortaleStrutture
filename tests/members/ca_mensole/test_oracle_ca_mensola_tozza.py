"""Oracle tests for `ca-mensola-tozza` against `tests/fixtures/ca_mensola_tozza_oracle.json`
(recalculated via LibreOffice — regenerate with `tests/fixtures/gen_ca_mensola_tozza.py`).
"""
import json
from pathlib import Path

import pytest

from strutture.members.ca_mensole.models import MensolaTozzaInput
from strutture.members.ca_mensole.tool import run
from strutture.shared.report import CalcError

FIXTURE = json.loads(Path(__file__).parents[2].joinpath("fixtures", "ca_mensola_tozza_oracle.json").read_text())

_SUCCESS_TEXT = "Verifica soddisfatta: Pr > Ped"
_GERARCHIA_FAIL_TEXT = "Gerarchia delle resistenze non verificata: Prs > Prc"
_ULS_FAIL_TEXT = "Verifica non soddisfatta: Pr < Ped"


def _to_input(cells: dict) -> MensolaTozzaInput:
    return MensolaTozzaInput(
        a_mm=cells["H5"], h_mm=cells["H6"], b_mm=cells["H7"], c_mm=cells["H8"],
        ped_kN=cells["H9"], hed_kN=cells["H10"],
        acciaio=cells["H14"], calcestruzzo=cells["H15"],
        n_hor=cells["H16"], phi_hor_mm=cells["H17"], n_incl=cells["H18"], phi_incl_mm=cells["H19"],
        angolo_incl_deg=cells["H22"], n_staffe=cells["H24"], phi_staffe_mm=cells["H25"],
        staffe_verticali=cells["H29"], legacy_compat=True,
    )


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle(case: dict) -> None:
    outputs = case["outputs"]
    if outputs["Z8"] == "#N/A":  # FeB22k selectable via H14 but absent from Tabelle!M45:P49 (spec §7)
        with pytest.raises(CalcError):
            run(_to_input(case["inputs"]))
        return

    report = run(_to_input(case["inputs"]))
    assert report.ok
    data = report.data

    assert data.materiali.gamma_s == pytest.approx(outputs["Z5"], rel=1e-6)
    assert data.materiali.gamma_c == pytest.approx(outputs["Z6"], rel=1e-6)
    assert data.materiali.fyd_MPa == pytest.approx(outputs["Z8"], rel=1e-6)
    assert data.materiali.fcd_MPa == pytest.approx(outputs["Z9"], rel=1e-6)

    assert data.geometria.d_mm == pytest.approx(outputs["H11"], rel=1e-6)
    assert data.geometria.l_mm == pytest.approx(outputs["H13"], rel=1e-6)

    assert data.armature.as_hor_mm2 == pytest.approx(outputs["H20"], rel=1e-6)
    assert data.armature.as_incl_mm2 == pytest.approx(outputs["H21"], rel=1e-6)
    assert data.armature.as_lnk_min_mm2 == pytest.approx(outputs["H23"], rel=1e-6)

    assert data.capacita.c_coeff == pytest.approx(float(outputs["H30"]), rel=1e-6)
    assert data.capacita.prs_kN == pytest.approx(outputs["H28"], rel=1e-6)
    assert data.capacita.prc_kN == pytest.approx(outputs["H31"], rel=1e-6)
    assert data.capacita.dpr_kN == pytest.approx(outputs["H32"], rel=1e-6)
    assert data.capacita.pr_kN == pytest.approx(outputs["H33"], rel=1e-6)

    checks_by_name = {check.name: check for check in report.checks}
    gerarchia = checks_by_name["Gerarchia delle resistenze (rottura duttile lato acciaio)"]
    uls = checks_by_name["Verifica PR > PEd"]
    staffe = checks_by_name["Area staffe orizzontali >= As,lnk minima"]

    c34 = outputs["C34"]
    if c34 == _SUCCESS_TEXT:
        assert gerarchia.passed and uls.passed
    elif c34 == _GERARCHIA_FAIL_TEXT:
        assert not gerarchia.passed
    elif c34 == _ULS_FAIL_TEXT:
        assert gerarchia.passed and not uls.passed
    else:  # pragma: no cover - fail loudly on an unrecognised verdict string
        pytest.fail(f"unrecognised C34 verdict: {c34!r}")

    assert staffe.passed == (outputs["A36"] is None)
