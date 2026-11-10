"""Permalink (Begrenzen und Einrasten), Presets und Seitenleisten-Schnellstart (Standardmuster aus dem Demo-Portfolio)."""

from dataclasses import dataclass

import streamlit as st

import brg_constants as C


@dataclass(frozen=True)
class SettingSpec:
    url_param: str
    caster: type
    default: object
    lo: float | None = None
    hi: float | None = None
    options: tuple | None = None   # Auswahlregler: erlaubte Werte; ein Wert aus der Adresszeile rastet auf den nächsten ein


DEFAULTS = C.PRESETS[C.DEFAULT_PRESET]

SETTING_SPECS = {
    "modus_radio": SettingSpec("modus", str, DEFAULTS["modus"], options=C.MODI),
    "L_slider": SettingSpec("L", int, DEFAULTS["L"], min(C.B_L), max(C.B_L)),
    "K_select": SettingSpec("K", float, DEFAULTS["K"], options=C.B_K),
    "ph_select": SettingSpec("ph", int, DEFAULTS["ph"], options=C.B_PH),
    "marke_select": SettingSpec("marke", int, DEFAULTS["marke"], options=C.MARKEN),
    "Khand_select": SettingSpec("Kh", float, DEFAULTS["K_hand"], options=C.HAND_K),
    "struktur_select": SettingSpec("struktur", str, DEFAULTS["struktur"], options=C.STRUKTUREN),
}
PRESET_KEYS = {"modus": "modus_radio", "L": "L_slider", "K": "K_select", "ph": "ph_select", "marke": "marke_select", "K_hand": "Khand_select",
               "struktur": "struktur_select"}


def init_session_state_defaults():
    for state_key, spec in SETTING_SPECS.items():
        if state_key not in st.session_state:
            st.session_state[state_key] = spec.default


def bounds(state_key):
    spec = SETTING_SPECS[state_key]
    return spec.lo, spec.hi


def _snap(spec: SettingSpec, value):
    """Wert auf die Reglergrenzen begrenzen bzw. auf die nächste erlaubte Option einrasten; None, wenn ein Text keine Option ist."""
    if spec.options is not None:
        if spec.caster is str:
            return value if value in spec.options else None
        return min(spec.options, key=lambda o: abs(o - value))
    if spec.lo is not None:
        value = max(spec.lo, value)
    if spec.hi is not None:
        value = min(spec.hi, value)
    return value


def load_permalink_settings():
    """Einmal je Sitzung: Werte aus der Adresszeile übernehmen, begrenzt bzw. auf die erlaubten Werte eingerastet."""
    if "permalink_loaded" in st.session_state:
        return
    qp = st.query_params
    for state_key, spec in SETTING_SPECS.items():
        if spec.url_param in qp:
            try:
                value = spec.caster(qp[spec.url_param])
            except (ValueError, TypeError):
                continue
            value = _snap(spec, value)
            if value is not None:
                st.session_state[state_key] = value
    st.session_state["permalink_loaded"] = True


def sync_query_params(values):
    """`values`: {state_key: aktueller Wert}; die Adresszeile spiegelt die Konfiguration."""
    try:
        for state_key, value in values.items():
            st.query_params[SETTING_SPECS[state_key].url_param] = str(value)
    except Exception:
        pass


def apply_preset(name):
    for key, state_key in PRESET_KEYS.items():
        if key in C.PRESETS[name]:
            st.session_state[state_key] = C.PRESETS[name][key]


def aktives_preset():
    """Name des Presets, dessen Werte GENAU den aktuellen Einstellungen entsprechen, sonst None.

    Zustandslos: verglichen wird jeder Regler aus SETTING_SPECS (ein Preset ohne Eintrag für einen Regler meint dessen Standardwert) mit dem Session State.
    Ein später ergänzter Regler braucht nur seinen Eintrag in SETTING_SPECS, dann hebt auch seine Änderung die Markierung auf (tests/test_layout.py prüft das für jeden Regler)."""
    preset_key_of = {state_key: key for key, state_key in PRESET_KEYS.items()}
    for name, preset in C.PRESETS.items():
        if all(
            st.session_state.get(state_key, spec.default) == preset.get(preset_key_of.get(state_key), spec.default)
            for state_key, spec in SETTING_SPECS.items()
        ):
            return name
    return None


def sidebar_presets():
    """Schnellstart oben in der Seitenleiste; das aktive Preset ist hervorgehoben (`type="primary"`)."""
    if not C.PRESETS:
        return
    st.header("🎯 Schnellstart")
    st.caption("Ein Beispielszenario laden:")
    aktiv = aktives_preset()
    for name in C.PRESETS:
        st.button(
            name, width="stretch", on_click=apply_preset, args=(name,), help=C.PRESET_HELP.get(name, ""), key=f"preset_{name}",
            type="primary" if aktiv == name else "secondary",
        )
