"""Verdict checks (`Mensola tozza!C34,A36`, spec §4 steps 17-18).

`C34` is `IF(PRS>PRC, "Gerarchia...non verificata", IF(PR>PEd, "...soddisfatta...", "...non
soddisfatta..."))`: a brittle-strut failure (PRS > PRC) always fails regardless of PR vs PEd,
otherwise the ULS check decides. That collapses to `passed = (PRS<=PRC) and (PR>PEd)`, reproduced
here as two separate `Check`s (per `docs/BUILD_CONTRACT.md`, text verdicts become `Check(passed=...)`).
`A36`'s message text is reproduced verbatim from the sheet even though its wording ("As > di
As,lnk") describes what should be true, not the failing condition itself (spec §3); not flagged as
a bug in spec §7, so left as-is.
"""
from strutture.shared.report import Check

from .rebar_helpers import bars_area_or_zero

CLAUSE = "NTC2018 §4.1.6.1.3"
STIRRUP_LEGS = 2  # closed stirrup: 2 legs per stirrup leg-pair (A36 factor, spec §6)
STIRRUP_INSUFFICIENT_NOTE = "NOTA: As > di As,lnk"


def verifica_gerarchia(prs_kN: float, prc_kN: float) -> Check:
    """Rottura duttile lato acciaio: PRS deve restare <= PRC."""
    return Check(
        name="Gerarchia delle resistenze (rottura duttile lato acciaio)",
        passed=prs_kN <= prc_kN,
        detail=f"PRS={prs_kN:.3f} kN, PRC={prc_kN:.3f} kN",
        clause=CLAUSE,
        value=prs_kN, limit=prc_kN, unit="kN",
    )


def verifica_uls(pr_kN: float, ped_kN: float) -> Check:
    """Verifica allo stato limite ultimo: PR > PEd."""
    return Check(
        name="Verifica PR > PEd",
        passed=pr_kN > ped_kN,
        detail=f"PR={pr_kN:.3f} kN, PEd={ped_kN:.3f} kN",
        clause=CLAUSE,
        value=ped_kN, limit=pr_kN, unit="kN",
    )


def verifica_staffe(n_staffe: int, phi_staffe_mm: float, as_lnk_min_mm2: float) -> Check:
    """A36: area staffe orizzontali effettiva (2 bracci/staffa) confrontata con As,lnk minima."""
    as_staffe_mm2 = bars_area_or_zero(n_staffe * STIRRUP_LEGS, phi_staffe_mm)
    passed = as_staffe_mm2 >= as_lnk_min_mm2
    return Check(
        name="Area staffe orizzontali >= As,lnk minima",
        passed=passed,
        detail="" if passed else STIRRUP_INSUFFICIENT_NOTE,
        clause=CLAUSE,
        value=as_lnk_min_mm2, limit=as_staffe_mm2, unit="mm²",
    )
