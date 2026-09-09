"""The prose beside a table, held against the table (RK1585).

RK1539 found one instance and closed it where it stood: the comment above `cli._accepting`'s
substitution named **two** collisions and the enumeration finds one, both examples written from
the tool table and neither checked against the parser. Nothing broke — the rule they illustrate
is right whichever example carries it — and what it cost was a reader following the wrong one.

That is not a defect about collisions. It is *the prose beside a table names what the table
holds*, and this package has several tables with prose beside them. A rule closed at each
instance is a rule stated five times; the finding was that nobody had asked how many there are.

**The extraction generalises and the claim does not**, which is why this file is a census and
not a sweep. `surface.claimed` reads the backticked words out of a span; what those words assert
differs per table and cannot be guessed at:

* :data:`~roadkeep.serving.TOOLS`' preamble names four verbs it says are **absent**, so both
  halves are decidable — each is a verb the parser has, and none is served.
* `cli._accepting`'s comment names collisions it says are **present**, so the totality half is
  decidable and the converse is not: a comment may illustrate with one of two and be right.
* `composing.SITES` and the six laws already have closures of their own —
  `test_composing::test_every_site_that_composes_a_command_is_accounted_for` and
  `test_invariants`' first assertion — so they are named here and checked there. A second
  reading would be the drift this file is about, in this file.

What is **not** here is the general form, and the reason is worth the line: a bare backticked
word in this package is a verb, a flag, a field, a file, a config key or an English word in
emphasis, and nothing in the text separates them. `composing` can scan a span because the
invocation prefix *is* the marker; prose about a verb carries no such thing. So the population
is declared and each row says what makes it checkable.

**And the span is addressed by its table, not by its own words** (RK1638). Both checks here
found their prose by splitting the source on a phrase somebody had written, which is this
file's own subject one level in: an author rewording the opening clause did not break the
test, they emptied it — silently, green, covering nothing. `surface.commented` reads the
comment block above a **named binding**, the way this suite addresses a module by its path and
a caller by its name, and refuses the three readings that used to be empty strings: a name
nothing binds, a name bound several times, a binding with no comment at all.
"""

from __future__ import annotations

import pytest

from surface import beside, claimed, commented

from roadkeep import serving
from roadkeep.cli import build_parser

#: Every table in this package with prose beside it that names members, and where the check
#: lives. Two rows are held here and two elsewhere, which is the point of writing them down:
#: the population was invisible, and RK1539 closed one instance of it.
BESIDE: dict[str, str] = {
    "serving.TOOLS": (
        "here — the preamble names four verbs it says are absent, read by `commented` off "
        "the assignment it sits above (RK1638)"
    ),
    "cli._accepting.line": (
        "here — the comment names the collisions the table finds (RK1539), read off the "
        "substitution it is about rather than off a phrase inside it (RK1638)"
    ),
    "composing.SITES": (
        "test_composing::test_every_site_that_composes_a_command_is_accounted_for, which "
        "holds the table total against the census rather than against prose"
    ),
    "the six laws": (
        "test_invariants, whose first assertion is that §0.3 declares exactly the six laws "
        "with a row — the compressed copy in agents.md says that one governs"
    ),
}


def _verbs() -> frozenset[str]:
    """Every subcommand this CLI declares — the set a claim about a verb is checked against."""
    return frozenset(
        [one for one in build_parser()._actions if getattr(one, "choices", None)][0].choices  # noqa: SLF001
    )


def test_the_verbs_the_tool_table_says_it_leaves_out_are_left_out():
    """RK1585, and the row where **both** halves are decidable. The preamble says `init` and
    `adopt` run before the project is governed and that `guard` and `mcp` are the harness's own
    entry points — four claims about a table, none of them checked.

    Each has to be a verb this CLI has, or the prose names something that does not exist; and
    none may be served, or the sentence describes a surface this build does not have.

    The span is addressed by the **table** since RK1638, not by the sentence that opens it: a
    phrase-split answered `""` to an author who reworded the first clause, which is a check
    drifting from its prose — the failure this file exists to end one level up."""
    said = claimed(commented("serving", "TOOLS"))
    served = {one.name.split()[0] for one in serving.TOOLS}
    verbs = _verbs()

    absent = [one for one in said if one in verbs]
    assert absent, "the preamble names no verb at all, so this check reads nothing"
    for verb in absent:
        assert verb not in served, f"the prose says `{verb}` is absent and the table serves it"


