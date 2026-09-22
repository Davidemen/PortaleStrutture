"""`relazione.py` (docs/architecture-phase2.md §6, wave-2 adoption): the harness on the tool's own
example, on every oracle input set of `test_oracle.py` (`acciaio_colonna_ec3_oracle.json`) — run
here in STANDARD mode, since `relazione` only describes the code-standard branch
(docs/architecture-phase2.md §1) and the oracle fixture itself was recorded with `legacy_compat=
True` — plus dedicated variations that switch branches: a governing M_N,Rd,z reduction (n>a, eq.
6.39b instead of the trivial 6.39a), the default (non-overridden) γ_M0/γ_M1 resolution, and a
shear-elevated reduction on ONE axis only (the oracle set's own case only exercises both at once).

The tool has a single golden/example case (`tool.ESEMPIO_AUREO` minus `legacy_compat`, identical to
`TOOL.example`, see `test_golden.py`); oracle case 0 duplicates it as case 0 of the LibreOffice
recalculation. Oracle case 3 ("class 4", `test_oracle.py`'s own comment) is unsupported outside
`legacy_compat` (`sezione.verifica_classe_supportata` raises `CalcError`, docs/architecture-phase2.md
§1 requires `report.ok`); it is fed back with `classe_sezione` overridden to "class 3" (its own
h/b>2 -> curva "d" scenario, unrelated to the class-4 gap, is otherwise unchanged) — mirroring
`ca_punzonamento.test_relazione`'s own `phi_staffa_mm` override for the same reason.
"""
from typing import Any

import pytest

from strutture.members.acciaio_colonna_ec3.tool import TOOLS
from strutture.shared.tool import execute
from tests.members.acciaio_colonna_ec3.test_oracle import _CASI as ORACLE_CASI
from tests.members.acciaio_colonna_ec3.test_oracle import FIXTURE as ORACLE_FIXTURE
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "acciaio-colonna-h-ec3")

_CLASSE_4_NON_SUPPORTATA_STANDARD = 3  # indice del caso oracolo "class 4" in CASI_CAMPI


def _oracle_raw_inputs(index: int) -> dict[str, Any]:
    raw = {**ORACLE_CASI[index], "legacy_compat": False}
    if index == _CLASSE_4_NON_SUPPORTATA_STANDARD:
        raw["classe_sezione"] = "class 3"
    return raw


VARIAZIONI = {
    # M_N,Rd,z governato dal ramo quadratico (n > a, eq. 6.39b) invece del ramo banale (eq. 6.39a):
    # nessun caso oracolo/esempio lo raggiunge (Nsd resta modesto ovunque).
    "n-maggiore-di-a-eq-6-39b": {**TOOL.example, "nsd_kN": 1500.0},
    # γ_M0/γ_M1 non sovrascritti dall'utente: risolti al valore normativo EC3 senza warning
    # (`materiale._risolvi_gamma`'s `valore_utente is None` branch, mai esercitato dall'esempio/
    # dall'oracolo, che impostano sempre un valore numerico esplicito).
    "gamma-non-sovrascritti": {**TOOL.example, "gamma_m0": None, "gamma_m1": None},
    # Riduzione per taglio elevato su un solo asse (oracle case 2 la innesca su ENTRAMBI): qui solo
    # V_y,sd supera la soglia, M_Rd,z resta sul ramo non ridotto.
    "riduzione-taglio-solo-asse-y": {**TOOL.example, "vy_sd_kN": 700.0},
}


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.oracle
@pytest.mark.parametrize("index", range(len(ORACLE_FIXTURE)), ids=range(len(ORACLE_FIXTURE)))
def test_relazione_coerente_sui_casi_oracolo(index: int):
    assert_relazione_coerente(TOOL, _oracle_raw_inputs(index))


