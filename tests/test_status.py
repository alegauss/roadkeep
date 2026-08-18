"""One marker, one file (RK7).

The rule under test is not "write the marker" — that is one line of code. It is that
every other place a status could be written is refused: the changelog, a rationale file
that grew a bullet, a second line for the same id, and ✅ in a file whose whole point is
that it holds only open work.

Each refusal leaves the roadmap byte-identical, because a command that half-applies a
status is how two files come to disagree in the first place.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pytest

from roadkeep.authoring import DuplicateId, StatusElsewhere, set_status
from roadkeep.backlog import NotOpen
from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, build_parser, main
from roadkeep.config import Config
from roadkeep.kernel.document import RoundTripError
from roadkeep.kernel.schema import SchemaError

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"

RK1 = "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1"
RK2 = "- 💭 **RK2** (deps: RK1) **A second symptom** — Because of another reason. → §RK2"

BACKLOG = f"""# Roadmap

## Block A — The model

{RK1}
{RK2}
"""

LEDGER = """# Shipped

## Block A — The model
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.
"""


def project(
    tmp_path: Path,
    *,
    roadmap: str = BACKLOG,
    changelog: str | None = LEDGER,
    improvements: str | None = RATIONALE,
) -> Config:
    declared = {ROADMAP: roadmap, CHANGELOG: changelog, IMPROVEMENTS: improvements}
    lines = ['prefix = "RK"', "[files]"]
    lines += [
        f'{role} = "{path}"'
        for role, path in (
            ("roadmap", ROADMAP),
            ("changelog", CHANGELOG),
            ("improvements", IMPROVEMENTS),
        )
        if declared[path] is not None
    ]
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for path, body in declared.items():
        if body is None:
            continue
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def read(config: Config, name: str = ROADMAP) -> str:
    with (config.root / name).open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


# -- writing the marker ------------------------------------------------------


def test_the_marker_is_written_and_nothing_else_in_the_file_moves(tmp_path):
    config = project(tmp_path)
    change = set_status(config, "RK1", "🛠")
    assert (change.before, change.after) == ("📋", "🛠")
    assert change.changed
    assert read(config) == BACKLOG.replace("- 📋 **RK1**", "- 🛠 **RK1**")
    assert change.lineno == 5


def test_the_line_is_re_rendered_and_not_patched(tmp_path):
    # The marker is a field, so the line comes back from `Schema.render`: a substitution
    # would happily write a marker into a line the schema would refuse.
    config = project(tmp_path)
    change = set_status(config, "RK2", "⏳")
    assert change.rendered == RK2.replace("💭", "⏳")
    assert config.document("roadmap").non_canonical == ()


def test_setting_the_marker_it_already_has_writes_nothing(tmp_path):
    config = project(tmp_path)
    before = read(config)
    change = set_status(config, "RK1", "📋")
    assert not change.changed
    assert read(config) == before


def test_the_file_keeps_its_line_endings(tmp_path):
    config = project(tmp_path, roadmap=BACKLOG.replace("\n", "\r\n"))
    set_status(config, "RK1", "🛠")
    written = read(config)
    assert "- 🛠 **RK1**" in written
    assert "\n" not in written.replace("\r\n", "")


def test_an_annotation_that_cached_this_marker_follows_it(tmp_path):
    # The cache goes stale in the write that changes the marker, and nothing else would
    # ever revisit it (RK8).
    annotated = BACKLOG.replace("(deps: RK1)", "(deps: RK1 📋)")
    config = project(tmp_path, roadmap=annotated)
    change = set_status(config, "RK1", "🛠")
    assert change.refreshed == ("RK2",)
    assert read(config) == annotated.replace("- 📋 **RK1**", "- 🛠 **RK1**").replace(
        "(deps: RK1 📋)", "(deps: RK1 🛠)"
    )


def test_an_unannotated_dependent_is_left_alone(tmp_path):
    # Nothing was cached, so there is nothing to correct: a write that annotated every
    # open dep would churn half the file to say what `deps <id>` answers better.
    config = project(tmp_path)
    change = set_status(config, "RK1", "🛠")
    assert change.refreshed == ()
    assert read(config) == BACKLOG.replace("- 📋 **RK1**", "- 🛠 **RK1**")


# -- the second file is always refused ---------------------------------------


def test_a_task_in_the_changelog_is_refused_not_updated(tmp_path):
    # The disagreement itself: the id is open in the roadmap and shipped in the ledger.
    config = project(
        tmp_path,
        changelog=LEDGER + "\n- ✅ **RK1** **A first symptom** — Because of a reason.\n",
    )
    with pytest.raises(StatusElsewhere) as raised:
        set_status(config, "RK1", "🛠")
    assert "changelog" in str(raised.value) and f"{CHANGELOG}:5" in str(raised.value)
    assert read(config) == BACKLOG


def test_an_entry_naming_a_half_is_the_one_pair_that_is_not_a_disagreement(tmp_path):
    """RK1114. `ship --part` writes a qualified entry and leaves the line open at ⏳ on purpose,
    so a ⏳ line beside it is the two files agreeing — and refusing it left the state the tool
    creates to mean "come back to this" as the one state no verb could start work on: measured
    on dockerdesk, `pick` named the line, `brief` called it ready, `brief --claim` refused."""
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace("- 📋 **RK1**", "- ⏳ **RK1**"),
        changelog=LEDGER
        + "\n- ✅ **RK1 (local half)** **A first symptom** — Because of a reason.\n",
    )
    change = set_status(config, "RK1", "🛠")
    assert change.before == "⏳" and change.after == "🛠"
    assert change.claim.name == "CLAIMED"


def test_an_unqualified_entry_is_still_the_disagreement(tmp_path):
    # The qualifier and never the marker (RK1075, RK1080), which is what keeps the relaxation
    # from reading every ledger entry as a live partial: an entry naming no half says the whole
    # of it shipped, and that beside an open line is the state `id.two-files` reports.
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace("- 📋 **RK1**", "- ⏳ **RK1**"),
        changelog=LEDGER + "\n- ✅ **RK1** **A first symptom** — Because of a reason.\n",
    )
    with pytest.raises(StatusElsewhere):
        set_status(config, "RK1", "🛠")
    assert read(config) == BACKLOG.replace("- 📋 **RK1**", "- ⏳ **RK1**")


def test_a_rationale_file_that_grew_a_marker_is_refused(tmp_path):
    config = project(
        tmp_path,
        improvements=RATIONALE + f"\n{RK1}\n",
    )
    with pytest.raises(StatusElsewhere) as raised:
        set_status(config, "RK1", "⏳")
    assert "improvements" in str(raised.value)
    assert read(config) == BACKLOG


def test_two_lines_for_one_id_are_two_statuses(tmp_path):
    config = project(tmp_path, roadmap=BACKLOG + f"{RK1.replace('📋', '⏳')}\n")
    with pytest.raises(DuplicateId) as raised:
        set_status(config, "RK1", "🛠")
    assert f"{ROADMAP}:5, 7" in str(raised.value)
    assert read(config) == BACKLOG + f"{RK1.replace('📋', '⏳')}\n"


def test_the_shipped_marker_is_refused_by_the_schema(tmp_path):
    # Not a special case in `status`: a roadmap that can say "done" is a second source of
    # truth, so the marker set itself excludes it and `ship` is the only way there.
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        set_status(config, "RK1", "✅")
    assert [v.code for v in raised.value.violations] == ["status.shipped"]
    assert read(config) == BACKLOG


def test_a_marker_outside_the_declared_set_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        set_status(config, "RK1", "🚀")
    assert [v.code for v in raised.value.violations] == ["status.unknown"]
    assert read(config) == BACKLOG


# -- the task has to be there ------------------------------------------------


def test_an_unknown_id_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotOpen) as raised:
        set_status(config, "RK9", "🛠")
    assert "nothing there carries that id" in str(raised.value)


def test_an_id_that_only_shipped_says_where_it_went(tmp_path):
    config = project(
        tmp_path,
        roadmap=BACKLOG.replace(f"{RK1}\n", ""),
        changelog=LEDGER + "\n- ✅ **RK1** **A first symptom** — Because of a reason.\n",
    )
    with pytest.raises(NotOpen) as raised:
        set_status(config, "RK1", "🛠")
    assert "already in the changelog" in str(raised.value)


def test_a_drifted_file_is_not_rewritten(tmp_path):
    drifted = BACKLOG.replace("→ §RK2", "→ §4.2")
    config = project(tmp_path, roadmap=drifted)
    with pytest.raises(RoundTripError):
        set_status(config, "RK1", "🛠")
    assert read(config) == drifted


def test_a_project_with_only_a_roadmap_still_works(tmp_path):
    config = project(tmp_path, changelog=None, improvements=None)
    assert set_status(config, "RK1", "🛠").changed
    assert read(config) == BACKLOG.replace("- 📋 **RK1**", "- 🛠 **RK1**")


# -- the command -------------------------------------------------------------


def test_the_command_prints_the_transition(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK1", "🛠"]) == EXIT_OK
    # The write is the event (RK38): what changed, its block, and whether that block
    # is finished — which is all a hook gets, and all it needs.
    assert capsys.readouterr().out.splitlines() == [
        f"RK1 📋 → 🛠  {ROADMAP}:5",
        # Writing the in-progress marker is one of the three ways to start work, so it takes
        # a claim and says so (RK158): a claim moved without being named is the silence
        # RK119 argued against for the answer itself.
        "  claimed  held for 60m unless a marker moves it sooner",
        # What to stage, projections included (RK1130): a marker write refreshes the derived
        # block like every other governed write, and a commit that took the roadmap alone
        # left that refresh behind — `export.stale` in a clean checkout.
        f"  stage    git add -- {ROADMAP}",
        "  event    RK1  Block A  live",
    ]


def test_the_command_says_when_there_was_nothing_to_do(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK1", "📋"]) == EXIT_OK
    # Still an event: a hook cannot tell 'nothing to do' from 'never ran' otherwise.
    assert capsys.readouterr().out.splitlines() == [
        f"RK1 is already 📋  {ROADMAP}:5",
        "  event    RK1  Block A  live",
    ]


def test_json_carries_both_markers_and_whether_it_changed(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK2", "⏳", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert (payload["from"], payload["to"], payload["changed"]) == ("💭", "⏳", True)
    assert payload["file"] == ROADMAP and payload["line"] == 6


def test_a_refusal_exits_two_and_names_the_other_file(tmp_path, capsys):
    config = project(
        tmp_path,
        changelog=LEDGER + "\n- ✅ **RK1** **A first symptom** — Because of a reason.\n",
    )
    assert main(["-C", str(tmp_path), "status", "RK1", "🛠"]) == EXIT_USAGE
    assert "status lives in exactly one file" in capsys.readouterr().err
    assert read(config) == BACKLOG


def test_a_drifted_file_exits_one_because_the_gate_says_no(tmp_path, capsys):
    project(tmp_path, roadmap=BACKLOG.replace("→ §RK2", "→ §4.2"))
    assert main(["-C", str(tmp_path), "status", "RK1", "🛠"]) == EXIT_GATE
    assert "will not be rewritten" in capsys.readouterr().err


# -- the verb whose name reads as the report (RK339) --------------------------


def refused(tmp_path: Path, *argv: str) -> None:
    """Run a call argparse itself rejects, and assert the exit code (RK339).

    `main` returns a code for the refusals this tool composes; a parser error raises
    `SystemExit` before any handler is reached, which is exactly the path under test.
    """
    with pytest.raises(SystemExit) as caught:
        main(["-C", str(tmp_path), *argv])
    assert caught.value.code == EXIT_USAGE


def test_status_with_no_arguments_says_it_writes_and_names_the_report(tmp_path, capsys):
    # `git status`, `docker status`, `systemctl status`: every other tool spends this name on
    # a read-only summary, so the verb typed wanting the backlog's state is the one that
    # takes arguments — and what came back was argparse naming neither fact.
    project(tmp_path)
    refused(tmp_path, "status")

    err = capsys.readouterr().err
    assert "status writes a marker" in err
    assert "`stats`" in err and "one character apart" in err
    # Nothing was written and nothing was at risk: the required positionals are what make
    # the mistake fail safe, and that is not what changed.
    assert (tmp_path / ROADMAP).read_text(encoding="utf-8") == BACKLOG


def test_the_same_refusal_answers_a_half_typed_call(tmp_path, capsys):
    # An id and no marker is the same missing-argument error, and a caller who reached for
    # the report and then guessed is exactly who needs the sentence.
    project(tmp_path)
    refused(tmp_path, "status", "RK1")
    assert "`stats`" in capsys.readouterr().err


def test_the_second_near_twin_answers_the_same_way(tmp_path, capsys):
    # The read RK339 asked for, and there is exactly one other pair in forty-one verbs that
    # differs by one edit *and* differs in whether it needs a positional.
    project(tmp_path)
    refused(tmp_path, "claim")

    err = capsys.readouterr().err
    assert "claim reads one line's scope back" in err and "`claims`" in err


def test_a_verb_with_no_twin_still_gets_argparses_own_answer(tmp_path, capsys):
    # One message per pair that has one, and never a second parser behaviour to reason about:
    # a missing argument on a verb nothing collides with reads exactly as it always did.
    project(tmp_path)
    refused(tmp_path, "show")
    assert "the following arguments are required" in capsys.readouterr().err


def test_an_unknown_flag_is_not_a_missing_argument(tmp_path, capsys):
    # Narrow on purpose: the sentence answers the caller who gave too little, and a typo in a
    # flag name is a different mistake that the twin's name does not explain. It is now a
    # refusal this tool writes rather than argparse's (RK1026), so it *returns* a code like
    # every other composed refusal — the mistake is the same one and it says which verb.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK1", "🛠", "--nope"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "`status` declares no --nope" in err
    assert "`stats`" not in err, "the twin's name explains a different mistake"


# -- the pair nobody has typed yet (RK350) ------------------------------------


def verbs(
    parser: argparse.ArgumentParser, path: tuple[str, ...] = ()
) -> dict[tuple[str, ...], argparse.ArgumentParser]:
    """Every subcommand this CLI declares, keyed by the words that reach it.

    Nested ones included, because a `_Verb` hands its class down and `section add` is one:
    a near-twin a level below the top is the same mistake with the same fix.
    """
    found: dict[tuple[str, ...], argparse.ArgumentParser] = {}
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in action.choices.items():
                found[(*path, name)] = sub
                found.update(verbs(sub, (*path, name)))
    return found


def needs_an_argument(parser: argparse.ArgumentParser) -> bool:
    """Whether this verb refuses when it is typed bare, which is the whole mistake."""
    return any(
        not action.option_strings
        and not isinstance(action, argparse._SubParsersAction)
        and action.nargs not in ("?", "*")
        for action in parser._actions
    )


def one_edit_apart(left: str, right: str) -> bool:
    """A distance of exactly one: a letter typed, dropped or changed."""
    if abs(len(left) - len(right)) > 1:
        return False
    row = list(range(len(right) + 1))
    for index, here in enumerate(left, start=1):
        following = [index]
        for column, there in enumerate(right, start=1):
            following.append(
                min(row[column] + 1, following[column - 1] + 1, row[column - 1] + (here != there))
            )
        row = following
    return row[-1] == 1


def near_twins() -> list[tuple[tuple[str, ...], str, argparse.ArgumentParser]]:
    """The verb that needs an argument, and the sibling one edit away that does not.

    Siblings, because that is where the confusion lives: `record add` and `section add` are
    reached by different first words, so neither is what the other's typo produces. And
    **exactly one** of the pair, which is what leaves `lint`/`list` and `ship`/`show` out —
    a pair where both calls fail the same way is one where neither name explains the other's
    refusal, and a gate demanding prose there would be answered with prose nobody needed.
    """
    kin: dict[tuple[str, ...], list[tuple[str, argparse.ArgumentParser]]] = {}
    for path, parser in verbs(build_parser()).items():
        kin.setdefault(path[:-1], []).append((path[-1], parser))

    found = []
    for family, siblings in kin.items():
        for index, (name, parser) in enumerate(siblings):
            for other, its in siblings[index + 1 :]:
                if not one_edit_apart(name, other) or needs_an_argument(parser) == (
                    needs_an_argument(its)
                ):
                    continue
                writes = (name, parser) if needs_an_argument(parser) else (other, its)
                reads = other if writes[0] == name else name
                found.append(((*family, writes[0]), reads, writes[1]))
    return found


def test_every_verb_that_shadows_a_report_declares_the_sentence():
    """The survey RK339 ran by hand, kept (RK350).

    That one was a script: edit distance over the verbs, crossed with whether each needs a
    positional, run once and thrown away. So the third pair would be found the way the first
    two were — by somebody typing the report's name and reading `error: the following
    arguments are required`. Both halves are read off the parsers here, the distance from
    their names and the requirement from their actions, so a verb added tomorrow is measured
    by this and never by a session.
    """
    missing = [path for path, _, parser in near_twins() if parser.get_default("twin") is None]
    assert missing == []


def test_the_survey_still_finds_the_two_pairs_it_was_written_from():
    # A property over a list read wrong is a test that passes by finding nothing, which is
    # exactly the failure `test_every_module_is_named_in_the_layout_index` was written against.
    assert {(path[-1], reads) for path, reads, _ in near_twins()} == {
        ("status", "stats"),
        ("claim", "claims"),
    }


def test_every_near_twin_prints_its_sentence_when_it_is_typed_bare(tmp_path, capsys):
    """The other half of the same property (RK362): declared is not delivered.

    Whether a `twin` default ever becomes output is `_Verb.error`, which fires on a substring
    of the sentence argparse composes — in argparse's English. The two pairs alive today each
    have a test that reads the printed words; a pair added tomorrow inherits the declaration
    gate and neither of those, and a Python release rewording that message turns the sentence
    off for every pair at once while leaving those green.

    It asserts only that the verb's own sentence arrived and argparse's did not, which is what
    keeps it from being a third copy of the two tests above: those say *which* words are right.
    """
    for path, _, parser in near_twins():
        refused(tmp_path, *path)
        err = capsys.readouterr().err
        assert parser.get_default("twin") in err
        # The whole delivery: `_Verb.error` short-circuited instead of falling through.
        assert "the following arguments are required" not in err


# -- the one refusal roadkeep did not write (RK1026) --------------------------


def test_an_unrecognised_flag_names_the_verb_s_own_surface_and_not_the_tool_s(tmp_path, capsys):
    """The reproduction. `ship RK1 --note "…"` printed argparse's usage line, thirty-odd
    verbs, and the **whole rejected value** — a paragraph meant for `--why`, burying the one
    line that mattered under text the caller had just typed."""
    project(tmp_path)
    prose = "a paragraph of prose meant for the why field, long enough to bury a message"
    assert main(["-C", str(tmp_path), "ship", "RK1", "--note", prose]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "`ship` declares no --note" in err
    # The verb's own surface, which is short, and never the tool's, which is not.
    assert "--why" in err and "--part" in err
    assert "add" not in err.split("takes")[1].split("see")[0]
    # The value is the caller's and the refusal does not read it back at them: the token is
    # the whole subject. RK86's capture offer below still reproduces the argv, deliberately —
    # that line exists to be pasted, and this one exists to be read.
    refusal = err.split("If roadkeep itself")[0]
    assert prose not in refusal


def test_a_flag_close_enough_to_be_a_typo_is_named_and_a_far_one_is_not(tmp_path, capsys):
    """A guess that is wrong is worse than the list: at `difflib`'s own default `--note` is
    offered `--lines`, which sends a caller who wanted `--why` to weigh a flag about
    something else entirely. `--seciton` is the case worth catching and scores far above."""
    project(tmp_path)
    argv = ["-C", str(tmp_path), "add", "--block", "A", "--symptom", "x", "--why", "A why."]
    assert main([*argv, "--seciton", "T"]) == EXIT_USAGE
    assert "did you mean `--section`?" in capsys.readouterr().err
    assert main(["-C", str(tmp_path), "ship", "RK1", "--note", "x"]) == EXIT_USAGE
    assert "did you mean" not in capsys.readouterr().err


def test_a_nested_verb_answers_for_itself(tmp_path, capsys):
    """The surface named is the one that was reached, not the family above it: `non-goal`
    declares subcommands and `non-goal list` declares the flags."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "non-goal", "list", "--bogus"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "`non-goal list` declares no --bogus" in err
    assert "non-goal list --help" in err


def test_one_argument_too_many_is_a_different_sentence(tmp_path, capsys):
    """A stray positional is not a flag typo, and naming the flags of a verb that takes an
    id would be advice about a mistake nobody made."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK1", "RK2"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "takes no further argument" in err and "'RK2'" in err
    assert "declares no" not in err


def test_a_verb_that_is_not_a_verb_is_still_argparse_s(tmp_path):
    """The bound. What this took back is the unrecognised *option*; an invalid choice is a
    message about the thing the caller got wrong, and argparse's is that message."""
    project(tmp_path)
    with pytest.raises(SystemExit) as caught:
        main(["-C", str(tmp_path), "shipp", "RK1"])
    assert caught.value.code == EXIT_USAGE


# -- the write a prefix reached (RK1032) -------------------------------------


#: Every flag this CLI declares as turning a read-only verb into a write, with a prefix that
#: reached it. Read as a table because that is what made this a task and not a preference:
#: each row was a write nobody typed, reported as a success.
WROTE = (
    ("lint", "--f", "--fix"),
    ("lint", "--fi", "--fix"),
    ("claims", "--pr", "--prune"),
    ("brief", "--cl", "--claim"),
    ("pick", "--cla", "--claim"),
)


@pytest.mark.parametrize(("verb", "typed", "meant"), WROTE)
def test_a_prefix_no_longer_reaches_the_flag_that_writes(tmp_path, capsys, verb, typed, meant):
    """`roadkeep lint --f` wrote files. argparse resolves any unambiguous prefix by default,
    and the four flags it handed over that way are exactly this CLI's own `writes_when` —
    the declaration `dispatch` reads to decide whether the write lock is taken."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), verb, typed]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert f"`{verb}` declares no {typed}" in err
    assert meant in err, "the flag meant is in the list even where difflib finds no hit"


@pytest.mark.parametrize(("verb", "typed", "meant"), WROTE)
def test_the_full_spelling_is_untouched(tmp_path, capsys, verb, typed, meant):
    """What this removes is an affordance nobody documented — no help string, no sentence of
    the shipped skill and no message in this tree spells a flag short. Every written
    spelling still parses, which is the half that must not move."""
    assert build_parser().parse_args([verb, meant]) is not None


def test_a_flag_typed_before_the_verb_is_the_top_level_s(tmp_path, capsys):
    """Which surface answers is decided by where the flag was typed: `roadkeep --vers lint`
    is somebody reaching for `--version`, and `lint`'s options would send them to a `--help`
    with none of what they wanted."""
    project(tmp_path)
    assert main(["--vers", "-C", str(tmp_path), "lint"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "`roadkeep` declares no --vers — did you mean `--version`?" in err
    # The name and the command are two things: one string for both prints a door that opens
    # nothing.
    assert "roadkeep roadkeep" not in err


# -- one field, two names (RK1038) -------------------------------------------


#: Every spelling this CLI gives a prose field a caller writes, and what each one is. A
#: declared set for `_MAY_GLOB`'s reason: a fourth name is a decision somebody makes rather
#: than a synonym somebody invents, and an exemption nobody can see reads exactly like a rule
#: being kept. RK399 settled the same question for the marker and kept both names accepted.
SPELLINGS = {
    ("--why",): "the task's one sentence, on the nine verbs that write one",
    ("--reason", "--why"): "the same sentence on `defer` and `retire`, which name it "
    "`--reason` in the shipped skill and accept both (RK1038)",
    ("--body",): "a section's paragraph, which is a different field with its own limit",
    ("--section-body",): "that paragraph inside an `add`, where the line is written too",
    # RK1176. Not a synonym for the sentence and not a paragraph: a clause naming the address
    # of the rationale a shipment overtook, which lands inside the `why` the ledger publishes.
    # It reads the pipe for the reason the sentence does — the address carries a `§`, which a
    # shell reads before this program does.
    ("--superseded-design",): "the clause naming an overtaken design, on `ship` alone",
    # RK1187. The falsifiable claim the line *is*, with a limit of its own — `amend` excludes
    # it for that reason and `restate` is its door. It reads the pipe because it carries the
    # backtick and the apostrophe a `why` does, which is not the same as being one.
    ("--symptom",): "the claim a line makes, on `restate` alone",
}


def prose_fields() -> dict[tuple[str, ...], list[tuple[str, ...]]]:
    """Every prose field this CLI declares, by the option strings that reach it.

    Read off `reads_stdin`, which is where each verb declares that one of its fields arrives
    on a pipe (RK171) — a claim about one command, kept on its own parser. So a verb added
    tomorrow is measured here rather than remembered.
    """
    found: dict[tuple[str, ...], list[tuple[str, ...]]] = {}
    for path, parser in verbs(build_parser()).items():
        for one in parser.get_default("reads_stdin") or ():
            names = tuple(
                option
                for action in parser._actions
                if action.dest == one.dest
                for option in action.option_strings
            )
            found.setdefault(names, []).append(path)
    return found


def test_the_prose_field_a_caller_writes_is_reachable_as_why(tmp_path, capsys):
    """The defect. `defer` and `retire` require the field, so a caller who spelled it the way
    the other nine verbs do got `error: the following arguments are required: --reason` —
    argparse naming what is missing and never what was typed."""
    project(tmp_path)
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "retire", "RK1", "--why", "Not work after all."]) == EXIT_OK
    # The spelling reached the handler and the write landed: the alias is the same field.
    assert "🗑 **RK1**" in read(config, CHANGELOG)
    assert "**RK1** (deps:" not in read(config)  # the open line left the roadmap
    capsys.readouterr()
    # And the refusal that stays names both, so neither spelling is the one nobody knows.
    with pytest.raises(SystemExit):
        main(["-C", str(tmp_path), "defer", "RK2"])
    assert "--reason/--why" in capsys.readouterr().err


def test_no_verb_spells_a_prose_field_a_way_nothing_else_does():
    """The closure. A third name for the one sentence is a red here until somebody writes
    down which field it is — which is the cost of a synonym, paid once, in a sentence."""
    found = prose_fields()
    assert set(found) == set(SPELLINGS), {
        "declared, no row": set(found) - set(SPELLINGS),
        "row, not declared": set(SPELLINGS) - set(found),
    }
    for names, where in found.items():
        assert SPELLINGS[names] and where, names


def test_the_two_that_rename_it_accept_the_name_the_rest_use():
    """The rule itself, stated so that dropping the alias is a red rather than a quiet
    return to the state this task was filed from."""
    for names, where in prose_fields().items():
        if names in (("--body",), ("--section-body",)):
            continue  # a paragraph is a different field, with its own limit
        if names in (("--superseded-design",), ("--symptom",)):
            # A clause about another address rather than this line's own sentence (RK1176),
            # and the claim the line is rather than the reason for it (RK1187). The alias rule
            # does not reach either: both are prose that reads the pipe, and neither is a
            # second name *of* anything — a `--symptom` accepting `--why` would make the two
            # fields `amend` deliberately keeps apart one field with two spellings.
            continue
        assert "--why" in names, (names, where)


# -- and the surface that is not only its flags (RK1254) ----------------------


def test_a_positional_spelled_as_a_flag_is_named_as_a_position(tmp_path, capsys):
    """The mirror of the sentence above, which RK1026 did not make. `show --id RK1` was
    answered with `takes --no-body, --json` — short, correct, and unable to contain the answer
    `show RK1`, because a verb's surface is not only its flags.

    Met four times on one throwaway project: `show --id`, `retire --id`, `renumber --from`,
    `brief --task`. Invited rather than hypothetical — `add` really does take `--id`, so a
    caller who learned it there spells it that way where the id is positional."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "--id", "RK1"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "`id` is taken by position" in err
    # And the answer is a runnable call, not a name to work out the placement of.
    from roadkeep.provenance import invocation

    assert f"{invocation()} show <id>" in err


def test_the_positionals_are_their_own_row_and_not_folded_into_takes(tmp_path, capsys):
    """Which of the two an argument is was exactly what the caller had wrong, so one list
    holding both would spell `<id>` beside `--json` as though the difference were
    punctuation."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "--task", "RK1"]) == EXIT_USAGE
    err = capsys.readouterr().err
    takes = err.split("takes")[1].split("by order")[0]
    assert "<id>" not in takes
    assert "by order <id>" in err


def test_a_verb_with_no_positionals_grows_no_row(tmp_path, capsys):
    """A heading over nothing is a line every caller reads and no caller uses (RK16)."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "lint", "--fixx"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "did you mean `--fix`?" in err
    assert "by order" not in err


def test_a_flag_that_is_a_near_miss_is_still_answered_as_a_flag(tmp_path, capsys):
    """The order of the two guesses, and it is not arbitrary: a caller who typed `--blockk`
    wanted `--block`, and sending them to a positional because the bare word also scores
    would be a worse answer than the one that already worked."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "list", "--blockk", "A"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "did you mean `--block`?" in err
    assert "taken by position" not in err


def test_a_flag_matching_nothing_still_gets_the_row(tmp_path, capsys):
    """`--from` is not `id` by any distance, so no sentence is composed — and the row is
    still what tells the caller the verb takes one."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "renumber", "--from", "RK1", "--to", "RK9"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "taken by position" not in err
    assert "by order <id>" in err


def test_the_names_are_the_ones_help_prints(tmp_path, capsys):
    """The metavar where a parser declares one, so a refusal and a `--help` screen do not
    spell one argument two ways."""
    from roadkeep.cli import _positionals, build_parser

    (verb,) = [
        one.choices["record"]
        for one in build_parser()._actions
        if getattr(one, "choices", None)
    ]
    # A family reaches its own subcommands through an action whose choices are verbs, and
    # naming that here would offer a command as a value.
    assert _positionals(verb) == ()


def test_every_verb_that_takes_an_id_by_position_says_so():
    """The property rather than the four instances: whatever a verb declares by position is
    what its refusal names, read off the parser and never a second list."""
    from roadkeep.cli import _positionals, build_parser

    (actions,) = [one for one in build_parser()._actions if getattr(one, "choices", None)]
    for name in ("show", "brief", "retire", "renumber", "amend"):
        assert "id" in _positionals(actions.choices[name]), name
