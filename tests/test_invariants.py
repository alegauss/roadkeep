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
kept. Three of the six laws were in that state when this file was written; RK1000 and
RK1021 wrote the two holders the rows had said were tasks, and one remains.

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

from surface import PACKAGE, addresses, modules

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
        # Reached by RK1021, and this row is what bought it: the surface is *the questions
        # somebody asks*, which no file enumerated, so the row said an inventory was a task
        # and not a test. `asking.QUESTIONS` is that inventory, joined to the parser — every
        # row's argv resolves to a handler the CLI declares as a read, and every read-only
        # verb either answers a row or says in a sentence why it answers none. The converse
        # RK167 held all along is still below it, and is still not the rule.
        over="asking.QUESTIONS",
        held_by="test_asking::test_every_declared_question_is_answered_by_a_command_that_only_reads",
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
        stated="RK1016",
        rule=(
            "every top-level entry this repository carries is named in the Layout index, or "
            "exempted there with a reason"
        ),
        # `git ls-files`, which nothing exports — RK478's case, and the third row here whose
        # surface is real and has no address. Writing one that only approximated it (a glob of
        # the working tree) would be the row claiming a set the holder does not sweep.
        over="",
        held_by="test_linting::test_every_surface_this_repository_carries_is_named_in_the_index",
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
    Invariant(
        stated="RK1022",
        rule=(
            "every command a message spells with a flag is one this CLI parses with that "
            "flag, so a hint hands over an argv that runs"
        ),
        over="surface.modules",
        held_by="test_hinting::test_every_command_a_message_spells_declares_the_flags_it_is_spelled_with",
    ),
)

#: The rules stated here that nothing holds, named so that losing a holder is a decision
#: somebody writes down rather than a row quietly going empty. Asserted equal to the rows
#: below, in both directions. L6 left this set with RK1000 and L5 with RK1021 — the one that
#: remains is the one whose surface is not a set at all, the rule being satisfied by an
#: absence: the services this package does not open and the schemas it does not migrate.
UNHELD = frozenset({"L2"})


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
    """The answer to the question this file was written to make askable, and the number it
    reports has moved twice: three of the six laws were unheld on the first run, and each of
    the two that left did so because its row had already said what an inventory would be."""
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


#: Calls this package may not make, keyed by the version that added them. Declared and not
#: derived: deriving every standard-library API's version needs a table nobody here maintains, and
#: what a row costs is one line. Each was measured — the first by CI, the afternoon it shipped.
#:
#: The keyword form is what bit: `Path.read_text(newline="")` is 3.13, `read_bytes` is not, and the
#: name alone would refuse every correct call. So a row is a callable's name and, where the version
#: is about an argument rather than the call, that keyword.
_NEWER_THAN_THE_FLOOR = {
    (3, 13): (("read_text", "newline"), ("read_bytes", "newline")),
    (3, 12): (("itertools.batched", ""), ("Path.walk", "")),
}


def _floor() -> tuple[int, int]:
    """The oldest Python this package supports, read from where it is declared.

    `requires-python` is the statement an installer enforces, so a second copy here would be a
    second answer to a question with one — the arrangement RK1000 removed from the config defaults
    and RK105 from the corpora. What this reads is the floor; what it holds is the calls above it.
    """
    declared = re.search(
        r'requires-python\s*=\s*">=(\d+)\.(\d+)"',
        (HERE / "pyproject.toml").read_text(encoding="utf-8"),
    )
    assert declared, "pyproject.toml declares no requires-python floor"
    return int(declared[1]), int(declared[2])


