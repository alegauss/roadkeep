"""L5, as a property: every question written down here is a command that only reads (RK1021).

`asking.py` is the inventory and this is what holds it. Four claims, and the second is the
one that keeps the first from decaying into a list somebody stopped adding to.

The law is *query instead of read*, and what it is worth depends on both directions being
checked. A question with no command sends its asker to an editor, which is the failure L5
names. A question whose command **writes** is worse than that: it answers by changing the
file it was asked about, and a reader who did not want that has no way to know before
running it. And a verb that answers a question nobody wrote down is an inventory that has
stopped covering the surface while still reporting itself total.

The join to `skills/roadkeep/SKILL.md` is the fourth, and it is what makes the inventory
somebody else's too: that file is what every adopting project loads, so a question this
project can answer and that file never names is one no adopting project will ever ask.
"""

from __future__ import annotations

import re
from pathlib import Path

from asking import ANSWERS_NO_QUESTION, QUESTIONS, read_only, verb_of, verbs

from roadkeep.cli import build_parser

SKILL = Path(__file__).resolve().parents[1] / "skills" / "roadkeep" / "SKILL.md"


def _skill() -> str:
    """The skill **whole** — the orientation and the reference pages beside it (RK1437).

    The split is a cadence and not a subtraction: a read named on `asking.md` is still named
    in the file every adopting project loads, one pointer away. Reading `SKILL.md` alone
    would have made this inventory report the whole query surface as unpublished the day it
    moved to the page whose subject it is.
    """
    from roadkeep.installing import PLUGIN_PAGES

    root = SKILL.resolve().parents[2]
    return "\n".join(
        [SKILL.read_text(encoding="utf-8")]
        + [(root / page).read_text(encoding="utf-8") for page in PLUGIN_PAGES]
    )


def _backticked(text: str) -> list[str]:
    """Every span the file spells as code, which is how it names a command."""
    return re.findall(r"`([^`]+)`", text)


def test_every_declared_question_is_answered_by_a_command_that_only_reads():
    """The law itself. Each row's argv is fed to the real parser: it has to resolve to a
    handler, and that handler has to be one the CLI declares as a read — the same
    `reads_only` the write lock is built on, so this inventory and RK117 can never disagree
    about which verbs answer without writing."""
    reads = read_only()
    for question in QUESTIONS:
        args = build_parser().parse_args(list(question.answered_by))
        assert getattr(args, "handler", None), question.asked
        assert verb_of(question) in reads, f"{question.asked}: {verb_of(question)} writes"


def test_every_read_only_verb_answers_a_declared_question_or_says_it_answers_none():
    """The closure, and the half that stops the inventory going stale. A verb added to the
    CLI is a red here until somebody either writes the question it answers or writes down
    why it answers none — which is the cost of a new read, paid once, in a sentence."""
    answered = {verb_of(question) for question in QUESTIONS}
    exempt = set(ANSWERS_NO_QUESTION)
    assert answered & exempt == set(), answered & exempt
    assert answered | exempt == read_only(), {
        "verb, no question": read_only() - answered - exempt,
        "question, no verb": answered | exempt - read_only(),
    }


def test_every_exemption_is_a_sentence_and_not_a_name():
    """The exemption is where an inventory rots, so it carries a reason and the reason is
    asserted to exist. Four verbs are here: two transports whose caller is a program, and
    two whose subject is a defect in this tool rather than a governed file."""
    for verb, why in ANSWERS_NO_QUESTION.items():
        assert verb in verbs(), f"{verb}: exempted, and this CLI has no such verb"
        assert len(why.split()) >= 6, f"{verb}: {why!r} is a name wearing a sentence"


def test_the_inventory_is_published_where_an_adopting_project_reads_it():
    """The join. Every question here is answered by a verb, and every one of those verbs is
    named in the skill — the file every adopting project loads and the only place another
    repository learns what it may ask. A read this project can make and that file never
    mentions is a read only this project will ever make."""
    published = _backticked(_skill())
    missing = [
        verb_of(question)
        for question in QUESTIONS
        if not any(
            re.search(rf"(?<![\w-]){re.escape(verb_of(question))}(?![\w-])", span)
            for span in published
        )
    ]
    assert missing == [], missing


def test_no_question_is_a_verb_spelled_as_a_sentence():
    """A row whose question is its own command asserts the surface against itself, which is
    the shape this inventory would decay into first: it would still be total, still green,
    and would have stopped saying anything about what somebody wanted to know."""
    for question in QUESTIONS:
        assert question.asked[:1].islower(), question.asked
        assert not question.asked.endswith("?"), f"{question.asked}: the row is a clause"
        assert verb_of(question) not in question.asked.split(), question.asked
    asked = [question.asked for question in QUESTIONS]
    assert len(asked) == len(set(asked)), asked
