"""Orakel für den Rückstand (ORACLE-PLAYBOOK §2).

O6  Rechnung auf der Bestandsposition gegen die Rechnung mit vollem Pipeline-Zustand (dünne Matrizen, allgemeine relative Wertiteration über alle Aktionen, ohne die Position
    als Zustand zu benutzen): Durchschnittskosten und Aktion je erreichter Position. Aufbau wie im Test des Stücks zur Bestellschwelle, hier ohne dessen Module.
N   Newsvendor-Formel bei K = 0: Niveau = Quantil der Poisson-Nachfrage über L + 1 Perioden (scipy), Kosten = E[h (S - D)+ + p (D - S)+] in geschlossener Form.
E   Aufzählung aller (s,S) gegen die DP (Rückstand, Lieferzeit 0 bis 2)."""

import numpy as np
import pytest
import scipy.sparse as sp
from scipy.stats import poisson

import brg_backorder as B

DMAX = 14
XMIN, XMAX = -25, 30
CELLS = [(0, 0.0, 10), (0, 10.0, 10), (1, 2.0, 10), (2, 5.0, 10), (3, 5.0, 6)]   # (Lieferzeit, K, Bestellgrenze)


def full_model(L, K, Q, p=9.0, h=1.0, mean=3.0):
    ks = np.arange(DMAX + 1)
    pd = poisson.pmf(ks, mean)
    pd[-1] += 1.0 - pd.sum()
    npipe = max(L - 1, 0)
    dims = [XMAX - XMIN + 1] + [Q + 1] * npipe
    S = int(np.prod(dims))
    grid = np.indices(dims).reshape(len(dims), -1)
    x = grid[0] + XMIN
    pipe = grid[1:]
    ip = x + (pipe.sum(axis=0) if npipe else 0)

    def idx(xn, pn):
        i = np.clip(xn, XMIN, XMAX) - XMIN
        for k in range(npipe):
            i = i * (Q + 1) + pn[k]
        return i

    cost = np.zeros((S, Q + 1))
    mats = []
    for a in range(Q + 1):
        rows, cols, vals = [], [], []
        y = x + a if L == 0 else x
        ec = np.zeros(S)
        for d, pr in zip(ks, pd):
            ec += pr * (h * np.maximum(y - d, 0) + p * np.maximum(d - y, 0))
            if L == 0:
                xn, pn = y - d, []
            elif L == 1:
                xn, pn = x - d + a, []
            else:
                xn, pn = x - d + pipe[0], list(pipe[1:]) + [np.full(S, a)]
            rows.append(np.arange(S))
            cols.append(idx(xn, pn))
            vals.append(np.full(S, pr))
        mats.append(sp.csr_matrix((np.concatenate(vals), (np.concatenate(rows), np.concatenate(cols))), shape=(S, S)))
        cost[:, a] = ec + (K if a > 0 else 0.0)
    return S, ip, cost, mats


def stationary(S, mats, pol, start):
    rows = [sp.diags((pol == a).astype(float)) @ mats[a] for a in np.unique(pol)]
    P = sum(rows).tocsr()
    pi = np.zeros(S)
    pi[start] = 1.0
    PT = ((P + sp.identity(S)) * 0.5).T.tocsr()
    for _ in range(4000):
        pi = PT @ pi
    return pi / pi.sum()


@pytest.mark.parametrize("L,K,Q", CELLS)
def test_o6_position_dp_equals_the_full_pipeline_dp(L, K, Q):
    S, ip, cost, mats = full_model(L, K, Q)
    ref = (-XMIN) * (Q + 1) ** max(L - 1, 0)            # Bezugszustand: Bestand 0, leere Pipeline
    h = np.zeros(S)
    for _ in range(5000):
        Qm = np.stack([cost[:, a] + mats[a] @ h for a in range(Q + 1)], axis=1)
        v = Qm.min(axis=1)
        g_full = v[ref]
        hn = v - g_full
        done = np.max(np.abs(hn - h)) < 1e-10
        h = hn
        if done:
            break
    Qm = np.stack([cost[:, a] + mats[a] @ h for a in range(Q + 1)], axis=1)
    pol_full = Qm.argmin(axis=1)

    model = B.Model(B.Settings(L=L, K=K, Q=Q, zmin=-40, ymax=60, dmax=DMAX))
    g_pos, q_pos = model.rvi()
    assert g_full == pytest.approx(g_pos, abs=1e-6)

    pi = stationary(S, mats, pol_full, ref)
    reached = pi > 1e-9
    checked = 0
    for pos in np.unique(ip[reached]):
        acts = np.unique(pol_full[reached & (ip == pos)])
        if len(acts) == 1 and -26 < pos < 30:
            assert acts[0] == q_pos[pos - model.st.zmin], (L, K, pos)
            checked += 1
    assert checked >= 10


@pytest.mark.parametrize("L", [0, 1, 2, 3, 4, 5])
def test_newsvendor_quantile_and_closed_form_cost_at_k_zero(L):
    """Bei K = 0 ist Base-Stock die DP-Politik: S = Poisson-Quantil (0,9) der Nachfrage über L + 1 Perioden, Kosten in geschlossener Form mit scipy (unabhängig von der
    Faltung im Code)."""
    res = B.solve(L, 0.0, 9)
    lam = 3.0 * (L + 1)
    S = int(poisson.ppf(0.9, lam))
    ks = np.arange(0, 200)
    pk = poisson.pmf(ks, lam)
    g_formula = float((pk * (np.maximum(S - ks, 0) + 9 * np.maximum(ks - S, 0))).sum())
    assert res["Sb"] == S
    assert res["g"] == pytest.approx(g_formula, abs=1e-6)
    assert res["gap_bs"] == pytest.approx(0.0, abs=1e-6)
    assert (res["s"], res["S"]) == (S - 1, S)


@pytest.mark.parametrize("L,K", [(0, 1.0), (1, 2.0), (2, 5.0)])
def test_enumeration_of_all_ss_equals_the_dp(L, K):
    m = B.Model(B.Settings(L=L, K=K))
    g, q = m.rvi()
    best = min(m.all_sS(s_lo=-5, S_hi=30).values())
    assert best == pytest.approx(g, abs=1e-8)


def test_base_stock_order_share_is_one_minus_exp_minus_mean():
    """Anteil der Perioden mit Bestellung unter Base-Stock im Modell: 1 - exp(-3), unabhängig von der Lieferzeit (Zeitanteil aus der exakten stationären Verteilung)."""
    from math import exp
    for L in (0, 2):
        m = B.Model(B.Settings(L=L, K=1.0))
        Sb = m.best_base_stock()[1]
        q = m.pol_base(Sb)
        _, pi = m.evaluate(q)
        assert float(pi[q > 0].sum()) == pytest.approx(1 - exp(-3.0), abs=1e-9)
