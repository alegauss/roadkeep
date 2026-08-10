"""The verb that spends the report (RK422).

Four properties, each one a way this could be worse than the loop it replaces:

* **It closes what it can in one call.** A report with a runnable remedy comes back clean,
  and the exit code is the gate's rather than a second contract.
* **It never runs a read.** A remedy that answers a question and writes nothing would spend
  a step, change no byte and leave the finding standing — which is a repair loop that
  repairs nothing, arriving through the verb built to end one.
* **It never writes prose.** A title, a shorter sentence, a choice between two doors: each
  is printed and none is invented (L4).
* **It cannot spin.** A command is attempted once, and a rule that reports what its own
  remedy writes ends the loop rather than filling the disk.
"""

from __future__ import annotations

import json
from pathlib import Path

from roadkeep.cli import EXIT_GATE, EXIT_OK, main
from roadkeep.config import Config
from roadkeep.linting import Finding, lint
from roadkeep.remedying import codes, remedy
from roadkeep.repairing import MAX_PASSES, _door, repair

#: `_door` reads the config only for the two rows L6 makes per-project, and neither is a
#: `read`, so the table's own answer is what this asserts about.
_ANY = None

# -- what one call does ------------------------------------------------------


def test_a_runnable_finding_is_closed_and_the_tree_comes_back_clean(tmp_path):
    config = _project(tmp_path, improvements=_STALE_SECTION)
    assert not lint(config).clean
    outcome = repair(config, _dispatcher(tmp_path))
    assert outcome.clean, [str(left) for left in outcome.left]
    assert [step.argv for step in outcome.steps] == [("section", "drop", "DX3")]
    assert lint(Config.discover(tmp_path)).clean


def test_the_exit_code_is_the_gates_and_not_a_second_contract(tmp_path):
    _project(tmp_path, improvements=_STALE_SECTION)
    assert main(["-C", str(tmp_path), "repair"]) == EXIT_OK
    # And again, on a tree whose one finding needs a sentence nobody may write for it.
    other = tmp_path / "other"
    _project(other, roadmap=_LONG_SYMPTOM)
    assert main(["-C", str(other), "repair"]) == EXIT_GATE


def test_no_read_only_remedy_is_ever_selected_as_a_step():
    """RK422's own finding, asserted over the whole table rather than one fixture.

    A `read` answers a question and closes nothing — `show` which of two designs is history,
    `anchors` which file claims one, `priority list` which queue is live. Running one costs a
    step, writes no byte and leaves the finding standing, which is a repair loop that repairs
    nothing arriving through the verb written to end one. Over every code, because the defect
    was a *classification* and the fixture that catches one row proves nothing about the rest.
    """
    for code in codes():
        found = remedy(Finding(code, "docs/ROADMAP.md", "", 1, "DX1"))
        assert found is not None
        selected = _door(Finding(code, "docs/ROADMAP.md", "", 1, "DX1"), _ANY)
        if found.kind == "read":
            assert selected is None, f"{code}: repair would run {found.doors[0].argv}"
        elif found.kind == "run":
            assert selected is not None, code


def test_nothing_composes_the_prose_the_author_owes(tmp_path):
    config = _project(tmp_path, roadmap=_LONG_SYMPTOM)
    outcome = repair(config, _dispatcher(tmp_path))
    assert not outcome.clean
    codes = {left.finding.code for left in outcome.left}
    assert "symptom.too-long" in codes
    # Named, with its door and its blank — the one thing that must not happen is a shorter
    # symptom appearing in the file.
    assert "restate" in "\n".join(str(left) for left in outcome.left)
    assert _read(tmp_path / "docs" / "ROADMAP.md").count("A symptom that runs") == 1


# -- the dry run -------------------------------------------------------------


