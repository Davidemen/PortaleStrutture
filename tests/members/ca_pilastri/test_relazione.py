"""`relazione.py` (docs/architecture-phase2.md §6, wave 2 adoption): the harness on both tools'
examples (which are themselves the golden case, `tool.py::ESEMPIO_RETTANGOLARE`/`ESEMPIO_CIRCOLARE`
== `test_golden.py`/`test_golden_ntc2018.py`/`test_golden_ec2.py`'s inputs) and on every oracle case
of `test_oracle_rettangolare_ntc2018.py`/`test_oracle_rettangolare_ec2.py`/
`test_oracle_circolare_ntc2018.py`/`test_oracle_circolare_ec2.py` (imported directly, per
docs/architecture-phase2.md §6) — always in STANDARD mode (`legacy_compat=False`): NTC2008 has no
code-standard branch (`regole.resolve`) and therefore no trace at all (`relazione` only describes
standard mode, docs/architecture-phase2.md §1), so the NTC2008-only oracle/golden fixtures
(`test_golden.py`, `test_oracle_rettangolare.py`, `test_oracle_circolare.py`) are not reused here.
"""
from typing import Any

import pytest

import tests.members.ca_pilastri.test_oracle_circolare_ec2 as oracolo_circolare_ec2
import tests.members.ca_pilastri.test_oracle_circolare_ntc2018 as oracolo_circolare_ntc2018
import tests.members.ca_pilastri.test_oracle_rettangolare_ec2 as oracolo_rettangolare_ec2
import tests.members.ca_pilastri.test_oracle_rettangolare_ntc2018 as oracolo_rettangolare_ntc2018
from strutture.members.ca_pilastri.tool import TOOLS
from strutture.shared.tool import execute
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL_RETTANGOLARE = next(t for t in TOOLS if t.name == "ca-pilastro-rettangolare")
TOOL_CIRCOLARE = next(t for t in TOOLS if t.name == "ca-pilastro-circolare")


def _oracolo_raw_inputs(modulo: Any, case: dict[str, Any], *, extra: dict[str, Any]) -> dict[str, Any]:
    """The oracle case's inputs, renamed to the tool's field names, WITHOUT `legacy_compat` (defaults
    to False/standard — `relazione` never runs in legacy mode), `norma` set explicitly to whichever
    the oracle module targets."""
    cells = {**modulo.DEFAULTS, **case["inputs"]}
    campi = {modulo.CELL_TO_FIELD[cella]: valore for cella, valore in cells.items()}
    return {**campi, **extra}


def _casi_oracolo_circolare(modulo: Any) -> list[dict[str, Any]]:
    """Skips the same #NUM! (over-reinforced stirrups) cases `modulo`'s own oracle test skips."""
    return [case for case in modulo.FIXTURE if not isinstance(case["outputs"].get("Z13"), str)]


# --- esempio (== caso golden) -----------------------------------------------------------------


def test_tool_declares_relazione():
    assert TOOL_RETTANGOLARE.relazione is not None
    assert TOOL_CIRCOLARE.relazione is not None


def test_relazione_coerente_sullesempio_rettangolare():
    assert_relazione_coerente(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example)


def test_relazione_coerente_sullesempio_circolare():
    assert_relazione_coerente(TOOL_CIRCOLARE, TOOL_CIRCOLARE.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden_ec2():
    """`test_golden_ec2.py` usa esattamente gli stessi input numerici del caso golden, con
    norma="EC2"."""
    assert_relazione_coerente(TOOL_RETTANGOLARE, {**TOOL_RETTANGOLARE.example, "norma": "EC2"})
    assert_relazione_coerente(TOOL_CIRCOLARE, {**TOOL_CIRCOLARE.example, "norma": "EC2"})


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example)
    assert_ogni_highlight_e_spiegato(TOOL_CIRCOLARE, TOOL_CIRCOLARE.example)


# --- casi oracolo (NTC2018 ed EC2, legacy_compat=False qui) -----------------------------------


@pytest.mark.oracle
@pytest.mark.parametrize("case", oracolo_rettangolare_ntc2018.FIXTURE, ids=range(len(oracolo_rettangolare_ntc2018.FIXTURE)))
def test_relazione_coerente_oracolo_rettangolare_ntc2018(case: dict[str, Any]):
    raw = _oracolo_raw_inputs(oracolo_rettangolare_ntc2018, case, extra={"n_ferri_l1": 3, "norma": "NTC2018"})
    assert_relazione_coerente(TOOL_RETTANGOLARE, raw)


