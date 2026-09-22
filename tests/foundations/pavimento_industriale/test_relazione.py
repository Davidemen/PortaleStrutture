"""`relazione.py` (docs/architecture-phase2.md §6, wave-2/3 adoption): the harness on the tool's own
example, on the golden case of `test_golden.py` and on every oracle case of `test_oracle.py`
(`tests/fixtures/pavimento_industriale_oracle.json`) — run here in STANDARD mode
(`legacy_compat=False`: `relazione` never runs in legacy mode) — plus variations that switch
branches: a manual `kT` (no Winkler-table lookup), the EN 1992-1-1:2004 punching coefficient
(0,5 instead of the 0,4 default), and a `carichi` table whose case name and row count differ from
the example (a different case governs, exercising the per-Check "own governing row" lookup instead
of the overall `governante` row)."""
import json
from pathlib import Path
from typing import Any

import pytest

from strutture.foundations.pavimento_industriale.tool import TOOLS
from strutture.shared.tool import execute
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "fond-pavimento-industriale")

_FIXTURES = Path(__file__).parents[2] / "fixtures"
_ORACLE_FIXTURE = json.loads((_FIXTURES / "pavimento_industriale_oracle.json").read_text(encoding="utf-8"))

_GOLDEN_KWARGS = {
    "classe_calcestruzzo": "C25/30", "gamma_c": 1.5, "gamma_s": 1.15, "nu_poisson": 0.2,
    "sottofondo_tipo": "materiale di riporto costipato", "kt_manuale_N_mm3": None,
    "h_mm": 200, "c_mm": 30, "phi_rete_mm": 8, "passo_rete_mm": 200,
    "g_daN_m2": 0.0, "gamma_g": 1.3, "q_daN_m2": 2600, "gamma_q": 1.5, "psi1_distribuito": 0.9,
    "carichi": [
        {"caso": "ruota motrice", "posizione": "centro", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
        {"caso": "ruota motrice", "posizione": "bordo", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
        {"caso": "ruota motrice", "posizione": "spigolo", "p_kN": 15.5, "impronta_a_mm": 500, "impronta_b_mm": 100, "gamma": 1.5, "psi1": 0.9},
    ],
    "a_contrazione_m": 20, "b_contrazione_m": 18, "a_isolamento_m": 30.9, "b_isolamento_m": 21.2,
    "alpha_termico": 1e-5, "delta_t_C": 30,
}

_ORACLE_DEFAULTS = {
    "C4": "C25/30", "C24": "materiale di riporto costipato", "C27": 200, "C28": 30,
    "G4": 0, "G6": 2600,
    "L5": 15.5, "L6": 1.5, "L7": 0.9, "M5": 15.5, "M6": 1.5, "M7": 0.9, "N5": 15.5, "N6": 1.5, "N7": 0.9,
    "L10": 500, "M10": 500, "N10": 500, "L11": 100, "M11": 100, "N11": 100,
}
_ORACLE_POSIZIONI = {"L": "centro", "M": "bordo", "N": "spigolo"}


def _oracle_raw_inputs(case: dict[str, Any]) -> dict[str, Any]:
    """The oracle case's inputs, renamed to `PavimentoIndustrialeInput` field names, WITHOUT
    `legacy_compat` (defaults to False/standard — `relazione` never runs in legacy mode)."""
    merged = {**_ORACLE_DEFAULTS, **case["inputs"]}
    carichi = [
        {
            "caso": "ruota motrice", "posizione": posizione, "p_kN": merged[f"{col}5"], "gamma": merged[f"{col}6"],
            "psi1": merged[f"{col}7"], "impronta_a_mm": merged[f"{col}10"], "impronta_b_mm": merged[f"{col}11"],
        }
        for col, posizione in _ORACLE_POSIZIONI.items()
    ]
    return {
        "classe_calcestruzzo": merged["C4"], "sottofondo_tipo": merged["C24"], "kt_manuale_N_mm3": None,
        "h_mm": merged["C27"], "c_mm": merged["C28"], "phi_rete_mm": 8, "passo_rete_mm": 200,
        "g_daN_m2": merged["G4"], "q_daN_m2": merged["G6"], "carichi": carichi,
        "a_contrazione_m": 20, "b_contrazione_m": 18, "a_isolamento_m": 30.9, "b_isolamento_m": 21.2,
        "alpha_termico": 1e-5, "delta_t_C": 30,
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


def test_relazione_covers_every_check_the_tool_declares():
    """Every `Check.name` of `tool.py::run` must appear as a `Passo` with a non-empty `esito`
    somewhere in the trace (13 Check: 6 carico distribuito + 5 carichi concentrati + 2 giunti)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert len(report.checks) == 13
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks)
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_ogni_highlight_output_e_un_passo_simbolo():
    """`l` (Westergaard), e `TL_max` (evidenziato sia da `VerificheDistribuitoResult.tl_massimo`
    sia da `RigaCaricoResult.utilizzo_max` — stesso simbolo, un solo Passo basta a spiegare entrambi)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    simboli = {p.simbolo for t in report.relazione for p in t.passi}
    assert "l" in simboli
    assert "TL_max" in simboli


def test_variazione_kt_manuale():
    """`kt_manuale_N_mm3` sostituisce la ricerca tabellare Winkler."""
    variazione = {**TOOL.example, "sottofondo_tipo": None, "kt_manuale_N_mm3": 0.05}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "Materiali" in t.titolo)
    passo_l = next(p for p in traccia.passi if p.simbolo == "l")
    assert passo_l.risultato == pytest.approx(report.data.sottofondo.l_mm)
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_coefficiente_vrd_max_en_2004():
    """`coeff_vrd_max=0,5` (EN 1992-1-1:2004 + Appendice Nazionale italiana) invece del default
    0,4 (A1:2014): il passo V_Rd,max lo cita come valore d'ingresso."""
    variazione = {**TOOL.example, "coeff_vrd_max": 0.5}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "resistenze di punzonamento" in t.titolo)
    passo = next(p for p in traccia.passi if p.simbolo == "V_Rd,max")
    assert next(v.valore for v in passo.valori if v.simbolo == "c") == pytest.approx(0.5)
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_caso_diverso_e_due_sole_righe():
    """Nome del caso di carico diverso da 'ruota motrice' e solo 2 righe (centro/spigolo): la
    traccia delle tensioni di Westergaard segue il caso governante, non un nome hardcoded."""
    variazione = {
        **TOOL.example,
        "carichi": [
            {"caso": "carrello X", "posizione": "centro", "p_kN": 10.0, "impronta_a_mm": 200, "impronta_b_mm": 200, "gamma": 1.5, "psi1": 0.9},
            {"caso": "carrello X", "posizione": "spigolo", "p_kN": 12.0, "impronta_a_mm": 200, "impronta_b_mm": 200, "gamma": 1.5, "psi1": 0.9},
        ],
    }
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "interno/bordo/spigolo" in t.titolo)
    assert len(traccia.passi) == 2
    assert {p.simbolo for p in traccia.passi} == {"σ_c,max (centro)", "σ_c,max (spigolo)"}
    assert_relazione_coerente(TOOL, variazione)


