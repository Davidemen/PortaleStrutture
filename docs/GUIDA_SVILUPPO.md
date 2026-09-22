# Guida allo sviluppo: rami, commit, issue, validazione

Riferimento breve per chi sviluppa e valida PortaleStrutture (repository
`github.com/Davidemen/PortaleStrutture`). Le regole tecniche su come si scrive il codice sono in `CLAUDE.md`;
qui c'è solo il modo di lavorare insieme.

## 1. I rami

| Ramo | A cosa serve | Chi lo muove |
|---|---|---|
| `main` | La versione rilasciata. Quello che c'è qui è usato in ufficio. | Solo avanzamento rapido (*fast-forward*) a `sviluppo` al momento di un rilascio. |
| `sviluppo` | Il ramo di lavoro comune: qui confluiscono le funzioni finite e validate. Nasce da `main`. | Unioni delle richieste di unione (*pull request*) approvate. |
| `funzione/<nome>` | Una funzione grande o una modifica di calcolo. Nasce da `sviluppo`. | Chi la sviluppa. |
| `correzione/<nome>` | Un difetto. Nasce da `sviluppo` (o da `main` se urgente, vedi §5). | Chi lo corregge. |

Regole:
- Su `main` non si committa mai direttamente. `main` non ha mai commit che `sviluppo` non abbia già.
- Nomi dei rami in italiano, minuscoli, con trattini: `funzione/varianti-affiancate`, `correzione/neve-alfa-zero`.
  Se il ramo nasce da una issue, il numero in testa: `funzione/42-tabella-progetto`.
- Un ramo = un argomento. Se si allarga, si divide.
- Modifiche piccole (un testo, un refuso) possono andare direttamente su `sviluppo`, ma sempre con le suite verdi.

## 2. Il ciclo di una funzione

1. **Issue.** Ogni lavoro parte da una issue su GitHub (§4). Chi lo prende se la assegna.
2. **Ramo.** In una cartella di lavoro separata (git worktree): la cartella principale resta su `main` per il server
   dell'ufficio e non si tocca (`CLAUDE.md`, regola 2):
   ```
   git fetch
   git worktree add ../PortaleStrutture-wt/42-tabella-progetto -b funzione/42-tabella-progetto origin/sviluppo
   cd ../PortaleStrutture-wt/42-tabella-progetto && uv sync
   ```
3. **Lavoro.** Prima il test che fallisce, poi il codice (`CLAUDE.md`, "Come si fa una modifica"). Commit piccoli.
4. **Tenersi aggiornati.** Se `sviluppo` va avanti mentre si lavora: `git fetch && git rebase origin/sviluppo`
   (oppure `git merge origin/sviluppo` se il ramo è già condiviso con altri).
5. **Controlli locali**, tutti verdi prima di chiedere l'unione:
   ```
   uv run pytest -q
   uv run ruff check .
   uv run python -m strutture.shared.divergences.check --strict
   node --test tests/e2e/*.mjs
   uv run pytest tests/e2e -m e2e -q        # se tocca l'interfaccia
   ```
