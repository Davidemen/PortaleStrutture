"""`relazione.py` (docs/architecture-phase2.md §6, wave 2/3 adoption) for `ca-sezione-dominio-mn`:
the harness on the tool's own example (biaxial governing row) and on the "outside the domain"
scenario `test_compose.py` already exercises (no golden/oracle fixture exists for this package —
`compose.py`'s own docstring: "No spreadsheet exists ... no legacy_compat mode"), plus 4
variations across the package that switch the governing row's `TipoPressoflessione` branch:
uniaxial x, uniaxial y, axial-only (minimum eccentricity) and outside-the-domain in tension."""
import pytest

from strutture.members.ca_sezione_mn.tool import TOOLS
from strutture.shared.tool import execute
from tests.members.ca_sezione_mn.test_compose import EXAMPLE as COMPOSE_EXAMPLE
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = TOOLS[0]


def test_tool_declares_relazione() -> None:
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio() -> None:
    """Il caso di esempio del tool: combinazione governante biassiale (SLU2)."""
    assert_relazione_coerente(TOOL, TOOL.example)


def test_relazione_coerente_sul_caso_di_test_compose() -> None:
    """`test_compose.py::EXAMPLE`, lo scenario end-to-end che il resto del pacchetto già usa come
    proprio caso di riferimento (nessun golden/oracle esiste per questo tool)."""
    assert_relazione_coerente(TOOL, COMPOSE_EXAMPLE)


def test_ogni_highlight_e_spiegato() -> None:
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_step_count_within_the_8_to_30_target() -> None:
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 30


def test_relazione_covers_every_check_the_tool_declares() -> None:
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert len(report.checks) == 1
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == len(report.checks)
    for check in report.checks:
        atteso = "soddisfatta" if check.passed else "non soddisfatta"
        assert any(p.esito == atteso for p in passi_di_verifica), f"nessun Passo per il Check {check.name!r}"


def _con_singola_azione(azione: dict) -> dict:
    return {**TOOL.example, "azioni": [azione]}


def test_variazione_ramo_uniassiale_x() -> None:
    variazione = _con_singola_azione({"nome": "UX", "n_ed_kN": 800.0, "m_ed_x_kNm": 150.0, "m_ed_y_kNm": 0.0})
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.governante.tipo == "uniassiale x"
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_ramo_uniassiale_y() -> None:
    variazione = _con_singola_azione({"nome": "UY", "n_ed_kN": 400.0, "m_ed_x_kNm": 0.0, "m_ed_y_kNm": 80.0})
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.governante.tipo == "uniassiale y"
    assert_relazione_coerente(TOOL, variazione)


def test_variazione_ramo_assiale_eccentricita_minima() -> None:
    variazione = _con_singola_azione({"nome": "N0", "n_ed_kN": 1500.0, "m_ed_x_kNm": 0.0, "m_ed_y_kNm": 0.0})
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.governante.tipo == "compressione/trazione semplice"
    assert_relazione_coerente(TOOL, variazione)


def test_m_rd_x_riporta_il_segno_di_m_ed_nel_simbolo() -> None:
    """review finding MISSING_STEP: 'M_Rd,x = M_Rd,x,pos' è vero solo nel ramo M_Ed,x ≥ 0; `nota`
    non è mai stampata da `traccia_a_testo`, quindi il segno selezionato deve comparire nel
    simbolo (esempio del tool: combinazione biassiale)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert report.data.governante.tipo == "biassiale"
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("M_Rd,x") and p.simbolo not in ("M_Rd,x+", "M_Rd,x-"))
    assert passo.simbolo != "M_Rd,x"
    assert "M_Ed,x" in passo.simbolo


def test_esponente_a_riporta_il_segmento_di_tabella_nel_simbolo() -> None:
    """review finding MISSING_STEP: l'esponente a (§5.8.9(4)) stampava solo il segmento
    effettivamente selezionato della tabella (N_Ed/N_Rd, a), senza dire quale — il segmento deve
    comparire nel simbolo stampato."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo.startswith("a") and "segmento" in p.simbolo)
    assert passo.simbolo != "a"


def test_variazione_fuori_dal_dominio_in_trazione() -> None:
    """N_Ed molto negativo (trazione), simmetrico allo scenario di compressione già in
    `test_compose.py::test_run_riga_fuori_dal_dominio_fallisce_senza_eccezione`."""
    variazione = _con_singola_azione({"nome": "OORNEG", "n_ed_kN": -1.0e7, "m_ed_x_kNm": 10.0, "m_ed_y_kNm": 0.0})
    report = execute(TOOL, variazione, con_relazione=True)
    assert report.ok
    assert report.data.governante.dentro is False
    assert report.data.governante.rapporto is None
    passo = next(p for t in report.relazione for p in t.passi if p.simbolo == "η")
    assert passo.esito == "non soddisfatta"
    assert "N_min" in passo.formula
    assert_relazione_coerente(TOOL, variazione)
