"""Overturning (ribaltamento) & sliding (scorrimento) checks, NTC2018 §6.5.3.1.2 / EC7 §6.5.3-6.5.4
(muro-sostegno rows 54-61 static, 85-88 seismic). Pure functions; `tool.py` assembles the
`RibaltamentoScorrimentoCombo` result and the pass/fail `Check`s."""
import math
from typing import NamedTuple

from strutture.shared.divergences import legacy

# NTC2018 Tab. 6.5.I γR for the "ribaltamento" verification row — the table only ships
# "capacita_portante"/"scorrimento"/"resistenza_terreno_a_valle" in `shared.ntc_combos`
# (a shared module outside this package's edit scope), so it is named here instead of imported.
GAMMA_R_RIBALTAMENTO_R3 = 1.15  # Approccio 2 (A1+M1+R3), NTC2018 §6.5.3.1.1
GAMMA_R_SISMA = 1.0  # NTC2018 §7.11.6.2.1 — γR = 1 per scorrimento/ribaltamento nelle combinazioni sismiche


def soglia_verifica(*, sismica: bool, legacy_compat: bool, gamma_r_statico: float) -> float:
    """Pass/fail threshold on OR/OS: 1 for the sheet (`legacy_compat=True`, no γR at all), γR=1 for
    seismic rows, `gamma_r_statico` (the Tab. 6.5.I R3 column) for static rows."""
    if legacy("muro-sostegno/coefficienti-resistenza-mancanti", legacy_compat):
        return 1.0
    return GAMMA_R_SISMA if sismica else gamma_r_statico


class SpinteOrizzontaliVerticali(NamedTuple):
    sh_q_kN: float
    sh_terr_kN: float
    sv_q_kN: float
    sv_terr_kN: float


def spinte_orizzontali_verticali(
    *, ka: float, delta_d_rad: float, dq_kN_m2: float, h_tot_m: float, gamma_g_terr: float, gamma_terr_kN_m3: float, fattore_sismico: float = 1.0
) -> SpinteOrizzontaliVerticali:
    """SH.q/SH.terr/SV.q/SV.terr (cols E-H). `fattore_sismico` = (1+kv)·γE for seismic rows, 1 for static."""
    spinta_terr_kN = 0.5 * gamma_g_terr * gamma_terr_kN_m3 * h_tot_m**2 * ka
    return SpinteOrizzontaliVerticali(
        sh_q_kN=ka * dq_kN_m2 * h_tot_m * math.cos(delta_d_rad) * fattore_sismico,
        sh_terr_kN=spinta_terr_kN * math.cos(delta_d_rad) * fattore_sismico,
        sv_q_kN=ka * dq_kN_m2 * h_tot_m * math.sin(delta_d_rad) * fattore_sismico,
        sv_terr_kN=spinta_terr_kN * math.sin(delta_d_rad) * fattore_sismico,
    )


def momento_ribaltante(*, sh_q_kN: float, sh_terr_kN: float, h_tot_m: float, braccio_terr_m: float, m_fh_kNm: float = 0.0) -> float:
    """MRIB (col M) = SH.q·H/2 + SH.terr·braccio (H/3 statico, H/2 sismico) + Mfh (inerzia sismica del
    muro/terreno, EN1998-5 §7.3.2.2(2)P; 0 per le combinazioni statiche e per `legacy_compat=True`)."""
    return sh_q_kN * h_tot_m / 2 + sh_terr_kN * braccio_terr_m + m_fh_kNm


def momento_stabilizzante(*, sv_q_kN: float, sv_terr_kN: float, x_sv_m: float, m_terr_kNm: float, m_muro_kNm: float) -> float:
    """MSTAB (col N) = MV,q + Mterr + Mmuro."""
    return (sv_q_kN + sv_terr_kN) * x_sv_m + m_terr_kNm + m_muro_kNm


def risultante_verticale(*, w_muro_kN: float, w_terr_kN: float, sv_q_kN: float, sv_terr_kN: float) -> float:
    """Ntot (col Q) = Wmuro + Wterr + SV.q + SV.terr."""
    return w_muro_kN + w_terr_kN + sv_q_kN + sv_terr_kN


def risultante_orizzontale(*, sh_q_kN: float, sh_terr_kN: float, fh_kN: float = 0.0) -> float:
    """Rtot (col R) = SH.q + SH.terr + Fh (inerzia sismica del muro/terreno, EN1998-5 §7.3.2.2(2)P;
    0 per le combinazioni statiche e per `legacy_compat=True`)."""
    return sh_q_kN + sh_terr_kN + fh_kN


def fattore_sicurezza_ribaltamento(*, m_stab_kNm: float, m_rib_kNm: float) -> float:
    """OR (col O) = MSTAB/MRIB, verifica NTC2018 §6.5.3.1.2 se OR ≥ 1."""
    return m_stab_kNm / m_rib_kNm


def forze_normale_tangente_base(*, n_tot_kN: float, r_tot_kN: float, omega_rad: float) -> tuple[float, float]:
    """Scompone la risultante (Ntot verticale, Rtot orizzontale) sulla base di fondazione inclinata
    di `omega_rad` rispetto all'orizzontale: componente normale alla base (compressione, l'N usato
    da EN1997-1 Annesso D quando la base e' inclinata, Annex D.2 nota 2: H/V vanno presi relativi
    alla base) e componente tangenziale alla base (taglio, la stessa che governa lo scorrimento).
    Stessa geometria gia' usata da `fattore_sicurezza_scorrimento`; estratta qui perche' anche la
    verifica di capacita' portante ne ha bisogno (docs/architecture-phase4.md §C, HIGH finding: H
    e V non venivano prima scomposti sulla base inclinata)."""
    normale_kN = n_tot_kN * math.cos(omega_rad) + r_tot_kN * math.sin(omega_rad)
    tangente_kN = -n_tot_kN * math.sin(omega_rad) + r_tot_kN * math.cos(omega_rad)
    return normale_kN, tangente_kN


def fattore_sicurezza_scorrimento(*, phi_d_rad: float, n_tot_kN: float, r_tot_kN: float, omega_rad: float) -> float:
    """OS (col S) = tanφd·(Ntot·cosω+Rtot·sinω) / (-Ntot·sinω+Rtot·cosω), verifica se OS ≥ 1."""
    normale_kN, tangente_kN = forze_normale_tangente_base(n_tot_kN=n_tot_kN, r_tot_kN=r_tot_kN, omega_rad=omega_rad)
    return math.tan(phi_d_rad) * normale_kN / tangente_kN
