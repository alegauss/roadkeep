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

**The exemption ends at a backtick** (RK1558). It was written for an *example* — `e.g. RK7`
illustrates the shape of an argument and claims nothing about the reader's vocabulary — and
a backticked span is not one: it is a command this package is telling somebody to run, and a
marker inside it offers a write their own schema refuses. That distinction is why the scan
below takes no exemption at all, and this was the only place saying so: the two readings
differed, one of them silently.

Measured before the rule was stated, so it is the code's own and not an opinion imposed on
it: of **192** backticked spans inside the words this parser shows a caller, not one carries
a marker, an id or a governed file's name. What help strings do carry is `add`, `pick`,
`git add --` — the verb, with the values left as placeholders — which is the rule already,
held by nothing.
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
#:
#: Skipped as an **example** and never as a command (RK1558): the backticked spans inside
#: these are held by :func:`test_no_command_a_help_string_offers_carries_a_project_value`,
#: which is where this exemption ends.
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


#: Every way this package spells a marker constant's **name**: imported, and reached through
#: its module. Both are ordinary style here — a module using one marker once reaches for the
#: second — and a gate that read one of them would be the defect RK1520 is about, one
#: dereference along (RK1557). Asserted as a pair below, so a third arrives as a red.
SPELLINGS = ("Name.id", "Attribute.attr")


def _named_marker(node: ast.AST) -> str:
    """The marker constant this node names, under either spelling, or `""`."""
    if isinstance(node, ast.Name) and node.id in MARKER_NAMES:
        return node.id
    if isinstance(node, ast.Attribute) and node.attr in MARKER_NAMES:
        return node.attr
    return ""


def _composed_markers(source: str) -> list[str]:
    """Every f-string that composes a command and interpolates a marker constant (RK1520).

    **A stated shape and never a rule about interpolation**, which is the distinction the
    scan above cannot make on its own: a report of what a write just did may name the marker
    it moved — that fact came off the file and is the reader's own — while a *command* built
    round one is offering a write the reader's schema would refuse.

    So the shape is the backtick. A span in backticks is how every composed command in this
    package is delimited, and a marker constant inside one is this package deciding what a
    project's vocabulary is. A marker read from the config arrives as a parameter or as
    `config.schema.<field>`, and neither is one of these names.

    **Every spelling of the name, and not the bare one** (RK1557). A constant is reached here
    two ways — imported (`IN_PROGRESS`) and through its module (`schema.IN_PROGRESS`) — and a
    scan that read only the first would be this gate walking past the same defect it was
    written to catch, one dereference along. :data:`SPELLINGS` is that pair, asserted as a
    pair, so a third way of naming one arrives as a red rather than as a silence.

    **And no exemption for the words a caller is shown** (RK1558), where :func:`_values` has
    one. Deliberate, and it follows from the shape above rather than contradicting that
    exemption: what a help string may do is *illustrate* a value, and what it may not do is
    build a command round one — so the backtick is already the line, and it falls in the same
    place here. `test_no_command_a_help_string_offers_carries_a_project_value` holds the other
    side of it, for the literal this scan does not read.
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
            _named_marker(inner)
            for one in node.values
            if isinstance(one, ast.FormattedValue)
            for inner in ast.walk(one.value)
            if _named_marker(inner)
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


def test_both_spellings_of_a_constant_are_one_defect(tmp_path):
    """RK1557. The first cut of this gate read an `ast.Name`, so the same constant reached
    through its module walked past — the defect it was written to catch, one dereference along.

    Held as a **pair** and never as one example each: what the rule is about is a marker
    constant being *named*, and Python has these two ways to name one. A third would arrive
    here as a red, which is what keeps the sweep's population honest."""
    assert set(SPELLINGS) == {"Name.id", "Attribute.attr"}
    imported = 'x = f"`status {one} {IN_PROGRESS}`"'
    dereferenced = 'x = f"`status {one} {schema.IN_PROGRESS}`"'
    assert _composed_markers(imported) == ["1: IN_PROGRESS"]
    assert _composed_markers(dereferenced) == ["1: IN_PROGRESS"]
    # And the exemption survives the widening: an attribute is not a command either.
    assert _composed_markers('x = f"moved to {schema.IN_PROGRESS}"') == []