@pytest.mark.oracle
@pytest.mark.parametrize("case", oracolo_rettangolare_ec2.FIXTURE, ids=range(len(oracolo_rettangolare_ec2.FIXTURE)))
def test_relazione_coerente_oracolo_rettangolare_ec2(case: dict[str, Any]):
    raw = _oracolo_raw_inputs(oracolo_rettangolare_ec2, case, extra={"n_ferri_l1": 3, "norma": "EC2"})
    assert_relazione_coerente(TOOL_RETTANGOLARE, raw)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _casi_oracolo_circolare(oracolo_circolare_ntc2018), ids=lambda c: str(c["inputs"]))
def test_relazione_coerente_oracolo_circolare_ntc2018(case: dict[str, Any]):
    raw = _oracolo_raw_inputs(oracolo_circolare_ntc2018, case, extra={"norma": "NTC2018"})
    assert_relazione_coerente(TOOL_CIRCOLARE, raw)


@pytest.mark.oracle
@pytest.mark.parametrize("case", _casi_oracolo_circolare(oracolo_circolare_ec2), ids=lambda c: str(c["inputs"]))
def test_relazione_coerente_oracolo_circolare_ec2(case: dict[str, Any]):
    raw = _oracolo_raw_inputs(oracolo_circolare_ec2, case, extra={"norma": "EC2"})
    assert_relazione_coerente(TOOL_CIRCOLARE, raw)


# --- copertura di ogni Check e conteggio dei passi ---------------------------------------------


def _assert_ogni_check_ha_un_passo(tool, raw_inputs: dict[str, Any]) -> None:
    report = execute(tool, raw_inputs, con_relazione=True)
    assert report.ok
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_relazione_covers_every_check_rettangolare_ntc2018():
    _assert_ogni_check_ha_un_passo(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example)


def test_relazione_covers_every_check_rettangolare_ec2():
    _assert_ogni_check_ha_un_passo(TOOL_RETTANGOLARE, {**TOOL_RETTANGOLARE.example, "norma": "EC2"})


def test_relazione_covers_every_check_circolare_ntc2018():
    _assert_ogni_check_ha_un_passo(TOOL_CIRCOLARE, TOOL_CIRCOLARE.example)


def test_relazione_covers_every_check_circolare_ec2():
    _assert_ogni_check_ha_un_passo(TOOL_CIRCOLARE, {**TOOL_CIRCOLARE.example, "norma": "EC2"})


@pytest.mark.parametrize("tool,norma", [(TOOL_RETTANGOLARE, "NTC2018"), (TOOL_RETTANGOLARE, "EC2"),
                                         (TOOL_CIRCOLARE, "NTC2018"), (TOOL_CIRCOLARE, "EC2")])
def test_step_count_within_the_10_to_30_target(tool, norma):
    """Upper bound raised 30 -> 32 (review finding fix, wave 2): the pressoflessione/compressione
    Tracce each gained one η passo (real substitution M_Ed/M_Rd, M_Rd's provenance declared) —
    still well inside architecture-phase2.md §6's 8-25 "target per tool" band per Traccia."""
    report = execute(tool, {**tool.example, "norma": norma}, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 10 <= totale <= 32, totale


# --- variazioni che cambiano ramo ---------------------------------------------------------------


def test_variazione_norma_ec2_aggiunge_il_check_area_massima():
    """EC2 (`rules.as_max_check=True`, `regole.py`) aggiunge il Check "Area massima di armatura
    longitudinale", assente in NTC2018: la traccia deve seguire la normativa selezionata."""
    report_ntc = execute(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example, con_relazione=True)
    report_ec2 = execute(TOOL_RETTANGOLARE, {**TOOL_RETTANGOLARE.example, "norma": "EC2"}, con_relazione=True)
    assert not any(c.name == "Area massima di armatura longitudinale" for c in report_ntc.checks)
    assert any(c.name == "Area massima di armatura longitudinale" for c in report_ec2.checks)
    simboli_ec2 = {p.simbolo for t in report_ec2.relazione for p in t.passi}
    assert "A_s,max" in simboli_ec2
    assert_relazione_coerente(TOOL_RETTANGOLARE, {**TOOL_RETTANGOLARE.example, "norma": "EC2"})


def test_variazione_forma_circolare():
    """Sezione circolare: A_c/A_s/λ_lim/taglio usano D e il lato equivalente al posto di L_1/L_2."""
    assert_relazione_coerente(TOOL_CIRCOLARE, TOOL_CIRCOLARE.example)
    report = execute(TOOL_CIRCOLARE, TOOL_CIRCOLARE.example, con_relazione=True)
    traccia_geometria = next(t for t in report.relazione if t.titolo == "Geometria della sezione")
    assert any(p.simbolo == "l_eq" for p in traccia_geometria.passi)


def test_variazione_check_fallito_pressoflessione():
    """M_Ed (500 kNm) > M_Rd (160 kNm): il Check "Resistenza a pressoflessione" fallisce; il Passo
    corrispondente riporta esito "non soddisfatta"."""
    variazione = {**TOOL_RETTANGOLARE.example, "med_kNm": 500.0}
    report = execute(TOOL_RETTANGOLARE, variazione, con_relazione=True)
    assert report.ok
    by_name = {c.name: c.passed for c in report.checks}
    assert by_name["Resistenza a pressoflessione"] is False
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "M_Ed/M_Rd")
    assert passo.esito == "non soddisfatta"
    assert_relazione_coerente(TOOL_RETTANGOLARE, variazione)


