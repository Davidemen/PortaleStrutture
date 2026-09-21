"""Tool 6 — dettagli-costruttivi-capacity-design: duttilità CD"A"/CD"B" e verifica a taglio
per capacity design (NTC2018 §7.4.6.1.1 lunghezza critica, §7.4.6.2.1 passo staffe zona
critica, §7.4.4.1.1 taglio di capacity design).

Divergenze rispetto al foglio (`legacy_compat=True` le riproduce, vedi docs/divergences/ca-travi.md):
- K60 (passo massimo staffe zona critica) include nel MIN il diametro di un tipo di ferro/staffa
  non utilizzato (0 mm) quando il tipo 2 non è impiegato, azzerando il risultato.
- K60 usa anche H7 (altezza lorda h) al posto dell'altezza utile d nel primo termine del MIN
  (NTC2018 §7.4.6.2.1 richiede "un quarto dell'ALTEZZA UTILE della sezione trasversale" = d/4).
- K81 restituisce una grandezza dimensionalmente un momento (γRd·MRb·min(1,MRc/MRb), in kNm) ma
  la confronta con VRd (una forza, in kN) senza mai dividere per la luce della trave Lt (K80,
  input validato ma mai usato). NTC2018 §7.4.4.1.1 richiede VEd = (ΣMi,d)/Lt.
"""
from .models import CapacityDesignOutput, ClasseDuttilita

LCR_FATTORE_CDA = 1.5  # NTC2018 §7.4.6.1.1 — lunghezza critica CD"A" = 1.5*h (CD"B" = h)
PASSO_MAX_FRAZIONE_ALTEZZA_LEGACY = 4.0  # sheet K60 — h/4 (vedi divergenze)
PASSO_MAX_FRAZIONE_ALTEZZA_UTILE = 4.0  # NTC2018 §7.4.6.2.1 — d/4 (altezza utile, non lorda)
PASSO_MAX_FATTORE_STAFFE = 24.0  # NTC2018 §7.4.6.2.1 — 24*diametro minimo staffe
PASSO_MAX_ASSOLUTO_MM = {"CDA": 175.0, "CDB": 225.0}  # NTC2018 §7.4.6.2.1
PASSO_MAX_FATTORE_BARRE = {"CDA": 6.0, "CDB": 8.0}  # NTC2018 §7.4.6.2.1
GAMMA_RD_CAPACITY = {"CDA": 1.2, "CDB": 1.0}  # NTC2018 §7.4.4.1.1 — fattore di sovraresistenza


def lunghezza_critica_mm(h_mm: float, classe: ClasseDuttilita) -> float:
    """Lcr (K59)."""
    return LCR_FATTORE_CDA * h_mm if classe == "CDA" else h_mm


def _diametro_minimo_effettivo(diametri_e_conteggi: tuple[tuple[float, int], ...]) -> float:
    """Il più piccolo diametro tra i tipi effettivamente presenti (conteggio > 0); ignora i tipi
    non utilizzati, a differenza del foglio che li include comunque nel MIN (vedi divergenze)."""
    presenti = [diametro for diametro, conteggio in diametri_e_conteggi if conteggio > 0]
    return min(presenti) if presenti else 0.0


