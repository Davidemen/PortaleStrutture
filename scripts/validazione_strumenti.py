"""Genera `docs/VALIDAZIONE_STRUMENTI.md`, il registro di validazione dei singoli strumenti.

    uv run python scripts/validazione_strumenti.py [--data-dir var] [--out docs/VALIDAZIONE_STRUMENTI.md]

La tabella "Stato di validazione" la compila a mano il validatore ed è CONSERVATA a ogni rigenerazione
(le righe si riconoscono dalla sigla). Le schede per strumento sono ricostruite dai dati: registro delle
correzioni (JSON + firme nel database), test, relazione con formule, schizzo, collegamenti, importazione MIDAS.
Portabile: solo libreria standard oltre al pacchetto `strutture`.
"""
from __future__ import annotations

import argparse
import datetime as dt
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from strutture.shared.collegamenti import raccogli
from strutture.shared.divergences.loader import load_register
from strutture.shared.divergences.models import Divergence
from strutture.shared.tool import Tool, discover, execute
from strutture.web.presentation import sigla_for

ROOT = Path(__file__).resolve().parents[1]
USCITA_PREDEFINITA = ROOT / "docs" / "VALIDAZIONE_STRUMENTI.md"
MARCATORE_INIZIO = "<!-- INIZIO TABELLA MANUALE: le righe qui sotto sono vostre, il generatore le conserva -->"
MARCATORE_FINE = "<!-- FINE TABELLA MANUALE -->"
INTESTAZIONE_TABELLA = ("Sigla", "Strumento", "Stato", "Passi fatti", "Validatore", "Data", "Note")
STATI_MANUALI = ("da validare", "in corso", "validato", "bloccato")
MARCATORE_MIDAS = "midas-reactions"

PASSI_VALIDAZIONE: tuple[str, ...] = (
    ("Esempio in modalità Excel: aprire lo strumento, \"Carica esempio\", accendere \"Riproduci il foglio Excel originale "
     "(errori inclusi)\" e confrontare i numeri con il foglio di origine (devono coincidere alla cifra)."),
    ("Registro: aprire \"Registro correzioni\" filtrato sullo strumento e firmare ogni voce (approvata o respinta) con la "
     "propria sigla; \"Confronta con Excel\" mostra l'effetto numerico di ciascuna."),
    ("Caso reale in modalità standard: inserire un elemento già calcolato in passato (o a mano) e confrontare verdetto e "
     "grandezze principali; le differenze devono essere spiegate dalle voci di registro."),
    "Relazione: \"Stampa relazione\" con \"Sviluppo dei calcoli\" e rileggere le formule, le sostituzioni e le clausole.",
    "Schizzo e verifiche: lo schizzo corrisponde all'elemento inserito; nomi, clausole e limiti delle verifiche sono giusti.",
    "Firma: stato \"validato\", sigla e data nella tabella; note su ciò che resta aperto.",
)

TIPI_IT: dict[str, str] = {
    "errore_foglio": "errore del foglio",
    "aggiornamento_normativo": "aggiornamento normativo",
    "scelta_ingegneristica": "scelta ingegneristica",
    "da_verificare": "da verificare",
}
STATI_IT: dict[str, tuple[str, str]] = {  # singolare, plurale
    "da_confermare": ("da confermare", "da confermare"),
    "approvato": ("approvata", "approvate"),
    "respinto": ("respinta", "respinte"),
}

