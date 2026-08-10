"""The record an approved shell write does not leave (RK175).

RK128 answers `ask` for a `Bash` command naming a governed path, and the user may say yes.
What is asserted here is the half that begins after they do: `lint` narrowed to the turn's
lines has no quarrel with a **conforming** hand-edit, so without this the file changed, no
verb wrote it, and every gate agreed it was correct.

Four failure modes, each of which would make it worse than nothing:

* **It must not fire on the normal path.** A verb's own write is the overwhelming majority
  of changes to these files, and a report that fires on `add` is one nobody reads.
* **It must be silent where it knows nothing.** A checkout in which no verb has run has no
  baseline, and reporting every file in it would report the history the project arrived with.
* **It must state one change once.** The record is the value; blocking every turn until
  somebody commits is the loop `stop_hook_active` exists to end, arrived at another way.
* **A query must not adopt bytes as attested.** `list` between two hand-edits reads the
  files, and a read that re-baselined would launder exactly the write this is about.

And what the fourth of those cost, closed by RK200: the report is consumed as it is made, so
the fact reached one reader at one moment and asking afterwards read as clean. `writes` is
that question as a command (L5) — three states, and no baseline moved by asking.
"""

from __future__ import annotations

import json
from pathlib import Path

from roadkeep import storing
from roadkeep.attesting import State, attest, record_path, survey, unattested
from roadkeep.cli import EXIT_OK, main
from roadkeep.config import Config
from roadkeep.guarding import attested, review
from roadkeep.provenance import invocation

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
"""

LEDGER = """# Shipped

