"""M-N / Mx-My domains and M_Rd solving — closed forms, invariants and benchmarks
(`docs/architecture-phase4.md` §A verification plan)."""
import math
import time

import pytest

from strutture.shared.materials.concrete import concrete_properties
from strutture.shared.materials.rebar import rebar_properties
from strutture.shared.numeric import bisect
from strutture.shared.report import CalcError
from strutture.shared.sezione_ca import forme, geometria
from strutture.shared.sezione_ca.domini import dominio_biassiale, dominio_nm, m_rd
from strutture.shared.sezione_ca.integrazione import risultante_sezione
from strutture.shared.sezione_ca.leggi import (
    EPS_CU2,
    EPS_CU3,
    sigma_calcestruzzo_bilineare,
    sigma_calcestruzzo_parabola_rettangolo,
)
from strutture.shared.sezione_ca.modelli import Barra, MaterialiSezione, Sezione
from strutture.shared.tool import discover, execute

B, H = 300.0, 500.0


def _barre_4(diametro_mm: float = 16.0) -> tuple[Barra, ...]:
    return forme.fila_superiore(B, H, 30.0, 2, diametro_mm) + forme.fila_inferiore(B, H, 30.0, 2, diametro_mm)


def _sezione(materiali: MaterialiSezione, barre: tuple[Barra, ...] = ()) -> Sezione:
    return Sezione(contorno=forme.rettangolo(B, H), barre=barre, materiali=materiali)


def _poligono_convesso_con_tolleranza(punti: list[tuple[float, float]]) -> bool:
    """Un poligono è convesso se ogni terna consecutiva gira sempre nello stesso verso — con una
    tolleranza relativa alla scala del poligono, perché l'integrazione converge solo entro
    `tolleranza_relativa` (1e-4 di default, vedi `integrazione.py`): a quella grana, differenze
    finite del terzo ordine (il prodotto vettoriale fra segmenti quasi collineari) possono cadere
    sotto il rumore numerico e non contano come inversione di convessità."""
    n = len(punti)
    scala = max(max(abs(x) for x, _ in punti), max(abs(y) for _, y in punti))
    tolleranza = 2e-3 * scala
    segni: set[int] = set()
    for i in range(n):
        x0, y0 = punti[i]
        x1, y1 = punti[(i + 1) % n]
        x2, y2 = punti[(i + 2) % n]
        prodotto_vettoriale = (x1 - x0) * (y2 - y1) - (y1 - y0) * (x2 - x1)
        if abs(prodotto_vettoriale) > tolleranza:
            segni.add(1 if prodotto_vettoriale > 0 else -1)
    return len(segni) <= 1


def test_dominio_nm_estremi_coincidono_con_gli_stati_uniformi(materiali_c25_b450c) -> None:
    """Gli estremi N del dominio sono esattamente `N=-fyd*As` e `N=fcd*Ac+fyd*As` (item 1)."""
    barre = _barre_4()
    sezione = _sezione(materiali_c25_b450c, barre)
    area_barre = sum(b.area_mm2 for b in barre)
    area_cls = B * H - area_barre
    n_min_atteso = -materiali_c25_b450c.acciaio.fyd_MPa * area_barre / 1000.0
    n_max_atteso = (
        materiali_c25_b450c.calcestruzzo.fcd_MPa * area_cls + materiali_c25_b450c.acciaio.fyd_MPa * area_barre
    ) / 1000.0
    dominio = dominio_nm(sezione, "x", 72)
    assert min(p.n_kN for p in dominio) == pytest.approx(n_min_atteso, rel=1e-6)
    assert max(p.n_kN for p in dominio) == pytest.approx(n_max_atteso, rel=1e-6)


def test_dominio_convesso(materiali_c25_b450c) -> None:
    """Item 2: il dominio è convesso (ogni vertice gira sempre nello stesso verso)."""
    sezione = _sezione(materiali_c25_b450c, _barre_4())
    dominio = dominio_nm(sezione, "x", 72)
    assert _poligono_convesso_con_tolleranza([(p.n_kN, p.m_kNm) for p in dominio])


