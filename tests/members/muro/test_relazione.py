"""`relazione.py` (docs/architecture-phase2.md §6, wave 2 adoption): the harness on the tool's own
example AND on every golden/oracle input set the package's own tests already use (Tratto A,
Tratto B..E, the LibreOffice oracle) — run here in STANDARD mode (`legacy_compat` stripped: the
fixtures' own `legacy_compat=True` is never set, `relazione` only describes standard mode,
docs/architecture-phase2.md §1) — plus variations that switch branches: a failing check, the
"non drenata" bearing-capacity branch, a different wall shape (inclined stem/base/slope), and the
optional "Terreno di fondazione" block both empty and filled.

Oracle case 1 is excluded: it CalcErrors in STANDARD mode on its own (`|e|` exceeds `B/2` for
SISMA_1 once the standard-mode seismic-inertia terms are added, see `tool.py`'s
`AVVISO_TAGLIO_GRAVITAZIONALE`-style inertia additions) — a pre-existing, unrelated-to-`relazione`
divergence between standard and legacy_compat mode; there is nothing for `relazione` to cover on a
run that never produces a `Report.data`.
"""
from typing import Any

import pytest

from strutture.members.muro.combinazioni import ALL_COMBOS
from strutture.members.muro.relazione_comune import combo_governante_stabilita
from strutture.members.muro.tool import TOOLS
from strutture.shared.tool import execute
from tests.members.muro.test_golden import TRATTO_A_INPUT
from tests.members.muro.test_golden_tratti import CASES as TRATTI_CASES
from tests.members.muro.test_golden_tratti import _inputs as _inputs_tratti
from tests.members.muro.test_oracle import CASES as ORACLE_CASES
from tests.members.muro.test_oracle import _inputs as _inputs_oracle
from tests.members.muro.test_terreno_fondazione import TERRENO_DRENATA, TERRENO_NON_DRENATA
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "muro-sostegno")

_ORACLE_CASO_INAMMISSIBILE_STANDARD = 1  # vedi il docstring del modulo


def _senza_legacy(inputs) -> dict[str, Any]:
    """`MuroSostegnoInput` -> dict grezzo senza `legacy_compat` (standard, default False)."""
    return {k: v for k, v in inputs.model_dump().items() if k != "legacy_compat"}


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
def test_relazione_coerente_sul_tratto_a():
    assert_relazione_coerente(TOOL, _senza_legacy(TRATTO_A_INPUT))


@pytest.mark.golden
@pytest.mark.parametrize("case", TRATTI_CASES, ids=[c["sheet"] for c in TRATTI_CASES])
def test_relazione_coerente_sui_tratti_b_e(case: dict[str, Any]):
    assert_relazione_coerente(TOOL, _senza_legacy(_inputs_tratti(case["outputs"])))


