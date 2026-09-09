"""Every pair of boolean flags a read can be given, and what it may not answer (RK467).

RK465 found `cost --tools --role` by probing refusal paths; RK466 found `anchors --claims
--next` and `export --readme --json` the same way, and one of the three it first claimed
turned out to be the transaction working. Three probes, two defects, one false positive —
which is what finding a class by hand looks like, and the read-only surface has more pairs
than anybody is going to try.

**The signature is mechanical and exact.** A swallowed flag leaves output *byte-identical to
one half alone* and different from the other: `anchors --claims --next` printed what `--next`
prints, to the character. So every pair is one of three things, and the fourth is the defect:

* **refused** — exit 2, which is two subjects saying so (`budget`'s five, RK465);
* **composed** — exit 0 and an answer that is neither half's, which is `list --block --json`
  and every ordinary combination;
* **idempotent** — exit 0 and an answer identical to *both* halves, which is a flag that
  changed nothing for a reason of its own and is stated below rather than guessed at;
* and **swallowed** — exit 0, identical to one half and not the other. That one is the bug.

An inventory rather than a call site, which is this project's answer to a class: `VOLATILE`
names the caches an autouse fixture clears and says why the rest are cleared for nothing
(RK268), and `remedying`'s table is asserted total over every code the gate can emit (RK421).

**And since RK489 it is a property rather than a search.** The refusal used to be twenty-five
hand-written lines inside `budget` and four smaller copies elsewhere, so this file was the
only thing that could say which verb had them — it reported the next defect *after* a flag
nothing reads had been written. Now every verb that takes more than one answer declares its
subjects at `add_parser` and one dispatcher enforces them, so each pair below is predicted
before it is run: a pair the declaration separates must exit 2, and one it does not must
compose. What this sweep now measures is whether the declaration is **complete**, which is a
question about a table rather than a hunt through eighty verbs.

**A reading is only as wide as the fixture** (RK1489). Both halves of the signature above are
about output that did or did not move, which says nothing where the fixture cannot hold the
state a flag is about: four files in a bare directory have no history, so `anchors --retired`
answered as `--json` alone and a correct flag was reported swallowed. The other half was
quieter — nine pairs exited non-zero for want of a git repository, a `[non_goals]` table or a
deferred store, and this file read every one of them as two subjects refusing. So the fixture
is a repository with a section shipped away between its two commits, and what it still cannot
reach is `_UNMEASURED`, named with the state each row wants. The first thing that came out of
the widening was a real defect: `origin --why --json`, where the payload carries the message
either way and the served tool set a flag that shaped nothing.

**And that defect is the second sweep** (RK1517). One flag rather than two, over the transport
rather than the terminal: `serving` appends `--json` to every call it makes, so a flag whose
whole effect is on the rendered form shapes nothing an agent can see, and eighteen booleans are
served with nothing asking that of them. The reading is the one above at arity one — the call
the *server* composes, run with the flag and without — and it is here rather than in a file of
its own because it is the same question, off the same fixture, through the same runner: a flag
that moved nothing, and whether the fixture or the flag is why. What it does not share is the
population: `pairs()` is every read-only verb and `served()` is `TOOLS`, writes included.
"""

from __future__ import annotations

import argparse
import contextlib
import inspect
import io
import itertools
import re
import shutil
from pathlib import Path

import pytest

from conftest import git_commit, git_init
from roadkeep.cli import _one_answer, build_parser, main
from roadkeep.verbs.querying import _cost as _cost_handler

ROADMAP = """# Roadmap

## Priority

- RK2

## Block A — The model

- 💭 **RK1** (deps: —) **A first symptom** — Because of a reason. → §I.1
- 🛠 **RK2** (deps: RK1) **A second symptom** — Because of another. → §I.2

## Non-goals

- **No web UI.** Files and a CLI.
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK9** **A shipped symptom** — It works now.
"""

PROSE = """# Improvements

## Block A — The model

## I A family

The prose a family opens with.

### I.1 The first design (RK1)

The reasoning the line has no room for.

### I.2 The second design

The reasoning the other line has no room for.
"""

#: The section this fixture ships away between its two commits (RK1489), so the diff holds a
#: retired address. Pointed at by nothing: what retires an address is a heading that was there
#: and is not, and a live pointer to it would be `ref.dangling` rather than history.
SHIPPED = """
### I.3 The design that has shipped

The reasoning a line that has left no longer needs.
"""

