"""Optional Hansen (1970) depth factors dq, dc (OFF by default — EN 1997-1 Annex D does not
define depth factors at all; this is an advanced, non-Annex-D option exposed with an explicit
warning string, docs/architecture-phase4.md §C). Simplified to the D/B' <= 1 branch of Hansen's
formula only (the common case for shallow footings); dγ = 1 always (Hansen sets dγ = 1)."""
import math

_AVVISO = (
    "Fattori di profondità di Hansen applicati: non previsti da EN 1997-1 Annex D, opzione avanzata "
    "(implementata solo per D/B' <= 1) — usare con cautela."
)


def fattore_profondita_dq(phi_deg: float, profondita_piano_posa_m: float, b_eff_m: float) -> float:
    if phi_deg <= 0.0:
        return 1.0
    phi_rad = math.radians(phi_deg)
    rapporto = min(profondita_piano_posa_m / b_eff_m, 1.0)
    return 1.0 + 2.0 * math.tan(phi_rad) * (1.0 - math.sin(phi_rad)) ** 2 * rapporto


def fattore_profondita_dc(phi_deg: float, profondita_piano_posa_m: float, b_eff_m: float, dq: float, nc: float) -> float:
    rapporto = min(profondita_piano_posa_m / b_eff_m, 1.0)
    if phi_deg <= 0.0:
        return 1.0 + 0.4 * rapporto
    return dq - (1.0 - dq) / (nc * math.tan(math.radians(phi_deg)))


def avviso_fattori_profondita() -> str:
    return _AVVISO