def test_dominio_contiene_origine(materiali_c25_b450c) -> None:
    """Item 2: il dominio contiene l'origine (N=0, M=0 è sempre uno stato ammissibile)."""
    sezione = _sezione(materiali_c25_b450c, _barre_4())
    dominio = dominio_nm(sezione, "x", 72)
    poligono = tuple((p.n_kN, p.m_kNm) for p in dominio)
    assert geometria.punto_in_poligono((0.0, 0.0), poligono)


def test_sezione_simmetrica_dominio_simmetrico_attorno_asse_n(materiali_c25_b450c) -> None:
    """Item 2: sezione e armatura simmetriche (rispetto a x) -> dominio simmetrico rispetto
    all'asse N (per ogni (N, M) esiste (N, -M))."""
    sezione = _sezione(materiali_c25_b450c, _barre_4())
    dominio = dominio_nm(sezione, "x", 48)
    meta = len(dominio) // 2
    for j in range(meta):
        positivo, negativo = dominio[meta + j], dominio[meta - 1 - j]
        assert positivo.n_kN == pytest.approx(negativo.n_kN, rel=1e-6)
        assert positivo.m_kNm == pytest.approx(-negativo.m_kNm, rel=1e-6, abs=1e-8)


def test_rotazione_90_gradi_scambia_i_domini_x_e_y(materiali_c25_b450c) -> None:
    """Item 2: ruotando l'intera sezione di 90°, il dominio 'y' della sezione ruotata coincide
    punto a punto con il dominio 'x' della sezione originale (armatura asimmetrica, per non
    ricadere in un caso già simmetrico)."""
    barre = forme.fila_superiore(B, H, 30.0, 3, 16.0)
    sezione = _sezione(materiali_c25_b450c, barre)
    dominio_x = dominio_nm(sezione, "x", 48)

    contorno_ruotato = geometria.ruota(sezione.contorno, math.pi / 2.0)
    barre_ruotate = tuple(Barra(x_mm=-b.y_mm, y_mm=b.x_mm, diametro_mm=b.diametro_mm) for b in barre)
    sezione_ruotata = Sezione(contorno=contorno_ruotato, barre=barre_ruotate, materiali=materiali_c25_b450c)
    dominio_y_ruotata = dominio_nm(sezione_ruotata, "y", 48)

    for originale, ruotato in zip(dominio_x, dominio_y_ruotata, strict=True):
        assert ruotato.n_kN == pytest.approx(originale.n_kN, rel=1e-6)
        assert ruotato.m_kNm == pytest.approx(originale.m_kNm, rel=1e-6, abs=1e-8)


def test_scala_k_scala_n_k2_e_m_rd_k3(materiali_c25_b450c) -> None:
    """Item 2: scalando tutte le dimensioni di `k`, `M_Rd` a `N=N_Ed*k²` scala di `k³`."""
    barre = forme.fila_superiore(B, H, 30.0, 3, 16.0)
    sezione = _sezione(materiali_c25_b450c, barre)
    n_ed_kN = 500.0
    base = m_rd(sezione, n_ed_kN, "x")

    k = 1.7
    contorno_scalato = tuple((x * k, y * k) for x, y in sezione.contorno)
    barre_scalate = tuple(Barra(x_mm=b.x_mm * k, y_mm=b.y_mm * k, diametro_mm=b.diametro_mm * k) for b in barre)
    sezione_scalata = Sezione(contorno=contorno_scalato, barre=barre_scalate, materiali=materiali_c25_b450c)
    scalato = m_rd(sezione_scalata, n_ed_kN * k ** 2, "x")

    assert scalato[0] == pytest.approx(base[0] * k ** 3, rel=1e-4)
    assert scalato[1] == pytest.approx(base[1] * k ** 3, rel=1e-4)


def test_raffinamento_n_punti_stabile(materiali_c25_b450c) -> None:
    """Item 2 (raffinamento): un dominio più fitto resta convesso e con gli stessi estremi N di
    uno più rado (la forma non "esplode" infittendo il campionamento)."""
    sezione = _sezione(materiali_c25_b450c, _barre_4())
    rado = dominio_nm(sezione, "x", 24)
    fitto = dominio_nm(sezione, "x", 144)
    assert min(p.n_kN for p in rado) == pytest.approx(min(p.n_kN for p in fitto), rel=1e-6)
    assert max(p.n_kN for p in rado) == pytest.approx(max(p.n_kN for p in fitto), rel=1e-6)
    assert _poligono_convesso_con_tolleranza([(p.n_kN, p.m_kNm) for p in fitto])


