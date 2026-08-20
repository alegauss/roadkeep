"""Every record that carries the served prefix, and the site that fills it (RK1246).

Four messages block a turn — a `PreToolUse` refusal, the `SessionStart` notice, the `Stop`
report and the attestation beside it — and each carries `served`, the prefix this session's
roadkeep tools arrive under, filled at its own construction site from `served_by(root)`.
Four sites, one fact, nothing holding them together.

Not a theory. RK479 found `Unattested` was the one **not** wired: it rendered a route a
served session could not call, and somebody found it by reading the message. The test written
then holds that one record, which leaves the property asserted per instance by whoever
remembered. RK1244 is the same family the other way round — a second field beside `served`
on one of the four, a three-way answer stored as two, and the census in `test_spelling` swept
both spellings and passed, because it compares what a message *offers* and has no opinion
about what a record *holds*.

So this is the census: :data:`CARRIERS` is total against :func:`carriers`, and each row names
the functions that fill the field. A fifth record added tomorrow is red until somebody says
which site fills it — `remedying`'s table over every code, `PREVENTION` over every finding,
`SITES` over every composed command, applied to the field these four share.

**Derived from the source and never listed**, which is `composing.census`' rule and the
answer to the objection that a field name drifts: renaming `served` empties the population,
and an empty population does not match a table with four rows in it. The rename is a red
here rather than a survey that quietly stops covering anything.

**The site and not merely its existence.** The cheap reading — this record is constructed
somewhere — would have caught RK479 and nothing else. What is asserted instead is that the
named function constructs the record *with `served=` off `served_by`*, which also catches a
site filling it from something the answer is not.
"""

from __future__ import annotations

import ast
from dataclasses import dataclass

from surface import modules

#: The one function that answers what a session's tools are prefixed with (RK488). Every
#: carrier's site reads it, and a site reading anything else is what this census is for.
SOURCE = "served_by"

#: The field itself, named once: it is both what the population is found by and what the
#: keyword at each site has to be.
FIELD = "served"


@dataclass(frozen=True)
class Carrier:
    """One record that carries the prefix, and where it is filled."""

    #: `module:Class`, as :func:`carriers` addresses it.
    where: str
    #: The functions that construct it with the field set. More than one where a module has
    #: two doors onto the same message — `guard` and `_mentioned` both build a `Refusal`.
    sites: tuple[str, ...]
    #: What this message is, so a reader of the table knows what a missing row would cost.
    what: str


CARRIERS: tuple[Carrier, ...] = (
    Carrier(
        "attesting.py:Unattested",
        ("unattested",),
        "the bytes a verb did not write, said once at the end of a turn (RK479)",
    ),
    Carrier(
        # RK1280. The one record that decides nothing: a hand edit to the config is allowed,
        # and the sentence names the verb four of its tables now have — so the door it spells
        # has to be one this session can call, exactly as a refusal's does.
        "guarding.py:Advice",
        ("advise",),
        "a write this gate allows, and the door four of its tables have (RK1280)",
    ),
    Carrier(
        "guarding.py:Notice",
        ("announce",),
        "the line every session is handed before it reads anything (RK82)",
    ),
    Carrier(
        # Two sites and both real: a tool that names the path it writes is denied, and a
        # `Bash` command that only mentions one is asked about (RK128).
        "guarding.py:Refusal",
        ("guard", "_mentioned"),
        "one write denied, and the commands that do it properly (RK22)",
    ),
    Carrier(
        "guarding.py:Review",
        ("review",),
        "what the gate found as the turn tries to end (RK478)",
    ),
)


def carriers() -> tuple[str, ...]:
    """Every class in the package with a `served` field, by address.

    Derived, for the reason `composing.census` is: a second view of the population agrees
    with the first right up to the moment somebody adds a carrier, which is the single moment
    either of them matters.
    """
    found: list[str] = []
    for module in modules():
        for node in ast.parse(module.text).body:
            if not isinstance(node, ast.ClassDef):
                continue
            fields = [
                one.target.id
                for one in node.body
                if isinstance(one, ast.AnnAssign) and isinstance(one.target, ast.Name)
            ]
            if FIELD in fields:
                found.append(f"{module.where}:{node.name}")
    return tuple(sorted(found))


def filled_in(module_where: str, record: str) -> tuple[str, ...]:
    """The functions in that module that construct ``record`` with `served=served_by(…)`.

    The keyword **and** its value, which is the half the cheap reading misses: a site setting
    the field from a literal, or from a second spelling of the question, is exactly the drift
    `served_by` was written to end (RK488).
    """
    (module,) = [one for one in modules() if one.where == module_where]
    found: list[str] = []

    for node in ast.walk(ast.parse(module.text)):
        if not isinstance(node, ast.FunctionDef):
            continue
        for inner in ast.walk(node):
            if not isinstance(inner, ast.Call) or not _names(inner.func, record):
                continue
            if any(
                keyword.arg == FIELD
                and isinstance(keyword.value, ast.Call)
                and _names(keyword.value.func, SOURCE)
                for keyword in inner.keywords
            ):
                found.append(node.name)
    return tuple(dict.fromkeys(found))


def _names(node: ast.expr, wanted: str) -> bool:
    """Whether this callee is that name, written bare or through a module."""
    if isinstance(node, ast.Name):
        return node.id == wanted
    return isinstance(node, ast.Attribute) and node.attr == wanted
