# Verifica su Windows

Il programma è stato sviluppato e collaudato su macOS ed è scritto per girare senza modifiche su Windows 10/11.
Questa lista è ciò che va eseguito una volta sul PC Windows. Ogni comando è identico in PowerShell, cmd e zsh
(si usano opzioni sulla riga di comando, non la forma `VAR=valore comando` che solo le shell POSIX capiscono).

LibreOffice **non** serve: era usato solo sulla macchina di sviluppo per generare i dati di prova, che sono
salvati come JSON in `tests/fixtures/`.

## 1. Installazione
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"   # installa uv (una volta)
cd <cartella>\StruttureMenni
uv sync                                                                              # Python + librerie
```

## 2. Test
```powershell
uv run pytest -q                       # strumenti di calcolo, API, moduli condivisi: devono essere tutti verdi
uv run ruff check src tests            # facoltativo: controllo dello stile
```
Test nel browser:
```powershell
uv run playwright install chromium     # una volta, circa 150 MB
uv run pytest tests/e2e -m e2e -q      # test del browser (circa 3 minuti)
```

## 3. Avvio del programma
```powershell
uv run python -m strutture.web                                  # http://127.0.0.1:8000  (31 strumenti)
uv run python scripts/avvia.py                                  # come sopra, e apre il browser quando il server risponde
# oppure doppio clic su "Avvia StruttureMenni.bat" in Esplora file (controllare: si apre una console, poi il browser; chiudendo la console il server si ferma)
uv run python -m strutture.web --port 8080                      # altra porta
uv run python -m strutture.web --host 127.0.0.1,192.168.1.20    # localhost + un indirizzo della rete dell'ufficio
```
- Al primo avvio Windows Defender Firewall chiede se Python può accettare connessioni. Consentirlo sulle reti
  *private* se i colleghi devono raggiungerlo in rete; localhost funziona in ogni caso.
- L'indirizzo dopo `--host` deve essere un indirizzo di QUESTO computer (`ipconfig`); se è un indirizzo VPN e la
  VPN è spenta, l'avvio fallisce.
- Si ferma con Ctrl+C.

## 4. Cosa controllare
| Controllo | Atteso |
|---|---|
| `uv run pytest -q` | **4123 superati** (riferimento macOS, 2026-09-22), 0 falliti; i test del browser sono esclusi per impostazione predefinita |
| `uv run pytest tests/e2e -m e2e -q` | **229 superati, 1 saltato** |
| `node --test tests/e2e/*.mjs` | **34 superati** (facoltativo, serve Node ≥ 20) |
| Testo accentato (à è ù § φ γ) in etichette, errori e risultati | reso correttamente: ogni file è letto esplicitamente come UTF-8 |
| Ricerca del comune ("Forlì", "Castro") | compaiono i suggerimenti; gli omonimi mostrano la provincia |
| Uno strumento con risultato tabellare (spettro, profilo del vento) → "Scarica CSV" | si apre in Excel con separatore `;` e virgola decimale |
| "Stampa relazione" | anteprima di stampa pulita in Edge/Chrome |
| Inserimento dei decimali | il browser accetta `,` o `.` secondo le impostazioni regionali di Windows; i risultati usano sempre il formato italiano |

## 5. Se qualcosa fallisce
Inviare l'output completo del comando fallito. Punti sensibili alla piattaforma, in ordine di probabilità:
1. un test che avvia il server web come processo secondario (porta già occupata → cambiare `--port`);
2. percorso più lungo di 260 caratteri se il progetto sta in una cartella molto annidata (spostarlo vicino a `C:\`);
3. l'antivirus che analizza `.venv` e rallenta il primo `uv sync` o la prima esecuzione dei test.

## Regole di portabilità che il codice rispetta (`docs/BUILD_CONTRACT.md`, sezione Portability)
`pathlib` ovunque · `encoding="utf-8"` su ogni lettura/scrittura di testo · nessuna sintassi di shell,
`shell=True`, `os.fork`, segnali POSIX · nomi di file generati in ASCII minuscolo senza `: * ? " < > |` ·
i socket in ascolto usano `SO_EXCLUSIVEADDRUSE` su Windows e `SO_REUSEADDR` altrove.