def test_no_call_needs_a_python_newer_than_the_floor():
    """RK1158. The suite runs on the version this machine develops with, so a newer call is green
    here and red only in CI — measured: `read_text(newline="")` is 3.13, it passed locally, the task
    shipped, and the gate this repository ships as an action found it a commit later, in a log
    somebody had to read. CI catching it is not the same as catching it.

    Over the package **and** the suite, because the one that shipped was in a test: a fixture is
    what runs on the floor as much as the code it exercises.
    """
    floor = _floor()
    watched = {
        name: (version, keyword)
        for version, rows in _NEWER_THAN_THE_FLOOR.items()
        if version > floor
        for name, keyword in rows
    }
    assert watched, f"nothing is newer than {floor}: the rows and the floor have met"
    found: list[str] = []
    for module in (*modules(), *sorted(Path(__file__).parent.glob("*.py"))):
        text = module.text if hasattr(module, "text") else module.read_text(encoding="utf-8")
        where = module.where if hasattr(module, "where") else f"tests/{module.name}"
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.Call):
                continue
            called = node.func.attr if isinstance(node.func, ast.Attribute) else getattr(
                node.func, "id", ""
            )
            if called not in watched:
                continue
            version, keyword = watched[called]
            passed = {word.arg for word in node.keywords}
            if not keyword or keyword in passed:
                spelled = f"{called}({keyword}=…)" if keyword else f"{called}()"
                found.append(f"{where}:{node.lineno} {spelled} needs {version[0]}.{version[1]}")
    assert found == [], found


#: Clauses that make a claim about a corpus's **past**. Each was measured for RK1148 and three
#: of the five skips RK1144 left carried one; three of those three were false — Shio conformed at
#: `b9302e8e` too and Turing spelled no lettered heading at `f08304fcb1` either — and RK1146 was
#: filed, worked and shipped on the strength of one. `corpora.retired` derives the clause from
#: the baseline instead, so what is forbidden here is writing one by hand.
_HISTORIES = ("any more", "has since", "used to", "it had", "since shipped")


#: Where git is spawned as its own process on purpose, and why each has to be. Every other call
#: goes through `conftest.git`, which is what carries `GIT_ENVIRONMENT` — the identity a fixture
#: repository needs and the machine is not asked for (RK456). Three call sites had grown around
#: it, and all three passed on a developer's machine and failed on every runner with no
#: `user.name`: `Committer identity unknown`, on this repository's own gate (RK1153).
_SPAWNS_GIT = {
    "conftest.py": "it is the runner: the one call that carries the environment is this one",
    "test_merging.py": "`git merge` is what invokes the driver, so it has to be git's own call",
    "test_linting.py": "it tolerates a non-zero exit, a tree git cannot answer for being an "
    "absent input rather than a failure, and the runner raises",
}


def test_no_test_spawns_git_around_the_suites_own_runner():
    """RK1153, and the reason it is a closure rather than three fixes.

    `conftest.git` exists because a fixture repository must need nothing from the machine, and a
    docstring saying so is not what the next inline `subprocess.run(["git", ...])` will read. So
    the sweep is over the argv: a `subprocess.run` whose first list element is `"git"` is a call
    that took the environment this suite was careful to replace.

    The exemption carries its reason and is asserted in both directions, which is RK491's rule:
    a file that stops spawning git leaves a row here that fails, and a file that starts spawning
    one fails until somebody writes down why it must.
    """
    spawning: dict[str, list[int]] = {}
    for module in sorted(Path(__file__).parent.glob("*.py")):
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            named = node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if named not in ("run", "Popen") or not isinstance(node.args[0], ast.List):
                continue
            first = node.args[0].elts[0] if node.args[0].elts else None
            if isinstance(first, ast.Constant) and first.value == "git":
                spawning.setdefault(module.name, []).append(node.lineno)
    assert set(spawning) == set(_SPAWNS_GIT), {
        "spawns git, no reason": sorted(set(spawning) - set(_SPAWNS_GIT)),
        "reason, spawns none": sorted(set(_SPAWNS_GIT) - set(spawning)),
    }
    assert all(len(why.split()) >= 6 for why in _SPAWNS_GIT.values())


