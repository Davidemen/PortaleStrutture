# Consegna — StruttureMenni (aggiornata il 2026-09-22)

Scritta per chi riceve il progetto: il titolare (vedi `docs/GUIDA_PROPRIETARIO.md`) e gli agenti di sviluppo che
lavoreranno per lui (vedi `CLAUDE.md`). Lo stato qui sotto è verificato alla data indicata: non ricavarlo di nuovo.

## 1. Cos'è
Strumenti di calcolo strutturale (NTC 2018 / Eurocodici) portati da 23 fogli Excel dello studio al pacchetto Python
`strutture` (31 strumenti) con interfaccia web FastAPI + JavaScript puro. Sviluppato dal 2026-09-20 al 2026-09-22
con agenti, in oltre 60 commit; tutto ciò che conta è nel repository, nulla dipende dalla macchina di sviluppo.
Gira su macOS (sviluppo) e Windows (scritto per, non ancora provato dall'ufficio: `docs/VERIFICA_WINDOWS.md`).

## 2. Stato alla consegna
- Git: solo locale, ramo `main`, nessun remoto (GitHub rinviato dal committente).
- Suite verdi al 2026-09-22: `uv run pytest -q` → 4123 superati · `uv run pytest tests/e2e -m e2e -q` → 229 superati,
  1 saltato (circa 3 minuti) · `node --test tests/e2e/*.mjs` → 34 · `uv run ruff check .` pulito ·
  `uv run python -m strutture.shared.divergences.check --strict` → 0 errori (26 avvertimenti di clausola vuota,
  innocui).
- Interfaccia servita: `src/strutture/web/static/`. Copia di lavoro: `src/strutture/web/static_next/` (ignorata da
  git; oggi identica a `static/`). Il flusso di lavoro e di promozione è in `CLAUDE.md`, regola 3.
- Server: `uv run python scripts/serve_live.py --host 127.0.0.1 --port 8000` (il lanciatore esiste perché una volta
  un agente ha fermato il server dell'ufficio con `pkill -f strutture.web`; la sua riga di comando non contiene
  il nome del modulo). Controllo: `curl -s http://127.0.0.1:8000/api/tools`.
- Dati: `var/strutture.db` (SQLite: firme del registro, progetti, elementi, revisioni). Registro delle correzioni:
  209 voci, tutte "da confermare".

## 3. In corso
Un costruttore sta completando in `static_next/` le tre ultime sezioni della specifica dell'interfaccia:
`docs/ui/WORKBENCH_SPEC.md` §15 ("Usa in…", collegamenti tipizzati fra strumenti), §16 (la modalità Excel si
ritira dagli strumenti con tutte le correzioni approvate) e il ripristino degli elementi eliminati di un progetto
(§14.3). Alla fine di quel lavoro questa sezione dirà "nessun lavoro in corso" e i numeri della sezione 2
saranno aggiornati. Se trovi `static_next/` diverso da `static/` e test nuovi in `tests/e2e/` (`test_usa_in.py`,
`test_excel_ritirato.py`) senza commit, il lavoro è stato interrotto: lancia la suite e2e su `static_next/` e
decidi se completarlo o scartarlo (`rm -rf static_next && cp -R static static_next`).

## 4. Lavori aperti, in ordine
1. Chiusura del punto 3, poi promozione in `static/` e riavvio del server (avvisando il titolare).
2. In attesa del titolare (non iniziare, ricordarglielo): verifica su Windows (`docs/VERIFICA_WINDOWS.md`,
   incluso il lanciatore `Avvia StruttureMenni.bat`); verifica MIDAS dal vivo (`docs/VERIFICA_MIDAS.md`); firma
   del registro delle correzioni (pagina `#/registro`); le decisioni di `docs/DECISIONI_DA_CONFERMARE.md`; poi i
   lavori rinviati di `docs/ROADMAP.md`: GitHub + test automatici, griglia di pericolosità sismica, relazione
   DOCX, MIDAS fase 2.
3. Piccoli seguiti lato calcolo (facoltativi): altri collegamenti tipizzati in `src/strutture/shared/collegamenti.py`
   (plinto su pali → punzonamento richiede prima uscite in mm); `avvisi_campi` per gli avvisi degli strumenti
   diversi da muro, plinti isolati, travi, vento (`docs/BUILD_CONTRACT.md`, sezione sugli avvisi legati a un solo campo).
4. Difetti noti minori: `neve-carico-falda` disegna la falda inclinata anche con α = 0°; lo schizzo della mensola
   tozza è schematico; i simboli con doppio pedice (`M_Ed/M_Rd`) si leggono male nelle evidenze della sintesi.

## 5. Decisioni che spettano all'ingegnere
Tutte in `docs/DECISIONI_DA_CONFERMARE.md`. Un agente non le prende: le segnala e chiede.

## 6. Dove stanno le cose
La mappa del codice è in `CLAUDE.md`. Documentazione: indice in `docs/INDICE.md`. In sintesi: regole di
costruzione `docs/BUILD_CONTRACT.md`; architettura `docs/architecture*.md` (`-batch2.md` §9 = decisioni del
committente D1–D5, `-phase2.md` formule, `-phase3.md` progetti, `-phase4.md` motore M-N e capacità portante);
piano `docs/ROADMAP.md`; interfaccia `docs/ui/DESIGN_SPEC.md`, `docs/ui/WORKBENCH_SPEC.md` §0–17,
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
