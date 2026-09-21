"""docs/BUILD_CONTRACT.md Batch 2 performance requirement: a 20 000-row `reazioni` table runs in
under 5 s."""
import time

import pytest

from strutture.foundations.plinti_pali.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]
ROW_COUNT = 20_000


def _tabella_grande() -> tuple[dict, ...]:
    return tuple(
        {
            "nodo": 18000, "combo": f"C{i}",
            "fx_kN": 0.1 + i * 1e-4, "fy_kN": 5.0 + i * 1e-4, "fz_kN": 800.0 + (i % 200),
            "mx_kNm": -30.0 - i * 1e-3, "my_kNm": 1.0 + i * 1e-4, "mz_kNm": -0.05,
        }
        for i in range(ROW_COUNT)
    )


@pytest.mark.unit
def test_20000_righe_sotto_5_secondi() -> None:
    inputs = {**TOOL.example, "reazioni": _tabella_grande()}
    inizio = time.perf_counter()
    report = execute(TOOL, inputs)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert len(report.data.righe) == ROW_COUNT
    assert durata < 5.0, f"20000 righe in {durata:.2f}s (limite 5s)"
