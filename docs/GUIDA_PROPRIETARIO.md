# Guida per chi gestisce StruttureMenni

Scritta per chi prende in carico il programma senza essere un programmatore. Spiega cosa avete ricevuto,
come si installa e si avvia, come si usa ogni giorno, dove stanno i dati, cosa va fatto subito e come far
lavorare un agente di sviluppo (Claude Code o simili) senza rischi.

## 1. Cosa avete ricevuto
Una cartella `StruttureMenni` che contiene:
- il programma (cartella `src/`), i test automatici (`tests/`), la documentazione (`docs/`);
- due file di avvio con doppio clic: `Avvia StruttureMenni.bat` (Windows) e `Avvia StruttureMenni.command` (macOS);
- la cartella `var/` con il database `strutture.db`: progetti, elementi salvati, firme del registro. Se la
  cartella non c'è, il programma la crea al primo avvio;
- la cronologia completa delle modifiche (cartella nascosta `.git`): ogni passo dello sviluppo è registrato e
  si può sempre tornare indietro.

I fogli Excel originali non fanno parte del programma e non devono essere copiati nella cartella condivisa: il
programma li ha già "dentro", sotto forma di codice e di valori di riferimento. La cartella `workbooks/` e i
file `.xls`/`.xlsx` sono ignorati dalla cronologia apposta.

Il programma gira interamente sul vostro computer. Non manda dati fuori dall'ufficio, non ha account né
password: chiunque apre la pagina vede e modifica tutto (scelta del committente).

## 2. Cosa serve
- Windows 10/11 oppure macOS. Nessun software a pagamento.
- `uv`, un piccolo programma gratuito che installa da solo Python e le librerie nella cartella del progetto
  (non tocca il resto del computer).
- Un browser moderno (Edge, Chrome, Firefox, Safari).
- MIDAS Gen NX o Civil NX solo se si usa l'importazione delle reazioni (facoltativa).
- LibreOffice e Node non servono per usare il programma.

## 3. Installazione (una volta per computer)
Windows, in PowerShell (tasto destro sul menu Start → "Terminale"):
```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
cd C:\percorso\della\cartella\StruttureMenni
uv sync
```
macOS, nel Terminale (Cmd+Spazio, scrivere «Terminale», Invio):
```
curl -LsSf https://astral.sh/uv/install.sh | sh
cd /percorso/della/cartella/StruttureMenni
uv sync
```
Consiglio per la riga `cd`: scrivere `cd ` con lo spazio, poi trascinare la cartella StruttureMenni dentro la
finestra del terminale: il percorso si scrive da solo; Invio per confermare.
`uv sync` scarica Python e le librerie dentro la cartella `.venv` del progetto (qualche minuto la prima volta).
Se il comando `uv` non viene trovato dopo l'installazione, chiudere e riaprire il terminale.

Per eseguire anche i test del browser (facoltativo, utile dopo ogni modifica di un agente):
```
uv run playwright install chromium
```

## 4. Avvio e arresto
- Doppio clic su `Avvia StruttureMenni.bat` (o `.command`). Si apre una finestra nera (il server) e poi il
  browser su `http://127.0.0.1:8000`. Chiudendo la finestra nera il programma si ferma.
- Su macOS, se il sistema blocca il doppio clic la prima volta: tasto destro → Apri.
- Server da lasciare acceso (Windows): dal terminale `strutture avvia`. Il server gira in background, resta acceso
  chiudendo il terminale ed è raggiungibile dai colleghi della rete (lo script mostra gli indirizzi). Parte solo
  dal ramo `main`, sempre sulla porta 8000. Gli altri comandi: `strutture stato`, `strutture riavvia` (dopo un
  aggiornamento), `strutture ferma`. Si avvia da solo all'accesso a Windows (Utilità di pianificazione,
  attività "StruttureMenni"). Senza l'alias: `powershell -ExecutionPolicy Bypass -File scripts\server.ps1 avvia`.
  L'alias è il file `%USERPROFILE%\.localin\strutture.cmd`, che contiene una riga sola:
  `powershell -NoProfile -ExecutionPolicy Bypass -File "<cartella del progetto>\scripts\server.ps1" %*`.