def test_variazione_blocco_opzionale_pieno_ec2():
    """φ_ef, r_m, l_0 sono opzionali (default assente in `TOOL.example`, blocco vuoto già coperto
    sopra): con il blocco compilato cambiano A, C e l_0 nella Traccia "Snellezza"."""
    variazione = {**TOOL_RETTANGOLARE.example, "norma": "EC2", "phi_ef": 1.2, "rm": -0.4, "l0_mm": 4000.0}
    report = execute(TOOL_RETTANGOLARE, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo == "Snellezza")
    passo_lambda = next(p for p in traccia.passi if p.simbolo == "λ")
    valore_l0 = next(v for v in passo_lambda.valori if v.simbolo == "l_0")
    assert valore_l0.valore == pytest.approx(4000.0)
    assert_relazione_coerente(TOOL_RETTANGOLARE, variazione)


def test_variazione_ramo_basso_coefficiente_ac():
    """N_Ed piccolo sposta σ_cp sotto 0,25·f_cd: il ramo basso del coefficiente a_c (1+σ_cp/f_cd);
    il simbolo del passo porta la condizione di validità del ramo (review finding MISLEADING:
    il foglio stampava solo il ramo attivo, senza intervallo di validità)."""
    variazione = {**TOOL_RETTANGOLARE.example, "ned_kN": 100.0}
    report = execute(TOOL_RETTANGOLARE, variazione, con_relazione=True)
    assert report.ok
    assert report.data.taglio.sigma_cp_MPa < 0.25 * report.data.materiali.fcd_MPa
    passo_ac = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("a_c"))
    assert "σ_cp" in passo_ac.formula
    assert "0,25" in passo_ac.simbolo
    assert_relazione_coerente(TOOL_RETTANGOLARE, variazione)


# --- review findings (wave 2, engineer proof-read) ----------------------------------------------


def test_pressoflessione_mostra_eta_con_substituzione_reale():
    """Review finding MISLEADING: il Check stampava solo 'tasso <= 100' (un numero opaco, mai
    M_Ed/M_Rd) e M_Rd (dato di ingresso, nessun dominio M-N) non compariva mai nella Traccia. Un
    passo η = M_Ed/M_Rd, con la sostituzione reale, deve precedere il check percentuale."""
    report = execute(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo == "Resistenza a pressoflessione")
    passo_eta = next(p for p in traccia.passi if p.simbolo == "η")
    assert passo_eta.formula == "M_Ed / M_Rd"
    valore_mrd = next(v for v in passo_eta.valori if v.simbolo == "M_Rd")
    assert "dato di ingresso" in valore_mrd.descrizione
    assert valore_mrd.valore == pytest.approx(report.data.flessione.mrd_kNm)
    assert passo_eta.risultato == pytest.approx(report.data.flessione.med_kNm / report.data.flessione.mrd_kNm)
    assert_relazione_coerente(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example)


def test_compressione_mostra_eta_con_substituzione_reale():
    """Stesso difetto (review finding MISLEADING), Check "Resistenza a compressione": η_N = N_Ed/N_Rcd."""
    report = execute(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo == "Resistenza a compressione")
    passo_eta = next(p for p in traccia.passi if p.simbolo == "η_N")
    assert passo_eta.formula == "N_Ed / N_Rcd"
    assert passo_eta.risultato == pytest.approx(TOOL_RETTANGOLARE.example["ned_kN"] / report.data.compressione.nrcd_kN)
    assert_relazione_coerente(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example)


