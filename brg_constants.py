"""Konstanten: Modell, Raster der Messung, Regler-Grenzen, Farben, Presets.

Modell überall: ein Artikel, Poisson-Nachfrage mit Mittel 3, Lagerkosten h = 1 je Stück und Periode, Strafkosten p = (p/h) * h je fehlendem Stück,
Bestellkosten je Stück 0, Fixkosten K je Bestellung (in Einheiten von h)."""

MEAN, H = 3.0, 1.0

# ---- Rückstand: Bestandsposition als Zustand (Rechnung wie im Stück zur Bestellschwelle)
B_PH = (4, 9, 19)
B_L = (0, 1, 2, 3, 4, 5)
B_K_FINE = tuple(round(0.05 * i, 2) for i in range(0, 81))     # 0 bis 4 in Schritten von 0,05
B_K_COARSE = (5.0, 7.5, 10.0, 15.0, 20.0, 30.0)
B_K = B_K_FINE + B_K_COARSE                                  # 87 Werte
B_Q, B_ZMIN, B_YMAX, B_DMAX = 40, -40, 60, 30                # Bestellgrenze, Position -40 bis 60, Nachfrage bei 30 abgeschnitten
B_S_RANGE = (B_ZMIN // 2, B_YMAX - 5)                        # Suchbereich des Base-Stock-Niveaus: -20 bis 54

# ---- verlorene Nachfrage: Bestand und Pipeline als Zustand (Tensor-DP)
V_PH = 9
V_L = (1, 2, 3, 4)
V_K = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0)
V_Q, V_XM, V_DMAX = 12, 26, 14                               # Bestellgrenze 12, Bestandsgrenze 26, Nachfrage bei 14 abgeschnitten
V_SMAX = 40                                                  # Suchbereich der Niveaus
V_MEASURED = {1: V_K, 2: V_K, 3: V_K, 4: (0.0, 1.0, 2.0, 5.0, 10.0)}   # gemessene Zellen (Lieferzeit 4: nur diese fünf K)

# ---- Karte und Regler
KARTE_K = (0.0, 0.5, 1.0, 1.5, 2.0, 3.0, 5.0, 10.0)           # Zeilen der Karte; alle liegen im Raster B_K und V_K
MARKEN = (1, 2, 5)                                           # Marke in Prozent der DP-Kosten
DEFAULT_MARKE = 2
MODUS_BACKORDER, MODUS_LOST = "Rückstand", "Verlorene Nachfrage"
MODI = (MODUS_BACKORDER, MODUS_LOST)
STRUKTUREN = ("Eine Stufe (Stücke 1 bis 3)", "Verderbliche Ware (Stück 4)", "Zwei Stufen (Stück 5)", "Jenseits der DP (Stück 6)")
HAND_K = (0.0, 0.25, 0.5, 1.0, 2.0, 4.0, 6.0)                # K der Handbeispiele (Regler)

# ---- Farben (Stufen 1 bis 4)
RUNG_COLORS = {1: "#2F6B65", 2: "#3b6ea5", 3: "#b8741a", 4: "#b03a37"}   # weiße Beschriftung bleibt lesbar
COLOR_LINE = "#4c78a8"
COLOR_MUTED = "rgba(150,150,150,0.55)"