def test_punzonamento_u0_e_u1_possono_essere_governati_da_righe_diverse():
    """Nell'esempio del tool, u0 è governato da 'ruote anteriori/centro' e u1 da 'ruota
    motrice/spigolo' — righe diverse fra loro e dalla riga governante complessiva ('ruota
    motrice/bordo'): ogni Check usa la propria riga, non quella complessiva."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert report.data.concentrati.governante.caso == "ruota motrice"
    assert report.data.concentrati.governante.posizione == "bordo"
    inviluppo = {e.grandezza: (e.caso, e.posizione) for e in report.data.concentrati.inviluppo}
    assert inviluppo["Punzonamento a u0"] == ("ruote anteriori", "centro")
    assert inviluppo["Punzonamento a u1"] == ("ruota motrice", "spigolo")
    traccia = next(t for t in report.relazione if t.titolo == "Verifiche dei carichi concentrati")
    passo_u0 = next(p for p in traccia.passi if p.simbolo.startswith("TL_u0"))
    passo_u1 = next(p for p in traccia.passi if p.simbolo.startswith("TL_u1"))
    assert passo_u0.risultato != pytest.approx(report.data.concentrati.governante.tl_punzonamento_u0)
    assert passo_u0.risultato == pytest.approx(
        next(e.valore for e in report.data.concentrati.inviluppo if e.grandezza == "Punzonamento a u0")
    )
    assert passo_u1.risultato == pytest.approx(
        next(e.valore for e in report.data.concentrati.inviluppo if e.grandezza == "Punzonamento a u1")
    )


def test_m_rd_non_si_chiama_nmm_m():
    """review finding MISLEADING: A_s·0,9d·f_yd = 251,3 mm²/m · 153 mm · 391,3 MPa = 1,505e7
    N·mm/m; la formula divide per 1000 (mm->m), quindi il risultato stampato (15050) è in
    N·m/m, non in 'Nmm/m' come etichettato — un fattore 1000 di differenza. L'harness non
    confronta le stringhe di unità con l'output (solo la loro presenza), quindi la traccia può
    correggere l'etichetta senza toccare `armatura.py`."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "Materiali" in t.titolo)
    passo_mrd = next(p for p in traccia.passi if p.simbolo == "M_Rd")
    assert passo_mrd.unita != "Nmm/m"
    assert passo_mrd.unita in ("N·m/m", "Nm/m")