@pytest.mark.parametrize("raw", VARIAZIONI.values(), ids=VARIAZIONI.keys())
def test_relazione_coerente_sulle_variazioni(raw):
    assert_relazione_coerente(TOOL, raw)


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_step_count_within_budget():
    """docs/architecture-phase2.md §6's "8-25 steps" is a TARGET, not a hard ceiling: the review
    (finding MISSING_STEP) asked for explicit lookup/derivation steps this 11-Check tool was
    missing (k_yy/k_yz/k_zy/k_zz, λ_w/χ_w, α_yy/α_zz, C_1) — 9 steps beyond the previous 30, still
    a small fraction of a tool this size (11 Check + several informative branches)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 40


def test_relazione_covers_every_check_the_tool_declares():
    """Every `Check.name` of `tool.py::run` must appear as a `Passo` with a non-empty `esito`
    somewhere in the trace (docs/architecture-phase2.md §6: "every Check"). `Traccia F`'s h_w/t_w
    threshold adds ONE extra esito-bearing `Passo` that maps to no `Check` (§5.1(2)'s trigger
    condition, not itself a safety verification), so containment is asserted, not equality."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert len(report.checks) == 11
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks) + 1
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_moduli_diversi_per_vpl_rd_anima_e_vpl_rd_ali():
    """`ColonnaEc3Output.taglio` dà LO STESSO hint UI `symbol` "V_pl,Rd" a `vpl_rd_anima_kN` e
    `vpl_rd_ali_kN` — riusarlo per entrambi i `Passo` collide (un solo simbolo, due valori diversi
    nella stessa traccia); qui devono restare distinti."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo == "Resistenza a taglio")
    simboli = {p.simbolo for p in traccia.passi}
    assert simboli == {"V_pl,Rd,w", "V_pl,Rd,f"}


def test_mpl_rd_distinto_da_mrd():
    """`M_c,y,Rd` (Annex A/interazione, senza riduzione per taglio) e `M_Rd,y` (§6.2.5/§6.2.8, CON
    riduzione) sono due grandezze diverse: devono restare simboli distinti anche quando coincidono
    numericamente (come sull'esempio, dove il taglio non innesca la riduzione). L'esempio è classe
    3 (`tool.py`): il modulo impiegato è quello ELASTICO, quindi il simbolo non può essere
    "M_pl" (review finding WRONG_CLAUSE: "M_pl,y,Rd = W_el,y·f_yd" è autocontraddittorio)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passi = {p.simbolo: p for t in report.relazione for p in t.passi}
    assert "M_c,y,Rd" in passi
    assert "M_pl,y,Rd" not in passi
    assert "M_Rd,y" in passi
    assert passi["M_c,y,Rd"].simbolo != passi["M_Rd,y"].simbolo
    assert passi["M_c,y,Rd"].formula.startswith("W_el,y")


def test_verifiche_semplificate_dichiarano_che_sono_un_criterio_classe_1_2():
    """review finding WRONG_CLAUSE: il blocco 'Verifiche semplificate di riscontro' applica
    EN1993-1-1 §6.2.9.1, titolato 'Class 1 and 2 cross-sections' (la classe 3 è §6.2.9.2, criterio
    elastico σ≤fy/γM0) — l'esempio è dichiarato classe 3 (`tool.py`). Il titolo deve dirlo."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "semplificate" in t.titolo.lower())
    assert "classe 1" in traccia.titolo.lower() or "classe 1-2" in traccia.titolo.lower()


def test_i56_cita_6_2_9_1_6_eq_6_41_non_6_2_1_7():
    """review finding WRONG_CLAUSE: (My/MN,y)²+(Mz/MN,z)^max(5n,1) è l'eq. (6.41) di §6.2.9.1(6),
    non §6.2.1(7) (il modulo stesso lo dice nel proprio docstring)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("I56"))
    assert "6.2.9.1" in passo.clausola
    assert "6.41" in passo.clausola
    assert "6.2.1(7)" not in passo.clausola


def test_m_n_rd_z_riporta_il_ramo_n_su_a_nel_simbolo():
    """review finding MISSING_STEP: 'M_N,Rd,z = M_pl,z,Rd' è vero solo nel ramo n ≤ a (eq. 6.39a);
    `nota` non è mai stampata da `traccia_a_testo`, quindi la condizione deve comparire nel simbolo."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("M_N,Rd,z"))
    assert passo.simbolo != "M_N,Rd,z"
    variazione = execute(TOOL, {**TOOL.example, "nsd_kN": 1500.0}, con_relazione=True)
    passo_alto = next(p for t in variazione.relazione for p in t.passi if p.simbolo.startswith("M_N,Rd,z"))
    assert passo_alto.simbolo != passo.simbolo


def test_utilizzo_yy_e_zz_citano_le_rispettive_equazioni():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo_yy = next(p for t in report.relazione for p in t.passi if p.simbolo == "N_Ed/N_Rd + ΣM_Ed/M_Rd (yy)")
    passo_zz = next(p for t in report.relazione for p in t.passi if p.simbolo == "N_Ed/N_Rd + ΣM_Ed/M_Rd (zz)")
    assert "6.61" in passo_yy.clausola
    assert "6.62" in passo_zz.clausola


def test_kij_citano_lannex_a():
    """Il compito richiede di dichiarare da quale annex provengono i fattori k_ij (Annex A Tab. A.1,
    non Annex B, che dà invece i soli C_m di Tab. B.3): ora nel Passo dedicato k_yy (non più nel
    Valore inline, "calcolato sopra" riferendosi a quel Passo)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo_yy = next(p for t in report.relazione for p in t.passi if p.simbolo == "N_Ed/N_Rd + ΣM_Ed/M_Rd (yy)")
    k_yy_inline = next(v for v in passo_yy.valori if v.simbolo == "k_yy")
    assert k_yy_inline.descrizione == "calcolato sopra"
    passo_k_yy = next(p for t in report.relazione for p in t.passi if p.simbolo == "k_yy")
    assert "Annex A" in passo_k_yy.clausola
    assert "Tab. A.1" in passo_k_yy.clausola


