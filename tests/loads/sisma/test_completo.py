"""`sisma-completo` composes the four existing tools: the result must equal feeding them by hand
(spec §8 golden case), in both `legacy_compat` modes, plus validation errors surfacing with field
names and the tool staying registered alongside the four originals."""
import pytest
from pydantic import ValidationError

from strutture.loads.sisma.models import (
    SismaFattoriStrutturaInput,
    SismaParametriSitoInput,
    SismaSpettroInput,
    SismaVitaRiferimentoInput,
)
from strutture.loads.sisma.models_completo import SismaCompletoInput, SismaCompletoOutput
from strutture.loads.sisma.tool import TOOLS
from strutture.shared.report import CalcError

TOOLS_BY_NAME = {t.name: t for t in TOOLS}

GOLDEN_KWARGS = {
    "vn_anni": 50,
    "classe_uso": "II",
    "stato_limite": "SLV",
    "ag_g": 0.098,
    "f0": 2.436,
    "tc_star_s": 0.272,
    "categoria_sottosuolo": "B",
    "categoria_topografica": "T1",
    "xi_pct": 5,
    "q0": 1.5,
    "regolare_altezza": "SI",
    "qv": 1.5,
    "comune": "Brembate",
}


def _run_four_tools_by_hand(*, legacy_compat: bool) -> SismaCompletoOutput:
    vr = TOOLS_BY_NAME["sisma-vita-riferimento"].run(
        SismaVitaRiferimentoInput(comune="Brembate", vn_anni=50, classe_uso="II", legacy_compat=legacy_compat)
    ).data
    sito = TOOLS_BY_NAME["sisma-parametri-sito"].run(
        SismaParametriSitoInput(
            categoria_sottosuolo="B", categoria_topografica="T1", tc_star_s=0.272, f0=2.436, ag_g=0.098,
            legacy_compat=legacy_compat,
        )
    ).data
    fs = TOOLS_BY_NAME["sisma-fattori-struttura"].run(
        SismaFattoriStrutturaInput(
            xi_pct=5, q0=1.5, regolare_altezza="SI", stato_limite="SLV", qv=1.5, legacy_compat=legacy_compat
        )
    ).data
    spettro = TOOLS_BY_NAME["sisma-spettro"].run(
        SismaSpettroInput(
            s=sito.amplificazione.s,
            eta=fs.eta,
            q=fs.q,
            ag_g=0.098,
            f0=2.436,
            tb_s=sito.periodi.tb,
            tc_s=sito.periodi.tc,
            td_s=sito.periodi.td,
            stato_limite="SLV",
            legacy_compat=legacy_compat,
        )
    ).data
    return SismaCompletoOutput(vita_riferimento=vr, parametri_sito=sito, fattori_struttura=fs, spettro=spettro)


@pytest.mark.golden
@pytest.mark.parametrize("legacy_compat", [True, False])
def test_completo_equals_four_tools_run_by_hand(legacy_compat: bool):
    expected = _run_four_tools_by_hand(legacy_compat=legacy_compat)

    report = TOOLS_BY_NAME["sisma-completo"].run(SismaCompletoInput(**GOLDEN_KWARGS, legacy_compat=legacy_compat))

    assert report.ok
    actual = report.data
    assert actual.vita_riferimento == expected.vita_riferimento
    assert actual.parametri_sito == expected.parametri_sito
    assert actual.fattori_struttura == expected.fattori_struttura
    assert actual.spettro == expected.spettro


@pytest.mark.golden
def test_completo_golden_values_match_spec_8():
    report = TOOLS_BY_NAME["sisma-completo"].run(SismaCompletoInput(**GOLDEN_KWARGS, legacy_compat=True))
    assert report.ok
    data = report.data

    assert data.vita_riferimento.comune_info.provincia == "Bergamo"
    assert data.vita_riferimento.comune_info.regione == "Lombardia"
    assert data.vita_riferimento.vita.cu == pytest.approx(1)
    assert data.vita_riferimento.vita.vr == pytest.approx(50)
    assert (
        data.vita_riferimento.periodi_ritorno.slo,
        data.vita_riferimento.periodi_ritorno.sld,
        data.vita_riferimento.periodi_ritorno.slv,
        data.vita_riferimento.periodi_ritorno.slc,
    ) == pytest.approx((30, 50, 475, 975))

    assert data.parametri_sito.amplificazione.cc == pytest.approx(1.42718, rel=1e-6)
    assert data.parametri_sito.amplificazione.s == pytest.approx(1.2)
    assert data.parametri_sito.periodi.tb == pytest.approx(0.129398, rel=1e-5)
    assert data.parametri_sito.periodi.tc == pytest.approx(0.388193, rel=1e-5)
    assert data.parametri_sito.periodi.td == pytest.approx(1.992, rel=1e-6)

    assert data.fattori_struttura.eta == pytest.approx(1)
    assert data.fattori_struttura.q == pytest.approx(1.5)
    assert data.fattori_struttura.eta_vert == pytest.approx(0.666667, rel=1e-5)

    punti = {round(p.t_s, 6): p for p in data.spettro.punti}
    assert punti[0.0].sd_g == pytest.approx(0.1176, rel=1e-5)


@pytest.mark.unit
def test_completo_registered_alongside_existing_tools():
    assert set(TOOLS_BY_NAME) == {
        "sisma-vita-riferimento",
        "sisma-parametri-sito",
        "sisma-fattori-struttura",
        "sisma-spettro",
        "sisma-completo",
    }
    assert TOOLS_BY_NAME["sisma-completo"].output_model is SismaCompletoOutput


@pytest.mark.unit
def test_completo_without_comune_omits_comune_info():
    kwargs = {**GOLDEN_KWARGS, "comune": None}
    report = TOOLS_BY_NAME["sisma-completo"].run(SismaCompletoInput(**kwargs))
    assert report.ok
    assert report.data.vita_riferimento.comune_info is None


@pytest.mark.unit
def test_completo_unknown_comune_becomes_calc_error():
    kwargs = {**GOLDEN_KWARGS, "comune": "NonEsisteSicuramente9999"}
    with pytest.raises(CalcError):
        TOOLS_BY_NAME["sisma-completo"].run(SismaCompletoInput(**kwargs))


@pytest.mark.unit
def test_completo_out_of_range_ag_becomes_calc_error():
    kwargs = {**GOLDEN_KWARGS, "ag_g": 5.0}
    with pytest.raises(CalcError):
        TOOLS_BY_NAME["sisma-completo"].run(SismaCompletoInput(**kwargs))


@pytest.mark.unit
def test_completo_validation_error_surfaces_field_name():
    kwargs = {**GOLDEN_KWARGS, "vn_anni": -1}
    with pytest.raises(ValidationError) as exc_info:
        SismaCompletoInput(**kwargs)
    assert "vn_anni" in str(exc_info.value)


@pytest.mark.unit
def test_completo_invalid_stato_limite_enum_surfaces_field_name():
    kwargs = {**GOLDEN_KWARGS, "stato_limite": "NOT-A-STATE"}
    with pytest.raises(ValidationError) as exc_info:
        SismaCompletoInput(**kwargs)
    assert "stato_limite" in str(exc_info.value)
