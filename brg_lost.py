"""Verlorene Nachfrage mit Lieferzeit L und Fixkosten K je Bestellung: exakte Rückwärtsrechnung als Tensor-DP, Regeln, Parametersuche.

Zustand (x, p1, ..., p_{L-1}) = Bestand und Pipeline; Aktion a = Bestellmenge 0..Q, sie kommt nach L Perioden an. Bestandsposition IP = x + Summe der Pipeline.
Zeitfolge je Periode: Entscheidung a, Nachfrage d, Kosten h (x - d)+ + p (d - x)+ (+ K bei a > 0), danach x' = min((x - d)+ + p1, XM), die Pipeline rückt auf:
(p2, ..., p_{L-1}, a). Bei L = 1 ist p1 = a.

Rechenweg: Mit Kern[(x, p1), y] = P(y = min((x - d)+ + p1, XM)) und G_a = h[:, a::(Q+1)] gilt T_a = Kern @ G_a (eine dichte Matrixmultiplikation je Aktion) statt einer
dünnen Übergangsmatrix je Aktion. Die Nachfrage wirkt nur auf (x, p1), die Pipeline schiebt sich nur. Zustandsindex = x * (Q+1)^(L-1) + Pipeline-Index, p1 höchstwertig.

Regeln auf der Bestandsposition: Base-Stock S, (s,S), Capped Base-Stock (Bestellmenge höchstens Kappe), (s,S) mit Kappe. Die Parameter sind ganzzahlig und werden
per Nachbarschaftssuche (+-1 je Parameter) aus mehreren Startpunkten gesucht und exakt bewertet: sie sind also obere Schranken der Lücke der Regelfamilie,
kein Beweis des Optimums der Familie. Für kleine Lieferzeiten prüft die vollständige Aufzählung die Suche (`enumerate_families`)."""

import time

import numpy as np

import brg_constants as C
from brg_demand import poisson_pmf
from brg_gap import clip_noise, gap


