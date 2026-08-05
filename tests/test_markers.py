"""The dep annotation as a derived field (RK8).

The property is one sentence: **after any write, no annotation in the file is a false
statement about another line.** The interesting half is what derivation refuses to do —
invent a marker where the author wrote none, and touch one it cannot resolve — because a
rule that rewrites every dep it can reach is a rule that makes half a backlog churn on
every commit, and churn is how a real diff stops being read.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roadkeep.backlog import Backlog
from roadkeep.config import Config
from roadkeep.markers import derive, refresh
from roadkeep.schema import Dep, SchemaError, Task

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

OPEN = "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1"
IDEA = "- 💭 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2"

BACKLOG = f"""# Roadmap

## Block A — The model

{OPEN}
{IDEA}

## Block B — Authoring
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK4** **A shipped symptom** — Because it shipped.
"""


def project(tmp_path: Path, *, roadmap: str = BACKLOG, changelog: str = LEDGER) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n',
        encoding="utf-8",
    )
    for name, body in {ROADMAP: roadmap, CHANGELOG: changelog}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def annotated(tmp_path: Path, *deps: str | Dep, roadmap: str = BACKLOG) -> list[str | None]:
    """The markers derivation produces for these deps, in order."""
    backlog = Backlog.load(project(tmp_path, roadmap=roadmap))
    task = Task(
        id="RK9",
        status="📋",
        block="B",
        symptom="A symptom",
        why="A reason.",
        deps=tuple(deps),
    )
    return [dep.marker for dep in derive(backlog, task).deps]


# -- shipped is always annotated ---------------------------------------------


def test_a_shipped_task_gains_the_shipped_marker(tmp_path):
    assert annotated(tmp_path, "RK4") == ["✅"]


def test_a_block_with_nothing_open_is_the_same_answer(tmp_path):
    # Three kinds, one meaning: waiting on this is over.
    assert annotated(tmp_path, "Block B", "RK1–RK2", roadmap="## Block B — Authoring\n") == [
        "✅",
        "✅",
    ]


def test_a_block_that_still_has_work_is_not_annotated(tmp_path):
    assert annotated(tmp_path, "Block A") == [None]


# -- what is never invented, and never destroyed -----------------------------


def test_an_unannotated_open_dep_stays_unannotated(tmp_path):
    # Deriving 📋 onto every open dep would rewrite half a backlog to say what
    # `deps <id>` answers better, and every such line would grow by two characters.
    assert annotated(tmp_path, "RK1", "RK2") == [None, None]


def test_an_annotation_that_exists_is_kept_true(tmp_path):
    # Shio annotates ⏳ and 📋 deps; those follow their target instead of being dropped.
    assert annotated(tmp_path, Dep("RK1", "⏳"), Dep("RK2", "📋")) == ["📋", "💭"]


def test_a_stale_shipped_marker_on_open_work_is_corrected(tmp_path):
    assert annotated(tmp_path, Dep("RK1", "✅")) == ["📋"]


def test_a_stale_shipped_marker_on_a_reopened_block_is_dropped(tmp_path):
    # A block is many lines with many markers, so no single marker replaces the ✅.
    assert annotated(tmp_path, Dep("Block A", "✅")) == [None]


def test_work_outside_the_backlog_is_left_exactly_as_written(tmp_path):
    assert annotated(tmp_path, "real design partners", Dep("real design partners", "✅")) == [
        None,
        "✅",
    ]


def test_an_unknown_id_is_a_lint_error_not_a_rendering_choice(tmp_path):
    assert annotated(tmp_path, "RK77", Dep("RK77", "✅")) == [None, "✅"]


# -- refreshing a whole document ---------------------------------------------


def test_only_the_lines_that_changed_are_rewritten(tmp_path):
    stale = BACKLOG.replace("(deps: —)", "(deps: RK4)", 1).replace(
        f"{IDEA}", IDEA.replace("(deps: —)", "(deps: RK1 ✅)")
    )
    config = project(tmp_path, roadmap=stale)
    result = refresh(Backlog.load(config))
    assert result.changed == ("RK1", "RK2")
    assert result.document.render() == stale.replace("(deps: RK4)", "(deps: RK4 ✅)").replace(
        "(deps: RK1 ✅)", "(deps: RK1 📋)"
    )


def test_a_file_with_nothing_to_derive_is_untouched(tmp_path):
    config = project(tmp_path)
    result = refresh(Backlog.load(config))
    assert result.changed == ()
    assert result.document.render() == BACKLOG


def test_a_line_the_annotation_would_push_over_the_cap_is_refused(tmp_path):
    # The derived ✅ costs two characters, so a line already at the limit cannot carry it.
    # Refusing names the id; writing it would put the file out of conformance silently.
    long = (
        "- 📋 **RK1** (deps: RK4) **A symptom that is quite long** — "
        "Because of a reason that fills the line. → §RK1"
    )
    project(tmp_path, roadmap=f"## Block A — The model\n\n{long}\n")
    # The cap is this line exactly, so a derived ✅ has nowhere to go.
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
        f"[limits]\nline = {len(long)}\n",
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    with pytest.raises(SchemaError) as raised:
        refresh(Backlog.load(config))
    # Named on the `why`, which is the field that has to give: the annotation grew the
    # structure, so the line has two fewer characters for prose and the message says so
    # (RK183). Either way the refusal is the point — the file is not written.
    (violation,) = raised.value.violations
    assert violation.code == "why.too-long"
    assert f"limit of {len(long)}" in violation.message
    assert config.document("roadmap").render().endswith(f"{long}\n")


def test_the_refusal_names_the_dependent_line_and_not_a_bare_count(tmp_path):
    """The sentence that went over is somebody else's, so the count alone sends the author
    to shorten the one they typed (RK348). The id and its `file:line` are what turn the
    refusal into an address; the limit it already stated survives beside them.
    """
    long = (
        "- 📋 **RK1** (deps: RK4) **A symptom that is quite long** — "
        "Because of a reason that fills the line. → §RK1"
    )
    project(tmp_path, roadmap=f"## Block A — The model\n\n{long}\n")
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
        f"[limits]\nline = {len(long)}\n",
        encoding="utf-8",
    )
    with pytest.raises(SchemaError) as raised:
        refresh(Backlog.load(Config.discover(tmp_path)))
    (violation,) = raised.value.violations
    assert f"RK1's line ({ROADMAP}:3)" in violation.message
    assert "dep annotation" in violation.message
    # Appended, never substituted: the rule and its number are still what a fix needs.
    assert violation.message.startswith("40 characters, limit is 38")
