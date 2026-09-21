# Phase 3 architecture — projects and saved elements

Decisions [U]: no user management (everyone reads and edits everything; `sigla` is free text); one SQLite database
per instance (`STRUTTURE_DATA_DIR`, default `var/`); a central instance AND local installs, NO synchronisation —
**Esporta / Importa progetto** (one JSON file) is the only bridge.

## Data (contract: `src/strutture/storage/models.py`, `interfaces.py`)
`Progetto` (codice, nome, committente, note) · `Elemento` (progetto, strumento, nome "Plinto P1", inputs = exactly
what the form submits, `sintesi` = small result summary for lists, stato, modalità, versione_app, provenienza e.g.
a MIDAS import) · `RevisioneElemento` (append-only history, written on every save, with optional sigla + nota).
- **Optimistic locking:** every update/delete carries the `revisione` the caller last read; stale -> `ConflictError`
  -> HTTP 409 "Modificato da un altro utente: ricarica e riprova" (the UI then offers reload or save-as-copy).
- **Soft delete** (`eliminato` timestamp) with restore — without accounts an accidental delete must be reversible.
- `stato`: `verificato` = saved together with a successful result; `dati_modificati` = inputs saved without a
  matching result (or the tool's code-version changed since); `non_verificato` = saved with failing checks.
- Inputs are stored as JSON text; large reaction tables are allowed (body limit 8 MB). No result payloads are
  stored — results are always recomputed from the inputs (the tool version is recorded for traceability).
- Migration 2 adds `progetto`, `elemento`, `elemento_revisione` (indexes on progetto_id, aggiornato). Migration 1
  (sign-off) is untouched.

## Export / import
`GET /api/progetti/{id}/esporta` -> `{"formato": "strutture-progetto", "versione": 1, "esportato": ISO, "app":
versione, "progetto": {...}, "elementi": [{..., "revisioni": [...]}]}`. `POST /api/progetti/importa` validates the
format/version and every element's `strumento` (unknown tools are imported but flagged), creates NEW ids, and if a
project with the same `codice`+`nome` exists imports as "nome (importato AAAA-MM-GG)" — never overwrites.

## HTTP API (`src/strutture/web/routes/progetti.py`)
`GET/POST /api/progetti` · `GET/PUT/DELETE /api/progetti/{id}` (+ `POST …/ripristina`) ·
`GET/POST /api/progetti/{id}/elementi` · `GET/PUT/DELETE /api/elementi/{id}` · `POST /api/elementi/{id}/duplica` ·
`GET /api/elementi/{id}/revisioni` · export/import as above. Italian messages, standard envelope, 404/409/400;
handlers are plain `def` (threadpool); the same-origin guard and rate limit already apply.

## UI (after the workbench is live)
Project picker in the header (current project persisted per browser), **Salva in progetto** in the Dati action bar
(name prompt, optional sigla + nota, 409 handling), project page listing elements (sigla chip, nome, stato, η max,
verifica governante, aggiornato; duplicate, rename, history, delete/restore), opening an element loads its inputs
into the tool, **Relazione di progetto** = the report of every element through the same `buildRelazione` options
(spec §10–11), Esporta / Importa.
