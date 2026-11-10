"""Welche Bestandsregel bei welchem Zustand? Regimekarte - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 7 der Reihe „Bestandspolitiken“ (Zusammenfluss der Stücke 1 bis 6): alle Lücken einfacher Bestellregeln gegen die exakte Rückwärtsrechnung auf einer Skala,
eine Leiter der Regeln, die Kreuzzellen „Fixkosten und Lieferzeit bei verlorener Nachfrage“. Die Karte liegt vorgerechnet in data/brg_karte.json (tools/build_karte.py).

Lauffähig mit: streamlit run app.py
"""

import os

os.environ.setdefault("OMP_NUM_THREADS", "1")  # kleine Matrizen: BLAS-Threads bremsen mehr, als sie helfen (vor dem Import von numpy setzen)

from fractions import Fraction  # noqa: E402

import streamlit as st  # noqa: E402

import brg_backorder as B  # noqa: E402
import brg_constants as C  # noqa: E402
import brg_data as D  # noqa: E402
import brg_evaluation as ev  # noqa: E402
import brg_hand as H  # noqa: E402
import brg_lost as V  # noqa: E402
import brg_texts as T  # noqa: E402
import brg_tree as TR  # noqa: E402
from brg_layout import dunkles_design, kopf_css  # noqa: E402
from brg_ladder import RULE_LABELS, RUNG_NAMES  # noqa: E402
from brg_lines import lower_hull  # noqa: E402
from brg_presets import bounds, init_session_state_defaults, load_permalink_settings, sidebar_presets, sync_query_params  # noqa: E402
from brg_visualization import build_gap_bars, build_gap_over_k, build_hand_lines, build_learning, build_map  # noqa: E402

