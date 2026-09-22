# StruttureMenni

Strumenti di calcolo strutturale (NTC 2018 / Eurocodici) nati da 23 fogli Excel dello studio e riscritti in
Python con un'interfaccia web. 31 strumenti: carichi (neve, vento, sisma), calcestruzzo armato, acciaio,
geotecnica, fondazioni. Ogni calcolo mostra verifiche, avvisi, uno schizzo dell'elemento e una relazione con
le formule; i progetti raccolgono gli elementi di un lavoro e stampano una relazione unica.

## Avvio rapido
1. Installare `uv` una volta sola: <https://docs.astral.sh/uv/> (Windows: PowerShell,
   `powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"`).
2. Aprire un terminale nella cartella del progetto ed eseguire `uv sync` (una volta; scarica Python e le librerie).
3. Doppio clic su `Avvia StruttureMenni.bat` (Windows) o `Avvia StruttureMenni.command` (macOS).
   Si apre il browser su <http://127.0.0.1:8000>. Chiudere la finestra del terminale per fermare il programma.

Tutto gira sul vostro computer: nessun dato esce dall'ufficio. I progetti salvati stanno nel file
`var/strutture.db` (vedi la guida per il backup).

## Documentazione
| Documento | Per chi |
|---|---|
| `docs/GUIDA_PROPRIETARIO.md` | chi gestisce e usa il programma, senza competenze di programmazione |
| `docs/CONSEGNA.md` | stato del progetto alla consegna, lavori aperti, cosa aspetta una decisione |
| `docs/DECISIONI_DA_CONFERMARE.md` | scelte tecniche che l'ingegnere responsabile deve confermare |
| `docs/VERIFICA_WINDOWS.md`, `docs/VERIFICA_MIDAS.md` | controlli da fare una volta sul PC dell'ufficio e con MIDAS NX |
| `CLAUDE.md` (e `AGENTS.md`) | istruzioni per gli agenti di sviluppo (Claude Code o simili) |
| `docs/INDICE.md` | indice di tutta la documentazione, con la lingua di ogni file |

## Comandi essenziali
```
uv run python scripts/serve_live.py --host 127.0.0.1 --port 8000   # server da lasciare acceso (senza aprire il browser)
uv run pytest -q                                              # test dei calcoli e dell'API
uv run pytest tests/e2e -m e2e -q                             # test del browser (circa 3 minuti)
uv run python -m strutture.shared.divergences.check --strict  # coerenza del registro delle correzioni
```