## Block A — The model
"""

CONFIG = f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'


def project(tmp_path: Path) -> Path:
    """A minimal governed project, written with `newline=""` like every other fixture."""
    tmp_path.mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(CONFIG, encoding="utf-8")
    for name, body in {ROADMAP: CLEAN, CHANGELOG: LEDGER}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


def edit(root: Path, old: str, new: str) -> None:
    """What `sed -i` leaves behind: bytes in the file that no verb put there."""
    path = root / ROADMAP
    with path.open("r+", encoding="utf-8", newline="") as handle:
        text = handle.read().replace(old, new)
        handle.seek(0)
        handle.truncate()
        handle.write(text)


def test_a_conforming_hand_edit_is_reported_where_lint_has_nothing_to_say(tmp_path):
    # The whole symptom in one assertion: the reworded `why` is a legal `why`, the pointer
    # still resolves, and the annotation is right — so the format is happy and the question
    # of who wrote it had no answer at all before this.
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert review({"hook_event_name": "Stop"}, root) is None
    found = unattested(config)
    assert found is not None
    assert [role for role, _ in found.files] == ["roadmap"]
    assert "ROADMAP.md" in str(found)


def test_a_verbs_own_write_is_not_reported(tmp_path):
    # `dispatch` records under the same lock the write took, so the bytes a command left are
    # the baseline the next turn is judged against — otherwise every `add` would report.
    root = project(tmp_path)
    assert main(["-C", str(root), "status", "RK1", "🛠"]) == EXIT_OK
    assert unattested(Config.discover(root)) is None


def test_nothing_recorded_is_silence(tmp_path):
    # No verb has run here, so there is no claim to make: the drift such a project arrives
    # with is `lint`'s subject and never this one's.
    root = project(tmp_path)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert unattested(Config.discover(root)) is None


def test_one_change_is_stated_once(tmp_path):
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert unattested(config) is not None
    assert unattested(config) is None


def test_a_deleted_governed_file_is_the_change_it_most_wants_to_state(tmp_path):
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    (root / ROADMAP).unlink()
    found = unattested(config)
    assert found is not None
    assert [role for role, _ in found.files] == ["roadmap"]


def test_a_query_does_not_adopt_the_bytes_it_read(tmp_path):
    # `list` takes no lock and writes nothing, so it must not re-baseline either: a read
    # between two hand-edits would otherwise launder the first one.
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert main(["-C", str(root), "list"]) == EXIT_OK
    assert unattested(config) is not None


def test_the_stop_answer_states_the_fact_without_asking_the_bytes_back(tmp_path):
    # The alternative RK128 left open was to *refuse* a change no verb made, and that is
    # deliberately not what this says: the user approved the command, and re-litigating the
    # approval at the end of the turn spends what the `ask` was collected for.
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    found = attested({"hook_event_name": "Stop", "cwd": str(root)}, root)
    assert found is not None
    assert "roadkeep verb" in str(found)
    assert "the approval stands" in str(found)


def test_the_stop_answer_names_the_engine_this_session_can_reach(tmp_path):
    """RK479. RK444, RK447, RK448, RK477 and RK478 moved every route `guarding` composes;
    this module was in none of those counts, and `Unattested` was the last of the four
    messages that block a turn still naming one route for every session.

    It matters most here: reporting re-baselines, so this text is shown **once** and can
    never be asked for again — RK200 built `survey` because the fact had one moment. A route
    the reader cannot take is worst on the message they get one shot at."""
    from dataclasses import replace as _replace

    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    found = attested({"hook_event_name": "Stop", "cwd": str(root)}, root)
    assert found is not None
    # The wiring and not only the rendering: a `served` the hook never fills is a field that
    # reads correct in a unit test and names the shell in every session.
    from roadkeep.provenance import serving

    assert found.served == (serving(root) or "")
    served = str(_replace(found, served="mcp__roadkeep__"))
    assert "`mcp__roadkeep__lint` judges the format" in served
    assert invocation() not in served
    # And the shell form is untouched where a session has no tools, which is the case it was
    # always right for — the split `Review` has kept since RK448.
    assert f"`{invocation()} lint` judges the format" in str(_replace(found, served=""))


def test_a_second_pass_never_blocks(tmp_path):
    # Blocking a turn the agent has already been told about is the loop `review` refuses,
    # and this one honours the same flag rather than inventing a second rule.
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    payload = {"hook_event_name": "Stop", "cwd": str(root), "stop_hook_active": True}
    assert attested(payload, root) is None


def test_a_project_that_declares_nothing_is_never_judged(tmp_path):
    # The guard's rule, kept: silence outside a roadkeep project, and silence on failure.
    (tmp_path / "notes.md").write_text("nothing here\n", encoding="utf-8")
    assert attested({"hook_event_name": "Stop", "cwd": str(tmp_path)}, tmp_path) is None


def test_an_unreadable_record_is_silence_and_not_a_blocked_turn(tmp_path):
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    record_path(root).write_text("[writes\nroadmap =", encoding="utf-8")
    edit(root, "Because of a reason.", "Because of another reason.")
    assert unattested(config) is None


def states(root: Path) -> dict[str, str]:
    return {row.role: str(row.state) for row in survey(Config.discover(root))}


def test_the_read_answers_the_question_the_stop_block_consumed(tmp_path):
    # The symptom: reporting re-baselines, so the one reader who was told is the only one who
    # can ever know. Asked as a command, the fact is there for whoever asks.
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert states(root) == {"roadmap": "unattested", "changelog": "attested"}


def test_asking_moves_no_baseline_so_the_answer_survives_being_read(tmp_path):
    # The whole difference from the `Stop` block: a query that changed the answer to the next
    # query would launder the write this module exists to name.
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert states(root)["roadmap"] == "unattested"
    assert states(root)["roadmap"] == "unattested"
    assert unattested(config) is not None


def test_a_checkout_no_verb_has_run_in_says_so_rather_than_reading_as_clean(tmp_path):
    # `unattested` answers this with silence, which is right for a report and wrong for a
    # listing: "no baseline" and "nothing drifted" are the two things a caller must not confuse.
    root = project(tmp_path)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert set(states(root).values()) == {"unrecorded"}


def test_a_role_recorded_as_absent_and_still_absent_agrees(tmp_path):
    # Absence is a value in the record (`_digests`), so a declared file nothing ever wrote is
    # not drift — and `present` is what says the row is about a file that is not there.
    root = project(tmp_path)
    config = Config.discover(root)
    (root / CHANGELOG).unlink()
    attest(config)
    rows = {row.role: row for row in survey(config)}
    assert rows["changelog"].state is State.ATTESTED
    assert rows["changelog"].present is False


def test_the_rows_to_act_on_come_first(tmp_path):
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert [str(row.state) for row in survey(config)] == ["unattested", "attested"]


def test_the_command_names_every_file_and_where_the_record_lives(tmp_path, capsys):
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert main(["-C", str(root), "writes"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("2 governed, 1 unattested")
    assert ROADMAP in out
    assert str(record_path(root)) in out


def test_the_command_says_which_checkout_never_ran_a_verb(tmp_path, capsys):
    root = project(tmp_path)
    assert main(["-C", str(root), "writes"]) == EXIT_OK
    assert "nothing to differ from" in capsys.readouterr().out


def test_the_command_is_a_read_and_leaves_the_record_where_it_found_it(tmp_path, capsys):
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    edit(root, "Because of a reason.", "Because of another reason.")
    assert main(["-C", str(root), "writes", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["unattested"] == 1
    assert [f["state"] for f in payload["files"]] == ["unattested", "attested"]
    assert unattested(config) is not None


def test_the_record_lives_outside_the_repository(tmp_path):
    # A file the tool creates in a project's root is one every adopting project has to add
    # to its `.gitignore` before the first `git status` reads as dirty (RK117).
    root = project(tmp_path)
    config = Config.discover(root)
    attest(config)
    assert root not in record_path(root).parents
    # And in the store every other sidecar shares (RK330), under this module's own table.
    assert set(storing.read(root).writes) == {"roadmap", "changelog"}
