"""Contract tests: identical behaviour required from both ProjectRepository implementations."""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from strutture.storage.interfaces import ConflictError, NotFoundError
from strutture.storage.models import MAX_NOME, MAX_NOTA, MAX_NOTE, MAX_SIGLA, Elemento, Progetto
from strutture.storage.progetti_memory import InMemoryProjectRepository
from strutture.storage.progetti_sqlite import open_project_repository

ISO_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


@pytest.fixture(params=["memory", "sqlite"])
def repository(request, tmp_path):
    if request.param == "memory":
        return InMemoryProjectRepository()
    return open_project_repository(tmp_path)


def _progetto(**overrides) -> Progetto:
    data = {"codice": "J-1", "nome": "Palazzina A", "committente": "Comune", "note": "prova"}
    data.update(overrides)
    return Progetto(**data)


def _elemento(progetto_id: str, **overrides) -> Elemento:
    data = {"progetto_id": progetto_id, "strumento": "plinto", "nome": "Plinto P1",
            "inputs": {"b_mm": 500}, "sintesi": {"ok": True}}
    data.update(overrides)
    return Elemento(**data)


# ---- progetti: CRUD ----

@pytest.mark.unit
def test_crea_progetto_assigns_id_and_timestamps(repository):
    created = repository.crea_progetto(_progetto())
    assert created.id
    assert created.revisione == 1
    assert ISO_RE.match(created.creato)
    assert ISO_RE.match(created.aggiornato)
    assert created.eliminato == ""


@pytest.mark.unit
def test_get_progetto_roundtrip(repository):
    created = repository.crea_progetto(_progetto())
    assert repository.get_progetto(created.id) == created


@pytest.mark.unit
def test_get_unknown_progetto_raises(repository):
    with pytest.raises(NotFoundError):
        repository.get_progetto("nope")


@pytest.mark.unit
def test_list_progetti_excludes_deleted_by_default(repository):
    keep = repository.crea_progetto(_progetto(nome="Vivo"))
    gone = repository.crea_progetto(_progetto(nome="Morto"))
    repository.elimina_progetto(gone.id, gone.revisione)
    listed = repository.list_progetti()
    ids = {p.id for p in listed}
    assert keep.id in ids
    assert gone.id not in ids
    assert gone.id in {p.id for p in repository.list_progetti(inclusi_eliminati=True)}


@pytest.mark.unit
def test_aggiorna_progetto_updates_fields_and_bumps_revisione(repository):
    created = repository.crea_progetto(_progetto())
    updated = repository.aggiorna_progetto(created.model_copy(update={"nome": "Palazzina B"}))
    assert updated.nome == "Palazzina B"
    assert updated.revisione == created.revisione + 1
    assert updated.creato == created.creato
    assert updated.aggiornato != "" and updated.aggiornato >= created.aggiornato


@pytest.mark.unit
def test_aggiorna_progetto_stale_revisione_conflicts(repository):
    created = repository.crea_progetto(_progetto())
    repository.aggiorna_progetto(created.model_copy(update={"nome": "Prima modifica"}))
    with pytest.raises(ConflictError):
        repository.aggiorna_progetto(created.model_copy(update={"nome": "Modifica in conflitto"}))


@pytest.mark.unit
def test_elimina_progetto_soft_deletes(repository):
    created = repository.crea_progetto(_progetto())
    repository.elimina_progetto(created.id, created.revisione)
    fetched = repository.get_progetto(created.id)
    assert fetched.eliminato != ""


@pytest.mark.unit
def test_elimina_progetto_stale_revisione_conflicts(repository):
    created = repository.crea_progetto(_progetto())
    with pytest.raises(ConflictError):
        repository.elimina_progetto(created.id, created.revisione + 1)


@pytest.mark.unit
def test_elimina_progetto_unknown_raises_not_found(repository):
    with pytest.raises(NotFoundError):
        repository.elimina_progetto("nope", 1)


@pytest.mark.unit
def test_ripristina_progetto_restores(repository):
    created = repository.crea_progetto(_progetto())
    repository.elimina_progetto(created.id, created.revisione)
    restored = repository.ripristina_progetto(created.id)
    assert restored.eliminato == ""
    assert repository.get_progetto(created.id).eliminato == ""


@pytest.mark.unit
def test_ripristina_unknown_progetto_raises(repository):
    with pytest.raises(NotFoundError):
        repository.ripristina_progetto("nope")


@pytest.mark.unit
def test_aggiorna_deleted_progetto_raises_not_found(repository):
    created = repository.crea_progetto(_progetto())
    repository.elimina_progetto(created.id, created.revisione)
    with pytest.raises(NotFoundError):
        repository.aggiorna_progetto(created.model_copy(update={"nome": "x"}))


# ---- elementi: CRUD, revisions, duplicate ----

@pytest.mark.unit
def test_crea_elemento_assigns_id_and_first_revision(repository):
    progetto = repository.crea_progetto(_progetto())
    created = repository.crea_elemento(_elemento(progetto.id), sigla="AB", nota="prima")
    assert created.id
    assert created.revisione == 1
    history = repository.revisioni(created.id)
    assert len(history) == 1
    assert history[0].revisione == 1
    assert history[0].sigla == "AB"
    assert history[0].nota == "prima"
    assert history[0].inputs == created.inputs


