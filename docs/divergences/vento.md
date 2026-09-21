<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `vento`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| L'etichetta del coefficiente di esposizione riporta un'unita' di misura errata | La cella etichetta ce(z) con l'unita' 'm', ma ce e' adimensionale | ce_h e il ce di ogni riga del profilo sono documentati con unita' '-' |  | nessuno (solo etichetta) | vento-pressione |
| Il profilo di pressione e' fisso a 1000 sezioni e non segue il parametro del foglio | La tabella del profilo e' scritta a mano per esattamente 1001 righe; l'ultima riga e' un valore letterale che non si aggiorna se si cambia il numero di sezioni | profilo_pressione genera esattamente n_sezioni+1 righe per qualsiasi n_sezioni, senza limite fisso |  | nessuno sul caso golden (n_sezioni=1000 riproduce la griglia del foglio); la divergenza riguarda solo numeri di sezioni diversi da 1000 | vento-pressione |
| La velocita' di riferimento e' rinormalizzata su TR=50 in modo incoerente con il coefficiente a_r esposto | vR(TR) viene ricalcolata dividendo per il fattore di Gumbel a TR=50, mentre il coefficiente a_r esposto in H14 resta quello non rinormalizzato, quindi a_r*vref non coincide con vr per TR diverso da 50 | vr = vref*a_r senza rinormalizzazione, coerente per costruzione con a_r esposto | NTC2018 §3.3.2 eq. 3.3.3 | TR=200, vref=25 m/s: foglio da' vr=26.88611 m/s (incoerente con a_r*vref=26.90584), corretto da' vr=26.90584 m/s; nessun impatto sul caso golden (TR=50) | vento-pressione |
| La zona di vento cerca la provincia nella colonna comune e fallisce spesso | VLOOKUP cerca la provincia risolta dentro la colonna Comune della tabella Comuni, un copia-incolla errato | La zona viene letta direttamente sul comune risolto |  | nessuno sul caso golden (Milano, comune omonimo della provincia); su 'Agrate Brianza' (provincia Monza e Brianza) il foglio fallisce, il modo corretto restituisce zona=1 | vento-pressione |

## Aggiornamenti normativi

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| La correzione di velocita' per l'altitudine usa la formula NTC2008 superata invece della NTC2018 | vb = vb0 + ka*(as-a0) con i valori ka [1/s] della Tab. 3.3.I pre-2018, senza limite superiore di quota | vb = vb0*ca secondo NTC2018 §3.3.2, con ks adimensionale (Tab. 3.3.I); oltre 1500 m viene sollevato un errore invece di estrapolare | NTC2018 §3.3.2 | zona 4, as=1500m: formula vecchia vb=48.00 m/s, formula NTC2018 vb=48.16 m/s (+0.33%); nessun impatto sul caso golden (as=120m < a0) | vento-pressione |
