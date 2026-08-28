"""The model page, and the one thing that tells whether it is doing its job (RK1407).

The verbs are learnable one at a time; the system behind them is not. A line, a pointer, a
block, a criterion and a decision are one thing, and learning it one refusal at a time is how a
tool gets used as six unrelated commands.

This is the one page here that is **prose all the way down** — every other reference in the
area is generated, because a flag or a config key retyped by hand is wrong at the first rename.
The model is what no read answers, so nothing checks its sentences. What *can* be checked is
whether it still covers the system:

* **Every role and every marker kind the package declares appears on it.** A seventh role added
  tomorrow is part of the model whether or not anybody remembers this file, and a page that
  quietly stopped describing one would read exactly like a complete one.
* **Every reference page links to it.** That is the task's own test: if a verb page has to say
  what a block is before it can say what the verb does, that sentence belongs on the model page
  and the reference points at it.
* **It generates nothing**, which is the other half of the same rule — a table imported here
  would be a second copy of something the reference already renders.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from roadkeep.config import PROSE_ROLES, ROLES, Config

HERE = Path(__file__).resolve().parent.parent
SITE = HERE / "site" / "docs"
PAGE = SITE / "src" / "content" / "docs" / "model.mdx"
REFERENCE = SITE / "src" / "content" / "docs" / "reference"

#: How the area addresses this page. One string, because a rename that moved the page and not
#: the six links would leave every reference pointing at a 404.
LINK = "/roadkeep/docs/model/"


def _text() -> str:
    return PAGE.read_text(encoding="utf-8")


# -- the census: what the model is, held against what the package declares -----


def test_every_role_the_package_declares_is_described():
    """A role is a job and not a filename, and which jobs exist is the package's claim. A
    seventh added tomorrow is part of the model whether or not anybody remembers this file."""
    text = _text()
    assert ROLES, "the package declares no roles, so this asserts nothing"
    missing = [role for role in ROLES if f"`{role}`" not in text]
    assert missing == [], missing


def test_the_prose_roles_are_told_apart_from_the_record_roles():
    """`improvements` and `strategy` are the pair a reader gets wrong: both hold prose, and
    only one of them is deleted in the ordinary course of work. A page that listed six files
    without that distinction would have described the filenames and not the model."""
    text = _text()
    assert set(PROSE_ROLES) <= set(ROLES)
    assert "deleted" in text
    assert "outlives" in text


def test_every_marker_kind_is_accounted_for():
    """Where a line *is* is the first thing anybody asks of a backlog. The four kinds are the
    package's, so a fifth is a red here rather than a page that silently covers four."""
    schema = Config.default().schema
    text = _text().lower()
    assert schema.markers, "no open markers are declared"
    for kind in ("open", "shipped", "retired", "paused"):
        assert kind in text, kind


def test_the_four_doors_are_named_with_what_each_leaves_behind():
    """The question this page exists to answer once: a task leaves by exactly one door, and
    what it leaves behind is what a later reader finds."""
    text = _text().lower()
    for door in ("ship", "retire", "defer", "supersede"):
        assert door in text, door


# -- the task's own test: does the reference have to explain itself? ----------


@pytest.mark.parametrize("page", sorted(REFERENCE.glob("*.mdx")), ids=lambda one: one.stem)
def test_every_reference_page_points_at_the_model_rather_than_restating_it(page):
    """RK1407's own test, stated as a check. If a verb page needs to say what a block is
    before it can say what the verb does, that sentence belongs on the model page — so every
    reference page carries the link, and a new one that forgot it is a red."""
    assert LINK in page.read_text(encoding="utf-8"), page.name


def test_the_link_is_the_address_the_page_is_published_at():
    """Six pages point here by a hand-written path, which is the one thing about this join that
    can rot silently: a moved page leaves every one of them on a 404."""
    assert PAGE.exists()
    base = re.search(r'const BASE = "([^"]+)"', (SITE / "astro.config.mjs").read_text("utf-8"))
    assert base
    assert LINK == f"{base.group(1)}/{PAGE.stem}/"


def test_the_page_is_reachable_from_the_sidebar_before_the_reference():
    """It is the read that makes the others cheaper, so it comes first."""
    config = (SITE / "astro.config.mjs").read_text(encoding="utf-8")
    assert 'link: "/model/"' in config
    assert config.index('link: "/model/"') < config.index('label: "Reference"')


# -- prose all the way down ---------------------------------------------------


def test_the_page_generates_nothing():
    """Every other reference here is derived, and this one may not be: a table imported here
    would be a second copy of what the reference already renders, and the copy nobody is
    looking at is the one that drifts."""
    text = _text()
    assert "import " not in text
    assert "<VerbTable" not in text
    assert "<ConfigTable" not in text


def test_the_page_says_it_is_the_one_thing_nothing_derives():
    """The rule a later author needs, written where they will read it. Every other page here
    is generated on purpose, so a reader of this source has to be told why this one is not."""
    assert "Nothing on this page is generated" in _text()
