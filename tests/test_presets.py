"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen; Hilfetexte gegen die Messung (DEMO-PLAYBOOK §11a Punkt 7)."""

import brg_constants as C
import brg_data as D
import brg_evaluation as ev
import brg_presets as P
from brg_ladder import rung


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_valid_option_values():
    for name, preset in C.PRESETS.items():
        for key, state_key in P.PRESET_KEYS.items():
            spec = P.SETTING_SPECS[state_key]
            value = preset[key]
            if spec.options is not None:
                assert value in spec.options, (name, key, value)
            else:
                assert spec.lo <= value <= spec.hi, (name, key, value)


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**dict(C.PRESETS[C.DEFAULT_PRESET])) == ev.Settings()
    assert all(P.SETTING_SPECS[sk].default == C.PRESETS[C.DEFAULT_PRESET][k] for k, sk in P.PRESET_KEYS.items())


def test_setting_specs_cover_every_preset_key():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)


def test_presets_are_pairwise_different():
    seen = {tuple(sorted((k, str(v)) for k, v in p.items())) for p in C.PRESETS.values()}
    assert len(seen) == len(C.PRESETS) == 9


def _cell(name):
    p = C.PRESETS[name]
    return ev.cell_view(ev.Settings(modus=p["modus"], L=p["L"], K=p["K"], ph=p["ph"], marke=p["marke"]))


def test_preset_cells_have_the_rung_their_help_text_claims():
    """Jedes Preset mit Zelle: die im Hilfetext genannte Aussage stimmt mit der gemessenen Stufe überein."""
    assert _cell(C.DEFAULT_PRESET).rung.rung == 2 and D.threshold_k(9, 3, 2) == 0.9 and "ab K = 0,9" in C.PRESET_HELP[C.DEFAULT_PRESET]
    lost0 = _cell("Nur Lieferzeit (verloren, K = 0, Lieferzeit 3)")
    assert lost0.gaps["bs"] > 2 and lost0.rung.rule == "cap" and "Base-Stock liegt bei Lieferzeit 3 über 2 %" in C.PRESET_HELP["Nur Lieferzeit (verloren, K = 0, Lieferzeit 3)"]
    both = _cell("Beides zugleich (verloren, Lieferzeit 3, K = 2)")
    assert both.rung.rung == 3 and min(both.gaps["ss"], both.gaps["cap"]) >= 2
    four = _cell("Keine einfache Regel (verloren, Lieferzeit 4, K = 5)")
    assert four.rung.rung == 4


def test_handbook_presets_are_the_cells_named_in_their_help():
    a, b = C.PRESETS["Handbeispiel A (Rückstand, K)"], C.PRESETS["Handbeispiel B (verloren, K)"]
    assert (a["modus"], a["L"], a["K"], a["K_hand"]) == (C.MODUS_BACKORDER, 0, 2.0, 2.0)
    assert (b["modus"], b["L"], b["K"], b["K_hand"]) == (C.MODUS_LOST, 1, 1.0, 1.0)
    assert ev.hand_a_gap(2.0) == 25                      # „Base-Stock 25 % über der besten Regel“
    assert "25 %" in C.PRESET_HELP["Handbeispiel A (Rückstand, K)"]


def test_structure_presets_choose_their_structure():
    assert C.PRESETS["Zwei Stufen: Lager sieht nichts"]["struktur"] == C.STRUKTUREN[2]
    assert C.PRESETS["Verderblich: LIFO"]["struktur"] == C.STRUKTUREN[1]
    assert C.PRESETS["Jenseits der DP (Stück 6, Lieferzeit 7 und 8)"]["struktur"] == C.STRUKTUREN[3]
    for name, stueck in (("Zwei Stufen: Lager sieht nichts", 5), ("Verderblich: LIFO", 4)):
        numbers = [w for w in C.PRESET_HELP[name].split() if w.startswith("+")]
        text = " ".join(e["aussage"] for e in D.uebernommen(stueck))
        assert numbers and all(n.strip(",.:;") in text for n in numbers), name       # jede Zahl des Hilfetextes steht in den übernommenen Aussagen


def test_permalink_values_snap_to_options():
    spec = P.SETTING_SPECS["K_select"]
    assert P._snap(spec, 1.23) == 1.25
    assert P._snap(spec, 29.0) == 30.0 and P._snap(spec, -4.0) == 0.0
    assert P._snap(P.SETTING_SPECS["modus_radio"], "Unsinn") is None and P._snap(P.SETTING_SPECS["modus_radio"], C.MODUS_LOST) == C.MODUS_LOST
    assert P._snap(P.SETTING_SPECS["L_slider"], 99) == 5 and P._snap(P.SETTING_SPECS["L_slider"], -3) == 0
