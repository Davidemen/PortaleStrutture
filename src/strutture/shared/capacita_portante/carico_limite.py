"""Ultimate bearing pressure q_lim (EN 1997-1 Annex D), drained (D.1) and undrained (D.3), with
water table (`_falda.py`) and optional Hansen depth factors (`_fattori_profondita_hansen.py`, off
by default). See docs/architecture-phase4.md §C.

    drained:   q_lim = c'·Nc·bc·sc·ic + q'·Nq·bq·sq·iq + 0.5·γ'·B'·Nγ·bγ·sγ·iγ
    undrained: q_lim = (π+2)·cu·bc·sc·ic + q
"""
import math

from strutture.shared.report import CalcError

from ._falda import gamma_efficace_kn_m3, sovraccarico_efficace_kpa
from ._fattori_profondita_hansen import avviso_fattori_profondita, fattore_profondita_dc, fattore_profondita_dq
from .area_efficace import area_efficace, area_efficace_nastriforme
from .fattori_base import fattori_inclinazione_base, fattori_inclinazione_base_non_drenata
from .fattori_forma import fattori_forma, fattori_forma_non_drenata
from .fattori_inclinazione import esponente_m, fattori_inclinazione_carico, fattori_inclinazione_carico_non_drenata
from .fattori_portanza import fattori_portanza
from .models import CaricoLimiteResult, Direzione, FattoriForma, FattoriInclinazioneCarico

_PI_PLUS_2 = math.pi + 2.0  # EN 1997-1 Annex D.3


def _direzione_effettiva(direzione_h: Direzione, theta_deg: float, scambiato: bool) -> tuple[Direzione, float]:
    """Map `direzione_h`/`theta_deg` (relative to the PHYSICAL B/L axes) to the direzione/theta
    that `esponente_m` expects for `area.b_eff_m`/`area.l_eff_m`, which `area_efficace` may have
    swapped to keep b_eff_m<=l_eff_m (EN 1997-1 Annex D.1). Without this, an eccentricity large
    enough to flip the axes would silently compute m for the wrong direction (CRITICAL finding)."""
    if not scambiato:
        return direzione_h, theta_deg
    if direzione_h == "B":
        return "L", theta_deg
    if direzione_h == "L":
        return "B", theta_deg
    return "theta", 90.0 - theta_deg


def carico_limite_drenato(
    *, b_m: float, l_m: float, eb_m: float = 0.0, el_m: float = 0.0, nastriforme: bool = False,
    phi_deg: float, c_kpa: float, gamma_kn_m3: float, profondita_piano_posa_m: float,
    profondita_falda_m: float | None = None, h_kn: float = 0.0, v_kn: float,
    direzione_h: Direzione = "B", theta_deg: float = 0.0, alpha_base_deg: float = 0.0,
    fattori_profondita: bool = False,
) -> CaricoLimiteResult:
    """Drained q_lim. Raises CalcError for invalid geometry/eccentricities, ValueError for
    phi_deg <= 0 or negative depths/weights, CalcError if H exceeds the available friction+adhesion."""
    if phi_deg <= 0.0:
        raise CalcError("La formula drenata richiede phi' > 0: per phi'=0 usare carico_limite_non_drenato.")
    if gamma_kn_m3 <= 0 or profondita_piano_posa_m < 0:
        raise ValueError(f"gamma_kn_m3 deve essere > 0 e profondita_piano_posa_m >= 0, ricevuti {gamma_kn_m3}, {profondita_piano_posa_m}")
    area = area_efficace_nastriforme(b_m, eb_m) if nastriforme else area_efficace(b_m, l_m, eb_m, el_m)
    portanza = fattori_portanza(phi_deg)
    forma = fattori_forma(area.b_eff_m, area.l_eff_m, phi_deg, portanza.nq, nastriforme=area.nastriforme)
    direzione_eff, theta_eff = _direzione_effettiva(direzione_h, theta_deg, area.scambiato)
    m = esponente_m(area.b_eff_m, area.l_eff_m, direzione=direzione_eff, theta_deg=theta_eff)
    inclinazione_carico = fattori_inclinazione_carico(h_kn, v_kn, area.a_eff_m2, c_kpa, phi_deg, portanza.nc, m)
    inclinazione_base = fattori_inclinazione_base(alpha_base_deg, phi_deg, portanza.nc)
    q_eff = sovraccarico_efficace_kpa(gamma_kn_m3, profondita_piano_posa_m, profondita_falda_m)
    gamma_eff = gamma_efficace_kn_m3(gamma_kn_m3, profondita_piano_posa_m, area.b_eff_m, profondita_falda_m)
    q_lim, avviso = _q_lim_drenato(
        c_kpa, q_eff, gamma_eff, area.b_eff_m, portanza, forma, inclinazione_carico, inclinazione_base,
        phi_deg, profondita_piano_posa_m, fattori_profondita,
    )
    return CaricoLimiteResult(
        condizione="drenata", q_lim_kpa=q_lim, area_efficace=area, fattori_portanza=portanza,
        fattori_forma=forma, fattori_inclinazione_carico=inclinazione_carico,
        fattori_inclinazione_base=inclinazione_base, q_eff_kpa=q_eff, gamma_eff_kn_m3=gamma_eff,
        avviso_fattori_profondita=avviso,
    )