#: The **first** commit's message, with a body (RK1554). A blank line and a sentence, which is
#: all a commit body is and all a flag that prints one needs to be readable — `origin --why`
#: adds each commit's under the rows, and against two subject-only commits it answered exactly
#: what `origin` answered, for a reason that was the fixture and not the flag.
#:
#: The first and **not the second**, which is the half writing it found: `--why` prints the
#: *shipping* commit's message, and the ledger's one shipped line lands in this commit. Which
#: also moved `NEEDS["origin"]` off RK1 — a line only ever proposed is one that flag can never
#: fire on, so the id was as much of why it read as inert as the missing body was.
#:
#: Its own constant so the two halves are visible together: the subject is what `origin` prints
#: and the body is what the flag adds, and a message assembled inline would put the difference
#: this fixture exists to hold inside a string literal in a call.
PROPOSING_MESSAGE = (
    "the project, with a design whose line has not left yet\n"
    "\n"
    "RK9 is recorded shipped here, which is the row `origin RK9 --why` reads — and this "
    "body is what that flag adds under it, which a subject alone cannot make readable."
)

#: Flags that **write**, inside commands whose parser is declared read-only. Each is the
#: RK16 exception — the repair belongs where a human is standing — and none of them belongs
#: in a sweep that runs every pair against one fixture: a `--fix` in the middle of it would
#: change what every later pair is measured against.
_WRITES = {
    ("lint", "--fix"),
    ("claims", "--prune"),
    ("merge", "--register"),
    ("brief", "--claim"),
    ("pick", "--claim"),
}

#: Commands this sweep does not reach, and why — stated rather than filtered in silence, for
#: the reason a truncated listing states its own truncation.
_UNREACHED = {
    "report": "it re-runs a named command and writes a capture, so it is not one read",
    "replay": "it needs a stored capture, which is a fixture and not a flag",
}

#: Pairs that answer identically to *both* halves, with the reason each does. A flag that
#: changes nothing here is not a swallowed flag — it is one whose effect this fixture does
#: not exhibit — and saying which is what keeps the sweep from being loosened to admit one.
#:
#: Empty, and that is the finding rather than the absence of one: every pair this reaches
#: either composes or is refused. It stays because the alternative to a named exception is
#: an unnamed one, and the assertion below is what makes adding a row a decision.
_IDEMPOTENT: dict[tuple[str, str, str], str] = {}

#: Pairs whose non-zero exit is the **fixture** and not the declaration, with the state each
#: wants (RK1489). The sweep used to end on any non-zero code — "refused, which is two
#: subjects saying so" — and nine exits were nothing of the kind, so its own reach was being
#: read as a result. RK1466 met that from the other side: `anchors --retired` answered as
#: `--json` alone because a directory with no `.git` has no retired address to withhold, and a
#: correct flag was reported swallowed.
#:
#: The history is in the fixture now, which is what took `origin` and `weight` off this list
#: and turned `origin --why --json` into the defect it was hiding. What is left is state a
#: read-only sweep cannot give itself: three of these want a `roadkeep.toml` that is not this
#: one, and a project cannot declare two schemes at once.
#:
#: `adopt --ledger --sections` left it the other way (RK1518). Its row said the exit was right
#: and came from a refusal raised inside the estimator, where nothing reading declarations can
#: see it — which is the row a table like this exists to make legible. The verb declares the
#: two flags two answers now, so `separated` reports it and this list is shorter by the one
#: entry that was describing a defect rather than a fixture.
_UNMEASURED: dict[tuple[str, str, str], str] = {
    ("adopt", "--ledger", "--json"): "this fixture's ledger is the roadmap `NEEDS` names",
    ("adopt", "--sections", "--json"): "the same, one flag over",
    ("brief", "--designed", "--json"): "no line here is both ready and designed",
    ("budget", "--defer", "--json"): "no `deferred` store is declared, and declaring one "
    "would change what every other pair on this fixture is measured against",
    ("budget", "--non-goal", "--json"): "no `[non_goals]` table, which is opt-in (RK66)",
    ("list", "--ids", "--stale"): "`--stale` names the deferred store (RK1547) and this "
    "fixture declares none — the same state `budget --defer` wants, and declaring one here "
    "would change what every other pair is measured against",
    ("list", "--json", "--stale"): "the same, one form over",
    ("merge", "--check", "--json"): "exit 1 is this verb's finding and not a refusal — a "
    "clean tree is the state it wants, and the fixture's is mid-build",
}


