"""Minimum flexural reinforcement of the wall (NTC2018 §4.1.6.1.1 / EN 1992-1-1 §9.2.1.1): the
sheet sized the bars on the flexural requirement alone — the engineering proof-read of the
calculation report found the stem asking for 1,55 cm²/m against a code minimum of ≈6,4 cm²/m."""
import math

import pytest

from strutture.members.muro.armatura_minima import area_disposta_cm2_m, as_min_cm2_m, as_progetto_cm2_m
from strutture.members.muro.models import MuroSostegnoInput
from strutture.members.muro.tool import ESEMPIO_TRATTO_A, run_muro_sostegno

pytestmark = pytest.mark.unit


def test_as_min_is_the_ntc_envelope_per_metre():
    # C25/30: f_ctm = 0,30·25^(2/3) = 2,565 MPa; B450C f_yk = 450; d = 430 mm, b = 1000 mm
    atteso_mm2 = max(0.26 * 2.5649 / 450.0 * 1000.0 * 430.0, 0.0013 * 1000.0 * 430.0)
    assert as_min_cm2_m(fctm_MPa=2.5649, fyk_MPa=450.0, d_m=0.43) == pytest.approx(atteso_mm2 / 100.0, rel=1e-6)
    assert as_min_cm2_m(fctm_MPa=2.5649, fyk_MPa=450.0, d_m=0.43) == pytest.approx(6.373, rel=1e-3)


def test_the_0013_floor_governs_for_high_strength_steel_or_weak_concrete():
    assert as_min_cm2_m(fctm_MPa=1.0, fyk_MPa=450.0, d_m=0.43) == pytest.approx(0.0013 * 1000.0 * 430.0 / 100.0)


def test_as_progetto_is_the_larger_of_required_and_minimum_in_standard_mode_only():
    assert as_progetto_cm2_m(1.55, 6.37, legacy_compat=False) == pytest.approx(6.37)
    assert as_progetto_cm2_m(8.0, 6.37, legacy_compat=False) == pytest.approx(8.0)
    assert as_progetto_cm2_m(1.55, 6.37, legacy_compat=True) == pytest.approx(1.55)  # the sheet: no minimum


def test_area_disposta_per_metre():
    assert area_disposta_cm2_m(diametro_mm=12.0, passo_m=0.20) == pytest.approx(math.pi * 36.0 / 0.20 / 100.0)


def test_the_example_stem_is_sized_on_the_minimum_and_the_three_checks_exist():
    standard = run_muro_sostegno(MuroSostegnoInput(**ESEMPIO_TRATTO_A, legacy_compat=False))
    excel = run_muro_sostegno(MuroSostegnoInput(**ESEMPIO_TRATTO_A, legacy_compat=True))
    par = standard.data.armatura_paramento
    assert par.as_min_cm2_m > par.as_nec_cm2_m
    assert par.as_progetto_cm2_m == pytest.approx(par.as_min_cm2_m)
    assert par.diametro_mm >= excel.data.armatura_paramento.diametro_mm
    assert excel.data.armatura_paramento.as_progetto_cm2_m == pytest.approx(excel.data.armatura_paramento.as_nec_cm2_m)
    nomi = {c.name: c for c in standard.checks}
    for nome in ("Armatura minima paramento", "Armatura minima mancia", "Armatura minima tacco"):
        assert nome in nomi and nomi[nome].passed, nome
        assert nomi[nome].clause == "NTC2018 §4.1.6.1.1"
    # in Excel mode the bars are chosen without the minimum: the same check reports it honestly
    nomi_excel = {c.name: c for c in excel.checks}
    assert nomi_excel["Armatura minima paramento"].passed is False
