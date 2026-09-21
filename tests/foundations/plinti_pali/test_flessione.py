import pytest

from strutture.foundations.plinti_pali.flessione import flessione
from strutture.foundations.plinti_pali.inviluppo import inviluppo
from strutture.foundations.plinti_pali.rows import riga_carico
from strutture.shared.load_table import ReactionRow
from strutture.shared.pile_group import pile_coordinates


def _righe_e_inviluppo(schema: str, count_x: int, count_y: int, lx_m: float, ly_m: float):
    piles = pile_coordinates(schema, lx_m, ly_m)
    rows = (
        ReactionRow(nodo=1, combo="A", fx_kN=0.0, fy_kN=0.0, fz_kN=500.0, mx_kNm=50.0, my_kNm=80.0, mz_kNm=0.0),
        ReactionRow(nodo=1, combo="B", fx_kN=0.0, fy_kN=0.0, fz_kN=1000.0, mx_kNm=10.0, my_kNm=20.0, mz_kNm=0.0),
    )
    righe = tuple(riga_carico(r, piles, count_x, count_y, lx_m, ly_m, 1.0, 0.0, 0.0, legacy_compat=False) for r in rows)
    env = inviluppo(righe, peso_proprio_kN=0.0, numero_pali=count_x * count_y, gamma_g1=1.3, legacy_compat=False)
    return righe, env


@pytest.mark.unit
def test_flessione_direzione_a_pilastro_singolo_usa_solo_il_momento() -> None:
    """`count_x=1` (schema "1x2"): X-X has no beam action, Mu is the extreme moment alone, per
    `_mu_beam`'s `n_own == 1` branch (docs/specs/fond-plinti-pali.md Tool-2 "Case3")."""
    righe, env = _righe_e_inviluppo("1x2", 1, 2, 0.0, 2.0)
    result = flessione(righe, env, 1, 2, 0.0, 2.0, 1.0, 0.0, 50.0, 24.0, 24.0, 100.0, 100.0,
                        20.0, 20.0, 200.0, 200.0, 391.3, 32.0, 1.5, legacy_compat=False)
    my_max = max(abs(r.my_finale_kNm) for r in righe)
    assert result.inf_x.mu_kNm == pytest.approx(my_max, rel=1e-9)


@pytest.mark.unit
def test_flessione_top_usa_letterale_3_14_solo_in_legacy() -> None:
    """docs/architecture-batch2.md §7 `plinti-pali AV51/AZ51`: legacy uses 3.14, fixed uses PI()."""
    righe, env = _righe_e_inviluppo("2x2", 2, 2, 2.0, 2.0)
    fisso = flessione(righe, env, 2, 2, 2.0, 2.0, 1.0, 0.0, 50.0, 24.0, 24.0, 100.0, 100.0,
                       20.0, 20.0, 200.0, 200.0, 391.3, 32.0, 1.5, legacy_compat=False)
    legacy = flessione(righe, env, 2, 2, 2.0, 2.0, 1.0, 0.0, 50.0, 24.0, 24.0, 100.0, 100.0,
                        20.0, 20.0, 200.0, 200.0, 391.3, 32.0, 1.5, legacy_compat=True)
    assert fisso.sup_x.as_prov_mm2 != pytest.approx(legacy.sup_x.as_prov_mm2)
    n_barre = fisso.sup_x.n_barre_per_m
    assert legacy.sup_x.as_prov_mm2 == pytest.approx(n_barre * 3.14 / 4.0 * 20.0**2, rel=1e-9)
    import math
    assert fisso.sup_x.as_prov_mm2 == pytest.approx(n_barre * math.pi / 4.0 * 20.0**2, rel=1e-9)


@pytest.mark.unit
def test_flessione_armatura_minima_governa_quando_il_momento_e_piccolo() -> None:
    righe, env = _righe_e_inviluppo("2x2", 2, 2, 2.0, 2.0)
    result = flessione(righe, env, 2, 2, 2.0, 2.0, 1.0, 0.0, 50.0, 24.0, 24.0, 100.0, 100.0,
                        20.0, 20.0, 200.0, 200.0, 391.3, 32.0, 1.5, legacy_compat=False)
    assert result.sup_x.as_req_mm2 == pytest.approx(result.sup_x.as_min_mm2, rel=1e-6)


@pytest.mark.unit
def test_altezza_utile_non_positiva_solleva_calc_error() -> None:
    """Code-review finding (HIGH): reachable from valid, in-bounds `PlintoSuPaliInput` fields;
    must raise `CalcError` (caught by `shared.tool.execute`), not a bare `ValueError`."""
    from strutture.shared.report import CalcError

    righe, env = _righe_e_inviluppo("2x2", 2, 2, 2.0, 2.0)
    with pytest.raises(CalcError):
        flessione(righe, env, 2, 2, 2.0, 2.0, 0.1, 0.0, 300.0, 24.0, 24.0, 100.0, 100.0,
                  20.0, 20.0, 200.0, 200.0, 391.3, 32.0, 1.5, legacy_compat=False)


@pytest.mark.unit
def test_fix_braccio_di_leva_z_riduce_d_in_modalita_normale() -> None:
    """Code-review finding (CRITICAL): the sheet uses z=d (no lever-arm reduction), understating
    As,req by ~10%; the fix solves z = d*(0.5+sqrt(0.25-mu)) < d, so As,req is larger in normal mode
    for the same governing moment (only `legacy_compat=False` changes; legacy is untouched)."""
    righe, env = _righe_e_inviluppo("2x2", 2, 2, 2.0, 2.0)
    fisso = flessione(righe, env, 2, 2, 2.0, 2.0, 1.0, 0.0, 50.0, 24.0, 24.0, 100.0, 100.0,
                       20.0, 20.0, 200.0, 200.0, 391.3, 32.0, 1.5, legacy_compat=False)
    legacy = flessione(righe, env, 2, 2, 2.0, 2.0, 1.0, 0.0, 50.0, 24.0, 24.0, 100.0, 100.0,
                        20.0, 20.0, 200.0, 200.0, 391.3, 32.0, 1.5, legacy_compat=True)
    assert fisso.inf_x.mu_kNm == pytest.approx(legacy.inf_x.mu_kNm, rel=1e-9)  # same governing moment.
    assert fisso.inf_x.as_req_flexural_mm2 > legacy.inf_x.as_req_flexural_mm2
