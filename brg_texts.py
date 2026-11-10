"""Texte der App, die auch in der README stehen (ein Test vergleicht die Annahmen-Fassung). Zahlen in diesen Texten prüft tests/test_claims.py."""

INTRO_MARKDOWN = """
Siebtes Stück der Reihe **Bestandspolitiken**, der Zusammenfluss der Stücke 1 bis 6. Stück 1 rechnet die exakte Rückwärtsrechnung, die Stücke 2 bis 6 haben je eine Schwäche einfacher Bestellregeln vermessen (Fixkosten, Lieferzeit, Verderb, zwei Stufen, Rechengrenze). Hier stehen alle Lücken auf **einer Skala**: Kosten der Regel geteilt durch die Kosten der exakten Rückwärtsrechnung (dynamische Programmierung, **DP**) minus 1, einschließlich Fixkosten.
Die **Kernfrage: Welche einfache Regel reicht in welchem Fall, und wie weit liegt sie vom Optimum?** Die Regeln bilden eine **Leiter** (Base-Stock, dann (s,S) oder Capped Base-Stock, dann (s,S) mit Kappe, danach nur noch DP oder gelernte Politik); eine Zelle bekommt die kleinste Stufe, deren Regel unter einer einstellbaren **Marke** liegt, voreingestellt 2 %.
Neu gegenüber den Einzelstücken: Was geschieht, wenn **zwei Schwächen zugleich** wirken, nämlich Fixkosten und Lieferzeit bei verlorener Nachfrage.

Alle Zahlen gelten für einen Artikel mit Poisson-Nachfrage (Mittel 3), Lagerkosten h = 1, p = 9 je fehlendem Stück (beim Rückstand zusätzlich p = 4 und 19), Bestellkosten je Stück 0 und Fixkosten K je Bestellung in Einheiten von h. Weiter unten: **Handbeispiele**, **Strukturen nebeneinander**, **Entscheidungsbaum**, **Rechengrenze und Lernen**, **weiße Flecken**, der Expander **⚠️ Annahmen, Grenzen und bekannte Probleme** und **📐 Mathematische Formulierung**.
"""

HOW_MARKDOWN = """
1. **Eine Zelle** ist eine Kombination aus der Art der Fehlmengen (**Rückstand**: Nicht Geliefertes wird nachgeliefert; **verlorene Nachfrage**: Es verfällt), der Lieferzeit L (Perioden zwischen Bestellung und Verfügbarkeit) und den Fixkosten K je Bestellung. Für jede gemessene Zelle liegen die Kosten der DP und die Kosten von vier Regeln vor.
2. **Die Lücke einer Regel** ist ihr Kostenüberschuss in Prozent der DP-Kosten, einschließlich Fixkosten. Die Regeln werden exakt bewertet (stationäre Verteilung der Bestandskette), nicht simuliert.
3. **Die Leiter.** Stufe 1: *Base-Stock* (bestelle bis zum Niveau S; ein Parameter). Stufe 2: *(s,S)* (bestelle bis S, sobald die Bestandsposition höchstens s ist) oder *Capped Base-Stock* (Base-Stock mit Obergrenze für die Bestellmenge), die bessere von beiden (zwei Parameter). Stufe 3: *(s,S) mit Kappe* (drei Parameter). Stufe 4: keine einfache Regel unter der Marke; dann bleibt die exakte DP, solange sie rechenbar ist, sonst bleibt nur eine gelernte Politik; in den zwei hier gemessenen Zellen erreichte sie im Median +1,14 bzw. +1,65 %. Die **Bestandsposition** ist Bestand plus Bestelltes minus Rückstand.
4. **Die Stufe einer Zelle** ist die erste Stufe, deren beste Regel **echt unter der Marke** liegt. Dieselbe Zelle hat bei anderer Marke eine andere Stufe; eine Zählung ohne Marke sagt nichts.
5. **Bezug.** Die Lücke gilt gegen die DP. Wo die DP nicht gerechnet wird, misst man gegen die beste Regel; das unterschätzt die Lücke zum Optimum um etwa deren eigene Lücke (Faktoren, nicht Punkte; Reiter „Rechengrenze und Lernen“).
"""

ASSUMPTIONS_MARKDOWN = """
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
"""

HAND_INTRO = """
Zwei Mini-Instanzen, in denen sich **alle Politiken aufzählen** lassen (exakte Brüche): Nachfrage 0 / 1 / 2 mit den Wahrscheinlichkeiten ¼, ½, ¼, h = 1, p = 4, Bestellkosten je Stück 0, Fixkosten K je Bestellung.
Die Kosten einer festen Politik sind eine **Gerade in K**: $g(K) = c_0 + c_1 K$, mit $c_0$ den Kosten je Periode ohne Fixkosten und $c_1$ dem Anteil der Perioden mit Bestellung. Das Optimum je K ist die **untere Hülle** aller Geraden.
"""

