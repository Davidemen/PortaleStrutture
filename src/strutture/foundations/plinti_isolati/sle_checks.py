"""Step: SLS stress checks against EC2 §7.2/§7.3 limits, factored out of `sle.py` to keep both
modules within the size limits (docs/BUILD_CONTRACT.md, regola 12). Same formulas, same
`senza_domanda` convention (a quantity with no governing family emits no `Check`)."""
from strutture.shared.report import Check

from .models_sle import Sle

SIGMA_C_QP_COEFFICIENT = 0.45  # EC2 §7.2(3) - limite tensione calcestruzzo, combinazione quasi permanente.
SIGMA_S_QP_LIMIT_MPA = 220.0  # EC2 §7.3.4, controllo fessurazione semplificato.
SIGMA_C_RARA_COEFFICIENT = 0.6  # EC2 §7.2(5) - limite tensione calcestruzzo, combinazione caratteristica.
SIGMA_S_RARA_COEFFICIENT = 0.8  # EC2 §7.2, limite tensione armatura, combinazione caratteristica.
SIGMA_S_FREQ_LIMIT_MPA = 240.0  # EC2 §7.3.4, controllo fessurazione semplificato.


def sle_checks(sle_result: Sle, fck_MPa: float, fyk_MPa: float) -> tuple[Check, ...]:
    """The (up to) 5 SLS stress checks against their EC2 §7.2/§7.3 limits (envelope-level, not per
    row/famiglia); a quantity whose governing family had no rows in the envelope is `None` and
    emits no `Check` (fix: no vacuous PASS, see `sle.py` module docstring)."""
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
