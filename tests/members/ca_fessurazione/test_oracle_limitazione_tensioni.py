import json
from pathlib import Path

import pytest

from strutture.members.ca_fessurazione.models import LimitazioneTensioniInput
from strutture.members.ca_fessurazione.tool import run_limitazione_tensioni

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_fessurazione_limitazione_tensioni_oracle.json").read_text())


def _verificato(verdetto: str) -> bool:
    return verdetto == "ok"


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs, outputs = case["inputs"], case["outputs"]
    report = run_limitazione_tensioni(
        LimitazioneTensioniInput(
            rck_MPa=inputs["C6"],
            fyk_MPa=inputs["C8"],
            sigma_c_rar_1_MPa=inputs["D13"],
            sigma_c_qpe_1_MPa=inputs["D14"],
            sigma_s_rar_1_MPa=inputs["D15"],
            sigma_c_rar_2_MPa=inputs["D21"],
            sigma_c_qpe_2_MPa=inputs["D22"],
            sigma_s_rar_2_MPa=inputs["D23"],
            sigma_c_rar_3_MPa=inputs["D29"],
            sigma_c_qpe_3_MPa=inputs["D30"],
            sigma_s_rar_3_MPa=inputs["D31"],
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    assert data.fck_MPa == pytest.approx(outputs["C7"], rel=1e-6)

    for sezione, (limite_prefix, util_prefix, verdetto_prefix) in zip(
        data.sezioni, (("C13", "E13", "F13"), ("C21", "E21", "F21"), ("C29", "E29", "F29")), strict=True
    ):
        base = int(limite_prefix[1:])
        assert sezione.sigma_c_max_rar_MPa == pytest.approx(outputs[f"C{base}"], rel=1e-6)
        assert sezione.utilizzo_c_rar == pytest.approx(outputs[f"E{base}"], rel=1e-6)
        assert sezione.verificato_c_rar is _verificato(outputs[f"F{base}"])
        assert sezione.sigma_c_max_qpe_MPa == pytest.approx(outputs[f"C{base + 1}"], rel=1e-6)
        assert sezione.utilizzo_c_qpe == pytest.approx(outputs[f"E{base + 1}"], rel=1e-6)
        assert sezione.verificato_c_qpe is _verificato(outputs[f"F{base + 1}"])
        assert sezione.sigma_s_max_rar_MPa == pytest.approx(outputs[f"C{base + 2}"], rel=1e-6)
        assert sezione.utilizzo_s_rar == pytest.approx(outputs[f"E{base + 2}"], rel=1e-6)
        assert sezione.verificato_s_rar is _verificato(outputs[f"F{base + 2}"])
