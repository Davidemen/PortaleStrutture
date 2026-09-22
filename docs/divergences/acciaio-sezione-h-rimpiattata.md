<!-- FILE GENERATO — non modificare a mano. Origine: src/strutture/data/divergences/*.json, prodotto da `python -m strutture.shared.divergences.render`. -->

# Correzioni — `acciaio-sezione-h-rimpiattata`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| L'altezza libera dell'anima e' un valore fisso invece di dipendere dall'altezza del profilo | L'altezza libera dell'anima e' calcolata come 114 meno due volte lo spessore ala, con 114 scritto come valore fisso invece di riferirsi all'altezza del profilo in input: cambiando l'altezza del profilo, anima e piatti si scollegano geometricamente. | L'altezza dell'anima e' sempre h_profilo_mm meno due volte lo spessore ala, coerente con l'input reale. | Geometria della sezione | nessuno sul caso golden (H=114mm gia' pari al valore fisso); con H=200mm: Ix circa 613 cm4 (foglio, anima fantasma) vs 2020 cm4 (corretto) | acciaio-sezione-h-rimpiattata | riprodotta |
| Il baricentro dell'ala inferiore usa lo spessore del primo piatto invece del proprio | Il baricentro dell'ala inferiore usa meta' dello spessore del primo piatto come proxy di meta' dello spessore ala, invece dello spessore ala proprio: coincide con il valore corretto solo quando i due spessori sono uguali per coincidenza. | Il baricentro dell'ala inferiore usa meta' del proprio spessore ala. | Geometria della sezione | nessuno sul caso golden (spessori coincidenti, 8=8mm); con un piatto da 20mm: baricentro a 10mm (foglio) invece di 4mm (corretto) | acciaio-sezione-h-rimpiattata | riprodotta |
| Il baricentro verticale usa la coordinata x invece della y per l'ultimo elemento | Nel calcolo del baricentro pesato yN, l'ultimo termine (piatto A5) usa la coordinata x dell'elemento invece della sua y. | Ogni termine della somma usa la propria coordinata y. | Baricentro a media pesata | nessuno sul caso golden (area del piatto A5 nulla); con entrambi i piatti attivi: yN circa 27.45mm (foglio) vs 57.00mm (corretto) | acciaio-sezione-h-rimpiattata | riprodotta |
| Lo scostamento orizzontale del secondo piatto rispecchia il primo invece di usare la propria larghezza | Lo scostamento orizzontale del piatto 2 (E10=-E9) rispecchia letteralmente quello del piatto 1, usando la larghezza del piatto 1 anche per posizionare il piatto 2, invece della propria. | Ogni piatto usa la propria larghezza per calcolare il proprio scostamento orizzontale dal profilo. | Geometria della sezione | nessuno sul caso golden (i due piatti hanno la stessa larghezza, 8mm); con piatti di larghezza diversa: lo scostamento del piatto 2 risulta quello del piatto 1 anziche' il proprio | acciaio-sezione-h-rimpiattata | riprodotta |

## Scelte ingegneristiche

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| In modalita' foglio il numero di piatti e' limitato alle due righe fisiche del foglio | Il foglio dispone di sole due righe fisiche per i piatti di rinforzo (A4/A5): non e' possibile modellare piu' di due piatti. | La modalita' standard generalizza a una tabella di piatti fino a 10 righe indipendenti; la modalita' foglio (legacy_compat=True) rifiuta piu' di due piatti con un errore esplicito invece di ignorare silenziosamente quelli in eccesso. |  | nessuno sul caso golden (2 piatti); con piu' di due piatti in modalita' foglio: errore esplicito invece di un calcolo indefinito | acciaio-sezione-h-rimpiattata | riprodotta |

## Da verificare

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| I moduli plastici riportati non sono il vero modulo plastico per sezioni con piatti asimmetrici | Wpl,x e Wpl,y sono calcolati come somma di area per distanza dal baricentro ELASTICO, che coincide col vero modulo plastico (asse neutro plastico a pari-area) solo per una sezione doppiamente simmetrica senza piatti sull'asse forte; sull'asse debole risulta sempre 0 per un profilo senza piatti, ed e' errato con piatti asimmetrici. | In modalita' standard il modulo plastico e' calcolato dal vero asse neutro plastico a pari area (ricerca numerica); la modalita' foglio riproduce l'approssimazione del foglio. | Modulo plastico - definizione |  | acciaio-sezione-h-rimpiattata | riprodotta |
