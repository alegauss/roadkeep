"""Which rules this package states, and which of them a property reaches (RK491).

RK421 asserts the remedy table is total over the codes `linting` and `schema` emit. RK467
sweeps every boolean pair a read takes. RK474 checks that every complete door is an argv the
CLI accepts. Three tests, three files, weeks apart, each the same act: a rule about the
*whole* surface, held by enumeration and not by example. Nothing recorded that they were one
family, so the question that matters could not be asked — and the distance between what this
project states and what a property reaches is where the last fifty commits' defects lived.

:data:`INVARIANTS` is that set. One row per rule, naming where it is stated, the surface it
quantifies over, and the test that holds it. **A rule nobody holds is a row with an empty
holder**, which is the point: an absence nobody can see reads exactly like a rule that is
kept, and two of the six laws are in that state right now.

The rows are not the deliverable — the **closure** is. A set that any stated rule can be
missing from is one more docstring, so what this file asserts first is that the six laws
`docs/IMPROVEMENTS.md` §0.3 declares are exactly the six laws with a row. That table is the
authoritative statement of them (`agents.md` says so), it is machine-readable, and a seventh
law added to it is a red here until somebody says whether anything holds it.

What the closure cannot reach is a rule stated in ordinary prose, and this file does not
pretend otherwise: no set enumerates the sentences in forty module docstrings, and deciding
which of them are rules would take a model this tool does not have (L4). The bound is honest
rather than total — the laws are closed, the surfaces are declared, and a property that
sweeps a surface no row names has nowhere to be recorded, which is what a new row costs.
"""

from __future__ import annotations

import ast
import importlib
import re
from dataclasses import dataclass
from pathlib import Path

from surface import PACKAGE, modules

HERE = Path(__file__).resolve().parents[1]

#: Where the six laws are stated authoritatively. `agents.md` carries a compressed copy and
#: says this one governs, so this is what the closure reads: a law added to the compressed
#: table and not to this one is a different defect, and `lint` already holds that file.
LAWS = HERE / "docs" / "IMPROVEMENTS.md"


@dataclass(frozen=True, slots=True)
class Invariant:
    """One rule this package states, and what — if anything — holds it."""

    #: Where the rule is written down: `L<n>` for one of the six laws, or the task that
    #: introduced the property. Unique, because it is this row's address.
    stated: str
    #: What it claims, in one sentence. Not a copy of the law's own wording: the law says
    #: what the project believes and this says what is quantified over.
    rule: str
    #: The surface it quantifies over, as a dotted name this suite can import. `""` in two
    #: different states, and :func:`test_a_rule_nothing_holds_is_a_row_and_never_an_absence`
    #: separates them: with no holder it means no enumeration could hold the rule, and with
    #: one it means the holder derives its own surface and there is no name to import — the
    #: dataclasses carrying a `served` field are a set with no address.
    over: str
    #: The test that holds it, `<module>::<test>`. **`""` is a real answer**: the rule is
    #: stated and nothing checks it, which is the fact this whole file exists to surface.
    held_by: str = ""
    #: Every task that turned out to be an *instance* of this rule (RK1001) — a defect in a
    #: class this row already claims to cover, which is a hole in the holder rather than new
    #: work. The durable half of a declaration a rationale section makes and a `ship` deletes,
    #: so two entries here are a number pointing at the property and not at the code.
    instances: tuple[str, ...] = ()


