"""Oracle tests against `30_Calcolo pilastri in c.a. secondo NTC 2018 e Circolare2019.xls`
(slug "ca-pilastri-ntc2018"), sheet "Pilastri circolari" — `norma="NTC2018"`,
`legacy_compat=True` (tests/fixtures/gen_ca_pilastri_circolare_ntc2018.py)."""
import json
from pathlib import Path

import pytest

from strutture.members.ca_pilastri.models import PilastroCircolareInput
from strutture.members.ca_pilastri.tool_circolare import run_pilastro_circolare

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_pilastri_circolare_ntc2018_oracle.json").read_text(encoding="utf-8"))

DEFAULTS = {
    "H6": 400, "H8": 5000, "H9": "B450C", "H10": "C25/30", "H11": 1200, "H12": 150,
    "H13": 80, "H14": 50, "H15": 25, "H16": 16, "H17": 10, "H18": 150, "H25": 160,
}
CELL_TO_FIELD = {
    "H6": "d_mm", "H8": "h_mm", "H9": "acciaio", "H10": "cls", "H11": "ned_kN",
    "H12": "ved_kN", "H13": "med_kNm", "H14": "c_mm", "H15": "n_ferri", "H16": "diametro_ferri_mm",
    "H17": "diametro_staffe_mm", "H18": "passo_staffe_mm", "H25": "mrd_kNm",
}


def _sheet_ok(text: str) -> bool:
    return text.endswith("OK")


def _build_inputs(overrides: dict[str, object]) -> PilastroCircolareInput:
    cells = {**DEFAULTS, **overrides}
    fields = {CELL_TO_FIELD[cell]: value for cell, value in cells.items()}
    return PilastroCircolareInput(**fields, norma="NTC2018", legacy_compat=True)


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs = _build_inputs(case["inputs"])
    outputs = case["outputs"]
    report = run_pilastro_circolare(inputs)
    assert report.ok
    data = report.data
    by_name = {c.name: c.passed for c in report.checks}

    assert data.materiali.fyd_MPa == pytest.approx(outputs["Z8"], rel=1e-6)
    assert data.materiali.fcd_MPa == pytest.approx(outputs["Z9"], rel=1e-6)
    assert data.geometria.ac_mm2 == pytest.approx(outputs["H22"], rel=1e-6)
    assert data.geometria.as_mm2 == pytest.approx(outputs["H23"], rel=1e-6)
    assert data.geometria.rs == pytest.approx(outputs["H24"], rel=1e-6)
    assert by_name["percentuale_armatura"] is _sheet_ok(outputs["J24"])
    assert data.geometria.e_min_mm == pytest.approx(outputs["H19"], rel=1e-6)
    assert data.geometria.med_ecc_kNm == pytest.approx(outputs["H20"], rel=1e-6)
    assert data.geometria.med_calc_kNm == pytest.approx(outputs["H21"], rel=1e-6)
    assert data.taglio.ac == pytest.approx(outputs["CX38"], rel=1e-6)

    if isinstance(outputs["Z13"], str):
        pytest.skip("case with #NUM! (over-reinforced stirrups, outside the method's validity range)")
    assert data.taglio.cot_theta == pytest.approx(outputs["Z13"], rel=1e-6)
    assert data.taglio.vrdc_kN == pytest.approx(outputs["Z15"], rel=1e-6)
    assert data.taglio.vrds_kN == pytest.approx(outputs["Z16"], rel=1e-6)
    assert data.taglio.vrd_kN == pytest.approx(outputs["Z17"], rel=1e-6)
    assert by_name["taglio"] is _sheet_ok(outputs["Y18"])
    assert by_name["gerarchia_resistenze"] is _sheet_ok(outputs["Y20"])
    assert by_name["flessione"] is _sheet_ok(outputs["G26"])
    assert data.compressione.nrcd_kN == pytest.approx(outputs["H27"], rel=1e-6)
    assert by_name["compressione"] is _sheet_ok(outputs["G28"])
    assert data.confinamento.hcr_mm == pytest.approx(outputs["Z24"], rel=1e-6)
    assert data.confinamento.passo_max_confinato_mm == pytest.approx(outputs["Z25"], rel=1e-6)
    assert data.snellezza.lambda_lim == pytest.approx(outputs["J60"], rel=1e-5)
    assert data.snellezza.i_mm == pytest.approx(outputs["J63"], rel=1e-6)
    assert data.snellezza.lambda_ == pytest.approx(outputs["J64"], rel=1e-6)
    assert data.dettagli.interasse_long_calcolato_mm == pytest.approx(outputs["CX24"], rel=1e-6)
    assert data.dettagli.diametro_long_min_mm == pytest.approx(outputs["J68"], rel=1e-6)
    assert by_name["diametro_minimo_longitudinale"] is _sheet_ok(outputs["L68"])
    assert data.dettagli.interasse_long_max_mm == pytest.approx(outputs["J69"], rel=1e-6)
    assert by_name["interasse_massimo_longitudinale"] is _sheet_ok(outputs["L69"])
    assert data.dettagli.as_long_min_mm2 == pytest.approx(outputs["J70"], rel=1e-6)
    assert by_name["area_minima_longitudinale"] is _sheet_ok(outputs["L70"])
    assert data.dettagli.diametro_staffe_min_mm == pytest.approx(outputs["J71"], rel=1e-6)
    assert by_name["diametro_minimo_staffe"] is _sheet_ok(outputs["L71"])
    assert data.dettagli.interasse_staffe_max_mm == pytest.approx(outputs["J72"], rel=1e-6)
    assert by_name["interasse_massimo_staffe"] is _sheet_ok(outputs["L72"])
