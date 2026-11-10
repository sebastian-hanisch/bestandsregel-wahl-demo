"""Einheiten von Hand gerechnet (DEMO-PLAYBOOK §1b): Lücke, Geraden, Leiter, die beiden Handbeispiele in exakten Brüchen.

Die Erwartungswerte stehen als Rechnung im Test. Beispiel A (Rückstand, Lieferzeit 0): Nachfrage 0 / 1 / 2 mit 1/4, 1/2, 1/4, h = 1, p = 4. Kosten bei Niveau y nach der Bestellung
L(y) = E[(y - D)+ + 4 (D - y)+]: L(2) = 1/4 * 2 + 1/2 * 1 + 1/4 * 0 = 1, L(1) = 1/4 * 1 + 1/2 * 0 + 1/4 * 4 = 5/4.
Base-Stock S = 2 bestellt, sobald die Vorperiode Nachfrage größer als 0 hatte (3/4), y = 2 immer: g_A(K) = 1 + 3K/4.
(s,S) = (0,2): stationäre Verteilung der Position (-1, 0, 1, 2) = (1/10, 7/20, 2/5, 3/20), Bestellanteil 1/10 + 7/20 = 9/20, y = 2 in 3/5 der Perioden (Kosten 1), y = 1 in 2/5 (5/4):
g_B(K) = 3/5 + 2/5 * 5/4 + 9K/20 = 11/10 + 9K/20. Kreuzung: 3K/4 - 9K/20 = 1/10 -> K = 1/3."""

from fractions import Fraction as F

import pytest

import brg_hand as H
from brg_gap import clip_noise, gap
from brg_ladder import best_two_parameter, distribution, rung
from brg_lines import Line, crossing, lower_hull, threshold


# ---------------------------------------------------------------- Lücke
def test_gap_of_the_hand_example_a_at_k2_is_25_percent():
    assert gap(F(5, 2), 2) == 25                    # 5/2 gegen 2: 5/2 / 2 - 1 = 1/4


def test_gap_of_the_hand_example_b_at_k1_is_5_53_percent():
    g = gap(F(41, 20), F(169, 87))                  # (41/20) / (169/87) - 1 = 41 * 87 / (20 * 169) - 1 = 3567/3380 - 1 = 187/3380
    assert g == 100 * F(187, 3380)
    assert float(g) == pytest.approx(5.5325, abs=1e-4)


def test_gap_with_floats_and_zero_gap():
    assert gap(5.0, 4.0) == pytest.approx(25.0)
    assert gap(4.0, 4.0) == 0.0


def test_gap_refuses_nonpositive_dp_cost():
    for g_dp in (0, 0.0, -1.0):
        with pytest.raises(ValueError):
            gap(1.0, g_dp)


def test_clip_noise_only_removes_rounding_dust():
    assert clip_noise(-3e-9) == 0.0 and clip_noise(4e-7) == 0.0
    assert clip_noise(-0.02) == -0.02 and clip_noise(1.5) == 1.5


# ---------------------------------------------------------------- Geraden
def test_crossing_of_the_two_lines_of_example_a_is_one_third():
    bs, ss = Line(F(1), F(3, 4)), Line(F(11, 10), F(9, 20))
    assert crossing(bs, ss) == F(1, 3)              # (11/10 - 1) / (3/4 - 9/20) = (1/10) / (3/10)
    assert bs.value(F(1, 3)) == ss.value(F(1, 3)) == F(5, 4)


def test_threshold_two_and_five_percent_of_example_a():
    bs, ss = Line(F(1), F(3, 4)), Line(F(11, 10), F(9, 20))
    # 1 + 3K/4 = 1,02 (11/10 + 9K/20)  ->  K (3/4 - 1,02 * 9/20) = 1,02 * 11/10 - 1  ->  K = 0,122 / 0,291
    assert threshold(bs, ss, 2) == F(122, 291)
    assert threshold(bs, ss, 5) == F(62, 111)       # 1,05 * 11/10 - 1 = 0,155; 3/4 - 1,05 * 9/20 = 0,2775
    assert float(threshold(bs, ss, 2)) == pytest.approx(0.4192, abs=1e-4)


def test_threshold_is_none_without_a_rising_ratio_or_with_negative_k():
    # a = 2 + K/2, b = 1 + K/2: das Verhältnis a/b fällt mit K (von 2 gegen 1): es gibt kein „ab“
    assert threshold(Line(F(2), F(1, 2)), Line(F(1), F(1, 2)), 2) is None
    # a = 2 + 2K, b = 1 + K/2: das Verhältnis steigt, liegt aber bei K = 0 schon bei 2: die 2 %-Schwelle läge bei negativem K
    assert threshold(Line(F(2), F(2)), Line(F(1), F(1, 2)), 2) is None
    # a = 1 + K, b = 2 + K: das Verhältnis steigt gegen 1 und erreicht 1,02 nie (K = (1,02 * 2 - 1) / (1 - 1,02) = -52)
    assert threshold(Line(F(1), F(1)), Line(F(2), F(1)), 2) is None


