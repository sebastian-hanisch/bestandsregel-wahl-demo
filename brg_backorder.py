"""Rückstand mit Lieferzeit L und Fixkosten K je Bestellung: Rechnung auf der Bestandsposition.

Zustand ist die Bestandsposition z (Bestand plus Bestelltes minus Rückstand) vor der Bestellung. Die Kosten einer Bestellung bis zum Niveau y fallen erst
L + 1 Perioden später an: im Mittel G(y) = E[h (y - D)+ + p (D - y)+] mit D = Summe der Nachfrage von L + 1 Perioden. Das ist eine Rechenidentität
im Modell dieser Demo (gegen die Rechnung mit dem vollen Pipeline-Zustand geprüft, tests/test_oracle_voll.py), kein Satz aus der Literatur.

Zwei Wege: relative Wertiteration (optimale Politik) und exakte Auswertung fester Politiken über die stationäre Verteilung. Die Bestellgrenze Q ist die
höchste Bestellmenge je Periode; die Randmasse (Zeitanteil an Gitterrändern und an der Bestellgrenze) wird mit ausgegeben."""

from dataclasses import dataclass

import numpy as np

import brg_constants as C
from brg_demand import poisson_pmf
from brg_gap import clip_noise, gap


@dataclass(frozen=True)
class Settings:
    L: int = 1
    K: float = 0.0
    h: float = 1.0
    p: float = 9.0
    mean: float = 3.0
    dmax: int = C.B_DMAX
    Q: int = C.B_Q
    zmin: int = C.B_ZMIN
    ymax: int = C.B_YMAX


class Model:
    def __init__(self, st: Settings):
        self.st = st
        self.z = np.arange(st.zmin, st.ymax + 1)
        self.n = len(self.z)
        pd = poisson_pmf(st.mean, st.dmax)
        self.pd = pd
        dn = np.array([1.0])
        for _ in range(st.L + 1):
            dn = np.convolve(dn, pd)
        self.dn = dn
        k = np.arange(len(dn))
        y = self.z[:, None]
        # G[y]: erwartete Kosten der Nachfrage über L + 1 Perioden bei Niveau y
        self.G = (dn[None, :] * (st.h * np.maximum(y - k[None, :], 0) + st.p * np.maximum(k[None, :] - y, 0))).sum(axis=1)
        # B[i, j] = P(y_i - d = z_j); Masse unterhalb zmin liegt auf zmin
        B = np.zeros((self.n, self.n))
        for i, yy in enumerate(self.z):
            for d, pr in enumerate(pd):
                B[i, max(yy - d, st.zmin) - st.zmin] += pr
        self.B = B

    # ---- optimale Politik: relative Wertiteration
    def rvi(self, tol=1e-11, maxit=50000):
        """Rückgabe (g, q): Kosten je Periode und Bestellmenge je Position (Bezugszustand z = 0)."""
        n = self.n
        h = np.zeros(n)
        ref = -self.st.zmin
        for it in range(maxit):
            W = self.G + self.B @ h
            v = self._backup(W)[0]
            g_new = v[ref]
            h_new = v - g_new
            diff = np.max(np.abs(h_new - h))
            h, g = h_new, g_new
            if diff < tol:
                break
        W = self.G + self.B @ h
        v, q = self._backup(W)
        return float(g), q

    def _backup(self, W):
        st, n = self.st, self.n
        v = W.copy()
        q = np.zeros(n, dtype=int)
        for i in range(n):
            hi = min(i + st.Q, n - 1)
            if hi > i:
                seg = W[i + 1:hi + 1]
                j = int(np.argmin(seg))
                c = st.K + seg[j]
                if c < v[i] - 1e-12:
                    v[i] = c
                    q[i] = j + 1
        return v, q

    # ---- feste Politiken: exakte Auswertung
    def evaluate(self, q):
        """Kosten je Periode einschließlich Fixkosten und stationäre Verteilung der Position."""
        y_idx = np.arange(self.n) + q
        P = self.B[y_idx]
        c = self.G[y_idx] + self.st.K * (q > 0)
        a = np.eye(self.n) - P.T
        a[-1, :] = 1.0
        b = np.zeros(self.n)
        b[-1] = 1.0
        pi = np.linalg.solve(a, b)
        pi = np.maximum(pi, 0.0)
        pi = pi / pi.sum()
        return float(pi @ c), pi

    def pol_sS(self, s, S):
        """Bestelle bis S, wenn die Position höchstens s ist, höchstens Q Stück, Niveau höchstens ymax."""
        z = self.z
        q = np.where(z <= s, np.minimum(S - z, self.st.Q), 0)
        q = np.where(z + q > self.st.ymax, self.st.ymax - z, q)
        return np.maximum(q, 0).astype(int)

    def pol_base(self, S):
        return self.pol_sS(S - 1, S)

    def best_base_stock(self, srange=None):
        """Bestes Niveau S (vollständige Suche im Bereich B_S_RANGE) und seine Kosten."""
        if srange is None:
            srange = range(C.B_S_RANGE[0], C.B_S_RANGE[1])
        best = (1e18, None)
        for S in srange:
            g, _ = self.evaluate(self.pol_base(S))
            if g < best[0]:
                best = (g, S)
        return best

    def all_sS(self, s_lo=-25, S_hi=None):
        """Aufzählung aller (s,S) mit s < S: Wörterbuch (s, S) -> Kosten (Orakel für die Struktur der DP-Politik)."""
        S_hi = self.st.ymax - 5 if S_hi is None else S_hi
        out = {}
        for S in range(s_lo + 1, S_hi + 1):
            for s in range(s_lo, S):
                out[(s, S)] = self.evaluate(self.pol_sS(s, S))[0]
        return out

    # ---- Struktur der DP-Politik
    def structure(self, q, pi, thr=1e-12):
        """Rückgabe Wörterbuch: s (höchste bestellende Position), S (Zielniveau), pure_ss (reine (s,S)-Form auf den erreichten Positionen),
        qcap (Zeitanteil an der Bestellgrenze), edge_lo, edge_hi (Zeitanteil an den Gitterrändern)."""
        z = self.z
        rec = pi > thr
        order = q > 0
        if not order[rec].any():
            return dict(s=None, S=None, pure_ss=True, qcap=0.0, edge_lo=float(pi[0]), edge_hi=float(pi[-1]))
        s = int(z[rec & order].max())
        tgt = (z + q)[rec & order]
        vals, cnt = np.unique(tgt, return_counts=True)
        S = int(vals[cnt.argmax()])
        pure = bool(len(vals) == 1 and np.all(order[rec & (z <= s)]) and not order[rec & (z > s)].any())
        return dict(s=s, S=S, pure_ss=pure, qcap=float(pi[q == self.st.Q].sum()), edge_lo=float(pi[0]), edge_hi=float(pi[-1]))


