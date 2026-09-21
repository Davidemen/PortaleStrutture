"""Oracle tests against `31_Calcolo pilastri in c.a. secondo UNI EN 1992-1-1 2005.xls`
(slug "ca-pilastri-ec2"), sheet "Ret._UNI EN 1992-1-1 2005" — `norma="EC2"`,
`legacy_compat=True` (tests/fixtures/gen_ca_pilastri_rettangolare_ec2.py)."""
import json
from pathlib import Path

import pytest

from strutture.members.ca_pilastri.models import PilastroRettangolareInput
from strutture.members.ca_pilastri.tool_rettangolare import run_pilastro_rettangolare

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_pilastri_rettangolare_ec2_oracle.json").read_text(encoding="utf-8"))

DEFAULTS = {
    "H6": 400, "H7": 400, "H8": 3500, "H9": "B450C", "H10": "C25/30", "H11": 1200, "H12": 150,
    "H13": 80, "H14": 50, "H15": 8, "H16": 16, "H17": 10, "H18": 150, "H25": 160,
}
CELL_TO_FIELD = {
    "H6": "l1_mm", "H7": "l2_mm", "H8": "h_mm", "H9": "acciaio", "H10": "cls", "H11": "ned_kN",
    "H12": "ved_kN", "H13": "med_kNm", "H14": "c_mm", "H15": "n_ferri", "H16": "diametro_ferri_mm",
    "H17": "diametro_staffe_mm", "H18": "passo_staffe_mm", "H25": "mrd_kNm",
}


def _sheet_ok(text: str) -> bool:
    return text.endswith("OK")


def _build_inputs(overrides: dict[str, object]) -> PilastroRettangolareInput:
    cells = {**DEFAULTS, **overrides}
    fields = {CELL_TO_FIELD[cell]: value for cell, value in cells.items()}
    return PilastroRettangolareInput(**fields, n_ferri_l1=3, norma="EC2", legacy_compat=True)


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
    assert data.geometria.ac_mm2 == pytest.approx(outputs["H22"], rel=1e-6)
    assert data.geometria.as_mm2 == pytest.approx(outputs["H23"], rel=1e-6)
    assert data.geometria.rs == pytest.approx(outputs["H24"], rel=1e-6)
    assert by_name["percentuale_armatura"] is _sheet_ok(outputs["J24"])
    assert data.geometria.e_min_mm == pytest.approx(outputs["H19"], rel=1e-6)
    assert data.geometria.med_ecc_kNm == pytest.approx(outputs["H20"], rel=1e-6)
    assert data.geometria.med_calc_kNm == pytest.approx(outputs["H21"], rel=1e-6)
    assert data.taglio.ac == pytest.approx(outputs["CX38"], rel=1e-6)
    assert data.regole.nu1 == pytest.approx(outputs["CX28"], rel=1e-6)
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
    assert data.regole.omega_meccanico == pytest.approx(outputs["CX49"], rel=1e-6)
    assert data.snellezza.lambda_lim == pytest.approx(outputs["J54"], rel=1e-5)
    assert data.snellezza.l0_mm == pytest.approx(outputs["J56"], rel=1e-6)
    assert data.snellezza.i_mm == pytest.approx(outputs["J57"], rel=1e-6)
    assert by_name["snellezza"] is _sheet_ok(outputs["J59"])
    assert data.dettagli.interasse_long_calcolato_mm == pytest.approx(outputs["CX24"], rel=1e-6)
    assert data.dettagli.diametro_long_min_mm == pytest.approx(outputs["J62"], rel=1e-6)
    assert by_name["diametro_minimo_longitudinale"] is _sheet_ok(outputs["L62"])
    assert by_name["area_massima_longitudinale"] is _sheet_ok(outputs["L63"])  # EC2-only standalone check
    assert data.armatura_minima.as_min_mm2 == pytest.approx(outputs["J64"], rel=1e-6)
    assert by_name["area_minima_longitudinale"] is _sheet_ok(outputs["L64"])
    # J65/L65 (diametro minimo staffe): compares against a text cell (H10, "Tipo di cls"), so
    # the sheet always reports "OK" regardless of the actual stirrup diameter — same class of
    # bug as the NTC2008/NTC2018 rectangular sheets.
    assert by_name["diametro_minimo_staffe"] is True
    assert _sheet_ok(outputs["L65"]) is True
    assert data.dettagli.interasse_staffe_max_mm == pytest.approx(outputs["J66"], rel=1e-6)
    assert by_name["interasse_massimo_staffe"] is _sheet_ok(outputs["L66"])
