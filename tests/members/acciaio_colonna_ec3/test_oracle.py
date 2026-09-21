"""Oracle: acciaio_colonna_ec3_oracle.json, legacy_compat=True, vs. real LibreOffice recalculation."""
import importlib.util
import json
from pathlib import Path

import pytest

from strutture.members.acciaio_colonna_ec3.models import ColonnaEc3Input
from strutture.members.acciaio_colonna_ec3.tool import run

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"
FIXTURE = json.loads((FIXTURES_DIR / "acciaio_colonna_ec3_oracle.json").read_text())


def _load_generator_module():
    spec = importlib.util.spec_from_file_location(
        "gen_acciaio_colonna_ec3_oracle", FIXTURES_DIR / "gen_acciaio_colonna_ec3_oracle.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # pure constants/functions, no LibreOffice call at import time
    return module


_GEN = _load_generator_module()
_CASI = [{**_GEN.BASE, **campi} for campi in _GEN.CASI_CAMPI]


def _sheet_ok(text: str) -> bool:
    return text == "OK"


@pytest.mark.oracle
@pytest.mark.parametrize("index", range(len(FIXTURE)), ids=range(len(FIXTURE)))
def test_oracle_case(index: int) -> None:
    campi = {k: v for k, v in _CASI[index].items() if k != "sezione_nome"}
    out = FIXTURE[index]["outputs"]

    inputs = ColonnaEc3Input(**campi, legacy_compat=True)
    report = run(inputs)
    assert report.ok
    d = report.data

    assert d.materiali.fyd_MPa == pytest.approx(out["H14"], rel=1e-6)
    assert d.materiali.fud_MPa == pytest.approx(out["H15"], rel=1e-6)
    assert d.sezione.curva_instabilita_lt == out["BC17"]
    assert d.sezione.alpha_yy == pytest.approx(out["Y25"], rel=1e-6)
    assert d.sezione.alpha_zz == pytest.approx(out["Y26"], rel=1e-6)
    assert d.sezione.alpha_lt == pytest.approx(out["BC25"], rel=1e-6)

    assert d.instabilita_flessionale.ncr_y_kN == pytest.approx(out["Y21"], rel=1e-6)
    assert d.instabilita_flessionale.ncr_z_kN == pytest.approx(out["Y22"], rel=1e-6)
    assert d.instabilita_flessionale.ncr_t_kN == pytest.approx(out["AV38"], rel=1e-6)
    assert d.instabilita_flessionale.lambda_yy == pytest.approx(out["W23"], rel=1e-6)
    assert d.instabilita_flessionale.lambda_zz == pytest.approx(out["W24"], rel=1e-6)
    assert d.instabilita_flessionale.chi_yy == pytest.approx(out["W29"], rel=1e-6)
    assert d.instabilita_flessionale.chi_zz == pytest.approx(out["W32"], rel=1e-6)

    assert d.instabilita_torso_flessionale.mcr_Nmm == pytest.approx(out["AI8"], rel=1e-6)
    assert d.instabilita_torso_flessionale.lambda_lt == pytest.approx(out["AI35"], rel=1e-6)
    assert d.instabilita_torso_flessionale.chi_lt == pytest.approx(out["U37"], rel=1e-6)
    assert d.instabilita_torso_flessionale.verifica_non_necessaria == (
        out["O59"] == "No allowance for lateral-torsional buckling necessary"
    )

    assert d.flessione.mrd_y_kNm == pytest.approx(out["D33"], rel=1e-6)
    assert d.flessione.mrd_z_kNm == pytest.approx(out["D43"], rel=1e-6)
    assert d.taglio.vpl_rd_anima_kN == pytest.approx(out["G26"], rel=1e-6)
    assert d.taglio.vpl_rd_ali_kN == pytest.approx(out["G36"], rel=1e-6)
    assert d.taglio.verifica_anima.passed == _sheet_ok(out["J26"])
    assert d.taglio.verifica_ali.passed == _sheet_ok(out["J36"])

    assert d.taglio_instabilita.hw_t == pytest.approx(out["AC27"], rel=1e-6)
    assert d.taglio_instabilita.limite_72_eps_eta == pytest.approx(out["AD27"], rel=1e-6)
    assert d.taglio_instabilita.richiede_verifica == (out["K32"] == "Shear buckling check")
    assert d.taglio_instabilita.cw == pytest.approx(out["C67"], rel=1e-6)
    assert d.taglio_instabilita.vb_rd_kN == pytest.approx(out["O75"], rel=1e-6)

    assert d.interazione.cmy == pytest.approx(out["AM64"], rel=1e-6)
    assert d.interazione.cmz == pytest.approx(out["AM65"], rel=1e-6)
    assert d.interazione.cm_lt == pytest.approx(out["AM66"], rel=1e-6)
    assert d.interazione.kyy == pytest.approx(out["X42"], rel=1e-6)
    assert d.interazione.kyz == pytest.approx(out["X43"], rel=1e-6)
    assert d.interazione.kzy == pytest.approx(out["X44"], rel=1e-6)
    assert d.interazione.kzz == pytest.approx(out["X45"], rel=1e-6)
    assert d.interazione.utilizzo_yy == pytest.approx(out["Y47"], rel=1e-6)
    assert d.interazione.utilizzo_zz == pytest.approx(out["Y50"], rel=1e-6)

    assert d.interazione_semplificata.n_ratio == pytest.approx(out["H46"], rel=1e-6)
    assert d.interazione_semplificata.mn_rd_y_kNm == pytest.approx(out["J53"], rel=1e-6)
    assert d.interazione_semplificata.mn_rd_z_kNm == pytest.approx(out["J54"], rel=1e-6)
    assert d.interazione_semplificata.v54 == pytest.approx(out["V54"], rel=1e-6)
    assert d.interazione_semplificata.i56 == pytest.approx(out["I56"], rel=1e-6)
