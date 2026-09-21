import pytest

from strutture.foundations.plinti_isolati.inviluppo import eccentricita_globale, inviluppo
from strutture.foundations.plinti_isolati.riga_verifica import riga_verifica

# docs/specs/fond-plinti-isolati.md Tool-2 golden case: sigma_t,max (kg/cm2) and governing combo, per family.
GOLDEN_PRESSIONE_MAX = {
    "SLU_STR": (1.91656, "ULS_CR96"), "SLV_STR": (1.34935, "EQK_7"), "SLE_RARA": (1.40068, "SLS CHA160"),
    "SLE_FREQ": (1.32108, "SLS FRE42"), "SLE_QP": (1.30679, "SLS QP6"), "SLU_EQU": (1.24675, "ULS EQU9"),
    "SLV_EQU": (1.3658, "EQK EQU7"),
}
GOLDEN_SCORRIMENTO_MIN = {
    "SLU_STR": (80.1776, "ULS_CR96"), "SLV_STR": (96.9745, "EQK_7"), "SLE_RARA": (86.0386, "SLS CHA160"),
    "SLU_EQU": (85.1282, "ULS EQU9"), "SLV_EQU": (89.2418, "EQK EQU7"),
}


def _righe(golden_rows):
    return tuple(
        riga_verifica(row, 4.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0, 20.0, 30.0,
                      metodo_pressioni="sovrapposizione", legacy_compat=True)
        for row in golden_rows
    )


@pytest.mark.golden
def test_inviluppo_pressione_max_golden(golden_rows) -> None:
    righe = _righe(golden_rows)
    inviluppo_righe = inviluppo(righe)
    per_famiglia = {r.famiglia: r for r in inviluppo_righe if r.grandezza == "pressione_max_kpa"}
    for famiglia, (valore_kgcm2, combo) in GOLDEN_PRESSIONE_MAX.items():
        riga = per_famiglia[famiglia]
        assert riga.valore / 100.0 == pytest.approx(valore_kgcm2, rel=1e-4), famiglia
        assert riga.combo == combo, famiglia


@pytest.mark.golden
def test_inviluppo_scorrimento_min_golden(golden_rows) -> None:
    """SLE_FREQ and SLE_QP have no shear demand anywhere in the golden table (>100 for every row),
    so their governing combo is a tie broken first-match, per docs/specs/fond-plinti-isolati.md."""
    righe = _righe(golden_rows)
    inviluppo_righe = inviluppo(righe)
    per_famiglia = {r.famiglia: r for r in inviluppo_righe if r.grandezza == "scorrimento_min"}
    for famiglia, (valore, combo) in GOLDEN_SCORRIMENTO_MIN.items():
        riga = per_famiglia[famiglia]
        assert riga.valore == pytest.approx(valore, rel=1e-4), famiglia
        assert riga.combo == combo, famiglia


@pytest.mark.golden
def test_eccentricita_globale_golden(golden_rows) -> None:
    """docs/specs/fond-plinti-isolati.md: ex/ey envelope mixes ALL 537 rows (not per family)."""
    righe = _righe(golden_rows)
    ecc = eccentricita_globale(righe)
    assert ecc.ex_max.valore == pytest.approx(0.00983574, rel=1e-4)
    assert ecc.ex_max.combo == "EQK_20"
    assert ecc.ex_min.valore == pytest.approx(3.2885e-05, rel=1e-2)
    assert ecc.ex_min.combo == "ULS_CR138"
    assert ecc.ey_max.valore == pytest.approx(0.0885579, rel=1e-4)
    assert ecc.ey_max.combo == "ULS EQU9"
    assert ecc.ey_min.valore == pytest.approx(0.00105179, rel=1e-4)
    assert ecc.ey_min.combo == "SLS CHA33"


@pytest.mark.unit
def test_inviluppo_omette_famiglie_senza_domanda() -> None:
    """A family whose every row has zero shear (senza_domanda) never wins a `min` envelope by
    accident: it is simply absent from the non-legacy inviluppo (no governing row can be picked)."""
    from strutture.shared.load_table import ReactionRow

    riga_senza_taglio = ReactionRow(nodo=1, combo="c1", famiglia="SLE_FREQ", fx_kN=0.0, fy_kN=0.0,
                                     fz_kN=1000.0, mx_kNm=0.0, my_kNm=0.0, mz_kNm=0.0)
    righe = (riga_verifica(riga_senza_taglio, 4.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0, 20.0, 30.0,
                           metodo_pressioni="esatto", legacy_compat=False),)
    inviluppo_righe = inviluppo(righe)
    scorrimento = [r for r in inviluppo_righe if r.grandezza == "scorrimento_min"]
    assert scorrimento == []
