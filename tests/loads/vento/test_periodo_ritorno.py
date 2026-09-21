import pytest

from strutture.loads.vento.periodo_ritorno import coefficiente_periodo_ritorno, velocita_riferimento


@pytest.mark.unit
def test_coefficiente_periodo_ritorno_tr50_matches_golden():
    assert coefficiente_periodo_ritorno(50) == pytest.approx(1.00073378, rel=1e-6)


# --- legacy_compat=True: must keep reproducing Vento!H15's baked-in /cr(50) renormalisation ---


@pytest.mark.unit
def test_legacy_velocita_riferimento_tr50_e_identita():
    """At TR=50 (the sheet's normalisation baseline) vR(TR) == vref exactly."""
    assert velocita_riferimento(vref=25, tr_anni=50, legacy_compat=True) == pytest.approx(25, rel=1e-9)


@pytest.mark.unit
def test_legacy_velocita_riferimento_tr_maggiore_aumenta_la_velocita():
    assert velocita_riferimento(vref=25, tr_anni=200, legacy_compat=True) > 25


@pytest.mark.unit
def test_legacy_velocita_riferimento_tr_minore_riduce_la_velocita():
    assert velocita_riferimento(vref=25, tr_anni=10, legacy_compat=True) < 25


@pytest.mark.unit
def test_legacy_a_r_e_vr_sono_inconsistenti_bug_noto():
    """Bug storico del foglio (spec §7 / finding): aR (Vento!H14=cr(TR)) e vR (Vento!H15, rinormalizzato
    rispetto a TR=50) non soddisfano aR*vref==vr, tranne esattamente a TR=50."""
    vref, tr = 25.0, 200
    a_r = coefficiente_periodo_ritorno(tr)
    vr = velocita_riferimento(vref, tr, legacy_compat=True)
    assert a_r * vref != pytest.approx(vr, rel=1e-9)


# --- legacy_compat=False: NTC2018 eq. 3.3.2/3.3.3, vr = vref*cr, nessuna rinormalizzazione ---


@pytest.mark.unit
def test_fixed_vr_tr50_hand_computed():
    """A TR=50, cr = 0.75*sqrt(1-0.2*ln(-ln(1-1/50))) = 1.00073378 (non 1, a differenza del foglio)."""
    vr = velocita_riferimento(vref=25, tr_anni=50, legacy_compat=False)
    assert vr == pytest.approx(25 * 1.00073378, rel=1e-6)


@pytest.mark.unit
def test_fixed_a_r_coerente_con_vr_no_renormalizzazione():
    """aR*vref == vr esattamente (nessuna divisione per cr(50), a differenza del foglio)."""
    vref, tr = 25.0, 200
    a_r = coefficiente_periodo_ritorno(tr)
    vr = velocita_riferimento(vref, tr, legacy_compat=False)
    assert a_r * vref == pytest.approx(vr, rel=1e-12)


@pytest.mark.unit
def test_fixed_differisce_dal_legacy_per_la_rinormalizzazione():
    """Il foglio divide per cr(50)=1.00073378: il modo standard non lo fa, quindi vr differisce
    dello 0.073% a parità di TR (divergenza documentata in docs/divergences/vento.md)."""
    vr_fixed = velocita_riferimento(vref=25, tr_anni=200, legacy_compat=False)
    vr_legacy = velocita_riferimento(vref=25, tr_anni=200, legacy_compat=True)
    assert vr_fixed != pytest.approx(vr_legacy, rel=1e-9)
    assert vr_fixed == pytest.approx(vr_legacy * 1.00073378, rel=1e-6)