_SISMA = ("Azione sismica da NTC - DM2018.xls",)
_PILASTRI = (
    "Calcolo pilastri in c.a. secondo NTC - DM2008.xls",
    "workbooks/30_Calcolo pilastri in c.a. secondo NTC 2018 e Circolare2019.xls",
    "workbooks/31_Calcolo pilastri in c.a. secondo UNI EN 1992-1-1 2005.xls",
)
_FESSURAZIONE = ("Verifica fessurazione - SLEF (X).xlsx",)
_CEDIMENTI = ("workbooks/2xxxx_Cedimenti fondazioni_elastico+edo.xlsx",)
FOGLI: dict[str, tuple[str, ...]] = {
    "neve-carico-falda": ("Carico neve da NTC - DM2018.xls",),
    "neve-accumulo": ("Carico neve da NTC - DM2018.xls",),
    "sisma-vita-riferimento": _SISMA, "sisma-parametri-sito": _SISMA, "sisma-fattori-struttura": _SISMA,
    "sisma-spettro": _SISMA, "sisma-completo": _SISMA,
    "vento-pressione": ("Carico vento da NTC - DM2018.xls",),
    "vento-cpe-rettangolare": ("Coefficienti Cpe Vento - DM2018.xlsx",),
    "acciaio-colonna-h-ec3": ("Verifica instabilità e resistenza colonne ad H secondo EC3.xlsx",),
    "acciaio-resistenza-incendio": ("Resistenza acciaio con incendio.xlsx",),
    "acciaio-proprieta-temperatura": ("workbooks/2xxxx_Verifiche al fuoco_proprietà materiali.xlsx",),
    "acciaio-sezione-h-rimpiattata": ("workbooks/2xxx_Sezione H rimpiattata.xlsx",),
    "ca-sle-limitazione-tensioni": _FESSURAZIONE, "ca-apertura-fessure": _FESSURAZIONE,
    "ca-apertura-fessure-semplificata": _FESSURAZIONE,
    "ca-mensola-tozza": ("Calcolo mensole tozze in c.a. secondo NTC - DM2008.xls",),
    "ca-pilastro-rettangolare": _PILASTRI, "ca-pilastro-circolare": _PILASTRI,
    "ca-punzonamento": ("workbooks/2xxxx_Punzonamento - EC2 §6.4.xlsx",),
    "ca-sezione-dominio-mn": (),
    "ca-taglio-non-armato": ("Taglio non armato NTC2018.xlsx", "workbooks/2xxxx_Taglio non armato NTC2018.xlsx"),
    "ca-trave-rettangolare": ("Calcolo travi in c.a. secondo NTC - DM2008.xls",),
    "muro-sostegno": ("Muro di sostegno DM2018.xlsx",),
    "geo-cedimento-edometrico": _CEDIMENTI, "geo-cedimento-elastico-newmark": _CEDIMENTI,
    "geo-cedimento-elastico-timoshenko-goodier": _CEDIMENTI,
    "fond-pavimento-industriale": ("workbooks/10x_Pavimento industriale CNR_DT211-2014.xlsx",),
    "fond-plinto-isolato": ("workbooks/2xxxx_Plinti isolati.xlsx",),
    "fond-plinto-su-pali": ("workbooks/2xxxx_Plinti su pali_PL-FX_S&T Eurocode 2.xlsx",),
    "fond-trave-collegamento": ("workbooks/50_Calcolo travi di collegamento NTC 2018.xlsx",),
}
SPECIFICHE_PER_PACCHETTO: dict[str, str] = {
    "strutture.loads.neve": "docs/specs/neve.md", "strutture.loads.sisma": "docs/specs/sisma.md",
    "strutture.loads.vento": "docs/specs/vento.md", "strutture.loads.vento_cpe": "docs/specs/small-units.md",
    "strutture.members.acciaio_colonna_ec3": "docs/specs/acciaio.md",
    "strutture.members.acciaio_incendio": "docs/specs/acciaio.md, docs/specs/small-units.md",
    "strutture.members.acciaio_sezione_composta": "docs/specs/small-units.md",
    "strutture.members.ca_fessurazione": "docs/specs/ca-fessurazione.md",
    "strutture.members.ca_mensole": "docs/specs/ca-mensole.md",
    "strutture.members.ca_pilastri": "docs/specs/ca-pilastri.md, ca-pilastri-ntc2018.md, ca-pilastri-ec2.md",
    "strutture.members.ca_punzonamento": "docs/specs/ca-punzonamento.md",
    "strutture.members.ca_sezione_mn": "docs/architecture-phase4.md (motore nuovo, nessun foglio)",
    "strutture.members.ca_taglio_non_armato": "docs/specs/ca-travi.md, docs/specs/small-units.md",
    "strutture.members.ca_travi": "docs/specs/ca-travi.md",
    "strutture.members.muro": "docs/specs/muro-sostegno.md",
    "strutture.geotechnics.cedimenti_edometrico": "docs/specs/geo-cedimenti-edometrico.md",
    "strutture.geotechnics.cedimenti_elastico": "docs/specs/geo-cedimenti-elastico.md",
    "strutture.foundations.pavimento_industriale": "docs/specs/pavimento-industriale.md",
    "strutture.foundations.plinti_isolati": "docs/specs/fond-plinti-isolati.md",
    "strutture.foundations.plinti_pali": "docs/specs/fond-plinti-pali.md",
    "strutture.foundations.travi_collegamento": "docs/specs/fond-travi-collegamento.md",
}