class LostSales:
    def __init__(self, L, K=0.0, mean=C.MEAN, h=C.H, p=C.V_PH * C.H, Q=C.V_Q, XM=C.V_XM, DMAX=C.V_DMAX):
        assert L >= 1, "Lieferzeit 0 ist bei verlorener Nachfrage in diesem Zeitablauf (Ankunft nach der Nachfrage der Periode) nicht vorgesehen"
        self.L, self.Kfix = L, float(K)
        self.mean, self.h, self.p, self.Q, self.XM, self.DMAX = mean, h, p, Q, XM, DMAX
        self.pd = poisson_pmf(mean, DMAX)
        self.d = np.arange(DMAX + 1)
        self.X, self.P = XM + 1, Q + 1
        self.A = self.P
        self.Pn = self.P ** (L - 1)                     # Pipeline-Zustände
        self.M = self.P ** (L - 2) if L >= 2 else 1     # Rest der Pipeline nach p1
        self.S = self.X * self.Pn                       # Zustandszahl
        x = np.arange(self.X)
        # erwartete Periodenkosten je Bestand
        self.ec = np.array([(self.pd * (h * np.maximum(xx - self.d, 0) + p * np.maximum(self.d - xx, 0))).sum() for xx in x])
        kern = np.zeros((self.X * self.P, self.X))
        for xx in range(self.X):
            for p1 in range(self.P):
                for dd, pr in zip(self.d, self.pd):
                    kern[xx * self.P + p1, min(max(xx - dd, 0) + p1, XM)] += pr
        self.K = kern
        ps = np.zeros(1, dtype=np.int64)
        for _ in range(L - 1):
            ps = (ps[:, None] + np.arange(self.P)[None, :]).reshape(-1)
        self.pipesum = ps
        self.IP = x[:, None] + ps[None, :]              # (X, Pn)

    # ---- Wertiteration mit Fixkosten
    def _T(self, hh, a):
        """T_a[x, pipeidx] = sum_d pd[d] * h[x', pipe'(a)]; hh hat die Form (X, Pn)."""
        if self.L == 1:
            return (self.K[a::self.P] @ hh[:, 0])[:, None]
        G = hh[:, a::self.P]
        return (self.K @ G).reshape(self.X, self.P, self.M).reshape(self.X, self.Pn)

    def rvi(self, tol=1e-9, maxit=20000):
        """Relative Wertiteration (Bezugszustand x = 0, leere Pipeline). Rückgabe (g, Politik (X, Pn), Wertetabelle, Iterationen)."""
        hh = np.zeros((self.X, self.Pn))
        ecb = self.ec[:, None]
        for it in range(maxit):
            v, pol = None, None
            for a in range(self.A):
                q = ecb + self.Kfix * (a > 0) + self._T(hh, a)
                if v is None:
                    v, pol = q, np.zeros(q.shape, dtype=np.int16)
                else:
                    m = q < v - 1e-12
                    v = np.where(m, q, v)
                    pol[m] = a
            g = v[0, 0]
            hn = v - g
            diff = np.max(np.abs(hn - hh))
            hh = hn
            if diff < tol:
                break
        return float(g), pol, hh, it + 1

    # ---- exakte Auswertung einer festen Politik
    def stationary(self, pol, tol=1e-13, maxit=400000):
        """Stationäre Verteilung der trägen Kette (die Hälfte der Masse bleibt stehen, das macht sie aperiodisch); pol (X, Pn) Aktionen."""
        pi = np.full((self.X, self.Pn), 1.0 / self.S)
        masks = [(pol == a) for a in range(self.A)]
        used = [a for a in range(self.A) if masks[a].any()]
        it = 0
        for it in range(maxit):
            new = np.zeros_like(pi)
            for a in used:
                mass = np.where(masks[a], pi, 0.0)
                if self.L == 1:
                    new[:, 0] += self.K[a::self.P].T @ mass[:, 0]
                else:
                    mm = mass.reshape(self.X * self.P, self.M)
                    new[:, a::self.P] += self.K.T @ mm
            new = 0.5 * pi + 0.5 * new
            if np.abs(new - pi).sum() < tol:
                pi = new
                break
            pi = new
        pi /= pi.sum()
        return pi, it + 1

    def evaluate(self, pol, tol=1e-12):
        """Kosten je Periode einschließlich Fixkosten; Rückgabe (g, Verteilung, Bestellanteil)."""
        pi, _ = self.stationary(pol, tol=tol)
        p_order = float(pi[pol > 0].sum())
        g = float((pi.sum(axis=1) * self.ec).sum()) + self.Kfix * p_order
        return g, pi, p_order

    def edge_mass(self, pi):
        """Zeitanteil am Bestandsrand x = XM."""
        return float(pi[self.XM].sum())

    # ---- Regeln als Politik-Tabellen
    def pol_ss(self, s, S, cap=None):
        """Bestelle bis S, wenn die Bestandsposition höchstens s ist (sonst nicht), höchstens `cap` Stück (Standard: Bestellgrenze)."""
        cap = self.Q if cap is None else min(cap, self.Q)
        q = np.clip(S - self.IP, 0, cap)
        return np.where(self.IP <= s, q, 0).astype(np.int16)

    def pol_bs(self, S):
        return self.pol_ss(S - 1, S)

    def pol_capped(self, S, cap):
        return self.pol_ss(S - 1, S, cap)

    # ---- Parametersuche
    def search(self, start, params_to_pol, bounds, cache, maxrounds=40):
        """Nachbarschaftssuche über ganzzahlige Parameter (+-1 je Koordinate), exakt bewertet. Rückgabe (Kosten, Parameter)."""
        def val(t):
            if t not in cache:
                cache[t] = self.evaluate(params_to_pol(t))[0]
            return cache[t]

        cur = tuple(start)
        gcur = val(cur)
        for _ in range(maxrounds):
            best, gbest = cur, gcur
            for i in range(len(cur)):
                for dlt in (-1, 1):
                    t = list(cur)
                    t[i] += dlt
                    if not (bounds[i][0] <= t[i] <= bounds[i][1]):
                        continue
                    t = tuple(t)
                    gt = val(t)
                    if gt < gbest - 1e-12:
                        best, gbest = t, gt
            if best == cur:
                break
            cur, gcur = best, gbest
        return gcur, cur

    def best_rules(self, smax=C.V_SMAX):
        """Beste Parameter der vier Regelfamilien (Base-Stock vollständig über S, die übrigen per Suche aus mehreren Startpunkten).
        Rückgabe Wörterbuch Familie -> (Kosten, Parameter)."""
        Q = self.Q
        cache_bs = {}
        for S in range(2, smax + 1):
            cache_bs[(S,)] = self.evaluate(self.pol_bs(S))[0]
        Sb = min(cache_bs, key=cache_bs.get)[0]
        gbs = cache_bs[(Sb,)]

        cache_ss = {}
        best_ss = (1e18, None)
        for ds, dS in ((1, 0), (3, 1), (5, 3), (8, 5), (11, 8)):
            s0 = max(Sb - ds, 0)
            S0 = max(Sb + dS, s0 + 1)
            res = self.search((s0, S0), lambda t: self.pol_ss(t[0], t[1]), [(0, smax - 1), (1, smax)], cache_ss)
            if res[0] < best_ss[0]:
                best_ss = res

        cache_cap = {}
        best_cap = (1e18, None)
        for dS, cap0 in ((0, 4), (1, 3), (2, 2), (0, 6), (-1, 5)):
            res = self.search((Sb + dS, cap0), lambda t: self.pol_capped(t[0], t[1]), [(2, smax), (1, Q)], cache_cap)
            if res[0] < best_cap[0]:
                best_cap = res
        Sc, capc = best_cap[1]

        cache_ssc = {}
        best_ssc = (1e18, None)
        ss, SS = best_ss[1]
        starts = [(ss, SS, Q), (Sc - 1, Sc, capc), (ss, SS, max(capc, 3)), (max(ss - 2, 0), SS, 6), (max(ss - 1, 0), SS + 1, 8), (max(ss - 2, 0), SS - 1, 4)]
        for st_ in starts:
            st_ = (min(max(st_[0], 0), smax - 1), min(max(st_[1], st_[0] + 1), smax), min(max(st_[2], 1), Q))
            res = self.search(st_, lambda t: self.pol_ss(t[0], t[1], t[2]), [(0, smax - 1), (1, smax), (1, Q)], cache_ssc)
            if res[0] < best_ssc[0]:
                best_ssc = res
        return {"bs": (gbs, (Sb,)), "ss": best_ss, "cap": best_cap, "ssc": best_ssc}

    def enumerate_families(self, smax=C.V_SMAX):
        """Vollständige Aufzählung der Zweiparameterfamilien: bestes (s,S) mit S <= smax und bestes Capped (S, Kappe). Rückgabe {'ss': (g, (s,S)), 'cap': (g, (S,k))}."""
        best_ss, best_cap = (1e18, None), (1e18, None)
        for S_ in range(2, smax + 1):
            for s_ in range(0, S_):
                g = self.evaluate(self.pol_ss(s_, S_))[0]
                if g < best_ss[0]:
                    best_ss = (g, (s_, S_))
            for c_ in range(1, self.Q + 1):
                g = self.evaluate(self.pol_capped(S_, c_))[0]
                if g < best_cap[0]:
                    best_cap = (g, (S_, c_))
        return {"ss": best_ss, "cap": best_cap}


