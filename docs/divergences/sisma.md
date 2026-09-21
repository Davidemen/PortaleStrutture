<!-- GENERATED FILE — do not edit by hand. Source: src/strutture/data/divergences/*.json, rendered by `python -m strutture.shared.divergences.render`. -->

# Divergences — `sisma`

## Errori del foglio

| titolo | foglio | corretto | clausola | impatto | strumenti |
|---|---|---|---|---|---|
| Il coefficiente eta di smorzamento non ha un limite inferiore per xi alti | eta = sqrt(10/(5+xi)) senza alcun limite inferiore; xi e' validato solo come maggiore di zero | eta = max(sqrt(10/(5+xi)), 0.55), applicato in entrambe le modalita' perche' e' un limite della formula stessa, non del foglio | NTC2018 §3.2.3.2.1 eq. 3.2.6 | a xi=40%: eta senza limite = 0.4714, eta con limite = 0.55 (+16.7%, conservativo); caso golden (xi=5) non e' interessato | sisma-fattori-struttura |
| Il coefficiente dissipativo verticale e' calcolato come 1/qv invece che dallo smorzamento | eta,v = 1/qv, non dipende dallo smorzamento nonostante l'etichetta 'coefficiente dissipativo' | Stessa formula eta(xi) della componente orizzontale: eta,v = sqrt(10/(5+xi)) | NTC2018 §7.3.3.2 | caso golden (xi=5, qv=1.5): foglio da' eta,v=0.666667, corretto da' eta,v=1 | sisma-fattori-struttura |
| Lo spettro elastico non torna esattamente ad ag*S a T=0 quando lo smorzamento non e' 5% | Il termine reciproco perde il fattore eta, quindi Se(0) = eta*ag*S invece del valore di ancoraggio ag*S | Se(T) = eta*ag*S*F0*[T/TB + 1/(eta*F0)*(1-T/TB)], che si riduce ad ag*S a T=0 per qualsiasi eta | NTC2018 §3.2.3.2.1 eq. 3.2.4 | per xi=10% (eta=0.8165): foglio da' Se(0)=0.8165*ag*S (18% in meno), corretto da' Se(0)=ag*S esatto; caso golden (xi=5) non e' interessato | sisma-spettro |
| Lo spettro di progetto puo' scendere sotto 0.2ag per periodi lunghi | Il ramo 1/T^2 (T>=TD) puo' decadere sotto 0.2*ag per T grandi, senza limite inferiore | Sd(T) = max(Se(T)/q, 0.2*ag) per gli stati limite ultimi (SLV/SLC) | NTC2018 §3.2.3.2.1 | caso golden a T=5s: foglio da' Sd=0.00590732g, corretto da' Sd=0.0196g (+3.3x) | sisma-spettro |
