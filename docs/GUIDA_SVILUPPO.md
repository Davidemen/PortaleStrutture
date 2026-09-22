# Guida allo sviluppo: branch, commit, issue, validazione

Riferimento breve per chi sviluppa e valida PortaleStrutture (repository
`github.com/Davidemen/PortaleStrutture`). Le regole tecniche su come si scrive il codice sono in `CLAUDE.md`;
qui c'è solo il modo di lavorare insieme. I termini di git e GitHub si usano in inglese (branch, commit, merge,
pull request, release, fast-forward, worktree, issue, milestone), come i nomi dei branch.

## 1. I branch

| Branch | A cosa serve | Chi lo muove |
|---|---|---|
| `main` | La release in uso in ufficio. | Solo fast-forward a `develop` al momento di una release. |
| `develop` | Il branch di lavoro comune: qui confluiscono le funzioni finite e validate. Nasce da `main`. | Merge delle pull request approvate. |
| `feat/<nome>` | Una funzione nuova o una modifica di calcolo. Nasce da `develop`. | Chi la sviluppa. |
| `fix/<nome>` | Un difetto. Nasce da `develop` (o da `main` se urgente, vedi §5). | Chi lo corregge. |
| `docs/`, `refactor/`, `test/`, `chore/`, `perf/`, `ci/<nome>` | Gli altri tipi di lavoro, come i tipi di commit (§6). Nascono da `develop`. | Chi ci lavora. |

Regole:
- Su `main` non si committa mai direttamente. `main` non ha mai commit che `develop` non abbia già.
- Nomi dei branch in inglese, minuscoli, con trattini: `feat/side-by-side-variants`, `fix/snow-alpha-zero`.
  Se il branch nasce da una issue, il numero in testa: `feat/42-project-table`.
- Un branch = un argomento. Se si allarga, si divide.
- Modifiche piccole (un testo, un refuso) possono andare direttamente su `develop`, ma sempre con le suite verdi.
- Ogni branch si lavora nel suo worktree, mai nella cartella principale del repository, che resta su `main` per
  il server dell'ufficio (`CLAUDE.md`, regola 2).

## 2. Il ciclo di una funzione

1. **Issue.** Ogni lavoro parte da una issue su GitHub (§4). Chi lo prende se la assegna.
2. **Branch e worktree.** Dalla cartella principale, senza cambiarne il branch:
   ```
   git fetch
   git worktree add ../PortaleStrutture-wt/42-project-table -b feat/42-project-table origin/develop
   cd ../PortaleStrutture-wt/42-project-table && uv sync
   ```
3. **Lavoro.** Prima il test che fallisce, poi il codice (`CLAUDE.md`, "Come si fa una modifica"). Commit piccoli.
4. **Tenersi aggiornati.** Se `develop` va avanti mentre si lavora: `git fetch && git rebase origin/develop`
   (oppure `git merge origin/develop` se il branch è già condiviso con altri).
5. **Controlli locali**, tutti verdi prima di aprire la pull request:
   ```
   uv run pytest -q
   uv run ruff check .
   uv run python -m strutture.shared.divergences.check --strict
   node --test tests/e2e/*.mjs
   uv run pytest tests/e2e -m e2e -q        # se tocca l'interfaccia
   ```
