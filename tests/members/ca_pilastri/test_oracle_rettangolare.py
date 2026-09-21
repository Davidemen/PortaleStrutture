import json
from pathlib import Path

import pytest

from strutture.members.ca_pilastri.models import PilastroRettangolareInput
from strutture.members.ca_pilastri.tool_rettangolare import run_pilastro_rettangolare

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_pilastri_rettangolare_oracle.json").read_text())

DEFAULTS = {
    "H5": 400, "H6": 400, "H7": 3500, "H8": "B450C", "H9": "C25/30", "H10": 1200, "H11": 150,
    "H12": 80, "H13": 50, "H14": 8, "H15": 16, "H16": 10, "H17": 150, "H24": 160,
}
CELL_TO_FIELD = {
    "H5": "l1_mm", "H6": "l2_mm", "H7": "h_mm", "H8": "acciaio", "H9": "cls", "H10": "ned_kN",
    "H11": "ved_kN", "H12": "med_kNm", "H13": "c_mm", "H14": "n_ferri", "H15": "diametro_ferri_mm",
    "H16": "diametro_staffe_mm", "H17": "passo_staffe_mm", "H24": "mrd_kNm",
}


def _sheet_ok(text: str) -> bool:
    return text.endswith("OK")


def _build_inputs(overrides: dict[str, object]) -> PilastroRettangolareInput:
    cells = {**DEFAULTS, **overrides}
    fields = {CELL_TO_FIELD[cell]: value for cell, value in cells.items()}
    return PilastroRettangolareInput(**fields, n_ferri_l1=3, legacy_compat=True, norma="NTC2008")


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs = _build_inputs(case["inputs"])
    outputs = case["outputs"]
    report = run_pilastro_rettangolare(inputs)
    assert report.ok
    data = report.data
    by_name = {c.name: c.passed for c in report.checks}

    assert data.materiali.fyd_MPa == pytest.approx(outputs["Z8"], rel=1e-6)
    assert data.materiali.fcd_MPa == pytest.approx(outputs["Z9"], rel=1e-6)
    assert data.geometria.ac_mm2 == pytest.approx(outputs["H21"], rel=1e-6)
    assert data.geometria.as_mm2 == pytest.approx(outputs["H22"], rel=1e-6)
    assert data.geometria.rs == pytest.approx(outputs["H23"], rel=1e-6)
    assert by_name["percentuale_armatura"] is _sheet_ok(outputs["J23"])
    assert data.geometria.e_min_mm == pytest.approx(outputs["H18"], rel=1e-6)
    assert data.geometria.med_ecc_kNm == pytest.approx(outputs["H19"], rel=1e-6)
    assert data.geometria.med_calc_kNm == pytest.approx(outputs["H20"], rel=1e-6)
    assert data.taglio.ac == pytest.approx(outputs["CX38"], rel=1e-6)
    assert data.taglio.cot_theta == pytest.approx(outputs["Z13"], rel=1e-6)
    assert data.taglio.vrdc_kN == pytest.approx(outputs["Z15"], rel=1e-6)
    assert data.taglio.vrds_kN == pytest.approx(outputs["Z16"], rel=1e-6)
    assert data.taglio.vrd_kN == pytest.approx(outputs["Z17"], rel=1e-6)
    assert by_name["taglio"] is _sheet_ok(outputs["Y18"])
    assert by_name["gerarchia_resistenze"] is _sheet_ok(outputs["Y20"])
    assert by_name["flessione"] is _sheet_ok(outputs["G25"])
    assert data.compressione.nrcd_kN == pytest.approx(outputs["H26"], rel=1e-6)
    assert by_name["compressione"] is _sheet_ok(outputs["G27"])
    assert data.confinamento.hcr_mm == pytest.approx(outputs["Z24"], rel=1e-6)
    assert data.confinamento.passo_max_confinato_mm == pytest.approx(outputs["Z25"], rel=1e-6)
    assert data.snellezza.lambda_lim == pytest.approx(outputs["J53"], rel=1e-5)
    assert data.snellezza.i_mm == pytest.approx(outputs["J55"], rel=1e-6)
    assert data.snellezza.lambda_ == pytest.approx(outputs["J56"], rel=1e-6)
    assert by_name["snellezza"] is _sheet_ok(outputs["J57"])
    assert data.dettagli.interasse_long_calcolato_mm == pytest.approx(outputs["CX24"], rel=1e-6)
    assert data.dettagli.diametro_long_min_mm == pytest.approx(outputs["J60"], rel=1e-6)
    assert by_name["diametro_minimo_longitudinale"] is _sheet_ok(outputs["L60"])
    assert data.dettagli.interasse_long_max_mm == pytest.approx(outputs["J61"], rel=1e-6)
    assert by_name["interasse_massimo_longitudinale"] is _sheet_ok(outputs["L61"])
    assert data.dettagli.as_long_min_mm2 == pytest.approx(outputs["J62"], rel=1e-6)
    assert by_name["area_minima_longitudinale"] is _sheet_ok(outputs["L62"])
    # J63/L63 (diametro minimo staffe): the sheet aggregates candidates with MIN and compares
    # against H9 (concrete class text) instead of H16 — always "OK" regardless of magnitude, a
    # confirmed bug (see docs/divergences/ca-pilastri.md). legacy_compat reproduces that exactly.
    assert by_name["diametro_minimo_staffe"] is True
    assert _sheet_ok(outputs["L63"]) is True
    assert data.dettagli.interasse_staffe_max_mm == pytest.approx(outputs["J64"], rel=1e-6)
    assert by_name["interasse_massimo_staffe"] is _sheet_ok(outputs["L64"])