def test_crossing_of_parallel_lines_is_none():
    assert crossing(Line(1, 2), Line(3, 2)) is None


def test_lower_hull_of_three_lines_by_hand():
    # a: 5 + 0 K (nie bestellen), b: 2 + K, c: 1 + 2 K. Bei K = 0 gewinnt c, ab K = 1 b (1 + 2K = 2 + K), ab K = 3 gewinnt a (2 + K = 5)
    hull = lower_hull([Line(F(5), F(0)), Line(F(2), F(1)), Line(F(1), F(2))], F(10))
    assert [(k, ln) for k, ln in hull] == [(F(0), Line(F(1), F(2))), (F(1), Line(F(2), F(1))), (F(3), Line(F(5), F(0)))]


# ---------------------------------------------------------------- Leiter
def test_ladder_reading_sample_lieferzeit_3_k2():
    gaps = {"bs": 4.98, "ss": 2.68, "cap": 2.78, "ssc": 0.67}   # Zahlen der Messung als Leseprobe
    assert rung(gaps, 2).rung == 3                  # Base-Stock 4,98 nein, kleinster Zweiparameterwert 2,68 nein, (s,S) mit Kappe 0,67 ja
    r3 = rung(gaps, 3)
    assert (r3.rung, r3.rule, r3.gap) == (2, "ss", 2.68)
    assert rung(gaps, 5).rung == 1                  # bei 5 %: Base-Stock 4,98 liegt unter 5


def test_ladder_all_above_the_mark_is_rung_four_and_mark_zero_is_rung_four():
    assert rung({"bs": 20.0, "ss": 3.76, "cap": 18.9, "ssc": 3.63}, 2).rung == 4
    assert rung({"bs": 0.0, "ss": 0.0, "cap": 0.0, "ssc": 0.0}, 0).rung == 4   # unter der Marke 0 liegt nichts echt


def test_ladder_mark_is_strict_and_ties_prefer_ss():
    assert rung({"bs": 2.0, "ss": 1.0}, 2).rung == 2                            # genau auf der Marke zählt nicht als unter der Marke
    r = rung({"bs": 9.0, "ss": 1.0, "cap": 1.0}, 2)
    assert (r.rung, r.rule) == (2, "ss")


def test_ladder_backorder_has_no_cap_rules():
    r = rung({"bs": 3.26, "ss": 0.0, "cap": None, "ssc": None}, 2)
    assert (r.rung, r.rule) == (2, "ss")
    assert rung({"bs": 0.33, "ss": 0.0, "cap": None, "ssc": None}, 2).rung == 1


def test_best_two_parameter_and_distribution():
    assert best_two_parameter({"ss": 2.68, "cap": 2.78}) == (2.68, "ss")
    assert best_two_parameter({"ss": 3.0, "cap": 2.0}) == (2.0, "cap")
    assert best_two_parameter({"bs": 1.0}) is None
    cells = [{"bs": 1.0}, {"bs": 5.0, "ss": 1.0}, {"bs": 5.0, "ss": 4.0, "cap": 4.0, "ssc": 1.0}, {"bs": 9.0, "ss": 9.0, "cap": 9.0, "ssc": 9.0}]
    assert distribution(cells, 2) == {1: 1, 2: 1, 3: 1, 4: 1}


# ---------------------------------------------------------------- Handbeispiel A (Rückstand, Lieferzeit 0)
def test_example_a_cost_function_by_hand():
    assert H.a_cost(2) == F(1)
    assert H.a_cost(1) == F(5, 4)
    assert H.a_cost(0) == F(1, 4) * 0 + F(1, 2) * 4 + F(1, 4) * 8     # y = 0: 0 + 2 + 2 = 4


def test_example_a_stationary_distribution_of_the_policy_zero_two():
    nxt = {z: [(max(H.a_policy_sS(0, 2)[z] - d, H.A_ZMIN), pr) for d, pr in H.DEMAND] for z in H.A_STATES}
    states, pi = H.stationary(nxt, 0)
    assert states == [-1, 0, 1, 2]
    assert pi == [F(1, 10), F(7, 20), F(2, 5), F(3, 20)]


def test_example_a_lines_and_crossing_in_fractions():
    lines = H.a_rule_lines()
    assert lines["bs"] == Line(F(1), F(3, 4))
    assert lines["ss"] == Line(F(11, 10), F(9, 20))
    assert crossing(lines["bs"], lines["ss"]) == F(1, 3)