def solve(L: int, K: float, p_h: float) -> dict:
    """Eine Zelle des Rückstandsrasters: Kosten der DP, bester Base-Stock, (s,S) der DP, Bestellanteil, Randmassen.

    gap_bs: Lücke des besten Base-Stock in Prozent der DP-Kosten. gap_ss: Lücke der (s,S)-Regel aus den Parametern der DP-Politik (exakt bewertet;
    0 bis auf Rechenrauschen, wenn die DP-Politik auf den erreichten Positionen reine (s,S)-Form hat)."""
    m = Model(Settings(L=L, K=float(K), p=float(p_h)))
    g, q = m.rvi()
    gd, pi = m.evaluate(q)
    assert abs(gd - g) < 1e-7, (L, K, p_h, g, gd)
    st = m.structure(q, pi)
    gb, Sb = m.best_base_stock()
    qb = m.pol_base(Sb)
    _, pib = m.evaluate(qb)
    if st["s"] is None:
        g_ss = gd
    else:
        g_ss = m.evaluate(m.pol_sS(st["s"], st["S"]))[0]
    return dict(
        L=L, K=float(K), p_h=float(p_h), g=g, gb=gb, Sb=Sb, gap_bs=gap(gb, g), gap_ss=clip_noise(gap(g_ss, g)),
        s=st["s"], S=st["S"], pure_ss=st["pure_ss"], pord=float(pi[q > 0].sum()),
        edge_lo=max(st["edge_lo"], float(pib[0])), edge_hi=max(st["edge_hi"], float(pib[-1])),
        qcap=max(st["qcap"], float(pib[qb == m.st.Q].sum())),
    )
