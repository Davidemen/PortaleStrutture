"""scambio.py: pure export/import — round trip, unknown tools flagged, malformed payloads rejected."""
from __future__ import annotations

import pytest

from strutture.storage.models import Elemento, Progetto
from strutture.storage.progetti_memory import InMemoryProjectRepository
from strutture.storage.scambio import FORMATO, VERSIONE_FORMATO, FormatoNonValido, esporta, importa

STRUMENTI_NOTI = frozenset({"plinto", "trave"})


def _repository_con_progetto() -> tuple[InMemoryProjectRepository, Progetto, Elemento]:
    repository = InMemoryProjectRepository()
    progetto = repository.crea_progetto(
        Progetto(codice="J-1", nome="Palazzina A", committente="Comune", note="prova")
    )
    elemento = repository.crea_elemento(
        Elemento(progetto_id=progetto.id, strumento="plinto", nome="Plinto P1",
                 inputs={"b_mm": 500}, sintesi={"ok": True}, stato="verificato"),
        sigla="AB", nota="prima",
    )
    return repository, progetto, elemento


@pytest.mark.unit
def test_esporta_produces_documented_envelope():
    repository, progetto, elemento = _repository_con_progetto()
    payload = esporta(progetto, [(elemento, repository.revisioni(elemento.id))], versione_app="1.2.3")

    assert payload["formato"] == FORMATO
    assert payload["versione"] == VERSIONE_FORMATO
    assert payload["app"] == "1.2.3"
    assert payload["progetto"]["nome"] == "Palazzina A"
    assert payload["elementi"][0]["strumento"] == "plinto"
    assert payload["elementi"][0]["revisioni"][0]["sigla"] == "AB"


@pytest.mark.unit
def test_importa_creates_new_ids_never_overwrites():
    source_repo, progetto, elemento = _repository_con_progetto()
    payload = esporta(progetto, [(elemento, source_repo.revisioni(elemento.id))], versione_app="1.0")

    target_repo = InMemoryProjectRepository()
    imported, avvisi = importa(payload, target_repo, STRUMENTI_NOTI)

    assert imported.id != progetto.id
    assert imported.nome == "Palazzina A"
    assert avvisi == ()
    imported_elementi = target_repo.list_elementi(imported.id)
    assert len(imported_elementi) == 1
    assert imported_elementi[0].id != elemento.id
    assert imported_elementi[0].inputs == {"b_mm": 500}


@pytest.mark.unit
def test_importa_flags_unknown_tool():
    source_repo, progetto, elemento = _repository_con_progetto()
    payload = esporta(progetto, [(elemento, source_repo.revisioni(elemento.id))], versione_app="1.0")
    payload["elementi"][0]["strumento"] = "strumento-non-esistente"

    target_repo = InMemoryProjectRepository()
    _, avvisi = importa(payload, target_repo, STRUMENTI_NOTI)

    assert len(avvisi) == 1
    assert "strumento-non-esistente" in avvisi[0]


@pytest.mark.unit
def test_importa_same_codice_and_nome_gets_suffixed_name():
    repository, progetto, _ = _repository_con_progetto()
    payload = {
        "formato": FORMATO, "versione": VERSIONE_FORMATO, "esportato": "2026-01-01T00:00:00Z", "app": "1.0",
        "progetto": {"codice": progetto.codice, "nome": progetto.nome, "committente": "", "note": ""},
        "elementi": [],
    }

    imported, _ = importa(payload, repository, STRUMENTI_NOTI)

    assert imported.id != progetto.id
    assert imported.nome != progetto.nome
    assert imported.nome.startswith(progetto.nome)
    assert "importato" in imported.nome


@pytest.mark.unit
def test_export_import_round_trip_equal_except_ids_and_timestamps():
    source_repo, progetto, elemento = _repository_con_progetto()
    payload = esporta(progetto, [(elemento, source_repo.revisioni(elemento.id))], versione_app="1.0")

    target_repo = InMemoryProjectRepository()
    imported, _ = importa(payload, target_repo, STRUMENTI_NOTI)

    assert imported.codice == progetto.codice
    assert imported.nome == progetto.nome
    assert imported.committente == progetto.committente
    assert imported.note == progetto.note

    original_elemento = source_repo.get_elemento(elemento.id)
    [imported_elemento] = target_repo.list_elementi(imported.id)
    assert imported_elemento.strumento == original_elemento.strumento
    assert imported_elemento.nome == original_elemento.nome
    assert imported_elemento.inputs == original_elemento.inputs
    assert imported_elemento.sintesi == original_elemento.sintesi
    assert imported_elemento.stato == original_elemento.stato


@pytest.mark.unit
@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"formato": "qualcos-altro", "versione": 1, "progetto": {"nome": "x"}, "elementi": []},
        {"formato": FORMATO, "versione": 99, "progetto": {"nome": "x"}, "elementi": []},
        {"formato": FORMATO, "versione": VERSIONE_FORMATO, "progetto": {}, "elementi": []},
        {"formato": FORMATO, "versione": VERSIONE_FORMATO, "progetto": {"nome": "x"}, "elementi": "non-una-lista"},
    ],
)
def test_importa_rejects_malformed_payloads(payload):
    repository = InMemoryProjectRepository()
    with pytest.raises(FormatoNonValido):
        importa(payload, repository, STRUMENTI_NOTI)
