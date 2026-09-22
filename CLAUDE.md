# StruttureMenni — istruzioni per gli agenti di sviluppo

Leggi tutto questo file prima di toccare qualsiasi cosa. Poi leggi `docs/CONSEGNA.md` (stato del progetto e
lavori aperti), `docs/BUILD_CONTRACT.md` (regole di costruzione, in inglese) e solo la sezione della specifica
che riguarda il tuo compito (`docs/INDICE.md` dice dove sta cosa). Non esplorare il repository a caso: usa
`grep -n` e `sed -n` per leggere sezioni mirate.

## Con chi lavori
Il titolare è un ingegnere strutturista, non un programmatore. Rispondi sempre in italiano, breve e concreto:
cosa hai fatto, cosa hai verificato e con quale comando, cosa resta da decidere a lui. Non chiedergli scelte di
programmazione: decidile tu e dichiarale. Chiedigli SOLO scelte ingegneristiche (coefficienti, clausole,
ipotesi di calcolo) e non prenderle mai al posto suo: elencale in `docs/DECISIONI_DA_CONFERMARE.md` e nel
registro delle correzioni. Interfaccia, messaggi, avvisi, nomi delle verifiche, registro e documenti per il
titolare sono in italiano, con la maiuscola solo sulla prima parola e mai in MAIUSCOLO. Nel codice segui la
lingua del file in cui lavori (è misto italiano/inglese): non tradurre ciò che esiste.

## Cos'è
31 strumenti di calcolo (NTC 2018 / Eurocodici) nati da 23 fogli Excel. Pacchetto Python `strutture` (layout
`src/`, Python ≥ 3.12, pydantic v2, FastAPI) più un'interfaccia web in JavaScript puro (moduli ES, nessuna
dipendenza esterna, CSP rigida). Ogni strumento ha modelli di ingresso e uscita congelati, passi di calcolo
puri in moduli piccoli, verifiche, avvisi, uno schizzo SVG, una relazione con le formule tracciate e due
modalità: standard (norma applicata, errori del foglio corretti) ed Excel (`legacy_compat=True`, riproduce il
foglio errori inclusi). Ogni differenza fra le due è una voce del registro delle correzioni.