def passo_max_zona_critica_mm(
    *,
    h_mm: float,
    d_mm: float,
    classe: ClasseDuttilita,
    diametro_staffe1_mm: float,
    diametro_staffe2_mm: float,
    n_bracci_staffe2: int,
    diametro_ferri1_mm: float,
    n_ferri1: int,
    diametro_ferri2_mm: float,
    n_ferri2: int,
    legacy_compat: bool = False,
) -> float:
    """Passo massimo staffe in zona critica (K60).

    NTC2018 §7.4.6.2.1 richiede un quarto dell'ALTEZZA UTILE d (non l'altezza lorda h) nel primo
    termine del MIN; il foglio (K60) usa H7 (h) — vedi docs/divergences/ca-travi.md item 4.
    """
    if legacy_compat:
        staffa_min_mm = diametro_staffe1_mm  # il foglio (K60) referenzia solo H15, non MIN(H15,H18)
        barra_min_mm = min(diametro_ferri1_mm, diametro_ferri2_mm)  # include lo 0 se il tipo 2 è inutilizzato
        primo_termine_mm = h_mm / PASSO_MAX_FRAZIONE_ALTEZZA_LEGACY
    else:
        staffa_min_mm = _diametro_minimo_effettivo(((diametro_staffe1_mm, 1), (diametro_staffe2_mm, n_bracci_staffe2)))
        barra_min_mm = _diametro_minimo_effettivo(((diametro_ferri1_mm, n_ferri1), (diametro_ferri2_mm, n_ferri2)))
        primo_termine_mm = d_mm / PASSO_MAX_FRAZIONE_ALTEZZA_UTILE
    return min(
        primo_termine_mm,
        PASSO_MAX_FATTORE_STAFFE * staffa_min_mm,
        PASSO_MAX_ASSOLUTO_MM[classe],
        PASSO_MAX_FATTORE_BARRE[classe] * barra_min_mm,
    )


def lunghezza_ancoraggio_mm(diametro_staffe1_mm: float, diametro_staffe2_mm: float) -> float:
    """L ancoraggio gancio staffa (K62)."""
    return 10.0 * max(diametro_staffe1_mm, diametro_staffe2_mm)


def taglio_capacity_design_kN(
    mrb_kNm: float, mrc_kNm: float, classe: ClasseDuttilita, *, lt_m: float, legacy_compat: bool = False
) -> float:
    """VEd,max (K81).

    `legacy_compat=True` reproduces the sheet's `K81` exactly: it returns
    `γRd·MRb·min(1,MRc/MRb)`, a MOMENT in kNm mislabeled/compared as a force in kN (`Lt`, K80, is
    a validated input never referenced by K81) — see docs/divergences/ca-travi.md item 5.

    `legacy_compat=False` implements NTC2018 §7.4.4.1.1's amplified capacity-design shear:
    VEd = (Mi,d + Mj,d)/Lt, with Mi,d = Mj,d = γRd·MRb·min(1,ΣMRc/ΣMRb) (the sheet supplies a
    single beam moment capacity for both ends, so both end moments use the same MRb/MRc pair).
    """
    momento_amplificato_kNm = GAMMA_RD_CAPACITY[classe] * mrb_kNm * min(1.0, mrc_kNm / mrb_kNm)
    if legacy_compat:
        return momento_amplificato_kNm
    return 2.0 * momento_amplificato_kNm / lt_m


def dettagli_costruttivi(
    *,
    h_mm: float,
    d_mm: float,
    classe: ClasseDuttilita,
    diametro_staffe1_mm: float,
    diametro_staffe2_mm: float,
    n_bracci_staffe2: int,
    diametro_ferri1_mm: float,
    n_ferri1: int,
    diametro_ferri2_mm: float,
    n_ferri2: int,
    mrb_kNm: float,
    mrc_kNm: float,
    lt_m: float,
    legacy_compat: bool = False,
) -> CapacityDesignOutput:
    return CapacityDesignOutput(
        lunghezza_critica_mm=lunghezza_critica_mm(h_mm, classe),
        passo_max_zona_critica_mm=passo_max_zona_critica_mm(
            h_mm=h_mm,
            d_mm=d_mm,
            classe=classe,
            diametro_staffe1_mm=diametro_staffe1_mm,
            diametro_staffe2_mm=diametro_staffe2_mm,
            n_bracci_staffe2=n_bracci_staffe2,
            diametro_ferri1_mm=diametro_ferri1_mm,
            n_ferri1=n_ferri1,
            diametro_ferri2_mm=diametro_ferri2_mm,
            n_ferri2=n_ferri2,
            legacy_compat=legacy_compat,
        ),
        lunghezza_ancoraggio_mm=lunghezza_ancoraggio_mm(diametro_staffe1_mm, diametro_staffe2_mm),
        ved_max_kN=taglio_capacity_design_kN(mrb_kNm, mrc_kNm, classe, lt_m=lt_m, legacy_compat=legacy_compat),
    )
