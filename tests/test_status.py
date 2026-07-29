"""One marker, one file (RK7).

The rule under test is not "write the marker" — that is one line of code. It is that
every other place a status could be written is refused: the changelog, a rationale file
that grew a bullet, a second line for the same id, and ✅ in a file whose whole point is
that it holds only open work.

Each refusal leaves the roadmap byte-identical, because a command that half-applies a
status is how two files come to disagree in the first place.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.authoring import DuplicateId, StatusElsewhere, set_status
from roadkeep.backlog import NotOpen
from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.document import RoundTripError
from roadkeep.schema import SchemaError

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
        "  event    RK1  Block A  open",
    ]


def test_the_command_says_when_there_was_nothing_to_do(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK1", "📋"]) == EXIT_OK
    # Still an event: a hook cannot tell 'nothing to do' from 'never ran' otherwise.
    assert capsys.readouterr().out.splitlines() == [
        f"RK1 is already 📋  {ROADMAP}:5",
        "  event    RK1  Block A  open",
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
