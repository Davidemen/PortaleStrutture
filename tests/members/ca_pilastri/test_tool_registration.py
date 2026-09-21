"""`TOOLS` registration sanity: both column tools are exposed with a matching name/model shape."""
import pytest

from strutture.members.ca_pilastri.models import PilastroCircolareInput, PilastroOutput, PilastroRettangolareInput
from strutture.members.ca_pilastri.tool import TOOLS


@pytest.mark.unit
def test_tools_registered_with_expected_names_and_models():
    by_name = {tool.name: tool for tool in TOOLS}
    assert set(by_name) == {"ca-pilastro-rettangolare", "ca-pilastro-circolare"}

    rett = by_name["ca-pilastro-rettangolare"]
    assert rett.input_model is PilastroRettangolareInput
    assert rett.output_model is PilastroOutput

    circ = by_name["ca-pilastro-circolare"]
    assert circ.input_model is PilastroCircolareInput
    assert circ.output_model is PilastroOutput


@pytest.mark.unit
def test_tools_run_end_to_end():
    by_name = {tool.name: tool for tool in TOOLS}
    rett_report = by_name["ca-pilastro-rettangolare"].run(
        PilastroRettangolareInput(
            l1_mm=400, l2_mm=400, h_mm=3500, acciaio="B450C", cls="C25/30", ned_kN=1200, ved_kN=150,
            med_kNm=80, c_mm=50, n_ferri=8, diametro_ferri_mm=16, diametro_staffe_mm=10,
            passo_staffe_mm=150, mrd_kNm=160, n_ferri_l1=3, legacy_compat=True,
        )
    )
    assert rett_report.ok

    circ_report = by_name["ca-pilastro-circolare"].run(
        PilastroCircolareInput(
            d_mm=400, h_mm=5000, acciaio="B450C", cls="C25/30", ned_kN=1200, ved_kN=150, med_kNm=80,
            c_mm=50, n_ferri=25, diametro_ferri_mm=16, diametro_staffe_mm=10, passo_staffe_mm=150,
            mrd_kNm=160, legacy_compat=True,
        )
    )
    assert circ_report.ok


@pytest.mark.unit
def test_check_names_are_readable_italian_phrases_not_python_keys():
    """Design review (P0): `Check(name=...)` must be a readable Italian phrase, never a raw
    snake_case Python key, so no check name may contain an underscore."""
    from strutture.shared.tool import execute

    for tool in TOOLS:
        report = execute(tool, tool.example)
        assert report.ok, report.errors
        assert report.checks
        for check in report.checks:
            assert "_" not in check.name, (tool.name, check.name)