def test_k_ij_hanno_un_passo_proprio():
    """review finding MISSING_STEP: k_yy/k_yz/k_zy/k_zz sono le grandezze più elaborate di tutta
    la verifica ma non avevano alcun passo dedicato (solo un Valore inline nella formula di
    utilizzo) — a differenza di C_my/C_mz/C_mLT, che un passo dedicato ce l'hanno già."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passi = {p.simbolo: p for t in report.relazione for p in t.passi}
    for k in ("k_yy", "k_yz", "k_zy", "k_zz"):
        assert k in passi, f"manca un Passo dedicato per {k}"
        assert "Annex A" in passi[k].clausola
        assert "Tab. A.1" in passi[k].clausola


def test_alpha_e_c1_hanno_un_passo_proprio():
    """review finding MISSING_STEP: α_yy/α_zz (curve di instabilità, Tab. 6.1/6.2) e C_1 (fattore
    del diagramma dei momenti) erano letterali senza alcun passo di lookup/derivazione."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passi = {p.simbolo: p for t in report.relazione for p in t.passi}
    for simbolo in ("α_yy", "α_zz", "C_1"):
        assert simbolo in passi, f"manca un Passo dedicato per {simbolo}"


def test_domanda_di_taglio_non_usa_la_convenzione_di_assi_ec3():
    """review finding MISLEADING: il codice appaia la capacità dell'ANIMA con `vy_sd_kN` e quella
    delle ALI con `vz_sd_kN` — l'opposto della convenzione di EN1993-1-1 (V_z,Ed nel piano
    dell'anima, V_y,Ed nel piano delle ali). Non potendo toccare models.py/taglio.py (codice di
    calcolo), la traccia evita del tutto la notazione V_y,sd/V_z,sd sulla domanda di taglio."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo == "Resistenza a taglio")
    for passo in traccia.passi:
        assert "V_y,sd" not in passo.formula
        assert "V_z,sd" not in passo.formula
        for v in passo.valori:
            assert v.simbolo not in ("V_y,sd", "V_z,sd")
    passo_anima = next(p for p in traccia.passi if p.simbolo == "V_pl,Rd,w")
    passo_ali = next(p for p in traccia.passi if p.simbolo == "V_pl,Rd,f")
    assert any(v.simbolo == "V_Ed,w" for v in passo_anima.valori)
    assert any(v.simbolo == "V_Ed,f" for v in passo_ali.valori)


def test_taglio_instabilita_non_usa_v_y_sd():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "instabilità per taglio" in t.titolo.lower())
    passo_vb = next(p for p in traccia.passi if p.simbolo == "V_b,Rd")
    assert "V_y,sd" not in passo_vb.formula
    assert any(v.simbolo == "V_Ed,w" for v in passo_vb.valori)


def test_hw_tw_soddisfatta_significa_snellezza_rispettata():
    """review finding MISLEADING: h_w/t_w > limite è una condizione di innesco (verifica di
    instabilità a taglio richiesta), non una verifica; con l'esempio (dove il ramo scatta:
    `taglio_instab.richiede_verifica`), stampare 'soddisfatta' per quel caso lo farebbe leggere
    come un esito favorevole. Si inverte il confronto: 'soddisfatta' significa che il limite di
    snellezza è rispettato (nessuna instabilità a taglio da verificare)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "h_w/t_w")
    atteso = "non soddisfatta" if report.data.taglio_instabilita.richiede_verifica else "soddisfatta"
    assert passo.esito == atteso
    assert "<=" in passo.formula
    assert_relazione_coerente(TOOL, TOOL.example)


def test_classe_sezione_non_calcolata_da_c_su_t():
    """Review-style guard: la classe è un dato di ingresso, non un rapporto c/t calcolato; il passo
    deve dirlo esplicitamente."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "classe")
    assert "dato di ingresso" in passo.nota