# ---- Presets
DEFAULT_PRESET = "Nur Fixkosten (Rückstand, Lieferzeit 3, K = 3)"
PRESETS = {
    "Handbeispiel A (Rückstand, K)": {"modus": MODUS_BACKORDER, "L": 0, "K": 2.0, "ph": 9, "marke": 2, "K_hand": 2.0, "struktur": STRUKTUREN[0]},
    "Handbeispiel B (verloren, K)": {"modus": MODUS_LOST, "L": 1, "K": 1.0, "ph": 9, "marke": 2, "K_hand": 1.0, "struktur": STRUKTUREN[0]},
    DEFAULT_PRESET: {"modus": MODUS_BACKORDER, "L": 3, "K": 3.0, "ph": 9, "marke": 2, "K_hand": 1.0, "struktur": STRUKTUREN[0]},
    "Nur Lieferzeit (verloren, K = 0, Lieferzeit 3)": {"modus": MODUS_LOST, "L": 3, "K": 0.0, "ph": 9, "marke": 2, "K_hand": 1.0, "struktur": STRUKTUREN[0]},
    "Beides zugleich (verloren, Lieferzeit 3, K = 2)": {"modus": MODUS_LOST, "L": 3, "K": 2.0, "ph": 9, "marke": 2, "K_hand": 1.0, "struktur": STRUKTUREN[0]},
    "Keine einfache Regel (verloren, Lieferzeit 4, K = 5)": {"modus": MODUS_LOST, "L": 4, "K": 5.0, "ph": 9, "marke": 2, "K_hand": 1.0, "struktur": STRUKTUREN[0]},
    "Zwei Stufen: Lager sieht nichts": {"modus": MODUS_BACKORDER, "L": 1, "K": 0.0, "ph": 9, "marke": 2, "K_hand": 1.0, "struktur": STRUKTUREN[2]},
    "Verderblich: LIFO": {"modus": MODUS_BACKORDER, "L": 0, "K": 0.0, "ph": 9, "marke": 2, "K_hand": 1.0, "struktur": STRUKTUREN[1]},
    "Jenseits der DP (Stück 6, Lieferzeit 7 und 8)": {"modus": MODUS_LOST, "L": 4, "K": 0.0, "ph": 9, "marke": 2, "K_hand": 1.0, "struktur": STRUKTUREN[3]},
}
PRESET_HELP = {
    "Handbeispiel A (Rückstand, K)": "Das Handbeispiel A (Rückstand, Lieferzeit 0, Nachfrage 0 / 1 / 2, p/h = 4) liegt im Reiter „Handbeispiele“; hier mit K = 2 (Base-Stock 25 % über der besten Regel). Die Karte zeigt dazu die Zelle Rückstand, Lieferzeit 0, K = 2 im Modell mit Mittel 3.",
    "Handbeispiel B (verloren, K)": "Das Handbeispiel B (verlorene Nachfrage, Lieferzeit 1) liegt im Reiter „Handbeispiele“; hier mit K = 1. Die Karte zeigt dazu die Zelle verlorene Nachfrage, Lieferzeit 1, K = 1.",
    DEFAULT_PRESET: "Rückstand, nur Fixkosten wirken: ab K = 0,9 liegt Base-Stock bei Lieferzeit 3 bei oder über der Marke 2 %; die (s,S)-Regel hat die Form der DP-Politik.",
    "Nur Lieferzeit (verloren, K = 0, Lieferzeit 3)": "Verlorene Nachfrage ohne Fixkosten: Base-Stock liegt bei Lieferzeit 3 über 2 %, Capped Base-Stock (Bestellmenge begrenzt) darunter.",
    "Beides zugleich (verloren, Lieferzeit 3, K = 2)": "Fixkosten und Lieferzeit bei verlorener Nachfrage zugleich: weder (s,S) noch Capped liegt unter 2 %; erst (s,S) mit Kappe erreicht die Marke.",
    "Keine einfache Regel (verloren, Lieferzeit 4, K = 5)": "Die einzige gemessene Zelle, in der auch (s,S) mit Kappe über 2 % bleibt: Stufe 4.",
    "Zwei Stufen: Lager sieht nichts": "Springt zu Stück 5 (zwei Stufen in Reihe): Eine lokale Regel, bei der das Lager nur seinen eigenen Bestand sieht (Sicht A), liegt in 48 Zellen +3,73 bis +20,94 % über der DP, also in allen über 2 %.",
    "Verderblich: LIFO": "Springt zu Stück 4 (verderbliche Ware): Mit LIFO-Ausgabe und Lieferzeit 0 liegt Base-Stock auf dem Gesamtbestand bei Verderbkosten w = 3 bis 30 zwischen +0,05 und +26,69 % über der DP.",
    "Jenseits der DP (Stück 6, Lieferzeit 7 und 8)": "Springt zu Stück 6: Wo die exakte DP nicht gerechnet wird, misst man gegen die beste Regel, nicht gegen das Optimum. Die Einstellungen setzen Lieferzeit 4, K = 0; Lieferzeit 7 und 8 liegen nur als Zahlen aus Stück 6 vor.",
}
