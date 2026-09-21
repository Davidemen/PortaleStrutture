"""Live sketches for `neve-carico-falda` and `neve-accumulo` (docs/ui/WORKBENCH_SPEC.md §7,
COMPOSITION RULES in shared/sketch.py): the "Sezione copertura" view follows the inputs, stays
readable (no slivers, no overlapping texts, bounded aspect ratio) across several realistic input
sets, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

from strutture.loads.neve import schizzo as schizzo_module
from strutture.loads.neve.models import AccumuloInput, AccumuloOutput, CaricoFaldaInput, CaricoFaldaOutput
from strutture.loads.neve.schizzo import disegna_accumulo, disegna_carico_falda
from strutture.loads.neve.tool import TOOLS, run_accumulo, run_carico_falda
from strutture.shared.sketch import etichetta_quota
from strutture.shared.tool import execute

TOOL_FALDA = next(t for t in TOOLS if t.name == "neve-carico-falda")
TOOL_ACCUMULO = next(t for t in TOOLS if t.name == "neve-accumulo")


def _output_falda(overrides: dict) -> tuple[CaricoFaldaInput, CaricoFaldaOutput]:
    inputs = CaricoFaldaInput.model_validate({**TOOL_FALDA.example, **overrides})
    report = run_carico_falda(inputs)
    assert report.ok, report.errors
    return inputs, report.data


def _output_accumulo(overrides: dict) -> tuple[AccumuloInput, AccumuloOutput]:
    inputs = AccumuloInput.model_validate({**TOOL_ACCUMULO.example, **overrides})
    report = run_accumulo(inputs)
    assert report.ok, report.errors
    return inputs, report.data


def _no_lint_problems(sketch) -> None:
    problems = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problems == [], problems


@pytest.mark.unit
def test_falda_esempio_una_falda_disegna_una_sola_falda() -> None:
    """L'esempio ha `tipo_copertura="Copertura ad una falda"` (con a1/parapetto1/a2/parapetto2
    comunque presenti): solo la falda singola deve comparire."""
    inputs, output = _output_falda({})
    assert output.qs is not None and output.qs1 is None and output.qs2 is None
    sketch = disegna_carico_falda(inputs, output)
    assert [v.titolo for v in sketch.viste] == ["Sezione copertura"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("line") == 2  # falda + richiamo verticale al blocco di carico
    assert kinds.count("diagram") == 1
    assert kinds.count("label") == 2  # μ e α
    assert sketch.nota != ""


@pytest.mark.unit
def test_falda_due_falde_disegna_entrambe_le_falde() -> None:
    """Stesso set di campi dell'esempio, ma con `tipo_copertura="Copertura a due falde"`: ora
    devono comparire le due falde, non quella singola."""
    inputs, output = _output_falda({"tipo_copertura": "Copertura a due falde"})
    assert output.qs is None and output.qs1 is not None and output.qs2 is not None
    sketch = disegna_carico_falda(inputs, output)
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("line") == 3  # 2 falde + un richiamo condiviso al colmo
    assert kinds.count("diagram") == 2
    assert kinds.count("label") == 4  # μ_1, μ_2, α_1, α_2


@pytest.mark.unit
def test_falda_legacy_compat_disegna_entrambi_i_blocchi_insieme() -> None:
    """Sotto `legacy_compat=True` il foglio valorizza sempre entrambi i blocchi: lo schizzo li
    disegna entrambi nella stessa vista, senza scartarne uno."""
    inputs, output = _output_falda({"legacy_compat": True})
    assert output.qs is not None and output.qs1 is not None and output.qs2 is not None
    sketch = disegna_carico_falda(inputs, output)
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("line") == 5  # (falda+richiamo) singola + (2 falde+richiamo condiviso) doppia
    assert kinds.count("diagram") == 3


@pytest.mark.unit
def test_falda_diagramma_riporta_qs_e_letichetta_mu_e_solo_il_valore() -> None:
    inputs, output = _output_falda({})
    sketch = disegna_carico_falda(inputs, output)
    diagramma = next(f for f in sketch.viste[0].forme if f.kind == "diagram")
    assert diagramma.valori == pytest.approx((output.qs, output.qs))
    assert diagramma.etichette[0].startswith("q_s =")

    etichetta = next(f for f in sketch.viste[0].forme if f.kind == "label")
    assert etichetta.simbolo == "μ"
    assert etichetta.testo == f"{output.mu:.2f}".replace(".", ",")
    assert "," in etichetta.testo


@pytest.mark.unit
def test_falda_geometria_segue_langolo_e_la_risalita_e_limitata() -> None:
    """Un angolo molto ripido non fa esplodere l'altezza disegnata (schema, non scala); un angolo
    nullo non produce una falda piatta (sliver): la risalita minima è il 15% della semiluce."""
    inputs_piatta, output_piatta = _output_falda({"a": 0})
    inputs_ripida, output_ripida = _output_falda({"a": 89})
    linea_piatta = disegna_carico_falda(inputs_piatta, output_piatta).viste[0].forme[0]
    linea_ripida = disegna_carico_falda(inputs_ripida, output_ripida).viste[0].forme[0]
    risalita_minima = schizzo_module._RISALITA_MIN_FRAZIONE * schizzo_module.SEMILUCE_M
    assert linea_piatta.p2[1] == pytest.approx(risalita_minima)
    assert risalita_minima <= linea_ripida.p2[1] <= schizzo_module.RISALITA_MAX_M + 1e-9


@pytest.mark.unit
@pytest.mark.parametrize(
    "overrides",
    [
        {},  # esempio: una falda piatta + campi due falde presenti ma non mostrati
        {"tipo_copertura": "Copertura a due falde"},
        {"tipo_copertura": "Copertura a due falde", "a1": 5, "a2": 55},  # falde molto asimmetriche
        {"a": 60},  # falda singola ripida
        {"legacy_compat": True},  # entrambi i blocchi insieme
    ],
)
def test_falda_esempi_realistici_non_hanno_problemi_di_layout(overrides: dict) -> None:
    inputs, output = _output_falda(overrides)
    _no_lint_problems(disegna_carico_falda(inputs, output))


@pytest.mark.unit
def test_accumulo_vista_e_forme_esempio() -> None:
    inputs, output = _output_accumulo({})
    sketch = disegna_accumulo(inputs, output)
    assert [v.titolo for v in sketch.viste] == ["Sezione copertura"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("rect") == 1
    assert kinds.count("line") == 2  # falda + tratto fantasma
    assert kinds.count("polygon") == 1
    assert kinds.count("dimension") == 2  # h, l_s
    assert kinds.count("label") == 2  # q_s2 al picco, q_s1 all'estremo
    assert sketch.nota != ""


@pytest.mark.unit
def test_accumulo_geometria_segue_h() -> None:
    """Cambiando `h` cambia l'altezza dell'edificio disegnato e la quota `h`."""
    inputs_a, output_a = _output_accumulo({"h": 6.0})
    inputs_b, output_b = _output_accumulo({"h": 30.0})
    sketch_a = disegna_accumulo(inputs_a, output_a)
    sketch_b = disegna_accumulo(inputs_b, output_b)

    edificio_a = sketch_a.viste[0].forme[0]
    edificio_b = sketch_b.viste[0].forme[0]
    assert edificio_a.kind == "rect" and edificio_b.kind == "rect"
    # h=30 è ben oltre il minimo per aspetto: l'altezza disegnata segue h esattamente.
    assert edificio_b.h == pytest.approx(30.0)

    quota_h_a = next(f for f in sketch_a.viste[0].forme if f.kind == "dimension" and f.testo.startswith("h ="))
    quota_h_b = next(f for f in sketch_b.viste[0].forme if f.kind == "dimension" and f.testo.startswith("h ="))
    assert quota_h_a.testo != quota_h_b.testo
    assert quota_h_a.testo == etichetta_quota("h", 6.0, "m")
    assert quota_h_b.testo == etichetta_quota("h", 30.0, "m")


@pytest.mark.unit
def test_accumulo_altezza_disegnata_ha_un_minimo_per_laspetto() -> None:
    """Con `h` molto piccolo (e `ls` al minimo di 5 m) l'edificio disegnato non collassa in uno
    sliver: la vista resta entro l'aspetto massimo anche se il muro reale è più basso."""
    inputs, output = _output_accumulo({"h": 0.5})
    sketch = disegna_accumulo(inputs, output)
    edificio = sketch.viste[0].forme[0]
    assert edificio.h > 0.5  # altezza disegnata rialzata rispetto al vero h=0.5 m
    # la quota riporta comunque il vero valore di input, non quello disegnato
    quota_h = next(f for f in sketch.viste[0].forme if f.kind == "dimension" and f.testo.startswith("h ="))
    assert quota_h.testo == etichetta_quota("h", 0.5, "m")


