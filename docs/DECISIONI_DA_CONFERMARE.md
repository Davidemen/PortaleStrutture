# Decisioni che l'ingegnere responsabile deve confermare

Aggiornato al 2026-09-22. Chi ha sviluppato il programma non è l'ingegnere responsabile dei calcoli: dove il
foglio Excel e la norma non coincidevano, il codice applica la lettura della norma che riteniamo corretta,
ma la scelta finale è vostra. Nulla di quanto segue è nascosto: ogni punto è nel registro delle correzioni
(pagina "Registro correzioni" del programma, `#/registro`) oppure in questo elenco.

## Come si conferma
- Aprire il programma, voce "Registro correzioni" nella barra laterale.
- Filtrare per strumento. Ogni voce mostra: cosa faceva il foglio, cosa fa il codice, la clausola, l'effetto
  numerico sull'esempio. Il pulsante "Confronta con Excel" su ogni strumento mostra i due risultati fianco a fianco.
- Approvare o respingere con la propria sigla. Una voce respinta resta applicata in modalità standard (regola
  scelta dal committente: "segnala e correggi nel codice"): il programma la evidenzia con un avviso rosso finché
  un agente non modifica il codice come deciso.
- Quando tutte le voci di uno strumento sono approvate, l'interruttore "Riproduci il foglio Excel originale"
  sparisce da quello strumento (resta nel codice come riferimento di regressione).

Stato del registro al 2026-09-22: 209 voci, tutte "da confermare".

## Scelte di calcolo da confermare
Capacità portante (fondazioni, `shared/capacita_portante`, usata da plinto isolato e muro di sostegno):
1. γR = 2,3 per il plinto (Tab. 6.4.I, approccio 2, R3).
2. γR = 1,4 statico e 1,2 sismico per il muro (Tab. 6.5.I e §7.11.6.2.1).
3. In condizioni sismiche si usa la formula statica dell'Annesso D dell'EC7 senza riduzione per l'inerzia del
   terreno (Paolucci-Pecker non applicato): il verdetto è segnato "da confermare".
4. Peso proprio del plinto fattorizzato con 1,35; la Tab. 6.2.I (A1) darebbe 1,3.
5. La verifica "a resistenza ammissibile" del foglio è ancora mostrata accanto alla nuova: decidere se tenerla.
6. Muro: la capacità portante sismica usa i parametri caratteristici del terreno (γM = 1, §7.11.1) mentre lo
   scorrimento sismico del foglio usa M2. È incoerente; voce di registro
   `muro-sostegno/capacita-portante-sismica-parametri-caratteristici`.

Sezione in c.a. a pressoflessione (`ca-sezione-dominio-mn`):
7. Esponente della verifica biassiale secondo EN 1992-1-1 §5.8.9(4).
8. Eccentricità minima e0 = max(h/30, 20 mm); Es = 210 000 MPa; N_max = fcd·(Ac − As) + fyd·As.
9. Sezioni a T, a L e pareti: le barre si inseriscono solo per tabella (nessun preset di armatura).

Travi in c.a. (`ca-trave-rettangolare`):
10. Nuovo ingresso V_g, taglio da carichi gravitazionali nella gerarchia delle resistenze (NTC 2018 §7.4.4.1.1).
    Il valore predefinito è 0 con un avviso: se dimenticato, la verifica è a favore di sicurezza mancata.

Plinti su pali (`fond-plinto-su-pali`):
11. β del punzonamento calcolato con i lati del pilastro e progetto a flessione su una striscia di 1 m: sono
    semplificazioni del foglio, tenute e documentate nel registro.

Punzonamento (`ca-punzonamento`):
12. β applicato al taglio lordo prima di dedurre la pressione del terreno: conservativo, segnalato nella relazione.

Comune ai moduli EC2 (`ec2-shared`):
13. Coefficiente di vRd,max: 0,4 (predefinito, EN 1992-1-1 A1:2014) oppure 0,5 (edizione 2004 e appendice
    nazionale). Voce `ec2-shared/coefficiente-vrd-max-scelta-ingegneristica`; ogni foglio in modalità Excel
    tiene il proprio.

Muro di sostegno (`muro-sostegno`), correzioni già applicate in modalità standard ma da confermare:
14. Esponenti del momento sul tallone (errore del foglio), armatura minima dei paramenti (§4.1.6.1.1, nuovo
    ingresso `tipo_cls`), scorrimento con φ' del terreno di fondazione quando il blocco drenato è compilato,
    clausola del ribaltamento §6.5.3.1.1.

