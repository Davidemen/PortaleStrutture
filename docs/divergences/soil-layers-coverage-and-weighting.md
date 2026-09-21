<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `soil-layers-coverage-and-weighting`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| La ricerca dello strato oltre l'ultima profondità coperta restituiva zero invece di segnalare un errore | La ricerca del modulo per una profondità oltre l'ultimo strato (o dentro un buco della stratigrafia) restituisce 0, che si traduce in un contributo di cedimento nullo silenzioso per quella fetta. | shared.soil_layers.layer_at solleva un errore che indica la profondità non coperta; in modalità legacy (usata dagli strumenti che devono riprodurre un caso cablato) restituisce None, trattato come contributo nullo, senza mai dividere per zero. |  | nessuno sui casi guida cablati (le tabelle degli strati coprono sempre profondità ben oltre la griglia di calcolo) | geo-cedimento-edometrico, geo-cedimento-elastico-newmark |
| Il modulo medio pesato su una profondità H sommava solo i primi 4 strati, ignorando quelli oltre e senza tagliarli a H | La somma pesata del modulo è sempre limitata ai primi 4 strati della tabella, mentre continua a dividere per l'intera altezza H; se la stratigrafia richiede un 5° strato dentro [0,H] (come nel caso guida del foglio), quella parte viene persa dal numeratore ma resta nel denominatore. | shared.soil_layers.weighted_modulus somma la sovrapposizione di ogni strato con [0,H], per un numero qualunque di strati, e segnala un errore se la tabella non copre l'intero intervallo. |  | caso guida della specifica: H11 foglio=138,8 kg/cmq (solo strati 1-2); calcolo corretto sugli stessi strati reali=166,8 kg/cmq (16,3559 MPa), +20,1% | geo-cedimento-elastico-timoshenko-goodier |
