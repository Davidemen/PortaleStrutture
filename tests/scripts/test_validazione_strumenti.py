"""Tests for scripts/validazione_strumenti.py (the per-tool validation tracker generator)."""
import importlib.util
import sys
from pathlib import Path

import pytest

_PATH = Path(__file__).resolve().parents[2] / "scripts" / "validazione_strumenti.py"
_SPEC = importlib.util.spec_from_file_location("validazione_strumenti", _PATH)
vs = importlib.util.module_from_spec(_SPEC)
assert _SPEC is not None and _SPEC.loader is not None
sys.modules["validazione_strumenti"] = vs  # dataclasses with postponed annotations need the module registered
_SPEC.loader.exec_module(vs)


def _scheda(name: str, sigla: str, **extra: object) -> object:
    base = {
        "name": name, "sigla": sigla, "title": f"Titolo {sigla}", "group": "Gruppo / Sotto", "norm": "NTC2018 §1", "package": "strutture.x.y",
        "fogli": ("Foglio.xlsx",), "specifica": "docs/specs/x.md", "esempio": True, "test_file": 3, "golden": 2, "oracle": 1,
        "passi_relazione": 12, "schizzo": True, "fornisce": ("sito.ag_g",), "riceve": (), "usa_in": ("muro-sostegno",), "midas": False,
        "voci": (vs.Voce("x/a", "Voce A", "errore_foglio", "da_confermare"), vs.Voce("x/b", "Voce B", "scelta_ingegneristica", "approvato")),
    }
    return vs.Scheda(**{**base, **extra})


@pytest.mark.unit
def test_riga_predefinita_per_strumento_nuovo() -> None:
    righe = vs.unisci((_scheda("neve-carico-falda", "NEV"),), {})
    assert righe == (vs.RigaManuale("NEV", "Titolo NEV", "da validare", "", "", "", ""),)


@pytest.mark.unit
def test_unisci_conserva_le_righe_compilate_a_mano() -> None:
    esistenti = {"MUR": vs.RigaManuale("MUR", "vecchio titolo", "validato", "1 2 3 4 5 6", "AB", "2026-10-01", "ok")}
    righe = vs.unisci((_scheda("neve-carico-falda", "NEV"), _scheda("muro-sostegno", "MUR")), esistenti)
    assert [r.sigla for r in righe] == ["NEV", "MUR"]
    mur = righe[1]
    assert (mur.stato, mur.passi, mur.validatore, mur.data, mur.note) == ("validato", "1 2 3 4 5 6", "AB", "2026-10-01", "ok")
    assert mur.strumento == "Titolo MUR"  # the title always follows the registry, only the manual cells are kept


@pytest.mark.unit
def test_leggi_righe_manuali_legge_solo_la_tabella_fra_i_marcatori() -> None:
    linee = (
        "# Titolo", "| Sigla | Strumento | Stato |", "|---|---|---|", "| XXX | fuori | validato |",
        vs.MARCATORE_INIZIO,
        "| Sigla | Strumento | Stato | Passi fatti | Validatore | Data | Note |",
        "|---|---|---|---|---|---|---|",
        "| MUR | Muro | in corso | 1 2 | AB | 2026-10-01 | nota con virgola, ok |",
        "| NEV | Neve | da validare |  |  |  |  |",
        vs.MARCATORE_FINE,
        "| YYY | dopo | validato |",
    )
    testo = "\n".join(linee)
    righe = vs.leggi_righe_manuali(testo)
    assert set(righe) == {"MUR", "NEV"}
    assert righe["MUR"].note == "nota con virgola, ok"
    assert righe["NEV"].stato == "da validare"


@pytest.mark.unit
def test_leggi_righe_manuali_senza_marcatori() -> None:
    assert vs.leggi_righe_manuali("nessuna tabella") == {}


@pytest.mark.unit
def test_scheda_md_riporta_i_fatti_utili_al_validatore() -> None:
    testo = vs.scheda_md(_scheda("muro-sostegno", "MUR"))
    assert "### MUR — Titolo MUR" in testo
    assert "Foglio.xlsx" in testo
    assert "docs/specs/x.md" in testo
    assert "12 passi" in testo
    assert "sito.ag_g" in testo and "muro-sostegno" in testo
    assert "2 voci" in testo and "1 da confermare" in testo and "1 approvata" in testo
    assert "`x/a` — Voce A" in testo and "errore del foglio" in testo


@pytest.mark.unit
def test_documento_ricostruisce_la_tabella_manuale_e_le_schede() -> None:
    schede = (_scheda("neve-carico-falda", "NEV"), _scheda("muro-sostegno", "MUR"))
    prima = vs.documento(schede, vs.unisci(schede, {}), data="2026-09-22")
    assert prima.count(vs.MARCATORE_INIZIO) == 1 and prima.count(vs.MARCATORE_FINE) == 1
    modificato = prima.replace("| MUR | Titolo MUR | da validare |  |  |  |  |", "| MUR | Titolo MUR | validato | 1 2 3 4 5 6 | AB | 2026-10-01 | firmato |")
    assert modificato != prima
    dopo = vs.documento(schede, vs.unisci(schede, vs.leggi_righe_manuali(modificato)), data="2026-09-23")
    assert "| MUR | Titolo MUR | validato | 1 2 3 4 5 6 | AB | 2026-10-01 | firmato |" in dopo
    assert "| NEV | Titolo NEV | da validare |  |  |  |  |" in dopo


@pytest.mark.unit
def test_conta_test_legge_i_marcatori_pytest(tmp_path: Path) -> None:
    pacchetto = tmp_path / "tests" / "loads" / "neve"
    pacchetto.mkdir(parents=True)
    (pacchetto / "test_a.py").write_text("@pytest.mark.golden\ndef test_x(): ...\n@pytest.mark.oracle\ndef test_y(): ...\n", encoding="utf-8")
    (pacchetto / "test_b.py").write_text("@pytest.mark.golden\ndef test_z(): ...\n", encoding="utf-8")
    assert vs.conta_test(tmp_path, "strutture.loads.neve") == (2, 2, 1)
    assert vs.conta_test(tmp_path, "strutture.loads.assente") == (0, 0, 0)


@pytest.mark.unit
def test_raccogli_schede_copre_ogni_strumento_registrato() -> None:
    from strutture.shared.divergences.loader import load_register
    from strutture.shared.tool import discover

    tools = discover()
    schede = vs.raccogli_schede(tools, load_register(), firme={}, root=vs.ROOT, con_passi=False)
    assert [s.name for s in schede] == list(tools)
    per_nome = {s.name: s for s in schede}
    assert per_nome["muro-sostegno"].schizzo and per_nome["muro-sostegno"].fogli == ("Muro di sostegno DM2018.xlsx",)
    assert "muro-sostegno" in per_nome["sisma-parametri-sito"].usa_in
    assert per_nome["fond-plinto-isolato"].midas is True
    assert per_nome["ca-sezione-dominio-mn"].fogli == ()
    assert all(s.sigla for s in schede) and len({s.sigla for s in schede}) == len(schede)
    assert sum(len(s.voci) for s in schede) > 0
    assert all(s.specifica for s in schede)
