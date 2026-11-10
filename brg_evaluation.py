"""Kennzahlen, Zellenansicht und Verdikte (reine Funktionen: `verdict_*(...) -> (Art, Text)`, die App ruft `getattr(st, Art)(Text)`)."""

from dataclasses import dataclass, field
from fractions import Fraction
from math import exp

import brg_constants as C
import brg_data as D
from brg_gap import gap
from brg_ladder import RULE_LABELS, Rung, best_two_parameter, rung


@dataclass(frozen=True, kw_only=True)
class Settings:
    modus: str = C.MODUS_BACKORDER
    L: int = 3
    K: float = 3.0
    ph: int = 9
    marke: int = C.DEFAULT_MARKE
    K_hand: float = 1.0
    struktur: str = C.STRUKTUREN[0]


@dataclass(frozen=True)
class CellView:
    modus: str
    L: int
    K: float
    ph: int
    marke: float
    measured: bool
    why: str = ""
    gaps: dict = field(default_factory=dict)
    rung: Rung | None = None
    cell: dict | None = None
    g_dp: float | None = None
    params: dict = field(default_factory=dict)       # Regel -> Text der Parameter
    p_order_dp: float | None = None

    def cost(self, key):
        """Kosten je Periode der Regel (aus Lücke und DP-Kosten) oder None."""
        g = self.gaps.get(key)
        return None if g is None or self.g_dp is None else self.g_dp * (1 + g / 100.0)

    def extra(self, key):
        """Mehrkosten je Periode gegenüber der DP (absolut, in Einheiten von h)."""
        c = self.cost(key)
        return None if c is None else c - self.g_dp


def _unmeasured(s: Settings, why: str) -> CellView:
    return CellView(s.modus, s.L, s.K, s.ph, s.marke, False, why=why)


def cell_view(s: Settings) -> CellView:
    """Die Zelle der Einstellungen mit Lücken, Stufe, Parametern. Zellen ohne Messung geben `measured=False` und den Grund statt einer Zahl."""
    if s.modus == C.MODUS_BACKORDER:
        if s.L not in C.B_L or s.ph not in C.B_PH:
            return _unmeasured(s, "Rückstand ist für Lieferzeit 0 bis 5 und p/h = 4, 9, 19 gemessen.")
        cell = D.backorder_cell(s.ph, s.L, s.K)
        if cell is None:
            return _unmeasured(s, "Dieses K liegt nicht im Raster der Messung (0 bis 4 in Schritten von 0,05, dann 5, 7,5, 10, 15, 20, 30).")
        gaps = D.backorder_gaps(cell)
        params = {"bs": f"S = {cell['S_base_stock']}", "ss": f"s = {cell['s_dp']}, S = {cell['S_dp']}" if cell["s_dp"] is not None else "bestellt nie"}
        return CellView(s.modus, s.L, s.K, s.ph, s.marke, True, gaps=gaps, rung=rung(gaps, s.marke), cell=cell, g_dp=cell["g_dp"], params=params,
                        p_order_dp=cell["order_share_dp"])
    if s.L < 1:
        return _unmeasured(s, "Bei verlorener Nachfrage ist Lieferzeit 0 in diesem Zeitablauf (Ankunft nach der Nachfrage der Periode) nicht vorgesehen.")
    if s.ph != C.V_PH:
        return _unmeasured(s, "Verlorene Nachfrage ist nur für p/h = 9 gemessen.")
    cell = D.lost_cell(s.L, s.K, s.ph)
    if cell is None:
        return _unmeasured(s, "Verlorene Nachfrage mit Fixkosten ist für Lieferzeit 1 bis 3 mit K = 0, 0,5, 1, 1,5, 2, 3, 5, 10 und für Lieferzeit 4 mit K = 0, 1, 2, 5, 10 gemessen; "
                              "Lieferzeit 5 mit Fixkosten ist nicht gerechnet.")
    gaps = D.lost_gaps(cell)
    pr = cell["params"]
    params = {"bs": f"S = {pr['bs'][0]}", "ss": f"s = {pr['ss'][0]}, S = {pr['ss'][1]}", "cap": f"S = {pr['cap'][0]}, Kappe {pr['cap'][1]}",
              "ssc": f"s = {pr['ssc'][0]}, S = {pr['ssc'][1]}, Kappe {pr['ssc'][2]}"}
    return CellView(s.modus, s.L, s.K, s.ph, s.marke, True, gaps=gaps, rung=rung(gaps, s.marke), cell=cell, g_dp=cell["g"], params=params, p_order_dp=cell["p_order"])


def base_stock_order_share() -> float:
    """Anteil der Perioden mit Bestellung unter Base-Stock bei Rückstand: 1 - exp(-Mittel) (bestellt wird, wenn die Nachfrage der Vorperiode größer als 0 war).
    Gilt im Modell der Demo, solange die Bestellgrenze nicht greift."""
    return 1.0 - exp(-C.MEAN)


