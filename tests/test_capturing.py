"""The report a losing session can write, and the four things it must not become (RK85).

Every assertion here is about a defect *in this tool*, hit in somebody else's repository,
by an agent whose session is about to end. That reporter has the facts and no way to send
them; what arrives instead is a paragraph written afterwards, in the genre this repository
was built to distrust.

* **The claim is refused, not the capture.** `symptom` and `why` are judged against this
  repository's schema — the backlog the line is destined for — before the command is run.
  A report that lands inside the limits was constrained where the claim was made.
* **It never composes the claim.** L4 is not suspended because the author is a machine in
  a hurry: what is rendered for the maintainer is the `add` command, and the id in it stays
  derived where the backlog is.
* **A crash is the report.** The most identifying artefact a session holds is a traceback,
  and it is exactly what a narration cannot reproduce.
* **The observed exit code is a fact, not this command's.** `report` succeeds when it
  captures a failure — the whole reason to run it is that something failed.

And the affordance that makes any of it reachable (RK86): a **fault** closes with the capture
command. A refusal that names only the rule it applied is a dead end in the one case where the
rule is the defect, and what an agent does with a dead end is work around it quietly — so the
surface with the worst failures produces the fewest reports. The two rules asserted below are
that it costs nothing on the runs that succeed, and that it never claims the refusal was wrong:
this tool has no way to know and no model to guess (L4).

A **verdict** is the exception, and it is RK271's (below): a read-only command's own 1 is the
answer somebody asked for, so `lint` reporting a finding closes with nothing. The exit code
alone cannot say which of the two a 1 is — a crashed `lint` is also a read-only 1 — so `main`
carries that as a flag rather than inferring it here.
"""

from __future__ import annotations

import ast
import io
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from roadkeep.provenance import invocation

from roadkeep.capturing import (
    HOME,
    IGNORE_RULE,
    PARTS,
    REPORTS,
    TEXT_VARIABLES,
    STOPPED_NOTICE,
    Capture,
    Failure,
    _USAGE,
    _tail,
    body,
    capture,
    check,
    delivered,
    handoff,
    keep,
    observe,
    offer,
)
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.provenance import engine

#: `src/`, for the subprocesses that read the codecs an interpreter settled at startup.
PACKAGE = Path(__file__).resolve().parents[1] / "src"

ROADMAP = "docs/ROADMAP.md"

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
"""

BROKEN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: RK99) **A first symptom** — Because of a reason. → §RK1
"""

CONFIG = f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\n'

SYMPTOM = "A dep nothing satisfies is reported without the group it is in"
WHY = "The finding addresses the line and not the field, so the fix is guessed."


def project(tmp_path: Path, *, roadmap: str = CLEAN, config: str = CONFIG) -> Path:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    path = tmp_path / ROADMAP
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(roadmap)
    return tmp_path


# -- the claim is judged where it is made ------------------------------------


def test_a_claim_inside_the_limits_is_accepted():
    assert check(SYMPTOM, WHY, "F") == ()


def test_a_symptom_over_this_repositorys_limit_is_refused():
    violations = check("x" * (HOME.symptom_max + 1), WHY, "F")
    assert [v.field for v in violations] == ["symptom"]


def test_a_why_of_two_sentences_is_refused_here_and_not_at_the_maintainer():
    """The rule a schema can check standing in for the one it cannot: a second sentence is
    the signal the content belongs in a rationale, and an issue is where that goes unsaid."""
    violations = check(SYMPTOM, "It fails. It fails again.", "F")
    assert [v.field for v in violations] == ["why"]


def test_the_reporting_projects_looser_limit_does_not_travel_with_the_report(tmp_path):
    """A project that declares `symptom = 400` would otherwise export a line the
    maintainer's own `add` refuses — the limits that judge are the destination's."""
    project(tmp_path, config=CONFIG + "[limits]\nsymptom = 400\n")
    assert check("x" * 200, WHY, "F")[0].field == "symptom"


# -- what the capture holds --------------------------------------------------


def test_the_failing_command_is_re_run_and_its_exit_code_kept(tmp_path):
    root = project(tmp_path, roadmap=BROKEN)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)
    assert found.failure.exit_code == 1
    assert "RK99" in found.failure.output


def test_a_command_that_succeeds_is_captured_just_as_faithfully(tmp_path):
    """Nothing here decides whether the observed run was wrong. A defect whose symptom is
    "this exits 0 and should not" is a defect, and judging it would be having a model."""
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)
    assert found.failure.exit_code == 0


def test_the_capture_names_which_tree_answered(tmp_path):
    """RK79 is the dep: with two engines answering `0.1.0`, a stale plugin cache and a
    real defect are the same report."""
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)
    assert str(found.engine.home) in str(found)


def test_the_capture_carries_the_configuration_as_it_was_read(tmp_path):
    root = project(tmp_path, roadmap=BROKEN)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)
    assert found.config == CONFIG
    assert 'prefix = "RK"' in str(found)


def test_the_capture_quotes_the_line_the_engine_objected_to(tmp_path):
    """Verbatim and read back, never reconstructed: the line as it is on disk is what
    reproduces the defect, and a re-rendered one is a different line (L3)."""
    root = project(tmp_path, roadmap=BROKEN)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)
    assert found.failure.where == f"{ROADMAP}:5"
    assert found.source == BROKEN.splitlines()[4]


def test_an_address_the_output_never_printed_leaves_no_line(tmp_path):
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)
    assert found.failure.where is None and found.source is None


# -- a re-run that never reached the rule (RK440) ----------------------------


def test_a_re_run_refused_before_the_verb_ran_says_so(tmp_path):
    """RK440: two of Shio's three field reports carry a refusal that fires before the verb
    does any work — a missing `--why`, an id the ledger already held — filed under a symptom
    the output has nothing to do with. The capture is triage input, and one whose evidence
    contradicts its own claim costs more than none: it has to be reproduced by hand before
    it can be dismissed."""
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "add", "--block", "A"], root)
    assert found.failure.exit_code == EXIT_USAGE and found.failure.stopped
    assert "stopped" in str(found)
    assert found.as_dict()["stopped"] == "usage"


