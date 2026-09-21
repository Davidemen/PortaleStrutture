"""Near an axial extreme, or with asymmetric reinforcement, the M interval of the domain at `N_Ed`
need not contain M = 0. Found by the engineering review of `ca-sezione-dominio-mn`: picking
`M_Rd+`/`M_Rd-` by the SIGN of `M_Ed` and dividing declared points OUTSIDE the domain as verified."""
import math

import pytest

from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.sezione_ca import forme
from strutture.shared.sezione_ca.domini import intervallo_n, m_rd
from strutture.shared.sezione_ca.modelli import MaterialiSezione, Sezione
from strutture.shared.sezione_ca.verifica import rapporto_uniassiale, verifica

pytestmark = pytest.mark.unit


def _sezione_asimmetrica() -> Sezione:
    materiali = MaterialiSezione(calcestruzzo=concrete_properties("C25/30"), acciaio=rebar_properties("B450C"))
    contorno = forme.rettangolo(300.0, 500.0)
    barre = (*forme.fila_superiore(300.0, 500.0, 30.0, 4, 20.0), *forme.fila_inferiore(300.0, 500.0, 30.0, 2, 20.0))
    return Sezione(contorno=contorno, barre=barre, materiali=materiali)


def test_interval_containing_zero_keeps_the_classic_ratio_along_the_ray_from_the_origin() -> None:
    assert rapporto_uniassiale(150.0, 200.0, -100.0) == pytest.approx(0.75)
    assert rapporto_uniassiale(-50.0, 200.0, -100.0) == pytest.approx(0.5)
    assert rapporto_uniassiale(0.0, 200.0, -100.0) == 0.0


def test_interval_excluding_zero_measures_from_its_centre_so_that_one_means_the_boundary() -> None:
    assert rapporto_uniassiale(20.0, 56.9, 42.5) > 1.0            # below the lower bound: outside
    assert rapporto_uniassiale(60.0, 56.9, 42.5) > 1.0            # above the upper bound: outside
    assert rapporto_uniassiale(49.7, 56.9, 42.5) == pytest.approx(0.0, abs=1e-9)
    assert rapporto_uniassiale(56.9, 56.9, 42.5) == pytest.approx(1.0)
    assert rapporto_uniassiale(0.0, 56.9, 42.5) > 1.0             # "no moment" is NOT safe here


def test_degenerate_interval() -> None:
    assert rapporto_uniassiale(10.0, 10.0, 10.0) == 0.0
    assert math.isinf(rapporto_uniassiale(11.0, 10.0, 10.0))


def test_a_point_below_the_lower_bound_is_outside_the_domain() -> None:
    sezione = _sezione_asimmetrica()
    n_min, n_max = intervallo_n(sezione)
    n_ed_kN = n_min + (n_max - n_min) * 0.99
    _m_pos, m_neg = m_rd(sezione, n_ed_kN, "x")
    assert m_neg > 0.0  # precondition: at this N the domain does not contain M = 0

    assert verifica(sezione, n_ed_kN, 20.0, 0.0).dentro is False
    assert verifica(sezione, n_ed_kN, 0.0, 0.0).dentro is False
    inside = verifica(sezione, n_ed_kN, (_m_pos + m_neg) / 2.0, 0.0)
    assert inside.dentro is True and inside.rapporto == pytest.approx(0.0, abs=1e-6)


def test_biaxial_request_where_the_origin_is_outside_the_domain_is_never_declared_inside() -> None:
    sezione = _sezione_asimmetrica()
    n_min, n_max = intervallo_n(sezione)
    esito = verifica(sezione, n_min + (n_max - n_min) * 0.99, 5.0, 5.0)
    assert esito.dentro is False and math.isinf(esito.rapporto)
