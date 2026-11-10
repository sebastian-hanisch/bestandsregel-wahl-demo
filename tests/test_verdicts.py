"""Verdikte an von Hand gesetzten Zeilen (DEMO-PLAYBOOK §12): jede Schwelle und jede Zahl im Text steht hier. Verdikte sind reine Funktionen (Art, Text)."""

import pytest

import brg_constants as C
import brg_evaluation as ev
from brg_ladder import rung


def _view(modus, gaps, marke=2, L=3, K=2.0, params=None, g_dp=6.888879, p_order=0.829, ph=9):
    return ev.CellView(modus, L, K, ph, marke, True, gaps=gaps, rung=rung(gaps, marke), cell={}, g_dp=g_dp, params=params or {}, p_order_dp=p_order)


LOST = C.MODUS_LOST
BACK = C.MODUS_BACKORDER


def test_verdict_rung1_is_success_and_names_the_gap():
    kind, text = ev.verdict_cell(_view(BACK, {"bs": 0.33, "ss": 0.0, "cap": None, "ssc": None}, L=0, K=1.0))
    assert kind == "success"
    assert "Stufe 1, Base-Stock" in text and "+0,33 %" in text and "Marke 2 %" in text and "Bezug: DP" in text and "Lieferzeit 0, K = 1" in text


def test_verdict_backorder_rung2_says_base_stock_is_not_enough_and_ss_meets_the_dp():
    kind, text = ev.verdict_cell(_view(BACK, {"bs": 10.76, "ss": 0.0, "cap": None, "ssc": None}, K=3.0))
    assert kind == "info"
    assert "Base-Stock reicht nicht mehr" in text and "+10,76 %" in text and "Stufe 2, (s,S)" in text and "reine (s,S)-Form" in text


def test_verdict_lost_rung2_names_the_better_two_parameter_rule_and_the_other():
    kind, text = ev.verdict_cell(_view(LOST, {"bs": 4.36, "ss": 0.99, "cap": 3.59, "ssc": 0.36}, L=1, K=2.0))
    assert kind == "info" and "Stufe 2, (s,S)" in text and "+0,99 %" in text and "Base-Stock liegt bei +4,36 %" in text and "Capped Base-Stock bei +3,59 %" in text
    kind, text = ev.verdict_cell(_view(LOST, {"bs": 3.36, "ss": 3.36, "cap": 0.69, "ssc": 0.69}, L=2, K=0.0))
    assert "Stufe 2, Capped Base-Stock" in text and "(s,S) bei +3,36 %" in text


def test_verdict_two_weaknesses_at_rung3():
    kind, text = ev.verdict_cell(_view(LOST, {"bs": 4.98, "ss": 2.68, "cap": 2.78, "ssc": 0.67}))
    assert kind == "warning"
    assert text.startswith("**Zwei Schwächen zugleich: keine Zweiparameterregel unter 2 %**")
    assert "(s,S) +2,68 %" in text and "Capped +2,78 %" in text and "Stufe 3, (s,S) mit Kappe" in text and "+0,67 %" in text


def test_verdict_rung4_is_an_error_and_names_the_best_rule():
    kind, text = ev.verdict_cell(_view(LOST, {"bs": 20.21, "ss": 3.76, "cap": 18.88, "ssc": 3.63}, L=4, K=5.0))
    assert kind == "error" and "Keine einfache Regel unter 2 %" in text and "(s,S) mit Kappe +3,63 %" in text and "gelernte Politik" in text


def test_verdict_depends_on_the_mark():
    gaps = {"bs": 4.98, "ss": 2.68, "cap": 2.78, "ssc": 0.67}
    assert ev.verdict_cell(_view(LOST, gaps, marke=1))[0] == "warning"      # 0,67 liegt unter 1 %: Stufe 3 auch bei Marke 1
    assert ev.verdict_cell(_view(LOST, gaps, marke=3))[0] == "info"         # Stufe 2 bei 3 %
    assert ev.verdict_cell(_view(LOST, gaps, marke=5))[0] == "success"      # Stufe 1 bei 5 %


