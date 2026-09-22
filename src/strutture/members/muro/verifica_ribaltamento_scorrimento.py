"""Assembles Tool 2 (`RibaltamentoScorrimentoCombo`) for one combination — split out of
`tool.py`, regola dura 12 dei moduli piccoli.
"""
from strutture.shared.report import Check

from .models import GeometriaResult, MuroSostegnoInput, NomeCombo, RibaltamentoScorrimentoCombo, SpintaCombo
from .ribaltamento_scorrimento_valori import valori_ribaltamento_scorrimento

CLAUSE_RIBALTAMENTO = "NTC2018 §6.5.3.1.1"  # SLU of gravity walls (§6.5.3.1.2 is the embedded-walls sub-clause)
CLAUSE_SCORRIMENTO = "NTC2018 §6.5.3.1.1 / EC7 §6.5.4"


def nome_combo_leggibile(nome: NomeCombo) -> str:
    """Nome del check, leggibile anche se l'interfaccia tronca il testo: le combinazioni sismiche
    SISMA_1/SISMA_2 differiscono solo nell'ultimo carattere (il segno di kv), che un'interfaccia che
    tronca a larghezza fissa può nascondere — il segno è quindi richiamato esplicitamente."""
    if nome == "SISMA_1":
        return f"{nome} (+kv)"
    if nome == "SISMA_2":
        return f"{nome} (−kv)"
    return nome


def ribaltamento_scorrimento_combo(spinta: SpintaCombo, *, inputs: MuroSostegnoInput, geometria: GeometriaResult) -> RibaltamentoScorrimentoCombo:
    v = valori_ribaltamento_scorrimento(spinta, inputs=inputs, geometria=geometria)
    return RibaltamentoScorrimentoCombo(
        phi_scorrimento_rad=v.phi_scorrimento_rad,
        nome=spinta.nome,
        dq_kN_m2=v.dq_kN_m2,
        sh_q_kN=v.sh_q_kN,
        sh_terr_kN=v.sh_terr_kN,
        sv_q_kN=v.sv_q_kN,
        sv_terr_kN=v.sv_terr_kN,
        braccio_terr_m=v.braccio_terr_m,
        fh_kN=v.fh_kN,
        m_fh_kNm=v.m_fh_kNm,
        m_rib_kNm=v.m_rib_kNm,
        m_stab_kNm=v.m_stab_kNm,
        n_tot_kN=v.n_tot_kN,
        r_tot_kN=v.r_tot_kN,
        or_ribaltamento=v.or_ribaltamento,
        os_scorrimento=v.os_scorrimento,
        verifica_ribaltamento=Check(
            name=f"Ribaltamento {nome_combo_leggibile(spinta.nome)}",
            passed=v.or_ribaltamento >= v.soglia_rib,
            detail=f"OR={v.or_ribaltamento:.3f} (soglia γR={v.soglia_rib:.2f})",
            clause=CLAUSE_RIBALTAMENTO,
            value=v.or_ribaltamento,
            limit=v.soglia_rib,
            unit="-",
        ),
        verifica_scorrimento=Check(
            name=f"Scorrimento {nome_combo_leggibile(spinta.nome)}",
            passed=v.os_scorrimento >= v.soglia_scorr,
            detail=f"OS={v.os_scorrimento:.3f} (soglia γR={v.soglia_scorr:.2f})",
            clause=CLAUSE_SCORRIMENTO,
            value=v.os_scorrimento,
            limit=v.soglia_scorr,
            unit="-",
        ),
    )
