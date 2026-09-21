"""Full composed `fond-plinto-isolato` tool, against the 537-row golden combo table
(docs/specs/fond-plinti-isolati.md, node 1832)."""
import pytest

from strutture.foundations.plinti_isolati.input import PlintoIsolatoInput
from strutture.foundations.plinti_isolati.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


@pytest.mark.golden
def test_tool_golden(golden_inputs: dict) -> None:
    report = execute(TOOL, golden_inputs)
    assert report.ok, report.errors
    data = report.data
    assert data is not None
    assert len(data.righe) == 537

    assert data.flessione.mx_slu_kNm == pytest.approx(1533.25, rel=1e-4)
    assert data.flessione.as_x_cm2 == pytest.approx(56.787, rel=1e-3)
    assert data.flessione.callout_inf_x == "33ø20"
    assert data.sle.sigma_c_qp_MPa == pytest.approx(3.35865, rel=1e-3)
    assert data.sle.sigma_s_freq_MPa == pytest.approx(139.873, rel=1e-3)

    assert data.eccentricita.ex_max.combo == "EQK_20"
    assert data.eccentricita.ey_max.combo == "ULS EQU9"

    inviluppo_ulu_str = {r.grandezza: r for r in data.inviluppo
                          if r.famiglia == "SLU_STR" and r.grandezza in ("pressione_max_kpa", "scorrimento_min")}
    assert inviluppo_ulu_str["pressione_max_kpa"].valore / 100.0 == pytest.approx(1.91656, rel=1e-4)
    assert inviluppo_ulu_str["pressione_max_kpa"].combo == "ULS_CR96"

    assert data.governante.combo == "ULS_CR96"  # overall worst bearing pressure, across every famiglia
    assert data.sigma_max_governante_kpa == pytest.approx(data.governante.sigma_max_kpa)
    assert data.mu_scorrimento_minimo == pytest.approx(80.1776, rel=1e-4)


@pytest.mark.golden
def test_tool_golden_checks(golden_inputs: dict) -> None:
    """Every family's bearing check is checkable (sigma_amm 2/1.5 kg/cm2); ULS families pass."""
    report = execute(TOOL, golden_inputs)
    checks_by_name = {c.name: c for c in report.checks}
    assert checks_by_name["Portanza (SLU_STR)"].passed  # 1.91656 <= 2 kg/cm2
    assert "Portanza (SLE_RARA)" in checks_by_name  # 1.40068 <= 1.5 kg/cm2
    assert checks_by_name["Portanza (SLE_RARA)"].passed
    assert all(c.passed for c in report.checks if c.name.startswith("Tensione"))


@pytest.mark.unit
def test_tool_famiglia_mancante_in_reazioni_rifiutata(golden_inputs: dict) -> None:
    riga = golden_inputs["reazioni"][0]
    inputs = {**golden_inputs, "reazioni": (riga.model_copy(update={"famiglia": None}),)}
    with pytest.raises(Exception):  # noqa: B017 - pydantic ValidationError, cross-row model_validator
        PlintoIsolatoInput.model_validate(inputs)


@pytest.mark.unit
def test_tool_resistenza_mancante_per_famiglia_rifiutata(golden_inputs: dict) -> None:
    inputs = {**golden_inputs, "resistenze": golden_inputs["resistenze"][:1]}
    with pytest.raises(Exception):  # noqa: B017
        PlintoIsolatoInput.model_validate(inputs)


@pytest.mark.unit
def test_tool_combo_duplicata_rifiutata(golden_inputs: dict) -> None:
    prima = golden_inputs["reazioni"][0]
    inputs = {**golden_inputs, "reazioni": (prima, prima)}
    with pytest.raises(Exception):  # noqa: B017
        PlintoIsolatoInput.model_validate(inputs)


@pytest.mark.unit
def test_tool_metodo_esatto_non_legacy(golden_inputs: dict) -> None:
    """legacy_compat=False lets `metodo_pressioni` through unforced."""
    inputs = {**golden_inputs, "legacy_compat": False, "metodo_pressioni": "esatto",
              "reazioni": golden_inputs["reazioni"][:1]}
    report = execute(TOOL, inputs)
    assert report.ok, report.errors
    assert report.data.righe[0].sigma_max_kpa > 0