@pytest.mark.oracle
@pytest.mark.parametrize(
    "case", [c for i, c in enumerate(ORACLE_CASES) if i != _ORACLE_CASO_INAMMISSIBILE_STANDARD],
    ids=[f"case{i}" for i in range(len(ORACLE_CASES)) if i != _ORACLE_CASO_INAMMISSIBILE_STANDARD],
)
def test_relazione_coerente_sui_casi_oracolo(case: dict[str, Any]):
    assert_relazione_coerente(TOOL, _senza_legacy(_inputs_oracle(case["inputs"])))


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_ogni_highlight_in_tupla_e_spiegato():
    """`or_ribaltamento`/`os_scorrimento` (`RibaltamentoScorrimentoCombo`, highlight=True) sono
    dentro una tupla: il controllo globale della harness non ricorre nelle tuple
    (`tests/shared/relazione/harness.py::_campi_output`), quindi qui si verifica direttamente che
    OGNI combinazione produca un Passo OR/OS con lo stesso risultato del suo output."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passi = {p.simbolo: p for t in report.relazione for p in t.passi}
    for verifica in report.data.ribaltamento_scorrimento:
        or_simboli = [p for p in passi.values() if p.simbolo == "OR" or p.simbolo.startswith("OR (")]
        os_simboli = [p for p in passi.values() if p.simbolo == "OS" or p.simbolo.startswith("OS (")]
        assert any(p.risultato == pytest.approx(verifica.or_ribaltamento) for p in or_simboli), verifica.nome
        assert any(p.risultato == pytest.approx(verifica.os_scorrimento) for p in os_simboli), verifica.nome


def test_relazione_covers_every_check_the_tool_declares():
    """Ogni `Check.name` di `tool.py` deve avere un Passo con lo stesso esito da qualche parte
    nella traccia (docs/architecture-phase2.md §6: "every Check"). +1 rispetto al conteggio dei
    Check: il confronto |e| vs B/6 di `relazione_pressioni.py` è un Passo di confronto informativo
    (non un Check autonomo, nessun `Check` in `tool.py` gli corrisponde) e porta comunque un esito
    perché la sua `formula` è un confronto (`verifica.py` lo richiede)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert len(report.checks) == 19, "il fixture dell'esempio non copre più i 19 Check attesi"
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks) + 1
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def test_as_nec_simbolo_ambiguo_un_solo_bare_gli_altri_disambiguati():
    """Review-driven fix: `A_s,nec` (UI symbol) è condiviso da tre output diversi (paramento/valle/
    monte, `models.py`); solo l'ultimo esposto da `MuroSostegnoOutput` (fondazione di monte) porta
    il simbolo nudo, gli altri due sono disambiguati — altrimenti il controllo incrociato della
    harness con l'output confonderebbe i tre valori (vedi i moduli `relazione_armatura_*`)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passi = [p for t in report.relazione for p in t.passi if p.simbolo.startswith("A_s,nec")]
    simboli = {p.simbolo for p in passi}
    assert simboli == {"A_s,nec (paramento)", "A_s,nec (valle)", "A_s,nec"}
    bare = next(p for p in passi if p.simbolo == "A_s,nec")
    assert bare.risultato == pytest.approx(report.data.armatura_fondazione_monte.as_nec_cm2_m)


def test_variazione_check_fallito_ribaltamento_scorrimento():
    """Muro più alto a parità di fondazione: lo scorrimento non è più verificato su alcune
    combinazioni (senza superare |e|>B/2, che farebbe fallire l'intero calcolo prima ancora della
    relazione)."""
    variazione = {**TOOL.example, "h_muro_m": 3.0}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert any(not c.passed for c in report.checks)
    assert_relazione_coerente(TOOL, variazione)
    passo_utilizzazione = next(p for t in report.relazione for p in t.passi if p.simbolo == "OS")
    assert passo_utilizzazione.esito == "non soddisfatta"


def test_variazione_capacita_portante_non_drenata():
    """Ramo "non drenata" dell'Annesso D (clausola diversa, niente b_q/N_q/N_γ nella formula di
    q_lim, solo b_c/N_c)."""
    variazione = {**TOOL.example, **TERRENO_NON_DRENATA}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    traccia = next(t for t in report.relazione if t.titolo.startswith("Capacità portante"))
    passo_q_lim = next(p for p in traccia.passi if p.simbolo == "q_lim")
    assert "c_u,k" in passo_q_lim.formula
    assert "N_q" not in passo_q_lim.formula
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_altra_forma_muro():
    """Altra geometria: paramento non verticale (ψ≠90°), base inclinata (ω≠0) e pendio a tergo
    (β≠0) — esercita i rami meno comuni di Ka (Coulomb/Mononobe-Okabe con β,ψ,ω non nulli) e della
    scomposizione normale/tangenziale alla base."""
    variazione = {**TOOL.example, "psi_deg": 80.0, "omega_deg": 8.0, "beta_deg": 10.0}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert_relazione_coerente(TOOL, variazione)
    assert_ogni_highlight_e_spiegato(TOOL, variazione)


def test_variazione_blocco_opzionale_vuoto():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert report.ok
    assert report.data.capacita_portante_fondazione is None
    assert not any(t.titolo.startswith("Capacità portante") for t in report.relazione)


def test_variazione_blocco_opzionale_compilato():
    variazione = {**TOOL.example, **TERRENO_DRENATA}
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.capacita_portante_fondazione is not None
    traccia = next(t for t in report.relazione if t.titolo.startswith("Capacità portante"))
    passo_check = next(p for p in traccia.passi if p.esito)
    assert passo_check.simbolo == "N_Ed/R_d"
    assert_relazione_coerente(TOOL, variazione)


def test_traccia_spinta_cita_la_combinazione_governante_nel_titolo():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo.startswith("Spinta attiva"))
    assert any(nome in traccia.titolo for nome in ALL_COMBOS)


def test_ka_usa_coulomb_o_mononobe_okabe_secondo_la_combinazione_governante():
    """La clausola del passo K_a deve citare Mononobe-Okabe quando la combinazione governante è
    sismica, Coulomb altrimenti — mai entrambe insieme."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo.startswith("Spinta attiva"))
    passo_ka = next(p for p in traccia.passi if p.simbolo == "K_a")
    if "SISMA" in traccia.titolo:
        assert "7.11.6.2.1" in passo_ka.clausola
    else:
        assert passo_ka.clausola == "NTC2018 §6.5.3.1.1"


# --- review findings (wave 2, engineer proof-read) ----------------------------------------------


