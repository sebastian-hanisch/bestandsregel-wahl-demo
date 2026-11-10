"""Die beiden Handbeispiele in exakten Brüchen (Mini-Instanzen, vollständige Aufzählung aller Politiken).

Nachfrage 0 / 1 / 2 mit den Wahrscheinlichkeiten 1/4, 1/2, 1/4, h = 1, p = 4, Bestellkosten je Stück 0, Fixkosten K je Bestellung.

Beispiel A: Rückstand, Lieferzeit 0. Zustand = Bestandsposition z (-3 bis 2) vor der Bestellung, Aktion = Niveau y >= z nach der Bestellung (y <= 2).
Beispiel B: verlorene Nachfrage, Lieferzeit 1 (die Bestellung kommt nach der Nachfrage der Periode an, die Position ist der Bestand). Bestand 0 bis 3
(Rest darüber verfällt), Bestellmenge 0 bis 2, x' = min((x - D)+ + a, 3).

Die Kosten einer festen Politik sind eine Gerade in K (siehe brg_lines): c0 = erwartete Periodenkosten ohne Fixkosten, c1 = Anteil der Perioden mit Bestellung,
beide aus der stationären Verteilung der von z = 0 bzw. x = 0 erreichbaren Zustände, per Gauß-Elimination in Brüchen."""

import itertools
from fractions import Fraction as F
from functools import lru_cache

from brg_lines import Line

DEMAND = ((0, F(1, 4)), (1, F(1, 2)), (2, F(1, 4)))
H, P = F(1), F(4)

A_ZMIN, A_YMAX = -3, 2
A_STATES = tuple(range(A_ZMIN, A_YMAX + 1))
B_XMAX, B_AMAX = 3, 2
B_STATES = tuple(range(B_XMAX + 1))


def _solve(matrix, rhs):
    """Gauß-Elimination in Brüchen; None, wenn die Matrix singulär ist."""
    n = len(matrix)
    m = [row[:] + [rhs[i]] for i, row in enumerate(matrix)]
    for c in range(n):
        piv = next((r for r in range(c, n) if m[r][c] != 0), None)
        if piv is None:
            return None
        m[c], m[piv] = m[piv], m[c]
        pv = m[c][c]
        m[c] = [v / pv for v in m[c]]
        for r in range(n):
            if r != c and m[r][c] != 0:
                f = m[r][c]
                m[r] = [a - f * b for a, b in zip(m[r], m[c])]
    return [m[i][n] for i in range(n)]


def stationary(next_states, start):
    """Stationäre Verteilung auf der von `start` erreichbaren Menge. next_states: Zustand -> Liste (Folgezustand, Wahrscheinlichkeit).
    Rückgabe (Zustände, Verteilung) oder None, wenn es mehrere abgeschlossene Klassen gibt."""
    reach, todo = {start}, [start]
    while todo:
        s = todo.pop()
        for s2, _ in next_states[s]:
            if s2 not in reach:
                reach.add(s2)
                todo.append(s2)
    states = sorted(reach)
    n = len(states)
    idx = {s: i for i, s in enumerate(states)}
    a = [[F(0)] * n for _ in range(n)]
    for s in states:
        for s2, pr in next_states[s]:
            a[idx[s2]][idx[s]] += pr
    for i in range(n):
        a[i][i] -= 1
    a[n - 1] = [F(1)] * n
    pi = _solve(a, [F(0)] * (n - 1) + [F(1)])
    if pi is None or any(v < 0 for v in pi):
        return None
    return states, pi


# ---------------------------------------------------------------- Beispiel A: Rückstand, Lieferzeit 0
def a_cost(y):
    """Erwartete Periodenkosten bei Niveau y nach der Bestellung: E[h (y - D)+ + p (D - y)+]."""
    return sum(pr * (H * max(y - d, 0) + P * max(d - y, 0)) for d, pr in DEMAND)