def test_the_set_it_recognises_is_this_clis_own_exit_code(tmp_path):
    """Off the number and never off the message: the two Shio filed came from the handlers
    and not from argparse, so a list of refusal sentences would have matched neither — and
    would be a second declaration of a contract `cli` already states."""
    assert _USAGE == EXIT_USAGE
    root = project(tmp_path)
    found = capture(
        SYMPTOM, WHY, "F", ["-C", str(root), "ship", "RK1"], root
    )
    assert found.failure.exit_code == EXIT_USAGE and found.failure.stopped
    assert "--why" in found.failure.output


def test_a_gate_finding_is_evidence_and_carries_no_annotation(tmp_path):
    root = project(tmp_path, roadmap=BROKEN)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)
    assert found.failure.exit_code == 1 and not found.failure.stopped
    assert "stopped" not in str(found) and "stopped" not in found.as_dict()


def test_the_annotation_is_never_a_verdict_on_whether_it_reproduces(tmp_path):
    """The argv *does* reproduce — the same command earns the same refusal, which is what
    `replay` asserts. What is in doubt is whether that refusal is the symptom above it, and
    that is a judgement about meaning this tool has no model to make (L4)."""
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "add", "--block", "A"], root)
    assert found.as_dict()["reproduces"] is True


def test_the_annotation_is_never_a_refusal_of_the_capture(tmp_path, capsys):
    """RK86 exists to make the capture the cheapest move a losing session has, and a report
    refused at the end of that session is the session lost. So the shape is stated to the one
    reader who can still correct the argv, and the capture is still taken and still kept."""
    root = project(tmp_path)
    code, out, err = run(
        capsys,
        [
            "-C", str(root), "report", "--symptom", SYMPTOM, "--why", WHY,
            "--", "-C", str(root), "add", "--block", "A",
        ],
    )
    assert code == EXIT_OK
    assert "A roadkeep field report" in out
    assert STOPPED_NOTICE in err
    assert list((root / REPORTS).iterdir())


def test_a_capture_that_reached_the_verb_is_told_nothing(tmp_path, capsys):
    root = project(tmp_path, roadmap=BROKEN)
    _, _, err = run(
        capsys,
        ["-C", str(root), "report", "--symptom", SYMPTOM, "--why", WHY,
         "--", "-C", str(root), "lint"],
    )
    assert STOPPED_NOTICE not in err


def test_a_crash_is_kept_because_it_is_the_most_identifying_fact_there_is(monkeypatch):
    def explode(*_args, **_kwargs):
        raise RuntimeError("the parser lost its footing")

    monkeypatch.setattr("roadkeep.cli.main", explode)
    failure = observe(["lint"])
    assert failure.exit_code == 1
    assert "RuntimeError: the parser lost its footing" in failure.traceback


def test_an_interrupt_is_not_swallowed_by_the_capture(monkeypatch):
    """`Exception` and not `BaseException`: an interrupt is the user asking for the session
    back, and no report is worth taking it from them."""

    def interrupt(*_args, **_kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr("roadkeep.cli.main", interrupt)
    with pytest.raises(KeyboardInterrupt):
        observe(["lint"])


def test_a_long_output_is_truncated_and_says_so():
    """A `lint` over an adopted corpus prints hundreds of findings: the first is the report
    and the rest is the corpus. A capped listing that does not say so reads as complete."""
    kept = _tail("\n".join(f"finding {n}" for n in range(200)))
    assert "not kept" in kept and kept.count("\n") < 60
    assert "finding 199" in kept and "finding 0\n" not in kept


def test_the_command_reads_back_as_a_shell_would_take_it():
    assert Failure(argv=("lint",), exit_code=1, output="x").command == "roadkeep lint"


# -- what it renders for the maintainer --------------------------------------


def test_the_capture_renders_the_command_that_files_it_and_not_a_line(tmp_path):
    """L4 holds for a machine in a hurry too. The id is `add`'s to derive, in the backlog
    that owns it — a report carrying one would be a report inventing an address."""
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)
    assert found.filing.startswith(f"{invocation()} add --block F --symptom ")
    assert SYMPTOM in found.filing and WHY in found.filing
    assert "RK" not in found.filing.replace("roadkeep", "")


# -- the command -------------------------------------------------------------


def run(capsys, argv: list[str]) -> tuple[int, str, str]:
    code = main(argv)
    out = capsys.readouterr()
    return code, out.out, out.err


def test_the_command_captures_a_failure_and_still_succeeds(tmp_path, capsys):
    root = project(tmp_path, roadmap=BROKEN)
    code, out, _ = run(
        capsys,
        ["-C", str(root), "report", "--symptom", SYMPTOM, "--why", WHY, "--", "-C", str(root), "lint"],
    )
    assert code == EXIT_OK
    assert "A roadkeep field report" in out and "exit     1" in out


def test_the_command_refuses_a_claim_over_the_limit_before_running_anything(tmp_path, capsys):
    root = project(tmp_path)
    code, out, err = run(
        capsys,
        [
            "-C",
            str(root),
            "report",
            "--symptom",
            "x" * (HOME.symptom_max + 1),
            "--why",
            WHY,
            "--",
            "lint",
        ],
    )
    assert code == EXIT_USAGE
    assert out == "" and "nothing captured" in err


def test_the_command_wants_the_command_that_failed(tmp_path, capsys):
    root = project(tmp_path)
    code, _, err = run(
        capsys, ["-C", str(root), "report", "--symptom", SYMPTOM, "--why", WHY]
    )
    assert code == EXIT_USAGE
    assert "after a bare --" in err


