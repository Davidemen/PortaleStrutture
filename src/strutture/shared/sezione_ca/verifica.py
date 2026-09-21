"""Utilisation ratio (`docs/architecture-phase4.md` §A): `rapporto = |M_Ed| / |M_Rd(N_Ed,
direzione)|` along the ray from the origin through `(Mx_Ed, My_Ed)` in the Mx-My plane, at `N =
N_Ed`.

Uniaxial shortcut (`My_Ed = 0` or `Mx_Ed = 0`): `domini.m_rd` already gives the two signed
capacities directly, no direction search needed. Biaxial case: search the neutral-axis angle
`theta` whose resistant moment `(Mx(theta), My(theta))` (`domini.mx_my_a_theta`) points in the
same direction as `(Mx_Ed, My_Ed)` — since the domain is convex and contains the origin, the
mapping `theta -> atan2(My, Mx)` sweeps monotonically once around the circle as `theta` does, so a
coarse angular scan brackets the crossing and `shared.numeric.bisect` refines it.

"Contains the origin" is NOT guaranteed at every `N`: near an axial extreme, or with asymmetric
reinforcement, the domain's M interval at `N_Ed` can lie entirely on one side of zero (both
`M_Rd+` and `M_Rd-` positive). There the ray from the origin is meaningless — even `M_Ed = 0` is
outside the domain. `rapporto_uniassiale` handles that case explicitly; the biaxial branch refuses
it (never "inside") rather than searching a direction that may not exist.
"""
from math import atan2, hypot, pi

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.numeric import bisect
from strutture.shared.report import CalcError

from .domini import Asse, intervallo_n, m_rd, mx_my_a_theta
from .modelli import Sezione

N_CAMPIONI_DIREZIONE = 24  # campionamento angolare grezzo per individuare l'intervallo di bisezione.
TOLLERANZA_SCANSIONE_T = 1e-4  # tolleranza (larga) su t durante la scansione grezza, per rapidità.


class Verifica(BaseModel):
    """Esito della verifica a pressoflessione (retta o deviata) per `N_Ed, Mx_Ed, My_Ed`."""

    model_config = ConfigDict(frozen=True)

    rapporto: float = Field(description="Tasso di sfruttamento |M_Ed| / |M_Rd|", json_schema_extra={"unit": "-"})
    dentro: bool = Field(description="True se (N_Ed, Mx_Ed, My_Ed) è dentro al dominio di resistenza")
    m_rd_direzione: float = Field(
        description="Momento resistente nella direzione di (Mx_Ed, My_Ed), a N = N_Ed",
        json_schema_extra={"unit": "kNm"},
    )


def _angolo_relativo(angolo: float, riferimento: float) -> float:
    """`angolo - riferimento` normalizzato in `(-pi, pi]` (differenza corretta a cavallo di ±pi)."""
    return (angolo - riferimento + pi) % (2.0 * pi) - pi


def _fase(sezione: Sezione, n_ed_kN: float, theta_rad: float, tolleranza_t: float) -> float:
    mx, my = mx_my_a_theta(sezione, n_ed_kN, theta_rad, tolleranza_t)
    return atan2(my, mx)


def _cerca_theta_direzione(sezione: Sezione, n_ed_kN: float, phi_ed: float) -> float:
    """Angolo `theta` dell'asse neutro il cui momento resistente punta in direzione `phi_ed`."""
    angoli = [2.0 * pi * k / N_CAMPIONI_DIREZIONE for k in range(N_CAMPIONI_DIREZIONE + 1)]
    fasi = [_fase(sezione, n_ed_kN, th, TOLLERANZA_SCANSIONE_T) for th in angoli[:-1]]
    fasi.append(fasi[0])
    for i in range(N_CAMPIONI_DIREZIONE):
        d0, d1 = _angolo_relativo(fasi[i], phi_ed), _angolo_relativo(fasi[i + 1], phi_ed)
        if d0 == 0.0:
            return angoli[i]
        if d0 * d1 < 0.0 and abs(d1 - d0) < pi:
            return bisect(lambda th: _angolo_relativo(_fase(sezione, n_ed_kN, th, TOLLERANZA_SCANSIONE_T), phi_ed), angoli[i], angoli[i + 1])
    raise CalcError("Impossibile individuare la direzione del momento resistente richiesta.")


