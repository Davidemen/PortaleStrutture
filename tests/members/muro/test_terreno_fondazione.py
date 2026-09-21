"""Integration tests for the optional 'Terreno di fondazione' block (docs/architecture-phase4.md
§C "Integration", divergence `muro-sostegno/verifica-portanza-non-segnalata`):
- block EMPTY -> exactly today's behaviour (AVVISO_CAPACITA_PORTANTE, no check) in BOTH modes;
- block FILLED + legacy_compat=True -> ignored, with a dedicated warning on top;
- block FILLED + legacy_compat=False -> the check replaces the "non calcolata" warning.
"""
import pytest
from pydantic import ValidationError

from strutture.members.muro.combinazioni import ALL_COMBOS
from strutture.members.muro.models import MuroSostegnoInput
from strutture.members.muro.tool import (
    AVVISO_CAPACITA_PORTANTE,
    AVVISO_CAPACITA_PORTANTE_SISMICA,
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


def test_filled_block_drenata_computes_the_check_in_default_mode():
    inputs = MuroSostegnoInput(**ESEMPIO_TRATTO_A, **TERRENO_DRENATA, legacy_compat=False)
    report = run_muro_sostegno(inputs)
    cp = report.data.capacita_portante_fondazione
    assert cp is not None
    assert tuple(c.nome for c in cp.combinazioni) == ALL_COMBOS
    assert cp.rapporto_governante == max(c.rapporto for c in cp.combinazioni)
    assert cp.combo_governante == max(cp.combinazioni, key=lambda c: c.rapporto).nome
    assert report.warnings == (AVVISO_CAPACITA_PORTANTE_SISMICA,)
    assert AVVISO_CAPACITA_PORTANTE not in report.warnings
    assert cp.verifica in report.checks
    assert cp.verifica.name == "Capacità portante del terreno di fondazione"
    assert cp.verifica.passed == (cp.rapporto_governante <= 1.0)


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
