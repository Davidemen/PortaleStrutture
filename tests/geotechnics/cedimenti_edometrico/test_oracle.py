"""Oracle tests against `tests/fixtures/geo_cedimenti_edometrico_oracle.json`
(regenerate with `tests/fixtures/gen_geo_cedimenti_edometrico.py`, slug `geo-cedimenti`, sheet
`Edometrico`). B/L/q/the layer table are themselves formulas pulling from sheet
`Elastico_centrale_Newmark` in the source workbook (docs/specs/geo-cedimenti-edometrico.md), so the
fixture's overrides use that sheet's cells for those; `sistema_unita="tecnico"` reproduces the
sheet's own cm/kg-mc/kg-cmq numbers directly (docs/architecture-batch2.md §9-D1)."""
import json
from pathlib import Path

import pytest

from strutture.geotechnics.cedimenti_edometrico.models import EdometricoInput
from strutture.geotechnics.cedimenti_edometrico.tool import run
from strutture.shared.units import kgcm2_to_mpa, kpa_to_kgcm2

FIXTURE = json.loads(Path(__file__).parents[2].joinpath("fixtures", "geo_cedimenti_edometrico_oracle.json").read_text(encoding="utf-8"))

# Cached-workbook defaults (sheet `Edometrico`/`Elastico_centrale_Newmark`), overridden per case.
_DEFAULT_LAYERS_KGCM2 = (
    (0, 370, 56.0843917137861),
    (370, 470, 71.380134908455),
    (470, 550, 91.7744591680136),
    (550, 3150, 71.380134908455),
    (3150, 11890, 71.380134908455),
)


def _layers(overrides: dict) -> list[dict]:
    rows = list(_DEFAULT_LAYERS_KGCM2)
    layer2_eed = overrides.get("Elastico_centrale_Newmark!F8")
    if layer2_eed is not None:
        rows[1] = (rows[1][0], rows[1][1], layer2_eed)
    return [{"z_top_m": top / 100, "z_bot_m": bot / 100, "modulo_MPa": kgcm2_to_mpa(eed)} for top, bot, eed in rows]


def _to_input(overrides: dict) -> EdometricoInput:
    return EdometricoInput(
        sistema_unita="tecnico",
        b=overrides.get("Elastico_centrale_Newmark!D1", 350),
        l=overrides.get("Elastico_centrale_Newmark!D2", 500),
        q=overrides.get("Elastico_centrale_Newmark!D3", 0.5),
        gamma=overrides.get("B3", 1800),
        d=overrides.get("B8", 0),  # metres, never converted (see models.py)
        strati=_layers(overrides),
        dz=10, z_max=5000,
        z_crit_input=overrides.get("B18"),
        metodo_tensioni="approssimato",  # legacy_compat forces this too; explicit for clarity
        legacy_compat=True,
    )


def _row_near(righe, z_m: float):
    return min(righe, key=lambda riga: abs(riga.z_m - z_m))


@pytest.mark.oracle
@pytest.mark.parametrize("case", FIXTURE, ids=range(len(FIXTURE)))
def test_oracle(case: dict) -> None:
    outputs = case["outputs"]
    report = run(_to_input(case["inputs"]))
    assert report.ok
    data = report.data

    assert kpa_to_kgcm2(data.carico.q_prime_kPa) == pytest.approx(outputs["B12"], rel=1e-5)
    assert data.cedimento.w_ed_cm == pytest.approx(outputs["B15"], rel=1e-5)

    riga_0 = _row_near(data.righe, 0.0)
    assert kpa_to_kgcm2(riga_0.delta_sigma_kPa) == pytest.approx(outputs["H3"], rel=1e-5)
    assert riga_0.delta_h_cm == pytest.approx(outputs["K3"], abs=1e-9)
    assert riga_0.cumulativo_cm == pytest.approx(outputs["L3"], abs=1e-9)

    riga_1 = _row_near(data.righe, 0.1)
    assert kpa_to_kgcm2(riga_1.delta_sigma_kPa) == pytest.approx(outputs["H4"], rel=1e-5)
    assert riga_1.delta_h_cm == pytest.approx(outputs["K4"], rel=1e-5)
    assert riga_1.cumulativo_cm == pytest.approx(outputs["L4"], rel=1e-5)

    riga_mid = _row_near(data.righe, 20.0)
    assert kpa_to_kgcm2(riga_mid.delta_sigma_kPa) == pytest.approx(outputs["H203"], rel=1e-5)
    assert riga_mid.delta_h_cm == pytest.approx(outputs["K203"], rel=1e-5)
    assert riga_mid.cumulativo_cm == pytest.approx(outputs["L203"], rel=1e-5)

    riga_ultima = _row_near(data.righe, 50.0)
    assert kpa_to_kgcm2(riga_ultima.delta_sigma_kPa) == pytest.approx(outputs["H503"], rel=1e-5)
    assert riga_ultima.cumulativo_cm == pytest.approx(outputs["L503"], rel=1e-5)
