# Istruzioni per gli agenti di sviluppo

Le istruzioni complete sono in `CLAUDE.md` alla radice del progetto e valgono per qualsiasi assistente
(Claude Code, Codex, Cursor, ecc.). Leggerlo per intero prima di toccare un file.

Regole irrinunciabili, in breve:
1. Si comunica in italiano con il titolare. Interfaccia, messaggi, registro e documentazione rivolta a lui: in italiano.
2. Mai fermare un processo per nome (`pkill`, `killall`, `taskkill /IM`): si ferma solo il PID che si è avviato.
   Il server dell'ufficio gira sulla porta 8000 e va riavviato solo dopo averlo detto al titolare.
3. Una modifica ai calcoli non è finita finché `uv run pytest -q`, il controllo del registro
   (`uv run python -m strutture.shared.divergences.check --strict`) e `uv run ruff check .` non sono puliti;
   una modifica all'interfaccia non è finita finché `uv run pytest tests/e2e -m e2e -q` non è verde.
4. Le decisioni ingegneristiche (coefficienti, clausole, ipotesi di calcolo) non si prendono da soli:
   si segnalano nel registro delle correzioni e si chiede al titolare (`docs/DECISIONI_DA_CONFERMARE.md`).
5. Non si committano i fogli Excel, la cartella `var/`, file `.env` o chiavi. Le chiavi MIDAS restano in variabili
   d'ambiente o nella sessione del browser.
6. Un pacchetto di lavoro finito = un commit locale, messaggio in stile `tipo: descrizione`.