@dataclass(frozen=True)
class Voce:
    id: str
    titolo: str
    tipo: str
    stato: str


@dataclass(frozen=True)
class Scheda:
    name: str
    sigla: str
    title: str
    group: str
    norm: str
    package: str
    fogli: tuple[str, ...]
    specifica: str
    esempio: bool
    test_file: int
    golden: int
    oracle: int
    passi_relazione: int | None  # None = nessuna relazione con formule
    schizzo: bool
    fornisce: tuple[str, ...]
    riceve: tuple[str, ...]
    usa_in: tuple[str, ...]
    midas: bool
    voci: tuple[Voce, ...]


@dataclass(frozen=True)
class RigaManuale:
    sigla: str
    strumento: str
    stato: str
    passi: str
    validatore: str
    data: str
    note: str


# ---- raccolta dei fatti ---------------------------------------------------------------------------

def pacchetto_di(tool: Tool) -> str:
    """`strutture.loads.neve` da `strutture.loads.neve.tool`."""
    modulo = tool.run.__module__
    return modulo.rsplit(".", 1)[0] if modulo.endswith(".tool") else modulo


def conta_test(root: Path, package: str) -> tuple[int, int, int]:
    """(file di test, marcatori golden, marcatori oracle) nella cartella dei test del pacchetto."""
    cartella = root.joinpath("tests", *package.split(".")[1:])
    if not cartella.is_dir():
        return (0, 0, 0)
    file = sorted(p for p in cartella.glob("test_*.py"))
    testi = [p.read_text(encoding="utf-8") for p in file]
    return (len(file), sum(t.count("pytest.mark.golden") for t in testi), sum(t.count("pytest.mark.oracle") for t in testi))


def passi_relazione(tool: Tool) -> int | None:
    """Numero di passi della relazione sull'esempio; None se lo strumento non ha una relazione."""
    if tool.relazione is None:
        return None
    if tool.example is None:
        return 0
    report = execute(tool, dict(tool.example), con_relazione=True)
    return sum(len(traccia.passi) for traccia in report.relazione)


def _contiene(valore: Any, cercato: str) -> bool:
    if isinstance(valore, str):
        return valore == cercato
    if isinstance(valore, Mapping):
        return any(_contiene(v, cercato) for v in valore.values())
    if isinstance(valore, (list, tuple)):
        return any(_contiene(v, cercato) for v in valore)
    return False


def usa_midas(tool: Tool) -> bool:
    return any(_contiene(campo.json_schema_extra, MARCATORE_MIDAS) for campo in tool.input_model.model_fields.values())


def voci_di(name: str, register: tuple[Divergence, ...], firme: Mapping[str, str]) -> tuple[Voce, ...]:
    return tuple(Voce(d.id, d.titolo, d.tipo, firme.get(d.id, "da_confermare")) for d in register if name in d.strumenti)


def raccogli_schede(tools: Mapping[str, Tool], register: tuple[Divergence, ...], firme: Mapping[str, str], root: Path,
                    *, con_passi: bool = True) -> tuple[Scheda, ...]:
    collegamenti = raccogli(tools)
    per_strumento = {name: {"fornisce": [], "riceve": [], "usa_in": set()} for name in tools}
    for chiave, coll in collegamenti.items():
        for f in coll.fornitori:
            per_strumento[f.strumento]["fornisce"].append(chiave)
            per_strumento[f.strumento]["usa_in"].update(c.strumento for c in coll.consumatori)
        for c in coll.consumatori:
            per_strumento[c.strumento]["riceve"].append(chiave)
    return tuple(_scheda(name, tool, register, firme, root, per_strumento[name], con_passi) for name, tool in tools.items())


