import json
from pathlib import Path

import pytest

from strutture.members.ca_fessurazione.models import AperturaFessureSempInput
from strutture.members.ca_fessurazione.tool import run_apertura_fessure_semplificata

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_fessurazione_apertura_fessure_semp_oracle.json").read_text())

# The diameter (mm) used to build each fixture case's D-column pair, in section order — see
# tests/fixtures/gen_ca_fessurazione_apertura_fessure_semp.py for the Tab. C4.1.II values chosen.
DIAMETRI_PER_CASO: tuple[tuple[float, float, float], ...] = (
    (16, 16, 16),
    (10, 20, 32),
    (12, 14, 18),
    (22, 24, 26),
    (28, 30, 32),
    (20, 32, 10),
)


def _verificato(verdetto: str) -> bool:
    return verdetto == "ok"


@pytest.mark.oracle
@pytest.mark.parametrize(("case", "diametri"), list(zip(FIXTURE, DIAMETRI_PER_CASO, strict=True)), ids=range(len(FIXTURE)))
def test_oracle_case(case: dict, diametri: tuple[float, float, float]):
    inputs, outputs = case["inputs"], case["outputs"]
    diametro_1, diametro_2, diametro_3 = diametri

    report = run_apertura_fessure_semplificata(
        AperturaFessureSempInput(
            diametro_mm_1=diametro_1,
            sigma_fre_MPa_1=inputs["E21"],
            sigma_qpe_MPa_1=inputs["E22"],
            diametro_mm_2=diametro_2,
            sigma_fre_MPa_2=inputs["E43"],
            sigma_qpe_MPa_2=inputs["E44"],
            diametro_mm_3=diametro_3,
            sigma_fre_MPa_3=inputs["E66"],
            sigma_qpe_MPa_3=inputs["E67"],
            legacy_compat=True,
        )
    )
    assert report.ok
    data = report.data

    prefissi_per_sezione = (
        ("D21", "D22", "F21", "G21", "F22", "G22"),
        ("D43", "D44", "F43", "G43", "F44", "G44"),
        ("D66", "D67", "F66", "G66", "F67", "G67"),
    )
    for sezione, prefissi in zip(data.sezioni, prefissi_per_sezione, strict=True):
        d_fre, d_qpe, f_fre, g_fre, f_qpe, g_qpe = prefissi
        assert sezione.sigma_lim_fre_MPa == pytest.approx(inputs[d_fre], rel=1e-6)
        assert sezione.sigma_lim_qpe_MPa == pytest.approx(inputs[d_qpe], rel=1e-6)
        assert sezione.utilizzo_fre == pytest.approx(outputs[f_fre], rel=1e-6)
        assert sezione.verificato_fre is _verificato(outputs[g_fre])
        assert sezione.utilizzo_qpe == pytest.approx(outputs[f_qpe], rel=1e-6)
        assert sezione.verificato_qpe is _verificato(outputs[g_qpe])
