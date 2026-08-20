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
from roadkeep.linting import lint
from roadkeep.provenance import invocation
from roadkeep.remedying import BLANK, remedy


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
    # A bare ellipsis stands for "and the rest of a call", with no flag in front to fill from.
    assert filled(["add", "--block", "Z", "…"]) == ["add", "--block", "Z"]


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
    ]
    assert main(shipping) == EXIT_USAGE
    said = capsys.readouterr().err
    ran = runs(root, said)
    assert ran and ran[0][:2] == ["declare", "decisions"], said
    # And the refused call now lands, which is the half a matched sentence cannot claim.
    assert main(shipping) == EXIT_OK
    capsys.readouterr()
    assert "The store is the repository" in (root / "docs" / "DECISIONS.md").read_text(
        encoding="utf-8"
    )
    assert lint(Config.discover(root)).clean
