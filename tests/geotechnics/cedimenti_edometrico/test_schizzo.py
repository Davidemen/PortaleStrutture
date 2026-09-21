"""Live sketch for `geo-cedimento-edometrico` (docs/ui/WORKBENCH_SPEC.md §7): the section follows
the inputs, and a drawing failure must never fail the calculation."""
import sys
import time
from pathlib import Path

import pytest

from strutture.geotechnics.cedimenti_edometrico import schizzo as schizzo_module
from strutture.geotechnics.cedimenti_edometrico.carico import pressione_netta
from strutture.geotechnics.cedimenti_edometrico.ingresso import converti_in_si
from strutture.geotechnics.cedimenti_edometrico.models import EdometricoInput
from strutture.geotechnics.cedimenti_edometrico.profondita_critica import profondita_critica
from strutture.geotechnics.cedimenti_edometrico.schizzo import disegna
from strutture.geotechnics.cedimenti_edometrico.tool import TOOLS
from strutture.shared.tool import execute

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "shared"))
from test_sketch_layout import layout_problems, overlap_problems, readability_problems

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
    """L'esempio ha 5 strati fino a 118,9 m: molto oltre il budget di profondità visibile, quindi
    lo strato più profondo è escluso (4 strati disegnati) e solo 2 sono etichettati (limite
    `_MAX_STRATI_ETICHETTATI`, ciascuno con quota di spessore + etichetta Eed), con un tratto
    "fantasma" a indicare la prosecuzione in profondità (oltre ai fantasma laterali e di
    diffusione 2:1, sempre presenti)."""
    inputs, si, profondita = _si_e_profondita(TOOL.example)
    sketch = disegna(inputs, si, profondita)

    assert [v.titolo for v in sketch.viste] == ["Sezione"]
    kinds = [f.kind for f in sketch.viste[0].forme]
    assert kinds[0] == "rect"
    assert kinds.count("rect") == 1 + 4  # plinto + 4 strati visibili (il 5° è oltre il ritaglio)
    assert kinds.count("label") == 2 + 1  # 2 Eed (limite) + 1 Z_crit
    assert kinds.count("dimension") == 2 + 1  # 2 Δz (spessore strato) + 1 B (D=0 nell'esempio -> quota D omessa)
    # 2 diffusione 2:1 + 1 Z,crit + 2 fantasma laterali + 1 fantasma di profondità (ritagliato)
    assert kinds.count("line") == 2 + 1 + 2 + 1
    assert len(kinds) == 17
    assert "interrotta" in sketch.nota


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
    assert len(rettangoli_terreno) == 4  # il 5° strato (fino a 118,9 m) è oltre il ritaglio
    primo = rettangoli_terreno[0]
    assert primo.y == pytest.approx(-3.70)  # D=0 nell'esempio: nessuno scostamento visibile
    assert primo.h == pytest.approx(3.70)
    etichette = [f for f in sketch.viste[0].forme if f.kind == "label" and f.testo.startswith("Eed =")]
    assert etichette[0].testo == "Eed = 5,5 MPa"  # il primo strato è sempre fra quelli etichettati


@pytest.mark.unit
def test_al_massimo_due_strati_etichettati_anche_con_molti_strati() -> None:
    """Con una stratigrafia lunga (fino al limite di 20 righe della tabella) le etichette Eed e le
    quote di spessore restano al massimo `_MAX_STRATI_ETICHETTATI`, cosi' non si accavallano mai."""
    strati = [{"z_top_m": float(i), "z_bot_m": float(i + 1), "modulo_MPa": 5.0 + i} for i in range(15)]
    modificato = {**TOOL.example, "strati": strati}
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    forme = sketch.viste[0].forme
    etichette_eed = [f for f in forme if f.kind == "label" and f.testo.startswith("Eed =")]
    quote_spessore = [f for f in forme if f.kind == "dimension" and f.testo.startswith("Δz =")]
    assert len(etichette_eed) <= 2
    assert len(quote_spessore) <= 2
    assert len(quote_spessore) == len(etichette_eed)
    # il primo strato (il più superficiale) è sempre fra quelli etichettati.
    assert any(f.testo == "Eed = 5,0 MPa" for f in etichette_eed)


@pytest.mark.unit
def test_blocco_di_terreno_largo_3b_con_fantasma_laterali() -> None:
    """Il blocco di terreno è disegnato 3 volte più largo del plinto (non deve leggersi come un
    palo) e ha un tacco tratteggiato "fantasma" per lato, a segnalare che il terreno prosegue oltre."""
    inputs, si, profondita = _si_e_profondita(TOOL.example)
    sketch = disegna(inputs, si, profondita)
    forme = sketch.viste[0].forme
    primo_strato = next(f for f in forme if f.kind == "rect" and f.stile == "terreno")
    assert primo_strato.w == pytest.approx(si.b_m * 3.0)
    fantasmi_laterali = [f for f in forme if f.kind == "line" and f.stile == "fantasma"
                          and f.p1[1] == pytest.approx(f.p2[1])]  # orizzontali (non la diffusione 2:1, obliqua)
    assert len(fantasmi_laterali) == 2
    estremi_esterni = sorted(f.p2[0] for f in fantasmi_laterali)
    assert estremi_esterni[0] < -primo_strato.w / 2  # oltre il bordo sinistro del blocco di terreno
    assert estremi_esterni[1] > primo_strato.w / 2  # oltre il bordo destro del blocco di terreno


