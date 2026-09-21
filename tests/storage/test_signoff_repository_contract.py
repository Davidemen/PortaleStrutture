"""Contract tests: identical behaviour required from both SignoffRepository implementations."""
from __future__ import annotations

import re

import pytest
from pydantic import ValidationError

from strutture.storage.memory import InMemorySignoffRepository
from strutture.storage.models import MAX_NOTA, MAX_SIGLA
from strutture.storage.signoff_sqlite import open_signoff_repository


@pytest.fixture(params=["memory", "sqlite"])
def repository(request, tmp_path):
    if request.param == "memory":
        return InMemorySignoffRepository()
    return open_signoff_repository(tmp_path)


@pytest.mark.unit
def test_get_undecided_returns_default(repository):
    result = repository.get("muro/divergenza-1")
    assert result.divergence_id == "muro/divergenza-1"
    assert result.stato == "da_confermare"
    assert result.sigla == ""
    assert result.nota == ""


@pytest.mark.unit
def test_set_then_get_roundtrip(repository):
    stored = repository.set("muro/d1", "approvato", "AB", nota="ok")
    assert stored.stato == "approvato"
    assert stored.sigla == "AB"
    assert stored.nota == "ok"
    assert stored.data
    assert repository.get("muro/d1") == stored


@pytest.mark.unit
def test_set_overwrites_current_value(repository):
    repository.set("muro/d1b", "da_confermare", "AB")
    updated = repository.set("muro/d1b", "approvato", "CD", nota="motivato")
    assert repository.get("muro/d1b") == updated
    assert repository.get("muro/d1b").sigla == "CD"


@pytest.mark.unit
def test_history_oldest_first(repository):
    repository.set("muro/d2", "da_confermare", "AB")
    repository.set("muro/d2", "approvato", "AB")
    repository.set("muro/d2", "respinto", "CD", nota="motivo")
    history = repository.history("muro/d2")
    assert [h.stato for h in history] == ["da_confermare", "approvato", "respinto"]
    assert history[-1].nota == "motivo"


@pytest.mark.unit
def test_history_empty_for_undecided(repository):
    assert repository.history("muro/mai-deciso") == ()


@pytest.mark.unit
def test_list_all_only_decided(repository):
    repository.set("muro/d3", "approvato", "AB")
    listed = repository.list_all()
    assert listed["muro/d3"].stato == "approvato"
    assert "muro/never-decided" not in listed


@pytest.mark.unit
def test_invalid_stato_rejected(repository):
    with pytest.raises(ValidationError):
        repository.set("muro/d4", "invalid_status", "AB")


@pytest.mark.unit
def test_unicode_sigla_and_nota(repository):
    repository.set("muro/d5", "approvato", "Àngelo Ω", nota="verificato λ, ρ e φ — più chiaro così")
    fetched = repository.get("muro/d5")
    assert fetched.sigla == "Àngelo Ω"
    assert "φ" in fetched.nota
    assert "—" in fetched.nota


@pytest.mark.unit
def test_max_length_sigla_rejected(repository):
    with pytest.raises(ValidationError):
        repository.set("muro/d6", "approvato", "x" * (MAX_SIGLA + 1))


@pytest.mark.unit
def test_max_length_nota_rejected(repository):
    with pytest.raises(ValidationError):
        repository.set("muro/d7", "approvato", "AB", nota="y" * (MAX_NOTA + 1))


@pytest.mark.unit
def test_max_length_boundary_accepted(repository):
    stored = repository.set("muro/d7b", "approvato", "x" * MAX_SIGLA, nota="y" * MAX_NOTA)
    assert len(stored.sigla) == MAX_SIGLA
    assert len(stored.nota) == MAX_NOTA


@pytest.mark.unit
def test_data_is_iso8601_utc_seconds(repository):
    stored = repository.set("muro/d8", "approvato", "AB")
    assert re.match(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$", stored.data)