def test_no_skip_writes_a_corpus_history_by_hand():
    """RK1148. The alternative this closes off is the one the section weighed and refused.

    A skip reason is prose an author writes once and nothing reads again, which is exactly the
    condition RK402 named in the other direction: a check that can only skip is one nobody
    notices. Forbidding the clause outright would lose what RK1145 needed it for — where the
    coverage went — so the clause is *derived* where it is true and refused where it is typed.

    Both directions, because a rule over an empty set is a rule about nothing: the helper has to
    be reached by more than one test, or this is a filter nobody trips and the histories are
    somewhere else.
    """
    typed: dict[str, list[int]] = {}
    reached = 0
    for module in sorted(Path(__file__).parent.glob("*.py")):
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Call):
                continue
            named = node.func.attr if isinstance(node.func, ast.Attribute) else ""
            if named == "retired":
                reached += 1
                continue
            if named != "skip":
                continue
            # The literal halves of the message, f-string or not: an interpolated revision is a
            # measurement and only the words around it can invent a history.
            said = " ".join(
                part.value
                for argument in node.args
                for part in (
                    argument.values if isinstance(argument, ast.JoinedStr) else [argument]
                )
                if isinstance(part, ast.Constant) and isinstance(part.value, str)
            )
            if any(clause in said for clause in _HISTORIES):
                typed.setdefault(module.name, []).append(node.lineno)
    assert typed == {}, typed
    assert reached >= 3, f"corpora.retired is reached {reached} time(s): the rule sweeps nothing"


def test_no_test_spells_an_address_the_package_no_longer_has():
    """RK1074. RK496 declared the module *set* and left the **addresses** hand-written.

    Moving two modules into `kernel/` for RK1069 broke seven surveys one at a time, each
    because a path literal somewhere had to be edited: a cache inventory key, the modules a
    denial may load, a `callers.pop(...)`, the pair a traceback note expects. Every one green
    afterwards, none of them wrong before — the failure RK496 names, arriving through the
    addresses rather than through the file set.

    Held on the literals that carry a **directory**, and deliberately not on bare ones: a
    test writing `schema.py` into its own `tmp_path` is naming a fixture, not this package,
    and a rule that could not tell them apart would be one somebody exempts their way around.
    Every address the move broke was of this shape or in a table one of these files declares,
    and `surface.address()` is what a test written tomorrow asks instead.
    """
    known = {module.where for module in modules()}
    stale: dict[str, list[str]] = {}
    for module in sorted(Path(__file__).parent.glob("*.py")):
        for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
            if not isinstance(node, ast.Constant) or not isinstance(node.value, str):
                continue
            if addresses(node.value) and node.value not in known:
                stale.setdefault(module.name, []).append(f"{node.value}:{node.lineno}")
    assert stale == {}, stale


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


# -- a fact the parser owns, guessed from the text (RK1102) -------------------


#: The **corpus** this repository is its own conformance fixture of: the governed files, plus
#: the directory they live in. Wider than `conftest.GOVERNED` on purpose — what the rule is
#: about is deciding a fact from a file this project *owns the reader for*, and `docs/` is where
#: those live, whatever a future file in it is called.
CORPUS = (
    "ROADMAP.md",
    "CHANGELOG.md",
    "IMPROVEMENTS.md",
    "STRATEGY.md",
    "roadkeep.toml",
    "agents.md",
    "README.md",
    "CLAUDE.md",
    "docs",
)

#: Every function in the suite that reads one of those as text, and why that is prose and not
#: a fact the parser owns (RK1104). RK1102 held this over `conftest.py` alone and said the
#: rest was out of reach; the measurement says otherwise — **six** functions in the whole
#: suite read this repository's own corpus, against 236 text reads overall, because almost
#: every one of those reads a file the test had just written under `tmp_path`.
#:
#: So the declarable set is small, and the reason to declare it is that each entry is a
#: sentence somebody had to write: reading prose *as prose* is legitimate, deriving structure
#: from it is what cost two reds, and no scan tells those apart. The reason is where the
#: telling happens.
READS_THE_CORPUS = {
    "test_exporting.test_this_repositorys_readme_is_current": (
        "the README as text, against the projection `export` writes into it — the assertion "
        "*is* about the characters, which is what makes it a comparison and not a guess"
    ),
    "test_exporting.test_the_landing_page_carries_no_projection_to_go_stale": (
        "the generated page under `docs/`, read for what it must *not* carry: no parser here "
        "reads HTML, and the fact being asserted is the absence of copied prose"
    ),
    "test_invariants.declared_instances": (
        "rationale prose, scanned for the ids it cites — a section body is text this format "
        "deliberately does not structure past its heading (L4)"
    ),
    "test_invariants.test_every_recorded_instance_is_a_task_this_project_carries": (
        "the same scan across both files, and the same reason: an id spelled inside a "
        "sentence is in no field a parser would return"
    ),
    "test_linting._layout_index": (
        "agents.md as text, to weigh one section of it against another — the budget is bytes "
        "and lines, so the characters are the subject and not a proxy for one"
    ),
    "test_linting.test_the_index_is_a_fifth_of_the_budget_and_the_prose_is_the_rest": (
        "the same weighing, whose whole finding (RK1094) was that a figure quoted from memory "
        "had gone stale — re-measuring the text is the correction, not the shape being warned "
        "about"
    ),
}