# ---------------------------------------------------------------- Formatierung
def fmt(x, nd=2) -> str:
    return f"{float(x):.{nd}f}".replace(".", ",")


def fmt_pct(x, nd=2) -> str:
    return f"{float(x):+.{nd}f}".replace(".", ",") + " %"


def fmt_k(K) -> str:
    """K mit so vielen Stellen wie nötig (0,05er-Raster): 1,3 statt 1,30."""
    s = f"{float(K):.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")


def fmt_frac(x) -> str:
    x = Fraction(x)
    return str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"


# ---------------------------------------------------------------- Verdikte
def verdict_cell(v: CellView) -> tuple[str, str]:
    """Verdikt der Kernfrage für die gewählte Zelle: kleinste Stufe unter der Marke, mit den Voraussetzungen (Modell, Bezug)."""
    if not v.measured:
        return "info", f"Diese Zelle ist nicht gemessen: {v.why}"
    modell = "Rückstand" if v.modus == C.MODUS_BACKORDER else "verlorene Nachfrage"
    kopf = f"Lieferzeit {v.L}, K = {fmt_k(v.K)}, {modell}, p/h = {v.ph}, Mittel 3, Marke {fmt(v.marke, 0)} %. Bezug: DP."
    r = v.rung
    if r.rung == 1:
        return "success", f"**Kleinste Stufe unter {fmt(v.marke, 0)} %: Stufe 1, Base-Stock** ({fmt_pct(r.gap)} gegen die DP). {kopf}"
    if r.rung == 2:
        if v.modus == C.MODUS_BACKORDER:
            return "info", (f"**Base-Stock reicht nicht mehr** ({fmt_pct(v.gaps['bs'])} gegen die DP, Marke {fmt(v.marke, 0)} %); **Stufe 2, (s,S)** trifft die DP "
                            f"({fmt_pct(v.gaps['ss'])}; die DP-Politik hat auf den erreichten Positionen reine (s,S)-Form). {kopf}")
        name = RULE_LABELS[r.rule]
        andere = "cap" if r.rule == "ss" else "ss"
        return "info", (f"**Kleinste Stufe unter {fmt(v.marke, 0)} %: Stufe 2, {name}** ({fmt_pct(r.gap)}); Base-Stock liegt bei {fmt_pct(v.gaps['bs'])}, "
                        f"{RULE_LABELS[andere]} bei {fmt_pct(v.gaps[andere])}. {kopf}")
    if r.rung == 3:
        two = best_two_parameter(v.gaps)
        return "warning", (f"**Zwei Schwächen zugleich: keine Zweiparameterregel unter {fmt(v.marke, 0)} %** ((s,S) {fmt_pct(v.gaps['ss'])}, Capped {fmt_pct(v.gaps['cap'])}); "
                           f"erst **Stufe 3, (s,S) mit Kappe** erreicht {fmt_pct(r.gap)} (bessere Zweiparameterregel: {RULE_LABELS[two[1]]} {fmt_pct(two[0])}). {kopf}")
    best = min((g, k) for k, g in v.gaps.items() if g is not None)
    return "error", (f"**Keine einfache Regel unter {fmt(v.marke, 0)} %** (beste Regel: {RULE_LABELS[best[1]]} {fmt_pct(best[0])}). Stufe 4: exakte DP, solange sie rechenbar ist, "
                     f"sonst bleibt nur eine gelernte Politik (in den zwei gemessenen Zellen im Median +1,14 bzw. +1,65 %). {kopf}")


def verdict_threshold(p_h: int, L: int, marke: float) -> tuple[str, str]:
    """Rückstand: ab welchem K Base-Stock die Marke erreicht (kleinstes K des Rasters mit Lücke >= Marke), mit dem Losgrößen-Takt dazu."""
    k = D.threshold_k(p_h, L, marke)
    if k is None:
        return "info", f"Rückstand, Lieferzeit {L}, p/h = {p_h}: Im Raster (K bis 30) erreicht die Lücke von Base-Stock {fmt(marke, 0)} % nie."
    return "info", (f"Rückstand, Lieferzeit {L}, p/h = {p_h}: **ab K = {fmt_k(k)} liegt Base-Stock bei oder über {fmt(marke, 0)} %** (kleinstes K des Rasters; Raster 0,05 bis K = 4). "
                    f"Der Takt der Losgrößenformel √(2K/(h·μ)) ist dort {fmt(D.eoq_takt(k))} Perioden (K gegen h mal Mittel μ = 3, nicht gegen eine Losgröße).")


