"""Heel (fondazione di monte/tacco) cantilever bending at the footing root: backfill self-weight
moment, surcharge vertical-component moment, heel-slab self-weight moment, and a 3-branch
soil-pressure moment (muro-sostegno rows 172-187). Pure functions; `tool.py` assembles the
`ArmaturaFondazioneMonteCombo`/`ArmaturaFondazioneMonteResult` and picks the governing combination
via `rebar_selection`.
"""


def pressione_interpolata_kPa(
    *, b_star_m: float, p_valle_kPa: float, p_monte_kPa: float, b_fond_m: float, b_monte_m: float
) -> float:
    """p** (col F) — pressione all'incastro della mensola di monte, all'ascissa x**=Bfond-Bmonte.

    Sheet formula: `IF(B*=0, ..., IF(B* > -(Bfond-Bmonte), (B*-(Bfond-Bmonte))*pvalle/B*, 0))`.
    Since B* >= 0 and Bmonte < Bfond always, the middle branch's condition is always true in
    practice (kept literally below for fidelity — it is *not* `B* > Bfond-Bmonte`, and can return
    a negative p** when B* < Bfond-Bmonte, which the sheet itself does)."""
    if b_star_m == 0:
        return p_monte_kPa + b_monte_m * (p_valle_kPa - p_monte_kPa) / b_fond_m
    soglia_m = b_fond_m - b_monte_m  # C179/C185/... = I33 - I173
    if b_star_m > -soglia_m:
        return (b_star_m - soglia_m) * p_valle_kPa / b_star_m
    return 0.0


def momento_pressione_kNm(
    *, p_monte_kPa: float, p_star_star_kPa: float, b_monte_m: float, b_fond_m: float, b_star_m: float
) -> float:
    """MEd.p (col G) — segno negativo: la spinta del terreno sotto la mensola resiste al
    ribaltamento verso monte (3 rami secondo la posizione di p** rispetto a pmonte/B*)."""
    if p_monte_kPa > 0:
        if p_star_star_kPa > p_monte_kPa:
            return -(p_monte_kPa * b_monte_m**2 / 2 + 0.5 * (p_star_star_kPa - p_monte_kPa) * b_monte_m * (b_monte_m / 3))
        return -(p_star_star_kPa * b_monte_m**2 / 2 + 0.5 * (p_monte_kPa - p_star_star_kPa) * b_monte_m * (2 * b_monte_m / 3))
    soglia_m = b_fond_m - b_monte_m
    return -(0.5 * p_star_star_kPa * (b_star_m - soglia_m) ** 2 / 3)


def momento_terreno_kNm(*, w_terr_kN: float, b_monte_m: float, b_fond_m: float, x_terr_m: float) -> float:
    """MEd.terr (col H) = Wterr·(Bmonte-(Bfond-xterr)) — momento del peso del cuneo di terreno a tergo."""
    return w_terr_kN * (b_monte_m - (b_fond_m - x_terr_m))


def momento_sovraccarico_verticale_kNm(*, sv_tot_kN: float, x_sv_m: float, b_fond_m: float, b_monte_m: float) -> float:
    """MEd.SV (col I) = SV.tot·(xSv-(Bfond-Bmonte)) — momento della componente verticale della spinta."""
    return sv_tot_kN * (x_sv_m - (b_fond_m - b_monte_m))


def momento_autopeso_kNm(*, b_monte_m: float, gamma_g_muro: float, gamma_cls_kN_m3: float, s_fond_m: float) -> float:
    """MEd.fond (col J) = Bmonte·γG,muro·γcls·sfondazione²/2 — peso proprio della soletta di monte."""
    return b_monte_m * gamma_g_muro * gamma_cls_kN_m3 * s_fond_m**2 / 2
