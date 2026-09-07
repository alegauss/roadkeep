"""The commands this tool composes, run rather than matched (RK1209).

Four tasks found the same defect and no test found any of them, because every test that
covered a composed command asserted the *sentence was printed*. Matching a composed command
tests the composer against itself: `test_the_command_offers_a_follow_up_that_runs` was named
for the claim it did not make, and stayed green for as long as the command it described
refused.

Two properties, and the first is the one that lasts. The **census** is total, so a site added
tomorrow is a red here until somebody says whether it is exercised; and what is exercised is
*executed*, through one instrument rather than a fourth hand-written copy of it.

The honest state of the second was written down in `composing.SITES` rather than implied:
thirty-odd sites had never been run, and this file is where that stopped being invisible.
Every one of them runs now, or is a decision that says why (RK1599).
"""

from __future__ import annotations

import shlex
from pathlib import Path

import pytest

from composing import (
    FILLS,
    FOREIGN,
    SITES,
    STATES,
    census,
    commanded,
    commands,
    filled,
    inconsistent,
    loose,
    runs,
    spoken,
    supplied,
    unreached,
)
from surface import modules
from conftest import git_commit, git_init
from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, build_parser, main
from roadkeep.config import Config
from roadkeep.linting import Finding, lint
from roadkeep.provenance import invocation, joined, quoted
from roadkeep.remedying import BLANK, codes, remedy


# -- the census, which is the deliverable -------------------------------------


def test_every_site_that_composes_a_command_is_accounted_for():
    """`invocation()` is the one function every composed command goes through, so the
    population is enumerable — and what this adds is a reason per site. An exemption nobody
    can see reads exactly like a rule being kept."""
    declared = {one.where for one in SITES}
    found = set(census())
    assert declared == found, {
        "composes a command, unaccounted for": sorted(found - declared),
        "accounted for, composes nothing": sorted(declared - found),
    }


def test_every_row_states_one_of_the_three_and_carries_a_reason_where_it_must():
    """`run` is coverage; `unreached` is a work-list; `deliberate` is a decision. Kept apart
    because a table spelling all three as "no" would hide which is which."""
    seen = [one.where for one in SITES]
    assert len(seen) == len(set(seen)), seen
    for one in SITES:
        assert one.state in STATES, one
        if one.state == "run":
            assert not one.why, f"{one.where}: coverage needs no excuse"
        else:
            assert one.why, f"{one.where}: not run, and nothing says why"


def test_every_site_is_run_or_deliberate_and_the_work_list_is_empty():
    """RK1599, and the sentence the emptied row asked for. This began as *six are executed and
    thirty are a work-list*, which was the finding four separate tasks had each met one
    instance of; the work-list is now gone, and what replaces the count is the claim it was
    counting towards.

    `unreached` stays a state a row may take. A site added tomorrow is a red here until
    somebody says which of the three it is, and *not run and here is the state it wants* has
    to remain sayable — what is asserted is that no row is standing on it today."""
    working = [one.where for one in SITES if one.state == "unreached"]
    assert not working, working
    assert [one.where for one in SITES if one.state not in ("run", "deliberate")] == []
    # And coverage is the majority of it, which the shape alone would not say: a table where
    # every row is `deliberate` passes the line above and executes nothing.
    assert len([one for one in SITES if one.state == "run"]) > len(SITES) / 2


# -- the instrument -----------------------------------------------------------


def test_a_command_is_found_by_its_backticks_and_never_by_a_line_prefix():
    """RK1220's finding, taken at the start rather than after: this tool spells its own errors
    `roadkeep: refused, …`, so wherever the console script is installed a prefix scan reads
    the preamble as a step — and the suite is green or red by whether somebody ran `pip
    install`."""
    said = (
        f"{invocation()}: refused, nothing written:\n"
        f"  ref: filing here is `{invocation()} block add Z --title \"<its title>\"`, "
        f"then `{invocation()} add --block Z …`"
    )
    found = commands(said)
    assert [one[0] for one in found] == ["block", "add"], found
    # The preamble begins with the invocation and is not a command; the backticks are what
    # tell them apart, and nothing about the sentence changes when a PATH does.
    assert all("refused," not in one for argv in found for one in argv)


def test_a_name_the_tool_is_a_prefix_of_is_not_a_command(tmp_path):
    """RK1498. `startswith` alone read `` `roadkeep.toml` `` as this tool plus the verb
    `.toml`, so every message quoting the config composed a command — RK1220's own failure one
    step in, and invisible until the sweep was pointed at a message that names the file.

    A verb is a separate word, which is the whole of the rule: the character after the prefix
    has to be whitespace or the span has to end there."""
    prefix = invocation()
    found = commands(
        f"declares no `{prefix}.toml`, so `{prefix} init` comes first — "
        f"the launcher is `{prefix}-launch.py`"
    )
    assert [one[0] for one in found] == ["init"], found


def test_a_placeholder_is_filled_and_never_stripped():
    """`add --why …` with the flag removed is a different command, refused for a reason this
    sweep is not about (L4): the words are the author's, so the harness supplies one rather
    than pretending the field was optional."""
    assert filled(["block", "add", "Z", "--title", "<its title>"])[-1] != "<its title>"
    assert filled(["block", "add", "Z", "--title", "<its title>"])[-2] == "--title"
    # A bare ellipsis stands for "and the rest of a call", with no flag in front to fill
    # from — and only where the caller says so (RK1339): dropping it is right for a command
    # read out of refusal prose and wrong for a remedy door, where the blank is a field.
    assert filled(["add", "--block", "Z", "…"], continuation=True) == ["add", "--block", "Z"]
    assert filled(["add", "--block", "Z", "…"])[-1] == "<unfilled positional>"


# -- what is executed ---------------------------------------------------------


OUTLINED = (
    'prefix = "TT"\nref_scheme = "outline"\n[files]\nroadmap = "ROADMAP.md"\n'
    'changelog = "CHANGELOG.md"\nimprovements = "IMPROVEMENTS.md"\n'
)


def outlined(tmp_path: Path) -> Path:
    """A project on the outline scheme, which is where a composed address can be wrong.

    Under `ref_scheme = "id"` the anchor *is* the id, so a command composed from either field
    lands and the two cannot be told apart — which is exactly why RK1206 was invisible on this
    repository and had to be met on somebody else's.
    """
    (tmp_path / "roadkeep.toml").write_text(OUTLINED, encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text("# Roadmap\n\n## Block A\n\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Shipped\n\n## Block A\n", encoding="utf-8")
    (tmp_path / "IMPROVEMENTS.md").write_text("# Improvements\n\n## Block A\n", encoding="utf-8")
    return tmp_path


@pytest.mark.parametrize(
    "families, first",
    [
        # An outline with nothing in it: the refusal declines to name an address and sends the
        # caller to the read that would (RK1211), which is itself a composed command.
        ("", ["anchors"]),
        # And one with a family, where the refusal names the whole stair — the family, the
        # design, the retry — because a fresh top-level exists nowhere by construction.
        ("### I A family\n\nProse enough to matter.\n", ["section", "add"]),
    ],
    ids=["empty-outline", "a-family-exists"],
)
def test_the_path_a_refusal_names_runs_as_printed(tmp_path, capsys, families, first):
    """RK1198's finding, through the shared instrument instead of a fourth copy of it: an `add`
    into a block whose prose has not started is refused with the whole path, and the value of
    printing it is that it runs, in the order printed.

    Both shapes, because which one a project is in changes what is composed and each was a
    separate discovery: an empty outline has no family to read a system off (RK1211) and one
    with a family has a stair whose first step nobody sees coming (RK1198).
    """
    root = outlined(tmp_path)
    if families:
        (root / "IMPROVEMENTS.md").write_text(
            f"# Improvements\n\n## Block A\n\n{families}", encoding="utf-8"
        )
    code = main([
        "-C", str(root), "add", "--block", "A",
        "--symptom", "A symptom plainly long enough to read",
        "--why", "Because of a reason.",
    ])
    assert code == EXIT_USAGE
    said = capsys.readouterr().err
    # Every command it composed was accepted, which `runs` asserts step by step: what is
    # returned is the sequence, so the shape can be asserted as well as the outcome.
    ran = runs(root, said)
    assert ran, said
    assert ran[0][: len(first)] == first, ran


def test_every_door_the_gate_offers_on_this_project_lands(tmp_path, capsys):
    """The doors, executed. `test_remedying` asserts a `run` remedy carries no placeholder and
    parses as a subcommand; what it cannot say is that the call is *accepted*, which is the
    difference RK1203 and RK1206 were each one instance of.

    A `compose` door carries the blank by design (L4), so it is filled here and run like the
    rest: what is being tested is the argv around the prose, not the prose.
    """
    root = outlined(tmp_path)
    # A line pointing at a section that is not there, with its family opened — so the door is
    # about the address and not about the stair above it.
    (root / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A\n\n### I A family\n\nProse enough to matter.\n",
        encoding="utf-8",
    )
    (root / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A\n\n"
        "- 📋 **TT1** (deps: —) **A symptom** — Because of a reason. → §I.1\n",
        encoding="utf-8",
    )
    config = Config.discover(root)
    findings = lint(config).findings
    assert findings, "the fixture stopped being defective, so this asserts nothing"

    for found in findings:
        rule = remedy(found, config)
        if rule is None or rule.kind not in ("run", "fix", "compose"):
            continue
        for door in rule.doors:
            argv = supplied(filled(list(door.argv)))
            assert all(not one.startswith("<unfilled ") for one in argv), argv
            assert main(["-C", str(root), *argv]) == EXIT_OK, (found.code, argv)
            capsys.readouterr()
    # And the gate is clean, which is the only proof the doors were the right ones.
    assert lint(Config.discover(root)).clean, [str(one) for one in lint(Config.discover(root)).findings]


def test_the_role_a_decision_needs_is_opened_by_the_command_the_refusal_names(tmp_path, capsys):
    """RK1269. `ship --decides` refuses where the project declares no decisions file, and the
    remedy is a role rather than a field — so the whole value of printing it is that it runs
    and the call that was refused then lands, in that order."""
    root = outlined(tmp_path)
    (root / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A\n\n### I A family\n\nProse enough to matter.\n",
        encoding="utf-8",
    )
    (root / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A\n\n"
        "- 📋 **TT1** (deps: —) **A symptom** — Because of a reason. → §I.1\n",
        encoding="utf-8",
    )
    shipping = [
        "-C", str(root), "ship", "TT1",
        "--why", "The symptom no longer happens.",
        "--decides", "The store is the repository: no database and no service.",
        # The address the record's body keeps, which this project numbers for itself
        # (RK1363) — named by the same refusal, so the retry is one call and not two.
        "--decides-ref", "II",
    ]
    assert main(shipping) == EXIT_USAGE
    said = capsys.readouterr().err
    ran = runs(root, said)
    assert ran and ran[0][:2] == ["declare", "decisions"], said
    # The whole path in one message and never a stair per call: an outline project is refused
    # twice for two facts, so the first refusal names the second one's flag too.
    assert "--decides-ref" in said
    # And the refused call now lands, which is the half a matched sentence cannot claim.
    assert main(shipping) == EXIT_OK
    capsys.readouterr()
    assert "The store is the repository" in (root / "docs" / "DECISIONS.md").read_text(
        encoding="utf-8"
    )
    # The pointer that ship wrote resolves once the body is there, which is `add --ref`'s own
    # two-step and the same `ref.unresolved` in between.
    assert main([
        "-C", str(root), "section", "add", "II", "--role", "decisions",
        "--title", "Why the repository", "--body", "A service was weighed and rejected.",
    ]) == EXIT_OK
    capsys.readouterr()
    assert lint(Config.discover(root)).clean


# -- the doors of a departure that cannot happen (RK1498) ---------------------

#: A governed project on the id scheme, whole: a pointer that resolves and a design under it,
#: so a door refused for the *fixture* — `ref.missing`, an unopened family — is not read as a
#: door that refuses. RK1475 published one that would have refused and the rule it broke is
#: `removable`'s own; what holds it is running the command, against a state that is otherwise
#: clean.
WHOLE = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    'improvements = "IMPROVEMENTS.md"\ndeferred = "DEFERRED.md"\n'
)
LINE = (
    "- {marker} **RK1** (deps: —) **A symptom worth reading here** — "
    "Because of a reason. → §RK1\n"
)


