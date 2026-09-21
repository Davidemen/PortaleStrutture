"""Bearing-capacity check of the wall's strip footing, docs/architecture-phase4.md §C
"Integration": reuses `strutture.shared.capacita_portante` on the base nastriforme (per metro di
sviluppo, L'->infinito, fattori di forma=1) with B'=B-2e from the combination's
`pressioni_terreno.eccentricita_m`. `n_ed_kn`/`h_kn` are the NORMAL/TANGENTIAL components of the
`ribaltamento_scorrimento` N_tot/R_tot resultants relative to the (possibly inclined) footing
base — `tool.py`'s `_capacita_portante_riga` decomposes them with
`ribaltamento_scorrimento.forze_normale_tangente_base` before calling this function (EN1997-1
Annex D.2 note 2: H/V are relative to the base, not the global vertical/horizontal); there is no
separate demand beyond that, same convention as `capacita_portante.verifica`.

γM = 1.0 (NTC2018 Tab. 6.2.II M1, approccio 2): the characteristic φ'k/c'k/cu,k passed in are used
unreduced as design values, so this calls `carico_limite_drenato`/`carico_limite_non_drenato`
directly rather than `capacita_portante.verifica_drenata`/`verifica_non_drenata` (which hard-code
γR=2.3 for ordinary/isolated footings, NTC2018 Tab. 6.4.I — not the muri di sostegno Tab. 6.5.I
value this module's caller applies, see `tool.py`)."""
from strutture.shared.capacita_portante import Condizione, carico_limite_drenato, carico_limite_non_drenato

from .models import CapacitaPortanteCombo, NomeCombo


def capacita_portante_combo(
    nome: NomeCombo,
    *,
    condizione: Condizione,
    b_fond_m: float,
    eccentricita_m: float,
    n_ed_kn: float,
    h_kn: float,
    profondita_posa_m: float,
    gamma_kn_m3: float,
    profondita_falda_m: float | None,
    phi_k_deg: float | None,
    c_k_kpa: float | None,
    cu_k_kpa: float | None,
    gamma_r: float,
    alpha_base_deg: float = 0.0,
) -> CapacitaPortanteCombo:
    """q_lim/R_d/rapporto for one combination. `l_m` is passed as `b_fond_m` but unused
    (`nastriforme=True` -> `area_efficace_nastriforme` ignores it, L' -> infinity).

    `alpha_base_deg` (the wall's `omega_deg`, base inclination) drives the Annex D.4 bq/bgamma/bc
    base-inclination factors, already implemented in `shared.capacita_portante.fattori_base`: a
    HIGH finding was this parameter never being forwarded (bq=bgamma=bc=1 always, non-conservative
    for the muri di sostegno the base inclination input already exists for)."""
    if condizione == "drenata":
        carico_limite = carico_limite_drenato(
            b_m=b_fond_m, l_m=b_fond_m, eb_m=eccentricita_m, nastriforme=True,
            phi_deg=phi_k_deg, c_kpa=c_k_kpa, gamma_kn_m3=gamma_kn_m3,
            profondita_piano_posa_m=profondita_posa_m, profondita_falda_m=profondita_falda_m,
            h_kn=h_kn, v_kn=n_ed_kn, alpha_base_deg=alpha_base_deg,
        )
    else:
        carico_limite = carico_limite_non_drenato(
            b_m=b_fond_m, l_m=b_fond_m, eb_m=eccentricita_m, nastriforme=True,
            cu_kpa=cu_k_kpa, gamma_kn_m3=gamma_kn_m3, profondita_piano_posa_m=profondita_posa_m, h_kn=h_kn,
            alpha_base_deg=alpha_base_deg,
        )
    r_d_kn = carico_limite.q_lim_kpa * carico_limite.area_efficace.a_eff_m2 / gamma_r
    rapporto = n_ed_kn / r_d_kn if r_d_kn > 0 else float("inf")
    return CapacitaPortanteCombo(nome=nome, q_lim_kPa=carico_limite.q_lim_kpa, r_d_kN=r_d_kn, rapporto=rapporto)
