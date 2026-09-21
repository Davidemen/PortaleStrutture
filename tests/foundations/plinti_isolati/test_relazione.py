"""`relazione.py` (docs/architecture-phase2.md §6, wave 1 adoption): the harness on the tool's own
example, on the golden/oracle input sets the package's OTHER tests already use (`conftest.py`'s
537-row golden combo table — `test_tool.py`; `test_capacita_portante.py`'s Annex D scalar set),
run in STANDARD mode (`legacy_compat=False`, `relazione` only describes standard mode, docs
§1) — plus parameter variations that switch branches: a footing with a bicchiere/pedestal, the
Annex D non-drenata formula, a seismic famiglia governing the Annex D check, and a failing
"Portanza" check. `test_oracle.py`'s 4 scalar cases are intentionally NOT reused here: that
fixture's own contract is `legacy_compat=True` throughout (module docstring), so forcing standard
mode on it would no longer be oracle-verified."""
import pytest

from strutture.foundations.plinti_isolati.tool import TOOLS
from strutture.shared.tool import execute
from tests.foundations.plinti_isolati.conftest import GOLDEN_SCALARI, load_golden_rows
from tests.foundations.plinti_isolati.test_capacita_portante import _inputs as _capacita_portante_inputs
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "fond-plinto-isolato")

# Annex D scalar golden set (test_capacita_portante.py's own `_SCALARI`/`_reazione`, condizione
# drenata): N=489 kN dopo i pesi propri, nessuna eccentricità/taglio. `sigma_ammissibile=2.0` resta
# in kPa (sistema_unita di default "SI"), quindi la verifica "Portanza" fallisce (166<<2): usato
# anche da `test_variazione_verifica_portanza_fallita`.
_CAPACITA_PORTANTE_GOLDEN = _capacita_portante_inputs(
    terreno_condizione="drenata", terreno_phi_k_deg=30.0, terreno_c_k_kpa=5.0, terreno_gamma_kn_m3=18.0,
).model_dump(mode="json")


def _golden_537_righe() -> dict:
    return {**GOLDEN_SCALARI, "reazioni": load_golden_rows(), "legacy_compat": False}


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
def test_relazione_coerente_sul_caso_golden():
    """537 combinazioni (`docs/specs/fond-plinti-isolati.md`, nodo 1832): la combinazione
    governante per σ_max, per lo scorrimento e per il ribaltamento non coincidono (vedi
    `relazione_sicurezza.py`), esercitando i 3 rami "governante diverso per grandezza"."""
    assert_relazione_coerente(TOOL, _golden_537_righe())


def test_relazione_coerente_sul_caso_capacita_portante():
    assert_relazione_coerente(TOOL, _CAPACITA_PORTANTE_GOLDEN)


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


@pytest.mark.golden
def test_ogni_highlight_e_spiegato_sul_caso_golden():
    assert_ogni_highlight_e_spiegato(TOOL, _golden_537_righe())


def test_step_count_within_the_8_to_25_target():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 25


