import pytest

from strutture.foundations.plinti_pali.taglio_punzonamento import punzonamento_colonna, punzonamento_palo, taglio
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_taglio_golden_case_legacy() -> None:
    result = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                     32.0, 1.5, legacy_compat=True)
    assert result.d_mm == pytest.approx(1102.0, rel=1e-9)
    assert result.vrd_c_kN == pytest.approx(1486.1767085042982, rel=1e-6)
    assert result.utilizzo == pytest.approx(0.22058853347117796, rel=1e-6)
    assert result.verificato is True


@pytest.mark.unit
def test_fix_k_e_rho_divergono_dal_legacy() -> None:
    """docs/architecture-batch2.md §7 `plinti-pali AR99`/`AR100`: k unclamped vs clamped at 2.0, and
    rho divided by the full plinth width vs the 1m design strip."""
    legacy = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                     32.0, 1.5, legacy_compat=True)
    fisso = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                    32.0, 1.5, legacy_compat=False)
    assert fisso.rho == pytest.approx(legacy.rho * 4.0, rel=1e-6)  # b=4000mm = 4 x 1000mm strip
    assert fisso.rho == pytest.approx(4523.893421169302 / (1000.0 * 1102.0), rel=1e-6)


@pytest.mark.unit
def test_k_si_clamps_a_2_con_altezza_utile_molto_piccola() -> None:
    fisso = taglio(500.0, 0.0, 4000.0, 250.0, 50.0, 24.0, 100.0, 1000.0, 30.0, 1.5, legacy_compat=False)
    legacy = taglio(500.0, 0.0, 4000.0, 250.0, 50.0, 24.0, 100.0, 1000.0, 30.0, 1.5, legacy_compat=True)
    assert fisso.k == pytest.approx(2.0, rel=1e-9)
    assert legacy.k > 2.0


@pytest.mark.unit
def test_altezza_utile_non_positiva_solleva_calc_error() -> None:
    """Code-review finding (CRITICAL): reachable from valid, in-bounds `PlintoSuPaliInput` fields
    (e.g. h_plinto_m=0.1, copriferro_cm=30, diametro_long_assunto_mm=24 -> d<0); must raise
    `CalcError` (caught by `shared.tool.execute`), not a bare `ValueError`."""
    with pytest.raises(CalcError):
        taglio(500.0, 0.0, 4000.0, 100.0, 300.0, 24.0, 100.0, 1000.0, 30.0, 1.5, legacy_compat=False)


@pytest.mark.unit
def test_av_troppo_piccolo_viene_clampato_a_0_5d_in_modalita_normale() -> None:
    """Code-review finding (CRITICAL, EC2 §6.2.2(6)): av below 0.5d must be raised to 0.5d before
    forming beta = av/(2d); the sheet's own default av=120mm with d=1102mm golden-case-like geometry
    gives an unclamped beta of ~0.054 instead of the required floor of 0.25."""
    fisso = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 120.0, 4523.893421169302,
                    32.0, 1.5, legacy_compat=False)
    legacy = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 120.0, 4523.893421169302,
                     32.0, 1.5, legacy_compat=True)
    d_mm = fisso.d_mm
    beta_fisso = fisso.ved_ridotto_kN / fisso.ved_kN
    beta_legacy = legacy.ved_ridotto_kN / legacy.ved_kN
    assert beta_fisso == pytest.approx(0.25, rel=1e-6)  # av clamped to 0.5*d -> beta = 0.5d/(2d) = 0.25.
    assert beta_legacy == pytest.approx(120.0 / (2.0 * d_mm), rel=1e-6)  # legacy stays unclamped.
    assert fisso.ved_ridotto_kN > legacy.ved_ridotto_kN


@pytest.mark.unit
def test_av_oltre_2d_viene_clampato_beta_a_1_in_modalita_normale() -> None:
    fisso = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 5000.0, 4523.893421169302,
                    32.0, 1.5, legacy_compat=False)
    beta_fisso = fisso.ved_ridotto_kN / fisso.ved_kN
    assert beta_fisso == pytest.approx(1.0, rel=1e-9)


@pytest.mark.unit
def test_verifica_schiacciamento_eq_6_5_puo_governare() -> None:
    """EC2 eq. 6.5 companion check: VEd (unreduced) <= coeff_vrd_max*b*d*nu*fcd; only enters
    `verificato` in normal mode (legacy reproduces the sheet, which has no such check)."""
    fisso = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                    32.0, 1.5, legacy_compat=False)
    assert fisso.ved_max_kN > 0.0
    assert fisso.verificato == (fisso.ved_ridotto_kN <= fisso.vrd_c_kN and fisso.ved_kN <= fisso.ved_max_kN)


@pytest.mark.unit
def test_taglio_coeff_vrd_max_default_is_04_a1_2014() -> None:
    default = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                      32.0, 1.5, legacy_compat=False)
    explicit = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                       32.0, 1.5, legacy_compat=False, coeff_vrd_max=0.4)
    assert default.ved_max_kN == pytest.approx(explicit.ved_max_kN, rel=1e-12)