def test_nothing_leaves_the_machine():
    """A capture and not a client: no network in this path, nothing to authenticate, and
    no identity. Delivery is somebody typing a separate command, and RK87 governs it.

    Imports and not a text scan — the prose here argues about sockets, and a test a comment
    can fail is a test somebody deletes. `subprocess` is in the list because handing the
    body to `gh` must stay something a *person* runs: this composes that command line and
    never executes it.
    """
    tree = ast.parse(
        (Path(__file__).resolve().parents[1] / "src" / "roadkeep" / "capturing.py").read_text(
            encoding="utf-8"
        )
    )
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported |= {alias.name.split(".")[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert not imported & {"urllib", "http", "socket", "requests", "smtplib", "subprocess"}


# -- the offer a fault closes with, and a verdict does not (RK86, RK271) ------


def test_the_offer_substitutes_the_failing_argv_so_the_move_costs_nothing():
    said = offer(["-C", "/somewhere", "lint"])
    assert said.endswith(
        f'{invocation()} report --symptom "…" --why "…" -- -C /somewhere lint'
    )


def test_the_offer_composes_no_part_of_the_claim():
    """The two fields stay ellipses. A tool that guessed a symptom would be a tool with a
    model, and the sentence it guessed is the one a maintainer would then be reading."""
    said = offer(["lint"])
    assert '--symptom "…"' in said and '--why "…"' in said


def test_the_offer_names_no_argv_where_git_has_already_deleted_it():
    """RK484. Seen end to end: a real `git merge` of two branches that both appended under
    one block reaches the driver, which refuses correctly and closes with `report … -- merge
    .merge_file_tbx68e .merge_file_Vbi0WP .merge_file_0jMb5m` — three `%O %A %B` temporaries
    git removes when the driver returns, gone before the line finishes printing.

    The verb where RK86's offer is worth most is the one where it was never takeable: a merge
    refusal is met by somebody already stopped, who cannot commit until they resolve it. What
    is durable is the merge itself, so that is what is asked for."""
    said = offer(["merge", ".merge_file_tbx68e", ".merge_file_Vbi0WP", ".merge_file_0jMb5m",
                  "--path", "docs/ROADMAP.md"])
    assert ".merge_file_" not in said
    assert "report --symptom" not in said
    assert "git rev-parse HEAD MERGE_HEAD" in said
    # Still conditional, and still the same opening: what changed is the second line only.
    assert said.startswith(
        "If roadkeep itself is what is wrong here, capture it before the session ends:"
    )


def test_a_merge_run_by_hand_keeps_the_offer_it_can_take():
    """Matched on the paths and not on the verb: `merge` with three real files is runnable,
    and refusing to say so would trade one wrong line for another."""
    said = offer(["merge", "base.md", "ours.md", "theirs.md", "--path", "docs/ROADMAP.md"])
    assert said.endswith(
        f'{invocation()} report --symptom "…" --why "…" -- '
        f"merge base.md ours.md theirs.md --path docs/ROADMAP.md"
    )


def test_the_offer_never_says_the_refusal_was_wrong():
    """Conditional, because nothing here can know. `lint` was right in every case but the
    one this exists for, and a tool that apologised for its own gate would teach the wrong
    lesson in all the others."""
    said = offer(["lint"]).lower()
    assert said.startswith("if roadkeep itself is what is wrong here")
    assert "sorry" not in said and "bug" not in said


def test_a_refused_write_closes_with_the_offer(tmp_path, capsys):
    root = project(tmp_path)
    code = main(["-C", str(root), "add", "--block", "A", "--symptom", "x" * 200, "--why", "B."])
    err = capsys.readouterr().err
    assert code == EXIT_USAGE
    assert "symptom.too-long" in err and f"{invocation()} report --symptom" in err


def test_a_failing_gate_says_nothing_about_reporting_the_gate(tmp_path, capsys):
    """RK271: the exit `lint` was *asked for*, which is the one exit that is never about this
    tool — and the highest-traffic one, the action and the pre-commit hook both being a `lint`.

    The finding already names the file, the line and the rule, so two lines saying roadkeep
    itself may be wrong close a complete answer with a doubt about it, in a run that has no
    session to capture before the end of.
    """
    root = project(tmp_path, roadmap=BROKEN)
    code = main(["-C", str(root), "lint"])
    out, err = capsys.readouterr()
    assert code == 1
    assert "deps.unknown" in out and err == ""


def test_a_query_refused_for_what_it_was_asked_still_offers(tmp_path, capsys):
    """The other half of the same split: exit 2 is about the caller's input, and RK86's measured
    case is a caller who thinks the refusal is wrong. Read-only is not the discriminator on its
    own — the verdict is a read-only command's **1**, and nothing else."""
    root = project(tmp_path)
    code = main(["-C", str(root), "show", "RK9999"])
    assert code == EXIT_USAGE
    assert f"{invocation()} report --symptom" in capsys.readouterr().err


def test_a_command_that_succeeds_says_nothing_about_reporting(tmp_path, capsys):
    """It costs nothing on the runs that work, which is the whole reason it can live on
    every failure path instead of in a document somebody loads first."""
    root = project(tmp_path)
    assert main(["-C", str(root), "lint"]) == EXIT_OK
    assert "report" not in capsys.readouterr().err


def test_argparse_refuses_before_a_handler_exists_and_still_offers(capsys):
    # A verb that is not a verb is still argparse's to refuse, and RK86's offer follows it:
    # the argv is all this knows, and all the offer needs.
    with pytest.raises(SystemExit) as exited:
        main(["no-such-verb"])
    assert exited.value.code == EXIT_USAGE
    assert f"{invocation()} report --symptom" in capsys.readouterr().err


def test_a_flag_no_verb_declares_is_refused_by_this_tool_and_still_offers(capsys):
    # The half RK1026 took back: an unrecognised option is a refusal this tool composes, so
    # it returns a code like every other one — and the offer is printed either way, the
    # session where something is wrong being exactly what `report` exists for.
    assert main(["lint", "--no-such-flag"]) == EXIT_USAGE
    err = capsys.readouterr().err
    assert "`lint` declares no --no-such-flag" in err
    assert f"{invocation()} report --symptom" in err


def test_help_and_version_are_not_failures(capsys):
    with pytest.raises(SystemExit) as exited:
        main(["--help"])
    assert exited.value.code == 0
    assert f"{invocation()} report" not in capsys.readouterr().err


def test_report_never_offers_to_report_itself(tmp_path, capsys):
    root = project(tmp_path)
    code = main(
        ["-C", str(root), "report", "--symptom", SYMPTOM, "--why", "One. Two.", "--", "lint"]
    )
    err = capsys.readouterr().err
    assert code == EXIT_USAGE
    assert "nothing captured" in err and f"{invocation()} report --symptom" not in err


def test_the_hook_is_never_given_prose_to_answer_a_protocol_with(tmp_path, capsys, monkeypatch):
    """`guard` and `mcp` answer a harness, not an agent. A sentence on their stderr is read
    by nobody, and on their stdout it would be a parse error."""
    root = project(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    assert main(["-C", str(root), "guard"]) == EXIT_OK
    assert capsys.readouterr().err == ""


def test_a_crash_is_printed_and_closed_with_the_offer(tmp_path, capsys, monkeypatch):
    """The third place RK86 names. A traceback that reaches a terminal raw is a session
    that ends, and what it ends without is the report only that session could write.

    And the exit that proves RK271's split needs more than the exit code: this is a read-only
    command exiting 1, exactly like the test above, and it is the case the offer exists for.
    The difference is not visible afterwards, so `main` carries it as `faulted`.
    """
    root = project(tmp_path)

    def explode(*_args, **_kwargs):
        raise RuntimeError("the parser lost its footing")

    monkeypatch.setattr("roadkeep.cli._lint", explode)
    code = main(["-C", str(root), "lint"])
    err = capsys.readouterr().err
    assert code == 1
    assert "RuntimeError: the parser lost its footing" in err
    assert err.index("Traceback") < err.index(f"{invocation()} report --symptom")


# -- what may leave, and how (RK87) ------------------------------------------


def test_a_capture_goes_nowhere_by_default(tmp_path, capsys):
    """The obvious ending is that it files itself, and it is the one ending that cannot be
    taken back: a sample of a private repository, chosen by the code path that crashed."""
    root = project(tmp_path)
    code = main(["-C", str(root), "report", "--symptom", SYMPTOM, "--why", WHY, "--", "lint"])
    out, err = capsys.readouterr()
    assert code == EXIT_OK
    assert "A roadkeep field report" in out and "gh issue" not in out
    # RK89 keeps it, and RK87 still sends nothing: the two are not the same step. What is
    # on disk is local, gitignored, and waiting for somebody to decide.
    assert err.startswith(f"kept  {root / REPORTS}")
    assert "gh issue" not in err


def test_a_part_is_deleted_by_name_and_the_deletion_is_stated(tmp_path):
    root = project(tmp_path, roadmap=BROKEN)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root).without("config", "source")
    said = str(found)
    assert CONFIG.strip() not in said and found.source not in said
    # Named, or a maintainer reads a missing section as evidence that never existed.
    assert "omitted  config, source" in said


def test_every_part_that_carries_the_reporting_project_can_be_dropped(tmp_path):
    root = project(tmp_path, roadmap=BROKEN)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root).without(*PARTS)
    said = str(found)
    assert str(root) not in said and "RK99" not in said


def test_the_claim_itself_can_never_be_dropped(tmp_path):
    """An empty report is worse than no report: what is left has to still be a claim."""
    root = project(tmp_path)
    said = str(capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root).without(*PARTS))
    assert SYMPTOM in said and WHY in said and "exit" in said


