"""Unit tests for `tool.run` composition — the `legacy_compat` dispatch of `metodo_tensioni`, and
the layer-coverage `CalcError` naming the depth (docs/architecture-batch2.md §7 "edometrico J")."""
import pytest

from strutture.geotechnics.cedimenti_edometrico.models import EdometricoInput
from strutture.geotechnics.cedimenti_edometrico.tool import run
from strutture.shared.report import CalcError

_STRATO_CORTO = {"z_top_m": 0.0, "z_bot_m": 2.0, "modulo_MPa": 7.0}
_BASE = {"sistema_unita": "SI", "b": 3.5, "l": 5.0, "gamma": 18.0, "q": 50.0, "strati": [_STRATO_CORTO], "z_max": 5.0}


@pytest.mark.unit
def test_standard_mode_raises_calc_error_naming_the_depth_when_layers_do_not_cover_z_max() -> None:
    """The message names the first depth past the stratigraphy (2.1 m), not the nominal z_max — a
    more useful diagnostic than the generic 5 m ceiling would be."""
    with pytest.raises(CalcError, match=r"z=2\.1 m"):
        run(EdometricoInput(**{**_BASE, "legacy_compat": False}))


@pytest.mark.unit
def test_legacy_mode_zeroes_past_coverage_instead_of_raising() -> None:
    report = run(EdometricoInput(**{**_BASE, "legacy_compat": True}))
    assert report.ok
    oltre_copertura = [riga for riga in report.data.righe if riga.z_m > 2.0]
    assert oltre_copertura
    assert all(riga.eed_kPa is None for riga in oltre_copertura)


@pytest.mark.unit
def test_legacy_compat_forces_the_approssimato_method_regardless_of_metodo_tensioni() -> None:
    strato_ampio = {"z_top_m": 0.0, "z_bot_m": 50.0, "modulo_MPa": 7.0}
    report = run(EdometricoInput(**{**_BASE, "strati": [strato_ampio], "metodo_tensioni": "newmark", "legacy_compat": True}))
    assert report.ok
    riga = next(r for r in report.data.righe if r.z_m > 0)
    assert riga.delta_sigma_kPa == pytest.approx(riga.delta_sigma_approssimato_kPa)


@pytest.mark.unit
def test_standard_mode_honours_metodo_tensioni_newmark() -> None:
    strato_ampio = {"z_top_m": 0.0, "z_bot_m": 50.0, "modulo_MPa": 7.0}
    report = run(EdometricoInput(**{**_BASE, "strati": [strato_ampio], "metodo_tensioni": "newmark", "legacy_compat": False}))
    assert report.ok
    riga = next(r for r in report.data.righe if r.z_m > 0)
    assert riga.delta_sigma_kPa == pytest.approx(riga.delta_sigma_newmark_kPa)


@pytest.mark.unit
def test_standard_mode_sigma_v0_uses_total_stress_from_ground_level() -> None:
    """docs/architecture-batch2.md §7 review finding HIGH: for a dry site (γ=18 kN/m³, no
    embedment, no water table) σ'v0(z) must be the plain total overburden γ·z, not the buoyant
    `γ − γw` the old code always applied below the foundation base."""
    strato_ampio = {"z_top_m": 0.0, "z_bot_m": 50.0, "modulo_MPa": 7.0}
    report = run(EdometricoInput(**{**_BASE, "strati": [strato_ampio], "legacy_compat": False}))
    assert report.ok
    riga_5m = next(r for r in report.data.righe if r.z_m == pytest.approx(5.0))
    assert riga_5m.sigma_v0_kPa == pytest.approx(18.0 * 5.0, rel=1e-6)


@pytest.mark.unit
def test_standard_mode_sigma_v0_includes_the_embedment_overburden() -> None:
    strato_ampio = {"z_top_m": 0.0, "z_bot_m": 50.0, "modulo_MPa": 7.0}
    report = run(EdometricoInput(**{**_BASE, "d": 1.5, "strati": [strato_ampio], "legacy_compat": False}))
    assert report.ok
    riga_5m = next(r for r in report.data.righe if r.z_m == pytest.approx(5.0))
    assert riga_5m.sigma_v0_kPa == pytest.approx(18.0 * (1.5 + 5.0), rel=1e-6)


@pytest.mark.unit
def test_standard_mode_deep_embedment_raises_calc_error() -> None:
    with pytest.raises(CalcError, match=r"q'"):
        run(EdometricoInput(**{**_BASE, "d": 10.0, "legacy_compat": False}))


@pytest.mark.unit
def test_legacy_mode_sigma_v0_stays_frozen_regardless_of_the_water_table_field() -> None:
    """`legacy_compat=True` must reproduce the sheet's own formula byte-for-byte, ignoring both
    the new `falda` input and the embedment, exactly as before this fix."""
    strato_ampio = {"z_top_m": 0.0, "z_bot_m": 50.0, "modulo_MPa": 7.0}
    report = run(EdometricoInput(**{**_BASE, "d": 1.5, "falda": 1.0, "strati": [strato_ampio], "legacy_compat": True}))
    assert report.ok
    riga_5m = next(r for r in report.data.righe if r.z_m == pytest.approx(5.0))
    assert riga_5m.sigma_v0_kPa == pytest.approx(18.0 * 5.0 - 9.80665 * 5.0, rel=1e-6)
