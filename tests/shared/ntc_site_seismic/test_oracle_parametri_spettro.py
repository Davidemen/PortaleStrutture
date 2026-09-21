"""Oracle test for periodi_spettro() against `ntc_site_seismic_parametri_spettro_oracle.json` (Sisma sheet)."""
import json
from pathlib import Path

import pytest

from strutture.shared.ntc_site_seismic.periodi_spettro import periodi_spettro
from strutture.shared.ntc_site_seismic.stratigrafia import coefficiente_correzione_cc

pytestmark = pytest.mark.oracle

FIXTURE = Path(__file__).parent.parent.parent / "fixtures" / "ntc_site_seismic_parametri_spettro_oracle.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    "case", CASES, ids=[f"{c['inputs']['I26']}-{c['inputs']['I28']}-{c['inputs']['I30']}" for c in CASES]
)
def test_periodi_spettro_match_libreoffice(case):
    inputs, outputs = case["inputs"], case["outputs"]
    cc = coefficiente_correzione_cc(inputs["I26"], inputs["I28"])
    assert cc == pytest.approx(outputs["I31"], rel=1e-6)

    result = periodi_spettro(cc, tc_star_s=inputs["I28"], ag_g=inputs["I30"])
    assert result.tb == pytest.approx(outputs["I48"], rel=1e-6)
    assert result.tc == pytest.approx(outputs["I49"], rel=1e-6)
    assert result.td == pytest.approx(outputs["I50"], rel=1e-6)
