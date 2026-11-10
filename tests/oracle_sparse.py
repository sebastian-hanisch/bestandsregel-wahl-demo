"""Unabhängige Umsetzung der verlorenen Nachfrage als dünn besetzter Markov-Entscheidungsprozess (Orakel für brg_lost, ohne Tensor-Trick).

Je Zustand (Bestand, Pipeline) und Aktion werden die Folgezustände über die Nachfrage einzeln aufgezählt (Python-Schleifen), die Übergangsmatrizen stehen als
scipy.sparse-Matrizen. Eigene relative Wertiteration, eigene Politik-Iteration nach Howard (lineares Gleichungssystem), eigene exakte Auswertung fester Politiken.
Nutzt nichts aus brg_lost; Poisson-Gewichte aus scipy.stats."""

import itertools

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla
from scipy.stats import poisson


class SparseLost:
    def __init__(self, L, K, Q, XM, DMAX, mean=3.0, h=1.0, p=9.0):
        self.L, self.Q, self.XM = L, Q, XM
        pmf = poisson.pmf(np.arange(DMAX + 1), mean)
        pmf[-1] += 1.0 - pmf.sum()                      # Rest der Verteilung auf DMAX gelegt
        states = list(itertools.product(range(XM + 1), *[range(Q + 1)] * (L - 1)))
        self.states = states
        self.idx = {s: i for i, s in enumerate(states)}
        n = len(states)
        self.n = n
        self.A = Q + 1
        self.cost = np.zeros((n, self.A))
        self.P = [sp.lil_matrix((n, n)) for _ in range(self.A)]
        for i, s in enumerate(states):
            x, pipe = s[0], s[1:]
            ec = sum(pmf[d] * (h * max(x - d, 0) + p * max(d - x, 0)) for d in range(DMAX + 1))
            for a in range(self.A):
                self.cost[i, a] = ec + (K if a > 0 else 0.0)
                for d in range(DMAX + 1):
                    left = max(x - d, 0)
                    if L == 1:
                        nx, npipe = min(left + a, XM), ()
                    else:
                        nx, npipe = min(left + pipe[0], XM), pipe[1:] + (a,)
                    self.P[a][i, self.idx[(nx,) + npipe]] += pmf[d]
        self.P = [m.tocsr() for m in self.P]
        self.IP = np.array([s[0] + sum(s[1:]) for s in states])

    def pol_ss(self, s, S, cap):
        q = np.where(self.IP <= s, np.clip(S - self.IP, 0, min(cap, self.Q)), 0)
        return q.astype(int)

    def chain(self, pol):
        rows = [sp.diags((pol == a).astype(float)) @ self.P[a] for a in range(self.A)]
        return sum(rows).tocsr(), self.cost[np.arange(self.n), pol]

    def evaluate(self, pol, start=0):
        """Durchschnittskosten der Politik: stationäre Verteilung der vom Startzustand erreichbaren Menge als lineares System."""
        Pp, c = self.chain(pol)
        reach, todo = {start}, [start]
        while todo:
            i = todo.pop()
            for j in Pp[i].indices:
                if j not in reach:
                    reach.add(j)
                    todo.append(j)
        R = sorted(reach)
        sub = Pp[R][:, R].toarray()
        m = len(R)
        a = sub.T - np.eye(m)
        a[-1, :] = 1.0
        b = np.zeros(m)
        b[-1] = 1.0
        pi = np.linalg.solve(a, b)
        return float(pi @ c[R])

    def rvi(self, tol=1e-11, maxit=50000):
        h = np.zeros(self.n)
        for _ in range(maxit):
            q = np.stack([self.cost[:, a] + self.P[a] @ h for a in range(self.A)], axis=1)
            v = q.min(axis=1)
            g = v[0]
            hn = v - g
            done = np.max(np.abs(hn - h)) < tol
            h = hn
            if done:
                break
        q = np.stack([self.cost[:, a] + self.P[a] @ h for a in range(self.A)], axis=1)
        return float(g), q.argmin(axis=1)

    def policy_iteration(self, pol, maxit=100):
        """Howard: Politik bewerten (g, h aus dem linearen System, h[0] = 0), dann verbessern, bis sich nichts mehr ändert. Rückgabe die Durchschnittskosten g."""
        pol = pol.copy()
        for _ in range(maxit):
            Pp, c = self.chain(pol)
            n = self.n
            # g + h(i) = c(i) + sum_j P(i,j) h(j), h(0) = 0  ->  Unbekannte (g, h(1..n-1))
            a = sp.lil_matrix((n, n))
            a[:, 0] = 1.0
            m = (sp.identity(n) - Pp).tolil()
            for i in range(n):
                for j in range(1, n):
                    v = m[i, j]
                    if v != 0:
                        a[i, j] = v
            sol = spla.spsolve(a.tocsc(), c)
            g, h = sol[0], np.concatenate([[0.0], sol[1:]])
            q = np.stack([self.cost[:, aa] + self.P[aa] @ h for aa in range(self.A)], axis=1)
            new = pol.copy()
            better = q.min(axis=1) < q[np.arange(n), pol] - 1e-10
            new[better] = q.argmin(axis=1)[better]
            if np.array_equal(new, pol):
                return float(g)
            pol = new
        raise AssertionError("Politik-Iteration konvergiert nicht")