def test_a_part_nobody_declared_is_refused_rather_than_ignored(tmp_path):
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["lint"], root)
    with pytest.raises(ValueError, match="no such part"):
        found.without("secrets")


def test_the_body_is_byte_for_byte_what_the_terminal_showed(tmp_path):
    """A reviewer approves what they read. A body composed differently from the preview is
    a body nobody reviewed."""
    root = project(tmp_path, roadmap=BROKEN)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root).without("config")
    assert body(found) == "```\n" + str(found) + "\n```"


def test_the_handoff_borrows_an_authentication_this_tool_never_holds():
    found = Capture(
        symptom=SYMPTOM,
        why=WHY,
        block="F",
        failure=Failure(argv=("lint",), exit_code=1, output=""),
        engine=engine(),
    )
    said = handoff(found, "alegauss/roadkeep")
    assert "Nothing was sent" in said
    assert "gh issue create -R alegauss/roadkeep" in said and SYMPTOM in said


def test_the_issue_body_is_stdout_and_the_command_is_stderr(tmp_path, capsys):
    """So the pipe is the operator's: `roadkeep report … --issue | gh issue create -F -`
    carries the artefact and nothing else."""
    root = project(tmp_path, config=CONFIG + '[report]\nupstream = "someone/theirs"\n')
    code = main(
        ["-C", str(root), "report", "--symptom", SYMPTOM, "--why", WHY, "--issue", "--", "lint"]
    )
    out, err = capsys.readouterr()
    assert code == EXIT_OK
    assert out.startswith("```") and "gh issue create" not in out
    assert "gh issue create -R someone/theirs" in err


def test_an_upstream_nobody_declared_is_refused_and_never_guessed(tmp_path, capsys):
    """A guessed destination is a private repository's contents in a stranger's tracker."""
    root = project(tmp_path)
    code = main(
        ["-C", str(root), "report", "--symptom", SYMPTOM, "--why", WHY, "--issue", "--", "lint"]
    )
    out, err = capsys.readouterr()
    assert code == EXIT_USAGE
    assert out == "" and "[report] upstream" in err


