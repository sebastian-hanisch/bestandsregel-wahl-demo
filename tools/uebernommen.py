"""Zahlen, die die Karte aus den Schwester-Demos der Linie übernimmt (nicht neu gerechnet), mit Quelle.

Jeder Eintrag nennt die Aussage, wie die App sie zeigt, und `phrases`: Textstücke, die **wörtlich** in der README des Stückes stehen müssen
(tests/test_verweise.py). Ändert ein Stück seine Zahlen, schlägt dieser Test fehl und die Karte veraltet nicht unbemerkt. Solange die README eines Stückes
noch Gerüst-Platzhalter enthält, überspringt sich der Test für dieses Stück; der Eintrag steht dann mit `stand = "Abschrift"`
(beim Bau dieser Demo war die README von Stück 6 noch nicht fertig; sie wurde danach gelesen).
`modell` nennt die Voraussetzungen im Modell des jeweiligen Stückes."""

GITHUB = "https://github.com/sebastian-hanisch/"

ENTRIES = [
    dict(id="s1_base_stock", stueck=1, repo="bestell-rueckwaerts-demo", struktur="Eine Stufe", regime="Rückstand, K = 0",
         aussage="Base-Stock ist die DP-Politik, das Niveau S ist das Quantil der Nachfrage über L + 1 Perioden: in 80 von 80 Zellen.",
         modell="Lieferzeit 0 bis 3, p/h = 1, 2, 4, 9, 19, Mittel 2 bis 5, Poisson-Nachfrage",
         phrases=["80 von 80 Zellen", "Lieferzeit 0 bis 3, p/h = 1, 2, 4, 9, 19, Mittel 2 bis 5"], stand="README gelesen"),
    dict(id="s2_ss_form", stueck=2, repo="bestellschwelle-demo", struktur="Eine Stufe", regime="Rückstand, K > 0",
         aussage="Die DP-Politik hat auf den erreichten Positionen die reine (s,S)-Form: in 1.464 von 1.464 Zellen (Messbefund, kein Satz).",
         modell="Lieferzeit 0 bis 3, p/h = 1, 2, 4, 9, 19, 39, K = 0 bis 30 in Schritten von 0,5, Mittel 3",
         phrases=["1.464 von 1.464", "Lieferzeit 0 bis 3, p/h = 1, 2, 4, 9, 19, 39, K = 0 bis 30 in Schritten von 0,5"], stand="README gelesen"),
    dict(id="s2_gap_k1_k2", stueck=2, repo="bestellschwelle-demo", struktur="Eine Stufe", regime="Rückstand, K > 0",
         aussage="Lücke von Base-Stock (p/h = 9, Lieferzeit 0 / 1 / 2 / 3): bei K = 1 0,33 / 1,27 / 1,49 / 2,41 %, bei K = 2 5,87 / 5,67 / 5,59 / 6,15 %.",
         modell="p/h = 9, Mittel 3, Bestellgrenze 40",
         phrases=["K = 1: 0,33 / 1,27 / 1,49 / 2,41 %", "K = 2: 5,87 / 5,67 / 5,59 / 6,15 %"], stand="README gelesen"),
    dict(id="s3_backorder", stueck=3, repo="lieferzeit-position-demo", struktur="Eine Stufe", regime="Rückstand, K = 0",
         aussage="Base-Stock ist die DP-Politik in 24 von 24 Zellen (Lieferzeit 0 bis 5, vier Werte von p).",
         modell="Rückstand, K = 0, Mittel 3, h = 1, p = 4, 9, 19, 39",
         phrases=["24 von 24 Zellen (L = 0 bis 5, vier Werte von p)"], stand="README gelesen"),
    dict(id="s3_lost_k0", stueck=3, repo="lieferzeit-position-demo", struktur="Eine Stufe", regime="Verlorene Nachfrage, K = 0",
         aussage="In 20 Zellen (Lieferzeit 1 bis 5, p = 4, 9, 19, 39): Base-Stock +0,42 bis +11,14 %, Capped Base-Stock +0,06 bis +2,35 %, beste gefundene Funktion der Position +0,00 bis +0,67 % über der DP.",
         modell="verlorene Nachfrage, K = 0, Mittel 3, h = 1, Bestellgrenze 8, Bestand höchstens 26 (Lieferzeit 5: 28)",
         phrases=["+0,42 bis +11,14 %", "+0,06 bis +2,35 %", "+0,00 bis +0,67 %", "p = 4, 9, 19 oder 39"], stand="README gelesen"),
    dict(id="s4_fifo_l0", stueck=4, repo="verderbliche-ware-demo", struktur="Verderbliche Ware", regime="Lieferzeit 0, FIFO-Ausgabe",
         aussage="Der beste Base-Stock auf dem Gesamtbestand ist in 26 von 30 Zellen exakt; die vier Ausnahmen liegen bei +0,36 bis +1,36 %.",
         modell="feste Haltbarkeit 2 bis 7, Verderbkosten w = 0, 1, 3, 10, 30, p = 9, verlorene Nachfrage, Bestandsgrenze 12",
         phrases=["26 von 30", "Haltbarkeit 2 mit w = 0 (+1,25 %), w = 10 (+0,36 %), w = 30 (+1,36 %) und Haltbarkeit 3 mit w = 30 (+1,01 %)"], stand="README gelesen"),
    dict(id="s4_lifo_l0", stueck=4, repo="verderbliche-ware-demo", struktur="Verderbliche Ware", regime="Lieferzeit 0, LIFO-Ausgabe",
         aussage="Base-Stock auf dem Gesamtbestand liegt bei w = 3 bis 30 zwischen +0,05 und +26,69 % über der DP (18 Zellen).",
         modell="wie oben, nur Zellen mit Verderbkosten w >= 3",
         phrases=["+0,05 bis +26,69 %", "über die 18 Zellen mit w ≥ 3"], stand="README gelesen"),
    dict(id="s4_fifo_l1", stueck=4, repo="verderbliche-ware-demo", struktur="Verderbliche Ware", regime="Lieferzeit 1, FIFO-Ausgabe",
         aussage="Die Lücke von Base-Stock liegt bei +1,36 bis +9,18 % in 25 Zellen, nie exakt; überwiegend der Effekt der Lieferzeit bei verlorener Nachfrage, nicht des Alters.",
         modell="wie oben, Lieferzeit 1",
         phrases=["Lieferzeit 1, FIFO: Base-Stock-Lücke +1,36 bis +9,18 % in 25 Zellen"], stand="README gelesen"),
    dict(id="s4_lifo_l1", stueck=4, repo="verderbliche-ware-demo", struktur="Verderbliche Ware", regime="Lieferzeit 1, LIFO-Ausgabe",
         aussage="Die Lücke von Base-Stock reicht bis +57,98 % (Haltbarkeit 2, w = 0; die einzige Zelle, in der Base-Stock an die Bestandsgrenze stößt, das Ergebnis ist mit Grenze 16 und 20 identisch).",
         modell="wie oben, Lieferzeit 1",
         phrases=["Lieferzeit 1, LIFO: Lücke bis +57,98 %"], stand="README gelesen"),
    dict(id="s5_echelon", stueck=5, repo="lager-und-haendler-demo", struktur="Zwei Stufen in Reihe", regime="Rückstand beim Händler, K = 0",
         aussage="Die Echelon-Politik (Base-Stock je Stufe auf dem Echelon-Bestand) hat dieselben Kosten wie die gemeinsame DP in 48 von 48 Zellen.",
         modell="Poisson-Mittel 3, Bestellgrenze 13 je Stufe, Lieferzeiten 1/1 bis 2/2, Lagerkosten h_w = 0,2 bis 0,8, p = 4, 9, 19",
         phrases=["In **48 von 48** Zellen sind die Kosten der Echelon-Politik"], stand="README gelesen"),
    dict(id="s5_lokal", stueck=5, repo="lager-und-haendler-demo", struktur="Zwei Stufen in Reihe", regime="Rückstand beim Händler, K = 0",
         aussage="Lokale Regel mit eigenem Niveau je Stufe, Lücke über der DP in 48 Zellen: Sicht A (das Lager sieht nur seinen Bestand) +3,73 bis +20,94 %, Sicht B +0,79 bis +11,27 %, Sicht C 0,00 %.",
         modell="wie oben; die Sicht benennt, was das Lager vom Händler sieht",
         phrases=["Sicht A +3,73 bis +20,94 %, Sicht B +0,79 bis +11,27 %, Sicht C 0,00 % in 48 von 48"], stand="README gelesen"),
    dict(id="s6_capped", stueck=6, repo="dp-grenze-demo", struktur="Jenseits der DP", regime="Verlorene Nachfrage, K = 0",
         aussage="Capped Base-Stock liegt bei Lieferzeit 1 bis 7 (p/h = 9) +0,10 / +0,69 / +1,63 / +0,82 / +0,36 / +0,37 / +0,39 % über der DP (Lieferzeit 7 per Simulation, Standardfehler rund 0,1 %; auf einem unabhängigen Strom mit 40.000 Ketten +0,62 %, Messung des Prüfers).",
         modell="verlorene Nachfrage, K = 0, Mittel 3, h = 1, p = 9, Bestellgrenze 8, Bestand höchstens 20",
         phrases=["Capped Base-Stock +0,10 / +0,69 / +1,63 / +0,82 / +0,36 / +0,37 / +0,39 %", "(L = 7: Simulation auf Strom 777, Standardfehler rund 0,1 %; auf einem unabhängigen Strom mit 40.000 Ketten +0,62 % und +10,18 %"], stand="README gelesen"),
    dict(id="s6_lernen", stueck=6, repo="dp-grenze-demo", struktur="Jenseits der DP", regime="Verlorene Nachfrage, K = 0",
         aussage="Gelernte Politik (Politikgradient), Lieferzeit 2 bis 6: Endstand im Median +0,53 / +0,67 / +1,00 / +0,77 / +0,62 % über der DP; 39 von 40 Läufen unter 2 %.",
         modell="wie oben, 10 Zufalls-Seeds bei Lieferzeit 2 bis 4, 5 bei Lieferzeit 5 und 6",
         phrases=["Median der Endstände +0,53 / +0,67 / +1,00 / +0,77 / +0,62", "39 von 40 Läufen (L = 2 bis 6) unter 2 %"], stand="README gelesen"),
    dict(id="s6_grenze", stueck=6, repo="dp-grenze-demo", struktur="Jenseits der DP", regime="Verlorene Nachfrage, K = 0",
         aussage="Zustandszahl 21 · 9^(L − 1): Lieferzeit 7 hat 11.160.261 Zustände (DP in rund einer Minute, Größenordnung), Lieferzeit 8 hat 100.442.349 Zustände (rund 0,8 GB je Wertetabelle). Die App von Stück 6 rechnet Lieferzeit 8 nicht; eine einmalige Messung außerhalb der App rechnete die DP dort in 522 s bei 5,95 GB Spitzenspeicher: möglich, aber aufwendig.",
         modell="Bestellgrenze 8, Bestand höchstens 20, K = 0",
         phrases=["11.160.261 Zustände) in rund einer Minute", "100.442.349 Zustände, rund 0,8 GB je Wertetabelle", "rechnete die DP dort in 522 s bei 5,95 GB Spitzenspeicher: möglich, aber aufwendig"], stand="README gelesen"),
]

RECHENGRENZE = dict(
    stueck6=dict(
        formel="21 · 9^(L − 1)", modell="Bestellgrenze 8, Bestand höchstens 20, K = 0", zustaende={"7": 11160261, "8": 100442349},
        tabelle_gb_L8=0.8, stand="Nach der README von Stück 6: Lieferzeit 7 in rund einer Minute (Größenordnung); bei Lieferzeit 8 rechnet die App von Stück 6 die DP nicht, eine einmalige Messung außerhalb der App rechnete sie in 522 s bei 5,95 GB Spitzenspeicher (möglich, aber aufwendig)",
        quelle="dp-grenze-demo, README"),
    diese_demo=dict(formel="27 · 13^(L − 1)", modell="Bestellgrenze 12, Bestand höchstens 26", zustaende={"1": 27, "2": 351, "3": 4563, "4": 59319, "5": 771147}),
)
