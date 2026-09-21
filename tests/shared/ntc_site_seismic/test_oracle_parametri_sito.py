"""Oracle test for amplificazione() against `ntc_site_seismic_parametri_sito_oracle.json` (Sisma sheet)."""
import json
from pathlib import Path

import pytest

from strutture.shared.ntc_site_seismic.amplificazione import amplificazione

pytestmark = pytest.mark.oracle

FIXTURE = Path(__file__).parent.parent.parent / "fixtures" / "ntc_site_seismic_parametri_sito_oracle.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "case", CASES, ids=[f"{c['inputs']['I26']}-{c['inputs']['I27']}-{c['inputs']['I29']}-{c['inputs']['I30']}" for c in CASES]
)
def test_amplificazione_matches_libreoffice_legacy_compat(case):
    inputs, outputs = case["inputs"], case["outputs"]
    result = amplificazione(
        inputs["I26"],
        inputs["I27"],
        tc_star_s=inputs["I28"],
        f0=inputs["I29"],
        ag_g=inputs["I30"],
        legacy_compat=True,
    )
    assert result.cc == pytest.approx(outputs["I31"], rel=1e-6)
    assert result.ss == pytest.approx(outputs["I32"], rel=1e-6)
    assert result.st == pytest.approx(outputs["I33"], rel=1e-6)
    assert result.s == pytest.approx(outputs["I34"], rel=1e-6)