6. **Pull request** verso `develop`, compilando il modello (cosa, perché, come provato, cosa controllare
   nell'app). Scrivere `Closes #42` nel testo: la issue si chiude da sola al merge.
7. **Controlli automatici.** GitHub esegue la suite (Windows e macOS) su ogni pull request. Se è rossa, niente merge.
8. **Validazione** (§3), poi **merge** con "Squash and merge" (un commit per funzione su `develop`) oppure
   "Rebase and merge" se i commit del branch sono già puliti. Dopo il merge si cancellano il branch e il worktree
   (`git worktree remove ../PortaleStrutture-wt/42-project-table`).

## 3. La validazione

Il validatore è l'esperto di dominio: decide se un risultato è giusto dal punto di vista ingegneristico. Il
programma può essere corretto per i test e sbagliato per la norma; il validatore è l'ultima difesa.

Cosa controlla in ogni pull request che tocca un calcolo:
- **Numeri.** Aprire l'app sul branch (dal suo worktree, sulla porta del branch: `CLAUDE.md`, regola 1), caricare
  l'esempio dello strumento e un caso suo di cui conosce il risultato. Confrontare.
- **Relazione.** Le formule stampate sono quelle della norma, con clausole giuste.
- **Registro delle correzioni.** Ogni differenza dal foglio Excel ha una voce in `src/strutture/data/divergences/`
  (pagina Registro dell'app). Il validatore la firma o la respinge con una nota.
- **Scelte ingegneristiche.** Nessun coefficiente o ipotesi deve essere stato scelto dallo sviluppatore senza
  dirlo: queste scelte stanno in `docs/DECISIONI_DA_CONFERMARE.md` e le prende il titolare.
- **Stato dello strumento** in `docs/VALIDAZIONE_STRUMENTI.md`, aggiornato solo su sua indicazione.

Per le pull request solo d'interfaccia basta provare il flusso nell'app e guardare che i controlli automatici
siano verdi.

Esito: su GitHub "Approve" (si fa il merge) o "Request changes" con commenti riga per riga. Chi sviluppa non
approva la propria pull request: se sviluppatore e validatore sono la stessa persona, la seconda lettura la fa il
titolare.

## 4. Issue: come si tiene traccia del lavoro

Tutto il lavoro, i difetti e le domande stanno nelle **issue** di GitHub. Niente liste parallele in email o chat:
se una cosa non è in una issue, non esiste.

Tre modelli (pulsante "New issue"):
- **Difetto**: cosa succede, cosa ci si aspettava, strumento, dati per riprodurlo (esportazione o valori).
- **Nuova funzione**: cosa serve e perché, come si capirà che è fatta.
- **Decisione ingegneristica**: una scelta che spetta al titolare (coefficiente, clausola, ipotesi), con le
  alternative. Una volta decisa si riporta in `docs/DECISIONI_DA_CONFERMARE.md`.

Label:

| Label | Significato |
|---|---|
| `difetto-calcolo` | Un numero è sbagliato. Priorità massima. |
| `difetto-interfaccia` | L'app si comporta male, i numeri sono giusti. |
| `funzione` | Nuova funzione o miglioria. |
| `decisione` | Serve una scelta del titolare. |
| `da-validare` | Pronto, aspetta il validatore. |
| `documentazione` | Solo documenti. |
| `urgente` | Blocca il lavoro in ufficio. |

Le **milestone** raccolgono le issue di una release (`v0.1.0`, …). Chi apre una issue non deve scegliere tutto:
bastano titolo, modello compilato e una label; il resto lo sistema chi la prende.

Commit e pull request citano la issue: `fix: neve con α = 0 non disegna la falda (#17)`.

## 5. Release e versioni

- Numerazione `vMAJOR.MINOR.PATCH`. Finché siamo sotto `v1.0.0` il programma è in prova: i risultati si usano
  solo dopo verifica indipendente.
  - PATCH (`v0.1.1`): solo difetti corretti.
  - MINOR (`v0.2.0`): funzioni nuove.
  - `v1.0.0`: tutti gli strumenti validati e il registro firmato.
- Release, fatta da chi ha i permessi, senza cambiare il branch di nessuna cartella:
  ```
  git fetch                                   # suite tutte verdi su origin/develop
  git push origin origin/develop:main         # fast-forward; se rifiuta, main ha qualcosa che develop non ha: fermarsi
  git tag -a v0.1.0 -m "v0.1.0: <riassunto>" origin/develop
  git push origin v0.1.0
  ```
  Poi nella cartella principale (sempre su `main`, `CLAUDE.md` regola 2): `git pull --ff-only` e `strutture riavvia`,
  dopo averlo detto al titolare. Infine su GitHub "Releases → Draft a new release" dal tag, con l'elenco delle
  issue chiuse.
- Hotfix in ufficio: branch `fix/<nome>` da `main`, pull request verso `develop`, poi release come sopra.
  Non si committa mai su `main` a mano.

## 6. Commit

- In italiano, formato `tipo: descrizione` al presente, minuscolo, senza punto finale. Tipi: `feat` (funzione),
  `fix` (difetto), `refactor`, `docs`, `test`, `chore`, `perf`, `ci`.
- Un commit = una modifica che sta in piedi da sola (la suite passa).
- Mai nel repository: fogli Excel, `var/`, `.env`, chiavi (MIDAS compresa). Il repository è **pubblico**.

## 7. Da fare una volta sola (proprietario del repository su GitHub)

- Settings → Branches → regole per `main` e `develop`: niente push forzati né cancellazioni; su `develop`
  pull request obbligatoria con 1 approvazione e controlli verdi; su `main` solo chi fa le release.
- Settings → General → Pull Requests: abilitare "Squash merging" e "Rebase merging", "Automatically delete head
  branches".
- Default branch: `develop` (così le pull request puntano lì in automatico).
