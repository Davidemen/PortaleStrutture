"""Live element sketches for `neve-carico-falda` and `neve-accumulo` (docs/ui/WORKBENCH_SPEC.md
§7, COMPOSITION RULES in shared/sketch.py). Both are schemas, not scale drawings: neither tool has
a real span/width input, so geometry is illustrative and `Sketch.nota` says so. Pure functions of
the validated inputs + outputs; a drawing failure must never fail the calculation (guarded in
`tool.py`)."""
from math import radians, tan

from strutture.shared.sketch import (
    Diagramma,
    Etichetta,
    Linea,
    Poligono,
    Punto,
    Quota,
    Rettangolo,
    Sketch,
    Vista,
    etichetta_quota,
)

from .models import AccumuloInput, AccumuloOutput, CaricoFaldaInput, CaricoFaldaOutput

NOTA_SCHEMA = "Schema non in scala."

# --- neve-carico-falda ---------------------------------------------------------------------------
SEMILUCE_M = 3.0  # semiluce orizzontale illustrativa: il tool non ha un input di luce, solo angoli
RISALITA_MAX_M = 1.5 * SEMILUCE_M  # tetto schematico alla risalita, per angoli molto ripidi (schema)
_RISALITA_MIN_FRAZIONE = 0.15  # risalita minima schematica, frazione della semiluce (mai una falda piatta)
_ALTEZZA_COLMO_M = RISALITA_MAX_M  # quota illustrativa del colmo, sopra la risalita massima di una falda
_OFFSET_ETICHETTA_MU_M = 0.35  # scostamento verticale dell'etichetta μ sopra la linea di falda
_GAP_CARICO_M = 0.6  # distanza verticale tra il colmo/la gronda alta e il blocco di carico
_OFFSET_ETICHETTA_ALFA_M = 0.15  # scostamento dell'etichetta α dalla gronda


def _risalita_m(angolo_deg: float) -> float:
    """Risalita della falda su `SEMILUCE_M`: mai una falda piatta (minimo il 15% della semiluce,
    una sliver visiva anche per α=0°) né, per angoli molto ripidi, oltre un tetto schematico."""
    risalita = SEMILUCE_M * tan(radians(angolo_deg))
    return min(max(risalita, _RISALITA_MIN_FRAZIONE * SEMILUCE_M), RISALITA_MAX_M)


def _blocco_carico(colmo_x_m: float, gronda_x_m: float, y_base_m: float, simbolo_q: str, qs: float) -> Diagramma:
    """Il carico neve è verticale per unità di superficie in pianta: un blocco su base ORIZZONTALE
    sopra il colmo, con ordinate verticali (non normali alla falda, che leggerebbero come vento)."""
    x0_m, x1_m = (gronda_x_m, colmo_x_m) if gronda_x_m < colmo_x_m else (colmo_x_m, gronda_x_m)
    return Diagramma(
        base=((x0_m, y_base_m), (x1_m, y_base_m)), valori=(qs, qs),
        etichette=(etichetta_quota(simbolo_q, qs, "kN/m²"),), stile="pressione",
    )


def _etichetta_mu(colmo: Punto, gronda: Punto, simbolo: str, mu: float) -> Etichetta:
    punto_medio = ((colmo[0] + gronda[0]) / 2.0, (colmo[1] + gronda[1]) / 2.0 + _OFFSET_ETICHETTA_MU_M)
    return Etichetta(punto=punto_medio, simbolo=simbolo, testo=f"{mu:.2f}".replace(".", ","), ancora="middle", stile="asse")


def _etichetta_alfa(gronda: Punto, simbolo: str, angolo_deg: float) -> Etichetta:
    """Angolo di falda α, etichettato vicino alla gronda (regola 6: le grandezze si etichettano
    dove sono più leggibili, non impilate sul carico)."""
    punto = (gronda[0], gronda[1] + _OFFSET_ETICHETTA_ALFA_M)
    return Etichetta(punto=punto, simbolo=simbolo, testo=f"{angolo_deg:.0f}°", ancora="middle", stile="asse")


def disegna_carico_falda(inputs: CaricoFaldaInput, output: CaricoFaldaOutput) -> Sketch:
    """Sezione della copertura: una falda, due falde, o entrambe se entrambi i blocchi di output
    sono valorizzati (es. legacy_compat con tutti i campi presenti)."""
    forme: list[Linea | Diagramma | Etichetta] = []
    if output.qs is not None:
        assert inputs.a is not None  # garantito da run_carico_falda quando qs è valorizzato
        eave: Punto = (0.0, 0.0)
        ridge: Punto = (SEMILUCE_M, _risalita_m(inputs.a))
        y_base_m = ridge[1] + _GAP_CARICO_M
        forme.append(Linea(p1=eave, p2=ridge, stile="calcestruzzo"))
        # linea di richiamo dal colmo al blocco di carico: collega visivamente il carico alla
        # falda a cui si applica, e porta l'estensione verticale del blocco nell'ingombro disegnato.
        forme.append(Linea(p1=ridge, p2=(ridge[0], y_base_m), stile="quota", tratteggio=True))
        forme.append(_blocco_carico(ridge[0], eave[0], y_base_m, "q_s", output.qs))
        forme.append(_etichetta_mu(ridge, eave, "μ", output.mu))
        forme.append(_etichetta_alfa(eave, "α", inputs.a))
    if output.qs1 is not None and output.qs2 is not None:
        assert inputs.a1 is not None and inputs.a2 is not None  # garantito da run_carico_falda
        colmo: Punto = (0.0, _ALTEZZA_COLMO_M)
        gronda1: Punto = (-SEMILUCE_M, _ALTEZZA_COLMO_M - _risalita_m(inputs.a1))
        gronda2: Punto = (SEMILUCE_M, _ALTEZZA_COLMO_M - _risalita_m(inputs.a2))
        y_base_m = colmo[1] + _GAP_CARICO_M
        forme.append(Linea(p1=colmo, p2=gronda1, stile="calcestruzzo"))
        forme.append(Linea(p1=colmo, p2=gronda2, stile="calcestruzzo"))
        forme.append(Linea(p1=colmo, p2=(colmo[0], y_base_m), stile="quota", tratteggio=True))
        forme.append(_blocco_carico(colmo[0], gronda1[0], y_base_m, "q_s1", output.qs1))
        forme.append(_blocco_carico(colmo[0], gronda2[0], y_base_m, "q_s2", output.qs2))
        forme.append(_etichetta_mu(colmo, gronda1, "μ_1", output.mu1))
        forme.append(_etichetta_mu(colmo, gronda2, "μ_2", output.mu2))
        forme.append(_etichetta_alfa(gronda1, "α_1", inputs.a1))
        forme.append(_etichetta_alfa(gronda2, "α_2", inputs.a2))
    return Sketch(viste=(Vista(titolo="Sezione copertura", forme=tuple(forme)),), nota=NOTA_SCHEMA)