def rapporto_uniassiale(m_ed_kNm: float, mrd_pos_kNm: float, mrd_neg_kNm: float) -> float:
    """Utilisation of `M_Ed` against the domain's M interval `[M_Rd-, M_Rd+]` at `N = N_Ed`; by
    construction `<= 1` exactly when `M_Rd- <= M_Ed <= M_Rd+`.

    Interval containing zero (the ordinary case): the classic `|M_Ed| / |M_Rd|` with `M_Rd` in the
    sign of `M_Ed` — the ratio along the ray from the origin, the number an engineer expects.
    Interval excluding zero: distance of `M_Ed` from the interval's centre over its half-width (the
    ray from the origin does not cross the domain at all; picking a branch by the sign of `M_Ed`
    and dividing reported points OUTSIDE the domain as verified)."""
    if mrd_neg_kNm <= 0.0 <= mrd_pos_kNm:
        mrd = mrd_pos_kNm if m_ed_kNm >= 0.0 else mrd_neg_kNm
        if mrd == 0.0:
            return 0.0 if m_ed_kNm == 0.0 else float("inf")
        return abs(m_ed_kNm) / abs(mrd)
    centro, semiampiezza = (mrd_pos_kNm + mrd_neg_kNm) / 2.0, (mrd_pos_kNm - mrd_neg_kNm) / 2.0
    if semiampiezza <= 0.0:
        return 0.0 if m_ed_kNm == centro else float("inf")
    return abs(m_ed_kNm - centro) / semiampiezza


def _verifica_uniassiale(sezione: Sezione, n_ed_kN: float, asse: Asse, m_ed_kNm: float) -> Verifica:
    mrd_pos, mrd_neg = m_rd(sezione, n_ed_kN, asse)
    rapporto = rapporto_uniassiale(m_ed_kNm, mrd_pos, mrd_neg)
    return Verifica(rapporto=rapporto, dentro=rapporto <= 1.0, m_rd_direzione=mrd_pos if m_ed_kNm >= 0.0 else mrd_neg)


def _origine_nel_dominio(sezione: Sezione, n_ed_kN: float) -> bool:
    """Necessary condition for the ray-from-the-origin search: M = 0 inside both uniaxial intervals."""
    return all(neg <= 0.0 <= pos for pos, neg in (m_rd(sezione, n_ed_kN, "x"), m_rd(sezione, n_ed_kN, "y")))


def verifica(sezione: Sezione, n_ed_kN: float, mx_ed_kNm: float, my_ed_kNm: float) -> Verifica:
    """Rapporto `|M_Ed| / |M_Rd|` a `N = N_Ed`, nella direzione di `(Mx_Ed, My_Ed)`.

    Se `N_Ed` è fuori da `[N_min, N_max]` (il ramo M-N del dominio non è definito lì: la
    combinazione eccede la sola capacità assiale della sezione, non un errore di calcolo) la
    verifica torna semplicemente `dentro=False, rapporto=inf` invece di sollevare — necessario per
    processare una tabella di più righe (Fase 4 parte B) senza abortire sull'intera tabella per
    una singola riga fuori range; `CalcError` resta per le sezioni davvero degeneri (proiezioni
    su `theta_rad` non individuabili, vedi `_cerca_theta_direzione`)."""
    n_min, n_max = intervallo_n(sezione)
    if not n_min <= n_ed_kN <= n_max:
        return Verifica(rapporto=float("inf"), dentro=False, m_rd_direzione=0.0)
    if my_ed_kNm == 0.0:
        return _verifica_uniassiale(sezione, n_ed_kN, "x", mx_ed_kNm)
    if mx_ed_kNm == 0.0:
        return _verifica_uniassiale(sezione, n_ed_kN, "y", my_ed_kNm)
    if not _origine_nel_dominio(sezione, n_ed_kN):
        # conservative: a point may still be inside, but no ray from the origin can prove it
        return Verifica(rapporto=float("inf"), dentro=False, m_rd_direzione=0.0)
    phi_ed = atan2(my_ed_kNm, mx_ed_kNm)
    theta = _cerca_theta_direzione(sezione, n_ed_kN, phi_ed)
    mx, my = mx_my_a_theta(sezione, n_ed_kN, theta)
    mrd = hypot(mx, my)
    rapporto = hypot(mx_ed_kNm, my_ed_kNm) / mrd if mrd != 0.0 else float("inf")
    return Verifica(rapporto=rapporto, dentro=rapporto <= 1.0, m_rd_direzione=mrd)
