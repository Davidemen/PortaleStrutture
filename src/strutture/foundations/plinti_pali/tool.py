"""Tool registration: `fond-plinto-su-pali` — one composed tool verifying one pile cap type by
strut-and-tie against a table of column reactions per load combination (docs/architecture-batch2.md
§1 `foundations/plinti_pali`). `run()` composes, in order: inviluppo -> flessione ->
puntoni/tiranti -> taglio/punzonamento (docs/specs/fond-plinti-pali.md Tools 1-4)."""
import logging

from strutture.shared.load_table import governing
from strutture.shared.pile_group import pile_coordinates
from strutture.shared.report import CalcError, Check, Report, success
from strutture.shared.sketch import Sketch
from strutture.shared.tool import Tool

from .capacita_pali import capacita_compressione, capacita_trazione
from .flessione import flessione
from .input import PlintoSuPaliInput
from .inviluppo import inviluppo, inviluppo_righe
from .materiali import materiali
from .models import PlintoSuPaliOutput
from .pesi_propri import peso_proprio_kN as calcola_peso_proprio
from .puntoni_tiranti import puntoni_tiranti
from .rows import RigaCarico, riga_carico
from .schema import grid_counts, numero_pali
from .schizzo import disegna as disegna_schizzo
from .taglio_punzonamento import punzonamento_colonna, punzonamento_palo, taglio

logger = logging.getLogger(__name__)

ESEMPIO = {
    "schema_pali": "2x2", "lx_m": 2.0, "ly_m": 2.0,
    "ax_m": 4.0, "by_m": 4.0, "h_plinto_m": 1.2, "copriferro_cm": 5.0,
    "bx_pilastro_m": 0.7, "by_pilastro_m": 0.7,
    "diametro_pila_mm": 600.0, "resistenza_pila_compressione_kN": 1000.0,
    "classe_calcestruzzo": "C32/40", "grado_acciaio": "B450C", "gamma_s": 1.15, "gamma_c": 1.5,
    "diametro_tirante_xy_mm": 32.0, "n_tirante_xy": 2, "diametro_tirante_x_mm": 24.0, "n_tirante_x": 8,
    "diametro_tirante_y_mm": 24.0, "n_tirante_y": 8,
    "reazioni": [
        {"nodo": 18000, "combo": "SLU1", "fx_kN": 0.0, "fy_kN": 0.0, "fz_kN": 847.1593, "mx_kNm": 0.0, "my_kNm": 0.0, "mz_kNm": 0.0},
        {"nodo": 18000, "combo": "SLU4", "fx_kN": -15.9477, "fy_kN": -0.93033, "fz_kN": 1899.9593, "mx_kNm": 9.91203, "my_kNm": -169.805, "mz_kNm": 2.7315},
        {"nodo": 18000, "combo": "SLV_10", "fx_kN": 69.6333, "fy_kN": -22.6831, "fz_kN": 1315.66, "mx_kNm": 241.562, "my_kNm": 741.541, "mz_kNm": 22.9383},
        {"nodo": 18000, "combo": "SLU_EQU4", "fx_kN": 0.0, "fy_kN": 34.3663, "fz_kN": 1184.09, "mx_kNm": -365.987, "my_kNm": 0.0, "mz_kNm": 12.69},
    ],
}


