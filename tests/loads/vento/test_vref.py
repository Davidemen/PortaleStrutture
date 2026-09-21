import pytest

from strutture.loads.vento.vref import coefficiente_altitudine, velocita_riferimento_suolo
from strutture.shared.report import CalcError

# --- legacy_compat=True: must keep reproducing Vento!H12 (superseded NTC2008 form) exactly ---


@pytest.mark.unit
def test_legacy_altitudine_sotto_soglia_restituisce_vb0():
    vref, ca = velocita_riferimento_suolo(vb0=25, ka=0.01, ks=0.40, a0=1000, altitudine_m=120, legacy_compat=True)
    assert vref == pytest.approx(25)
    assert ca == pytest.approx(1.0)


@pytest.mark.unit
def test_legacy_altitudine_esattamente_a0_restituisce_vb0():
    vref, _ca = velocita_riferimento_suolo(vb0=25, ka=0.01, ks=0.40, a0=1000, altitudine_m=1000, legacy_compat=True)
    assert vref == pytest.approx(25)


@pytest.mark.unit
def test_legacy_altitudine_sopra_soglia_applica_correzione_ka():
    """Forma NTC2008 superata: vb = vb0 + ka*(as-a0), riprodotta solo in legacy_compat=True."""
    vref, _ca = velocita_riferimento_suolo(vb0=25, ka=0.01, ks=0.40, a0=1000, altitudine_m=1200, legacy_compat=True)
    assert vref == pytest.approx(27)


@pytest.mark.unit
def test_legacy_non_solleva_calc_error_oltre_1500m():
    """Il foglio storico non blocca oltre 1500 m (solo avviso, Vento!L8): legacy_compat non deve rompersi."""
    vref, _ca = velocita_riferimento_suolo(vb0=25, ka=0.01, ks=0.40, a0=1000, altitudine_m=2000, legacy_compat=True)
    assert vref == pytest.approx(25 + 0.01 * 1000)


# --- legacy_compat=False: NTC2018 §3.3.2, vb = vb0*ca, Tab. 3.3.I ks ---


@pytest.mark.unit
def test_fixed_altitudine_sotto_soglia_ca_unitario():
    vref, ca = velocita_riferimento_suolo(vb0=25, ka=0.01, ks=0.40, a0=1000, altitudine_m=120, legacy_compat=False)
    assert ca == pytest.approx(1.0)
    assert vref == pytest.approx(25)


@pytest.mark.unit
def test_fixed_altitudine_esattamente_a0_ca_unitario():
    vref, ca = velocita_riferimento_suolo(vb0=25, ka=0.01, ks=0.40, a0=1000, altitudine_m=1000, legacy_compat=False)
    assert ca == pytest.approx(1.0)
    assert vref == pytest.approx(25)


@pytest.mark.unit
def test_fixed_zona4_as1500_hand_computed():
    """Zona 4 (vb0=28, a0=500, ks=0.36), as=1500 m -> vb = 28*(1+0.36*2) = 48.16 m/s (Tab. 3.3.I)."""
    vref, ca = velocita_riferimento_suolo(vb0=28, ka=0.02, ks=0.36, a0=500, altitudine_m=1500, legacy_compat=False)
    assert ca == pytest.approx(1.72, rel=1e-9)
    assert vref == pytest.approx(48.16, rel=1e-9)


@pytest.mark.unit
def test_fixed_zona3_as1500_hand_computed():
    """Zona 3 (vb0=27, a0=500, ks=0.37), as=1500 m -> vb = 27*(1+0.37*2) = 46.98 m/s."""
    vref, ca = velocita_riferimento_suolo(vb0=27, ka=0.02, ks=0.37, a0=500, altitudine_m=1500, legacy_compat=False)
    assert ca == pytest.approx(1.74, rel=1e-9)
    assert vref == pytest.approx(46.98, rel=1e-9)


@pytest.mark.unit
def test_fixed_oltre_1500m_solleva_calc_error_in_italiano():
    with pytest.raises(CalcError, match="1500"):
        velocita_riferimento_suolo(vb0=25, ka=0.01, ks=0.40, a0=1000, altitudine_m=1600, legacy_compat=False)


@pytest.mark.unit
def test_fixed_vref_uguale_vb0_per_ca():
    """Consistenza richiesta: vref == vb0*ca sempre (per costruzione)."""
    vref, ca = velocita_riferimento_suolo(vb0=28, ka=0.02, ks=0.36, a0=500, altitudine_m=900, legacy_compat=False)
    assert vref == pytest.approx(28 * ca, rel=1e-9)


@pytest.mark.unit
def test_coefficiente_altitudine_boundary_esattamente_1500():
    """as == 1500 m è ancora ammesso dalla formula (limite incluso, §3.3.2: 'fino a 1500 m')."""
    ca = coefficiente_altitudine(ks=0.36, a0=500, altitudine_m=1500)
    assert ca == pytest.approx(1.72, rel=1e-9)


@pytest.mark.unit
def test_coefficiente_altitudine_oltre_1500_solleva_calc_error():
    with pytest.raises(CalcError):
        coefficiente_altitudine(ks=0.36, a0=500, altitudine_m=1500.01)
