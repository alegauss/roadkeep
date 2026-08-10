"""Field captures, run against the tree that is here now (RK88).

A capture that is only read is spent once: someone reads it, forms a theory, edits, and has
no way to check the theory except rebuilding the reporter's repository from a description
of it — the step that does not happen, so field defects get closed on plausibility and
reopen from a second project.

The material for a test is already in the capture. The argv, the config and the file it
objected to are the input half; the exit code and the address it printed are the expected
half. Nothing needs a fixture author, which is the same argument this repository already
makes everywhere else: round-trip is a property test over real files, `docs/` is the
conformance fixture for the format, and Shio's and Turing's roadmaps are in the corpus
because they supply dep kinds no invented file would.

Two things this settles, and one it does not:

* **Replay never touches the reporting project.** The capture carries its own inputs and
  they are staged in a scratch directory — a replay that needed the original repository
  would be the step that does not happen, again.
* **A capture that was not made replayable says so.** RK87 makes embedding opt-in, because
  the file that makes a capture runnable is a file leaving somebody's repository. Staging
  from a guess would be a test whose input this repository invented.
* **stdin is not held.** A command driven by a hook payload cannot be replayed from a
  capture, and nothing here pretends otherwise.

`tests/captures/` is the corpus, and `reproduces` in each file is this repository's
standing answer. A verdict that moves is either a fix to record or a regression to answer,
and both want the file updated in the same commit that moved it.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.capturing import Capture, Failure, capture, environment, replay
from roadkeep.cli import EXIT_GATE, EXIT_OK, main
from roadkeep.provenance import engine

HERE = Path(__file__).resolve().parent
CAPTURES = HERE / "captures"

ROADMAP = "docs/ROADMAP.md"
BROKEN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: RK99) **A first symptom** — Because of a reason. → §RK1
"""
CONFIG = f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\n'

SYMPTOM = "A dep nothing satisfies is reported without the group it is in"
WHY = "The finding addresses the line and not the field, so the fix is guessed."


def project(tmp_path: Path) -> Path:
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(CONFIG, encoding="utf-8")
    path = tmp_path / ROADMAP
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(BROKEN)
    return tmp_path


# -- the corpus this repository keeps ----------------------------------------


def corpus() -> list[Path]:
    return sorted(CAPTURES.glob("*.json"))


def test_the_corpus_is_not_empty():
    """A directory with no captures in it proves nothing about a replay that works."""
    assert corpus()


@pytest.mark.parametrize("path", corpus(), ids=lambda p: p.stem)
def test_every_stored_capture_still_answers_what_it_recorded(path, tmp_path):
    """The gate a field report becomes. Failing here is not a broken test: it is the tree
    disagreeing with a capture, which is either a fix nobody recorded or a defect that came
    back — and the file is where the answer goes."""
    recorded = json.loads(path.read_text(encoding="utf-8"))
    outcome = replay(recorded, tmp_path)
    assert outcome.ran, outcome.missing
    assert outcome.reproduces == bool(recorded["reproduces"]), str(outcome)


@pytest.mark.parametrize("path", corpus(), ids=lambda p: p.stem)
def test_every_stored_capture_states_a_claim_within_the_limits(path):
    """A corpus entry is a task line that has not been filed yet, so the schema that judged
    it when it was captured is the schema it is still held to."""
    from roadkeep.capturing import check

    recorded = json.loads(path.read_text(encoding="utf-8"))
    assert check(recorded["symptom"], recorded["why"], recorded["block"]) == ()


def test_the_command_agrees_with_the_corpus(capsys):
    for path in corpus():
        assert main(["replay", str(path)]) == EXIT_OK, capsys.readouterr().out


# -- replaying one capture ---------------------------------------------------


def staging(tmp_path: Path) -> Path:
    """The scratch the replay writes into — never the reporting project, and never
    the working tree of whoever is asking."""
    where = tmp_path / "mine"
    where.mkdir(parents=True, exist_ok=True)
    return where


def recorded_from(tmp_path: Path) -> dict:
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root, embed=True)
    return found.as_dict()


def test_a_capture_replays_without_the_repository_it_came_from(tmp_path):
    """The whole claim: the staging holds a `roadkeep.toml` and one file, both the
    capture's own, and the reporter's project is never opened."""
    recorded = recorded_from(tmp_path / "theirs")
    outcome = replay(recorded, staging(tmp_path))
    assert outcome.ran and outcome.reproduces
    assert outcome.exit_code == recorded["exit"] == 1


