import pytest

from strutture.loads.vento.models import VentoPressioneOutput
from strutture.loads.vento.tool import TOOLS
from strutture.shared.report import CalcError

BASE = {"altitudine_m": 120, "periodo_ritorno_anni": 50, "categoria_esposizione": "II", "ct": 1, "altezza_edificio_m": 60}


@pytest.mark.unit
def test_tool_registered_with_expected_shape():
    assert len(TOOLS) == 1
    tool = TOOLS[0]
    assert tool.name == "vento-pressione"
    assert tool.output_model is VentoPressioneOutput


@pytest.mark.unit
def test_tool_run_returns_ok_report_with_zona_diretta():
    tool = TOOLS[0]
    report = tool.run(tool.input_model(zona=1, **BASE))
    assert report.ok
    assert report.data.zona == 1
    assert report.data.provincia is None
    assert len(report.data.profilo) == 11  # default n_sezioni=10 -> 11 rows (0..10)


@pytest.mark.unit
def test_tool_run_echoes_provincia_regione_da_comune():
    tool = TOOLS[0]
    report = tool.run(tool.input_model(comune="Milano", **BASE))
    assert report.ok
    assert report.data.provincia == "Milano"
    assert report.data.regione == "Lombardia"


@pytest.mark.unit
def test_tool_run_avvisa_oltre_1500m_in_legacy_compat():
    """Il foglio storico (legacy_compat=True) si limita ad avvisare oltre 1500 m (Vento!L8), non blocca."""
    tool = TOOLS[0]
    report = tool.run(tool.input_model(zona=1, **{**BASE, "altitudine_m": 1600, "legacy_compat": True}))
    assert report.ok
    assert any("1500" in w for w in report.warnings)


@pytest.mark.unit
def test_tool_run_rifiuta_oltre_1500m_in_code_standard():
    """In modalità standard (legacy_compat=False, default) oltre 1500 m la norma richiede uno studio
    specifico del sito: CalcError, non un semplice avviso (§3.3.2)."""
    tool = TOOLS[0]
    with pytest.raises(CalcError, match="1500"):
        tool.run(tool.input_model(zona=1, **{**BASE, "altitudine_m": 1600}))


@pytest.mark.unit
def test_tool_run_non_avvisa_sotto_1500m():
    tool = TOOLS[0]
    report = tool.run(tool.input_model(zona=1, **BASE))
    assert report.ok
    assert report.warnings == ()


@pytest.mark.unit
def test_tool_run_avvisa_oltre_1000_sezioni():
    tool = TOOLS[0]
    report = tool.run(tool.input_model(zona=1, **{**BASE, "n_sezioni": 1001}))
    assert report.ok
    assert any("1000" in w for w in report.warnings)
    assert len(report.data.profilo) == 1002


@pytest.mark.unit
def test_tool_execute_maps_calc_error_to_failure():
    from strutture.shared.tool import execute

    tool = TOOLS[0]
    report = execute(tool, {**BASE, "comune": "Agrate Brianza", "legacy_compat": True})
    assert not report.ok
    assert report.errors


@pytest.mark.unit
def test_direct_run_raises_calc_error_for_legacy_bug():
    tool = TOOLS[0]
    with pytest.raises(CalcError):
        tool.run(tool.input_model(comune="Agrate Brianza", legacy_compat=True, **BASE))
