"""Erzeugt data/brg_karte.json: die vorgerechnete Karte (Rückstandsraster, Kreuzzellen verlorene Nachfrage mit Fixkosten, Lernläufe, übernommene Zahlen der Schwester-Demos).

Aufruf (im Repo-Ordner, Test-venv; OMP_NUM_THREADS=1 setzen, sonst bremsen die BLAS-Threads die kleinen Matrizen stark):
    python tools/build_karte.py --teil rueckstand     # 1.566 Zellen, Größenordnung 30 s
    python tools/build_karte.py --teil verloren       # 29 Zellen mit Aufzählung zur Kontrolle, Größenordnung 10 Minuten
    python tools/build_karte.py --teil lernen         # liest data/rohdaten/lernen_*.jsonl
    python tools/build_karte.py --teil uebernommen    # Zahlen aus den READMEs der Stücke 1 bis 6 (tools/uebernommen.py)
    python tools/build_karte.py --teil check          # Zelle Lieferzeit 4, K = 5: Aufzählung, Raster, ein Sweep der Positionsfunktion (Größenordnung 20 Minuten)
    python tools/build_karte.py --teil alles          # alle außer check
Jeder Teil ersetzt nur seinen Schlüssel in der Datei; die übrigen bleiben stehen. Rechenzeiten sind Größenordnungen unter Last, keine festen Zahlen."""

import argparse
import glob
import json
import os
import re
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "1")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import numpy as np  # noqa: E402

import brg_backorder as B  # noqa: E402
import brg_constants as C  # noqa: E402
import brg_lost as V  # noqa: E402
from brg_gap import clip_noise, gap  # noqa: E402

OUT = os.path.join(ROOT, "data", "brg_karte.json")


def _load():
    if os.path.exists(OUT):
        with open(OUT, encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data, keys):
    """Schreibt nur die genannten Schlüssel: die Datei wird vorher neu gelesen, damit parallel laufende Teile einander nicht überschreiben."""
    current = _load()
    for k in keys:
        current[k] = data[k]
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    tmp = OUT + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        json.dump(current, f, ensure_ascii=False, separators=(",", ":"))
    os.replace(tmp, OUT)
    print(f"geschrieben: {OUT} ({os.path.getsize(OUT) / 1024:.0f} kB)", flush=True)


def part_rueckstand(data):
    t0 = time.time()
    rows, worst = [], dict(edge_lo=0.0, edge_hi=0.0, qcap=0.0, not_pure=0)
    for p in C.B_PH:
        for L in C.B_L:
            for K in C.B_K:
                r = B.solve(L, K, p)
                rows.append([p, L, K, round(r["g"], 9), round(r["gb"], 9), r["Sb"], round(r["gap_bs"], 6), r["s"], r["S"], int(r["pure_ss"]),
                             round(r["pord"], 6), round(r["gap_ss"], 9)])
                worst["edge_lo"] = max(worst["edge_lo"], r["edge_lo"])
                worst["edge_hi"] = max(worst["edge_hi"], r["edge_hi"])
                worst["qcap"] = max(worst["qcap"], r["qcap"])
                worst["not_pure"] += int(not r["pure_ss"])
        print(f"p/h = {p} fertig ({time.time() - t0:.0f} s)", flush=True)
    data["rueckstand"] = dict(
        spalten=["p_h", "L", "K", "g_dp", "g_base_stock", "S_base_stock", "gap_base_stock_pct", "s_dp", "S_dp", "dp_pure_ss", "order_share_dp", "gap_ss_pct"],
        modell=dict(mean=C.MEAN, h=C.H, Q=C.B_Q, zmin=C.B_ZMIN, ymax=C.B_YMAX, dmax=C.B_DMAX, zustand="Bestandsposition"),
        zellen=len(rows), ohne_reine_ss_form=worst["not_pure"], rand_unten_max=worst["edge_lo"], rand_oben_max=worst["edge_hi"], bestellgrenze_max=worst["qcap"],
        rows=rows)


def part_verloren(data):
    cells = []
    t0 = time.time()
    for L in C.V_L:
        for K in C.V_MEASURED[L]:
            cell = V.solve_cell(L, K, enumerate_check=(L <= 3))
            cell["g"] = round(cell["g"], 9)
            cells.append(cell)
            print(f"L={L} K={K:g}: {cell['gaps']} {cell['params']} ({time.time() - t0:.0f} s)", flush=True)
    data["verloren"] = dict(
        modell=dict(mean=C.MEAN, h=C.H, p_h=C.V_PH, Q=C.V_Q, XM=C.V_XM, dmax=C.V_DMAX, smax=C.V_SMAX, zustand="Bestand und Pipeline"),
        zellen=cells)


def _gap_of(g, g_dp):
    return 100.0 * (g / g_dp - 1.0)


