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
import re

from surface import address, PACKAGE, modules

#: The two modules the mechanism lives in. Named rather than derived: which files are the
#: kernel is the decision this test exists to hold, and a rule that computed its own subject
#: would move every time somebody added a file.
KERNEL = (address("schema"), address("document"))

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
#:
#: **Re-measured for RK1072, and four lower.** The first count matched a vocabulary word
#: anywhere in an identifier, so `codepoint` contained `dep` and `_named_codepoint`,
#: `codepoint_kind`, `_codepoints` and `CODEPOINT_KINDS` were counted as this backlog's
#: words. A ceiling that counts the wrong things is one nobody can bring down on purpose —
#: the same defect this project files about every other number it publishes.
SPOKEN = {address("schema"): 43, address("document"): 17}

#: How many of them anything **above** the kernel refers to. The split RK1072 was filed to
#: find, and the answer it did not expect: two thirds are the kernel's public surface —
#: `Task`, `Dep`, `block`, `marker`, `symptom` and the fields that spell them — which are
#: the mechanism's own words for a record and a reference, sharing vocabulary with the
#: backlog rather than belonging to it. What is left is private, and moves only if its whole
#: role does. So the count falls by renaming, which RK1072's own design rules out, or by
#: moving a rule whose reason for being where it is survives the reading (see `_ledger_slots`,
#: which states an adoption remedy in the one place a reader of that file is looking).
PUBLIC = 41


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
    inside = {f"roadkeep.{where.removesuffix('.py').replace('/', '.')}" for where in KERNEL}
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


def speaks(name: str) -> bool:
    """Whether an identifier pronounces one of the backlog's words (RK1072).

    Token by token and never as a substring: `codepoint` contains `dep`, and the first
    version of this counted four codepoint helpers as dependency vocabulary. A prefix match
    on the token, so `deps`, `markers` and `shipped` count and `codepoint` does not —
    English is what the plural and the participle are, and a stemmer would be a dependency
    to answer a question a `startswith` answers.
    """
    tokens = re.findall(r"[A-Z]+(?![a-z])|[A-Z][a-z]*|[a-z]+|[0-9]+", name)
    return any(t.lower().startswith(word) for t in tokens for word in VOCABULARY)


def spoken(where: str) -> set[str]:
    return {name for name in declared(where) if speaks(name)}


def test_the_backlog_vocabulary_in_the_kernel_does_not_grow():
    # The half that is not true yet and so is a ceiling rather than an assertion. `Task` and
    # `Dep` are defined in `schema.py`; the rule is that the number comes down, and a rise is
    # a rule being written into the mechanism while it is still one name to move.
    for where, ceiling in SPOKEN.items():
        speaking = spoken(where)
        assert len(speaking) <= ceiling, (
            f"{where} now declares {len(speaking)} names from the backlog's vocabulary "
            f"against a recorded {ceiling}: {sorted(speaking)}"
        )


def test_most_of_what_the_kernel_speaks_is_its_own_public_surface():
    # RK1072's finding, kept as a reading rather than a sentence: the count is dominated by
    # the names everything above reaches for, which are the mechanism's words for a record
    # and a reference. A drop that came from hiding one of those would be the meter moving
    # and nothing else, so the split is measured beside the total.
    every = {name for where in SPOKEN for name in spoken(where)}
    above = "\n".join(
        module.text for module in modules() if module.where not in SPOKEN
    )
    public = {name for name in every if re.search(rf"\b{re.escape(name)}\b", above)}
    assert len(public) <= PUBLIC, sorted(public)
    # Two thirds, which is the number that says renaming is the only large lever left.
    assert len(public) * 2 > len(every)


def test_the_kernel_is_the_share_of_the_package_this_task_measured():
    # The figure §RK1065 argued from, kept where it can be re-read rather than in a sentence
    # that was true once: a boundary worth drawing is one whose size somebody can check.
    counted = {
        where: len((PACKAGE / where).read_text(encoding="utf-8").splitlines())
        for where in KERNEL
    }
    assert 3000 < sum(counted.values()) < 4500, counted
