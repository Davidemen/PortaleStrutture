"""Extract the 537 live `reazioni` rows of the node-1832 footing instance from
`build/data/fond-plinti-isolati/input.csv` into `tests/fixtures/plinti_isolati_golden_rows.csv`
(docs/architecture-batch2.md §6 "Golden rows").

`famiglia` is assigned by ROW POSITION, replicating the sheet's own hard-coded family row-ranges
(`INPUT!AE4:AG10`, docs/architecture-batch2.md §7): the sheet's own `I` (comboType) text column is
unreliable for this — the last 24-row block (`EQK EQU`, family `SLV_EQU`) is labelled "STR EQK" in
that column, identical to the `SLV_STR` block's text. Run once:
`uv run python tests/fixtures/gen_plinti_isolati_golden_rows.py`.
"""
import csv
from pathlib import Path

SOURCE = Path(__file__).parent.parent.parent / "build/data/fond-plinti-isolati/input.csv"
TARGET = Path(__file__).parent / "plinti_isolati_golden_rows.csv"

# (famiglia, row count), in sheet order — INPUT!AE4:AE10, sum = 537.
BUCKETS = (
    ("SLU_STR", 216), ("SLV_STR", 48), ("SLE_RARA", 192), ("SLE_FREQ", 42),
    ("SLE_QP", 6), ("SLU_EQU", 9), ("SLV_EQU", 24),
)
HEADER = ("nodo", "combo", "famiglia", "fx_kN", "fy_kN", "fz_kN", "mx_kNm", "my_kNm", "mz_kNm")


def main() -> None:
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    data = rows[2:539]  # INPUT rows 3..539 (header row1, units row2), the 537 live combo rows.
    if len(data) != sum(size for _, size in BUCKETS):
        raise ValueError(f"expected {sum(size for _, size in BUCKETS)} rows, got {len(data)}")

    out_rows = []
    index = 0
    for famiglia, size in BUCKETS:
        for row in data[index:index + size]:
            nodo, combo, fx, fy, fz, mx, my, mz = row[:8]
            out_rows.append((nodo, combo, famiglia, fx, fy, fz, mx, my, mz))
        index += size

    with TARGET.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(out_rows)


if __name__ == "__main__":
    main()
