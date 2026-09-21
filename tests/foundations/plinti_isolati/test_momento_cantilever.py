import pytest

from strutture.foundations.plinti_isolati.momento_cantilever import momento_cantilever_kNm


@pytest.mark.golden
def test_momento_cantilever_golden_qp() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: Mx,QP = My,QP = 1045.43 kNm (sigma=1.30679 kg/cm2)."""
    m = momento_cantilever_kNm(130.679, 4.0, 4.0, 0.0, 0.0, legacy_compat=True)
    assert m == pytest.approx(1045.43, rel=1e-4)


@pytest.mark.golden
def test_momento_cantilever_golden_slu() -> None:
    """docs/specs/fond-plinti-isolati.md golden case: Mx,SLU = My,SLU = 1533.25 kNm (sigma=1.91656 kg/cm2)."""
    m = momento_cantilever_kNm(191.656, 4.0, 4.0, 0.0, 0.0, legacy_compat=True)
    assert m == pytest.approx(1533.25, rel=1e-4)


@pytest.mark.unit
def test_momento_cantilever_fix_dal_filo_pilastro() -> None:
    """Fix: non-legacy measures the cantilever from the column/pedestal face, so a wider pedestal
    reduces M; legacy always measures from the centre (unaffected by the pedestal)."""
    senza_pedestal = momento_cantilever_kNm(100.0, 4.0, 4.0, 0.0, 0.0, legacy_compat=False)
    con_pedestal = momento_cantilever_kNm(100.0, 4.0, 4.0, 0.5, 0.0, legacy_compat=False)
    assert con_pedestal < senza_pedestal

    legacy_senza = momento_cantilever_kNm(100.0, 4.0, 4.0, 0.0, 0.0, legacy_compat=True)
    legacy_con = momento_cantilever_kNm(100.0, 4.0, 4.0, 0.5, 0.0, legacy_compat=True)
    assert legacy_senza == pytest.approx(legacy_con)


@pytest.mark.unit
def test_momento_cantilever_pedestal_oltre_meta_luce_azzera() -> None:
    m = momento_cantilever_kNm(100.0, 4.0, 4.0, 3.0, 0.0, legacy_compat=False)
    assert m == 0.0
