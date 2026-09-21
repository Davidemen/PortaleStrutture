import math

import pytest

from strutture.foundations.plinti_pali.puntoni_tiranti import puntoni_tiranti
from strutture.shared.report import CalcError

COMUNI = {
    "h_plinto_m": 1.2, "copriferro_mm": 50.0, "diametro_inf_x_mm": 24.0, "diametro_inf_y_mm": 24.0,
    "diametro_pila_mm": 600.0, "diametro_tirante_xy_mm": 32.0, "diametro_tirante_x_mm": 24.0,
    "diametro_tirante_y_mm": 24.0, "n_tirante_xy": 2, "n_tirante_x": 8, "n_tirante_y": 8,
    "n_max_env_kN": 896.06124265, "bx_pilastro_mm": 700.0, "by_pilastro_mm": 700.0,
    "fck_MPa": 32.0, "gamma_c": 1.5, "fyd_MPa": 391.304347826087,
}


@pytest.mark.unit
def test_schema_1x1_appoggio_diretto_senza_tiranti() -> None:
    result = puntoni_tiranti(1, 1, 0.0, 0.0, legacy_compat=False, **COMUNI)
    assert result.puntone.theta_deg is None
    assert result.puntone.fus_kN == pytest.approx(COMUNI["n_max_env_kN"], rel=1e-9)
    assert result.puntone.acs_mm2 == pytest.approx(700.0 * 700.0, rel=1e-9)
    assert result.tirante_xy is None
    assert result.tirante_x is None
    assert result.tirante_y is None


@pytest.mark.unit
def test_schema_2x1_un_solo_tirante_lungo_x() -> None:
    result = puntoni_tiranti(2, 1, 2.0, 0.0, legacy_compat=False, **COMUNI)
    assert result.puntone.theta_deg is not None
    assert result.puntone.lxy_m == pytest.approx(1.0, rel=1e-9)
    assert result.tirante_xy is None
    assert result.tirante_x is not None
    assert result.tirante_y is None
    # Single-tie geometry: the full strut thrust goes to the one tie (no XY/orthogonal split).
    assert result.tirante_x.fut_kN == pytest.approx(
        result.puntone.fus_kN * math.cos(math.radians(result.puntone.theta_deg)), rel=1e-9,
    )


@pytest.mark.unit
def test_fix_tiranti_ortogonali_usa_seno_per_y_su_griglia_non_quadrata() -> None:
    """Da verificare / fix: the sheet resolves both orthogonal ties with the same `cos(alpha)`
    (only correct for Lx=Ly); the fix uses `sin(alpha)` for the Y tie on a non-square grid. Both
    fixed ties also carry the strut's `cos(theta)` horizontal-thrust projection (see next test)."""
    fisso = puntoni_tiranti(2, 2, 3.0, 1.0, legacy_compat=False, **COMUNI)
    legacy = puntoni_tiranti(2, 2, 3.0, 1.0, legacy_compat=True, **COMUNI)
    theta_rad = math.radians(fisso.puntone.theta_deg)
    assert fisso.tirante_y.fut_kN != pytest.approx(legacy.tirante_y.fut_kN)
    # cos(theta) projection now scales the fixed X tie too (node equilibrium, EC2 §6.5.3).
    assert fisso.tirante_x.fut_kN == pytest.approx(legacy.tirante_x.fut_kN * math.cos(theta_rad), rel=1e-9)


@pytest.mark.unit
def test_fix_tiranti_ortogonali_usano_la_proiezione_orizzontale_del_puntone() -> None:
    """Code-review finding (MEDIUM, EC2 §6.5.3 node equilibrium): the orthogonal ties must resolve
    the strut's HORIZONTAL thrust (Fus*cos(theta)), not the full inclined strut force; `legacy_compat`
    keeps the sheet's own formula (missing this projection) unconditionally."""
    fisso = puntoni_tiranti(2, 2, 2.0, 2.0, legacy_compat=False, **COMUNI)
    legacy = puntoni_tiranti(2, 2, 2.0, 2.0, legacy_compat=True, **COMUNI)
    theta_rad = math.radians(fisso.puntone.theta_deg)
    assert theta_rad != pytest.approx(0.0)
    assert fisso.tirante_x.fut_kN == pytest.approx(legacy.tirante_x.fut_kN * math.cos(theta_rad), rel=1e-9)
    assert fisso.tirante_y.fut_kN == pytest.approx(legacy.tirante_y.fut_kN * math.cos(theta_rad), rel=1e-9)


