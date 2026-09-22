"""`relazione.py` (docs/architecture-phase2.md §6, wave-2/3 adoption): the harness on the tool's
own example, on every oracle case of `test_oracle.py`
(`tests/fixtures/geo_cedimenti_edometrico_oracle.json`) and on the golden case of `test_golden.py`
— run here in STANDARD mode (`legacy_compat=False`: `relazione` only ever describes standard mode,
docs/architecture-phase2.md §1) — plus variations that switch branches: the exact Newmark stress
method, the auto-computed Z,crit (no manual override), a shallow water table above the embedment,
and a Z,crit so shallow that no depth slice is traced individually."""
import json
import re
from pathlib import Path
from typing import Any

import pytest

from strutture.geotechnics.cedimenti_edometrico.tool import TOOLS
from strutture.shared.tool import execute
from strutture.shared.units import kgcm2_to_mpa
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "geo-cedimento-edometrico")

_ORACLE_FIXTURE = json.loads(
    (Path(__file__).parents[2] / "fixtures" / "geo_cedimenti_edometrico_oracle.json").read_text(encoding="utf-8")
)
_GOLDEN_STRATI = [
    {"z_top_m": 0.00, "z_bot_m": 3.70, "modulo_MPa": 5.500000812600001},
    {"z_top_m": 3.70, "z_bot_m": 4.70, "modulo_MPa": 6.99999657665},
    {"z_top_m": 4.70, "z_bot_m": 5.50, "modulo_MPa": 9.00000400425},
    {"z_top_m": 5.50, "z_bot_m": 31.50, "modulo_MPa": 6.99999657665},
    {"z_top_m": 31.50, "z_bot_m": 118.90, "modulo_MPa": 6.99999657665},
]
_GOLDEN_KWARGS = {
    "sistema_unita": "tecnico", "b": 350, "l": 500, "d": 0, "gamma": 1800, "q": 0.5,
    "strati": _GOLDEN_STRATI, "metodo_tensioni": "approssimato", "z_crit_input": 10000,
    "dz": 10, "z_max": 5000,
}

# Cached-workbook defaults (sheet `Edometrico`/`Elastico_centrale_Newmark`), same map as test_oracle.py.
_DEFAULT_LAYERS_KGCM2 = (
    (0, 370, 56.0843917137861),
    (370, 470, 71.380134908455),
    (470, 550, 91.7744591680136),
    (550, 3150, 71.380134908455),
    (3150, 11890, 71.380134908455),
)


def _oracle_layers(overrides: dict[str, Any]) -> list[dict[str, Any]]:
    rows = list(_DEFAULT_LAYERS_KGCM2)
    layer2_eed = overrides.get("Elastico_centrale_Newmark!F8")
    if layer2_eed is not None:
        rows[1] = (rows[1][0], rows[1][1], layer2_eed)
    return [{"z_top_m": top / 100, "z_bot_m": bot / 100, "modulo_MPa": kgcm2_to_mpa(eed)} for top, bot, eed in rows]


def _oracle_raw_inputs(case: dict[str, Any]) -> dict[str, Any]:
    """The oracle case's inputs, renamed to `EdometricoInput` field names, WITHOUT `legacy_compat`
    (defaults to False/standard — `relazione` never runs in legacy mode)."""
    overrides = case["inputs"]
    return {
        "sistema_unita": "tecnico",
        "b": overrides.get("Elastico_centrale_Newmark!D1", 350),
        "l": overrides.get("Elastico_centrale_Newmark!D2", 500),
        "q": overrides.get("Elastico_centrale_Newmark!D3", 0.5),
        "gamma": overrides.get("B3", 1800),
        "d": overrides.get("B8", 0),
        "strati": _oracle_layers(overrides),
        "dz": 10, "z_max": 5000,
        "z_crit_input": overrides.get("B18"),
        "metodo_tensioni": "approssimato",
    }


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden():
    assert_relazione_coerente(TOOL, _GOLDEN_KWARGS)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_FIXTURE, ids=range(len(_ORACLE_FIXTURE)))
def test_relazione_coerente_sui_casi_oracolo(case: dict[str, Any]):
    assert_relazione_coerente(TOOL, _oracle_raw_inputs(case))


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_step_count_within_the_8_to_30_target():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 30


