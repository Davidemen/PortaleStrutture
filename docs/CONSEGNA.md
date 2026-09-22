# Consegna — StruttureMenni (aggiornata il 2026-09-22)

Scritta per chi riceve il progetto: il titolare (vedi `docs/GUIDA_PROPRIETARIO.md`) e gli agenti di sviluppo che
lavoreranno per lui (vedi `CLAUDE.md`). Lo stato qui sotto è verificato alla data indicata: non ricavarlo di nuovo.

## 1. Cos'è
Strumenti di calcolo strutturale (NTC 2018 / Eurocodici) portati da 23 fogli Excel dello studio al pacchetto Python
`strutture` (31 strumenti) con interfaccia web FastAPI + JavaScript puro. Sviluppato dal 2026-09-20 al 2026-09-22
con agenti, in oltre 60 commit; tutto ciò che conta è nel repository, nulla dipende dalla macchina di sviluppo.
Gira su macOS (sviluppo) e Windows (scritto per, non ancora provato dall'ufficio: `docs/VERIFICA_WINDOWS.md`).

## 2. Stato alla consegna
- Git: remoto `origin` = github.com/Davidemen/PortaleStrutture (pubblico). Rami `main` (rilasci, solo avanzamento
  rapido) e `sviluppo` (lavoro comune); rami di funzione e issue come in `docs/GUIDA_SVILUPPO.md`.
- Suite verdi al 2026-09-22 (sera, dopo il pacchetto "Dimensiona"/"Sensibilità"/"Impostazioni", interfaccia
  §23/§24/§26): `uv run pytest -q` → 4348 superati · `uv run pytest tests/e2e -m e2e -q` → 283 superati,
  1 saltato (circa 3 minuti e mezzo) · `node --test tests/e2e/*.mjs` → 67 · `uv run ruff check .` pulito ·
  `uv run python -m strutture.shared.divergences.check --strict` → 0 errori (26 avvertimenti di clausola vuota,
  innocui).
- Interfaccia servita: `src/strutture/web/static/`. Copia di lavoro: `src/strutture/web/static_next/` (ignorata da
  git; identica a `static/` dopo la promozione del 2026-09-22). Il flusso di lavoro e di promozione è in `CLAUDE.md`, regola 3.
- Server: `uv run python scripts/serve_live.py --host 127.0.0.1 --port 8000` (il lanciatore esiste perché una volta
  un agente ha fermato il server dell'ufficio con `pkill -f strutture.web`; la sua riga di comando non contiene
  il nome del modulo). Controllo: `curl -s http://127.0.0.1:8000/api/tools`.
- Dati: `var/strutture.db` (SQLite: firme del registro, progetti, elementi, revisioni). Registro delle correzioni:
  209 voci, tutte "da confermare".

## 3. In corso
Nessun lavoro in corso. Le ultime tre sezioni della specifica dell'interfaccia (`docs/ui/WORKBENCH_SPEC.md` §15
"Usa in…", §16 ritiro della modalità Excel per strumento, §14.3 ripristino degli elementi eliminati) sono state
completate, provate con la suite e2e (`test_usa_in.py`, `test_excel_ritirato.py`, `test_progetti.py`) e promosse in
`static/` il 2026-09-22. Il server dell'ufficio (porta 8000) è stato riavviato alle 14:54 sull'ultimo commit: serve
l'interfaccia promossa e il codice corrente (verificato: l'API restituisce i collegamenti `campo` degli schizzi).

## 4. Lavori aperti, in ordine
1. In attesa del titolare (non iniziare, ricordarglielo): verifica su Windows (`docs/VERIFICA_WINDOWS.md`,
   incluso il lanciatore `Avvia StruttureMenni.bat`); verifica MIDAS dal vivo (`docs/VERIFICA_MIDAS.md`); firma
   del registro delle correzioni (pagina `#/registro`); validazione strumento per strumento
   (`docs/VALIDAZIONE_STRUMENTI.md`: sei passi, tabella di stato compilata da lui o su sua richiesta, schede
   rigenerate con `uv run python scripts/validazione_strumenti.py`); le decisioni di
   `docs/DECISIONI_DA_CONFERMARE.md`; poi i lavori rinviati di `docs/ROADMAP.md`: GitHub + test automatici,
   griglia di pericolosità sismica, relazione DOCX, MIDAS fase 2.
