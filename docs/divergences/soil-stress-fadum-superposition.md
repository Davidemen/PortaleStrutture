<!-- FILE GENERATO — non modificare a mano. Origine: src/strutture/data/divergences/*.json, prodotto da `python -m strutture.shared.divergences.render`. -->

# Correzioni — `soil-stress-fadum-superposition`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti | modalità Excel |
|---|---|---|---|---|---|---|
| La sovrapposizione di Fadum per il punto generico accoppia due segmenti dello stesso lato invece di un segmento per lato | I due blocchi di calcolo accoppiano due segmenti dello stesso lato del rettangolo (invece di un segmento per ciascuno dei due lati), il che non è un rettangolo d'angolo valido per la sovrapposizione di Newmark quando il punto non è centrato. | shared.soil_stress.under_point costruisce ognuno dei 4 sotto-rettangoli accoppiando sempre uno split in x con uno split in y, mai due segmenti dello stesso lato; verificato per confronto indipendente con un'integrazione numerica diretta di Boussinesq (punto interno ed esterno). | sovrapposizione classica a 4 rettangoli di Newmark/Fadum (Poulos & Davis) | nessuno sui casi guida 500/400/350 (punto sempre centrato, le due formule coincidono); per un punto non centrato le due formule danno risultati diversi | geo-cedimento-elastico-newmark | riprodotta insieme a geo-cedimenti-elastico/punto-o-accoppiamento-lati-errato — shared.soil_stress.under_point non ha parametro legacy_compat: costruisce sempre i 4 sotto-rettangoli nel modo corretto; il vecchio accoppiamento errato, se riprodotto, è responsabilità dello strumento consumatore con un proprio id di registro |