def departing(tmp_path: Path, *, marker: str = "📋", **files: str) -> Path:
    """One open line with its design, and whichever other files a refusal needs."""
    written = {
        "roadkeep.toml": WHOLE,
        "ROADMAP.md": "# Roadmap\n\n## Block A\n\n" + LINE.format(marker=marker),
        "CHANGELOG.md": "# Shipped\n\n## Block A\n",
        "IMPROVEMENTS.md": (
            "# Improvements\n\n## Block A\n\n### §RK1 A design\n\n"
            "The reasoning the line has no room for.\n"
        ),
        "DEFERRED.md": "# Deferred\n\n## Block A\n",
        **files,
    }
    for name, body in written.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


#: A ledger holding RK1, which is what makes a second departure a refusal.
def _recorded(symptom: str = "A symptom worth reading here") -> str:
    return f"# Shipped\n\n## Block A\n\n- ✅ **RK1** **{symptom}** — It works now.\n"


def test_the_door_a_line_the_ledger_already_records_names_runs(tmp_path, capsys):
    """RK1498. `runs()` executes each command a message composes and asserts the code it was
    told to expect, which is exactly the property RK1475 broke — and it was pointed at six of
    thirty-six composers. This is one of the thirty, and the state is two lines of fixture:
    an id the ledger holds whole, and a roadmap line still carrying ⏳ beside it — which is
    the one state that door is true of (RK1045), a `--part` against an entry with no half in
    it having nowhere else to go."""
    root = departing(tmp_path, marker="⏳", **{"CHANGELOG.md": _recorded()})
    assert main([
        "-C", str(root), "ship", "RK1", "--part", "the second half", "--why", "It works now."
    ]) == EXIT_USAGE
    said = capsys.readouterr().err
    # The closure, which is the one state that door is true of (RK1045): it runs, and what it
    # writes is the roadmap edit the interrupted transaction never made.
    ran = runs(root, said)
    assert ran and ran[0][:2] == ["ship", "RK1"], said
    capsys.readouterr()
    assert "RK1" not in (root / "ROADMAP.md").read_text(encoding="utf-8")


def test_the_door_a_paused_line_names_runs(tmp_path, capsys):
    # The store still says paused while the roadmap says open, so a departure would record the
    # work as gone against a copy that has not moved. The door removes the store's copy.
    root = departing(
        tmp_path,
        **{"DEFERRED.md": "# Deferred\n\n## Block A\n\n" + LINE.format(marker="⏸")},
    )
    assert main(["-C", str(root), "ship", "RK1", "--why", "It works now."]) == EXIT_USAGE
    said = capsys.readouterr().err
    ran = runs(root, said)
    assert ran and ran[0][:2] == ["resume", "RK1"], said
    capsys.readouterr()
    # And the call that was refused now lands, which is the half a matched sentence cannot say.
    assert main(["-C", str(root), "ship", "RK1", "--why", "It works now."]) == EXIT_OK


def test_the_door_two_tasks_sharing_an_id_names_runs(tmp_path, capsys):
    # Both files carry RK1 and describe different work, so they are two tasks with one address
    # rather than an interrupted transaction — and the door gives the open one its own.
    root = departing(tmp_path, **{"CHANGELOG.md": _recorded("A wholly different symptom")})
    assert main(["-C", str(root), "ship", "RK1"]) == EXIT_USAGE
    said = capsys.readouterr().err
    ran = runs(root, said)
    assert ran and ran[0][:2] == ["renumber", "RK1"], said


def test_the_offer_an_emptied_block_makes_runs(tmp_path, capsys):
    """The event line every write ends with, which names the heading a departure left behind.
    Composed on the closure path and never run: a `block drop` offered on a block that still
    holds a line is the shape RK1475 withdrew one instance of."""
    root = departing(tmp_path, **{"CHANGELOG.md": _recorded()})
    assert main(["-C", str(root), "ship", "RK1"]) == EXIT_OK
    said = capsys.readouterr().out
    ran = runs(root, said)
    assert ran and ran[-1][:2] == ["block", "drop"], said
    capsys.readouterr()
    assert "## Block A" not in (root / "ROADMAP.md").read_text(encoding="utf-8")


#: Defective lines whose remedy doors the sweep can already fill, each closing one code. The
#: fixture is a *table* and not one hand-made defect because that is the finding RK1338
#: measured: the door-execution test above builds a state producing exactly one finding, so
#: one row of the remedy table had its doors run, and RK1337 was a bug in one of the others.
#: What made the others unreachable was never the state — the suite constructs all 118 coded
#: findings — but the call: a door whose blank is `--ref` or `--dep` cannot be filled from a
#: constant, and one whose flag is `--why` or `--symptom` can. So these are the rows the
#: sweep can reach today, and the number is asserted below rather than described.
DEFECTIVE = (
    "- 📋 **TT2** (deps: —) **A symptom plainly long enough to read** — Because of a reason\n",
    "- 📋 **TT3** (deps: —) **A symptom plainly long enough to read** — One sentence. Two.\n",
    "- 📋 **TT4** (deps: —) **A symptom plainly long enough to read.** — Because of a reason.\n",
    "- 📋 **TT5** (deps: —) **"
    + "a symptom plainly long enough to read " * 4
    + "** — Because of a reason.\n",
    # Terminated as well as long: without the stop, `why.no-terminator` fires first and its
    # door rewrites the whole field, closing this one on the way past and costing the sweep a
    # code it looked like it had covered.
    "- 📋 **TT6** (deps: —) **A symptom plainly long enough to read** — "
    + "Because of a reason that goes on and on and on " * 5
    + "and it ends.\n",
)