- Su macOS, o per un avvio in primo piano:
  ```
  uv run python scripts/serve_live.py --host 127.0.0.1 --port 8000
  ```
- Per farlo raggiungere ai colleghi dalla rete dell'ufficio, aggiungere l'indirizzo del computer
  (`ipconfig` su Windows, `ifconfig` su macOS) dopo `--host`, separato da una virgola:
  `--host 127.0.0.1,192.168.1.20`. I colleghi aprono `http://192.168.1.20:8000`. Al primo avvio Windows chiede
  di consentire Python sulle reti private: dire sì. Se l'indirizzo è di una VPN e la VPN è spenta, l'avvio fallisce.
- Ogni computer con la propria copia ha il proprio database: i progetti NON si sincronizzano da soli. Per passare
  un progetto da un computer all'altro: "Esporta" nella pagina del progetto, poi "Importa" sull'altro.
- "Porta già in uso" all'avvio: un altro programma (o una copia precedente) occupa la porta 8000. Chiudere
  l'altra finestra oppure avviare con `--port 8080` e aprire `http://127.0.0.1:8080`.

## 5. Uso quotidiano
- **Home**: gli strumenti sono raggruppati per famiglia; la barra laterale a sinistra li elenca con una sigla
  (per esempio MUR, PLI, TRV) e ricorda i recenti. Ctrl+K apre la ricerca.
- **Dati** (colonna sinistra della pagina di uno strumento): i campi sono raggruppati in sezioni; i coefficienti
  rari stanno sotto "Avanzate". "Carica esempio" riempie un caso di prova. Ogni campo ha simbolo e unità; i campi
  con una tabella accettano incolla da Excel e CSV.
- **Calcolo automatico**: i risultati si aggiornano mentre si scrive, come in un foglio. Si può spegnere
  nell'intestazione e usare "Calcola" (Ctrl+Invio).
- **Sintesi e risultati**: in alto il verdetto e le tre grandezze principali, poi lo schizzo dell'elemento, poi i
  gruppi di risultati (espandibili), le verifiche con clausola e utilizzo, gli avvisi. Un avviso che riguarda un
  dato è un collegamento: cliccandolo si va al campo. Le quote del disegno sottolineate a puntini (b, d, B…)
  si possono modificare sul posto: clic (o Invio da tastiera) apre una casella, Invio applica e il calcolo
  si aggiorna; le quote calcolate (non un dato) restano semplice testo.
- **Stampa relazione**: apre una finestra per scegliere cosa includere (relazione completa, sintetica o
  personalizzata, con o senza "Sviluppo dei calcoli" cioè le formule) e stampa in PDF dal browser. La relazione
  è sempre costruita da un calcolo fresco e contiene tutto, anche ciò che sullo schermo era chiuso.
- **Registro correzioni** (barra laterale): l'elenco delle differenze fra i fogli Excel e il programma. Ogni voce
  dice cosa faceva il foglio, cosa fa il codice, la clausola e l'effetto sul numero. Va firmato voce per voce
  con la propria sigla: approvata o respinta. La firma è una decisione salvata nel database, non un interruttore:
  le voci respinte le applica poi un agente ("Applica le voci respinte del registro"). La pagina lo spiega
  sotto "Come funziona il registro". Vedi `docs/DECISIONI_DA_CONFERMARE.md`.
- **Modalità Excel**: sotto "Avanzate" di ogni strumento, "Riproduci il foglio Excel originale (errori inclusi)" rifà il conto
  come lo faceva il foglio, errori inclusi. Serve per confrontare, non per progettare. "Confronta con Excel" nei
  risultati mostra le due colonne e quale correzione spiega ogni differenza. Quando tutte le correzioni di uno
  strumento sono approvate, l'interruttore sparisce da quello strumento.
