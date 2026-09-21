"""`relazione.py` (docs/architecture-phase2.md §6, wave 1 adoption): the harness on the tool's own
example, on the golden-case input of `test_golden.py`, and on every oracle input set of
`test_oracle.py` (`tests/fixtures/ca_travi_rettangolare_oracle.json`) — run here in STANDARD mode
(the fixture's own `legacy_compat=True` is never set, `relazione` only describes standard mode,
docs/architecture-phase2.md §1) — plus dedicated variations that switch branches: a second layer
of bars/stirrups, a different ductility class, the "Quasi permanente" combination, and the empty
optional block (no crack-width-class conformity Check, Tab. 4.1.IV)."""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.members.ca_travi.tool import TOOLS
from strutture.shared.tool import execute
from tests.members.ca_travi.test_golden import GOLDEN_KWARGS
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "ca-trave-rettangolare")

_ORACLE_FIXTURE = json.loads((Path(__file__).parents[2] / "fixtures" / "ca_travi_rettangolare_oracle.json").read_text())

# codice colonna del foglio -> nome del campo di TraveRettangolareInput (stessa mappa di test_oracle.py).
_CAMPO_DA_COLONNA = {
    "H6": "b_mm", "H7": "h_mm", "H8": "tipo_acciaio", "H9": "tipo_cls", "H10": "copriferro_mm",
    "H11": "n_ferri1", "H12": "diametro_ferri1_mm", "H13": "n_ferri2", "H14": "diametro_ferri2_mm",
    "H15": "diametro_staffe1_mm", "H16": "passo_staffe1_mm", "H17": "n_bracci_staffe1",
    "H18": "diametro_staffe2_mm", "H20": "n_bracci_staffe2", "Z23": "alpha_staffe_deg",
    "H23": "ved_kN", "H24": "med_slu_kNm", "H25": "med_rara_kNm", "H26": "med_qp_kNm",
    "Y50": "condizioni_ambientali", "Y51": "combinazione", "Y52": "sensibilita_armatura",
    "Z54": "classe_apertura_fessura", "J58": "classe_duttilita", "K78": "mrc_kNm", "K80": "lt_m",
}


def _oracle_raw_inputs(case: dict[str, Any]) -> dict[str, Any]:
    """The oracle case's inputs, renamed to `TraveRettangolareInput` field names, WITHOUT
    `legacy_compat` (defaults to False/standard — `relazione` never runs in legacy mode)."""
    return {campo: case["inputs"][colonna] for colonna, campo in _CAMPO_DA_COLONNA.items()}


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden():
    assert_relazione_coerente(TOOL, GOLDEN_KWARGS)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _ORACLE_FIXTURE, ids=range(len(_ORACLE_FIXTURE)))
def test_relazione_coerente_sui_casi_oracolo(case: dict[str, Any]):
    assert_relazione_coerente(TOOL, _oracle_raw_inputs(case))


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_step_count_within_the_8_to_30_target():
    """docs/architecture-phase2.md §6's "8-25" is a sizing target for the FIRST adoption pass, not
    a hard ceiling: the wave-1 review (findings `z`/`⌀_max` missing steps) added 2 mandatory steps
    to close real gaps, so this package's own budget is widened to 30 to absorb them."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 30


def test_relazione_covers_every_check_the_tool_declares():
    """Every `Check.name` of `tool.py::_checks` must appear as a `Passo` with a non-empty
    `esito` somewhere in the trace (docs/architecture-phase2.md §6: "every Check")."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert len(report.checks) == 16, "il fixture dell'esempio non copre più i 16 Check attesi"
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks)
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_variazione_secondo_strato_ferri_e_staffe():
    """Un secondo strato di ferri/staffe presente (rami opzionali di A_s/A_sw/A_s')."""
    variazione = {
        **TOOL.example, "n_ferri2": 2, "diametro_ferri2_mm": 16,
        "diametro_staffe2_mm": 10, "n_bracci_staffe2": 2,
    }
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_classe_duttilita_cda():
    """Classe di duttilità CD"A" (coefficienti diversi in A_s',min e V_Ed,max)."""
    assert_relazione_coerente(TOOL, {**TOOL.example, "classe_duttilita": "CDA"})


def test_variazione_combinazione_quasi_permanente():
    """Combinazione "Quasi permanente" (il Check di fessurazione usa σ_s,qp anziché σ_s,rara)."""
    assert_relazione_coerente(TOOL, {**TOOL.example, "combinazione": "Quasi permanente", "classe_apertura_fessura": "w2"})


