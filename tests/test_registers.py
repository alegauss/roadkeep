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
