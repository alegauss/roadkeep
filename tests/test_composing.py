"""The commands this tool composes, run rather than matched (RK1209).

Four tasks found the same defect and no test found any of them, because every test that
covered a composed command asserted the *sentence was printed*. Matching a composed command
tests the composer against itself: `test_the_command_offers_a_follow_up_that_runs` was named
for the claim it did not make, and stayed green for as long as the command it described
refused.

Two properties, and the first is the one that lasts. The **census** is total, so a site added
tomorrow is a red here until somebody says whether it is exercised; and what is exercised is
*executed*, through one instrument rather than a fourth hand-written copy of it.

The honest state of the second is written down in `composing.SITES` rather than implied:
thirty-odd sites have never been run, and this file is where that stops being invisible.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from composing import SITES, STATES, census, commands, filled, runs, supplied
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.linting import Finding, lint
from roadkeep.provenance import invocation
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


def test_the_unreached_are_named_as_work_and_not_as_an_exemption():
    """The number is the finding. Six sites are executed and the rest have never been run,
    which is what four separate tasks each discovered one instance of."""
    unreached = [one.where for one in SITES if one.state == "unreached"]
    assert unreached, "if this empties, the row that says so should go too"
    # Stated as a bound rather than a count, so ordinary progress does not fail this file:
    # what a reader needs is which half they are standing on.
    assert len(unreached) < len(SITES), "everything unreached would mean nothing is covered"


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
