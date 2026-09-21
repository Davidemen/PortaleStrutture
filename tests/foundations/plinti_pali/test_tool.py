import pytest

from strutture.foundations.plinti_pali.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


@pytest.mark.unit
def test_run_con_legacy_compat_false() -> None:
    inputs = {**TOOL.example, "legacy_compat": False}
    report = execute(TOOL, inputs)
    assert report.ok, report.errors
    assert report.data.capacita_trazione is None  # Nmax_env is compressive in the example.


@pytest.mark.unit
def test_avverte_quando_av_si_discosta_da_diametro_pila_su_5() -> None:
    inputs = {**TOOL.example, "av_mm": 470.0}  # default av_mm already equals diametro_pila_mm/5.
    report = execute(TOOL, inputs)
    assert report.ok, report.errors
    assert any("av=" in w for w in report.warnings)


@pytest.mark.unit
def test_nessun_avviso_quando_av_coincide_col_valore_atteso() -> None:
    inputs = {**TOOL.example, "av_mm": TOOL.example["diametro_pila_mm"] / 5.0}
    report = execute(TOOL, inputs)
    assert report.ok, report.errors
    assert report.warnings == ()


@pytest.mark.unit
def test_reazioni_duplicate_rifiutate() -> None:
    riga = TOOL.example["reazioni"][0]
    inputs = {**TOOL.example, "reazioni": [riga, riga]}
    report = execute(TOOL, inputs)
    assert not report.ok
    assert any("duplicata" in e for e in report.errors)


@pytest.mark.unit
def test_palo_teso_richiede_resistenza_a_trazione() -> None:
    reazioni = [{"nodo": 1, "combo": "uplift", "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 10.0,
                 "mx_kNm": 500.0, "my_kNm": 500.0, "mz_kNm": 0.0}]
    inputs = {**TOOL.example, "reazioni": reazioni}
    report = execute(TOOL, inputs)
    assert not report.ok
    assert any("teso" in e for e in report.errors)


@pytest.mark.unit
def test_palo_teso_con_resistenza_a_trazione_fornita() -> None:
    reazioni = [{"nodo": 1, "combo": "uplift", "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 10.0,
                 "mx_kNm": 500.0, "my_kNm": 500.0, "mz_kNm": 0.0}]
    inputs = {**TOOL.example, "reazioni": reazioni, "resistenza_pila_trazione_kN": 500.0}
    report = execute(TOOL, inputs)
    assert report.ok, report.errors
    assert report.data.capacita_trazione is not None


@pytest.mark.unit
def test_avverte_quando_mx_non_e_resistibile_su_schema_2x1() -> None:
    """Code-review finding (MEDIUM, `shared/pile_group/reactions.py`): on a "2x1" schema (no pile
    spread along Y) a real Mx cannot be resisted by differential pile axial force; the tool should
    flag it rather than silently reporting Nmax/Nmin = N/n as if Mx did not exist."""
    inputs = {
        **TOOL.example, "schema_pali": "2x1", "lx_m": 2.0, "ly_m": 0.0,
        "reazioni": [{"nodo": 1, "combo": "A", "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 1000.0,
                      "mx_kNm": 300.0, "my_kNm": 0.0, "mz_kNm": 0.0}],
    }
    report = execute(TOOL, inputs)
    assert report.ok, report.errors
    assert any("Mx" in w for w in report.warnings)


@pytest.mark.unit
def test_nessun_avviso_di_momento_non_resistito_su_schema_2x2() -> None:
    """The default 2x2 example has pile spread in both directions, so this new warning must not
    fire (only the pre-existing `av` warning check applies, which is already covered above)."""
    inputs = {**TOOL.example, "av_mm": TOOL.example["diametro_pila_mm"] / 5.0}
    report = execute(TOOL, inputs)
    assert report.ok, report.errors
    assert not any("non e' resistito" in w for w in report.warnings)


@pytest.mark.unit
def test_avverte_quando_my_non_e_resistibile_su_schema_1x2() -> None:
    inputs = {
        **TOOL.example, "schema_pali": "1x2", "lx_m": 0.0, "ly_m": 2.0,
        "reazioni": [{"nodo": 1, "combo": "A", "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 1000.0,
                      "mx_kNm": 0.0, "my_kNm": 300.0, "mz_kNm": 0.0}],
    }
    report = execute(TOOL, inputs)
    assert report.ok, report.errors
    assert any("My" in w for w in report.warnings)
