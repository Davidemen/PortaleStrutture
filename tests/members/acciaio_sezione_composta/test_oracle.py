"""Oracle test: legacy_compat=True vs LibreOffice recalculation of Rev01/Rev00
(tests/fixtures/gen_acciaio_sezione_composta.py + gen_acciaio_sezione_composta_rev00.py), across
8 Rev01 cases exercising every branch (unreinforced, one plate, both plates symmetric, thin/thick
sections, hard-coded-web-height and B9-proxy bugs) plus the Rev00 free extra golden case."""
import json
from pathlib import Path

import pytest

from strutture.members.acciaio_sezione_composta.models import SezioneHRimpiattataInput
from strutture.members.acciaio_sezione_composta.tool import run

pytestmark = pytest.mark.oracle

FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"
REV01 = json.loads((FIXTURES_DIR / "acciaio_sezione_composta_oracle.json").read_text(encoding="utf-8"))
REV00 = json.loads((FIXTURES_DIR / "acciaio_sezione_composta_rev00_oracle.json").read_text(encoding="utf-8"))


def _inputs_from_case(outputs: dict) -> SezioneHRimpiattataInput:
    return SezioneHRimpiattataInput(
        h_profilo_mm=outputs["B1"], b_profilo_mm=outputs["B2"], tf_mm=outputs["C6"], tw_mm=outputs["B7"],
        piatti=(
            {"b_mm": outputs["B9"], "h_mm": outputs["C9"]},
            {"b_mm": outputs["B10"], "h_mm": outputs["C10"]},
        ),
        legacy_compat=True,
    )


@pytest.mark.parametrize("case", REV01, ids=lambda c: f"B1={c['outputs']['B1']}_B9={c['outputs']['B9']}_B10={c['outputs']['B10']}")
def test_rev01_matches_libreoffice_recalculation(case):
    outputs = case["outputs"]
    report = run(_inputs_from_case(outputs))
    assert report.ok
    sezione = report.data.sezione

    assert sezione.x_n_mm == pytest.approx(outputs["G6"], abs=1e-6)
    assert sezione.y_n_mm == pytest.approx(outputs["H6"], abs=1e-6)
    assert sezione.wpl_x_cm3 == pytest.approx(outputs["M13"], rel=1e-6)
    assert sezione.wpl_y_cm3 == pytest.approx(outputs["N13"], abs=1e-6)
    assert sezione.iy_cm4 == pytest.approx(outputs["O13"], rel=1e-6)
    assert sezione.iy_base_cm4 == pytest.approx(outputs["P13"], rel=1e-6)


def test_rev00_free_extra_golden_case_matches_libreoffice_recalculation():
    outputs = REV00[0]["outputs"]
    report = run(_inputs_from_case(outputs))
    assert report.ok
    sezione = report.data.sezione

    assert sezione.x_n_mm == pytest.approx(outputs["G6"], abs=1e-6)
    assert sezione.y_n_mm == pytest.approx(outputs["H6"], abs=1e-6)
    assert sezione.wpl_x_cm3 == pytest.approx(outputs["M13"], rel=1e-6)
    assert sezione.wpl_y_cm3 == pytest.approx(outputs["N13"], abs=1e-6)
