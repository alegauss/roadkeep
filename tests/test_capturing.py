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

And the affordance that makes any of it reachable (RK86): every non-zero exit closes with
the capture command. A refusal that names only the rule it applied is a dead end in the one
case where the rule is the defect, and what an agent does with a dead end is work around it
quietly — so the surface with the worst failures produces the fewest reports. The two rules
asserted below are that it costs nothing on the runs that succeed, and that it never claims
the refusal was wrong: this tool has no way to know and no model to guess (L4).
"""

from __future__ import annotations

import io
from pathlib import Path

import pytest

from roadkeep.capturing import HOME, Failure, _tail, capture, check, observe, offer
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main

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
    assert found.filing.startswith("roadkeep add --block F --symptom ")
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
    assert "roadkeep capture" in out and "exit     1" in out


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


def test_nothing_leaves_the_machine(tmp_path):
    """A capture and not a client: no network in this path, nothing to authenticate, and
    no identity. Delivery is somebody typing a separate command, and RK87 governs it."""
    source = (Path(__file__).resolve().parents[1] / "src" / "roadkeep" / "capturing.py").read_text(
        encoding="utf-8"
    )
    for forbidden in ("urllib", "http", "socket", "requests", "smtplib"):
        assert forbidden not in source, forbidden


# -- the offer every failure closes with (RK86) -------------------------------


def test_the_offer_substitutes_the_failing_argv_so_the_move_costs_nothing():
    said = offer(["-C", "/somewhere", "lint"])
    assert said.endswith('roadkeep report --symptom "…" --why "…" -- -C /somewhere lint')


def test_the_offer_composes_no_part_of_the_claim():
    """The two fields stay ellipses. A tool that guessed a symptom would be a tool with a
    model, and the sentence it guessed is the one a maintainer would then be reading."""
    said = offer(["lint"])
    assert '--symptom "…"' in said and '--why "…"' in said


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
    assert "symptom.too-long" in err and "roadkeep report --symptom" in err


def test_a_failing_gate_closes_with_the_offer(tmp_path, capsys):
    root = project(tmp_path, roadmap=BROKEN)
    code = main(["-C", str(root), "lint"])
    assert code == 1
    assert "roadkeep report --symptom" in capsys.readouterr().err


def test_a_command_that_succeeds_says_nothing_about_reporting(tmp_path, capsys):
    """It costs nothing on the runs that work, which is the whole reason it can live on
    every failure path instead of in a document somebody loads first."""
    root = project(tmp_path)
    assert main(["-C", str(root), "lint"]) == EXIT_OK
    assert "report" not in capsys.readouterr().err


def test_argparse_refuses_before_a_handler_exists_and_still_offers(capsys):
    with pytest.raises(SystemExit) as exited:
        main(["lint", "--no-such-flag"])
    assert exited.value.code == EXIT_USAGE
    assert "roadkeep report --symptom" in capsys.readouterr().err


def test_help_and_version_are_not_failures(capsys):
    with pytest.raises(SystemExit) as exited:
        main(["--help"])
    assert exited.value.code == 0
    assert "roadkeep report" not in capsys.readouterr().err


def test_report_never_offers_to_report_itself(tmp_path, capsys):
    root = project(tmp_path)
    code = main(
        ["-C", str(root), "report", "--symptom", SYMPTOM, "--why", "One. Two.", "--", "lint"]
    )
    err = capsys.readouterr().err
    assert code == EXIT_USAGE
    assert "nothing captured" in err and "roadkeep report --symptom" not in err


def test_the_hook_is_never_given_prose_to_answer_a_protocol_with(tmp_path, capsys, monkeypatch):
    """`guard` and `mcp` answer a harness, not an agent. A sentence on their stderr is read
    by nobody, and on their stdout it would be a parse error."""
    root = project(tmp_path)
    monkeypatch.setattr("sys.stdin", io.StringIO("not json at all"))
    assert main(["-C", str(root), "guard"]) == EXIT_OK
    assert capsys.readouterr().err == ""


def test_a_crash_is_printed_and_closed_with_the_offer(tmp_path, capsys, monkeypatch):
    """The third place RK86 names. A traceback that reaches a terminal raw is a session
    that ends, and what it ends without is the report only that session could write."""
    root = project(tmp_path)

    def explode(*_args, **_kwargs):
        raise RuntimeError("the parser lost its footing")

    monkeypatch.setattr("roadkeep.cli._lint", explode)
    code = main(["-C", str(root), "lint"])
    err = capsys.readouterr().err
    assert code == 1
    assert "RuntimeError: the parser lost its footing" in err
    assert err.index("Traceback") < err.index("roadkeep report --symptom")
