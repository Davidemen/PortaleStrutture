"""Live sketch for `acciaio-sezione-h-rimpiattata` (docs/ui/WORKBENCH_SPEC.md §7): the "Sezione"
view follows the inputs, and a drawing failure must never fail the calculation."""
import time

import pytest

from strutture.members.acciaio_sezione_composta import schizzo as schizzo_module
from strutture.members.acciaio_sezione_composta.baricentro import baricentro
from strutture.members.acciaio_sezione_composta.elementi import costruisci_elementi
from strutture.members.acciaio_sezione_composta.models import SezioneHRimpiattataInput
from strutture.members.acciaio_sezione_composta.schizzo import disegna
from strutture.members.acciaio_sezione_composta.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


def _elementi_e_baricentro(raw_inputs: dict):
    inputs = SezioneHRimpiattataInput.model_validate(raw_inputs)
    elementi = costruisci_elementi(inputs.h_profilo_mm, inputs.b_profilo_mm, inputs.tf_mm, inputs.tw_mm,
                                    inputs.piatti, legacy_compat=inputs.legacy_compat)
    x_n_mm, y_n_mm = baricentro(elementi, legacy_compat=inputs.legacy_compat)
    return inputs, elementi, x_n_mm, y_n_mm


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    """L'esempio aureo ha la seconda riga di piatti disattivata (b_mm=0): 3 elementi di profilo +
    1 piatto attivo = 4 rettangoli, 2 assi baricentrici, 1 marcatore."""
    inputs, elementi, x_n_mm, y_n_mm = _elementi_e_baricentro(TOOL.example)
    sketch = disegna(elementi, x_n_mm, y_n_mm, inputs.h_profilo_mm, inputs.b_profilo_mm)

    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds.count("rect") == 4
    assert kinds.count("line") == 2
    assert kinds.count("circle") == 1
    rettangoli = [f for f in sketch.viste[0].forme if f.kind == "rect"]
    assert all(f.stile == "acciaio" for f in rettangoli)
    assi = [f for f in sketch.viste[0].forme if f.kind == "line"]
    assert all(f.stile == "asse" for f in assi)
    marcatore = next(f for f in sketch.viste[0].forme if f.kind == "circle")
    assert marcatore.stile == "asse"


@pytest.mark.unit
def test_secondo_piatto_attivo_aggiunge_un_rettangolo() -> None:
    """Abilitando anche la seconda riga di piatti (b_mm>0) compaiono 5 rettangoli."""
    modificato = {**TOOL.example, "piatti": [{"b_mm": 8, "h_mm": 105}, {"b_mm": 8, "h_mm": 105}]}
    inputs, elementi, x_n_mm, y_n_mm = _elementi_e_baricentro(modificato)
    sketch = disegna(elementi, x_n_mm, y_n_mm, inputs.h_profilo_mm, inputs.b_profilo_mm)
    rettangoli = [f for f in sketch.viste[0].forme if f.kind == "rect"]
    assert len(rettangoli) == 5


@pytest.mark.unit
def test_rettangoli_dal_centro_elemento_a_spigolo_inferiore_sinistro() -> None:
    """Ogni rettangolo è l'elemento convertito da centro+dimensione a spigolo inferiore sinistro,
    in metri."""
    inputs, elementi, x_n_mm, y_n_mm = _elementi_e_baricentro(TOOL.example)
    sketch = disegna(elementi, x_n_mm, y_n_mm, inputs.h_profilo_mm, inputs.b_profilo_mm)
    rettangoli = [f for f in sketch.viste[0].forme if f.kind == "rect"]
    attivi = [e for e in elementi if e.b_mm > 0 and e.h_mm > 0]
    assert len(rettangoli) == len(attivi)
    for rettangolo, elemento in zip(rettangoli, attivi, strict=True):
        assert rettangolo.x == pytest.approx((elemento.x_mm - elemento.b_mm / 2.0) / 1000.0)
        assert rettangolo.y == pytest.approx((elemento.y_mm - elemento.h_mm / 2.0) / 1000.0)
        assert rettangolo.w == pytest.approx(elemento.b_mm / 1000.0)
        assert rettangolo.h == pytest.approx(elemento.h_mm / 1000.0)


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Allargando b_profilo_mm il piatto si sposta più lontano dall'anima: l'ingombro disegnato
    (asse orizzontale, che si estende oltre il bounding box di tutti gli elementi) si allarga di
    conseguenza su entrambi i lati."""
    inputs_base, elementi_base, x_n0, y_n0 = _elementi_e_baricentro(TOOL.example)
    sketch_base = disegna(elementi_base, x_n0, y_n0, inputs_base.h_profilo_mm, inputs_base.b_profilo_mm)
    asse_orizzontale_base = next(f for f in sketch_base.viste[0].forme if f.kind == "line")

    modificato = {**TOOL.example, "b_profilo_mm": 260}
    inputs_mod, elementi_mod, x_n1, y_n1 = _elementi_e_baricentro(modificato)
    sketch_mod = disegna(elementi_mod, x_n1, y_n1, inputs_mod.h_profilo_mm, inputs_mod.b_profilo_mm)
    asse_orizzontale_mod = next(f for f in sketch_mod.viste[0].forme if f.kind == "line")

    assert asse_orizzontale_mod.p1[0] < asse_orizzontale_base.p1[0]
    assert asse_orizzontale_mod.p2[0] > asse_orizzontale_base.p2[0]

    marcatore_base = next(f for f in sketch_base.viste[0].forme if f.kind == "circle")
    marcatore_mod = next(f for f in sketch_mod.viste[0].forme if f.kind == "circle")
    assert marcatore_mod.centro[0] == pytest.approx(x_n1 / 1000.0)
    assert marcatore_base.centro[0] == pytest.approx(x_n0 / 1000.0)


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
    import strutture.members.acciaio_sezione_composta.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")
