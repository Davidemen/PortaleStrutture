import pytest

from strutture.loads.sisma.models import (
    SismaFattoriStrutturaInput,
    SismaFattoriStrutturaOutput,
    SismaParametriSitoInput,
    SismaParametriSitoOutput,
    SismaSpettroInput,
    SismaSpettroOutput,
    SismaVitaRiferimentoInput,
    SismaVitaRiferimentoOutput,
)
from strutture.loads.sisma.tool import TOOLS
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_tools_registered_with_expected_names_and_shapes():
    by_name = {t.name: t for t in TOOLS}
    assert set(by_name) == {
        "sisma-vita-riferimento",
        "sisma-parametri-sito",
        "sisma-fattori-struttura",
        "sisma-spettro",
        "sisma-completo",
    }
    assert by_name["sisma-vita-riferimento"].output_model is SismaVitaRiferimentoOutput
    assert by_name["sisma-parametri-sito"].output_model is SismaParametriSitoOutput
    assert by_name["sisma-fattori-struttura"].output_model is SismaFattoriStrutturaOutput
    assert by_name["sisma-spettro"].output_model is SismaSpettroOutput


@pytest.mark.unit
def test_vita_riferimento_unknown_comune_becomes_calc_error():
    tool = next(t for t in TOOLS if t.name == "sisma-vita-riferimento")
    with pytest.raises(CalcError):
        tool.run(SismaVitaRiferimentoInput(comune="NonEsisteSicuramente9999", vn_anni=50, classe_uso="II"))


@pytest.mark.unit
def test_vita_riferimento_without_comune_omits_comune_info():
    tool = next(t for t in TOOLS if t.name == "sisma-vita-riferimento")
    report = tool.run(SismaVitaRiferimentoInput(vn_anni=50, classe_uso="II"))
    assert report.ok
    assert report.data.comune_info is None


@pytest.mark.unit
def test_parametri_sito_out_of_range_ag_becomes_calc_error():
    tool = next(t for t in TOOLS if t.name == "sisma-parametri-sito")
    with pytest.raises(CalcError):
        tool.run(SismaParametriSitoInput(categoria_sottosuolo="B", categoria_topografica="T1", tc_star_s=0.272, f0=2.436, ag_g=5.0))


@pytest.mark.unit
def test_spettro_rejects_inverted_range():
    tool = next(t for t in TOOLS if t.name == "sisma-spettro")
    inputs = SismaSpettroInput(
        s=1.2, eta=1, q=1.5, ag_g=0.1, f0=2.4, tb_s=0.1, tc_s=0.3, td_s=2.0, stato_limite="SLV",
        t_start_s=4.0, t_end_s=1.0,
    )
    with pytest.raises(CalcError):
        tool.run(inputs)


@pytest.mark.unit
def test_spettro_rejects_out_of_order_corner_periods():
    tool = next(t for t in TOOLS if t.name == "sisma-spettro")
    inputs = SismaSpettroInput(s=1.2, eta=1, q=1.5, ag_g=0.1, f0=2.4, tb_s=0.5, tc_s=0.3, td_s=2.0, stato_limite="SLV")
    with pytest.raises(CalcError):
        tool.run(inputs)


@pytest.mark.unit
def test_fattori_struttura_run_returns_ok_report():
    tool = next(t for t in TOOLS if t.name == "sisma-fattori-struttura")
    report = tool.run(SismaFattoriStrutturaInput(xi_pct=5, q0=1.5, regolare_altezza="SI", stato_limite="SLV", qv=1.5))
    assert report.ok
    assert report.data.q == pytest.approx(1.5)