def test_sezioni_a_t_e_a_l_senza_errori_e_convesse(materiali_c25_b450c) -> None:
    """Item 2/architettura: sezioni non convesse (T, L) sono gestite senza errori e producono un
    dominio N-M comunque convesso."""
    sezione_t = Sezione(
        contorno=forme.sezione_a_t(600.0, 150.0, 300.0, 500.0),
        barre=(Barra(x_mm=-100.0, y_mm=30.0, diametro_mm=20.0), Barra(x_mm=100.0, y_mm=30.0, diametro_mm=20.0)),
        materiali=materiali_c25_b450c,
    )
    dominio_t = dominio_nm(sezione_t, "x", 48)
    assert _poligono_convesso_con_tolleranza([(p.n_kN, p.m_kNm) for p in dominio_t])

    sezione_l = Sezione(
        contorno=forme.sezione_a_l(400.0, 150.0, 200.0, 500.0),
        barre=(
            Barra(x_mm=350.0, y_mm=75.0, diametro_mm=20.0),
            Barra(x_mm=30.0, y_mm=470.0, diametro_mm=16.0),
            Barra(x_mm=170.0, y_mm=470.0, diametro_mm=16.0),
        ),
        materiali=materiali_c25_b450c,
    )
    dominio_l = dominio_nm(sezione_l, "x", 48)
    assert _poligono_convesso_con_tolleranza([(p.n_kN, p.m_kNm) for p in dominio_l])


def _integra_zona_compressa_rettangolo(sigma_fn, fcd_MPa: float, b_mm: float, x_mm: float, eps_cu: float, n: int = 20000):
    """Integrazione trapezoidale indipendente (NON usa `integrazione.py`) di forza e baricentro
    della risultante di compressione del cls su una zona rettangolare di profondità `x_mm` dal
    lembo compresso, con deformazione lineare da `-eps_cu` (lembo) a `0` (asse neutro a `x_mm`).
    Restituisce `(F, ybar)`: `F` positiva se di compressione, `ybar` distanza del baricentro dal
    lembo compresso -- il "closed form" di riferimento richiesto dal piano di verifica (item 1)."""
    passo = x_mm / n
    forza = momento = 0.0
    for i in range(n + 1):
        peso = 0.5 if i in (0, n) else 1.0
        zeta = i * passo
        eps = -eps_cu * (1.0 - zeta / x_mm)
        sigma = sigma_fn(eps, fcd_MPa)
        forza += peso * sigma * b_mm * passo
        momento += peso * sigma * b_mm * passo * zeta
    return -forza, (momento / forza if forza != 0.0 else 0.0)


def _mrd_chiuso_rettangolo(sigma_fn, eps_cu: float, fcd_MPa: float, fyd_MPa: float, b_mm: float, d_mm: float, as_mm2: float) -> float:
    """M_Rd in forma chiusa (equilibrio + baricentro esatti via `_integra_zona_compressa_rettangolo`,
    non tramite l'engine di Parte 1/2): profondità dell'asse neutro `x` dall'equilibrio `Fc(x) =
    As*fyd`, poi `M_Rd = As*fyd*(d - ybar(x))`."""
    target = as_mm2 * fyd_MPa
    x_mm = bisect(lambda x: _integra_zona_compressa_rettangolo(sigma_fn, fcd_MPa, b_mm, x, eps_cu)[0] - target, 1.0, d_mm * 2.0)
    _, ybar = _integra_zona_compressa_rettangolo(sigma_fn, fcd_MPa, b_mm, x_mm, eps_cu)
    return as_mm2 * fyd_MPa * (d_mm - ybar) / 1e6


