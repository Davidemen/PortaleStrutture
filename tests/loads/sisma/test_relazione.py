"""`relazione.py` (docs/architecture-phase2.md §6, wave 3 adoption): the harness on each of the 5
tools' own example AND on every oracle case the package's own oracle tests already use
(`test_oracle_vita_riferimento.py`, `test_oracle_parametri_sito.py`,
`test_oracle_fattori_struttura.py`, `test_oracle_spettro.py`), run here in STANDARD mode (the
fixtures' own `legacy_compat=True` is never set, `relazione` only describes standard mode, docs
§1) — plus variations that switch branches. None of the 5 tools ever emits a `Check` (`docs/specs/
sisma.md`: "no explicit pass/fail cells exist ... a spectrum generator, not a verifica"), so
"every Check has a Passo with esito" (docs §6) is vacuous here and is asserted as such rather than
skipped silently. The 5 tools' own `example` dicts are already the spec's golden Brembate case
(`docs/specs/sisma.md` "Golden test case"; `tests/loads/sisma/test_golden.py`), so
`test_relazione_coerente_sullesempio` already covers it — no separate golden-case test would add
anything a second time.
"""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.loads.sisma.fattore_struttura_q import fattore_struttura_q
from strutture.loads.sisma.kr_regolarita import kr_regolare_altezza
from strutture.loads.sisma.smorzamento import smorzamento_eta
from strutture.loads.sisma.stato_limite import is_stato_limite_uls
from strutture.loads.sisma.tool import TOOLS
from strutture.shared.ntc_site_seismic import amplificazione, periodi_spettro
from strutture.shared.tool import execute
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOLS_BY_NAME = {t.name: t for t in TOOLS}
_FIXTURES_DIR = Path(__file__).parents[2] / "fixtures"


def _fixture(nome: str) -> list[dict[str, Any]]:
    return json.loads((_FIXTURES_DIR / f"{nome}.json").read_text())


_ORACLE_VITA_RIFERIMENTO = _fixture("sisma_vita_riferimento_oracle")
_ORACLE_PARAMETRI_SITO = _fixture("sisma_parametri_sito_oracle")
_ORACLE_FATTORI_STRUTTURA = _fixture("sisma_fattori_struttura_oracle")
_ORACLE_SPETTRO = _fixture("sisma_spettro_oracle")


def _vita_riferimento_raw(case: dict[str, Any]) -> dict[str, Any]:
    inputs = case["inputs"]
    return {"comune": inputs.get("I4"), "vn_anni": inputs["I7"], "classe_uso": inputs["I8"]}


def _parametri_sito_raw(case: dict[str, Any]) -> dict[str, Any]:
    inputs = case["inputs"]
    return {
        "categoria_sottosuolo": inputs["I26"], "categoria_topografica": inputs["I27"],
        "tc_star_s": inputs["I28"], "f0": inputs["I29"], "ag_g": inputs["I30"],
    }


def _fattori_struttura_raw(case: dict[str, Any]) -> dict[str, Any]:
    inputs = case["inputs"]
    return {
        "xi_pct": inputs["I37"], "q0": inputs["I39"], "regolare_altezza": inputs["I40"].upper(),
        "stato_limite": inputs["I25"].upper(), "qv": inputs["I44"],
    }


def _spettro_raw_da_oracolo_sito(case: dict[str, Any]) -> dict[str, Any]:
    """`sisma_spettro_oracle.json`'s cases give the full site+structure chain (I25-I30, I37,
    I39-I40), not `SismaSpettroInput`'s own S/η/q/T_B/T_C/T_D directly: derive them here, in
    STANDARD mode (`legacy_compat=False`), the same composition `tool.py::run_completo` uses."""
    inputs = case["inputs"]
    amp = amplificazione(inputs["I26"], inputs["I27"], inputs["I28"], inputs["I29"], inputs["I30"], legacy_compat=False)
    periodi = periodi_spettro(amp.cc, inputs["I28"], inputs["I30"])
    eta = smorzamento_eta(inputs["I37"])
    is_uls = is_stato_limite_uls(inputs["I25"])
    kr = kr_regolare_altezza(inputs["I40"])
    q = fattore_struttura_q(inputs["I39"], kr, is_uls=is_uls)
    return {
        "s": amp.s, "eta": eta, "q": q, "ag_g": inputs["I30"], "f0": inputs["I29"],
        "tb_s": periodi.tb, "tc_s": periodi.tc, "td_s": periodi.td, "stato_limite": inputs["I25"].upper(),
    }


# --- ogni tool dichiara relazione e supera l'harness sul proprio esempio -----------------------


@pytest.mark.parametrize("nome", sorted(TOOLS_BY_NAME))
def test_tool_declares_relazione(nome: str):
    assert TOOLS_BY_NAME[nome].relazione is not None


@pytest.mark.parametrize("nome", sorted(TOOLS_BY_NAME))
def test_relazione_coerente_sullesempio(nome: str):
    assert_relazione_coerente(TOOLS_BY_NAME[nome], TOOLS_BY_NAME[nome].example)


