"""Integration tests for the optional 'Terreno di fondazione' block (docs/architecture-phase4.md
§C "Integration", divergence `muro-sostegno/verifica-portanza-non-segnalata`):
- block EMPTY -> exactly today's behaviour (AVVISO_CAPACITA_PORTANTE, no check) in BOTH modes;
- block FILLED + legacy_compat=True -> ignored, with a dedicated warning on top;
- block FILLED + legacy_compat=False -> the check replaces the "non calcolata" warning.
"""
import math

import pytest
from pydantic import ValidationError

from strutture.members.muro.models import MuroSostegnoInput
from strutture.members.muro.ribaltamento_scorrimento import forze_normale_tangente_base
from strutture.members.muro.tool import (
    AVVISO_CAPACITA_PORTANTE,
    AVVISO_CAPACITA_PORTANTE_SISMICA,
    AVVISO_ECCENTRICITA_LIMITE,
    AVVISO_TERRENO_IGNORATO_LEGACY,
    ESEMPIO_TRATTO_A,
    run_muro_sostegno,
)

pytestmark = pytest.mark.unit

TERRENO_DRENATA = {
    "terreno_condizione": "drenata",
    "terreno_phi_k_deg": 28.0,
    "terreno_c_k_kpa": 5.0,
    "terreno_gamma_kn_m3": 18.0,
    "terreno_profondita_posa_m": 0.3,
}
TERRENO_NON_DRENATA = {
    "terreno_condizione": "non_drenata",
    "terreno_cu_k_kpa": 60.0,
    "terreno_gamma_kn_m3": 18.0,
    "terreno_profondita_posa_m": 0.3,
}


def _nome_check(report):
    return {c.name for c in report.checks}


@pytest.mark.parametrize("legacy_compat", [False, True])
def test_empty_block_is_todays_behaviour_in_both_modes(legacy_compat):
    inputs = MuroSostegnoInput(**ESEMPIO_TRATTO_A, legacy_compat=legacy_compat)
    report = run_muro_sostegno(inputs)
    assert report.data.capacita_portante_fondazione is None
    assert report.warnings == (AVVISO_CAPACITA_PORTANTE,)
    assert "Capacità portante del terreno di fondazione" not in _nome_check(report)


def test_legacy_compat_ignores_a_filled_block():
    inputs = MuroSostegnoInput(**ESEMPIO_TRATTO_A, **TERRENO_DRENATA, legacy_compat=True)
    report = run_muro_sostegno(inputs)
    assert report.data.capacita_portante_fondazione is None
    assert report.warnings == (AVVISO_CAPACITA_PORTANTE, AVVISO_TERRENO_IGNORATO_LEGACY)
    assert "Capacità portante del terreno di fondazione" not in _nome_check(report)


COMBO_CAPACITA_PORTANTE_ATTESE = ("STR_1", "STR_2", "SISMA_1", "SISMA_2")


def test_filled_block_drenata_computes_the_check_in_default_mode():
    inputs = MuroSostegnoInput(**ESEMPIO_TRATTO_A, **TERRENO_DRENATA, legacy_compat=False)
    report = run_muro_sostegno(inputs)
    cp = report.data.capacita_portante_fondazione
    assert cp is not None
    # HIGH finding: GEO_1/GEO_2 (A2+M2) ed EQU_1/EQU_2 (approccio EQU) non condividono il gamma_R
    # statico=1.4 (Tab. 6.5.I R3, Approccio 2 A1+M1+R3) di STR_1/STR_2 ne' i parametri geotecnici
    # M1 usati qui per il terreno di fondazione: restano solo le righe coerenti con quello schema
    # (A1+M1) e le sismiche (gamma_R dedicato 1.2).
    assert tuple(c.nome for c in cp.combinazioni) == COMBO_CAPACITA_PORTANTE_ATTESE
    assert cp.rapporto_governante == max(c.rapporto for c in cp.combinazioni)
    assert cp.combo_governante == max(cp.combinazioni, key=lambda c: c.rapporto).nome
    # MEDIUM finding: il blocco compilato calcola la portanza ma NON introduce alcun limite su e/B
    # (ne' e<=B/6 ne' il limite di 1/3 di EN1997-1 §6.5.4): l'avviso sull'eccentricita' deve restare.
    assert report.warnings == (AVVISO_ECCENTRICITA_LIMITE, AVVISO_CAPACITA_PORTANTE_SISMICA)
    assert AVVISO_CAPACITA_PORTANTE not in report.warnings
    assert cp.verifica in report.checks
    assert cp.verifica.name == "Capacità portante del terreno di fondazione"
    assert cp.verifica.passed == (cp.rapporto_governante <= 1.0)


def test_omega_deg_changes_the_check_outcome():
    """HIGH: `omega_deg` (inclinazione della base) era gia' un input, gia' usato dalla verifica a
    scorrimento, ma non arrivava alla capacita' portante (bq=bgamma=bc=1 sempre, H/V mai scomposti
    sulla base inclinata): con omega_deg!=0 il grado di sfruttamento governante deve cambiare
    (prima restava identico, indipendentemente da omega_deg)."""
    orizzontale = MuroSostegnoInput(**ESEMPIO_TRATTO_A, **TERRENO_DRENATA, legacy_compat=False)
    inclinato = MuroSostegnoInput(**{**ESEMPIO_TRATTO_A, "omega_deg": 10.0}, **TERRENO_DRENATA, legacy_compat=False)
    rapporto_orizzontale = run_muro_sostegno(orizzontale).data.capacita_portante_fondazione.rapporto_governante
    rapporto_inclinato = run_muro_sostegno(inclinato).data.capacita_portante_fondazione.rapporto_governante
    assert rapporto_inclinato != pytest.approx(rapporto_orizzontale)


