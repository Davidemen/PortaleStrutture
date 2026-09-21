import pytest
from pydantic import ValidationError

from strutture.loads.sisma.models import (
    SismaFattoriStrutturaInput,
    SismaParametriSitoInput,
    SismaSpettroInput,
    SismaVitaRiferimentoInput,
)


@pytest.mark.unit
def test_vita_riferimento_rejects_non_positive_vn():
    with pytest.raises(ValidationError):
        SismaVitaRiferimentoInput(vn_anni=0, classe_uso="II")


@pytest.mark.unit
def test_vita_riferimento_rejects_unknown_classe():
    with pytest.raises(ValidationError):
        SismaVitaRiferimentoInput(vn_anni=50, classe_uso="V")


@pytest.mark.unit
def test_vita_riferimento_comune_optional():
    inputs = SismaVitaRiferimentoInput(vn_anni=50, classe_uso="II")
    assert inputs.comune is None


@pytest.mark.unit
def test_vita_riferimento_is_frozen():
    inputs = SismaVitaRiferimentoInput(vn_anni=50, classe_uso="II")
    with pytest.raises(ValidationError):
        inputs.vn_anni = 100


@pytest.mark.unit
def test_parametri_sito_rejects_unknown_categoria():
    with pytest.raises(ValidationError):
        SismaParametriSitoInput(categoria_sottosuolo="Z", categoria_topografica="T1", tc_star_s=0.3, f0=2.4, ag_g=0.1)


@pytest.mark.unit
def test_fattori_struttura_rejects_unknown_regolare_altezza():
    with pytest.raises(ValidationError):
        SismaFattoriStrutturaInput(xi_pct=5, q0=1.5, regolare_altezza="FORSE", stato_limite="SLV", qv=1.5)


@pytest.mark.unit
def test_spettro_default_sampling_range():
    inputs = SismaSpettroInput(s=1.2, eta=1, q=1.5, ag_g=0.1, f0=2.4, tb_s=0.1, tc_s=0.3, td_s=2.0, stato_limite="SLV")
    assert inputs.t_start_s == pytest.approx(0.0)
    assert inputs.t_end_s == pytest.approx(4.0)
    assert inputs.step_s == pytest.approx(0.05)
