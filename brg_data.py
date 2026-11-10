"""Zugriff auf die vorgerechnete Karte data/brg_karte.json (Erzeugung: tools/build_karte.py) und daraus abgeleitete Größen.

Die Datei enthält: das Rückstandsraster (1.566 Zellen), die Kreuzzellen der verlorenen Nachfrage mit Fixkosten (29 Zellen), die Lernläufe, die Gegenprobe der Zelle
Lieferzeit 4 / K = 5 und die aus den Schwester-Demos übernommenen Zahlen mit Quelle."""

import json
from functools import lru_cache
from math import sqrt
from pathlib import Path

import brg_constants as C
from brg_ladder import rung

DATA_PATH = Path(__file__).resolve().parent / "data" / "brg_karte.json"
_COLS = ("p_h", "L", "K", "g_dp", "g_base_stock", "S_base_stock", "gap_base_stock_pct", "s_dp", "S_dp", "dp_pure_ss", "order_share_dp", "gap_ss_pct")


@lru_cache(maxsize=1)
def load() -> dict:
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _backorder_index() -> dict:
    rows = load()["rueckstand"]["rows"]
    assert tuple(load()["rueckstand"]["spalten"]) == _COLS
    return {(int(r[0]), int(r[1]), round(float(r[2]), 2)): dict(zip(_COLS, r)) for r in rows}


@lru_cache(maxsize=1)
def _lost_index() -> dict:
    return {(c["L"], round(c["K"], 2)): c for c in load()["verloren"]["zellen"]}


def backorder_cell(p_h: int, L: int, K: float):
    """Zelle des Rückstandsrasters oder None, wenn nicht gemessen."""
    return _backorder_index().get((int(p_h), int(L), round(float(K), 2)))


def lost_cell(L: int, K: float, p_h: int = C.V_PH):
    """Zelle der verlorenen Nachfrage oder None (nur p/h = 9, Lieferzeit 1 bis 4, bei Lieferzeit 4 nur fünf Werte von K)."""
    if int(p_h) != C.V_PH:
        return None
    return _lost_index().get((int(L), round(float(K), 2)))


def backorder_gaps(cell: dict) -> dict:
    """Lücken der Regeln des Rückstands in Prozent: Base-Stock und (s,S) (exakt: reine Form der DP-Politik). Capped und (s,S) mit Kappe gibt es dort nicht."""
    return {"bs": cell["gap_base_stock_pct"], "ss": cell["gap_ss_pct"], "cap": None, "ssc": None}


def lost_gaps(cell: dict) -> dict:
    return dict(cell["gaps"])


def cell_gaps(modus: str, p_h: int, L: int, K: float):
    """(Lücken, Zelle) oder (None, None), wenn die Zelle nicht gemessen ist."""
    if modus == C.MODUS_BACKORDER:
        cell = backorder_cell(p_h, L, K)
        return (backorder_gaps(cell), cell) if cell else (None, None)
    cell = lost_cell(L, K, p_h)
    return (lost_gaps(cell), cell) if cell else (None, None)


def karte(modus: str, marke: float, p_h: int = 9) -> dict:
    """Raster der Karte: Zeilen K in KARTE_K, Spalten Lieferzeit (Rückstand 0 bis 5, verloren 1 bis 4). Je Zelle ein Wörterbuch mit Stufe, Regel, Lücke der Stufe
    und allen Lücken; None für nicht gemessene Zellen. Bei Stufe 4 steht die kleinste Lücke aller Regeln in `gap` (mit ihrer Regel in `rule`)."""
    ls = C.B_L if modus == C.MODUS_BACKORDER else C.V_L
    cells = []
    for K in C.KARTE_K:
        row = []
        for L in ls:
            gaps, cell = cell_gaps(modus, p_h, L, K)
            if gaps is None:
                row.append(None)
                continue
            r = rung(gaps, marke)
            rule, g = r.rule, r.gap
            if r.rung == 4:   # keine Regel unter der Marke: die Zelle zeigt die kleinste Lücke aller Regeln
                g, rule = min((v, k) for k, v in gaps.items() if v is not None)
            row.append(dict(L=L, K=K, rung=r.rung, rule=rule, gap=g, gaps=gaps))
        cells.append(row)
    return dict(modus=modus, marke=marke, p_h=p_h, K=list(C.KARTE_K), L=list(ls), cells=cells)


def count_rungs(k: dict) -> dict:
    out = {1: 0, 2: 0, 3: 0, 4: 0}
    for row in k["cells"]:
        for c in row:
            if c is not None:
                out[c["rung"]] += 1
    return out


def count_cells(k: dict) -> int:
    return sum(c is not None for row in k["cells"] for c in row)


def threshold_k(p_h: int, L: int, marke: float):
    """Kleinstes K des Rasters, ab dem die Lücke von Base-Stock beim Rückstand die Marke erreicht (>=); None, wenn sie im Raster nie so groß wird."""
    for K in C.B_K:
        cell = backorder_cell(p_h, L, K)
        if cell is not None and cell["gap_base_stock_pct"] >= marke:
            return K
    return None


def gap_grows_with_k(p_h: int, L: int, tol: float = 1e-6) -> bool:
    """Wächst die Lücke von Base-Stock beim Rückstand mit K (Raster, ohne Rückgang größer als tol Punkte)?"""
    gaps = [backorder_cell(p_h, L, K)["gap_base_stock_pct"] for K in C.B_K]
    return all(b >= a - tol for a, b in zip(gaps, gaps[1:]))


def eoq_takt(K: float, h: float = C.H, mean: float = C.MEAN) -> float:
    """Takt der Losgrößenformel T = sqrt(2 K / (h mu)) in Perioden (Bezugsgröße: K gegen h mal Mittel, nicht gegen die Losgröße)."""
    return sqrt(2.0 * K / (h * mean))


def takt_band(marke: float, p_h: int = 9):
    """(kleinster, größter) EOQ-Takt über die Lieferzeiten 0 bis 5 bei der K-Schwelle der Marke, p/h gegeben."""
    ts = [eoq_takt(k) for k in (threshold_k(p_h, L, marke) for L in C.B_L) if k is not None]
    return (min(ts), max(ts)) if ts else (None, None)


def takt_band_all(marke: float):
    """(kleinster, größter) EOQ-Takt über alle 18 Reihen (p/h = 4, 9, 19; Lieferzeit 0 bis 5)."""
    ts = [eoq_takt(k) for p in C.B_PH for k in (threshold_k(p, L, marke) for L in C.B_L) if k is not None]
    return (min(ts), max(ts)) if ts else (None, None)


def threshold_range(marke: float):
    """(kleinste, größte) K-Schwelle über alle 18 Reihen und die Zahl der Reihen mit Schwelle."""
    ks = [k for p in C.B_PH for k in (threshold_k(p, L, marke) for L in C.B_L) if k is not None]
    return (min(ks), max(ks), len(ks)) if ks else (None, None, 0)


def lernen_cell(L: int, K: float):
    for c in load()["lernen"]["zellen"]:
        if c["L"] == L and abs(c["K"] - K) < 1e-9:
            return c
    return None


def uebernommen(stueck: int | None = None) -> list:
    es = load()["uebernommen"]
    return [e for e in es if stueck is None or e["stueck"] == stueck]
