"""docs/BUILD_CONTRACT.md Batch 2 performance requirement: a 20 000-row `reazioni` table runs in
under 5 s (spec's own invariant note: 10 634 rows < 2 s)."""
import time

import pytest

from strutture.foundations.plinti_isolati.tool import TOOLS
from strutture.shared.load_table import Famiglia
from strutture.shared.tool import execute

TOOL = TOOLS[0]
FAMIGLIE: tuple[Famiglia, ...] = ("SLU_STR", "SLU_EQU", "SLV_STR", "SLV_EQU", "SLE_RARA", "SLE_FREQ", "SLE_QP")
ROW_COUNT = 20_000


def _tabella_grande() -> tuple[dict, ...]:
    return tuple(
        {
            "nodo": 1832, "combo": f"C{i}", "famiglia": FAMIGLIE[i % len(FAMIGLIE)],
            "fx_kN": 0.1 + i * 1e-4, "fy_kN": 5.0 + i * 1e-4, "fz_kN": 200.0 + (i % 50),
            "mx_kNm": -30.0 - i * 1e-3, "my_kNm": 1.0 + i * 1e-4, "mz_kNm": -0.05,
        }
        for i in range(ROW_COUNT)
    )


@pytest.mark.unit
def test_20000_righe_sotto_5_secondi() -> None:
    inputs = {
        **TOOL.example,
        "reazioni": _tabella_grande(),
        "resistenze": [{"famiglia": f, "sigma_ammissibile": 200.0} for f in FAMIGLIE],
        "sistema_unita": "SI",
        "legacy_compat": True,
    }
    inizio = time.perf_counter()
    report = execute(TOOL, inputs)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert len(report.data.righe) == ROW_COUNT
    assert durata < 5.0, f"20000 righe in {durata:.2f}s (limite 5s)"