@pytest.mark.unit
def test_taglio_coeff_vrd_max_04_vs_05_ratio_08_in_modalita_normale() -> None:
    a1_2014 = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                      32.0, 1.5, legacy_compat=False, coeff_vrd_max=0.4)
    na_it = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                    32.0, 1.5, legacy_compat=False, coeff_vrd_max=0.5)
    assert a1_2014.ved_max_kN == pytest.approx(na_it.ved_max_kN * 0.8, rel=1e-9)


@pytest.mark.unit
def test_taglio_coeff_vrd_max_ignored_in_legacy_mode() -> None:
    legacy_04 = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                        32.0, 1.5, legacy_compat=True, coeff_vrd_max=0.4)
    legacy_05 = taglio(1899.9593, 1174.7008, 4000.0, 1200.0, 50.0, 24.0, 470.0, 4523.893421169302,
                        32.0, 1.5, legacy_compat=True, coeff_vrd_max=0.5)
    assert legacy_04.ved_max_kN == pytest.approx(legacy_05.ved_max_kN, rel=1e-12)


@pytest.mark.unit
def test_punzonamento_colonna_golden_case() -> None:
    result = punzonamento_colonna(3074.6601, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                   legacy_compat=True)
    assert result.u_mm == pytest.approx(2800.0, rel=1e-9)
    assert result.vrd_max_kN == pytest.approx(17220.116479999997, rel=1e-6)
    assert result.utilizzo == pytest.approx(0.17855048213936356, rel=1e-6)
    assert result.beta == pytest.approx(1.0, rel=1e-9)
    assert result.interasse_x_sufficiente is True
    assert result.interasse_y_sufficiente is True


@pytest.mark.unit
def test_punzonamento_colonna_alpha_cc_085_in_modalita_normale() -> None:
    """Code-review finding (HIGH): `alpha_cc=1.0` was hard-coded, contradicting NTC2018 §4.1.2.1.1.1
    (and `shared.materials.concrete.ALPHA_CC=0.85`, used by every other tool). `coeff_vrd_max` is held
    at the sheet's own 0.5 here so only `alpha_cc`'s effect is isolated."""
    legacy = punzonamento_colonna(3074.6601, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                   legacy_compat=True)
    fisso = punzonamento_colonna(3074.6601, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                  legacy_compat=False, coeff_vrd_max=0.5)
    assert fisso.vrd_max_kN == pytest.approx(legacy.vrd_max_kN * 0.85, rel=1e-6)


@pytest.mark.unit
def test_punzonamento_colonna_coeff_vrd_max_default_is_04_a1_2014() -> None:
    """docs/divergences/ec2-shared.md: `coeff_vrd_max` is the tool's own explicit advanced choice,
    defaulting to the more conservative EN 1992-1-1/A1:2014 value (0.4), not a silent shared default."""
    default = punzonamento_colonna(3074.6601, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                    legacy_compat=False)
    explicit = punzonamento_colonna(3074.6601, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                     legacy_compat=False, coeff_vrd_max=0.4)
    assert default.vrd_max_kN == pytest.approx(explicit.vrd_max_kN, rel=1e-12)


@pytest.mark.unit
def test_punzonamento_colonna_coeff_vrd_max_04_vs_05_ratio_08_in_modalita_normale() -> None:
    a1_2014 = punzonamento_colonna(3074.6601, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                    legacy_compat=False, coeff_vrd_max=0.4)
    na_it = punzonamento_colonna(3074.6601, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                  legacy_compat=False, coeff_vrd_max=0.5)
    assert a1_2014.vrd_max_kN == pytest.approx(na_it.vrd_max_kN * 0.8, rel=1e-9)


@pytest.mark.unit
def test_punzonamento_colonna_coeff_vrd_max_ignored_in_legacy_mode() -> None:
    """legacy_compat=True must keep reproducing the sheet's own `0.5`/`alpha_cc=1.0` combination
    regardless of `coeff_vrd_max`."""
    legacy_04 = punzonamento_colonna(3074.6601, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                      legacy_compat=True, coeff_vrd_max=0.4)
    legacy_05 = punzonamento_colonna(3074.6601, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                      legacy_compat=True, coeff_vrd_max=0.5)
    assert legacy_04.vrd_max_kN == pytest.approx(legacy_05.vrd_max_kN, rel=1e-12)
    assert legacy_04.vrd_max_kN == pytest.approx(17220.116479999997, rel=1e-6)


@pytest.mark.unit
def test_punzonamento_colonna_beta_eccentricita_in_modalita_normale() -> None:
    """Code-review finding (HIGH, EC2 §6.4.3): beta=1 (no eccentricity effect) was assumed
    unconditionally; a governing moment must raise VEd above NSd in normal mode."""
    senza_momento = punzonamento_colonna(1315.66, 0.0, 0.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                          legacy_compat=False)
    con_momento = punzonamento_colonna(1315.66, 241.562, 741.541, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                        legacy_compat=False)
    assert senza_momento.beta == pytest.approx(1.0, rel=1e-9)
    assert con_momento.beta > 1.0
    assert con_momento.ved_kN == pytest.approx(con_momento.beta * 1315.66, rel=1e-9)
    assert con_momento.utilizzo > senza_momento.utilizzo