def test_m_rd_riusato_nelle_verifiche_ha_la_stessa_unita_corretta():
    traccia = next(t for t in execute(TOOL, TOOL.example, con_relazione=True).relazione if t.titolo == "Verifiche dei carichi concentrati")
    passo_as = next(p for p in traccia.passi if p.simbolo.startswith("TL_As"))
    valore_mrd = next(v for v in passo_as.valori if v.simbolo == "M_Rd")
    assert valore_mrd.unita != "Nmm/m"


def test_righe_di_inviluppo_nominano_caso_e_posizione_governanti():
    """review finding MISLEADING: ogni riga TL_*(inviluppo) sostituisce valori da una riga di
    carico DIVERSA (beta, P, b_x/b_y cambiano riga per riga) senza nominarla: il simbolo stampato
    deve nominare il caso e la posizione governanti, come le righe σ già fanno con
    (centro)/(bordo)/(spigolo)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo == "Verifiche dei carichi concentrati")
    inviluppo = {e.grandezza: (e.caso, e.posizione) for e in report.data.concentrati.inviluppo}
    attese = {
        "TL_σ": inviluppo["Tensionale (Westergaard)"],
        "TL_f": inviluppo["Fessurazione"],
        "TL_As": inviluppo["Armatura"],
        "TL_u0": inviluppo["Punzonamento a u0"],
        "TL_u1": inviluppo["Punzonamento a u1"],
    }
    for prefisso, (caso, posizione) in attese.items():
        passo = next(p for p in traccia.passi if p.simbolo.startswith(prefisso))
        assert caso in passo.simbolo, f"{prefisso}: manca il caso {caso!r} in {passo.simbolo!r}"
        assert posizione in passo.simbolo, f"{prefisso}: manca la posizione {posizione!r} in {passo.simbolo!r}"


def test_b_formula_segue_il_ramo_effettivamente_usato():
    """Un'impronta molto grande rispetto allo spessore fa cadere r_r/h oltre la soglia 1,724: la
    formula stampata deve seguire quel ramo (b=r_r), non sempre la correzione di Westergaard."""
    variazione = {
        **TOOL.example,
        "carichi": [{"caso": "grande", "posizione": "centro", "p_kN": 10.0, "impronta_a_mm": 650, "impronta_b_mm": 650, "gamma": 1.5, "psi1": 0.9}],
    }
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if "geometria di contatto" in t.titolo)
    passo_b = next(p for p in traccia.passi if p.simbolo == "b")
    assert passo_b.formula == "sqrt(b_x * b_y / π)"
    assert_relazione_coerente(TOOL, variazione)