#: Every rule this package states that anybody has thought to write down, and its holder.
#:
#: Two of the six laws have none. That is not an oversight to be tidied away — it is the
#: measurement this task was for, and the rows say what a property over each would have to
#: quantify over before anybody writes one.
INVARIANTS: tuple[Invariant, ...] = (
    Invariant(
        stated="L1",
        rule=(
            "every command the barrier offers instead of a hand-edit is one this CLI "
            "parses, so the enforcement point never teaches a command that does not run"
        ),
        over="roadkeep.guarding._INSTEAD",
        held_by="test_guarding::test_the_verbs_the_refusal_recommends_do_not_trip_it",
    ),
    Invariant(
        stated="L2",
        rule=(
            "the store is the repository: Markdown, greppable, no database and no service"
        ),
        # Nothing enumerates it, and the honest reason is that the rule is satisfied by an
        # *absence*. A property would have to quantify over the services this package does
        # not open and the schemas it does not migrate, which is not a set. What exists is
        # evidence — `test_packaging::test_there_are_no_runtime_dependencies` — and evidence
        # is not a holder, which is exactly the distinction this file is for.
        over="",
    ),
    Invariant(
        stated="L3",
        rule=(
            "every governed file of every pinned corpus parses and renders back to the "
            "bytes it was read as"
        ),
        over="roadkeep.config.ROLES",
        held_by="test_corpora::test_the_live_tree_still_round_trips",
    ),
    Invariant(
        stated="L4",
        # This row is what the register bought on its first run. What held L4 was a test over
        # five codes somebody listed — which is the state RK421 replaced for the table's
        # *domain* and nobody had replaced for its *content* — and the closure below could
        # not accept it, because a row claiming a surface has to reach one.
        rule=(
            "no row in the remedy table writes a word the author would have to: every one "
            "is a verb, a flag, a blank, a value the finding gave, or a declared role"
        ),
        over="roadkeep.remedying.codes",
        held_by="test_remedying::test_no_row_writes_a_word_only_the_author_could_have",
    ),
    Invariant(
        stated="L5",
        rule="every question a maintainer asks a governed file is answerable as a command",
        # Unheld, and the surface is why: the set is *the questions somebody asks*, which no
        # file enumerates. What is held is the converse — RK167 below, that every command
        # this surface publishes is one the CLI parses — and a converse is not the rule. A
        # property here would need a declared inventory of the reads, which is a task and
        # not a test, and stating that is what this row buys.
        over="",
    ),
    Invariant(
        stated="L6",
        rule=(
            "prefix, paths, markers and limits are read from roadkeep.toml and never "
            "written into the package"
        ),
        # Reached by RK1000, which is what the row was for: the two above are unheld because
        # no set exists, and this one was unheld because nobody had written the scan. What it
        # sweeps is the package's own source, minus the two modules a default is declared in.
        over="surface.modules",
        held_by="test_configured::test_no_module_writes_a_marker_a_project_declares",
    ),
    Invariant(
        stated="RK421",
        rule="every code the gate can emit has a row in the remedy table",
        over="roadkeep.remedying.codes",
        held_by="test_remedying::test_every_code_the_package_can_emit_has_a_door",
    ),
    Invariant(
        stated="RK467",
        rule=(
            "every pair of boolean flags a read-only verb takes is refused exactly where "
            "that verb's own declaration says the two are separate answers"
        ),
        over="roadkeep.cli.build_parser",
        held_by="test_pairs::test_the_dispatcher_refuses_exactly_the_pairs_a_verb_declares",
    ),
    Invariant(
        stated="RK474",
        rule="every complete door in the remedy table is an argv this CLI accepts",
        over="roadkeep.remedying.codes",
        held_by="test_remedying::test_every_complete_door_is_an_argv_the_cli_accepts",
    ),
    Invariant(
        stated="RK167",
        rule="every tool this server publishes is a subcommand the CLI parses",
        over="roadkeep.serving.TOOLS",
        held_by="test_serving::test_every_tool_is_a_subcommand_the_cli_accepts",
    ),
    Invariant(
        stated="RK478",
        rule=(
            "every message that blocks a turn offers its verbs in the spelling the session "
            "can call, and what the sweep lets through says why"
        ),
        # The surface is *every dataclass in `guarding` and `attesting` carrying a `served`
        # field*, which the holder derives and nothing exports: there is no name to put here,
        # and writing one that only approximates it would be worse than the blank.
        over="",
        held_by="test_spelling::test_the_sweep_reaches_every_message_that_blocks_a_turn",
    ),
    Invariant(
        stated="RK488",
        rule=(
            "no module outside the renderer turns the served prefix into text, so a new "
            "surface is one change rather than forty"
        ),
        # `every module of this package`, which had no address until RK496 gave it one: the
        # holder globbed its own, and after RK494 it was answering about 43 of 51 files.
        over="surface.modules",
        held_by="test_remedying::test_no_module_outside_the_renderer_spells_a_served_command",
    ),
    Invariant(
        stated="RK496",
        rule=(
            "every survey over this package's source quantifies over all of it, and no test "
            "derives a second view of which files that is"
        ),
        over="surface.modules",
        held_by="test_invariants::test_no_survey_derives_its_own_view_of_the_package",
    ),
    Invariant(
        stated="RK498",
        rule=(
            "every code the gate can emit says whether the write path refuses it, and the "
            "rows claiming it does are measured by a probe rather than asserted"
        ),
        over="roadkeep.remedying.codes",
        held_by="test_prevention::test_every_code_the_gate_can_emit_has_a_row",
    ),
    Invariant(
        stated="RK1004",
        rule=(
            "every code a write refuses says what the gate reports about a file already in "
            "that state — the same code, another one, or nothing and why"
        ),
        over="test_backstop.BACKSTOP",
        held_by="test_backstop::test_every_code_a_write_refuses_has_a_row",
    ),
    Invariant(
        stated="RK1005",
        rule=(
            "every key a `--json` payload promises a reader outside this process is still "
            "in it, one level into the rows a client walks"
        ),
        over="test_payloads.PROMISED",
        held_by="test_payloads::test_the_top_level_keys_a_client_is_promised_are_there",
    ),
    Invariant(
        stated="RK490",
        rule=(
            "every field a remedy row may name between braces is one the finding answers, "
            "in both directions"
        ),
        over="roadkeep.remedying.FIELDS",
        held_by="test_remedying::test_the_declared_fields_are_exactly_the_ones_a_finding_answers",
    ),
)

