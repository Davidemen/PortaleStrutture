"""Oracle test for coefficiente_uso/vita_riferimento/periodi_ritorno against `sisma_oracle.json` (Sisma sheet)."""
import json
from pathlib import Path

import pytest

from strutture.shared.ntc_site_seismic.classe_uso import coefficiente_uso
from strutture.shared.ntc_site_seismic.periodo_ritorno import periodi_ritorno
from strutture.shared.ntc_site_seismic.vita_riferimento import vita_riferimento

pytestmark = pytest.mark.oracle

FIXTURE = Path(__file__).parent.parent.parent / "fixtures" / "ntc_site_seismic_vita_riferimento_oracle.json"
CASES = json.loads(FIXTURE.read_text(encoding="utf-8"))


@pytest.mark.parametrize("case", CASES, ids=[f"{c['inputs']['I8']}-VN{c['inputs']['I7']}" for c in CASES])
def test_vita_riferimento_and_periodi_ritorno_match_libreoffice(case):
    vn, classe = case["inputs"]["I7"], case["inputs"]["I8"]
    outputs = case["outputs"]

    cu = coefficiente_uso(classe)
    assert cu == pytest.approx(outputs["I9"], rel=1e-6)

    vr_result = vita_riferimento(vn, cu, legacy_compat=True)
    assert vr_result.vr == pytest.approx(outputs["I10"], rel=1e-6)

    tr = periodi_ritorno(vr_result.vr)
    assert tr.slo == pytest.approx(outputs["E13"], rel=1e-6)
    assert tr.sld == pytest.approx(outputs["E14"], rel=1e-6)
    assert tr.slv == pytest.approx(outputs["E15"], rel=1e-6)
    assert tr.slc == pytest.approx(outputs["E16"], rel=1e-6)
