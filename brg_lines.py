"""Kosten einer festen Politik als Gerade in den Fixkosten K: g(K) = c0 + c1 * K.

c0 sind die Kosten je Periode ohne Fixkosten, c1 der Anteil der Perioden mit Bestellung. Zwei Regeln kreuzen sich dort, wo ihre Geraden
gleich sind; die beste Politik je K ist die untere Hülle aller Geraden. Alle Funktionen rechnen mit `Fraction` exakt oder mit `float`."""

from typing import NamedTuple


class Line(NamedTuple):
    c0: object
    c1: object

    def value(self, K):
        return self.c0 + self.c1 * K


def line(c0, c1) -> Line:
    return Line(c0, c1)


def crossing(a: Line, b: Line):
    """K, bei dem beide Geraden gleich sind; None bei gleicher Steigung (parallel, kein einzelner Kreuzungspunkt)."""
    if a.c1 == b.c1:
        return None
    return (b.c0 - a.c0) / (a.c1 - b.c1)


def threshold(a: Line, b: Line, pct):
    """K, ab dem a um pct Prozent teurer ist als b: a.c0 + a.c1 K = (1 + pct/100) (b.c0 + b.c1 K). Das Verhältnis a/b muss mit K steigen (sonst None: dann
    gibt es kein „ab“, sondern ein „bis“); None auch bei negativem K (a liegt schon bei K = 0 darüber oder erreicht die Marke nie)."""
    if a.c1 * b.c0 - a.c0 * b.c1 <= 0:
        return None
    f = 1 + _ratio(pct)
    denom = a.c1 - f * b.c1
    if denom == 0:
        return None
    K = (f * b.c0 - a.c0) / denom
    return K if K >= 0 else None


def _ratio(pct):
    """pct / 100, exakt (Fraction), wenn pct ganzzahlig oder ein Bruch ist."""
    from fractions import Fraction
    if isinstance(pct, (int, Fraction)):
        return Fraction(pct) / 100
    return pct / 100


def lower_hull(lines, k_max):
    """Untere Hülle der Geraden auf 0 <= K <= k_max: Liste (K_ab, Line); die Gerade gilt ab K_ab bis zum nächsten Eintrag.
    Gleiche Geraden zählen einmal; bei Gleichstand an einer Stelle gewinnt die mit der kleineren Steigung (weniger Bestellungen)."""
    uniq = sorted({(l.c0, l.c1) for l in lines}, key=lambda t: (t[0], t[1]))
    cand = [Line(*t) for t in uniq]
    zero = type(cand[0].c0)(0) if cand else 0
    K = zero
    cur = min(cand, key=lambda l: (l.value(K), l.c1))
    hull = [(K, cur)]
    while True:
        # nächste Kreuzung rechts von K mit einer Geraden kleinerer Steigung
        nxt_K, nxt_line = None, None
        for l in cand:
            if l.c1 >= cur.c1:
                continue
            x = crossing(cur, l)
            if x is None or x <= K:
                continue
            if nxt_K is None or x < nxt_K or (x == nxt_K and l.c1 < nxt_line.c1):
                nxt_K, nxt_line = x, l
        if nxt_K is None or nxt_K > k_max:
            break
        K, cur = nxt_K, nxt_line
        hull.append((K, cur))
    return hull