def _reads_the_corpus() -> dict[str, str]:
    """Every function in `tests/` that reads this repository's own corpus as text.

    Attributed to the enclosing function and not to a line, because a line number moves with
    every edit above it and the declaration would be re-keyed by an unrelated change. Matched
    on the *spelling* of the receiver — `HERE / "docs" / name`, `governed / "README.md"` — for
    the reason RK1103's own guard is a scan for spellings: nothing about a `read_text` call
    marks its argument as this project's file, so the reading is textual and says so.
    """
    found: dict[str, str] = {}
    for path in sorted(Path(HERE / "tests").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            for inner in ast.walk(node):
                if not (
                    isinstance(inner, ast.Call)
                    and isinstance(inner.func, ast.Attribute)
                    and inner.func.attr in ("read_text", "read_bytes")
                ):
                    continue
                spelled = ast.unparse(inner.func.value)
                if ("HERE" in spelled or "governed" in spelled) and any(
                    one in spelled for one in CORPUS
                ):
                    found[f"{path.stem}.{node.name}"] = spelled
    return found


#: The other half, and it is not the same claim (RK1102): a shared fixture answers once for
#: every test that asks, so *any* text read there is declared — not only a corpus one. Kept
#: beside the wider table rather than folded into it, because the two catch different things
#: and folding them would leave `conftest` covered only where it reads this project's files.
CONFTEST_READS_TEXT = {
    "frontmatter": (
        "a skill or command file, which no parser in this package owns: what it reproduces "
        "*is* the loader's own reading, and that is the whole point of it (RK331)"
    ),
}


def test_no_shared_fixture_decides_a_files_shape_from_its_text():
    """RK1102, held over the one file where a wrong predicate reaches furthest.

    Every test that asks receives one session-scoped answer, so a guess here is a guess made
    in fifty places at once — which is what `populated` was, matching `- ` and calling a
    roadmap of non-goals a populated backlog.
    """
    tree = ast.parse((HERE / "tests" / "conftest.py").read_text(encoding="utf-8"))
    readers = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        for inner in ast.walk(node)
        if isinstance(inner, ast.Call)
        and isinstance(inner.func, ast.Attribute)
        and inner.func.attr == "read_text"
    }
    assert readers == set(CONFTEST_READS_TEXT), (
        "a shared fixture reads a file as text: declare why in CONFTEST_READS_TEXT, or ask "
        "the parser — `Config.discover(HERE).document(role)` answers what a line is"
    )


def test_every_reader_of_this_projects_own_corpus_says_why():
    """RK1104: the rule RK1102 argued, held over the whole suite rather than one file.

    That task scoped the guard to `conftest.py` and said the rest was out of reach, because
    reading prose *as prose* is legitimate and no syntactic rule separates it from deriving
    structure. Both halves are still true. What was wrong was the size: the suite makes 236
    text reads and **six** of them touch this repository's own corpus — the rest read a file
    the test had just written under `tmp_path`, which is a fixture and not a fact.

    So the list is short enough to declare, and the declaration is where the telling-apart
    happens: each entry is somebody's sentence saying this one is prose. A new reader is a red
    with one question in it — is it prose, or is it a fact
    `Config.discover(HERE).document(role)` already answers.
    """
    assert set(_reads_the_corpus()) == set(READS_THE_CORPUS), (
        "a test reads this project's own corpus as text: declare why in READS_THE_CORPUS, "
        "or ask the parser — `Config.discover(HERE).document(role)` answers what a line is"
    )