@pytest.mark.unit
def test_accumulo_falda_ritagliata_a_1_4_ls_con_tratto_fantasma() -> None:
    """La falda inferiore (potenzialmente lunga decine di metri, `b2`) è ritagliata a ~1.4·ls,
    non disegnata alla sua vera lunghezza; un tratto tratteggiato "fantasma" la continua."""
    inputs, output = _output_accumulo({"b2": 40.0})
    sketch = disegna_accumulo(inputs, output)
    falda = next(f for f in sketch.viste[0].forme if f.kind == "line" and f.stile == "calcestruzzo")
    fantasma = next(f for f in sketch.viste[0].forme if f.kind == "line" and f.stile == "fantasma")
    assert falda.p2[0] == pytest.approx(schizzo_module._CROP_SU_LS * output.ls_final)
    assert falda.p2[0] < inputs.b2  # ritagliata, non la vera larghezza
    assert fantasma.tratteggio is True
    assert fantasma.p1[0] == pytest.approx(falda.p2[0])


@pytest.mark.unit
def test_accumulo_profilo_di_carico_riporta_i_picchi_a_qs2_e_qs1() -> None:
    inputs, output = _output_accumulo({})
    sketch = disegna_accumulo(inputs, output)
    poligono = next(f for f in sketch.viste[0].forme if f.kind == "polygon")
    assert poligono.punti[0] == pytest.approx((0.0, 0.0))
    picco_su_muro = poligono.punti[1][1]
    valore_a_ls = poligono.punti[2][1]
    assert picco_su_muro > valore_a_ls >= 0.0  # q_s2 (al muro) > q_s1 (a ls), coerente col calcolo

    quota_ls = next(f for f in sketch.viste[0].forme if f.kind == "dimension" and f.testo.startswith("l_s ="))
    assert quota_ls.testo == etichetta_quota("l_s", output.ls_final, "m")

    picco = next(f for f in sketch.viste[0].forme if f.kind == "label" and f.simbolo == "q_s2")
    uniforme = next(f for f in sketch.viste[0].forme if f.kind == "label" and f.simbolo == "q_s1")
    assert picco.testo == f"{output.qs2_final:.2f}".replace(".", ",") + " kN/m²"
    assert uniforme.testo == f"{output.qs1_final:.2f}".replace(".", ",") + " kN/m²"


