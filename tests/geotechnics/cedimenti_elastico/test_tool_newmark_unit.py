import pytest
from pydantic import ValidationError

from strutture.geotechnics.cedimenti_elastico.models_newmark import NewmarkInput
from strutture.geotechnics.cedimenti_elastico.tool_newmark import run_newmark
from strutture.shared.report import CalcError

CENTRO_STRATI = [{"z_top_m": 0.0, "z_bot_m": 120.0, "modulo_MPa": 10.0}]


@pytest.mark.unit
def test_centro_requires_b_and_l():
    with pytest.raises(ValidationError, match="indicare B e L"):
        NewmarkInput(modalita="CENTRO", q=100.0, d=0.0, strati=CENTRO_STRATI)


@pytest.mark.unit
def test_punto_requires_its_own_fields():
    with pytest.raises(ValidationError, match="O'd, O'g"):
        NewmarkInput(modalita="PUNTO", q=100.0, d=0.0, strati=CENTRO_STRATI)


@pytest.mark.unit
def test_layer_gap_or_start_not_at_zero_only_matters_when_it_falls_below_the_base():
    # first ground layer starting above 0 is fine (mirrors the CENTRO sheet's own B7=80cm start):
    # it is entirely irrelevant once the embedment truncates it away.
    inputs = NewmarkInput(modalita="CENTRO", q=100.0, d=0.0, b=1.0, l=1.0, strati=CENTRO_STRATI, z_max=1.0, dz=0.5)
    report = run_newmark(inputs)
    assert report.ok, report.errors


@pytest.mark.unit
def test_overlapping_strati_are_rejected():
    strati = [{"z_top_m": 0.0, "z_bot_m": 2.0, "modulo_MPa": 10.0}, {"z_top_m": 1.0, "z_bot_m": 5.0, "modulo_MPa": 100.0}]
    with pytest.raises(ValidationError, match="non è contigua"):
        NewmarkInput(modalita="CENTRO", q=100.0, d=0.0, b=1.0, l=1.0, strati=strati, z_max=1.0, dz=0.5)


@pytest.mark.unit
def test_gapped_strati_are_rejected():
    strati = [{"z_top_m": 0.0, "z_bot_m": 1.0, "modulo_MPa": 10.0}, {"z_top_m": 2.0, "z_bot_m": 5.0, "modulo_MPa": 100.0}]
    with pytest.raises(ValidationError, match="non è contigua"):
        NewmarkInput(modalita="CENTRO", q=100.0, d=0.0, b=1.0, l=1.0, strati=strati, z_max=1.0, dz=0.5)


@pytest.mark.unit
def test_code_standard_raises_past_the_layer_table():
    inputs = NewmarkInput(
        modalita="CENTRO", q=100.0, d=0.0, b=1.0, l=1.0,
        strati=[{"z_top_m": 0.0, "z_bot_m": 1.0, "modulo_MPa": 10.0}], z_max=5.0, dz=1.0, legacy_compat=False,
    )
    with pytest.raises(CalcError, match="stratigrafia"):
        run_newmark(inputs)


@pytest.mark.unit
def test_legacy_silently_zeroes_past_the_layer_table():
    inputs = NewmarkInput(
        modalita="CENTRO", q=100.0, d=0.0, b=1.0, l=1.0,
        strati=[{"z_top_m": 0.0, "z_bot_m": 1.0, "modulo_MPa": 10.0}], z_max=5.0, dz=1.0, legacy_compat=True,
    )
    report = run_newmark(inputs)
    assert report.ok
    assert any(r.modulo_MPa is None for r in report.data.righe)


@pytest.mark.unit
def test_code_standard_unifies_the_two_centro_integration_depths():
    """docs/architecture-batch2.md §7 'newmark T6 vs Z6': legacy has two different depths
    (9.00m / 8.10m); code-standard fixes this by sharing one grid."""
    inputs = NewmarkInput(modalita="CENTRO", q=100.0, d=0.0, b=1.0, l=1.0, strati=CENTRO_STRATI, z_max=5.0, dz=0.5, legacy_compat=False)
    report = run_newmark(inputs)
    assert [r.z_m for r in report.data.righe] == [r.z_m for r in report.data.righe_qa]


@pytest.mark.unit
def test_out_of_kern_point_settlement_is_positive_but_smaller_than_center():
    inputs_center = NewmarkInput(
        modalita="PUNTO", q=100.0, d=0.0, side_p=1.0, side_q=1.0, e1=0.5, e2=0.5,
        strati=CENTRO_STRATI, z_max=1.0, dz=0.5, legacy_compat=False,
    )
    inputs_outside = inputs_center.model_copy(update={"e1": 2.0})
    center_report, outside_report = run_newmark(inputs_center), run_newmark(inputs_outside)
    assert center_report.ok and outside_report.ok
    assert 0 < outside_report.data.punto.w_o_cm < center_report.data.punto.w_o_cm
