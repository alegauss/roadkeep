"""A command's answer is built in one of three shapes, or it is a carry somebody named (RK1614).

RK1170 moved one verb's two registers onto one result and said what was left behind: most of
the printing never moved. What it could not say is how much, because nothing declared what a
result *is* — so the count was a grep somebody ran once and the shape was whatever the
neighbour a new verb was written beside had chosen.

Counted when this was written: ninety-two `payload` methods in **twenty** signatures, as many
`stated` methods in twenty-one, and thirty-four `__str__` doing `stated`'s job under another
name. :data:`roadkeep.rendering.SHAPES` declares the three that carry seventy of the
ninety-two; the forty-five builders outside them are :data:`CARRIED`, named one row each.

**The list is the deliverable and the shrinking is the point.** A test that asserted the three
shapes and exempted "the ones that are already wrong" as a count would pass while the
forty-sixth is being added; one that names them makes a new one-off a red line and a reviewer's
question — RK1307's argument, which held the same kind of asymmetry by naming its calls. So
:func:`test_a_builder_outside_the_three_shapes_is_one_somebody_named` refuses a shape nobody
declared, and :func:`test_a_carry_that_conforms_is_a_row_to_delete` refuses a stale row, which
is what keeps the list from becoming a permanent exemption as RK1615 empties it.

Not a `Protocol`: `runtime_checkable` sees that a method exists and never what it takes, and
what drifted here is exactly the parameters. The shapes are data and this is the reader.

RK1617 added the second list. :data:`PRINTING` is every handler still answering
`(config, args) -> int` — printing one register and returning a code, so its answer exists
nowhere a second surface can take it. Eighty-seven when the contract landed, and the same rule
governs it: named rather than counted, shrinking rather than exempting, and empty is what
RK1615 means by done — at which point `serving` stops capturing stdout for an answer it was
handed one frame earlier.
"""

from __future__ import annotations

import ast

from surface import modules

from roadkeep.rendering import SHAPES

#: The two names a command's answer publishes itself under. `__str__` is deliberately not one:
#: thirty-four classes spell `stated`'s job that way and folding them in is RK1615's work, not
#: a row this sweep can classify — the shape of `__str__` is fixed by Python.
REGISTERS = ("payload", "stated")

#: Every builder that answers in a shape :data:`~roadkeep.rendering.SHAPES` does not declare,
#: as `(module, class, register)`. Forty-five rows across twenty-four classes, each a parameter
#: that should have been a field: `Weighed` holds `where`, `weights` and `records` and answers
#: either register with no argument, and every row here is a result that did not.
#:
#: A row leaves by the result taking the fact as a field, which is one call site simplified and
#: never an exemption widened. Nothing is added without saying why the fact cannot be a field.
CARRIED: frozenset[tuple[str, str, str]] = frozenset(
    {
        ("adopting.py", "Created", "payload"),
        ("budgeting.py", "Body", "stated"),
        ("budgeting.py", "Denied", "payload"),
        ("budgeting.py", "Denied", "stated"),
        ("budgeting.py", "Noted", "payload"),
        ("budgeting.py", "Noted", "stated"),
        ("budgeting.py", "Session", "payload"),
        ("budgeting.py", "Session", "stated"),
        ("budgeting.py", "Skilled", "payload"),
        ("budgeting.py", "Skilled", "stated"),
        ("capturing.py", "Debt", "stated"),
        ("capturing.py", "Replay", "payload"),
        ("capturing.py", "Replay", "stated"),
        ("counting.py", "Split", "stated"),
        ("governing.py", "Measured", "stated"),
        ("history.py", "Addresses", "payload"),
        ("history.py", "Addresses", "stated"),
        ("history.py", "Cited", "payload"),
        ("history.py", "Cited", "stated"),
        ("ids.py", "Derivation", "payload"),
        ("installing.py", "Plan", "payload"),
        ("installing.py", "Plan", "stated"),
        ("installing.py", "Removal", "payload"),
        ("installing.py", "Removal", "stated"),
        ("installing.py", "Vendored", "stated"),
        ("linting.py", "Report", "payload"),
        ("linting.py", "Report", "stated"),
        ("remedying.py", "Door", "payload"),
        ("remedying.py", "Explained", "payload"),
        ("remedying.py", "Remedy", "payload"),
        ("repairing.py", "Repaired", "payload"),
        ("repairing.py", "Repaired", "stated"),
        ("sections.py", "Found", "payload"),
        ("sections.py", "Rewritten", "payload"),
        ("sections.py", "Rewritten", "stated"),
        ("sections.py", "Section", "payload"),
        ("sections.py", "Shown", "stated"),
        ("serving.py", "Detail", "payload"),
        ("serving.py", "Detail", "stated"),
        ("serving.py", "Surface", "payload"),
        ("serving.py", "Surface", "stated"),
        ("shipping.py", "Corrected", "payload"),
        ("shipping.py", "Corrected", "stated"),
        ("showing.py", "View", "payload"),
        ("showing.py", "View", "stated"),
    }
)


