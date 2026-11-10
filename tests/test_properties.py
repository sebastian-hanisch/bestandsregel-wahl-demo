"""Eigenschaften: Monotonie, Skalierung, Stufenlogik."""

import itertools

import pytest

import brg_backorder as B
import brg_constants as C
import brg_data as D
import brg_lost as V
from brg_ladder import rung


def test_base_stock_gap_grows_with_k_in_18_of_18_rows():
    assert sum(D.gap_grows_with_k(p, L) for p in C.B_PH for L in C.B_L) == 18


@pytest.mark.parametrize("modus", [C.MODUS_BACKORDER, C.MODUS_LOST])
def test_a_larger_mark_never_gives_a_larger_rung(modus):
    for L, K in itertools.product(C.B_L, C.KARTE_K):
        gaps, _ = D.cell_gaps(modus, 9, L, K)
        if gaps is None:
            continue
        rungs = [rung(gaps, m).rung for m in (0.5, 1, 2, 5, 10, 50)]
        assert rungs == sorted(rungs, reverse=True), (modus, L, K, rungs)


def test_rung_four_only_if_every_rule_is_at_or_above_the_mark():
    for c in D.load()["verloren"]["zellen"]:
        for m in (1, 2, 5):
            r = rung(c["gaps"], m)
            assert (r.rung == 4) == all(v >= m for v in c["gaps"].values())


def test_scaling_h_p_and_k_by_the_same_factor_leaves_the_gaps_unchanged_backorder():
    a = B.Model(B.Settings(L=2, K=1.5, h=1.0, p=9.0))
    b = B.Model(B.Settings(L=2, K=3.0, h=2.0, p=18.0))
    ga, _ = a.rvi()
    gb, _ = b.rvi()
    assert gb == pytest.approx(2 * ga, rel=1e-9)
    gba, gbb = a.best_base_stock()[0], b.best_base_stock()[0]
    assert (gbb / gb) == pytest.approx(gba / ga, rel=1e-9)


def test_scaling_h_p_and_k_by_the_same_factor_leaves_the_gaps_unchanged_lost():
    a = V.LostSales(1, 1.0, h=1.0, p=9.0)
    b = V.LostSales(1, 2.0, h=2.0, p=18.0)
    ga, pol_a, *_ = a.rvi()
    gb, pol_b, *_ = b.rvi()
    assert gb == pytest.approx(2 * ga, rel=1e-9)
    assert (pol_a == pol_b).all()
    ra, rb = a.best_rules(smax=14), b.best_rules(smax=14)
    for k in ra:
        assert rb[k][1] == ra[k][1]
        assert rb[k][0] / gb == pytest.approx(ra[k][0] / ga, rel=1e-9)


def test_dp_order_share_falls_with_k_in_the_backorder_grid():
    for p in C.B_PH:
        for L in C.B_L:
            shares = [D.backorder_cell(p, L, K)["order_share_dp"] for K in (0.0, 1.0, 2.0, 5.0, 10.0)]
            assert all(b <= a + 1e-9 for a, b in zip(shares, shares[1:])), (p, L, shares)


def test_dp_order_share_falls_with_k_in_the_lost_grid():
    for L in (1, 2, 3, 4):
        shares = [D.lost_cell(L, K)["p_order"] for K in sorted(C.V_MEASURED[L])]
        assert all(b <= a + 1e-9 for a, b in zip(shares, shares[1:])), (L, shares)


def test_base_stock_cost_is_linear_in_k_for_fixed_s_backorder():
    m0, m1, m2 = (B.Model(B.Settings(L=1, K=K)) for K in (0.0, 1.0, 2.0))
    q = m0.pol_base(9)
    g0, g1, g2 = (m.evaluate(q)[0] for m in (m0, m1, m2))
    assert g1 - g0 == pytest.approx(g2 - g1, abs=1e-9)