Pilastri (`ca-pilastro-*`):
15. Snellezza sull'asse debole, tolto il limite del 4 % su As,min, clausole di dettaglio (§4.1.6.1.2 contro
    §7.4.6.2.2). Non implementati: rapporto di confinamento ωwd e classe di duttilità (l'ingresso manca).

Sisma (`sisma-spettro`) e mensole (`ca-mensola-tozza`):
16. Spettro di progetto sopra T_B senza η residuo (continuo in T_B); mensola P_R = min(P_Rs + 0,8·ΔP_R, P_Rc).

## Dubbi aperti su unità e riferimenti (voci `da_verificare` del registro)
- Vento: coefficiente cr con TR = 50 anni.
- Cedimenti: nel foglio "500" il rettangolo O' vale 40 m o 4 m?
- Cedimento edometrico: unità dell'affondamento D.

## Due riscritture volutamente NON fatte
Il muro potrebbe usare `shared/footing_pressure` e la mensola tozza `shared/ec2_strut_tie` (fase 7 della
roadmap). Cambierebbero i numeri rispetto ai fogli: è una decisione ingegneristica, non una pulizia del codice.

## Lavori rinviati in attesa del titolare
| Cosa | Cosa serve per partire |
|---|---|
| Verifica su Windows (`docs/VERIFICA_WINDOWS.md`) | un PC Windows dell'ufficio, mezz'ora |
| Verifica con MIDAS NX (`docs/VERIFICA_MIDAS.md`) | MIDAS Gen NX o Civil NX con un modello aperto |
| Repository GitHub privato con test automatici | un account GitHub; il file di configurazione è di 30 righe |
| Griglia di pericolosità sismica (ag, F0, T*C dalle coordinate) | una copia fidata dell'Allegato B delle NTC e 5 siti di controllo |
| Relazione in formato Word (DOCX) | dopo la relazione PDF, già disponibile via stampa del browser |
| MIDAS fase 2 (sollecitazioni degli elementi, non solo reazioni) | esito della verifica MIDAS |
| Cartiglio dello studio (logo, numerazione) | logo e campi che volete in relazione |
| Login e permessi | escluso dal committente: tutti vedono e modificano tutto |

## Scelte dell'interfaccia (specifica interfaccia §23-26)
Decise dal titolare il 2026-09-22 (restano qui come traccia; la specifica è già aggiornata):
17. Obiettivo di sfruttamento: **impostabile**. È un valore d'ufficio nella pagina "Impostazioni"
    (`docs/ui/WORKBENCH_SPEC.md` §26), valore di fabbrica 1,00, modificabile; la finestra "Dimensiona" lo propone e
    resta modificabile a ogni ricerca.
18. Passi di arrotondamento: **impostabili** nella pagina "Impostazioni", per tipo di dato (lunghezze in m, cm, mm,
    diametri di armatura, passi di armatura, copriferri, spessori, numeri interi) con eccezioni per singolo campo di
    uno strumento. Valori di fabbrica: tutti vuoti; il programma non inventa passi, li inserisce l'ufficio.
19. Verifiche senza rapporto numerico nella ricerca: **sì**, contano solo come "passa / non passa", senza
    obiettivo; il contratto `Check` non si modifica per questo.
20. "Provvisorio" nella relazione stampata: **no**. L'indicatore resta solo nella pagina del progetto (e nella
    finestra "Dimensiona"); la relazione del singolo strumento e quella di progetto non cambiano.
21. Una correzione del registro respinta rende l'elemento "provvisorio" come una da confermare: **sì**.
22. "Da ricalcolare" e "provvisorio" si propagano lungo la catena "Usa in…": **sì**. Va costruita con la regola
    di `docs/ui/WORKBENCH_SPEC.md` §25.1 (limite di profondità, protezione dai cicli, "provvisorio per origine").

23. Livello di gravità degli avvisi (per la colonna "avviso più grave" della tabella di progetto, §20): **no**
    (titolare, 2026-09-22). `shared/report.py` resta invariato; la tabella mostra il numero di avvisi e il primo.

Ancora aperta:
19-bis. L'obiettivo di sfruttamento < 1 vale anche per le verifiche di minimo o di dettaglio (armatura minima,
    passo, copriferro, rapporto massimo di armatura)? Risposta del titolare il 2026-09-22: "non so". Diventa
    un'**impostazione** della pagina "Impostazioni" (§26), **predefinita "no"**: con "no" l'obiettivo si applica
    alle verifiche "valore ≤ limite" e le verifiche di minimo ("valore ≥ limite", come As ≥ As,min) contano solo
    come passa/non passa; con "sì" si applica a tutte le verifiche con rapporto. Il programma non sa ancora
    distinguere una verifica di resistenza da un limite massimo di dettaglio (ρ ≤ ρmax): con "no" e obiettivo < 1
    la finestra "Dimensiona" segna quindi il risultato "da controllare". La voce resta aperta finché il titolare
    non sceglie un valore definitivo.