@pytest.mark.unit
def test_list_elementi_scoped_to_progetto_excludes_deleted(repository):
    progetto_a = repository.crea_progetto(_progetto(nome="A"))
    progetto_b = repository.crea_progetto(_progetto(nome="B"))
    keep = repository.crea_elemento(_elemento(progetto_a.id, nome="Vivo"))
    gone = repository.crea_elemento(_elemento(progetto_a.id, nome="Morto"))
    repository.crea_elemento(_elemento(progetto_b.id, nome="Altro progetto"))
    repository.elimina_elemento(gone.id, gone.revisione)

    listed = repository.list_elementi(progetto_a.id)
    ids = {e.id for e in listed}
    assert ids == {keep.id}


@pytest.mark.unit
def test_aggiorna_elemento_appends_revision_in_order(repository):
    progetto = repository.crea_progetto(_progetto())
    created = repository.crea_elemento(_elemento(progetto.id))
    updated = repository.aggiorna_elemento(
        created.model_copy(update={"inputs": {"b_mm": 600}}), sigla="CD", nota="seconda"
    )
    assert updated.revisione == 2
    history = repository.revisioni(created.id)
    assert [r.revisione for r in history] == [1, 2]
    assert history[1].inputs == {"b_mm": 600}
    assert history[1].sigla == "CD"


@pytest.mark.unit
def test_aggiorna_elemento_stale_revisione_conflicts(repository):
    progetto = repository.crea_progetto(_progetto())
    created = repository.crea_elemento(_elemento(progetto.id))
    repository.aggiorna_elemento(created.model_copy(update={"inputs": {"b_mm": 700}}))
    with pytest.raises(ConflictError):
        repository.aggiorna_elemento(created.model_copy(update={"inputs": {"b_mm": 800}}))


@pytest.mark.unit
def test_duplica_elemento_new_id_revision_one_given_name(repository):
    progetto = repository.crea_progetto(_progetto())
    created = repository.crea_elemento(_elemento(progetto.id))
    repository.aggiorna_elemento(created.model_copy(update={"inputs": {"b_mm": 900}}))
    duplicate = repository.duplica_elemento(created.id, "Plinto P1 (copia)")
    assert duplicate.id != created.id
    assert duplicate.revisione == 1
    assert duplicate.nome == "Plinto P1 (copia)"
    assert duplicate.inputs == {"b_mm": 900}
    assert len(repository.revisioni(duplicate.id)) == 1
    # original untouched
    assert repository.get_elemento(created.id).inputs == {"b_mm": 900}


@pytest.mark.unit
def test_duplica_unknown_elemento_raises(repository):
    with pytest.raises(NotFoundError):
        repository.duplica_elemento("nope", "copia")


@pytest.mark.unit
def test_elimina_elemento_soft_deletes(repository):
    progetto = repository.crea_progetto(_progetto())
    created = repository.crea_elemento(_elemento(progetto.id))
    repository.elimina_elemento(created.id, created.revisione)
    assert repository.get_elemento(created.id).eliminato != ""


@pytest.mark.unit
def test_revisioni_empty_for_unknown_elemento(repository):
    assert repository.revisioni("nope") == ()


# ---- unicode / max lengths ----

@pytest.mark.unit
def test_unicode_fields_roundtrip(repository):
    progetto = repository.crea_progetto(_progetto(nome="Àngelo Ω — φ", note="verificato λ, ρ e φ"))
    fetched = repository.get_progetto(progetto.id)
    assert fetched.nome == "Àngelo Ω — φ"
    assert "φ" in fetched.note


@pytest.mark.unit
def test_progetto_nome_max_length_rejected():
    with pytest.raises(ValidationError):
        _progetto(nome="x" * (MAX_NOME + 1))


@pytest.mark.unit
def test_progetto_note_max_length_boundary_accepted():
    progetto = _progetto(note="y" * MAX_NOTE)
    assert len(progetto.note) == MAX_NOTE


@pytest.mark.unit
def test_elemento_nome_max_length_rejected(repository):
    progetto = repository.crea_progetto(_progetto())
    with pytest.raises(ValidationError):
        _elemento(progetto.id, nome="x" * (MAX_NOME + 1))


@pytest.mark.unit
def test_revisione_sigla_nota_max_length_boundary(repository):
    progetto = repository.crea_progetto(_progetto())
    created = repository.crea_elemento(
        _elemento(progetto.id), sigla="s" * MAX_SIGLA, nota="n" * MAX_NOTA
    )
    history = repository.revisioni(created.id)
    assert len(history[0].sigla) == MAX_SIGLA
    assert len(history[0].nota) == MAX_NOTA


# ---- concurrency: exactly one writer wins per revision ----

@pytest.mark.unit
def test_eight_threads_update_same_element_exactly_one_wins_per_revision(repository):
    progetto = repository.crea_progetto(_progetto())
    created = repository.crea_elemento(_elemento(progetto.id))

    successes: list[int] = []
    lock_free_conflicts: list[int] = []

    def _attempt(thread_id: int) -> None:
        try:
            repository.aggiorna_elemento(created.model_copy(update={"inputs": {"b_mm": thread_id}}))
            successes.append(thread_id)
        except ConflictError:
            lock_free_conflicts.append(thread_id)

    with ThreadPoolExecutor(max_workers=8) as pool:
        list(pool.map(_attempt, range(8)))

    assert len(successes) == 1
    assert len(lock_free_conflicts) == 7
    final = repository.get_elemento(created.id)
    assert final.revisione == 2
    assert len(repository.revisioni(created.id)) == 2