@pytest.mark.unit
@pytest.mark.parametrize(
    "overrides",
    [
        {},  # esempio
        {"h": 2.0, "b2": 60.0},  # muro basso, falda molto lunga (ls al minimo)
        {"h": 25.0, "b1": 50.0, "b2": 45.0},  # muro molto alto (ls al massimo)
        {"m1_input": 0.1, "msup": 0.1},  # carico di accumulo modesto
    ],
)
def test_accumulo_esempi_realistici_non_hanno_problemi_di_layout(overrides: dict) -> None:
    inputs, output = _output_accumulo(overrides)
    _no_lint_problems(disegna_accumulo(inputs, output))


@pytest.mark.unit
def test_esempio_falda_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(TOOL_FALDA, TOOL_FALDA.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert len(report.data.schizzo.viste) == 1
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_esempio_accumulo_ha_schizzo_e_gira_in_meno_di_300ms() -> None:
    inizio = time.perf_counter()
    report = execute(TOOL_ACCUMULO, TOOL_ACCUMULO.example)
    durata = time.perf_counter() - inizio
    assert report.ok, report.errors
    assert report.data.schizzo is not None
    assert len(report.data.schizzo.viste) == 1
    assert durata < 0.3, f"esempio in {durata:.3f}s"


@pytest.mark.unit
def test_errore_nel_disegno_falda_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.loads.neve.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo_falda", _rompi)
    report = execute(TOOL_FALDA, TOOL_FALDA.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_errore_nel_disegno_accumulo_non_fa_fallire_il_calcolo(monkeypatch: pytest.MonkeyPatch) -> None:
    """Un'eccezione nello schizzo deve essere loggata e assorbita: il calcolo resta valido."""
    import strutture.loads.neve.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo_accumulo", _rompi)
    report = execute(TOOL_ACCUMULO, TOOL_ACCUMULO.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    """Il modulo non tocca I/O: verifica solo che sia importabile senza effetti collaterali."""
    assert hasattr(schizzo_module, "disegna_carico_falda")
    assert hasattr(schizzo_module, "disegna_accumulo")


@pytest.mark.unit
def test_accumulo_etichette_staccate_dal_profilo_di_carico() -> None:
    """q_s2 e q_s1 non poggiano sul contorno del profilo di carico: la base del testo sta SOPRA il
    proprio vertice (il testo cresce verso l'alto dal suo punto), e q_s2 parte scostato dalla parete
    — sul vertice stesso il testo veniva tagliato dal lato inclinato del triangolo di accumulo."""
    inputs, output = _output_accumulo({})
    forme = disegna_accumulo(inputs, output).viste[0].forme
    profilo = next(f for f in forme if f.kind == "polygon")
    picco = max(y for _, y in profilo.punti)
    uniforme = profilo.punti[3][1]
    q_s2 = next(f for f in forme if f.kind == "label" and f.simbolo == "q_s2")
    q_s1 = next(f for f in forme if f.kind == "label" and f.simbolo == "q_s1")

    assert q_s2.punto[0] > 0.0 and q_s2.punto[1] > picco
    assert q_s1.punto[1] > uniforme
    assert q_s2.ancora == "start" and q_s1.ancora == "end"
