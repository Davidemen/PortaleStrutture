"""Concurrent writers must not corrupt data or crash: WAL + busy_timeout + a connection per operation."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pytest

from strutture.storage.signoff_sqlite import open_signoff_repository

THREAD_COUNT = 8
WRITES_PER_THREAD = 15


@pytest.mark.unit
def test_concurrent_writers_from_eight_threads(tmp_path):
    repository = open_signoff_repository(tmp_path)

    def _write(thread_id: int) -> None:
        for i in range(WRITES_PER_THREAD):
            repository.set(f"muro/d-{thread_id}", "approvato", f"T{thread_id}", nota=str(i))

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as pool:
        list(pool.map(_write, range(THREAD_COUNT)))

    for thread_id in range(THREAD_COUNT):
        record = repository.get(f"muro/d-{thread_id}")
        assert record.nota == str(WRITES_PER_THREAD - 1)
        history = repository.history(f"muro/d-{thread_id}")
        assert len(history) == WRITES_PER_THREAD


@pytest.mark.unit
def test_concurrent_writers_same_divergence(tmp_path):
    repository = open_signoff_repository(tmp_path)

    def _write(i: int) -> None:
        repository.set("muro/shared", "approvato", "AB", nota=str(i))

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as pool:
        list(pool.map(_write, range(THREAD_COUNT * WRITES_PER_THREAD)))

    history = repository.history("muro/shared")
    assert len(history) == THREAD_COUNT * WRITES_PER_THREAD
    current = repository.get("muro/shared")
    assert current == history[-1]