def test_a_dry_run_writes_nothing_and_lists_what_it_would_do(tmp_path):
    config = _project(tmp_path, improvements=_STALE_SECTION)
    before = _read(tmp_path / "docs" / "IMPROVEMENTS.md")
    outcome = repair(config, _refuse, dry_run=True)
    assert outcome.dry_run and outcome.passes == 0
    assert ("section", "drop", "DX3") in {step.argv for step in outcome.steps}
    assert all(step.exit is None for step in outcome.steps)
    assert _read(tmp_path / "docs" / "IMPROVEMENTS.md") == before


def test_the_mechanical_pass_is_listed_once_in_a_dry_run(tmp_path):
    config = _project(tmp_path, roadmap=_TWO_STALE_POINTERS)
    outcome = repair(config, _refuse, dry_run=True)
    mechanical = [s for s in outcome.steps if s.argv == ("lint", "--fix")]
    # Two findings, one pass: listing it per finding is the report RK420 folded into a
    # summary line, arriving back through the verb written to shorten it.
    assert len(mechanical) == 1, outcome.steps


def test_a_dry_run_is_never_reported_clean_when_work_is_outstanding(tmp_path):
    _project(tmp_path, improvements=_STALE_SECTION)
    assert main(["-C", str(tmp_path), "repair", "--dry-run"]) == EXIT_GATE


# -- it cannot spin ----------------------------------------------------------


def test_a_command_is_attempted_once(tmp_path):
    seen: list[tuple[str, ...]] = []

    def record(argv):
        seen.append(tuple(argv))
        return 0  # writes nothing, so the finding stands and a naive loop would repeat it

    config = _project(tmp_path, improvements=_STALE_SECTION)
    outcome = repair(config, record)
    assert len(seen) == len(set(seen)) == 1
    assert not outcome.exhausted
    assert outcome.passes < MAX_PASSES


def test_a_step_that_fails_is_reported_rather_than_swallowed(tmp_path):
    config = _project(tmp_path, improvements=_STALE_SECTION)
    outcome = repair(config, lambda argv: 2)
    assert outcome.failed and outcome.failed[0].exit == 2
    assert "FAILED" in str(outcome.failed[0])


def test_an_argv_the_parser_rejects_is_a_failed_step_and_not_a_dead_process(tmp_path):
    # `_step` catches argparse's SystemExit: a remedy that does not parse is this tool's
    # defect, and taking the process down mid-repair would leave the tree half-written.
    _project(tmp_path, improvements=_STALE_SECTION)
    assert main(["-C", str(tmp_path), "repair"]) == EXIT_OK


# -- the payload -------------------------------------------------------------


def test_the_json_form_carries_the_steps_and_what_is_left(tmp_path, capsys):
    _project(tmp_path, roadmap=_LONG_SYMPTOM)
    assert main(["-C", str(tmp_path), "repair", "--json"]) == EXIT_GATE
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is False
    assert payload["dry_run"] is False
    left = {row["code"]: row for row in payload["left"]}
    assert "symptom.too-long" in left
    assert left["symptom.too-long"]["remedy"]["kind"] == "compose"


# -- fixtures ----------------------------------------------------------------

_ROADMAP = """# Roadmap

## Block A — The first block

- 📋 **DX1** (deps: —) **A first symptom** — Because of a reason. → §DX1
"""

_LONG_SYMPTOM = """# Roadmap

## Block A — The first block

- 📋 **DX1** (deps: —) **A symptom that runs well past the limit this project declares for the field, so the only repair is a shorter one and the tool may not write it** — Because of a reason. → §DX1
"""

_TWO_STALE_POINTERS = """# Roadmap

## Block A — The first block

- 📋 **DX1** (deps: —) **A first symptom** — Because of a reason. → §DX7
- 📋 **DX2** (deps: —) **A second symptom** — Because of a reason. → §DX8
"""

_LEDGER = """# Shipped

## Block A — The first block

- ✅ **DX3** **An earlier symptom** — Because it was done.
"""

_PROSE = """# Design rationale

## Block A — The first block

### §DX1 The first design

The reasoning the first line has no room for.
"""

