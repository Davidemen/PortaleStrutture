"""Vertical stem (paramento) rebar: cantilever bending at the stem base from the combination's
earth+surcharge thrust (muro-sostegno rows 133-151). Pure functions; `tool.py` assembles the
`ArmaturaParamentoCombo`/`ArmaturaParamentoResult` and picks the governing combination via
`rebar_selection`.

The sheet (`legacy_compat=True`) reuses Tool 2's FULL-HEIGHT thrust resultants (computed over
H = hmuro + sfond) with reduced lever arms `leva_sovraccarico_m`/`leva_terreno_m` (H/2 - sfond,
braccio - sfond). That is not the moment of the pressure diagram actually acting on the stem: the
correct value only integrates the pressure over the stem height hs = H - sfond, using the stem's
own natural lever arms (hs/2 for the uniform surcharge block, hs/3 for the triangular earth
wedge) — see `leva_sovraccarico_stelo_m`/`leva_terreno_stelo_m`/`spinte_stelo`, used under
`legacy_compat=False` (NTC2018 §6.5.3.1.1/§4.1.2)."""
import math
from typing import NamedTuple


def leva_sovraccarico_m(*, h_muro_tot_m: float, s_fond_m: float) -> float:
    """zq (col C) = H/2 - sfondazione — braccio di SH.q rispetto alla base del paramento (sheet)."""
    return h_muro_tot_m / 2 - s_fond_m


def leva_terreno_m(*, braccio_terr_m: float, s_fond_m: float) -> float:
    """zterr (col D) = braccio di SH.terr (Tool 2, col K) - sfondazione (sheet)."""
    return braccio_terr_m - s_fond_m


def momento_flettente_kNm(*, sh_q_kN: float, sh_terr_kN: float, zq_m: float, zterr_m: float) -> float:
    """MEd (col G) = SH.q·zq + zterr·SH.terr."""
    return sh_q_kN * zq_m + zterr_m * sh_terr_kN


def leva_sovraccarico_stelo_m(*, hs_m: float) -> float:
    """Fixed behaviour: lever arm of the uniform surcharge pressure block on the stem, hs/2."""
    return hs_m / 2


def leva_terreno_stelo_m(*, hs_m: float) -> float:
    """Fixed behaviour: lever arm of the triangular earth-pressure wedge on the stem, hs/3."""
    return hs_m / 3


class SpinteStelo(NamedTuple):
    sh_q_kN: float
    sh_terr_kN: float


def spinte_stelo(
    *, ka: float, delta_d_rad: float, dq_kN_m2: float, hs_m: float, gamma_g_terr: float, gamma_terr_kN_m3: float, fattore_sismico: float = 1.0
) -> SpinteStelo:
    """Fixed behaviour: horizontal thrust on the STEM only (height hs = H - sfond), not on the full
    H used by Tool 2 — same shape as `ribaltamento_scorrimento.spinte_orizzontali_verticali`'s
    horizontal components, with hs replacing the full wall height."""
    cos_delta = math.cos(delta_d_rad)
    return SpinteStelo(
        sh_q_kN=ka * dq_kN_m2 * hs_m * cos_delta * fattore_sismico,
        sh_terr_kN=0.5 * gamma_g_terr * gamma_terr_kN_m3 * hs_m**2 * ka * cos_delta * fattore_sismico,
    )