2. Testi modificabili nel disegno (`docs/ui/WORKBENCH_SPEC.md` §18): quote, etichette, testi delle frecce e dei
   diagrammi si collegano al campo in automatico per simbolo, unità e valore mostrato; dove il disegno stampa un
   altro simbolo o unità, o un valore guidato da un dato, lo schizzo mette `campo=` (fatto per tutti gli strumenti:
   cedimenti `B`, trave di collegamento `B`/`H`, muro `H` → `h_muro_m`, neve `α`, sezione H rimpiattata `h`/`b`, taglio
   non armato `b` e `d` → `h`). Regola permanente: `tests/shared/test_sketch_campi.py` fallisce se un testo dello
   schizzo d'esempio porta il simbolo di un dato senza essere collegato, o se `campo=` nomina un campo inesistente;
   un testo calcolato omonimo di un dato va rinominato (fatto: punzonamento `a` → `a_gov`, cedimenti `Δz` → `s`).
   Restano testo semplice, giustamente, i risultati e le somme di più dati (muro `B`, punzonamento `2d`, neve-accumulo `l_s`).
3. Piccoli seguiti lato calcolo (facoltativi): altri collegamenti tipizzati in `src/strutture/shared/collegamenti.py`
   (plinto su pali → punzonamento richiede prima uscite in mm); `avvisi_campi` per gli avvisi degli strumenti
   diversi da muro, plinti isolati, travi, vento (`docs/BUILD_CONTRACT.md`, sezione sugli avvisi legati a un solo campo).
4. Difetti noti minori. Corretti il 2026-09-22 dalle segnalazioni del titolare: menu "⋯" della barra Dati sotto la
   barra laterale; simboli con pedice lungo sopra la descrizione (colonna 4,5 rem + a capo solo dopo virgola o barra,
   `js/symbols.js`); schizzo CPE con due impaginazioni diverse; pulsante "Comprimi la barra di navigazione" sotto il
   bordo dello schermo (il token `--head-h` era 23 px più corto dell'intestazione reale: ora è derivato e l'intestazione
   è bloccata su di esso). Restano: `neve-carico-falda` disegna la falda inclinata anche con α = 0°; lo schizzo della mensola
   tozza è schematico; i simboli con doppio pedice (`M_Ed/M_Rd`) si leggono male nelle evidenze della sintesi.
5. Blocco 1 (rifattorizzazione regola 12 + specifica §19-22) integrato il 2026-09-22; interfaccia §19-22 da costruire.
6. Interfaccia §23/§24/§26 (pacchetto "dimensiona_ui", 2026-09-22): finestre "Dimensiona" e "Sensibilità"
   (`js/dimensiona*.js`, `js/sensibilita*.js`), pagina `#/impostazioni` (`js/impostazioni*.js`), voce nella barra
   laterale e nella tavolozza, scorciatoie `g d`/`g s`/`g i`, link "Dimensiona" nel popover dello schizzo (§18),
   grafico con linea dell'obiettivo e fino a 5 serie (`js/chart.js`, `js/chart-axis.js`). Provato con
   `tests/e2e/test_dimensiona.py`, `test_sensibilita.py`, `test_impostazioni.py` e i pure-test `.mjs` omonimi.
   Restano aperti (non bloccanti): la tabella "Storia delle modifiche" mostra un diff testuale semplice (non ogni
   caso limite del §26.8 è coperto da un test dedicato); non è stata provata la vista a foglio intero sotto 720 px
   per ogni combinazione di campi lunga (solo un controllo di visibilità generico); i test e2e coprono i percorsi
   principali della specifica, non ogni comportamento elencato in §23.6/§24.3/§26.10 (es. campionamento non
   monotono, limite di validità, conflitto 409 con due schede aperte).

## 5. Decisioni che spettano all'ingegnere
Tutte in `docs/DECISIONI_DA_CONFERMARE.md`. Un agente non le prende: le segnala e chiede.

## 6. Dove stanno le cose
La mappa del codice è in `CLAUDE.md`. Documentazione: indice in `docs/INDICE.md`. In sintesi: regole di
costruzione `docs/BUILD_CONTRACT.md`; architettura `docs/architecture*.md` (`-batch2.md` §9 = decisioni del
committente D1–D5, `-phase2.md` formule, `-phase3.md` progetti, `-phase4.md` motore M-N e capacità portante);
piano `docs/ROADMAP.md`; validazione `docs/VALIDAZIONE_STRUMENTI.md`; interfaccia `docs/ui/DESIGN_SPEC.md`, `docs/ui/WORKBENCH_SPEC.md` §0–17,
`docs/ui/REVIEW_FABLE_2026-09-21.md`; MIDAS `docs/integrations/MIDAS.md`; specifiche per strumento `docs/specs/`.

