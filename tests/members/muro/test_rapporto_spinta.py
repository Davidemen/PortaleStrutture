"""Unit tests for the shared U/(V·(1+√(W/X))²) branch."""
import pytest

from strutture.members.muro.rapporto_spinta import rapporto_spinta

pytestmark = pytest.mark.unit


def test_rapporto_spinta_cuneo_valido_branch():
    assert rapporto_spinta(4.0, 2.0, 1.0, 1.0, cuneo_valido=True) == pytest.approx(4.0 / (2.0 * 4.0))


def test_rapporto_spinta_else_branch_ignores_w_x():
    assert rapporto_spinta(4.0, 2.0, 999.0, 0.0, cuneo_valido=False) == pytest.approx(2.0)
