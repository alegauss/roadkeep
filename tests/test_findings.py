"""The finding pages, held against the table the gate explains from (RK1403).

The reader this exists for is the one who has *not* adopted the tool: a person looking at a
failed CI job, or at a hook that has just denied a write. `explain` answers them and answers
only from an installed copy, so the answer is behind the door the code is keeping shut.

A page per code fixes that, and being generated is what keeps it true — a code added to the
gate is documented in the commit that adds it, and one deleted stops being documented rather
than becoming a page about a check nobody runs.

The one half that is written by hand is the **situation**: the ordinary act that put the reader
there. A code is a classification, and a classification is not what somebody staring at a
failed job needs first. So `situations.json` is committed, the pages are not, and the join
between them is what this file holds:

* **No orphan.** A key naming a code this build does not have is a sentence about a check that
  is gone — which the generator refuses outright, because a page rendered from it would look
  exactly like a page about a live code.
* **No situation that only restates the cause.** The page would then say one thing twice under
  two headings, and a reader concludes the second is an answer to something the first missed.
* **The shortfall is reported and not hidden.** Most codes have no situation yet. That is a
  number the generator prints on every build rather than a silence, because a coverage figure
  nobody sees is one nobody closes.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site"
SITUATIONS = SITE / "src" / "data" / "situations.json"
GENERATOR = SITE / "scripts" / "findings.mjs"


def _codes() -> dict[str, dict]:
    """Every finding code this checkout declares, asked the way the generator asks."""
    found = subprocess.run(
        [sys.executable, "-m", "roadkeep.cli", "explain", "--json"],
        cwd=HERE,
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={"PYTHONPATH": str(HERE / "src"), "PYTHONIOENCODING": "utf-8", "PATH": ""},
    )
    assert found.returncode == 0, found.stderr
    return {one["code"]: one for one in json.loads(found.stdout)}


def _situations() -> dict[str, str]:
    """The hand-written half, without the file's own prose about how to write one."""
    raw = json.loads(SITUATIONS.read_text(encoding="utf-8"))
    return {key: value for key, value in raw.items() if not key.startswith("_")}


# -- the join, in the direction that must never drift -------------------------


def test_every_situation_names_a_code_this_build_declares():
    """An orphan is a sentence describing a check that no longer exists, and nothing on the
    page would say so — it renders exactly like a page about a live code. Caught here, and
    refused by the generator too, for the reason `lint` and `add` both hold the line format."""
    declared = set(_codes())
    assert declared, "the gate declares no codes, so this asserts nothing"
    assert set(_situations()) <= declared, {
        "described, but no such code": sorted(set(_situations()) - declared)
    }


def test_no_situation_merely_restates_the_cause():
    """`explain` already prints the cause on every page. A situation that paraphrases it makes
    the page say one thing twice under two headings, and the reader concludes the second half
    is an answer to something the first did not cover.

    Held as a shape rather than by reading the English: a situation says what somebody *did*,
    so it is longer than the clause it sits above and does not open with the same words.
    """
    codes = _codes()
    for code, situation in _situations().items():
        cause = codes[code]["cause"]
        assert situation.strip() != cause.strip(), code
        opening = " ".join(cause.split()[:5]).lower()
        assert not situation.lower().startswith(opening), code


def test_every_situation_is_a_sentence_somebody_wrote():
    """The failure a table of hand-written prose has: a row added to make a count go up."""
    for code, situation in _situations().items():
        assert len(situation.split()) >= 12, f"{code} has no situation in it"
        assert situation[0].isupper(), f"{code}: a sentence, not a clause"
        assert situation.rstrip().endswith("."), code


def test_the_file_argues_for_how_a_situation_is_written():
    """The rule that decides what belongs here, beside the entries rather than in a commit
    message — which is where the next author will look for it, and the only place they will."""
    raw = json.loads(SITUATIONS.read_text(encoding="utf-8"))
    prose = " ".join(raw["_comment"])
    assert "no read can derive" in prose
    assert "restates the cause" in prose


# -- what the generator must and must not do ----------------------------------


def test_the_generator_refuses_an_orphan_rather_than_skipping_it():
    """A generator that quietly dropped an unknown key would leave the drift invisible until
    somebody read the situations file and wondered why one had no page."""
    source = GENERATOR.read_text(encoding="utf-8")
    assert "situations.json describes codes this build does not have" in source
    assert "throw new Error" in source


def test_the_generator_reports_how_many_codes_have_no_situation():
    """Most of them do not, and that number is printed on every build. A bound nobody prints
    reads exactly like full coverage."""
    source = GENERATOR.read_text(encoding="utf-8")
    assert re.search(r"carry a hand-written situation", source)
    assert "do not" in source


def test_the_generator_empties_the_directory_before_it_writes():
    """A page left behind by a deleted code keeps rendering, and is the one kind of stale page
    nothing else here can detect: it is well-formed, it is indexed, and it documents a check
    that no longer runs."""
    source = GENERATOR.read_text(encoding="utf-8")
    assert "rmSync" in source


def test_the_generated_pages_are_never_committed_and_the_situations_always_are():
    """Two files under `src/data/` with opposite lives. Ignoring the directory — which is what
    the first version did — would have left the hand-written half out of the repository."""
    ignored = [
        line.strip()
        for line in (SITE / ".gitignore").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert "src/content/docs/findings/" in ignored
    assert "src/data/*.generated.json" in ignored
    assert not [one for one in ignored if one.rstrip("/") == "src/data"]
    assert SITUATIONS.exists()


def test_both_generators_run_before_the_build():
    scripts = json.loads((SITE / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert "scripts/findings.mjs" in scripts["prebuild"]
    assert "scripts/commands.mjs" in scripts["prebuild"]


def test_the_sidebar_carries_the_findings_collapsed():
    """A hundred-odd codes is a list for browsing and never the way in — the reader arrives
    with the code already in hand, from a job log or a search engine."""
    config = (SITE / "astro.config.mjs").read_text(encoding="utf-8")
    assert re.search(r'label:\s*"Findings"', config)
    assert re.search(r'autogenerate:\s*\{\s*directory:\s*"findings"', config)
    assert "collapsed: true" in config


@pytest.mark.parametrize(
    "code", ["char.bom", "deps.unknown", "line.too-long", "id.duplicate"]
)
def test_the_codes_a_reader_meets_first_are_the_ones_described(code):
    """Not a coverage bar — the shortfall is real and reported. What is held is that the
    handful anybody actually hits are not the ones left undescribed."""
    assert code in _situations()


def test_the_url_carries_the_code_a_reader_pasted():
    """Astro slugifies a dot away, so `block.emptied` first shipped at `/findings/block/
    blockemptied/` — a URL that does not contain the string somebody pasted into a search
    engine, which is the entire reason these pages exist. The slug is declared, and a hyphen
    keeps the two halves apart and reads back as the code."""
    source = GENERATOR.read_text(encoding="utf-8")
    assert re.search(r'replace\(/\\./g,\s*"-"\)', source)
    assert "slug: ${slug}" in source