def test_a_fork_reports_to_itself(tmp_path, capsys):
    """The upstream is configuration and not a constant (L6)."""
    root = project(tmp_path, config=CONFIG + '[report]\nupstream = "someone/theirs"\n')
    main(["-C", str(root), "report", "--symptom", SYMPTOM, "--why", WHY, "--issue", "--to",
          "other/fork", "--", "lint"])
    assert "-R other/fork" in capsys.readouterr().err


def test_a_command_declared_to_survive_a_broken_config_survives_a_broken_one(tmp_path, capsys):
    """A TOML *syntax* error never reached `ConfigError`, so the commands that promise to
    tolerate a bad config did not tolerate the way one is most often bad — and `report`,
    whose whole subject is the session where something is wrong, crashed on the very file
    it was about to carry as evidence."""
    (tmp_path / "roadkeep.toml").write_text("prefix = [\n", encoding="utf-8")
    code = main(["-C", str(tmp_path), "report", "--symptom", SYMPTOM, "--why", WHY, "--", "lint"])
    assert code == EXIT_OK
    assert "A roadkeep field report" in capsys.readouterr().out


# -- the capture survives the session that took it (RK89) ---------------------


def test_a_capture_is_on_disk_before_it_is_printed(tmp_path):
    """What exists only on a stdout depends on the caller taking a second step, and this
    block's own RK86 is the record of second steps not being taken."""
    root = project(tmp_path)
    kept = keep(capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root), root)
    assert kept.path.is_file()
    assert kept.path.parent == root / REPORTS
    assert json.loads(kept.path.read_text(encoding="utf-8"))["symptom"] == SYMPTOM


def test_what_is_kept_is_what_was_produced(tmp_path):
    """One artefact and one set of contents: the file on disk is the text that was read,
    `--without` applied. A local copy that quietly held more would make the redaction a
    thing the operator has to be told about twice."""
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root).without("config")
    stored = json.loads(keep(found, root).path.read_text(encoding="utf-8"))
    assert "config" not in stored and stored["omitted"] == ["config"]


def test_two_captures_of_one_command_are_two_files(tmp_path):
    root = project(tmp_path)
    first = keep(capture(SYMPTOM, WHY, "F", ["lint"], root), root)
    second = keep(capture("A different symptom entirely", WHY, "F", ["lint"], root), root)
    assert first.path != second.path
    assert len(list((root / REPORTS).glob("*.json"))) == 2


def test_the_filename_names_the_command_that_failed(tmp_path):
    """Asked of the parser, not guessed: the first non-flag word is the value of `-C` half
    the time, and a filename naming a directory is a listing nobody can read."""
    root = project(tmp_path)
    kept = keep(capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root), root)
    assert "-lint-" in kept.path.name


# -- and the repository never has to see it ----------------------------------


def test_git_is_told_to_ignore_the_directory(tmp_path):
    root = project(tmp_path)
    keep(capture(SYMPTOM, WHY, "F", ["lint"], root), root)
    assert (root / ".gitignore").read_text(encoding="utf-8").splitlines() == [IGNORE_RULE]


def test_a_rule_that_already_covers_it_is_left_alone(tmp_path):
    """Append one line, only when absent. Reordering somebody's ignore rules to add one is
    the write this tool refuses everywhere else."""
    root = project(tmp_path)
    (root / ".gitignore").write_text("node_modules/\n.roadkeep\n*.log\n", encoding="utf-8")
    keep(capture(SYMPTOM, WHY, "F", ["lint"], root), root)
    assert (root / ".gitignore").read_text(encoding="utf-8") == "node_modules/\n.roadkeep\n*.log\n"


def test_nothing_already_there_is_reordered_or_rewritten(tmp_path):
    root = project(tmp_path)
    before = "# mine\nnode_modules/\n\n*.log\n"
    (root / ".gitignore").write_text(before, encoding="utf-8")
    keep(capture(SYMPTOM, WHY, "F", ["lint"], root), root)
    after = (root / ".gitignore").read_text(encoding="utf-8")
    assert after == before + f"{IGNORE_RULE}\n"


def test_a_file_with_no_trailing_newline_does_not_get_a_glued_rule(tmp_path):
    root = project(tmp_path)
    (root / ".gitignore").write_text("node_modules/", encoding="utf-8")
    keep(capture(SYMPTOM, WHY, "F", ["lint"], root), root)
    assert (root / ".gitignore").read_text(encoding="utf-8") == f"node_modules/\n{IGNORE_RULE}\n"


def test_keeping_the_capture_wins_over_teaching_git_about_it(tmp_path, monkeypatch):
    """If `.gitignore` cannot be written, say so and keep the capture anyway: the evidence
    is the point, and an unwritable ignore file is a sentence, not a failure."""
    root = project(tmp_path)

    opened = Path.open

    def refuse(self, *args, **kwargs):
        if self.name == ".gitignore":
            raise OSError("read-only file system")
        return opened(self, *args, **kwargs)

    monkeypatch.setattr(Path, "open", refuse)
    kept = keep(capture(SYMPTOM, WHY, "F", ["lint"], root), root)
    assert kept.path.is_file()
    assert "could not add" in kept.complaint


def test_the_command_says_where_it_kept_it_on_stderr(tmp_path, capsys):
    """stderr, so `--json` and `--issue` stay pipeable."""
    root = project(tmp_path)
    main(["-C", str(root), "report", "--json", "--symptom", SYMPTOM, "--why", WHY, "--", "lint"])
    out, err = capsys.readouterr()
    assert json.loads(out)["symptom"] == SYMPTOM
    assert "kept  " in err and str(REPORTS) in err


