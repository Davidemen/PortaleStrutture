"""Shared fixtures for `strutture.foundations.plinti_pali` tests: the 36-row golden LCC table
extracted from the source workbook (docs/architecture-batch2.md §6 "Golden rows"), and the golden-
case scalar inputs from docs/specs/fond-plinti-pali.md."""
import csv
from pathlib import Path

import pytest

from strutture.shared.load_table import ReactionRow

GOLDEN_ROWS_CSV = Path(__file__).parent.parent.parent / "fixtures/plinti_pali_golden_rows.csv"

# docs/specs/fond-plinti-pali.md "Golden test case (Case 1: 4 piles, 2x2, cached values)".
GOLDEN_SCALARI: dict = {
    "schema_pali": "2x2", "lx_m": 2.0, "ly_m": 2.0,
    "ax_m": 4.0, "by_m": 4.0, "h_plinto_m": 1.2, "copriferro_cm": 5.0, "ex_m": 0.0, "ey_m": 0.0,
    "bx_pilastro_m": 0.7, "by_pilastro_m": 0.7,
    "diametro_pila_mm": 600.0, "diametro_long_assunto_mm": 24.0, "av_mm": 470.0,
    "resistenza_pila_compressione_kN": 1200.0,
    "carico_aggiuntivo_kN": 550.7008,  # AR26 (job-specific extra load); AR24 = 624.0 + 550.7008 = 1174.7008.
    "gamma_g1": 1.3,
    "classe_calcestruzzo": "C32/40", "grado_acciaio": "B450C", "gamma_s": 1.15, "gamma_c": 1.5,
    "diametro_inf_x_mm": 24.0, "passo_inf_x_mm": 100.0, "diametro_inf_y_mm": 24.0, "passo_inf_y_mm": 100.0,
    "diametro_sup_x_mm": 24.0, "passo_sup_x_mm": 200.0, "diametro_sup_y_mm": 24.0, "passo_sup_y_mm": 200.0,
    "diametro_tirante_xy_mm": 32.0, "n_tirante_xy": 2,
    "diametro_tirante_x_mm": 24.0, "n_tirante_x": 8,
    "diametro_tirante_y_mm": 24.0, "n_tirante_y": 8,
}


def load_golden_rows() -> tuple[ReactionRow, ...]:
    with GOLDEN_ROWS_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return tuple(
            ReactionRow(
                nodo=int(row["nodo"]), combo=row["combo"],
                fx_kN=float(row["fx_kN"]), fy_kN=float(row["fy_kN"]), fz_kN=float(row["fz_kN"]),
                mx_kNm=float(row["mx_kNm"]), my_kNm=float(row["my_kNm"]), mz_kNm=float(row["mz_kNm"]),
            )
            for row in reader
        )


@pytest.fixture(scope="session")
def golden_rows() -> tuple[ReactionRow, ...]:
    return load_golden_rows()


@pytest.fixture
def golden_inputs(golden_rows: tuple[ReactionRow, ...]) -> dict:
    return {**GOLDEN_SCALARI, "reazioni": golden_rows, "legacy_compat": True}