def test_spinta_deriva_kv_e_theta_per_la_combinazione_governante():
    """Review finding MISSING_STEP: la Traccia "Geometria e parametri sismici" deriva k_v/θ SOLO
    per SISMA_1 (segno +1); quando (come nell'esempio) governa SISMA_2, K_a sostituiva
    θ = atan(k_h/(1-k_v)) citandolo come "derivato sopra" senza che nessun passo lo derivasse per
    quel segno. La Traccia "Spinta attiva" deve ora derivare essa stessa k_v/θ per la combinazione
    governante, segno incluso."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo.startswith("Spinta attiva"))
    assert "SISMA_2" in traccia.titolo
    passo_kv = next(p for p in traccia.passi if p.simbolo == "k_v")
    assert "segno_kv" in passo_kv.formula
    valore_segno = next(v for v in passo_kv.valori if v.simbolo == "segno_kv")
    assert valore_segno.valore == pytest.approx(-1.0)
    passo_theta = next(p for p in traccia.passi if p.simbolo == "θ")
    assert passo_theta.formula == "atan(k_h / (1 + k_v))"
    assert_relazione_coerente(TOOL, TOOL.example)


def test_stabilita_deriva_fh_e_mfh_per_combinazione_sismica():
    """Review finding MISSING_STEP: F_h/M_fh (inerzia sismica EN1998-5 §7.3.2.2(2)P, ~12%/11% di
    R_TOT/M_RIB nell'esempio) entravano in R_TOT/M_RIB come numeri nudi, senza alcun passo che li
    derivasse."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo.startswith("Ribaltamento e scorrimento"))
    passo_fh = next(p for p in traccia.passi if p.simbolo == "F_h")
    passo_mfh = next(p for p in traccia.passi if p.simbolo == "M_fh")
    assert passo_fh.formula == "k_h * (W_muro + W_terr)"
    assert passo_mfh.formula == "k_h * (W_muro * z_muro + W_terr * z_terr)"
    nome_gov = combo_governante_stabilita(report.data)
    verifica = next(c for c in report.data.ribaltamento_scorrimento if c.nome == nome_gov)
    assert passo_fh.risultato == pytest.approx(verifica.fh_kN)
    assert passo_mfh.risultato == pytest.approx(verifica.m_fh_kNm)
    assert_relazione_coerente(TOOL, TOOL.example)


def test_pressioni_deriva_b_star_quando_fuori_dal_nocciolo():
    """Review finding MISSING_STEP: B* = 3*(B/2-|e|) entrava in p_valle come numero nudo subito
    dopo il confronto |e|>B/6 "non soddisfatta"."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo.startswith("Pressioni sul terreno"))
    passo_nocciolo = next(p for p in traccia.passi if p.simbolo == "|e| entro il nocciolo")
    if passo_nocciolo.esito == "non soddisfatta":
        passo_bstar = next(p for p in traccia.passi if p.simbolo == "B_star")
        assert passo_bstar.formula == "3 * (B / 2 - abs(e))"
    assert_relazione_coerente(TOOL, TOOL.example)


def test_ribaltamento_m_rib_dichiara_il_braccio_di_leva_nel_simbolo():
    """Review finding MISLEADING: l'unica formula di M_RIB stampata usa il braccio H/2 quando la
    combinazione governante è sismica, ma le sette righe di riepilogo statiche sotto la riusano con
    numeri calcolati H/3 (diagramma triangolare) — il simbolo deve dichiarare quale braccio si
    applica alla riga derivata per esteso."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia = next(t for t in report.relazione if t.titolo.startswith("Ribaltamento e scorrimento"))
    passo_m_rib = next(p for p in traccia.passi if p.simbolo.startswith("M_RIB"))
    assert "sismica" in passo_m_rib.simbolo or "statica" in passo_m_rib.simbolo
    assert_relazione_coerente(TOOL, TOOL.example)


def test_armatura_fondazione_deriva_p_star_e_p_star_star():
    """Review finding MISSING_STEP: p*/p** (pressione all'incastro delle mensole di valle/monte)
    entravano in MEd.p.1/MEd.tot come numeri nudi, con l'assunzione del ramo attivo invisibile."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia_valle = next(t for t in report.relazione if t.titolo.startswith("Armatura della fondazione di valle"))
    traccia_monte = next(t for t in report.relazione if t.titolo.startswith("Armatura della fondazione di monte"))
    passo_p_star = next(p for p in traccia_valle.passi if p.simbolo == "p_star")
    passo_p_star_star = next(p for p in traccia_monte.passi if p.simbolo == "p_star_star")
    assert "p_valle" in passo_p_star.formula
    assert "p_valle" in passo_p_star_star.formula
    assert_relazione_coerente(TOOL, TOOL.example)


def test_ribaltamento_cita_la_clausola_verifiche_slu_non_paratie():
    """Review finding WRONG_CLAUSE: il ribaltamento (e M_RIB/M_STAB che lo alimentano) citava
    NTC2018 §6.5.3.1.2 (paratie), non §6.5.3.1.1 (verifiche SLU dei muri di sostegno a gravità,
    Tab. 6.5.I — la stessa clausola già citata dallo scorrimento nella stessa pagina)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    traccia_stab = next(t for t in report.relazione if t.titolo.startswith("Ribaltamento e scorrimento"))
    for simbolo in ("M_RIB", "M_STAB", "OR"):
        passo = next(p for p in traccia_stab.passi if p.simbolo == simbolo or p.simbolo.startswith(simbolo))
        assert passo.clausola == "NTC2018 §6.5.3.1.1", (simbolo, passo.clausola)
    traccia_spinta = next(t for t in report.relazione if t.titolo.startswith("Spinta attiva"))
    for simbolo in ("M_muro", "M_terr"):
        passo = next(p for p in traccia_spinta.passi if p.simbolo == simbolo)
        assert passo.clausola == "NTC2018 §6.5.3.1.1", (simbolo, passo.clausola)
    assert_relazione_coerente(TOOL, TOOL.example)