- **Progetti** (barra laterale): un progetto raccoglie gli elementi di un lavoro. Dalla pagina di uno strumento,
  "Salva in progetto" salva i dati e la sintesi; nella pagina del progetto si vedono stato (verificato / non
  verificato / dati modificati), utilizzo massimo, storia delle revisioni, duplica, rinomina, elimina e
  ripristina; "Relazione di progetto" stampa un'unica relazione con tutti gli elementi, ricalcolati al momento;
  "Esporta"/"Importa" spostano un progetto in un file JSON.
- **Usa in…**: dopo un calcolo, il pulsante propone gli strumenti che possono ricevere i risultati (per esempio
  i parametri di sito del sisma vanno nel muro di sostegno). I campi ricevuti sono contrassegnati "da <sigla>".
- **Importa da MIDAS**: nelle tabelle di reazioni (plinti, plinti su pali) il pulsante chiede la chiave API
  personale di MIDAS (Apps > API Settings), che resta nel browser per la sessione e non viene salvata. Prima di
  fidarsi va fatta la verifica `docs/VERIFICA_MIDAS.md`.

### Gli strumenti
| Famiglia | Sigla | Strumento |
|---|---|---|
| Carichi / Neve | NEV | Carico neve su copertura (una/due falde) |
| Carichi / Neve | NAC | Accumulo neve su coperture adiacenti a costruzioni più alte |
| Carichi / Sisma | SVR | Vita di riferimento e periodi di ritorno |
| Carichi / Sisma | SPS | Parametri di sito e amplificazione |
| Carichi / Sisma | SFS | Fattori di struttura |
| Carichi / Sisma | SSP | Spettro di risposta |
| Carichi / Sisma | SIS | Analisi completa (vita, sito, struttura, spettro) |
| Carichi / Vento | VEN | Pressione del vento |
| Carichi / Vento | CPE | Coefficienti Cpe, edifici a pianta rettangolare |
| Acciaio / Colonne | COL | Instabilità e resistenza di colonne ad H/I (EC3) |
| Acciaio / Fuoco | INC | Resistenza e rigidezza in condizioni di incendio |
| Acciaio / Fuoco | TMP | Proprietà del materiale a temperatura |
| Acciaio / Sezioni | SHR | Sezione H rimpiattata (profilo + piatti saldati) |
| C.a. / Fessurazione | SLE | Verifica SLE, limitazione delle tensioni |
| C.a. / Fessurazione | FES | Verifica SLE, apertura delle fessure |
| C.a. / Fessurazione | FSS | Verifica SLE, apertura delle fessure (semplificata) |
| C.a. / Mensole | MEN | Progetto e verifica di mensole tozze |
| C.a. / Pilastri | PIR | Pilastro rettangolare/quadrato (CD "B") |
| C.a. / Pilastri | PIC | Pilastro circolare (CD "B") |
| C.a. / Pilastri | SMN | Dominio di resistenza N-M di una sezione |
| C.a. / Punzonamento | PUN | Punzonamento e armature verticali |
| C.a. / Travi | TNA | Taglio di sezione priva di armatura trasversale |
| C.a. / Travi | TRV | Trave rettangolare, progetto e verifica |
| Geotecnica / Muri | MUR | Muro di sostegno a mensola |
| Geotecnica / Cedimenti | EDO | Cedimento edometrico su terreno stratificato |
| Geotecnica / Cedimenti | NEW | Cedimento elastico, integrazione di Newmark |
| Geotecnica / Cedimenti | TG | Cedimento elastico, Timoshenko & Goodier |
| Fondazioni / Pavimenti | PAV | Pavimento industriale su sottofondo Winkler (CNR-DT 211/2014) |
| Fondazioni / Plinti | PLI | Plinto isolato su tabella reazioni |
| Fondazioni / Plinti | PLP | Plinto su pali (puntoni e tiranti) |
| Fondazioni / Travi | TCO | Trave di collegamento tra plinti (NTC 2018 / EN 1998) |

## 6. I dati e il backup
- Tutto ciò che salvate sta in un solo file: `var/strutture.db`. Backup = copiare quel file (meglio a server
  fermo) in un posto sicuro. Ripristino = rimettere il file al suo posto.