@pytest.mark.parametrize("nome", sorted(TOOLS_BY_NAME))
def test_ogni_highlight_e_spiegato(nome: str):
    assert_ogni_highlight_e_spiegato(TOOLS_BY_NAME[nome], TOOLS_BY_NAME[nome].example)


@pytest.mark.parametrize("nome", sorted(TOOLS_BY_NAME))
def test_nessun_check_emesso_quindi_nessun_passo_di_verifica_atteso(nome: str):
    """docs/architecture-phase2.md §6 chiede un Passo con esito per ogni Check: nessuno dei 5 tool
    sisma emette un Check (`docs/specs/sisma.md`), quindi il requisito è vuoto per costruzione —
    verificato esplicitamente, non semplicemente saltato."""
    report = execute(TOOLS_BY_NAME[nome], TOOLS_BY_NAME[nome].example, con_relazione=True)
    assert report.checks == ()


# --- oracolo: ogni caso già usato dai test del pacchetto ----------------------------------------


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_VITA_RIFERIMENTO, ids=range(len(_ORACLE_VITA_RIFERIMENTO)))
def test_relazione_coerente_oracolo_vita_riferimento(case: dict[str, Any]):
    assert_relazione_coerente(TOOLS_BY_NAME["sisma-vita-riferimento"], _vita_riferimento_raw(case))


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_PARAMETRI_SITO, ids=range(len(_ORACLE_PARAMETRI_SITO)))
def test_relazione_coerente_oracolo_parametri_sito(case: dict[str, Any]):
    assert_relazione_coerente(TOOLS_BY_NAME["sisma-parametri-sito"], _parametri_sito_raw(case))


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_FATTORI_STRUTTURA, ids=range(len(_ORACLE_FATTORI_STRUTTURA)))
def test_relazione_coerente_oracolo_fattori_struttura(case: dict[str, Any]):
    assert_relazione_coerente(TOOLS_BY_NAME["sisma-fattori-struttura"], _fattori_struttura_raw(case))


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_SPETTRO, ids=range(len(_ORACLE_SPETTRO)))
def test_relazione_coerente_oracolo_spettro(case: dict[str, Any]):
    assert_relazione_coerente(TOOLS_BY_NAME["sisma-spettro"], _spettro_raw_da_oracolo_sito(case))


# --- dimensionamento (docs/architecture-phase2.md §6: 8-30 passi per tool) ----------------------


