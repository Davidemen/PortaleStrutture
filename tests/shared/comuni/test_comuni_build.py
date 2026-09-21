"""Integration tests for the build script: merge + validate + write, fail on conflicts."""
import csv
from pathlib import Path

import pytest

from strutture.shared.comuni.build import ComuniBuildError, build

pytestmark = pytest.mark.unit

FIXTURES = Path(__file__).resolve().parents[2] / "fixtures"


def test_build_writes_merged_csv(tmp_path):
    output = tmp_path / "comuni.csv"

    count = build(
        sisma_csv=FIXTURES / "comuni_build_sisma.csv",
        vento_csv=FIXTURES / "comuni_build_vento.csv",
        neve_csv=FIXTURES / "comuni_build_neve.csv",
        output_csv=output,
    )

    assert count == 5
    with output.open(newline="", encoding="utf-8") as handle:
        rows = {row["comune"]: row for row in csv.DictReader(handle)}
    assert rows["Agrate Brianza"]["provincia"] == "Monza e Brianza"  # neve provincia wins
    assert rows["Arbus"]["zona_vento"] == "3"  # sisma vento wins over neve's invalid 56
    assert rows["Livo"]["zona_neve"] == "I (alpina)"  # neve fills sisma's blank


def test_build_fails_on_unresolved_merge_conflict(tmp_path):
    with pytest.raises(ComuniBuildError, match="unresolved merge conflicts"):
        build(
            sisma_csv=FIXTURES / "comuni_conflict_sisma.csv",
            vento_csv=FIXTURES / "comuni_conflict_vento.csv",
            neve_csv=FIXTURES / "comuni_conflict_neve.csv",
            output_csv=tmp_path / "comuni.csv",
        )


def test_build_fails_on_validation_violation(tmp_path):
    with pytest.raises(ComuniBuildError, match="validation violations"):
        build(
            sisma_csv=FIXTURES / "comuni_invalid_sisma.csv",
            vento_csv=FIXTURES / "comuni_invalid_vento.csv",
            neve_csv=FIXTURES / "comuni_invalid_neve.csv",
            output_csv=tmp_path / "comuni.csv",
        )


def test_build_does_not_write_output_when_it_fails(tmp_path):
    output = tmp_path / "comuni.csv"
    with pytest.raises(ComuniBuildError):
        build(
            sisma_csv=FIXTURES / "comuni_conflict_sisma.csv",
            vento_csv=FIXTURES / "comuni_conflict_vento.csv",
            neve_csv=FIXTURES / "comuni_conflict_neve.csv",
            output_csv=output,
        )
    assert not output.exists()
