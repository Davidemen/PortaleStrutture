"""Free golden case (docs/BUILD_CONTRACT.md "Member tools"): `Shotblast_375N` is a byte-identical
clone of `Shotblast_225N`'s formulas with different inputs (A=520, B=900 — a non-square rectangular
column, exercising the `A_a` divergence for `A != B`, docs/divergences/ca-punzonamento.md), read with
an empty override via `extract.fixtures.generate`."""
import json
from pathlib import Path

import pytest

from strutture.members.ca_punzonamento.compose import run
from strutture.members.ca_punzonamento.models import PunzonamentoInput
from strutture.members.ca_punzonamento.perimeter_area import area_within_perimeter_mm2

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_punzonamento_375n_oracle.json").read_text(encoding="utf-8"))
CASE = FIXTURE[0]
INPUTS = CASE["inputs"] if CASE["inputs"] else CASE["outputs"]  # empty override -> read the defaults back


def _punzonamento_inputs() -> PunzonamentoInput:
    i = INPUTS
    return PunzonamentoInput(
        ved_kN=i["D2"], pterreno_MPa=i["D3"], lato_a_mm=i["D4"], lato_b_mm=i["D5"], h_mm=i["D6"],
        diametro_mm=i["D7"], fck_MPa=i["D8"], copriferro_mm=i["D9"], posizione="interno",
        umanuale_mm=None if i["D21"] == "x" else i["D21"], a_amanuale_mm2=None if i["D24"] == "x" else i["D24"],
        px_mm=i["D27"], py_mm=i["D28"], phix_mm=i["D29"], phiy_mm=i["D30"], paddx_mm=i["D31"], paddy_mm=i["D32"],
        phiaddx_mm=i["D33"], phiaddy_mm=i["D34"], a1eff_mm=i["D46"], bu_mm=i["D47"], st_mm=i["D52"],
        phi_staffa_mm=i["D55"], n_staffe=i["D58"], legacy_compat=True,
    )


@pytest.mark.golden
def test_375n_free_golden_case():
    assert INPUTS["D4"] == 520 and INPUTS["D5"] == 900  # non-square column, A != B
    outputs = CASE["outputs"]
    report = run(_punzonamento_inputs())
    assert report.ok
    data = report.data

    assert data.geometria.u0_mm == pytest.approx(outputs["D16"], rel=1e-6)
    assert data.faccia_pilastro.v_ed_0_MPa == pytest.approx(outputs["D18"], rel=1e-5)
    assert data.perimetro_critico.a_governante_su_d == pytest.approx(outputs["AX154"], rel=1e-6)
    assert data.perimetro_critico.ui_mm == pytest.approx(outputs["D22"], rel=1e-5)
    assert data.perimetro_critico.area_mm2 == pytest.approx(outputs["D23"], rel=1e-5)
    assert data.perimetro_critico.v_rd_i_MPa == pytest.approx(outputs["D37"], rel=1e-5)
    assert data.perimetro_critico.v_ed_i_MPa == pytest.approx(outputs["D38"], rel=1e-4)
    assert data.perimetro_critico.armatura_necessaria is False
    assert data.armatura.v_rrd_kN == pytest.approx(outputs["D61"], rel=1e-5)


@pytest.mark.golden
def test_375n_a_over_b_rectangle_area_diverges_from_code_standard():
    """A=520 != B=900: the sheet's `4*MIN(A,B)*a` term differs from the standard `2*(A+B)*a` — the
    two formulas only coincide for a square column (docs/divergences/ec2-shared.md)."""
    a_governing_mm = CASE["outputs"]["D20"]
    legacy = area_within_perimeter_mm2(520.0, 900.0, 0.0, a_governing_mm, legacy_compat=True)
    fixed = area_within_perimeter_mm2(520.0, 900.0, 0.0, a_governing_mm, legacy_compat=False)
    assert legacy == pytest.approx(CASE["outputs"]["D23"], rel=1e-5)
    assert fixed > legacy  # 2*(A+B) > 4*MIN(A,B) whenever A != B
