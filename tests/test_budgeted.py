"""The area's own budget, and the proof that it refuses (RK1409).

The measurement that started this project is what an unbounded prose file costs. A
documentation area is that same invitation with better typography — every page has room,
nothing refuses a paragraph, and the author who diagnoses the drift is usually the one who
wrote most of it. So the area declares its own numbers and something holds them.

What is checked here is not the prose. It is that the arrangement still works:

* **The declared number is one this corpus does not break.** A limit whose first act is a
  finding is one somebody lowers, reads the report and raises again — which is `govern`'s rule
  about `[limits]`, applied to the area.
* **The check refuses.** A budget nothing enforces is a comment, so this runs the script
  against a page written deliberately over the line and asserts it fails.
* **Every number is argued where it is declared**, not in a commit message nobody will find.
* **The generated half is counted apart.** A verb page's table is as long as the parser makes
  it, and cutting it would be editing a schema to fit a budget.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site"
DECLARED = SITE / "budget.mjs"
SCRIPT = SITE / "scripts" / "budget.mjs"
DOCS = SITE / "src" / "content" / "docs"

node = shutil.which("node")
needs_node = pytest.mark.skipif(node is None, reason="node is not on this machine")


def _declared() -> dict[str, object]:
    """The numbers, read off the module that declares them.

    Read as text rather than imported, for `test_describing`'s reason about the config: this
    suite has no JavaScript to run, and what is being asked — which numbers are declared, and
    is each one argued — is answerable from the source.
    """
    text = DECLARED.read_text(encoding="utf-8")
    default = re.search(r"^export const WORDS = (\d+);$", text, re.MULTILINE)
    assert default, "budget.mjs declares no default"
    named = dict(re.findall(r'^\s*"([^"]+)":\s*(\d+),$', text, re.MULTILINE))
    return {"default": int(default.group(1)), "pages": {k: int(v) for k, v in named.items()}}


def _run(where: Path) -> subprocess.CompletedProcess[str]:
    """Run the check that belongs to `where`, which on a copy is the copy's own.

    It resolves the pages from its **own** file location and not from the working directory —
    so pointing the real script at a copied tree measures the real one, and a test written that
    way passes whatever the copy contains.
    """
    return subprocess.run(
        [node, str(where / "scripts" / "budget.mjs")],
        cwd=where,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


# -- the number, measured rather than picked ----------------------------------


def test_the_declared_number_is_one_this_corpus_does_not_break():
    """`govern` refuses a limit the corpus already breaks, because a number whose first act is
    a finding is one somebody lowers and quietly raises again. The area is held to its own
    rule, and this is that assertion — run rather than argued."""
    found = _run(SITE)
    assert found.returncode == 0, found.stderr


def test_every_number_is_argued_where_it_is_declared():
    """A number without its reasoning is one the next person changes on instinct, and the
    reasoning is the expensive half. Held as a shape: a run of comment above each key."""
    text = DECLARED.read_text(encoding="utf-8")
    for key in ("export const WORDS", *(f'"{one}"' for one in _declared()["pages"])):
        at = text.index(key)
        above = text[:at].rstrip().rsplit("\n\n", 1)[-1]
        assert above.lstrip().startswith("//"), key
        assert len(above.split()) >= 25, f"{key} has a label, not an argument"


def test_the_default_is_not_simply_the_widest_page():
    """A ceiling set at whatever the longest page happens to be refuses nothing on the day it
    is written, which is how "under 150 lines" ends up describing 20 KB. The default is below
    the page that needed its own number, and that page had to be argued for separately."""
    declared = _declared()
    assert declared["pages"], "no page has its own number, so the default was fitted to the max"
    assert declared["default"] < min(declared["pages"].values())


# -- and it refuses, which is the whole of it ---------------------------------


@needs_node
def test_a_page_over_the_line_fails_the_build(tmp_path):
    """A budget nothing enforces is a comment. Run against a copy of the area carrying one
    deliberately over-long page, so what is asserted is the refusal and not the intent."""
    where = tmp_path / "site"
    shutil.copytree(SITE, where, ignore=shutil.ignore_patterns("node_modules", ".astro"))
    over = where / "src" / "content" / "docs" / "sprawl.mdx"
    over.write_text(
        "---\ntitle: Sprawl\n---\n\n" + ("word " * 2000),
        encoding="utf-8",
        newline="\n",
    )
    found = _run(where)
    assert found.returncode != 0
    assert "over the area's budget" in found.stderr
    assert "sprawl.mdx" in found.stderr
    # It says how much to cut, which is the difference between a gate and a complaint.
    assert "cut " in found.stderr


@needs_node
def test_a_page_that_states_a_count_fails_the_build(tmp_path):
    """Every figure in this area is rendered — the tool counts its own tools, keys, codes and
    pages — so a number typed into a sentence is one that goes stale with nothing reporting
    it. Two pages carried one when this was written, both restating figures another file owns.
    """
    where = tmp_path / "site"
    shutil.copytree(SITE, where, ignore=shutil.ignore_patterns("node_modules", ".astro"))
    counted = where / "src" / "content" / "docs" / "counted.mdx"
    counted.write_text(
        "---\ntitle: Counted\n---\n\nThis tool serves 64 tools today.\n",
        encoding="utf-8",
        newline="\n",
    )
    found = _run(where)
    assert found.returncode != 0
    assert "state a count in prose" in found.stderr
    assert "counted.mdx" in found.stderr


@needs_node
def test_a_number_inside_code_is_not_a_claim(tmp_path):
    """The rule is about **sentences**. A command somebody types and a fragment in a link
    target are examples rather than measurements, and a check that refused them would be one
    every page works around.

    Link *text* is not exempt, and deliberately: it is prose a reader sees, so "the 64 tools"
    written as a link label is the same claim as writing it plainly.
    """
    where = tmp_path / "site"
    shutil.copytree(SITE, where, ignore=shutil.ignore_patterns("node_modules", ".astro"))
    page = where / "src" / "content" / "docs" / "fine.mdx"
    page.write_text(
        "---\ntitle: Fine\n---\n\nRun `roadkeep lint --baseline HEAD~10` and see"
        " [the gate](https://example.com/a#L42).\n\n```bash\nport 8080\n```\n",
        encoding="utf-8",
        newline="\n",
    )
    found = _run(where)
    assert found.returncode == 0, found.stderr


# -- what is counted, and what is reported apart ------------------------------


def test_the_generated_pages_are_counted_apart_and_said_so():
    """A verb page's table is as long as the parser makes it. Counting it would make the budget
    a rule about the schema, and skipping it silently would make the figure meaningless."""
    found = _run(SITE)
    assert "generated and not counted" in found.stdout
    assert re.search(r"\[budget\] \d+ page\(s\) counted", found.stdout)


def test_the_widest_page_is_reported_so_the_next_number_is_read_not_guessed():
    """The reading behind the number, printed on every build. RK1094 is the case against not
    doing this: a percentage quoted from memory had gone stale, and re-measuring reversed the
    advice it supported."""
    found = _run(SITE)
    assert re.search(r"widest is \S+ at \d+ of \d+", found.stdout)


def test_the_check_runs_before_the_build():
    scripts = json.loads((SITE / "package.json").read_text(encoding="utf-8"))["scripts"]
    assert "scripts/budget.mjs" in scripts["prebuild"]


def test_no_page_in_the_area_states_a_count():
    """The corpus itself, held here as well as by the build — so it is red in a suite run on a
    machine with no node on it."""
    for page in sorted(DOCS.rglob("*.mdx")):
        if "findings" in page.parts:
            continue
        text = page.read_text(encoding="utf-8")
        body = text.split("---", 2)[2] if text.startswith("---") else text
        body = re.sub(r"```[\s\S]*?```", " ", body)
        body = re.sub(r"`[^`]*`", " ", body)
        body = re.sub(r"\]\([^)]*\)", " ", body)
        body = re.sub(r"<[^>]+>", " ", body)
        assert not re.findall(r"\b\d{2,}\b", body), page.name
