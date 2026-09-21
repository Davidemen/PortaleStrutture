<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `shared-ca`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| Alcune combinazioni della tabella classe di apertura fessura sono vuote nel foglio | tre combinazioni (aggressive/quasi permanente/sensibile; molto aggressive/frequente/sensibile; molto aggressive/quasi permanente/sensibile) sono celle vuote, lette come 0 | restituisce esplicitamente 'nessun limite di apertura' (richiede verifica di decompressione) per queste tre combinazioni, invece di un valore fittizio | NTC2018 Tab. 4.1.IV | nessuno sui casi golden (tutti usano condizioni ordinarie/poco sensibile) |  |
| La tabella diametro-vs-tensione limite (Tab. C4.1.II) usa solo la ricerca esatta, senza interpolazione | ricerca a corrispondenza esatta del diametro; un diametro non tabulato genera un errore | interpolazione lineare tra i due diametri tabellati più vicini | NTC2018 Tab. C4.1.II | nessuno sul caso golden di ca-travi (Ø=20mm è un valore esatto in tabella, σs,limite=240 MPa in entrambe le modalità) |  |
| La tabella tensione-vs-interferro delle barre era invertita e mancava della classe di apertura fessura | n/a, riguarda un modulo di libreria condiviso (non legato a una cella specifica di ca-travi/ca-mensole/ca-pilastri): la tabella era indicizzata tensione->interferro massimo (la direzione della norma), ma veniva consultata come se fosse interferro->tensione, restituendo valori sbagliati e senza gestire la classe di apertura fessura | la tabella è ora indicizzata correttamente interferro->tensione massima, con una colonna per ciascuna classe di apertura fessura (w1/w2/w3), invertita da Tab. C4.1.III/Table 7.3N | NTC2018 Tab. C4.1.III / EN1992-1-1 Table 7.3N | nessun caso golden/oracolo chiama questa funzione; solo test unitari |  |

## Aggiornamenti normativi

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| Asse neutro sezione fessurata generalizzato al caso con armatura compressa, oltre alla semplice del foglio | il foglio calcola solo il caso a semplice armatura (As2=0) | formula generalizzata a sezione rettangolare con armatura compressa; con As2=0 si riduce esattamente alla formula del foglio |  | nessuno, il caso As2=0 riproduce esattamente y=126,44mm del foglio | ca-trave-rettangolare |
