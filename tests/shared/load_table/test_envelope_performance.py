"""Envelope performance on the real MIDAS export (~13 800 cells, build/data/fond-plinti-pali).

`famiglia` is absent from this pile-cap export (§2 `reazioni` table: "pali: famiglia optional
(None -> one global envelope)"), so every row is loaded with famiglia=None and enveloped globally.
"""
import csv
import time
from pathlib import Path

import pytest

from strutture.shared.load_table import ReactionRow, envelope, governing

CSV_PATH = Path(__file__).parents[3] / "build" / "data" / "fond-plinti-pali" / "lcc-reactions.csv"


def _load_rows() -> tuple[ReactionRow, ...]:
    with CSV_PATH.open(encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        rows = list(reader)
    header_index = next(i for i, row in enumerate(rows) if row[1] == "Node")
    data_rows = rows[header_index + 2 :]  # skip header row + unit row
    return tuple(
        ReactionRow(
            nodo=int(row[1]),
            combo=row[2],
            famiglia=None,
            fx_kN=float(row[3]),
            fy_kN=float(row[4]),
            fz_kN=float(row[5]),
            mx_kNm=float(row[6]),
            my_kNm=float(row[7]),
            mz_kNm=float(row[8]),
        )
        for row in data_rows
        if len(row) >= 9 and row[1]
    )


@pytest.mark.skipif(not CSV_PATH.exists(), reason="real fixture data not available in this checkout")
def test_load_and_envelope_real_export_under_one_second():
    rows = _load_rows()
    assert len(rows) > 1000

    start = time.perf_counter()
    n_max = envelope(rows, lambda row: row.fz_kN, "max", by=None)
    n_min = envelope(rows, lambda row: row.fz_kN, "min", by=None)
    m_absmax = governing(rows, lambda row: row.mx_kNm, "absmax")
    elapsed = time.perf_counter() - start

    assert elapsed < 1.0
    assert n_max[0].valore >= n_min[0].valore
    assert m_absmax is not None
