"""A test about one rule may not assert over every rule the gate has (RK1448).

RK1440 gave the gate one more **note** — a wired project whose engine is a modified checkout
— and nineteen tests went red in one run. None of them was about engines. Six read
`(note,) = report.notes` or `report.notes == ()` while meaning *exactly one `deps.collective`
note*, one read `report.notes[0]`, and the rest were the same shape one file over.

The assertion is wrong in both directions. It fails on a note the test does not care about,
which is what happened; and it passes while a note it *should* have seen is absent, because a
list of one is a list of one whatever is in it. Neither failure names the rule under test, so
the repair is mechanical and the reader learns nothing. It also made the suite's verdict
depend on whether the checkout running it happened to be dirty.

**Notes and not findings**, which is the whole distinction. A finding moves the exit code: a
clean fixture that grows one is a regression, so `assert not lint(config).findings` is a claim
somebody meant. A note is advisory, does not move the verdict, and the set of them grows —
so the same sentence about notes is a claim about every advisory rule this tool will ever add.

What is refused is the **whole list used as a value**: unpacked, subscripted or compared.
Binding it to a name and filtering that name twice is the right shape and stays legal, which
is why this follows the binding rather than banning the attribute.
"""

from __future__ import annotations

import ast
from pathlib import Path

from surface import suite

HERE = Path(__file__).resolve().parent

#: Reads of a `notes` attribute that are not a gate report's, with the reason. Declared rather
#: than guessed at: this sweep is over a name, and duck typing means two objects may answer to
#: it — an exemption nobody can see reads exactly like a rule being kept.
NOT_A_REPORT = {
    "test_blocking.py": "`Removal.notes` is a mapping of role to line count, not a gate report",
}


def _bound(body: ast.AST) -> set[str]:
    """Names a function binds to a bare `.notes`, so the sweep follows one step of dataflow.

    `said = lint(config).notes` and then two filters over `said` is the shape a test *should*
    have, and a rule that stopped at the attribute would refuse it.
    """
    found = set()
    for node in ast.walk(body):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and _is_notes(node.value):
            found.add(target.id)
    return found


def _is_notes(node: ast.AST) -> bool:
    """A gate report's notes, however this file spells the read: attribute or payload key."""
    if isinstance(node, ast.Attribute) and node.attr == "notes":
        return True
    return (
        isinstance(node, ast.Subscript)
        and isinstance(node.slice, ast.Constant)
        and node.slice.value == "notes"
    )


def _whole(function: ast.AST, bound: set[str]) -> list[int]:
    """Line numbers where the list is used as a value rather than filtered."""
    over: list[int] = []

    def names_it(node: ast.AST) -> bool:
        return _is_notes(node) or (isinstance(node, ast.Name) and node.id in bound)

    for node in ast.walk(function):
        # Unpacked: `(note,) = report.notes`, which claims the gate said exactly this one.
        if isinstance(node, ast.Assign) and names_it(node.value):
            if any(isinstance(one, (ast.Tuple, ast.List)) for one in node.targets):
                over.append(node.lineno)
        # Compared: `report.notes == ()`, the same claim spelled as equality.
        elif isinstance(node, ast.Compare) and (
            names_it(node.left) or any(names_it(one) for one in node.comparators)
        ):
            over.append(node.lineno)
        # Indexed: `report.notes[0]`, which is the first of a list nobody ordered.
        elif isinstance(node, ast.Subscript) and names_it(node.value):
            over.append(node.lineno)
    return over


def test_no_test_asserts_over_the_whole_list_of_notes():
    """The sweep that would have caught all seven the first time, and costs nothing on the
    ones that filter. Over `surface.suite`, which is where the set of test modules is
    declared: a sweep deriving its own view of the directory is RK496's failure one directory
    across, and this is the second sweep that wanted it."""
    guilty: dict[str, list[int]] = {}
    for path in suite():
        if path.name == Path(__file__).name:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            at = _whole(node, _bound(node))
            if at and path.name not in NOT_A_REPORT:
                guilty.setdefault(path.name, []).extend(at)
    assert not guilty, (
        f"these assert over every note the gate has, not the one they are about: {guilty}"
    )


def test_every_exemption_names_a_file_that_is_still_here():
    """A row for a file that moved is a reason nobody will read, and it leaves the rule
    looking stricter than it is."""
    for name, because in NOT_A_REPORT.items():
        assert (HERE / name).is_file(), name
        assert because.strip(), name
