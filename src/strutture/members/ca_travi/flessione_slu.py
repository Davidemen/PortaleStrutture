"""Tool 2 — verifica-flessione-slu: momento resistente ULS a flessione semplice, sezione
rettangolare in semplice armatura, blocco di tensioni rettangolare (NTC2018 §4.1.2.3.4.2).

Divergenza rispetto al foglio (`legacy_compat=True` la riproduce, vedi docs/divergences/ca-travi.md):
- Z32 (profondità dell'asse neutro y) usa un fattore di blocco 0.81 al posto di 0.8 (NTC2018
  §4.1.2.3.4.2, fck<=50MPa). Il fattore si semplifica algebricamente nel calcolo di MRd (Z33),
  che quindi resta invariato tra le due modalità, ma y (l'unica grandezza pubblicata che un
  utente può usare per uno screening di duttilità) risulta ~1.25% sotto il vero asse neutro x in
  modalità legacy.

Aggiunta (in entrambe le modalità, non è una divergenza numerica dal foglio: il foglio non
verifica mai questa compatibilità): §4.1.2.3.4.2/§4.1.2.1.2.2 richiedono che l'acciaio sia
snervato (eps_s >= eps_yd) prima di applicare MRd = As*fyd*(d-0.4x); `eps_s_permille`/
`acciaio_snervato` riportano questo controllo di compatibilità/duttilità.
"""
from .models import FlessioneOutput

STRESS_BLOCK_FATTORE_LEGACY = 0.81  # sheet Z32/Z33 (vedi divergenze)
STRESS_BLOCK_FATTORE = 0.8  # NTC2018 §4.1.2.3.4.2 — fattore lambda del blocco rettangolare (fck<=50MPa)
EPS_CU_PERMILLE = 3.5  # NTC2018 §4.1.2.1.2.2 — deformazione ultima a compressione del cls [per mille]


def _fattore_blocco(legacy_compat: bool) -> float:
    return STRESS_BLOCK_FATTORE_LEGACY if legacy_compat else STRESS_BLOCK_FATTORE


def profondita_asse_neutro_mm(as_o_mm2: float, fyd_MPa: float, b_mm: float, fcd_MPa: float, *, legacy_compat: bool = False) -> float:
    """y (Z32): profondità dell'asse neutro nel blocco di tensioni [mm]."""
    return as_o_mm2 * fyd_MPa / (b_mm * fcd_MPa) / _fattore_blocco(legacy_compat)


def momento_resistente_kNm(as_o_mm2: float, fyd_MPa: float, d_mm: float, y_mm: float, *, legacy_compat: bool = False) -> float:
    """MRd (Z33) [kNm]. Il fattore di blocco si semplifica algebricamente: MRd non dipende dalla
    modalità (stesso fattore usato per calcolare `y_mm` e per pesarlo qui)."""
    return as_o_mm2 * fyd_MPa * (d_mm - _fattore_blocco(legacy_compat) * y_mm / 2.0) / 1e6


def deformazione_acciaio_permille(d_mm: float, y_mm: float) -> float:
    """eps_s [per mille], per compatibilità delle deformazioni (Bernoulli, eps_cu=3.5 per mille),
    usando y come profondità dell'asse neutro."""
    return EPS_CU_PERMILLE * (d_mm - y_mm) / y_mm


def verifica_flessione_slu(
    *,
    as_o_mm2: float,
    fyd_MPa: float,
    fcd_MPa: float,
    b_mm: float,
    d_mm: float,
    med_slu_kNm: float,
    es_MPa: float,
    legacy_compat: bool = False,
) -> FlessioneOutput:
    y_mm = profondita_asse_neutro_mm(as_o_mm2, fyd_MPa, b_mm, fcd_MPa, legacy_compat=legacy_compat)
    mrd_kNm = momento_resistente_kNm(as_o_mm2, fyd_MPa, d_mm, y_mm, legacy_compat=legacy_compat)
    eps_s_permille = deformazione_acciaio_permille(d_mm, y_mm)
    eps_yd_permille = fyd_MPa / es_MPa * 1000.0
    return FlessioneOutput(
        d_mm=d_mm,
        y_mm=y_mm,
        mrd_kNm=mrd_kNm,
        tasso_sfruttamento=med_slu_kNm / mrd_kNm,
        eps_s_permille=eps_s_permille,
        acciaio_snervato=eps_s_permille >= eps_yd_permille,
    )