#: The rules stated here that nothing holds, named so that losing a holder is a decision
#: somebody writes down rather than a row quietly going empty. Asserted equal to the rows
#: below, in both directions. L6 left this set with RK1000, and the two that remain are the
#: two whose surface is not a set: an absence, and an inventory nobody has written down.
UNHELD = frozenset({"L2", "L5"})


def declared_laws() -> set[str]:
    """The laws §0.3 states, read out of the file rather than listed here (RK491)."""
    body = LAWS.read_text(encoding="utf-8")
    section = body[body.index("### §0.3") :]
    section = section[: section.index("\n### ")]
    return set(re.findall(r"^\|\s*(L\d+)\s*\|", section, flags=re.MULTILINE))


# -- the closure --------------------------------------------------------------


def test_every_law_this_project_states_has_a_row():
    """The deliverable, and not the rows: a set any stated rule can be missing from is one
    more docstring. §0.3 is the authoritative table — `agents.md` carries a compressed copy
    and says so — it is machine-readable, and a seventh law added to it fails here until
    somebody says whether anything holds it."""
    stated = declared_laws()
    assert stated, "§0.3 stopped yielding laws: the closure is reading nothing"
    covered = {one.stated for one in INVARIANTS if one.stated.startswith("L")}
    assert covered == stated, {"stated, no row": stated - covered, "row, not stated": covered - stated}


def test_a_rule_nothing_holds_is_a_row_and_never_an_absence():
    """The answer to the question this file was written to make askable. Three of the rules
    stated here are reached by a property and three of the six laws are not, and the second
    number is the one that could not be read anywhere before."""
    empty = {one.stated for one in INVARIANTS if not one.held_by}
    assert empty == UNHELD, {"newly unheld": empty - UNHELD, "newly held": UNHELD - empty}
    # And an unheld row says what a holder would have to quantify over, in prose beside it —
    # which is why `over` is empty on every one of them: a surface named with no test is a
    # claim that the property is one line away, and none of these is.
    for one in INVARIANTS:
        if not one.held_by:
            assert not one.over, f"{one.stated}: names a surface and holds nothing"


# -- the rows are real --------------------------------------------------------


def test_every_row_is_addressed_once_and_states_one_rule():
    stated = [one.stated for one in INVARIANTS]
    assert len(stated) == len(set(stated)), stated
    for one in INVARIANTS:
        assert one.rule and one.rule[0].islower(), one.stated
        assert not one.rule.endswith("."), f"{one.stated}: the rule is a clause, not a sentence"


def test_every_holder_names_a_test_that_exists():
    """A holder that stopped existing is a rule that stopped being held, and the row would
    still read as kept — which is the exact failure mode this file exists to remove."""
    for one in INVARIANTS:
        if not one.held_by:
            continue
        where, _, name = one.held_by.partition("::")
        module = importlib.import_module(where)
        assert callable(getattr(module, name, None)), f"{one.stated}: no {one.held_by}"