@pytest.mark.unit
def test_schema_2x2_e_2x1_concordano_su_griglia_quadrata_al_limite() -> None:
    """On a square grid `cos(alpha)=sin(alpha)`, so the fix and legacy X/Y tie formulas agree up to
    the `cos(theta)` horizontal-thrust projection (docs/specs/fond-plinti-pali.md golden case)."""
    fisso = puntoni_tiranti(2, 2, 2.0, 2.0, legacy_compat=False, **COMUNI)
    legacy = puntoni_tiranti(2, 2, 2.0, 2.0, legacy_compat=True, **COMUNI)
    theta_rad = math.radians(fisso.puntone.theta_deg)
    assert fisso.tirante_y.fut_kN == pytest.approx(legacy.tirante_y.fut_kN * math.cos(theta_rad), rel=1e-9)


@pytest.mark.unit
def test_nodo_2x2_usa_ctt_en_in_modalita_normale() -> None:
    """Code-review finding (CRITICAL): the sheet's own non-standard node coefficients
    (K1_CCC=1.18/0.85, K2=0.88 for the "two ties anchored" node) must be gated behind
    `legacy_compat=True`; the fixed mode uses EN 1992-1-1 §6.5.4(4) k1=1.0/k3=0.75, classifying the
    2x2 bottom node (two tie directions anchored) as CTT. C32/40, gammaC=1.5, alphaCC=0.85 gives
    sigma_Rd,max = 0.75*0.872*18.1333 = 11.86 MPa (vs the sheet's 13.915 MPa, +17% non-conservative)."""
    fisso = puntoni_tiranti(2, 2, 2.0, 2.0, legacy_compat=False, **COMUNI)
    legacy = puntoni_tiranti(2, 2, 2.0, 2.0, legacy_compat=True, **COMUNI)
    assert legacy.puntone.sigma_rd_max_MPa == pytest.approx(13.914794666666667, rel=1e-6)
    assert fisso.puntone.sigma_rd_max_MPa == pytest.approx(11.8592, rel=1e-4)
    assert fisso.puntone.sigma_rd_max_MPa < legacy.puntone.sigma_rd_max_MPa


@pytest.mark.unit
def test_nodo_2x1_usa_cct_en_in_modalita_normale() -> None:
    """One tie direction anchored ("2x1"/"1x2") -> CCT node, k2=0.85 (EN default)."""
    fisso = puntoni_tiranti(2, 1, 2.0, 0.0, legacy_compat=False, **COMUNI)
    assert fisso.puntone.sigma_rd_max_MPa == pytest.approx(0.85 * (1.0 - 32.0 / 250.0) * (0.85 * 32.0 / 1.5), rel=1e-6)


@pytest.mark.unit
def test_puntone_troppo_inclinato_solleva_calc_error_in_modalita_normale() -> None:
    """Code-review finding (CRITICAL): the sheet's 25° floor silently substitutes a flatter-than-real
    strut, understating both Fus and Fut; the fix raises `CalcError` outside the valid band instead
    (a flat, wide-spaced cap gives a real theta well below the 21.8deg floor)."""
    piatto = {**COMUNI, "h_plinto_m": 0.6}
    with pytest.raises(CalcError):
        puntoni_tiranti(2, 2, 6.0, 6.0, legacy_compat=False, **piatto)


@pytest.mark.unit
def test_puntone_inclinazione_reale_non_forzata_a_25_gradi_in_modalita_normale() -> None:
    """docs review example: lx=ly=4m, h=1.2m -> real theta=21.43deg (inside the valid band, so no
    CalcError), the legacy 25deg floor previously understated Fus/Fut by clamping it upward."""
    comuni = {**COMUNI, "h_plinto_m": 1.2}
    fisso = puntoni_tiranti(2, 2, 4.0, 4.0, legacy_compat=False, **comuni)
    legacy = puntoni_tiranti(2, 2, 4.0, 4.0, legacy_compat=True, **comuni)
    assert fisso.puntone.theta_deg == pytest.approx(21.43, abs=0.1)
    assert legacy.puntone.theta_deg == pytest.approx(25.0, rel=1e-9)
    assert fisso.puntone.fus_kN > legacy.puntone.fus_kN