# -- where the exemption for a shown word ends (RK1558) -----------------------

#: One backticked span. The same delimiter :data:`SPAN` names and the census in
#: `tests/composing.py` finds a command by — read here as a pattern rather than as a
#: character, because what this scan wants is the text *between* two of them.
SPANS = re.compile(r"`([^`]+)`")


def _shown(source: str) -> list[tuple[int, str]]:
    """Every string a parser shows a caller, with its line — exactly what :func:`_values` skips.

    The complement of that function's exemption, so the two cannot drift apart: one reads
    every string a module uses and drops these, this one reads these and nothing else.
    """
    out = []
    for node in ast.walk(ast.parse(source)):
        if not isinstance(node, ast.Call):
            continue
        for keyword in node.keywords:
            if keyword.arg not in SHOWN:
                continue
            out += [
                (inner.lineno, inner.value)
                for inner in ast.walk(keyword.value)
                if isinstance(inner, ast.Constant) and isinstance(inner.value, str)
            ]
    return out


def _offered(text: str) -> str:
    """The backticked spans of one shown string, joined — what a reader is told to *run*.

    The rest of the sentence is an illustration and stays exempt, which is the whole of this
    task's decision: `e.g. RK7` claims nothing about the reader's vocabulary, and
    `` `status RK7 🛠` `` is a command whose two values their own config decides.
    """
    return " ".join(SPANS.findall(text))


def test_no_command_a_help_string_offers_carries_a_project_value():
    """RK1558. Two scans read this package for the same rule and disagreed about the words a
    caller is shown — :func:`_values` exempts them and :func:`_composed_markers` does not —
    and nothing said which reading was the rule. Neither flagged anything, so the difference
    was invisible in both directions.

    Settled towards the narrower exemption, on a measurement rather than a preference: of the
    192 backticked spans inside these strings, not one carries a marker, an id or a governed
    file's name. The code already keeps the rule; stating it is what keeps it kept — and the
    third route, a *literal* marker inside a help string's command, was caught by neither scan.

    The whole check and not just the marker, because the three values leak the same way: a
    command shown to a reader whose prefix is `SH` and whose roadmap is `docs/BACKLOG.md` is
    a command they cannot run, whichever of the three this package spelled.
    """
    found: dict[str, list[str]] = {}
    for module in modules():
        if module.where in DECLARES:
            continue
        for lineno, text in _shown(module.text):
            offered = _offered(text)
            leaked = (
                any(marker in offered for marker in MARKERS)
                or IS_A_GOVERNED_FILE.search(offered)
                or any(IS_AN_ID.match(word.strip(".,;:")) for word in offered.split())
            )
            if leaked:
                found.setdefault(module.where, []).append(f"{lineno}: {offered[:60]!r}")
    assert found == {}, (
        "a help string may illustrate a value and may not build a command round one: the "
        "reader's own config decides it, and this parser is built before any config is read"
    )


def test_the_illustration_stays_exempt_and_the_command_does_not():
    """The distinction, exhibited — because it is the only thing this rule is, and a scan that
    held both halves the same way would be the forty-string allow-list the module rejects."""
    assert _shown('p.add_argument("--id", help="an existing line, e.g. RK12")') == [
        (1, "an existing line, e.g. RK12")
    ]
    # Outside a backtick nothing is offered, so the example this module was written to allow
    # is still allowed.
    assert _offered("an existing line, e.g. RK12") == ""
    assert _offered("take it first with `status RK7 🛠`") == "status RK7 🛠"
    # And the shape the code actually writes: the verb, with the values left as placeholders.
    assert _offered("what a commit script feeds to `git add --`") == "git add --"


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