def test_every_declared_surface_resolves_and_is_not_empty():
    """A row claiming a property sweeps something has to name something to sweep. Called
    where the surface is a function, because `codes()` and `build_parser()` are the two
    shapes an enumerator takes here and both answer the same question."""
    for one in INVARIANTS:
        if not one.over:
            continue
        where, _, name = one.over.rpartition(".")
        surface = getattr(importlib.import_module(where), name)
        if callable(surface) and not isinstance(surface, type):
            surface = surface()
        assert len(getattr(surface, "_actions", surface)) > 0, one.over


def test_a_holder_reaches_the_surface_its_row_names():
    """The row is a claim about *what* the test quantifies over, and a claim nothing checks
    is the state RK421, RK467 and RK474 were already in. Read off the holder's own source:
    a test that stopped mentioning its surface is one whose row now describes a different
    property."""
    for one in INVARIANTS:
        if not one.held_by or not one.over:
            continue
        where, _, name = one.held_by.partition("::")
        source = Path(importlib.import_module(where).__file__).read_text(encoding="utf-8")
        body = next(
            node
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.FunctionDef) and node.name == name
        )
        named = one.over.rpartition(".")[2]
        reached = any(
            isinstance(node, ast.Name) and node.id == named for node in ast.walk(body)
        ) or f"{named}" in ast.get_source_segment(source, body).replace(name, "")
        assert reached, f"{one.stated}: {one.held_by} never names {one.over}"


# -- the surface the surveys share (RK496) ------------------------------------


#: The two modules allowed to ask the filesystem for a set of `.py` files, and why: `surface`
#: **is** the declaration, and this one reads `tests/` rather than the package — the single
#: read that cannot come from the declaration it exists to check. Spelled as a list for
#: `_MAY_SPELL`'s reason: an exemption nobody can see reads exactly like a rule being kept.
_MAY_GLOB = frozenset({"surface.py", "test_invariants.py"})


def test_no_survey_derives_its_own_view_of_the_package():
    """RK496. Seven tests sweep every module of `roadkeep`, and each used to glob for them
    inline — against whatever layout existed the day it was written. RK494 added
    `src/roadkeep/verbs/` and its eight modules: two of the seven failed loudly, and **three
    kept passing while covering nothing new**, which is a claim rather than a message.

    Held at the source, for the reason the rows above are: a second file set agrees with this
    one right up until the layout moves, which is the single moment either of them matters.
    `surface.py` is the one module allowed to ask the filesystem what the package holds, so a
    survey written tomorrow either imports the set or fails here.
    """
    asking = {}
    for module in sorted(Path(__file__).parent.glob("*.py")):
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            if node.func.attr not in ("glob", "rglob") or not node.args:
                continue
            first = node.args[0]
            # A glob of the caller's own tmp_path or of some other file type is nobody's
            # business here: what is held is the set of *this package's modules*.
            if isinstance(first, ast.Constant) and str(first.value).endswith(".py"):
                asking.setdefault(module.name, []).append(node.lineno)
    assert set(asking) == _MAY_GLOB, asking
    assert asking["surface.py"], "surface.py stopped reading the package at all"


def test_the_declared_surface_reaches_the_directories_under_the_package():
    """The half the gate above cannot hold. Every survey asking one set is worth nothing if
    that set is the top level, and `glob` for `rglob` is a one-character regression that no
    count would show. Decidable because a subpackage exists: `verbs/` is eight modules, and a
    surface that stopped recursing answers about none of them while still answering.
    """
    inside = [one.name for one in PACKAGE.iterdir() if (one / "__init__.py").exists()]
    assert inside, "the package holds no subpackage: this property stopped being decidable"
    for one in inside:
        assert any(module.where.startswith(f"{one}/") for module in modules()), one


# -- a recurrence is a hole in a holder, and it is declarable (RK1001) ---------
#
# **The count is zero today, and that is the first honest reading rather than a mechanism
# that does nothing.** Twelve rows carry a holder, and no open design is an instance of one:
# RK1000's three literals were instances of L6, which had no holder until that task wrote
# one — a rung, correctly. The declaration is what makes the first real recurrence countable
# instead of arriving as new work, and nothing here invents one to look busy: matching a
# symptom to a class takes meaning, and L4 forbids the model.


#: The info string a rationale section carries to say which rule it is an instance of.
#: Hyphenated for :data:`roadkeep.remaining.FENCE`'s reason: a colon in an info string is how
#: several renderers spell a language attribute, and this has to survive being read on a forge.
INSTANCE_FENCE = "roadkeep-instance"