def test_example_a_enumeration_of_all_720_policies_gives_the_hull_with_one_change_at_one_third():
    allp = H.a_all_lines()
    assert len(allp) == 720                                     # 6 * 5 * 4 * 3 * 2 * 1 Niveaus
    hull = lower_hull(allp.values(), F(6))
    assert [(k, ln) for k, ln in hull] == [(F(0), Line(F(1), F(3, 4))), (F(1, 3), Line(F(11, 10), F(9, 20)))]
    for K in (F(0), F(1, 4), F(1, 3), F(1), F(2), F(6)):
        assert min(ln.value(K) for ln in allp.values()) == min(H.a_rule_lines()["bs"].value(K), H.a_rule_lines()["ss"].value(K))


def test_example_a_gap_values():
    lines = H.a_rule_lines()
    assert gap(lines["bs"].value(F(2)), lines["ss"].value(F(2))) == 25      # 5/2 gegen 2
    assert float(gap(lines["bs"].value(F(1, 2)), lines["ss"].value(F(1, 2)))) == pytest.approx(3.774, abs=5e-4)   # 11/8 gegen 53/40


# ---------------------------------------------------------------- Handbeispiel B (verlorene Nachfrage, Lieferzeit 1)
def test_example_b_cost_per_stock_by_hand():
    # c(0) = 1/4 * 0 + 1/2 * 4 + 1/4 * 8 = 4; c(1) = 1/4 * 1 + 1/2 * 0 + 1/4 * 4 = 5/4; c(2) = 1/4 * 2 + 1/2 * 1 + 0 = 1; c(3) = 1/4 * 3 + 1/2 * 2 + 1/4 * 1 = 2
    assert [H.b_cost(x) for x in range(4)] == [F(4), F(5, 4), F(1), F(2)]


def test_example_b_six_fractions():
    k0, k1 = F(0), F(1)
    capped3 = H.b_line(H.b_policy("cap", 3, 1))        # a = (1,1,1,0): pi(1,2,3) = (1/2, 3/8, 1/8)
    assert capped3.value(k0) == F(5, 4)
    bs3 = H.b_line(H.b_policy("bs", 3))                # a = (2,2,1,0): 13/10 + 3K/4
    assert bs3 == Line(F(13, 10), F(3, 4))
    assert bs3.value(k1) == F(41, 20)
    ss13 = H.b_line(H.b_policy("ss", 1, 3))            # a = (2,2,0,0): 134/87 + 35K/87
    assert ss13 == Line(F(134, 87), F(35, 87))
    assert ss13.value(k1) == F(169, 87)
    cap2 = H.b_line(H.b_policy("cap", 2, 1))           # a = (1,1,0,0): 23/17 + 13K/17
    assert cap2 == Line(F(23, 17), F(13, 17))
    assert cap2.value(k1) == F(36, 17)
    assert gap(bs3.value(k0), capped3.value(k0)) == 4                       # +4 % bei K = 0
    assert float(gap(cap2.value(k1), ss13.value(k1))) == pytest.approx(9.01, abs=5e-3)


def test_example_b_enumeration_of_81_policies_hull_with_exact_breakpoints():
    """Wechsel der besten Politik, exakt aus den Kreuzungen der Geraden (von Hand: (13/10 - 5/4) / (7/8 - 3/4) = 2/5; (134/87 - 13/10) / (3/4 - 35/87) = 38/55; (2 - 134/87) / (35/87 - 9/29) = 5;
    (4 - 2) / (9/29) = 58/9). Der Plan nannte 5/12, 7/10 und 129/20: das waren Rasterwerte (K = i/60), keine Knickpunkte."""
    allp = H.b_all_lines()
    assert len(allp) == 81
    hull = lower_hull(allp.values(), F(12))
    assert [k for k, _ in hull] == [F(0), F(2, 5), F(38, 55), F(5), F(58, 9)]
    assert [ln for _, ln in hull] == [Line(F(5, 4), F(7, 8)), Line(F(13, 10), F(3, 4)), Line(F(134, 87), F(35, 87)), Line(F(2), F(9, 29)), Line(F(4), F(0))]


def test_example_b_the_map_reverses_between_k0_and_k1():
    best0, best1 = H.b_family_best(F(0)), H.b_family_best(F(1))
    assert best0["cap"][2].value(F(0)) < best0["ss"][2].value(F(0)) == best0["bs"][2].value(F(0))   # K = 0: Capped gewinnt, (s,S) = Base-Stock
    assert best1["ss"][2].value(F(1)) < best1["cap"][2].value(F(1))                               # K = 1: (s,S) gewinnt