@pytest.mark.parametrize(
    ("legge_calcestruzzo", "sigma_fn", "eps_cu", "tolleranza_forma_chiusa", "tolleranza_tool"),
    [
        ("bilineare", sigma_calcestruzzo_bilineare, EPS_CU3, 1e-3, 5e-3),
        ("parabola-rettangolo", sigma_calcestruzzo_parabola_rettangolo, EPS_CU2, 1e-3, 2e-2),
    ],
)
def test_flessione_pura_rettangolo_forma_chiusa_e_tool(legge_calcestruzzo, sigma_fn, eps_cu, tolleranza_forma_chiusa, tolleranza_tool) -> None:
    """Item 1/3: `M_Rd` a flessione pura di una trave rettangolare in semplice armatura coincide
    con (a) la forma chiusa del blocco di tensioni della STESSA legge costitutiva (equilibrio +
    baricentro integrati indipendentemente, derivazione sopra) entro un rumore numerico < 0.1 %,
    e (b) il valore MRd del tool esistente `ca-trave-rettangolare` (che usa il blocco 0.8x fisso,
    NTC2018 §4.1.2.3.4.2) entro 0.5 % per la legge bilineare (beta1 = 1-eps_c3/(2*eps_cu3) = 0.75,
    vicino al blocco 0.8x) e 2 % per la parabola-rettangolo (beta1 = 1-eps_c2/(3*eps_cu2) = 0.81,
    la deviazione teorica nota fra parabola-rettangolo e blocco semplificato)."""
    tools = discover()
    tool = tools["ca-trave-rettangolare"]
    riferimento = execute(tool, dict(tool.example))
    assert riferimento.ok
    mrd_tool_kNm = riferimento.data.flessione.mrd_kNm

    b_mm, h_mm, copriferro_mm = tool.example["b_mm"], tool.example["h_mm"], tool.example["copriferro_mm"]
    n_ferri, diametro_mm = tool.example["n_ferri1"], tool.example["diametro_ferri1_mm"]
    as_mm2 = n_ferri * math.pi * diametro_mm ** 2 / 4.0
    d_mm = h_mm - copriferro_mm
    y_barra = -h_mm / 2.0 + copriferro_mm
    diametro_equivalente = math.sqrt(4.0 * as_mm2 / math.pi)

    materiali = MaterialiSezione(
        calcestruzzo=concrete_properties(tool.example["tipo_cls"]),
        acciaio=rebar_properties(tool.example["tipo_acciaio"]),
        legge_calcestruzzo=legge_calcestruzzo,
    )
    fcd_MPa, fyd_MPa = materiali.calcestruzzo.fcd_MPa, materiali.acciaio.fyd_MPa
    sezione = Sezione(
        contorno=forme.rettangolo(b_mm, h_mm),
        barre=(Barra(x_mm=0.0, y_mm=y_barra, diametro_mm=diametro_equivalente),),
        materiali=materiali,
    )

    mrd_chiuso_kNm = _mrd_chiuso_rettangolo(sigma_fn, eps_cu, fcd_MPa, fyd_MPa, b_mm, d_mm, as_mm2)
    mrd_engine_kNm, _ = m_rd(sezione, 0.0, "x")

    assert mrd_engine_kNm == pytest.approx(mrd_chiuso_kNm, rel=tolleranza_forma_chiusa)
    assert mrd_engine_kNm == pytest.approx(mrd_tool_kNm, rel=tolleranza_tool)


def test_punto_bilanciato_xi_eps_cu_su_eps_cu_piu_eps_yd(materiali_c25_b450c) -> None:
    """Item 1: punto bilanciato (asse neutro tale che il cls raggiunge `eps_cu2` mentre l'acciaio
    teso raggiunge esattamente `eps_yd`), `xi = x/d = eps_cu2/(eps_cu2+eps_yd)` (similitudine di
    Thales sul diagramma piano delle deformazioni). Costruito qui INDIPENDENTEMENTE dal parametro
    pivot `t` (direttamente dalla definizione, non da `stati_ultimi.py`), poi confrontato con la
    bisezione di `m_rd` allo stesso N -- i due percorsi devono coincidere."""
    copriferro_mm = 40.0
    acciaio = materiali_c25_b450c.acciaio
    eps_yd = acciaio.fyd_MPa / acciaio.es_MPa
    d_mm = H - copriferro_mm
    xi = EPS_CU2 / (EPS_CU2 + eps_yd)
    x_bal_mm = xi * d_mm

    y_top, y_barra = H / 2.0, -(H / 2.0 - copriferro_mm)
    y_asse_neutro = y_top - x_bal_mm
    kx = -EPS_CU2 / (y_top - y_asse_neutro)
    eps0 = -kx * y_asse_neutro

    from strutture.shared.sezione_ca.integrazione import epsilon, risultante_sezione

    assert epsilon(eps0, kx, 0.0, 0.0, y_barra) == pytest.approx(eps_yd, rel=1e-9)

    sezione = Sezione(
        contorno=forme.rettangolo(B, H), barre=(Barra(x_mm=0.0, y_mm=y_barra, diametro_mm=20.0),), materiali=materiali_c25_b450c,
    )
    bilanciato = risultante_sezione(sezione, eps0, kx, 0.0)
    mrd_pos, _ = m_rd(sezione, bilanciato.n_kN, "x")
    assert mrd_pos == pytest.approx(bilanciato.mx_kNm, rel=1e-3)