def _write(root: Path, name: str, body: str) -> None:
    with (root / name).open("w", encoding="utf-8", newline="") as handle:
        handle.write(body)


def _build(root: Path) -> Path:
    """The fixture, and the history three of these flags are about (RK1489).

    An **outline** project (RK467): under `ref_scheme = "id"` the anchor is the id, so
    `anchors` refuses for want of a family and every pair on it exits 2 — which a sweep reads
    as "refused, nothing to check" and learns nothing from.

    And **a repository, with a section shipped away between two commits** (RK1489). The sweep's
    reading of a swallowed flag is that the output did not move, which is only evidence where
    the fixture can hold what the flag is about. It could not: retired addresses come out of
    `git log -U0` over the prose file and this wrote four files into a bare directory, so
    `anchors --retired --json` answered byte for byte as `--json` and the sweep called a
    correct flag swallowed. `origin --why` and `weight --records` did not answer at all —
    "no history to resolve against", which the pair test read as a refusal two subjects made.

    So the state is here rather than exempted: one commit with §I.3 in it, one that takes the
    heading out. Nothing gives an address back, which is the whole of what `--retired` lists.

    **And a message under one of them** (RK1554). RK1489 gave this a history and not a
    message: both commits were a subject with no body, so `origin --why` — which adds each
    commit's body under the rows — answered identically to `origin` on the terminal too, for a
    reason that is nothing to do with the flag. It went unnoticed because that one is closed
    twice over, withheld from the served tool and declared a second subject beside `--json`,
    so neither sweep asks it anything; the next flag about a commit body will have neither.

    **One of the two and never both**, which is this fixture's whole value: its commits differ
    in named ways, and a body on each would take a difference back out to add one. The one that
    carries it is the **first**, because `--why` prints the *shipping* commit's message and the
    ledger's one shipped line is recorded there.
    """
    _write(
        root,
        "roadkeep.toml",
        'prefix = "RK"\nref_scheme = "outline"\n[files]\n'
        'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n',
    )
    _write(root, "ROADMAP.md", ROADMAP)
    _write(root, "CHANGELOG.md", LEDGER)
    _write(root, "IMPROVEMENTS.md", PROSE + SHIPPED)
    git_init(root)
    git_commit(root, PROPOSING_MESSAGE)
    _write(root, "IMPROVEMENTS.md", PROSE)
    git_commit(root, "ship the line that pointed at I.3")
    return root


