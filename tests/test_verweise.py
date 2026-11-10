"""Verweis-Test: jede aus den Stücken 1 bis 6 übernommene Zahl steht wörtlich in der README des Stückes (data/brg_karte.json, tools/uebernommen.py).

Ohne diesen Test würde die Karte unbemerkt veralten, wenn ein Stück seine Zahlen ändert. Der Test überspringt sich, wenn der Schwester-Ordner fehlt (Repo allein ausgecheckt)
und für ein Stück, dessen README noch Gerüst-Platzhalter (Platzhalter-Marke) enthält. Dann steht der Eintrag in der Karte mit dem Stand „Abschrift“."""

import re
from pathlib import Path

import pytest

import brg_data as D

SIBLINGS = Path(__file__).resolve().parent.parent.parent
PLATZHALTER = "TO" + "DO"                  # Marke, mit der new_demo.py ein noch nicht geschriebenes Gerüst kennzeichnet
ENTRIES = D.load()["uebernommen"]


def _readme(repo):
    path = SIBLINGS / repo / "README.md"
    if not path.exists():
        pytest.skip(f"Schwester-Ordner {repo} fehlt")
    return path.read_text(encoding="utf-8")


@pytest.mark.parametrize("entry", ENTRIES, ids=[e["id"] for e in ENTRIES])
def test_every_taken_over_number_stands_verbatim_in_the_sibling_readme(entry):
    text = _readme(entry["repo"])
    if PLATZHALTER in text:
        assert entry["stand"] == "Abschrift", "README noch Gerüst, der Eintrag muss als Abschrift gekennzeichnet sein"
        pytest.skip(f"README von {entry['repo']} ist noch Gerüst (Platzhalter-Marke)")
    for phrase in entry["phrases"]:
        assert phrase in text, f"{entry['repo']}: „{phrase}“ steht nicht mehr in der README"


def test_entries_cover_each_of_the_six_pieces_and_name_source_and_assumptions():
    assert {e["stueck"] for e in ENTRIES} == {1, 2, 3, 4, 5, 6}
    for e in ENTRIES:
        assert e["repo"].endswith("-demo") and e["modell"] and e["aussage"] and e["phrases"] and e["stand"] in ("README gelesen", "Abschrift"), e["id"]


def test_entries_marked_as_read_have_the_sibling_readme_checked_when_present():
    """Ein als „README gelesen“ geführter Eintrag darf nicht auf eine Gerüst-README zeigen."""
    for e in ENTRIES:
        path = SIBLINGS / e["repo"] / "README.md"
        if path.exists() and e["stand"] == "README gelesen":
            assert PLATZHALTER not in path.read_text(encoding="utf-8"), e["id"]


def test_k0_rows_agree_with_piece_three_within_0_02_points():
    """Verlorene Nachfrage, p/h = 9, K = 0, Lieferzeit 1 bis 4: Base-Stock und Capped dieser Demo (Bestellgrenze 12, Bestand 26) gegen die Tabelle in Stück 3 (Bestellgrenze 8)."""
    text = _readme("lieferzeit-position-demo")
    for L in (1, 2, 3, 4):
        m = re.search(rf"^\| 9 \| {L} \| [\d.]+ \| [\d,]+ \| \+([\d,]+) \| \+([\d,]+) \|", text, re.M)
        assert m, L
        bs3, cap3 = (float(x.replace(",", ".")) for x in m.groups())
        cell = D.lost_cell(L, 0.0)
        assert abs(cell["gaps"]["bs"] - bs3) <= 0.02 + 1e-9, (L, cell["gaps"]["bs"], bs3)
        assert abs(cell["gaps"]["cap"] - cap3) <= 0.02 + 1e-9, (L, cell["gaps"]["cap"], cap3)


def test_backorder_rows_agree_with_piece_two_k1_and_k2_rows():
    """Die Zeilen K = 1 und K = 2 des Stücks zur Bestellschwelle (p/h = 9, Lieferzeit 0 bis 3) auf zwei Stellen gerundet."""
    text = _readme("bestellschwelle-demo")
    for K, expected in ((1.0, "0,33 / 1,27 / 1,49 / 2,41"), (2.0, "5,87 / 5,67 / 5,59 / 6,15")):
        ours = " / ".join(f"{D.backorder_cell(9, L, K)['gap_base_stock_pct']:.2f}".replace(".", ",") for L in range(4))
        assert ours == expected
        assert f"K = {int(K)}: {expected} %" in text


def test_k0_rows_agree_with_piece_six_within_0_02_points():
    """Stück 6 nennt dieselben Zeilen mit Bestellgrenze 8 und Bestand 20: Base-Stock +1,75 / +3,35 / +5,03 / +6,44 und Capped +0,10 / +0,69 / +1,63 / +0,82 für Lieferzeit 1 bis 4."""
    text = _readme("dp-grenze-demo")
    if PLATZHALTER in text:
        pytest.skip("README von dp-grenze-demo ist noch Gerüst (Platzhalter-Marke)")
    for label, key in (("(?<!Capped )Base-Stock", "bs"), ("Capped Base-Stock", "cap")):
        m = re.search(rf"{label} \+([\d,]+) / \+([\d,]+) / \+([\d,]+) / \+([\d,]+) / ", text)
        assert m, label
        for L, val in zip((1, 2, 3, 4), m.groups()):
            assert abs(D.lost_cell(L, 0.0)["gaps"][key] - float(val.replace(",", "."))) <= 0.02 + 1e-9, (label, L)
