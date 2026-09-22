"""Contract tests: identical behaviour required from both ImpostazioniRepository implementations."""
from __future__ import annotations

import json

import pytest

from strutture.shared.impostazioni.modelli import FABBRICA, Impostazioni
from strutture.storage.database import connect
from strutture.storage.impostazioni_memory import InMemoryImpostazioniRepository
from strutture.storage.impostazioni_sqlite import open_impostazioni_repository
from strutture.storage.interfaces import ConflictError


@pytest.fixture(params=["memory", "sqlite"])
def repository(request, tmp_path):
    if request.param == "memory":
        return InMemoryImpostazioniRepository()
    return open_impostazioni_repository(tmp_path)


@pytest.mark.unit
def test_empty_database_gives_factory_at_revision_0(repository):
    salvate = repository.leggi()
    assert salvate.valori == FABBRICA
    assert salvate.revisione == 0
    assert salvate.sigla == ""


@pytest.mark.unit
def test_save_increments_revision_and_appends_history(repository):
    saved = repository.salva(Impostazioni(obiettivo_sfruttamento=0.9), 0, "AB")
    assert saved.revisione == 1
    assert repository.leggi() == saved
    saved2 = repository.salva(Impostazioni(obiettivo_sfruttamento=0.8), 1, "CD")
    assert saved2.revisione == 2
    storia = repository.storia()
    assert [s.revisione for s in storia] == [2, 1]


@pytest.mark.unit
def test_stale_revision_raises_conflict_and_writes_nothing(repository):
    repository.salva(Impostazioni(obiettivo_sfruttamento=0.9), 0, "AB")
    with pytest.raises(ConflictError):
        repository.salva(Impostazioni(obiettivo_sfruttamento=0.5), 0, "CD")
    assert repository.leggi().valori.obiettivo_sfruttamento == 0.9


@pytest.mark.unit
def test_history_limit(repository):
    for revisione in range(3):
        repository.salva(Impostazioni(obiettivo_sfruttamento=1.0), revisione, "AB")
    assert len(repository.storia(limite=2)) == 2


@pytest.mark.unit
def test_corrupted_valori_falls_back_to_factory_merge(tmp_path):
    repository = open_impostazioni_repository(tmp_path)
    repository.salva(Impostazioni(obiettivo_sfruttamento=0.9), 0, "AB")
    connection = connect(tmp_path / "strutture.db")
    try:
        connection.execute(
            "UPDATE impostazioni SET valori = ? WHERE id = 1",
            (json.dumps({"obiettivo_sfruttamento": 0.9, "obiettivo_su_verifiche_minimo": "non un booleano"}),),
        )
        connection.commit()
    finally:
        connection.close()

    salvate, avvisi = repository.leggi_con_avvisi()
    assert salvate.valori.obiettivo_sfruttamento == 0.9  # the field that still validates survives
    assert salvate.valori.obiettivo_su_verifiche_minimo is False  # the broken one falls back to factory
    assert avvisi and "obiettivo_su_verifiche_minimo" in avvisi[0]


@pytest.mark.unit
def test_garbage_valori_falls_back_entirely(tmp_path):
    repository = open_impostazioni_repository(tmp_path)
    repository.salva(Impostazioni(obiettivo_sfruttamento=0.9), 0, "AB")
    connection = connect(tmp_path / "strutture.db")
    try:
        connection.execute("UPDATE impostazioni SET valori = ? WHERE id = 1", ("questo non è json {{{",))
        connection.commit()
    finally:
        connection.close()

    salvate, avvisi = repository.leggi_con_avvisi()
    assert salvate.valori == FABBRICA
    assert avvisi