def test_no_reason_is_a_placeholder():
    # The failure a table of reasons has: a row written to make the test above pass. Each says
    # what *this* read is about, so the cheapest wrong answer is one that does not.
    for where, why in {**READS_THE_CORPUS, **CONFTEST_READS_TEXT}.items():
        assert len(why.split()) >= 12, f"{where} has no reason in it"
        assert not why[0].isupper(), f"{where}: a clause, like every other row"


def test_the_rule_is_argued_where_the_next_predicate_is_written():
    """A rule stated nowhere is one the next author re-derives from scratch, which is how this
    one arrived twice. `conftest.py` is where it goes: its docstring is already the authority
    for what a test cannot get from its own assertion, and it costs no turn that reads none."""
    docstring = ast.get_docstring(
        ast.parse((HERE / "tests" / "conftest.py").read_text(encoding="utf-8"))
    )
    assert docstring is not None
    assert "Ask the parser, never the line" in docstring
    # Both failures named, because the rule without them is advice: what makes it land is that
    # it has already cost two reds, and one of those was written the same week as the rule.
    assert "RK1090" in docstring and "RK1098" in docstring


# -- one terminator per file (RK1132) ------------------------------------------


def test_no_file_mixes_the_two_line_terminators():
    """Measured before it was fixed: 45 of the package's modules held CRLF in the working tree
    and 11 held LF, and eight test files held **both** — because the index is normalised and
    some editors write CRLF back.

    Nothing renders differently and no diff is at stake, which is exactly what makes it
    expensive: an edit anchored on one terminator matches nothing in a file that uses the
    other, **silently**. That is RK1091's defect one layer down, and it stopped two scripted
    patches in a single session — cheap only because each carried an `assert` on its anchor.

    The declaration is `.gitattributes` (`* text=auto eol=lf`), which decides a *checkout*;
    this is what holds a tree somebody edited afterwards. Mixing and never "must be LF": a
    Windows checkout with `core.autocrlf=true` is uniformly CRLF and perfectly editable, and a
    test demanding LF would redden that machine for a setting the repository does not own.
    """
    mixed = []
    for module in (*modules(), *_test_modules()):
        raw = module.path.read_bytes()
        crlf = raw.count(b"\r\n")
        if crlf and raw.count(b"\n") - crlf:
            mixed.append(module.where)
    assert not mixed, mixed


def test_no_top_level_definition_lost_its_separator():
    """A `def`, `class` or decorator at column zero has two blank lines above it (RK1195).

    Python does not care and no diff is at stake, which is what makes it expensive — the same
    argument the terminator invariant above makes about the same kind of damage. What produces
    it is a scripted deletion: every one in this tree since RK1091 cuts from a definition to
    the next blank-line run, so the separator goes out with the block and the next definition
    closes the gap behind it. The anchor is the thing being counted on to survive.

    Measured when this was written: exactly one instance, in `rendering.py`, which four
    printers had been removed from two commits earlier. This tree takes no dev dependency, so
    a formatter is not the door — the sweep is.

    The first definition after the imports is exempt: one blank line there is this package's
    own convention in several modules, and a test that reddened them would be stating a rule
    the tree does not keep.
    """
    glued = []
    for module in (*modules(), *_test_modules()):
        text = module.path.read_text(encoding="utf-8")
        lines = text.splitlines()
        definitions = [
            node
            for node in ast.parse(text).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        ]
        # The first one carries no separator rule: what is above it is the import block, and
        # this package writes one blank line there as often as two.
        for node in definitions[1:]:
            # A decorator is where the definition starts, and the AST is what knows that: a
            # `@pytest.mark.parametrize(...)` spanning four lines leaves a bare `)` above the
            # `def`, which no reading of the text alone tells from a definition against a call.
            index = min(
                [node.lineno, *(one.lineno for one in node.decorator_list)]
            ) - 1
            # A comment written above a definition belongs to it, so the separator is above
            # the comment. Walk the run up, which is also how `#:` docs are written here.
            while index and lines[index - 1].lstrip().startswith("#"):
                index -= 1
            if lines[index - 1] or (index >= 2 and lines[index - 2]):
                glued.append(f"{module.where}:{index + 1}")
    assert not glued, glued


