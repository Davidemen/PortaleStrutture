"""Golden test: spec §8 cached case (comune=Brembate, VN=50, classe=II, statoLimite=SLV,
categoriaSottosuolo=B, categoriaTopografica=T1, T*C=0.272, F0=2.436, ag=0.098, ξ=5, q0=1.5,
regolare in altezza=SI, q,v=1.5), `legacy_compat=True`, end to end through the 4 tools."""
import pytest

from strutture.loads.sisma.models import (
    SismaFattoriStrutturaInput,
    SismaParametriSitoInput,
    SismaSpettroInput,
    SismaVitaRiferimentoInput,
)
from strutture.loads.sisma.tool import TOOLS

TOOLS_BY_NAME = {t.name: t for t in TOOLS}


@pytest.mark.golden
def test_golden_case_sisma_brembate():
    vr_report = TOOLS_BY_NAME["sisma-vita-riferimento"].run(
        SismaVitaRiferimentoInput(comune="Brembate", vn_anni=50, classe_uso="II", legacy_compat=True)
    )
    assert vr_report.ok
    vr = vr_report.data
    assert vr.comune_info.provincia == "Bergamo"
    assert vr.comune_info.regione == "Lombardia"
    assert vr.vita.cu == pytest.approx(1)
    assert vr.vita.vr == pytest.approx(50)
    assert (vr.periodi_ritorno.slo, vr.periodi_ritorno.sld, vr.periodi_ritorno.slv, vr.periodi_ritorno.slc) == pytest.approx(
        (30, 50, 475, 975)
    )

    sito_report = TOOLS_BY_NAME["sisma-parametri-sito"].run(
        SismaParametriSitoInput(
            categoria_sottosuolo="B", categoria_topografica="T1", tc_star_s=0.272, f0=2.436, ag_g=0.098, legacy_compat=True
        )
    )
    assert sito_report.ok
    sito = sito_report.data
    assert sito.amplificazione.cc == pytest.approx(1.42718, rel=1e-6)
    assert sito.amplificazione.ss == pytest.approx(1.2)
    assert sito.amplificazione.st == pytest.approx(1)
    assert sito.amplificazione.s == pytest.approx(1.2)
    assert sito.periodi.tb == pytest.approx(0.129398, rel=1e-5)
    assert sito.periodi.tc == pytest.approx(0.388193, rel=1e-5)
    assert sito.periodi.td == pytest.approx(1.992, rel=1e-6)

    fs_report = TOOLS_BY_NAME["sisma-fattori-struttura"].run(
        SismaFattoriStrutturaInput(xi_pct=5, q0=1.5, regolare_altezza="SI", stato_limite="SLV", qv=1.5, legacy_compat=True)
    )
    assert fs_report.ok
    fs = fs_report.data
    assert fs.eta == pytest.approx(1)
    assert fs.q == pytest.approx(1.5)
    assert fs.eta_vert == pytest.approx(0.666667, rel=1e-5)

    spettro_report = TOOLS_BY_NAME["sisma-spettro"].run(
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
            legacy_compat=True,
        )
    )
    assert spettro_report.ok
    punti = {round(p.t_s, 6): p for p in spettro_report.data.punti}
    assert punti[0.0].sd_g == pytest.approx(0.1176, rel=1e-5)

    from strutture.loads.sisma.spettro_elastico import se_elastico
    from strutture.loads.sisma.spettro_progetto import valore_spettro

    for t_s, expected_sd in (
        (sito.periodi.tb, 0.190982),
        (sito.periodi.tc, 0.190982),
        (sito.periodi.td, 0.0372179),
        (5.0, 0.00590732),
    ):
        se_g = se_elastico(
            t_s, sito.periodi.tb, sito.periodi.tc, sito.periodi.td, 0.098, sito.amplificazione.s, 2.436, fs.eta, legacy_compat=True
        )
        sd_g = valore_spettro(
            se_g,
            fs.q,
            t_s,
            is_uls=True,
            ag_g=0.098,
            s=sito.amplificazione.s,
            f0=2.436,
            tb_s=sito.periodi.tb,
            legacy_compat=True,
        )
        assert sd_g == pytest.approx(expected_sd, rel=1e-5)
