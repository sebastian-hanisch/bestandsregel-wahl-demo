"""Orakel für die verlorene Nachfrage mit Fixkosten (ORACLE-PLAYBOOK §2): andere Rechenwege als der Tensor-Kern in brg_lost.

O1  dünn besetzter MDP (tests/oracle_sparse.py, Python-Schleifen, scipy): DP-Kosten und exakte Auswertung von vier Regeln, Lieferzeit 1 bis 3, K = 0 und 3
O2  Politik-Iteration nach Howard gegen die Wertiteration (gleiche Zellen)
O3  Simulation (SplitMix64) der DP-Politik und einer (s,S)-Regel gegen die exakte Auswertung, vier Zufalls-Seeds, Band von 4 Standardfehlern
O4  Handbeispiel B: relative Wertiteration (Gleitkomma) gegen die Aufzählung aller 81 Politiken in Brüchen
O5  Aufzählung aller (s,S) und Capped-Paare (S bis 14 bzw. 15) gegen die Parametersuche im selben Bereich (Lieferzeit 1 und 2; die große Aufzählung bis S = 40 steht in data/brg_karte.json)"""

import numpy as np
import pytest

import brg_hand as H
import brg_lost as V
from oracle_sparse import SparseLost

Q, XM, DMAX = 5, 12, 40
SMAX = 14                                         # Suchbereich der Niveaus im Test (die Optima liegen bei S = 9 bis 13)


@pytest.mark.parametrize("L", [1, 2, 3])
@pytest.mark.parametrize("K", [0.0, 3.0])
def test_o1_o2_tensor_dp_equals_sparse_dp_and_policy_iteration(L, K):
    m = V.LostSales(L, K, Q=Q, XM=XM, DMAX=DMAX)
    g, pol, _, _ = m.rvi(tol=1e-11)
    o = SparseLost(L, K, Q, XM, DMAX)
    g_sp, pol_sp = o.rvi()
    assert g == pytest.approx(g_sp, abs=1e-8)
    assert o.policy_iteration(pol_sp) == pytest.approx(g, abs=1e-8)             # O2
    assert o.evaluate(pol.reshape(-1).astype(int)) == pytest.approx(g, abs=1e-8)   # die Politik des Tensor-Kerns kostet im unabhängigen Modell dasselbe
    S0 = 7 + L
    for s, S, cap in ((S0 - 1, S0, Q), (S0 - 3, S0 + 1, Q), (S0 - 1, S0, 3), (S0 - 4, S0, 4)):
        ga = m.evaluate(m.pol_ss(s, S, cap))[0]
        gb = o.evaluate(o.pol_ss(s, S, cap))
        assert ga == pytest.approx(gb, abs=1e-8), (L, K, s, S, cap)


def test_o1_fixed_costs_enter_as_expected_in_the_sparse_model():
    """Zweig: K = 3 gegen K = 0 ändert die DP-Kosten, und bei K > 0 liegt Base-Stock über dem besten (s,S) (Nullspaltenwächter)."""
    for L in (1, 2):
        m0, m3 = V.LostSales(L, 0.0, Q=Q, XM=XM, DMAX=DMAX), V.LostSales(L, 3.0, Q=Q, XM=XM, DMAX=DMAX)
        assert m3.rvi()[0] > m0.rvi()[0] + 0.5
        S = 7 + L
        bs3 = m3.evaluate(m3.pol_bs(S))[0]
        ss3 = min(m3.evaluate(m3.pol_ss(s, S))[0] for s in range(0, S))
        assert bs3 > ss3 + 1e-6
        bs0 = m0.evaluate(m0.pol_bs(S))[0]
        ss0 = min(m0.evaluate(m0.pol_ss(s, S))[0] for s in range(0, S))
        assert bs0 == pytest.approx(ss0, abs=1e-12)                              # bei K = 0 ist Base-Stock das beste (s,S) mit festem S


@pytest.mark.parametrize("which", ["dp", "ss"])
def test_o3_simulation_matches_exact_value_within_four_standard_errors(which):
    L, K = 2, 3.0
    m = V.LostSales(L, K, Q=Q, XM=XM, DMAX=DMAX)
    g, pol, _, _ = m.rvi(tol=1e-11)
    tab = pol if which == "dp" else m.pol_ss(8, 10)
    exact = m.evaluate(tab)[0]
    for seed in range(4):
        c = V.simulate(m, tab, 2000, 1500, 300, seed)
        se = c.std(ddof=1) / np.sqrt(len(c))
        assert abs(c.mean() - exact) < 4 * se, (which, seed, c.mean(), exact, se)


def test_o3_simulation_is_deterministic_per_seed_and_differs_between_seeds():
    m = V.LostSales(1, 2.0, Q=Q, XM=XM, DMAX=DMAX)
    tab = m.pol_ss(5, 8)
    a, b, c = (V.simulate(m, tab, 200, 100, 20, s).mean() for s in (1, 1, 2))
    assert a == b and a != c


def test_o4_example_b_value_iteration_equals_enumeration_of_all_81_policies():
    lines = H.b_all_lines()
    demand = {d: float(pr) for d, pr in H.DEMAND}
    for K in (0.0, 2.0, 8.0):
        h = np.zeros(4)
        for _ in range(20000):
            Qv = np.zeros((4, 3))
            for x in range(4):
                for a in range(3):
                    Qv[x, a] = float(H.b_cost(x)) + K * (a > 0) + sum(pr * h[min(max(x - d, 0) + a, 3)] for d, pr in demand.items())
            v = Qv.min(axis=1)
            g, hn = v[0], v - v[0]
            done = np.max(np.abs(hn - h)) < 1e-13
            h = hn
            if done:
                break
        gmin = min(float(ln.c0) + float(ln.c1) * K for ln in lines.values())
        assert g == pytest.approx(gmin, abs=1e-9), K


@pytest.mark.parametrize("L,K", [(1, 0.0), (1, 1.0), (1, 5.0)])
def test_o5_enumeration_of_all_ss_and_capped_pairs_equals_the_search(L, K):
    m = V.LostSales(L, K)
    g, *_ = m.rvi()
    rules = m.best_rules(smax=SMAX)
    en = m.enumerate_families(smax=SMAX)
    assert rules["ss"][0] == pytest.approx(en["ss"][0], abs=1e-9)
    assert rules["cap"][0] == pytest.approx(en["cap"][0], abs=1e-9)
    assert rules["ssc"][0] <= min(rules["ss"][0], rules["cap"][0]) + 1e-9        # (s,S) mit Kappe enthält beide Familien
    assert all(r[0] >= g - 1e-9 for r in rules.values())                          # keine Regel unterbietet die DP


def test_o5_enumeration_equals_the_search_at_lead_time_two():
    m = V.LostSales(2, 2.0)
    rules = m.best_rules(smax=15)
    en = m.enumerate_families(smax=15)
    assert rules["ss"][0] == pytest.approx(en["ss"][0], abs=1e-9)
    assert rules["cap"][0] == pytest.approx(en["cap"][0], abs=1e-9)
