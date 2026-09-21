import json
import math
from pathlib import Path

import pytest

from strutture.members.ca_fessurazione.models import AperturaFessureInput
from strutture.members.ca_fessurazione.tool import run_apertura_fessure

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_fessurazione_apertura_fessure_oracle.json").read_text())

# The sheet's own dropdown literal ("smplice", not "semplice") — the tool's own Literal is the
# corrected spelling; only the oracle recalculation needs the sheet's exact validation string.
_SOLLECITAZIONE_SHEET_TO_TOOL = {
    "caso di flessione": "caso di flessione",
    "caso di trazione smplice": "caso di trazione semplice",
}

_RAMO_SHEET_TO_TOOL = {"Usare C4.1.7": "C4.1.7", "Caso C4.1.10": "C4.1.10"}


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs, outputs = case["inputs"], case["outputs"]
    report = run_apertura_fessure(
        AperturaFessureInput(
            classe_calcestruzzo=inputs["E4"],
            tipo_barre=inputs["E5"],
            tipo_sollecitazione=_SOLLECITAZIONE_SHEET_TO_TOOL[inputs["E6"]],
            durata_carico=inputs["E7"],
            classe_fessurazione=inputs["E8"],
            interferro_mm=inputs["E9"],
            sigma_s_MPa=inputs["E10"],
            h_mm=inputs["E23"],
            x_mm=inputs["E25"],
            b_mm=inputs["E26"],
            n1=inputs["E29"],
            phi1_mm=inputs["E30"],
            n2=inputs["E31"],
            phi2_mm=inputs["E32"],
            copriferro_mm=inputs["E38"],
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.geometria.d_mm == pytest.approx(outputs["E24"], rel=1e-6)
    assert data.geometria.hc_eff_mm == pytest.approx(outputs["E22"], rel=1e-6)
    assert data.geometria.ac_eff_mm2 == pytest.approx(outputs["E27"], rel=1e-6)
    assert data.geometria.as_mm2 == pytest.approx(outputs["E35"], rel=1e-6)
    assert data.geometria.phi_eq_mm == pytest.approx(outputs["E33"], rel=1e-6)
    assert data.geometria.rho_eff == pytest.approx(outputs["E36"], rel=1e-6)

    assert data.materiale.ecm_MPa == pytest.approx(outputs["E18"], rel=1e-6)
    assert data.materiale.fctm_MPa == pytest.approx(outputs["E19"], rel=1e-6)
    assert data.materiale.alpha_e == pytest.approx(outputs["E20"], rel=1e-6)

    assert data.coefficienti.k1 == pytest.approx(outputs["E39"], rel=1e-9)
    assert data.coefficienti.k2 == pytest.approx(outputs["E40"], rel=1e-9)
    assert data.coefficienti.kt == pytest.approx(outputs["E43"], rel=1e-9)

    assert data.fessurazione.slim_mm == pytest.approx(outputs["E12"], rel=1e-6)
    assert data.fessurazione.ramo == _RAMO_SHEET_TO_TOOL[outputs["H12"]]
    assert data.fessurazione.delta_sm_mm == pytest.approx(outputs["E15"], rel=1e-6)
    assert data.fessurazione.epsilon_sm == pytest.approx(outputs["E45"], rel=1e-6)
    assert data.fessurazione.wlim_mm == pytest.approx(outputs["E46"], rel=1e-9)
    assert data.fessurazione.wk_mm == pytest.approx(outputs["E47"], rel=1e-6)
    atteso_utilizzo = math.ceil(outputs["E47"] / outputs["E46"] * 100) / 100
    assert data.fessurazione.utilizzo == pytest.approx(atteso_utilizzo, rel=1e-9)
    assert data.fessurazione.verificato is (outputs["E47"] < outputs["E46"])
