"""Toe (fondazione di valle/mancia) cantilever bending at the footing root, from the
trapezoid/triangle soil-pressure diagram (Tool 3) plus the toe self-weight (muro-sostegno rows
154-169). Pure functions; `tool.py` assembles the `ArmaturaFondazioneValleCombo`/
`ArmaturaFondazioneValleResult` and picks the governing combination via `rebar_selection`.

`x_star_m` (col C, "x*") is the toe-root abscissa; the sheet always sets it to Bvalle regardless
of combination (`=I155` on the first row, `=C161` — i.e. "same as above" — on every following row).
"""


def pressione_interpolata_kPa(
    *, b_star_m: float, p_valle_kPa: float, p_monte_kPa: float, b_fond_m: float, x_star_m: float
) -> float:
    """p* (col F) — pressione all'incastro della mensola di valle, all'ascissa x*=Bvalle."""
    if b_star_m == 0:
        return p_monte_kPa + (p_valle_kPa - p_monte_kPa) * (b_fond_m - x_star_m) / b_fond_m
    return p_valle_kPa * (b_star_m - x_star_m) / b_star_m


def momento_pressione_1_kNm(*, p_star_kPa: float, p_valle_kPa: float, b_valle_m: float) -> float:
    """MEd.p.1 (col G) — momento del blocco di pressione rettangolare/triangolare inferiore."""
    p_kPa = min(p_star_kPa, p_valle_kPa)
    return p_kPa * b_valle_m**2 / 2


def momento_pressione_2_kNm(*, p_star_kPa: float, p_valle_kPa: float, b_star_m: float, b_valle_m: float) -> float:
    """MEd.p.2 (col H) — momento del cuneo di pressione residuo (3 rami)."""
    if p_star_kPa > 0:
        if p_star_kPa <= p_valle_kPa:
            return 0.5 * b_valle_m * (p_valle_kPa - p_star_kPa) * (2 / 3) * b_valle_m
        return 0.5 * (p_star_kPa - p_valle_kPa) * b_valle_m * b_valle_m / 3
    return 0.5 * b_star_m * p_valle_kPa * (b_valle_m - b_star_m / 3)


def momento_autopeso_kNm(*, gamma_g_muro: float, s_fond_m: float, gamma_cls_kN_m3: float, b_valle_m: float) -> float:
    """MEd.fond (col I) = -γG,muro·sfondazione·γcls·Bvalle²/2 (peso proprio della mensola, controllante)."""
    return -gamma_g_muro * s_fond_m * gamma_cls_kN_m3 * b_valle_m**2 / 2