# --- neve-accumulo --------------------------------------------------------------------------------
_LARGHEZZA_EDIFICIO_SU_LS = 0.35  # larghezza schematica dell'edificio più alto, proporzionale a ls
_CROP_SU_LS = 1.4  # falda inferiore ritagliata a ~1.4·ls, poi tratto "fantasma"
_FANTASMA_SU_CROP = 0.15  # lunghezza del tratto fantasma, frazione del tratto ritagliato
_ASPETTO_MAX = 3.0  # margine sotto il limite 3.5:1 del lint, per l'altezza minima disegnata dell'edificio
_CARICO_SU_ALTEZZA = 0.35  # altezza massima del profilo di carico, frazione dell'altezza disegnata
_STACCO_ETICHETTA_FRAZIONE = 0.05  # stacco delle etichette q_s dal profilo di carico, frazione dell'altezza disegnata
_OFFSET_QUOTA_FRAZIONE = 0.07  # scostamento delle quote, frazione del lato maggiore della vista (regola 3)


def _altezza_edificio_disegnata_m(h_m: float, larghezza_vista_m: float) -> float:
    """Altezza minima disegnata dell'edificio, per non superare l'aspetto massimo della vista."""
    return max(h_m, larghezza_vista_m / _ASPETTO_MAX)


def disegna_accumulo(inputs: AccumuloInput, output: AccumuloOutput) -> Sketch:
    """Sezione: edificio più alto (a sinistra), falda inferiore ritagliata a ~1.4·ls con
    continuazione "fantasma", profilo di carico (triangolo di accumulo + tratto uniforme oltre `ls`)."""
    ls_m = output.ls_final
    larghezza_edificio_m = _LARGHEZZA_EDIFICIO_SU_LS * ls_m
    crop_m = _CROP_SU_LS * ls_m
    fantasma_m = _FANTASMA_SU_CROP * crop_m
    larghezza_vista_m = larghezza_edificio_m + crop_m
    altezza_m = _altezza_edificio_disegnata_m(inputs.h, larghezza_vista_m)
    scostamento_m = _OFFSET_QUOTA_FRAZIONE * max(larghezza_vista_m, altezza_m)

    picco_m = _CARICO_SU_ALTEZZA * altezza_m
    uniforme_m = picco_m * (output.qs1_final / output.qs2_final) if output.qs2_final > 0 else 0.0

    edificio = Rettangolo(x=-larghezza_edificio_m, y=0.0, w=larghezza_edificio_m, h=altezza_m, stile="calcestruzzo")
    falda = Linea(p1=(0.0, 0.0), p2=(crop_m, 0.0), stile="calcestruzzo")
    fantasma = Linea(p1=(crop_m, 0.0), p2=(crop_m + fantasma_m, 0.0), stile="fantasma", tratteggio=True)
    profilo_carico = Poligono(
        punti=((0.0, 0.0), (0.0, picco_m), (ls_m, uniforme_m), (crop_m, uniforme_m), (crop_m, 0.0)),
        stile="pressione",
    )
    quota_h = Quota(
        p1=(-larghezza_edificio_m, 0.0), p2=(-larghezza_edificio_m, altezza_m), distanza=scostamento_m,
        testo=etichetta_quota("h", inputs.h, "m"),
    )
    quota_ls = Quota(
        p1=(0.0, 0.0), p2=(ls_m, 0.0), distanza=-scostamento_m, testo=etichetta_quota("l_s", ls_m, "m"),
    )
    # Le etichette stanno SOPRA il proprio vertice, staccate dal contorno (il testo cresce verso
    # l'alto dal suo punto): sul vertice stesso il lato inclinato del triangolo tagliava il testo.
    stacco_m = _STACCO_ETICHETTA_FRAZIONE * altezza_m
    etichetta_picco = Etichetta(
        punto=(stacco_m, picco_m + stacco_m), simbolo="q_s2", testo=f"{output.qs2_final:.2f}".replace(".", ",") + " kN/m²",
        ancora="start", stile="asse",
    )
    etichetta_uniforme = Etichetta(
        punto=(crop_m, uniforme_m + stacco_m), simbolo="q_s1", testo=f"{output.qs1_final:.2f}".replace(".", ",") + " kN/m²",
        ancora="end", stile="asse",
    )
    forme = (edificio, falda, fantasma, profilo_carico, quota_h, quota_ls, etichetta_picco, etichetta_uniforme)
    return Sketch(viste=(Vista(titolo="Sezione copertura", forme=forme),), nota=NOTA_SCHEMA)
