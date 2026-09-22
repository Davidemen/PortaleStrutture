# Validazione dei singoli strumenti

Aggiornato il 2026-09-22. Questo è il registro del lavoro di validazione, strumento per strumento, che l'ingegnere
responsabile fa una volta prima di usare il programma in produzione. La tabella qui sotto si compila a mano
(anche tramite un agente: "segna PLI come validato, sigla AB, oggi"); le schede più in basso sono generate dai dati.
Rigenerare con `uv run python scripts/validazione_strumenti.py`: la tabella compilata viene conservata, le schede
aggiornate (registro firmato, test, relazioni).

## I sei passi di validazione di uno strumento
1. Esempio in modalità Excel: aprire lo strumento, "Carica esempio", accendere "Riproduci il foglio Excel originale (errori inclusi)" e confrontare i numeri con il foglio di origine (devono coincidere alla cifra).
2. Registro: aprire "Registro correzioni" filtrato sullo strumento e firmare ogni voce (approvata o respinta) con la propria sigla; "Confronta con Excel" mostra l'effetto numerico di ciascuna.
3. Caso reale in modalità standard: inserire un elemento già calcolato in passato (o a mano) e confrontare verdetto e grandezze principali; le differenze devono essere spiegate dalle voci di registro.
4. Relazione: "Stampa relazione" con "Sviluppo dei calcoli" e rileggere le formule, le sostituzioni e le clausole.
5. Schizzo e verifiche: lo schizzo corrisponde all'elemento inserito; nomi, clausole e limiti delle verifiche sono giusti.
6. Firma: stato "validato", sigla e data nella tabella; note su ciò che resta aperto.

## Come si compila la tabella
- Stato: `da validare` → `in corso` → `validato`; `bloccato` se serve una decisione o una correzione (dirlo nelle note).
- Passi fatti: i numeri dei passi completati, separati da spazio (es. `1 2 3`).
- Validatore: sigla; Data: AAAA-MM-GG; Note: senza il carattere `|`.
- Il registro delle correzioni si firma nell'app, non qui: le schede riportano lo stato letto dal database.

## Stato di validazione
<!-- INIZIO TABELLA MANUALE: le righe qui sotto sono vostre, il generatore le conserva -->
| Sigla | Strumento | Stato | Passi fatti | Validatore | Data | Note |
|---|---|---|---|---|---|---|
| NEV | Carico neve su copertura (una/due falde) | da validare |  |  |  |  |
| NAC | Accumulo neve su coperture adiacenti a costruzioni più alte | da validare |  |  |  |  |
| SVR | Sisma — vita di riferimento e periodi di ritorno | da validare |  |  |  |  |
| SPS | Sisma — parametri di sito e amplificazione | da validare |  |  |  |  |
| SFS | Sisma — fattori di struttura | da validare |  |  |  |  |
| SSP | Sisma — spettro di risposta | da validare |  |  |  |  |
| SIS | Sisma — analisi completa (vita, sito, struttura, spettro) | da validare |  |  |  |  |
| VEN | Pressione del vento | da validare |  |  |  |  |
| CPE | Coefficienti Cpe vento — edifici a pianta rettangolare | da validare |  |  |  |  |
| COL | Verifica di instabilità e resistenza colonne ad H/I — EC3 | da validare |  |  |  |  |
| INC | Acciaio — resistenza e rigidezza in condizioni di incendio | da validare |  |  |  |  |
| TMP | Acciaio — proprietà del materiale a temperatura | da validare |  |  |  |  |
| SHR | Sezione H rimpiattata (profilo + piatti saldati) | da validare |  |  |  |  |
| SLE | Verifica SLE — limitazione delle tensioni | da validare |  |  |  |  |
| FES | Verifica SLE — apertura delle fessure | da validare |  |  |  |  |
| FSS | Verifica SLE — apertura delle fessure (semplificata) | da validare |  |  |  |  |
| MEN | Progetto e verifica di mensole tozze | da validare |  |  |  |  |
| PIR | Verifica pilastro in c.a. rettangolare/quadrato (CD "B") | da validare |  |  |  |  |
| PIC | Verifica pilastro in c.a. circolare (CD "B") | da validare |  |  |  |  |
| PUN | Verifica a punzonamento e progetto armature verticali (solai/platee su pilastri o pali) | da validare |  |  |  |  |
| SMN | Dominio di resistenza a pressoflessione N-M di una sezione in c.a. | da validare |  |  |  |  |
| TNA | Resistenza a taglio di sezione in c.a. priva di armatura trasversale | da validare |  |  |  |  |
| TRV | Trave in c.a. a sezione rettangolare — progetto e verifica | da validare |  |  |  |  |
| MUR | Muro di sostegno a mensola | da validare |  |  |  |  |
| EDO | Cedimento edometrico di una fondazione rettangolare su terreno stratificato | da validare |  |  |  |  |
| NEW | Cedimento elastico - integrazione di Newmark | da validare |  |  |  |  |
| TG | Cedimento elastico - Timoshenko & Goodier (rettangolo flessibile) | da validare |  |  |  |  |
| PAV | Verifica pavimento industriale su sottofondo Winkler (CNR-DT 211/2014) | da validare |  |  |  |  |
| PLI | Verifica plinto isolato su tabella reazioni | da validare |  |  |  |  |
| PLP | Verifica plinto su pali (puntoni e tiranti) | da validare |  |  |  |  |
| TCO | Verifica trave di collegamento tra plinti (NTC2018 / EN1998) | da validare |  |  |  |  |
<!-- FINE TABELLA MANUALE -->
Strumenti: 31 · validati: 0 · voci di registro legate a uno strumento: 203

## Schede per strumento (generate)

