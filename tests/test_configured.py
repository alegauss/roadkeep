"""L6, as a property: nothing a project configures is written into the package (RK1000).

Prefix, paths, markers and limits are read from `roadkeep.toml`, and a literal standing in
for one of them is a rule that holds here — where this repository's own numbers happen to
match what was hardcoded — and fails in Shio, in Turing, or in a fork whose prefix is three
letters. It fails as behaviour nobody can derive from the config they wrote, which is the
worst shape a defect takes: correct on the maintainer's machine, wrong on everyone else's.

RK491 recorded L6 as **reachable and unreached** — the one of the three unheld laws that a
source scan decides, unheld because nobody had written the scan rather than because no set
exists. This is that scan. `config.py` and `schema.py` are where a default is written down,
so they are the two modules it does not read: a scan that cannot tell a default from a leak
is a red nobody keeps.

What the first run found, in a package of 51 modules: `capturing` spelled `RK1` as the
placeholder it validates a reported claim against, and two messages — one in `guarding`, one
in `remedying`'s cause table — wrote `(deps: … ✅)` with the shipped marker in it, which is
`[markers]`' to declare.

**Two things it deliberately does not scan, both measured before being dropped.**

*Numbers.* Every integer default of :class:`~roadkeep.kernel.schema.Schema` was swept across the
package and the three hits were `_MOST_OUTPUT_LINES = 40`, a roman-numeral table's `("XL",
40)` and `MAX_PASSES = 200` — three coincidences and no leaks. A limit is a bare integer and
a bare integer is the most common literal in any program, so the scan cannot separate them
and would report noise for ever.

*The words a caller is shown.* `help`, `description` and `metavar` are full of `e.g. RK7`
and `e.g. docs/ROADMAP.md`, and none of it is derivable: :func:`~roadkeep.cli.build_parser`
is built without a config, so an example in a help string has no project to read. Scanning
them would produce an allow-list of forty strings, which is the same red nobody keeps.
"""

from __future__ import annotations

import ast
import re

from surface import modules

from roadkeep.kernel.schema import (
    DEFERRED,
    IDEA,
    IN_PROGRESS,
    PARTIAL,
    RETIRED,
    SHIPPED,
    DESIGNED,
    Schema,
)

#: Where a default is written down, and therefore the two modules a leak cannot be in.
#: `config` reads `roadkeep.toml` and `schema` is the dataclass whose field defaults are what
#: it falls back to — spelling a marker or a prefix in either is the declaration itself.
DECLARES = frozenset({"config.py", "kernel/schema.py"})

#: The keyword arguments whose value is shown to a caller rather than used as one. Skipped
#: with the reason this module's docstring gives: nothing in a help string can be derived,
#: because the parser that carries it is built before any project is known.
SHOWN = frozenset({"help", "description", "metavar", "epilog", "title"})

MARKERS = (DESIGNED, IDEA, PARTIAL, IN_PROGRESS, SHIPPED, RETIRED, DEFERRED)
#: An id as this project spells one — the **whole** literal and never a substring, which is
#: the distinction that makes the check keep its meaning: a sentence citing `RK325` is a
#: reference to this repository's own history, and a literal that *is* `RK1` is a value.
IS_AN_ID = re.compile(r"^[A-Z]{1,4}\d+$")
#: A governed file under its default name. The role is `[files]`' to declare, so a module
#: naming one has decided where somebody else's backlog lives.
IS_A_GOVERNED_FILE = re.compile(r"\b(ROADMAP|CHANGELOG|IMPROVEMENTS|STRATEGY)\.md\b")


