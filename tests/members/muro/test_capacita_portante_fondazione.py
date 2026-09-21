"""Unit tests for the optional bearing-capacity check on the wall's strip footing
(docs/architecture-phase4.md §C "Integration"): `capacita_portante_combo` reuses
`strutture.shared.capacita_portante` with `nastriforme=True` (B'=B-2e, per metro di sviluppo)."""
import pytest

from strutture.members.muro.capacita_portante_fondazione import capacita_portante_combo

pytestmark = pytest.mark.unit

# Base drained case: phi'k=30 deg, c'k=5 kPa, gamma=18 kN/m3, B=2.0 m, D=1.0 m (no falda),
# centred (e=0) and vertical-only load (H=0), gammaR=1.4 (static, NTC2018 Tab. 6.5.I R3).
_BASE = {
    "condizione": "drenata",
    "b_fond_m": 2.0,
    "n_ed_kn": 400.0,
    "h_kn": 0.0,
    "profondita_posa_m": 1.0,
    "gamma_kn_m3": 18.0,
    "profondita_falda_m": None,
    "phi_k_deg": 30.0,
    "c_k_kpa": 5.0,
    "cu_k_kpa": None,
    "gamma_r": 1.4,
}


def test_hand_computed_centred_vertical_strip_case():
    """EN1997-1 Annex D.1, centred vertical load (H=0 -> all shape/inclination/base factors = 1,
    strip footing -> B'=B=2.0 m, fattori di forma = 1):

        Nq = e^(pi*tan(30°))·tan²(45°+15°) = e^1.8137996...·3 = 18.401122...
        Nc = (Nq-1)·cot(30°) = 17.401122·1.7320508 = 30.139628...
        Nγ = 2·(Nq-1)·tan(30°) = 2·17.401122·0.5773503 = 20.093085...
        q' = γ·D = 18·1.0 = 18 kPa (no falda)
        q_lim = c'·Nc + q'·Nq + 0.5·γ·B·Nγ
              = 5·30.139628 + 18·18.401122 + 0.5·18·2.0·20.093085
              = 150.698 + 331.220 + 361.675 = 843.594 kPa
        R_d = q_lim·B'/γR = 843.594·2.0/1.4 = 1205.134 kN (per metro)
        rapporto = N_Ed/R_d = 400/1205.134 = 0.3319
    """
    r = capacita_portante_combo("STR_1", eccentricita_m=0.0, **_BASE)
    assert r.q_lim_kPa == pytest.approx(843.594, rel=1e-5)
    assert r.r_d_kN == pytest.approx(1205.134, rel=1e-5)
    assert r.rapporto == pytest.approx(0.33191, rel=1e-4)


def test_hand_computed_seismic_gamma_r_is_smaller_so_rd_is_larger():
    """Same q_lim/B' as the static case; γR=1.2 (sismico) vs 1.4 (statico) -> R_d larger."""
    statico = capacita_portante_combo("STR_1", eccentricita_m=0.0, **_BASE)
    sismico = capacita_portante_combo("SISMA_1", eccentricita_m=0.0, **{**_BASE, "gamma_r": 1.2})
    assert sismico.q_lim_kPa == pytest.approx(statico.q_lim_kPa)
    assert sismico.r_d_kN > statico.r_d_kN
    assert sismico.r_d_kN == pytest.approx(statico.q_lim_kPa * 2.0 / 1.2, rel=1e-6)


@pytest.mark.parametrize("eccentricita_m", [0.2, 0.4, 0.6])
def test_monotonic_in_eccentricity(eccentricita_m):
    """More eccentricity -> smaller B' -> smaller q_lim (gamma term) and smaller area -> R_d never
    increases and the utilisation ratio never decreases (EN1997-1 Annex D.1 B'=B-2e)."""
    centrato = capacita_portante_combo("STR_1", eccentricita_m=0.0, **_BASE)
    eccentrico = capacita_portante_combo("STR_1", eccentricita_m=eccentricita_m, **_BASE)
    assert eccentrico.r_d_kN < centrato.r_d_kN
    assert eccentrico.rapporto > centrato.rapporto


@pytest.mark.parametrize("h_kn", [50.0, 100.0, 150.0])
def test_monotonic_in_load_inclination(h_kn):
    """More horizontal load H (at fixed V) -> smaller iq/iγ/ic (EN1997-1 Annex D.2) -> smaller
    q_lim/R_d and a larger utilisation ratio."""
    verticale = capacita_portante_combo("STR_1", eccentricita_m=0.0, **_BASE)
    inclinato = capacita_portante_combo("STR_1", eccentricita_m=0.0, **{**_BASE, "h_kn": h_kn})
    assert inclinato.r_d_kN < verticale.r_d_kN
    assert inclinato.rapporto > verticale.rapporto


def test_non_drenata_branch_uses_cu():
    r = capacita_portante_combo(
        "SISMA_1", condizione="non_drenata", b_fond_m=2.0, eccentricita_m=0.0, n_ed_kn=300.0, h_kn=20.0,
        profondita_posa_m=1.0, gamma_kn_m3=18.0, profondita_falda_m=None, phi_k_deg=None, c_k_kpa=None,
        cu_k_kpa=40.0, gamma_r=1.2,
    )
    assert r.q_lim_kPa == pytest.approx(209.887, rel=1e-5)
    assert r.r_d_kN == pytest.approx(349.811, rel=1e-5)
    assert r.rapporto == pytest.approx(0.85760, rel=1e-4)
