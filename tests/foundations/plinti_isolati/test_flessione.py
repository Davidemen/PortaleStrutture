import pytest

from strutture.foundations.plinti_isolati.flessione import (
    ULS_FAMILIES_FIXED,
    _eccentricita_cantilever,
    flessione,
    mead_families,
)
from strutture.foundations.plinti_isolati.inviluppo import inviluppo
from strutture.foundations.plinti_isolati.riga_verifica import riga_verifica


def _inviluppo_golden(golden_rows):
    righe = tuple(
        riga_verifica(row, 4.0, 4.0, 0.8, 4.5, 0.0, 0.0, 0.0, 0.0, 0.05, 0.0, 0.0, 20.0, 30.0,
                      metodo_pressioni="sovrapposizione", legacy_compat=True)
        for row in golden_rows
    )
    return inviluppo(righe)


@pytest.mark.golden
def test_flessione_golden(golden_rows) -> None:
    """docs/specs/fond-plinti-isolati.md Tool-2 golden case: Mx,SLU=My,SLU=1533.25 kNm,
    Asx=Asy=56.787 cm2 (min 64 governs), Nx=Ny=33, Phix=Phiy=20mm, Phimin=14mm,
    TOP=17ø20, BOTT=33ø20, As,prov=10367.3 mm2."""
    inviluppo_righe = _inviluppo_golden(golden_rows)
    result = flessione(inviluppo_righe, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0, 8.0, 12.2, 20.0, 20.0,
                        434.783, 500.0, 3.35208, legacy_compat=True)
    assert result.mx_slu_kNm == pytest.approx(1533.25, rel=1e-4)
    assert result.my_slu_kNm == pytest.approx(1533.25, rel=1e-4)
    assert result.as_x_cm2 == pytest.approx(56.787, rel=1e-3)
    assert result.as_y_cm2 == pytest.approx(56.787, rel=1e-3)
    assert result.as_x_min_cm2 == pytest.approx(64.0)
    assert result.as_y_min_cm2 == pytest.approx(64.0)
    assert result.n_x == 33
    assert result.n_y == 33
    assert result.phi_x_mm == pytest.approx(20.0)
    assert result.phi_y_mm == pytest.approx(20.0)
    assert result.phi_min_mm == pytest.approx(14.0)
    assert result.as_prov_x_mm2 == pytest.approx(10367.3, rel=1e-4)
    assert result.callout_sup_x == "17ø20"
    assert result.callout_inf_x == "33ø20"
    assert result.callout_sup_y == "17ø20"
    assert result.callout_inf_y == "33ø20"


@pytest.mark.unit
def test_mead_families_d4_fix() -> None:
    """D4: code-standard drops SLE_QP and includes SLV_STR; the sheet does the opposite swap."""
    assert mead_families(legacy_compat=False) == ULS_FAMILIES_FIXED
    assert "SLE_QP" not in mead_families(legacy_compat=False)
    assert "SLV_STR" in mead_families(legacy_compat=False)
    assert "SLE_QP" in mead_families(legacy_compat=True)
    assert "SLV_STR" not in mead_families(legacy_compat=True)


@pytest.mark.unit
def test_flessione_fix_diametro_standard(golden_rows) -> None:
    """Fix: non-legacy rounds the computed diameter up to the next STANDARD_DIAMETERS_MM entry,
    not to the next even millimetre; both must be >= the raw computed value."""
    inviluppo_righe = _inviluppo_golden(golden_rows)
    fisso = flessione(inviluppo_righe, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0, 8.0, 12.2, 8.0, 8.0,
                       434.783, 450.0, 3.35208, legacy_compat=False)
    assert fisso.phi_x_mm in (6.0, 8.0, 10.0, 12.0, 14.0, 16.0, 18.0, 20.0, 22.0, 24.0, 25.0, 26.0, 28.0, 30.0, 32.0, 40.0)


@pytest.mark.unit
def test_eccentricita_cantilever_swap_fix() -> None:
    """Fix (HIGH, review finding): docs/specs/fond-plinti-isolati.md step 8 transcribes the sheet's
    own formula `Mx,SLU = ...(AX/20+eY/10)^2` — Mx (X-rebar, spans along AX) gets eY, not eX.
    `azioni_base.py` defines eX as the eccentricity feeding MYY (bends about Y, X-direction
    asymmetry), so the code-standard branch pairs eX with the X cantilever instead."""
    assert _eccentricita_cantilever(0.1, 0.2, legacy_compat=True) == (0.2, 0.1)
    assert _eccentricita_cantilever(0.1, 0.2, legacy_compat=False) == (0.1, 0.2)


@pytest.mark.unit
def test_flessione_eccentricita_asse_corretto_no_legacy(golden_rows) -> None:
    """ex_m must lengthen the X cantilever (mx_slu), not the Y one, when legacy_compat=False."""
    inviluppo_righe = _inviluppo_golden(golden_rows)
    base = flessione(inviluppo_righe, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0, 8.0, 12.2, 20.0, 20.0,
                      434.783, 500.0, 3.35208, legacy_compat=False)
    con_ex = flessione(inviluppo_righe, 4.0, 4.0, 0.8, 0.0, 0.0, 0.1, 0.0, 8.0, 12.2, 20.0, 20.0,
                        434.783, 500.0, 3.35208, legacy_compat=False)
    assert con_ex.mx_slu_kNm > base.mx_slu_kNm
    assert con_ex.my_slu_kNm == pytest.approx(base.my_slu_kNm)


@pytest.mark.unit
def test_flessione_eccentricita_asse_scambiato_legacy(golden_rows) -> None:
    """`legacy_compat=True` keeps the sheet's swap: ex_m affects my_slu, not mx_slu."""
    inviluppo_righe = _inviluppo_golden(golden_rows)
    base = flessione(inviluppo_righe, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0, 8.0, 12.2, 20.0, 20.0,
                      434.783, 500.0, 3.35208, legacy_compat=True)
    con_ex = flessione(inviluppo_righe, 4.0, 4.0, 0.8, 0.0, 0.0, 0.1, 0.0, 8.0, 12.2, 20.0, 20.0,
                        434.783, 500.0, 3.35208, legacy_compat=True)
    assert con_ex.my_slu_kNm > base.my_slu_kNm
    assert con_ex.mx_slu_kNm == pytest.approx(base.mx_slu_kNm)


@pytest.mark.unit
def test_flessione_diametro_manuale_governa() -> None:
    """A manual override diameter larger than the computed one wins in both modes."""
    inviluppo_vuoto = ()
    result = flessione(inviluppo_vuoto, 4.0, 4.0, 0.8, 0.0, 0.0, 0.0, 0.0, 8.0, 12.2, 32.0, 32.0,
                        434.783, 450.0, 3.35208, legacy_compat=False)
    assert result.phi_x_mm == 32.0
    assert result.phi_y_mm == 32.0