def test_relazione_covers_every_check_the_tool_declares():
    """Ogni `Check` emesso su `TOOL.example` (Portanza, Scorrimento; nessun bicchiere/Terreno/
    famiglia EQU: niente Ribaltamento) deve comparire come un Passo di verifica con lo stesso
    esito (docs/architecture-phase2.md §6, "every Check")."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert {c.name for c in report.checks} == {"Portanza (SLU_STR)", "Scorrimento (SLU_STR)"}
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks)
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_variazione_bicchiere_presente():
    """Bicchiere/pilastrino con dimensioni non nulle: esercita `W_bicchiere` e la sottrazione del
    semi-bicchiere nella luce della mensola (`relazione_azioni.py`/`relazione_armatura.py`)."""
    variazione = {
        "ax_m": 3.0, "by_m": 3.0, "h_plinto_m": 0.7, "h_interro_m": 1.2,
        "a_pedestal_m": 0.6, "b_pedestal_m": 0.6, "h_pedestal_sopra_m": 0.4, "h_pedestal_sotto_m": 0.3,
        "copriferro_cm": 6.0, "passo_armatura_cm": 15.0, "sistema_unita": "tecnico",
        "resistenze": ({"famiglia": "SLU_STR", "sigma_ammissibile": 3.0},),
        "reazioni": ({"nodo": 10, "combo": "C10", "famiglia": "SLU_STR",
                       "fx_kN": 5.0, "fy_kN": 3.0, "fz_kN": 500.0, "mx_kNm": 20.0, "my_kNm": 15.0, "mz_kNm": 0.0},),
    }
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok, report.errors
    passo_bicchiere = next(p for t in report.relazione for p in t.passi if p.simbolo == "W_bicchiere")
    assert passo_bicchiere.risultato > 0
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_terreno_non_drenata():
    """Condizione non drenata: niente Nq/Nc/Nγ (assenti dalla formula D.3), sc/ic con le formule
    non drenate (`relazione_capacita_portante.py::_passi_non_drenata`)."""
    variazione = {
        "ax_m": 2.0, "by_m": 2.0, "h_plinto_m": 0.6, "h_interro_m": 1.0,
        "copriferro_cm": 5.0, "passo_armatura_cm": 15.0,
        "resistenze": ({"famiglia": "SLU_STR", "sigma_ammissibile": 300.0},),
        "reazioni": ({"nodo": 1, "combo": "C1", "famiglia": "SLU_STR",
                       "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 300.0, "mx_kNm": 0.0, "my_kNm": 0.0, "mz_kNm": 0.0},),
        "terreno_condizione": "non_drenata", "terreno_cu_k_kpa": 40.0, "terreno_gamma_kn_m3": 18.0,
    }
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok, report.errors
    traccia_ad = next(t for t in report.relazione if "Capacità portante" in t.titolo)
    assert {p.simbolo for p in traccia_ad.passi} == {"s_c", "i_c", "q_lim", "R_d", "N_Ed/R_d"}
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_famiglia_sismica_governante_capacita_portante():
    """Famiglia SLV_STR governante la capacità portante: il Passo "N_Ed/R_d" deve citare la
    clausola sismica (`capacita_portante_checks.CLAUSOLA_SISMICA`), non quella statica ordinaria."""
    variazione = {
        "ax_m": 2.0, "by_m": 2.0, "h_plinto_m": 0.6, "h_interro_m": 1.0,
        "copriferro_cm": 5.0, "passo_armatura_cm": 15.0,
        "resistenze": ({"famiglia": "SLV_STR", "sigma_ammissibile": 300.0},),
        "reazioni": ({"nodo": 1, "combo": "EQK1", "famiglia": "SLV_STR",
                       "fx_kN": 10.0, "fy_kN": 5.0, "fz_kN": 300.0, "mx_kNm": 15.0, "my_kNm": 10.0, "mz_kNm": 0.0},),
        "terreno_condizione": "drenata", "terreno_phi_k_deg": 28.0, "terreno_c_k_kpa": 0.0, "terreno_gamma_kn_m3": 19.0,
    }
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok, report.errors
    passo_ratio = next(p for t in report.relazione for p in t.passi if p.simbolo == "N_Ed/R_d")
    assert "7.11.5.3.1" in passo_ratio.clausola
    assert_relazione_coerente(TOOL, variazione)


def test_scorrimento_cita_6_4_2_1_non_6_4_3_1():
    """Review finding (WRONG_CLAUSE): §6.4.3.1 NTC2018 è "Fondazioni su pali" — per un plinto
    superficiale lo scorrimento sul piano di posa è §6.4.2.1, Tab. 6.4.I (R3)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "μ_scorr")
    assert passo.clausola == "NTC2018 §6.4.2.1, Tab. 6.4.I (R3)"