st.set_page_config(page_title="Welche Bestandsregel bei welchem Zustand? Regimekarte – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner=False)
def _live_backorder(L, K, ph):
    return B.solve(L, K, ph)


@st.cache_data(show_spinner=False)
def _live_lost(L, K):
    return V.solve_cell(L, K, enumerate_check=False)


@st.cache_data(show_spinner=False)
def _hand_a():
    return H.a_rule_lines(), lower_hull(H.a_all_lines().values(), Fraction(6))


@st.cache_data(show_spinner=False)
def _hand_b():
    lines = H.b_all_lines()
    named = {
        "Base-Stock S = 3": lines[H.b_policy("bs", 3)],
        "(s,S) = (1,3)": lines[H.b_policy("ss", 1, 3)],
        "Capped (Kappe 1, S = 3)": lines[H.b_policy("cap", 3, 1)],
        "Capped (Kappe 1, S = 2)": lines[H.b_policy("cap", 2, 1)],
    }
    return named, lower_hull(lines.values(), Fraction(8))


@st.cache_data(show_spinner=False)
def _simulate(L, K, rule, params, paths, periods, burn, seeds):
    m = V.LostSales(L, K)
    pol = {"bs": lambda: m.pol_bs(*params), "ss": lambda: m.pol_ss(*params), "cap": lambda: m.pol_capped(*params), "ssc": lambda: m.pol_ss(*params)}[rule]()
    out = []
    for sd in seeds:
        c = V.simulate(m, pol, paths, periods, burn, sd)
        out.append((float(c.mean()), float(c.std(ddof=1) / len(c) ** 0.5)))
    return out


def _table(rows):
    st.dataframe(rows, hide_index=True, width="stretch")


def _latex_frac(x) -> str:
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else rf"\tfrac{{{x.numerator}}}{{{x.denominator}}}"


def _latex_line(name, ln) -> str:
    return rf"g_{{\text{{{name}}}}}(K) = {_latex_frac(ln.c0)} + {_latex_frac(ln.c1)}\,K"


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in brg_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("🗺️ Welche Bestandsregel bei welchem Zustand? Regimekarte")
st.markdown(T.INTRO_MARKDOWN)

with st.expander("So lesen Sie die Karte", expanded=True):
    st.markdown(T.HOW_MARKDOWN)

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Zelle**")
    modus = st.radio("Fehlmengen", C.MODI, key="modus_radio",
                     help="Rückstand: Nicht Geliefertes wird nachgeliefert, der Nettobestand wird negativ. Verlorene Nachfrage: Nicht Geliefertes verfällt.")
    L = st.slider("Lieferzeit L (Perioden)", *bounds("L_slider"), key="L_slider",
                  help="Perioden zwischen Bestellung und Verfügbarkeit. Rückstand: 0 bis 5 gemessen. Verlorene Nachfrage: 1 bis 4 (Lieferzeit 0 ist dort in diesem Zeitablauf nicht vorgesehen, Lieferzeit 5 mit Fixkosten nicht gerechnet).")
    K = st.select_slider("Fixkosten K je Bestellung (in Einheiten von h)", options=C.B_K, format_func=ev.fmt_k, key="K_select",
                         help="Nur gemessene Werte. Rückstand: 0 bis 4 in Schritten von 0,05, dann 5, 7,5, 10, 15, 20, 30. Verlorene Nachfrage: 0, 0,5, 1, 1,5, 2, 3, 5, 10 (Lieferzeit 4: 0, 1, 2, 5, 10).")
    ph = st.select_slider("Strafe je fehlendem Stück, p/h", options=C.B_PH, key="ph_select",
                          help="Rückstand: 4, 9, 19 gemessen. Verlorene Nachfrage: nur 9; andere Werte zeigen „nicht gemessen“.")
    st.markdown("**Karte und Handbeispiele**")
    marke = st.select_slider("Marke (Prozent der DP-Kosten)", options=C.MARKEN, format_func=lambda m: f"{m} %", key="marke_select",
                             help="Eine Regel „reicht“, wenn ihre Lücke gegen die DP echt unter der Marke liegt. Die Stufe einer Zelle hängt an der Marke.")
    K_hand = st.select_slider("Fixkosten K im Handbeispiel", options=C.HAND_K, format_func=ev.fmt_k, key="Khand_select",
                              help="Markiert K in den Geraden der beiden Handbeispiele (Reiter „Handbeispiele“).")
    st.markdown("**Struktur im Vergleich**")
    struktur = st.selectbox("Struktur", C.STRUKTUREN, key="struktur_select",
                            help="Die Zahlen der Stücke 4 bis 6 stehen im Reiter „Strukturen nebeneinander“; die Wahl hebt die Struktur dort hervor und steuert den Entscheidungsbaum.")

sync_query_params({"modus_radio": modus, "L_slider": int(L), "K_select": float(K), "ph_select": int(ph), "marke_select": int(marke), "Khand_select": float(K_hand),
                   "struktur_select": struktur})

cfg = ev.Settings(modus=modus, L=int(L), K=float(K), ph=int(ph), marke=int(marke), K_hand=float(K_hand), struktur=struktur)
view = ev.cell_view(cfg)
kmap = D.karte(cfg.modus, cfg.marke, cfg.ph)

# --- Ergebnis --------------------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Ergebnis")
if cfg.struktur != C.STRUKTUREN[0]:
    stueck = {C.STRUKTUREN[1]: 4, C.STRUKTUREN[2]: 5, C.STRUKTUREN[3]: 6}[cfg.struktur]
    st.info(f"**Gewählte Struktur: {cfg.struktur}.** Die Zahlen stammen aus der Demo des jeweiligen Stücks und gelten in deren Modell (Reiter „Strukturen nebeneinander“). "
            "Die Karte unten zeigt weiter die Regel-Lücken einer Stufe mit Fixkosten und Lieferzeit.")
    _table([dict(Regime=e["regime"], Aussage=e["aussage"], Voraussetzungen=e["modell"], Stand=e["stand"]) for e in D.uebernommen(stueck)])

if view.measured:
    r = view.rung
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("DP (Kosten je Periode)", ev.fmt(view.g_dp, 3), delta="Referenz", delta_color="off")
    m2.metric(f"Base-Stock ({view.params['bs']})", ev.fmt(view.cost("bs"), 3), delta=f"{ev.fmt_pct(view.gaps['bs'])} gegen DP", delta_color="inverse")
    two = view.gaps["ss"], "ss"
    if view.gaps.get("cap") is not None and view.gaps["cap"] < view.gaps["ss"]:
        two = view.gaps["cap"], "cap"
    m3.metric(f"{RULE_LABELS[two[1]]} ({view.params[two[1]]})", ev.fmt(view.cost(two[1]), 3), delta=f"{ev.fmt_pct(two[0])} gegen DP", delta_color="inverse")
    if view.gaps.get("ssc") is not None:
        m4.metric(f"(s,S) mit Kappe ({view.params['ssc']})", ev.fmt(view.cost("ssc"), 3), delta=f"{ev.fmt_pct(view.gaps['ssc'])} gegen DP", delta_color="inverse")
    else:
        m4.metric("Bestellanteil der DP", f"{ev.fmt(100 * view.p_order_dp, 1)} %", delta="der Perioden mit Bestellung", delta_color="off")
else:
    st.warning(f"Diese Zelle ist nicht gemessen: {view.why}")

st.plotly_chart(build_map(kmap, selected=(cfg.L, cfg.K)), width="stretch", key="main_map")
st.caption(T.LEITER_CAPTION + (" Verlorene Nachfrage: nur p/h = 9 gemessen." if cfg.modus == C.MODUS_LOST else ""))

# --- Kernfrage -------------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Welche einfache Regel reicht in dieser Zelle?")
kind, text = ev.verdict_cell(view)
getattr(st, kind)(text)
if cfg.modus == C.MODUS_BACKORDER:
    kind, text = ev.verdict_threshold(cfg.ph, cfg.L, cfg.marke)
    getattr(st, kind)(text)
kind, text = ev.verdict_map(kmap)
getattr(st, kind)(text)

st.subheader("🔍 Ihre Zelle")
if view.measured:
    keys = [k for k in ("bs", "ss", "cap", "ssc") if view.gaps.get(k) is not None]
    st.plotly_chart(build_gap_bars(view, cfg.marke), width="stretch", key="cell_bars")
    rows = []
    for k in keys:
        rows.append({"Regel": RULE_LABELS[k], "Parameter": view.params[k], "Lücke gegen DP": ev.fmt_pct(view.gaps[k]), "Kosten je Periode": ev.fmt(view.cost(k), 3),
                     "Mehrkosten gegen DP": ev.fmt(view.extra(k), 3), "Unter der Marke": "ja" if view.gaps[k] < cfg.marke else "nein"})
    _table(rows)
    cap_txt = (f" Base-Stock bestellt beim Rückstand in {ev.fmt(100 * ev.base_stock_order_share(), 1)} % der Perioden (1 − e^(−3): bestellt wird, sobald die Nachfrage der Vorperiode größer als 0 war); "
               if cfg.modus == C.MODUS_BACKORDER else " ")
    st.caption(f"Bezug: DP, Kosten je Periode einschließlich Fixkosten (in Einheiten von h). Bestellanteil der DP: {ev.fmt(100 * view.p_order_dp, 1)} % der Perioden." + cap_txt +
               "Bei hohem K ist die Prozentzahl überwiegend ein Effekt der Bestellhäufigkeit (zerlegt ist nur die Zelle Rückstand, Lieferzeit 1, K = 20); deshalb stehen Bestellanteil und absolute Mehrkosten daneben.")
    if cfg.modus == C.MODUS_BACKORDER:
        if st.button("🔁 Zelle live nachrechnen", key="live_button", help="Rechnet DP und Regeln dieser Zelle neu (Größenordnung 10 Millisekunden bis eine Sekunde) und vergleicht mit der Karte."):
            res = _live_backorder(cfg.L, cfg.K, cfg.ph)
            st.success(f"Live gerechnet: DP {ev.fmt(res['g'], 6)}, Base-Stock {ev.fmt_pct(res['gap_bs'])}; Unterschied zur vorgerechneten Karte: "
                       f"{abs(res['g'] - view.g_dp):.1e} bei den DP-Kosten, {abs(res['gap_bs'] - view.gaps['bs']):.1e} Punkte bei der Lücke von Base-Stock.")
    elif cfg.L <= 2:
        if st.button("🔁 Zelle live nachrechnen", key="live_button",
                     help="Rechnet DP und die Suche der vier Regeln neu; Größenordnung 2 bis 15 Sekunden bei Lieferzeit 1 und 2, je nach Last."):
            with st.spinner("Rechnet DP und Regelsuche, Größenordnung 2 bis 15 Sekunden …"):
                res = _live_lost(cfg.L, cfg.K)
            diff = max(abs(res["gaps"][k] - view.gaps[k]) for k in keys)
            st.success(f"Live gerechnet: DP {ev.fmt(res['g'], 6)}; größter Unterschied der vier Lücken zur vorgerechneten Karte: {diff:.1e} Punkte.")
    else:
        st.caption("Lieferzeit 3 und 4 sind vorgerechnet (`tools/build_karte.py`, Größenordnung zehn Sekunden bis eine Minute je Zelle unter Last); live nachrechnen lässt sich Lieferzeit 1 und 2.")
    if cfg.modus == C.MODUS_LOST:
        sim_rule = view.rung.rule if view.rung.rule else "ssc"
        if st.button("🎲 Simulationsprobe der Regel der Stufe", key="sim_button",
                     help="Simuliert die Regel der Zelle (die der Stufe, bei Stufe 4 die beste) mit den Zufalls-Seeds 1 bis 4 und vergleicht mit der exakten Auswertung."):
            params = tuple(view.cell["params"][sim_rule])
            with st.spinner("Simuliert vier Zufalls-Seeds mit je 2.000 Pfaden …"):
                sims = _simulate(cfg.L, cfg.K, sim_rule, params, 2000, 2000, 300, (1, 2, 3, 4))
            exact = view.cost(sim_rule)
            _table([{"Zufalls-Seed": sd, "Simuliert (Mittel je Periode)": ev.fmt(m_, 3), "Standardfehler": ev.fmt(se, 3), "Abweichung vom exakten Wert in Standardfehlern": ev.fmt((m_ - exact) / se, 2)}
                    for sd, (m_, se) in zip((1, 2, 3, 4), sims)])
            st.caption(f"Regel: {RULE_LABELS[sim_rule]} ({view.params[sim_rule]}), exakt {ev.fmt(exact, 3)} je Periode (stationäre Verteilung). Pfade starten leer, die ersten 300 Perioden zählen nicht "
                       "(Einschwingzeit); Zufallsstrom SplitMix64 mit Inversion der Verteilungsfunktion.")
if cfg.modus == C.MODUS_BACKORDER:
    st.markdown("**Lücke von Base-Stock über K** (Rückstand, Lieferzeit 0 bis 5): Die Lücke wächst mit K; die Marke zeigt, wo Base-Stock sie verlässt.")
    st.plotly_chart(build_gap_over_k(cfg.ph, cfg.marke), width="stretch", key="gap_over_k")

st.markdown("---")

# --- Reiter ----------------------------------------------------------------------------------------------------------------------------------

tab_hand, tab_struct, tab_tree, tab_limit, tab_white = st.tabs(
    ["📝 Handbeispiele", "🧱 Strukturen nebeneinander", "🌳 Entscheidungsbaum", "🧮 Rechengrenze und Lernen", "⚪ Weiße Flecken"])

with tab_hand:
    st.markdown(T.HAND_INTRO)
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(T.HAND_A)
        lines_a, hull_a = _hand_a()
        names_a = {"Base-Stock S = 2": lines_a["bs"], "(s,S) = (0,2)": lines_a["ss"]}
        st.latex(_latex_line("Base-Stock", lines_a["bs"]))
        st.latex(_latex_line("(0,2)", lines_a["ss"]))
        st.plotly_chart(build_hand_lines(names_a, hull_a, cfg.K_hand, 6), width="stretch", key="hand_a_chart")
        kind, text = ev.verdict_hand_a(cfg.K_hand)
        getattr(st, kind)(text)
        st.caption("Dicke graue Linie: Optimum aller 720 Politiken (untere Hülle in exakten Brüchen). Senkrechte Linie: das K der Seitenleiste.")
    with col_b:
        st.markdown(T.HAND_B)
        named_b, hull_b = _hand_b()
        st.plotly_chart(build_hand_lines(named_b, hull_b, cfg.K_hand, 8), width="stretch", key="hand_b_chart")
        kind, text = ev.verdict_hand_b(cfg.K_hand)
        getattr(st, kind)(text)
        st.caption("Dicke graue Linie: Optimum aller 81 Politiken. Die Wechsel der besten Politik liegen bei den K-Werten: " +
                   ", ".join(ev.fmt_frac(k) for k, _ in hull_b[1:]) + ".")

with tab_struct:
    st.markdown("Die Zahlen der Stücke 1 bis 6 **nebeneinander**, mit Quelle und Voraussetzung. Sie sind **nicht neu gerechnet**, sondern aus den READMEs übernommen; ein Test vergleicht sie wörtlich "
                "mit den Schwester-Demos. Die Karte zeigt damit, **welche Stufe der Leiter** in welcher Struktur die erste ist, keine Rangfolge der Regeln. Zahlen aus verschiedenen Stücken "
                "haben verschiedene Modelle (Raster, Bestellgrenzen); ein Vergleich der Zeilen untereinander ist nur mit den Voraussetzungen möglich.")
    gewaehlt = {C.STRUKTUREN[0]: (1, 2, 3), C.STRUKTUREN[1]: (4,), C.STRUKTUREN[2]: (5,), C.STRUKTUREN[3]: (6,)}[cfg.struktur]
    entries = sorted(D.uebernommen(), key=lambda e: (e["stueck"] not in gewaehlt, e["stueck"]))
    _table([{"Stück": e["stueck"], "Struktur": e["struktur"], "Fehlmengen, Fixkosten": e["regime"], "Aussage": e["aussage"], "Voraussetzungen": e["modell"], "Stand": e["stand"],
             "Demo": f"{e['repo']}"} for e in entries])
    abschriften = [e["repo"] for e in D.uebernommen() if e["stand"] == "Abschrift"]
    st.caption((f"Stand „Abschrift“: Die README von {', '.join(sorted(set(abschriften)))} war noch nicht fertig, die Zahl stammt aus dem Plan des Stückes und seinen Rohausgaben. " if abschriften else "") +
               "Die Stücke 3 bis 6 rechnen ohne Fixkosten; mit Fixkosten rechnen nur Stück 2 (Rückstand) und diese Demo (Rückstand und verlorene Nachfrage).")

with tab_tree:
    st.markdown(T.BAUM_INTRO)
    verderblich = "nein"
    if cfg.struktur == C.STRUKTUREN[1]:
        regel = st.radio("Ausgaberegel der verderblichen Ware", ["FIFO", "LIFO"], index=1, horizontal=True, key="tree_ausgabe",
                         help="FIFO: das älteste Stück wird zuerst verkauft. LIFO: das frischeste zuerst.")
        verderblich = regel.lower()
    antworten = dict(stufen="zwei" if cfg.struktur == C.STRUKTUREN[2] else "eine", verderblich=verderblich, fehlmenge="rueckstand" if cfg.modus == C.MODUS_BACKORDER else "verloren",
                     K=cfg.K, L=cfg.L, marke=cfg.marke, rechenbar=cfg.struktur != C.STRUKTUREN[3])
    path = [("1. Mehrere Stufen in Reihe?", "ja" if antworten["stufen"] == "zwei" else "nein"),
            ("2. Verderbliche Ware?", "nein" if verderblich == "nein" else f"ja, {verderblich.upper()}-Ausgabe"),
            ("3. Fehlmengen?", "Rückstand" if antworten["fehlmenge"] == "rueckstand" else "verlorene Nachfrage"),
            ("4. Fixkosten K und Lieferzeit L?", f"K = {ev.fmt_k(cfg.K)}, L = {cfg.L}" + (f" (Takt {ev.fmt(D.eoq_takt(cfg.K))} Perioden)" if cfg.K > 0 else "")),
            ("5. Marke?", f"{cfg.marke} %"),
            ("6. Zustandszahl der exakten DP rechenbar?", "ja" if antworten["rechenbar"] else "nein (angenommen: DP nicht gerechnet, wie in Stück 6)")]
    _table([{"Frage": q, "Antwort": a} for q, a in path])
    lf = TR.leaf(antworten)
    st.markdown(f"**Blatt: {lf.titel}.** Regel: **{lf.regel}**.")
    getattr(st, "success" if lf.gemessen else "info")(lf.text)
    st.caption(f"Quelle: {lf.quelle}.")

with tab_limit:
    st.markdown("**Rechengrenze.** Bei verlorener Nachfrage wächst die Zahl der DP-Zustände mit jeder Periode Lieferzeit um den Faktor Bestellgrenze + 1.")
    rg = D.load()["rechengrenze"]
    rows = []
    for l_ in (1, 2, 3, 4, 5):
        n = rg["diese_demo"]["zustaende"][str(l_)]
        art = {1: "live", 2: "live (Knopf in „Ihre Zelle“)", 3: "vorgerechnet", 4: "vorgerechnet", 5: "nicht gerechnet, nur gezählt"}[l_]
        rows.append({"Lieferzeit": l_, f"Zustände ({rg['diese_demo']['formel']}, Bestellgrenze 12, Bestand höchstens 26)": f"{n:,}".replace(",", "."), "Zelle mit Fixkosten": art})
    _table(rows)
    s6 = rg["stueck6"]
    def _de(n):
        return f"{n:,}".replace(",", ".")

    st.caption(f"Stück 6 (ohne Fixkosten, Bestellgrenze 8, Bestand höchstens 20): {s6['formel']} Zustände; Lieferzeit 7: {_de(s6['zustaende']['7'])} Zustände, Lieferzeit 8: {_de(s6['zustaende']['8'])} "
               f"Zustände (etwa {ev.fmt(s6['tabelle_gb_L8'], 1)} GB je Wertetabelle). {s6['stand']}. Wo die DP nicht gerechnet wird, misst man gegen die beste Regel; das unterschätzt die Lücke zum Optimum "
               "um etwa deren eigene Lücke (Faktoren, nicht Punkte). Das Verdikt und die Unterschrift jeder Zelle nennen deshalb den Bezug (DP); alle Zellen dieser Demo haben ihn.")
    st.markdown("**Gelernte Politik mit Fixkosten** (Politikgradient, Verfahren und Einstellung aus Stück 6, Fixkosten in den Kosten; fünf Zufalls-Seeds, 3.000 Updates, 7,7e7 simulierte Perioden je Lauf; "
                "die Läufe liegen als Messwerte in `data/rohdaten/` und werden hier nicht wiederholt):")
    cols = st.columns(2)
    for col, (l_, k_) in zip(cols, ((3, 2.0), (4, 5.0))):
        cell = D.lernen_cell(l_, k_)
        with col:
            st.markdown(f"**Lieferzeit {l_}, K = {ev.fmt_k(k_)}**")
            st.plotly_chart(build_learning(cell, 2), width="stretch", key=f"learn_{l_}_{int(k_)}")
            kind, text = ev.verdict_learning(cell)
            getattr(st, kind)(text)
    chk = D.load().get("check_L4_K5")
    if chk:
        st.markdown("**Zelle Lieferzeit 4, K = 5: reicht die Position?** Beste Aufzählung (s,S) "
                    f"{ev.fmt_pct(chk['enum_ss']['gap'])}, Raster (s,S) mit Kappe {ev.fmt_pct(chk['raster_ssc']['gap'])}, beste gefundene Funktion der Bestandsposition nach einem Sweep der lokalen Suche "
                    f"{ev.fmt_pct(chk['position_function']['gap'])} (obere Schranke, nicht konvergiert). Ob das an der Zusammensetzung der Pipeline liegt, ist **offen**: in Lieferzeit 3, K = 2 liegt die Projektion der DP-Politik auf die Bestandsposition nach einer unabhängigen Prüfrechnung bei +0,26 %.")

with tab_white:
    st.markdown("Was diese Karte **nicht** sagt. Jede Zeile ist eine Grenze der Messung, keine Aussage über die Welt.")
    _table([
        dict(Frage="Anderes Mittel, andere Verteilung, anderes p/h bei Fixkosten und verlorener Nachfrage", Stand="nicht gemessen", Anmerkung="Gerechnet ist Poisson-Mittel 3, p/h = 9; beim Rückstand zusätzlich p/h = 4 und 19."),
        dict(Frage="Fixkosten bei verderblicher Ware", Stand="nicht gemessen", Anmerkung="Stück 4 rechnet ohne Fixkosten."),
        dict(Frage="Fixkosten bei zwei Stufen in Reihe", Stand="nicht gemessen", Anmerkung="Stück 5 rechnet ohne Fixkosten."),
        dict(Frage="Verlorene Nachfrage mit Fixkosten ab Lieferzeit 5", Stand="nicht gerechnet", Anmerkung="Die DP hätte 771.147 Zustände (Bestellgrenze 12, Bestand höchstens 26); nur gezählt."),
        dict(Frage="Verlorene Nachfrage mit K = 20 und mehr", Stand="nicht gerechnet", Anmerkung="Bei K = 10 bestellt die DP höchstens 10 bis 11 Stück (Bestellgrenze 12); für größeres K ist eine größere Bestellgrenze zu erwarten, sie wurde nicht gerechnet."),
        dict(Frage="Parameter der Stufen 2 und 3 sind global optimal in ihrer Familie", Stand="offen", Anmerkung="Lokale Suche, obere Schranke; Aufzählung nur für Lieferzeit 1 bis 3 und für die Zelle Lieferzeit 4 / K = 5."),
        dict(Frage="Reicht die Bestandsposition bei Fixkosten und verlorener Nachfrage?", Stand="offen", Anmerkung="Eine Zelle (Lieferzeit 4, K = 5), obere Schranke aus einem Sweep."),
        dict(Frage="Sätze der Literatur zu (s,S) bei verlorener Nachfrage", Stand="nicht geprüft", Anmerkung="In den gelesenen Quellen kommt verlorene Nachfrage mit Fixkosten nicht vor."),
        dict(Frage="Rechenzeit auf dem Server", Stand="nicht gemessen", Anmerkung="Zeitangaben dieser Demo sind Größenordnungen unter Last."),
    ])

st.markdown("---")

with st.expander("⚠️ Annahmen, Grenzen und bekannte Probleme"):
    st.markdown(T.ASSUMPTIONS_MARKDOWN)

with st.expander("📐 Mathematische Formulierung"):
    for part in T.MATH_MARKDOWN:
        st.markdown(part)
    st.markdown("**Literatur.** Feinberg, „Optimality Conditions for Inventory Control“ (arXiv 1606.00957; Volltext gelesen, Abschnitte 1 und 4); van Jaarsveld und Arts (arXiv 2101.07519, Volltext); "
                "Xin, Operations Research 69(1), 61–70 (2021), nur Abstract; Xin und Goldberg (arXiv 1409.1499, Volltext).")

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zur Reihe: [Bestandspolitiken: von Base-Stock bis Regelwahl](https://sebastianhanisch.net/konzepte-bestandspolitiken.html)."
)
