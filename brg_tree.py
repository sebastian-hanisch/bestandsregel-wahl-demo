"""Entscheidungsbaum: aus den Antworten auf sechs Fragen das Blatt (Regel, Zahl, Quelle).

Die Fragen, in dieser Reihenfolge:
  1. Mehrere Stufen in Reihe (Lager und Händler)?                           stufen: "eine" | "zwei"
  2. Verderbliche Ware, und welche Ausgaberegel?                            verderblich: "nein" | "fifo" | "lifo"
  3. Fehlmengen als Rückstand oder als verlorene Nachfrage?                  fehlmenge: "rueckstand" | "verloren"
  4. Wie groß sind die Fixkosten K gegen den Takt (Rückstand) bzw. welche Zelle (verloren)?   K (in Einheiten von h), Lieferzeit L, Marke
  5. Ist die Zustandszahl der exakten DP rechenbar?                         rechenbar: True | False
Jedes Blatt nennt eine Regel, die gemessene Zahl mit ihrer Voraussetzung und die Quelle. Zellen ohne Messung geben ein Blatt „nicht gemessen“ statt einer Zahl.
Die Blätter stehen in der Datei data/brg_karte.json bzw. in den README der Schwester-Demos; der Baum rechnet nichts neu."""

from typing import NamedTuple

import brg_constants as C
import brg_data as D
from brg_ladder import RULE_LABELS, rung


class Leaf(NamedTuple):
    id: str
    titel: str
    regel: str
    text: str
    gemessen: bool
    quelle: str


def _fmt(x, nd=2):
    return f"{x:.{nd}f}".replace(".", ",")


def _k(K):
    """K ohne überflüssige Nullen (1,3 statt 1,30)."""
    return f"{float(K):.2f}".rstrip("0").rstrip(".").replace(".", ",")


def _unmeasured(why: str) -> Leaf:
    return Leaf("nicht_gemessen", "Nicht gemessen", "keine Aussage", why, False, "Tabelle „Weiße Flecken“")