def test_the_declaration_that_decides_a_checkout_is_committed():
    # The other half, and the one a test cannot enforce on its own: a per-machine
    # `core.autocrlf` is not a promise to a contributor who never set it (L6).
    declared = (Path(__file__).parent.parent / ".gitattributes").read_text(encoding="utf-8")
    assert "* text=auto eol=lf" in declared
    assert "RK1132" in declared  # the measurement it came from, where a reader will look


def _test_modules():
    """This suite's own files, as `Module`-shaped rows. The one read `surface` cannot make:
    it declares the *package*, and the terminator invariant is about every file an author
    edits — which is why `test_invariants.py` is in `_MAY_GLOB` at all."""
    from surface import Module

    return tuple(
        Module(where=f"tests/{path.name}", path=path)
        for path in sorted(Path(__file__).parent.glob("*.py"))
    )


def test_no_module_defines_one_name_twice():
    """RK1170's find, and the cheapest closure this package did not have.

    `rendering.py` held two `_commit_json`s — one nullable and one not — and the second shadowed
    the first, so a caller written against the older signature raised on the `None` it was built
    to accept. Both definitions read correctly on their own, which is what makes this invisible:
    the defect is in what the *module* resolves, and nothing was asking.

    Over the package and the suite, and over functions, classes **and top-level constants** alike:
    a fixture redefined halfway down a test file is the same failure with a friendlier name.
    Assignments were left out of the first version of this and cost a session within the hour —
    a new `STANDING` fixture at the end of `test_shipping.py` rebound the roadmap of that name
    250 lines above it, and three tests started shipping against a TOML file. Measured before
    widening: one other case existed in the whole tree, and it was a constant bound twice to the
    same value, which is noise rather than a pattern to protect.

    Only **module level**. A name re-bound inside a function or under a condition is ordinary
    Python and says nothing about what a reader resolves.
    """
    twice: dict[str, list[str]] = {}
    for module in (*modules(), *sorted(Path(__file__).parent.glob("*.py"))):
        text = module.text if hasattr(module, "text") else module.read_text(encoding="utf-8")
        where = module.where if hasattr(module, "where") else f"tests/{module.name}"
        seen: dict[str, int] = {}
        for node in ast.parse(text).body:
            bound: list[str] = []
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bound = [node.name]
            elif isinstance(node, ast.Assign):
                bound = [one.id for one in node.targets if isinstance(one, ast.Name)]
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                bound = [node.target.id]
            for name in bound:
                if name in seen:
                    twice.setdefault(where, []).append(
                        f"{name} at {seen[name]} and {node.lineno}"
                    )
                seen[name] = node.lineno
    assert twice == {}, twice


def test_no_dict_literal_states_one_key_twice():
    """The duplicate definition's smaller sibling, found while moving `delivered` (RK1170).

    `_standing_json` spelled `"sentence"` twice in one literal — harmless, because both said the
    same thing, and invisible for exactly that reason: the second binding wins silently, so the
    day the two spellings differ the payload publishes whichever came last. Python has no error
    here and this package runs no linter (RK1158), so the closure is the check.

    Over the package and the suite, both directions of the same rule as
    :func:`test_no_module_defines_one_name_twice`: a name bound twice in one place is a question
    about what the reader resolves, not a style.
    """
    twice: dict[str, list[str]] = {}
    for module in (*modules(), *sorted(Path(__file__).parent.glob("*.py"))):
        text = module.text if hasattr(module, "text") else module.read_text(encoding="utf-8")
        where = module.where if hasattr(module, "where") else f"tests/{module.name}"
        for node in ast.walk(ast.parse(text)):
            if not isinstance(node, ast.Dict):
                continue
            said = [
                key.value
                for key in node.keys
                if isinstance(key, ast.Constant) and isinstance(key.value, str)
            ]
            for key in sorted({one for one in said if said.count(one) > 1}):
                twice.setdefault(where, []).append(f"{key!r} at line {node.lineno}")
    assert twice == {}, twice
