"""The state between open and terminal, as data (RK96).

Every marker this format had was one of two things: an open one the roadmap keeps, or a
terminal one the ledger owns. So "not now" and "not ever" were recorded the same way, and
the tests here are about the third file that makes them different — before any command
writes to it, because a store a `defer` invented on its way past would be a format decided
by a verb (Block A).

Four claims, and the third is the one that would rot silently:

* the store reads the **same grammar**, in the configuration `as_deferred` returns — one
  marker, and every other slot kept, because a resume restores what a pause set aside;
* ⏸ is **legal there and nowhere else**, the rule 🗑 already obeys, in both directions:
  neither a paused line in the roadmap nor an open one in the store is read as prose;
* a deferred task **keeps its id and its `§id` section** — the gate has to know that, or it
  reports the rationale a resume needs as an orphan and asks for its deletion;
* an annotation may **cache ⏸** like any other status (RK8), so the derivation RK91 runs
  cannot write a dep the gate then refuses.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roadkeep.authoring import IdInUse, StatusElsewhere, refuse_reuse, set_status
from roadkeep.config import Config, ConfigError
from roadkeep.document import Document
from roadkeep.linting import lint
from roadkeep.schema import DEFERRED, DESIGNED, IDEA, SHIPPED, Dep, Schema, Task

ROADMAP = f"""# Roadmap

## Block A — The model

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- {DESIGNED} **RK4** (deps: RK2 {DEFERRED}) **A fourth symptom** — Because of another. → §RK4
"""

LEDGER = """# Shipped

## Block A — The model
"""

DEFERRED_STORE = f"""# Set aside

## Block A — The model

- {DEFERRED} **RK2** (deps: RK1) **A paused symptom** — Because it waits on a decision. → §RK2
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.

### §RK2 A design set aside

The reasoning a resume gets back.

### §RK4 A fourth design