def part_lernen(data):
    out = dict(quelle="data/rohdaten/lernen_L*_K*_s*.jsonl", update_pro_messung=25600, zellen=[])
    groups = {}
    for f in sorted(glob.glob(os.path.join(ROOT, "data", "rohdaten", "lernen_L*_K*_s*.jsonl"))):
        m = re.search(r"lernen_L(\d)_K([\d.]+)_s(\d+)\.jsonl", f)
        with open(f, encoding="utf-8") as fh:
            recs = [json.loads(z) for z in fh if z.strip()]
        fin = [r for r in recs if r.get("final")]
        pts = [r for r in recs if "update" in r]
        assert fin and pts and pts[-1]["update"] == 3000, f
        groups.setdefault((int(m.group(1)), float(m.group(2))), {})[int(m.group(3))] = (fin[0], pts)
    for (L, K), runs in sorted(groups.items()):
        seeds = sorted(runs)
        g_dp = runs[seeds[0]][0]["g_dp"]
        refs = runs[seeds[0]][0]["refs"]
        finals = [round(_gap_of(runs[s][0]["g"], g_dp), 4) for s in seeds]
        late = [[_gap_of(p["g"], g_dp) for p in runs[s][1] if p["update"] >= 1000] for s in seeds]
        mean15 = [round(float(np.mean([_gap_of(p["g"], g_dp) for p in runs[s][1] if p["update"] >= 1500])), 4) for s in seeds]
        worst_diff = min(min(runs[s][0]["g"] - g_dp, min(p["g"] - g_dp for p in runs[s][1])) for s in seeds)
        out["zellen"].append(dict(
            L=L, K=K, g_dp=round(g_dp, 6), seeds=seeds, final_gaps=finals, mean_gap_from_update_1500=mean15,
            ref_gaps={k: round(_gap_of(v, g_dp), 4) for k, v in refs.items()},
            points_from_1000=dict(n=int(sum(len(x) for x in late)), share_below_2=round(float(np.mean([v < 2.0 for x in late for v in x])), 4),
                                  max_gap=round(max(max(x) for x in late), 4), min_gap=round(min(min(x) for x in late), 4)),
            updates=3000, periods_total=int(runs[seeds[0]][1][-1]["periods"]), min_diff_to_dp=float(worst_diff)))
    data["lernen"] = out


def part_uebernommen(data):
    import uebernommen as U
    data["uebernommen"] = U.ENTRIES
    data["rechengrenze"] = U.RECHENGRENZE


def part_check(data):
    """Zelle Lieferzeit 4, K = 5: Aufzählung aller (s,S), Raster (s,S,Kappe) um das beste (s,S), ein Sweep der Positionsfunktion (Koordinatenabstieg)."""
    L, K = 4, 5.0
    m = V.LostSales(L, K)
    g, pol, _, _ = m.rvi()
    t0 = time.time()
    res = dict(L=L, K=K, g_dp=round(g, 9), states=m.S)
    best = (1e18, None)
    for S in range(2, C.V_SMAX + 1):
        for s in range(0, S):
            v = m.evaluate(m.pol_ss(s, S))[0]
            if v < best[0]:
                best = (v, (s, S))
    res["enum_ss"] = dict(params=list(best[1]), gap=round(gap(best[0], g), 4), seconds=round(time.time() - t0))
    print("Aufzählung (s,S):", res["enum_ss"], flush=True)
    s0, S0 = best[1]
    bests, n = (1e18, None), 0
    for s in range(max(s0 - 3, 0), s0 + 4):
        for S in range(max(S0 - 3, s + 1), S0 + 5):
            for cap in range(2, m.Q + 1):
                v = m.evaluate(m.pol_ss(s, S, cap))[0]
                n += 1
                if v < bests[0]:
                    bests = (v, (s, S, cap))
    res["raster_ssc"] = dict(params=list(bests[1]), gap=round(gap(bests[0], g), 4), evaluations=n, seconds=round(time.time() - t0))
    print("Raster (s,S,Kappe):", res["raster_ssc"], flush=True)
    s, S, cap = bests[1]
    ipmax = 34

    def pol_pos(f):
        return f[np.minimum(m.IP, len(f) - 1)].astype(np.int16)

    f = np.clip(np.array([min(cap, S - v) if v <= s else 0 for v in range(ipmax + 1)], dtype=int), 0, m.Q)
    gcur = m.evaluate(pol_pos(f))[0]
    nev = 1
    for v in range(0, ipmax + 1):
        keep = f[v]
        bv, ba = gcur, keep
        for a in range(m.Q + 1):
            if a == keep:
                continue
            f[v] = a
            gg = m.evaluate(pol_pos(f))[0]
            nev += 1
            if gg < bv - 1e-12:
                bv, ba = gg, a
        f[v] = ba
        if ba != keep:
            gcur = bv
    res["position_function"] = dict(sweeps=1, gap=round(gap(gcur, g), 4), evaluations=nev, seconds=round(time.time() - t0),
                                    table=[int(a) for a in f], converged=False, art="obere Schranke (lokale Suche, ein Sweep)")
    print("Positionsfunktion nach einem Sweep:", res["position_function"]["gap"], flush=True)
    data["check_L4_K5"] = res


KEYS = dict(rueckstand=["rueckstand"], verloren=["verloren"], lernen=["lernen"], uebernommen=["uebernommen", "rechengrenze"], check=["check_L4_K5"])
PARTS = dict(rueckstand=part_rueckstand, verloren=part_verloren, lernen=part_lernen, uebernommen=part_uebernommen, check=part_check)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--teil", default="alles", choices=list(PARTS) + ["alles"])
    args = ap.parse_args()
    data = _load()
    for name in (["rueckstand", "verloren", "lernen", "uebernommen"] if args.teil == "alles" else [args.teil]):
        PARTS[name](data)
        _save(data, KEYS[name])  # nach jedem Teil sichern: ein langer Lauf geht nicht verloren
    data["meta"] = dict(erzeugt_von="tools/build_karte.py", hinweis="Rechenzeiten (seconds) sind Größenordnungen unter Last, keine festen Zahlen.")
    _save(data, ["meta"])


if __name__ == "__main__":
    main()