@pytest.mark.unit
def test_quota_b_sopra_il_plinto() -> None:
    """Correzione P1: la quota B sta sopra il plinto (il lato superiore, non sotto la base)."""
    inputs, si, profondita = _si_e_profondita(TOOL.example)
    sketch = disegna(inputs, si, profondita)
    forme = sketch.viste[0].forme
    plinto = forme[0]
    quota_b = next(f for f in forme if f.kind == "dimension" and f.testo.startswith("B ="))
    sommo_plinto = plinto.y + plinto.h
    assert quota_b.p1[1] == pytest.approx(sommo_plinto)
    assert quota_b.distanza > 0  # verso l'alto: fuori dal plinto


@pytest.mark.unit
def test_diffusione_2a1_tratteggiata_fino_a_zcrit() -> None:
    """Correzione P1 (solo edometrico): due linee tratteggiate di diffusione 2:1 dal filo del
    plinto fino alla quota (disegnata) di Z,crit — pendenza 2 verticale : 1 orizzontale."""
    inputs, si, profondita = _si_e_profondita(TOOL.example)
    sketch = disegna(inputs, si, profondita)
    forme = sketch.viste[0].forme
    plinto = forme[0]
    diffusione = [f for f in forme if f.kind == "line" and f.stile == "fantasma"
                  and f.p1[0] != f.p2[0] and f.p1[1] != f.p2[1]]  # oblique (non i fantasma orizzontali/verticali)
    assert len(diffusione) == 2
    sinistra, destra = sorted(diffusione, key=lambda f: f.p1[0])
    assert sinistra.p1[0] == pytest.approx(-si.b_m / 2)
    assert sinistra.p1[1] == pytest.approx(plinto.y)  # dal filo del plinto (piano di posa)
    profondita_diffusione = sinistra.p1[1] - sinistra.p2[1]
    sporgenza = sinistra.p1[0] - sinistra.p2[0]
    assert sporgenza == pytest.approx(profondita_diffusione / 2.0)  # pendenza 2:1
    assert destra.p1[0] == pytest.approx(si.b_m / 2)


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
def test_zcrit_etichetta_riporta_sempre_la_profondita_reale() -> None:
    """`z_crit_utilizzato_m` è misurato dal piano di posa: con D>0 il testo deve riportare la
    profondità assoluta D+Z,crit dal piano campagna (schema non in scala: la LINEA può essere
    ritagliata al budget di profondità visibile, ma il testo riporta sempre il valore vero)."""
    # `d` non è mai convertito (sempre metri, anche in sistema "tecnico": vedi `ingresso.py`).
    modificato = {**TOOL.example, "d": 1.5}  # z_crit_input resta 10000 cm = 100 m -> ritagliato
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    etichetta_zcrit = next(f for f in sketch.viste[0].forme if f.kind == "label" and f.testo.startswith("Z_crit ="))
    atteso_m = si.d_m + profondita.z_crit_utilizzato_m
    assert atteso_m == pytest.approx(1.5 + 100.0)
    assert etichetta_zcrit.testo == f"Z_crit = {atteso_m:.2f} m".replace(".", ",")


@pytest.mark.unit
def test_zcrit_linea_alla_profondita_reale_quando_entro_il_ritaglio() -> None:
    """Quando Z,crit cade entro il budget di profondità visibile, la linea è disegnata alla sua
    vera posizione (nessun ritaglio necessario)."""
    modificato = {**TOOL.example, "z_crit_input": 300}  # tecnico: 300 cm = 3 m, ben entro il budget
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    linea_zcrit = next(f for f in sketch.viste[0].forme if f.kind == "line" and f.stile == "evidenza")
    atteso_m = si.d_m + profondita.z_crit_utilizzato_m
    assert atteso_m == pytest.approx(3.0)
    assert linea_zcrit.p1[1] == pytest.approx(-atteso_m)


@pytest.mark.unit
def test_falda_disegnata_quando_presente() -> None:
    modificato = {**TOOL.example, "falda": 200}  # tecnico: 200 cm = 2.0 m
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    falda = next(f for f in sketch.viste[0].forme if f.kind == "line" and f.stile == "acqua")
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


# --- composizione: layout/leggibilità/sovrapposizioni su input realistici oltre l'esempio --------

_CASI_COMPOSIZIONE = {
    "infissione profonda": {"d": 1.8},  # `d` non è mai convertito: sempre metri (limite del campo: 200 m)
    "molti strati": {"strati": [{"z_top_m": float(i) * 0.8, "z_bot_m": float(i + 1) * 0.8,
                                  "modulo_MPa": 5.0 + i} for i in range(12)]},
    "plinto molto largo": {"b": 1200, "l": 1200},  # tecnico: 1200 cm = 12 m
}


@pytest.mark.unit
@pytest.mark.parametrize("nome", list(_CASI_COMPOSIZIONE))
def test_composizione_su_input_realistici(nome: str) -> None:
    modificato = {**TOOL.example, **_CASI_COMPOSIZIONE[nome]}
    inputs, si, profondita = _si_e_profondita(modificato)
    sketch = disegna(inputs, si, profondita)
    problemi = layout_problems(sketch) + readability_problems(sketch) + overlap_problems(sketch)
    assert problemi == [], f"{nome}: {problemi}"