def test_the_recorded_argv_is_repointed_and_otherwise_untouched(tmp_path):
    """A replay that rewrote the flags would be testing a command nobody ran."""
    recorded = recorded_from(tmp_path / "theirs")
    recorded["argv"] = ["-C", "/gone", "lint", "--json"]
    outcome = replay(recorded, staging(tmp_path))
    assert outcome.ran
    # `--json` survived; only `-C` moved. Asserted on the *tail* of the payload rather than
    # on the code near its top: a capture keeps the last 40 lines and says so (`_tail`), and
    # since RK449 a finding's remedy carries both spellings of every door, so the report for
    # one finding is longer than the window. What proves the flag survived is the shape.
    assert '"id": "RK1"' in outcome.output and '"notes": []' in outcome.output


def test_a_capture_with_no_c_flag_is_still_pointed_at_the_staging(tmp_path):
    recorded = recorded_from(tmp_path / "theirs")
    recorded["argv"] = ["lint"]
    assert replay(recorded, staging(tmp_path)).ran


def test_a_defect_that_was_fixed_stops_reproducing(tmp_path):
    """The other half of the question, and the reason a capture is kept after it is closed:
    the same run against the tree before a fix is what says the fix did anything."""
    recorded = recorded_from(tmp_path / "theirs")
    recorded["exit"] = 99  # what the tree answered then, and does not answer now
    outcome = replay(recorded, staging(tmp_path))
    assert not outcome.reproduces
    assert "no longer reproduces" in str(outcome)


def test_a_message_this_repository_improved_is_not_a_defect_that_came_back(tmp_path):
    """Reproduction is the exit code and the recorded address, never the output text: a
    reworded finding would otherwise read as a regression in every capture at once."""
    recorded = recorded_from(tmp_path / "theirs")
    recorded["output"] = "a completely different sentence"
    assert replay(recorded, staging(tmp_path)).reproduces


# -- what is not replayable, and says so -------------------------------------


def test_a_capture_that_embedded_nothing_names_what_it_lacks(tmp_path):
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)  # no embed
    outcome = replay(found.as_dict(), staging(tmp_path))
    assert not outcome.ran and outcome.missing == ("document",)
    assert "not replayable" in str(outcome)


def test_a_redacted_part_is_missing_for_the_replay_too(tmp_path):
    """RK87 and RK88 pull against each other and the tension is named, not resolved: a
    capture safe enough to publish can be one nobody can re-run."""
    root = project(tmp_path)
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root, embed=True)
    outcome = replay(found.without("config").as_dict(), staging(tmp_path))
    assert not outcome.ran and "config" in outcome.missing


def test_a_config_only_defect_needs_no_document(tmp_path):
    """A failure that named no file has no governed file in its input, and demanding one
    would make the cheapest class of field report the one class that cannot be replayed."""
    found = Capture(
        symptom=SYMPTOM,
        why=WHY,
        block="F",
        failure=Failure(argv=("lint",), exit_code=2, output="roadkeep: Invalid value"),
        engine=engine(),
        config="prefix = [\n",
        config_path="roadkeep.toml",
    )
    assert found.replayable
    assert replay(found.as_dict(), tmp_path).ran


def test_the_command_exits_one_when_the_tree_stopped_agreeing(tmp_path, capsys):
    """Exit 1 and not 2: nothing about the caller's input has to change, the answer moved."""
    recorded = recorded_from(tmp_path / "theirs")
    recorded["reproduces"] = False
    path = tmp_path / "capture.json"
    path.write_text(json.dumps(recorded), encoding="utf-8")
    assert main(["replay", str(path)]) == EXIT_GATE
    assert "still reproduces" in capsys.readouterr().out


def test_a_file_that_is_not_a_capture_is_refused_and_not_staged(tmp_path, capsys):
    path = tmp_path / "notes.json"
    path.write_text("this is not json", encoding="utf-8")
    assert main(["replay", str(path)]) != EXIT_OK
    assert "roadkeep:" in capsys.readouterr().err


# -- the one input a replay cannot stage (RK341) ------------------------------


def unshared(name: str, *candidates: str) -> str:
    """A value for ``name`` that this process does not itself hold (RK352).

    These assertions are about the *comparison*: `_drifted` names the recorded facts this
    reader does not share, so a fixture recording one it happens to share is asserting about
    the shell. It used to hard-code `utf-8:surrogateescape`, which is realistic for exactly the
    reason a shell exports it — measured here, the PowerShell tool starts Python with that
    value, so the drift came back as one fact of two and the red was about the terminal the
    suite was launched from.

    So the value is read against this process rather than fixed once in a constant: the first
    candidate is the realistic one, and the rest are there for the environment that already
    declares it. Which is the thing a constant cannot say — that the choice is about avoiding a
    collision and not about the value meaning anything.
    """
    here = environment().facts.get(name, "")
    for candidate in candidates:
        if candidate != here:
            return candidate
    raise AssertionError(f"{name} is {here!r} here, and every candidate collides with it")