## 7. Convenzioni e lezioni (ognuna è costata tempo una volta)
- Modalità Excel: `legacy_compat=True` riproduce il foglio, errori inclusi; la modalità standard li corregge; ogni
  ramo è `legacy("<unita>/<slug>", flag)` legato a una voce del registro (`ramo` codice | condiviso | nessuno);
  gli esempi degli strumenti non contengono mai `legacy_compat`; `check --strict` resta a 0 errori (test permanente).
- Formule: ogni strumento ha `relazione*.py`; il harness valuta ogni formula stampata contro il numero dello
  strumento, quindi un cambiamento di calcolo senza cambiare la traccia fallisce lì (voluto). La rilettura del
  testo RESO delle formule da parte di un modello forte ha trovato dieci difetti reali di calcolo in tre ondate:
  farla per ogni calcolo nuovo.
- Regola del committente "segnala e correggi nel codice": un difetto trovato in un calcolo si corregge in modalità
  standard con una voce di registro (Excel conserva il foglio), mai nascosto nella traccia.
- Verifiche: nomi brevi (≤ 25 caratteri circa) e dettagli corti (≤ 150 px circa), altrimenti
  `test_wall_results_height_budget` (900 px) fallisce; nomi in italiano, senza trattini bassi.
- Schizzi: le regole di `tests/shared/test_sketch_layout.py` modellano il testo delle frecce alla CODA e il testo
  delle quote verticali all'ESTERNO, esattamente come disegna il renderer; 8 testi per vista; nota "Schema non in scala".
- e2e: `get_by_role("button", name="Calcola", exact=True)` (l'etichetta di un pulsante di aiuto contiene
  "calcola"); i problemi di tempistica si indagano con un file di test temporaneo in `tests/e2e` (stesse fixture),
  non con uno script a parte; un browser condiviso resta bloccato dalle finestre di stampa native: usare
  Playwright headless in Python con `window.print` sostituito.
- Interfaccia: CSP rigida (niente stile o script in linea, mai `innerHTML`; `el.style.setProperty` va bene);
  nessun CDN; italiano, maiuscola solo iniziale, icona + parola mai solo colore; le relazioni esportate sono
  sempre complete e costruite da un calcolo fresco (regola del committente).
- Agenti: costruttori economici, revisori forti, modelli costosi solo per architettura o UX; ogni prompt a un
  costruttore dice "fai il lavoro tu stesso, non delegare" e "non fermare processi per nome"; i requisiti vanno
  nelle specifiche del repository e nel prompt iniziale (i messaggi a metà corsa vengono ignorati); i limiti di
  sessione hanno ucciso lavori a metà due volte: committare ogni pacchetto finito subito e non lanciare più di
  circa 5 agenti pesanti insieme.
- Server reale contro test: i test dell'API usano repository in memoria; il server con `--data-dir` passa dai
  wrapper pigri di `web/app.py`. Un metodo o un parametro mancante lì dà 500 solo in produzione: il test
  `tests/web/test_lazy_repositories.py` confronta le firme dei wrapper con i Protocol di `storage/interfaces.py`.
- Test e2e con letture di stile: leggere i colori calcolati in una sola `evaluate` dopo `wait_for_function`,
  mai una chiamata per elemento (un nodo staccato durante un ridisegno risponde con stringa vuota).
- Git: commit locali, messaggi `tipo: descrizione`; nessun remoto senza il consenso del titolare.

## 8. Primi 15 minuti per un agente nuovo
1. `git status --short`; `diff -rq src/strutture/web/static src/strutture/web/static_next` (sezione 3).
2. Avviare il server (sezione 2) e dirlo al titolare.
3. `uv run pytest -q` e `uv run python -m strutture.shared.divergences.check --strict` per confermare la base.
4. Continuare dalla sezione 4, punto 1, oppure dalla richiesta del titolare.

## 9. Trasferire il progetto su un altro computer
- Copia diretta: comprimere la cartella escludendo `.venv/`, `build/`, `.playwright-mcp/`, `.pytest_cache/`,
  `.ruff_cache/`, i file `.xls`/`.xlsx` e `workbooks/` (i fogli restano sulla condivisione dello studio). Tenere
  `.git/` (la cronologia) e `var/` (i dati) se si vogliono portare. Sull'altro computer: `uv sync`, poi il lanciatore.
- Oppure GitHub privato: `git remote add origin <url>` e `git push -u origin main`; il file `.gitignore` esclude già
  fogli, dati e segreti. Poi `git clone` sull'altro computer e `uv sync`.