## Mappa del repository
- `src/strutture/shared/`: contratto `Tool`/`Report` (`tool.py`, `report.py`), schizzi (`sketch.py`), formule
  (`relazione/`), registro (`divergences/`: `legacy("<unita>/<slug>", flag)`, `check`, `render`), collegamenti
  fra strumenti (`collegamenti.py`), sezione M-N (`sezione_ca/`), capacità portante (`capacita_portante/`),
  unità (`units.py`, l'unico posto per i fattori di conversione), tabelle (`tables.py`, `tabular.py`).
- `src/strutture/{loads,members,geotechnics,foundations}/<pacchetto>/`: uno strumento per pacchetto:
  `models.py`, un modulo per passo di calcolo, `tables.py`, `tool.py` (espone `TOOLS`), `schizzo.py`,
  `relazione*.py`. Esempio piccolo e completo da copiare: `members/ca_taglio_non_armato/`.
- `src/strutture/data/divergences/*.json`: il registro delle correzioni (dati). `docs/divergences/*.md` sono
  GENERATI con `uv run python -m strutture.shared.divergences.render`: mai modificarli a mano.
- `src/strutture/storage/`: SQLite (firme del registro, progetti, elementi, revisioni). Dati in `var/strutture.db`.
- `src/strutture/integrations/midas/`: client MIDAS NX in sola lettura. `src/strutture/web/`: `app.py`,
  `routes/{tools,comuni,midas,divergences,progetti}.py`, `middleware/`, `static/` (interfaccia servita,
  `js/` e `css/`), `static_next/` (copia di lavoro dell'interfaccia, ignorata da git).
- `tests/` rispecchia `src/`. `tests/e2e/` è Playwright (fixture in `conftest.py`, azioni in `_actions.py`,
  server in memoria in `_server.py`). `tests/fixtures/*.json` sono valori di riferimento calcolati dai fogli.
- `docs/`: indice in `docs/INDICE.md`. `docs/VALIDAZIONE_STRUMENTI.md`: tabella di stato compilata dal titolare (le
  righe fra i marcatori si toccano solo su sua richiesta) + schede generate da `scripts/validazione_strumenti.py`. `extract/`: strumenti di sviluppo per leggere i fogli Excel (non servono
  in produzione). `scripts/serve_live.py`, `scripts/avvia.py`, `Avvia StruttureMenni.{bat,command}`: avvio.

## Comandi
```
uv sync                                                         # una volta
uv run python -m strutture.web --host 127.0.0.1 --port 8013     # prova rapida in primo piano; il server dell'ufficio (porta 8000) parte SOLO come dice la regola dura 2
uv run pytest -q                                                # calcoli, API, moduli condivisi
uv run pytest tests/e2e -m e2e -q                               # browser (circa 3 minuti; prima: uv run playwright install chromium)
node --test tests/e2e/*.mjs                                     # test JavaScript puri
uv run ruff check .                                             # stile
uv run python -m strutture.shared.divergences.check --strict    # registro: deve dare 0 errori
uv run python -m strutture.shared.divergences.render            # rigenera docs/divergences/*.md
uv run python scripts/validazione_strumenti.py                  # rigenera docs/VALIDAZIONE_STRUMENTI.md (schede dai dati; la tabella di stato è del titolare e viene conservata)
```
Numeri attesi al 2026-09-22: vedi `docs/CONSEGNA.md`, sezione "Stato". Un lavoro non è finito finché quei
comandi non sono tutti verdi.

## Regole dure
1. Mai fermare un processo per nome (`pkill -f`, `killall`, `taskkill /IM`, `lsof | xargs kill`). Avvia i tuoi
   server di prova su una porta libera fra 8012 e 8015, annota il PID e ferma solo quello.
2. Il server dell'ufficio gira sulla porta 8000, avviato con `uv run python scripts/serve_live.py --host … --port 8000`
   (la riga di comando non contiene il nome del modulo, apposta). Riavvialo solo dopo averlo detto al titolare.
3. Interfaccia: si lavora nella copia `src/strutture/web/static_next/` (se manca: `cp -R static static_next`),
   servita con `--static-dir src/strutture/web/static_next --data-dir build/ui-dev-data`, si prova con
   `STRUTTURE_E2E_STATIC_DIR=src/strutture/web/static_next uv run pytest tests/e2e -m e2e -q`, poi si promuove:
   `rm -rf build/static_prev_backup && mv src/strutture/web/static build/static_prev_backup && cp -R
   src/strutture/web/static_next src/strutture/web/static && sed -i '' 's#web/static_next/js/#web/static/js/#'
   tests/e2e/*.mjs`, si rilancia la suite e2e su `static/`, si committa `src/strutture/web/static tests/e2e`.
4. CSP rigida: niente stile o script in linea, mai `innerHTML`; `el.style.setProperty` va bene. Nessun CDN,
   font ospitati in locale. Ogni comando da tastiera; icona + parola, mai solo il colore.
5. Modalità Excel: ogni ramo che riproduce il foglio è `if legacy("<unita>/<slug>", legacy_compat):` con una
   voce di registro; gli esempi degli strumenti non contengono mai `legacy_compat`; `check --strict` resta a 0
   errori (è anche un test permanente). Formato dei JSON del registro: `json.dumps(…, ensure_ascii=False,
   indent=1)`, senza a capo finale.
6. Regola del committente "segnala e correggi nel codice": un difetto trovato in un calcolo si corregge in
   modalità standard con una voce di registro (la modalità Excel conserva il foglio); mai nasconderlo nella
   relazione o in un avviso.
7. Formule: ogni strumento ha `relazione*.py`; il harness (`tests/shared/relazione/harness.py`) valuta ogni
   formula stampata contro il numero dello strumento, quindi un cambiamento di calcolo senza cambiare la
   traccia fallisce lì: è voluto. Dopo ogni nuovo calcolo, far rileggere il testo RESO delle formule a un
   modello forte: ha trovato dieci difetti reali in tre ondate.
8. Verifiche (`checks`): nomi brevi (≤ 25 caratteri circa, in italiano, senza trattini bassi) e dettagli corti
   (`"3,93 >= 3,56 cm²/m"`), altrimenti `test_wall_results_height_budget` fallisce. Ingressi piatti, uscite
   annidate; ogni campo con descrizione italiana, unità, simbolo, gruppo; `advanced: true` sui coefficienti rari.
9. Schizzi: `tests/shared/test_sketch_layout.py` impone le stesse regole del renderer (testo delle frecce alla
   coda, quote verticali con testo all'esterno, al massimo 8 testi per vista, nota "Schema non in scala");
   `tests/shared/test_sketch_campi.py` impone che ogni testo con il simbolo di un dato sia modificabile dal disegno
   (collegamento automatico per simbolo, unità e valore, altrimenti `campo="nome_campo"` sulla forma) e che un
   testo calcolato non prenda in prestito il simbolo di un dato (spec interfaccia §18).
10. Test e2e: `get_by_role("button", name="Calcola", exact=True)` (un pulsante di aiuto contiene "calcola");
    i problemi di tempistica si indagano con un file di test temporaneo in `tests/e2e`, non con uno script a
    parte; browser Playwright headless in Python con `window.print` sostituito da una funzione vuota.
11. Portabilità Windows e macOS: `pathlib`, `encoding="utf-8"` ovunque, `subprocess.run([...])` senza
    `shell=True`, nessun percorso assoluto, nomi di file ASCII (`docs/BUILD_CONTRACT.md`, Portability).
12. File piccoli: moduli di calcolo ≤ 150 righe, funzioni ≤ 40, moduli JS ≤ 400. Dati immutabili (modelli
    congelati, tuple), nessuna mutazione sul posto, niente numeri magici (costanti col nome della clausola).
13. Non committare mai i fogli Excel (`*.xls`, `*.xlsx`, `workbooks/`), `var/`, `.env`, chiavi. La chiave MIDAS
    vive in `MIDAS_MAPI_KEY` (ambiente) o nella sessione del browser (intestazione `X-Midas-Key`): mai nei log,
    mai nelle risposte, mai nel codice.
14. Fai il lavoro tu stesso: non delegare ad altri agenti a catena. Se il titolare vuole più agenti, ognuno
    lavora su file disgiunti e committa il proprio pacchetto appena finito.
15. Non modificare `pyproject.toml` né `src/strutture/shared/{tool,report,numeric,tables}.py` senza dirlo prima al
    titolare: sono il contratto condiviso da tutti gli strumenti e dall'interfaccia, che si costruisce dallo schema.

## Come si fa una modifica
1. Leggi la specifica pertinente (`docs/specs/<unità>.md` per un calcolo, `docs/ui/WORKBENCH_SPEC.md` e
   `docs/ui/DESIGN_SPEC.md` per l'interfaccia, `docs/integrations/MIDAS.md` per MIDAS).
2. Scrivi prima il test che fallisce (unit/golden/oracle per i calcoli, e2e per l'interfaccia), poi il codice.
3. Esegui i comandi della sezione "Comandi" che il tuo cambiamento tocca; per i calcoli anche il registro e le
   formule; per l'interfaccia la suite e2e completa.
4. Aggiorna `docs/CONSEGNA.md` se cambi lo stato del progetto (numeri dei test, lavori aperti).
5. Un commit locale per pacchetto finito, messaggio `tipo: descrizione` (feat, fix, refactor, docs, test,
   chore, perf, ci). Non creare rami o remoti senza che il titolare lo chieda.
6. Riferisci al titolare in italiano: cosa è cambiato, cosa hai verificato, cosa deve controllare lui
   nell'app (quale strumento, quale esempio), cosa resta aperto.

## Ricette
- Nuovo strumento: copia la struttura di `members/ca_taglio_non_armato/`, segui `docs/BUILD_CONTRACT.md`
  (modelli congelati con `Field(description=…, json_schema_extra={"unit": …, "group": …, "symbol": …})`,
  `TOOLS` in `tool.py`, `Tool(..., example=…)`, schizzo, relazione, test ≥ 80 %). L'interfaccia si costruisce
  da sola dallo schema: non serve toccare il JavaScript.
- Correzione di un calcolo: test con il valore atteso a mano → codice in modalità standard → voce di registro
  (`src/strutture/data/divergences/<unita>.json`, poi `render`) → `legacy(...)` sul ramo Excel → harness delle
  formule → suite completa.
- Collegamento fra strumenti ("Usa in…"): `provides`/`accepts` in `json_schema_extra` dei campi, chiave
  `<ambito>.<nome_unità>`; il test permanente di `shared/collegamenti.py` rifiuta i collegamenti incoerenti.
- Voce del registro respinta dal titolare (la pagina Registro promette che "le applica un agente"): leggere stato e
  nota della firma (`GET /api/divergences/{unita}/{slug}` o la pagina), adeguare la modalità standard a quanto
  chiede la nota (spesso: il comportamento del foglio), aggiornare voce JSON, test e golden, `render`,
  `check --strict`, harness delle formule; riferire al titolare voce per voce.
- Avviso legato a un ingresso: `success(..., avvisi_campi={testo: "nome_campo"})` (spec §17).
- Firme del registro, progetti, elementi: API in `routes/divergences.py` e `routes/progetti.py`; SQLite via
  repository in `storage/`; blocco ottimistico con `revisione` (409 = ricarica e riprova).

## Modelli e costi (consiglio, non obbligo)
Costruire e correggere con modelli economici e veloci; revisione ingegneristica e rilettura delle formule con
un modello forte; le decisioni di architettura si scrivono nei documenti prima di costruire. Ogni prompt a un
agente costruttore deve contenere: "fai il lavoro tu stesso, non delegare" e "non fermare processi per nome".
