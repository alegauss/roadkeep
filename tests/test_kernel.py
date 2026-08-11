"""The kernel boundary, held here and not in a paragraph (RK1065).

`schema.py` and `document.py` are the format's *mechanism* — a record's shape, its identity,
and a file that round-trips. Everything above them is this backlog's *rules*: a dependency
graph, blocks, a queue, a ledger with three doors. The reusable half is the mechanism, and by
import direction the boundary very nearly exists already: 3.6k of the package's 44k lines,
reaching up in exactly one place.

Held by a test for the reason the Layout index is (RK203): a boundary asserted in prose is one
that has already drifted by the time anybody reads the prose. §RK1065 claimed these two modules
*"import nothing but stdlib and each other"*, and measuring it here is what found the two places
that is not true — one deliberate and documented, one a type annotation. Both are named below,
which is the difference between an exception and a leak.

Two rules, and the second is a ceiling rather than a claim. The vocabulary half — that a kernel
should not pronounce task, dep, block or ship — is **not** true today and cannot be asserted
without failing: `Task` and `Dep` are defined here. So it is recorded as a number that may fall
and may not rise, which is what `[budgets]` does to a file nobody can finish shrinking today.
"""

from __future__ import annotations

import ast

from surface import PACKAGE

#: The two modules the mechanism lives in. Named rather than derived: which files are the
#: kernel is the decision this test exists to hold, and a rule that computed its own subject
#: would move every time somebody added a file.
KERNEL = ("schema.py", "document.py")

#: What the kernel may reach for above itself, and why each one is allowed. Empty would be the
#: goal; two entries with reasons is the honest state, and a third arriving without one is what
#: this test is for.
ALLOWED = {
    "roadkeep.exporting": (
        "the projection refresh a transaction owes (RK188), imported inside `_projected` "
        "because the dependency genuinely runs the other way — `exporting` reads documents. "
        "The one real upward call, and the one thing that would have to move first"
    ),
    "roadkeep.config": (
        "a name for an annotation only, under `TYPE_CHECKING`: a document *carries* a project "
        "so a save can re-derive what it stales, and never reads one. No runtime import"
    ),
}

#: The backlog's own words. A kernel that spoke none of these would be a format library; every
#: one it does speak is a rule that has leaked into the mechanism.
VOCABULARY = (
    "task",
    "dep",
    "block",
    "ship",
    "roadmap",
    "ledger",
    "backlog",
    "queue",
    "marker",
    "symptom",
)

#: How many names each kernel module declares out of :data:`VOCABULARY`, measured. A ceiling
#: and not a target: it may fall, and a rise is a rule being written into the mechanism, which
#: is the drift this file exists to catch while it is still one name.
SPOKEN = {"schema.py": 47, "document.py": 17}


def declared(where: str) -> set[str]:
    """Every name this module binds at any level — classes, functions and assignments."""
    tree = ast.parse((PACKAGE / where).read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            names.add(node.name)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
        elif isinstance(node, ast.Assign):
            names.update(t.id for t in node.targets if isinstance(t, ast.Name))
    return names


def reaches(where: str) -> set[str]:
    """Every `roadkeep.*` module this one imports, at module level or inside a function."""
    tree = ast.parse((PACKAGE / where).read_text(encoding="utf-8"))
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and (node.module or "").startswith("roadkeep"):
            found.add(node.module)
        elif isinstance(node, ast.Import):
            found.update(a.name for a in node.names if a.name.startswith("roadkeep"))
    return found


def test_the_kernel_reaches_up_only_where_it_is_allowed_to():
    # The rule, and the whole reason the boundary is worth naming: a mechanism that imports
    # the rules above it is not a mechanism, it is the middle of one package.
    inside = {f"roadkeep.{where.removesuffix('.py')}" for where in KERNEL}
    for where in KERNEL:
        for module in reaches(where) - inside:
            assert module in ALLOWED, (
                f"{where} reaches {module}, which is above it and has no entry in ALLOWED: "
                f"add the reason, or move the call"
            )


def test_every_allowance_is_still_taken():
    # The other direction, and the one a green test loses without: an exception nobody uses is
    # a permission left standing over code that stopped needing it.
    taken = {module for where in KERNEL for module in reaches(where)}
    for module in ALLOWED:
        assert module in taken, f"{module} is allowed and reached by neither kernel module"


def test_the_backlog_vocabulary_in_the_kernel_does_not_grow():
    # The half that is not true yet and so is a ceiling rather than an assertion. `Task` and
    # `Dep` are defined in `schema.py`; the rule is that the number comes down, and a rise is
    # a rule being written into the mechanism while it is still one name to move.
    for where, ceiling in SPOKEN.items():
        names = declared(where)
        speaking = {
            name for name in names if any(word in name.lower() for word in VOCABULARY)
        }
        assert len(speaking) <= ceiling, (
            f"{where} now declares {len(speaking)} names from the backlog's vocabulary "
            f"against a recorded {ceiling}: {sorted(speaking)}"
        )


def test_the_kernel_is_the_share_of_the_package_this_task_measured():
    # The figure §RK1065 argued from, kept where it can be re-read rather than in a sentence
    # that was true once: a boundary worth drawing is one whose size somebody can check.
    counted = {
        where: len((PACKAGE / where).read_text(encoding="utf-8").splitlines())
        for where in KERNEL
    }
    assert 3000 < sum(counted.values()) < 4500, counted
