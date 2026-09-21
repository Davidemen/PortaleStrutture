"""Shared fixtures for `strutture.foundations.plinti_isolati` tests: the 537-row golden combo table
extracted from the source workbook (docs/architecture-batch2.md §6 "Golden rows"), and the scalar
golden-case inputs from docs/specs/fond-plinti-isolati.md."""
import csv
from pathlib import Path

import pytest

from strutture.shared.load_table import ReactionRow

GOLDEN_ROWS_CSV = Path(__file__).parent.parent.parent / "fixtures/plinti_isolati_golden_rows.csv"

# docs/specs/fond-plinti-isolati.md Tool-1/Tool-2 golden case (node 1832).
GOLDEN_SCALARI: dict = {
    "ax_m": 4.0, "by_m": 4.0, "h_plinto_m": 0.8, "h_interro_m": 4.5,
    "a_pedestal_m": 0.0, "b_pedestal_m": 0.0, "h_pedestal_sopra_m": 0.0, "h_pedestal_sotto_m": 0.0,
    "offset_leva_m": 0.05, "ex_m": 0.0, "ey_m": 0.0,
    "gamma_terreno_kNm3": 20.0, "phi_terreno_deg": 30.0,
    "classe_calcestruzzo": "C35/45", "grado_acciaio": "B500C", "gamma_s": 1.15,
    "copriferro_cm": 8.0, "passo_armatura_cm": 12.2,
    "diametro_manuale_x_mm": 20.0, "diametro_manuale_y_mm": 20.0,
    "sistema_unita": "tecnico",
    "metodo_pressioni": "sovrapposizione",
    "resistenze": tuple(
        {"famiglia": famiglia, "sigma_ammissibile": sigma}
        for famiglia, sigma in (
            ("SLU_STR", 2.0), ("SLU_EQU", 2.0), ("SLV_STR", 2.0), ("SLV_EQU", 2.0),
            ("SLE_RARA", 1.5), ("SLE_FREQ", 1.5), ("SLE_QP", 1.5),
        )
    ),
}


def load_golden_rows() -> tuple[ReactionRow, ...]:
    with GOLDEN_ROWS_CSV.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return tuple(
            ReactionRow(
                nodo=int(row["nodo"]), combo=row["combo"], famiglia=row["famiglia"],
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