- Ogni progetto si può anche esportare in JSON dalla sua pagina: è un backup leggibile e portabile.
- I dati inseriti in uno strumento senza salvarli in un progetto restano solo nel browser di quel computer.

## 7. Cose da fare adesso
1. Verifica su un PC Windows dell'ufficio: `docs/VERIFICA_WINDOWS.md` (mezz'ora). Il programma è stato sviluppato
   su macOS e scritto per Windows, ma nessuno l'ha ancora provato lì.
2. Verifica con MIDAS: `docs/VERIFICA_MIDAS.md`, con un modello aperto. Finché non è fatta, l'importazione da
   MIDAS va considerata non collaudata.
3. Firmare il registro delle correzioni (209 voci) e le decisioni in `docs/DECISIONI_DA_CONFERMARE.md`. Finché
   una voce è "da confermare", la relazione lo dice.
4. Validare gli strumenti uno per uno prima di usarli in produzione: `docs/VALIDAZIONE_STRUMENTI.md` elenca i sei
   passi (esempio in modalità Excel contro il foglio, registro, caso reale, relazione, schizzo, firma) e tiene la
   tabella di stato per sigla. Si compila a mano o dicendo a un agente "segna PLI come validato, sigla AB, oggi";
   le schede sotto la tabella si rigenerano con `uv run python scripts/validazione_strumenti.py`.
5. Decidere se aprire un repository GitHub privato (consigliato: backup del codice fuori dal computer e test
   automatici a ogni modifica). Un agente lo fa in pochi minuti; serve un vostro account.

## 8. Lavorare con un agente di sviluppo
Il programma è pensato per essere modificato da agenti (Claude Code o strumenti simili) guidati da voi. Le
istruzioni tecniche per l'agente sono già nel file `CLAUDE.md` (e `AGENTS.md`) alla radice: l'agente le legge
da solo all'avvio. A voi restano le richieste e i controlli.

Come si avvia: aprire un terminale nella cartella del progetto ed eseguire `claude` (o il comando del vostro
strumento). Poi scrivere la richiesta in italiano, come a un collaboratore.

Esempi di richieste che funzionano bene:
- "Leggi docs/CONSEGNA.md e dimmi lo stato del progetto e cosa aspetta una mia decisione."
- "Nello strumento Muro di sostegno l'etichetta del campo X è poco chiara: cambiala in '…'."
- "Il registro segna la voce muro-sostegno/… come respinta: applica la mia decisione (spiegare quale) e
  aggiorna il registro."
- "Aggiungi uno strumento per … partendo da questa specifica (allegare il foglio o la descrizione). Segui
  docs/BUILD_CONTRACT.md."
- "Esegui tutti i test e dimmi se è tutto verde."
- "Segna MUR come validato, passi 1-6, sigla AB, oggi, e rigenera docs/VALIDAZIONE_STRUMENTI.md."
- "Fai un backup del database e dimmi dove l'hai messo."

Cosa pretendere sempre, a fine lavoro:
- che dica quali test ha eseguito e che siano tutti verdi (calcoli: `uv run pytest -q`; interfaccia:
  `uv run pytest tests/e2e -m e2e -q`; registro: `check --strict` con 0 errori);
- che abbia fatto un commit (un "punto di salvataggio" nella cronologia) con un messaggio chiaro;
- che vi dica in italiano cosa controllare nell'app (quale strumento, quale esempio);
- che NON abbia deciso da solo coefficienti, clausole o ipotesi di calcolo: se la richiesta le tocca, deve
  chiedere e proporre; la firma è vostra.

Cose da evitare:
- lasciare che fermi "tutti i processi Python" o simili: in `CLAUDE.md` è vietato, ma se lo vedete fare
  fermatelo. Il server dell'ufficio va riavviato solo con il vostro consenso;
- incollare la chiave MIDAS o altre credenziali in una richiesta;
- chiedere modifiche ai calcoli senza dare la fonte (clausola, tabella, foglio): l'agente non deve inventare.