def _scheda(name: str, tool: Tool, register: tuple[Divergence, ...], firme: Mapping[str, str], root: Path,
            legami: Mapping[str, Any], con_passi: bool) -> Scheda:
    package = pacchetto_di(tool)
    file, golden, oracle = conta_test(root, package)
    return Scheda(
        name=name, sigla=sigla_for(name, tool.title), title=tool.title, group=tool.group, norm=tool.norm, package=package,
        fogli=FOGLI.get(name, ()), specifica=SPECIFICHE_PER_PACCHETTO.get(package, f"docs/specs/ (pacchetto {package})"),
        esempio=tool.example is not None, test_file=file, golden=golden, oracle=oracle,
        passi_relazione=passi_relazione(tool) if con_passi else (None if tool.relazione is None else 0),
        schizzo="schizzo" in tool.output_model.model_fields,
        fornisce=tuple(legami["fornisce"]), riceve=tuple(legami["riceve"]), usa_in=tuple(sorted(legami["usa_in"])),
        midas=usa_midas(tool), voci=voci_di(name, register, firme),
    )


def leggi_firme(data_dir: Path) -> dict[str, str]:
    """`{id: stato}` dal database, se esiste (mai crearlo per leggere)."""
    from strutture.storage import signoff_sqlite

    if not (data_dir / signoff_sqlite.DB_FILENAME).is_file():
        return {}
    repository = signoff_sqlite.open_signoff_repository(data_dir)
    return {divergence_id: firma.stato for divergence_id, firma in repository.list_all().items()}


# ---- tabella manuale ----------------------------------------------------------------------------

def leggi_righe_manuali(testo: str) -> dict[str, RigaManuale]:
    """Le righe della tabella fra i marcatori, per sigla; vuoto se il documento non esiste ancora."""
    inizio, fine = testo.find(MARCATORE_INIZIO), testo.find(MARCATORE_FINE)
    if inizio < 0 or fine < 0 or fine < inizio:
        return {}
    righe: dict[str, RigaManuale] = {}
    for linea in testo[inizio:fine].splitlines():
        celle = [c.strip() for c in linea.strip().strip("|").split("|")] if linea.strip().startswith("|") else []
        if len(celle) != len(INTESTAZIONE_TABELLA) or celle[0] in ("Sigla", "") or set(celle[0]) <= {"-"}:
            continue
        righe[celle[0]] = RigaManuale(*celle)
    return righe


def unisci(schede: tuple[Scheda, ...], esistenti: Mapping[str, RigaManuale]) -> tuple[RigaManuale, ...]:
    """Una riga per strumento nell'ordine del registro: celle manuali conservate, titolo sempre aggiornato."""
    righe = []
    for s in schede:
        r = esistenti.get(s.sigla)
        righe.append(RigaManuale(s.sigla, s.title, r.stato, r.passi, r.validatore, r.data, r.note) if r
                     else RigaManuale(s.sigla, s.title, STATI_MANUALI[0], "", "", "", ""))
    return tuple(righe)


def tabella_manuale(righe: tuple[RigaManuale, ...]) -> str:
    testa = "| " + " | ".join(INTESTAZIONE_TABELLA) + " |\n|" + "|".join("---" for _ in INTESTAZIONE_TABELLA) + "|"
    corpo = "\n".join(f"| {r.sigla} | {r.strumento} | {r.stato} | {r.passi} | {r.validatore} | {r.data} | {r.note} |" for r in righe)
    return f"{MARCATORE_INIZIO}\n{testa}\n{corpo}\n{MARCATORE_FINE}"


# ---- schede -------------------------------------------------------------------------------------

def _conteggio(voci: tuple[Voce, ...]) -> str:
    if not voci:
        return "nessuna voce di registro"
    parti = []
    for stato, (sing, plur) in STATI_IT.items():
        n = sum(1 for v in voci if v.stato == stato)
        if n:
            parti.append(f"{n} {sing if n == 1 else plur}")
    return f"{len(voci)} {'voce' if len(voci) == 1 else 'voci'}: " + ", ".join(parti)


def _elenco(valori: tuple[str, ...]) -> str:
    return ", ".join(f"`{v}`" for v in valori) if valori else "—"


