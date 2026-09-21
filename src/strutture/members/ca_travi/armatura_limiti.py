"""Tool 1 — armatura-minima-massima: limiti di armatura longitudinale e trasversale.

NTC2018 §4.1.6.1.1 (EC2 9.2.1.1 As,min/As,max; EC2 9.2.2(5)/(6) Asw,min e passo massimo staffe).

Divergenze rispetto al foglio (`legacy_compat=True` le riproduce, vedi docs/divergences/ca-travi.md):
- Z12 (As,min) usa il braccio di leva z al posto dell'altezza utile d, e la tensione di rottura
  ftk (cella Z7) al posto di fyk nel termine 0.26·fctm/fyk.
- Z16 (Ast,min staffe) è una quota storica 1.5·B [mm²/m]; il foglio la usa come UNICO minimo,
  scartando ρw,min·b·1000 (EC2 9.2.2(5)). NTC2018 §4.1.6.1.1 impone letteralmente "staffe con
  sezione complessiva non inferiore ad Ast=1,5·b mm²/m": è un minimo NTC cogente, non una regola
  empirica pre-Eurocodice, quindi in modalità fissa non va sostituito ma solo integrato con
  ρw,min·b·1000 come minimo aggiuntivo (`max(1.5·b, ρw,min·b·1000)`).
- Z18 (passo massimo staffe) usa 1000/3 mm e 0.8·z invece del tetto assoluto 330 mm e 0.8·d.

Il foglio non verifica mai i limiti sismici di armatura longitudinale di NTC2018 §7.4.6.2.1
(rho_min=1.4/fyk lato teso, rho_max=rho_comp+3.5/fyk, armatura compressa >= quota minima della
tesa): `duttilita_longitudinale_sismica` aggiunge questo controllo in ENTRAMBE le modalità (non è
una divergenza numerica dal foglio, perché il foglio non lo calcola affatto — è un controllo
aggiuntivo, come la conformità Tab. 4.1.IV in `fessurazione.py`). Il ferro tipo 2 (`n_ferri2`/
`diametro_ferri2_mm`), già presente come armatura tesa aggiuntiva, è qui riusato come strato
compresso As' per questa sola verifica (approssimazione esplicitamente richiesta dalla review:
non introduce un nuovo input).
"""
import math

from strutture.shared.divergences import legacy
from strutture.shared.rebar_catalog import asw_per_m, bars_area

from .models import ArmaturaLimitiOutput, ClasseDuttilita

AS_MIN_RHO_ASSOLUTO = 0.0013  # NTC2018 §4.1.6.1.1 — quota assoluta minima
AS_MIN_RHO_FCTM = 0.26  # NTC2018 §4.1.6.1.1 — quota 0.26*fctm/fyk
AS_MAX_RHO = 0.04  # NTC2018 §4.1.6.1.1 — armatura massima, 4% dell'area lorda
AST_MIN_LEGACY_COEFF = 1.5  # sheet Z16 (fill-down storico, non-NTC2018, vedi divergenze)
PASSO_MAX_LEGACY_MM = 1000.0 / 3.0  # sheet Z18 (vedi divergenze)
RHO_W_MIN_COEFF = 0.08  # EC2 9.2.2(5) — rho_w,min = 0.08*sqrt(fck)/fyk
PASSO_MAX_ASSOLUTO_MM = 330.0  # NTC2018 §4.1.6.1.1 — tetto assoluto passo massimo staffe
PASSO_MAX_RAPPORTO_D = 0.8  # NTC2018 §4.1.6.1.1 — passo massimo = 0.8*d
MM2_PER_M2 = 1000.0
RHO_MIN_SISMICO_NUMERATORE = 1.4  # NTC2018 §7.4.6.2.1 — rho_min = 1.4/fyk (zona tesa)
RHO_MAX_SISMICO_ADDENDO = 3.5  # NTC2018 §7.4.6.2.1 — rho_max = rho_comp + 3.5/fyk
RAPPORTO_ARMATURA_COMPRESSA_MIN = {"CDA": 0.5, "CDB": 0.25}  # NTC2018 §7.4.6.2.1 — As'/As minimo