6. **Richiesta di unione (PR)** verso `sviluppo`, compilando il modello (cosa, perché, come provato, cosa
   controllare nell'app). Scrivere `Chiude #42` nel testo: la issue si chiude da sola all'unione.
7. **Controlli automatici.** GitHub esegue la suite (Windows e macOS) su ogni PR. Se è rossa, non si unisce.
8. **Validazione** (§3), poi **unione** con "Squash and merge" (un commit per funzione su `sviluppo`) oppure
   "Rebase and merge" se i commit del ramo sono già puliti. Il ramo si cancella dopo l'unione.

## 3. La validazione

Il validatore è l'esperto di dominio: decide se un risultato è giusto dal punto di vista ingegneristico. Il
programma può essere corretto per i test e sbagliato per la norma; il validatore è l'ultima difesa.

Cosa controlla in ogni PR che tocca un calcolo:
- **Numeri.** Aprire l'app sul ramo (`uv run python -m strutture.web --port 8013`), caricare l'esempio dello
  strumento e un caso suo di cui conosce il risultato. Confrontare.
- **Relazione.** Le formule stampate sono quelle della norma, con clausole giuste.
- **Registro delle correzioni.** Ogni differenza dal foglio Excel ha una voce in `src/strutture/data/divergences/`
  (pagina Registro dell'app). Il validatore la firma o la respinge con una nota.
- **Scelte ingegneristiche.** Nessun coefficiente o ipotesi deve essere stato scelto dallo sviluppatore senza
  dirlo: queste scelte stanno in `docs/DECISIONI_DA_CONFERMARE.md` e le prende il titolare.
- **Stato dello strumento** in `docs/VALIDAZIONE_STRUMENTI.md`, aggiornato solo su sua indicazione.

Per le PR solo d'interfaccia basta provare il flusso nell'app e guardare che i controlli automatici siano verdi.

Esito: su GitHub "Approve" (si unisce) o "Request changes" con commenti riga per riga. Chi sviluppa non approva
la propria PR: se sviluppatore e validatore sono la stessa persona, la seconda lettura la fa il titolare.

## 4. Issue: come si tiene traccia del lavoro

Tutto il lavoro, i difetti e le domande stanno nelle **Issue** di GitHub. Niente liste parallele in email o chat:
se una cosa non è in una issue, non esiste.

Tre modelli (pulsante "New issue"):
- **Difetto**: cosa succede, cosa ci si aspettava, strumento, dati per riprodurlo (esportazione o valori).
- **Nuova funzione**: cosa serve e perché, come si capirà che è fatta.
- **Decisione ingegneristica**: una scelta che spetta al titolare (coefficiente, clausola, ipotesi), con le
  alternative. Una volta decisa si riporta in `docs/DECISIONI_DA_CONFERMARE.md`.

Etichette:

| Etichetta | Significato |
|---|---|
| `difetto-calcolo` | Un numero è sbagliato. Priorità massima. |
| `difetto-interfaccia` | L'app si comporta male, i numeri sono giusti. |
| `funzione` | Nuova funzione o miglioria. |
| `decisione` | Serve una scelta del titolare. |
| `da-validare` | Pronto, aspetta il validatore. |
| `documentazione` | Solo documenti. |
| `urgente` | Blocca il lavoro in ufficio. |

I **traguardi** (*milestone*) raccolgono le issue di un rilascio (`v0.1.0`, …). Chi apre una issue non deve
scegliere tutto: bastano titolo, modello compilato e un'etichetta; il resto lo sistema chi la prende.

Commit e PR citano la issue: `fix: neve con α = 0 non disegna la falda (#17)`.

## 5. Rilasci e versioni

- Numerazione `vMAGGIORE.MINORE.CORREZIONE`. Finché siamo sotto `v1.0.0` il programma è in prova: i risultati si
  usano solo dopo verifica indipendente.
  - CORREZIONE (`v0.1.1`): solo difetti corretti.
  - MINORE (`v0.2.0`): funzioni nuove.
  - `v1.0.0`: tutti gli strumenti validati e il registro firmato.
- Rilascio, fatto da chi ha i permessi:
  ```
  git fetch                                  # suite tutte verdi su origin/sviluppo
  git push origin origin/sviluppo:main       # avanzamento rapido; se rifiuta, main ha qualcosa che sviluppo non ha: fermarsi
  git tag -a v0.1.0 -m "v0.1.0: <riassunto>" origin/sviluppo
  git push origin v0.1.0
  ```
  Poi nella cartella principale (sempre su `main`, `CLAUDE.md` regola 2): `git pull --ff-only` e `strutture riavvia`.
  Poi su GitHub "Releases → Draft a new release" dal tag, con l'elenco delle issue chiuse.
- Correzione urgente in ufficio: ramo `correzione/<nome>` da `main`, PR verso `sviluppo`, poi rilascio come sopra.
  Non si committa mai su `main` a mano.
- Dopo un rilascio il server dell'ufficio si riavvia sulla nuova versione (`CLAUDE.md`, regola dura 2).

## 6. Commit

- In italiano, formato `tipo: descrizione` al presente, minuscolo, senza punto finale. Tipi: `feat` (funzione),
  `fix` (difetto), `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.
- Un commit = una modifica che sta in piedi da sola (la suite passa).
- Mai nel repository: fogli Excel, `var/`, `.env`, chiavi (MIDAS compresa). Il repository è **pubblico**.

## 7. Da fare una volta sola (proprietario del repository su GitHub)

- Settings → Branches → regole per `main` e `sviluppo`: niente push forzati né cancellazioni; su `sviluppo`
  PR obbligatoria con 1 approvazione e controlli verdi; su `main` solo chi fa i rilasci.
- Settings → General → Pull Requests: abilitare "Squash merging" e "Rebase merging", "Automatically delete head
  branches".
- Default branch: `sviluppo` (così le PR puntano lì in automatico).
