"""sezione.py — derived section quantities (column-check!P9, P12, AI9, AI10, AI24, AI28, AV41, Q39-Q41)."""
import pytest

from strutture.members.acciaio_colonna_ec3.sezione import (
    alpha_lt_torsione,
    area_taglio_ali_mm2,
    area_taglio_anima_mm2,
    costante_ingobbamento_mm6,
    momento_plastico_resistente_kNm,
    npl_kN,
    numero_classe,
    raggio_polare_quadro_mm2,
    rapporto_moduli,
    verifica_classe_supportata,
)
from strutture.shared.report import CalcError


@pytest.mark.unit
@pytest.mark.parametrize("testo,atteso", [("class 1", 1), ("class 2", 2), ("class 3", 3), ("class 4", 4)])
def test_numero_classe(testo: str, atteso: int) -> None:
    assert numero_classe(testo) == atteso  # type: ignore[arg-type]


@pytest.mark.unit
def test_area_taglio_anima() -> None:
    assert area_taglio_anima_mm2(500, 12, 8) == pytest.approx(1.2 * (500 - 24) * 8)


@pytest.mark.unit
def test_area_taglio_ali() -> None:
    assert area_taglio_ali_mm2(280, 12) == pytest.approx(2 * 280 * 12)


@pytest.mark.unit
def test_costante_ingobbamento() -> None:
    assert costante_ingobbamento_mm6(4.39243e7, 500, 12) == pytest.approx(4.39243e7 * 488**2 / 4.0)


@pytest.mark.unit
def test_rapporto_moduli_clamped_at_1_5() -> None:
    assert rapporto_moduli(2.09283e6, 1.88825e6) == pytest.approx(2.09283e6 / 1.88825e6)
    assert rapporto_moduli(200, 100) == 1.5  # ratio 2.0 clamped


@pytest.mark.unit
def test_momento_plastico_usa_wpl_per_classe_1_2_e_wel_per_3_4() -> None:
    assert momento_plastico_resistente_kNm(1, 100, 200, 345) == pytest.approx(200 * 345 / 1e6)
    assert momento_plastico_resistente_kNm(3, 100, 200, 345) == pytest.approx(100 * 345 / 1e6)


@pytest.mark.unit
def test_npl() -> None:
    assert npl_kN(10528, 345) == pytest.approx(10528 * 345 / 1000.0)


@pytest.mark.unit
def test_alpha_lt_torsione_clamped_at_zero() -> None:
    assert alpha_lt_torsione(4.05255e5, 4.72063e8) == pytest.approx(1.0 - 4.05255e5 / 4.72063e8)
    assert alpha_lt_torsione(1e9, 1e8) == 0.0  # IT > Iyy -> clamped, not negative


@pytest.mark.unit
def test_raggio_polare_quadro() -> None:
    assert raggio_polare_quadro_mm2(211.752, 62.5921) == pytest.approx(211.752**2 + 62.5921**2)


@pytest.mark.unit
def test_classe_4_accepted_in_legacy_mode() -> None:
    """Legacy mode reproduces the sheet's implicit treatment of class 4 as class 3."""
    verifica_classe_supportata(4, legacy_compat=True)  # does not raise


@pytest.mark.unit
def test_classe_4_rejected_in_fixed_mode() -> None:
    """No EN1993-1-5 §4.4 effective-width calculation exists: fixed mode refuses class 4 rather
    than silently checking against the gross section (non-conservative, unbounded)."""
    with pytest.raises(CalcError):
        verifica_classe_supportata(4, legacy_compat=False)


@pytest.mark.unit
@pytest.mark.parametrize("classe_num", [1, 2, 3])
def test_classe_1_2_3_accepted_in_both_modes(classe_num: int) -> None:
    verifica_classe_supportata(classe_num, legacy_compat=True)
    verifica_classe_supportata(classe_num, legacy_compat=False)
