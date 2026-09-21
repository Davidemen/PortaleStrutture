"""Register contract: id format, loader validation, the legacy() marker."""
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from strutture.shared.divergences import Divergence, legacy
from strutture.shared.divergences.loader import load_register, parse_file

pytestmark = pytest.mark.unit
VALID = {"id": "ca-pilastri/lambda-lim-unita", "titolo": "Snellezza limite senza conversione kN→N", "tipo": "errore_foglio",
         "strumenti": ["ca-pilastro-rettangolare"], "foglio": "λlim calcolata con NEd in kN", "corretto": "NEd convertito in N"}


def test_ids_are_unit_slash_slug() -> None:
    assert Divergence.model_validate(VALID).id == VALID["id"]
    for bad in ("Ca-Pilastri/x", "ca-pilastri", "ca pilastri/x", "ca-pilastri/x/y"):
        with pytest.raises(ValidationError):
            Divergence.model_validate({**VALID, "id": bad})


def test_file_ids_must_match_the_file_name(tmp_path: Path) -> None:
    (tmp_path / "ca-travi.json").write_text(json.dumps([VALID]), encoding="utf-8")
    with pytest.raises(ValueError, match="must start with 'ca-travi/'"):
        parse_file(tmp_path / "ca-travi.json")


def test_duplicate_ids_across_files_are_rejected(tmp_path: Path) -> None:
    (tmp_path / "ca-pilastri.json").write_text(json.dumps([VALID, VALID]), encoding="utf-8")
    load_register.cache_clear()
    with pytest.raises(ValueError, match="duplicate"):
        load_register(tmp_path)
    load_register.cache_clear()


def test_legacy_marker_returns_the_flag_unchanged() -> None:
    assert legacy("ca-pilastri/lambda-lim-unita", True) is True
    assert legacy("ca-pilastri/lambda-lim-unita", False) is False