def test_the_doors_close_the_gate_and_not_only_parse(tmp_path, capsys):
    """RK1338. `test_every_door_the_gate_offers_on_this_project_lands` runs the doors of one
    remedy row of 118: this project's gate is clean, so the doors it offers are the doors of
    a single hand-made defect. RK1337 was a bug in one of the other 117 — `section move`
    refuses an id-addressed section by construction — and it was found by hand.

    Converging rather than iterating a snapshot, which is the stronger claim and the one worth
    the fixture: each door is run against the state that produced its finding, and the loop
    ends when the gate is clean. A door that parses, is accepted and leaves the finding
    standing would pass an acceptance check and hang this one.
    """
    root = tmp_path
    # The id scheme, where the pointer is derived: an outline raises `ref.missing` on every
    # line, and that door takes an anchor no constant can supply — `filled` failing loudly
    # rather than guessing one is the behaviour this sweep depends on, not a gap in it.
    (root / "roadkeep.toml").write_text(
        'prefix = "TT"\n[files]\nroadmap = "ROADMAP.md"\n'
        'changelog = "CHANGELOG.md"\nimprovements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    (root / "CHANGELOG.md").write_text("# Shipped\n\n## Block A\n", encoding="utf-8")
    (root / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A\n\n"
        + "".join(
            f"### §TT{n} A design\n\nThe reasoning the line has no room for.\n\n"
            for n in range(2, 2 + len(DEFECTIVE))
        ),
        encoding="utf-8",
    )
    (root / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A\n\n"
        + "".join(
            f"{line.rstrip()} → §TT{n}\n"
            for n, line in enumerate(DEFECTIVE, start=2)
        ),
        encoding="utf-8",
    )
    assert lint(Config.discover(root)).findings, "the fixture stopped being defective"

    closed: list[str] = []
    for _ in range(len(DEFECTIVE) * 4):
        findings = lint(Config.discover(root)).findings
        runnable = [
            (f, r)
            for f in findings
            if (r := remedy(f, Config.discover(root))) is not None
            # Not `fix`: `lint --fix` exits 1 while any unfixed finding still stands, so a
            # mechanical row run mid-loop would be asserted against the wrong code. The
            # fixer closes the derived and has its own suite; these doors close the rest,
            # and the single `--fix` below is what the two halves meet at.
            and r.kind in ("run", "compose")
        ]
        if not runnable:
            break
        found, rule = runnable[0]
        for door in rule.doors:
            argv = supplied(filled(list(door.argv)))
            assert all(not one.startswith("<unfilled ") for one in argv), (found.code, argv)
            assert main(["-C", str(root), *argv]) == EXIT_OK, (found.code, argv)
            capsys.readouterr()
        closed.append(found.code)

    # What the doors left is the derived, which is the fixer's half by construction (RK16).
    main(["-C", str(root), "lint", "--fix"])
    capsys.readouterr()
    # The gate closing is the proof the doors were the right ones, as it is above.
    report = lint(Config.discover(root))
    assert report.clean, [str(one) for one in report.findings]
    # And the count, stated rather than described: this is where door coverage stands, so a
    # row whose door stops being reachable shows up as a number that fell rather than as a
    # code quietly skipped. Five, against the one the sweep above reaches.
    assert len(set(closed)) >= 5, sorted(set(closed))


#: Doors whose blank sits in a positional, which `filled` cannot supply from a table keyed by
#: flag (RK1339). Named rather than counted, for the reason the site table above is: a number
#: hides which, and which is the work-list. Each is a value the *finding* holds — the id, the
#: cited anchor, the label, the marker — so what closes them is doors carrying a substitution
#: like `{id}`, not more entries in `FILLS`.
POSITIONAL: dict[str, str] = {
    "priority.shape": "the id or the `Block X` the bullet should have addressed",
    "block.format": "the label, which is what the finding says cannot be rendered",
    "ref.dangling": "the cited anchor, which the finding names",
    "status.unknown": "the marker to set, which is a choice among those declared",
    "grammar.unreadable": "any one line, so the reader compares it with the rendering",
}


def test_a_door_the_sweep_cannot_fill_is_named_and_not_dropped():
    """RK1339. `filled` marks a blank it cannot fill as `<unfilled --flag>` so the sweep fails
    loudly rather than running a different command — and reached that branch only for a blank
    after a `--flag`. A blank in a positional fell to the drop, on a reading that belongs to
    `runs()`, which takes commands out of refusal prose and asks `abridged` which kind of
    ellipsis it has. A remedy door is never asked, so for a door the drop was unconditional:
    `block add … --title …` filled to `block add --title A title`.

    Total against the table, so a door added with a positional blank is a red here rather than
    a command that quietly runs without its argument."""
    found: dict[str, list[str]] = {}
    for code in codes():
        rule = remedy(Finding(code, "ROADMAP.md", "", 1, "RK1"))
        if rule is None:
            continue
        for door in rule.doors:
            if any(one == "<unfilled positional>" for one in filled(list(door.argv))):
                found.setdefault(code, []).append(" ".join(door.argv))
    assert sorted(found) == sorted(POSITIONAL), {
        "unnamed": sorted(set(found) - set(POSITIONAL)),
        "named and no longer positional": sorted(set(POSITIONAL) - set(found)),
    }
    # And a flag blank still fails loudly, which is the half that already held: this asserts
    # the new branch did not swallow the old one.
    assert filled(["amend", "RK1", "--ref", "…"]) == ["amend", "RK1", "--ref", "<unfilled --ref>"]
    # While a genuine continuation — the caller's own remaining call, in refusal prose — is
    # still dropped, which is the case the reading was right about.
    printed = ["add", "--block", "Z", "--ref", "XXI.1", "…"]
    assert filled(printed, continuation=True) == printed[:-1]


def test_no_two_rows_that_are_not_run_share_one_reason():
    """RK1532, widened by RK1599. Thirty-one rows carried one sentence — *the message needs a
    state no fixture in this suite builds yet* — accurate about every one and useful about
    none: an item whose cost is unstated reads as open-ended, and a list of thirty-one
    open-ended items is one nobody starts at. RK1498 started at it anyway, two lines of
    fixture at a time, which is what the constant had been hiding.

    Every not-run row and no longer the work-list alone, the work-list being empty: a shared
    reason is a constant wearing a sentence whichever state it sits under, and `FOREIGN` is
    shared on purpose — genuinely one cause, which is the exception the rule is stated
    against."""
    reasons = [one.why for one in SITES if one.state != "run"]
    assert reasons
    shared = {one for one in reasons if reasons.count(one) > 1}
    assert shared <= {FOREIGN}, sorted(shared - {FOREIGN})


def test_a_row_filed_as_work_names_the_state_its_fixture_wants():
    """`_UNMEASURED` in `test_pairs` is the same table one file over, and what makes a row there
    actionable is that it says the state — *no `[non_goals]` table*, *no deferred store*.

    Asserted on the composer rather than on the table (RK1599): no row is `unreached` today,
    and a loop over none would be a rule that stopped holding the moment it started mattering
    — which is the sitting a new site is filed in."""
    said = unreached("a prose file with two namespaces and a line pointing across them")
    assert said.startswith("unreached: "), said
    state = said[len("unreached: ") :]
    assert "runnable once a fixture has it" in state, said
    assert len(state.split(", and the command")[0].split()) >= 6, said
    for one in SITES:
        if one.state == "unreached":
            assert one.why.startswith("unreached: "), one.where


#: A ledger holding half of RK1, which is the state the three doors below are true of.
def _half(part: str = "the local half") -> str:
    return (
        f"# Shipped\n\n## Block A\n\n- ✅ **RK1 ({part})** **A symptom worth reading here** "
        f"— The local half landed.\n"
    )


def test_the_door_a_partial_ship_names_runs(tmp_path, capsys):
    """RK1498, one fixture family in (RK1532). `ship --part` leaves the line open and names
    what completes it — the one composed command here that rides a **successful** write rather
    than a refusal, so what it proves is that a door offered on the way out is takeable.

    Two writes of fixture, which is what the row now says it costs: the partial, then the
    command it printed."""
    root = departing(tmp_path, marker="🛠")
    assert main([
        "-C", str(root), "ship", "RK1", "--part", "the local half",
        "--why", "The local half landed.", "--remainder", "The rest of it is still open.",
    ]) == EXIT_OK
    said = capsys.readouterr().out
    # Two doors, and only one of them is this suite's to take: `--dep <id>` names what the
    # remainder waits on, which is the author's reading of their own backlog (L4) and has no
    # legal fill here — a fixture with one line can only name itself. So it is parsed, as
    # every author-blank door in this suite is, and the completion is the one that runs.
    (waits,) = [one for one in commands(said) if one[:1] == ["amend"]]
    assert build_parser().parse_args([one if one != "<id>" else "RK1" for one in waits])
    (finish,) = [one for one in commands(said) if one[:1] == ["ship"]]
    # Filled and run: the completion carries the `--why` it requires, which is the half the
    # door was printed without — spelled bare it refused as printed, on the one write whose
    # outcome may not be inherited from the line's own sentence.
    assert main(["-C", str(root), *supplied(filled(finish))]) == EXIT_OK, finish
    capsys.readouterr()
    # The completion landed, which is what makes the door a door: the line is gone and the
    # ledger holds one entry per outcome rather than a qualifier nobody replaced.
    assert "RK1" not in (root / "ROADMAP.md").read_text(encoding="utf-8")


def test_the_door_a_second_partial_names_runs(tmp_path, capsys):
    """One id carries one partial and then the completion, so a second is two answers about one
    piece of work. The door is an `add` for the step that was delivered — filled, since the
    symptom and the why are the author's own sentences (L4), and the block is a placeholder
    this project's own listing decides."""
    root = departing(tmp_path, marker="⏳", **{"CHANGELOG.md": _half()})
    assert main([
        "-C", str(root), "ship", "RK1", "--part", "the second half", "--why", "It works now."
    ]) == EXIT_USAGE
    said = capsys.readouterr().err
    (argv,) = [one for one in commands(said) if one[:1] == ["add"]]
    ready = supplied(filled(argv))
    assert ready[:1] == ["add"]
    # `<x>` is the block, which this project spells `A` — the one placeholder no table fills,
    # because which block a delivered step belongs under is the author's reading.
    assert build_parser().parse_args([one if one != "<x>" else "A" for one in ready])


def test_the_door_a_retirement_over_a_recorded_half_names_runs(tmp_path, capsys):
    """RK129's refusal: retiring an id whose half the ledger records would replace the entry
    holding it, so the half that shipped would leave the only file that holds it. The exit is
    the completion, and RK1138 is why it has to be a door that runs rather than a hint."""
    root = departing(tmp_path, marker="⏳", **{"CHANGELOG.md": _half()})
    assert main([
        "-C", str(root), "retire", "RK1", "--reason", "The rest will not be built."
    ]) == EXIT_USAGE
    said = capsys.readouterr().err
    ran = runs(root, said)
    assert ["ship", "RK1"] in [one[:2] for one in ran], said
    capsys.readouterr()
    assert "RK1" not in (root / "ROADMAP.md").read_text(encoding="utf-8")


# -- the `declare` family (RK1498, sized by RK1532) ----------------------------

#: The same project `departing` writes, with the opt-in tables left out — which `init` is not:
#: that verb opens `[non_goals]` and `[criteria]` itself (RK1313), and the half RK1328 was
#: filed for is every project already past that.
UNGOVERNED = WHOLE.replace('deferred = "DEFERRED.md"\n', "")


def test_the_door_a_scaffold_names_runs(tmp_path, capsys):
    """RK1498. `init` says what the backlog now takes and names the write that puts the first
    line in it — the one composed command in this family that a bare directory reaches, which
    is what its row now says it costs."""
    assert main(["-C", str(tmp_path), "init"]) == EXIT_OK
    said = capsys.readouterr().out
    ran = runs(tmp_path, said)
    # The one door a scaffold offers, and it ends in the caller's own `…` — so it is filled
    # and run as the template it is, which is what `abridged` exists to tell apart.
    assert [one[:3] for one in ran] == [["add", "--block", "A"]], said
    capsys.readouterr()
    # The line landed, which is the whole claim: a scaffold that names a write nobody can make
    # is a scaffold that answered about somebody else's project.
    assert "RK1" in (tmp_path / "docs" / "ROADMAP.md").read_text(encoding="utf-8")


def test_the_door_a_retrofitted_role_names_runs(tmp_path, capsys):
    """`declare <role>` opens a file a configured project was missing, and names the verb that
    role exists for. Two writes of fixture: the scaffold, then the role it left out."""
    assert main(["-C", str(tmp_path), "init"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "declare", "deferred"]) == EXIT_OK
    said = capsys.readouterr().out
    (argv,) = [one for one in commands(said) if one[:1] == ["defer"]]
    ready = supplied(filled(argv))
    # Parsed and not run: `defer` takes an id and a reason, and which line a caller sets aside
    # is theirs — the door names the verb, which is what the refusal that sent them here was
    # about. `<id>` is the one token no table fills, being the caller's own line.
    assert build_parser().parse_args([one if one != "<id>" else "RK1" for one in ready])


def test_the_door_an_opened_table_names_runs(tmp_path, capsys):
    """`declare non_goals` opens the table that governs a list, and names the write it gates —
    RK1328's own point, since a table opened and never written to is a project that opted in
    and got nothing."""
    # A configured project that does **not** declare the table, which `init` is not: that verb
    # opens `[non_goals]` and `[criteria]` itself (RK1313), and the half RK1328 was filed for
    # is every project already past it.
    departing(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(UNGOVERNED, encoding="utf-8")
    # **And with no heading either**, which is the state this row was a defect about until
    # RK1573: the door refused where the roadmap declared no list, `init` writes that heading
    # once and no verb since, and `Edit` is denied — so the write a table gates was unopenable
    # on exactly the population the table is opened for. Writing the first non-goal opens the
    # list now, so the fixture is the bare project and the door is the whole path.
    assert "Non-goals" not in (tmp_path / "ROADMAP.md").read_text(encoding="utf-8")
    assert main(["-C", str(tmp_path), "declare", "non_goals"]) == EXIT_OK
    said = capsys.readouterr().out
    ran = runs(tmp_path, said)
    assert ["non-goal", "add"] == ran[-1][:2], said
    capsys.readouterr()
    # And it wrote one, which is what makes the door a door rather than a verb being named.
    assert "Non-goals" in (tmp_path / "ROADMAP.md").read_text(encoding="utf-8")


# -- the outline's own listing (RK1498, sized by RK1532) -----------------------

#: Two families under one block, which is what makes `anchors --block` ambiguous and the door
#: it prints a real one. No git in it: the row's state guessed a history and the reading wanted
#: only an outline (RK1577).
SPANNING = "\n".join(
    [
        "# Roadmap",
        "",
        "## Block A",
        "",
        "- 📋 **TT1** (deps: —) **A symptom worth reading here** — "
        "Because of a reason. → §I.1",
        "- 📋 **TT2** (deps: —) **A second symptom worth reading** — "
        "Because of another. → §II.1",
        "",
    ]
)

FAMILIED = (
    "# Improvements\n\n## Block A\n\n## I A family\n\nProse enough to matter.\n\n"
    "### I.1 A design\n\nThe reasoning.\n\n## II Another family\n\nMore prose here.\n\n"
    "### II.1 A second design\n\nThe other reasoning.\n"
)


def test_the_door_two_families_under_one_block_names_runs(tmp_path, capsys):
    """RK1498. A block whose prose spans two families cannot be narrowed for the caller — which
    subtree a new line belongs under is a judgement no file holds — so the listing names the
    command that picks one, with a family it read off the file rather than a blank."""
    root = outlined(tmp_path)
    (root / "IMPROVEMENTS.md").write_text(FAMILIED, encoding="utf-8", newline="")
    # Two lines pointing into the two families, which is what makes a block resolve
    # to more than one: a block with no pointer under it has no prose to narrow.
    (root / "ROADMAP.md").write_text(SPANNING, encoding="utf-8", newline="")
    assert main(["-C", str(root), "anchors", "--block", "A"]) == EXIT_OK
    said = capsys.readouterr().out
    ran = runs(root, said)
    assert ["anchors", "--family", "I"] in ran, said


def test_the_door_a_wide_outline_listing_names_runs(tmp_path, capsys):
    """The addresses are what a caller came for and are one flag away, never printed by the
    hundred unasked (RK1466) — so the door is the narrowing, and `<anchor>` is the one token a
    reader substitutes from the rows above it."""
    root = outlined(tmp_path)
    (root / "IMPROVEMENTS.md").write_text(FAMILIED, encoding="utf-8", newline="")
    assert main(["-C", str(root), "anchors"]) == EXIT_OK
    said = capsys.readouterr().out
    (argv,) = [one for one in commands(said) if one[:2] == ["anchors", "--family"]]
    assert main(["-C", str(root), *[one if one != "<anchor>" else "II" for one in argv]]) == EXIT_OK


def test_the_doors_a_two_answer_refusal_names_run(tmp_path, capsys):
    """RK1498, and the third defect this sweep has found in a family it took: the narrowing door
    spelled its placeholder `<one of them>`, which any shell splits — RK1548's class, met in a
    command a caller is being told to run."""
    root = outlined(tmp_path)
    (root / "IMPROVEMENTS.md").write_text(FAMILIED, encoding="utf-8", newline="")
    # Two lines pointing into the two families, which is what makes a block resolve
    # to more than one: a block with no pointer under it has no prose to narrow.
    (root / "ROADMAP.md").write_text(SPANNING, encoding="utf-8", newline="")
    assert main(["-C", str(root), "anchors", "--block", "A", "--family", "I"]) == EXIT_USAGE
    said = capsys.readouterr().err
    argv = [one for one in commands(said) if one[:1] == ["anchors"]]
    assert [one[1] for one in argv] == ["--block", "--family"], argv
    # Both, in the order printed: the first names the families and the second narrows to one.
    assert main(["-C", str(root), *argv[0]]) == EXIT_OK
    filled_in = [one if one != "<family>" else "I" for one in argv[1]]
    assert main(["-C", str(root), *filled_in]) == EXIT_OK


# -- the capture family (RK1498, sized by RK1532) ------------------------------


def test_the_door_a_kept_capture_names_runs(tmp_path, capsys):
    """RK1498. A capture is a defect in *this tool*, and the whole of what a maintainer does
    with one is file it — so the dump ends with the `add` that files it, with the flag naming
    the capture filled in (RK1141), because a command a caller has to complete is a second step.

    It was spelled bare until this ran it (RK1577's find, one family over): every composed
    command here is backticked, and one that is not is a door no instrument can take.

    And it is **run** since RK1599. `filing` is a `shlex.join` and the path was the one token
    appended outside it, so a capture under a directory with a space split into two arguments
    and a Windows separator did not survive being read back — one quoting fixes both, and the
    row stops being a work-list item about the splitter."""
    root = departing(tmp_path)
    # The block a capture is filed under, opened first — `report` defaults to it and a
    # project without the heading is told to open it, which is a door of its own.
    assert main(["-C", str(root), "block", "add", "F", "--title", "Defects in this tool"]) == EXIT_OK
    assert main([
        "-C", str(root), "report", "--symptom", "A symptom plainly long enough to read",
        "--why", "Because of a reason.", "--", "show", "RK9",
    ]) == EXIT_OK
    said = capsys.readouterr()
    (argv,) = [one for one in commands(said.err) if one[:1] == ["add"]]
    assert argv[:3] == ["add", "--block", "F"], argv
    assert Path(argv[argv.index("--capture") + 1]).is_file(), argv
    assert main(["-C", str(root), *argv]) == EXIT_OK
    # And the flag took effect, which is what filling it in was for (RK1141): the capture
    # names the line that was filed, so a maintainer who ran this door has the evidence and
    # the backlog entry joined rather than a second step to remember.
    filed = capsys.readouterr().out
    assert "now names" in filed, filed
    assert "RK2" in Path(argv[argv.index("--capture") + 1]).read_text(encoding="utf-8")


# -- the orientation an install prints (RK1498, sized by RK1532) ---------------


def _oriented(said: str) -> str:
    """The orientation's own rows, which is what these three read (RK1534).

    The report names other commands — `merge --register` on a `.gitattributes` it did not
    write, and the capture offer — and the claim here is about the order **within** the five
    lines a session is handed at the end. `from here` is the label `stated` gives them.
    """
    return chr(10).join(
        one for one in said.splitlines() if one.strip().startswith("from here")
    )


def _wired(tmp_path: Path) -> Path:
    """A checkout of this tool beside a project, which is what `install` needs to run."""
    from roadkeep.installing import CARRIED

    here = Path(__file__).resolve().parents[1]
    source = tmp_path / "roadkeep"
    for part in CARRIED:
        target = source / part
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((here / part).read_bytes())
    return source


def test_the_orientation_names_what_has_to_happen_first(tmp_path, capsys):
    """RK1534. On a tree with no `roadkeep.toml` the orientation named five commands and every
    one of them refused — there is nothing to brief, add to, ship from or lint — and the
    sentence saying what has to happen first was not there at all.

    What the sweep reads is the order printed (RK1198), so the assertion is the order: the
    first command an ungoverned tree is handed is the one that governs it, and it runs."""
    project = tmp_path / "adopter"
    project.mkdir()
    assert main(["-C", str(project), "install", "--source", str(_wired(tmp_path))]) == EXIT_OK
    said = capsys.readouterr().out
    argv = commands(_oriented(said))
    assert argv[0][:1] == ["init"], argv[:2]
    assert main(["-C", str(project), *argv[0]]) == EXIT_OK
    capsys.readouterr()
    assert (project / "roadkeep.toml").is_file()


def test_every_verb_the_orientation_names_is_one_this_cli_takes(tmp_path, capsys):
    """The rest are a **list of verbs and not a path**, which is what the order above settles:
    `roadkeep add` here is a verb being named in a sentence, not a call somebody pastes, so
    what is asserted is that each names a subcommand this CLI declares — the same distinction
    `composing` draws everywhere between a command and a word in prose."""
    project = tmp_path / "adopter"
    project.mkdir()
    assert main(["-C", str(project), "install", "--source", str(_wired(tmp_path))]) == EXIT_OK
    said = capsys.readouterr().out
    verbs = [
        one for one in build_parser()._actions if getattr(one, "choices", None)  # noqa: SLF001
    ][0].choices
    named = commands(_oriented(said))
    assert len(named) >= 8, named
    for argv in named:
        assert argv[0] in verbs, argv


def test_a_governed_tree_is_told_what_it_already_is(tmp_path, capsys):
    """The other branch, and the reason the first line is conditional rather than added: an
    adopter with files reads *these are the tool's now*, which is true of them and false of a
    tree that declares nothing."""
    project = tmp_path / "adopter"
    project.mkdir()
    assert main(["-C", str(project), "init"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(project), "install", "--source", str(_wired(tmp_path))]) == EXIT_OK
    said = capsys.readouterr().out
    assert "the files `roadkeep.toml` declares are the tool's now" in said
    assert "nothing here is governed yet" not in said
    argv = commands(_oriented(said))
    assert argv[0][:1] == ["brief"], argv[:2]


# -- the merge row an install prints (RK1498, sized by RK1532) -----------------


def _adopter(tmp_path: Path) -> Path:
    """A governed project inside a repository, which is the state the merge row is about.

    `git init` because the row's three states are about what git would find: without a
    repository `_routed` cannot answer, and the fixture would be reading the tool's fallback
    rather than the state the sentence names.
    """
    project = tmp_path / "adopter"
    git_init(project)
    assert main(["-C", str(project), "init"]) == EXIT_OK
    return project


def _attributes(said: str) -> str:
    """The one row of the plan this family is about, which all three states begin with."""
    return chr(10).join(one for one in said.splitlines() if ".gitattributes" in one)


def test_the_doors_an_unwired_merge_row_names_run(tmp_path, capsys):
    """RK1498. The fifth surface is opt-in, so the row that says it is unwritten is the only
    place an adopter is told the driver exists — and it names two commands for one write
    (RK148). Both are run here, in the order printed, which is what makes it a path.

    The find is the second of them: `install --register-merge` was spelled without the
    invocation, so `commands` skipped it as prose. Not a scan's problem — RK1220's, met again:
    a door that omits the prefix is a line that does nothing on a machine whose console script
    is named anything else, and the sibling door in the same sentence always carried it."""
    project = _adopter(tmp_path)
    capsys.readouterr()
    assert main([
        "-C", str(project), "install", "--check", "--source", str(_wired(tmp_path)),
    ]) == EXIT_GATE
    row = _attributes(capsys.readouterr().out)
    ran = runs(project, row)
    assert [one[:2] for one in ran] == [
        ["merge", "--register"],
        ["install", "--register-merge"],
    ], row


def test_the_remedy_moves_the_row_it_was_offered_from(tmp_path, capsys):
    """RK393's rule, which is the only proof the door was the right command: a verdict whose
    remedy leaves the verdict standing is a loop. So the row is read twice — once before the
    command it names and once after — and it has to have moved to the state that says the
    attribute half is written."""
    project = _adopter(tmp_path)
    capsys.readouterr()
    source = _wired(tmp_path)
    checking = ["-C", str(project), "install", "--check", "--source", str(source)]
    assert main(checking) == EXIT_GATE
    assert "wires the merge driver" in _attributes(capsys.readouterr().out)
    assert main(["-C", str(project), "merge", "--register"]) == EXIT_OK
    capsys.readouterr()
    assert main(checking) == EXIT_GATE
    row = _attributes(capsys.readouterr().out)
    assert "the attribute half is written" in row, row
    assert "wires the merge driver" not in row, row


def test_the_door_a_wired_merge_row_names_answers_rather_than_refuses(tmp_path, capsys):
    """The second door of the wired state is a **read**, and its 1 is that read's answer: the
    config half is a `git config` this tool prints and never runs (RK266), so a clone that
    holds the attributes and not the key is exactly what `merge --check` exists to say.

    Which is why this asserts the code rather than passing the row to `runs`: the sweep's
    contract is one expected code per message, and a message whose two doors answer with
    different ones is a message that has to name which is which."""
    project = _adopter(tmp_path)
    assert main(["-C", str(project), "merge", "--register"]) == EXIT_OK
    capsys.readouterr()
    assert main([
        "-C", str(project), "install", "--check", "--source", str(_wired(tmp_path)),
    ]) == EXIT_GATE
    row = _attributes(capsys.readouterr().out)
    argv = commands(row)
    assert [one[:2] for one in argv] == [
        ["install", "--register-merge"],
        ["merge", "--check"],
    ], row
    # The write first, and the row's own claim about it: there is nothing here for it to
    # write, so the file it would have written comes back byte-identical.
    before = (project / ".gitattributes").read_bytes()
    assert main(["-C", str(project), *argv[0]]) == EXIT_OK
    assert (project / ".gitattributes").read_bytes() == before
    assert main(["-C", str(project), *argv[1]]) == EXIT_GATE


def test_the_door_a_blocked_merge_row_names_refuses_as_it_says(tmp_path, capsys):
    """RK394's state, and the one sentence in this family that predicts a refusal: with the
    path taken by something that is not a file the row stops advertising the flag and says
    that running it would exit 2.

    A claim about a command, so it is checked by running the command — and by the half the
    sentence leaves implicit, which is the one RK393 was filed for: *nothing was written*."""
    project = _adopter(tmp_path)
    (project / ".gitattributes").mkdir()
    capsys.readouterr()
    assert main([
        "-C", str(project), "install", "--check", "--source", str(_wired(tmp_path)),
    ]) == EXIT_GATE
    row = _attributes(capsys.readouterr().out)
    (argv,) = commands(row)
    assert argv == ["install", "--register-merge"], row
    assert main(["-C", str(project), *argv]) == EXIT_USAGE
    assert not (project / ".mcp.json").exists()
    assert not (project / ".claude").exists()


# -- what the gate says about a project's own surfaces (RK1498) ----------------


PROJECTED = (
    "# A project\n\n<!-- roadkeep:begin -->\nnothing the governed files render\n"
    "<!-- roadkeep:end -->\n"
)


def test_the_door_a_stale_projection_names_runs(tmp_path):
    """RK1498. A derived block is compared and never repaired (L4), so the whole of what the
    finding carries is the command that rewrites it — and nothing had run one.

    The gate is read again at the end, which is what makes it a door rather than a sentence:
    a remedy that leaves its own finding standing is the loop RK393 named."""
    project = _adopter(tmp_path)
    (project / "README.md").write_text(PROJECTED, encoding="utf-8", newline="")
    (found,) = lint(Config.discover(project)).findings
    assert found.code == "export.stale", found.code
    assert runs(project, found.message) == (["export", "--readme"],), found.message
    assert lint(Config.discover(project)).clean


def test_the_door_a_half_marked_projection_names_refuses_until_the_paste(tmp_path):
    """RK1591, which this family was taken to find. The other branch of the same function
    emits a finding whose door **refuses on the state that emitted it**: `export` may not
    invent where a block belongs in a file this tool does not own, so the paste comes first
    and `repair`, which walks `run` doors, dispatches one it cannot open.

    Recorded rather than asserted away — RK1591 holds the question, there being no kind for a
    remedy whose first step is an edit outside this tool, and a `read` or a `decide` here
    would each say something false about the command. What is held is the shape either answer
    has to keep: the door names the projection the finding is about, it refuses before the
    two lines are there, and it lands the moment they are."""
    project = _adopter(tmp_path)
    (project / "README.md").write_text(
        "# A project\n\n<!-- roadkeep:begin -->\nnothing the governed files render\n",
        encoding="utf-8",
        newline="",
    )
    config = Config.discover(project)
    (found,) = lint(config).findings
    assert found.code == "export.unmarked", found.code
    # The message composes nothing of its own: it says paste two lines, which is prose.
    assert not commands(found.message), found.message
    rule = remedy(found, config)
    assert rule is not None
    (door,) = rule.doors
    assert list(door.argv) == ["export", "--readme"], rule
    assert main(["-C", str(project), *door.argv]) == EXIT_USAGE
    (project / "README.md").write_text(PROJECTED, encoding="utf-8", newline="")
    assert main(["-C", str(project), *door.argv]) == EXIT_OK
    assert lint(Config.discover(project)).clean


def test_the_door_a_ceiling_over_the_served_surface_names_runs(tmp_path):
    """RK1498. The tool budget is filed at `roadkeep.toml` and there is no path a reader can
    open to see the cost, so the ranking the message names is the only way to the number —
    which makes running it the whole claim.

    One run for however many tools are over: every finding here composes the same read, and
    the ranking is what answers *which*, so the door does not vary with the subject."""
    project = _adopter(tmp_path)
    declared = (project / "roadkeep.toml").read_text(encoding="utf-8")
    (project / "roadkeep.toml").write_text(
        f"{declared}\n[tools]\ncharacters = 200\n", encoding="utf-8", newline=""
    )
    over = [one for one in lint(Config.discover(project)).findings if one.code == "budget.tool"]
    assert over, "the fixture stopped being over the ceiling, so this asserts nothing"
    assert {tuple(commands(one.message)[0]) for one in over} == {("cost", "--tools")}
    assert runs(project, over[0].message) == (["cost", "--tools"],), over[0].message


def _vendored(project: Path) -> tuple:
    """The notes this fixture is about, and never every note the gate carries.

    `engine.disagreement` fires on a **modified** checkout, which is what a developer running
    this suite has — so a test asserting the whole list would be green on a clean tree and red
    on the one the work is done in, for a reason that is not the state under test.
    """
    return tuple(
        one for one in lint(Config.discover(project)).notes if one.code.startswith("install.")
    )


def test_the_door_a_surface_behind_the_engine_names_runs(tmp_path):
    """RK1498, over RK1192's note. Two codes and one door: a vendored surface older than the
    engine answering, and one the project never had at all. `install --check` answers this on
    demand and nobody runs it, which is why the gate says it — so what has to be true is that
    the command it names writes both back and the note then goes.

    Installed from the checkout this process is and not from a copy: `staleness` compares
    against `_source()`, so a fixture vendoring from anywhere else would report drift that is
    the fixture's own and call it the state under test."""
    project = _adopter(tmp_path)
    assert main(["-C", str(project), "install"]) == EXIT_OK
    assert not _vendored(project), "the install left drift of its own"
    skill = project / ".claude" / "skills" / "roadkeep"
    (skill / "SKILL.md").write_text("older than the engine\n", encoding="utf-8", newline="")
    (skill / "writing.md").unlink()
    notes = _vendored(project)
    assert {one.code for one in notes} == {"install.stale", "install.absent"}, notes
    for note in notes:
        assert runs(project, note.message) == (["install"],), note.message
    assert not _vendored(project)


# -- the pause, and what does not come back with it (RK1498) -------------------


PAUSING = (
    'prefix = "TT"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    'improvements = "IMPROVEMENTS.md"\ndeferred = "DEFERRED.md"\n'
)

QUEUED = (
    "# Roadmap\n\n## Priority\n\n1. TT2\n\n## Block A\n\n"
    "- 📋 **TT1** (deps: —) **A symptom worth reading** — Because of a reason. → §TT1\n"
    "- 📋 **TT2** (deps: —) **A second symptom worth it** — Because of another. → §TT2\n"
)

_TT1 = "- 📋 **TT1** (deps: —) **A symptom worth reading** — Because of a reason. → §TT1\n"

PAUSED_DESIGNS = (
    "# Improvements\n\n## Block A\n\n### §TT1 A design\n\nProse enough to matter.\n\n"
    "### §TT2 Another design\n\nProse enough to matter here too.\n"
)


def paused(tmp_path: Path) -> Path:
    """A project with a store to pause into and an order in the roadmap to fall out of.

    Both halves, because the two sites this fixture serves need one each: the store is what
    `resume` reconciles against, and the queue is what a resumed line is no longer in.
    """
    root = tmp_path / "paused"
    root.mkdir()
    for name, body in (
        ("roadkeep.toml", PAUSING),
        ("ROADMAP.md", QUEUED),
        ("CHANGELOG.md", "# Shipped\n\n## Block A\n"),
        ("IMPROVEMENTS.md", PAUSED_DESIGNS),
        ("DEFERRED.md", "# Deferred\n\n## Block A\n"),
    ):
        with (root / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return root


def test_the_offer_a_resumed_line_makes_runs(tmp_path, capsys):
    """RK1498, over RK327's offer. The pause takes the line out of the order and the store
    keeps a line rather than a rank, so where it sat is the one thing a resume cannot put
    back — and the verb says so by naming the command that would, rather than choosing a
    position nobody stated (L4, one field over).

    An offer and not a remedy, which is why running it is the whole claim: nothing refuses if
    it is ignored, so a command that had quietly stopped being accepted would never be met by
    anyone but the reader who pasted it."""
    root = paused(tmp_path)
    assert main([
        "-C", str(root), "defer", "TT2", "--reason", "It waits on a decision.",
    ]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(root), "resume", "TT2"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "if it goes back in the order" in said, said
    assert runs(root, said) == (["priority", "add", "TT2"],), said
    assert "1. TT2" in (root / "ROADMAP.md").read_text(encoding="utf-8")


def test_the_door_a_resume_that_places_nothing_names_runs(tmp_path, capsys):
    """RK1083's refusal, run — and RK1593, which is what running it found. It named one
    command, `status <id> <marker>`, and that command **refuses** in the state the refusal
    is about: the store still holds the id, and status lives in exactly one file.

    The removal is what this call was going to do and did not, so the same call without the
    flag is the step before it. Both are asserted in the order printed, which is the half
    RK1198 is about: a sequence whose second step refuses is a sequence, not a set.

    The marker itself is filled here rather than by `filled`: a positional blank has no flag
    in front of it to read a value off, which is what `<unfilled positional>` says out loud
    instead of guessing — so the substitution is the test's, from the project's own schema."""
    root = paused(tmp_path)
    assert main([
        "-C", str(root), "defer", "TT1", "--reason", "It waits on a decision.",
    ]) == EXIT_OK
    capsys.readouterr()
    # The line back in the roadmap while the store still holds it, which is the state the
    # reconciling path is about: two copies, and only one of them is the work.
    text = (root / "ROADMAP.md").read_text(encoding="utf-8")
    with (root / "ROADMAP.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write(text.replace("## Block A\n\n", f"## Block A\n\n{_TT1}"))
    working = Config.discover(root).schema.working
    assert main(["-C", str(root), "resume", "TT1", "--marker", working]) == EXIT_USAGE
    said = capsys.readouterr().err
    first, second = [one for one in commands(said) if one[:1] != ["report"]]
    assert first == ["resume", "TT1"], said
    assert second == ["status", "TT1", "<marker>"], said
    assert main(["-C", str(root), *first]) == EXIT_OK
    assert main([
        "-C", str(root), *[one if one != "<marker>" else working for one in second]
    ]) == EXIT_OK
    assert f"{working} **TT1**" in (root / "ROADMAP.md").read_text(encoding="utf-8")


# -- the address a malformed anchor is answered with (RK1498) ------------------


@pytest.mark.parametrize(
    "typed, listing, offered",
    [
        # A family the file declares, mistyped in its separator: the answer is that family's
        # next child, and the listing is narrowed to it (RK363).
        ("I-2", ["anchors", "--family", "I"], "I.2"),
        # A segment naming no family at all, where the answer is the free top-level and the
        # listing is the whole outline — a different read, from the same refusal.
        ("ZZ-2", ["anchors"], "III"),
    ],
    ids=["a-family-typed", "no-family-typed"],
)
def test_the_listing_a_malformed_anchor_is_answered_with_runs(
    tmp_path, capsys, typed, listing, offered
):
    """RK1498, over RK363's read. A malformed address is answered with a free one *and* with
    the listing that shows what is taken — and which listing depends on what the caller typed,
    a leading segment naming a live family being a typo inside it rather than a new subtree.

    Two branches and two reads, so both are run: a narrowing that named a family the file does
    not declare would exit 2 in the reader's hands, and nothing said the wide one was still a
    command at all."""
    root = outlined(tmp_path)
    (root / "IMPROVEMENTS.md").write_text(FAMILIED, encoding="utf-8", newline="")
    assert main([
        "-C", str(root), "section", "add", typed,
        "--title", "A title", "--body", "Prose enough to matter, and it ends.",
    ]) == EXIT_USAGE
    said = capsys.readouterr().err
    (argv,) = [one for one in commands(said) if one[:1] == ["anchors"]]
    assert argv == listing, said
    assert main(["-C", str(root), *argv]) == EXIT_OK
    # The address beside the listing is the retry's, and it is **not** a composed command:
    # the `retry` row prints it unbackticked, which is `commands`' own rule about what a
    # message offers to run. Asserted as text, because which address the branch gives is the
    # whole of what the two differ on — a narrowing that answered `III` would be the guess
    # RK363 refused, printed beside the read that contradicts it.
    assert f"--ref {offered}" in said, said
    assert f"§{offered} " in said, said


# -- the two ways a governed number is refused (RK1498) ------------------------


def test_the_read_an_address_this_build_has_no_key_for_names_runs(tmp_path, capsys):
    """RK1498, over RK1272's refusal. `govern` writes the tables a reading decides, so an
    address that is a *name* — a `[files]` role, a `[markers]` glyph — is refused with the
    listing of every key there is rather than with the subset this verb takes.

    A read and not a repair, which is what makes running it the claim: nothing about the
    caller's tree has to change, so the only way this door is ever wrong is by not being a
    command any more — and the census had it as a state no fixture built."""
    project = tmp_path / "governed"
    project.mkdir()
    assert main(["-C", str(project), "init"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(project), "govern", "files.roadmap", "5"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert runs(project, said) == (["config"],), said


def test_the_door_a_tree_with_no_table_names_runs(tmp_path, capsys):
    """The other refusal of the same verb, and the census had this one wrong twice over: its
    state named a corpus reading, and the command is composed on the branch **before** any
    reading happens — a tree that declares no `roadkeep.toml` has no table to write into.

    So the door is the scaffold, and what it has to buy is the call that was refused: `init`
    runs, and the same `govern` then lands. That is the whole of RK393's rule — a remedy
    leaving its own refusal standing is a loop — and it is the shape a two-step path takes
    when the second step is the caller's original one."""
    bare = tmp_path / "bare"
    bare.mkdir()
    governing = ["-C", str(bare), "govern", "limits.why", "200"]
    assert main(governing) == EXIT_USAGE
    said = capsys.readouterr().err
    assert runs(bare, said) == (["init"],), said
    assert (bare / "roadkeep.toml").is_file()
    assert main(governing) == EXIT_OK


# -- the surface a mistyped argument is answered with (RK1498) -----------------


def _mistyped(tmp_path: Path) -> Path:
    """An outline with one line, so a verb taking an id has one to be given."""
    root = outlined(tmp_path)
    (root / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A\n\n"
        "- 📋 **TT1** (deps: —) **A symptom** — Because of a reason. → §I.1\n",
        encoding="utf-8",
        newline="",
    )
    (root / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A\n\n### I A family\n\nProse.\n\n"
        "### I.1 A design\n\nProse enough to matter.\n",
        encoding="utf-8",
        newline="",
    )
    return root


@pytest.mark.parametrize(
    "argv, doors",
    [
        # A flag the verb does not declare, where the whole answer is its own short surface.
        (["list", "--nope"], (["list", "--help"],)),
        # A stray positional, which keeps its own sentence: naming the flags of a verb that
        # takes an id would be advice about a mistake nobody made.
        (["show", "TT1", "TT2"], (["show", "--help"],)),
        # A flag before the verb is the top level's, so the door carries no verb at all.
        (["--vers", "list"], (["--help"],)),
    ],
    ids=["an-unknown-flag", "a-stray-positional", "before-the-verb"],
)
def test_the_surface_a_mistyped_argument_names_runs(tmp_path, capsys, argv, doors):
    """RK1498, over RK1026 and RK1032. The answer to a mistyped argument is a **surface**, and
    every shape of it ends in a door: the verb's own help where the flag was the verb's, and
    the top level's where it was typed before one.

    Running them is what the census could not do until now. `--help` opens by ending the
    process, so `runs` reads a `SystemExit` as the code it carries (RK1595) — every `see
    <verb> --help` row in this tool was a command the instrument treated as a failure, which
    is a door being unrunnable for a reason that has nothing to do with the door."""
    root = _mistyped(tmp_path)
    assert main(["-C", str(root), *argv]) == EXIT_USAGE
    assert runs(root, capsys.readouterr().err) == doors


def test_the_position_a_flag_spelled_wrong_names_runs(tmp_path, capsys):
    """RK1254's mirror, and the one shape composing two doors: a flag naming an argument the
    verb takes **by order** is answered with the position and with the surface, because which
    of the two an argument is is exactly what the caller had wrong.

    The id is filled from the fixture's own line rather than by `filled`: a positional blank
    has no flag in front of it to read a value off, which is what `<unfilled positional>` says
    out loud instead of guessing."""
    root = _mistyped(tmp_path)
    assert main(["-C", str(root), "show", "--id", "TT1"]) == EXIT_USAGE
    said = capsys.readouterr().err
    position, surface = [one for one in commands(said) if one[:1] != ["report"]]
    assert position == ["show", "<id>"], said
    assert surface == ["show", "--help"], said
    assert main(["-C", str(root), "show", "TT1"]) == EXIT_OK
    with pytest.raises(SystemExit) as ended:
        main(["-C", str(root), *surface])
    assert (ended.value.code or 0) == EXIT_OK


# -- what a ledger already holds, and what it holds under one id (RK1498) ------


PLAIN = (
    'prefix = "TT"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    'improvements = "IMPROVEMENTS.md"\n'
)


def blocked(tmp_path: Path, declare: str = PLAIN, **files: str) -> Path:
    """A project with one block and nothing in it, which the three tests below fill."""
    root = tmp_path / "blocked"
    root.mkdir(parents=True)
    written = {
        "roadkeep.toml": declare,
        "ROADMAP.md": "# Roadmap\n\n## Block A\n\n",
        "CHANGELOG.md": "# Shipped\n\n## Block A\n",
        "IMPROVEMENTS.md": "# Improvements\n\n## Block A\n",
        **files,
    }
    for name, body in written.items():
        with (root / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return root


def _filed(root: Path, number: int) -> None:
    assert main([
        "-C", str(root), "add", "--block", "A",
        "--symptom", f"A symptom number {number} worth reading",
        "--why", "Because of a reason.",
        "--section", f"A design number {number}",
        "--section-body", "Prose enough to matter, and it ends.",
    ]) == EXIT_OK


def test_the_read_the_near_row_names_runs(tmp_path, capsys):
    """RK1498, over RK441. The nearest lines are ranked by word overlap and that is an order
    rather than a verdict, so the row says how many it left out and names the two reads that
    are the whole of them — one over the ledger, one over what is still open.

    Run against a block that has **recorded** something, which is the state the count is about:
    a listing whose `is all 0` never opened a file would answer the same on a ledger of two
    hundred, and nothing here would have noticed."""
    root = blocked(tmp_path)
    _filed(root, 1)
    _filed(root, 2)
    assert main(["-C", str(root), "ship", "TT1", "--why", "The first no longer happens."]) == EXIT_OK
    capsys.readouterr()
    _filed(root, 3)
    said = capsys.readouterr().out
    assert "is all 1" in said, said
    assert runs(root, said) == (["delivered", "A"], ["list", "--block", "A"]), said


def test_the_two_doors_an_inherited_claim_names_each_close_it(tmp_path, capsys):
    """RK1281's refusal, run. A `--decides` writes no symptom of its own — the claim is the
    roadmap line's, carried whole — so the ordinary *shorten it* remedy would send the author
    to a rationale section this very ship is deleting.

    Two doors and they are alternatives, so each is run on its own tree: rewriting the claim
    in both files, and widening the number the decisions role is held to. Either has to make
    the refused call land, which is the only thing that makes printing two of them better
    than printing one.

    The first was spelled with no invocation in front of it while the second, in the same
    sentence, carried one — RK1589's class again (RK1596), and found the same way: a scan
    reading the prefix took it for prose, so the sweep saw one door where there are two."""
    declaring = f"{PLAIN}[limits.decisions]\nsymptom = 20\n".replace(
        'improvements = "IMPROVEMENTS.md"\n',
        'improvements = "IMPROVEMENTS.md"\ndecisions = "DECISIONS.md"\n',
    )
    shipping = [
        "ship", "TT1", "--why", "It no longer happens at all.",
        "--decides", "The store is the repository: no database and no service.",
    ]
    for closing in (
        ["restate", "TT1", "--symptom", "A shorter claim"],
        ["govern", "limits.symptom", "60", "--role", "decisions"],
    ):
        root = blocked(
            tmp_path / closing[0], declaring, **{"DECISIONS.md": "# Decisions\n\n## Block A\n"}
        )
        _filed(root, 1)
        capsys.readouterr()
        assert main(["-C", str(root), *shipping]) == EXIT_USAGE
        said = capsys.readouterr().err
        named = [one for one in commands(said) if one[:1] == [closing[0]]]
        assert named, (closing, said)
        assert main(["-C", str(root), *closing]) == EXIT_OK
        assert main(["-C", str(root), *shipping]) == EXIT_OK


def test_the_read_an_id_no_entry_leads_with_names_runs(tmp_path, capsys):
    """RK1498, over RK1048. An entry keyed by the id it **leads with** is invisible under the
    second one it delivered, and history knows better than the parse does — so the refusal
    stops saying *never written* and names the read that resolves which line holds it.

    The commit is what makes the sentence true, so the fixture commits: a refusal claiming a
    commit wrote an id, on a tree with no history, would be a message about nothing."""
    root = blocked(
        tmp_path,
        PLAIN,
        **{
            "CHANGELOG.md": "# Shipped\n\n## Block A\n\n"
            "- ✅ **TT7** **A first symptom** — it was done, and so was **TT8**.\n"
        },
    )
    git_init(root)
    git_commit(root, "feat: two at once")
    assert main(["-C", str(root), "show", "TT8"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "wrote it" in said, said
    assert runs(root, said) == (["gaps"],), said


# -- the line a marker is written on, and the ones nothing counted (RK1498) ----


_FIRST = "- 📋 **TT1** (deps: —) **A short first symptom** — Short. → §TT1"
_SECOND = (
    "- 📋 **TT2** (deps: TT1) **A second symptom worth it** "
    "— A reason of some length here. → §TT2"
)
_DESIGNS = (
    "# Improvements\n\n## Block A\n\n### §TT1 A design\n\nProse.\n\n"
    "### §TT2 Another design\n\nMore prose.\n"
)


def _lined(tmp_path: Path, roadmap: str, limit: int | None = None) -> Path:
    root = tmp_path / "lined"
    root.mkdir(parents=True)
    bound = "" if limit is None else f"[limits]\nline = {limit}\n"
    for name, body in (
        ("roadkeep.toml", f"{PLAIN}{bound}"),
        ("ROADMAP.md", roadmap),
        ("CHANGELOG.md", "# Shipped\n\n## Block A\n"),
        ("IMPROVEMENTS.md", _DESIGNS),
    ):
        with (root / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return root


def test_the_door_a_dependent_s_line_names_runs(tmp_path, capsys):
    """RK1498, over RK348 and RK1152. A ship ticks its dependents' annotations, and a ✅ is two
    characters wider — so the line that overflows is somebody else's, and the refusal leads
    with **whose** before it says how much to delete.

    The door is the edit on that line, and running it is the only thing that says the id in
    it is the right one: a message naming the dependent and a door naming the caller's own id
    would read as a path and be a loop, which is the shape RK1198 is about."""
    # One character of room, so the ✅ is exactly what does not fit.
    root = _lined(tmp_path, f"# Roadmap\n\n## Block A\n\n{_FIRST}\n{_SECOND}\n", len(_SECOND) + 1)
    shipping = ["-C", str(root), "ship", "TT1", "--why", "It no longer happens."]
    assert main(shipping) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "on TT2's line" in said, said
    assert runs(root, said) == (["amend", "TT2", "--why", FILLS["--why"]],), said
    assert main(shipping) == EXIT_OK


def test_the_read_an_uncounted_line_names_runs(tmp_path, capsys):
    """RK1498, over RK10. A listing that looked complete is the whole symptom, so a count says
    how many marker-bearing lines it could not take — and names the read that shows them.

    It was quoted with apostrophes rather than backticks (RK1597), which reads the same to a
    person and is invisible to anything scanning for a door: the delimiter is what says *this
    span is a command*, and RK1577 found the same thing spelled without one at all."""
    root = _lined(
        tmp_path,
        f"# Roadmap\n\n## Block A\n\n{_FIRST}\n- 📋 a marker on a line that is not a task\n",
    )
    assert main(["-C", str(root), "list", "--block", "A"]) == EXIT_OK
    said = capsys.readouterr().err
    assert "1 marker-bearing line(s)" in said, said
    assert runs(root, said) == (["audit"],), said


# -- the last three, and what each of them is about (RK1498) -------------------


def test_the_read_a_key_this_build_cannot_read_names_runs(tmp_path, capsys):
    """RK1498. An unknown key is a typo if nothing declares it and an **upgrade** if a newer
    roadkeep does, and the config cannot tell which — so the clause names the one command that
    says which copies answer here, and a caller who has three of them can look.

    Run, and it did not run (RK1598): the config load is ahead of every handler, so the read
    offered for a config this build cannot parse gave back the identical refusal. `engines`
    needs the root and nothing else — its own docstring says so — and it now tolerates a
    broken config the way `guard` and `report` already do."""
    root = outlined(tmp_path)
    (root / "roadkeep.toml").write_text(
        f"{OUTLINED}nonsense = 1\n", encoding="utf-8", newline=""
    )
    assert main(["-C", str(root), "list"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "unknown to this build" in said, said
    assert runs(root, said) == (["engines"],), said


def test_the_command_a_free_top_level_names_opens_it(tmp_path, capsys):
    """RK1140's note, run — and RK1598, which is what running it found. It said a free
    top-level makes `add --ref <it>.1` **refuse until one exists**, and that is not what
    happens: the line lands, and `add` prints the `section add` calls that close the pointer
    it just made. A reader who believed the refusal would not have filed the line at all.

    So the sentence names the command that acts and says what the gate says meanwhile. Both
    halves are checked: the door opens the family, and a line pointing into it is accepted
    with a pointer `lint` reports until a section answers."""
    root = outlined(tmp_path)
    (root / "IMPROVEMENTS.md").write_text(FAMILIED, encoding="utf-8", newline="")
    assert main(["-C", str(root), "anchors", "--next"]) == EXIT_OK
    said = capsys.readouterr().err
    (opened,) = runs(root, said)
    assert opened[:4] == ["section", "add", "III", "--title"], said
    capsys.readouterr()
    filed = ["add", "--block", "A", "--symptom", FILLS["--symptom"], "--why", FILLS["--why"]]
    assert main(["-C", str(root), *filed, "--ref", "III.1"]) == EXIT_OK
    unresolved = [
        one for one in lint(Config.discover(root)).findings if one.code == "ref.unresolved"
    ]
    assert [one.subject for one in unresolved] == ["III.1"], unresolved


def test_the_door_a_registration_with_no_config_names_runs(tmp_path, capsys):
    """RK1498. A merge driver is wired per **governed file**, so a project declaring none has
    nothing to register — writing lines for the paths a default config happens to name would
    wire a driver for files nobody declared (L6).

    The census had this one aimed at the wrong verb: `merge --register` writes on a bare tree,
    and it is `install --register-merge` that reaches this refusal. And the sentence claimed
    *the four surfaces above do not depend on it* (RK1598) — true of the flag and false of
    this call, which sits above the first write by RK393's own rule and leaves the tree
    exactly as it found it, so a reader was told the install half had happened."""
    bare = tmp_path / "bare"
    bare.mkdir()
    registering = ["-C", str(bare), "install", "--register-merge"]
    assert main(registering) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "nothing was written" in said, said
    assert not (bare / ".mcp.json").exists(), "the refusal is above the first write"
    assert runs(bare, said) == (["init"],), said
    assert main(registering) == EXIT_OK
    assert (bare / ".gitattributes").is_file()
    assert (bare / ".mcp.json").is_file()


# -- the placeholder that cannot survive its own quotes (RK1548) ---------------


def test_no_composed_command_holds_an_unquoted_placeholder_with_a_space():
    """RK1548. RK1513's door read `--lead <what is true when it is>` and the test that parses
    it refused the call: `shlex.split` takes `<what` as the value and hands argparse four
    stray words, so the line as printed is a **different command**.

    Nothing caught it. `_BLANKS` accepts `<x>` and `"<x>"` alike and only the quoted one
    survives a split, so the unquoted placeholder never matches — and `filled`'s loud
    `<unfilled --flag>` branch, which exists so an argument is never quietly dropped, never
    sees it either. It arrives as literal argv.

    **From the string alone**, which is what makes this worth having beside `SITES`: a span
    holding one is wrong whether or not a test reaches the site that prints it, so one pass
    covers what nothing runs as well as what does. Three of the four RK1548 named were found
    by grep after the fourth was found by a hand-written test."""
    found = [
        f"{module.where}:{lineno}: {said}"
        for module in modules()
        for lineno, text in spoken(module)
        for said in loose(text)
    ]
    assert not found, found


def test_the_reading_is_of_what_the_tool_prints_and_not_of_its_prose():
    """The line RK1548 draws: `--part <what landed>` outside backticks is a flag being named
    in a sentence and is correct, and a docstring is prose about the code. So the population is
    the strings a module **composes**, read off the AST — pointed at the file's text instead,
    the first attempt matched a backtick in a comment against one three functions later and
    reported the span between them."""
    said = "a door `roadkeep section move I.1 --to <free anchor>` here"
    assert loose(said) == ["roadkeep section move I.1 --to <free anchor>"]
    # Quoted is the fix, and it is what the check is for.
    assert not loose('a door `roadkeep ship RK1 --part "<what landed>"` here')
    # A flag named in a sentence is not a command, backticks or none.
    assert not loose("a flag <what landed> named in a sentence")
    assert not loose("`<what landed>` is where the qualifier goes")
    # And one word inside the brackets is runnable as printed.
    assert not loose("`roadkeep anchors --family <family>`")


def test_a_door_spelled_without_the_invocation_is_still_read():
    """Wider than `commands`' boundary, and the one live site is why: `section move {anchor}
    --to <free anchor>` was bare **and** unquoted at once, and a reading that took only
    prefixed spans walked straight past it.

    Two checks, not one. RK1590 asks whether a door is findable at all; this asks whether the
    one in front of a reader runs as printed, and a door missing its prefix is still a door."""
    assert loose("`section move I.1 --to <free anchor>`") == [
        "section move I.1 --to <free anchor>"
    ]
    # A word that is not a verb of this CLI is prose, whichever way it is delimited.
    assert not loose("`shuffle the deck --to <a new place>`")


# -- the prefix that says a span is a door (RK1590) ----------------------------


def test_no_message_pairs_a_door_with_a_verb_spelled_bare():
    """RK1590. `commands` skips a span that does not open with the invocation, so a door
    spelled without one is not counted as unreached — it is not counted at all. RK1589 met
    that: `install --register-merge` bare, in a sentence whose sibling door carried the prefix.

    **The population cannot be read off the prefix**, which is the finding. 421 backticked
    spans in this package lead with a verb and carry none, and most are prose — `install
    --vendor` named as a flag, `ship --decides` as a family. Narrowing to spans inside a
    function that calls `invocation()` leaves 126, which is no better: a composer's message
    names verbs in prose too.

    So this reads the one tell the defect actually had. Within **one message**, a span that
    runs and a span that names a verb are already told apart by whoever wrote it — what is
    checkable is that they agree. A message naming verbs throughout is left alone, which is
    the prose the two rules the design weighed would each have refused.

    Empty today, and that is the answer rather than the absence of one: RK1589 fixed the
    instance, and what this buys is that the next one is red instead of invisible."""
    found = [
        f"{module.where}:{lineno}: {said}"
        for module in modules()
        for lineno, text in spoken(module)
        for said in inconsistent(text)
    ]
    assert not found, (
        "a message spells one door with the invocation and another verb without it — the "
        f"second is a door nothing runs, or prose the first makes ambiguous: {found}"
    )


def test_the_reading_is_of_a_pair_and_not_of_a_prefix():
    """The line RK1590 draws, at the three shapes this package actually holds."""
    # A door beside a bare verb: the defect, and the only thing that fires.
    assert inconsistent("take `roadkeep add --block A` then `install --register-merge`") == [
        "install --register-merge"
    ]
    # Prose naming a flag family, with no door beside it — 421 spans of this and none wrong.
    assert not inconsistent("`install --vendor` moves the engine forward")
    # And the bare invocation is the tool's **name**, not a door: three messages in
    # `installing` pair one with the word `install`, and counting them would fire on the
    # sentences the rule exists to permit.
    assert not inconsistent("a copy carrying `roadkeep` where `install` wired a checkout")


# -- the shell the composer assumed (RK1580) -----------------------------------


def test_no_composed_command_is_quoted_for_one_family_of_shells():
    """RK1580. `shlex` is POSIX by default and this project's own platform is not, so every
    door composed with it was quoted with `'` — which Git Bash and PowerShell both read and
    **`cmd.exe` does not read at all**.

    Measured before it was fixed, running the line this repository's own `report` prints:
    Git Bash and PowerShell each gave argparse the right argv, and in a clean `cmd` the
    symptom arrived as `'A` plus seven stray positionals and the capture path arrived with
    the quotes inside it — naming a file Windows has not got. So the door on a Windows
    checkout had never been takeable, which is the one of the design's two outcomes that
    does not close as declined.

    Held from the strings alone, the way `loose` is and for its reason: a span quoted for
    one shell is wrong whether or not a test reaches the site that prints it."""
    found = [
        f"{module.where}:{lineno}: {said}"
        for module in modules()
        for lineno, text in spoken(module)
        for said in commanded(text)
        if "'" in said
    ]
    assert not found, found


def test_the_quote_is_the_one_every_shell_reads():
    """The composer itself, at the three shapes the doors carry. A double quote is what `cmd`,
    PowerShell and a POSIX shell all read back as one token; a single quote is a quoting
    character in only the last of the three."""
    # A path, which is quoted for the separator alone — unquoted, a POSIX shell reads every
    # backslash as an escape and `C:\Users\x` arrives as `C:Usersx` (RK1579's finding).
    assert quoted(r"C:\Users\alexa\x.json") == '"C:\\Users\\alexa\\x.json"'
    # Prose, which is quoted for the spaces, and an apostrophe in it survives — the shape
    # `shlex.quote` spells `'It'"'"'s'`, which is unreadable in two of the three shells.
    assert quoted("It isn't short") == '"It isn\'t short"'
    # A plain word is left alone: `'--help'` reads as a literal somebody typed.
    assert quoted("--help") == "--help"
    # And the whole argv round-trips through the reader this suite runs doors with.
    line = joined(["roadkeep", "add", "--symptom", "It isn't short", "--capture", r"C:\a\b.json"])
    assert shlex.split(line) == [
        "roadkeep", "add", "--symptom", "It isn't short", "--capture", r"C:\a\b.json",
    ]


# -- the vendored copy the un-wiring keeps (RK1549) ----------------------------


def test_the_door_the_kept_engine_names_reclaims_it(tmp_path, capsys):
    """RK1549. RK1514 gave the vendored copy a `kept` row and left the removal to a sentence —
    *delete the directory* — the one line in an un-wiring report that hands work back to the
    reader in English. What decided it was the size, and the size is **22 MiB across 970
    files** on this repository's own checkout.

    So the row names a verb, and the whole value of that is the verb running: the copy is
    weighed, the door reclaims it, and the row is gone from the next report."""
    project = tmp_path / "adopter"
    project.mkdir()
    assert main(["-C", str(project), "init"]) == EXIT_OK
    home = project / ".roadkeep" / "src" / "roadkeep"
    home.mkdir(parents=True)
    (home / "__init__.py").write_text('__version__ = "0.2.0"\n', encoding="utf-8")
    capsys.readouterr()
    assert main(["-C", str(project), "uninstall", "--check"]) == EXIT_OK
    said = capsys.readouterr().out
    (argv,) = [one for one in commands(said) if one[:2] == ["uninstall", "--engine"]]
    assert main(["-C", str(project), *argv]) == EXIT_OK
    assert not (project / ".roadkeep").exists()
    # And the row it came from is gone, which is what makes the door the right one (RK393).
    capsys.readouterr()
    assert main(["-C", str(project), "uninstall", "--check"]) == EXIT_OK
    assert ".roadkeep/" not in capsys.readouterr().out


def test_the_removal_is_weighed_before_it_is_taken(tmp_path, capsys):
    """`--check` is the same computation with the deletion left off, which is `install
    --check`'s rule one verb over — and the count is in both answers, because a caller about
    to lose megabytes is owed the number before the loss and not after it."""
    project = tmp_path / "adopter"
    project.mkdir()
    assert main(["-C", str(project), "init"]) == EXIT_OK
    (project / ".roadkeep").mkdir()
    (project / ".roadkeep" / "big.txt").write_text("x" * 4096, encoding="utf-8")
    capsys.readouterr()
    assert main(["-C", str(project), "uninstall", "--engine", "--check"]) == EXIT_GATE
    said = capsys.readouterr().out
    assert "would delete   1 file(s), 4,096 bytes" in said, said
    assert (project / ".roadkeep").is_dir(), "a check writes nothing"


def test_a_clone_at_that_path_is_refused_and_left(tmp_path, capsys):
    """The one refusal, and the only state where a caller's *yes* is about something else than
    they think: `install --vendor` excludes `.git` by name, so a `.roadkeep/` carrying one is
    somebody's clone and removing it takes history this command cannot give back.

    Anything else in the tree is the caller's judgement (L4) — an engine an adopter has edited
    is still an engine they asked to remove, and a check guessing at edits would refuse the
    ordinary case."""
    project = tmp_path / "adopter"
    project.mkdir()
    assert main(["-C", str(project), "init"]) == EXIT_OK
    (project / ".roadkeep" / ".git").mkdir(parents=True)
    capsys.readouterr()
    assert main(["-C", str(project), "uninstall", "--engine"]) == EXIT_USAGE
    said = capsys.readouterr()
    assert "is a clone and not a vendored copy" in said.err
    # And the row above it does not claim a write that did not happen.
    assert "deleted" not in said.out, said.out
    assert (project / ".roadkeep").is_dir()