def test_every_collision_the_table_finds_is_named_in_the_prose_beside_it():
    """RK1539's totality half, on `surface.claimed` rather than on a regex written once
    (RK1585). The converse is deliberately not asserted: a comment illustrating a rule with one
    of two collisions is right, and what went wrong was an example naming a verb the parser has
    not got — which is the assertion below it.

    Addressed by the assignment the comment is above since RK1638 — `_accepting.line`, the
    substitution the whole span is about — rather than by two phrases and a statement the read
    happened to stop at. The dotted path is what makes it one address: `line` is bound in a
    dozen functions here, and the reader refuses rather than taking the first."""
    from test_serving import COLLIDING  # noqa: PLC0415 - the census lives with its table

    said = claimed(commented("cli", "_accepting.line"))
    assert said, "the comment beside the substitution names nothing, so this check reads nothing"
    for name in COLLIDING:
        assert name in said, f"the table finds `{name}` and the prose beside it does not"


#: One table with prose beside it, in the two spellings this package writes: a `#:` block over
#: a module-level annotation, and a plain comment over an assignment inside a function.
_FIXTURE = '''"""A module."""
#: The table names `alpha` and `beta`.
#: And nothing else.
TABLE: tuple[str, ...] = ("alpha", "beta")


def f(argv):
    line = None
    # The rule turns on `gamma`, which is the one collision.
    picked = line or argv
    return picked


def g(argv):
    # A comment, above the first of two.
    seen = argv
    seen = seen or ()
    return seen
'''


def test_the_span_is_addressed_by_the_binding_and_not_by_its_own_words():
    """RK1638. Both checks above found their prose by splitting the source on a phrase
    somebody had written, so rewording the opening clause did not break them — it emptied
    them. Addressed by the binding the comment sits above, a rewrite of the prose changes what
    is read and nothing about whether it is found.

    Exercised on a fixture, because the proof is that a *reworded* span still reads: this
    package's own comments cannot be reworded from inside a test."""
    assert claimed(beside(_FIXTURE, "TABLE")) == ("alpha", "beta")
    assert claimed(beside(_FIXTURE, "f.picked")) == ("gamma",)

    # The same table, opening clause rewritten and the members untouched: what the old reading
    # answered here was the empty string.
    reworded = _FIXTURE.replace("The table names", "These are the ones it holds:")
    assert claimed(beside(reworded, "TABLE")) == ("alpha", "beta")


def test_the_three_readings_that_used_to_be_silent_are_refusals():
    """Each is a way the phrase-split answered `""` and stayed green: a name nothing binds, a
    name bound in several places, and a binding with no comment above it. A reader that
    defaulted to the empty string in any of them is the check covering nothing.

    A bare `line` is the first of the three and not the second, which is the whole reason the
    address is dotted: every binding here is scoped, so `line` names nothing at module level
    while `f.line` names one thing exactly. `g.seen` is the second — one scope assigning a
    name twice has no single comment to be above it."""
    for name, said in (
        ("MISSING", "is bound 0 times"),
        ("line", "is bound 0 times"),
        ("g.seen", "is bound 2 times"),
        ("f.line", "has no comment above it"),
    ):
        with pytest.raises(LookupError, match=said):
            beside(_FIXTURE, name)


def test_the_population_is_declared_and_every_row_says_where_it_is_held():
    """The half that fails on the *next* table rather than on these: a fifth one with prose
    beside it is a row somebody writes, and a row with no holder in it is the state RK1539 was.

    `test_invariants`' own shape — a rule and what holds it — applied to this one rule."""
    assert len(BESIDE) >= 4, BESIDE
    for table, held in BESIDE.items():
        assert held.startswith("here") or "::" in held or "test_" in held, table
        assert len(held.split()) >= 6, f"{table} names a holder with no reason in it"
