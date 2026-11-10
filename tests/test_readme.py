"""README und App: gleicher Annahmen-Text, genannte Tests existieren, Testzahl stimmt, keine Platzhalter."""

import re
import subprocess
import sys
from pathlib import Path

import brg_texts as T

ROOT = Path(__file__).resolve().parent.parent
PLATZHALTER = "TO" + "DO"
README = (ROOT / "README.md").read_text(encoding="utf-8")


def test_the_assumptions_text_of_the_app_stands_in_the_readme():
    assert T.ASSUMPTIONS_MARKDOWN.strip() in README


def test_every_claim_number_named_in_the_readme_has_a_test():
    claims = (ROOT / "tests" / "test_claims.py").read_text(encoding="utf-8")
    named = set(re.findall(r"\| (K\d\d[a-z]?)(?:,| \|)", README))
    assert len(named) >= 19
    for k in sorted(named):
        assert re.search(rf"def test_{k.lower()}_", claims), f"{k} steht in der README, aber ohne Test in test_claims.py"


def test_every_test_file_named_in_the_readme_exists():
    for name in set(re.findall(r"`(tests/[a-z_]+\.py|test_[a-z_]+\.py)`", README)):
        path = ROOT / "tests" / Path(name).name
        assert path.exists(), name
    assert (ROOT / "tests" / "test_oracle_lost.py").exists() and (ROOT / "tests" / "test_oracle_backorder.py").exists()


def test_the_test_count_in_the_readme_is_the_suite():
    out = subprocess.run([sys.executable, "-m", "pytest", "--collect-only", "-q", "-p", "no:cacheprovider", str(ROOT / "tests")], capture_output=True, text=True, cwd=ROOT).stdout
    m = re.search(r"(\d+) tests? collected", out)
    assert m, out[-300:]
    n = int(m.group(1))
    named = re.search(r"([\d.]+) Tests \(`pytest --collect-only -q tests`\)", README)
    assert named and int(named.group(1).replace(".", "")) == n


def test_no_placeholders_remain_in_readme_and_code():
    for path in list(ROOT.glob("*.py")) + [ROOT / "README.md"] + list((ROOT / "tests").glob("*.py")) + list((ROOT / "tools").glob("*.py")):
        text = path.read_text(encoding="utf-8")
        if path.name == "test_readme.py":
            continue
        assert PLATZHALTER not in text, path.name
        if path.name == "README.md":
            assert "{{" not in text


def test_readme_numbers_of_the_ladder_text_match_the_app_default_mark():
    assert "voreingestellt 2 %" in README and "voreingestellt 2 %" in T.INTRO_MARKDOWN
