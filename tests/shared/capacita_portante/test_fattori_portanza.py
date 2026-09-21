"""Nq, Nc, Nγ against PUBLISHED EN 1997-1 Annex D table values (not a copy of the module's own
formula, per the MEDIUM finding on this file: a helper that re-transcribes the exact expression
under test proves only that it was copied twice, not that it is correct). Reference: R. Frank
et al., "Designers' Guide to EN 1997-1", Table 9 (Nq, Nc, Nγ computed from EN 1997-1 Annex D
eq. D.4-D.6, Nγ = 2(Nq-1)tanφ' — the same rough-base Nγ form specified by Annex D.4, distinct
from Vesic's 1.5(Nq-1)tanφ' used elsewhere in the literature); cross-checked to 4-5 significant
figures against the standard tan²(45°+φ'/2) (not tan²(45°-φ'/2), which would instead give the
*passive* earth-pressure-style coefficients and much smaller Nq) closed form.
"""
import math

import pytest

from strutture.shared.capacita_portante.fattori_portanza import fattori_portanza

pytestmark = pytest.mark.unit

# phi' [deg]: (Nq, Nc, Ngamma), EN 1997-1 Annex D.4 rough-base values.
_ANNEX_D4_TABLE = {
    20.0: (6.400, 14.835, 3.930),
    25.0: (10.662, 20.721, 9.011),
    30.0: (18.401, 30.140, 20.093),
    35.0: (33.296, 46.124, 45.228),
    40.0: (64.195, 75.313, 106.054),
}


@pytest.mark.parametrize("phi_deg", sorted(_ANNEX_D4_TABLE))
def test_matches_published_annex_d4_table_values(phi_deg):
    nq_atteso, nc_atteso, ngamma_atteso = _ANNEX_D4_TABLE[phi_deg]
    fattori = fattori_portanza(phi_deg)
    assert fattori.nq == pytest.approx(nq_atteso, rel=1e-3)
    assert fattori.nc == pytest.approx(nc_atteso, rel=1e-3)
    assert fattori.ngamma == pytest.approx(ngamma_atteso, rel=1e-3)


def test_phi_zero_limit_gives_the_undrained_nc_pi_plus_2():
    # lim(phi->0) Nc = lim (Nq(phi)-1)/tan(phi) = (dNq/dphi at 0)/(d tan(phi)/dphi at 0) = (pi+2)/1, l'Hopital.
    fattori = fattori_portanza(0.0)
    assert fattori.nq == pytest.approx(1.0)
    assert fattori.nc == pytest.approx(math.pi + 2.0)
    assert fattori.ngamma == pytest.approx(0.0)


def test_small_phi_is_continuous_with_the_phi_zero_limit():
    # At phi'=0.01 deg the table's phi=20 deg row is far away; use the pi+2 limit itself as the
    # independent check (matches this module's own docstring derivation, not its formula).
    fattori = fattori_portanza(0.01)
    assert fattori.nc == pytest.approx(math.pi + 2.0, abs=0.01)


def test_negative_phi_raises_value_error():
    with pytest.raises(ValueError):
        fattori_portanza(-5.0)


def test_factors_increase_monotonically_with_phi():
    valori = [fattori_portanza(phi) for phi in (10.0, 20.0, 30.0, 40.0)]
    assert [v.nq for v in valori] == sorted(v.nq for v in valori)
    assert [v.nc for v in valori] == sorted(v.nc for v in valori)
    assert [v.ngamma for v in valori] == sorted(v.ngamma for v in valori)
