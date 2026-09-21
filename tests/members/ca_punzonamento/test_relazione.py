"""`relazione.py` (docs/architecture-phase2.md §6 wave-1 adoption): the harness on the tool's own
example, on every golden/oracle input set this package's own tests already use (test_golden.py,
test_oracle.py, test_free_golden_375n.py — all recorded `legacy_compat=True`; `relazione` only
describes the code-standard branch, docs/architecture-phase2.md §1, so every reused fixture is fed
back with the flag flipped), and on parameter variations that switch branches: a different column
shape, a failing check, a manual perimeter/area override, and the `armatura` block present vs empty
(the tool's own example already covers "empty" — no reinforcement needed)."""
import pytest

from strutture.members.ca_punzonamento.tool import TOOLS
from strutture.shared.tool import execute
from tests.members.ca_punzonamento.test_fixed_behaviour import BASE as FIXED_BASE
from tests.members.ca_punzonamento.test_free_golden_375n import INPUTS as N375_INPUTS
from tests.members.ca_punzonamento.test_golden import GOLDEN_INPUTS
from tests.members.ca_punzonamento.test_oracle import FIXTURE as ORACLE_FIXTURE
from tests.members.ca_punzonamento.test_oracle import _inputs as _oracle_inputs
from tests.shared.relazione.harness import assert_ogni_highlight_e_spiegato, assert_relazione_coerente

pytestmark = pytest.mark.unit

TOOL = next(t for t in TOOLS if t.name == "ca-punzonamento")


def _standard(raw: dict) -> dict:
    return {**raw, "legacy_compat": False}


def _oracle_case(index: int) -> dict:
    raw = _standard(_oracle_inputs(ORACLE_FIXTURE[index]).model_dump())
    if index == 4:
        # D55=28 (tables.PHI_STAFFA_LEGACY_TYPO_MM) is rejected outside legacy_compat; 18
        # (PHI_STAFFA_LEGACY_FIX_MM) is its code-standard replacement, exactly as
        # test_fixed_behaviour.test_phi_staffa_18_is_the_code_standard_replacement_for_the_typo
        # establishes — the case itself (D2 raised until the armatura block is needed) is unchanged.
        raw["phi_staffa_mm"] = 18.0
    return raw


def _375n_case() -> dict:
    i = N375_INPUTS
    return _standard({
        "ved_kN": i["D2"], "pterreno_MPa": i["D3"], "lato_a_mm": i["D4"], "lato_b_mm": i["D5"], "h_mm": i["D6"],
        "diametro_mm": i["D7"], "fck_MPa": i["D8"], "copriferro_mm": i["D9"], "posizione": "interno",
        "px_mm": i["D27"], "py_mm": i["D28"], "phix_mm": i["D29"], "phiy_mm": i["D30"],
        "paddx_mm": i["D31"], "paddy_mm": i["D32"], "phiaddx_mm": i["D33"], "phiaddy_mm": i["D34"],
        "a1eff_mm": i["D46"], "bu_mm": i["D47"], "st_mm": i["D52"], "phi_staffa_mm": i["D55"], "n_staffe": i["D58"],
    })


GOLDEN_CASES = {
    # test_golden.py §8 (Shotblast_225N) — same numbers as TOOL.example, plus legacy_compat=True.
    "golden-shotblast-225n": _standard(GOLDEN_INPUTS),
    # test_oracle.py cases 0-5 (Shotblast_225N variations, LibreOffice-recalculated).
    "oracle-0-rettangolare": _oracle_case(0),
    "oracle-1-circolare": _oracle_case(1),  # different column shape (D4=0, D7=500)
    "oracle-2-perimetro-manuale": _oracle_case(2),  # umanuale_mm set (D21=3000)
    "oracle-3-area-manuale": _oracle_case(3),  # a_amanuale_mm2 set (D24=3000000)
    "oracle-4-armatura-necessaria": _oracle_case(4),  # armatura block present (Ved raised)
    "oracle-5-rho-oltre-2pc": _oracle_case(5),  # rho_l > 2%, v_rd_c uses the capped value
    # test_free_golden_375n.py: non-square rectangular column (A=520, B=900).
    "375n-rettangolo-non-quadrato": _375n_case(),
}

VARIAZIONI = {
    # A failing check the golden/oracle sets above do not exercise: the Asw,min check itself fails
    # (larger tangential spacing st_mm raises Asw,min past the fixed phi8 stirrup area).
    "asw-min-non-soddisfatto": {**FIXED_BASE, "ved_kN": 1300, "phi_staffa_mm": 8, "st_mm": 600},
    # An additional top-up rebar layer in x only (paddx_mm/phiaddx_mm > 0, y direction empty):
    # switches the rho_x formula branch none of the golden/oracle sets exercise.
    "armatura-aggiuntiva-in-x": {**FIXED_BASE, "paddx_mm": 300, "phiaddx_mm": 12},
}


def test_tool_declares_relazione():
    assert TOOL.relazione is not None


def test_relazione_coerente_sullesempio():
    assert_relazione_coerente(TOOL, TOOL.example)


@pytest.mark.golden
@pytest.mark.parametrize("raw", GOLDEN_CASES.values(), ids=GOLDEN_CASES.keys())
def test_relazione_coerente_sui_casi_golden(raw):
    assert_relazione_coerente(TOOL, raw)


@pytest.mark.parametrize("raw", VARIAZIONI.values(), ids=VARIAZIONI.keys())
def test_relazione_coerente_sulle_variazioni(raw):
    assert_relazione_coerente(TOOL, raw)