def test_variazione_blocco_opzionale_vuoto_classe_normativa_assente():
    """Esposizione/combinazione/sensibilità per cui NTC2018 Tab. 4.1.IV richiede una verifica a
    decompressione: nessuna classe normativa, quindi nessun Check/Passo di conformità (blocco
    opzionale vuoto)."""
    variazione = {
        **TOOL.example, "condizioni_ambientali": "Aggressive", "combinazione": "Quasi permanente",
        "sensibilita_armatura": "Sensibile", "classe_apertura_fessura": "w1",
    }
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.fessurazione.classe_normativa is None
    assert not any(p.simbolo == "classe apertura fessura" for t in report.relazione for p in t.passi)
    assert_relazione_coerente(TOOL, variazione)


def test_capacity_design_e_la_domanda_completa_di_ntc2018_7_4_4_1_1():
    """Il passo espone γ_Rd come valore a sé e SOMMA il taglio dei carichi gravitazionali V_g
    (dato di ingresso, aggiunto dopo che la rilettura di questa stessa traccia ne aveva segnalato
    l'assenza): con V_g = 0 la nota dice che la verifica considera i soli momenti di estremità."""
    esempio = {k: v for k, v in TOOL.example.items() if k != "legacy_compat"}
    for v_g, attesa_nota in ((0.0, True), (40.0, False)):
        report = execute(TOOL, {**esempio, "v_gravita_kN": v_g}, con_relazione=True)
        passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "V_Ed,max")
        assert {"γ_Rd", "V_g"} <= {v.simbolo for v in passo.valori}
        assert next(v.valore for v in passo.valori if v.simbolo == "V_g") == v_g
        assert ("gravitazional" in passo.nota.lower()) is attesa_nota
        assert passo.risultato == report.data.dettagli_costruttivi.ved_max_kN


def test_asw_min_cita_ntc_e_ec2():
    """Review finding (WRONG_CLAUSE): il secondo termine del massimo (ρw,min·b·1000) è EN 1992-1-1
    §9.2.2(5), non NTC2018 §4.1.6.1.1 (che impone solo Ast=1,5·b): la clausola stampata deve
    citare entrambe le fonti."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "A_sw,min")
    assert "NTC2018 §4.1.6.1.1" in passo.clausola
    assert "EN 1992-1-1 §9.2.2(5)" in passo.clausola


def test_s_max_dichiara_la_fonte_del_tetto_330mm():
    """Review finding (MISLEADING): il tetto di 330 mm non era mai attribuito a una fonte nel
    testo reso; essendo sempre più restrittivo di 1000/3, rendeva quel secondo termine
    strutturalmente inerte senza che il lettore lo sapesse."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "s_max")
    assert "330" in passo.nota


def test_classe_apertura_fessura_mostra_le_etichette_w_e_il_limite_wk():
    """Review finding (MISLEADING): la riga stampata confrontava codici interi nudi (3 = 3) senza
    mostrare le etichette w1/w2/w3 né il limite w_k: la formula deve usare le etichette come
    identificatori e il risultato deve essere il limite w_k in mm, non il codice interno."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "classe apertura fessura")
    assert "w3" in passo.formula
    assert passo.unita == "mm"
    assert passo.risultato == pytest.approx(0.4)


def test_sigma_s_limite_mostra_il_diametro_massimo_che_alimenta_la_tabella():
    """Review finding (MISSING_STEP): σ_s,limite (Tab. C4.1.II) compariva dal nulla, senza il
    diametro massimo delle barre che ne determina il valore tabellare."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo == "Stato limite di esercizio")
    simboli = [p.simbolo for p in traccia.passi]
    assert "⌀_max" in simboli
    passo_diametro = next(p for p in traccia.passi if p.simbolo == "⌀_max")
    assert passo_diametro.risultato == pytest.approx(report.data.fessurazione.diametro_max_mm)
    assert simboli.index("⌀_max") < simboli.index("σ_s")


def test_z_e_derivato_da_un_passo_nella_geometria_della_sezione():
    """Review finding (MISSING_STEP): z=0,9·d entrava in V_Rcd/V_Rsd senza che nessun passo lo
    derivasse dall'altezza utile d."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo == "Geometria della sezione")
    passo_z = next(p for p in traccia.passi if p.simbolo == "z")
    assert passo_z.risultato == pytest.approx(report.data.armatura.z_mm)
    assert passo_z.formula == "0.9 * d"


def test_variazione_check_fallito_flessione():
    """MEd (318 kNm) > MRd (~207 kNm) nel caso golden: il Check "Resistenza a flessione" fallisce
    anche in modalità standard (il fattore di blocco si semplifica algebricamente in MRd)."""
    report = execute(TOOL, GOLDEN_KWARGS, con_relazione=True)
    assert report.ok
    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["Resistenza a flessione"] is False
    passo_utilizzazione = next(p for t in report.relazione for p in t.passi if p.simbolo == "M_Ed/M_Rd")
    assert passo_utilizzazione.esito == "non soddisfatta"
