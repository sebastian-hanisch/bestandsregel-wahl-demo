"""Die vorgerechnete Karte (data/brg_karte.json) gegen Neuberechnung und gegen sich selbst.

Das Rückstandsraster hat 3 * 6 * 87 = 1.566 Zellen; die verlorene Nachfrage 29 Zellen. Kleine Zellen werden hier mit dem Code neu gerechnet und mit der Datei verglichen;
die großen (Lieferzeit 3 und 4) liegen nur vorgerechnet vor (Größenordnung Minuten je Zelle) und werden über ihre inneren Beziehungen geprüft."""

import json
import random

import pytest

import brg_backorder as B
import brg_constants as C
import brg_data as D
import brg_lost as V


def test_file_is_small_and_has_the_expected_keys():
    assert D.DATA_PATH.stat().st_size < 300 * 1024
    data = D.load()
    for key in ("rueckstand", "verloren", "lernen", "uebernommen", "rechengrenze", "check_L4_K5", "meta"):
        assert key in data, key


def test_backorder_grid_has_every_cell_once():
    rows = D.load()["rueckstand"]["rows"]
    assert len(rows) == len(C.B_PH) * len(C.B_L) * len(C.B_K) == 1566
    assert len({(r[0], r[1], round(r[2], 2)) for r in rows}) == 1566
    assert D.load()["rueckstand"]["zellen"] == 1566


def test_lost_grid_has_the_29_cells_and_the_measured_k_per_lead_time():
    cells = D.load()["verloren"]["zellen"]
    assert len(cells) == 29
    for L, ks in C.V_MEASURED.items():
        assert sorted(c["K"] for c in cells if c["L"] == L) == sorted(ks)
    assert D.lost_cell(4, 1.5) is None and D.lost_cell(5, 0.0) is None and D.lost_cell(0, 0.0) is None and D.lost_cell(3, 2.0, p_h=4) is None


def test_map_rows_are_measured_cells_of_the_grids():
    for K in C.KARTE_K:
        assert K in C.B_K
        for L in C.B_L:
            assert D.backorder_cell(9, L, K) is not None
    assert sum(D.lost_cell(L, K) is not None for L in C.V_L for K in C.KARTE_K) == 29


@pytest.mark.parametrize("L,K,p", [(0, 1.0, 9), (1, 0.0, 9), (2, 1.5, 4), (3, 5.0, 19), (4, 0.3, 9), (5, 10.0, 9), (5, 30.0, 4)])
def test_backorder_cells_equal_a_fresh_calculation(L, K, p):
    row = D.backorder_cell(p, L, K)
    r = B.solve(L, K, p)
    assert row["g_dp"] == pytest.approx(r["g"], abs=1e-8)
    assert row["gap_base_stock_pct"] == pytest.approx(r["gap_bs"], abs=1e-5)
    assert (row["s_dp"], row["S_dp"], row["S_base_stock"]) == (r["s"], r["S"], r["Sb"])
    assert row["order_share_dp"] == pytest.approx(r["pord"], abs=1e-5)


def test_backorder_sample_of_40_random_cells_equals_a_fresh_calculation():
    rng = random.Random(20261110)
    for _ in range(40):
        p, L, K = rng.choice(C.B_PH), rng.choice(C.B_L), rng.choice(C.B_K)
        row = D.backorder_cell(p, L, K)
        r = B.solve(L, K, p)
        assert row["gap_base_stock_pct"] == pytest.approx(r["gap_bs"], abs=1e-5), (p, L, K)


def test_backorder_cells_are_all_pure_ss_with_negligible_edge_mass():
    bo = D.load()["rueckstand"]
    assert bo["ohne_reine_ss_form"] == 0
    assert all(r[9] == 1 for r in bo["rows"])
    assert bo["rand_unten_max"] < 1e-4 and bo["rand_oben_max"] < 1e-4 and bo["bestellgrenze_max"] < 1e-4


@pytest.mark.parametrize("K", [0.0, 2.0, 10.0])
def test_lost_lead_time_one_cells_equal_a_fresh_calculation(K):
    stored = D.lost_cell(1, K)
    fresh = V.solve_cell(1, K, enumerate_check=False)
    assert stored["g"] == pytest.approx(fresh["g"], abs=1e-8)
    for rule in ("bs", "ss", "cap", "ssc"):
        assert stored["gaps"][rule] == pytest.approx(fresh["gaps"][rule], abs=1e-6), rule
        assert stored["params"][rule] == fresh["params"][rule], rule
    assert stored["p_order"] == pytest.approx(fresh["p_order"], abs=1e-9)


def test_lost_state_counts_are_27_times_13_to_the_power_l_minus_one():
    for c in D.load()["verloren"]["zellen"]:
        assert c["states"] == 27 * 13 ** (c["L"] - 1)
    assert V.LostSales(2, 0.0).S == 351


def test_lost_cells_have_negligible_edge_mass_and_never_reach_the_order_limit():
    for c in D.load()["verloren"]["zellen"]:
        assert c["edge_mass"] < 1e-4 and c["q_mass"] == 0.0 and c["max_action"] < C.V_Q


def test_lost_search_equals_full_enumeration_in_all_24_cells_up_to_lead_time_three():
    enumerated = [c for c in D.load()["verloren"]["zellen"] if "enum" in c]
    assert len(enumerated) == 24 and {c["L"] for c in enumerated} == {1, 2, 3}
    for c in enumerated:
        for rule in ("ss", "cap"):
            assert abs(c["enum"][rule]["gap"] - c["gaps"][rule]) < 1e-3, (c["L"], c["K"], rule)


def test_lost_rules_never_undercut_the_dp_and_ssc_contains_both_two_parameter_families():
    for c in D.load()["verloren"]["zellen"]:
        g = c["gaps"]
        assert min(g.values()) >= 0.0
        assert g["ssc"] <= min(g["ss"], g["cap"]) + 1e-6, (c["L"], c["K"])
        assert g["ss"] <= g["bs"] + 1e-6                          # (s,S) mit s = S - 1 ist Base-Stock


def test_lost_costs_rise_with_k_in_every_lead_time():
    for L in C.V_L:
        gs = [D.lost_cell(L, K)["g"] for K in sorted(C.V_MEASURED[L])]
        assert all(b > a for a, b in zip(gs, gs[1:]))


def test_backorder_dp_cost_rises_with_k_in_every_row():
    for p in C.B_PH:
        for L in C.B_L:
            gs = [D.backorder_cell(p, L, K)["g_dp"] for K in C.B_K]
            assert all(b > a for a, b in zip(gs, gs[1:])), (p, L)


def test_json_is_valid_utf8_without_nan():
    text = D.DATA_PATH.read_text(encoding="utf-8")
    assert "NaN" not in text and "Infinity" not in text
    json.loads(text)
