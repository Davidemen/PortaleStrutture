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
_ALTEZZA_COLMO_M = RISALITA_MAX_M  # quota illustrativa del colmo, sopra la risalita massima di una falda
_OFFSET_ETICHETTA_MU_M = 0.35  # scostamento verticale dell'etichetta μ sopra la linea di falda


def _risalita_m(angolo_deg: float) -> float:
    """Risalita della falda su `SEMILUCE_M`, con un tetto schematico per angoli molto ripidi."""
    return min(SEMILUCE_M * tan(radians(angolo_deg)), RISALITA_MAX_M)


def _pitch(p1: Punto, p2: Punto, simbolo_mu: str, mu: float, qs: float, qsk: float) -> tuple[Linea, Diagramma, Etichetta]:
    """Linea di falda tra `p1` e `p2` + diagramma di carico uniforme `qs` (etichettato al colmo,
    l'estremo alto) + etichetta del coefficiente di forma μ a centro falda."""
    punto_medio = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0 + _OFFSET_ETICHETTA_MU_M)
    numero_mu = f"{mu:.2f}".replace(".", ",")
    return (
        Linea(p1=p1, p2=p2, stile="calcestruzzo"),
        Diagramma(base=(p1, p2), valori=(qs, qs), etichette=(etichetta_quota("q_s", qs, "kN/m²"),), stile="pressione"),
        Etichetta(punto=punto_medio, simbolo=simbolo_mu, testo=numero_mu, ancora="middle", stile="asse"),
    )


def disegna_carico_falda(inputs: CaricoFaldaInput, output: CaricoFaldaOutput) -> Sketch:
    """Sezione della copertura: una falda, due falde, o entrambe se entrambi i blocchi di output
    sono valorizzati (es. legacy_compat con tutti i campi presenti)."""
    forme: list[Linea | Diagramma | Etichetta] = []
    if output.qs is not None:
        assert inputs.a is not None  # garantito da run_carico_falda quando qs è valorizzato
        eave: Punto = (0.0, 0.0)
        ridge: Punto = (SEMILUCE_M, _risalita_m(inputs.a))
        forme.extend(_pitch(eave, ridge, "μ", output.mu, output.qs, output.qsk))
    if output.qs1 is not None and output.qs2 is not None:
        assert inputs.a1 is not None and inputs.a2 is not None  # garantito da run_carico_falda
        colmo: Punto = (0.0, _ALTEZZA_COLMO_M)
        gronda1: Punto = (-SEMILUCE_M, _ALTEZZA_COLMO_M - _risalita_m(inputs.a1))
        gronda2: Punto = (SEMILUCE_M, _ALTEZZA_COLMO_M - _risalita_m(inputs.a2))
        forme.extend(_pitch(colmo, gronda1, "μ_1", output.mu1, output.qs1, output.qsk))
        forme.extend(_pitch(colmo, gronda2, "μ_2", output.mu2, output.qs2, output.qsk))
    return Sketch(viste=(Vista(titolo="Sezione copertura", forme=tuple(forme)),), nota=NOTA_SCHEMA)


# --- neve-accumulo --------------------------------------------------------------------------------
_LARGHEZZA_EDIFICIO_SU_LS = 0.35  # larghezza schematica dell'edificio più alto, proporzionale a ls
_CROP_SU_LS = 1.4  # falda inferiore ritagliata a ~1.4·ls, poi tratto "fantasma"
_FANTASMA_SU_CROP = 0.15  # lunghezza del tratto fantasma, frazione del tratto ritagliato
_ASPETTO_MAX = 3.0  # margine sotto il limite 3.5:1 del lint, per l'altezza minima disegnata dell'edificio
_CARICO_SU_ALTEZZA = 0.35  # altezza massima del profilo di carico, frazione dell'altezza disegnata
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
    etichetta_picco = Etichetta(
        punto=(0.0, picco_m), simbolo="q_s2", testo=f"{output.qs2_final:.2f}".replace(".", ",") + " kN/m²",
        ancora="start", stile="asse",
    )
    etichetta_uniforme = Etichetta(
        punto=(crop_m, uniforme_m), simbolo="q_s1", testo=f"{output.qs1_final:.2f}".replace(".", ",") + " kN/m²",
        ancora="end", stile="asse",
    )
    forme = (edificio, falda, fantasma, profilo_carico, quota_h, quota_ls, etichetta_picco, etichetta_uniforme)
    return Sketch(viste=(Vista(titolo="Sezione copertura", forme=forme),), nota=NOTA_SCHEMA)
