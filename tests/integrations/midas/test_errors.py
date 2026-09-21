"""MidasError.status_code mapping and redact() edge cases."""
import pytest

from strutture.integrations.midas import MidasError, redact


@pytest.mark.unit
@pytest.mark.parametrize(
    ("kind", "status"),
    [("forbidden_url", 400), ("auth", 401), ("bad_response", 502), ("not_connected", 502), ("timeout", 504)],
)
def test_status_code_mapping(kind: str, status: int) -> None:
    assert MidasError(kind, "x").status_code == status


@pytest.mark.unit
def test_redact_replaces_every_occurrence() -> None:
    assert redact("key=SECRET, again SECRET", "SECRET") == "key=***, again ***"


@pytest.mark.unit
@pytest.mark.parametrize("key", [None, ""])
def test_redact_is_a_noop_without_a_key(key: str | None) -> None:
    assert redact("nothing to redact here", key) == "nothing to redact here"
