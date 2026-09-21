<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `vento-cpe`

## Scelte ingegneristiche

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| Le etichette di classificazione tozzo/snello sono tutte maiuscole nel foglio | La cella B10 restituisce le stringhe interamente maiuscole 'EDIFICIO SNELLO' / 'EDIFICIO TOZZO' per i casi non misti (entrambe le direzioni snelle o entrambe tozze), e 'EDIFICIO SNELLO DIR 1' / 'EDIFICIO SNELLO DIR 2' per il caso misto per direzione | Le stesse stringhe sono riprodotte in stile frase ('Edificio snello' / 'Edificio tozzo' / 'Edificio snello, direzione 1' / 'Edificio snello, direzione 2'), per coerenza con le altre etichette di output del pacchetto |  | nessuno sul calcolo, cambia solo il testo del campo classification in tutti i casi | vento-cpe-rettangolare | riprodotta |

## Da verificare

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| L'etichetta di classificazione per il caso misto per direzione non e' scritta nella specifica originale | La cella genera le stringhe 'EDIFICIO SNELLO DIR 1' / 'EDIFICIO SNELLO DIR 2' per il caso misto per direzione, lette direttamente dalla formula del foglio | La riscrittura maiuscolo/stile frase di vento-cpe/etichetta-classificazione-maiuscolo copre anche queste due stringhe; non esiste una divergenza numerica separata per il caso misto |  | nessuno oltre a quanto gia' descritto in vento-cpe/etichetta-classificazione-maiuscolo; solo il testo non era presente letteralmente nella specifica | vento-cpe-rettangolare | riprodotta insieme a vento-cpe/etichetta-classificazione-maiuscolo — Il ramo e' condiviso con vento-cpe/etichetta-classificazione-maiuscolo: un'unica chiamata legacy() in classify() governa tutte e quattro le stringhe di B10, incluso il caso misto. |
