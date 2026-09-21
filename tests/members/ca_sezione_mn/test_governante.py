"""`governante.py`: picks the max-`rapporto` row; an out-of-domain row (`rapporto=None`) always
wins the envelope (worse than any finite ratio)."""
import pytest

from strutture.members.ca_sezione_mn.models_output import RigaAzione

pytestmark = pytest.mark.unit


def _riga(nome: str, rapporto: float | None, dentro: bool = True) -> RigaAzione:
    return RigaAzione(
        nome=nome, n_ed_kN=100.0, m_ed_x_kNm=10.0, m_ed_y_kNm=0.0, tipo="uniassiale x",
        mx_rd_kNm=20.0 if rapporto is not None else None, my_rd_kNm=None, rapporto=rapporto, dentro=dentro,
    )


def test_riga_con_rapporto_massimo_vince() -> None:
    from strutture.members.ca_sezione_mn.governante import riga_governante

    righe = (_riga("A", 0.3), _riga("B", 0.9), _riga("C", 0.5))
    assert riga_governante(righe).nome == "B"


def test_riga_fuori_dominio_vince_sempre() -> None:
    from strutture.members.ca_sezione_mn.governante import riga_governante

    righe = (_riga("A", 0.99), _riga("B", None, dentro=False), _riga("C", 0.5))
    assert riga_governante(righe).nome == "B"


def test_singola_riga() -> None:
    from strutture.members.ca_sezione_mn.governante import riga_governante

    righe = (_riga("Unica", 0.4),)
    assert riga_governante(righe).nome == "Unica"


def test_indice_governante_coincide_con_la_riga_governante() -> None:
    from strutture.members.ca_sezione_mn.governante import indice_governante, riga_governante

    righe = (_riga("A", 0.3), _riga("B", 0.9), _riga("C", 0.5))
    assert righe[indice_governante(righe)] == riga_governante(righe)


def test_indice_governante_fuori_dominio_vince_sempre() -> None:
    from strutture.members.ca_sezione_mn.governante import indice_governante

    righe = (_riga("A", 0.99), _riga("B", None, dentro=False), _riga("C", 0.5))
    assert indice_governante(righe) == 1