def leaf(antworten: dict) -> Leaf:
    """Blatt zu den Antworten (Schlüssel siehe Modul). Fehlende Schlüssel gelten als: eine Stufe, nicht verderblich, Rückstand, K = 0, Lieferzeit 0, Marke 2, rechenbar."""
    stufen = antworten.get("stufen", "eine")
    verderblich = antworten.get("verderblich", "nein")
    fehlmenge = antworten.get("fehlmenge", "rueckstand")
    K = float(antworten.get("K", 0.0))
    L = int(antworten.get("L", 0))
    marke = float(antworten.get("marke", C.DEFAULT_MARKE))
    rechenbar = bool(antworten.get("rechenbar", True))

    if stufen == "zwei":
        e = {x["id"]: x for x in D.uebernommen(5)}
        txt = (f"Base-Stock je Stufe auf dem Echelon-Bestand (Bestand der Stufe plus alles, was hinter ihr liegt). {e['s5_echelon']['aussage']} "
               f"{e['s5_lokal']['aussage']} Fixkosten bei zwei Stufen sind nicht gemessen.")
        return Leaf("zwei_stufen", "Zwei Stufen in Reihe", "Echelon-Base-Stock", txt, K == 0.0, "Stück 5, lager-und-haendler-demo")

    if verderblich in ("fifo", "lifo"):
        e = {x["id"]: x for x in D.uebernommen(4)}
        if verderblich == "fifo":
            key = "s4_fifo_l0" if L == 0 else "s4_fifo_l1"
            if L > 1:
                return _unmeasured("Verderbliche Ware ist nur für Lieferzeit 0 und 1 gemessen.")
            regel = "Base-Stock auf dem Gesamtbestand"
        else:
            key = "s4_lifo_l0" if L == 0 else "s4_lifo_l1"
            if L > 1:
                return _unmeasured("Verderbliche Ware ist nur für Lieferzeit 0 und 1 gemessen.")
            regel = "Base-Stock auf dem Gesamtbestand, je nach Verderbkosten und Haltbarkeit nicht genug: dann Altersregel oder Tabelle nach dem Alter"
        txt = e[key]["aussage"] + " " + ("Fixkosten sind bei verderblicher Ware nicht gemessen." if K > 0 else "")
        return Leaf("verderblich_" + verderblich, f"Verderbliche Ware, {verderblich.upper()}-Ausgabe, Lieferzeit {L}", regel, txt.strip(), K == 0.0 and L <= 1,
                    "Stück 4, verderbliche-ware-demo")

    if fehlmenge == "rueckstand":
        if L not in C.B_L:
            return _unmeasured("Rückstand ist für Lieferzeit 0 bis 5 gemessen.")
        cell = D.backorder_cell(9, L, round(K, 2))
        if cell is None:
            return _unmeasured("Rückstand ist für die K-Werte des Rasters gemessen (0 bis 4 in Schritten von 0,05, dann 5, 7,5, 10, 15, 20, 30).")
        gaps = D.backorder_gaps(cell)
        r = rung(gaps, marke)
        takt = D.eoq_takt(K)
        if r.rung == 1:
            return Leaf("rueckstand_base_stock", "Rückstand, Base-Stock reicht", RULE_LABELS["bs"],
                        f"Bei Lieferzeit {L} und K = {_k(K)} liegt Base-Stock {_fmt(gaps['bs'])} % über der DP (Marke {_fmt(marke, 0)} %; Losgrößen-Takt {_fmt(takt)} Perioden). "
                        "Im Modell der Demo (p/h = 9, Mittel 3).", True, "Karte, Rückstand")
        return Leaf("rueckstand_ss", "Rückstand, (s,S)", RULE_LABELS["ss"],
                    f"Bei Lieferzeit {L} und K = {_k(K)} liegt Base-Stock {_fmt(gaps['bs'])} % über der DP (Marke {_fmt(marke, 0)} %; Losgrößen-Takt {_fmt(takt)} Perioden). "
                    f"Die (s,S)-Regel mit s = {cell['s_dp']}, S = {cell['S_dp']} hat die Form der DP-Politik (Bestellanteil der DP {_fmt(cell['order_share_dp'] * 100, 0)} % der Perioden). "
                    "Im Modell der Demo (p/h = 9, Mittel 3).", True, "Karte, Rückstand")

    # verlorene Nachfrage
    if L < 1:
        return _unmeasured("Bei verlorener Nachfrage ist Lieferzeit 0 in diesem Zeitablauf (Ankunft nach der Nachfrage der Periode) nicht vorgesehen.")
    cell = D.lost_cell(L, round(K, 2))
    if (cell is None and K == 0.0 and L >= 5) or (not rechenbar and K == 0.0):
        return Leaf("verloren_k0_jenseits", "Verlorene Nachfrage ohne Fixkosten, große Lieferzeit", RULE_LABELS["cap"],
                    "Ohne Fixkosten (Stück 6): " + D.uebernommen(6)[0]["aussage"] + " Wo die DP nicht gerechnet wird, misst man gegen die beste Regel, nicht gegen das Optimum; "
                    "das unterschätzt die Lücke zum Optimum um etwa deren eigene Lücke (Faktoren, nicht Punkte).", False, "Stück 6, dp-grenze-demo")
    if cell is None:
        return _unmeasured("Verlorene Nachfrage mit Fixkosten ist für Lieferzeit 1 bis 3 mit K = 0, 0,5, 1, 1,5, 2, 3, 5, 10 und für Lieferzeit 4 mit K = 0, 1, 2, 5, 10 gemessen.")
    gaps = D.lost_gaps(cell)
    r = rung(gaps, marke)
    base = (f"Lieferzeit {L}, K = {_k(K)}, Marke {_fmt(marke, 0)} %: Base-Stock {_fmt(gaps['bs'])} %, (s,S) {_fmt(gaps['ss'])} %, Capped {_fmt(gaps['cap'])} %, "
            f"(s,S) mit Kappe {_fmt(gaps['ssc'])} % über der DP.")
    if r.rung == 4:
        if rechenbar:
            return Leaf("verloren_dp", "Keine einfache Regel unter der Marke: exakte DP", "exakte DP", base + " Die DP ist hier rechenbar (Zustände: " + f"{cell['states']:,}".replace(",", ".") + ").",
                        True, "Karte, verlorene Nachfrage")
        lern = D.lernen_cell(4, 5.0)
        lo, hi = min(lern["final_gaps"]), max(lern["final_gaps"])
        return Leaf("verloren_gelernt", "Keine einfache Regel unter der Marke: gelernte Politik", "gelernte Politik", base + " Angenommen, die DP wäre hier nicht rechenbar: dann bliebe eine gelernte Politik. Sie "
                    f"(Politikgradient) erreichte in der Zelle Lieferzeit 4, K = 5 (dort ist die DP gerechnet) Endstände von +{_fmt(lo)} bis +{_fmt(hi)} % (fünf Zufalls-Seeds).", True, "Karte, Lernläufe")
    names = {1: "Base-Stock", 2: RULE_LABELS[r.rule], 3: RULE_LABELS["ssc"]}
    return Leaf(f"verloren_stufe{r.rung}", f"Verlorene Nachfrage, Stufe {r.rung}", names[r.rung], base + f" Die kleinste Stufe unter der Marke ist Stufe {r.rung}.", True, "Karte, verlorene Nachfrage")
