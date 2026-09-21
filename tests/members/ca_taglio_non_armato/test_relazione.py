"""`relazione.py` (docs/architecture-phase2.md §6 demo adoption): the harness on the tool's own
example AND on each golden-case input of this package (test_golden.py), both sheets (`Foglio1`
v1: fck from Rck, Asl direct; `1m` v2: fck direct, Asl from N°/Ø) — plus the tool-level checks of
§4 not covered by the harness (the register linkage / relazione text is left to the human review
of §6, not asserted here)."""
import pytest

from strutture.members.ca_taglio_non_armato.tool import TOOLS
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "ca-taglio-non-armato")

# test_golden.py: Spec §8 (Foglio1, v1) and docs/specs/small-units.md ca-taglio-non-armato-v2 (`1m`).
GOLDEN_V1 = {"rck_MPa": 35, "h_mm": 500, "c_mm": 50, "bw_mm": 1000, "asl_mm2": 1005, "ned_kN": 0}
GOLDEN_V2 = {
    "rck_MPa": 40, "fck_MPa": 32, "h_mm": 250, "c_mm": 68, "bw_mm": 1000,
    "n_barre": 5, "diametro_barre_mm": 12, "ned_kN": 0,
}


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
@pytest.mark.parametrize("golden", [GOLDEN_V1, GOLDEN_V2], ids=["v1-Foglio1", "v2-1m"])
def test_relazione_coerente_sui_casi_golden(golden):
    assert_relazione_coerente(TOOL, golden)


def test_ogni_highlight_e_spiegato():
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_relazione_covers_the_one_check_the_tool_declares():
    """The rho_l limit (NTC2018 §4.1.2.3.5.1) is the only `Check` this tool reports; the trace
    must restate it as a comparison step with a non-empty `esito`."""
    from strutture.shared.tool import execute

    report = execute(TOOL, TOOL.example, con_relazione=True)
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == 1
    assert passi_di_verifica[0].simbolo == "ρ_l"
    assert passi_di_verifica[0].esito == "soddisfatta"


def test_step_count_within_the_8_to_25_target():
    from strutture.shared.tool import execute

    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 25