def _area_ferri_tesi(n1: int, diametro1_mm: float, n2: int, diametro2_mm: float) -> float:
    """As,o (AM32): somma solo i tipi di ferro effettivamente presenti (n > 0)."""
    area = bars_area(n1, diametro1_mm) if n1 > 0 else 0.0
    return area + (bars_area(n2, diametro2_mm) if n2 > 0 else 0.0)


def _area_staffe_per_m(
    diametro1_mm: float, bracci1: int, diametro2_mm: float, bracci2: int, passo_mm: float
) -> float:
    """Area di staffe complessiva per metro: entrambi i tipi condividono lo stesso passo
    (il foglio replica sempre H19=H16, vedi divergenze)."""
    area = asw_per_m(diametro1_mm, bracci1, passo_mm) if bracci1 > 0 else 0.0
    return area + (asw_per_m(diametro2_mm, bracci2, passo_mm) if bracci2 > 0 else 0.0)


def area_minima_tesa_mm2(
    *, b_mm: float, d_mm: float, z_mm: float, fctm_MPa: float, fyk_MPa: float, ftk_MPa: float, legacy_compat: bool
) -> float:
    """As,min (Z12)."""
    altezza_mm, denominatore_MPa = (
        (z_mm, ftk_MPa) if legacy("ca-travi/as-min-usa-z-e-ftk", legacy_compat) else (d_mm, fyk_MPa)
    )
    return max(
        AS_MIN_RHO_ASSOLUTO * b_mm * altezza_mm,
        AS_MIN_RHO_FCTM * b_mm * altezza_mm * fctm_MPa / denominatore_MPa,
    )


def limiti_staffe(*, b_mm: float, d_mm: float, z_mm: float, fck_MPa: float, fyk_MPa: float, legacy_compat: bool) -> tuple[float, float]:
    """(Ast,min per metro [Z16], passo massimo [Z18]).

    Ast,min: NTC2018 §4.1.6.1.1 impone il floor cogente 1.5*b [mm²/m] (Z16); EC2 9.2.2(5) impone
    un floor aggiuntivo rho_w,min*b*1000. In modalità fissa i due minimi si sommano come MAX, mai
    come sostituzione dell'uno con l'altro (il floor NTC non può essere abbassato).

    Un unico `if legacy_compat` calcola sia Ast,min (Z16, id `ast-min-staffe-doppio-limite`) sia
    il passo massimo (Z18, id `passo-max-staffe-usa-z`): il foglio degenera entrambi con la stessa
    condizione, quindi qui è collegato solo il primo id (vedi il campo `motivo_senza_ramo` del
    secondo nel registro)."""
    ast_min_ntc_mm2 = AST_MIN_LEGACY_COEFF * b_mm
    if legacy("ca-travi/ast-min-staffe-doppio-limite", legacy_compat):
        return ast_min_ntc_mm2, min(PASSO_MAX_LEGACY_MM, PASSO_MAX_RAPPORTO_D * z_mm)
    rho_w_min = RHO_W_MIN_COEFF * math.sqrt(fck_MPa) / fyk_MPa
    ast_min_ec2_mm2 = rho_w_min * b_mm * MM2_PER_M2
    passo_max_mm = min(PASSO_MAX_ASSOLUTO_MM, PASSO_MAX_LEGACY_MM, PASSO_MAX_RAPPORTO_D * d_mm)
    return max(ast_min_ntc_mm2, ast_min_ec2_mm2), passo_max_mm


