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

**And the exemption is a receiver, not a file** (RK1653). Five classes answer to this name and
one of them is a gate report, so RK1603 and RK1611 each added a module to a list — three rows,
each turning the rule off for every assertion in that file, and `test_installing` alone reads a
gate report thirty times. :data:`RECEIVERS` is that list re-keyed by *which object* the read is
of, held total against the suite: a receiver nobody classified is a red with one question in it
rather than a silence. Two of the six reads it removed were not lists at all — `remedying.
notes()` and `describing.notes()` are functions, and an attribute being **called** is now told
apart from one being read.
"""

from __future__ import annotations

import ast
from pathlib import Path

from surface import suite

HERE = Path(__file__).resolve().parent

#: What a row says when the receiver **is** a gate report, and so the rule applies to it.
#: A sentinel rather than a second table, because the population is one and the two answers
#: are what a reader is looking for on the same row.
REPORT = "a gate report"

#: Every `notes` read in the suite, by the receiver it is a read *of* — `(module, the head
#: symbol of the receiver)` — and either :data:`REPORT` or the reason it is not one.
#:
#: **Keyed by the receiver and no longer by the file** (RK1653). Duck typing means several
#: objects answer to this name, and the exemption for one of them was a whole module: three
#: rows, and no assertion anywhere in `test_blocking`, `test_describing` or `test_installing`
#: was swept — where `test_installing` alone reads a gate report thirty times. The rule is
#: about a name reached from a `Report`, and a file was never the shape of that.
#:
#: Held **total** against the suite below, which is what the narrowing costs and buys: a
#: receiver nobody classified is a red here with one question in it, where a file-keyed
#: exemption turned the rule off for everything else in the file that answered it.
#:
#: Two modules spell one local name for two things — `found` is a `cost --notes` payload in
#: `test_budgeting` and a `describing.Shape` in `test_describing` — which is why the key is a
#: pair and not the symbol alone.
RECEIVERS: dict[tuple[str, str], str] = {
    ("test_baseline.py", "lint"): REPORT,
    ("test_baseline.py", "report"): REPORT,
    # `blocking.Closed.notes` is a mapping of role to line count, not a gate report.
    ("test_blocking.py", "closed"): "a mapping of role to the lines a close removed",
    # `cost --notes` prices what a clean gate says beside its verdict, so its payload carries
    # the notes as **rows of a measurement** — the population, not this run's findings.
    ("test_budgeting.py", "found"): "the `cost --notes` payload, whose notes are priced rows",
    ("test_budgeting.py", "lint"): REPORT,
    ("test_budgeting.py", "report"): REPORT,
    ("test_composing.py", "lint"): REPORT,
    # RK1603 moved the harvested sentence off every key row of `config --json` and onto a
    # mapping of table to sentence. `config` reports no findings at all.
    ("test_describing.py", "found"): "a `describing.Shape`, mapping a table to its sentence",
    ("test_installing.py", "_linted"): REPORT,
    # RK1611's, and the third object to answer to this name: what a withdrawal does to
    # something the un-wiring keeps. Two receivers, one per spelling the module uses.
    ("test_installing.py", "intent"): "an `installing.Removal`, bound before it is read",
    ("test_installing.py", "removal"): "an `installing.Removal` read straight off the call",
    ("test_installing.py", "lint"): REPORT,
    ("test_installing.py", "report"): REPORT,
    ("test_linting.py", "lint"): REPORT,
    ("test_linting.py", "linting"): REPORT,
    ("test_linting.py", "payload"): REPORT,
    ("test_linting.py", "report"): REPORT,
    ("test_queueing.py", "report"): REPORT,
    ("test_remedying.py", "lint"): REPORT,
    ("test_scoping.py", "lint"): REPORT,
    ("test_scoping.py", "report"): REPORT,
    # The same report one register over: `lint --json` parsed back out of stdout.
    ("test_turning.py", "json"): REPORT,
    ("test_turning.py", "report"): REPORT,
    ("test_unpaired.py", "payload"): REPORT,
    ("test_unpaired.py", "report"): REPORT,
}


def _bound(body: ast.AST, path: Path) -> set[str]:
    """Names a function binds to a **report's** notes, following one step of dataflow.

    `said = lint(config).notes` and then two filters over `said` is the shape a test *should*
    have, and a rule that stopped at the attribute would refuse it.

    A read of something else that answers to the name binds nothing here (RK1653): `said =
    found.notes` in `test_describing` is a mapping, and following it would carry the rule onto
    every later use of a local variable the rule is not about.
    """
    found = set()
    for node in ast.walk(body):
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if isinstance(target, ast.Name) and _is_notes(node.value) and _reports(path, node.value):
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


def _receiver(node: ast.AST) -> str:
    """The head symbol of what this read is a read **of** — `lint(config).notes` is `lint`.

    Structural and not a spelling (RK1653): a receiver keyed by its source text would be a new
    row for every fixture a call happens to take, and what the rule is about is *which object*
    answers to the name. Walked down through calls, attributes and subscripts to the name at
    the bottom, which is the one part a reader recognises.
    """
    head = getattr(node, "value", node)
    while isinstance(head, (ast.Call, ast.Attribute, ast.Subscript)):
        head = head.func if isinstance(head, ast.Call) else head.value
    return head.id if isinstance(head, ast.Name) else ast.unparse(head)


def _read(tree: ast.AST) -> list[ast.AST]:
    """Every `notes` read in this module — and never the function of the same name (RK1653).

    `remedying.notes()` and `describing.notes()` are *functions* returning a population, and
    the sweep read each as a list it was about: six reads across two modules, one of which was
    a whole module's exemption on its own. An attribute being **called** is not a list, which
    is the one structural fact that tells them apart.
    """
    called = {id(node.func) for node in ast.walk(tree) if isinstance(node, ast.Call)}
    return [
        node for node in ast.walk(tree) if _is_notes(node) and id(node) not in called
    ]


def _whole(function: ast.AST, bound: set[str], path: Path) -> list[int]:
    """Line numbers where a **report's** list is used as a value rather than filtered.

    ``path`` decides which reads are a report's, per receiver (RK1653): the same name reaches
    a mapping in three modules, and the rule is about the object rather than about the word.
    """
    over: list[int] = []

    def names_it(node: ast.AST) -> bool:
        if isinstance(node, ast.Name):
            return node.id in bound
        return _is_notes(node) and _reports(path, node)

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


def _reports(path: Path, node: ast.AST) -> bool:
    """Whether this read is a read of a gate report, off :data:`RECEIVERS`."""
    return RECEIVERS.get((path.name, _receiver(node))) == REPORT


def test_no_test_asserts_over_the_whole_list_of_notes():
    """The sweep that would have caught all seven the first time, and costs nothing on the
    ones that filter. Over `surface.suite`, which is where the set of test modules is
    declared: a sweep deriving its own view of the directory is RK496's failure one directory
    across, and this is the second sweep that wanted it.

    Per **receiver** since RK1653, so a module reading a report and something else that
    answers to the same name is swept for the first and exempt for the second — which is three
    modules, one of them the heaviest reader of gate reports in the suite."""
    guilty: dict[str, list[int]] = {}
    for path in suite():
        if path.name == Path(__file__).name:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            bound = _bound(node, path)
            for at in _whole(node, bound, path):
                guilty.setdefault(path.name, []).append(at)
    assert not guilty, (
        f"these assert over every note the gate has, not the one they are about: {guilty}"
    )


def test_every_notes_read_in_the_suite_is_classified():
    """The total the narrowing rests on. A receiver nobody classified is a read this sweep
    cannot decide about, and the answer it would give — *not a report, so exempt* — is the
    silence a file-keyed exemption already was.

    Both directions: a row naming a receiver the suite no longer spells is a reason nobody
    will read, and it leaves the rule looking stricter than it is."""
    found = {
        (path.name, _receiver(node))
        for path in suite()
        if path.name != Path(__file__).name
        for node in _read(ast.parse(path.read_text(encoding="utf-8")))
    }
    assert found == set(RECEIVERS), {
        "read and unclassified": sorted(found - set(RECEIVERS)),
        "classified and not read": sorted(set(RECEIVERS) - found),
    }
    for (name, _symbol), because in RECEIVERS.items():
        assert (HERE / name).is_file(), name
        assert because.strip(), name
    # And the majority are reports, which the shape alone would not say: a register where
    # every row is an exemption passes the total above and sweeps nothing.
    swept = [one for one in RECEIVERS.values() if one == REPORT]
    assert len(swept) > len(RECEIVERS) / 2, RECEIVERS


def test_the_function_of_the_same_name_is_not_a_list_of_notes():
    """RK1653's other half, and the cheaper one: `remedying.notes()` returns the population of
    notes this build can say, and `describing.notes()` the sentences a config's source carries.
    Both are calls, both were read as lists, and one of them was a module's whole exemption."""
    tree = ast.parse("said = remedying.notes()\nother = report.notes\n")
    assert [_receiver(one) for one in _read(tree)] == ["report"]
