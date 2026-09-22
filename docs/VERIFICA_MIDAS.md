# MIDAS NX — lista di verifica dal vivo

`docs/integrations/MIDAS.md` è stato scritto a partire dalla libreria Python ufficiale di MIDAS (`midas-gen`)
e dal manuale dell'API, **non** da un'istanza MIDAS in funzione: sulla macchina di sviluppo non ce n'era una.
Tutti i test automatici usano `httpx.MockTransport` con le risposte documentate. Questa lista è ciò che un
ingegnere con MIDAS Gen NX o Civil NX installato deve eseguire una volta, su un modello reale, prima di fidarsi
dell'importazione in un progetto. I comandi sono per PowerShell (opzioni sulla riga di comando, non
`VAR=valore comando`: quella sintassi è solo POSIX e su Windows fallirebbe in silenzio).

Riferire superato/fallito per ogni passo numerato e, per ogni fallimento, il JSON grezzo di richiesta e risposta
(la chiave non compare mai nella risposta, vedi il passo 8, quindi si può incollare così com'è).

## 0. Trovare la Base URL e la MAPI-Key

1. Aprire MIDAS Gen NX o Civil NX con il modello da provare.
2. Menu **Apps > API Settings**.
3. Portare **Connect** su ON: l'applicazione deve restare aperta e connessa per tutti i passi seguenti; se è
   spenta si ottiene `502 not_connected`.
4. **Base URL**: è mostrata nello stesso pannello, per esempio `https://moa-engineers.midasit.com:443/gen`
   (Gen NX) oppure `.../civil` (Civil NX). Le installazioni regionali possono mostrare `moa-engineers-gb`,
   `-in`, `-kr`, `-us`, o il relay cinese `moa-engineers.midasit.cn`. Copiarla esattamente, non ribatterla.
5. **MAPI-Key** (chiave API personale): generarne una se non esiste, poi copiarla. Trattarla come una password:
   incollarla in una variabile PowerShell, mai in un comando che verrà incollato altrove.

## 1. Avviare il server

```powershell
uv sync
uv run python -m strutture.web --port 8000
```

Lasciare aperta questa finestra; fare tutto il resto in una seconda finestra PowerShell.

```powershell
$key = "<incolla qui la tua MAPI-Key>"
$baseUrl = "<incolla qui la tua Base URL, es. https://moa-engineers.midasit.com:443/gen>"
```

## 2. Connessione e versione

```powershell
curl.exe -s http://127.0.0.1:8000/api/midas/status
```
Atteso `{"server_key":false,"base_url":null,"product":null}` (nessuna chiave configurata sul server: è normale,
la chiave è personale e viene inviata con ogni richiesta).

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/verify -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d "{}"
```
Se il riconoscimento automatico non trova il vostro relay, passare la Base URL esplicitamente:
```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/verify -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d "{`"base_url`":`"$baseUrl`"}"
```
Confrontare con MIDAS stesso:
- `name`/`version` coincidono con **Help > About**;
- `product` è `gen` o `civil` a seconda del caso;
- `units.force`/`units.dist` coincidono con ciò che **Tools > Unit System** mostra per il modello in questo momento.

## 3. Combinazioni

```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/combinations -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d "{`"base_url`":`"$baseUrl`"}" | Out-File combinations.json -Encoding utf8
notepad combinations.json
```
Confrontare con le tabelle **Results > Load Combinations** di MIDAS (General, Concrete Design, Steel Design,
SRC, Steel Composite, Seismic):
- ogni combinazione mostrata da MIDAS compare esattamente una volta, sotto la `classification` giusta;
- `table_name` è `NOME` seguito dal suffisso dell'analisi tra parentesi. Il codice assume `(CB)` per General e
  Seismic, `(CBC)` Concrete, `(CBS)` Steel e Steel Composite, `(CBR)` SRC (vedi
  `src/strutture/integrations/midas/combinations.py`). **È la singola ipotesi non verificata più importante di
  tutta l'integrazione**: se il passo 4 restituisce zero righe per una combinazione che in MIDAS ha chiaramente
  dei risultati, questo suffisso è la prima cosa da controllare (guardare la colonna `Load` della tabella delle
  reazioni di MIDAS per la stringa esatta);
- `famiglia_suggerita` è una proposta ragionevole secondo le NTC 2018 (SLU_STR / SLU_EQU / SLV_STR / SLV_EQU /
  SLE_RARA / SLE_FREQ / SLE_QP): una proposta sbagliata non fa danni, l'interfaccia permette di cambiarla.

## 4. Reazioni su un modello piccolo: il controllo principale

Scegliere 2-3 nodi e 2-3 combinazioni di carico che si possono leggere anche a occhio nella tabella
**Results > Reactions > Reaction Table** di MIDAS (impostare prima le unità di visualizzazione a kN / m,
Tools > Unit System, così il confronto è omogeneo).

```powershell
$body = '{"base_url":"' + $baseUrl + '","nodi":[12,13],"combinazioni":[{"table_name":"SLU1(CB)","famiglia":"SLU_STR"}]}'
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/reactions -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d $body
```
(Sostituire gli id dei nodi e `table_name` con valori presi da `combinations.json` del passo 3.)

Per ogni riga, confrontare con la tabella delle reazioni di MIDAS, riga per riga:
- **Valori**: `fx_kN`/`fy_kN`/`fz_kN`/`mx_kNm`/`my_kNm`/`mz_kNm` coincidono a 5 cifre significative (si chiede
  `STYLES.PLACE=5`).
- **Segni**: controllarli esplicitamente, è il modo più facile in cui un'importazione corrompe in silenzio una
  verifica di fondazione. Prendere una combinazione solo gravitazionale e confermare che il segno di `fz_kN`
  corrisponde alla convenzione di MIDAS per un carico verso il basso reagito verso l'alto (convenzione degli
  assi globali di MIDAS; alcune installazioni la invertono per modello di progetto).
- **Unità**: i nostri valori sono sempre in kN / kNm, qualunque cosa mostri l'interfaccia di MIDAS. Se si passa
  temporaneamente la visualizzazione di MIDAS a kgf o tonf, convertire una riga a mano e confermare che coincide.
- `combo` è il nome della combinazione senza suffisso (`SLU1(CB)` -> `SLU1`).
- `famiglia` è ciò che si è passato in `combinazioni`.

## 4 bis. Nodi vincolati

L'interfaccia, con la scelta "Tutti i nodi vincolati", chiede a MIDAS l'elenco dei vincoli invece di far
digitare gli id dei nodi:
```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/supports -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d "{`"base_url`":`"$baseUrl`"}"
```
Confrontare il numero di nodi restituiti (campo `nodo` di ogni riga) con i vincoli del modello (**Model > Boundaries**
oppure la tabella delle reazioni): devono coincidere per numero e per id. Se la risposta è vuota su un modello
che ha vincoli, riferire il JSON grezzo: la forma della risposta di MIDAS per i vincoli è una delle ipotesi non
verificate (`src/strutture/integrations/midas/supports.py`).

## 5. Modello con unità non SI

Passare il sistema di unità del modello (**Tools > Unit System**) a uno non SI (per esempio kgf/cm o tonf/m),
ripetere il passo 4 e confermare che `fz_kN` ecc. sono ancora valori corretti in kN. Questo esercita il ripiego
su `/db/UNIT` in `reactions.py` (regola 4 di `docs/integrations/MIDAS.md` §2): la richiesta chiede sempre a
MIDAS `KN`/`M`, ma se la risposta di una tabella non riporta le unità effettivamente usate, si interroga
`/db/UNIT` invece di assumere che la richiesta sia stata rispettata. Se questo passo dà valori sbagliati,
salvare la risposta grezza `SS_Table` (contiene le chiavi `FORCE`/`DIST` oppure no?): è il modo più rapido
per diagnosticare.

## 6. Modello con fasi costruttive

Se il modello ha un'analisi per fasi costruttive, ripetere il passo 4 su un caso/combinazione di una fase e
confermare che l'importazione non va in errore. Se la colonna `Load` di MIDAS per un risultato di fase usa uno
schema di nomi diverso da `NOME(SUFFISSO)`, annotare qui la stringa esatta: `_strip_suffix` in `reactions.py`
potrebbe aver bisogno di un nuovo schema.

## 7. Importazione grande

Su un modello con molti nodi e combinazioni, chiedere le reazioni per più di 100 combinazioni su tutti i
vincoli e cronometrare:
```powershell
Measure-Command { curl.exe -s -X POST http://127.0.0.1:8000/api/midas/reactions -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d $bigBody }
```
La richiesta va spezzata in blocchi da 50 combinazioni per chiamata a MIDAS (`CHUNK_SIZE` in `reactions.py`):
se MIDAS espone un registro delle connessioni, si devono vedere più chiamate, non una. Se le righe totali
superassero 20 000, `avvisi` deve contenere un messaggio esplicito di troncamento e `n_righe` deve essere
esattamente 20 000.

## 8. Rinnovo della chiave

In MIDAS, **Apps > API Settings**, rigenerare la MAPI-Key. Poi riprovare con la VECCHIA chiave:
```powershell
curl.exe -s -X POST http://127.0.0.1:8000/api/midas/verify -H "Content-Type: application/json" -H "X-Midas-Key: $key" -d "{}"
```
Atteso HTTP 401 con `{"ok":false,"kind":"auth",...}` e, da controllare a occhio, la vecchia chiave **non**
compare da nessuna parte nel corpo della risposta. Poi impostare `$key` al nuovo valore e confermare che il
passo 2 funziona di nuovo.

## Come si presenta un errore

| Sintomo | Causa probabile |
|---|---|
| `400 forbidden_url` | Base URL scritta male, oppure non è il relay `moa-engineers...midasit.(com\|cn)`: copiarla da Apps > API Settings, non ribatterla |
| `401 auth` | chiave scaduta o rigenerata: rigenerarla (passo 8) |
| `502 not_connected` | MIDAS non è in esecuzione, oppure **Apps > API Settings > Connect** è spento |
| `504 timeout` | rete lenta, o MIDAS impegnato a ricalcolare: riprovare |
| `502 bad_response` | MIDAS ha restituito una forma che il nostro parser non riconosce; questa lista esiste proprio per scoprirlo: riferire il JSON grezzo (si può condividere, non contiene mai la chiave) |