def solve_cell(L: int, K: float, enumerate_check: bool = False) -> dict:
    """Eine Zelle der verlorenen Nachfrage: DP, vier Regeln mit Lücke und Parametern, Bestellanteil der DP, Randmassen, optional Aufzählung zur Kontrolle."""
    t0 = time.time()
    m = LostSales(L, K)
    g, pol, _hh, _it = m.rvi()
    gd, pi, po = m.evaluate(pol)
    assert abs(gd - g) < 1e-7, (L, K, g, gd)
    rules = m.best_rules()
    cell = dict(L=L, K=float(K), states=m.S, reachable=int((pi > 1e-9).sum()), g=g,
                gaps={k: clip_noise(gap(v[0], g)) for k, v in rules.items()},
                params={k: list(v[1]) for k, v in rules.items()},
                p_order=po, max_action=int(pol[pi > 1e-12].max()), q_mass=float(pi[pol == m.Q].sum()), edge_mass=m.edge_mass(pi))
    if enumerate_check:
        en = m.enumerate_families()
        cell["enum"] = {k: dict(gap=gap(v[0], g), params=list(v[1])) for k, v in en.items()}
    cell["seconds"] = round(time.time() - t0, 1)
    return cell


def simulate(model: LostSales, pol, paths: int, periods: int, burn: int, seed: int) -> np.ndarray:
    """Simulation der Politik `pol` (Tabelle (X, Pn)) über `paths` Pfade, `periods` Perioden nach einer Einschwingzeit von `burn` Perioden (ein leerer Start
    verfälscht den Mittelwert). Zufallsstrom: SplitMix64 mit Inversion der Verteilungsfunktion. Rückgabe: Kosten je Periode je Pfad (einschließlich Fixkosten)."""
    from brg_rng import SplitMix64

    rng = SplitMix64(seed, paths)
    cdf = np.cumsum(model.pd)
    cdf[-1] = 1.0
    P1, L = model.P, model.L
    x = np.zeros(paths, dtype=np.int64)
    pipe = np.zeros((paths, max(L - 1, 0)), dtype=np.int64)
    tot = np.zeros(paths)
    pol = np.asarray(pol, dtype=np.int64)
    for t in range(periods + burn):
        pidx = np.zeros(paths, dtype=np.int64)
        for j in range(L - 1):
            pidx = pidx * P1 + pipe[:, j]
        act = pol[x, pidx]
        d = rng.inverse_cdf(cdf)
        cost = model.h * np.maximum(x - d, 0) + model.p * np.maximum(d - x, 0) + model.Kfix * (act > 0)
        if t >= burn:
            tot += cost
        left = np.maximum(x - d, 0)
        if L == 1:
            x = np.minimum(left + act, model.XM)
        else:
            x = np.minimum(left + pipe[:, 0], model.XM)
            pipe = np.concatenate([pipe[:, 1:], act[:, None]], axis=1)
    return tot / periods
