"""Minimum stirrup check, NTC sheet variant (C51:C56)."""
from pydantic import BaseModel, ConfigDict, Field

from strutture.shared.rebar_catalog import asw_per_m, bars_area
from strutture.shared.report import Check

from .geometria import altezza_utile_mm

PMAX_FRAZIONE_D_NTC = 0.8  # NTC §7.2.5 — passo massimo staffe, frazione dell'altezza utile.
PMAX_ASSOLUTO_MM_NTC = 1000.0 / 3.0  # ≈333 mm — limite assoluto sheet C52.
AST_MIN_PER_B_NTC = 1.5  # mm²/m per mm di base B — area minima staffe trasversali per travi di collegamento.


class MinimiNtcResult(BaseModel):
    """d, pmax, Ast,min, Ast, verifica."""

    model_config = ConfigDict(frozen=True)

    d_mm: float = Field(description="Altezza utile d", json_schema_extra={"unit": "mm", "symbol": "d"}, gt=0)
    pmax_mm: float = Field(description="Passo staffe massimo pmax", json_schema_extra={"unit": "mm"}, gt=0)
    ast_min_mm2_per_m: float = Field(description="Area staffe minima Ast,min", json_schema_extra={"unit": "mm2/m", "symbol": "A_st,min"}, gt=0)
    ast_mm2: float = Field(description="Area staffe Ast", json_schema_extra={"unit": "mm2", "symbol": "A_st"}, gt=0)
    verifica: Check


def minimi_ntc(b_mm: float, h_mm: float, cf_mm: float, phi_staffa_mm: float, n_bracci: int, p_mm: float) -> MinimiNtcResult:
    """d[C51], pmax[C52], Ast,min[C54], Ast[C55]; verifica: Ast·1000/p > Ast,min."""
    d_mm = altezza_utile_mm(h_mm, cf_mm)
    pmax_mm = min(PMAX_FRAZIONE_D_NTC * d_mm, PMAX_ASSOLUTO_MM_NTC)
    ast_min_mm2_per_m = AST_MIN_PER_B_NTC * b_mm
    ast_mm2 = bars_area(n_bracci, phi_staffa_mm)
    densita_mm2_per_m = asw_per_m(phi_staffa_mm, n_bracci, p_mm)
    return MinimiNtcResult(
        d_mm=d_mm, pmax_mm=pmax_mm, ast_min_mm2_per_m=ast_min_mm2_per_m, ast_mm2=ast_mm2,
        verifica=Check(
            name="Verifica area staffe", passed=densita_mm2_per_m > ast_min_mm2_per_m, clause="NTC2018 §7.2.5",
            value=densita_mm2_per_m, limit=ast_min_mm2_per_m, unit="mm2/m",
        ),
    )
