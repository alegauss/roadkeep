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


#: The four relations this backlog has. Two share a resolver and two do not, which is a
#: fact about the target space rather than an omission: an id lives in a set of records and a
#: heading lives in a tree of prose, and a resolver that pretended otherwise would answer
#: `ref.ambiguous` — two files declaring one anchor — with a lookup that has no such case.
#:
#: The fourth arrived the way this index was written to make possible (RK1106): a citation
#: was always a reference and nothing resolved it, so `ship` deleted designs other designs
#: argued from and the gate reported clean over 11 of them in claude-tray and 25 in Turing.
#: What it cost to add was a row here, a scan `citing` already had, and the pointer's own
#: resolver — which is the argument §RK1066 made and could not yet demonstrate.
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
        name="citation",
        # Not a field of a task line at all — the first relation whose carrier is prose, which
        # is why it took a scan to find and not a lookup: `body` is the whole paragraph, and
        # which of its tokens is a reference is `sections.references`' reading to make.
        field="body",
        targets="heading",
        empty="",
        # The pointer's resolver, deliberately: a citation of `§S:I.2` resolves in the same
        # index a `→ §S:I.2` does, and two answers about one address would be the disagreement
        # this file exists to prevent — one of them across the namespaces and one inside a file.
        resolver="roadkeep.sections.anchored",
        # Two, since RK1168: an address neither file declares is `ref.dangling`, and one that
        # resolves into the *other* prose file while the citing file declares the same address
        # is `ref.crossed` — the state a namespace leaves behind, which reads as correct.
        answers=("ref.dangling", "ref.crossed"),
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


@dataclass(frozen=True, slots=True)
class Carried:
    """One pair of governed files that may not both hold a line for the same id (RK1082).

    The fourth relation, and the same kind as the other three: a target, a sentinel meaning
    *no reference*, and a policy for a target that turned out to be somewhere else. What
    differs is the direction — a dep points at an id and this one points at a **file**, so
    the pairs are a cross product over :data:`~roadkeep.ids.CARRIERS` rather than a rule
    somebody writes per pair.

    Written per pair and not folded into one message, which is the line RK1081 drew and this
    keeps: open-and-gone, open-and-paused and gone-and-paused are three sentences with three
    doors. The declaration holds *which pairs exist*; the wording and the remedy stay with
    the code. A pair with no code yet is a pair nobody has walked into, and it says so here
    rather than by being absent — which is the whole difference from the arrangement RK1077
    was filed about, where a gap was found by the project that reached it.
    """

    #: The role a finding about this pair is filed against, and whose line number it carries.
    first: str
    #: The other file holding a line for the same id.
    second: str
    #: The gate code, or `""` where no rule reads this pair yet — and then :attr:`because`
    #: says what is missing rather than leaving a silence.
    code: str = ""
    #: What the two files each claim, as the finding's own sentence spells it.
    says: str = ""
    #: Why there is no rule, on a pair whose `code` is empty.
    because: str = ""


#: Every pair of governed files that can hold a line for one id (RK1082). Three, because
#: `CARRIERS` is three, and all three are read since RK1084 — which measured first and found
#: that **neither adopting corpus declares a store at all**, so the pair nobody had walked
#: into is one nobody *can* walk into yet. The rule is written anyway: a contradiction the
#: format can express should not be silent, and the cost of the third row is one entry here.
PAIRS: tuple[Carried, ...] = (
    Carried(
        first="roadmap",
        second="changelog",
        code="id.two-files",
        says="open and recorded as gone are not both true",
    ),
    Carried(
        first="roadmap",
        second="deferred",
        code="id.paused-and-open",
        says="open and paused are not both true",
    ),
    Carried(
        first="changelog",
        second="deferred",
        code="id.paused-and-gone",
        says="recorded as gone and still paused are not both true",
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
