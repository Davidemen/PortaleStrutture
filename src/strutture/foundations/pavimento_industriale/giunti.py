"""`pav-giunti` — joint spacing/thickness prescriptions (spec calculation steps 1-5, geometric rules
of thumb, no code clause stamped on the sheet). Divergence noted but NOT fixed (architecture-
batch2.md §7 `pavimento I39`, "Da verificare"): the contraction-panel row's label says "a/b < 1.2"
but its own formula tests `< 1.5` (matching the isolation-panel row exactly) -- kept as `1.5` in both
`legacy_compat` modes since the formula, not the label, is very likely the correct one, and the
architecture marks this a label mismatch rather than a confirmed formula bug."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.report import Check

CONTRACTION_LMAX_COEFFICIENT = 18.0  # spec step 2: Lmax[cm] = 18*(h[mm]/10) + 100.
CONTRACTION_LMAX_OFFSET_CM = 100.0
ISOLATION_THICKNESS_DIVISOR = 5.0  # spec step 3: t_iso[mm] = h[mm]/5.
MM_PER_M = 1000.0
ASPECT_RATIO_LIMIT = 1.5  # spec steps 1/4 (both rows use this threshold; see module docstring).


class GiuntiResult(BaseModel):
    """`pav-giunti` outputs G39/I39, G40/H40, G41/H41, G47/I47, G50/H50."""

    model_config = ConfigDict(frozen=True)

    rapporto_contrazione: float = Field(description="Rapporto a'/b' del pannello di contrazione", gt=0, json_schema_extra={"unit": "-", "symbol": "a'/b'"})
    verifica_contrazione: Check
    l_max_contrazione_cm: float = Field(description="Dimensione massima del pannello di contrazione Lmax", gt=0, json_schema_extra={"unit": "cm", "symbol": "L_max"})
    spessore_isolamento_mm: float = Field(description="Spessore del giunto di isolamento t_iso", gt=0, json_schema_extra={"unit": "mm", "symbol": "t_iso"})
    rapporto_isolamento: float = Field(description="Rapporto a/b del pannello di isolamento", gt=0, json_schema_extra={"unit": "-", "symbol": "a/b"})
    verifica_isolamento: Check
    apertura_dilatazione_mm: float = Field(description="Apertura del giunto di dilatazione sp", gt=0, json_schema_extra={"unit": "mm", "symbol": "s_p"})


def giunti(
    a_contrazione_m: float, b_contrazione_m: float, a_isolamento_m: float, b_isolamento_m: float,
    alpha_termico: float, delta_t_C: float, h_mm: float,
) -> GiuntiResult:
    """spec steps 1-5."""
    rapporto_contrazione = a_contrazione_m / b_contrazione_m
    rapporto_isolamento = a_isolamento_m / b_isolamento_m
    return GiuntiResult(
        rapporto_contrazione=rapporto_contrazione,
        verifica_contrazione=_check("Pannello di contrazione", rapporto_contrazione),
        l_max_contrazione_cm=CONTRACTION_LMAX_COEFFICIENT * (h_mm / 10.0) + CONTRACTION_LMAX_OFFSET_CM,
        spessore_isolamento_mm=h_mm / ISOLATION_THICKNESS_DIVISOR,
        rapporto_isolamento=rapporto_isolamento,
        verifica_isolamento=_check("Pannello di isolamento", rapporto_isolamento),
        apertura_dilatazione_mm=alpha_termico * delta_t_C * max(a_isolamento_m, b_isolamento_m) * MM_PER_M,
    )


def _check(name: str, rapporto: float) -> Check:
    return Check(name=name, passed=rapporto < ASPECT_RATIO_LIMIT, value=rapporto, limit=ASPECT_RATIO_LIMIT, unit="-")