def builders() -> dict[tuple[str, str, str], tuple[str, ...]]:
    """Every `payload` and `stated` in the package, addressed, with what it takes after `self`.

    Off :func:`surface.modules` and never a glob of its own (RK496): a survey that derived the
    package's shape inline is one that kept passing after `verbs/` arrived and stopped covering
    eight files. Parsed rather than imported, for the reason that census gives — importing to
    enumerate finds only what happened to be imported.
    """
    found: dict[tuple[str, str, str], tuple[str, ...]] = {}
    for module in modules():
        for node in ast.walk(ast.parse(module.text)):
            if not isinstance(node, ast.ClassDef):
                continue
            for item in node.body:
                if not isinstance(item, ast.FunctionDef | ast.AsyncFunctionDef):
                    continue
                if item.name not in REGISTERS:
                    continue
                args = item.args
                taken = [one.arg for one in args.posonlyargs + args.args][1:]
                found[module.where, node.name, item.name] = tuple(
                    taken + [one.arg for one in args.kwonlyargs]
                )
    return found


def test_a_builder_outside_the_three_shapes_is_one_somebody_named():
    """The asymmetry and never a count: a forty-sixth one-off is a row, not a tolerance."""
    shapes = set(SHAPES.values())
    strayed = {
        where: taken
        for where, taken in builders().items()
        if taken not in shapes and where not in CARRIED
    }
    assert not strayed, (
        "a builder answers in a shape nothing declares — make the parameters fields on the "
        f"result, or add the row to CARRIED saying why they cannot be: {sorted(strayed)}"
    )


def test_a_carry_that_conforms_is_a_row_to_delete():
    """RK1615 empties this list, and a row it emptied has to leave with it.

    Without this the list is a permanent exemption: a result that took its parameters as fields
    would keep its row, and the next one-off added under the same address would land inside an
    entry nobody re-read. So a row that now conforms — or that names a class this package no
    longer has — is red, and closing it is a deletion.
    """
    found = builders()
    shapes = set(SHAPES.values())
    # Membership before shape, and that order is the whole of it: `found.get(one, ())` reads a
    # row this package no longer has as one answering in the `answer` shape, which is a *row to
    # delete* diagnosed as the wrong reason to delete it. The two states are separate answers.
    settled = sorted(one for one in CARRIED if one in found and found[one] in shapes)
    gone = sorted(one for one in CARRIED if one not in found)
    assert not settled, f"these now answer in a declared shape — delete their rows: {settled}"
    assert not gone, f"these name a builder this package no longer has: {gone}"


def test_the_declared_shapes_are_the_ones_the_package_actually_answers_in():
    """A row nothing uses is a shape somebody imagined, which is the other way this drifts."""
    answered = set(builders().values())
    unused = sorted(name for name, taken in SHAPES.items() if taken not in answered)
    assert not unused, f"SHAPES declares a shape no builder answers in: {unused}"