@pytest.mark.parametrize(
    ("nome", "minimo", "massimo"),
    [
        ("sisma-vita-riferimento", 8, 30),
        ("sisma-parametri-sito", 8, 30),
        ("sisma-fattori-struttura", 8, 30),
        ("sisma-spettro", 8, 30),
        # sisma-completo compone per intero le Traccia degli altri 4 tool (relazione_completo.py):
        # 8+8+8+10=34 sul caso aureo, oltre il budget 8-30 di un singolo tool per costruzione.
        ("sisma-completo", 8, 40),
    ],
)
def test_step_count(nome: str, minimo: int, massimo: int):
    report = execute(TOOLS_BY_NAME[nome], TOOLS_BY_NAME[nome].example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert minimo <= totale <= massimo


# --- variazioni che cambiano ramo ----------------------------------------------------------------


def test_variazione_vita_riferimento_senza_comune():
    esempio = {k: v for k, v in TOOLS_BY_NAME["sisma-vita-riferimento"].example.items() if k != "comune"}
    assert_relazione_coerente(TOOLS_BY_NAME["sisma-vita-riferimento"], esempio)


def test_variazione_vita_riferimento_classe_iv_minimo_di_35_anni_non_vincolante():
    assert_relazione_coerente(
        TOOLS_BY_NAME["sisma-vita-riferimento"], {"comune": "Brembate", "vn_anni": 100, "classe_uso": "IV"}
    )


def test_variazione_vita_riferimento_minimo_di_35_anni_vincolante():
    """VN=35, classe I (Cu=0,7): V_R,0=24,5 anni < 35, il minimo di legge governa (Passo V_R)."""
    assert_relazione_coerente(TOOLS_BY_NAME["sisma-vita-riferimento"], {"vn_anni": 35, "classe_uso": "I"})


def test_variazione_parametri_sito_categoria_a():
    """Categoria A: Cc=Ss=1, nessuna formula/clip (ramo banale)."""
    assert_relazione_coerente(
        TOOLS_BY_NAME["sisma-parametri-sito"],
        {**TOOLS_BY_NAME["sisma-parametri-sito"].example, "categoria_sottosuolo": "A"},
    )


def test_variazione_parametri_sito_categoria_e_topografica_t4():
    assert_relazione_coerente(
        TOOLS_BY_NAME["sisma-parametri-sito"],
        {**TOOLS_BY_NAME["sisma-parametri-sito"].example, "categoria_sottosuolo": "E", "categoria_topografica": "T4"},
    )


def test_variazione_fattori_struttura_stato_limite_di_esercizio():
    """SLO: stato limite di esercizio, q=1 (nessuna riduzione)."""
    assert_relazione_coerente(
        TOOLS_BY_NAME["sisma-fattori-struttura"], {**TOOLS_BY_NAME["sisma-fattori-struttura"].example, "stato_limite": "SLO"}
    )


def test_variazione_fattori_struttura_non_regolare_in_altezza():
    assert_relazione_coerente(
        TOOLS_BY_NAME["sisma-fattori-struttura"], {**TOOLS_BY_NAME["sisma-fattori-struttura"].example, "regolare_altezza": "NO"}
    )


def test_variazione_spettro_stato_limite_di_esercizio():
    """SLD: Sd(T)=Se(T) su tutti i 5 punti rappresentativi (nessuna riduzione per q, nessun pavimento)."""
    assert_relazione_coerente(
        TOOLS_BY_NAME["sisma-spettro"], {**TOOLS_BY_NAME["sisma-spettro"].example, "stato_limite": "SLD"}
    )


def test_variazione_spettro_smorzamento_non_convenzionale():
    """η≠1 esercita per intero il termine reciproco 1/(η·F0) del ramo di salita (NTC2018 eq. 3.2.4)."""
    assert_relazione_coerente(
        TOOLS_BY_NAME["sisma-spettro"], {**TOOLS_BY_NAME["sisma-spettro"].example, "eta": 0.8165, "q": 3.0}
    )


def test_variazione_completo_stato_limite_di_esercizio():
    assert_relazione_coerente(
        TOOLS_BY_NAME["sisma-completo"], {**TOOLS_BY_NAME["sisma-completo"].example, "stato_limite": "SLO"}
    )


# --- review finding WRONG_CLAUSE: il limite inferiore 0,2·ag di Sd(T) appartiene solo al §3.2.3.5 ---


def test_sd_uls_cita_solo_3_2_3_5_non_3_2_3_2_1():
    """Il limite inferiore 'Sd(T) non può assumere valori inferiori a 0,2·ag' appartiene a
    NTC2018 §3.2.3.5 (spettro di progetto): §3.2.3.2.1 definisce lo spettro ELASTICO e non
    contiene questo limite (review finding WRONG_CLAUSE su loads/sisma)."""
    report = execute(TOOLS_BY_NAME["sisma-spettro"], TOOLS_BY_NAME["sisma-spettro"].example, con_relazione=True)
    passi_sd = [p for t in report.relazione for p in t.passi if p.simbolo.startswith("S_d(") and p.clausola]
    assert passi_sd, "nessun passo S_d trovato: il caso di esempio deve essere uno stato limite ultimo"
    for passo in passi_sd:
        assert passo.clausola == "NTC2018 §3.2.3.5", passo.clausola
        assert "3.2.3.2.1" not in passo.clausola


def test_sd_uls_non_usa_la_parola_pavimento():
    """'pavimento' è una traduzione letterale scorretta dell'inglese 'floor' (limite inferiore):
    in italiano tecnico indica il pavimento di un vano, non un limite (review finding
    WRONG_CLAUSE su loads/sisma) — non deve comparire nella traccia."""
    report = execute(TOOLS_BY_NAME["sisma-spettro"], TOOLS_BY_NAME["sisma-spettro"].example, con_relazione=True)
    for traccia in report.relazione:
        for passo in traccia.passi:
            assert "pavimento" not in passo.simbolo.lower()
            assert "pavimento" not in passo.formula.lower()
            assert "pavimento" not in passo.clausola.lower()
            assert "pavimento" not in passo.nota.lower()


# --- review finding MISSING_STEP: categoria di sottosuolo/topografica invisibili nella traccia ---


def test_parametri_sito_riporta_le_categorie_nel_titolo():
    """Le formule di C_c/S_s/S_T cambiano con la categoria di sottosuolo e topografica (Tab.
    3.2.IV/3.2.V), ma né l'una né l'altra comparivano nella traccia stampata: un revisore non
    poteva confermare la riga giusta (review finding MISSING_STEP)."""
    esempio = TOOLS_BY_NAME["sisma-parametri-sito"].example
    report = execute(TOOLS_BY_NAME["sisma-parametri-sito"], esempio, con_relazione=True)
    titolo = report.relazione[0].titolo
    assert esempio["categoria_sottosuolo"] in titolo
    assert esempio["categoria_topografica"] in titolo


def test_relazione_coerente_con_smorzamento_diverso_dal_5_percento():
    """With η ≠ 1 the printed S_d formula must state the η→1/q substitution (the example, at ξ = 5 %,
    cannot tell S_e/q from a_g·S·F_0/q)."""
    from strutture.loads.sisma.tool import TOOLS
    from tests.shared.relazione.harness import assert_relazione_coerente

    spettro = next(t for t in TOOLS if t.name == "sisma-spettro")
    assert_relazione_coerente(spettro, {**spettro.example, "eta": 0.8165})
    completo = next(t for t in TOOLS if t.name == "sisma-completo")
    assert_relazione_coerente(completo, {**completo.example, "xi_pct": 10})
