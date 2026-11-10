"""Zweig-Tests (Nullspalte = Variante läuft nie, DEMO-PLAYBOOK §0): jede Variante weicht auf mindestens einer Zelle von der Nachbarvariante ab,
und die Zählungen der Stufen ändern sich mit der Marke."""

import brg_constants as C
import brg_data as D
import brg_evaluation as ev
from brg_ladder import distribution, rung

LOST_GAPS = [c["gaps"] for c in D.load()["verloren"]["zellen"]]


def test_the_mark_changes_the_distribution_of_rungs_over_the_29_lost_cells():
    assert distribution(LOST_GAPS, 1) == {1: 0, 2: 11, 3: 9, 4: 9}
    assert distribution(LOST_GAPS, 2) == {1: 2, 2: 20, 3: 6, 4: 1}
    assert distribution(LOST_GAPS, 5) == {1: 14, 2: 15, 3: 0, 4: 0}


def test_fixed_costs_change_the_rung_in_the_lost_branch():
    k0 = rung(D.lost_cell(3, 0.0)["gaps"], 2).rung
    k2 = rung(D.lost_cell(3, 2.0)["gaps"], 2).rung
    assert (k0, k2) == (2, 3)                                    # Lieferzeit 3: ohne K reicht Capped, mit K = 2 erst (s,S) mit Kappe


def test_the_cap_changes_ss_in_cell_lead_time_3_k_2():
    cell = D.lost_cell(3, 2.0)
    gaps = cell["gaps"]
    assert gaps["ss"] > gaps["ssc"] + 1.0 and gaps["cap"] > gaps["ssc"] + 1.0     # die dritte Parameterstufe wirkt (2,68 und 2,78 gegen 0,67)
    assert cell["params"]["ssc"][2] == 4 and cell["params"]["ss"] != cell["params"]["ssc"][:2]


def test_cell_lead_time_4_k_5_is_the_only_rung_four_at_mark_2():
    four = [(c["L"], c["K"]) for c in D.load()["verloren"]["zellen"] if rung(c["gaps"], 2).rung == 4]
    assert four == [(4, 5.0)]


def test_backorder_and_lost_branches_differ_in_the_same_nominal_cell():
    """Lieferzeit 3, K = 3: Rückstand Stufe 2 mit exaktem (s,S); verlorene Nachfrage hat dort ein anderes Bild (Zweiparameterregeln über der Marke)."""
    back = ev.cell_view(ev.Settings(modus=C.MODUS_BACKORDER, L=3, K=3.0))
    lost = ev.cell_view(ev.Settings(modus=C.MODUS_LOST, L=3, K=3.0))
    assert back.gaps["ss"] == 0.0 and lost.gaps["ss"] > 2.0
    assert back.gaps["bs"] != lost.gaps["bs"]
    assert back.rung.rung == 2 and lost.rung.rung == 3


def test_capped_helps_without_fixed_costs_and_does_not_help_with_large_fixed_costs():
    cells = D.load()["verloren"]["zellen"]
    k0 = [c for c in cells if c["K"] == 0.0]
    big = [c for c in cells if c["K"] >= 5.0]
    assert all(c["gaps"]["cap"] < c["gaps"]["ss"] for c in k0) and len(k0) == 4
    assert all(c["gaps"]["ss"] < c["gaps"]["cap"] for c in big) and len(big) == 8


def test_each_two_parameter_family_is_the_winner_of_a_rung_two_cell_somewhere():
    winners = {rung(c["gaps"], 2).rule for c in D.load()["verloren"]["zellen"] if rung(c["gaps"], 2).rung == 2}
    assert winners == {"ss", "cap"}


def test_every_rung_occurs_at_mark_2_in_the_union_of_both_modes():
    seen = set()
    for modus in C.MODI:
        for row in D.karte(modus, 2)["cells"]:
            seen |= {c["rung"] for c in row if c}
    assert seen == {1, 2, 3, 4}


def test_threshold_varies_with_the_lead_time_without_a_monotone_trend():
    ks = [D.threshold_k(9, L, 2) for L in C.B_L]
    assert ks == [1.3, 1.2, 1.3, 0.9, 1.2, 0.95]
    assert ks != sorted(ks) and ks != sorted(ks, reverse=True)