@pytest.mark.unit
def test_punzonamento_colonna_interasse_insufficiente() -> None:
    result = punzonamento_colonna(1000.0, 0.0, 0.0, 500.0, 400.0, 400.0, 0.5, 0.5, 600.0, 32.0, 1.5,
                                   legacy_compat=True)
    assert result.interasse_x_sufficiente is False
    assert result.interasse_y_sufficiente is False


@pytest.mark.unit
def test_punzonamento_palo_legacy_usa_perimetro_2d_pieno() -> None:
    result = punzonamento_palo(896.06124265, 1102.0, 600.0, 0.0010262916109730722 * 4.0, 1.426014322842305,
                                32.0, 1.5, lx_m=2.0, ly_m=2.0, ax_m=4.0, by_m=4.0, count_x=2, count_y=2,
                                legacy_compat=True)
    assert result.u_mm > 600.0 * 3.14  # perimeter beyond the pile's own diameter circumference.
    assert result.a_mm == pytest.approx(2.0 * 1102.0, rel=1e-9)
    assert result.verificato is True


@pytest.mark.unit
def test_punzonamento_palo_perimetro_ridotto_per_sovrapposizione_in_modalita_normale() -> None:
    """Code-review finding (CRITICAL): the sheet's own example (4 piles at 2m spacing on a 4x4m cap,
    d=1102mm) gives a 2d=2204mm reach, far beyond the ~1000mm-1300mm available before the pile-cone
    overlap / cap edge; the fixed perimeter must be much smaller than the unclamped one."""
    legacy = punzonamento_palo(896.06124265, 1102.0, 600.0, 0.0010262916109730722 * 4.0, 1.426014322842305,
                                32.0, 1.5, lx_m=2.0, ly_m=2.0, ax_m=4.0, by_m=4.0, count_x=2, count_y=2,
                                legacy_compat=True)
    fisso = punzonamento_palo(896.06124265, 1102.0, 600.0, 0.0010262916109730722 * 4.0, 1.426014322842305,
                               32.0, 1.5, lx_m=2.0, ly_m=2.0, ax_m=4.0, by_m=4.0, count_x=2, count_y=2,
                               legacy_compat=False)
    assert fisso.a_mm < legacy.a_mm
    assert fisso.u_mm < legacy.u_mm
    # a = min(2d, lx/2 - r, edge margin - r) = min(2204, 1000-300, 1000-300) = 700 mm.
    assert fisso.a_mm == pytest.approx(700.0, rel=1e-6)


@pytest.mark.unit
def test_punzonamento_palo_geometria_impossibile_solleva_calc_error() -> None:
    with pytest.raises(CalcError):
        punzonamento_palo(896.0, 1102.0, 900.0, 0.001, 1.4, 32.0, 1.5,
                           lx_m=0.95, ly_m=0.95, ax_m=1.0, by_m=1.0, count_x=2, count_y=2, legacy_compat=False)


@pytest.mark.unit
def test_punzonamento_colonna_beta_1_se_nsd_non_positivo() -> None:
    result = punzonamento_colonna(0.0, 500.0, 500.0, 1102.0, 700.0, 700.0, 2.0, 2.0, 600.0, 32.0, 1.5,
                                   legacy_compat=False)
    assert result.beta == pytest.approx(1.0, rel=1e-9)


def test_punzonamento_palo_perimetro_ravvicinato_aumenta_la_resistenza_unitaria() -> None:
    """EC2 §6.4.4(2) eq. 6.50: a control perimeter at a < 2d gets v_Rd,c·(2d/a) ≥ v_Rd,c. The
    code passed a/(2d) — the inverse — which understated V_Rd,c,palo about 10× on the example and
    made pile punching the 'governing' mechanism of the report (proof-read finding)."""
    comune = {"d_mm": 1102.0, "diametro_pila_mm": 600.0, "rho": 0.0010262916109730722 * 4.0, "k": 1.426014322842305,
              "fck_MPa": 32.0, "gamma_c": 1.5, "lx_m": 2.0, "ly_m": 2.0, "ax_m": 4.0, "by_m": 4.0, "count_x": 2, "count_y": 2}
    pieno = punzonamento_palo(896.06124265, **comune, legacy_compat=True)   # a = 2d, no enhancement
    ridotto = punzonamento_palo(896.06124265, **comune, legacy_compat=False)  # a = 700 mm < 2d
    unitario_pieno = pieno.vrd_c_kN / pieno.u_mm
    unitario_ridotto = ridotto.vrd_c_kN / ridotto.u_mm
    assert unitario_ridotto / unitario_pieno == pytest.approx(2.0 * 1102.0 / 700.0, rel=1e-6)
    assert ridotto.utilizzo < 0.5  # no longer the governing mechanism of the example
