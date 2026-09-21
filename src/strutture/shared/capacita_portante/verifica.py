"""NTC 2018 §6.4.2.1 bearing-capacity check, approccio 2 (combinazione A1+M1+R3): characteristic
soil parameters (γM = 1.0, i.e. φ'k, c'k, cu,k are used unreduced) and R_d = q_lim·A'/γR with
γR = 2.3 (static). See docs/architecture-phase4.md §C.

The vertical design action N_Ed is the SAME V that enters iq/iγ (EN 1997-1 Annex D.4:
[1 - H/(V + A'·c'·cotφ')]^m) — there is no separate `v_kn`; passing a larger V than N_Ed would
silently inflate iq/iγ (and therefore q_lim/R_d) relative to the load combination actually
checked, so `carico_limite_*` is always called with V = n_ed_kn.

Seismic option (`sismico=True`): NTC 2018 §7.11.5.3.1 requires the seismic bearing-capacity check
to account for inertial forces in the soil below the foundation (Paolucci-Pecker reduction
factors). This is not implemented ("Da confermare" with the engineer), so `sismico=True` raises
`CalcError` instead of silently returning a result computed with the static formula under a
seismic label.
"""
from strutture.shared.report import CalcError

from .carico_limite import carico_limite_drenato, carico_limite_non_drenato
from .models import VerificaCapacitaPortante

GAMMA_R_STATICO_NTC_6_4_2_1 = 2.3  # NTC 2018 §6.4.2.1 Tab. 6.4.I, R3 (capacità portante, fondazioni superficiali)
GAMMA_M_APPROCCIO_2_NTC_6_4_2_1 = 1.0  # NTC 2018 Tab. 6.2.II, M1 (nessuna riduzione dei parametri caratteristici)
CITAZIONE_GAMMA_R = "NTC 2018 §6.4.2.1 Tab. 6.4.I, R3 (capacità portante, fondazioni superficiali)"

_ERRORE_SISMICO_NON_IMPLEMENTATO = (
    "Verifica sismica non implementata: la riduzione inerziale della capacita' portante "
    "(Paolucci-Pecker, NTC 2018 §7.11.5.3.1) e' 'Da confermare' con il progettista; nessun "
    "risultato viene prodotto dalla formula statica sotto etichetta sismica."
)


def verifica_drenata(
    *, n_ed_kn: float, sismico: bool = False,
    b_m: float, l_m: float, eb_m: float = 0.0, el_m: float = 0.0, nastriforme: bool = False,
    phi_k_deg: float, c_k_kpa: float, gamma_kn_m3: float, profondita_piano_posa_m: float,
    profondita_falda_m: float | None = None, h_kn: float = 0.0,
    direzione_h: str = "B", theta_deg: float = 0.0, alpha_base_deg: float = 0.0,
    fattori_profondita: bool = False,
) -> VerificaCapacitaPortante:
    """Bearing-capacity check for a drained soil (γM = 1.0 on φ'k, c'k)."""
    if sismico:
        raise CalcError(_ERRORE_SISMICO_NON_IMPLEMENTATO)
    if n_ed_kn < 0:
        raise ValueError(f"n_ed_kn deve essere >= 0, ricevuto {n_ed_kn}")
    carico_limite = carico_limite_drenato(
        b_m=b_m, l_m=l_m, eb_m=eb_m, el_m=el_m, nastriforme=nastriforme,
        phi_deg=phi_k_deg / GAMMA_M_APPROCCIO_2_NTC_6_4_2_1, c_kpa=c_k_kpa / GAMMA_M_APPROCCIO_2_NTC_6_4_2_1,
        gamma_kn_m3=gamma_kn_m3, profondita_piano_posa_m=profondita_piano_posa_m,
        profondita_falda_m=profondita_falda_m, h_kn=h_kn, v_kn=n_ed_kn, direzione_h=direzione_h,
        theta_deg=theta_deg, alpha_base_deg=alpha_base_deg, fattori_profondita=fattori_profondita,
    )
    return _verifica_da_carico_limite(carico_limite, n_ed_kn)


def verifica_non_drenata(
    *, n_ed_kn: float, sismico: bool = False,
    b_m: float, l_m: float, eb_m: float = 0.0, el_m: float = 0.0, nastriforme: bool = False,
    cu_k_kpa: float, gamma_kn_m3: float, profondita_piano_posa_m: float, h_kn: float = 0.0, alpha_base_deg: float = 0.0,
) -> VerificaCapacitaPortante:
    """Bearing-capacity check for an undrained soil (γM = 1.0 on cu,k)."""
    if sismico:
        raise CalcError(_ERRORE_SISMICO_NON_IMPLEMENTATO)
    if n_ed_kn < 0:
        raise ValueError(f"n_ed_kn deve essere >= 0, ricevuto {n_ed_kn}")
    carico_limite = carico_limite_non_drenato(
        b_m=b_m, l_m=l_m, eb_m=eb_m, el_m=el_m, nastriforme=nastriforme,
        cu_kpa=cu_k_kpa / GAMMA_M_APPROCCIO_2_NTC_6_4_2_1, gamma_kn_m3=gamma_kn_m3,
        profondita_piano_posa_m=profondita_piano_posa_m, h_kn=h_kn, alpha_base_deg=alpha_base_deg,
    )
    return _verifica_da_carico_limite(carico_limite, n_ed_kn)


def _verifica_da_carico_limite(carico_limite, n_ed_kn: float) -> VerificaCapacitaPortante:
    r_d_kn = carico_limite.q_lim_kpa * carico_limite.area_efficace.a_eff_m2 / GAMMA_R_STATICO_NTC_6_4_2_1
    ratio = n_ed_kn / r_d_kn if r_d_kn > 0 else float("inf")
    return VerificaCapacitaPortante(
        carico_limite=carico_limite, r_d_kn=r_d_kn, n_ed_kn=n_ed_kn, ratio=ratio, passed=n_ed_kn <= r_d_kn,
    )
