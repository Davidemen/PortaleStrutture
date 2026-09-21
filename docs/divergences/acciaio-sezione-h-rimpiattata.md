<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `acciaio-sezione-h-rimpiattata`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| L'altezza libera dell'anima e' un valore fisso invece di dipendere dall'altezza del profilo | L'altezza libera dell'anima e' calcolata come 114 meno due volte lo spessore ala, con 114 scritto come valore fisso invece di riferirsi all'altezza del profilo in input: cambiando l'altezza del profilo, anima e piatti si scollegano geometricamente. | L'altezza dell'anima e' sempre h_profilo_mm meno due volte lo spessore ala, coerente con l'input reale. | Geometria della sezione | nessuno sul caso golden (H=114mm gia' pari al valore fisso); con H=200mm: Ix circa 613 cm4 (foglio, anima fantasma) vs 2020 cm4 (corretto) | acciaio-sezione-h-rimpiattata |
| Il baricentro dell'ala inferiore usa lo spessore del primo piatto invece del proprio | Il baricentro dell'ala inferiore usa meta' dello spessore del primo piatto come proxy di meta' dello spessore ala, invece dello spessore ala proprio: coincide con il valore corretto solo quando i due spessori sono uguali per coincidenza. | Il baricentro dell'ala inferiore usa meta' del proprio spessore ala. | Geometria della sezione | nessuno sul caso golden (spessori coincidenti, 8=8mm); con un piatto da 20mm: baricentro a 10mm (foglio) invece di 4mm (corretto) | acciaio-sezione-h-rimpiattata |
| Il baricentro verticale usa la coordinata x invece della y per l'ultimo elemento | Nel calcolo del baricentro pesato yN, l'ultimo termine (piatto A5) usa la coordinata x dell'elemento invece della sua y. | Ogni termine della somma usa la propria coordinata y. | Baricentro a media pesata | nessuno sul caso golden (area del piatto A5 nulla); con entrambi i piatti attivi: yN circa 27.45mm (foglio) vs 57.00mm (corretto) | acciaio-sezione-h-rimpiattata |

## Da verificare

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| I moduli plastici riportati non sono il vero modulo plastico per sezioni con piatti asimmetrici | Wpl,x e Wpl,y sono calcolati come somma di area per distanza dal baricentro ELASTICO, che coincide col vero modulo plastico (asse neutro plastico a pari-area) solo per una sezione doppiamente simmetrica senza piatti sull'asse forte; sull'asse debole risulta sempre 0 per un profilo senza piatti, ed e' errato con piatti asimmetrici. | In modalita' standard il modulo plastico e' calcolato dal vero asse neutro plastico a pari area (ricerca numerica); la modalita' foglio riproduce l'approssimazione del foglio. | Modulo plastico - definizione |  | acciaio-sezione-h-rimpiattata |