HAND_A = """
**Beispiel A: Rückstand, Lieferzeit 0.** Zustand ist die Bestandsposition z von −3 bis 2, die Aktion das Niveau y ≥ z nach der Bestellung (höchstens 2); Aufzählung aller 720 Politiken.
Base-Stock S = 2 bestellt, sobald die Nachfrage der Vorperiode größer als 0 war (Wahrscheinlichkeit ¾); die Regel (s,S) = (0,2) bestellt nur bei Position höchstens 0 (Anteil 9/20 der Perioden).
"""

HAND_B = """
**Beispiel B: verlorene Nachfrage, Lieferzeit 1.** Die Bestellung kommt nach der Nachfrage der Periode an, die Bestandsposition ist also der Bestand (0 bis 3, was darüber liegt, verfällt); Bestellmenge 0 bis 2; Aufzählung aller 81 Politiken.
Capped Base-Stock (Kappe 1, S = 3) ist bei K = 0 das Optimum; bei K = 1 gewinnt (s,S) = (1,3). Die Karte der Mini-Instanz kehrt sich also um: Fixkosten kehren die Reihenfolge von Capped und (s,S) um.
"""

LEITER_CAPTION = ("Farbe = Stufe der Leiter (kleinste Stufe, deren beste Regel unter der Marke liegt), Zahl = Lücke dieser Regel in Prozent der DP-Kosten "
                  "(„0“: gleich der DP); grau: nicht gemessen. Schwarz umrandet: Ihre Zelle.")

BAUM_INTRO = ("Sechs Fragen führen zu einem Blatt mit Regel, Zahl und Quelle. Die Antworten zu Stufen, Verderb, Fehlmengen, Lieferzeit, K und Marke kommen aus der Seitenleiste; "
              "der Baum rechnet nichts neu, er liest die vorgerechnete Karte und die übernommenen Zahlen.")

MATH_MARKDOWN = [
    r"**Lücke.** Für eine Regel mit mittleren Kosten $g_{\text{Regel}}$ je Periode (stationärer Betrieb, einschließlich Fixkosten) und die DP mit $g_{\text{DP}}$:",
    r"$$\text{Lücke} = 100\,\Bigl(\frac{g_{\text{Regel}}}{g_{\text{DP}}} - 1\Bigr)\ \%$$",
    r"**Kosten als Gerade in K.** Eine feste Politik bestellt in einem Anteil $c_1$ der Perioden; ihre Kosten sind linear in den Fixkosten $K$, $c_0$ sind die Kosten ohne Fixkosten:",
    r"$$g(K) = c_0 + c_1 K$$",
    r"**Kreuzung zweier Regeln.** Zwei Geraden $a$ und $b$ sind gleich bei",
    r"$$K^{\ast} = \frac{c_0^{b} - c_0^{a}}{c_1^{a} - c_1^{b}}$$",
    r"**Schwelle für eine Marke von $m\ \%$.** Regel $a$ liegt $m\ \%$ über Regel $b$ bei",
    r"$$K_m = \frac{(1 + m/100)\,c_0^{b} - c_0^{a}}{c_1^{a} - (1 + m/100)\,c_1^{b}}$$",
    r"**Takt der Losgrößenformel** (Bezugsgröße: Fixkosten $K$ gegen Lagerkosten $h$ mal Mittel $\mu$ der Nachfrage je Periode, keine Losgröße):",
    r"$$T = \sqrt{\frac{2K}{h\,\mu}}$$",
    r"**Rückstand mit der Position als Zustand.** Mit $D_{L+1}$ der Nachfrage über $L + 1$ Perioden und dem Niveau $y$ nach der Bestellung gilt für die Kosten der Bestellung, die erst $L + 1$ Perioden später anfallen:",
    r"$$G(y) = \mathbb{E}\bigl[h\,(y - D_{L+1})^{+} + p\,(D_{L+1} - y)^{+}\bigr]$$",
    r"**Verlorene Nachfrage, Zustand und Übergang.** Bestand $x$, Pipeline $(p_1, \dots, p_{L-1})$, Bestellung $a$ und Nachfrage $d$ geben den neuen Bestand",
    r"$$x' = \min\bigl((x - d)^{+} + p_1,\ \bar{x}\bigr)$$",
    r"und die Pipeline rückt auf: $(p_2, \dots, p_{L-1}, a)$. Die Periodenkosten sind",
    r"$$c(x, a) = h\,(x - d)^{+} + p\,(d - x)^{+} + K\,\mathbf{1}[a > 0]$$",
]
