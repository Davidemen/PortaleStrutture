"""No storage operation may ever create a file under src/ (data belongs under the data directory only)."""
from __future__ import annotations

from pathlib import Path

import pytest

from strutture.storage.database import PROJECT_ROOT
from strutture.storage.signoff_sqlite import open_signoff_repository

SRC_ROOT = PROJECT_ROOT / "src"


def _snapshot(root: Path) -> set[Path]:
    return set(root.rglob("*")) if root.exists() else set()


@pytest.mark.unit
def test_full_repository_flow_never_writes_under_src(tmp_path):
    before = _snapshot(SRC_ROOT)

    repository = open_signoff_repository(tmp_path)
    repository.set("muro/d1", "approvato", "AB", nota="prova")
    repository.get("muro/d1")
    repository.list_all()
    repository.history("muro/d1")

    after = _snapshot(SRC_ROOT)
    assert after == before