def test_omega_deg_is_decomposed_onto_the_inclined_base():
    """Cross-check di cablaggio: N_ed usato dalla capacita' portante per ciascuna combinazione deve
    essere la componente NORMALE di Ntot/Rtot sulla base inclinata di omega_deg
    (`forze_normale_tangente_base`, la stessa geometria gia' collaudata da
    `fattore_sicurezza_scorrimento`), non Ntot globale."""
    inputs = MuroSostegnoInput(**{**ESEMPIO_TRATTO_A, "omega_deg": 10.0}, **TERRENO_DRENATA, legacy_compat=False)
    data = run_muro_sostegno(inputs).data
    rs_per_nome = {r.nome: r for r in data.ribaltamento_scorrimento}
    omega_rad = math.radians(inputs.omega_deg)
    for combo in data.capacita_portante_fondazione.combinazioni:
        rs = rs_per_nome[combo.nome]
        normale_atteso, _ = forze_normale_tangente_base(n_tot_kN=rs.n_tot_kN, r_tot_kN=rs.r_tot_kN, omega_rad=omega_rad)
        rapporto_atteso = normale_atteso / combo.r_d_kN if combo.r_d_kN > 0 else float("inf")
        assert combo.rapporto == pytest.approx(rapporto_atteso, rel=1e-6)


def test_filled_block_non_drenata_also_computes_the_check():
    inputs = MuroSostegnoInput(**ESEMPIO_TRATTO_A, **TERRENO_NON_DRENATA, legacy_compat=False)
    report = run_muro_sostegno(inputs)
    cp = report.data.capacita_portante_fondazione
    assert cp is not None
    assert all(c.q_lim_kPa > 0 for c in cp.combinazioni)


def test_seismic_combos_use_a_smaller_gamma_r_than_static_combos():
    """NTC2018 Tab. 6.5.I: γR=1.2 sismico vs 1.4 statico. R_d = q_lim·B'/γR is re-derived here from
    q_lim/B' (B'=B-2e, geometria.b_fond_m + pressioni_terreno.eccentricita_m of the SAME
    combination) to recover the γR each combo actually used, independently of tool.py's constants."""
    inputs = MuroSostegnoInput(**ESEMPIO_TRATTO_A, **TERRENO_DRENATA, legacy_compat=False)
    data = run_muro_sostegno(inputs).data
    pressioni_per_nome = {p.nome: p for p in data.pressioni_terreno}
    for combo in data.capacita_portante_fondazione.combinazioni:
        b_eff_m = data.geometria.b_fond_m - 2 * abs(pressioni_per_nome[combo.nome].eccentricita_m)
        gamma_r_ricavato = combo.q_lim_kPa * b_eff_m / combo.r_d_kN
        gamma_r_atteso = 1.2 if combo.nome.startswith("SISMA") else 1.4
        assert gamma_r_ricavato == pytest.approx(gamma_r_atteso, rel=1e-6)


@pytest.mark.parametrize("terreno", [
    {"terreno_condizione": "drenata"},
    {"terreno_condizione": "drenata", "terreno_phi_k_deg": 28.0},
    {"terreno_condizione": "non_drenata"},
])
def test_incomplete_terreno_block_is_rejected(terreno):
    with pytest.raises(ValidationError):
        MuroSostegnoInput(**ESEMPIO_TRATTO_A, **terreno)


def test_terreno_block_filled_in_reverse_without_condizione_is_rejected():
    """HIGH: se l'utente valorizza i campi del blocco (phi'k/c'k/gamma/D) senza selezionare
    `terreno_condizione`, il blocco non deve essere saltato in silenzio (prima:
    `capacita_portante_fondazione=None` con il solo avviso generico 'non e' calcolata da questo
    strumento', l'utente crede di aver attivato la verifica e non la ottiene)."""
    with pytest.raises(ValidationError, match="terreno_condizione"):
        MuroSostegnoInput(
            **ESEMPIO_TRATTO_A, terreno_phi_k_deg=28.0, terreno_c_k_kpa=5.0,
            terreno_gamma_kn_m3=18.0, terreno_profondita_posa_m=0.3,
        )


def test_profondita_posa_implausibile_rispetto_al_muro_emette_avviso():
    """HIGH: `terreno_profondita_posa_m` (D) non e' incrociata con la geometria del muro. Un valore
    che supera l'altezza fuori terra del muro (qui h_muro_m=2.4, D=2.7=h_muro+s_fond) e' quasi
    certamente la quota del piano campagna a MONTE, non a valle (dove D va misurato): senza un
    avviso il calcolo procede silenziosamente con un risultato non cautelativo."""
    inputs = MuroSostegnoInput(
        **{**ESEMPIO_TRATTO_A, **TERRENO_DRENATA, "terreno_profondita_posa_m": 2.7}, legacy_compat=False,
    )
    report = run_muro_sostegno(inputs)
    assert any("valle" in w.lower() and "profondità di posa" in w.lower() for w in report.warnings)


def test_profondita_posa_plausibile_non_emette_avviso():
    inputs = MuroSostegnoInput(**ESEMPIO_TRATTO_A, **TERRENO_DRENATA, legacy_compat=False)
    report = run_muro_sostegno(inputs)
    assert not any("profondità di posa" in w.lower() for w in report.warnings)