The reasoning that outlives the pause.
"""

DECLARE = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    'improvements = "IMPROVEMENTS.md"\ndeferred = "DEFERRED.md"\n'
)


def project(
    tmp_path: Path, files: dict[str, str] | None = None, declare: str = DECLARE
) -> Config:
    (tmp_path / "roadkeep.toml").write_text(declare, encoding="utf-8")
    written = {
        "ROADMAP.md": ROADMAP,
        "CHANGELOG.md": LEDGER,
        "IMPROVEMENTS.md": RATIONALE,
        "DEFERRED.md": DEFERRED_STORE,
        **(files or {}),
    }
    for name, body in written.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


# -- the same grammar, in one more configuration ------------------------------


def test_the_store_keeps_every_slot_the_ledger_drops():
    schema = Schema().as_deferred()
    assert schema.markers == (DEFERRED,) and schema.is_deferred
    # The ledger drops all three because a shipped line has no design and no blocker left.
    # A paused one has both, and a resume that had to reinvent them would be a re-add.
    assert schema.deps_field and schema.symptom_field and schema.marker_field
    assert schema.ref_required


def test_a_deferred_line_parses_and_round_trips(tmp_path):
    config = project(tmp_path)
    document = config.document("deferred")
    source = (tmp_path / "DEFERRED.md").read_text(encoding="utf-8")

    assert document.render() == source  # L3, with a ⏸ line in the file
    assert document.non_canonical == () and document.rejects == ()
    (entry,) = document.entries
    task = entry.task
    assert (task.id, task.status, task.block) == ("RK2", DEFERRED, "A")
    assert task.symptom == "A paused symptom" and task.ref == "RK2"
    assert task.deps == (Dep("RK1"),)  # the thread a resume keys on, kept verbatim


def test_the_store_refuses_the_markers_of_the_two_files_it_sits_between():
    schema = Schema().as_deferred()
    line = {"id": "RK2", "block": "A", "symptom": "A symptom", "why": "A reason.", "ref": "RK2"}
    for marker in (DESIGNED, IDEA, SHIPPED):
        codes = {v.code for v in schema.validate(Task(status=marker, **line))}
        assert "status.shipped" in codes or "status.unknown" in codes
    assert schema.validate(Task(status=DEFERRED, **line)) == ()


# -- legal there and nowhere else, in both directions -------------------------


def test_a_deferred_marker_in_the_roadmap_is_not_silently_prose():
    # The rule 🗑 already obeys (RK32): declared, but not for that file, so it is a reject
    # with a reason (RK10) rather than a line no count sees.
    text = f"# Roadmap\n\n## Block A\n\n- {DEFERRED} **RK1** (deps: —) **A symptom** — why.\n"
    document = Document.parse(text, Schema())
    assert document.entries == () and len(document.rejects) == 1
    assert "not a marker this project declares" in document.rejects[0].reason


def test_an_open_marker_in_the_store_is_not_silently_prose():
    # The other direction, which is the half that makes the file *be* the state: a store
    # that quietly held 📋 would be a second roadmap, and two files would say "open".
    text = f"# Set aside\n\n## Block A\n\n- {DESIGNED} **RK1** (deps: —) **A symptom** — why.\n"
    document = Document.parse(text, Schema().as_deferred())
    assert document.entries == () and len(document.rejects) == 1
    assert "not a marker this project declares" in document.rejects[0].reason


def test_the_marker_may_not_also_be_an_open_one(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[markers]\nopen = ["{DESIGNED}", "{DEFERRED}"]\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="is the deferred marker"):
        Config.discover(tmp_path)


def test_the_marker_may_not_be_a_departure(tmp_path):
    # Spelled the same as 🗑, a pause and an abandonment are recorded identically — which
    # is the whole defect. Refused at the file it is typed in, not inside `as_ledger`.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[markers]\ndeferred = "🗑"\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="markers.deferred must differ"):
        Config.discover(tmp_path)


def test_a_project_may_declare_its_own_marker(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[markers]\ndeferred = "❄"\n', encoding="utf-8"
    )
    config = Config.discover(tmp_path)
    assert config.schema.deferred_marker == "❄"
    assert config.schema_for("deferred").markers == ("❄",)


# -- the id and the section a resume needs ------------------------------------


def test_the_gate_reads_the_store_and_leaves_its_section_alone(tmp_path):
    config = project(tmp_path)
    report = lint(config)
    assert "DEFERRED.md" in report.checked and report.lines == 3
    # §RK2 is pointed at from the store, so it is kept — not the `section.orphan` the gate
    # would otherwise ask to delete, taking the rationale a resume gets back with it.
    assert [f.code for f in report.findings if f.id == "RK2"] == []
    assert not [f for f in report.findings if f.file == "DEFERRED.md"]


def test_a_dep_on_paused_work_is_the_one_thing_left_unresolved(tmp_path):
    # The seam RK92 is filed for, tested where it is rather than left to be discovered: the
    # resolver's four outcomes are shipped, open, unknown and unresolvable, and a deferred
    # dep is none of them — so today it reads as unknown. Data before the query (Block A).
    (found,) = lint(project(tmp_path)).findings
    assert found.code == "deps.unknown" and found.id == "RK4"


def test_a_pointer_the_store_dangles_is_the_same_finding(tmp_path):
    without = RATIONALE.replace(
        "### §RK2 A design set aside\n\nThe reasoning a resume gets back.\n\n", ""
    )
    config = project(tmp_path, {"IMPROVEMENTS.md": without})
    (found,) = [f for f in lint(config).findings if f.code == "ref.unresolved"]
    assert found.id == "RK2" and found.file == "DEFERRED.md"


def test_the_id_stays_taken(tmp_path):
    # What separates a pause from a retirement is that the id is still the same task's,
    # so nothing may mint it again while the store holds it (RK4).
    config = project(tmp_path)
    with pytest.raises(IdInUse):
        refuse_reuse(config, "RK2")


def test_two_files_may_not_both_carry_one_status(tmp_path):
    # The rule that makes the file the state: a hand-edit that left RK1 in both is refused
    # rather than resolved, because nothing says which of the two answers is right.
    twice = DEFERRED_STORE + (
        f"- {DEFERRED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1\n"
    )
    config = project(tmp_path, {"DEFERRED.md": twice})
    with pytest.raises(StatusElsewhere, match="deferred"):
        set_status(config, "RK1", IDEA)


# -- an annotation caches it like any other status ----------------------------


def test_a_dep_may_be_annotated_deferred(tmp_path):
    # RK8 derives the annotation from the target's status, so a status the store can hold
    # and an annotation cannot is a re-derivation that fails the gate that just ran.
    config = project(tmp_path)
    (entry,) = [e for e in config.document("roadmap").entries if e.task.id == "RK4"]
    assert entry.task.deps == (Dep("RK2", marker=DEFERRED),)
    assert config.schema.validate(entry.task) == ()