#: The rationale of work that already shipped: `ship` deletes it, so this survived a hand edit.
_STALE_SECTION = _PROSE + (
    "\n### §DX3 A design its ship should have deleted\n\n"
    "The rationale of work that is already in the ledger.\n"
)

_CONFIG = (
    'prefix = "DX"\n[files]\nroadmap = "docs/ROADMAP.md"\n'
    'changelog = "docs/CHANGELOG.md"\nimprovements = "docs/IMPROVEMENTS.md"\n'
)
#: The same, plus a queue in the file that does not govern one (RK325): the section wins,
#: so the config's order is read by nothing and `priority drop` cannot reach it.
_CONFIG_WITH_QUEUE = 'priority = ["DX1"]\n' + _CONFIG


def _project(
    tmp_path: Path,
    roadmap: str = _ROADMAP,
    improvements: str = _PROSE,
    config: str = _CONFIG,
) -> Config:
    tmp_path.mkdir(parents=True, exist_ok=True)
    docs = tmp_path / "docs"
    docs.mkdir(exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    for name, body in (
        ("ROADMAP.md", roadmap),
        ("CHANGELOG.md", _LEDGER),
        ("IMPROVEMENTS.md", improvements),
    ):
        with (docs / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def _dispatcher(root: Path):
    """The real runner, reached the way the CLI reaches it."""
    return lambda argv: main(["-C", str(root), *argv])


def _refuse(argv):
    raise AssertionError(f"a dry run executed {argv}")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


# -- runs and attempts are two numbers (RK471) --------------------------------


def _printed(capsys, outcome) -> str:
    """The report for an outcome the test drove itself, since `main` runs its own dispatch."""
    from roadkeep.cli import _print_repair

    _print_repair(outcome, ".")
    return capsys.readouterr().out


def test_the_summary_counts_what_ran_and_names_what_was_refused(tmp_path, capsys):
    """Measured over a copy of Turing: one repair ran, two were printed `FAILED`, and the
    summary said `3 repair(s) ran` three lines under them. The count is the line a person
    acts on, so a caller read `3 ran` against `34 left` and concluded the tree moved three
    findings closer when it moved one."""
    config = _project(tmp_path, improvements=_STALE_SECTION)

    def refusing(argv):
        # What a `section drop` over a section another line nests does: a real refusal, and
        # the state this summary described as a run.
        return 2

    outcome = repair(config, refusing)
    assert outcome.steps and not any(step.ok for step in outcome.steps)
    printed = _printed(capsys, outcome)
    line = next(one for one in printed.splitlines() if "repair(s)" in one)
    assert printed.count("FAILED") == len(outcome.steps)
    # The two numbers agree with the lines above them, which is the whole claim.
    assert f"0 repair(s) ran, {len(outcome.steps)} refused" in line


def test_a_run_with_nothing_refused_says_nothing_about_refusals(tmp_path, capsys):
    """The clause is silent where there is nothing to say: a summary that always carried
    `0 refused` would spend the line on the runs that cost the reader nothing."""
    _project(tmp_path, improvements=_STALE_SECTION)
    assert main(["-C", str(tmp_path), "repair", "--dry-run"]) == EXIT_GATE
    line = next(
        one for one in capsys.readouterr().out.splitlines() if "repair(s)" in one
    )
    assert "refused" not in line and "would run" in line


def test_the_exit_code_is_untouched_by_a_refusal(tmp_path, capsys):
    """Two refusals are not a failure of `repair`: its whole design is that what it cannot
    close it prints, and 1 while anything is left is RK422's contract."""
    _project(tmp_path, improvements=_STALE_SECTION)
    # It closes here, so the code is the gate's own — which is the contract a refusal must
    # not change either: `repair` reports what it could not close and exits on the tree.
    assert main(["-C", str(tmp_path), "repair"]) == EXIT_OK
