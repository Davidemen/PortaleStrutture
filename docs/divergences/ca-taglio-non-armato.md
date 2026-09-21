<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `ca-taglio-non-armato`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| Il rapporto di armatura longitudinale ρl non è mai limitato al 2% | ρl = Asl/(bw·d), mai limitato | ρl limitato a 0,02 come richiesto da NTC2018 §4.1.2.3.5.1 | NTC2018 §4.1.2.3.5.1 | nessuno per il caso golden (ρl=0,00223); caso di verifica Asl=25000/bw=1500/d=560: ρl 0,02976 (foglio, non limitato) -> 0,02 (corretto), riduce VRd,1 | ca-taglio-non-armato |

## Aggiornamenti normativi

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| Nessun controllo di coerenza tra fck digitato liberamente e Rck nel foglio a striscia (v2) | il foglio v2 (a striscia da 1m) accetta fck come input libero, scollegato da Rck, senza alcun controllo incrociato | aggiunto un avviso in entrambe le modalità quando \|fck - 0,83·Rck\|/(0,83·Rck) > 5%; il calcolo di VRd resta invariato |  | nessuno per il caso golden (fck=32 vs Rck-derivato 33,2, entro tolleranza, nessun avviso) | ca-taglio-non-armato |
| La verifica del limite di armatura longitudinale confrontava il valore già limitato, mascherando i superamenti reali | n/a, riguarda solo la modalità standard: la verifica 'rapporto di armatura longitudinale entro il limite' confrontava il limite con il valore già limitato a 0,02, quindi non poteva mai fallire | la verifica confronta ora il valore grezzo (non limitato) con il limite di 0,02; se il limite interviene, viene aggiunto un avviso esplicito; il valore usato nella formula di VRd,1 resta quello limitato | NTC2018 §4.1.2.3.5.1 | nessuno per il caso golden e i casi oracolo (ρl ben sotto il limite in entrambi) | ca-taglio-non-armato |