def scheda_md(s: Scheda) -> str:
    relazione = "nessuna" if s.passi_relazione is None else f"sì ({s.passi_relazione} passi sull'esempio)"
    righe = [
        f"### {s.sigla} — {s.title}",
        f"- Gruppo: {s.group} · norma: {s.norm} · pacchetto: `{s.package}`",
        "- Fogli Excel di origine: " + (", ".join(f"`{f}`" for f in s.fogli) if s.fogli else "nessuno (strumento nuovo, non deriva da un foglio)"),
        f"- Specifica: {s.specifica}",
        (f"- Esempio (\"Carica esempio\"): {'sì' if s.esempio else 'no'} · test: {s.test_file} file, {s.golden} golden (valori del foglio), "
         f"{s.oracle} oracle (ricalcolo LibreOffice)"),
        f"- Relazione con formule: {relazione} · schizzo: {'sì' if s.schizzo else 'no'} · importazione MIDAS: {'sì' if s.midas else 'no'}",
        f"- Collegamenti: fornisce {_elenco(s.fornisce)} · riceve {_elenco(s.riceve)} · \"Usa in…\" verso {_elenco(s.usa_in)}",
        f"- Registro: {_conteggio(s.voci)}",
    ]
    righe += [f"  - `{v.id}` — {v.titolo} ({TIPI_IT.get(v.tipo, v.tipo)}, {STATI_IT.get(v.stato, (v.stato, v.stato))[0]})" for v in s.voci]
    return "\n".join(righe)


def intestazione(data: str) -> str:
    passi = "\n".join(f"{i}. {p}" for i, p in enumerate(PASSI_VALIDAZIONE, 1))
    return f"""# Validazione dei singoli strumenti

Aggiornato il {data}. Questo è il registro del lavoro di validazione, strumento per strumento, che l'ingegnere
responsabile fa una volta prima di usare il programma in produzione. La tabella qui sotto si compila a mano
(anche tramite un agente: "segna PLI come validato, sigla AB, oggi"); le schede più in basso sono generate dai dati.
Rigenerare con `uv run python scripts/validazione_strumenti.py`: la tabella compilata viene conservata, le schede
aggiornate (registro firmato, test, relazioni).

## I sei passi di validazione di uno strumento
{passi}

## Come si compila la tabella
- Stato: `da validare` → `in corso` → `validato`; `bloccato` se serve una decisione o una correzione (dirlo nelle note).
- Passi fatti: i numeri dei passi completati, separati da spazio (es. `1 2 3`).
- Validatore: sigla; Data: AAAA-MM-GG; Note: senza il carattere `|`.
- Il registro delle correzioni si firma nell'app, non qui: le schede riportano lo stato letto dal database.

## Stato di validazione
"""


def documento(schede: tuple[Scheda, ...], righe: tuple[RigaManuale, ...], *, data: str) -> str:
    validati = sum(1 for r in righe if r.stato == "validato")
    voci_uniche = {v.id for s in schede for v in s.voci}
    riepilogo = f"\nStrumenti: {len(schede)} · validati: {validati} · voci di registro legate a uno strumento: {len(voci_uniche)}\n"
    schede_md = "\n\n".join(scheda_md(s) for s in schede)
    return intestazione(data) + tabella_manuale(righe) + riepilogo + "\n## Schede per strumento (generate)\n\n" + schede_md + "\n"


# ---- CLI ----------------------------------------------------------------------------------------

def genera(out: Path, data_dir: Path, *, oggi: str | None = None) -> str:
    tools = discover()
    schede = raccogli_schede(tools, load_register(), leggi_firme(data_dir), ROOT)
    esistenti = leggi_righe_manuali(out.read_text(encoding="utf-8")) if out.is_file() else {}
    testo = documento(schede, unisci(schede, esistenti), data=oggi or dt.datetime.now(dt.UTC).date().isoformat())
    out.write_text(testo, encoding="utf-8")
    return testo


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Genera il registro di validazione dei singoli strumenti")
    parser.add_argument("--data-dir", type=Path, default=ROOT / "var", help="cartella del database (predefinita: var/)")
    parser.add_argument("--out", type=Path, default=USCITA_PREDEFINITA, help="file markdown da scrivere")
    args = parser.parse_args(argv)
    testo = genera(args.out, args.data_dir)
    righe = leggi_righe_manuali(testo)
    print(f"scritto {args.out} ({len(righe)} strumenti)")


if __name__ == "__main__":
    main()
