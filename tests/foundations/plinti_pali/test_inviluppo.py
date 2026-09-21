import pytest

from strutture.foundations.plinti_pali.inviluppo import inviluppo, inviluppo_righe
from strutture.foundations.plinti_pali.rows import riga_carico
from strutture.shared.load_table import ReactionRow
from strutture.shared.pile_group import pile_coordinates

PILES = pile_coordinates("2x2", 2.0, 2.0)


def _righe():
    rows = (
        ReactionRow(nodo=1, combo="A", fx_kN=0.0, fy_kN=0.0, fz_kN=800.0, mx_kNm=0.0, my_kNm=0.0, mz_kNm=0.0),
        ReactionRow(nodo=1, combo="B", fx_kN=0.0, fy_kN=0.0, fz_kN=1200.0, mx_kNm=100.0, my_kNm=200.0, mz_kNm=0.0),
    )
    return tuple(riga_carico(r, PILES, 2, 2, 2.0, 2.0, 1.2, 0.0, 0.0, legacy_compat=False) for r in rows)


@pytest.mark.unit
def test_inviluppo_prende_n_totale_dalla_colonna_non_dal_singolo_palo() -> None:
    env = inviluppo(_righe(), peso_proprio_kN=0.0, numero_pali=4, gamma_g1=1.3, legacy_compat=False)
    assert env.n_totale_max.valore == pytest.approx(1200.0, rel=1e-9)
    assert env.n_totale_min.valore == pytest.approx(800.0, rel=1e-9)


@pytest.mark.unit
def test_fix_d4_divisore_peso_favorevole_usa_gamma_g1_reale() -> None:
    """docs/architecture-batch2.md §7 `plinti-pali AF12`: sheet divides by a hardcoded 1.4 regardless
    of the actual gammaG1; the fix divides by the real `gamma_g1` the self-weight was built with."""
    righe = _righe()
    peso_kN, numero_pali, gamma_g1 = 400.0, 4, 1.3
    fisso = inviluppo(righe, peso_kN, numero_pali, gamma_g1, legacy_compat=False)
    legacy = inviluppo(righe, peso_kN, numero_pali, gamma_g1, legacy_compat=True)

    peso_per_palo = peso_kN / numero_pali
    assert fisso.n_min_env_kN == pytest.approx(fisso.n_min.valore + peso_per_palo / gamma_g1 * 0.9, rel=1e-9)
    assert legacy.n_min_env_kN == pytest.approx(legacy.n_min.valore + peso_per_palo / 1.4 * 0.9, rel=1e-9)
    assert fisso.n_min_env_kN != pytest.approx(legacy.n_min_env_kN)
    # Nmax uses the full unfavourable self-weight in both modes (no divergence there).
    assert fisso.n_max_env_kN == pytest.approx(legacy.n_max_env_kN, rel=1e-9)
    assert fisso.n_max_env_kN == pytest.approx(fisso.n_max.valore + peso_per_palo, rel=1e-9)


@pytest.mark.unit
def test_inviluppo_righe_espone_le_8_grandezze() -> None:
    env = inviluppo(_righe(), peso_proprio_kN=100.0, numero_pali=4, gamma_g1=1.3, legacy_compat=False)
    grandezze = {r.grandezza for r in inviluppo_righe(env)}
    assert grandezze == {"n_pila_min", "n_pila_max", "mx_max", "mx_min", "my_max", "my_min", "n_totale_max", "n_totale_min"}


@pytest.mark.unit
def test_inviluppo_rifiuta_tabella_vuota() -> None:
    with pytest.raises(ValueError, match="vuota"):
        inviluppo((), peso_proprio_kN=0.0, numero_pali=4, gamma_g1=1.3, legacy_compat=False)
