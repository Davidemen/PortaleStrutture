"""`capacita_portante_riga` — NTC2018 §6.4.2.1 / EN 1997-1 Annex D bearing-capacity check of one
`reazioni` row (docs/architecture-phase4.md §C)."""
from itertools import pairwise

import pytest

from strutture.foundations.plinti_isolati.capacita_portante_riga import capacita_portante_riga
from strutture.foundations.plinti_isolati.riga_verifica import RigaVerifica
from strutture.shared.report import CalcError


def _riga(**overrides) -> RigaVerifica:
    base = {
        "nodo": 1, "combo": "C1", "famiglia": "SLU_STR",
        "n_kN": 500.0, "vx_kN": 0.0, "vy_kN": 0.0, "myy_kNm": 0.0, "mxx_kNm": 0.0,
        "ex_m": 0.0, "ey_m": 0.0, "sigma_max_kpa": 125.0, "sigma_min_kpa": 125.0,
        "compressed_ratio": 1.0, "mu_ribaltamento_x": None, "mu_ribaltamento_y": None, "mu_scorrimento": None,
    }
    return RigaVerifica(**{**base, **overrides})


@pytest.mark.unit
def test_capacita_portante_riga_calcolo_a_mano() -> None:
    """Carico centrato N_Ed=500 kN, H=0, plinto quadrato B'=L'=2 m, D=1 m, terreno drenato phi'k=30
    deg, c'k=0, gamma=18 kN/m3, senza falda.

    Calcolo a mano (EN 1997-1 Annesso D.1, c'=0 -> il termine di coesione e' nullo):
      Nq = e^(pi*tan(30 deg)) * tan^2(60 deg) = e^1.813799 * 3.0 = 18.401122
      Ngamma = 2*(Nq-1)*tan(30 deg) = 2*17.401122*0.577350 = 20.093085
      sq = 1 + (B'/L')*sin(30 deg) = 1 + 1*0.5 = 1.5   (B'/L'=1, footing quadrato)
      sgamma = 1 - 0.3*(B'/L') = 1 - 0.3 = 0.7
      q' = gamma*D = 18*1 = 18 kPa (nessuna falda)
      qlim = q'*Nq*sq + 0.5*gamma*B'*Ngamma*sgamma
           = 18*18.401122*1.5 + 0.5*18*2*20.093085*0.7
           = 496.830300 + 253.172873 = 750.003173 kPa
      A' = B'*L' = 4 m2
      Rd = qlim*A'/gammaR = 750.003173*4/2.3 = 1304.353345 kN   (gammaR=2.3, NTC2018 6.4.2.1 R3)
      ratio = N_Ed/Rd = 500/1304.353345 = 0.383332
    """
    riga = capacita_portante_riga(
        _riga(n_kN=500.0), ax_m=2.0, by_m=2.0, profondita_piano_posa_m=1.0,
        condizione="drenata", phi_k_deg=30.0, c_k_kpa=0.0, cu_k_kpa=None,
        gamma_kn_m3=18.0, profondita_falda_m=None,
    )
    assert riga.q_lim_kpa == pytest.approx(750.003173, rel=1e-6)
    assert riga.r_d_kn == pytest.approx(1304.353345, rel=1e-6)
    assert riga.n_ed_kn == pytest.approx(500.0)
    assert riga.ratio == pytest.approx(0.383332, rel=1e-5)
    assert riga.b_eff_m == pytest.approx(2.0)
    assert riga.l_eff_m == pytest.approx(2.0)
    assert riga.nodo == 1 and riga.combo == "C1" and riga.famiglia == "SLU_STR"


