"""Oracle test for Sd(T) (Sisma!I55:J149), sampled at representative rows across all four branches
and both SLE (undivided) / SLU (divided by q) regimes. Points are evaluated directly at the sheet's
own T values via the closed-form functions (`campionamento`'s default grid need not land on them —
see `docs/specs/sisma.md` Tool 6 and `strutture.loads.sisma.campionamento`).
"""
import json
from pathlib import Path

import pytest

from strutture.loads.sisma.fattore_struttura_q import fattore_struttura_q
from strutture.loads.sisma.kr_regolarita import kr_regolare_altezza
from strutture.loads.sisma.smorzamento import smorzamento_eta
from strutture.loads.sisma.spettro_elastico import se_elastico
from strutture.loads.sisma.spettro_progetto import valore_spettro
from strutture.loads.sisma.stato_limite import is_stato_limite_uls
from strutture.shared.ntc_site_seismic import amplificazione, periodi_spettro

FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "sisma_spettro_oracle.json").read_text())
ROWS = (55, 56, 57, 58, 90, 94, 107, 149)


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle_case(case: dict):
    inputs = case["inputs"]
    outputs = case["outputs"]

    amp = amplificazione(inputs["I26"], inputs["I27"], inputs["I28"], inputs["I29"], inputs["I30"], legacy_compat=True)
    periodi = periodi_spettro(amp.cc, inputs["I28"], inputs["I30"])
    eta = smorzamento_eta(inputs["I37"])
    is_uls = is_stato_limite_uls(inputs["I25"])
    kr = kr_regolare_altezza(inputs["I40"])
    q = fattore_struttura_q(inputs["I39"], kr, is_uls=is_uls)

    for row in ROWS:
        t_s = outputs[f"I{row}"]
        expected_sd = outputs[f"J{row}"]
        se_g = se_elastico(t_s, periodi.tb, periodi.tc, periodi.td, inputs["I30"], amp.s, inputs["I29"], eta, legacy_compat=True)
        sd_g = valore_spettro(
            se_g,
            q,
            t_s,
            is_uls=is_uls,
            ag_g=inputs["I30"],
            s=amp.s,
            f0=inputs["I29"],
            tb_s=periodi.tb,
            legacy_compat=True,
        )
        assert sd_g == pytest.approx(expected_sd, rel=1e-5), f"row {row}"
