"""The real register stays fully linked: every entry either owns a `legacy("<id>", …)` call in the
code, or declares how Excel mode relates to it (`ramo="condiviso"` / `"nessuno"` with a reason).
A new `if legacy_compat:` without a register id, or a new entry nobody links, fails here."""
import pytest

from strutture.shared.divergences.check import REPO_SRC, run_checks
from strutture.shared.divergences.loader import load_register
from strutture.shared.tool import discover

pytestmark = pytest.mark.unit


def test_the_register_is_fully_linked_in_strict_mode() -> None:
    report = run_checks(load_register(), discover(), REPO_SRC, strict=True)
    assert report.errors == ()


def test_every_entry_not_reproduced_in_excel_mode_says_why_in_italian() -> None:
    for divergence in load_register():
        if divergence.ramo != "codice":
            assert len(divergence.motivo_senza_ramo) >= 20, divergence.id
