"""`relazione.py` (docs/architecture-phase2.md §6, wave 2 adoption): the harness on the tool's own
example, on the golden-case input of `conftest.py` and on every oracle input set of `test_oracle.py`
— run here in STANDARD mode (`legacy_compat=False`; the golden/oracle fixtures' own `legacy_compat=
True` is never set, `relazione` only describes standard mode, docs/architecture-phase2.md §1) — plus
dedicated variations that switch branches: another pile schema (single-row strut-and-tie, no diagonal
tie XY), another vRd,max coefficient (EN 1992-1-1:2004 + Appendice Nazionale italiana), a failing
check, a tension pile (filled "Capacità portante ... (trazione)" block) and no tension pile (that
same block empty, the tool's own example)."""
from typing import Any

import pytest

from strutture.foundations.plinti_pali.tool import TOOLS
from strutture.shared.tool import execute
from tests.foundations.plinti_pali.conftest import GOLDEN_SCALARI
from tests.foundations.plinti_pali.test_oracle import CASO_SCALARI
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "fond-plinto-su-pali")

_CAMPI_ORACOLO = (
    "h_plinto_m", "copriferro_cm", "lx_m", "ly_m", "diametro_long_assunto_mm", "av_mm",
    "classe_calcestruzzo", "grado_acciaio", "bx_pilastro_m", "by_pilastro_m", "diametro_pila_mm",
)


def _oracle_raw_inputs(caso: tuple[Any, ...], golden_rows) -> dict[str, Any]:
    """Same scalars/rows as `test_oracle.py::test_oracle_inviluppo_flessione_puntoni_taglio`,
    WITHOUT `legacy_compat` (defaults to False/standard — `relazione` never runs in legacy mode)."""
    scalari = dict(zip(_CAMPI_ORACOLO, caso, strict=True))
    return {
        "schema_pali": "2x2", "lx_m": scalari["lx_m"], "ly_m": scalari["ly_m"],
        "ax_m": 4.0, "by_m": 4.0, "h_plinto_m": scalari["h_plinto_m"], "copriferro_cm": scalari["copriferro_cm"],
        "bx_pilastro_m": scalari["bx_pilastro_m"], "by_pilastro_m": scalari["by_pilastro_m"],
        "diametro_pila_mm": scalari["diametro_pila_mm"], "diametro_long_assunto_mm": scalari["diametro_long_assunto_mm"],
        "av_mm": scalari["av_mm"], "resistenza_pila_compressione_kN": 2000.0,
        "carico_aggiuntivo_kN": 550.7008, "gamma_g1": 1.3,
        "classe_calcestruzzo": scalari["classe_calcestruzzo"], "grado_acciaio": scalari["grado_acciaio"],
        "gamma_s": 1.15, "gamma_c": 1.5,
        "diametro_inf_x_mm": 24.0, "passo_inf_x_mm": 100.0, "diametro_inf_y_mm": 24.0, "passo_inf_y_mm": 100.0,
        "diametro_sup_x_mm": 24.0, "passo_sup_x_mm": 200.0, "diametro_sup_y_mm": 24.0, "passo_sup_y_mm": 200.0,
        "diametro_tirante_xy_mm": 32.0, "n_tirante_xy": 2,
        "diametro_tirante_x_mm": 24.0, "n_tirante_x": 8, "diametro_tirante_y_mm": 24.0, "n_tirante_y": 8,
        "reazioni": golden_rows,
    }


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden(golden_rows):
    assert_relazione_coerente(TOOL, {**GOLDEN_SCALARI, "reazioni": golden_rows, "legacy_compat": False})


@pytest.mark.oracle
@pytest.mark.parametrize("caso", CASO_SCALARI, ids=range(len(CASO_SCALARI)))
def test_relazione_coerente_sui_casi_oracolo(caso: tuple[Any, ...], golden_rows):
    assert_relazione_coerente(TOOL, _oracle_raw_inputs(caso, golden_rows))


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_step_count_within_target():
    """docs/architecture-phase2.md §6's "8-25" is a sizing target for the FIRST adoption pass, not a
    hard ceiling (`ca_travi.relazione`'s own test widens it to 30 for the same reason): this tool
    composes 4 analyst sub-tools (envelope, flexure, strut-and-tie, shear/punching) into one trace,
    so its own budget is wider still."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 10 <= totale <= 45


def test_relazione_covers_every_check_the_tool_declares():
    """Every `Check` of `tool.py::_checks` must appear as a `Passo` with a non-empty `esito`
    somewhere in the trace (docs/architecture-phase2.md §6: "every Check")."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert len(report.checks) == 11, "il fixture dell'esempio non copre più gli 11 Check attesi"
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks)
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_variazione_schema_fila_singola_senza_tirante_diagonale():
    """Schema "2x1": un solo puntone/tirante (niente diagonale XY), e la direzione Y-Y (una sola fila
    di pali) passa per il ramo "trasferimento diretto del momento" di `relazione_flessione.py`/
    `relazione_armatura_superiore.py` (n_own == 1, nessun termine trave)."""
    variazione = {**TOOL.example, "schema_pali": "2x1"}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.puntoni_tiranti.tirante_xy is None
    assert not any(p.simbolo == "α" for t in report.relazione for p in t.passi)
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_altra_norma_coefficiente_vrd_max():
    """coeff_vrd_max=0,5 (EN 1992-1-1:2004 + Appendice Nazionale italiana, invece del valore
    raccomandato 0,4 di EN 1992-1-1/A1:2014)."""
    assert_relazione_coerente(TOOL, {**TOOL.example, "coeff_vrd_max": 0.5})