Dopo una modifica: riavviare il server (chiudere la finestra nera e rifare doppio clic sul file di avvio),
premere Ctrl+F5 nel browser per svuotare la cache, provare "Carica esempio" sullo strumento toccato.

Costi: gli agenti si pagano a consumo. Richieste piccole e precise costano poco; "rifai tutto" costa molto.
Un lavoro grande (nuovo strumento con verifiche) vale in genere da alcune decine di centesimi a qualche euro
di elaborazione; una correzione di etichetta, centesimi.

## 9. Versioni e ritorno indietro
La cronologia è gestita da git. Non serve impararlo: chiedere all'agente "mostrami le ultime modifiche"
(`git log --oneline -20`) o "torna alla versione di ieri prima della modifica X". Ogni lavoro finito è un
commit; nulla viene mai perso. Se aprite un repository GitHub privato, chiedere all'agente di "collegare il
repository a GitHub e attivare i test automatici": esiste già la lista di ciò che serve.

## 10. Limiti noti
- Importazione MIDAS non ancora collaudata su un'istanza reale (vedi punto 7.2).
- Windows non ancora provato dall'ufficio (punto 7.1).
- La griglia di pericolosità sismica (ag, F0, T*C dalle coordinate) non c'è: i parametri si inseriscono a mano
  o si prendono da SPS "Parametri di sito".
- Relazione solo in PDF (via stampa del browser); il formato Word è rinviato.
- Piccoli difetti grafici: lo strumento neve disegna la falda anche con pendenza 0°; lo schizzo della mensola
  tozza è schematico; alcuni simboli con pedice doppio (M_Ed/M_Rd) si leggono male nella sintesi.
- Pilastri: rapporto di confinamento ωwd e classe di duttilità non implementati.
L'elenco completo dei lavori rinviati è in `docs/DECISIONI_DA_CONFERMARE.md`, in fondo.

## 11. Se qualcosa non va
| Sintomo | Cosa fare |
|---|---|
| Il browser dice "impossibile connettersi" | il server non è partito: guardare la finestra nera; se dice "porta in uso" vedere il punto 4 |
| Pagina bianca o pezzi vecchi dopo una modifica | Ctrl+F5 (svuota la cache) |
| Un risultato sembra sbagliato | controllare che "Riproduci il foglio Excel originale (errori inclusi)" sia spento; leggere gli avvisi; aprire il registro per lo strumento; se resta il dubbio, chiedere all'agente allegando i dati e il risultato atteso |
| Un test fallisce dopo una modifica | incollare all'agente l'output completo del comando |
| "Modificato da un altro utente" salvando un elemento | qualcun altro l'ha salvato prima: "Ricarica" per prendere la sua versione o "Salva come copia" |
| Errore 415 o 403 usando l'API a mano | mancano le intestazioni `Content-Type: application/json` e stessa origine: usare l'interfaccia, oppure gli esempi in `docs/VERIFICA_MIDAS.md` |

## 12. Glossario minimo
- **Server**: il programma che risponde al browser; è la finestra nera. **Porta**: il numero dopo i due punti
  nell'indirizzo (8000). **Terminale**: la finestra in cui si scrivono i comandi.
- **Commit**: un punto di salvataggio nella cronologia del codice. **Repository**: la cartella con la sua cronologia.
- **Test**: programmi che rifanno i calcoli su casi noti e confrontano i numeri; "verde" = tutto coincide.
- **Registro delle correzioni**: l'elenco delle differenze volute fra i fogli Excel e il programma, da firmare.
- **Modalità standard / Excel**: norma applicata / foglio riprodotto (errori inclusi).
- **Agente**: un assistente di intelligenza artificiale che legge e modifica il codice su vostra richiesta.
- **Cache**: la copia locale, nel browser, delle pagine già viste; dopo una modifica va svuotata (Ctrl+F5) per
  vedere la versione nuova. **API**: il canale con cui due programmi si scambiano dati senza passare dallo
  schermo (qui: fra StruttureMenni e MIDAS). **VPN**: collegamento cifrato alla rete dell'ufficio da fuori;
  se è spenta, gli indirizzi di quella rete non rispondono.
