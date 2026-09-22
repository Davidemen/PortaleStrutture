"""Live sketch for `acciaio-colonna-h-ec3` (docs/ui/WORKBENCH_SPEC.md §7, COMPOSITION RULES in
shared/sketch.py): the "Sezione" view follows the inputs, stays readable across several realistic
H/I proportions (no slivers, no overlapping texts), and a drawing failure must never fail the
calculation."""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

from strutture.members.acciaio_colonna_ec3 import schizzo as schizzo_module
from strutture.members.acciaio_colonna_ec3.models import ColonnaEc3Input
from strutture.members.acciaio_colonna_ec3.schizzo import disegna
from strutture.members.acciaio_colonna_ec3.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)

    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("rect") == 3
    assert kinds.count("line") == 2
    assert kinds.count("dimension") == 3  # h, b, t_f (t_w è un'etichetta, non una quota)
    assert kinds.count("label") == 3  # y, z, t_w


@pytest.mark.unit
def test_ali_e_anima_seguono_gli_input() -> None:
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)
    rettangoli = [f for f in sketch.viste[0].forme if f.kind == "rect"]
    ala_superiore, ala_inferiore, anima = rettangoli

    b_m, h_m = inputs.b_mm / 1000.0, inputs.h_mm / 1000.0
    tw_m, tf_m = inputs.tw_mm / 1000.0, inputs.tf_mm / 1000.0
    tw_dis, tf_dis = schizzo_module._spessori_disegnati_m(b_m, h_m, tw_m, tf_m)

    assert ala_superiore.x == pytest.approx(-b_m / 2)
    assert ala_superiore.y == pytest.approx(h_m / 2 - tf_dis)
    assert ala_superiore.w == pytest.approx(b_m)
    assert ala_superiore.h == pytest.approx(tf_dis)

    assert ala_inferiore.x == pytest.approx(-b_m / 2)
    assert ala_inferiore.y == pytest.approx(-h_m / 2)
    assert ala_inferiore.w == pytest.approx(b_m)
    assert ala_inferiore.h == pytest.approx(tf_dis)

    assert anima.x == pytest.approx(-tw_dis / 2)
    assert anima.y == pytest.approx(-h_m / 2 + tf_dis)
    assert anima.w == pytest.approx(tw_dis)
    assert anima.h == pytest.approx(h_m - 2 * tf_dis)


@pytest.mark.unit
def test_spessori_sottili_ricevono_uno_spessore_minimo_schematico() -> None:
    """L'anima (8 mm) e l'ala dell'esempio sono sotto il minimo schematico del 3 %: il rettangolo
    disegnato è più spesso del vero valore, ma le quote riportano sempre il valore vero (mm)."""
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)
    rettangoli = [f for f in sketch.viste[0].forme if f.kind == "rect"]
    ala_superiore, _, anima = rettangoli

    assert anima.w > inputs.tw_mm / 1000.0  # spessore disegnato > vero spessore dell'anima
    assert ala_superiore.h >= inputs.tf_mm / 1000.0  # spessore ala disegnato >= vero spessore

    etichetta_tw = next(f for f in sketch.viste[0].forme if f.kind == "label" and f.simbolo == "t_w")
    assert etichetta_tw.testo == "8 mm"  # il vero valore, non quello disegnato (regola 4: solo il valore)