def test_variazione_palo_teso_blocco_trazione_pieno():
    """Un palo in trazione: il Check "Capacità portante del palo (trazione)" compare (blocco
    opzionale pieno), con un Passo di verifica dedicato."""
    variazione = {
        **TOOL.example, "resistenza_pila_trazione_kN": 50.0,
        "reazioni": [
            {"nodo": 18000, "combo": "SLU1", "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 400.0, "mx_kNm": 0.0, "my_kNm": 0.0, "mz_kNm": 0.0},
            {"nodo": 18000, "combo": "SLV_10", "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 400.0, "mx_kNm": 0.0, "my_kNm": 1500.0, "mz_kNm": 0.0},
        ],
    }
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.capacita_trazione is not None
    assert not report.data.capacita_trazione.verificato
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "N_min/R_t,d")
    assert passo.esito == "non soddisfatta"
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_blocco_opzionale_vuoto_nessun_palo_teso():
    """L'esempio del tool non ha pali tesi: il blocco "Capacità portante del palo (trazione)" è
    assente (blocco opzionale vuoto)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert report.ok
    assert report.data.capacita_trazione is None
    assert not any(p.simbolo == "N_min/R_t,d" for t in report.relazione for p in t.passi)


def test_variazione_check_fallito_capacita_compressione():
    """Resistenza ammissibile del palo troppo bassa: il Check "Capacità portante del palo
    (compressione)" fallisce anche in modalità standard."""
    variazione = {**TOOL.example, "resistenza_pila_compressione_kN": 10.0}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["Capacità portante del palo (compressione)"] is False
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "N_max/R_c,d")
    assert passo.esito == "non soddisfatta"
    assert_relazione_coerente(TOOL, variazione)


# --- review findings (wave 2, engineer proof-read) ----------------------------------------------


def test_capacita_portante_pali_etichetta_rcd_come_dato_di_progetto():
    """Review finding MISSING_STEP: R_c era etichettato come "resistenza ammissibile ... dato di
    ingresso" con clausola "Geotecnica" (non una clausola normativa): nulla dichiarava se il valore
    fornito fosse caratteristico o di progetto — NTC2018 §6.4.3.1.1/Tab. 6.4.II richiede R_c,d, non
    R_c,k. Simbolo e descrizione devono ora dichiararlo esplicitamente."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo.startswith("Capacità portante assiale"))
    passo = next(p for p in traccia.passi if p.simbolo == "N_max/R_c,d")
    assert passo.clausola == "NTC2018 §6.4.3.1.1"
    valore_rcd = next(v for v in passo.valori if v.simbolo == "R_c,d")
    assert "progetto" in valore_rcd.descrizione
    assert_relazione_coerente(TOOL, TOOL.example)


def test_puntoni_tiranti_theta_normalizzato_in_radianti_negli_argomenti_trigonometrici():
    """Review finding MISLEADING: la sostituzione mescolava θ in GRADI (nessun marcatore) e α in
    RADIANTI nella stessa riga (F_ut,X = F_us·cos(θ)·0,6·cos(α)); ora ogni argomento trigonometrico
    di questa Traccia è in radianti, come α, uniformemente."""
    variazione = {**TOOL.example, "schema_pali": "2x2"}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo.startswith("Puntoni e tiranti"))
    for simbolo in ("F_us", "A_cs", "F_ut,XY", "F_ut,X", "F_ut,Y"):
        passo = next(p for p in traccia.passi if p.simbolo == simbolo)
        if "θ" not in passo.formula:
            continue
        valore_theta = next(v for v in passo.valori if v.simbolo == "θ")
        assert valore_theta.unita == "rad", (simbolo, valore_theta)
    assert_relazione_coerente(TOOL, variazione)


def test_flessione_nomina_la_combinazione_governante_nel_titolo_e_disambigua_n():
    """Review finding MISLEADING: le Tracce di flessione non dichiaravano MAI la combinazione
    governante (diversa, in generale, da quella di "Reazioni sui pali") e il simbolo "N" veniva
    riusato per una grandezza diversa (inviluppo + peso proprio) da quella di "Reazioni sui pali"
    (colonna della sola combinazione governante lì)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert report.ok
    for direzione in ("X-X", "Y-Y"):
        traccia = next(t for t in report.relazione if f"direzione {direzione}" in t.titolo)
        assert "combinazione governante" in traccia.titolo
        assert not any(p.simbolo == "N" for p in traccia.passi)
    assert_relazione_coerente(TOOL, TOOL.example)


def test_gamma_c_diverso_da_1_5_non_rompe_la_coerenza():
    """`materiali.py` costruisce `ConcreteProperties.fcd_MPa` con il γc di default del modulo
    condiviso (1,5), non col γc del tool (vedi CALCULATION FINDINGS): questo test usa γc=1,6 apposta,
    così una `relazione` che citasse per errore quel campo invece di ricalcolare f_cd=α_cc·f_ck/γc con
    l'input del tool fallirebbe qui."""
    assert_relazione_coerente(TOOL, {**TOOL.example, "gamma_c": 1.6})
