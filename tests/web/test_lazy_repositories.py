"""The lazy SQLite wrappers in `web/app.py` must expose the SAME surface as the Protocols they
stand in for: the real server (`--data-dir`) goes through them, the test suite's in-memory
fakes do not, so a missing keyword only shows up in production as a 500."""
from __future__ import annotations

import inspect

import pytest

from strutture.storage.interfaces import ProjectRepository, SignoffRepository
from strutture.storage.models import Elemento, Progetto
from strutture.web.app import _LazySqliteProjectRepository, _LazySqliteSignoffRepository

pytestmark = pytest.mark.unit


def _public_methods(cls: type) -> dict[str, inspect.Signature]:
    return {name: inspect.signature(member) for name, member in inspect.getmembers(cls, inspect.isfunction)
            if not name.startswith("_")}


@pytest.mark.parametrize(("protocol", "wrapper"), [
    (ProjectRepository, _LazySqliteProjectRepository),
    (SignoffRepository, _LazySqliteSignoffRepository),
])
def test_lazy_wrapper_mirrors_the_protocol_signatures(protocol: type, wrapper: type) -> None:
    expected = _public_methods(protocol)
    actual = _public_methods(wrapper)
    assert set(expected) <= set(actual), f"missing on {wrapper.__name__}: {sorted(set(expected) - set(actual))}"
    for name, signature in expected.items():
        assert list(actual[name].parameters) == list(signature.parameters), name


def test_lazy_project_repository_lists_and_restores_deleted_elements(tmp_path) -> None:
    repository = _LazySqliteProjectRepository(tmp_path)
    progetto = repository.crea_progetto(Progetto(codice="J-1", nome="Palazzina A", committente="", note=""))
    elemento = repository.crea_elemento(Elemento(progetto_id=progetto.id, strumento="plinto", nome="P1",
                                                 inputs={"b_mm": 500}, sintesi={"ok": True}))
    repository.elimina_elemento(elemento.id, elemento.revisione)
    assert repository.list_elementi(progetto.id) == ()
    assert [e.id for e in repository.list_elementi(progetto.id, inclusi_eliminati=True)] == [elemento.id]
    restored = repository.ripristina_elemento(elemento.id)
    assert restored.eliminato == ""
    assert [e.id for e in repository.list_elementi(progetto.id)] == [elemento.id]
