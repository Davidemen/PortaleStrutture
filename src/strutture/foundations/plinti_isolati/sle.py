"""Step: SLS concrete/steel stress checks (docs/specs/fond-plinti-isolati.md Tool-2 steps 14-16,
`INPUT!X3:X23,AB20:AB23,X26:AA30`). Composes `momento_cantilever` (per SLS family) with
`sezione_parzializzata` (cracked-section stresses); reuses the flexural design's provided steel.

Fix 1 (CRITICAL, review finding sezione_parzializzata.py): the sheet plugs the *gross* plinth
height H as both the effective depth fed to the cracked-section formulas and the lever-arm base,
understating the SLS stresses (quantified in the finding: +16.5% steel stress, +26.6% concrete
stress on a realistic footing). `legacy_compat=False` now uses the effective depth
`d = H - copriferro - MARGIN_EFFECTIVE_DEPTH_MM` (the same margin `flessione._as_required_cm2`
already uses for the ULS steel area); `legacy_compat=True` keeps H (sheet behaviour).

Fix 2 (HIGH, review finding): `max_pressione_kpa(inviluppo, (famiglia,))` used to return `0.0` when
no row of that family is present, silently emitting a vacuous PASS (all 5 checks "passed" at 0.0
without ever having been computed). `_sigma_famiglia_kpa`/`momenti` now return `None` when the
family has no rows, and `sle_checks` emits no `Check` for the affected quantities (`senza_domanda`
convention, matching `ribaltamento`/`scorrimento`).

Fix 3 (HIGH, review finding flessione.py): reuses `flessione._eccentricita_cantilever` so the SLS
cantilever moments pair `ex_m`/`ey_m` with their own axis in the fixed mode, matching the ULS fix."""
from typing import NamedTuple

from strutture.shared.divergences import legacy
from strutture.shared.load_table import Famiglia

from .flessione import MARGIN_EFFECTIVE_DEPTH_MM, _eccentricita_cantilever
from .inviluppo import InviluppoRiga
from .models_flessione import Flessione
from .models_sle import Sle
from .momento_cantilever import momento_cantilever_kNm
from .sezione_parzializzata import profondita_asse_neutro_mm, sigma_acciaio_MPa, sigma_calcestruzzo_MPa
from .sle_checks import sle_checks  # re-exported: `tool.py` imports `sle_checks` from here.

__all__ = ["sle", "sle_checks"]

_FAMIGLIA_QP: Famiglia = "SLE_QP"
_FAMIGLIA_RARA: Famiglia = "SLE_RARA"
_FAMIGLIA_FREQ: Famiglia = "SLE_FREQ"


class _GeometriaSle(NamedTuple):
    """Section geometry feeding the cracked-section stress formulas, both directions."""

    by_mm: float
    ax_mm: float
    xi_x_mm: float
    xi_y_mm: float
    altezza_utile_mm: float
    extra_x_m: float
    extra_y_m: float


def _geometria_sle(flessione: Flessione, ax_m: float, by_m: float, h_plinto_m: float, ex_m: float, ey_m: float, *,
                    copriferro_cm: float, legacy_compat: bool) -> _GeometriaSle:
    h_mm = h_plinto_m * 1000.0
    altezza_utile_mm = (h_mm
                        if legacy("plinti-isolati/sezione-parzializzata-altezza-lorda-non-effettiva", legacy_compat)
                        else h_mm - copriferro_cm * 10.0 - MARGIN_EFFECTIVE_DEPTH_MM)
    by_mm, ax_mm = by_m * 1000.0, ax_m * 1000.0
    extra_x_m, extra_y_m = _eccentricita_cantilever(ex_m, ey_m, legacy_compat=legacy_compat)
    return _GeometriaSle(
        by_mm=by_mm, ax_mm=ax_mm, altezza_utile_mm=altezza_utile_mm, extra_x_m=extra_x_m, extra_y_m=extra_y_m,
        xi_x_mm=profondita_asse_neutro_mm(by_mm, altezza_utile_mm, flessione.as_prov_x_mm2),
        xi_y_mm=profondita_asse_neutro_mm(ax_mm, altezza_utile_mm, flessione.as_prov_y_mm2),
    )


