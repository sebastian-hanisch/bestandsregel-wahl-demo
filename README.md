# Welche Bestandsregel bei welchem Zustand? Regimekarte – Streamlit-Demo

**[→ Demo live ausprobieren](https://sebastianhanisch-bestandsregel-wahl-demo.streamlit.app/)**

Siebtes Stück der Linie **Bestandspolitiken** in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“, der **Zusammenfluss** der Stücke 1 bis 6: `bestell-rueckwaerts-demo` (Rückwärtsrechnung, Base-Stock), `bestellschwelle-demo` (Fixkosten, (s,S)), `lieferzeit-position-demo` (Lieferzeit, Bestandsposition), `verderbliche-ware-demo` (Alter als Zustand), `lager-und-haendler-demo` (zwei Stufen in Reihe) und `dp-grenze-demo` (Rechengrenze, gelernte Politik). Stück 1 rechnet die exakte Rückwärtsrechnung, die Stücke 2 bis 6 haben je eine Schwäche einfacher Bestellregeln vermessen; diese Demo stellt alle Lücken auf **eine Skala** und beantwortet, **welche einfache Regel in welchem Fall reicht**. Ein Artikel, eine Entscheidung je Periode („wie viel bestellen“), Poisson-Nachfrage mit Mittel 3, h = 1, p = 9 je fehlendem Stück, Bestellkosten je Stück 0, Fixkosten K je Bestellung in Einheiten von h. Die Kante zu den Vorgängern ist ein `fix` mit eigener Rechnung: die Kreuzzellen (Fixkosten **und** Lieferzeit bei verlorener Nachfrage) stehen in keinem der Stücke 1 bis 6.

## Warum dieses Problem

Die Stücke 1 bis 6 liefern Einzelbefunde in verschiedenen Modellen und Rastern: „Base-Stock ist optimal“, „(s,S) bei Fixkosten“, „Capped Base-Stock bei verlorener Nachfrage“, „Echelon bei zwei Stufen“. Wer eine Regel wählen muss, braucht eine Antwort auf **eine** Frage: **Welche einfache Regel reicht in welchem Fall, und wie weit liegt sie vom Optimum?** Die Karte beantwortet sie mit einer Leiter: Stufe 1 Base-Stock (ein Parameter), Stufe 2 (s,S) oder Capped Base-Stock (zwei Parameter), Stufe 3 (s,S) mit Kappe (drei Parameter), Stufe 4 keine einfache Regel unter der **Marke** (voreingestellt 2 % der DP-Kosten; 1 und 5 % wählbar). Die neue Frage ist, was geschieht, wenn zwei Schwächen zugleich wirken: Bei verlorener Nachfrage **verlangen Fixkosten und Lieferzeit verschiedene Reparaturen** ((s,S) gegen die Fixkosten, Capped Base-Stock gegen die Lieferzeit), und die Reparaturen **addieren sich nur ungefähr**: In 7 von 29 Zellen liegt keine der beiden allein unter der Marke von 2 %, die Kombination (s,S) mit Kappe erreicht sie in 6 davon.

## Modell

**Rückstand:** Zustand ist die Bestandsposition (Bestand plus Bestelltes minus Rückstand), Bestellmenge höchstens 40, Position von −40 bis 60, Nachfrage bei 30 abgeschnitten, Lieferzeit 0 bis 5, p/h = 4, 9, 19, K = 0 bis 4 in Schritten von 0,05 und 5, 7,5, 10, 15, 20, 30 (3 · 6 · 87 = 1.566 Zellen). **Verlorene Nachfrage:** Zustand ist Bestand und Pipeline, Bestellmenge höchstens 12, Bestand höchstens 26, Nachfrage bei 14 abgeschnitten, Lieferzeit 1 bis 4, p/h = 9, K = 0, 0,5, 1, 1,5, 2, 3, 5, 10 (bei Lieferzeit 4 nur 0, 1, 2, 5, 10): 29 Zellen. **Lücke** = Kosten der Regel (exakt über die stationäre Verteilung bewertet, einschließlich Fixkosten) geteilt durch die Kosten der DP minus 1. Die Regeln: Base-Stock S, (s,S), Capped Base-Stock (Bestellmenge höchstens Kappe) und (s,S) mit Kappe; ihre Parameter sind ganzzahlige Suchergebnisse. Formeln im Expander „📐 Mathematische Formulierung“ der App.

## Methodik

- **Rückstand (`brg_backorder.py`):** relative Wertiteration auf der Bestandsposition. Die Kosten einer Bestellung fallen L + 1 Perioden später an (Rechenidentität im Modell, in `tests/test_oracle_backorder.py` gegen die Rechnung mit vollem Pipeline-Zustand geprüft). Beste Base-Stock-Niveaus durch vollständige Suche, (s,S) aus der DP-Politik.
- **Verlorene Nachfrage (`brg_lost.py`):** Tensor-DP über (Bestand, Pipeline) mit Fixkosten in der Wertiteration; ein dichtes Matrixprodukt je Bestellmenge statt einer dünnen Übergangsmatrix je Bestellmenge. Parameter der Regeln per Nachbarschaftssuche (±1 je Parameter) aus mehreren Startpunkten, exakt bewertet; Base-Stock vollständig über S.
- **Karte, Leiter, Baum (`brg_data.py`, `brg_ladder.py`, `brg_tree.py`):** Die Stufe einer Zelle ist die erste Stufe, deren beste Regel echt unter der Marke liegt. Der Baum liest die vorgerechnete Karte und die übernommenen Zahlen und rechnet nichts neu.
- **Handbeispiele (`brg_hand.py`):** alle Politiken der Mini-Instanzen in exakten Brüchen aufgezählt (720 und 81), Kosten je Politik als Gerade in K, Optimum als untere Hülle.
- **Simulationsprobe:** SplitMix64 (`brg_rng.py`), Inversion der Verteilungsfunktion, vier feste Zufalls-Seeds, Einschwingzeit.
- **Vorgerechnet** (`data/brg_karte.json`, 124 kB, erzeugt von `tools/build_karte.py`; Lernläufe in `data/rohdaten/`): das Rückstandsraster, die 29 Zellen der verlorenen Nachfrage mit Aufzählung zur Kontrolle, die Lernläufe, die Zelle Lieferzeit 4 / K = 5 und die übernommenen Zahlen. **Live:** jede Zelle des Rückstands (Knopf „Zelle live nachrechnen“), die verlorene Nachfrage bei Lieferzeit 1 und 2 (Spinner, Größenordnung Sekunden), die Handbeispiele, die Simulationsprobe, Leiter, Karte und Baum. Lieferzeit 3 und 4 mit Fixkosten brauchen je Zelle Größenordnung zehn Sekunden bis eine Minute (unter Last) und liegen vorgerechnet vor.

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen: Poisson-Nachfrage Mittel 3, h = 1, p/h = 9 (Rückstand zusätzlich 4 und 19), Lücke in Prozent der DP-Kosten, einschließlich Fixkosten; „Zellen“ sind die Zellen der oben genannten Raster. Die Spalte „Test“ nennt den Test in `tests/test_claims.py`, der genau diese Zählung prüft („Zahl → Test“).

| Befund | Test |
|---|---|
| **Raster:** Rückstand 1.566 Zellen (p/h = 4, 9, 19; Lieferzeit 0 bis 5; 87 Werte K), verlorene Nachfrage 29 Zellen | K01 |
| **Rückstand, Form:** Die DP-Politik hat auf den erreichten Positionen reine (s,S)-Form in 1.566 von 1.566 Zellen (Messbefund, kein Satz); (s,S) mit den Parametern der DP-Politik kostet dasselbe wie die DP. Zeitanteil an den Rändern und an der Bestellgrenze numerisch null: unten 0, oben höchstens 7,3e-17, an der Bestellgrenze höchstens 2,4e-16 (unter der Maschinengenauigkeit, Rechenrauschen des Lösers und keine Anteile; die Ziffern sind nicht plattformstabil) | K02 |
| **Rückstand, Fixkosten entscheiden:** Die Lücke von Base-Stock wächst mit K in 18 von 18 Reihen (p/h x Lieferzeit). Sie erreicht 2 % bei K = 0,75 bis 1,55 (1 %: 0,50 bis 1,15; 5 %: 1,35 bis 2,35; kleinstes K des Rasters, ab dem die Lücke die Marke erreicht) | K03 |
| **Takt:** Der Takt der Losgrößenformel √(2K/(h·μ)) liegt bei diesen 18 Schwellen (Marke 2 %) zwischen 0,71 und 1,02 Perioden. Bezugsgröße: K gegen h mal Mittel μ, nicht gegen eine Losgröße | K04 |
| **Lieferzeit verschiebt die Schwelle, ohne dass sie steigt oder fällt:** K bei 2 % für p/h = 9 und Lieferzeit 0 bis 5: 1,30 / 1,20 / 1,30 / 0,90 / 1,20 / 0,95 (p/h = 4: 0,75 bis 1,00; p/h = 19: 1,20 bis 1,55) | K05 |
| **Tabelle A (Rückstand, p/h = 9, Lücke von Base-Stock in %):** K = 1: 0,33 / 1,27 / 1,49 / 2,41 / 1,44 / 2,26 für Lieferzeit 0 bis 5; K = 5: 20,78 / 21,97 / 20,90 / 21,47 / 20,13 / 20,08; K = 10: 50,21 / 48,07 / 47,24 / 46,06 / 44,17 / 43,61 (alle Zeilen im Test). Für Lieferzeit 0 bis 3 stimmen die Zahlen mit `bestellschwelle-demo` überein (K = 1: 0,33 / 1,27 / 1,49 / 2,41 %) | K06, `test_verweise.py` |
| **(s,S) der DP bei K = 5** (p/h = 9, Lieferzeit 0 bis 5): (3,8) / (6,12) / (10,16) / (13,19) / (16,23) / (20,26) | K07 |
| **Prozent bei hohem K sind überwiegend ein Effekt der Bestellhäufigkeit:** Rückstand, Lieferzeit 1, K = 20: Base-Stock +93,96 % und bestellt in 95,0 % der Perioden (1 − e⁻³), die DP in 24 % | K08 |
| **Verlorene Nachfrage, die Reparaturen kehren sich um:** Bei K = 0 ist Capped besser als (s,S) in 4 von 4 Lieferzeiten; bei K ≥ 5 ist (s,S) besser als Capped in 8 von 8 Zellen. Capped liegt dort bei 18,55 bis 47,27 %, Base-Stock bei 19,66 bis 47,44 %; die DP bestellt in 29 bis 44 % der Perioden | K09 |
| **Zwei Schwächen zugleich:** In 7 von 29 Zellen liegt weder (s,S) noch Capped unter 2 % (Lieferzeit 3: K = 1,5 / 2 / 3 / 5; Lieferzeit 4: K = 2 / 5 / 10). (s,S) mit Kappe schließt davon 6 (+0,67 bis +1,92 %); Lieferzeit 4, K = 5 bleibt mit +3,63 % über der Marke. Die Zählung hängt an der Marke: mehrere Zellen liegen innerhalb 0,15 Punkte neben 2 %; bei Lieferzeit 4 sind die Werte von (s,S) mit Kappe das Ergebnis einer lokalen Suche, keine vollständige Aufzählung | K10 |
| **Stufen der 29 Zellen nach Marke** (Stufe 1 / 2 / 3 / 4): Marke 1 %: 0 / 11 / 9 / 9; Marke 2 %: 2 / 20 / 6 / 1; Marke 5 %: 14 / 15 / 0 / 0. Die Zählung gilt für dieses Raster und hängt an der Marke | K11 |
| **Karte des Rückstands** (8 Werte K x 6 Lieferzeiten = 48 Zellen, p/h = 9): Base-Stock reicht in 13 / 16 / 24 Zellen bei Marke 1 / 2 / 5 % (Zählung im Raster, kein Anteil der Welt) | K11b |
| **Lieferzeit 4, K = 5, Pipeline:** beste Aufzählung (s,S) (S ≤ 40) +3,76 % bei (15,20); Raster (s,S) mit Kappe (583 Auswertungen) +3,63 % bei (14,21, Kappe 8); beste gefundene Funktion der Bestandsposition nach einem Sweep des Koordinatenabstiegs (421 Auswertungen, nicht konvergiert) **+3,56 %**. Die Suche liefert eine obere Schranke; ob bei Fixkosten die Pipeline der Grund ist, ist **offen** (in Lieferzeit 3, K = 2 liegt die Projektion der DP-Politik auf die Bestandsposition nach einer unabhängigen Prüfrechnung bei +0,26 %) | K12 |
| **Gelernte Politik mit Fixkosten** (Politikgradient wie in `dp-grenze-demo`, fünf Zufalls-Seeds, 3.000 Updates, 7,7e7 Perioden je Lauf): Lieferzeit 3, K = 2: Endstände +1,19 / +1,54 / +0,85 / +0,58 / +1,14 %, Median +1,14 %, 5 von 5 unter 2 % und unter der besten Zweiparameterregel (+2,68 %), 1 von 5 unter (s,S) mit Kappe (+0,67 %). Lieferzeit 4, K = 5: +2,01 / +1,65 / +3,32 / +0,94 / +1,40 %, Median +1,65 %, 3 von 5 unter 2 %, 5 von 5 unter (s,S) mit Kappe (+3,63 %); ab Update 1.000 liegen 56 % der Messpunkte unter 2 % (bei Lieferzeit 3: 80 %; je Seed fünf zeitlich korrelierte Messpunkte). Der Endstand ist eine Momentaufnahme eines schwankenden Verlaufs: im Mittel der Messpunkte ab Update 1.500 liegt in Lieferzeit 4, K = 5 nur 1 von 5 Läufen unter 2 % (Zählung aus den Rohdaten, nicht in den Tests). Kein Lauf liegt unter dem Optimum (die Politik wird exakt bewertet, das folgt schon aus der Optimalität der DP) | K13 |
| **Handbeispiele in Brüchen:** A (Rückstand, Lieferzeit 0): Base-Stock g = 1 + ¾K, (s,S) = (0,2) g = 11/10 + 9K/20, Kreuzung bei K = 1/3 (darüber ist (0,2) die beste der 720 Politiken bis K = 58/9, danach wechselt das Optimum weiter), Lücke 2 % bei K = 122/291 ≈ 0,419, 5 % bei 62/111 ≈ 0,559, 25,0 % bei K = 2; 720 Politiken aufgezählt. B (verloren, Lieferzeit 1): Capped (Kappe 1, S = 3) ist bei K = 0 das Optimum (5/4), (s,S) = (1,3) bei K = 1 (169/87), Base-Stock 41/20 (+5,53 %), Capped (Kappe 1, S = 2) 36/17 (+9,01 %); 81 Politiken aufgezählt, die beste Politik wechselt bei K = 2/5, 38/55, 5, 58/9 | K14 |
| **Zustandszahlen** bei verlorener Nachfrage, Bestellgrenze 12, Bestand höchstens 26: 27 · 13^(L−1) = 27 / 351 / 4.563 / 59.319 / 771.147 (Lieferzeit 1 bis 5; die letzte nur gezählt, nicht gerechnet); Stück 6: 21 · 9^(L−1) mit 11.160.261 (L = 7) und 100.442.349 (L = 8, rund 0,8 GB je Wertetabelle; die App von Stück 6 rechnet L = 8 nicht, eine einmalige Messung außerhalb der App rechnete die DP dort in 522 s bei 5,95 GB Spitzenspeicher) | K15 |
| **Grenzen werden nicht erreicht:** Zeitanteil am Bestandsrand praktisch null (unter 1e-20 in den 29 Zellen; Reste der Iteration, keine gemessenen Anteile), die Bestellgrenze 12 wird nicht gewählt (Anteil 0), größte Bestellmenge der DP 11 (bei K = 10 liegt die Grenze nahe) | K16 |
| **Suche gegen Aufzählung:** In den 24 Zellen mit Lieferzeit 1 bis 3 geben die Aufzählung aller (s,S) und aller Capped-Paare dieselben Lücken wie die Suche (Unterschied unter 0,001 Punkte) | K17 |
| **Leseprobe:** verlorene Nachfrage, Lieferzeit 3, K = 2: Base-Stock +4,98 %, (s,S) +2,68 %, Capped +2,78 %, (s,S) mit Kappe +0,67 %; Marke 2 % gibt Stufe 3, Marke 3 % Stufe 2, Marke 5 % Stufe 1 | K18 |
| **Größe:** Repo unter 3 MB, Datendatei unter 300 kB | K19 |
| **Übereinstimmung mit den Vorgängern:** Die K-Zeilen ohne Fixkosten (verlorene Nachfrage, p/h = 9, Lieferzeit 1 bis 4, Bestellgrenze 12) liegen höchstens 0,02 Punkte neben der Tabelle in `lieferzeit-position-demo` (Bestellgrenze 8); die übernommenen Zahlen stehen wörtlich in den READMEs der Stücke | `test_verweise.py` |
| **Hilfetexte der Presets** nennen nur Zahlen aus diesen Zeilen und den übernommenen Aussagen; Text der Annahmen in README und App gleich | `test_presets.py`, `test_readme.py` |

**Lehre.** Die Aussage „die Position reicht fast“ aus dem Stück zur Lieferzeit (höchstens +0,67 % bei K = 0) ist mit Fixkosten nur in zwei Zellen geprüft: in Lieferzeit 4, K = 5 liegt die beste gefundene Funktion der Position bei +3,56 % (obere Schranke), in Lieferzeit 3, K = 2 die Projektion der DP-Politik auf die Position bei +0,26 % (unabhängige Prüfrechnung).

## Ehrliche Grenzen

- **Modell.** Ein Artikel, Poisson-Nachfrage mit Mittel 3, h = 1, p/h = 9 (beim Rückstand zusätzlich 4 und 19), Bestellkosten je Stück 0, Fixkosten K je Bestellung. Andere Mittel, andere Verteilungen und andere p/h bei Fixkosten und verlorener Nachfrage sind **nicht gemessen**; die Karte gilt nur für dieses Modell.
- **Gewählte Grenzen.** Rückstand: Bestellmenge höchstens 40, Bestandsposition von −40 bis 60, Nachfrage bei 30 abgeschnitten. Verlorene Nachfrage: Bestellmenge höchstens 12, Bestand höchstens 26, Nachfrage bei 14 abgeschnitten. Die Grenzen sind so gewählt, dass der Zeitanteil an den Rändern und an der Bestellgrenze unter 1e-4 bleibt (gemessene Werte im Test); die Stücke 3 und 6 rechnen ohne Fixkosten mit Bestellgrenze 8 und Bestand 20 bis 28, die Zeilen mit K = 0 stimmen bei Lieferzeit 1 bis 4 und p/h = 9 mit der Tabelle in Stück 3 auf höchstens 0,02 Punkte überein. **K = 20 und mehr ist bei verlorener Nachfrage nicht gerechnet.**
- **Die Parameter der Stufen 2 und 3 sind Suchergebnisse.** Ganzzahlig, per Nachbarschaftssuche aus mehreren Startpunkten gefunden und exakt bewertet; die Lücken sind also obere Schranken der Lücke der Regelfamilie, kein Beweis des Optimums der Familie. Die Aufzählung aller (s,S) und aller Capped-Paare ergibt in den 24 Zellen mit Lieferzeit 1 bis 3 dieselben Lücken wie die Suche (Unterschied unter 0,001 Punkte).
- **Die Stufe hängt an der Marke.** Zählungen („in x von y Zellen“) gelten für das gemessene Raster und die gewählte Marke, nicht für alle Fälle der Welt.
- **Prozent bei hohem K sind überwiegend ein Effekt der Bestellhäufigkeit.** Base-Stock bestellt beim Rückstand in 1 − e⁻³ = 95,0 % der Perioden, die DP bei Lieferzeit 1 und K = 20 in 24 %; in dieser Zelle sind die Mehrkosten für Fixkosten größer als der ganze Kostenunterschied (Lager- und Fehlmengenkosten liegen bei Base-Stock niedriger), für andere Zellen ist das nicht zerlegt. Die Zelle zeigt deshalb Bestellanteil und absolute Mehrkosten neben der Prozentzahl.
- **Rückstand mit der Bestandsposition als Zustand** ist eine Rechenidentität im Modell dieser Demo (Kosten einer Bestellung fallen L + 1 Perioden später an), gegen die Rechnung mit vollem Pipeline-Zustand in fünf Zellen geprüft. Dass die DP-Politik reine (s,S)-Form hat, ist ein Messbefund in diesem Raster, kein Satz; nach Feinberg (arXiv 1606.00957, Volltext gelesen, Abschnitte 1 und 4) ist (s,S) unter Voraussetzungen optimal (Rückstand, Lieferzeit null, konvexe Kosten, unbeschränkte Bestellmenge, unabhängige, identisch verteilte Nachfrage, je nach Kriterium weitere Bedingungen an den Horizont); Scarf (1960) ist nur über Feinberg bekannt.
- **Verlorene Nachfrage mit Fixkosten** kommt in den gelesenen Quellen nicht vor; die 29 Zellen sind eigene Messungen. Ob die Literatur Sätze zu (s,S) bei verlorener Nachfrage hat, ist nicht geprüft. Capped Base-Stock als Vergleichsregel stammt aus der Literatur zu verlorener Nachfrage (Xin, Operations Research 2021, nur Abstract gelesen; van Jaarsveld und Arts, arXiv 2101.07519, Volltext).
- **Die Pipeline-Frage ist offen.** In der Zelle Lieferzeit 4, K = 5 liegt die beste gefundene Funktion der Bestandsposition nach einem Sweep der lokalen Suche bei einer kleineren Lücke als (s,S) mit Kappe; die Suche ist abgebrochen und nicht konvergiert, der Wert ist eine obere Schranke. Ob das an der Zusammensetzung der Pipeline liegt, ist **offen**: in Lieferzeit 3, K = 2 liegt die Projektion der DP-Politik auf die Bestandsposition nach einer unabhängigen Prüfrechnung bei +0,26 %, besser als (s,S) mit Kappe. Die Aussage „die Position reicht fast“ aus Stück 3 (höchstens +0,67 % bei K = 0) ist mit Fixkosten nur in diesen zwei Zellen geprüft.
- **Gelernte Politiken:** ein Verfahren (Politikgradient wie in Stück 6), eine Einstellung, zwei Zellen, fünf Zufalls-Seeds je Zelle, nicht in dieser Demo wiederholbar (Messwerte liegen vor). Gezeigt werden Median und Spannweite der Endstände; die Endstände streuen mit dem Zufalls-Seed, eine Rangfolge der Verfahren folgt daraus nicht.
- **Übernommene Zahlen** (Reiter „Strukturen nebeneinander“) stammen aus den READMEs der Stücke 1 bis 6 und gelten im Modell des jeweiligen Stückes; `tests/test_verweise.py` vergleicht sie wörtlich mit den READMEs, solange die Schwester-Ordner vorhanden sind. Die README des Stückes 6 wurde beim Bau dieser Demo gelesen; ändert ein Stück seine Zahlen, schlägt der Test fehl.
- **Nicht gemessen:** Fixkosten bei verderblicher Ware und bei zwei Stufen; verlorene Nachfrage mit Fixkosten ab Lieferzeit 5; andere Mittel, Verteilungen, p/h bei Fixkosten; die Rechenzeit auf dem Server. Rechenzeiten in dieser Demo sind Größenordnungen unter Last.

## Verifikation

- **Einheiten von Hand** (`tests/test_units.py`): Lücke (5/2 gegen 2 = 25 %; 41/20 gegen 169/87 = 5,53 %), Geraden, Kreuzung 1/3, Schwellen 122/291 und 62/111, untere Hülle, Leiter (Leseprobe), beide Handbeispiele in Brüchen.
- **Orakel** (`tests/test_oracle_*.py`): Tensor-DP gegen einen dünn besetzten MDP mit Python-Schleifen (DP-Kosten und vier Regeln, Lieferzeit 1 bis 3, K = 0 und 3); Politik-Iteration nach Howard gegen die Wertiteration; Simulation der DP-Politik und einer (s,S)-Regel gegen die exakte Auswertung (vier Zufalls-Seeds, Band von vier Standardfehlern); Handbeispiel B (Wertiteration gegen die Aufzählung aller 81 Politiken); Aufzählung aller (s,S) und Capped-Paare gegen die Suche; Rückstand: Position-DP gegen volle Pipeline-DP (fünf Zellen), geschlossene Newsvendor-Formel mit scipy (Lieferzeit 0 bis 5), Aufzählung aller (s,S) gegen die DP, Bestellanteil 1 − e⁻³.
- **Daten** (`tests/test_data.py`): jede Zelle des Rasters einmal vorhanden; kleine Zellen gegen Neuberechnung (Rückstand: 7 Zellen und 40 zufällige; verlorene Nachfrage: Lieferzeit 1 mit K = 0, 2, 10); innere Beziehungen der großen Zellen.
- **Eigenschaften und Zweige** (`tests/test_properties.py`, `tests/test_branches.py`): Kosten wachsen mit K, Lücke von Base-Stock wächst mit K, größere Marke gibt keine größere Stufe, Stufe 4 nur, wenn alle Regeln über der Marke liegen, Skalierung (h, p, K) · 2 ändert die Lücken nicht, jede Variante weicht auf mindestens einer Zelle ab (Fixkosten, Kappe, Marke, Rückstand gegen verloren).
- **Verweise** (`tests/test_verweise.py`): jede übernommene Zahl wörtlich in der README des Stückes; überspringt sich ohne den Schwester-Ordner.
- **Verdikte, Baum, Randfälle:** `tests/test_verdicts.py`, `tests/test_tree.py`, `tests/test_edge_cases.py` (Marke 0, Lieferzeit 0 bei verlorener Nachfrage, Zellen ohne Messung, Grenzen inklusive).
- **Oberfläche:** AppTest jedes Presets, jedes Buttons, jedes Reglers an Minimum und Maximum, Permalink mit Einrasten, Live-Knöpfe, Reiter, Layout und Footer, Laufzeit-Importe. 231 Tests (`pytest --collect-only -q tests`).

## Dateistruktur

| Datei | Zweck |
|---|---|
| `.github/workflows/tests.yml` | CI: Push, Pull Request, wöchentlicher Canary |
| `.gitignore` | venv, Caches, Streamlit-Secrets |
| `.streamlit/config.toml` | Streamlit-Einstellungen (keine Nutzungsstatistik) |
| `app.py` | Streamlit-App: Karte, Ihre Zelle, Handbeispiele, Strukturen, Baum, Rechengrenze und Lernen, weiße Flecken |
| `brg_backorder.py` | Rückstand: Position-DP, Regeln, Zelle |
| `brg_constants.py` | Raster, Reglergrenzen, Farben, Presets |
| `brg_data.py` | Zugriff auf `data/brg_karte.json`, Karte, Schwellen, Takt |
| `brg_demand.py` | Poisson-Verteilung, abgeschnitten |
| `brg_evaluation.py` | Zellenansicht, Verdikte (reine Funktionen) |
| `brg_gap.py` | Lücke einer Regel gegen die DP |
| `brg_hand.py` | Handbeispiele in Brüchen, Aufzählung aller Politiken |
| `brg_ladder.py` | Die Leiter der Regeln, Stufe einer Zelle |
| `brg_layout.py` | Fester Kopf (Stylesheet) |
| `brg_lines.py` | Kosten als Gerade in K, Kreuzung, Schwelle, untere Hülle |
| `brg_lost.py` | Verlorene Nachfrage: Tensor-DP, Regeln, Suche, Simulation |
| `brg_presets.py` | Permalink (Begrenzen, Einrasten), Presets (Schnellstart in der Seitenleiste, aktives Preset hervorgehoben) |
| `brg_rng.py` | SplitMix64 für die Simulationsprobe |
| `brg_texts.py` | Texte der App (Einleitung, Annahmen, Handbeispiele, Formeln) |
| `brg_tree.py` | Entscheidungsbaum |
| `brg_visualization.py` | Plotly-Abbildungen (Achsen gesperrt) |
| `data/brg_karte.json` | vorgerechnete Karte (124 kB) |
| `data/rohdaten/` | Rohläufe der gelernten Politiken (zehn Dateien) |
| `tools/build_karte.py` | erzeugt `data/brg_karte.json` (Teile: Rückstand, verloren, Lernen, übernommen, Zelle Lieferzeit 4 / K = 5) |
| `tools/uebernommen.py` | die aus den Stücken 1 bis 6 übernommenen Zahlen mit Quelle und wörtlichen Textstücken |
| `requirements-dev.txt` | Laufzeit plus pytest und scipy (nur Orakel) |
| `requirements.txt` | Laufzeit-Bibliotheken (ungepinnt) |
| `tests/` | Einheiten, Orakel, Daten, Claims, Verweise, Zweige, Eigenschaften, Verdikte, Baum, Randfälle, Presets, Layout, AppTest, Footer, README, Laufzeit-Importe |

## Bewusst nicht umgesetzt

- **Kein freier Regler ohne gemessene Zelle.** Fixkosten, Lieferzeit und p/h sind Auswahlregler über gemessene Werte; eine Zelle ohne Messung zeigt den Grund statt einer Zahl.
- **Keine Fixkosten bei verderblicher Ware und zwei Stufen, keine Lieferzeit 5 mit Fixkosten bei verlorener Nachfrage, kein K = 20 bei verlorener Nachfrage:** nicht gerechnet (siehe „Weiße Flecken“ in der App).
- **Keine Wiederholung der Lernläufe in der App:** ein Lauf dauerte in den vorliegenden Läufen 167 bis 706 Sekunden (wechselnde Last, Größenordnung Minuten); die Läufe liegen als Messwerte vor.
- **Keine Simulationsprobe beim Rückstand:** die Rückstandsregeln werden exakt bewertet; die Simulation prüft die verlorene Nachfrage, deren Zustand die Pipeline enthält. Der Zufalls-Seed ist daher kein Regler; die Probe nutzt die Zufalls-Seeds 1 bis 4.
- **Kein Servicegrad, keine Schätzung der Nachfrage:** siehe `forecast-inventory-demo`.

## Lokal ausführen

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

pip install -r requirements.txt
streamlit run app.py
```

Die Karte neu erzeugen (der Teil `verloren` braucht Größenordnung zehn Minuten, `OMP_NUM_THREADS=1` setzen): `python tools/build_karte.py --teil verloren`.

## Tests ausführen

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Gebaut mit Streamlit, Plotly und NumPy.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zur Reihe: [Bestandspolitiken: von Base-Stock bis Regelwahl](https://sebastianhanisch.net/konzepte-bestandspolitiken.html).
