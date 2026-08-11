"""Reference as a field type — the relations this backlog has, declared (RK1066).

A field whose type is a *reference* carries its own integrity, and this gate asks that
question in three vocabularies: a dep names an id, a pointer names a heading, a queue entry
names an id or a block. Sixteen of the thirty-eight codes those four families emit are
reference questions, and the argument for declaring them is that a **fourth** relation
should be a line here rather than a fourth implementation somewhere.

**What measuring found, and it is not what §RK1066 assumed.** That section reads *deps
resolve in backlog.py, pointers and orphan sections in linting.py and the queue's tokens in a
third place*. There is no third place: `_queued` calls `Backlog.resolve_dep` and turns one
:class:`~roadkeep.backlog.Resolution` into the `priority.*` codes, so the queue and the deps
have shared one machine since RK326. Two vocabularies, one resolver. What was missing was
never the resolver — it was the **index**: nothing said which relations exist, which machine
each uses, or which codes each is the source of, so the answer to "where does a fourth one
go" was a reading of three modules.

So this is that index, and its one hard property is that it is **total**. Every reference
code the gate can emit is named by exactly one relation, and every rule that stays code is
named in :data:`ELSEWHERE` with the reason it cannot be a constraint over a record. A
declaration listing only the half that fit is the second source of truth this tool exists to
remove, and it would be one carrying the tool's own authority — so `tests/test_referring.py`
holds the closure rather than this paragraph.

The line this draws is the one that decides whether a declaration is worth anything: a
vocabulary of *scalar* types — string, max, enum — buys none of this, and a **relational**
one buys all of it. A `maxLength` with better branding is not the thing.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Relation:
    """One kind of reference a record's field can carry, and what answers about it.

    `resolver` is the code that says what the target *is*, named rather than imported: this
    module is an index and importing the three would make it a layer. `answers` is every
    gate code this relation is the source of, which is what makes the index checkable —
    a code belonging to no relation and to no :data:`ELSEWHERE` entry is a rule nothing here
    accounts for, and that is the state this file exists to make impossible.
    """

    #: What the field means, in the words the format uses for it.
    name: str
    #: The field that carries it, as the record spells it.
    field: str
    #: What a value points at: an id, a heading anchor, or either an id or a block label.
    targets: str
    #: The value meaning *no reference*, which is not an unresolved one — a line with no
    #: deps is complete, and a resolver that could not tell the two apart would report
    #: every such line. `""` where the field is simply absent.
    empty: str
    #: Where the target's state is decided, by qualified name.
    resolver: str
    #: Every code this relation is the source of.
    answers: tuple[str, ...]


#: The three relations this backlog has. Two share a resolver and one does not, which is a
#: fact about the target space rather than an omission: an id lives in a set of records and a
#: heading lives in a tree of prose, and a resolver that pretended otherwise would answer
#: `ref.ambiguous` — two files declaring one anchor — with a lookup that has no such case.
RELATIONS: tuple[Relation, ...] = (
    Relation(
        name="dep",
        field="deps",
        targets="id",
        # The em dash a rendered line carries where a task waits on nothing (`NO_DEPS`).
        empty="—",
        resolver="roadkeep.backlog.Backlog.resolve_dep",
        answers=("deps.unknown", "deps.retired", "deps.cycle", "deps.block"),
    ),
    Relation(
        name="pointer",
        field="ref",
        targets="heading",
        empty="",
        resolver="roadkeep.sections.anchored",
        answers=(
            "ref.unresolved",
            "ref.ambiguous",
            "section.orphan",
            "section.unreachable",
            # The same ambiguity from the target's side (RK239): two prose files declaring
            # one anchor is a defect at both headings whether or not a line reached it.
            # §RK1066 counted four here and there are five, which the closure test found on
            # its first run — the argument for a total index, made by the index.
            "section.ambiguous",
        ),
    ),
    Relation(
        name="queued",
        field="priority",
        targets="id-or-block",
        empty="",
        # The same machine the deps use, which is the half of RK1066 that was already
        # done: `_queued` reads one `Resolution` and spells it in this family's codes.
        resolver="roadkeep.backlog.Backlog.resolve_dep",
        answers=(
            "priority.unknown",
            "priority.shipped",
            "priority.retired",
            "priority.deferred",
            "priority.block",
            "priority.block-empty",
            "priority.block-paused",
            "priority.block-unstarted",
        ),
    ),
)


#: The rules in these four families that are **not** reference questions, each with why. Here
#: rather than left out, because the index has to name every rule including the ones it does
#: not implement: a reader asking "is this relation declared" must not have to know which
#: half of the file to look in. Three kinds — the shape of a value before anything is
#: resolved, a traversal that reads more than one record, and a procedure over history.
ELSEWHERE: Mapping[str, str] = {
    # -- the shape of the value, which is a scalar question and stays one -------------
    "deps.format": "the token's own shape, refused before any target is looked for",
    "deps.range": "a range whose ends are the wrong way round: a shape, not a target",
    "deps.compound": "two relations written into one token, which is a spelling",
    "deps.self": "a line naming itself, decidable from the record alone",
    "deps.duplicate": "one target named twice in one field, decidable from the field",
    "deps.marker": "the cached annotation, which is derived and re-derived (RK8)",
    "deps.stale": "the same annotation gone out of date, which `--fix` rewrites",
    "deps.unexpected": "a field the role's grammar drops carrying a value (RK1064)",
    "deps.collective": "a note about what `Block X` names, not a defect about a target",
    "ref.format": "the anchor's shape under `ref_scheme`, before it is resolved",
    "ref.sigil": "the `§` itself, a character question",
    "ref.missing": "a line that carries no pointer where the role requires one",
    "ref.mismatch": "a pointer that is not the one the id derives (RK1063)",
    "priority.shape": "a queue token that is neither an id nor a block label",
    "priority.duplicate": "one token queued twice, decidable from the queue alone",
    # -- traversals and procedures, which are not constraints over a record ----------
    "section.too-long": "a word budget over a subtree, which is a traversal (RK9)",
    "section.duplicate": "two headings at one address, a property of the prose file",
    "section.stale": "a section whose task left, decided against the other files",
    "section.unpaired": "a design with no line since a revision, which reads git",
    "priority.config": "where the queue is declared, a fact about `roadkeep.toml`",
    "priority.unmigrated": "a queue in the old home, a migration and not a target",
}