def run(inputs: PlintoSuPaliInput) -> Report[PlintoSuPaliOutput]:
    """Compose the per-row per-pile demand, the envelope, and the flexural/strut-tie/shear design."""
    count_x, count_y = grid_counts(inputs.schema_pali)
    n_pali = numero_pali(inputs.schema_pali)
    piles = pile_coordinates(inputs.schema_pali, inputs.lx_m, inputs.ly_m)

    righe: tuple[RigaCarico, ...] = tuple(
        riga_carico(row, piles, count_x, count_y, inputs.lx_m, inputs.ly_m, inputs.h_plinto_m,
                    inputs.ex_m, inputs.ey_m, legacy_compat=inputs.legacy_compat)
        for row in inputs.reazioni
    )
    peso_kN = calcola_peso_proprio(inputs.ax_m, inputs.by_m, inputs.h_plinto_m, inputs.gamma_g1,
                                    inputs.carico_aggiuntivo_kN)
    env = inviluppo(righe, peso_kN, n_pali, inputs.gamma_g1, legacy_compat=inputs.legacy_compat)
    inviluppo_result = inviluppo_righe(env)

    governante_env = governing(righe, lambda r: r.n_max_pila_kN, "max")  # type: ignore[arg-type]
    if governante_env is None:
        raise CalcError("la tabella reazioni non puo' essere vuota")
    governante = righe[governante_env.indice]

    materiali_result = materiali(inputs.classe_calcestruzzo, inputs.grado_acciaio, inputs.gamma_s)
    fyd_MPa = materiali_result.acciaio.fyd_MPa
    fck_MPa = materiali_result.calcestruzzo.fck_MPa

    flessione_result = flessione(
        righe, env, count_x, count_y, inputs.lx_m, inputs.ly_m, inputs.h_plinto_m, peso_kN,
        inputs.copriferro_cm * 10.0,
        inputs.diametro_inf_x_mm, inputs.diametro_inf_y_mm, inputs.passo_inf_x_mm, inputs.passo_inf_y_mm,
        inputs.diametro_sup_x_mm, inputs.diametro_sup_y_mm, inputs.passo_sup_x_mm, inputs.passo_sup_y_mm,
        fyd_MPa, fck_MPa, inputs.gamma_c, legacy_compat=inputs.legacy_compat,
    )

    puntoni_tiranti_result = puntoni_tiranti(
        count_x, count_y, inputs.lx_m, inputs.ly_m, inputs.h_plinto_m, inputs.copriferro_cm * 10.0,
        inputs.diametro_inf_x_mm, inputs.diametro_inf_y_mm, inputs.diametro_pila_mm,
        inputs.diametro_tirante_xy_mm, inputs.diametro_tirante_x_mm, inputs.diametro_tirante_y_mm,
        inputs.n_tirante_xy, inputs.n_tirante_x, inputs.n_tirante_y,
        env.n_max_env_kN, inputs.bx_pilastro_m * 1000.0, inputs.by_pilastro_m * 1000.0,
        fck_MPa, inputs.gamma_c, fyd_MPa, legacy_compat=inputs.legacy_compat,
    )

    taglio_result = taglio(
        env.n_totale_max.valore, peso_kN, inputs.ax_m * 1000.0, inputs.h_plinto_m * 1000.0,
        inputs.copriferro_cm * 10.0, inputs.diametro_long_assunto_mm, inputs.av_mm,
        flessione_result.inf_x.as_prov_mm2, fck_MPa, inputs.gamma_c, legacy_compat=inputs.legacy_compat,
        coeff_vrd_max=inputs.coeff_vrd_max,
    )
    nsd_kN = env.n_totale_max.valore + peso_kN
    riga_governante_colonna = righe[env.n_totale_max.indice]
    punzonamento_result = punzonamento_colonna(
        nsd_kN, riga_governante_colonna.mx_finale_kNm, riga_governante_colonna.my_finale_kNm,
        taglio_result.d_mm, inputs.bx_pilastro_m * 1000.0, inputs.by_pilastro_m * 1000.0,
        inputs.lx_m, inputs.ly_m, inputs.diametro_pila_mm, fck_MPa, inputs.gamma_c,
        legacy_compat=inputs.legacy_compat, coeff_vrd_max=inputs.coeff_vrd_max,
    )
    punzonamento_palo_result = punzonamento_palo(
        env.n_max_env_kN, taglio_result.d_mm, inputs.diametro_pila_mm, taglio_result.rho, taglio_result.k,
        fck_MPa, inputs.gamma_c, lx_m=inputs.lx_m, ly_m=inputs.ly_m, ax_m=inputs.ax_m, by_m=inputs.by_m,
        count_x=count_x, count_y=count_y, legacy_compat=inputs.legacy_compat,
    )

    capacita_compressione_result = capacita_compressione(env.n_max_env_kN, inputs.resistenza_pila_compressione_kN)
    capacita_trazione_result = None
    if env.n_min_env_kN < 0:
        if inputs.resistenza_pila_trazione_kN is None:
            raise CalcError("un palo risulta teso (Nmin < 0): specificare resistenza_pila_trazione_kN")
        capacita_trazione_result = capacita_trazione(env.n_min_env_kN, inputs.resistenza_pila_trazione_kN)

    checks = _checks(puntoni_tiranti_result, taglio_result, punzonamento_result, punzonamento_palo_result,
                      capacita_compressione_result, capacita_trazione_result, flessione_result)
    warnings = _warnings(inputs, count_x, count_y, env)

    utilizzo_st = max(
        puntoni_tiranti_result.puntone.utilizzo,
        *(t.utilizzo for t in (puntoni_tiranti_result.tirante_xy, puntoni_tiranti_result.tirante_x,
                                puntoni_tiranti_result.tirante_y) if t is not None),
    )
    utilizzo_v = max(taglio_result.utilizzo, punzonamento_result.utilizzo, punzonamento_palo_result.utilizzo)

    schizzo: Sketch | None
    try:
        schizzo = disegna_schizzo(inputs, piles, puntoni_tiranti_result, env.n_max_env_kN)
    except Exception:
        logger.exception("errore nel disegno dello schizzo per fond-plinto-su-pali")
        schizzo = None

    data = PlintoSuPaliOutput(
        materiali=materiali_result, righe=righe, inviluppo=inviluppo_result, governante=governante,
        flessione=flessione_result, puntoni_tiranti=puntoni_tiranti_result, taglio=taglio_result,
        punzonamento=punzonamento_result, punzonamento_palo=punzonamento_palo_result,
        capacita_compressione=capacita_compressione_result, capacita_trazione=capacita_trazione_result,
        n_max_pila_kN=env.n_max_env_kN, utilizzo_puntoni_tiranti=utilizzo_st, utilizzo_taglio_punzonamento=utilizzo_v,
        schizzo=schizzo,
    )
    return success(data, inputs, checks=checks, warnings=warnings)


