"""Which modules of this package import each other, and why each pair does (RK1383).

RK1382 removed one cycle on an argument: a record belongs with the reading that builds it, and
a presenter imports a record rather than declaring one. Twenty-one pairs remained, and the
finding was not that they are defects — it is that the set was invisible. A cycle written
tomorrow is indistinguishable from the ones already there, so that argument has to be remade
from scratch each time somebody happens to notice one.

**Read from the source and never from `sys.modules`.** The cycle RK1382 removed lived in two
call-time imports, which is precisely what a runtime check does not see: by the time a module
object exists, an import inside a function has not run.

**Two states, and the second is a work-list.** `shape` is a pair somebody looked at and a
sentence saying what the boundary is doing; `unexamined` is a pair nobody has, carrying the one
reason that says so. Kept apart because a table spelling both as a sentence would let the
second read as a decision — which is the failure every census in this suite is written against.

Several of the pairs below already carry their reason at the import site, in a comment or a
docstring. That is where a reason belongs and this is where it becomes countable: the argument
was written once and no reader could tell you how many others there were.
"""

from __future__ import annotations

import ast

from surface import modules

#: A pair nobody has examined. One sentence for all of them, so the state is visible as a state
#: rather than dressed as twenty judgements — `composing.SITES` draws the same line, for the
#: same reason: an exemption nobody can see reads exactly like a rule being kept.
UNEXAMINED = (
    "unexamined: which of the two owns what passes between them is the question RK1382 "
    "answered for one pair, and nobody has asked it of this one"
)

#: The shared printer, which is a hub by construction: a reader imports its row composers and
#: it imports their records to name what those rows are about. RK1382's direction holds on the
#: presenter's side — it imports the record — and the reader importing a row helper back is what
#: closes the loop. Whether the records belong under `rendering` is the question this states.
PRINTER = (
    "shape: `rendering` composes the rows every write answers with, and names the record each "
    "row is about — a hub the layout declares, and the loop is a reader calling into it"
)

#: The entry point, for the same reason and one layer out: `build_parser` and `dispatch` are how
#: every surface is reached, and each surface is named by the parser that reaches it.
ENTRY = (
    "shape: `cli` is the parser and the dispatch every surface is reached through, and each "
    "names the other because one builds the argv and the other is what it runs"
)

#: One row per pair, keyed by the two module addresses in sorted order. Held total against the
#: source below, so a pair added tomorrow is a red here with one question in it: say what the
#: boundary is doing, or say that nobody has looked.
CYCLES: dict[tuple[str, str], str] = {
    ("authoring", "rendering"): PRINTER,
    ("blocking", "rendering"): PRINTER,
    ("briefing", "rendering"): PRINTER,
    ("claiming", "rendering"): PRINTER,
    ("deferring", "rendering"): PRINTER,
    ("graph", "rendering"): PRINTER,
    ("ids", "rendering"): PRINTER,
    ("merging", "rendering"): PRINTER,
    ("picking", "rendering"): PRINTER,
    ("capturing", "cli"): ENTRY,
    ("cli", "serving"): ENTRY,
    ("cli", "verbs.linting"): ENTRY,
    ("config", "kernel.document"): (
        "shape: the kernel names `Config` under `TYPE_CHECKING` alone, so at runtime it imports "
        "nothing above it and the layout's claim about this layer holds as written"
    ),
    ("exporting", "kernel.document"): (
        "shape: a call-time import whose own docstring argues it — a projection refresh planned "
        "anywhere but where the transaction is assembled lands outside the all-or-nothing write"
    ),
    ("adopting", "serving"): UNEXAMINED,
    ("authoring", "blocking"): UNEXAMINED,
    ("authoring", "budgeting"): UNEXAMINED,
    ("authoring", "sections"): UNEXAMINED,
    ("briefing", "budgeting"): UNEXAMINED,
    ("history", "provenance"): UNEXAMINED,
    ("history", "sections"): UNEXAMINED,
    ("installing", "linting"): UNEXAMINED,
}


def _imports(text: str) -> set[str]:
    """Every module of this package one file imports, call-time imports included.

    `ImportFrom` and `Import` both, and no filtering on where in the tree the node sits: the
    cycle RK1382 removed was two imports inside functions, and a reader that only looked at the
    top of the file would have reported the package as acyclic while it was not.
    """
    out: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("roadkeep."):
            out.add(node.module[len("roadkeep.") :])
        elif isinstance(node, ast.Import):
            out.update(
                one.name[len("roadkeep.") :]
                for one in node.names
                if one.name.startswith("roadkeep.")
            )
    return out


def _pairs() -> set[tuple[str, str]]:
    """Every pair of this package's modules that import each other, sorted within the pair."""
    edges = {
        one.where[: -len(".py")].replace("/", "."): _imports(one.text) for one in modules()
    }
    return {
        tuple(sorted((name, other)))  # type: ignore[misc]
        for name, seen in edges.items()
        for other in seen
        if other in edges and name in edges[other]
    }


def test_every_pair_that_imports_itself_back_is_named():
    """The census, which is the deliverable. A pair reaches this file one of two ways and there
    is no third: a sentence about what the boundary is doing, or the one that says nobody has
    looked. Total against the source, so a cycle written tomorrow is a red rather than a
    twenty-second one nobody counts."""
    found = _pairs()
    assert found, "the reader stopped finding pairs: this census is reading nothing"
    assert found == set(CYCLES), {
        "imports itself back, unnamed": sorted(found - set(CYCLES)),
        "named, no longer a cycle": sorted(set(CYCLES) - found),
    }


def test_the_unexamined_are_named_as_work_and_not_as_an_exemption():
    """The number is the finding, as it is in `composing.SITES`: what a reader needs is which
    half they are standing on, and a table where every row read as a decision would hide it."""
    unexamined = [pair for pair, why in CYCLES.items() if why is UNEXAMINED]
    assert unexamined, "if this empties, the row that says so should go too"
    assert len(unexamined) < len(CYCLES), "everything unexamined would mean nothing was looked at"


def test_no_reason_is_left_as_a_placeholder():
    """`withheld`'s rule, three files over: the cheapest way to make the census pass is a row
    with no reason in it, so each states which of the two kinds it is and is long enough to be
    a sentence about this pair rather than about the table."""
    for pair, why in CYCLES.items():
        assert why.startswith(("shape:", "unexamined:")), pair
        assert len(why.split()) >= 12, f"{pair} has no reason in it"
