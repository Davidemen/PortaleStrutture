"""Extract the 36 live `reazioni` rows (node 18000, the golden pile cap) from
`build/data/fond-plinti-pali/footing-check.csv` into `tests/fixtures/plinti_pali_golden_rows.csv`.

The workbook's `B6:I10639` fill-down template holds ~10634 rows, but only the first 36 carry a
non-blank `LCC` name (`SLU1..SLU15`, `SLU_EQU1..4`, `SLV_1..16` + one wind case); every row after
that is an all-zero padding template row (docs/architecture-batch2.md §6 "Golden rows"). Pile caps
have no `famiglia` column (§9-D5: `None` -> one global envelope), unlike `plinti_isolati`. Run once:
`uv run python tests/fixtures/gen_plinti_pali_golden_rows.py`.
"""
import csv
from pathlib import Path

SOURCE = Path(__file__).parent.parent.parent / "build/data/fond-plinti-pali/footing-check.csv"
TARGET = Path(__file__).parent / "plinti_pali_golden_rows.csv"
HEADER = ("nodo", "combo", "fx_kN", "fy_kN", "fz_kN", "mx_kNm", "my_kNm", "mz_kNm")


def main() -> None:
    with SOURCE.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.reader(f))
    data = rows[5:]  # `Footing check!B6:I...`: header rows 1-5 (0-indexed 0-4) precede the data.
    live = [row[1:9] for row in data if row[2].strip()]
    if len(live) != 36:
        raise ValueError(f"expected 36 live combo rows, got {len(live)}")

    with TARGET.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(HEADER)
        writer.writerows(live)


if __name__ == "__main__":
    main()