def test_the_command_says_which_of_the_two_captures_it_wrote(tmp_path, capsys):
    """RK481. Probed on a copy of Shio: `report` keeps a file, prints `kept <path>`, and
    `replay` on it answers *not replayable — the config declares three files the capture does
    not carry*. That refusal is correct and read too late: by then the reporting session is
    over, and the only caller who could have passed `--embed` was the one running `report`,
    which named the flag in no line it printed.

    Not-embedding stays the default — `--embed` is this project's text leaving it, and a tool
    that published a private repository's roadmap by being helpful is the worse failure. The
    silence was the defect, which is RK420's rule one module over."""
    root = project(tmp_path)
    main(["-C", str(root), "report", "--symptom", SYMPTOM, "--why", WHY, "--", "lint"])
    plain = capsys.readouterr().err
    assert "`--embed`" in plain and "replay  refuses it" in plain
    main(["-C", str(root), "report", "--embed", "--symptom", SYMPTOM, "--why", WHY, "--", "lint"])
    embedded = capsys.readouterr().err
    assert "replay  runs it anywhere" in embedded
    # And the flag is not advertised where it was already taken, which is the note nobody
    # reads by the third time (RK242's rule for the refusal's own note).
    assert "--embed" not in embedded


def test_the_replay_refusal_names_what_that_reader_can_actually_do(tmp_path):
    """The other voice (RK481): a reader holding a finished capture cannot pass `--embed` —
    the session is gone — but asking for one that was is a thing they can do. RK313's rule,
    which is that a message closes on something the reader can perform."""
    from roadkeep.capturing import Replay

    said = str(
        Replay(
            unstaged=("docs/ROADMAP.md",),
            recorded_exit=1,
            exit_code=1,
            reproduces=True,
            output="",
        )
    )
    assert "not replayable" in said and "ask for one taken with `--embed`" in said


def test_there_is_no_flag_for_not_keeping_it(tmp_path):
    """Unconditional. A capture nobody pruned costs kilobytes; a capture nobody kept costs
    the only session that could have identified the defect."""
    from roadkeep.cli import build_parser

    flags = {
        option
        for action in build_parser()._subparsers._group_actions[0].choices["report"]._actions
        for option in action.option_strings
    }
    assert not {"--no-keep", "--keep", "--dry-run"} & flags


# -- the half of the input the re-run cannot supply (RK341) -------------------


def report_under(root: Path, environment: dict[str, str], *without: str) -> dict:
    """One `report --json` in a process whose text handling is declared, parsed back.

    A subprocess, and not `main` here: the streams this process holds are pytest's, and the
    fact under test is the one an interpreter settles before its first line runs. `-m
    roadkeep.cli` deliberately — that is how this repository invokes the tool, and it loads
    `cli` twice, as `__main__` and as `roadkeep.cli`.
    """
    argv = [
        sys.executable,
        "-m",
        "roadkeep.cli",
        "-C",
        str(root),
        "report",
        "--symptom",
        SYMPTOM,
        "--why",
        WHY,
        "--block",
        "F",
        "--json",
    ]
    for part in without:
        argv += ["--without", part]
    done = subprocess.run(
        [*argv, "--", "lint"],
        capture_output=True,
        check=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONPATH": str(PACKAGE), **environment},
    )
    return json.loads(done.stdout)


def test_the_capture_records_the_codecs_the_environment_declared(tmp_path):
    """The whole of RK341 in one assertion: a capture taken under a declared encoding says so.

    Bounded to the variables that decide how a process reads and writes text — the class of
    cause that is outside the repository and that `--embed` therefore cannot stage.
    """
    found = report_under(project(tmp_path), {"PYTHONIOENCODING": "utf-8:surrogateescape"})
    said = found["environment"]
    assert said["declared"]["PYTHONIOENCODING"] == "utf-8:surrogateescape"
    assert said["locale"] and said["filesystem"]  # resolved, and always present


def test_the_recorded_streams_are_the_ones_before_the_hardening(tmp_path):
    """The trap this closes, and the reason the reading is taken at import.

    `main` reconfigures all three streams to UTF-8 in its first three statements, so a capture
    composed afterwards would read `utf-8/strict` off stdin no matter what the session
    declared — which is a capture agreeing with itself about a codec nobody used. RK337 came
    in that shape: a field `UnicodeEncodeError` whose stored capture blamed a module that
    opens its file `rb` and encodes nothing.
    """
    found = report_under(project(tmp_path), {"PYTHONIOENCODING": "utf-8:surrogateescape"})
    streams = found["environment"]["streams"]
    assert streams["stdin"] == "utf-8/surrogateescape"
    assert streams["stdout"] == "utf-8/surrogateescape"
    # stderr is Python's own default and not the same word, which is why all three are kept:
    # one reading would have been asserted as "whatever stdin said" and hidden the asymmetry.
    assert streams["stderr"] == "utf-8/backslashreplace"


def test_the_reading_is_the_interpreters_and_not_one_module_copys(tmp_path):
    """`python -m roadkeep.cli` imports `cli` twice, and a fact held in that module would be
    recorded by whichever copy `main` ran in — the launcher's — while the copy `capturing`
    imports stays empty and answers `?/?`. Measured, before it moved to `provenance`.

    So the two invocations have to agree: one where `cli` is `__main__` and one where it is
    only ever `roadkeep.cli`.
    """
    declared = {"PYTHONIOENCODING": "utf-8:surrogateescape"}
    once = subprocess.run(
        [
            sys.executable,
            "-c",
            "import json; from roadkeep.capturing import environment; "
            "print(json.dumps(environment().as_dict()['streams']))",
        ],
        capture_output=True,
        check=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONPATH": str(PACKAGE), **declared},
    )
    twice = report_under(project(tmp_path), declared)
    assert json.loads(once.stdout) == twice["environment"]["streams"]


