"""Jede Zahl der README (Tabelle „Befunde“, Spalte Test) wird hier nachgerechnet: gegen die vorgerechnete Karte (data/brg_karte.json), die ihrerseits in test_data.py
gegen Neuberechnung geprüft ist, und gegen die exakten Brüche der Handbeispiele. K-Nummern wie in der README. „Exakt“: Gleichheit oder Brüche; „Band“: Rundung auf die gedruckten Stellen."""

from fractions import Fraction as F
from math import exp
from pathlib import Path

import pytest

import brg_constants as C
import brg_data as D
import brg_evaluation as ev
import brg_hand as H
from brg_gap import gap
from brg_ladder import distribution, rung
from brg_lines import crossing, lower_hull, threshold

ROOT = Path(__file__).resolve().parent.parent
LOST = D.load()["verloren"]["zellen"]


def _r2(x):
    return f"{x:.2f}".replace(".", ",")


def test_k01_grid_sizes():
    """Rückstand 1.566 Zellen (3 Werte p/h x 6 Lieferzeiten x 87 Werte K), verlorene Nachfrage 29 Zellen. Exakt."""
    assert len(C.B_PH) * len(C.B_L) * len(C.B_K) == 1566 == D.load()["rueckstand"]["zellen"]
    assert len(LOST) == 29 and len(C.B_K) == 87


def test_k02_backorder_dp_has_pure_ss_form_in_all_cells_with_negligible_edge_mass():
    bo = D.load()["rueckstand"]
    assert sum(r[9] for r in bo["rows"]) == 1566 and bo["ohne_reine_ss_form"] == 0
    assert bo["rand_unten_max"] == 0.0 and 7.2e-17 < bo["rand_oben_max"] < 7.4e-17 and 2.3e-16 < bo["bestellgrenze_max"] < 2.4e-16
    assert max(abs(r[11]) for r in bo["rows"]) < 1e-6              # (s,S) mit den Parametern der DP-Politik kostet dasselbe wie die DP


def test_k03_gap_grows_with_k_in_18_of_18_rows_and_threshold_ranges():
    assert sum(D.gap_grows_with_k(p, L) for p in C.B_PH for L in C.B_L) == 18
    assert D.threshold_range(2) == (0.75, 1.55, 18)
    assert D.threshold_range(1)[:3] == (0.5, 1.15, 18)
    assert D.threshold_range(5)[:3] == (1.35, 2.35, 18)


def test_k04_eoq_takt_at_the_two_percent_threshold():
    lo, hi = D.takt_band_all(2)
    assert f"{lo:.2f}" == "0.71" and f"{hi:.2f}" == "1.02"


def test_k05_threshold_by_lead_time_for_p_over_h_9_has_no_monotone_trend():
    ks = [D.threshold_k(9, L, 2) for L in C.B_L]
    assert ks == [1.3, 1.2, 1.3, 0.9, 1.2, 0.95]
    assert ks != sorted(ks) and ks != sorted(ks, reverse=True)
    for p, expected in ((4, (0.75, 1.0)), (19, (1.2, 1.55))):
        ks_p = [D.threshold_k(p, L, 2) for L in C.B_L]
        assert (min(ks_p), max(ks_p)) == expected


TABLE_A = {  # Lücke von Base-Stock in %, Rückstand, p/h = 9; Zeilen K, Spalten Lieferzeit 0 bis 5
    0.0: ("0,00", "0,00", "0,00", "0,00", "0,00", "0,00"),
    0.5: ("0,00", "0,00", "0,53", "0,91", "0,41", "0,77"),
    1.0: ("0,33", "1,27", "1,49", "2,41", "1,44", "2,26"),
    1.5: ("3,26", "3,60", "2,86", "4,15", "3,33", "3,75"),
    2.0: ("5,87", "5,67", "5,59", "6,15", "5,57", "5,82"),
    5.0: ("20,78", "21,97", "20,90", "21,47", "20,13", "20,08"),
    10.0: ("50,21", "48,07", "47,24", "46,06", "44,17", "43,61"),
}