#: Every handler still answering `(config, args) -> int`: it prints one register and returns a
#: code, so its answer exists nowhere a second surface can take it. Eighty-seven rows when
#: RK1617 landed the contract and migrated the first six, and the list RK1615 empties — at
#: which point `serving` stops capturing stdout and `cli._rendered`'s passthrough branch goes
#: with it.
#:
#: Named and not counted, for :data:`CARRIED`'s reason: a count passes while the next verb is
#: written on the old contract by copying the neighbour it sits beside, which is exactly how
#: twenty signatures happened one module at a time.
PRINTING: frozenset[tuple[str, str]] = frozenset(
    {
        ("verbs/adopting.py", "_init"),
        ("verbs/adopting.py", "_declare"),
        ("verbs/adopting.py", "_adopt"),
        ("verbs/adopting.py", "_engines"),
        ("verbs/adopting.py", "_install"),
        ("verbs/adopting.py", "_capture_filed"),
        ("verbs/adopting.py", "_capture_sweep"),
        ("verbs/adopting.py", "_uninstall"),
        ("verbs/adopting.py", "_report"),
        ("verbs/adopting.py", "_replay"),
        ("verbs/adopting.py", "_mcp"),
        ("verbs/authoring.py", "_next_id"),
        ("verbs/authoring.py", "_add"),
        ("verbs/linting.py", "_merge"),
        ("verbs/linting.py", "_merge_check"),
        ("verbs/linting.py", "_lint"),
        ("verbs/linting.py", "_repair"),
        ("verbs/linting.py", "_explain"),
        ("verbs/linting.py", "_guard"),
        ("verbs/querying.py", "_list"),
        ("verbs/querying.py", "_stats"),
        ("verbs/querying.py", "_audit"),
        ("verbs/querying.py", "_claims"),
        ("verbs/querying.py", "_claim"),
        ("verbs/querying.py", "_writes"),
        ("verbs/querying.py", "_brief"),
        ("verbs/querying.py", "_show"),
        ("verbs/querying.py", "_cost"),
        ("verbs/querying.py", "_budget"),
        ("verbs/querying.py", "_body_budget"),
        ("verbs/querying.py", "_file_budget"),
        ("verbs/querying.py", "_non_goal_budget"),
        ("verbs/querying.py", "_session_budget"),
        ("verbs/querying.py", "_skill_budget"),
        ("verbs/querying.py", "_deny_budget"),
        ("verbs/querying.py", "_notes_budget"),
        ("verbs/querying.py", "_brief_budget"),
        ("verbs/querying.py", "_tools_budget"),
        ("verbs/querying.py", "_pick"),
        ("verbs/querying.py", "_export"),
        ("verbs/querying.py", "_gaps"),
        ("verbs/querying.py", "_govern"),
        ("verbs/querying.py", "_config_shape"),
        ("verbs/querying.py", "_commands"),
        ("verbs/querying.py", "_anchors"),
        ("verbs/querying.py", "_deps"),
        ("verbs/querying.py", "_origin"),
        ("verbs/querying.py", "_cited"),
        ("verbs/querying.py", "_weight"),
        ("verbs/querying.py", "_remaining"),
        ("verbs/querying.py", "_unclosed"),
        ("verbs/querying.py", "_evidence"),
        ("verbs/sections.py", "_block_add"),
        ("verbs/sections.py", "_block_drop"),
        ("verbs/sections.py", "_block_amend"),
        ("verbs/sections.py", "_block_merge"),
        ("verbs/sections.py", "_block_list"),
        ("verbs/sections.py", "_section_add"),
        ("verbs/sections.py", "_refs"),
        ("verbs/sections.py", "_section_amend"),
        ("verbs/sections.py", "_section_move"),
        ("verbs/sections.py", "_section_show"),
        ("verbs/sections.py", "_section_find"),
        ("verbs/sections.py", "_section_drop"),
        ("verbs/sections.py", "_non_goal_add"),
        ("verbs/sections.py", "_non_goal_amend"),
        ("verbs/sections.py", "_non_goal_list"),
        ("verbs/sections.py", "_non_goal_drop"),
        ("verbs/sections.py", "_criterion_add"),
        ("verbs/sections.py", "_criterion_amend"),
        ("verbs/sections.py", "_criterion_drop"),
        ("verbs/sections.py", "_criterion_list"),
        ("verbs/sections.py", "_priority_add"),
        ("verbs/sections.py", "_priority_list"),
        ("verbs/sections.py", "_priority_drop"),
        ("verbs/sections.py", "_priority_migrate"),
        ("verbs/shipping.py", "_ship"),
        ("verbs/shipping.py", "_record"),
        ("verbs/shipping.py", "_record_amend"),
        ("verbs/shipping.py", "_record_move"),
        ("verbs/shipping.py", "_record_renumber"),
        ("verbs/shipping.py", "_record_drop"),
        ("verbs/shipping.py", "_delivered"),
        ("verbs/shipping.py", "_reversals"),
        ("verbs/shipping.py", "_supersede"),
        ("verbs/shipping.py", "_revise"),
        ("verbs/shipping.py", "_retire"),
    }
)


def handlers() -> dict[tuple[str, str], str]:
    """Every verb handler in the package, with what it returns.

    A handler is `(config, args: argparse.Namespace)` and nothing else: `verbs/declaring` has
    two helpers taking `(x, args)` and `verbs/querying` two more taking a config, and a sweep
    keyed on the shape alone counted all four as verbs this contract is about.

    Under `verbs/` and nowhere else, because `cli.dispatch` has a handler's exact signature and
    is the thing that *calls* them — a sweep over the whole package told the dispatcher to
    return its own answer as a value. RK494 put a module per verb family there, so the
    directory is the population rather than a list of files.
    """
    found: dict[tuple[str, str], str] = {}
    for module in modules():
        if not module.where.startswith("verbs/"):
            continue
        for node in ast.walk(ast.parse(module.text)):
            if not isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                continue
            taken = node.args.args
            if len(taken) != 2 or taken[0].arg != "config" or taken[1].arg != "args":
                continue
            if ast.unparse(taken[1].annotation or ast.Constant(None)) != "argparse.Namespace":
                continue
            found[module.where, node.name] = ast.unparse(node.returns) if node.returns else ""
    return found


def test_a_handler_that_prints_its_answer_is_one_somebody_named():
    """A verb written on the old contract by copying its neighbour is a row, not a silence."""
    printing = sorted(
        where for where, returns in handlers().items()
        if returns == "int" and where not in PRINTING
    )
    assert not printing, (
        "a handler answers in a printed register and a code — return `answered(...)` so a "
        f"second surface can take the answer, or add the row to PRINTING: {printing}"
    )


def test_a_migrated_handler_is_a_row_to_delete():
    """The list is RK1615's work-list, so a handler it already moved has to leave it."""
    found = handlers()
    moved = sorted(one for one in PRINTING if found.get(one, "int") != "int")
    gone = sorted(one for one in PRINTING if one not in found)
    assert not moved, f"these no longer print their answer - delete their rows: {moved}"
    assert not gone, f"these name a handler this package no longer has: {gone}"