def a_line(policy):
    """policy: Zustand z -> Niveau y. Gerade (c0, c1) oder None."""
    nxt = {z: [(max(policy[z] - d, A_ZMIN), pr) for d, pr in DEMAND] for z in A_STATES}
    sol = stationary(nxt, 0)
    if sol is None:
        return None
    states, pi = sol
    c0 = sum(p_ * a_cost(policy[z]) for z, p_ in zip(states, pi))
    c1 = sum(p_ for z, p_ in zip(states, pi) if policy[z] > z)
    return Line(c0, c1)


def a_policy_sS(s, S):
    """Bestelle bis S, wenn z <= s, sonst nicht."""
    return {z: (S if z <= s else z) for z in A_STATES}


@lru_cache(maxsize=1)
def a_all_lines():
    """Alle 720 Politiken (Niveau y von z bis 2 je Zustand): Wörterbuch Niveau-Tupel -> Line."""
    out = {}
    for ys in itertools.product(*[range(z, A_YMAX + 1) for z in A_STATES]):
        ln = a_line(dict(zip(A_STATES, ys)))
        if ln is not None:
            out[ys] = ln
    return out


def a_rule_lines():
    """Die beiden Regeln des Beispiels: Base-Stock S = 2 (s = 1) und (s,S) = (0,2)."""
    return {"bs": a_line(a_policy_sS(1, 2)), "ss": a_line(a_policy_sS(0, 2))}


# ---------------------------------------------------------------- Beispiel B: verlorene Nachfrage, Lieferzeit 1
def b_cost(x):
    """Erwartete Periodenkosten bei Bestand x zu Beginn: E[h (x - D)+ + p (D - x)+]."""
    return sum(pr * (H * max(x - d, 0) + P * max(d - x, 0)) for d, pr in DEMAND)


def b_line(policy):
    """policy: Bestand x -> Bestellmenge a (Tupel der Länge 4). Gerade oder None."""
    nxt = {x: [(min(max(x - d, 0) + policy[x], B_XMAX), pr) for d, pr in DEMAND] for x in B_STATES}
    sol = stationary(nxt, 0)
    if sol is None:
        return None
    states, pi = sol
    c0 = sum(p_ * b_cost(x) for x, p_ in zip(states, pi))
    c1 = sum(p_ for x, p_ in zip(states, pi) if policy[x] > 0)
    return Line(c0, c1)


def b_policy(family, *params):
    """Regeln als Bestelltabelle a(x): 'bs' (S), 'ss' (s, S), 'cap' (S, Kappe)."""
    if family == "bs":
        (S,) = params
        return tuple(min(max(S - x, 0), B_AMAX) for x in B_STATES)
    if family == "ss":
        s, S = params
        return tuple(min(max(S - x, 0), B_AMAX) if x <= s else 0 for x in B_STATES)
    if family == "cap":
        S, cap = params
        return tuple(min(max(S - x, 0), cap) for x in B_STATES)
    raise ValueError(family)


@lru_cache(maxsize=1)
def b_all_lines():
    """Alle 3^4 = 81 Politiken (Bestellmenge 0 bis 2 je Bestand 0 bis 3): Wörterbuch Tabelle -> Line."""
    out = {}
    for pol in itertools.product(range(B_AMAX + 1), repeat=len(B_STATES)):
        ln = b_line(pol)
        if ln is not None:
            out[pol] = ln
    return out


def b_family_best(K):
    """Je Regelfamilie die beste Politik bei K (Bestell-Tabelle, Line); die Familien durchsuchen ihre Parameter vollständig:
    bs: S = 1..5; ss: s = 0..3, S = s+1..5; cap: S = 1..5 mit Kappe 1."""
    fams = {
        "bs": [((S,), b_policy("bs", S)) for S in range(1, 6)],
        "ss": [((s, S), b_policy("ss", s, S)) for s in range(0, 4) for S in range(s + 1, 6)],
        "cap": [((S, 1), b_policy("cap", S, 1)) for S in range(1, 6)],
    }
    lines = b_all_lines()
    out = {}
    for fam, cands in fams.items():
        best = min(((lines[tab].value(K), prm, tab) for prm, tab in cands), key=lambda t: t[0])
        out[fam] = (best[1], best[2], lines[best[2]])
    return out
