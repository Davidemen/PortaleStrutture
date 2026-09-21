"""Wall/backfill geometry and centroids (muro-sostegno rows 29-39), shared by every combination."""
from .models import GeometriaResult


def geometria_muro(
    *, h_muro_m: float, s_fond_m: float, s_base_m: float, s_top_m: float, b_valle_m: float, b_monte_m: float
) -> GeometriaResult:
    """H, B, area/baricentro del muro (I30/I33:I35) e del cuneo di terreno a tergo (I11/I12/I39)."""
    h_muro_tot_m = h_muro_m + s_fond_m
    b_fond_m = b_valle_m + s_base_m + b_monte_m
    a_muro_m2 = b_fond_m * s_fond_m + h_muro_m * (s_base_m + s_top_m) * 0.5
    x_muro_m = (
        (b_fond_m * s_fond_m) * (b_fond_m / 2)
        + (s_top_m * h_muro_m) * (b_valle_m + s_base_m - s_top_m / 2)
        + (0.5 * (s_base_m - s_top_m) * h_muro_m) * (1 / 3) * (b_valle_m + s_base_m - s_top_m)
    ) / a_muro_m2
    a_terr_m2 = b_monte_m * h_muro_m
    x_terr_m = b_valle_m + s_base_m + b_monte_m / 2

    # Vertical centroid heights from the base of the footing (EN1998-5 §7.3.2.2(2)P inertia arms):
    # footing rectangle + stem rectangle (width s_top, full stem height) + stem triangle (the
    # s_base-s_top taper, thick end at the footing -> centroid at h/3 from the footing).
    a_fond_m2 = b_fond_m * s_fond_m
    a_stelo_rett_m2 = s_top_m * h_muro_m
    a_stelo_tri_m2 = 0.5 * (s_base_m - s_top_m) * h_muro_m
    z_muro_m = (
        a_fond_m2 * (s_fond_m / 2)
        + a_stelo_rett_m2 * (s_fond_m + h_muro_m / 2)
        + a_stelo_tri_m2 * (s_fond_m + h_muro_m / 3)
    ) / a_muro_m2
    z_terr_m = s_fond_m + h_muro_m / 2

    return GeometriaResult(
        h_muro_tot_m=h_muro_tot_m,
        b_fond_m=b_fond_m,
        a_muro_m2=a_muro_m2,
        x_muro_m=x_muro_m,
        z_muro_m=z_muro_m,
        a_terr_m2=a_terr_m2,
        x_terr_m=x_terr_m,
        z_terr_m=z_terr_m,
        x_sv_m=x_terr_m,
    )