@pytest.mark.unit
def test_assi_yy_zz_con_etichette() -> None:
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)
    linee = [f for f in sketch.viste[0].forme if f.kind == "line"]
    etichette = [f for f in sketch.viste[0].forme if f.kind == "label"]

    assert {e.simbolo for e in etichette} == {"y", "z", "t_w"}
    for linea in linee:
        assert linea.stile == "asse"
    for etichetta in etichette:
        assert etichetta.stile == "asse"
    # y-y è ancorata all'estremo sinistro (libero da h e t_w, entrambi a destra a mezzeria),
    # z-z all'estremo superiore (spostata lateralmente, libera da t_f): vedi il docstring del modulo.
    etichetta_y = next(e for e in etichette if e.simbolo == "y")
    etichetta_z = next(e for e in etichette if e.simbolo == "z")
    assert etichetta_y.ancora == "end"
    assert etichetta_z.ancora == "start"

    asse_yy = next(l for l in linee if l.p1[1] == pytest.approx(0.0) and l.p2[1] == pytest.approx(0.0))
    assert asse_yy.p1[0] == pytest.approx(-asse_yy.p2[0])
    asse_zz = next(l for l in linee if l.p1[0] == pytest.approx(0.0) and l.p2[0] == pytest.approx(0.0))
    assert asse_zz.p1[1] == pytest.approx(-asse_zz.p2[1])


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando h_mm le ali, l'anima e la quota h cambiano di conseguenza."""
    modificato = {**TOOL.example, "h_mm": 700}
    inputs = ColonnaEc3Input.model_validate(modificato)
    sketch = disegna(inputs)
    rettangoli = [f for f in sketch.viste[0].forme if f.kind == "rect"]
    ala_superiore, ala_inferiore, anima = rettangoli
    b_m, h_m, tf_m = inputs.b_mm / 1000.0, 700 / 1000.0, inputs.tf_mm / 1000.0
    _, tf_dis = schizzo_module._spessori_disegnati_m(b_m, h_m, inputs.tw_mm / 1000.0, tf_m)

    assert ala_superiore.y == pytest.approx(h_m / 2 - tf_dis)
    assert ala_inferiore.y == pytest.approx(-h_m / 2)
    assert anima.h == pytest.approx(h_m - 2 * tf_dis)

    quote = [f for f in sketch.viste[0].forme if f.kind == "dimension"]
    quota_h = next(q for q in quote if q.testo.startswith("h ="))
    assert quota_h.testo == "h = 700 mm"


@pytest.mark.unit
def test_quote_riportano_i_valori_corretti() -> None:
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)
    quote = {q.testo.split(" =")[0]: q.testo for q in sketch.viste[0].forme if q.kind == "dimension"}
    assert quote["h"] == "h = 500 mm"
    assert quote["b"] == "b = 280 mm"
    assert quote["t_f"] == "t_f = 12 mm"
    etichetta_tw = next(f for f in sketch.viste[0].forme if f.kind == "label" and f.simbolo == "t_w")
    assert etichetta_tw.testo == "8 mm"


@pytest.mark.unit
@pytest.mark.parametrize(
    "b_mm,h_mm,tw_mm,tf_mm",
    [
        (280, 500, 8, 12),  # esempio
        (300, 300, 11, 19),  # HEB300-ish: sezione tozza (b/h=1.0)
        (220, 600, 12, 19),  # IPE600-ish: sezione snella (b/h=0.37)
        (400, 1200, 12, 25),  # trave a doppio T saldata molto alta
        (100, 96, 5, 8),  # sezione piccola (HEA100-ish)
        (500, 300, 10, 16),  # sezione larga e bassa (b/h=1.67)
    ],
    ids=["esempio", "HEB300", "IPE600", "trave-alta", "HEA100", "larga-bassa"],
)
def test_sezioni_realistiche_non_hanno_problemi_di_layout(b_mm: float, h_mm: float, tw_mm: float, tf_mm: float) -> None:
    modificato = {**TOOL.example, "b_mm": b_mm, "h_mm": h_mm, "tw_mm": tw_mm, "tf_mm": tf_mm}
    inputs = ColonnaEc3Input.model_validate(modificato)
    sketch = disegna(inputs)
    problems = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problems == [], problems


@pytest.mark.unit
def test_etichetta_tw_e_ancorata_sullanima_non_una_quota() -> None:
    """Design review: t_w è un'etichetta (non una linea di quota) ancorata vicino all'anima, sul
    lato libero tra l'anima e la punta dell'ala; t_f resta invece una quota fuori dall'ala."""
    inputs = ColonnaEc3Input.model_validate(TOOL.example)
    sketch = disegna(inputs)
    b_m, tw_m = inputs.b_mm / 1000.0, inputs.tw_mm / 1000.0
    etichetta_tw = next(f for f in sketch.viste[0].forme if f.kind == "label" and f.simbolo == "t_w")
    assert 0.0 < etichetta_tw.punto[0] < b_m / 2.0  # tra l'anima e la punta dell'ala, non oltre
    assert etichetta_tw.punto[0] > tw_m / 2.0  # fuori dal rettangolo dell'anima stessa

    quota_tf = next(f for f in sketch.viste[0].forme if f.kind == "dimension" and f.testo.startswith("t_f"))
    assert quota_tf.p1[0] == pytest.approx(-b_m / 2)  # sul filo dell'ala sinistra
    assert quota_tf.distanza > 0  # spostata ulteriormente fuori dal profilo (a sinistra)


@pytest.mark.unit
def test_esempio_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(TOOL, TOOL.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert len(report.data.schizzo.viste) == 1
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_errore_nel_disegno_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.members.acciaio_colonna_ec3.compose as compose_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(compose_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")
