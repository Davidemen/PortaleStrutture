"""Utilisation ratio (`docs/architecture-phase4.md` §A): `rapporto = |M_Ed| / |M_Rd(N_Ed,
direzione)|` along the ray from the origin through `(Mx_Ed, My_Ed)` in the Mx-My plane, at `N =
N_Ed`.

Uniaxial shortcut (`My_Ed = 0` or `Mx_Ed = 0`): `domini.m_rd` already gives the two signed
capacities directly, no direction search needed. Biaxial case: search the neutral-axis angle
`theta` whose resistant moment `(Mx(theta), My(theta))` (`domini.mx_my_a_theta`) points in the
same direction as `(Mx_Ed, My_Ed)` — since the domain is convex and contains the origin, the
mapping `theta -> atan2(My, Mx)` sweeps monotonically once around the circle as `theta` does, so a
coarse angular scan brackets the crossing and `shared.numeric.bisect` refines it.
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


def _rapporto_uniassiale(sezione: Sezione, n_ed_kN: float, asse: Asse, m_ed_kNm: float) -> tuple[float, float]:
    mrd_pos, mrd_neg = m_rd(sezione, n_ed_kN, asse)
    return (m_ed_kNm, mrd_pos) if m_ed_kNm >= 0.0 else (m_ed_kNm, mrd_neg)


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
        m_ed, mrd = _rapporto_uniassiale(sezione, n_ed_kN, "x", mx_ed_kNm)
    elif mx_ed_kNm == 0.0:
        m_ed, mrd = _rapporto_uniassiale(sezione, n_ed_kN, "y", my_ed_kNm)
    else:
        phi_ed = atan2(my_ed_kNm, mx_ed_kNm)
        theta = _cerca_theta_direzione(sezione, n_ed_kN, phi_ed)
        mx, my = mx_my_a_theta(sezione, n_ed_kN, theta)
        m_ed, mrd = hypot(mx_ed_kNm, my_ed_kNm), hypot(mx, my)

    rapporto = abs(m_ed) / abs(mrd) if mrd != 0.0 else float("inf")
    return Verifica(rapporto=rapporto, dentro=rapporto <= 1.0, m_rd_direzione=mrd)
