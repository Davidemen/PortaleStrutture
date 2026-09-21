import pytest

from strutture.members.ca_travi.fessurazione import classe_normativa, diametro_massimo_mm, verifica_fessurazione
from strutture.shared.report import CalcError


@pytest.mark.unit
def test_diametro_massimo_takes_the_larger_bar():
    assert diametro_massimo_mm(20.0, 0.0) == 20.0
    assert diametro_massimo_mm(16.0, 20.0) == 20.0


@pytest.mark.unit
def test_classe_normativa_matches_tab_4_1_iv():
    assert classe_normativa("Ordinarie", "Frequente", "Poco sensibile") == "w3"
    assert classe_normativa("Ordinarie", "Quasi permanente", "Sensibile") == "w1"


@pytest.mark.unit
def test_classe_normativa_none_when_decompression_check_applies():
    # NTC2018 Tab.4.1.IV leaves this cell blank: decompression check required, not a crack-width limit.
    assert classe_normativa("Aggressive", "Quasi permanente", "Sensibile") is None


@pytest.mark.unit
def test_verifica_fessurazione_matches_golden_case():
    out = verifica_fessurazione(
        sigma_s_MPa=528.576, diametro_ferri1_mm=20.0, diametro_ferri2_mm=0.0,
        condizioni_ambientali="Ordinarie", combinazione="Frequente", sensibilita_armatura="Poco sensibile",
        classe_apertura_fessura="w3", legacy_compat=True,
    )
    assert out.diametro_max_mm == 20.0
    assert out.sigma_limite_MPa == pytest.approx(240.0)
    assert out.classe_normativa == "w3"


@pytest.mark.unit
def test_verifica_fessurazione_legacy_raises_on_non_catalog_diameter():
    """Bug §7.4: exact-match VLOOKUP -> #N/A for a diameter not in Tab. C4.1.II for that w-class
    (25mm is not tabulated for w3, only for w1/w2). legacy_compat=True reproduces the failure as
    a CalcError instead of silently guessing."""
    with pytest.raises(CalcError):
        verifica_fessurazione(
            sigma_s_MPa=200.0, diametro_ferri1_mm=25.0, diametro_ferri2_mm=0.0,
            condizioni_ambientali="Ordinarie", combinazione="Frequente", sensibilita_armatura="Poco sensibile",
            classe_apertura_fessura="w3", legacy_compat=True,
        )


@pytest.mark.unit
def test_verifica_fessurazione_fixed_interpolates_non_catalog_diameter():
    """legacy_compat=False interpolates instead of raising (fix for bug §7.4)."""
    out = verifica_fessurazione(
        sigma_s_MPa=200.0, diametro_ferri1_mm=25.0, diametro_ferri2_mm=0.0,
        condizioni_ambientali="Ordinarie", combinazione="Frequente", sensibilita_armatura="Poco sensibile",
        classe_apertura_fessura="w3", legacy_compat=False,
    )
    # w3 table brackets 25mm between (24.0, 226.66) and (26.0, 219.999): interpolated, strictly between.
    assert 219.999 < out.sigma_limite_MPa < 226.66
