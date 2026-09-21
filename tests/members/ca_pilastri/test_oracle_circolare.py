import json
from pathlib import Path

import pytest

from strutture.members.ca_pilastri.models import PilastroCircolareInput
from strutture.members.ca_pilastri.tool_circolare import run_pilastro_circolare

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_pilastri_circolare_oracle.json").read_text())

DEFAULTS = {
    "H5": 400, "H7": 5000, "H8": "B450C", "H9": "C25/30", "H10": 1200, "H11": 150,
    "H12": 80, "H13": 50, "H14": 25, "H15": 16, "H16": 10, "H17": 150, "H24": 160,
}
CELL_TO_FIELD = {
    "H5": "d_mm", "H7": "h_mm", "H8": "acciaio", "H9": "cls", "H10": "ned_kN",
    "H11": "ved_kN", "H12": "med_kNm", "H13": "c_mm", "H14": "n_ferri", "H15": "diametro_ferri_mm",
    "H16": "diametro_staffe_mm", "H17": "passo_staffe_mm", "H24": "mrd_kNm",
}


def _sheet_ok(text: str) -> bool:
    return text.endswith("OK")


def _build_inputs(overrides: dict[str, object]) -> PilastroCircolareInput:
    cells = {**DEFAULTS, **overrides}
    fields = {CELL_TO_FIELD[cell]: value for cell, value in cells.items()}
    return PilastroCircolareInput(**fields, legacy_compat=True, norma="NTC2008")


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
    assert data.geometria.ac_mm2 == pytest.approx(outputs["H21"], rel=1e-6)
    assert data.geometria.as_mm2 == pytest.approx(outputs["H22"], rel=1e-6)
    assert data.geometria.rs == pytest.approx(outputs["H23"], rel=1e-6)
    assert by_name["Percentuale di armatura longitudinale"] is _sheet_ok(outputs["J23"])
    assert data.geometria.e_min_mm == pytest.approx(outputs["H18"], rel=1e-6)
    assert data.geometria.med_ecc_kNm == pytest.approx(outputs["H19"], rel=1e-6)
    assert data.geometria.med_calc_kNm == pytest.approx(outputs["H20"], rel=1e-6)
    assert data.taglio.ac == pytest.approx(outputs["CX38"], rel=1e-6)

    if isinstance(outputs["Z13"], str):
        pytest.skip("case with #NUM! (over-reinforced stirrups, outside the method's validity range)")
    assert data.taglio.cot_theta == pytest.approx(outputs["Z13"], rel=1e-6)
    assert data.taglio.vrdc_kN == pytest.approx(outputs["Z15"], rel=1e-6)
    assert data.taglio.vrds_kN == pytest.approx(outputs["Z16"], rel=1e-6)
    assert data.taglio.vrd_kN == pytest.approx(outputs["Z17"], rel=1e-6)
    assert by_name["Resistenza a taglio"] is _sheet_ok(outputs["Y18"])
    assert by_name["Gerarchia delle resistenze a taglio"] is _sheet_ok(outputs["Y20"])
    assert by_name["Resistenza a pressoflessione"] is _sheet_ok(outputs["G25"])
    assert data.compressione.nrcd_kN == pytest.approx(outputs["H26"], rel=1e-6)
    assert by_name["Resistenza a compressione"] is _sheet_ok(outputs["G27"])
    assert data.confinamento.hcr_mm == pytest.approx(outputs["Z24"], rel=1e-6)
    assert data.confinamento.passo_max_confinato_mm == pytest.approx(outputs["Z25"], rel=1e-6)
    assert data.snellezza.lambda_lim == pytest.approx(outputs["J60"], rel=1e-5)
    assert data.snellezza.i_mm == pytest.approx(outputs["J62"], rel=1e-6)
    assert data.snellezza.lambda_ == pytest.approx(outputs["J63"], rel=1e-6)
    assert by_name["Verifica di snellezza"] is _sheet_ok(outputs["J64"])
    assert data.dettagli.interasse_long_calcolato_mm == pytest.approx(outputs["CX24"], rel=1e-6)
    assert data.dettagli.diametro_long_min_mm == pytest.approx(outputs["J67"], rel=1e-6)
    assert by_name["Diametro minimo delle barre longitudinali"] is _sheet_ok(outputs["L67"])
    assert data.dettagli.interasse_long_max_mm == pytest.approx(outputs["J68"], rel=1e-6)
    assert by_name["Interasse massimo delle barre longitudinali"] is _sheet_ok(outputs["L68"])
    assert data.dettagli.as_long_min_mm2 == pytest.approx(outputs["J69"], rel=1e-6)
    assert by_name["Area minima di armatura longitudinale"] is _sheet_ok(outputs["L69"])
    # J70/L70 (diametro minimo staffe): the circular sheet compares correctly against H16, but
    # still aggregates the two candidates with MIN instead of MAX (same bug as the rectangular
    # sheet's row); legacy_compat reproduces the MIN aggregation, see docs/divergences.
    assert data.dettagli.diametro_staffe_min_mm == pytest.approx(outputs["J70"], rel=1e-6)
    assert by_name["Diametro minimo delle staffe"] is _sheet_ok(outputs["L70"])
    assert data.dettagli.interasse_staffe_max_mm == pytest.approx(outputs["J71"], rel=1e-6)
    assert by_name["Interasse massimo delle staffe"] is _sheet_ok(outputs["L71"])