def test_m_rd_fuori_dominio_solleva_calc_error_in_italiano(materiali_c25_b450c) -> None:
    sezione = _sezione(materiali_c25_b450c, _barre_4())
    with pytest.raises(CalcError, match="fuori dal dominio"):
        m_rd(sezione, 1.0e7, "x")


def test_m_rd_coerente_con_dominio_nm_per_interpolazione(materiali_c25_b450c) -> None:
    """`m_rd` (bisezione diretta) e `dominio_nm` (campionamento sui pivot) devono concordare: `M`
    interpolato linearmente fra i due punti del dominio che racchiudono `N_Ed` deve avvicinarsi al
    valore bisezionato da `m_rd` allo stesso `N_Ed` (stessa curva, due modi di leggerla)."""
    sezione = _sezione(materiali_c25_b450c, _barre_4())
    dominio = dominio_nm(sezione, "x", 144)
    meta = len(dominio) // 2  # ramo N crescente, M >= 0 (vedi costruzione in domini.py)
    ramo_positivo = dominio[: meta]
    n_ed_kN = 300.0
    inferiore = max((p for p in ramo_positivo if p.n_kN <= n_ed_kN), key=lambda p: p.n_kN)
    superiore = min((p for p in ramo_positivo if p.n_kN >= n_ed_kN), key=lambda p: p.n_kN)
    if superiore.n_kN > inferiore.n_kN:
        frazione = (n_ed_kN - inferiore.n_kN) / (superiore.n_kN - inferiore.n_kN)
        m_interpolato = inferiore.m_kNm + (superiore.m_kNm - inferiore.m_kNm) * frazione
    else:
        m_interpolato = inferiore.m_kNm

    mrd_pos, _ = m_rd(sezione, n_ed_kN, "x")
    assert mrd_pos == pytest.approx(m_interpolato, rel=2e-2)


def test_ramo_compresso_coincide_con_la_famiglia_pivot_c_indipendente(materiali_c25_b450c) -> None:
    """CRITICO (item 3 del piano di verifica) — benchmark indipendente del ramo pivot C: costruisce
    la famiglia pivot C direttamente dalla sua definizione (NON tramite `stati_ultimi.py`) e la
    confronta con `m_rd`. Punto C è fissato a `(1 - eps_c2/eps_cu2)*h` dal lembo PIU' COMPRESSO
    (`eps_c2 = 2e-3`, `eps_cu2 = 3.5e-3`, sezione rettangolare `H = 500` mm simmetrica -> punto C a
    `y_c = H/2 - (1-eps_c2/eps_cu2)*H = -500/2 + 3/7*500 ≈ 32.14` mm dal centro, cioè a
    `(1-3/7)*H = 4/7*H` dal lembo teso -- `eps(y_c) = -eps_c2` esatto per costruzione), con
    `eps_top` (al lembo compresso, y=+H/2) che spazza `-eps_cu2 -> -eps_c2`: questo È il ramo
    "pivot C" per definizione (senza passare dal parametro pivot `t`). Confrontato con `m_rd(N)`
    dell'engine per diversi `N` fra lo stato `eps_bot=0` (fine del ramo pivot B, N ≈ 603 kN qui) e
    la compressione pura (`N = fcd*Ac + fyd*As`)."""
    barre = _barre_4()
    sezione = _sezione(materiali_c25_b450c, barre)
    eps_c2, eps_cu2 = 0.002, EPS_CU2
    y_c = H / 2.0 - (1.0 - eps_c2 / eps_cu2) * H  # punto C, a (1-eps_c2/eps_cu2)*H dal lembo compresso.

    for frazione_eps_top in (0.05, 0.3, 0.6, 0.9, 1.0):
        eps_top = -eps_cu2 + (eps_cu2 - eps_c2) * frazione_eps_top  # -eps_cu2 -> -eps_c2.
        kx = (eps_top - (-eps_c2)) / (H / 2.0 - y_c)
        eps0 = -eps_c2 - kx * y_c
        n_kN = risultante_sezione(sezione, eps0, kx, 0.0).n_kN

        mrd_pos, _ = m_rd(sezione, n_kN, "x")
        r = risultante_sezione(sezione, eps0, kx, 0.0)
        assert mrd_pos == pytest.approx(r.mx_kNm, rel=2e-3)


