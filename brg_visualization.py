"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben.
Beschriftungen stehen als Annotation oder Heatmap-Text, nicht als Text-Spur; kategoriale Achsen tragen Text-Beschriftungen (L = 0, K = 0,5)."""

import plotly.graph_objects as go

import brg_constants as C
import brg_data as D
from brg_ladder import RULE_LABELS


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360, bottom=10):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=bottom), legend=dict(orientation="h", y=-0.25), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _k_label(K) -> str:
    s = f"{float(K):.2f}".rstrip("0").rstrip(".")
    return "K = " + s.replace(".", ",")


def _g(x, nd=2) -> str:
    return f"{x:.{nd}f}".replace(".", ",")


def build_map(k: dict, selected=None):
    """Karte: Zeilen K, Spalten Lieferzeit; Farbe = Stufe, Zahl = Lücke der Regel der Stufe in Prozent der DP-Kosten (grau: nicht gemessen).
    `selected`: (L, K) der gewählten Zelle, wird umrandet."""
    xs = [f"L = {L}" for L in k["L"]]
    ys = [_k_label(K) for K in k["K"]]
    z, text, hover = [], [], []
    for row in k["cells"]:
        zr, tr, hr = [], [], []
        for c in row:
            if c is None:
                zr.append(None)
                tr.append("")
                hr.append("nicht gemessen")
            else:
                zr.append(c["rung"])
                tr.append("0" if abs(c["gap"]) < 0.005 else _g(c["gap"], 2))
                parts = [f"{RULE_LABELS[key]} {_g(v)} %" for key, v in c["gaps"].items() if v is not None]
                hr.append(f"Stufe {c['rung']}; " + "; ".join(parts))
        z.append(zr)
        text.append(tr)
        hover.append(hr)
    colorscale = []
    for r in (1, 2, 3, 4):
        lo, hi = (r - 1) / 4.0, r / 4.0
        colorscale += [[lo, C.RUNG_COLORS[r]], [hi, C.RUNG_COLORS[r]]]
    fig = go.Figure(go.Heatmap(z=z, x=xs, y=ys, text=text, texttemplate="%{text}", customdata=hover, hovertemplate="%{y}, %{x}<br>%{customdata}<extra></extra>",
                               colorscale=colorscale, zmin=0.5, zmax=4.5, showscale=False, xgap=3, ygap=3, textfont=dict(color="white", size=13)))
    for r in (1, 2, 3, 4):
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", marker=dict(size=12, symbol="square", color=C.RUNG_COLORS[r]), name=f"Stufe {r}"))
    if selected is not None and selected[0] in k["L"] and any(abs(selected[1] - kk) < 1e-9 for kk in k["K"]):
        i = k["L"].index(selected[0])
        j = next(n for n, kk in enumerate(k["K"]) if abs(selected[1] - kk) < 1e-9)
        fig.add_shape(type="rect", x0=i - 0.5, x1=i + 0.5, y0=j - 0.5, y1=j + 0.5, line=dict(color="#111111", width=3))
    fig.update_yaxes(autorange="reversed", title_text="Fixkosten K (in Einheiten von h)")
    fig.update_xaxes(title_text="Lieferzeit L (Perioden)", side="bottom")
    return _base(fig, height=420, bottom=10)


def build_gap_bars(view, marke):
    """Balken der Lücken aller Regeln der Zelle mit der Marke als senkrechte Linie; Regeln ohne Wert fehlen."""
    keys = [k for k in ("bs", "ss", "cap", "ssc") if view.gaps.get(k) is not None]
    labels = [RULE_LABELS[k] for k in keys]
    vals = [max(view.gaps[k], 0.0) for k in keys]
    colors = [C.RUNG_COLORS[2] if view.gaps[k] < marke else C.RUNG_COLORS[4] for k in keys]
    fig = go.Figure(go.Bar(y=labels, x=vals, orientation="h", marker_color=colors,
                           hovertemplate="%{y}: %{x:.2f} % über der DP<extra></extra>"))
    fig.add_vline(x=marke, line=dict(color="#111111", dash="dash", width=2))
    fig.add_annotation(x=marke, y=1.0, yref="paper", text=f"Marke {marke} %", showarrow=False, yanchor="bottom", bgcolor="rgba(255,255,255,0.85)", font=dict(color="#111111"))
    fig.update_xaxes(title_text="Lücke gegen die DP (%)", rangemode="tozero")
    fig.update_yaxes(autorange="reversed")
    return _base(fig, height=260)


def build_gap_over_k(p_h, marke):
    """Rückstand: Lücke von Base-Stock über K (Raster 0 bis 4) für Lieferzeit 0 bis 5; die Marke als waagerechte Linie."""
    fig = go.Figure()
    ks = [K for K in C.B_K if K <= 4.0]
    for L in C.B_L:
        ys = [D.backorder_cell(p_h, L, K)["gap_base_stock_pct"] for K in ks]
        fig.add_trace(go.Scatter(x=ks, y=ys, mode="lines", name=f"L = {L}", hovertemplate=f"L = {L}, K = %{{x}}: %{{y:.2f}} %<extra></extra>"))
    fig.add_hline(y=marke, line=dict(color="#111111", dash="dash", width=2))
    fig.add_annotation(x=0, y=marke, xref="x", yref="y", text=f"Marke {marke} %", showarrow=False, xanchor="left", yanchor="bottom", bgcolor="rgba(255,255,255,0.85)",
                       font=dict(color="#111111"))
    fig.update_xaxes(title_text="Fixkosten K (in Einheiten von h)")
    fig.update_yaxes(title_text="Lücke von Base-Stock (%)", rangemode="tozero")
    return _base(fig, height=340, bottom=40)


def build_hand_lines(lines: dict, hull, K, k_max, title_y="Kosten je Periode g(K)"):
    """Handbeispiel: Gerade je benannter Regel (float), untere Hülle als dicke graue Linie, senkrechte Linie beim gewählten K. lines: Name -> Line."""
    fig = go.Figure()
    xs = [0.0, float(k_max)]
    hx, hy = [], []
    for (k0, ln), nxt in zip(hull, list(hull[1:]) + [None]):
        k1 = float(nxt[0]) if nxt is not None else float(k_max)
        for kk in (float(k0), k1):
            hx.append(kk)
            hy.append(float(ln.value(kk)))
    fig.add_trace(go.Scatter(x=hx, y=hy, mode="lines", line=dict(color=C.COLOR_MUTED, width=9), name="Optimum (untere Hülle aller Politiken)", hoverinfo="skip"))
    palette = [C.RUNG_COLORS[1], C.RUNG_COLORS[3], C.RUNG_COLORS[4], C.COLOR_LINE]
    for (name, ln), col in zip(lines.items(), palette):
        fig.add_trace(go.Scatter(x=xs, y=[float(ln.value(x)) for x in xs], mode="lines", line=dict(color=col, width=2.5), name=name,
                                 hovertemplate=f"{name}<br>K = %{{x:.2f}}: %{{y:.3f}}<extra></extra>"))
    fig.add_vline(x=float(K), line=dict(color="#111111", dash="dot", width=1.5))
    fig.update_xaxes(title_text="Fixkosten K (in Einheiten von h)", range=[0, float(k_max)])
    fig.update_yaxes(title_text=title_y)
    return _base(fig, height=380, bottom=60)


def build_learning(cell: dict, marke=2):
    """Lernläufe einer Zelle: Endstand je Zufalls-Seed (Punkte) gegen die Lücken der Regeln (senkrechte Linien) und die Marke 2 %."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cell["final_gaps"], y=[f"Seed {s}" for s in cell["seeds"]], mode="markers", marker=dict(size=12, color=C.RUNG_COLORS[1]),
                             name="Endstand je Zufalls-Seed", hovertemplate="%{y}: %{x:.2f} %<extra></extra>"))
    lines = [("ss", "(s,S)", C.RUNG_COLORS[2]), ("cap", "Capped", C.RUNG_COLORS[3]), ("ssc", "(s,S) mit Kappe", C.RUNG_COLORS[4])]
    for i, (key, label, col) in enumerate(lines):
        x = cell["ref_gaps"][key]
        fig.add_vline(x=x, line=dict(color=col, dash="dash", width=2))
        fig.add_annotation(x=x, y=1.0, yref="paper", text=label, showarrow=False, yanchor="bottom", bgcolor="rgba(255,255,255,0.85)", font=dict(color="#111111", size=10),
                           yshift=14 * (i % 2))
    fig.add_vline(x=marke, line=dict(color="#111111", dash="dot", width=1.5))
    fig.update_xaxes(title_text="Lücke gegen die DP (%)", rangemode="tozero")
    fig.update_yaxes(autorange="reversed")
    return _base(fig, height=300, bottom=40)
