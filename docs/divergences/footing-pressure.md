<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `footing-pressure`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| La pressione massima biassiale è la somma di due verifiche uniassiali, non quella esatta | La pressione massima combinata è calcolata come somma dei due massimi trapezoidali uniassiali (uno per x, uno per y) meno un termine di base, un'approssimazione non equivalente alla vera pressione biassiale sul piano rigido. | footing_pressure.pressure con metodo esatto calcola il piano di Navier lineare dentro il nocciolo biassiale e risolve il problema della pressione senza trazione fuori dal nocciolo (metodo di punto fisso 2D); il metodo per sovrapposizione riproduce esattamente la formula del foglio ed è quello forzato in modalità legacy. | NTC2018 §6.4.2.1 | nessuno sul caso guida (eccentricità piccole, ben dentro il nocciolo biassiale): i due metodi coincidono a 6 cifre significative (σt=1,66283 kg/cm²); i metodi divergono quando la risultante esce dal nocciolo in una o entrambe le direzioni | fond-plinto-isolato | riprodotta |

## Da verificare

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| Il fattore di conversione MPa -> kg/cm² usato per le colonne di pressione è un'approssimazione, non il valore esatto | Le colonne di pressione in kg/cm² moltiplicano per il letterale 10 invece del fattore esatto 98,0665 kPa per kgf/cm² (1 kgf/cm² ≈ 10,1972, non 10). | Questo modulo calcola sempre in kPa esatti; la conversione a kg/cm² con il fattore esatto o con il fattore approssimato del foglio è responsabilità dello strumento che lo consuma, a seconda della modalità. |  | ≈1,97% su qualunque pressione riportata in kg/cm² (es. σt,total 1,66283 kg/cm² con il fattore del foglio contro ≈1,6957 kg/cm² con il fattore esatto) | fond-plinto-isolato | riprodotta insieme a plinti-isolati/fattore-mpa-kgcm2-approssimato — shared.footing_pressure calcola sempre e solo in kPa esatti, senza parametro legacy_compat; la conversione a kg/cm² (e la scelta del fattore) è interamente a carico dello strumento consumatore, che la traccia con un proprio id di registro |