def test_only_the_declared_variables_leave(tmp_path):
    """An allow-list and not `os.environ`. RK87's answer to a disclosure is a reviewer who can
    read what leaves before it goes, and a dump of the environment is one nobody can approve —
    every capture would carry a token, a hostname and a home directory."""
    secret = "gho_thisisnotatokenbutitwouldbe"
    found = report_under(
        project(tmp_path),
        {"PYTHONIOENCODING": "utf-8", "GITHUB_TOKEN": secret, "AWS_SECRET_ACCESS_KEY": secret},
    )
    assert secret not in json.dumps(found)
    assert set(found["environment"]["declared"]) <= set(TEXT_VARIABLES)


def test_the_environment_is_a_part_that_can_be_dropped_by_name(tmp_path):
    """It is the reporting *machine* and not the defect, so RK87 governs it like every other
    part: deletable by name, and named in what is left."""
    found = report_under(project(tmp_path), {"PYTHONIOENCODING": "utf-8"}, "environment")
    assert "environment" not in found and found["omitted"] == ["environment"]


def test_what_is_shown_and_what_is_stored_are_one_reading(tmp_path):
    """The printed block and the JSON come from the same object, which is what makes the
    reviewer's approval mean anything (RK87)."""
    found = capture(SYMPTOM, WHY, "F", ["-C", str(project(tmp_path)), "lint"], tmp_path)
    assert found.environment is not None
    said = str(found)
    assert "--- how this process reads and writes text ---" in said
    assert found.environment.locale in said
    assert found.as_dict()["environment"] == found.environment.as_dict()


# -- the name the other surface publishes (RK353) -----------------------------


def test_a_tool_name_typed_at_the_cli_is_answered_with_the_verb_it_is_here(capsys):
    """Measured in a session: the skill teaches `scope`, argparse answers `invalid choice`
    and forty verbs, and none of them is the one the reader was sent for. The arguments they
    typed are already the right ones, so the answer is the verb and nothing else."""
    with pytest.raises(SystemExit):
        main(["scope", "RK1", "--path", "src/x.py"])
    err = capsys.readouterr().err
    assert f"the same act is `{invocation()} claim`" in err
    assert "publishes that verb as over MCP" in err


def test_the_qualified_name_is_answered_too(capsys):
    # A name pasted out of a tool list arrives with its prefix (RK333).
    with pytest.raises(SystemExit):
        main(["mcp__roadkeep__merge_check"])
    assert f"the same act is `{invocation()} merge --check`" in capsys.readouterr().err


def test_a_typo_is_not_told_about_a_tool(capsys):
    # A name nothing publishes is a typo, and the offer below is the whole of what is said.
    with pytest.raises(SystemExit):
        main(["nonsence"])
    assert "publishes that verb" not in capsys.readouterr().err


def test_a_word_inside_an_argument_is_not_read_as_the_verb(capsys, tmp_path):
    # The first token that is not an option, and nothing after it: a `--why` about `scope` is
    # not the command somebody typed.
    with pytest.raises(SystemExit):
        main(["-C", str(tmp_path), "add", "--why", "scope"])
    assert "publishes that verb" not in capsys.readouterr().err


# -- a capture nothing counts is a note in a drawer (RK1139) --------------------


def _capture_file(root: Path, name: str, symptom: str) -> Path:
    """One capture on disk, written the way `keep` writes one: the fields, as JSON."""
    directory = root / ".roadkeep" / "reports"
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_text(
        json.dumps({"symptom": symptom, "why": "Because of a reason.", "block": "A"}),
        encoding="utf-8",
    )
    return path


def test_the_captures_a_project_holds_are_readable_in_filename_order(tmp_path):
    """RK1139. `report` printed `kept <path>` and nothing listed, counted or contradicted it — a
    session read that line as "filed", and `stats` answered `total 2` and was right, which is
    what made the mistake invisible."""
    from roadkeep.capturing import captures

    _capture_file(tmp_path, "20260101T000000Z-run-b.json", "The second symptom")
    _capture_file(tmp_path, "20250101T000000Z-run-a.json", "The first symptom")
    held = captures(tmp_path)
    # Filename order is time order, because the name carries the stamp `keep` wrote it with.
    assert [one.symptom for one in held] == ["The first symptom", "The second symptom"]


def test_a_project_that_has_never_hit_a_defect_holds_none(tmp_path):
    from roadkeep.capturing import captures

    assert captures(tmp_path) == ()


def test_a_file_that_is_not_a_capture_is_skipped_and_never_counted(tmp_path):
    # A capture is evidence somebody may have hand-edited, so a directory that cannot be
    # parsed must not stop a query — and junk counted as unfiled is a number nobody trusts.
    from roadkeep.capturing import captures

    directory = tmp_path / ".roadkeep" / "reports"
    directory.mkdir(parents=True)
    (directory / "broken.json").write_text("{not json", encoding="utf-8")
    (directory / "empty.json").write_text('{"why": "no symptom here"}', encoding="utf-8")
    _capture_file(tmp_path, "real.json", "A real symptom")
    assert [one.symptom for one in captures(tmp_path)] == ["A real symptom"]


# -- the row a stamp clears (RK1141) --------------------------------------------


def test_a_stamp_names_the_id_and_keeps_every_other_key(tmp_path):
    """RK1141. RK1139's count cleared a row by an exact symptom match — right for an author who
    ran the pre-filled `add`, and permanent for one who reworded the sentence: this repository
    carried a row that could never reach zero, which is the check RK402 says nobody reads."""
    from roadkeep.capturing import captures, stamp

    path = _capture_file(tmp_path, "one.json", "A symptom")
    assert stamp(path, "RK9") is True
    payload = json.loads(path.read_text(encoding="utf-8"))
    # A capture is what a replay runs from, so every other key survives the write.
    assert payload["filed"] == "RK9"
    assert payload["symptom"] == "A symptom" and payload["why"] == "Because of a reason."
    assert captures(tmp_path)[0].filed == "RK9"