def _checks(pt, taglio_result, punzonamento_result, punzonamento_palo_result, capacita_c, capacita_t, flessione_result) -> tuple[Check, ...]:
    checks = (
        Check(name="Puntone", passed=pt.puntone.verificato, clause="EC2 §6.5.2/§6.5.4",
              value=pt.puntone.fus_kN, limit=pt.puntone.fns_kN, unit="kN"),
        Check(name="Taglio", passed=taglio_result.verificato, clause="EC2 §6.2.2",
              value=taglio_result.ved_ridotto_kN, limit=taglio_result.vrd_c_kN, unit="kN"),
        Check(name="Schiacciamento del calcestruzzo al filo (taglio)", passed=taglio_result.ved_kN <= taglio_result.ved_max_kN,
              clause="EC2 eq. 6.5", value=taglio_result.ved_kN, limit=taglio_result.ved_max_kN, unit="kN"),
        Check(name="Punzonamento al filo pilastro", passed=punzonamento_result.verificato, clause="EC2 §6.4.5/§6.4.3",
              value=punzonamento_result.ved_kN, limit=punzonamento_result.vrd_max_kN, unit="kN"),
        Check(name="Punzonamento del palo d'angolo", passed=punzonamento_palo_result.verificato, clause="EC2 §6.4.2",
              value=punzonamento_palo_result.ved_kN, limit=punzonamento_palo_result.vrd_c_kN, unit="kN"),
        Check(name="Capacità portante del palo (compressione)", passed=capacita_c.verificato, clause="Geotecnica",
              value=capacita_c.domanda_kN, limit=capacita_c.resistenza_kN, unit="kN"),
        Check(name="Armatura inferiore X-X", passed=flessione_result.inf_x.verificato, clause="EC2 §9.3.1.1",
              value=flessione_result.inf_x.as_req_mm2, limit=flessione_result.inf_x.as_prov_mm2, unit="mm2/m"),
        Check(name="Armatura inferiore Y-Y", passed=flessione_result.inf_y.verificato, clause="EC2 §9.3.1.1",
              value=flessione_result.inf_y.as_req_mm2, limit=flessione_result.inf_y.as_prov_mm2, unit="mm2/m"),
    )
    for nome, tirante in (("Tirante XY", pt.tirante_xy), ("Tirante X", pt.tirante_x), ("Tirante Y", pt.tirante_y)):
        if tirante is not None:
            checks = (*checks, Check(name=nome, passed=tirante.verificato, clause="EC2 §6.5.3/§9.8.1",
                                      value=tirante.fut_kN, limit=tirante.fnt_kN, unit="kN"))
    if capacita_t is not None:
        checks = (*checks, Check(name="Capacità portante del palo (trazione)", passed=capacita_t.verificato,
                                  clause="Geotecnica", value=capacita_t.domanda_kN, limit=capacita_t.resistenza_kN, unit="kN"))
    return checks