def test_k06_table_a_gap_of_base_stock_backorder():
    for K, row in TABLE_A.items():
        got = tuple(_r2(abs(D.backorder_cell(9, L, K)["gap_base_stock_pct"])) for L in C.B_L)
        assert got == row, K


def test_k07_ss_of_the_dp_at_k5():
    got = [(D.backorder_cell(9, L, 5.0)["s_dp"], D.backorder_cell(9, L, 5.0)["S_dp"]) for L in C.B_L]
    assert got == [(3, 8), (6, 12), (10, 16), (13, 19), (16, 23), (20, 26)]


def test_k08_order_frequency_explains_the_percentages_at_high_k():
    """Rückstand, Lieferzeit 1, p/h = 9, K = 20: Lücke von Base-Stock +93,96 %, Base-Stock bestellt in 95,0 % der Perioden (1 - e^-3), die DP in 24 %."""
    cell = D.backorder_cell(9, 1, 20.0)
    assert _r2(cell["gap_base_stock_pct"]) == "93,96" and cell["order_share_dp"] == 0.24
    assert f"{100 * ev.base_stock_order_share():.1f}" == "95.0" and ev.base_stock_order_share() == pytest.approx(1 - exp(-3))
    assert cell["g_base_stock"] == pytest.approx(23.6168, abs=5e-5) and cell["g_dp"] == pytest.approx(12.1759, abs=5e-5)
    assert D.backorder_cell(9, 1, 20.0)["g_base_stock"] - 0.9502 * 20 == pytest.approx(4.6, abs=0.02)    # Fixkosten-Anteil 19,0, Rest 4,6 (Stück 2: 19,00 + 4,61)


def test_k09_lost_sales_k0_capped_wins_and_k_at_least_5_ss_wins():
    k0 = [c for c in LOST if c["K"] == 0.0]
    big = [c for c in LOST if c["K"] >= 5.0]
    assert len(k0) == 4 and sum(c["gaps"]["cap"] < c["gaps"]["ss"] for c in k0) == 4
    assert len(big) == 8 and sum(c["gaps"]["ss"] < c["gaps"]["cap"] for c in big) == 8
    assert (_r2(min(c["gaps"]["cap"] for c in big)), _r2(max(c["gaps"]["cap"] for c in big))) == ("18,55", "47,27")
    assert (_r2(min(c["gaps"]["bs"] for c in big)), _r2(max(c["gaps"]["bs"] for c in big))) == ("19,66", "47,44")
    assert (_r2(min(c["p_order"] for c in big)), _r2(max(c["p_order"] for c in big))) == ("0,29", "0,44")


def test_k10_seven_of_29_cells_have_neither_two_parameter_rule_below_2_percent():
    both = [(c["L"], c["K"], c["gaps"]["ssc"]) for c in LOST if c["gaps"]["ss"] >= 2 and c["gaps"]["cap"] >= 2]
    assert [(L, K) for L, K, _ in both] == [(3, 1.5), (3, 2.0), (3, 3.0), (3, 5.0), (4, 2.0), (4, 5.0), (4, 10.0)]
    below = [g for _, _, g in both if g < 2]
    assert len(below) == 6 and (_r2(min(below)), _r2(max(below))) == ("0,67", "1,92")
    assert _r2(D.lost_cell(4, 5.0)["gaps"]["ssc"]) == "3,63"


def test_k11_distribution_of_rungs_over_the_29_cells_by_mark():
    gaps = [c["gaps"] for c in LOST]
    assert distribution(gaps, 1) == {1: 0, 2: 11, 3: 9, 4: 9}
    assert distribution(gaps, 2) == {1: 2, 2: 20, 3: 6, 4: 1}
    assert distribution(gaps, 5) == {1: 14, 2: 15, 3: 0, 4: 0}