def test_dominio_biassiale_quadrato_4_barre_simmetrico_e_coerente_con_uniassiale(materiali_c25_b450c) -> None:
    """Item 4: sezione quadrata con 4 barre d'angolo -> dominio Mx-My simmetrico rispetto alla
    diagonale, e ai bordi (theta=0, theta=pi/2) coincide con i valori uniassiali di `m_rd`."""
    lato, copriferro_mm = 400.0, 40.0
    semiluce = lato / 2.0 - copriferro_mm
    barre = tuple(
        Barra(x_mm=sx * semiluce, y_mm=sy * semiluce, diametro_mm=20.0) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)
    )
    sezione = Sezione(contorno=forme.rettangolo(lato, lato), barre=barre, materiali=materiali_c25_b450c)
    n_ed_kN = 500.0
    n_angoli = 36
    dominio = dominio_biassiale(sezione, n_ed_kN, n_angoli)

    mrd_x, _ = m_rd(sezione, n_ed_kN, "x")
    mrd_y, _ = m_rd(sezione, n_ed_kN, "y")
    assert dominio[0].mx_kNm == pytest.approx(mrd_x, rel=1e-6)
    assert dominio[0].my_kNm == pytest.approx(0.0, abs=1e-6)
    assert dominio[n_angoli // 4].my_kNm == pytest.approx(mrd_y, rel=1e-6)
    assert dominio[n_angoli // 4].mx_kNm == pytest.approx(0.0, abs=1e-6)

    for mx, my in ((p.mx_kNm, p.my_kNm) for p in dominio):
        specchiato = min(dominio, key=lambda p: (p.mx_kNm - my) ** 2 + (p.my_kNm - mx) ** 2)
        distanza = math.hypot(specchiato.mx_kNm - my, specchiato.my_kNm - mx)
        assert distanza < 0.05 * max(abs(mx), abs(my), 1.0)


def test_dominio_biassiale_quadrato_convesso(materiali_c25_b450c) -> None:
    lato, copriferro_mm = 400.0, 40.0
    semiluce = lato / 2.0 - copriferro_mm
    barre = tuple(
        Barra(x_mm=sx * semiluce, y_mm=sy * semiluce, diametro_mm=20.0) for sx in (-1.0, 1.0) for sy in (-1.0, 1.0)
    )
    sezione = Sezione(contorno=forme.rettangolo(lato, lato), barre=barre, materiali=materiali_c25_b450c)
    dominio = dominio_biassiale(sezione, 500.0, 36)
    assert _poligono_convesso_con_tolleranza([(p.mx_kNm, p.my_kNm) for p in dominio])


def test_asse_letterale_invalido_non_ammesso(materiali_c25_b450c) -> None:
    """`mx_my_a_theta` è la primitiva generale; `asse` resta vincolato a "x"/"y" da `Literal` a
    livello di tipo — verifica indiretta che il dominio 'x' e 'y' non coincidano per una sezione
    palesemente asimmetrica (T)."""
    sezione = Sezione(
        contorno=forme.sezione_a_t(600.0, 150.0, 300.0, 500.0),
        barre=(Barra(x_mm=0.0, y_mm=30.0, diametro_mm=20.0),),
        materiali=materiali_c25_b450c,
    )
    dominio_x = dominio_nm(sezione, "x", 24)
    dominio_y = dominio_nm(sezione, "y", 24)
    assert dominio_x != dominio_y


def test_timing_dominio_nm_72_punti_sotto_un_secondo(materiali_c25_b450c) -> None:
    """Vincolo di prestazione dell'architettura: un dominio di 72 punti calcola in < 1 s (limite
    generoso nel test per evitare fragilità in CI)."""
    sezione = _sezione(materiali_c25_b450c, _barre_4())
    inizio = time.perf_counter()
    dominio_nm(sezione, "x", 72)
    assert time.perf_counter() - inizio < 1.0
