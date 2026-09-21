"""Unit tests for the rectangular-section geometry helpers."""
import math

import pytest

from strutture.foundations.travi_collegamento.geometria import altezza_utile_mm, raggio_inerzia_debole_mm


@pytest.mark.unit
def test_raggio_inerzia_square_section() -> None:
    assert raggio_inerzia_debole_mm(400, 400) == pytest.approx(115.470, rel=1e-5)


@pytest.mark.unit
def test_raggio_inerzia_symmetric_in_b_h() -> None:
    assert raggio_inerzia_debole_mm(300, 500) == pytest.approx(raggio_inerzia_debole_mm(500, 300))


@pytest.mark.unit
def test_raggio_inerzia_matches_min_over_sqrt12() -> None:
    # For b << h, i tends to b/sqrt(12).
    assert raggio_inerzia_debole_mm(100, 100000) == pytest.approx(100 / math.sqrt(12), rel=1e-3)


@pytest.mark.unit
def test_altezza_utile() -> None:
    assert altezza_utile_mm(400, 40) == 360
