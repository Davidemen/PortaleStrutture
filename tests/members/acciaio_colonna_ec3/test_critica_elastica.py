"""critica_elastica.py — Ncr,y/Ncr,z/Ncr,T (column-check!Y21, Y22, AV38)."""
import math

import pytest

from strutture.members.acciaio_colonna_ec3.critica_elastica import ncr_flessionale_kN, ncr_torsionale_kN


@pytest.mark.unit
def test_ncr_flessionale() -> None:
    e_MPa, iyy_mm4, lcr_mm = 206000.0, 4.72063e8, 16485.6
    atteso = (math.pi**2 * e_MPa * iyy_mm4 / lcr_mm**2) / 1000.0
    assert ncr_flessionale_kN(e_MPa, iyy_mm4, lcr_mm) == pytest.approx(atteso)
    assert ncr_flessionale_kN(e_MPa, iyy_mm4, lcr_mm) == pytest.approx(3531.51, rel=1e-4)


@pytest.mark.unit
def test_ncr_torsionale() -> None:
    valore = ncr_torsionale_kN(g_MPa=79230.8, it_mm4=4.05255e5, e_MPa=206000.0, iw_mm6=2.6151e12, lt_mm=1800.0, i0_quadro_mm2=48756.7)
    assert valore == pytest.approx(34315.3, rel=1e-3)