def test_the_fixture_picks_a_value_this_process_does_not_hold(monkeypatch):
    # The helper is the fix, so it is the thing asserted on: with the realistic value exported,
    # the fixture must move off it rather than record a fact this reader shares.
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8:surrogateescape")
    assert unshared("PYTHONIOENCODING", "utf-8:surrogateescape", "iso-8859-15") == "iso-8859-15"
    monkeypatch.delenv("PYTHONIOENCODING")
    assert unshared("PYTHONIOENCODING", "utf-8:surrogateescape", "iso-8859-15") == (
        "utf-8:surrogateescape"
    )


def test_a_verdict_reached_under_different_codecs_says_which_ones(tmp_path):
    """The defect RK341 names, from the reader's side.

    `observe` runs the argv through the `main` this interpreter already loaded — a subprocess
    would be a second engine to be wrong about (RK79) — and an interpreter's stdio codecs are
    settled before its first line runs, so no assignment here reaches them. A replay therefore
    answers under *its* text handling and not the reporter's, and a bare "no longer reproduces"
    is how RK337 was closed against a module that encodes nothing.
    """
    recorded = recorded_from(tmp_path / "theirs")
    recorded["environment"] = {
        **recorded["environment"],
        "declared": {
            "PYTHONIOENCODING": unshared(
                "PYTHONIOENCODING", "utf-8:surrogateescape", "iso-8859-15"
            )
        },
        "locale": unshared("locale", "iso-8859-15", "cp874"),
    }
    recorded["exit"] = 99  # so the verdict is the negative one the caveat exists for
    outcome = replay(recorded, staging(tmp_path))
    assert not outcome.reproduces
    assert outcome.drifted == ("PYTHONIOENCODING", "locale")
    assert "under a different PYTHONIOENCODING, locale" in str(outcome)


def test_an_environment_this_process_shares_adds_no_caveat(tmp_path):
    """The other half, or the note is one every replay carries and nobody reads: the capture
    was taken in this process, so there is nothing to warn about."""
    recorded = recorded_from(tmp_path / "theirs")
    outcome = replay(recorded, staging(tmp_path))
    assert outcome.drifted == () and "different" not in str(outcome)


def test_a_capture_with_no_environment_says_so_rather_than_reading_as_a_fix(tmp_path):
    """`None` and not `()`: *nothing drifted* and *nothing to compare* are different answers,
    and every capture this repository stored before RK341 is the second one.

    Only on the negative verdict. "Still reproduces" is a claim the run just demonstrated; "no
    longer reproduces" is an inference from an absence, and an unrecorded environment is
    another absence — so the two are said together or the first is read as a fix.
    """
    recorded = recorded_from(tmp_path / "theirs")
    recorded.pop("environment")
    recorded["exit"] = 99
    outcome = replay(recorded, staging(tmp_path))
    assert outcome.drifted is None
    assert "records no environment" in str(outcome)


def test_a_capture_with_no_environment_that_reproduces_is_stated_plainly(tmp_path):
    recorded = recorded_from(tmp_path / "theirs")
    recorded.pop("environment")
    outcome = replay(recorded, staging(tmp_path))
    assert outcome.reproduces and str(outcome).endswith(f"now {outcome.exit_code}")


