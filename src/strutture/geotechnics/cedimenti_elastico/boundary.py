"""Sistema-unità boundary conversion (user decision D1, `docs/architecture-batch2.md` §9): the
flat, dimensional scalar inputs (`q`, `b`, `d`, ...) are unit-neutral and carry `unit_options`;
this module is the one place that converts them to SI before any step module runs, all of which
compute exclusively in SI (m, kPa, MPa).

The `strati` table is intentionally NOT unit-selected: it reuses `shared.soil_layers.SoilLayer`
verbatim (`docs/architecture-batch2.md` §2 fixes its column names/units as `z_top_m`, `z_bot_m`,
`modulo_MPa` for every cedimenti package), so it is always SI regardless of `sistema_unita`.
"""
from typing import Literal

from strutture.shared.units import cm_to_m, kgcm2_to_kpa

SistemaUnita = Literal["SI", "tecnico"]


def to_m(value: float, sistema_unita: SistemaUnita) -> float:
    """`value` in m ("SI") or cm ("tecnico") -> m."""
    return value if sistema_unita == "SI" else cm_to_m(value)


def to_kpa(value: float, sistema_unita: SistemaUnita) -> float:
    """`value` in kPa ("SI") or kg/cm² ("tecnico") -> kPa."""
    return value if sistema_unita == "SI" else kgcm2_to_kpa(value)
