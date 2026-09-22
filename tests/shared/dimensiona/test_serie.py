"""calcola_serie (WORKBENCH_SPEC §24): even spacing, per-point limits, errors preserved, a partial
series when the time budget runs out, and `verifiche_solo_esito` covering every outcome-only check
seen -- not just the ones `impara_orientamenti` happened to give an orientation to."""
import time

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.dimensiona.serie import calcola_serie, punti_equispaziati
from strutture.shared.report import CalcError, Check, Report, success
from strutture.shared.tool import Tool


def test_punti_equispaziati_covers_both_ends_and_is_evenly_spaced():
    valori = punti_equispaziati(0.0, 10.0, 5)
    assert valori[0] == 0.0
    assert valori[-1] == 10.0
    passi = {round(b - a, 9) for a, b in zip(valori, valori[1:])}
    assert passi == {2.5}


def test_punti_equispaziati_below_two_points_returns_only_da():
    assert punti_equispaziati(0.0, 10.0, 1) == (0.0,)


class _Inputs(BaseModel):
    model_config = ConfigDict(frozen=True)

    x: float = Field(gt=-100, lt=100)
    legacy_compat: bool = False


class _Outputs(BaseModel):
    model_config = ConfigDict(frozen=True)

    ok: bool = True


def _run(inputs: _Inputs) -> Report[_Outputs]:
    if inputs.x < 0:
        raise CalcError("x negativo non ammesso")
    # A demand/capacity check (has a ratio, x/10) and an outcome-only check with NO value/limit at
    # all -- exactly the ca-pilastro/ca-trave shape `test_copertura_rapporti.py` documents.
    checks = (
        Check(name="Resistenza", passed=inputs.x <= 10, clause="TEST", value=inputs.x, limit=10.0),
        Check(name="Dettaglio minimo", passed=inputs.x >= 2, clause="TEST"),
    )
    return success(_Outputs(), inputs, checks=checks)


_TOOL = Tool(name="prova-serie", title="Prova", group="g", norm="n", input_model=_Inputs, output_model=_Outputs, run=_run)


def test_verifiche_solo_esito_includes_a_check_with_no_ratio_anywhere():
    serie = calcola_serie(_TOOL, {}, "x", 1.0, 9.0, 5)
    assert "Dettaglio minimo" in serie.verifiche_solo_esito
    assert "Resistenza" not in serie.verifiche_solo_esito
    voce = next(v for v in serie.verifiche if v.nome == "Dettaglio minimo")
    assert voce.eta == (None, None, None, None, None)  # outcome-only: never an η
    assert voce.esito == (False, True, True, True, True)  # x=1,3,5,7,9 -> passed at x>=2


def test_errors_are_preserved_per_value():
    serie = calcola_serie(_TOOL, {}, "x", -5.0, 5.0, 3)  # -5, 0, 5 -> only -5 raises
    assert len(serie.errori) == 1
    assert "x negativo" in serie.errori[0]["messaggio"]
    assert serie.errori[0]["valore"] == -5.0
    assert serie.valori == (-5.0, 0.0, 5.0)


def test_time_budget_gives_a_partial_series():
    scadenza_gia_passata = -1.0
    serie = calcola_serie(_TOOL, {}, "x", 1.0, 9.0, 5, tempo_max_s=scadenza_gia_passata)
    assert serie.completa is False
    assert serie.valori == ()  # the deadline was already in the past before the first point ran
