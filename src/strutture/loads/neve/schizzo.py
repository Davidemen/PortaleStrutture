"""Live element sketches for `neve-carico-falda` and `neve-accumulo` (docs/ui/WORKBENCH_SPEC.md
§7). Pure functions of the validated inputs + outputs; a drawing failure must never fail the
calculation (guarded in `tool.py`)."""
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

SEMILUCE_M = 3.0  # semiluce orizzontale illustrativa: il tool non ha un input di luce, solo angoli
_ALTEZZA_COLMO_M = 2.0  # quota illustrativa del colmo, solo per tenere la "tenda" sopra y=0
LARGHEZZA_MURO_M = 0.3  # spessore illustrativo del muro/salto di quota, non è un input reale
ALTEZZA_TRIANGOLO_FATTORE = 0.5  # frazione illustrativa di h per il vertice del triangolo di accumulo
_QUOTA_OFFSET_M = 0.5  # scostamento illustrativo della linea di quota sotto la falda inferiore


def _pitch(p1: Punto, p2: Punto, mu: float, qs: float, qsk: float) -> tuple[Linea, Diagramma, Etichetta]:
    """Linea di falda tra `p1` e `p2` + diagramma di carico uniforme `qs` + etichetta μ·qsk."""
    punto_medio = ((p1[0] + p2[0]) / 2.0, (p1[1] + p2[1]) / 2.0)
    testo = f"μ={mu:.2f} · qsk={qsk:.2f} kN/m²".replace(".", ",")
    return (
        Linea(p1=p1, p2=p2, stile="calcestruzzo"),
        Diagramma(base=(p1, p2), valori=(qs, qs), etichette=(etichetta_quota("q_s", qs, "kN/m²"),), stile="pressione"),
        Etichetta(punto=punto_medio, simbolo="μ·q_sk", testo=testo, stile="asse"),
    )


def disegna_carico_falda(inputs: CaricoFaldaInput, output: CaricoFaldaOutput) -> Sketch:
    """Sezione della copertura: una falda, due falde, o entrambe se entrambi i blocchi di output
    sono valorizzati (es. legacy_compat con tutti i campi presenti)."""
    forme: list[Linea | Diagramma | Etichetta] = []
    if output.qs is not None:
        assert inputs.a is not None  # garantito da run_carico_falda quando qs è valorizzato
        eave: Punto = (0.0, 0.0)
        ridge: Punto = (SEMILUCE_M, SEMILUCE_M * tan(radians(inputs.a)))
        forme.extend(_pitch(eave, ridge, output.mu, output.qs, output.qsk))
    if output.qs1 is not None and output.qs2 is not None:
        assert inputs.a1 is not None and inputs.a2 is not None  # garantito da run_carico_falda
        colmo: Punto = (0.0, _ALTEZZA_COLMO_M)
        gronda1: Punto = (-SEMILUCE_M, _ALTEZZA_COLMO_M - SEMILUCE_M * tan(radians(inputs.a1)))
        gronda2: Punto = (SEMILUCE_M, _ALTEZZA_COLMO_M - SEMILUCE_M * tan(radians(inputs.a2)))
        forme.extend(_pitch(colmo, gronda1, output.mu1, output.qs1, output.qsk))
        forme.extend(_pitch(colmo, gronda2, output.mu2, output.qs2, output.qsk))
    return Sketch(viste=(Vista(titolo="Sezione copertura", forme=tuple(forme)),))


def disegna_accumulo(inputs: AccumuloInput, output: AccumuloOutput) -> Sketch:
    """Sezione: muro/salto di quota, falda inferiore, triangolo di accumulo su `ls_final`."""
    vertice_y = min(inputs.h, ALTEZZA_TRIANGOLO_FATTORE * inputs.h)
    forme = (
        Rettangolo(x=0.0, y=0.0, w=LARGHEZZA_MURO_M, h=inputs.h, stile="calcestruzzo"),
        Linea(p1=(LARGHEZZA_MURO_M, 0.0), p2=(LARGHEZZA_MURO_M + inputs.b2, 0.0), stile="calcestruzzo"),
        Poligono(
            punti=(
                (LARGHEZZA_MURO_M, 0.0),
                (LARGHEZZA_MURO_M, vertice_y),
                (LARGHEZZA_MURO_M + output.ls_final, 0.0),
            ),
            stile="pressione",
        ),
        Quota(
            p1=(LARGHEZZA_MURO_M, 0.0), p2=(LARGHEZZA_MURO_M + output.ls_final, 0.0),
            distanza=-_QUOTA_OFFSET_M, testo=etichetta_quota("l_s", output.ls_final, "m"),
        ),
        Etichetta(punto=(LARGHEZZA_MURO_M, vertice_y), simbolo="q_s2",
                  testo=etichetta_quota("q_s2", output.qs2_final, "kN/m²")),
    )
    return Sketch(viste=(Vista(titolo="Sezione copertura", forme=forme),))
