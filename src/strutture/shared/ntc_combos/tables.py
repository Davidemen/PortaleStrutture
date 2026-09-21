"""NTC 2018 Tab. 6.2.I / 6.2.II / 6.5.I — typed immutable partial-factor tables (§6.2.1, §6.5.3.1.1)."""
from .models import (
    ApproccioAzioni,
    ApproccioGeotecnico,
    FattoriAzioni,
    FattoriGeotecnici,
    FattoriResistenza,
    VerificaOpereDiSostegno,
)

# Tab. 6.2.I — coefficienti parziali per le azioni.
FATTORI_AZIONI: tuple[tuple[ApproccioAzioni, FattoriAzioni], ...] = (
    ("EQU", FattoriAzioni(
        gamma_g1_favorevole=0.9, gamma_g1_sfavorevole=1.1,
        gamma_g2_favorevole=0.8, gamma_g2_sfavorevole=1.5,
        gamma_q_favorevole=0.0, gamma_q_sfavorevole=1.5,
    )),
    ("A1", FattoriAzioni(
        gamma_g1_favorevole=1.0, gamma_g1_sfavorevole=1.3,
        gamma_g2_favorevole=0.8, gamma_g2_sfavorevole=1.5,
        gamma_q_favorevole=0.0, gamma_q_sfavorevole=1.5,
    )),
    ("A2", FattoriAzioni(
        gamma_g1_favorevole=1.0, gamma_g1_sfavorevole=1.0,
        gamma_g2_favorevole=0.8, gamma_g2_sfavorevole=1.3,
        gamma_q_favorevole=0.0, gamma_q_sfavorevole=1.3,
    )),
)

# Tab. 6.2.II — coefficienti parziali per i parametri geotecnici.
FATTORI_GEOTECNICI: tuple[tuple[ApproccioGeotecnico, FattoriGeotecnici], ...] = (
    ("M1", FattoriGeotecnici(gamma_tan_phi=1.0, gamma_c=1.0, gamma_cu=1.0, gamma_gamma=1.0)),
    ("M2", FattoriGeotecnici(gamma_tan_phi=1.25, gamma_c=1.25, gamma_cu=1.4, gamma_gamma=1.0)),
)

# Tab. 6.5.I — coefficienti parziali γR per le verifiche di sicurezza delle opere di sostegno (muri).
FATTORI_RESISTENZA: tuple[tuple[VerificaOpereDiSostegno, FattoriResistenza], ...] = (
    ("capacita_portante", FattoriResistenza(r1=1.0, r2=1.0, r3=1.4)),
    ("scorrimento", FattoriResistenza(r1=1.0, r2=1.0, r3=1.1)),
    ("resistenza_terreno_a_valle", FattoriResistenza(r1=1.0, r2=1.0, r3=1.4)),
    ("ribaltamento", FattoriResistenza(r1=1.0, r2=1.15, r3=1.15)),
)
