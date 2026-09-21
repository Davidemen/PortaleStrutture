"""Live sketch for `geo-cedimento-edometrico` (docs/ui/WORKBENCH_SPEC.md §7): the section follows
the inputs, and a drawing failure must never fail the calculation."""
import time

import pytest

from strutture.geotechnics.cedimenti_edometrico import schizzo as schizzo_module
from strutture.geotechnics.cedimenti_edometrico.carico import pressione_netta
from strutture.geotechnics.cedimenti_edometrico.ingresso import converti_in_si
from strutture.geotechnics.cedimenti_edometrico.models import EdometricoInput
from strutture.geotechnics.cedimenti_edometrico.profondita_critica import profondita_critica
from strutture.geotechnics.cedimenti_edometrico.schizzo import disegna
from strutture.geotechnics.cedimenti_edometrico.tool import TOOLS
from strutture.shared.tool import execute

TOOL = TOOLS[0]


def _si_e_profondita(raw: dict):
    """Mirrors `tool.run`'s composition, stopping right before `righe`/`schizzo` (schizzo only
    needs `si` and `profondita`, not the per-slice rows)."""
    inputs = EdometricoInput.model_validate(raw)
    si = converti_in_si(inputs)
    metodo = "approssimato" if inputs.legacy_compat else inputs.metodo_tensioni
    d_m_sigma = 0.0 if inputs.legacy_compat else si.d_m
    falda_m_sigma = 0.0 if inputs.legacy_compat else si.falda_m
    carico = pressione_netta(si.q_kPa, si.gamma_kN_m3, si.d_m, water_table_m=si.falda_m, legacy_compat=inputs.legacy_compat)
    profondita = profondita_critica(
        carico.q_prime_kPa, si.b_m, si.l_m, si.gamma_kN_m3, metodo=metodo,
        z_crit_input_m=si.z_crit_input_m, legacy_compat=inputs.legacy_compat, z_max_m=si.z_max_m,
        d_m=d_m_sigma, water_table_m=falda_m_sigma,
    )
    return inputs, si, profondita


@pytest.mark.unit
def test_vista_titolo_e_forme_esempio() -> None:
    inputs, si, profondita = _si_e_profondita(TOOL.example)
    sketch = disegna(inputs, si, profondita)

    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    # 1 plinto + 5 strati*(rect+label) + niente falda + zcrit(line+label) + 2 quote
    assert kinds[0] == "rect"
    assert kinds.count("rect") == 1 + 5
    assert kinds.count("label") == 5 + 1
    assert kinds.count("line") == 1  # niente falda nell'esempio (falda non impostata)
    assert kinds.count("dimension") == 1  # solo B: D=0 nell'esempio -> quota D omessa (degenere)
    assert len(kinds) == 14


@pytest.mark.unit
def test_plinto_segue_gli_input() -> None:
    inputs, si, profondita = _si_e_profondita(TOOL.example)
    sketch = disegna(inputs, si, profondita)
    plinto = sketch.viste[0].forme[0]
    assert plinto.x == pytest.approx(-si.b_m / 2)
    assert plinto.y == pytest.approx(-si.d_m)
    assert plinto.w == pytest.approx(si.b_m)


@pytest.mark.unit
def test_quota_b_testo_con_virgola_italiana() -> None:
    inputs, si, profondita = _si_e_profondita(TOOL.example)
    sketch = disegna(inputs, si, profondita)
    quote = [f for f in sketch.viste[0].forme if f.kind == "dimension"]
    quota_b = next(q for q in quote if q.testo.startswith("B ="))
    assert quota_b.testo == "B = 3,50 m"
    # D=0 nell'esempio: una quota di lunghezza nulla non viene disegnata.
    assert not any(q.testo.startswith("D =") for q in quote)


@pytest.mark.unit
def test_quota_d_compare_solo_con_infissione_positiva() -> None:
    modificato = {**TOOL.example, "d": 1.5}  # `d` non è mai convertito: sempre metri (vedi ingresso.py)
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    quota_d = next(f for f in sketch.viste[0].forme if f.kind == "dimension" and f.testo.startswith("D ="))
    assert quota_d.testo == "D = 1,50 m"


@pytest.mark.unit
def test_geometria_segue_una_dimensione_modificata() -> None:
    """Cambiando `b` (in sistema tecnico, cm) il plinto e la quota B cambiano di conseguenza."""
    modificato = {**TOOL.example, "b": 500}
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    plinto = sketch.viste[0].forme[0]
    quota_b = next(f for f in sketch.viste[0].forme if f.kind == "dimension" and f.testo.startswith("B ="))
    assert plinto.w == pytest.approx(5.0)
    assert quota_b.testo == "B = 5,00 m"


