"""bq, bγ, bc base-inclination factors (EN 1997-1 Annex D.2/D.3)."""
import math

import pytest

from strutture.shared.capacita_portante.fattori_base import (
    fattori_inclinazione_base,
    fattori_inclinazione_base_non_drenata,
)

pytestmark = pytest.mark.unit


def test_horizontal_base_gives_unit_factors():
    fattori = fattori_inclinazione_base(0.0, 30.0, 30.14)
    assert fattori.bq == pytest.approx(1.0)
    assert fattori.bgamma == pytest.approx(1.0)
    assert fattori.bc == pytest.approx(1.0)


def test_inclined_base_hand_computed():
    alpha_deg, phi_deg, nc = 5.0, 30.0, 30.14
    alpha_rad, phi_rad = math.radians(alpha_deg), math.radians(phi_deg)
    fattori = fattori_inclinazione_base(alpha_deg, phi_deg, nc)
    bq_atteso = (1.0 - alpha_rad * math.tan(phi_rad)) ** 2
    assert fattori.bq == pytest.approx(bq_atteso)
    assert fattori.bgamma == pytest.approx(bq_atteso)
    assert fattori.bc == pytest.approx(bq_atteso - (1.0 - bq_atteso) / (nc * math.tan(phi_rad)))


def test_base_factors_never_increase_with_more_inclination():
    valori = [fattori_inclinazione_base(alpha, 30.0, 30.14) for alpha in (0.0, 5.0, 10.0, 15.0)]
    assert [v.bq for v in valori] == sorted((v.bq for v in valori), reverse=True)
    assert [v.bc for v in valori] == sorted((v.bc for v in valori), reverse=True)


def test_phi_zero_drained_raises_value_error():
    with pytest.raises(ValueError):
        fattori_inclinazione_base(5.0, 0.0, 5.14)


def test_undrained_horizontal_base_is_one():
    fattori = fattori_inclinazione_base_non_drenata(0.0)
    assert fattori.bq == pytest.approx(1.0)
    assert fattori.bc == pytest.approx(1.0)


def test_undrained_inclined_base_hand_computed():
    alpha_deg = 10.0
    atteso = 1.0 - 2.0 * math.radians(alpha_deg) / (math.pi + 2.0)
    fattori = fattori_inclinazione_base_non_drenata(alpha_deg)
    assert fattori.bc == pytest.approx(atteso)


def test_invalid_alpha_raises_value_error():
    with pytest.raises(ValueError):
        fattori_inclinazione_base(95.0, 30.0, 30.14)


def test_undrained_invalid_alpha_raises_value_error():
    with pytest.raises(ValueError):
        fattori_inclinazione_base_non_drenata(-95.0)


def test_negative_alpha_uses_magnitude_and_never_increases_bq_above_one():
    """MEDIUM finding: alpha_deg=-10, phi'=30 must give the SAME bq as alpha_deg=+10 (Annex D.4's
    alpha is the magnitude of the base inclination; a negative sign is a direction, not a
    capacity increase). Hand-derived: alpha_rad=|radians(-10)|=0.174533, tan(30 deg)=0.577350,
    bq=(1-0.174533*0.577350)^2=(1-0.100798)^2=0.899202^2=0.808565 <= 1 (satisfies the model's
    le=1 bound); the unfixed formula instead used the signed alpha_rad, giving
    bq=(1+0.100798)^2=1.211687 > 1, a pydantic ValidationError."""
    positivo = fattori_inclinazione_base(10.0, 30.0, 30.14)
    negativo = fattori_inclinazione_base(-10.0, 30.0, 30.14)
    assert negativo.bq == pytest.approx(positivo.bq)
    assert negativo.bc == pytest.approx(positivo.bc)
    assert negativo.bq <= 1.0


def test_undrained_negative_alpha_uses_magnitude():
    positivo = fattori_inclinazione_base_non_drenata(10.0)
    negativo = fattori_inclinazione_base_non_drenata(-10.0)
    assert negativo.bc == pytest.approx(positivo.bc)
    assert negativo.bc <= 1.0