def test_k11b_count_of_cells_in_the_displayed_grid_where_base_stock_suffices():
    """Raster der Karte, Rückstand, p/h = 9, acht Werte K x sechs Lieferzeiten = 48 Zellen: Base-Stock reicht in 13 / 16 / 24 Zellen bei Marke 1 / 2 / 5 %."""
    assert [D.count_rungs(D.karte(C.MODUS_BACKORDER, m))[1] for m in (1, 2, 5)] == [13, 16, 24]
    assert all(D.count_cells(D.karte(C.MODUS_BACKORDER, m)) == 48 for m in (1, 2, 5))


def test_k12_cell_lead_time_4_k5_enumeration_raster_and_position_function():
    chk = D.load()["check_L4_K5"]
    assert chk["states"] == 59319 and _r2(chk["g_dp"]) == "8,63"
    assert chk["enum_ss"]["params"] == [15, 20] and f"{chk['enum_ss']['gap']:.2f}" == "3.76"
    assert chk["raster_ssc"]["params"] == [14, 21, 8] and f"{chk['raster_ssc']['gap']:.2f}" == "3.63" and chk["raster_ssc"]["evaluations"] == 583
    pf = chk["position_function"]
    assert f"{pf['gap']:.2f}" == "3.56" and pf["evaluations"] == 421 and pf["sweeps"] == 1 and pf["converged"] is False
    assert pf["gap"] < chk["raster_ssc"]["gap"] < chk["enum_ss"]["gap"]
    assert D.lost_cell(4, 5.0)["gaps"]["ss"] == pytest.approx(chk["enum_ss"]["gap"], abs=1e-3) and D.lost_cell(4, 5.0)["gaps"]["ssc"] == pytest.approx(chk["raster_ssc"]["gap"], abs=1e-3)


def test_k13_learned_policies_in_two_cells():
    a, b = D.lernen_cell(3, 2.0), D.lernen_cell(4, 5.0)
    assert [f"{x:+.2f}" for x in a["final_gaps"]] == ["+1.19", "+1.54", "+0.85", "+0.58", "+1.14"]
    assert [f"{x:+.2f}" for x in b["final_gaps"]] == ["+2.01", "+1.65", "+3.32", "+0.94", "+1.40"]
    for cell, med, n2, n_two, n_ssc, share in ((a, "1.14", 5, 5, 1, 0.8), (b, "1.65", 3, 5, 5, 0.56)):
        f = sorted(cell["final_gaps"])
        assert f"{f[2]:.2f}" == med and sum(x < 2 for x in f) == n2
        two = min(cell["ref_gaps"]["ss"], cell["ref_gaps"]["cap"])
        assert sum(x < two for x in f) == n_two and sum(x < cell["ref_gaps"]["ssc"] for x in f) == n_ssc
        assert cell["points_from_1000"]["share_below_2"] == share and cell["points_from_1000"]["n"] == 25
        assert cell["periods_total"] == 3000 * 25600 and cell["updates"] == 3000
        assert cell["min_diff_to_dp"] > 0                                        # nie unter dem Optimum
    assert a["ref_gaps"]["ssc"] < 1 and b["ref_gaps"]["ssc"] > 3.6