def verdict_map(k: dict) -> tuple[str, str]:
    """Zählung im Raster der Karte (kein Anteil der Welt): in x von y gemessenen Zellen reicht Base-Stock."""
    n = D.count_cells(k)
    c = D.count_rungs(k)
    modell = "Rückstand" if k["modus"] == C.MODUS_BACKORDER else "verlorene Nachfrage"
    return "info", (f"Raster {modell}, p/h = {k['p_h']}, Marke {fmt(k['marke'], 0)} %: in **{c[1]} von {n} Zellen reicht Base-Stock**; Stufe 2 in {c[2]}, Stufe 3 in {c[3]}, "
                    f"Stufe 4 in {c[4]} Zellen. Das ist eine Zählung im gemessenen Raster, kein Anteil der Welt.")


def hand_a_gap(K) -> Fraction:
    """Lücke von Base-Stock gegen (s,S) = (0,2) im Handbeispiel A bei K, in Prozent (exakt): (1 + 3K/4) / (11/10 + 9K/20) - 1, aus den Geraden der Aufzählung."""
    import brg_hand as H
    lines = H.a_rule_lines()
    K = Fraction(K).limit_denominator(1000)
    return gap(lines["bs"].value(K), lines["ss"].value(K))


def hand_a_ss_until() -> Fraction:
    """Obergrenze von K, bis zu der (s,S) = (0, 2) im Handbeispiel A die beste der 720 Politiken ist (untere Hülle; danach wechselt das Optimum weiter)."""
    import brg_hand as H
    from brg_lines import lower_hull
    hull = lower_hull(list(H.a_all_lines().values()), 10 ** 6)
    ss = H.a_rule_lines()["ss"]
    i = next(i for i, (_k, ln) in enumerate(hull) if ln == ss)
    return hull[i + 1][0]


def verdict_hand_a(K: float) -> tuple[str, str]:
    import brg_hand as H
    from brg_lines import crossing, threshold
    lines = H.a_rule_lines()
    kx = crossing(lines["bs"], lines["ss"])
    t2 = threshold(lines["bs"], lines["ss"], 2)
    k_end = hand_a_ss_until()
    g = hand_a_gap(K)
    return "info", (f"Handbeispiel A (Rückstand, Lieferzeit 0): bei K = {fmt_k(K)} liegt Base-Stock {fmt_pct(float(g), 1)} über (s,S) = (0, 2). Die Geraden g(K) kreuzen sich bei K = {fmt_frac(kx)}; "
                    f"darunter ist Base-Stock optimal, darüber (0, 2) bis K = {fmt_frac(k_end)} (≈ {fmt(float(k_end), 2)}; danach wechselt das Optimum weiter). "
                    f"Die Lücke erreicht 2 % bei K = {fmt_frac(t2)} (≈ {fmt(float(t2), 3)}).")


def verdict_hand_b(K: float) -> tuple[str, str]:
    import brg_hand as H
    K = Fraction(K).limit_denominator(1000)
    best = H.b_family_best(K)
    g_opt = min(l.value(K) for l in H.b_all_lines().values())
    parts = []
    for fam, label in (("bs", "Base-Stock"), ("ss", "(s,S)"), ("cap", "Capped (Kappe 1)")):
        prm, _tab, ln = best[fam]
        parts.append(f"{label} {fmt_pct(float(gap(ln.value(K), g_opt)), 2)}")
    return "info", (f"Handbeispiel B (verlorene Nachfrage, Lieferzeit 1), K = {fmt_k(float(K))}: gegen das Optimum aller 81 Politiken liegen die besten Regeln der Familien bei " + ", ".join(parts) +
                    ". Bei K = 0 gewinnt Capped, bei K = 1 gewinnt (s,S): die Reihenfolge kehrt sich um.")


def verdict_learning(cell: dict) -> tuple[str, str]:
    """Gelernte Politik in einer Zelle: Endstände je Zufalls-Seed, Median und Spannweite; nie „schlägt“, nur Zählung gegen Marke und beste Regel."""
    finals = sorted(cell["final_gaps"])
    n = len(finals)
    med = finals[n // 2] if n % 2 else 0.5 * (finals[n // 2 - 1] + finals[n // 2])
    refs = cell["ref_gaps"]
    two = min(refs["ss"], refs["cap"])
    below2 = sum(f < 2.0 for f in finals)
    below_two = sum(f < two for f in finals)
    below_ssc = sum(f < refs["ssc"] for f in finals)
    return "info", (f"Lieferzeit {cell['L']}, K = {fmt_k(cell['K'])}, {n} Zufalls-Seeds, {cell['updates']} Updates: Endstand im Median {fmt_pct(med)}, von {fmt_pct(finals[0])} bis {fmt_pct(finals[-1])} gegen die DP. "
                    f"Unter 2 %: {below2} von {n}; unter der besten Zweiparameterregel ({fmt_pct(two)}): {below_two} von {n}; unter (s,S) mit Kappe ({fmt_pct(refs['ssc'])}): {below_ssc} von {n}. "
                    "Der Endstand ist eine Momentaufnahme des schwankenden Verlaufs. Gilt für ein Verfahren, eine Einstellung, zwei Zellen.")
