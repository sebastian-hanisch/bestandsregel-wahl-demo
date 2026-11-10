"""Die Leiter der Regeln und das Lesen einer Zelle.

Stufe 1  Base-Stock (ein Parameter)
Stufe 2  (s,S) oder Capped Base-Stock (zwei Parameter; die bessere von beiden)
Stufe 3  (s,S) mit Kappe (drei Parameter)
Stufe 4  keine einfache Regel unter der Marke: exakte DP, solange sie rechenbar ist, sonst eine gelernte Politik

Die Stufe einer Zelle ist die erste Stufe, deren beste Regel unter der Marke liegt (Lücke in Prozent der DP-Kosten, echt kleiner als die Marke)."""

from typing import NamedTuple

RULE_LABELS = {"bs": "Base-Stock", "ss": "(s,S)", "cap": "Capped Base-Stock", "ssc": "(s,S) mit Kappe"}
RUNG_NAMES = {1: "Stufe 1: Base-Stock (ein Parameter)", 2: "Stufe 2: (s,S) oder Capped Base-Stock (zwei Parameter)",
              3: "Stufe 3: (s,S) mit Kappe (drei Parameter)", 4: "Stufe 4: keine einfache Regel unter der Marke"}


class Rung(NamedTuple):
    rung: int
    rule: str | None   # Schlüssel der Regel, die die Stufe erreicht; None bei Stufe 4
    gap: float | None  # Lücke dieser Regel in Prozent; None bei Stufe 4


def rung(gaps: dict, marke: float) -> Rung:
    """gaps: Lücken in Prozent mit den Schlüsseln 'bs', 'ss', 'cap', 'ssc' (fehlt ein Schlüssel oder ist er None, gibt es die Regel in dieser Zelle nicht).
    Marke <= 0: keine Lücke liegt echt darunter, also Stufe 4. Bei Gleichstand der Zweiparameterregeln gewinnt (s,S)."""
    if marke <= 0:
        return Rung(4, None, None)
    g = {k: v for k, v in gaps.items() if v is not None}
    if "bs" in g and g["bs"] < marke:
        return Rung(1, "bs", g["bs"])
    two = [(g[k], k) for k in ("ss", "cap") if k in g and g[k] < marke]
    if two:
        v, k = min(two, key=lambda t: (t[0], 0 if t[1] == "ss" else 1))
        return Rung(2, k, v)
    if "ssc" in g and g["ssc"] < marke:
        return Rung(3, "ssc", g["ssc"])
    return Rung(4, None, None)


def best_two_parameter(gaps: dict):
    """(Lücke, Schlüssel) der besseren Zweiparameterregel ((s,S) oder Capped); None, wenn keine vorhanden."""
    c = [(gaps[k], k) for k in ("ss", "cap") if gaps.get(k) is not None]
    return min(c, key=lambda t: (t[0], 0 if t[1] == "ss" else 1)) if c else None


def distribution(cells_gaps, marke: float) -> dict:
    """Zahl der Zellen je Stufe 1 bis 4 für eine Liste von gaps-Wörterbüchern."""
    out = {1: 0, 2: 0, 3: 0, 4: 0}
    for gaps in cells_gaps:
        out[rung(gaps, marke).rung] += 1
    return out