def test_the_drift_is_null_and_not_empty_in_the_json(tmp_path, capsys):
    """The distinction has to survive the machine-readable form too, or a caller reading
    `drifted: []` concludes the environment matched when none was recorded."""
    recorded = recorded_from(tmp_path / "theirs")
    recorded.pop("environment")
    path = tmp_path / "old.json"
    path.write_text(json.dumps(recorded), encoding="utf-8")
    assert main(["replay", str(path), "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["drifted"] is None


def test_a_capture_that_cannot_run_still_reports_the_drift(tmp_path):
    """The two answers are independent: what the staging lacks is about the capture, and what
    the codecs are is about this machine, so a report missing a document still says the one it
    can — which is the half that decides whether re-taking the capture is worth it."""
    root = project(tmp_path / "theirs")
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root)  # no embed
    recorded = found.as_dict()
    recorded["environment"] = {**recorded["environment"], "filesystem": "ascii"}
    outcome = replay(recorded, staging(tmp_path))
    assert outcome.missing == ("document",) and outcome.drifted == ("filesystem",)


# -- a staging that is not the project (RK343) --------------------------------

#: Two governed files declared, which is the ordinary shape and the one `--embed` cannot fill:
#: it carries the single file a finding named, so a project declaring more than one stages
#: fewer files than its own commands read.
TWO_FILES = f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "docs/CHANGELOG.md"\n'


def declaring_two(tmp_path: Path) -> Path:
    root = project(tmp_path)
    (root / "roadkeep.toml").write_text(TWO_FILES, encoding="utf-8")
    with (root / "docs/CHANGELOG.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write("# Changelog\n\n## Block A — The model\n")
    return root


def address_free(root: Path) -> dict:
    """A capture whose failure named no `file:line`, which is where the exit code is the whole
    of the evidence. `list --block Z` is the measured one: the block is not declared, so the
    refusal is about the argument and mentions no line."""
    found = capture(SYMPTOM, WHY, "C", ["-C", str(root), "list", "--block", "Z"], root)
    assert found.failure.where is None and found.failure.exit_code == 2
    return found.as_dict()


def test_a_staging_the_command_cannot_read_answers_nothing(tmp_path):
    """The measured false positive, and the worst kind: a green.

    `list --block Z` against a project with no such block exits 2. Replayed, the staging holds
    `roadkeep.toml` and no governed file at all, so the run exits 2 again — on `No such file or
    directory` — and both `reproduces` and the corpus gate agreed that the recorded defect was
    still there. 2 is the code for a usage error, a refused config and an unreadable file alike.
    """
    recorded = address_free(declaring_two(tmp_path / "theirs"))
    outcome = replay(recorded, staging(tmp_path))
    assert not outcome.ran
    assert outcome.unstaged == (ROADMAP, "docs/CHANGELOG.md")
    assert not outcome.reproduces
    assert "the config declares" in str(outcome) and "not replayable" in str(outcome)


def test_the_two_reasons_not_to_run_are_kept_apart(tmp_path):
    """A part the capture lacks is a redaction somebody made; a file it never carried is a
    capture to take again. Answering both with one list would tell the reader to un-redact a
    file that was never in there."""
    root = project(tmp_path / "theirs")
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root, embed=True)
    redacted = replay(found.without("config").as_dict(), staging(tmp_path))
    assert redacted.missing == ("config",) and redacted.unstaged == ()

    absent = replay(address_free(declaring_two(tmp_path / "theirs2")), staging(tmp_path))
    assert absent.missing == () and absent.unstaged


def test_a_config_that_does_not_parse_declares_no_files(tmp_path):
    """The exemption that keeps this repository's own first corpus entry replayable: a defect in
    *reading* `roadkeep.toml` has no governed file in its input, and demanding files from a
    config nobody could read would refuse the one class of report that needs none."""
    found = Capture(
        symptom=SYMPTOM,
        why=WHY,
        block="F",
        failure=Failure(argv=("lint",), exit_code=2, output="roadkeep: Invalid value"),
        engine=engine(),
        config="prefix = [\n",
        config_path="roadkeep.toml",
    )
    outcome = replay(found.as_dict(), tmp_path)
    assert outcome.ran and outcome.unstaged == ()


def test_the_command_says_which_files_the_capture_never_carried(tmp_path, capsys):
    """Exit 1 like every other capture that answered nothing, and the sentence names the files:
    what to do next is take the capture again, which needs to know what was short."""
    recorded = address_free(declaring_two(tmp_path / "theirs"))
    path = tmp_path / "capture.json"
    path.write_text(json.dumps(recorded), encoding="utf-8")
    assert main(["replay", str(path)]) == EXIT_GATE
    said = capsys.readouterr().out
    assert "not replayable" in said and "docs/CHANGELOG.md" in said


# -- what `--embed` carries (RK344) -------------------------------------------


def three_files(tmp_path: Path) -> Path:
    """The ordinary project: a roadmap, a ledger and the rationale beside them — the shape
    `lint` reads whole, and the shape one embedded file cannot stage."""
    root = declaring_two(tmp_path)
    (root / "roadkeep.toml").write_text(
        TWO_FILES + 'improvements = "docs/IMPROVEMENTS.md"\n', encoding="utf-8"
    )
    with (root / "docs/IMPROVEMENTS.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write("# Improvements\n\n## Block A — The model\n\n### RK1 — A first symptom\n\nBecause.\n")
    return root


def test_an_embed_carries_every_governed_file_the_project_declares(tmp_path):
    """What RK343 left: `lint` is the command the fault offer suggests most, and a capture of it
    carrying the one file its finding named stages two short of what it reads."""
    root = three_files(tmp_path / "theirs")
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root, embed=True)
    assert [name for name, _ in found.documents] == [
        ROADMAP,
        "docs/CHANGELOG.md",
        "docs/IMPROVEMENTS.md",
    ]
    outcome = replay(found.as_dict(), staging(tmp_path))
    assert outcome.ran and outcome.reproduces, str(outcome)


def test_nothing_the_config_does_not_declare_leaves(tmp_path):
    """The governed files and never the project. `--embed` is a wider disclosure than it was,
    and the list a reviewer checks it against is the `roadkeep.toml` printed beside it."""
    root = three_files(tmp_path / "theirs")
    (root / ".env").write_text("TOKEN=hunter2\n", encoding="utf-8")
    (root / "docs/notes.md").write_text("what we actually think\n", encoding="utf-8")
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root, embed=True)
    said = json.dumps(found.as_dict())
    assert "hunter2" not in said and "what we actually think" not in said