def _momenti_famiglia(
    inviluppo: tuple[InviluppoRiga, ...], famiglia: Famiglia, geo: _GeometriaSle,
    ax_m: float, by_m: float, a_pedestal_m: float, b_pedestal_m: float, *, legacy_compat: bool,
) -> tuple[float, float] | tuple[None, None]:
    sigma_kpa = _sigma_famiglia_kpa(inviluppo, famiglia)
    if sigma_kpa is None:
        return None, None
    mx = momento_cantilever_kNm(sigma_kpa, by_m, ax_m, a_pedestal_m / 2.0, geo.extra_x_m, legacy_compat=legacy_compat)
    my = momento_cantilever_kNm(sigma_kpa, ax_m, by_m, b_pedestal_m / 2.0, geo.extra_y_m, legacy_compat=legacy_compat)
    return mx, my


def _tensioni_famiglia(mx: float | None, my: float | None, flessione: Flessione,
                        geo: _GeometriaSle) -> tuple[float | None, float | None]:
    sigma_c = _max_opt(_sigma_calcestruzzo_opt(mx, geo.by_mm, geo.xi_x_mm, geo.altezza_utile_mm),
                        _sigma_calcestruzzo_opt(my, geo.ax_mm, geo.xi_y_mm, geo.altezza_utile_mm))
    sigma_s = _max_opt(_sigma_acciaio_opt(mx, flessione.as_prov_x_mm2, geo.xi_x_mm, geo.altezza_utile_mm),
                        _sigma_acciaio_opt(my, flessione.as_prov_y_mm2, geo.xi_y_mm, geo.altezza_utile_mm))
    return sigma_c, sigma_s


def sle(
    inviluppo: tuple[InviluppoRiga, ...], flessione: Flessione, ax_m: float, by_m: float, h_plinto_m: float,
    a_pedestal_m: float, b_pedestal_m: float, ex_m: float, ey_m: float, *,
    copriferro_cm: float, legacy_compat: bool,
) -> Sle:
    """SLS concrete/steel stresses under the quasi-permanent/characteristic/frequent envelopes."""
    geo = _geometria_sle(flessione, ax_m, by_m, h_plinto_m, ex_m, ey_m,
                          copriferro_cm=copriferro_cm, legacy_compat=legacy_compat)

    def momenti(famiglia: Famiglia) -> tuple[float, float] | tuple[None, None]:
        return _momenti_famiglia(inviluppo, famiglia, geo, ax_m, by_m, a_pedestal_m, b_pedestal_m,
                                  legacy_compat=legacy_compat)

    sigma_c_qp, sigma_s_qp = _tensioni_famiglia(*momenti(_FAMIGLIA_QP), flessione, geo)
    sigma_c_rara, sigma_s_rara = _tensioni_famiglia(*momenti(_FAMIGLIA_RARA), flessione, geo)
    _, sigma_s_freq = _tensioni_famiglia(*momenti(_FAMIGLIA_FREQ), flessione, geo)

    return Sle(
        sigma_c_qp_MPa=sigma_c_qp, sigma_s_qp_MPa=sigma_s_qp,
        sigma_c_rara_MPa=sigma_c_rara, sigma_s_rara_MPa=sigma_s_rara,
        sigma_s_freq_MPa=sigma_s_freq,
    )


def _sigma_famiglia_kpa(inviluppo: tuple[InviluppoRiga, ...], famiglia: Famiglia) -> float | None:
    """MAX `pressione_max_kpa` for the given `famiglia`, or `None` when it has no envelope row
    (fix: no vacuous `0.0` stand-in, see module docstring)."""
    valori = [r.valore for r in inviluppo if r.grandezza == "pressione_max_kpa" and r.famiglia == famiglia]
    return max(valori) if valori else None


def _sigma_calcestruzzo_opt(m_kNm: float | None, larghezza_mm: float, xi_mm: float, altezza_mm: float) -> float | None:
    return None if m_kNm is None else sigma_calcestruzzo_MPa(m_kNm, larghezza_mm, xi_mm, altezza_mm)


def _sigma_acciaio_opt(m_kNm: float | None, as_prov_mm2: float, xi_mm: float, altezza_mm: float) -> float | None:
    return None if m_kNm is None else sigma_acciaio_MPa(m_kNm, as_prov_mm2, xi_mm, altezza_mm)


def _max_opt(a: float | None, b: float | None) -> float | None:
    valori = [v for v in (a, b) if v is not None]
    return max(valori) if valori else None
