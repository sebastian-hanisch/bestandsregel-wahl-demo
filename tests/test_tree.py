"""Entscheidungsbaum: jedes Blatt an handgewählten Antworten, Zahlen im Text gegen die Karte."""

import pytest

import brg_data as D
import brg_tree as TR


def test_two_stages_leaf_names_the_views_and_says_fixed_costs_are_not_measured():
    lf = TR.leaf(dict(stufen="zwei", K=2.0))
    assert lf.id == "zwei_stufen" and lf.regel == "Echelon-Base-Stock" and "+3,73 bis +20,94 %" in lf.text and "Fixkosten bei zwei Stufen sind nicht gemessen" in lf.text
    assert lf.gemessen is False and TR.leaf(dict(stufen="zwei", K=0.0)).gemessen is True


def test_perishable_leaves_depend_on_the_issue_rule_and_the_lead_time():
    assert "26 von 30" in TR.leaf(dict(verderblich="fifo", L=0)).text
    assert "+1,36 bis +9,18 %" in TR.leaf(dict(verderblich="fifo", L=1)).text
    assert "zwischen +0,05 und +26,69 %" in TR.leaf(dict(verderblich="lifo", L=0)).text
    assert "+57,98 %" in TR.leaf(dict(verderblich="lifo", L=1)).text
    assert TR.leaf(dict(verderblich="lifo", L=2)).id == "nicht_gemessen"
    assert "nicht gemessen" in TR.leaf(dict(verderblich="fifo", L=0, K=1.0)).text


def test_backorder_leaf_is_base_stock_below_the_threshold_and_ss_above():
    low = TR.leaf(dict(fehlmenge="rueckstand", L=3, K=0.5, marke=2))
    high = TR.leaf(dict(fehlmenge="rueckstand", L=3, K=3.0, marke=2))
    assert low.id == "rueckstand_base_stock" and low.regel == "Base-Stock" and "0,91 %" in low.text
    assert high.id == "rueckstand_ss" and high.regel == "(s,S)" and "10,76 %" in high.text and "s = 13, S = 18" in high.text
    assert TR.leaf(dict(fehlmenge="rueckstand", L=3, K=1.0, marke=5)).id == "rueckstand_base_stock"       # dieselbe Zelle, andere Marke
    assert TR.leaf(dict(fehlmenge="rueckstand", L=3, K=1.0, marke=2)).id == "rueckstand_ss"


def test_backorder_leaf_for_unmeasured_k_and_lead_time():
    assert TR.leaf(dict(fehlmenge="rueckstand", L=3, K=1.234)).id == "nicht_gemessen"
    assert TR.leaf(dict(fehlmenge="rueckstand", L=6, K=1.0)).id == "nicht_gemessen"


@pytest.mark.parametrize("L,K,marke,expected", [
    (1, 1.0, 2, "verloren_stufe2"),   # (s,S) 1,27 %
    (2, 0.0, 2, "verloren_stufe2"),   # Capped 0,69 %
    (3, 2.0, 2, "verloren_stufe3"),   # nur (s,S) mit Kappe
    (3, 2.0, 5, "verloren_stufe1"),   # Base-Stock 4,98 % unter 5
    (1, 0.0, 2, "verloren_stufe1"),   # Base-Stock 1,75 %
])
def test_lost_leaves_follow_the_ladder(L, K, marke, expected):
    assert TR.leaf(dict(fehlmenge="verloren", L=L, K=K, marke=marke)).id == expected


def test_lost_rung4_leaf_depends_on_whether_the_dp_is_computable():
    dp = TR.leaf(dict(fehlmenge="verloren", L=4, K=5.0, marke=2, rechenbar=True))
    learned = TR.leaf(dict(fehlmenge="verloren", L=4, K=5.0, marke=2, rechenbar=False))
    assert dp.id == "verloren_dp" and "59.319" in dp.text
    assert learned.id == "verloren_gelernt" and "+0,94 bis +3,32 %" in learned.text and "fünf Zufalls-Seeds" in learned.text


def test_hypothetical_dp_limit_is_not_stated_as_a_fact_for_a_cell_whose_dp_was_computed():
    """Regression: Struktur „Jenseits der DP“ bei Lieferzeit 4, K = 5 (dort ist die DP gerechnet) behauptete „Die DP ist hier nicht rechenbar“."""
    cell = D.lost_cell(4, 5.0)
    assert cell["states"] == 59319
    learned = TR.leaf(dict(fehlmenge="verloren", L=4, K=5.0, marke=2, rechenbar=False))
    assert "Die DP ist hier nicht rechenbar" not in learned.text
    assert "Angenommen, die DP wäre hier nicht rechenbar" in learned.text and "dort ist die DP gerechnet" in learned.text


def test_lost_leaf_without_measurement_gives_a_reason():
    assert TR.leaf(dict(fehlmenge="verloren", L=0, K=0.0)).id == "nicht_gemessen"
    assert TR.leaf(dict(fehlmenge="verloren", L=4, K=1.5)).id == "nicht_gemessen"
    assert TR.leaf(dict(fehlmenge="verloren", L=5, K=2.0)).id == "nicht_gemessen"
    jenseits = TR.leaf(dict(fehlmenge="verloren", L=5, K=0.0))
    assert jenseits.id == "verloren_k0_jenseits" and "unterschätzt die Lücke zum Optimum" in jenseits.text
    assert TR.leaf(dict(fehlmenge="verloren", L=4, K=0.0, rechenbar=False)).id == "verloren_k0_jenseits"


def test_defaults_give_a_backorder_leaf():
    assert TR.leaf({}).id == "rueckstand_base_stock"


def test_every_leaf_text_numbers_come_from_the_data():
    d = D.lost_cell(3, 2.0)
    lf = TR.leaf(dict(fehlmenge="verloren", L=3, K=2.0, marke=2))
    for key, name in (("bs", "Base-Stock"), ("ss", "(s,S)"), ("cap", "Capped"), ("ssc", "(s,S) mit Kappe")):
        assert f"{name} {d['gaps'][key]:.2f}".replace(".", ",") + " %" in lf.text