MOMENTO_NON_RESISTITO_TOLLERANZA_KNM = 1.0  # below this, a moment is treated as numerical noise.


def _warnings(inputs: PlintoSuPaliInput, count_x: int, count_y: int, env) -> tuple[str, ...]:
    """`av` should be close to `Ø_palo/5` (docs/architecture-batch2.md §7 `plinti-pali AR97`); the
    sheet's own default is a disconnected literal, so a mismatch is only flagged, never rejected.

    Also flags a moment about an axis whose pile grid has zero second moment (every pile on that
    axis, e.g. Mx on a "2x1" schema): `shared.pile_group.rigid_cap_axial` correctly drops that term
    (a rigid cap cannot resist it by differential pile axial force alone), but silently — the cap
    would need pile-head fixity or a second pile line to carry it (code-review finding,
    `shared/pile_group/reactions.py`)."""
    avvisi: list[str] = []
    av_atteso_mm = inputs.diametro_pila_mm / 5.0
    if abs(inputs.av_mm - av_atteso_mm) > 0.01 * av_atteso_mm:
        avvisi.append(f"av={inputs.av_mm:.1f} mm si discosta dal valore Ø_palo/5={av_atteso_mm:.1f} mm normalmente assunto")
    if count_y == 1 and max(abs(env.mx_max.valore), abs(env.mx_min.valore)) > MOMENTO_NON_RESISTITO_TOLLERANZA_KNM:
        avvisi.append(
            "Mx applicato su uno schema pali senza sviluppo lungo Y: il momento non e' resistito da "
            "reazioni assiali differenziali sui pali (richiede incastro in testa palo o una seconda fila di pali)",
        )
    if count_x == 1 and max(abs(env.my_max.valore), abs(env.my_min.valore)) > MOMENTO_NON_RESISTITO_TOLLERANZA_KNM:
        avvisi.append(
            "My applicato su uno schema pali senza sviluppo lungo X: il momento non e' resistito da "
            "reazioni assiali differenziali sui pali (richiede incastro in testa palo o una seconda fila di pali)",
        )
    return tuple(avvisi)


TOOLS = (
    Tool(
        name="fond-plinto-su-pali",
        title="Verifica plinto su pali (puntoni e tiranti)",
        group="Fondazioni / Plinti",
        norm="EC2 §6.5 (puntoni e tiranti) / §9.8.1 (plinti su pali) / §6.4 (punzonamento) / §6.2.2 (taglio)",
        input_model=PlintoSuPaliInput,
        output_model=PlintoSuPaliOutput,
        run=run,
        example=ESEMPIO,
        summary="Verifica il plinto su pali a puntoni e tiranti, con taglio, punzonamento e capacità portante dei pali.",
        live=False,
    ),
)
