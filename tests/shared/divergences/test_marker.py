"""`legacy()` returns the flag unchanged — except inside the two analysis contexts used by the
Excel comparison: `traccia()` records which ids a run consults, `solo()` makes exactly the given
ids take the spreadsheet path whatever the flag says (one correction at a time)."""
import threading

import pytest

from strutture.shared.divergences.marker import legacy, solo, traccia

pytestmark = pytest.mark.unit


def test_legacy_returns_the_flag_unchanged_by_default() -> None:
    assert legacy("demo/a", True) is True
    assert legacy("demo/a", False) is False


def test_traccia_collects_the_ids_consulted_with_the_flag_on() -> None:
    with traccia() as visti:
        legacy("demo/a", True)
        legacy("demo/b", True)
        legacy("demo/a", True)
        legacy("demo/spento", False)
    assert visti() == frozenset({"demo/a", "demo/b"})
    assert legacy("demo/c", True) is True  # nothing leaks out of the context


def test_solo_forces_only_the_given_ids_whatever_the_flag() -> None:
    with solo({"demo/a"}):
        assert legacy("demo/a", False) is True
        assert legacy("demo/b", True) is False
    assert legacy("demo/b", True) is True


def test_contexts_do_not_leak_across_threads() -> None:
    seen: list[bool] = []
    with solo({"demo/a"}):
        worker = threading.Thread(target=lambda: seen.append(legacy("demo/a", False)))
        worker.start()
        worker.join()
    assert seen == [False]


def test_a_failure_inside_the_context_still_restores_the_default() -> None:
    with pytest.raises(RuntimeError), solo({"demo/a"}):
        raise RuntimeError("boom")
    assert legacy("demo/a", False) is False
