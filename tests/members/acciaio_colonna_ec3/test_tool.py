"""tool.py — Tool registration and end-to-end report composition."""
import pytest

from strutture.members.acciaio_colonna_ec3.models import ColonnaEc3Input
from strutture.members.acciaio_colonna_ec3.tool import ESEMPIO_AUREO, TOOLS, run
from strutture.shared.tool import discover


@pytest.mark.unit
def test_tools_tuple_exposes_one_composed_tool() -> None:
    assert len(TOOLS) == 1
    tool = TOOLS[0]
    assert tool.name == "acciaio-colonna-h-ec3"
    assert tool.input_model is ColonnaEc3Input
    assert tool.example == {k: v for k, v in ESEMPIO_AUREO.items() if k != "legacy_compat"}


@pytest.mark.unit
def test_discoverable_via_shared_registry() -> None:
    found = discover()
    assert "acciaio-colonna-h-ec3" in found


@pytest.mark.unit
def test_fixed_mode_warns_on_nonstandard_gamma_override() -> None:
    inputs = ColonnaEc3Input(**{**ESEMPIO_AUREO, "legacy_compat": False, "gamma_m0": 1.2, "gamma_m1": None})
    report = run(inputs)
    assert report.ok
    assert any("1.2" in w for w in report.warnings)


@pytest.mark.unit
def test_fixed_mode_defaults_do_not_warn() -> None:
    inputs = ColonnaEc3Input(**{**ESEMPIO_AUREO, "legacy_compat": False, "gamma_m0": None, "gamma_m1": None})
    report = run(inputs)
    assert report.ok
    assert report.warnings == ()


@pytest.mark.unit
def test_report_exposes_every_group() -> None:
    report = run(ColonnaEc3Input(**ESEMPIO_AUREO))
    d = report.data
    for group in (
        d.materiali, d.sezione, d.instabilita_flessionale, d.instabilita_torso_flessionale,
        d.flessione, d.taglio, d.taglio_instabilita, d.interazione, d.interazione_semplificata,
    ):
        assert group is not None
    assert len(report.checks) >= 9