def test_a_file_it_cannot_parse_is_left_exactly_as_it_was(tmp_path):
    from roadkeep.capturing import stamp

    directory = tmp_path / ".roadkeep" / "reports"
    directory.mkdir(parents=True)
    broken = directory / "broken.json"
    broken.write_text("{not json", encoding="utf-8")
    assert stamp(broken, "RK9") is False
    assert broken.read_text(encoding="utf-8") == "{not json"


def test_a_capture_that_is_not_there_is_not_a_failure_of_the_write(tmp_path):
    # The rule this keeps: a stamp is the transient half, and the task is already filed by the
    # time it runs — so an absent path answers False and raises nothing.
    from roadkeep.capturing import stamp

    assert stamp(tmp_path / "nowhere.json", "RK9") is False


# -- the door a capture already on disk has (RK1142) -----------------------------


def test_the_command_stamps_a_capture_this_project_holds(tmp_path, capsys):
    """RK1142. RK1141 covered every capture filed from then on and none of the ones held:
    clearing this repository's own row took a `python -c`, which is the shape L5 exists
    against — every question this tool answers is a command."""
    project(tmp_path)
    path = _capture_file(tmp_path, "held.json", "A captured symptom")
    argv = ["-C", str(tmp_path), "capture", "filed", str(path), "--as", "RK1"]
    capsys.readouterr()
    assert main(argv) == EXIT_OK
    assert "now names RK1" in capsys.readouterr().out
    assert json.loads(path.read_text(encoding="utf-8"))["filed"] == "RK1"


def test_an_id_no_governed_file_holds_is_refused_at_the_door(tmp_path, capsys):
    # A stamp naming nothing is a link to nothing, which is the reading `stats` already makes
    # — so the refusal is L1's: at the door, and naming the command that files it instead.
    project(tmp_path)
    path = _capture_file(tmp_path, "held.json", "A captured symptom")
    argv = ["-C", str(tmp_path), "capture", "filed", str(path), "--as", "RK404"]
    capsys.readouterr()
    assert main(argv) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "no governed file holds RK404" in said and "add --capture" in said
    assert "filed" not in json.loads(path.read_text(encoding="utf-8"))


def test_a_path_that_is_not_a_capture_is_refused(tmp_path, capsys):
    # Somebody's file is not this tool's to annotate, and the refusal names the read that
    # lists the ones that are.
    project(tmp_path)
    stray = tmp_path / "notes.json"
    stray.write_text('{"symptom": "not under the report directory"}', encoding="utf-8")
    argv = ["-C", str(tmp_path), "capture", "filed", str(stray), "--as", "RK1"]
    capsys.readouterr()
    assert main(argv) == EXIT_USAGE
    assert "is not a capture this project holds" in capsys.readouterr().err


def test_the_payload_says_what_it_wrote(tmp_path, capsys):
    project(tmp_path)
    path = _capture_file(tmp_path, "held.json", "A captured symptom")
    argv = ["-C", str(tmp_path), "capture", "filed", str(path), "--as", "RK1", "--json"]
    capsys.readouterr()
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload == {"path": ".roadkeep/reports/held.json", "filed": "RK1"}


# -- a capture delivered to another backlog (RK1160) ---------------------------

#: The spelling every tracker already uses for a cross-repository reference, which is what an
#: author types after filing a defect in this tool's own backlog rather than in their project's.
UPSTREAM = "alegauss/roadkeep#RK1128"


def test_a_stamp_naming_a_repository_is_read_as_a_delivery_and_a_bare_one_is_not() -> None:
    """The shape, and it is the only thing this can check: a qualified id belongs to a backlog
    this project cannot open, so what is verified is that the author named where it went. Both
    directions, because a predicate answering *delivered* to everything would clear every row —
    the state RK1139 was filed to end."""
    assert delivered(UPSTREAM) == "alegauss/roadkeep"
    assert delivered("a/b#SH41a") == "a/b"  # another project's `[ids] suffix` (RK110)
    assert delivered("RK1128") == ""  # a local id, which the backlog still has to hold
    assert delivered("roadkeep#RK1") == ""  # no repository: a local id with punctuation in it
    assert delivered("alegauss/roadkeep#nope") == ""


def test_a_capture_filed_upstream_clears_the_row_the_local_backlog_cannot(tmp_path, capsys):
    """The defect, measured in Viglet Turing: a capture whose defect shipped here as RK1128 read
    `1 unfiled` for ever, because both readings resolve the stamp against the *capturing*
    project's ids — and a capture of a defect in this tool has one correct destination, which is
    never that project. The two ways to silence it were a stamp from the wrong repository and
    deleting the evidence."""
    root = project(tmp_path)
    kept = keep(capture(SYMPTOM, WHY, "F", ["lint"], root), root)
    main(["-C", str(root), "stats"])
    assert "1 unfiled" in capsys.readouterr().out

    assert main(["-C", str(root), "capture", "filed", str(kept.path), "--as", UPSTREAM]) == EXIT_OK
    said = capsys.readouterr().out
    assert "delivered to alegauss/roadkeep" in said and "taken as filed" in said
    main(["-C", str(root), "stats"])
    assert "unfiled" not in capsys.readouterr().out


def test_a_local_id_the_backlog_does_not_hold_is_still_a_link_to_nothing(tmp_path, capsys):
    """The control, which is what makes the row above a defect rather than a nag: the bare
    reading is unchanged, so a stamp naming a task nothing here holds is still refused — and the
    refusal now names the spelling that records a delivery instead."""
    root = project(tmp_path)
    kept = keep(capture(SYMPTOM, WHY, "F", ["lint"], root), root)
    assert main(["-C", str(root), "capture", "filed", str(kept.path), "--as", "RK999"]) != EXIT_OK
    refused = capsys.readouterr().err
    assert "no governed file holds RK999" in refused
    assert "--as owner/repo#RK999" in refused
