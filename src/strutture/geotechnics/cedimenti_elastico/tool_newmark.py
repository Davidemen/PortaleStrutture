"""Composed tool: `geo-cedimento-elastico-newmark` (`docs/specs/geo-cedimenti-elastico.md` Tool 1).
`run` only wires the boundary conversion, the ground->base layer shift and the CENTRO/PUNTO step
modules; the physics stays in `centro.py` / `punto.py` / `integrate.py`."""
from strutture.shared.report import Report, success
from strutture.shared.tool import Tool
from strutture.shared.units import CM_PER_M, MM_PER_M

from .boundary import to_kpa, to_m
from .centro import centro_settlement
from .ground_to_base import shift_to_base
from .integrate import Slice, total_settlement_m
from .models_newmark import CaricoNewmark, CentroCedimento, NewmarkInput, NewmarkOutput, PuntoCedimento, RigaNewmark
from .punto import punto_settlement

ESEMPIO_CENTRO = {
    "modalita": "CENTRO", "sistema_unita": "tecnico", "q": 0.5, "d": 110, "b": 350, "l": 500, "z_max": 910, "dz": 10,
    "strati": [
        {"z_top_m": 0.80, "z_bot_m": 4.80, "modulo_MPa": 5.5}, {"z_top_m": 4.80, "z_bot_m": 5.80, "modulo_MPa": 7.0},
        {"z_top_m": 5.80, "z_bot_m": 6.60, "modulo_MPa": 9.0}, {"z_top_m": 6.60, "z_bot_m": 32.60, "modulo_MPa": 7.0},
        {"z_top_m": 32.60, "z_bot_m": 120.0, "modulo_MPa": 7.0},
    ],
}


def _righe(slices: tuple[Slice, ...]) -> tuple[RigaNewmark, ...]:
    return tuple(RigaNewmark(z_m=s.z_m, delta_sigma_kPa=s.sigma_kPa, modulo_MPa=s.modulo_MPa, delta_w_m=s.delta_w_m) for s in slices)


def _scarto_pct(principale_m: float, qa_m: float) -> float:
    return 100.0 * (principale_m - qa_m) / principale_m if principale_m != 0 else 0.0


def run_newmark(inputs: NewmarkInput) -> Report[NewmarkOutput]:
    sistema = inputs.sistema_unita
    q_kPa = to_kpa(inputs.q, sistema)
    d_m = to_m(inputs.d, sistema)
    layers = shift_to_base(inputs.strati, d_m)
    z_max_m, dz_m = to_m(inputs.z_max, sistema), to_m(inputs.dz, sistema)
    carico = CaricoNewmark(q_kPa=q_kPa, d_m=d_m)

    if inputs.modalita == "CENTRO":
        b_m, l_m = to_m(inputs.b, sistema), to_m(inputs.l, sistema)
        main_slices, qa_slices = centro_settlement(q_kPa, b_m, l_m, layers, z_max_m=z_max_m, dz_m=dz_m, legacy_compat=inputs.legacy_compat)
        w_centro_m, w_qa_m = total_settlement_m(main_slices), total_settlement_m(qa_slices)
        data = NewmarkOutput(
            carico=carico, righe=_righe(main_slices), righe_qa=_righe(qa_slices),
            centro=CentroCedimento(
                w_centro_cm=w_centro_m * CM_PER_M, w_centro_mm=w_centro_m * MM_PER_M,
                w_qa_cm=w_qa_m * CM_PER_M, scarto_qa_pct=_scarto_pct(w_centro_m, w_qa_m),
            ),
        )
        return success(data, inputs)

    side_p_m, side_q_m = to_m(inputs.side_p, sistema), to_m(inputs.side_q, sistema)
    e1_m, e2_m = to_m(inputs.e1, sistema), to_m(inputs.e2, sistema)
    o_slices, o_prime_slices = punto_settlement(
        q_kPa, side_p_m, side_q_m, e1_m, e2_m, layers, z_max_m=z_max_m, dz_m=dz_m, legacy_compat=inputs.legacy_compat
    )
    w_o_m, w_o_prime_m = total_settlement_m(o_slices), total_settlement_m(o_prime_slices)
    data = NewmarkOutput(
        carico=carico, righe=_righe(o_slices), righe_o_prime=_righe(o_prime_slices),
        punto=PuntoCedimento(
            w_o_cm=w_o_m * CM_PER_M, w_o_mm=w_o_m * MM_PER_M,
            w_o_prime_cm=w_o_prime_m * CM_PER_M, w_o_prime_mm=w_o_prime_m * MM_PER_M,
        ),
    )
    return success(data, inputs)


TOOLS: tuple[Tool, ...] = (
    Tool(
        name="geo-cedimento-elastico-newmark",
        title="Cedimento elastico - integrazione di Newmark",
        group="Geotecnica / Cedimenti",
        norm="Newmark 1942 (?)",
        input_model=NewmarkInput,
        output_model=NewmarkOutput,
        run=run_newmark,
        example=ESEMPIO_CENTRO,
    ),
)