def test_al_massimo_6_fette_di_profondita_tracciate_singolarmente():
    """docs/architecture-phase2.md §5: "many-rows tools trace the GOVERNING row only" — al più 3
    fette individuali (Δσ_k/ΔH_k, una coppia di passi ciascuna) più il passo "resto" lumped."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "fette" in t.titolo.lower())
    fette_individuali = [p for p in traccia.passi if p.simbolo.startswith("ΔH_") and not p.simbolo.startswith("ΔH_resto")]
    assert 1 <= len(fette_individuali) <= 6


def test_clausole_citano_il_metodo_reale_non_ntc2018_6_2_2():
    """review finding WRONG_CLAUSE: NTC2018 §6.2.2/Circolare C6.2.2 prescrivono QUALI verifiche
    fare, non la formula di diffusione 2:1 né quella di compressione edometrica monodimensionale —
    nessun passo di questo strumento (q', Δσ, ΔH, w_ed) può citarle come se fosse la fonte della
    formula stampata."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    for traccia in report.relazione:
        for passo in traccia.passi:
            assert "6.2.2" not in passo.clausola, f"{passo.simbolo}: {passo.clausola!r}"
    traccia_fette = next(t for t in report.relazione if "fette" in t.titolo.lower())
    passo_sigma = next(p for p in traccia_fette.passi if p.simbolo.startswith("Δσ_"))
    assert "2:1" in passo_sigma.clausola or "2 a 1" in passo_sigma.clausola
    passo_dh = next(p for p in traccia_fette.passi if p.simbolo.startswith("ΔH_") and not p.simbolo.startswith("ΔH_resto"))
    assert "edometric" in passo_dh.clausola.lower()


def test_delta_h_resto_riporta_il_numero_di_fette_e_lintervallo_di_profondita():
    """review finding MISSING_STEP: il passo che somma le fette non tracciate singolarmente non
    aveva né formula, né clausola, né conteggio, né intervallo di profondità — non riproducibile.
    `nota` non è mai stampata da `traccia_a_testo`: l'informazione va nel simbolo stampato."""
    variazione = {**TOOL.example, "dz": 1}  # passo più fitto: più fette, sicuramente oltre 3
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "fette" in t.titolo.lower())
    passo_resto = next(p for p in traccia.passi if p.simbolo.startswith("ΔH_resto"))
    assert passo_resto.simbolo != "ΔH_resto", "il simbolo deve portare conteggio/intervallo, non restare nudo"
    assert re.search(r"\d+\s*fette", passo_resto.simbolo)
    assert "z=" in passo_resto.simbolo
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_metodo_newmark():
    """`metodo_tensioni="newmark"`: Δσ non è restituito in forma chiusa (correzione di ramo
    dell'arcotangente), il passo cita il valore già calcolato."""
    variazione = {**TOOL.example, "metodo_tensioni": "newmark"}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "fette" in t.titolo.lower())
    passo_sigma = next(p for p in traccia.passi if p.simbolo.startswith("Δσ_"))
    assert passo_sigma.formula == "Δσ_Newmark"
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_z_crit_automatico():
    """Nessun `z_crit_input`: la profondità critica utilizzata è la radice calcolata per bisezione,
    non un valore manuale."""
    variazione = {**TOOL.example, "z_crit_input": None}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "critica" in t.titolo)
    passo = next(p for p in traccia.passi if p.simbolo == "Z_crit")
    assert passo.formula == "Z_crit,calc"
    assert passo.risultato == pytest.approx(report.data.profondita_critica.z_crit_calcolato_m)
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_falda_sopra_il_piano_di_posa():
    """Falda più superficiale del piano di posa: il sovraccarico rimosso usa il peso di volume
    alleggerito γ−γw sotto falda, non il peso totale."""
    variazione = {**TOOL.example, "d": 2.0, "falda": 100.0}  # D=2 m, falda=1 m (tecnico: cm)
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "Pressione" in t.titolo)
    passo = next(p for p in traccia.passi)
    assert "Zw" in passo.formula
    assert passo.risultato == pytest.approx(report.data.carico.q_prime_kPa)
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_z_crit_cosi_superficiale_che_nessuna_fetta_e_tracciata():
    """Z,crit più superficiale della prima fetta non degenere: la traccia non elenca alcuna coppia
    Δσ/ΔH individuale, il cedimento totale resta 0."""
    variazione = {**TOOL.example, "z_crit_input": 5}  # 0,05 m: sotto la prima fetta reale (0,1 m)
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.cedimento.w_ed_cm == pytest.approx(0.0)
    traccia = next(t for t in report.relazione if "fette" in t.titolo.lower())
    assert not any(p.simbolo.startswith("Δσ_") for p in traccia.passi)
    passo_totale = next(p for p in traccia.passi if p.simbolo == "w_ed")
    assert passo_totale.risultato == pytest.approx(0.0)
    assert_relazione_coerente(TOOL, variazione)


def test_w_ed_e_z_crit_sono_spiegati_come_evidenziati():
    """I due output evidenziati del pacchetto (`w_ed`, `Z_crit`) appaiono come `Passo.simbolo`."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    simboli = {p.simbolo for t in report.relazione for p in t.passi}
    assert "w_ed" in simboli
    assert "Z_crit" in simboli