def _values(source: str) -> list[tuple[int, str]]:
    """Every string constant a module *uses*, with its line — prose excluded.

    Two exclusions and each is the same argument RK488's own sweep makes: a docstring is
    written for a reader of this source, so a comment recording what a defect was is not the
    defect; and a help string is written for a caller of the CLI, where nothing is derivable.
    Read from the AST rather than the text, because a grep cannot tell those apart.
    """
    tree = ast.parse(source)
    skip = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
        and ast.get_docstring(node) is not None
    }
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg in SHOWN:
                skip |= {id(inner) for inner in ast.walk(keyword.value)}
    return [
        (node.lineno, node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in skip
    ]


def _leaks(surface, matches) -> dict[str, list[str]]:
    """Which modules of ``surface`` carry a literal ``matches`` recognises, by line.

    The surface is an argument and not a reach, so each property below names what it sweeps
    — which is what `tests/test_invariants.py` reads off a holder to check that its row still
    describes the property it claims (RK491).
    """
    found: dict[str, list[str]] = {}
    for module in surface:
        if module.where in DECLARES:
            continue
        for lineno, text in _values(module.text):
            if matches(text):
                found.setdefault(module.where, []).append(f"{lineno}: {text[:60]!r}")
    return found


def test_no_module_writes_a_marker_a_project_declares():
    """`[markers]` is per-project, so a package literal carrying one is a message that names
    a codepoint the reader's own files do not use. Two of these were live: a refusal and a
    remedy's cause both wrote `(deps: … ✅)` where the marker is the project's to declare."""
    assert _leaks(modules(), lambda text: any(m in text for m in MARKERS)) == {}


#: The names those markers are imported under. The **other** route to the same message
#: (RK1520): `f"status {task_id} {IN_PROGRESS}"` renders the six bytes the scan above refuses
#: and is invisible to it — so the repair that gate rewards is the one a developer reaches for
#: *because* the gate is there, and the reader is told about a glyph their project may not use.
MARKER_NAMES = frozenset(
    {"DESIGNED", "IDEA", "PARTIAL", "IN_PROGRESS", "SHIPPED", "RETIRED", "DEFERRED"}
)

#: How this tool delimits a composed command, everywhere: `sections.quotes` reads it, the
#: census in `tests/composing.py` finds a command by it, and a message that carries one is
#: offering the reader something to run.
SPAN = "`"


def _composed_markers(source: str) -> list[str]:
    """Every f-string that composes a command and interpolates a marker constant (RK1520).

    **A stated shape and never a rule about interpolation**, which is the distinction the
    scan above cannot make on its own: a report of what a write just did may name the marker
    it moved — that fact came off the file and is the reader's own — while a *command* built
    round one is offering a write the reader's schema would refuse.

    So the shape is the backtick. A span in backticks is how every composed command in this
    package is delimited, and a marker constant inside one is this package deciding what a
    project's vocabulary is. A marker read from the config arrives as a parameter or an
    attribute, and neither is a name in this set.
    """
    found = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.JoinedStr):
            continue
        literal = "".join(
            one.value
            for one in node.values
            if isinstance(one, ast.Constant) and isinstance(one.value, str)
        )
        if SPAN not in literal:
            continue
        named = {
            inner.id
            for one in node.values
            if isinstance(one, ast.FormattedValue)
            for inner in ast.walk(one.value)
            if isinstance(inner, ast.Name) and inner.id in MARKER_NAMES
        }
        found += [f"{node.lineno}: {name}" for name in sorted(named)]
    return found


def test_no_composed_command_carries_a_marker_this_package_spells():
    """RK1520. The gate above scans for the codepoint, and interpolating the constant renders
    the same bytes and walks past it — both of this package's remaining sites were that shape,
    and one was a refusal telling a caller how to take a line.

    Held over the same surface and for the same reason, one route further along: what the rule
    is about is a message naming a marker the reader's project may not declare, and the literal
    was only the first way to write one."""
    found = {
        module.where: leaked
        for module in modules()
        if module.where not in DECLARES and (leaked := _composed_markers(module.text))
    }
    assert found == {}, (
        "a composed command built round a package marker offers the reader a write their "
        "own schema refuses: read the marker off the config and pass it in"
    )


def test_the_two_routes_to_one_message_are_both_shut():
    """The gate's own claim, exhibited: the literal and the constant render the same six bytes,
    so a check that catches one and not the other is a check the repair walks past."""
    spelled = f'x = "`status RK1 {IN_PROGRESS}`"'
    composed = 'x = f"`status {one} {IN_PROGRESS}`"'
    # One message, two sources. The first scan reads the codepoint and sees only the first.
    assert any(one in spelled for one in MARKERS)
    assert not any(one in composed for one in MARKERS)
    assert _composed_markers(composed) == ["1: IN_PROGRESS"]
    # And the reading that stays legitimate: a report of what a write did is not a command,
    # so it carries no backtick and this says nothing about it.
    assert _composed_markers('x = f"moved to {IN_PROGRESS}"') == []


def test_no_module_writes_an_id_in_this_project_s_shape():
    """The prefix and the padding are `[ids]`', so a literal that *is* an id is a value from
    a project the package cannot have read. `capturing` held one: the placeholder a reported
    claim is validated against, spelled `RK1` beside the schema that could spell it."""
    assert _leaks(modules(), lambda text: bool(IS_AN_ID.match(text))) == {}


def test_no_module_names_a_governed_file_by_its_default_name():
    """`[files]` says where a backlog lives, and a module that spells one has answered for
    somebody else's repository. Green on the first run, and held so it stays that way."""
    assert _leaks(modules(), lambda text: bool(IS_A_GOVERNED_FILE.search(text))) == {}


def test_the_two_modules_that_may_declare_a_default_are_the_two_that_do():
    """The exemption is the scan's whole risk, so it is asserted rather than trusted: these
    two carry the defaults, and a third name appearing here would be a module that declared
    what it should have read."""
    assert {module.where for module in modules()} >= DECLARES
    schema = Schema()
    assert schema.prefixes and schema.markers, "the defaults moved out of `schema`"
