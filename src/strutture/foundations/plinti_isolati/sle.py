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
from strutture.shared.divergences import legacy
from strutture.shared.load_table import Famiglia
from strutture.shared.report import Check

from .flessione import MARGIN_EFFECTIVE_DEPTH_MM, _eccentricita_cantilever
from .inviluppo import InviluppoRiga
from .models_flessione import Flessione
from .models_sle import Sle
from .momento_cantilever import momento_cantilever_kNm
from .sezione_parzializzata import profondita_asse_neutro_mm, sigma_acciaio_MPa, sigma_calcestruzzo_MPa

SIGMA_C_QP_COEFFICIENT = 0.45  # EC2 §7.2(3) - limite tensione calcestruzzo, combinazione quasi permanente.
SIGMA_S_QP_LIMIT_MPA = 220.0  # EC2 §7.3.4, controllo fessurazione semplificato.
SIGMA_C_RARA_COEFFICIENT = 0.6  # EC2 §7.2(5) - limite tensione calcestruzzo, combinazione caratteristica.
SIGMA_S_RARA_COEFFICIENT = 0.8  # EC2 §7.2, limite tensione armatura, combinazione caratteristica.
SIGMA_S_FREQ_LIMIT_MPA = 240.0  # EC2 §7.3.4, controllo fessurazione semplificato.

_FAMIGLIA_QP: Famiglia = "SLE_QP"
_FAMIGLIA_RARA: Famiglia = "SLE_RARA"
_FAMIGLIA_FREQ: Famiglia = "SLE_FREQ"


def sle(
    inviluppo: tuple[InviluppoRiga, ...], flessione: Flessione, ax_m: float, by_m: float, h_plinto_m: float,
    a_pedestal_m: float, b_pedestal_m: float, ex_m: float, ey_m: float, *,
    copriferro_cm: float, legacy_compat: bool,
) -> Sle:
    """SLS concrete/steel stresses under the quasi-permanent/characteristic/frequent envelopes."""
    h_mm = h_plinto_m * 1000.0
    altezza_utile_mm = (h_mm
                        if legacy("plinti-isolati/sezione-parzializzata-altezza-lorda-non-effettiva", legacy_compat)
                        else h_mm - copriferro_cm * 10.0 - MARGIN_EFFECTIVE_DEPTH_MM)
    by_mm, ax_mm = by_m * 1000.0, ax_m * 1000.0
    xi_x_mm = profondita_asse_neutro_mm(by_mm, altezza_utile_mm, flessione.as_prov_x_mm2)
    xi_y_mm = profondita_asse_neutro_mm(ax_mm, altezza_utile_mm, flessione.as_prov_y_mm2)
    extra_x_m, extra_y_m = _eccentricita_cantilever(ex_m, ey_m, legacy_compat=legacy_compat)

    def momenti(famiglia: Famiglia) -> tuple[float, float] | tuple[None, None]:
        sigma_kpa = _sigma_famiglia_kpa(inviluppo, famiglia)
        if sigma_kpa is None:
            return None, None
        mx = momento_cantilever_kNm(sigma_kpa, by_m, ax_m, a_pedestal_m / 2.0, extra_x_m, legacy_compat=legacy_compat)
        my = momento_cantilever_kNm(sigma_kpa, ax_m, by_m, b_pedestal_m / 2.0, extra_y_m, legacy_compat=legacy_compat)
        return mx, my

    mx_qp, my_qp = momenti(_FAMIGLIA_QP)
    mx_rara, my_rara = momenti(_FAMIGLIA_RARA)
    mx_freq, my_freq = momenti(_FAMIGLIA_FREQ)

    sigma_c_x_qp = _sigma_calcestruzzo_opt(mx_qp, by_mm, xi_x_mm, altezza_utile_mm)
    sigma_c_y_qp = _sigma_calcestruzzo_opt(my_qp, ax_mm, xi_y_mm, altezza_utile_mm)
    sigma_s_x_qp = _sigma_acciaio_opt(mx_qp, flessione.as_prov_x_mm2, xi_x_mm, altezza_utile_mm)
    sigma_s_y_qp = _sigma_acciaio_opt(my_qp, flessione.as_prov_y_mm2, xi_y_mm, altezza_utile_mm)

    sigma_c_x_rara = _sigma_calcestruzzo_opt(mx_rara, by_mm, xi_x_mm, altezza_utile_mm)
    sigma_c_y_rara = _sigma_calcestruzzo_opt(my_rara, ax_mm, xi_y_mm, altezza_utile_mm)
    sigma_s_x_rara = _sigma_acciaio_opt(mx_rara, flessione.as_prov_x_mm2, xi_x_mm, altezza_utile_mm)
    sigma_s_y_rara = _sigma_acciaio_opt(my_rara, flessione.as_prov_y_mm2, xi_y_mm, altezza_utile_mm)

    sigma_s_x_freq = _sigma_acciaio_opt(mx_freq, flessione.as_prov_x_mm2, xi_x_mm, altezza_utile_mm)
    sigma_s_y_freq = _sigma_acciaio_opt(my_freq, flessione.as_prov_y_mm2, xi_y_mm, altezza_utile_mm)

    return Sle(
        sigma_c_qp_MPa=_max_opt(sigma_c_x_qp, sigma_c_y_qp),
        sigma_s_qp_MPa=_max_opt(sigma_s_x_qp, sigma_s_y_qp),
        sigma_c_rara_MPa=_max_opt(sigma_c_x_rara, sigma_c_y_rara),
        sigma_s_rara_MPa=_max_opt(sigma_s_x_rara, sigma_s_y_rara),
        sigma_s_freq_MPa=_max_opt(sigma_s_x_freq, sigma_s_y_freq),
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


def sle_checks(sle_result: Sle, fck_MPa: float, fyk_MPa: float) -> tuple[Check, ...]:
    """The (up to) 5 SLS stress checks against their EC2 §7.2/§7.3 limits (envelope-level, not per
    row/famiglia); a quantity whose governing family had no rows in the envelope is `None` and
    emits no `Check` (fix: no vacuous PASS, see module docstring)."""
    limite_c_qp = SIGMA_C_QP_COEFFICIENT * fck_MPa
    limite_c_rara = SIGMA_C_RARA_COEFFICIENT * fck_MPa
    limite_s_rara = SIGMA_S_RARA_COEFFICIENT * fyk_MPa
    candidati: tuple[tuple[str, float | None, float, str], ...] = (
        ("Tensione calcestruzzo (quasi permanente)", sle_result.sigma_c_qp_MPa, limite_c_qp, "EC2 §7.2(3)"),
        ("Tensione acciaio (quasi permanente)", sle_result.sigma_s_qp_MPa, SIGMA_S_QP_LIMIT_MPA, "EC2 §7.3.4"),
        ("Tensione calcestruzzo (caratteristica)", sle_result.sigma_c_rara_MPa, limite_c_rara, "EC2 §7.2(5)"),
        ("Tensione acciaio (caratteristica)", sle_result.sigma_s_rara_MPa, limite_s_rara, "EC2 §7.2"),
        ("Tensione acciaio (frequente)", sle_result.sigma_s_freq_MPa, SIGMA_S_FREQ_LIMIT_MPA, "EC2 §7.3.4"),
    )
    return tuple(
        Check(name=nome, passed=valore <= limite, clause=clausola, value=valore, limit=limite, unit="N/mm2")
        for nome, valore, limite, clausola in candidati if valore is not None
    )