def duttilita_longitudinale_sismica(
    *, b_mm: float, d_mm: float, as_tesa_mm2: float, as_comp_mm2: float, fyk_MPa: float, classe: ClasseDuttilita
) -> tuple[float, float, float, float]:
    """NTC2018 §7.4.6.2.1: (rho, rho_min, rho_max, as_comp_min_mm2).

    rho/rho_comp sono riferiti a b*d; rho_min=1.4/fyk; rho_max=rho_comp+3.5/fyk; l'armatura
    compressa deve essere almeno il 50% (CD"A") / 25% (CD"B") di quella tesa."""
    area_sezione_mm2 = b_mm * d_mm
    rho = as_tesa_mm2 / area_sezione_mm2
    rho_comp = as_comp_mm2 / area_sezione_mm2
    rho_min = RHO_MIN_SISMICO_NUMERATORE / fyk_MPa
    rho_max = rho_comp + RHO_MAX_SISMICO_ADDENDO / fyk_MPa
    as_comp_min_mm2 = RAPPORTO_ARMATURA_COMPRESSA_MIN[classe] * as_tesa_mm2
    return rho, rho_min, rho_max, as_comp_min_mm2


def armatura_minima_massima(
    *,
    b_mm: float,
    h_mm: float,
    d_mm: float,
    z_mm: float,
    n_ferri1: int,
    diametro_ferri1_mm: float,
    n_ferri2: int,
    diametro_ferri2_mm: float,
    diametro_staffe1_mm: float,
    n_bracci_staffe1: int,
    passo_staffe1_mm: float,
    diametro_staffe2_mm: float,
    n_bracci_staffe2: int,
    fck_MPa: float,
    fctm_MPa: float,
    fyk_MPa: float,
    ftk_MPa: float,
    classe_duttilita: ClasseDuttilita,
    legacy_compat: bool = False,
) -> ArmaturaLimitiOutput:
    as_o_mm2 = _area_ferri_tesi(n_ferri1, diametro_ferri1_mm, n_ferri2, diametro_ferri2_mm)
    as_min_mm2 = area_minima_tesa_mm2(
        b_mm=b_mm, d_mm=d_mm, z_mm=z_mm, fctm_MPa=fctm_MPa, fyk_MPa=fyk_MPa, ftk_MPa=ftk_MPa, legacy_compat=legacy_compat
    )
    ast_min_per_m_mm2, passo_max_mm = limiti_staffe(
        b_mm=b_mm, d_mm=d_mm, z_mm=z_mm, fck_MPa=fck_MPa, fyk_MPa=fyk_MPa, legacy_compat=legacy_compat
    )
    asw_per_m_mm2 = _area_staffe_per_m(diametro_staffe1_mm, n_bracci_staffe1, diametro_staffe2_mm, n_bracci_staffe2, passo_staffe1_mm)

    as_tesa_mm2 = bars_area(n_ferri1, diametro_ferri1_mm)
    as_comp_mm2 = bars_area(n_ferri2, diametro_ferri2_mm) if n_ferri2 > 0 else 0.0
    rho, rho_min_sismico, rho_max_sismico, as_comp_min_mm2 = duttilita_longitudinale_sismica(
        b_mm=b_mm, d_mm=d_mm, as_tesa_mm2=as_tesa_mm2, as_comp_mm2=as_comp_mm2, fyk_MPa=fyk_MPa, classe=classe_duttilita
    )

    return ArmaturaLimitiOutput(
        z_mm=z_mm,
        as_o_mm2=as_o_mm2,
        as_min_mm2=as_min_mm2,
        as_max_mm2=AS_MAX_RHO * b_mm * h_mm,
        asw_per_m_mm2=asw_per_m_mm2,
        ast_min_per_m_mm2=ast_min_per_m_mm2,
        passo_max_staffe_mm=passo_max_mm,
        as_comp_mm2=as_comp_mm2,
        rho_tesa=rho,
        rho_min_sismico=rho_min_sismico,
        rho_max_sismico=rho_max_sismico,
        as_comp_min_sismico_mm2=as_comp_min_mm2,
    )