def _q_lim_drenato(c_kpa, q_eff, gamma_eff, b_eff_m, portanza, forma, ic_carico, ic_base, phi_deg, profondita_m, con_fattori_profondita):
    dq = dc = 1.0
    avviso = None
    if con_fattori_profondita:
        dq = fattore_profondita_dq(phi_deg, profondita_m, b_eff_m)
        dc = fattore_profondita_dc(phi_deg, profondita_m, b_eff_m, dq, portanza.nc)
        avviso = avviso_fattori_profondita()
    termine_c = c_kpa * portanza.nc * ic_base.bc * forma.sc * ic_carico.ic * dc
    termine_q = q_eff * portanza.nq * ic_base.bq * forma.sq * ic_carico.iq * dq
    termine_gamma = 0.5 * gamma_eff * b_eff_m * portanza.ngamma * ic_base.bgamma * forma.sgamma * ic_carico.igamma
    return termine_c + termine_q + termine_gamma, avviso


def carico_limite_non_drenato(
    *, b_m: float, l_m: float, eb_m: float = 0.0, el_m: float = 0.0, nastriforme: bool = False,
    cu_kpa: float, gamma_kn_m3: float, profondita_piano_posa_m: float, h_kn: float = 0.0, alpha_base_deg: float = 0.0,
) -> CaricoLimiteResult:
    """Undrained q_lim = (π+2)·cu·bc·sc·ic + q (q = total overburden, no buoyancy split)."""
    if cu_kpa <= 0:
        raise CalcError(f"cu deve essere positivo, ricevuto {cu_kpa} kPa.")
    if gamma_kn_m3 <= 0 or profondita_piano_posa_m < 0:
        raise ValueError(f"gamma_kn_m3 deve essere > 0 e profondita_piano_posa_m >= 0, ricevuti {gamma_kn_m3}, {profondita_piano_posa_m}")
    area = area_efficace_nastriforme(b_m, eb_m) if nastriforme else area_efficace(b_m, l_m, eb_m, el_m)
    sc = fattori_forma_non_drenata(area.b_eff_m, area.l_eff_m, nastriforme=area.nastriforme)
    ic = fattori_inclinazione_carico_non_drenata(h_kn, area.a_eff_m2, cu_kpa)
    base = fattori_inclinazione_base_non_drenata(alpha_base_deg)
    q_kpa = gamma_kn_m3 * profondita_piano_posa_m
    q_lim = _PI_PLUS_2 * cu_kpa * base.bc * sc * ic + q_kpa
    return CaricoLimiteResult(
        condizione="non_drenata", q_lim_kpa=q_lim, area_efficace=area, fattori_portanza=None,
        fattori_forma=FattoriForma(sq=1.0, sgamma=1.0, sc=sc),
        fattori_inclinazione_carico=FattoriInclinazioneCarico(m=1.0, iq=1.0, igamma=1.0, ic=ic),
        fattori_inclinazione_base=base, q_eff_kpa=q_kpa, gamma_eff_kn_m3=None, avviso_fattori_profondita=None,
    )