def test_ogni_highlight_e_spiegato_senza_armatura():
    """`PerimetroCriticoOutput.rapporto` ("v_Ed,i/v_Rd,i") is the only highlight on the tool's own
    example (no reinforcement needed)."""
    assert_ogni_highlight_e_spiegato(TOOL, TOOL.example)


def test_ogni_highlight_e_spiegato_con_armatura():
    """`ArmaturaOutput.ved_su_vrd` ("V_Ed/V_Rd") only exists once reinforcement is needed — covered
    separately since the tool's own example does not need it."""
    assert_ogni_highlight_e_spiegato(TOOL, GOLDEN_CASES["oracle-4-armatura-necessaria"])


def test_relazione_covers_every_check_of_the_example():
    """The 3 `Check` entries compose.py always reports (no armatura on the example) each get their
    own restated comparison `Passo`."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    assert len(report.checks) == 3
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == 3
    assert {p.simbolo for p in passi_di_verifica} == {"v_Ed,0", "ρ_l", "v_Ed,i/v_Rd,i"}


def test_relazione_covers_every_check_when_reinforcement_is_needed():
    """All 8 `Check` entries (3 base + 5 armatura) get a restated comparison `Passo`; the a1,eff
    range check restates as two `Passo` (lower and upper bound: the notation allows at most ONE
    comparison per formula, docs/architecture-phase2.md §2)."""
    raw = GOLDEN_CASES["oracle-4-armatura-necessaria"]
    report = execute(TOOL, raw, con_relazione=True)
    assert report.data.armatura is not None
    assert len(report.checks) == 8
    passi_di_verifica = [p for t in report.relazione for p in t.passi if p.esito]
    assert len(passi_di_verifica) == 9


def test_step_count_within_the_8_to_25_target_on_the_example():
    report = execute(TOOL, TOOL.example, con_relazione=True)
    totale = sum(len(t.passi) for t in report.relazione)
    assert 8 <= totale <= 25


def test_titolo_del_perimetro_critico_indica_il_perimetro_governante():
    """docs/architecture-phase2.md §5: a many-rows tool traces the GOVERNING row only, and says so
    in the Traccia title."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    titoli = [t.titolo for t in report.relazione]
    assert any("perimetro governante" in t for t in titoli)


def test_a_governante_non_collide_con_il_lato_del_pilastro():
    """Review finding (WRONG_FORMULA): the defining Passo for `a_governante_mm` (860 mm on the
    golden case) used to be printed under the SAME identifier `a` that `u_i`/`A_a` use for the
    column side (`lato_a_mm`, 400 mm) — a reader re-evaluating those formulas with the only `a`
    definition on the page (860) gets u_i≈7924mm/wrong A_a instead of the real 7003,54mm. The
    defining Passo must use a distinct identifier from the column side `a`/`b`."""
    report = execute(TOOL, GOLDEN_CASES["golden-shotblast-225n"], con_relazione=True)
    traccia = next(t for t in report.relazione if "perimetro governante" in t.titolo)
    passo_a_gov = next(p for p in traccia.passi if p.risultato == pytest.approx(860.0))
    assert passo_a_gov.simbolo != "a"

    passo_ui = next(p for p in traccia.passi if p.simbolo == "u_i")
    valore_a_in_ui = next(v.valore for v in passo_ui.valori if v.simbolo == "a")
    assert valore_a_in_ui == pytest.approx(400.0)  # il lato del pilastro, mai il valore di a_gov (860)


def test_riduzione_terreno_cita_leq_6_48_non_6_4_5_3():
    """Review finding (WRONG_FORMULA): beta is applied to the gross shear before the soil-pressure
    deduction (a conservative simplification of EN1992-1-1 eq. 6.48, which reduces first and only
    then applies beta); the printed clause used to cite §6.4.5(3) (v_Rd,max at the column face, an
    unrelated clause) for `V_Ed,red,0` and the generic §6.4.4 for `V_Ed,red,ui`. Both must cite the
    real source of the soil-pressure reduction, §6.4.4(2) eq. (6.48)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo_red_0 = next(p for t in report.relazione for p in t.passi if p.simbolo == "V_Ed,red,0")
    passo_red_ui = next(p for t in report.relazione for p in t.passi if p.simbolo == "V_Ed,red,ui")
    for passo in (passo_red_0, passo_red_ui):
        assert "6.4.4(2)" in passo.clausola
        assert "6.4.5(3)" not in passo.clausola


def test_dx_e_d_citano_6_4_2_1_non_6_4_4_1():
    """Review finding (WRONG_CLAUSE): `d_x`/`d` (effective depth) used to cite §6.4.4(1), which is
    the v_Rd,c/rho_l clause; the effective-depth definition is §6.4.2(1) eq. (6.32)."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    for simbolo in ("d_x", "d"):
        passo = next(p for t in report.relazione for p in t.passi if p.simbolo == simbolo)
        assert passo.clausola == "EN 1992-1-1 §6.4.2(1)"


def test_coefficiente_vrd_max_non_collide_con_il_copriferro():
    """Review finding (MISLEADING): `c` names the cover (`d_x = H - c - φ_x/2`) AND, four rows
    later, the v_Rd,max coefficient (`v_Rd,max = c·(0,6·(1-f_ck/250))·f_cd`) — the same symbol with
    two different meanings/units in the same trace. The v_Rd,max coefficient must use a distinct
    identifier."""
    report = execute(TOOL, TOOL.example, con_relazione=True)
    passo_dx = next(p for t in report.relazione for p in t.passi if p.simbolo == "d_x")
    assert any(v.simbolo == "c" for v in passo_dx.valori)  # il copriferro resta "c"
    passo_vrdmax = next(p for t in report.relazione for p in t.passi if p.simbolo == "v_Rd,max")
    assert "c" not in {v.simbolo for v in passo_vrdmax.valori}