@pytest.mark.unit
def test_strati_seguono_la_tabella_di_ingresso() -> None:
    inputs, si, profondita = _si_e_profondita(TOOL.example)
    sketch = disegna(inputs, si, profondita)
    rettangoli_terreno = [f for f in sketch.viste[0].forme if f.kind == "rect" and f.stile == "terreno"]
    assert len(rettangoli_terreno) == 5
    primo = rettangoli_terreno[0]
    assert primo.y == pytest.approx(-3.70)  # D=0 nell'esempio: nessuno scostamento visibile
    assert primo.h == pytest.approx(3.70)
    etichette = [f for f in sketch.viste[0].forme if f.kind == "label" and f.testo.startswith("Eed =")]
    assert etichette[0].testo == "Eed = 5,5 MPa"


@pytest.mark.unit
def test_strati_sono_relativi_al_piano_di_posa_non_al_piano_campagna() -> None:
    """`strati[i].z_top_m`/`z_bot_m` sono misurati dal piano di posa (non dal piano campagna, a
    differenza di cedimenti_elastico): con D>0 ogni strato deve traslare in basso di D."""
    modificato = {**TOOL.example, "d": 1.5}  # `d` non è mai convertito: sempre metri (vedi ingresso.py)
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    plinto = sketch.viste[0].forme[0]
    rettangoli_terreno = [f for f in sketch.viste[0].forme if f.kind == "rect" and f.stile == "terreno"]
    primo = rettangoli_terreno[0]  # z_top=0, z_bot=3.70 m rispetto al piano di posa
    assert primo.y == pytest.approx(-1.5 - 3.70)
    assert primo.h == pytest.approx(3.70)
    # il primo strato inizia esattamente alla base del plinto (continuità fisica).
    assert primo.y + primo.h == pytest.approx(plinto.y)


@pytest.mark.unit
def test_zcrit_e_offset_dalla_profondita_di_posa() -> None:
    """`z_crit_utilizzato_m` è misurato dal piano di posa: con D>0 la linea disegnata deve stare
    alla profondità assoluta D+Z,crit dal piano campagna, non a Z,crit da solo."""
    # `d` non è mai convertito (sempre metri, anche in sistema "tecnico": vedi `ingresso.py`).
    modificato = {**TOOL.example, "d": 1.5}  # z_crit_input resta 10000 cm = 100 m
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    linea_zcrit = next(f for f in sketch.viste[0].forme if f.kind == "line")
    etichetta_zcrit = next(f for f in sketch.viste[0].forme if f.kind == "label" and f.testo.startswith("Z_crit ="))
    atteso_m = si.d_m + profondita.z_crit_utilizzato_m
    assert atteso_m == pytest.approx(1.5 + 100.0)
    assert linea_zcrit.p1[1] == pytest.approx(-atteso_m)
    assert linea_zcrit.p2[1] == pytest.approx(-atteso_m)
    assert etichetta_zcrit.testo == f"Z_crit = {atteso_m:.2f} m".replace(".", ",")


@pytest.mark.unit
def test_falda_disegnata_quando_presente() -> None:
    modificato = {**TOOL.example, "falda": 200}  # tecnico: 200 cm = 2.0 m
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    linee = [f for f in sketch.viste[0].forme if f.kind == "line"]
    assert len(linee) == 2  # falda + zcrit
    falda = next(f for f in linee if f.stile == "acqua")
    assert falda.tratteggio is True
    assert falda.p1[1] == pytest.approx(-2.0)
    assert falda.p2[1] == pytest.approx(-2.0)


@pytest.mark.unit
def test_falda_assente_di_default() -> None:
    inputs, si, profondita = _si_e_profondita(TOOL.example)
    sketch = disegna(inputs, si, profondita)
    linee_falda = [f for f in sketch.viste[0].forme if f.kind == "line" and f.stile == "acqua"]
    assert linee_falda == []


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
    import strutture.geotechnics.cedimenti_edometrico.tool as tool_module

    def _rompi(*_args: object, **_kwargs: object) -> None:
        raise RuntimeError("errore forzato di disegno")

    monkeypatch.setattr(tool_module, "disegna_schizzo", _rompi)
    report = execute(TOOL, TOOL.example)
    assert report.ok, report.errors
    assert report.data.schizzo is None


@pytest.mark.unit
def test_modulo_schizzo_importabile_e_puro() -> None:
    assert hasattr(schizzo_module, "disegna")