### NEV — Carico neve su copertura (una/due falde)
- Gruppo: Carichi / Neve · norma: NTC2018 §3.4 · pacchetto: `strutture.loads.neve`
- Fogli Excel di origine: `Carico neve da NTC - DM2018.xls`
- Specifica: docs/specs/neve.md
- Esempio ("Carica esempio"): sì · test: 12 file, 6 golden (valori del foglio), 4 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (9 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 5 voci: 5 da confermare
  - `comuni/zona-neve-mancante-in-sisma-vento` — Lo snapshot comuni dei fogli sisma e vento ha righe senza zona neve compilata (errore del foglio, da confermare)
  - `neve/mu-falda-discontinuo-a-30-gradi` — Il coefficiente di forma mu si azzera bruscamente a falda esattamente 30 gradi (errore del foglio, da confermare)
  - `neve/qsk-confine-200m-non-conservativo` — A quota esattamente 200 m il foglio usa la formula meno conservativa (errore del foglio, da confermare)
  - `neve/tipo-copertura-non-filtra-output` — Il foglio calcola sempre entrambe le falde anche se il tetto ne ha una sola (errore del foglio, da confermare)
  - `neve/zona-mediterranea-scambiata-con-alpina` — La ricerca approssimata della zona scambia i coefficienti mediterranea/alpina (errore del foglio, da confermare)

### NAC — Accumulo neve su coperture adiacenti a costruzioni più alte
- Gruppo: Carichi / Neve · norma: Circ. NTC2018 §C3.4.5.6 · pacchetto: `strutture.loads.neve`
- Fogli Excel di origine: `Carico neve da NTC - DM2018.xls`
- Specifica: docs/specs/neve.md
- Esempio ("Carica esempio"): sì · test: 12 file, 6 golden (valori del foglio), 4 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (10 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 7 voci: 7 da confermare
  - `comuni/zona-neve-mancante-in-sisma-vento` — Lo snapshot comuni dei fogli sisma e vento ha righe senza zona neve compilata (errore del foglio, da confermare)
  - `neve/accumulo-branch-qsk-invertito` — Il ramo qsk1/qsk2 di Neve accumulo e' invertito rispetto a Neve (errore del foglio, da confermare)
  - `neve/accumulo-m1-interpolato-senza-limiti` — L'interpolazione di m1 per l'accumulo non ha limiti e puo' andare fuori range fisico (errore del foglio, da confermare)
  - `neve/qsk-accumulo-quota-altro-foglio` — Neve accumulo legge la quota dal foglio Neve invece che dalla propria (errore del foglio, da confermare)
  - `neve/qsk-confine-200m-non-conservativo` — A quota esattamente 200 m il foglio usa la formula meno conservativa (errore del foglio, da confermare)
  - `neve/zona-lookup-su-provincia-invece-che-comune` — La zona di Neve accumulo cerca la provincia nella colonna comune e fallisce spesso (errore del foglio, da confermare)
  - `neve/zona-mediterranea-scambiata-con-alpina` — La ricerca approssimata della zona scambia i coefficienti mediterranea/alpina (errore del foglio, da confermare)

### SVR — Sisma — vita di riferimento e periodi di ritorno
- Gruppo: Carichi / Sisma · norma: NTC2018 §3.2.1, §2.4.3 · pacchetto: `strutture.loads.sisma`
- Fogli Excel di origine: `Azione sismica da NTC - DM2018.xls`
- Specifica: docs/specs/sisma.md
- Esempio ("Carica esempio"): sì · test: 21 file, 3 golden (valori del foglio), 8 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (12 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 2 voci: 2 da confermare
  - `comuni/provincia-nome-non-aggiornato` — Il nome provincia nei fogli sisma e vento non riflette le province istituite dopo il 2009 (errore del foglio, da confermare)
  - `ntc-site-seismic/vita-riferimento-senza-minimo-35-anni` — La vita di riferimento VR non ha il minimo di 35 anni (errore del foglio, da confermare)

### SPS — Sisma — parametri di sito e amplificazione
- Gruppo: Carichi / Sisma · norma: NTC2018 §3.2.2, §3.2.3.2.1 · pacchetto: `strutture.loads.sisma`
- Fogli Excel di origine: `Azione sismica da NTC - DM2018.xls`
- Specifica: docs/specs/sisma.md
- Esempio ("Carica esempio"): sì · test: 21 file, 3 golden (valori del foglio), 8 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (8 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce `sito.ag_g`, `sito.categoria_sottosuolo`, `sito.categoria_topografica`, `sito.f0` · riceve — · "Usa in…" verso `fond-trave-collegamento`, `muro-sostegno`
- Registro: 1 voce: 1 da confermare
  - `ntc-site-seismic/ss-categoria-b-limite-inferiore-basso` — Il coefficiente di amplificazione stratigrafica Ss per il suolo B ha un limite inferiore troppo basso (errore del foglio, da confermare)

### SFS — Sisma — fattori di struttura
- Gruppo: Carichi / Sisma · norma: NTC2018 §3.2.3.5, §7.3.1, §7.3.3.2 · pacchetto: `strutture.loads.sisma`
- Fogli Excel di origine: `Azione sismica da NTC - DM2018.xls`
- Specifica: docs/specs/sisma.md
- Esempio ("Carica esempio"): sì · test: 21 file, 3 golden (valori del foglio), 8 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (8 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 2 voci: 2 da confermare
  - `sisma/eta-smorzamento-senza-limite-inferiore` — Il coefficiente eta di smorzamento non ha un limite inferiore per xi alti (errore del foglio, da confermare)
  - `sisma/eta-verticale-reciproco-di-qv` — Il coefficiente dissipativo verticale e' calcolato come 1/qv invece che dallo smorzamento (errore del foglio, da confermare)

### SSP — Sisma — spettro di risposta
- Gruppo: Carichi / Sisma · norma: NTC2018 §3.2.3.2.1 · pacchetto: `strutture.loads.sisma`
- Fogli Excel di origine: `Azione sismica da NTC - DM2018.xls`
- Specifica: docs/specs/sisma.md
- Esempio ("Carica esempio"): sì · test: 21 file, 3 golden (valori del foglio), 8 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (10 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 4 voci: 4 da confermare
  - `sisma/spettro-elastico-t0-non-ancorato-ad-ags` — Lo spettro elastico non torna esattamente ad ag*S a T=0 quando lo smorzamento non e' 5% (errore del foglio, da confermare)
  - `sisma/spettro-progetto-plateau-eta-non-sostituita` — Lo spettro di progetto sopra T_B divide per q l'ordinata elastica con η dentro, invece di sostituire η con 1/q (errore del foglio, da confermare)
  - `sisma/spettro-progetto-salita-eta-sostituita-da-1-q` — Il ramo 0<=T<TB dello spettro di progetto divide Se(T) per q invece di sostituire eta con 1/q (errore del foglio, da confermare)
  - `sisma/spettro-progetto-senza-pavimento-0-2ag` — Lo spettro di progetto puo' scendere sotto 0.2ag per periodi lunghi (errore del foglio, da confermare)

### SIS — Sisma — analisi completa (vita, sito, struttura, spettro)
- Gruppo: Carichi / Sisma · norma: NTC2018 §3.2 · pacchetto: `strutture.loads.sisma.completo`
- Fogli Excel di origine: `Azione sismica da NTC - DM2018.xls`
- Specifica: docs/specs/ (pacchetto strutture.loads.sisma.completo)
- Esempio ("Carica esempio"): sì · test: 0 file, 0 golden (valori del foglio), 0 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (38 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 3 voci: 3 da confermare
  - `ntc-site-seismic/ss-categoria-b-limite-inferiore-basso` — Il coefficiente di amplificazione stratigrafica Ss per il suolo B ha un limite inferiore troppo basso (errore del foglio, da confermare)
  - `ntc-site-seismic/vita-riferimento-senza-minimo-35-anni` — La vita di riferimento VR non ha il minimo di 35 anni (errore del foglio, da confermare)
  - `sisma/spettro-progetto-plateau-eta-non-sostituita` — Lo spettro di progetto sopra T_B divide per q l'ordinata elastica con η dentro, invece di sostituire η con 1/q (errore del foglio, da confermare)

### VEN — Pressione del vento
- Gruppo: Carichi / Vento · norma: NTC2018 §3.3 / Circ. NTC2019 C3.3.2 · pacchetto: `strutture.loads.vento`
- Fogli Excel di origine: `Carico vento da NTC - DM2018.xls`
- Specifica: docs/specs/vento.md
- Esempio ("Carica esempio"): sì · test: 12 file, 2 golden (valori del foglio), 2 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (13 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 7 voci: 7 da confermare
  - `comuni/provincia-nome-non-aggiornato` — Il nome provincia nei fogli sisma e vento non riflette le province istituite dopo il 2009 (errore del foglio, da confermare)
  - `comuni/vento-zona-invalida-56-in-neve` — Lo snapshot comuni del foglio neve contiene un valore di zona vento non valido (errore del foglio, da confermare)
  - `vento/correzione-altitudine-formula-ntc2008` — La correzione di velocita' per l'altitudine usa la formula NTC2008 superata invece della NTC2018 (aggiornamento normativo, da confermare)
  - `vento/etichetta-ce-unita-di-misura-errata` — L'etichetta del coefficiente di esposizione riporta un'unita' di misura errata (errore del foglio, da confermare)
  - `vento/profilo-pressione-limitato-a-1000-righe` — Il profilo di pressione e' fisso a 1000 sezioni e non segue il parametro del foglio (errore del foglio, da confermare)
  - `vento/velocita-riferimento-rinormalizzata-su-tr50` — La velocita' di riferimento e' rinormalizzata su TR=50 in modo incoerente con il coefficiente a_r esposto (errore del foglio, da confermare)
  - `vento/zona-lookup-su-provincia-invece-che-comune` — La zona di vento cerca la provincia nella colonna comune e fallisce spesso (errore del foglio, da confermare)

### CPE — Coefficienti Cpe vento — edifici a pianta rettangolare
- Gruppo: Carichi / Vento · norma: Circ. NTC2019 §C3.3.8.1 · pacchetto: `strutture.loads.vento_cpe`
- Fogli Excel di origine: `Coefficienti Cpe Vento - DM2018.xlsx`
- Specifica: docs/specs/small-units.md
- Esempio ("Carica esempio"): sì · test: 12 file, 2 golden (valori del foglio), 3 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (8 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 2 voci: 2 da confermare
  - `vento-cpe/etichetta-classificazione-edificio-snello-mista` — L'etichetta di classificazione per il caso misto per direzione non e' scritta nella specifica originale (da verificare, da confermare)
  - `vento-cpe/etichetta-classificazione-maiuscolo` — Le etichette di classificazione tozzo/snello sono tutte maiuscole nel foglio (scelta ingegneristica, da confermare)

### COL — Verifica di instabilità e resistenza colonne ad H/I — EC3
- Gruppo: Acciaio / Colonne · norma: EN1993-1-1 §5.5, §6.2, §6.3 · pacchetto: `strutture.members.acciaio_colonna_ec3`
- Fogli Excel di origine: `Verifica instabilità e resistenza colonne ad H secondo EC3.xlsx`
- Specifica: docs/specs/acciaio.md
- Esempio ("Carica esempio"): sì · test: 20 file, 1 golden (valori del foglio), 2 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (39 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 20 voci: 20 da confermare
  - `acciaio-colonna-ec3/alpha-instabilita-flessionale-non-da-curva` — Il coefficiente alpha di instabilita flessionale non deriva dalla curva di stabilita (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/chi-lt-radicando-incompleto` — Il fattore chi_LT omette un termine dalla radice quadrata (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/cij-denominatore-lambda-zz-da-verificare` — I termini correttivi Cij dell'Annex A usano la snellezza invece del fattore chi (da verificare, da confermare)
  - `acciaio-colonna-ec3/classe-4-non-implementata` — La classe di sezione 4 e' accettata ma trattata come classe 3 senza larghezze efficaci (da verificare, da confermare)
  - `acciaio-colonna-ec3/cmz-usa-iyy-invece-di-izz` — Il coefficiente Cmz per diagrammi di tipo 2 usa il momento d'inerzia dell'asse sbagliato (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/cw-formula-taglio-instabilita-da-verificare` — La formula del coefficiente cw per l'instabilita a taglio usa sempre il ramo intermedio (da verificare, da confermare)
  - `acciaio-colonna-ec3/czy-usa-wz-invece-di-wy` — Il coefficiente Czy usa l'esponente della snellezza dell'asse sbagliato (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/epsilon-eta-limite-taglio-instabilita` — Epsilon/eta per l'instabilita a taglio usano fyd invece di fyk e il limite anima ha formula e verso invertiti (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/eq-6-61-terzo-termine-gamma-m1-extra` — Il terzo termine dell'equazione 6.61 ha una divisione per gammaM1 di troppo (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/fud-diviso-gamma-m0` — fud e' calcolato dividendo fuk per gammaM0 invece che per gammaM2 (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/gamma-m-hardcoded-a-1` — I coefficienti gammaM0/gammaM1 sono input liberi scollegati dai valori di norma (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/i56-usa-mpl-invece-di-mn-rd` — Il controllo dell'eq. 6.41 usa il momento plastico non ridotto invece di quello ridotto dall'assiale (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/interazione-doppia-divisione-gamma-m0-m1` — Le equazioni di interazione 6.61/6.62 applicano gammaM0 e gammaM1 in serie invece che solo gammaM1 (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/mn-rd-z-formula-sbagliata` — Il momento resistente ridotto sull'asse debole usa una formula impropria dell'asse forte (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/mrd-y-doppia-divisione-gamma-m0` — Il momento resistente MRd,y e' diviso due volte per gammaM0 (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/snellezze-adimensionali-usano-fyd` — Le snellezze adimensionali di instabilita usano fyd invece della resistenza caratteristica fyk (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/tipo-lavorazione-curva-lt-da-verificare` — La voce 'formato a freddo' potrebbe non essere la curva EC3 corretta per profili H aperti (da verificare, da confermare)
  - `acciaio-colonna-ec3/trigger-taglio-elevato-asse-scambiato` — Il criterio di taglio elevato per la riduzione del momento resistente legge l'asse sbagliato (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/v54-termine-assiale-mille-volte-piccolo` — Nel controllo lineare semplificato il termine assiale e' scalato in modo errato di circa 1000 volte (errore del foglio, da confermare)
  - `acciaio-colonna-ec3/verifica-taglio-assi-scambiati` — Le verifiche a taglio anima/ali confrontano la domanda dell'asse sbagliato (errore del foglio, da confermare)

### INC — Acciaio — resistenza e rigidezza in condizioni di incendio
- Gruppo: Acciaio / Fuoco · norma: EN1993-1-2 §3.2.1, Tab. 3.1 · pacchetto: `strutture.members.acciaio_incendio`
- Fogli Excel di origine: `Resistenza acciaio con incendio.xlsx`
- Specifica: docs/specs/acciaio.md, docs/specs/small-units.md
- Esempio ("Carica esempio"): sì · test: 8 file, 2 golden (valori del foglio), 4 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (8 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 1 voce: 1 da confermare
  - `acciaio-incendio/fu-s275-mai-selezionato` — La resistenza a rottura a 20°C dell'acciaio S275 non viene mai selezionata correttamente (errore del foglio, da confermare)

### TMP — Acciaio — proprietà del materiale a temperatura
- Gruppo: Acciaio / Fuoco · norma: EN1993-1-2 §3.2.1, Tab. 3.1 · pacchetto: `strutture.members.acciaio_incendio.proprieta_tool`
- Fogli Excel di origine: `workbooks/2xxxx_Verifiche al fuoco_proprietà materiali.xlsx`
- Specifica: docs/specs/ (pacchetto strutture.members.acciaio_incendio.proprieta_tool)
- Esempio ("Carica esempio"): sì · test: 0 file, 0 golden (valori del foglio), 0 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (6 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: nessuna voce di registro

### SHR — Sezione H rimpiattata (profilo + piatti saldati)
- Gruppo: Acciaio / Sezioni · norma: EN1993-1-1 · pacchetto: `strutture.members.acciaio_sezione_composta`
- Fogli Excel di origine: `workbooks/2xxx_Sezione H rimpiattata.xlsx`
- Specifica: docs/specs/small-units.md
- Esempio ("Carica esempio"): sì · test: 6 file, 1 golden (valori del foglio), 3 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (17 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 6 voci: 6 da confermare
  - `acciaio-sezione-h-rimpiattata/altezza-anima-valore-fisso` — L'altezza libera dell'anima e' un valore fisso invece di dipendere dall'altezza del profilo (errore del foglio, da confermare)
  - `acciaio-sezione-h-rimpiattata/centroide-ala-inferiore-spessore-sbagliato` — Il baricentro dell'ala inferiore usa lo spessore del primo piatto invece del proprio (errore del foglio, da confermare)
  - `acciaio-sezione-h-rimpiattata/centroide-yn-ultimo-termine-x` — Il baricentro verticale usa la coordinata x invece della y per l'ultimo elemento (errore del foglio, da confermare)
  - `acciaio-sezione-h-rimpiattata/legacy-max-due-piatti` — In modalita' foglio il numero di piatti e' limitato alle due righe fisiche del foglio (scelta ingegneristica, da confermare)
  - `acciaio-sezione-h-rimpiattata/piatto-2-offset-rispecchia-piatto-1` — Lo scostamento orizzontale del secondo piatto rispecchia il primo invece di usare la propria larghezza (errore del foglio, da confermare)
  - `acciaio-sezione-h-rimpiattata/wpl-non-e-il-vero-modulo-plastico` — I moduli plastici riportati non sono il vero modulo plastico per sezioni con piatti asimmetrici (da verificare, da confermare)

### SLE — Verifica SLE — limitazione delle tensioni
- Gruppo: Calcestruzzo armato / Fessurazione · norma: NTC2018 §4.1.2.2.5 · pacchetto: `strutture.members.ca_fessurazione`
- Fogli Excel di origine: `Verifica fessurazione - SLEF (X).xlsx`
- Specifica: docs/specs/ca-fessurazione.md
- Esempio ("Carica esempio"): sì · test: 18 file, 6 golden (valori del foglio), 6 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (13 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve `trave.sigma_s_rara_MPa` · "Usa in…" verso —
- Registro: nessuna voce di registro

### FES — Verifica SLE — apertura delle fessure
- Gruppo: Calcestruzzo armato / Fessurazione · norma: Circ. 2019 §C4.1.2.2.4.5 · pacchetto: `strutture.members.ca_fessurazione`
- Fogli Excel di origine: `Verifica fessurazione - SLEF (X).xlsx`
- Specifica: docs/specs/ca-fessurazione.md
- Esempio ("Carica esempio"): sì · test: 18 file, 6 golden (valori del foglio), 6 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (21 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 4 voci: 4 da confermare
  - `ca-fessurazione/costante-delta-sm-arrotondata` — La costante del ramo Δsm §C4.1.10 è arrotondata a 2 decimali invece del rapporto esatto 1,3/1,7 (errore del foglio, da confermare)
  - `ca-fessurazione/link-esterno-morto-materiali` — Ecm e fctm puntano a un collegamento verso un altro file non disponibile (errore del foglio, da confermare)
  - `ca-fessurazione/opzione-trazione-eccentrica-divisione-per-zero` — L'opzione 'trazione eccentrica' del tipo di sollecitazione genera una divisione per zero ed è comunque inattingibile (errore del foglio, da confermare)
  - `materials/fck-calcestruzzo-fill-down-083-rck` — fck del calcestruzzo è calcolato come 0,83·Rck invece del valore letterale di Tab. 4.1.I (errore del foglio, da confermare)

### FSS — Verifica SLE — apertura delle fessure (semplificata)
- Gruppo: Calcestruzzo armato / Fessurazione · norma: NTC2018 §4.1.2.2.4 · pacchetto: `strutture.members.ca_fessurazione`
- Fogli Excel di origine: `Verifica fessurazione - SLEF (X).xlsx`
- Specifica: docs/specs/ca-fessurazione.md
- Esempio ("Carica esempio"): sì · test: 18 file, 6 golden (valori del foglio), 6 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (17 passi sull'esempio) · schizzo: no · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 3 voci: 3 da confermare
  - `ca-fessurazione/classe-fissa-invece-di-condizioni-ambientali` — I limiti FRE/QPE sono fissi alla classe w3/w2, senza condizioni ambientali/sensibilità armatura (aggiornamento normativo, da confermare)
  - `ca-fessurazione/limiti-sigma-s-senza-formula` — I limiti di tensione dell'acciaio (FRE/QPE) sono numeri digitati senza formula di supporto (errore del foglio, da confermare)
  - `ca-fessurazione/sottotitolo-zero-invece-di-vuoto` — Il sottotitolo di sezione mostra 0 invece di restare vuoto quando la cella sorgente è vuota (errore del foglio, da confermare)

### MEN — Progetto e verifica di mensole tozze
- Gruppo: Calcestruzzo armato / Mensole · norma: NTC2018 §4.1.6.1.3 · pacchetto: `strutture.members.ca_mensole`
- Fogli Excel di origine: `Calcolo mensole tozze in c.a. secondo NTC - DM2008.xls`
- Specifica: docs/specs/ca-mensole.md
- Esempio ("Carica esempio"): sì · test: 12 file, 2 golden (valori del foglio), 2 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (17 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 7 voci: 7 da confermare
  - `ca-mensole/acciaio-feb22k-mancante-in-tabella` — L'acciaio FeB22k è selezionabile dal menu ma assente dalla tabella dei materiali (errore del foglio, da confermare)
  - `ca-mensole/capacita-globale-non-limitata-dal-puntone` — La capacità globale della mensola non è limitata dal puntone di calcestruzzo (errore del foglio, da confermare)
  - `ca-mensole/coefficiente-c-tipo-misto` — Il coefficiente c restituisce un testo invece di un numero su uno dei due rami (errore del foglio, da confermare)
  - `ca-mensole/continuita-as-lnk-a-05h` — Continuità non verificata tra i due rami della formula dell'armatura di sospensione al variare di a/h (da verificare, da confermare)
  - `ca-mensole/costanti-formule-tirante-puntone` — Le costanti delle formule puntone-tirante (0,2; 0,4; 0,8; 0,9; 1,5) non sono verificate contro il testo NTC2018 (da verificare, da confermare)
  - `materials/acciaio-armatura-classificazione-storica` — Il catalogo acciai per armatura include gradi storici non più ammessi dalla normativa vigente (aggiornamento normativo, da confermare)
  - `materials/fck-calcestruzzo-fill-down-083-rck` — fck del calcestruzzo è calcolato come 0,83·Rck invece del valore letterale di Tab. 4.1.I (errore del foglio, da confermare)

### PIR — Verifica pilastro in c.a. rettangolare/quadrato (CD "B")
- Gruppo: Calcestruzzo armato / Pilastri · norma: NTC2018 §4.1/§7.4 + Circolare 7/2019; norma=EC2 -> UNI EN 1992-1-1:2005 con Allegato Nazionale italiano (α_cc=0.85); norma=NTC2008 -> solo riproduzione del foglio Excel originale (richiede legacy_compat=True) · pacchetto: `strutture.members.ca_pilastri.tool_rettangolare`
- Fogli Excel di origine: `Calcolo pilastri in c.a. secondo NTC - DM2008.xls`, `workbooks/30_Calcolo pilastri in c.a. secondo NTC 2018 e Circolare2019.xls`, `workbooks/31_Calcolo pilastri in c.a. secondo UNI EN 1992-1-1 2005.xls`
- Specifica: docs/specs/ (pacchetto strutture.members.ca_pilastri.tool_rettangolare)
- Esempio ("Carica esempio"): sì · test: 0 file, 0 golden (valori del foglio), 0 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (30 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve `sezione.mrd_x_kNm` · "Usa in…" verso —
- Registro: 25 voci: 25 da confermare
  - `ca-pilastri/area-minima-longitudinale-min-invece-max` — L'area minima di armatura longitudinale combina i due criteri con il minimo invece del massimo (errore del foglio, da confermare)
  - `ca-pilastri/confinamento-lato-sbagliato` — Geometria di confinamento del pilastro rettangolare usa sempre lo stesso lato invece del lato maggiore/minore corretti (errore del foglio, da confermare)
  - `ca-pilastri/controllo-percentuale-minima-rimosso-ntc2018-ec2` — I fogli NTC2018 ed EC2 non verificano più il limite minimo di percentuale di armatura, solo il tetto massimo del 4% (errore del foglio, da confermare)
  - `ca-pilastri/cot-theta-nu1-incoerente-ec2` — L'angolo del traliccio (cotθ) usava sempre il coefficiente ν1 NTC anche in norma EC2, incoerente col resto (errore del foglio, da confermare)
  - `ca-pilastri/diametro-minimo-staffe-min-invece-max` — Il diametro minimo delle staffe combina i due criteri con il minimo invece del massimo (errore del foglio, da confermare)
  - `ca-pilastri/ec2-coefficiente-area-minima-annesso-nazionale` — Area minima armatura EC2 standard deve usare 0,003 dell'Annesso Nazionale italiano, non 0,002 raccomandato (aggiornamento normativo, da confermare)
  - `ca-pilastri/ec2-fattore-nu1-resistenza-taglio` — Il foglio EC2 usa il fattore ν1 nella resistenza a taglio calcestruzzo, diverso dal valore fisso NTC (aggiornamento normativo, da confermare)
  - `ca-pilastri/ec2-snellezza-limite-a-c-fissi` — Il foglio EC2 fissa a 0,7 i coefficienti A e C della snellezza limite, invece di calcolarli dai dati reali (errore del foglio, da confermare)
  - `ca-pilastri/interasse-barre-formula-circolare` — L'interasse barre longitudinali del pilastro rettangolare usa la formula circolare, ignora il secondo lato (errore del foglio, da confermare)
  - `ca-pilastri/interasse-barre-sismico-etichetta-errata` — Verifica interasse massimo barre longitudinali etichettata sismica ma confrontava il limite non sismico 300mm (aggiornamento normativo, da confermare)
  - `ca-pilastri/l0-fisso-3000mm` — La lunghezza libera di inflessione l0 è fissata a 3000 mm indipendentemente dall'altezza reale del pilastro (errore del foglio, da confermare)
  - `ca-pilastri/lambda-lim-manca-conversione-kn` — Snellezza limite (NTC2008) confronta Ned in kN direttamente contro Ac·fcd in N, senza conversione (errore del foglio, da confermare)
  - `ca-pilastri/lambda-lim-ntc2018-foglio-non-normativo` — Snellezza limite del foglio NTC2018 usa una formula empirica diversa dal testo normativo (aggiornamento normativo, da confermare)
  - `ca-pilastri/limite-area-minima-longitudinale-stretto` — Verifica area minima armatura longitudinale con confronto stretto invece che inclusivo (errore del foglio, da confermare)
  - `ca-pilastri/limite-diametro-barre-longitudinali-stretto` — Verifica diametro minimo barre longitudinali con confronto stretto invece che inclusivo (errore del foglio, da confermare)
  - `ca-pilastri/limite-diametro-staffe-stretto` — Verifica diametro minimo staffe con confronto stretto invece che inclusivo (errore del foglio, da confermare)
  - `ca-pilastri/norma-scelta-e-modalita-foglio-per-norma` — Il pilastro supporta tre norme (NTC2018/EC2/NTC2008), ciascuna col proprio foglio in modalità 'riproduci il foglio' (scelta ingegneristica, da confermare)
  - `ca-pilastri/raggio-inerzia-sezione-netta` — Raggio d'inerzia calcolato sulla sezione netta (ridotta del copriferro) invece che sulla sezione lorda (errore del foglio, da confermare)
  - `ca-pilastri/ramo-morto-coefficiente-ac` — Il ramo 'sezione in trazione' del coefficiente ac è inattingibile per un errore nella condizione (errore del foglio, da confermare)
  - `ca-pilastri/rm-default-non-noto-va-a-c-07` — Il valore di default di rm quando non noto deve dare C=0,7, non C=1,7 (aggiornamento normativo, da confermare)
  - `ca-pilastri/taglio-capacity-design-manca-gamma-rd` — Il taglio da capacity design non applica il fattore di sovraresistenza γRd e considera un solo momento resistente (errore del foglio, da confermare)
  - `ca-pilastri/verifica-passo-staffe-zona-critica-mancante` — Il passo massimo delle staffe in zona critica era calcolato ma mai confrontato con il passo effettivo in una verifica (aggiornamento normativo, da confermare)
  - `ca-pilastri/verifica-staffe-confronta-classe-calcestruzzo` — Verifica diametro minimo staffe (rett.) confronta con la classe calcestruzzo (testo), non col diametro effettivo (errore del foglio, da confermare)
  - `materials/acciaio-armatura-classificazione-storica` — Il catalogo acciai per armatura include gradi storici non più ammessi dalla normativa vigente (aggiornamento normativo, da confermare)
  - `materials/fck-calcestruzzo-fill-down-083-rck` — fck del calcestruzzo è calcolato come 0,83·Rck invece del valore letterale di Tab. 4.1.I (errore del foglio, da confermare)

### PIC — Verifica pilastro in c.a. circolare (CD "B")
- Gruppo: Calcestruzzo armato / Pilastri · norma: NTC2018 §4.1/§7.4 + Circolare 7/2019; norma=EC2 -> UNI EN 1992-1-1:2005 con Allegato Nazionale italiano (α_cc=0.85); norma=NTC2008 -> solo riproduzione del foglio Excel originale (richiede legacy_compat=True) · pacchetto: `strutture.members.ca_pilastri.tool_circolare`
- Fogli Excel di origine: `Calcolo pilastri in c.a. secondo NTC - DM2008.xls`, `workbooks/30_Calcolo pilastri in c.a. secondo NTC 2018 e Circolare2019.xls`, `workbooks/31_Calcolo pilastri in c.a. secondo UNI EN 1992-1-1 2005.xls`
- Specifica: docs/specs/ (pacchetto strutture.members.ca_pilastri.tool_circolare)
- Esempio ("Carica esempio"): sì · test: 0 file, 0 golden (valori del foglio), 0 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (31 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve `sezione.mrd_x_kNm` · "Usa in…" verso —
- Registro: 22 voci: 22 da confermare
  - `ca-pilastri/area-minima-longitudinale-min-invece-max` — L'area minima di armatura longitudinale combina i due criteri con il minimo invece del massimo (errore del foglio, da confermare)
  - `ca-pilastri/controllo-percentuale-minima-rimosso-ntc2018-ec2` — I fogli NTC2018 ed EC2 non verificano più il limite minimo di percentuale di armatura, solo il tetto massimo del 4% (errore del foglio, da confermare)
  - `ca-pilastri/cot-theta-nu1-incoerente-ec2` — L'angolo del traliccio (cotθ) usava sempre il coefficiente ν1 NTC anche in norma EC2, incoerente col resto (errore del foglio, da confermare)
  - `ca-pilastri/diametro-minimo-staffe-min-invece-max` — Il diametro minimo delle staffe combina i due criteri con il minimo invece del massimo (errore del foglio, da confermare)
  - `ca-pilastri/ec2-coefficiente-area-minima-annesso-nazionale` — Area minima armatura EC2 standard deve usare 0,003 dell'Annesso Nazionale italiano, non 0,002 raccomandato (aggiornamento normativo, da confermare)
  - `ca-pilastri/ec2-fattore-nu1-resistenza-taglio` — Il foglio EC2 usa il fattore ν1 nella resistenza a taglio calcestruzzo, diverso dal valore fisso NTC (aggiornamento normativo, da confermare)
  - `ca-pilastri/ec2-snellezza-limite-a-c-fissi` — Il foglio EC2 fissa a 0,7 i coefficienti A e C della snellezza limite, invece di calcolarli dai dati reali (errore del foglio, da confermare)
  - `ca-pilastri/interasse-barre-sismico-etichetta-errata` — Verifica interasse massimo barre longitudinali etichettata sismica ma confrontava il limite non sismico 300mm (aggiornamento normativo, da confermare)
  - `ca-pilastri/l0-fisso-3000mm` — La lunghezza libera di inflessione l0 è fissata a 3000 mm indipendentemente dall'altezza reale del pilastro (errore del foglio, da confermare)
  - `ca-pilastri/lambda-lim-manca-conversione-kn` — Snellezza limite (NTC2008) confronta Ned in kN direttamente contro Ac·fcd in N, senza conversione (errore del foglio, da confermare)
  - `ca-pilastri/lambda-lim-ntc2018-foglio-non-normativo` — Snellezza limite del foglio NTC2018 usa una formula empirica diversa dal testo normativo (aggiornamento normativo, da confermare)
  - `ca-pilastri/limite-area-minima-longitudinale-stretto` — Verifica area minima armatura longitudinale con confronto stretto invece che inclusivo (errore del foglio, da confermare)
  - `ca-pilastri/limite-diametro-barre-longitudinali-stretto` — Verifica diametro minimo barre longitudinali con confronto stretto invece che inclusivo (errore del foglio, da confermare)
  - `ca-pilastri/limite-diametro-staffe-stretto` — Verifica diametro minimo staffe con confronto stretto invece che inclusivo (errore del foglio, da confermare)
  - `ca-pilastri/norma-scelta-e-modalita-foglio-per-norma` — Il pilastro supporta tre norme (NTC2018/EC2/NTC2008), ciascuna col proprio foglio in modalità 'riproduci il foglio' (scelta ingegneristica, da confermare)
  - `ca-pilastri/raggio-inerzia-sezione-netta` — Raggio d'inerzia calcolato sulla sezione netta (ridotta del copriferro) invece che sulla sezione lorda (errore del foglio, da confermare)
  - `ca-pilastri/ramo-morto-coefficiente-ac` — Il ramo 'sezione in trazione' del coefficiente ac è inattingibile per un errore nella condizione (errore del foglio, da confermare)
  - `ca-pilastri/rm-default-non-noto-va-a-c-07` — Il valore di default di rm quando non noto deve dare C=0,7, non C=1,7 (aggiornamento normativo, da confermare)
  - `ca-pilastri/taglio-capacity-design-manca-gamma-rd` — Il taglio da capacity design non applica il fattore di sovraresistenza γRd e considera un solo momento resistente (errore del foglio, da confermare)
  - `ca-pilastri/verifica-passo-staffe-zona-critica-mancante` — Il passo massimo delle staffe in zona critica era calcolato ma mai confrontato con il passo effettivo in una verifica (aggiornamento normativo, da confermare)
  - `materials/acciaio-armatura-classificazione-storica` — Il catalogo acciai per armatura include gradi storici non più ammessi dalla normativa vigente (aggiornamento normativo, da confermare)
  - `materials/fck-calcestruzzo-fill-down-083-rck` — fck del calcestruzzo è calcolato come 0,83·Rck invece del valore letterale di Tab. 4.1.I (errore del foglio, da confermare)

### PUN — Verifica a punzonamento e progetto armature verticali (solai/platee su pilastri o pali)
- Gruppo: Calcestruzzo armato / Punzonamento · norma: EN 1992-1-1 §6.4 · pacchetto: `strutture.members.ca_punzonamento.compose`
- Fogli Excel di origine: `workbooks/2xxxx_Punzonamento - EC2 §6.4.xlsx`
- Specifica: docs/specs/ (pacchetto strutture.members.ca_punzonamento.compose)
- Esempio ("Carica esempio"): sì · test: 0 file, 0 golden (valori del foglio), 0 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (23 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 12 voci: 12 da confermare
  - `ca-punzonamento/altezza-utile-non-positiva-crash` — Un'altezza utile non positiva causava un errore generico invece di un messaggio chiaro (aggiornamento normativo, da confermare)
  - `ca-punzonamento/area-perimetro-colonna-circolare-errata` — L'area del perimetro di controllo usa sempre la formula rettangolare, sbagliata per colonne circolari (errore del foglio, da confermare)
  - `ca-punzonamento/armatura-calcolata-anche-se-non-necessaria` — L'armatura a punzonamento è sempre calcolata anche quando la verifica passa già senza armatura (errore del foglio, da confermare)
  - `ca-punzonamento/diametro-staffa-28-probabile-refuso` — Il diametro staffa 28mm nel menu a tendina è probabilmente un refuso per 18mm (da verificare, da confermare)
  - `ca-punzonamento/fywd-ef-senza-limite` — La tensione efficace di snervamento delle staffe non è mai limitata a fyd (errore del foglio, da confermare)
  - `ca-punzonamento/perimetro-troncato-bordo-angolo-non-implementato` — Per colonne di bordo/angolo, il perimetro critico non è troncato al bordo libero (da verificare, da confermare)
  - `ca-punzonamento/rho-l-punzonamento-senza-limite-2pc` — Il rapporto di armatura longitudinale ρl usato nella resistenza a punzonamento non è mai limitato al 2% (errore del foglio, da confermare)
  - `ca-punzonamento/verifica-asw-min-mancante` — L'area minima delle staffe (eq. 9.11) era calcolata ma mai confrontata con l'armatura effettiva in una verifica (aggiornamento normativo, da confermare)
  - `ca-punzonamento/vrd-max-filo-pilastro-coefficiente-semplificato` — Resistenza massima a punzonamento al filo del pilastro usa un coefficiente semplificato senza base normativa (errore del foglio, da confermare)
  - `ec2-shared/area-perimetro-rettangolare-formula-non-standard` — Area perimetro rettangolare del foglio punzonamento coincide con la formula standard solo per colonne quadrate (da verificare, da confermare)
  - `ec2-shared/coefficiente-vrd-max-scelta-ingegneristica` — Il coefficiente della resistenza massima a punzonamento/taglio vRd,max (0,4 vs 0,5) è una scelta dell'ingegnere (scelta ingegneristica, da confermare)
  - `ec2-shared/vrdc-capacita-portante-senza-limite-vmin` — Il ramo av/2d della resistenza a punzonamento vicino all'appoggio non applicava il limite minimo vmin (aggiornamento normativo, da confermare)

### SMN — Dominio di resistenza a pressoflessione N-M di una sezione in c.a.
- Gruppo: Calcestruzzo armato / Pilastri · norma: NTC2018 §4.1.2.3.4.2 · pacchetto: `strutture.members.ca_sezione_mn.compose`
- Fogli Excel di origine: nessuno (strumento nuovo, non deriva da un foglio)
- Specifica: docs/specs/ (pacchetto strutture.members.ca_sezione_mn.compose)
- Esempio ("Carica esempio"): sì · test: 0 file, 0 golden (valori del foglio), 0 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (17 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce `sezione.mrd_x_kNm` · riceve — · "Usa in…" verso `ca-pilastro-circolare`, `ca-pilastro-rettangolare`
- Registro: nessuna voce di registro

### TNA — Resistenza a taglio di sezione in c.a. priva di armatura trasversale
- Gruppo: Calcestruzzo armato / Travi · norma: NTC2018 §4.1.2.3.5.1 · pacchetto: `strutture.members.ca_taglio_non_armato.compose`
- Fogli Excel di origine: `Taglio non armato NTC2018.xlsx`, `workbooks/2xxxx_Taglio non armato NTC2018.xlsx`
- Specifica: docs/specs/ (pacchetto strutture.members.ca_taglio_non_armato.compose)
- Esempio ("Carica esempio"): sì · test: 0 file, 0 golden (valori del foglio), 0 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (10 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 3 voci: 3 da confermare
  - `ca-taglio-non-armato/incoerenza-fck-rck-non-segnalata` — Nessun controllo di coerenza tra fck digitato liberamente e Rck nel foglio a striscia (v2) (aggiornamento normativo, da confermare)
  - `ca-taglio-non-armato/rho-l-senza-limite` — Il rapporto di armatura longitudinale ρl non è mai limitato al 2% (errore del foglio, da confermare)
  - `ca-taglio-non-armato/verifica-rho-l-su-valore-gia-limitato` — La verifica del limite di armatura longitudinale confrontava il valore già limitato, mascherando i superamenti reali (aggiornamento normativo, da confermare)

### TRV — Trave in c.a. a sezione rettangolare — progetto e verifica
- Gruppo: Calcestruzzo armato / Travi · norma: NTC2018 §4.1.6.1.1, §4.1.2.3.4.2, §4.1.2.3.5.2, §4.1.2.2.5, §4.1.2.2.4, §7.4.4.1.1, §7.4.6 · pacchetto: `strutture.members.ca_travi`
- Fogli Excel di origine: `Calcolo travi in c.a. secondo NTC - DM2008.xls`
- Specifica: docs/specs/ca-travi.md
- Esempio ("Carica esempio"): sì · test: 15 file, 3 golden (valori del foglio), 2 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (27 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce `trave.sigma_s_rara_MPa` · riceve — · "Usa in…" verso `ca-sle-limitazione-tensioni`
- Registro: 15 voci: 15 da confermare
  - `ca-travi/as-min-usa-z-e-ftk` — As,min di armatura tesa calcolata con z e ftk invece di d e fyk (errore del foglio, da confermare)
  - `ca-travi/ast-min-staffe-doppio-limite` — Area minima delle staffe: il limite NTC2018 1,5·b e il limite EC2 9.2.2(5) vanno applicati entrambi, il maggiore governa (errore del foglio, da confermare)
  - `ca-travi/blocco-tensioni-081-vs-08` — Fattore del blocco di tensioni in flessione 0,81 invece di 0,80 e nessuna verifica di duttilità (errore del foglio, da confermare)
  - `ca-travi/classe-fessurazione-non-verificata` — La classe di apertura fessura scelta dall'utente non è confrontata con la tabella 4.1.IV (da verificare, da confermare)
  - `ca-travi/duplicazione-classe-duttilita` — La classe di duttilità va inserita due volte in due celle non collegate (da verificare, da confermare)
  - `ca-travi/duttilita-longitudinale-sismica-mancante` — Nessuna verifica dei limiti di armatura longitudinale sismica del §7.4.6.2.1 (da verificare, da confermare)
  - `ca-travi/limite-sigma-acciaio-sle-fisso` — Limite di tensione dell'acciaio in combinazione rara fissato a 360 MPa invece di 0,80·fyk (errore del foglio, da confermare)
  - `ca-travi/passo-max-staffe-usa-z` — Passo massimo staffe calcolato con 1000/3 mm e il braccio di leva z invece di 330 mm e d (errore del foglio, da confermare)
  - `ca-travi/passo-max-zona-critica-degenera` — Passo massimo staffe in zona critica si azzera se la seconda fila di ferri non è usata, e usa h invece di d (errore del foglio, da confermare)
  - `ca-travi/tabella-fessurazione-diametri-non-tabulati` — Ricerca esatta del limite di tensione per apertura fessure fallisce per diametri di barra non tabulati (errore del foglio, da confermare)
  - `ca-travi/taglio-capacity-design-ignora-luce` — Taglio da capacity design confonde un momento con una forza e ignora la luce della trave (errore del foglio, da confermare)
  - `ca-travi/taglio-gerarchia-senza-carichi-gravitazionali` — Il taglio di gerarchia delle resistenze non somma il taglio dei carichi gravitazionali (errore del foglio, da confermare)
  - `materials/acciaio-armatura-classificazione-storica` — Il catalogo acciai per armatura include gradi storici non più ammessi dalla normativa vigente (aggiornamento normativo, da confermare)
  - `materials/fck-calcestruzzo-fill-down-083-rck` — fck del calcestruzzo è calcolato come 0,83·Rck invece del valore letterale di Tab. 4.1.I (errore del foglio, da confermare)
  - `shared-ca/asse-neutro-fessurato-generalizzato-a-doppia-armatura` — Asse neutro sezione fessurata generalizzato al caso con armatura compressa, oltre alla semplice del foglio (aggiornamento normativo, da confermare)

### MUR — Muro di sostegno a mensola
- Gruppo: Geotecnica / Muri di sostegno · norma: NTC2018 §6.5.3.1.1, §6.5.3.1.2, §6.4.2.1, §7.11.6.2.1, §4.1.2 · pacchetto: `strutture.members.muro`
- Fogli Excel di origine: `Muro di sostegno DM2018.xlsx`
- Specifica: docs/specs/muro-sostegno.md
- Esempio ("Carica esempio"): sì · test: 24 file, 4 golden (valori del foglio), 2 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (81 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve `sito.ag_g`, `sito.categoria_sottosuolo`, `sito.categoria_topografica`, `sito.f0` · "Usa in…" verso —
- Registro: 19 voci: 19 da confermare
  - `muro-sostegno/armatura-necessaria-senza-limite-inferiore` — L'armatura necessaria governante non ha un limite inferiore a zero (errore del foglio, da confermare)
  - `muro-sostegno/armatura-senza-minimo-normativo` — Le armature di paramento e fondazione sono scelte senza l'armatura minima di norma (errore del foglio, da confermare)
  - `muro-sostegno/capacita-portante-sismica-parametri-caratteristici` — Capacità portante sismica con parametri caratteristici, scorrimento sismico con parametri ridotti M2 (scelta ingegneristica, da confermare)
  - `muro-sostegno/coefficienti-resistenza-mancanti` — Le verifiche a scorrimento e ribaltamento non applicano i coefficienti di resistenza di norma (errore del foglio, da confermare)
  - `muro-sostegno/diametro-armatura-non-commerciale` — Il diametro di armatura calcolato non corrisponde a un diametro commerciale disponibile (errore del foglio, da confermare)
  - `muro-sostegno/fyk-input-libero-invece-di-classe` — La resistenza dell'acciaio d'armatura era un valore libero invece di una classe commerciale (scelta ingegneristica, da confermare)
  - `muro-sostegno/gamma-e-unita-ambigua` — L'unita' di misura dichiarata per il coefficiente di importanza sismica gamma_E e' incoerente (da verificare, da confermare)
  - `muro-sostegno/inerzia-sismica-muro-terreno-assente` — Le forze d'inerzia sismiche di muro e terreno non sono incluse nella domanda di scorrimento e ribaltamento (errore del foglio, da confermare)
  - `muro-sostegno/momento-autopeso-tacco-esponenti-scambiati` — Il momento da peso proprio della soletta di monte scambia sporgenza e spessore (errore del foglio, da confermare)
  - `muro-sostegno/momento-paramento-altezza-piena-invece-di-stelo` — Il momento flettente del paramento usa l'altezza totale invece della sola altezza dello stelo (errore del foglio, da confermare)
  - `muro-sostegno/phi-d-divide-angolo-invece-di-tangente` — L'angolo di attrito di progetto divide direttamente l'angolo invece della sua tangente (errore del foglio, da confermare)
  - `muro-sostegno/pressione-interpolata-tacco-negativa` — La pressione interpolata nel tacco puo' risultare negativa per alcune geometrie (da verificare, da confermare)
  - `muro-sostegno/scorrimento-con-attrito-del-terreno-di-fondazione` — La resistenza allo scorrimento usa l'angolo di attrito del terreno di fondazione quando è noto (scelta ingegneristica, da confermare)
  - `muro-sostegno/ss-sempre-calcolato-dal-vivo` — Il fattore di amplificazione stratigrafica Ss viene sempre ricalcolato invece di essere un valore congelato (aggiornamento normativo, da confermare)
  - `muro-sostegno/st-input-libero-invece-di-enum` — Il fattore topografico ST era un numero libero invece di derivare dalla categoria topografica (aggiornamento normativo, da confermare)
  - `muro-sostegno/verifica-portanza-non-segnalata` — La capacita' portante del terreno di fondazione non era mai calcolata, solo segnalata come esclusa (errore del foglio, da confermare)
  - `ntc-combos/gamma-g2-favorevole-valore-2008` — Il coefficiente gamma_G2 favorevole era ancora il valore NTC2008 (aggiornamento normativo, da confermare)
  - `ntc-combos/riga-ribaltamento-mancante` — La tabella dei coefficienti di resistenza non includeva la riga per la verifica a ribaltamento (aggiornamento normativo, da confermare)
  - `ntc-site-seismic/ss-categoria-b-limite-inferiore-basso` — Il coefficiente di amplificazione stratigrafica Ss per il suolo B ha un limite inferiore troppo basso (errore del foglio, da confermare)

### EDO — Cedimento edometrico di una fondazione rettangolare su terreno stratificato
- Gruppo: Geotecnica / Cedimenti · norma: NTC2018 §6.2.2 / Circolare 2019 C6.2.2 (metodo edometrico di Terzaghi) · pacchetto: `strutture.geotechnics.cedimenti_edometrico`
- Fogli Excel di origine: `workbooks/2xxxx_Cedimenti fondazioni_elastico+edo.xlsx`
- Specifica: docs/specs/geo-cedimenti-edometrico.md
- Esempio ("Carica esempio"): sì · test: 15 file, 2 golden (valori del foglio), 2 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (11 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 7 voci: 7 da confermare
  - `geo-cedimenti-edometrico/metodo-tensioni-forzato-approssimato` — In modalità legacy il metodo di tensione indotta è sempre quello approssimato, mai Newmark (scelta ingegneristica, da confermare)
  - `geo-cedimenti-edometrico/modulo-edometrico-zero-fuori-stratigrafia` — Il modulo edometrico oltre l'ultimo strato diventa 0 e genera un contributo di cedimento nullo silenzioso (errore del foglio, da confermare)
  - `geo-cedimenti-edometrico/pressione-netta-senza-controllo-segno` — La pressione netta di progetto non controlla il segno e può diventare negativa senza un messaggio chiaro (errore del foglio, da confermare)
  - `geo-cedimenti-edometrico/tensione-verticale-sempre-sommersa` — La tensione verticale efficace assume sempre falda alla base della fondazione, ignorando l'affondamento reale (errore del foglio, da confermare)
  - `geo-cedimenti-edometrico/unita-affondamento-non-confermata` — L'unità di misura dell'affondamento usato nella pressione netta non è confermata contro il foglio sorgente (da verificare, da confermare)
  - `geo-cedimenti-edometrico/z-crit-manuale-non-derivata` — La profondità critica Z,crit del metodo edometrico è un valore manuale, non calcolato (errore del foglio, da confermare)
  - `soil-layers-coverage-and-weighting/lookup-strato-zero-oltre-copertura` — La ricerca dello strato oltre l'ultima profondità coperta restituiva zero invece di segnalare un errore (errore del foglio, da confermare)

### NEW — Cedimento elastico - integrazione di Newmark
- Gruppo: Geotecnica / Cedimenti · norma: Newmark 1942 (?) · pacchetto: `strutture.geotechnics.cedimenti_elastico.tool_newmark`
- Fogli Excel di origine: `workbooks/2xxxx_Cedimenti fondazioni_elastico+edo.xlsx`
- Specifica: docs/specs/ (pacchetto strutture.geotechnics.cedimenti_elastico.tool_newmark)
- Esempio ("Carica esempio"): sì · test: 0 file, 0 golden (valori del foglio), 0 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (10 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 8 voci: 8 da confermare
  - `geo-cedimenti-elastico/blocco-500-profondita-integrazione-troncata` — Il blocco di calcolo del punto generico integra la tensione un passo più corto di quanto sembri dalla tabella (errore del foglio, da confermare)
  - `geo-cedimenti-elastico/profondita-integrazione-centro-t6-z6-diverse` — Le due stime di cedimento al centro sono integrate a profondità diverse e arbitrarie (errore del foglio, da confermare)
  - `geo-cedimenti-elastico/punto-o-accoppiamento-lati-errato` — Il cedimento nel punto O generico accoppia due volte lo stesso lato invece di un lato per ciascun rettangolo d'angolo (errore del foglio, da confermare)
  - `geo-cedimenti-elastico/rettangolo-confronto-500-dieci-volte-piu-grande` — Il rettangolo di confronto del foglio 500 è dieci volte più grande dei fogli gemelli, forse un refuso (da verificare, da confermare)
  - `geo-cedimenti-elastico/stratigrafia-senza-controllo-continuita` — La stratigrafia del terreno non era controllata per sovrapposizioni o buchi tra gli strati (errore del foglio, da confermare)
  - `geo-cedimenti-elastico/tensione-valutata-a-fondo-fetta` — L'incremento di tensione è valutato sempre al fondo di ogni fetta, sottostimando sistematicamente il cedimento integrato (errore del foglio, da confermare)
  - `soil-layers-coverage-and-weighting/lookup-strato-zero-oltre-copertura` — La ricerca dello strato oltre l'ultima profondità coperta restituiva zero invece di segnalare un errore (errore del foglio, da confermare)
  - `soil-stress-fadum-superposition/sovrapposizione-fadum-coppie-dello-stesso-lato` — La sovrapposizione di Fadum per il punto generico accoppia due segmenti dello stesso lato invece di un segmento per lato (errore del foglio, da confermare)

### TG — Cedimento elastico - Timoshenko & Goodier (rettangolo flessibile)
- Gruppo: Geotecnica / Cedimenti · norma: Timoshenko & Goodier 1970 (?) · pacchetto: `strutture.geotechnics.cedimenti_elastico.tool_timoshenko_goodier`
- Fogli Excel di origine: `workbooks/2xxxx_Cedimenti fondazioni_elastico+edo.xlsx`
- Specifica: docs/specs/ (pacchetto strutture.geotechnics.cedimenti_elastico.tool_timoshenko_goodier)
- Esempio ("Carica esempio"): sì · test: 0 file, 0 golden (valori del foglio), 0 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (10 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 5 voci: 5 da confermare
  - `geo-cedimenti-elastico/fattore-forma-bordo-usa-formula-di-spigolo` — Il cedimento al bordo (punto medio) usa la formula dello spigolo, non quella del punto medio (errore del foglio, da confermare)
  - `geo-cedimenti-elastico/modulo-medio-pesato-solo-primi-4-strati` — Il modulo elastico medio (T&G) considera solo i primi 4 strati, senza limitarli all'altezza significativa (errore del foglio, da confermare)
  - `geo-cedimenti-elastico/stratigrafia-senza-controllo-continuita` — La stratigrafia del terreno non era controllata per sovrapposizioni o buchi tra gli strati (errore del foglio, da confermare)
  - `geo-cedimenti-elastico/timoshenko-goodier-coefficiente-1-meno-mu` — Il cedimento elastico di Timoshenko & Goodier usa (1−μ) invece del corretto (1−μ²) (errore del foglio, da confermare)
  - `soil-layers-coverage-and-weighting/modulo-pesato-solo-primi-4-strati` — Il modulo medio pesato su una profondità H sommava solo i primi 4 strati, ignorando quelli oltre e senza tagliarli a H (errore del foglio, da confermare)

### PAV — Verifica pavimento industriale su sottofondo Winkler (CNR-DT 211/2014)
- Gruppo: Fondazioni / Pavimenti industriali · norma: CNR-DT 211/2014 · EC2 §6.4 · pacchetto: `strutture.foundations.pavimento_industriale`
- Fogli Excel di origine: `workbooks/10x_Pavimento industriale CNR_DT211-2014.xlsx`
- Specifica: docs/specs/pavimento-industriale.md
- Esempio ("Carica esempio"): sì · test: 21 file, 2 golden (valori del foglio), 2 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (30 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 6 voci: 6 da confermare
  - `ec2-shared/coefficiente-vrd-max-scelta-ingegneristica` — Il coefficiente della resistenza massima a punzonamento/taglio vRd,max (0,4 vs 0,5) è una scelta dell'ingegnere (scelta ingegneristica, da confermare)
  - `pavimento-industriale/carico-slu-bordo-spigolo-riferimento-gamma-centro` — Il carico ULS bordo/spigolo leggeva il coefficiente di sicurezza della colonna centro (errore del foglio, da confermare)
  - `pavimento-industriale/coefficiente-vrd-max-punzonamento-scelta-utente` — Il coefficiente della resistenza massima a punzonamento è un parametro normativo da scegliere (scelta ingegneristica, da confermare)
  - `pavimento-industriale/etichetta-soglia-giunto-1-2-vs-formula-1-5` — L'etichetta della verifica dei giunti indica una soglia diversa da quella realmente usata nella formula (da verificare, da confermare)
  - `pavimento-industriale/perimetro-punzonamento-bordo-spigolo-usa-spessore-non-altezza-utile` — Il perimetro a punzonamento in bordo/spigolo usa lo spessore totale invece dell'altezza utile (errore del foglio, da confermare)
  - `pavimento-industriale/verifica-tensionale-superiore-usa-resistenza-caratteristica` — La verifica tensionale in fibra superiore confronta con la resistenza caratteristica, non di progetto (errore del foglio, da confermare)

### PLI — Verifica plinto isolato su tabella reazioni
- Gruppo: Fondazioni / Plinti · norma: NTC2018 §6.4.2 / §6.4.3, EC2 §7.2/§7.3 · pacchetto: `strutture.foundations.plinti_isolati`
- Fogli Excel di origine: `workbooks/2xxxx_Plinti isolati.xlsx`
- Specifica: docs/specs/fond-plinti-isolati.md
- Esempio ("Carica esempio"): sì · test: 25 file, 24 golden (valori del foglio), 1 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (19 passi sull'esempio) · schizzo: sì · importazione MIDAS: sì
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 17 voci: 17 da confermare
  - `footing-pressure/fattore-mpa-kgcm2-approssimato` — Il fattore di conversione MPa -> kg/cm² usato per le colonne di pressione è un'approssimazione, non il valore esatto (da verificare, da confermare)
  - `footing-pressure/pressione-biassiale-sovrapposizione-approssimata` — La pressione massima biassiale è la somma di due verifiche uniassiali, non quella esatta (errore del foglio, da confermare)
  - `plinti-isolati/capacita-portante-terreno-assente-nel-foglio` — La verifica di capacità portante NTC2018 §6.4.2.1 è una funzionalità nuova, assente dal foglio originale (scelta ingegneristica, da confermare)
  - `plinti-isolati/clausola-portanza-etichettata-come-verifica-ntc-completa` — La clausola di portanza era etichettata come verifica NTC2018 completa, che in realtà non esegue (errore del foglio, da confermare)
  - `plinti-isolati/diametro-armatura-arrotondato-a-pari-non-commerciale` — Il diametro dell'armatura è arrotondato al millimetro pari superiore, non al diametro realmente commerciale (errore del foglio, da confermare)
  - `plinti-isolati/eccentricita-cantilever-x-y-scambiate` — Il momento a sbalzo lungo X usa l'eccentricità di Y e viceversa, invertendo la convenzione degli assi (errore del foglio, da confermare)
  - `plinti-isolati/fattore-mpa-kgcm2-approssimato` — Le pressioni riportate in kg/cm² usano un fattore di conversione approssimato invece di quello esatto (da verificare, da confermare)
  - `plinti-isolati/inviluppo-momento-slu-include-famiglia-sle` — L'inviluppo del momento a flessione include una famiglia di esercizio ed esclude una famiglia sismica ULS (errore del foglio, da confermare)
  - `plinti-isolati/momento-mensola-divisore-kgfcm-knm-approssimato` — Il ramo legacy del momento a sbalzo usa un fattore di conversione kgf·cm→kN·m approssimato (da verificare, da confermare)
  - `plinti-isolati/momento-mensola-misurato-dal-centro-non-dal-filo-pilastro` — Il momento a sbalzo della soletta è misurato dal centro del plinto, ignorando il pilastro/plinto rialzato (errore del foglio, da confermare)
  - `plinti-isolati/phi-min-divisore-500-invece-di-fyk` — Il diametro minimo di armatura divide sempre per l'acciaio da 500 N/mm², anche con una classe di armatura diversa (errore del foglio, da confermare)
  - `plinti-isolati/ribaltamento-autopeso-famiglia-sbagliata` — La verifica al ribaltamento usa il fattore di sicurezza del peso proprio della famiglia sbagliata (errore del foglio, da confermare)
  - `plinti-isolati/ribaltamento-mrib-zero-valore-fittizio` — Il coefficiente al ribaltamento tratta allo stesso modo l'assenza di momento ribaltante e una verifica molto sicura (errore del foglio, da confermare)
  - `plinti-isolati/scorrimento-senza-fattore-parziale-gammar` — La verifica di scorrimento non applicava il fattore parziale di resistenza richiesto dalla normativa (errore del foglio, da confermare)
  - `plinti-isolati/scorrimento-taglio-zero-valore-fittizio` — Il coefficiente di sicurezza allo scorrimento tratta allo stesso modo l'assenza di taglio e una verifica molto sicura (errore del foglio, da confermare)
  - `plinti-isolati/sezione-parzializzata-altezza-lorda-non-effettiva` — Le tensioni di esercizio in sezione parzializzata usano l'altezza lorda del plinto invece dell'altezza utile effettiva (errore del foglio, da confermare)
  - `plinti-isolati/sle-famiglia-assente-passa-a-zero` — Le verifiche di esercizio davano un esito positivo fittizio quando la famiglia non era presente (errore del foglio, da confermare)

### PLP — Verifica plinto su pali (puntoni e tiranti)
- Gruppo: Fondazioni / Plinti · norma: EC2 §6.5 (puntoni e tiranti) / §9.8.1 (plinti su pali) / §6.4 (punzonamento) / §6.2.2 (taglio) · pacchetto: `strutture.foundations.plinti_pali`
- Fogli Excel di origine: `workbooks/2xxxx_Plinti su pali_PL-FX_S&T Eurocode 2.xlsx`
- Specifica: docs/specs/fond-plinti-pali.md
- Esempio ("Carica esempio"): sì · test: 17 file, 5 golden (valori del foglio), 2 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (38 passi sull'esempio) · schizzo: sì · importazione MIDAS: sì
- Collegamenti: fornisce — · riceve — · "Usa in…" verso —
- Registro: 26 voci: 26 da confermare
  - `ec2-shared/coefficiente-vrd-max-scelta-ingegneristica` — Il coefficiente della resistenza massima a punzonamento/taglio vRd,max (0,4 vs 0,5) è una scelta dell'ingegnere (scelta ingegneristica, da confermare)
  - `ec2-shared/strut-tie-coefficienti-non-standard-plinto-pali` — I coefficienti di resistenza dei nodi puntone-tirante del plinto su pali non corrispondono a quelli standard EC2 (da verificare, da confermare)
  - `ec2-shared/vrdc-capacita-portante-senza-limite-vmin` — Il ramo av/2d della resistenza a punzonamento vicino all'appoggio non applicava il limite minimo vmin (aggiornamento normativo, da confermare)
  - `plinti-pali/angolo-puntone-fascia-sicurezza-20-70-non-normativa` — La fascia di sicurezza 20°-70° sull'angolo del puntone è una cautela ingegneristica, non una clausola della norma (da verificare, da confermare)
  - `plinti-pali/angolo-puntone-limitato-a-25-gradi` — L'angolo del puntone era limitato a un minimo di 25 gradi invece di usare la vera geometria (errore del foglio, da confermare)
  - `plinti-pali/armatura-superiore-diametro-unico-semplificazione` — L'armatura superiore del plinto è un dimensionamento semplificato con un unico diametro, non riportato nella relazione (da verificare, da confermare)
  - `plinti-pali/armatura-superiore-pi-letterale-invece-di-pi-greco` — L'area di barra dell'armatura superiore usa il letterale 3,14 invece del valore esatto di pi greco (errore del foglio, da confermare)
  - `plinti-pali/beta-con-lati-del-pilastro` — Il fattore di eccentricità β usa i lati del pilastro invece delle dimensioni del perimetro di verifica (scelta ingegneristica, da confermare)
  - `plinti-pali/braccio-leva-flessione-pari-a-d-senza-riduzione` — Il braccio di leva a flessione usa l'intera altezza utile invece del braccio ridotto da equilibrio (errore del foglio, da confermare)
  - `plinti-pali/coefficiente-k-taglio-non-limitato-a-2` — Il coefficiente di scala per il taglio senza armatura non è limitato al valore massimo previsto dalla norma (errore del foglio, da confermare)
  - `plinti-pali/coefficiente-vrd-max-scelta-da-confermare` — La scelta del coefficiente di resistenza massima a taglio/punzonamento va confermata dall'ingegnere (scelta ingegneristica, da confermare)
  - `plinti-pali/coefficiente-vrd-max-taglio-punzonamento` — Il coefficiente della resistenza massima a taglio/punzonamento è un parametro normativo da scegliere (scelta ingegneristica, da confermare)
  - `plinti-pali/flessione-soletta-momento-di-fascia-su-striscia-di-1-m` — Il momento flettente dell'intera fascia di pali è progettato su una striscia di 1 m (da verificare, da confermare)
  - `plinti-pali/lunghezza-ancoraggio-fissa-non-legata-diametro-palo` — La lunghezza di appoggio usata per l'ancoraggio è un valore fisso, non collegato al diametro del palo realmente inserito (errore del foglio, da confermare)
  - `plinti-pali/nodi-puntone-tirante-coefficienti-non-standard` — I coefficienti di resistenza dei nodi puntone-tirante non erano quelli standard della norma (errore del foglio, da confermare)
  - `plinti-pali/peso-proprio-diviso-per-1-4-invece-di-gammag1` — Il peso proprio nella reazione minima per palo è diviso per 1,4 invece del vero coefficiente parziale (errore del foglio, da confermare)
  - `plinti-pali/punzonamento-colonna-alpha-cc-fisso-a-1` — La resistenza a punzonamento sulla colonna usa un coefficiente riduttivo del calcestruzzo pari a 1 (errore del foglio, da confermare)
  - `plinti-pali/punzonamento-colonna-beta-eccentricita-ignorata` — La verifica a punzonamento sulla colonna non considerava l'effetto dell'eccentricità del carico (errore del foglio, da confermare)
  - `plinti-pali/punzonamento-palo-perimetro-non-limitato-interasse` — Il perimetro a punzonamento del palo d'angolo non tiene conto dell'interasse tra pali o del bordo (errore del foglio, da confermare)
  - `plinti-pali/quota-pila-formula-simmetrica-non-generale` — La ripartizione della quota di momento tra i pali usa una formula approssimata valida solo per la griglia quadrata (errore del foglio, da confermare)
  - `plinti-pali/rho-taglio-divisa-per-larghezza-piena-plinto` — La percentuale di armatura per il taglio è divisa per l'intera larghezza del plinto, non per la fascia da 1 m (errore del foglio, da confermare)
  - `plinti-pali/schema-non-2x2-generalizzazione-da-verificare` — Gli schemi puntone-tirante per griglie diverse da 2x2 sono una generalizzazione senza caso cablato (da verificare, da confermare)
  - `plinti-pali/taglio-riduzione-av-senza-limite-inferiore` — La riduzione del taglio per carico vicino all'appoggio non ha un limite inferiore sulla distanza (errore del foglio, da confermare)
  - `plinti-pali/taglio-verifica-equazione-6-5-mancante` — La verifica di taglio senza la riduzione per carico vicino all'appoggio (eq. 6.5) non era mai eseguita (errore del foglio, da confermare)
  - `plinti-pali/tiranti-2x2-senza-proiezione-coseno` — Le forze nei tiranti ortogonali (schema 4 pali) non proiettano la spinta inclinata del puntone (errore del foglio, da confermare)
  - `plinti-pali/tiranti-ortogonali-stesso-angolo-griglia-non-quadrata` — Le forze nei tiranti ortogonali usano lo stesso angolo, corretto solo per una griglia quadrata (errore del foglio, da confermare)

### TCO — Verifica trave di collegamento tra plinti (NTC2018 / EN1998)
- Gruppo: Fondazioni / Travi di collegamento · norma: NTC2018 §7.2.5 / EN1998-1 §5.8.2 / EN1998-5 §5.4.1.2 · pacchetto: `strutture.foundations.travi_collegamento`
- Fogli Excel di origine: `workbooks/50_Calcolo travi di collegamento NTC 2018.xlsx`
- Specifica: docs/specs/fond-travi-collegamento.md
- Esempio ("Carica esempio"): sì · test: 19 file, 3 golden (valori del foglio), 4 oracle (ricalcolo LibreOffice)
- Relazione con formule: sì (25 passi sull'esempio) · schizzo: sì · importazione MIDAS: no
- Collegamenti: fornisce — · riceve `sito.ag_g`, `sito.categoria_topografica`, `sito.f0` · "Usa in…" verso —
- Registro: 4 voci: 4 da confermare
  - `fond-travi-collegamento/coefficiente-alfa-terreno-a-ntc-vs-en` — NTC ed EN danno valori diversi del coefficiente alfa per il terreno di categoria A (da verificare, da confermare)
  - `fond-travi-collegamento/etichetta-snellezza-lambda-scambiata` — L'etichetta della verifica di snellezza indica il confronto invertito rispetto alla formula realmente calcolata (errore del foglio, da confermare)
  - `fond-travi-collegamento/etichetta-tipo-spettro-en-invertita` — L'etichetta del tipo di spettro sismico EN è invertita rispetto alla norma, anche se il valore S usato è corretto (errore del foglio, da confermare)
  - `fond-travi-collegamento/trazione-confronta-resistenza-con-rapporto-non-con-forza` — La verifica a trazione confronta la resistenza con un rapporto di lavoro, non con la forza di progetto (errore del foglio, da confermare)