@pytest.fixture(scope="session")
def _origin(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Built once and copied per test, because it is now nine processes and not four writes.

    The pair sweep's calls are read-only by construction — `_WRITES` is the list of what is
    kept out for exactly that reason — and the served sweep's are not (RK1517): five of the
    eighteen tools write, so the copy that was about isolating a `.git` is now also what keeps
    a `restate` out of every later row. Each of those calls takes a copy of its own besides,
    the two forms of one flag being two trees.
    """
    return _build(tmp_path_factory.mktemp("pairs"))


@pytest.fixture
def project(_origin: Path, tmp_path: Path) -> Path:
    root = tmp_path / "project"
    shutil.copytree(_origin, root)
    return root


#: What a verb needs before its flags mean anything: the positional it declares required. One
#: table for both halves of the sweep (RK1147) — they read it for different reasons, one to
#: parse and one to run, and two copies is how a verb ends up covered by only one of them.
#: `adopt` arrived here by being declared `reads_only`, which it always was, and its file is
#: the project's own roadmap: a real corpus this fixture already writes, so the pair runs
#: against an answer rather than against argparse's missing-argument exit.
NEEDS = {
    "claim": ["RK2"],
    "show": ["RK1"],
    # **A line this fixture shipped** (RK1554), which RK1 is not: `origin --why` prints the
    # *shipping* commit's message, so an id that only ever got proposed is one that flag can
    # never fire on — the id was as much of why it read as inert as the missing body was.
    "origin": ["RK9"],
    "adopt": ["docs/ROADMAP.md"],
    # The label and the sentence, for `_SUPPLIED`'s reason one sweep over (RK1624): the block
    # is required and `--open` widens what `--near` ranks, so a call missing either is argparse
    # refusing before a flag is read rather than a pair being separated.
    "delivered": ["A", "--near", "A symptom that is plainly long enough"],
}


def run(root: Path, command: str, *flags: str) -> tuple[int, str]:
    """One call, with its stdout — which is the thing a swallowed flag leaves identical."""
    out = io.StringIO()
    argv = ["-C", str(root), command, *NEEDS.get(command, []), *flags]
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = main(argv)
        except SystemExit as leaving:  # argparse refuses before a handler exists
            code = leaving.code if isinstance(leaving.code, int) else 2
    return code, out.getvalue()


def subcommands() -> dict[str, argparse.ArgumentParser]:
    """Every verb, off the real parser — the one reader this file has of what is declared."""
    return [one for one in build_parser()._actions if getattr(one, "choices", None)][0].choices  # noqa: SLF001


def separated(command: str, first: str, second: str) -> bool:
    """Whether this verb's own declaration says these two flags are two answers (RK489).

    Read off `subjects`, which is what `dispatch` reads: a prediction taken from anywhere else
    would be this file holding a second opinion about the rule it is checking.
    """
    parser = subcommands()[command]
    groups = parser.get_default("subjects") or ()
    held = [
        {option for _, option, _ in group.flags}
        for group in groups
    ]
    return any(
        first in one and second in other
        for one in held
        for other in held
        if one is not other
    )


def pairs() -> list[tuple[str, str, str]]:
    """Every two boolean flags one read-only command takes, off the real parser."""
    found = []
    for name, parser in sorted(subcommands().items()):
        if not parser.get_default("reads_only") or name in _UNREACHED:
            continue
        flags = [
            one.option_strings[0]
            for one in parser._actions  # noqa: SLF001
            if isinstance(one, argparse._StoreTrueAction)  # noqa: SLF001
            and (name, one.option_strings[0]) not in _WRITES
        ]
        found += [(name, first, second) for first, second in itertools.combinations(flags, 2)]
    return found


@pytest.mark.parametrize("command, first, second", pairs())
def test_a_pair_is_refused_or_answers_as_neither_half(project, command, first, second):
    """The defect this catches, stated as the shape it leaves: exit 0, and an answer that is
    one half's to the character. Both halves are run against the same fixture, so what
    separates a composed pair from a swallowed one is only whether the output moved."""
    root = project
    code, both = run(root, command, first, second)
    if code != 0:
        # **Only where the declaration is what produced it** (RK1489). A non-zero exit used to
        # end this test with "refused, which is two subjects saying so", and nine of these
        # exits were nothing of the kind: no `[non_goals]` table, no deferred store, a `merge`
        # with a finding. That is the fixture's reach reported as a result, which is the same
        # mistake one state further than the one this task was filed for.
        assert separated(command, first, second) or (command, first, second) in _UNMEASURED, (
            f"`{command} {first} {second}` exited {code} and the declaration does not "
            f"separate the two: this is the fixture failing to hold what the pair is about, "
            f"not a refusal — give it that state, or name the pair in _UNMEASURED with why"
        )
        return
    _, alone_first = run(root, command, first)
    _, alone_second = run(root, command, second)
    if alone_first == alone_second == both:
        assert (command, first, second) in _IDEMPOTENT, (
            f"`{command} {first} {second}` answers as both halves and no reason is stated: "
            f"add it to _IDEMPOTENT with why, or the pair is doing nothing"
        )
        return
    dropped = first if both == alone_second else second if both == alone_first else ""
    assert not dropped, (
        f"`{command} {first} {second}` answered exactly as `{command} "
        f"{second if dropped == first else first}` alone: {dropped} was swallowed"
    )


@pytest.mark.parametrize("command, first, second", pairs())
def test_the_dispatcher_refuses_exactly_the_pairs_a_verb_declares(command, first, second):
    """The property RK489 turned this sweep into, asked of the dispatcher and not of a run.

    An exit code cannot answer it: five of these pairs exit 2 for reasons that are nothing to
    do with the flags — no `[non_goals]` table, no git history, no live claim — so a test
    reading the code alone would call each of those a declared refusal. `_one_answer` is the
    whole rule and takes a parsed namespace, so this asks it directly: refused **iff** the
    verb's own `answers(...)` puts the two flags in different groups.

    Which is what makes the declaration complete rather than merely present. A verb that grows
    a sixth subject and forgets to declare it fails here on the pair it swallows, in the file
    that has always been the one able to see the class."""
    parser = build_parser()
    args = parser.parse_args([command, *NEEDS.get(command, []), first, second])
    refused = _one_answer(args) is not None
    assert refused == separated(command, first, second), (
        f"`{command} {first} {second}`: the dispatcher "
        f"{'refuses' if refused else 'allows'} a pair the declaration "
        f"{'does not separate' if refused else 'separates'}"
    )


def test_the_sweep_reaches_every_read_that_takes_two(tmp_path):
    """The count is the claim: a command that stops being read-only, or a flag that stops
    being boolean, silently leaves this sweep — and a sweep nobody can size is one that can
    go empty without saying so."""
    found = pairs()
    assert len(found) >= 12, f"only {len(found)} pairs reached: {found}"
    covered = {command for command, _, _ in found}
    assert {"anchors", "budget", "list", "show", "brief"} <= covered
    assert covered.isdisjoint(_UNREACHED)
    # And at least one of them is a pair a declaration separates, so the prediction above is
    # exercised rather than being an `if` nothing enters (RK489).
    assert any(separated(*one) for one in found), found


def test_the_fixture_holds_the_history_the_flags_are_about(project):
    """RK1489's deliverable, asserted rather than assumed. Two commits and a shipped heading
    are three lines of fixture that nothing else here reads, so without this they rot quietly
    and the sweep goes back to measuring its own reach — which is the defect, not a symptom of
    it: `anchors --retired` was reported swallowed for want of exactly this state."""
    wide, retired = run(project, "anchors")[1], run(project, "anchors", "--retired")[1]
    assert "I.3" in retired, retired
    assert "I.3" not in wide, wide
    # And the two verbs that could not answer at all, which is what a sweep reads as a refusal.
    # Through `run`, so the id comes off `NEEDS` exactly as it does for every pair above.
    assert run(project, "origin")[0] == 0
    assert run(project, "weight", "--records")[0] == 0


def test_what_the_sweep_does_not_run_says_why(tmp_path):
    """Every exclusion is named with a reason, so widening any of them is a decision somebody
    writes down rather than a filter that quietly grew."""
    assert all(reason for reason in _UNREACHED.values())
    assert all(reason for reason in _IDEMPOTENT.values())
    # The third list (RK1489), held to the same rule and to one more: a row here is a pair the
    # fixture cannot hold, so it may not name a pair the declaration already separates — that
    # would be an exemption standing in front of a working refusal.
    assert all(reason for reason in _UNMEASURED.values())
    assert not [one for one in _UNMEASURED if separated(*one)], sorted(_UNMEASURED)
    assert set(_UNMEASURED) <= set(pairs()), sorted(set(_UNMEASURED) - set(pairs()))
    # And the sweep's own finding: nothing needed an exception. `lint --quiet --json` and
    # `list --ids --json` were the two it caught, and both are refused now rather than listed
    # here — a flag shaping one form beside another form is RK465's rule, not an exemption.
    assert _IDEMPOTENT == {}
    declared = subcommands()
    for command, flag in _WRITES:
        assert command in declared, command
        assert flag in {
            one for action in declared[command]._actions for one in action.option_strings
        }, f"{command} no longer takes {flag}"


def test_every_declared_answer_names_a_flag_its_verb_actually_has():
    """RK489's build-time half, stated as a test as well: `answers` and `narrows` resolve a
    dest through the subparser and raise where it has none, so a declaration naming a flag
    that was renamed fails when the parser is *constructed*. This asserts what that buys —
    every group is non-empty, every subject says what it answers, and every narrowing flag
    names a subject the same verb declares."""
    seen = 0
    for name, parser in sorted(subcommands().items()):
        options = {
            one for action in parser._actions for one in action.option_strings  # noqa: SLF001
        }
        for group in parser.get_default("subjects") or ():
            seen += 1
            assert group.flags, name
            assert group.what, (name, group.flags)
            for _, option, _ in group.flags:
                assert option in options, (name, option)
        subjects = {
            option
            for group in parser.get_default("subjects") or ()
            for _, option, _ in group.flags
        }
        for (_, flag, _), (_, subject, _) in parser.get_default("narrowing") or ():
            assert flag in options, (name, flag)
            assert subject in subjects, (name, flag, subject)
    # Five verbs declare between them, and the count is the claim: a declaration deleted with
    # the branch it replaced would leave this file measuring nothing.
    assert seen >= 12, seen


# -- the cadences a table now counts (RK1637) ----------------------------------

#: Every cadence `cost` prices: the flag that reads it, and **when what it measures is paid**.
#: The population, held total against the parser below — which is the whole of this task. Five
#: tasks each filed a subject as *the Nth cadence, and the one nothing counted*, each correctly
#: and none able to say how many were left, because the count lived in prose in five docstrings
#: and in a sentence a reader incremented by hand. `SITES` says what every composed command is
#: and `USES` what every caller of `Part` holds; this is the same shape about the thing those
#: tables are for.
CADENCES = {
    "--tools": "once at connect",
    "--brief": "once per read",
    "--session": "once at connect and once per turn",
    "--skill": "once per turn that loads it",
    "--deny": "once per refused write",
    "--notes": "once per run of the gate",
    "--near": "once per `add`",
}

#: The three of them paid **per write**, which is the group RK1491, RK1524 and RK1582 each
#: argued into existence one at a time. Named as a subset rather than as a fourth table: what
#: makes them one group is prose composed by a write rather than a state somebody reads.
PER_WRITE = ("--deny", "--notes", "--near")


def _cadences() -> dict[str, str]:
    """What `cost` declares, off the real parser — the one reader this file has."""
    return {
        one.option: one.trigger
        for one in subcommands()["cost"].get_default("subjects") or ()
    }


def test_every_cadence_cost_prices_is_one_this_table_counts():
    """RK1637. Total against the declaration, so the eighth subject is a red here with one
    question in it: what is it paid per. That question had no place to be asked before — the
    trigger is what makes the set a set, and without it a subject was a flag with a sentence
    beside it that happened to mention a cadence."""
    assert _cadences() == CADENCES


def test_no_two_cadences_share_a_trigger():
    """The property the field exists for: two subjects paid at the same moment are one cadence
    counted twice, which is the arithmetic `--session` refuses to do with its own two figures.
    Checkable only once the trigger is declared rather than described."""
    triggers = list(_cadences().values())
    assert len(triggers) == len(set(triggers)), sorted(triggers)


def test_every_subject_this_verb_dispatches_is_declared_with_a_cadence():
    """Both directions, because either alone is green on the state RK1637 was filed from: a
    branch in the handler nothing declared, or a declaration nothing dispatches. Read off the
    handler's own source, so a subject added to one and not the other is the red.

    Not a limit on the total, deliberately (RK1095): different surfaces are paid by different
    callers and a sum charges one session for all of them."""
    source = inspect.getsource(_cost_handler)
    dispatched = {
        f"--{one}"
        for one in re.findall(r"args\.(\w+)", source)
        if one not in {"subjects", "json"}
    }
    assert dispatched == set(CADENCES)
    # And the per-write group is the three it is: a fourth is the next task's argument, not a
    # row somebody quietly adds to a tuple.
    assert set(PER_WRITE) <= set(CADENCES)
    assert len(PER_WRITE) == 3, PER_WRITE


# -- the flag one flag alone, over the transport that appends --json (RK1517) ---

#: What a served tool needs before its own flag can mean anything, by **dest** — `NEEDS`'
#: rule one surface over, and by dest rather than as argv because this half composes the call
#: through `serving.argv` and never by hand. Only the tools whose parser declares a required
#: positional appear: everything else takes its flag and nothing more.
_SUPPLIED: dict[str, dict[str, object]] = {
    "show": {"id": "RK1"},
    "block drop": {"label": "B"},
    "block merge": {"label": "A"},
    "restate": {"id": "RK1", "symptom": "A restated symptom, plainly long enough"},
    "priority add": {"token": "RK1"},
    # The label this verb is *about*, and a sentence to rank against (RK1624): `--open` widens
    # the corpus `--near` orders, so without one both forms refuse and the sweep would be
    # reading its own reach rather than whether the flag reaches anything.
    "delivered": {"block": "A", "near": "A symptom that is plainly long enough"},
}

#: Served booleans whose two forms **both** refuse here, with the state each wants. The same
#: rule as `_UNMEASURED` one arity up: a fixture that cannot reach a flag says so, because the
#: alternative is reading its own reach as a result. Neither of these is about the transport —
#: `block drop` wants a label with nothing filed under it and `block merge` wants a label
#: written twice, and this fixture is one project with one well-formed Block A.
_WITHOUT_STATE: dict[tuple[str, str], str] = {
    ("block drop", "--prose"): "no empty block here: every label this project declares has "
    "work filed under it, so the verb refuses by name before the flag is read",
    ("block merge", "--prose"): "no duplicated heading here, which is the one state this "
    "verb exists for and the one a well-formed fixture does not have",
}


def _subparser(command: str) -> argparse.ArgumentParser:
    """The parser for a command path, nested or not — `serving._subparser`'s descent."""
    parser = subcommands()[command.split()[0]]
    for token in command.split()[1:]:
        parser = next(
            one.choices[token]
            for one in parser._actions  # noqa: SLF001
            if isinstance(one, argparse._SubParsersAction)  # noqa: SLF001
        )
    return parser


def served() -> list[tuple[str, str, str]]:
    """Every boolean flag this surface exposes, as (tool, command, flag) (RK1517).

    Off `TOOLS` and the real parser, never a list here: a flag added to a served command
    reaches this sweep by being exposed, which is the population the question is about.

    `unconditional` and not :meth:`Tool.exposed`, which is the one place the two differ and a
    difference this sweep can state rather than assume: a conditional argument is opened by a
    project whose config makes it the only way to spell a legal id (RK111), so it is a *value*
    and never a boolean — asserted below, so the day one is a boolean this population is a red
    rather than a silence. Reading it that way also keeps the enumeration free of a config,
    which is what lets it run at collection.
    """
    from roadkeep.serving import TOOLS

    found = []
    for tool in TOOLS:
        found += [
            (tool.named or tool.command, tool.command, one.option_strings[0])
            for one in _subparser(tool.command)._actions  # noqa: SLF001
            if isinstance(one, argparse._StoreTrueAction)  # noqa: SLF001
            and one.dest in tool.unconditional
        ]
    return found


def _tool(name: str):
    """The served tool this row is about, by the name a client calls it."""
    from roadkeep.serving import TOOLS

    return next(one for one in TOOLS if (one.named or one.command) == name)


def _dest(command: str, flag: str) -> str:
    """The dest behind a flag, off the parser — the key `serving.argv` takes."""
    return next(
        one.dest
        for one in _subparser(command)._actions  # noqa: SLF001
        if flag in one.option_strings
    )


def _copied(root: Path, name: str) -> Path:
    """A second tree beside this test's own, for the call that writes."""
    into = root.parent / name
    shutil.copytree(root, into)
    return into


def _ran(root: Path, args: list[str]) -> tuple[int, str]:
    """One call with an argv composed elsewhere, and its stdout (`run`'s other half)."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = main(["-C", str(root), *args])
        except SystemExit as leaving:  # argparse refuses before a handler exists
            code = leaving.code if isinstance(leaving.code, int) else 2
    return code, out.getvalue()


@pytest.mark.parametrize("name, command, flag", served())
def test_a_served_boolean_is_not_made_inert_by_the_transport(project, name, command, flag):
    """RK1517. `serving` appends `--json` to every call it makes, so a flag whose whole effect
    is on the terminal rendering shapes nothing over this transport — `origin --why` was one,
    the payload carrying each commit's `reasoning` either way, and an agent setting it read an
    unchanged answer as the one it had asked for.

    The signature is the pair sweep's one arity down: the call the **server** composes, run
    with the flag and without, and an answer identical both ways is a flag this surface cannot
    honour. Both argvs come from `serving.argv`, so what is measured is what the transport
    sends — `--json` and the tool's `always` included — and never a line assembled here.

    A refusal on one side and an answer on the other is a flag that shaped the call, which is
    the whole question: what is asked is whether the flag reaches anything, not whether the
    answer is right. Refused on **both** sides is the fixture's reach, named in
    :data:`_WITHOUT_STATE` for `_UNMEASURED`'s reason.
    """
    from roadkeep.config import Config
    from roadkeep.serving import argv

    tool = _tool(name)
    config = Config.discover(project)
    supplied = _SUPPLIED.get(command, {})
    dest = _dest(command, flag)
    # Two copies and never one tree, because five of these tools write: what the flag did to
    # the file is not what is being read, and the second call on a changed tree would answer
    # differently for a reason that has nothing to do with the flag.
    plain = _ran(_copied(project, "plain"), argv(tool, dict(supplied), config))
    with_flag = _ran(_copied(project, "flag"), argv(tool, {**supplied, dest: True}, config))
    if plain[0] and with_flag[0]:
        assert (command, flag) in _WITHOUT_STATE, (
            f"`{command} {flag}` refuses both with the flag and without on this fixture: "
            f"that is this sweep's reach and not a reading — give it the state it wants, "
            f"or name it in _WITHOUT_STATE with why"
        )
        return
    assert plain != with_flag, (
        f"`{command} {flag}` is served and answers identically with the flag and without it, "
        f"over a transport that appends --json: the flag shapes the terminal form only, so "
        f"either it belongs in `cli.withheld` or the payload has to carry what it composes"
    )


def test_the_sweep_reaches_every_boolean_this_surface_serves():
    """The count is the claim, as it is one arity up: a flag that stops being served, or a
    tool withdrawn, silently leaves this sweep — and eighteen is the number RK1517 was filed
    against, so a run measuring five would be a green nobody could size."""
    found = served()
    assert len(found) >= 16, f"only {len(found)} served booleans reached: {found}"
    assert {"budget", "anchors", "show", "engines", "cost"} <= {one for _, one, _ in found}
    # The two tools that are one command with a flag always passed (RK150) are two rows here,
    # because they are two calls: `claim` sends `--claim` and `brief` does not.
    assert ("claim", "brief", "--designed") in found
    assert ("brief", "brief", "--designed") in found


def test_a_conditional_argument_is_never_one_of_these():
    """What `served()` reads `unconditional` on, asserted rather than assumed: a conditional
    argument exists because a project's config makes it the only way to spell a legal id
    (RK111), so it is a value. The day one is a boolean, this population is quietly short by
    one and nothing else in this file would say so."""
    from roadkeep.serving import TOOLS

    for tool in TOOLS:
        booleans = {
            one.dest
            for one in _subparser(tool.command)._actions  # noqa: SLF001
            if isinstance(one, argparse._StoreTrueAction)  # noqa: SLF001
        }
        assert not booleans & set(tool.conditional), (tool.command, booleans)


def test_what_the_served_sweep_cannot_reach_says_why():
    """`_UNMEASURED`'s rule at the other arity, and the second half is what keeps it honest: a
    row here claims *both* forms refuse, so it may not name a flag this fixture in fact
    answers — that would be an exemption standing in front of a working reading."""
    assert all(reason for reason in _WITHOUT_STATE.values())
    rows = {(command, flag) for _, command, flag in served()}
    assert set(_WITHOUT_STATE) <= rows, sorted(set(_WITHOUT_STATE) - rows)
    # And every one of them is a *write*, which is the honest shape of this list: what the
    # read-only tools want, this fixture has. A read landing here is a fixture to widen.
    for command, _ in _WITHOUT_STATE:
        assert not _subparser(command).get_default("reads_only"), command


def test_the_defect_this_was_filed_from_is_closed_at_both_ends(project):
    """`origin --why` is the flag RK1489 found and RK1517 was filed from, and it cannot be
    exhibited any more — which is worth asserting rather than assuming, because it is the
    reason the sweep above is prospective and finds nothing today.

    Two writes closed it and either would have. It is withheld from the tool, so no served
    argv carries it; and `--why` and `--json` are declared **two subjects**, so the call the
    server would compose is refused outright rather than answered identically. The flag itself
    was never broken: on the terminal form it shapes exactly what it says it does.
    """
    from roadkeep.config import Config
    from roadkeep.serving import Tool, argv, withheld

    assert "why" in withheld().get("origin", {}), "the withholding RK1489 wrote"
    served_again = Tool("origin", ("id", "why"))
    config = Config.discover(project)
    both = argv(served_again, {"id": "RK1", "why": True}, config)
    assert both == ["origin", "RK1", "--why", "--json"]
    assert _ran(project, both)[0] == 2, "two subjects, so the composed call never answers"
    # **And on the terminal form it shapes something, which is now checkable** (RK1554). This
    # read the two as identical and said so: `--why` adds each commit's message *body* under
    # the rows, and both commits were a subject and nothing else — so the flag moved nothing
    # for a reason that was the fixture. One of them has a body now, and the assertion is the
    # one that was wanted all along.
    assert run(project, "origin")[1] != run(project, "origin", "--why")[1]
