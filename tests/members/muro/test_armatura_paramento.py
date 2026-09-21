"""Unit tests for `armatura_paramento` (muro-sostegno rows 133-151), Tratto A SISMA_1 values."""
import pytest

from strutture.members.muro import armatura_paramento

pytestmark = pytest.mark.unit


def test_leva_sovraccarico_m():
    assert armatura_paramento.leva_sovraccarico_m(h_muro_tot_m=2.7, s_fond_m=0.3) == pytest.approx(1.05)


def test_leva_terreno_m_static_and_seismic():
    assert armatura_paramento.leva_terreno_m(braccio_terr_m=0.9, s_fond_m=0.3) == pytest.approx(0.6)  # STR_1 (H/3)
    assert armatura_paramento.leva_terreno_m(braccio_terr_m=1.35, s_fond_m=0.3) == pytest.approx(1.05)  # SISMA_1 (H/2)


def test_momento_flettente_kNm_matches_golden_sisma1():
    m_ed = armatura_paramento.momento_flettente_kNm(sh_q_kN=1.4773257803562723, sh_terr_kN=32.74123260714588, zq_m=1.05, zterr_m=1.05)
    assert m_ed == pytest.approx(35.92948630687726, rel=1e-6)
