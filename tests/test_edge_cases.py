"""Randfälle: Marke 0, K = 0, Lieferzeit 0 bei verlorener Nachfrage, Zellen ohne Messung, Gleichstände, Grenzen inklusive."""

import pytest

import brg_constants as C
import brg_data as D
import brg_evaluation as ev
import brg_lost as V
from brg_ladder import rung
from brg_lines import Line, crossing, lower_hull


def test_mark_zero_puts_every_cell_on_rung_four():
    for modus in C.MODI:
        k = D.karte(modus, 0)
        assert D.count_rungs(k)[4] == D.count_cells(k)


def test_a_very_large_mark_puts_every_cell_on_rung_one():
    for modus in C.MODI:
        k = D.karte(modus, 1000)
        assert D.count_rungs(k)[1] == D.count_cells(k)


def test_lead_time_zero_with_lost_sales_is_undefined():
    with pytest.raises(AssertionError):
        V.LostSales(0, 0.0)
    v = ev.cell_view(ev.Settings(modus=C.MODUS_LOST, L=0, K=0.0))
    assert not v.measured and "nicht vorgesehen" in v.why and "nicht definiert" not in v.why


def test_unmeasured_cells_give_a_reason_not_a_number():
    cases = [ev.Settings(modus=C.MODUS_LOST, L=4, K=1.5), ev.Settings(modus=C.MODUS_LOST, L=5, K=0.0), ev.Settings(modus=C.MODUS_LOST, L=2, K=1.0, ph=4),
             ev.Settings(modus=C.MODUS_BACKORDER, L=2, K=1.23), ev.Settings(modus=C.MODUS_BACKORDER, L=2, K=1.0, ph=7)]
    for s in cases:
        v = ev.cell_view(s)
        assert not v.measured and v.why and v.rung is None and v.gaps == {}


def test_k_zero_has_no_fixed_cost_effect_backorder_base_stock_is_the_dp():
    for L in C.B_L:
        for p in C.B_PH:
            assert abs(D.backorder_cell(p, L, 0.0)["gap_base_stock_pct"]) < 1e-5


def test_k_grid_boundaries_are_inclusive():
    assert D.backorder_cell(9, 0, 0.0) is not None and D.backorder_cell(9, 5, 30.0) is not None and D.backorder_cell(19, 5, 4.0) is not None
    assert D.backorder_cell(9, 5, 30.05) is None and D.backorder_cell(9, 6, 0.0) is None and D.backorder_cell(9, -1, 0.0) is None


def test_threshold_none_when_the_mark_is_never_reached_and_first_k_when_reached_at_k_zero():
    assert D.threshold_k(9, 3, 500) is None
    assert D.threshold_k(9, 3, 0) == 0.0                      # Lücke >= 0 gilt schon bei K = 0


def test_k_formatting_of_grid_values():
    assert [ev.fmt_k(k) for k in (0.0, 0.05, 1.3, 7.5, 30.0)] == ["0", "0,05", "1,3", "7,5", "30"]


def test_equal_lines_and_single_line_hull():
    assert lower_hull([Line(2.0, 1.0), Line(2.0, 1.0)], 10.0) == [(0.0, Line(2.0, 1.0))]
    assert crossing(Line(1.0, 1.0), Line(1.0, 1.0)) is None


def test_ties_between_ss_and_cap_prefer_ss():
    assert rung({"bs": 5.0, "ss": 1.5, "cap": 1.5, "ssc": 1.5}, 2).rule == "ss"


def test_takt_formula_by_hand():
    assert D.eoq_takt(1.5) == pytest.approx(1.0)               # sqrt(2 * 1,5 / (1 * 3)) = 1
    assert D.eoq_takt(0.0) == 0.0