def test_verdict_for_an_unmeasured_cell_gives_the_reason_instead_of_a_number():
    v = ev.cell_view(ev.Settings(modus=LOST, L=5, K=2.0))
    kind, text = ev.verdict_cell(v)
    assert kind == "info" and "nicht gemessen" in text and "Lieferzeit 5" in text


def test_verdict_threshold_names_k_and_takt():
    kind, text = ev.verdict_threshold(9, 3, 2)
    assert kind == "info" and "ab K = 0,9" in text and "0,77 Perioden" in text and "Raster 0,05" in text
    assert "ab K = 1,3 " in ev.verdict_threshold(9, 0, 2)[1] and "0,93 Perioden" in ev.verdict_threshold(9, 0, 2)[1]


def test_verdict_threshold_when_the_gap_never_reaches_the_mark(monkeypatch):
    monkeypatch.setattr(ev.D, "threshold_k", lambda p, L, m: None)
    kind, text = ev.verdict_threshold(9, 3, 2)
    assert "nie" in text


def test_verdict_map_counts_cells():
    import brg_data as D
    k = D.karte(BACK, 2, 9)
    kind, text = ev.verdict_map(k)
    assert "in **16 von 48 Zellen reicht Base-Stock**" in text and "Stufe 2 in 32" in text and "kein Anteil der Welt" in text
    kind, text = ev.verdict_map(D.karte(LOST, 2, 9))
    assert "in **2 von 29 Zellen reicht Base-Stock**" in text and "Stufe 2 in 20, Stufe 3 in 6, Stufe 4 in 1" in text


def test_verdict_hand_a_numbers_at_k2():
    kind, text = ev.verdict_hand_a(2.0)
    assert "+25,0 %" in text and "K = 1/3" in text and "K = 122/291" in text and "0,419" in text


def test_verdict_hand_a_names_the_upper_limit_of_the_second_rule():
    """Regression: „darüber (0, 2)“ ohne Obergrenze; (0, 2) ist nur bis K = 58/9 die beste der 720 Politiken (untere Hülle)."""
    from fractions import Fraction
    assert ev.hand_a_ss_until() == Fraction(58, 9)
    for K in (2.0, 6.0):
        text = ev.verdict_hand_a(K)[1]
        assert "darüber (0, 2) bis K = 58/9" in text and "danach wechselt das Optimum weiter" in text


def test_verdict_hand_b_reverses_the_order_between_k0_and_k1():
    t0 = ev.verdict_hand_b(0.0)[1]
    t1 = ev.verdict_hand_b(1.0)[1]
    assert "Base-Stock +4,00 %" in t0 and "Capped (Kappe 1) +0,00 %" in t0
    assert "Base-Stock +5,53 %" in t1 and "(s,S) +0,00 %" in t1 and "Capped (Kappe 1) +9,01 %" in t1


def test_verdict_learning_counts_against_mark_and_rules():
    cell = dict(L=4, K=5.0, updates=3000, final_gaps=[2.0133, 1.6505, 3.3155, 0.9377, 1.4002], ref_gaps={"bs": 20.2, "ss": 3.76, "cap": 18.88, "ssc": 3.633})
    kind, text = ev.verdict_learning(cell)
    assert "im Median +1,65 %" in text and "von +0,94 % bis +3,32 %" in text
    assert "Unter 2 %: 3 von 5" in text and "unter der besten Zweiparameterregel (+3,76 %): 5 von 5" in text and "unter (s,S) mit Kappe (+3,63 %): 5 von 5" in text
    assert "schlägt" not in text


def test_formatting_helpers():
    assert ev.fmt_k(1.3) == "1,3" and ev.fmt_k(3.0) == "3" and ev.fmt_k(0.05) == "0,05" and ev.fmt_k(7.5) == "7,5"
    assert ev.fmt_pct(-0.5) == "-0,50 %" and ev.fmt_pct(0.0) == "+0,00 %"
    assert ev.fmt_frac(0.5) == "1/2" and ev.fmt_frac(3) == "3"
