"""M-N / Mx-My interaction domains and M_Rd solving (`docs/architecture-phase4.md` §A): sweep the
pivot strain planes of `stati_ultimi.py` to build closed interaction curves, and bisect on the
pivot parameter `t` to solve for the resistant moment at a given `N_Ed`.

Sign convention (see `integrazione.py`): `N > 0` compression, `M > 0` tension at the bottom fibre.
`dominio_nm` reports `N` and the moment component of `asse` (`Mx` for `"x"`, `My` for `"y"`);
`dominio_biassiale` reports the full `(Mx, My)` pair at constant `N`.

`dominio_nm` traces a closed curve by sweeping `t: 0 -> 1` (tension -> compression) at the
neutral-axis angle for `asse`, then `t: 1 -> 0` at the OPPOSITE angle (`theta + pi`): both ends of
each branch are the angle-independent uniform pure-tension/pure-compression states (see
`stati_ultimi.py`), so the two branches stitch into one closed loop without an explicit duplicate
point, and the curve's `N` range is `[-fyd*As, fcd*Ac + fyd*As]` at both ends by construction.
"""
from math import pi
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.numeric import bisect
from strutture.shared.report import CalcError

from .modelli import Sezione
from .stati_ultimi import risultante_pivot

Asse = Literal["x", "y"]

TOLLERANZA_T = 1e-6  # tolleranza (relativa su t in [0, 1]) per la bisezione N(t) = N_Ed.


class PuntoDominio(BaseModel):
    """Un punto del dominio N-M uniassiale (`N > 0` compressione)."""

    model_config = ConfigDict(frozen=True)

    n_kN: float = Field(description="Sforzo normale resistente", json_schema_extra={"unit": "kN"})
    m_kNm: float = Field(description="Momento resistente", json_schema_extra={"unit": "kNm"})


class PuntoBiassiale(BaseModel):
    """Un punto del dominio Mx-My a `N` costante."""

    model_config = ConfigDict(frozen=True)

    mx_kNm: float = Field(description="Momento resistente attorno a x", json_schema_extra={"unit": "kNm"})
    my_kNm: float = Field(description="Momento resistente attorno a y", json_schema_extra={"unit": "kNm"})


def _theta_asse(asse: Asse) -> float:
    return 0.0 if asse == "x" else pi / 2.0


def _momento(asse: Asse, mx_kNm: float, my_kNm: float) -> float:
    return mx_kNm if asse == "x" else my_kNm


def dominio_nm(sezione: Sezione, asse: Asse, n_punti: int = 72) -> tuple[PuntoDominio, ...]:
    """Dominio N-M chiuso attorno all'asse `asse` (`n_punti` punti, default 72), N > 0 compressione."""
    theta = _theta_asse(asse)
    meta = max(n_punti // 2, 2)
    punti: list[PuntoDominio] = []
    for angolo, indici in ((theta, range(meta)), (theta + pi, range(meta - 1, -1, -1))):
        for i in indici:
            r = risultante_pivot(sezione, angolo, i / (meta - 1))
            punti.append(PuntoDominio(n_kN=r.n_kN, m_kNm=_momento(asse, r.mx_kNm, r.my_kNm)))
    return tuple(punti)


def _n_di_t(sezione: Sezione, theta_rad: float, t: float) -> float:
    return risultante_pivot(sezione, theta_rad, t).n_kN


def intervallo_n(sezione: Sezione) -> tuple[float, float]:
    """`(N_min, N_max)` del dominio di resistenza (`-fyd*As`, `fcd*Ac+fyd*As`): gli estremi sono
    stati angolo-indipendenti (vedi `stati_ultimi.py`), quindi `theta_rad=0.0` basta."""
    return _n_di_t(sezione, 0.0, 0.0), _n_di_t(sezione, 0.0, 1.0)


def _bisezione_t(sezione: Sezione, theta_rad: float, n_ed_kN: float, tolleranza_t: float = TOLLERANZA_T) -> float:
    """`t` tale che `N(t) = n_ed_kN` lungo `theta_rad`; `CalcError` se `n_ed_kN` è fuori dal
    dominio di resistenza (i cui estremi non dipendono da `theta_rad`, vedi `stati_ultimi.py`)."""
    n_min, n_max = _n_di_t(sezione, theta_rad, 0.0), _n_di_t(sezione, theta_rad, 1.0)
    if not n_min <= n_ed_kN <= n_max:
        raise CalcError(
            f"N_Ed = {n_ed_kN:.1f} kN è fuori dal dominio di resistenza "
            f"[{n_min:.1f}, {n_max:.1f}] kN della sezione.",
        )
    return bisect(lambda t: _n_di_t(sezione, theta_rad, t) - n_ed_kN, 0.0, 1.0, tol=tolleranza_t)


def mx_my_a_theta(
    sezione: Sezione, n_ed_kN: float, theta_rad: float, tolleranza_t: float = TOLLERANZA_T,
) -> tuple[float, float]:
    """`(Mx, My)` resistenti per `N = n_ed_kN` con asse neutro all'angolo `theta_rad`."""
    t = _bisezione_t(sezione, theta_rad, n_ed_kN, tolleranza_t)
    r = risultante_pivot(sezione, theta_rad, t)
    return r.mx_kNm, r.my_kNm


def m_rd(sezione: Sezione, n_ed_kN: float, asse: Asse) -> tuple[float, float]:
    """`(M_Rd+, M_Rd-)` per flessione uniassiale attorno a `asse`, a `N = n_ed_kN` costante."""
    theta = _theta_asse(asse)
    mrd_pos = _momento(asse, *mx_my_a_theta(sezione, n_ed_kN, theta))
    mrd_neg = _momento(asse, *mx_my_a_theta(sezione, n_ed_kN, theta + pi))
    return mrd_pos, mrd_neg


def dominio_biassiale(sezione: Sezione, n_ed_kN: float, n_angoli: int = 36) -> tuple[PuntoBiassiale, ...]:
    """Dominio Mx-My chiuso a `N = n_ed_kN` costante, `n_angoli` angoli d'asse neutro su `[0, 2*pi)`."""
    punti: list[PuntoBiassiale] = []
    for k in range(n_angoli):
        mx, my = mx_my_a_theta(sezione, n_ed_kN, 2.0 * pi * k / n_angoli)
        punti.append(PuntoBiassiale(mx_kNm=mx, my_kNm=my))
    return tuple(punti)