def test_a_declared_file_that_is_absent_is_not_invented(tmp_path):
    """An empty file in its place would be a project the reporter did not have, and the
    absence is a finding of its own — `lint` reports it as `file.missing`."""
    root = three_files(tmp_path / "theirs")
    (root / "docs/IMPROVEMENTS.md").unlink()
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root, embed=True)
    assert "docs/IMPROVEMENTS.md" not in dict(found.documents)
    assert replay(found.as_dict(), staging(tmp_path)).unstaged == ("docs/IMPROVEMENTS.md",)


def test_a_capture_written_before_the_format_changed_still_replays(tmp_path):
    """A corpus that only accepts the current spelling is a corpus that loses the field reports
    it exists to keep, and those are already on somebody's disk."""
    root = project(tmp_path / "theirs")
    found = capture(SYMPTOM, WHY, "F", ["-C", str(root), "lint"], root, embed=True)
    recorded = found.as_dict()
    (name, text), = found.documents
    recorded.pop("documents")
    recorded["document"], recorded["document_path"] = text, name  # how RK344 found them
    outcome = replay(recorded, staging(tmp_path))
    assert outcome.ran and outcome.reproduces, str(outcome)


# -- the annotation the triaging reader was missing (RK443) --------------------


def stopped_capture(tmp_path: Path) -> dict:
    """A capture whose own re-run was refused before the verb ran — the shape two of Shio's
    three field reports have, and the one whose evidence contradicts its claim."""
    root = project(tmp_path)
    found = capture(
        SYMPTOM, WHY, "F", ["-C", str(root), "add", "--block", "A"], root, embed=True
    )
    return found.as_dict()


def test_a_verdict_about_a_run_that_never_reached_the_verb_says_so(tmp_path):
    """RK440 annotated the capture for whoever took it; the command a maintainer runs to
    decide whether a field report is still live said `still reproduces` about a run that
    proved nothing. It reproduces by construction — the same argv earns the same refusal —
    so the boolean is right and what it is about is the refusal."""
    outcome = replay(stopped_capture(tmp_path / "theirs"), staging(tmp_path))
    assert outcome.ran and outcome.reproduces and outcome.stopped
    assert "refused before the verb ran" in str(outcome)
    assert "not the symptom it was filed under" in str(outcome)


def test_a_capture_that_reached_the_verb_carries_no_such_caveat(tmp_path):
    outcome = replay(recorded_from(tmp_path / "theirs"), staging(tmp_path))
    assert outcome.ran and outcome.reproduces and not outcome.stopped
    assert "refused before the verb ran" not in str(outcome)


def test_the_caveat_is_derived_from_the_exit_the_capture_already_carried(tmp_path):
    """Never from a stored field, which is what makes it reach the two reports Shio filed
    before RK440 wrote one: every capture ever taken carries `exit`."""
    recorded = stopped_capture(tmp_path / "theirs")
    recorded.pop("stopped")  # how a capture taken before RK440 arrives
    assert replay(recorded, staging(tmp_path)).stopped


def test_the_caveat_never_moves_the_verdict_or_the_gate(tmp_path, capsys):
    """The corpus gate is deliberately not wired to it: refusing such an entry would fail
    this repository's own suite on captures that are honest records of a mistyped argv, and
    which of the two a capture is takes meaning this tool has none of (L4)."""
    recorded = stopped_capture(tmp_path / "theirs")
    path = tmp_path / "stopped.json"
    path.write_text(json.dumps(recorded), encoding="utf-8")
    assert main(["replay", str(path)]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "still reproduces" in printed and "refused before the verb ran" in printed

    assert main(["replay", str(path), "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["stopped"] is True and payload["reproduces"] is True
