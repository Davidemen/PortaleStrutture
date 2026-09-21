"""Merge logic unit tests: per-column provenance rule from architecture.md §3, C3."""
import pytest

from strutture.shared.comuni.merge import SourceRow, merge_rows

pytestmark = pytest.mark.unit

BREMBATE_SISMA = SourceRow("Lombardia", "Bergamo", "3016037", "Brembate", "4", "1", "I (alpina)")
BREMBATE_VENTO = SourceRow("Lombardia", "Bergamo", "3016037", "Brembate", "4", "1", "I (alpina)")
BREMBATE_NEVE = SourceRow("Lombardia", "Bergamo", "3016037", "Brembate", "4", "1", "I (alpina)")


def test_merge_clean_row_uses_sisma_columns_and_neve_provincia_neve():
    result = merge_rows((BREMBATE_SISMA,), (BREMBATE_VENTO,), (BREMBATE_NEVE,))
    assert result.conflicts == ()
    assert result.rows == (
        {
            "regione": "Lombardia", "provincia": "Bergamo", "istat": "3016037", "comune": "Brembate",
            "zona_sismica": "4", "zona_vento": "1", "zona_neve": "I (alpina)",
        },
    )


def test_merge_takes_provincia_and_neve_zone_from_neve_snapshot():
    sisma = SourceRow("Lombardia", "Monza", "3015003", "Agrate Brianza", "4", "1", "I (mediterranea)")
    vento = SourceRow("Lombardia", "Monza", "3015003", "Agrate Brianza", "4", "1", "I (mediterranea)")
    neve = SourceRow("Lombardia", "Monza e Brianza", "3015003", "Agrate Brianza", "4", "1", "II")

    result = merge_rows((sisma,), (vento,), (neve,))

    assert result.conflicts == ()
    assert result.rows[0]["provincia"] == "Monza e Brianza"
    assert result.rows[0]["zona_neve"] == "II"


def test_merge_ignores_invalid_vento_literal_in_neve_snapshot():
    """The neve copy holds the corrupt literal 56 in the Vento column; the merge must never use it."""
    sisma = SourceRow("Sardegna", "Cagliari", "20092001", "Arbus", "4", "3", "III")
    vento = SourceRow("Sardegna", "Cagliari", "20092001", "Arbus", "4", "3", "III")
    neve = SourceRow("Sardegna", "Cagliari", "20092001", "Arbus", "4", "56", "III")

    result = merge_rows((sisma,), (vento,), (neve,))

    assert result.conflicts == ()
    assert result.rows[0]["zona_vento"] == "3"


def test_merge_fills_blank_sisma_neve_zone_from_neve_snapshot():
    sisma = SourceRow("Lombardia", "Como", "3013130", "Livo", "4", "1", "")
    vento = SourceRow("Lombardia", "Como", "3013130", "Livo", "4", "1", "")
    neve = SourceRow("Lombardia", "Como", "3013130", "Livo", "4", "1", "I (alpina)")

    result = merge_rows((sisma,), (vento,), (neve,))

    assert result.conflicts == ()
    assert result.rows[0]["zona_neve"] == "I (alpina)"


def test_merge_flags_shared_column_disagreement_between_sisma_and_vento():
    sisma = BREMBATE_SISMA
    vento = SourceRow("Lombardia", "Bergamo", "3016037", "Brembate", "4", "2", "I (alpina)")  # Vento differs

    result = merge_rows((sisma,), (vento,), (BREMBATE_NEVE,))

    assert result.rows == ()
    assert len(result.conflicts) == 1
    assert "3016037" in result.conflicts[0]
    assert "vento" in result.conflicts[0]


def test_merge_flags_comune_missing_from_one_source():
    result = merge_rows((BREMBATE_SISMA,), (), (BREMBATE_NEVE,))

    assert result.rows == ()
    assert len(result.conflicts) == 1
    assert "missing from vento" in result.conflicts[0]


def test_merge_flags_comune_missing_from_neve():
    result = merge_rows((BREMBATE_SISMA,), (BREMBATE_VENTO,), ())

    assert result.rows == ()
    assert len(result.conflicts) == 1
    assert "missing from neve" in result.conflicts[0]
