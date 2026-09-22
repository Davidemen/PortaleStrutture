"""Regole di validazione di `SezioneMnInput` (geometria e armatura): estratte in modulo a parte
per restare entro i 150 righe per modulo (regola dura 12); nessun cambiamento di comportamento
rispetto ai validator che prima vivevano dentro la classe."""
from .rows import BarraRow, VerticeRow

FORME_T_L = ("a_t", "a_l")
LAYOUT_CON_N_BARRE = ("fila_superiore", "fila_inferiore", "circolare")
LAYOUT_RETTANGOLARI_ARMATURA = ("fila_superiore", "fila_inferiore", "perimetrale")


def valida_geometria(
    *,
    forma: str,
    b_mm: float | None,
    h_mm: float | None,
    diametro_mm: float | None,
    bf_mm: float | None,
    hf_mm: float | None,
    bw_mm: float | None,
    lw_mm: float | None,
    tw_mm: float | None,
    le_mm: float | None,
    te_mm: float | None,
    vertici: tuple[VerticeRow, ...],
) -> None:
    if forma == "rettangolare" and (b_mm is None or h_mm is None):
        raise ValueError("sezione rettangolare: indicare base (b) e altezza (h)")
    if forma == "circolare" and diametro_mm is None:
        raise ValueError("sezione circolare: indicare il diametro")
    if forma in FORME_T_L and (bf_mm is None or hf_mm is None or bw_mm is None or h_mm is None):
        raise ValueError("sezione a T/a L: indicare bf, hf, bw e h")
    if forma == "parete" and (lw_mm is None or tw_mm is None or le_mm is None or te_mm is None):
        raise ValueError("parete: indicare lw, tw, le e te")
    if forma == "poligono_libero" and len(vertici) < 3:
        raise ValueError("il contorno poligonale libero deve avere almeno 3 vertici")


def valida_armatura(
    *,
    forma: str,
    armatura_modo: str,
    barre: tuple[BarraRow, ...],
    layout_tipo: str | None,
    layout_copriferro_mm: float | None,
    layout_diametro_mm: float | None,
    layout_n_barre: int | None,
    layout_n_per_lato: int | None,
    b_mm: float | None,
    h_mm: float | None,
    diametro_mm: float | None,
) -> None:
    if armatura_modo == "tabella" and len(barre) == 0:
        raise ValueError("specificare almeno una barra di armatura")
    if armatura_modo != "layout":
        return
    if layout_tipo is None or layout_copriferro_mm is None or layout_diametro_mm is None:
        raise ValueError("layout armatura: indicare tipo, copriferro e diametro")
    if layout_tipo in LAYOUT_CON_N_BARRE and layout_n_barre is None:
        raise ValueError(f"layout '{layout_tipo}': indicare il numero di barre")
    if layout_tipo == "perimetrale" and layout_n_per_lato is None:
        raise ValueError("layout 'perimetrale': indicare il numero di barre per lato")
    if layout_tipo in ("fila_superiore", "fila_inferiore", "perimetrale") and forma != "rettangolare":
        raise ValueError(f"il layout '{layout_tipo}' richiede una sezione rettangolare")
    if layout_tipo == "circolare" and forma != "circolare":
        raise ValueError("il layout 'circolare' richiede una sezione circolare")
    _valida_copriferro_layout(
        layout_tipo=layout_tipo, layout_copriferro_mm=layout_copriferro_mm, layout_diametro_mm=layout_diametro_mm,
        b_mm=b_mm, h_mm=h_mm, diametro_mm=diametro_mm,
    )


def _valida_copriferro_layout(
    *,
    layout_tipo: str,
    layout_copriferro_mm: float,
    layout_diametro_mm: float,
    b_mm: float | None,
    h_mm: float | None,
    diametro_mm: float | None,
) -> None:
    """Il copriferro netto più mezzo diametro non deve raggiungere il semilato (layout
    rettangolari) o il raggio (layout circolare), altrimenti le barre cadrebbero oltre l'asse di
    simmetria e la fila si "specchia" silenziosamente restando comunque interna al contorno
    (nessun errore veniva sollevato: copriferro fino a 200 mm era accettato indipendentemente da
    b/h/D)."""
    messaggio = "copriferro troppo grande per la sezione: le barre cadrebbero oltre l'asse"
    margine_mm = layout_copriferro_mm + layout_diametro_mm / 2.0
    rettangolare_pronta = layout_tipo in LAYOUT_RETTANGOLARI_ARMATURA and b_mm is not None and h_mm is not None
    if rettangolare_pronta and margine_mm >= min(b_mm, h_mm) / 2.0:  # type: ignore[arg-type]
        raise ValueError(messaggio)
    if layout_tipo == "circolare" and diametro_mm is not None and margine_mm >= diametro_mm / 2.0:
        raise ValueError(messaggio)