def test_k14_hand_examples_in_fractions():
    a = H.a_rule_lines()
    assert (a["bs"].c0, a["bs"].c1, a["ss"].c0, a["ss"].c1) == (F(1), F(3, 4), F(11, 10), F(9, 20))
    assert crossing(a["bs"], a["ss"]) == F(1, 3) and threshold(a["bs"], a["ss"], 2) == F(122, 291) and threshold(a["bs"], a["ss"], 5) == F(62, 111)
    assert round(float(F(122, 291)), 3) == 0.419 and round(float(F(62, 111)), 3) == 0.559
    assert gap(a["bs"].value(F(2)), a["ss"].value(F(2))) == 25 and len(H.a_all_lines()) == 720
    assert [k for k, _ in lower_hull(H.a_all_lines().values(), F(6))] == [F(0), F(1, 3)]
    bl = H.b_all_lines()
    assert len(bl) == 81
    assert [k for k, _ in lower_hull(bl.values(), F(12))] == [F(0), F(2, 5), F(38, 55), F(5), F(58, 9)]
    cap3 = bl[H.b_policy("cap", 3, 1)]
    ss13, bs3, cap2 = bl[H.b_policy("ss", 1, 3)], bl[H.b_policy("bs", 3)], bl[H.b_policy("cap", 2, 1)]
    assert cap3.value(F(0)) == F(5, 4) == min(ln.value(F(0)) for ln in bl.values())
    assert ss13.value(F(1)) == F(169, 87) == min(ln.value(F(1)) for ln in bl.values())
    assert (bs3.value(F(1)), cap2.value(F(1))) == (F(41, 20), F(36, 17))
    assert [round(float(gap(x.value(F(1)), ss13.value(F(1)))), 2) for x in (bs3, cap2)] == [5.53, 9.01]


def test_k15_state_counts_and_the_cell_not_computed():
    assert [27 * 13 ** (L - 1) for L in range(1, 6)] == [27, 351, 4563, 59319, 771147]
    assert D.load()["rechengrenze"]["diese_demo"]["zustaende"] == {"1": 27, "2": 351, "3": 4563, "4": 59319, "5": 771147}
    assert 21 * 9 ** 6 == 11160261 and 21 * 9 ** 7 == 100442349 and round(21 * 9 ** 7 * 8 / 1e9, 1) == 0.8


def test_k16_limits_are_not_reached():
    assert max(c["edge_mass"] for c in LOST) < 6.6e-21 and max(c["q_mass"] for c in LOST) == 0.0
    assert max(c["max_action"] for c in LOST) == 11 < C.V_Q
    assert sorted({c["max_action"] for c in LOST if c["K"] == 10.0}) == [10, 11]          # „Weiße Flecken“: bei K = 10 höchstens 10 bis 11 Stück
    assert (C.V_Q, C.V_XM, C.V_DMAX, C.B_Q, C.B_ZMIN, C.B_YMAX, C.B_DMAX) == (12, 26, 14, 40, -40, 60, 30)


def test_k17_enumeration_of_all_ss_and_capped_pairs_equals_the_search_in_24_cells():
    en = [c for c in LOST if "enum" in c]
    assert len(en) == 24 and max(abs(c["enum"][r]["gap"] - c["gaps"][r]) for c in en for r in ("ss", "cap")) < 1e-3


def test_k18_the_leseprobe_of_the_ladder():
    """Verlorene Nachfrage, Lieferzeit 3, K = 2: Base-Stock +4,98 %, (s,S) +2,68 %, Capped +2,78 %, (s,S) mit Kappe +0,67 %: Marke 2 % gibt Stufe 3, Marke 3 % Stufe 2, Marke 5 % Stufe 1."""
    g = D.lost_cell(3, 2.0)["gaps"]
    assert [_r2(g[k]) for k in ("bs", "ss", "cap", "ssc")] == ["4,98", "2,68", "2,78", "0,67"]
    assert [rung(g, m).rung for m in (2, 3, 5)] == [3, 2, 1]


def test_k19_size_of_the_repo():
    files = [p for p in ROOT.rglob("*") if p.is_file() and not any(part in (".git", "__pycache__", ".pytest_cache", "venv") for part in p.parts)]
    assert sum(p.stat().st_size for p in files) < 3 * 1024 * 1024
    assert D.DATA_PATH.stat().st_size < 300 * 1024


def test_k20_marks_of_the_map_only_use_the_three_documented_values():
    assert C.MARKEN == (1, 2, 5) and C.DEFAULT_MARKE == 2