@pytest.mark.unit
def test_capacita_portante_riga_non_drenata() -> None:
    """cu,k=80 kPa, gamma=19 kN/m3, D=1.2 m, B'=L'=1.5 m, N_Ed=200 kN, H=0: q_lim = (pi+2)*cu*sc + q,
    sc=1+0.2*(B'/L')=1.2 -> q_lim = 5.14159*80*1.2 + 19*1.2 = 493.593 + 22.8 = 516.393 kPa."""
    riga = capacita_portante_riga(
        _riga(n_kN=200.0), ax_m=1.5, by_m=1.5, profondita_piano_posa_m=1.2,
        condizione="non_drenata", phi_k_deg=None, c_k_kpa=None, cu_k_kpa=80.0,
        gamma_kn_m3=19.0, profondita_falda_m=None,
    )
    assert riga.q_lim_kpa == pytest.approx(516.393, rel=1e-3)
    assert riga.r_d_kn == pytest.approx(516.393 * 2.25 / 2.3, rel=1e-3)


@pytest.mark.unit
def test_capacita_portante_riga_monotonia_eccentricita() -> None:
    """Piu' eccentricita' (a parita' di N_Ed, H=0) non deve mai aumentare R_d (area efficace piu'
    piccola)."""
    r_d = [
        capacita_portante_riga(
            _riga(n_kN=300.0, ex_m=ex), ax_m=3.0, by_m=3.0, profondita_piano_posa_m=1.0,
            condizione="drenata", phi_k_deg=28.0, c_k_kpa=5.0, cu_k_kpa=None,
            gamma_kn_m3=18.0, profondita_falda_m=None,
        ).r_d_kn
        for ex in (0.0, 0.2, 0.4, 0.6)
    ]
    assert all(a > b for a, b in pairwise(r_d))


@pytest.mark.unit
def test_capacita_portante_riga_monotonia_inclinazione() -> None:
    """Piu' carico orizzontale H (a parita' di N_Ed, eccentricita' nulla) non deve mai aumentare
    R_d (fattori di inclinazione iq/igamma/ic decrescenti)."""
    r_d = [
        capacita_portante_riga(
            _riga(n_kN=300.0, vx_kN=h), ax_m=3.0, by_m=3.0, profondita_piano_posa_m=1.0,
            condizione="drenata", phi_k_deg=28.0, c_k_kpa=5.0, cu_k_kpa=None,
            gamma_kn_m3=18.0, profondita_falda_m=None,
        ).r_d_kn
        for h in (0.0, 20.0, 60.0, 100.0)
    ]
    assert all(a > b for a, b in pairwise(r_d))


@pytest.mark.unit
def test_capacita_portante_riga_carico_orizzontale_eccessivo_solleva_calc_error() -> None:
    with pytest.raises(CalcError, match="C1"):
        capacita_portante_riga(
            _riga(n_kN=10.0, vx_kN=500.0), ax_m=2.0, by_m=2.0, profondita_piano_posa_m=1.0,
            condizione="drenata", phi_k_deg=30.0, c_k_kpa=0.0, cu_k_kpa=None,
            gamma_kn_m3=18.0, profondita_falda_m=None,
        )


@pytest.mark.unit
def test_capacita_portante_riga_drenata_senza_phi_o_c_solleva_value_error() -> None:
    """Invariante difensiva (già garantita dal model_validator di `PlintoIsolatoInput`)."""
    with pytest.raises(ValueError, match="phi_k_deg e c_k_kpa"):
        capacita_portante_riga(
            _riga(), ax_m=2.0, by_m=2.0, profondita_piano_posa_m=1.0,
            condizione="drenata", phi_k_deg=None, c_k_kpa=None, cu_k_kpa=None,
            gamma_kn_m3=18.0, profondita_falda_m=None,
        )


@pytest.mark.unit
def test_capacita_portante_riga_non_drenata_senza_cu_solleva_value_error() -> None:
    """Invariante difensiva (già garantita dal model_validator di `PlintoIsolatoInput`)."""
    with pytest.raises(ValueError, match="cu_k_kpa"):
        capacita_portante_riga(
            _riga(), ax_m=2.0, by_m=2.0, profondita_piano_posa_m=1.0,
            condizione="non_drenata", phi_k_deg=None, c_k_kpa=None, cu_k_kpa=None,
            gamma_kn_m3=18.0, profondita_falda_m=None,
        )
