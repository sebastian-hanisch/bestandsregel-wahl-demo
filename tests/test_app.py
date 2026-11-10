"""End-to-end Smoke-Test via Streamlits AppTest: lädt app.py, klickt jedes Preset und jeden Button, fährt jeden Regler an seine Grenzen, prüft Permalink und Reiter.

Geprüft wird, dass kein Python-Fehler auftritt (insbesondere `StreamlitDuplicateElementId` bei Diagrammen ohne eindeutiges key= und Fehler bei Auswahlreglern mit
Werten außerhalb der Optionen) und dass die Reiter Inhalt haben. Zahlen im Text prüfen test_verdicts.py, test_tree.py und test_claims.py."""

import os
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

import brg_constants as C
import brg_presets as P

APP_PATH = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))  # unter Last (parallele Läufe) reichen 180 s nicht immer; Umgebungsvariable zum Anpassen


def _fresh_app() -> AppTest:
    at = AppTest.from_file(APP_PATH)
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at) -> str:
    parts = [e.value for e in at.markdown] + [e.value for e in at.caption] + [e.value for e in at.info] + [e.value for e in at.success] + [e.value for e in at.warning] + [e.value for e in at.error]
    return "\n".join(parts)


def test_app_loads_without_exception():
    at = _fresh_app()
    assert at.title and [m.label for m in at.metric][:2] == ["DP (Kosten je Periode)", "Base-Stock (S = 17)"]
    assert len(at.tabs) == 5


@pytest.mark.parametrize("name", list(C.PRESETS))
def test_every_preset_runs_and_shows_a_verdict(name):
    at = _fresh_app()
    at.sidebar.button(key=f"preset_{name}").click().run(timeout=TIMEOUT)
    assert not at.exception, (name, [str(e) for e in at.exception])
    text = _texts(at)
    assert "Kleinste Stufe unter" in text or "Base-Stock reicht nicht mehr" in text or "Zwei Schwächen zugleich" in text or "Keine einfache Regel unter" in text, name


def test_every_button_click_does_not_raise():
    labels = [b.label for b in _fresh_app().button]
    assert labels, "keine Buttons gefunden"
    for index, label in enumerate(labels):
        at = _fresh_app()
        at.button[index].click().run(timeout=TIMEOUT)
        assert not at.exception, (label, [str(e) for e in at.exception])


def test_every_control_at_its_extremes_does_not_raise():
    for state_key, spec in P.SETTING_SPECS.items():
        values = [spec.options[0], spec.options[-1]] if spec.options is not None else [spec.lo, spec.hi]
        for value in values:
            at = _fresh_app()
            for art in ("slider", "select_slider", "selectbox", "radio"):
                try:
                    getattr(at.sidebar, art)(key=state_key).set_value(value)
                    break
                except KeyError:
                    continue
            at.run(timeout=TIMEOUT)
            assert not at.exception, (state_key, value, [str(e) for e in at.exception])


def test_lost_lead_time_zero_and_unmeasured_cells_show_a_hint_not_an_error():
    at = _fresh_app()
    at.sidebar.radio(key="modus_radio").set_value(C.MODUS_LOST)
    at.sidebar.slider(key="L_slider").set_value(0)
    at.run(timeout=TIMEOUT)
    assert not at.exception
    assert any("nicht gemessen" in w.value for w in at.warning)
    at.sidebar.slider(key="L_slider").set_value(5)
    at.run(timeout=TIMEOUT)
    assert not at.exception and any("Lieferzeit 5" in w.value for w in at.warning)


def test_permalink_values_are_taken_over_and_snapped():
    at = AppTest.from_file(APP_PATH)
    at.query_params["modus"] = C.MODUS_LOST
    at.query_params["L"] = "99"
    at.query_params["K"] = "1.23"
    at.query_params["marke"] = "4"
    at.query_params["struktur"] = "Unsinn"
    at.run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert at.sidebar.radio(key="modus_radio").value == C.MODUS_LOST
    assert at.sidebar.slider(key="L_slider").value == 5                    # begrenzt
    assert at.sidebar.select_slider(key="K_select").value == 1.25          # eingerastet
    assert at.sidebar.select_slider(key="marke_select").value in (2, 5)    # eingerastet (4 liegt näher an 5)
    assert at.sidebar.selectbox(key="struktur_select").value == C.STRUKTUREN[0]   # unbekannter Text: Standard


def test_live_recalculation_button_for_backorder_and_lost():
    at = _fresh_app()
    at.button(key="live_button").click().run(timeout=TIMEOUT)
    assert not at.exception and any("Live gerechnet" in s.value for s in at.success)
    at = _fresh_app()
    at.sidebar.button(key="preset_Handbeispiel B (verloren, K)").click().run(timeout=TIMEOUT)
    at.button(key="live_button").click().run(timeout=TIMEOUT)
    assert not at.exception and any("Live gerechnet" in s.value and "vorgerechneten Karte" in s.value for s in at.success)


def test_simulation_probe_button_for_a_lost_cell():
    at = _fresh_app()
    at.sidebar.button(key="preset_Handbeispiel B (verloren, K)").click().run(timeout=TIMEOUT)
    at.button(key="sim_button").click().run(timeout=TIMEOUT)
    assert not at.exception, [str(e) for e in at.exception]
    assert any("Simuliert (Mittel je Periode)" in " ".join(map(str, df.value.columns)) for df in at.dataframe)


def test_tabs_have_content_and_tree_reacts_to_the_structure():
    at = _fresh_app()
    text = _texts(at)
    for needle in ("Handbeispiel A (Rückstand, Lieferzeit 0)", "Blatt:", "Rechengrenze.", "Was diese Karte"):
        assert needle in text, needle
    at.sidebar.selectbox(key="struktur_select").set_value(C.STRUKTUREN[1]).run(timeout=TIMEOUT)
    assert not at.exception
    assert at.radio(key="tree_ausgabe").value == "LIFO"
    at.sidebar.slider(key="L_slider").set_value(0).run(timeout=TIMEOUT)
    at.radio(key="tree_ausgabe").set_value("FIFO").run(timeout=TIMEOUT)
    assert not at.exception and "26 von 30" in _texts(at)
    at.radio(key="tree_ausgabe").set_value("LIFO").run(timeout=TIMEOUT)
    assert not at.exception and "26 von 30" not in " ".join(s.value for s in at.success) and "+26,69 %" in _texts(at)


def test_app_has_the_assumptions_expander_and_the_math_expander():
    at = _fresh_app()
    labels = [e.label for e in at.expander]
    assert "⚠️ Annahmen, Grenzen und bekannte Probleme" in labels and "📐 Mathematische Formulierung" in labels