def test_ribaltamento_cita_6_4_2_1_equ_quando_e_verifica():
    """Review finding (WRONG_CLAUSE): stessa costante OVERTURNING_CLAUSE (§6.4.3.1) riusata per
    scorrimento e ribaltamento; il ribaltamento EQU è §6.4.2.1 con Tab. 2.6.I/6.2.I (EQU)."""
    variazione = {
        **TOOL.example, "resistenze": ({"famiglia": "SLU_EQU", "sigma_ammissibile": 200.0},),
        "reazioni": ({"nodo": 1, "combo": "C1", "famiglia": "SLU_EQU",
                       "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 300.0, "mx_kNm": 5.0, "my_kNm": 5.0, "mz_kNm": 0.0},),
    }
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok, report.errors
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "μ_rib")
    assert passo.esito != ""
    assert passo.clausola == "NTC2018 §6.4.2.1 con Tab. 2.6.I/6.2.I (EQU)"


def test_ribaltamento_informativo_lo_dichiara_nel_titolo():
    """Review finding (MISLEADING): quando la famiglia governante non è EQU il rapporto è solo
    informativo (N include il γ_G della famiglia, non γ_G,stab=0,9): il titolo — sempre reso,
    a differenza di `nota` — deve dirlo esplicitamente, non solo presentarsi come "combinazione
    governante"."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo.startswith("Ribaltamento"))
    passo = traccia.passi[0]
    assert passo.esito == ""  # SLU_STR sull'esempio: non è una vera verifica EQU
    assert "valore informativo" in traccia.titolo


def test_scorrimento_dichiara_il_gamma_g_di_n():
    """Review finding (MISLEADING): N al numeratore di μ_scorr include il γ_G della famiglia
    governante (1,35 per SLU_STR) anche quando il peso proprio agisce a favore di sicurezza."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "μ_scorr")
    assert "γ_G" in passo.nota


def test_armatura_x_mostra_as_min_e_larea_governante():
    """Review finding (MISSING_STEP): A_s,x compariva come area nuda senza il confronto con
    A_s,min (NTC2018 §4.1.6.1.1) né il passo di scelta max(A_s, A_s,min) che determina il
    diametro adottato."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "Momento a sbalzo" in t.titolo)
    simboli = [p.simbolo for p in traccia.passi]
    assert "A_s,x,min" in simboli
    assert "A_s,x,gov" in simboli
    passo_min = next(p for p in traccia.passi if p.simbolo == "A_s,x,min")
    assert passo_min.risultato == pytest.approx(report.data.flessione.as_x_min_cm2)
    assert passo_min.clausola == "NTC2018 §4.1.6.1.1"
    passo_gov = next(p for p in traccia.passi if p.simbolo == "A_s,x,gov")
    assert passo_gov.risultato == pytest.approx(max(report.data.flessione.as_x_cm2, report.data.flessione.as_x_min_cm2))


def test_armatura_x_deriva_laltezza_utile_d():
    """Review finding (MISSING_STEP): d=690mm entrava nella formula di A_s,x senza un passo che lo
    derivasse da H/copriferro/margine."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if "Momento a sbalzo" in t.titolo)
    passo_d = next(p for p in traccia.passi if p.simbolo == "d")
    assert passo_d.risultato == pytest.approx(TOOL.example["h_plinto_m"] * 1000.0 - TOOL.example["copriferro_cm"] * 10.0 - 30.0)


def test_variazione_verifica_portanza_fallita():
    """`_CAPACITA_PORTANTE_GOLDEN` (sistema_unita "SI" di default, sigma_ammissibile=2 kPa) fa
    fallire la verifica "Portanza": il Passo "σ_max/σ_amm" deve riportare lo stesso esito."""
    report = execute(TOOL, _CAPACITA_PORTANTE_GOLDEN, con_relazione=True)
    assert report.ok, report.errors
    check = next(c for c in report.checks if c.name == "Portanza (SLU_STR)")
    assert check.passed is False
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "σ_max/σ_amm")
    assert passo.esito == "non soddisfatta"