def test_taglio_vrdc_non_e_piu_etichettato_come_resistenza_senza_armatura():
    """Review finding MISLEADING: la resistenza di schiacciamento dei puntoni era etichettata
    'V_Rd,c', lo stesso simbolo che EC2 §6.2.2/plinti_pali usano per la resistenza SENZA armatura
    a taglio — rinominata V_Rcd (NTC2018) / V_Rd,max (EC2)."""
    report = execute(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo.startswith("Resistenza a taglio"))
    simboli = {p.simbolo for p in traccia.passi}
    assert "V_Rd,c" not in simboli
    assert "V_Rcd" in simboli
    assert_relazione_coerente(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example)


def test_taglio_usa_simboli_reali_per_z_e_larghezza():
    """Review finding MISLEADING: 'dimensione'/'larghezza' erano parole indefinite; in codice z usa
    SEMPRE L_2 (leva_interna(inputs.l2_mm, c)) e la larghezza dell'anima è SEMPRE L_1
    (vrdc/cot_theta(..., inputs.l1_mm, ...)), qualunque sia la direzione di V_Ed. Con L_1 != L_2 il
    passo z doveva restituire 0,9*(L_2-c), non 0,9*(L_1-c) (bug di coerenza scoperto qui: prima
    della correzione z riusava L_1 per entrambi gli usi)."""
    variazione = {**TOOL_RETTANGOLARE.example, "l1_mm": 300.0, "l2_mm": 600.0, "diametro_ferri_mm": 16.0}
    report = execute(TOOL_RETTANGOLARE, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo.startswith("Resistenza a taglio"))
    assert "L_2" in traccia.titolo and "L_1" in traccia.titolo
    passo_z = next(p for p in traccia.passi if p.simbolo == "z")
    assert "L_2" in passo_z.formula
    assert passo_z.risultato == pytest.approx(0.9 * (600.0 - variazione["c_mm"]))
    passo_vrdc = next(p for p in traccia.passi if p.simbolo == "V_Rcd")
    assert "L_1" in passo_vrdc.formula
    assert_relazione_coerente(TOOL_RETTANGOLARE, variazione)


def test_dettagli_staffe_citano_la_clausola_di_dettaglio_ordinario():
    """Review finding WRONG_CLAUSE: s_staffe,max e φ_sw,min citavano NTC2018 §7.4.6.2.2 (dettaglio
    SISMICO di zona critica, già usato correttamente dal passo di confinamento) invece di
    NTC2018 §4.1.6.1.2 (dettaglio ordinario, EC2 §9.5.3(1))."""
    report = execute(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo == "Dettagli costruttivi")
    passo_s_staffe = next(p for p in traccia.passi if p.simbolo == "s_staffe,max")
    passo_phi_sw = next(p for p in traccia.passi if p.simbolo == "φ_sw,min")
    assert passo_s_staffe.clausola == "NTC2018 §4.1.6.1.2"
    assert passo_phi_sw.clausola == "NTC2018 §4.1.6.1.2"
    assert_relazione_coerente(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example)


def test_rho_s_min_cita_la_clausola_colonne():
    """Review finding WRONG_CLAUSE: ρ_s,min citava NTC2018 §7.4.6.2.1 (sotto-clausola TRAVI di
    §7.4.6.2), non §7.4.6.2.2 (colonne, la stessa che cita il vincolo ρ_s<4% accanto)."""
    variazione = {**TOOL_RETTANGOLARE.example, "norma": "NTC2018"}
    report = execute(TOOL_RETTANGOLARE, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo == "Limiti di armatura longitudinale")
    passo = next(p for p in traccia.passi if p.simbolo == "ρ_s,min")
    assert passo.clausola == "NTC2018 §7.4.6.2.2"
    assert_relazione_coerente(TOOL_RETTANGOLARE, variazione)


def test_as_min_non_applica_il_tetto_del_4_percento_alla_formula_stampata():
    """Review finding MISLEADING: la formula stampata di A_s,min applicava min(..., 0,04*A_c),
    convertendo silenziosamente "serve più acciaio del tetto ammesso" in "va bene" — il tetto ha
    già un proprio Check ("ρ_s < 4%"). La formula ristata non deve più includere quel min esterno
    (il valore numerico non cambia: il tetto non è mai attivo nei casi testati)."""
    report = execute(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo == "Limiti di armatura longitudinale")
    passo = next(p for p in traccia.passi if p.simbolo == "A_s,min")
    assert "0.04" not in passo.formula
    assert_relazione_coerente(TOOL_RETTANGOLARE, TOOL_RETTANGOLARE.example)
