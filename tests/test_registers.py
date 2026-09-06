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

RK1617 added the second list and RK1615 emptied it down to nine. :data:`PRINTING` is every
handler still answering `(config, args) -> int`, and what is left in it is not work nobody got
to — each has a prior reason, and none of the nine is served.

That last clause is the invariant, and
:func:`test_no_tool_this_project_serves_answers_in_an_exit_code` is what holds it. "Empty" was
the wrong target: `guard` has no plain register at all — three harness protocols keyed by hook
event, not readings of one result — and `merge`'s driver branches are bytes in git's `%A` and an
exit code, which is the contract this tool is called under rather than an answer it composes.
Forcing either into a `Result` would be inventing a register to satisfy a count. What the
transport actually needs is that **no answer it asks for is one it has to read off a stream**,
which nine unserved handlers do not threaten and a tenth served one would.
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
        # `adopt`, `install`, `uninstall` and `mcp` are the once-per-project wiring verbs, and
        # `report`, `replay` and `capture sweep` have this tool as their subject. None is
        # served, and each writes a multi-part report a transport never asks for.
        ("verbs/adopting.py", "_adopt"),
        ("verbs/adopting.py", "_install"),
        ("verbs/adopting.py", "_capture_sweep"),
        ("verbs/adopting.py", "_uninstall"),
        ("verbs/adopting.py", "_report"),
        ("verbs/adopting.py", "_replay"),
        ("verbs/adopting.py", "_mcp"),
        # The one with no plain register at all: three harness protocols keyed by hook event,
        # which are contracts rather than readings of one result. Its own docstring says so.
        ("verbs/linting.py", "_guard"),
        # `--spec` writes markdown with no trailing newline, for a caller that pipes it — and a
        # `Result` is printed with one. The rest of the verb writes files and reports the lines.
        ("verbs/querying.py", "_export"),
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


def test_no_tool_this_project_serves_answers_in_an_exit_code():
    """What RK1615 actually bought, and the reason "PRINTING empty" was the wrong target.

    The transport takes `Result.fields` now instead of capturing the stdout a handler printed
    for a terminal. That holds exactly while every **served** verb answers with a value: one
    that did not would send the transport back to reading its own output, and the nine rows in
    :data:`PRINTING` are safe only because none of them is reachable over MCP.

    Derived at both ends rather than listed. The tools come off `serving.TOOLS`, the handler off
    the parser's own `handler` default — which is how `serving` resolves it — so a verb newly
    served, or a served verb whose handler is rewritten to print, is red here on the day it
    happens rather than on the day somebody notices the payload went back to prose.
    """
    from roadkeep.cli import build_parser  # noqa: PLC0415 - imported for the parser it builds
    from roadkeep.serving import TOOLS, _parsers, _subparser

    parsers = _parsers(build_parser())
    printing = sorted(
        (tool.name, handler.__name__)
        for tool in TOOLS
        if (handler := _subparser(tool.command, parsers).get_default("handler")) is not None
        and (handler.__module__.rpartition(".")[2] + ".py", handler.__name__)
        in {(where.rpartition("/")[2], name) for where, name in PRINTING}
    )
    assert not printing, (
        "a served tool's handler answers in an exit code, so the transport is back to reading "
        f"what it printed — return `Result` from it: {printing}"
    )


def test_a_migrated_handler_is_a_row_to_delete():
    """The list is RK1615's work-list, so a handler it already moved has to leave it."""
    found = handlers()
    moved = sorted(one for one in PRINTING if found.get(one, "int") != "int")
    gone = sorted(one for one in PRINTING if one not in found)
    assert not moved, f"these no longer print their answer - delete their rows: {moved}"
    assert not gone, f"these name a handler this package no longer has: {gone}"