def declared_instances(body: str | None = None) -> dict[str, tuple[str, ...]]:
    """Which rule each open design says it instantiates, by task id.

    Read off `docs/IMPROVEMENTS.md` rather than off a list here, because the person who can
    say what a task is an instance of is the person writing its design — and that is where
    the claim is made, in the shape RK492 established for a machine-readable one.

    A section is **deleted on ship**, so this answers about the backlog and never about
    history. :attr:`Invariant.instances` is the durable half, and the two are held in step
    below: a design declaring a row must also appear in that row, which is what lets the
    count outlive the paragraph that made the claim.
    """
    if body is None:
        body = (HERE / "docs" / "IMPROVEMENTS.md").read_text(encoding="utf-8")
    out: dict[str, tuple[str, ...]] = {}
    task = ""
    inside = False
    rows: list[str] = []
    for line in body.splitlines():
        heading = re.match(r"^#+\s+§(\S+)", line)
        if heading:
            task, inside, rows = heading.group(1), False, []
        elif line.strip() == f"```{INSTANCE_FENCE}":
            inside = True
        elif inside and line.strip().startswith("```"):
            inside = False
            if task and rows:
                out[task] = tuple(rows)
        elif inside and line.strip():
            rows.append(line.strip())
    return out


def test_every_declared_instance_names_a_rule_that_exists():
    """A design naming a row nothing declares is a claim about a rule this project does not
    state — the one half of RK1001 that is decidable without meaning (L4)."""
    stated = {one.stated for one in INVARIANTS}
    for task, rows in declared_instances().items():
        unknown = [row for row in rows if row not in stated]
        assert not unknown, f"§{task} names {unknown}, which no row declares"


def test_an_instance_only_names_a_rule_something_holds():
    """A row with no holder is the other answer, and it stays silent: an instance of L2 or L5
    is a **rung** and not a recurrence, correctly, because nothing ever claimed to cover it.
    Declaring one would file new work under a heading meaning "this should have been caught"."""
    held = {one.stated for one in INVARIANTS if one.held_by}
    for task, rows in declared_instances().items():
        loose = [row for row in rows if row not in held]
        assert not loose, f"§{task} names {loose}, which nothing holds: that is a rung"


def test_the_durable_half_carries_every_open_declaration():
    """What keeps the count from dying with the paragraph. `ship` deletes the section, so a
    declaration that lived only in prose would leave the row it was an instance of unable to
    say it had taken one — and the number is the whole point: two instances of a rule twelve
    rows claim to hold is a hole in the holder, and the fix belongs in the test."""
    instances = {one.stated: one.instances for one in INVARIANTS}
    for task, rows in declared_instances().items():
        for row in rows:
            assert task in instances.get(row, ()), (
                f"§{task} declares {row}; add {task!r} to that row's `instances` so the "
                f"count survives the ship that deletes this section"
            )


def test_every_recorded_instance_is_a_task_this_project_carries():
    """The other direction: a row naming an id no file carries is a count of nothing."""
    carried = set()
    for name in ("ROADMAP.md", "CHANGELOG.md"):
        carried |= set(re.findall(r"\*\*([A-Z]+\d+[a-z]?)", (HERE / "docs" / name).read_text(encoding="utf-8")))
    for one in INVARIANTS:
        missing = [task for task in one.instances if task not in carried]
        assert not missing, f"{one.stated}: {missing} is in neither governed file"


def test_the_reader_finds_a_declaration_and_stops_at_the_section_that_made_it():
    """Held over a fixture and not over `docs/`, because the backlog may honestly declare
    none: a mechanism whose only evidence is an empty answer is one nobody can tell from a
    reader that is broken."""
    body = "\n".join(
        [
            "### §RK9 A design",
            "",
            "A paragraph.",
            "",
            f"```{INSTANCE_FENCE}",
            "RK421",
            "RK467",
            "```",
            "",
            "### §RK10 Another design",
            "",
            f"A paragraph naming ```{INSTANCE_FENCE}``` in prose and declaring nothing.",
            "",
            "### §RK11 A third",
            "",
            "```roadkeep-remaining",
            "src/**.py :: pattern",
            "```",
            "",
        ]
    )
    # One section, one declaration: the fence a *second* section opens is another block, and
    # a sentence quoting the info string is prose — the same two mistakes RK492's reader has
    # to survive in a file whose subject is the format itself.
    assert declared_instances(body) == {"RK9": ("RK421", "RK467")}
