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
from roadkeep.kernel.schema import Dep, SchemaError, Task, width

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
STORE = "docs/DEFERRED.md"

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


def project(
    tmp_path: Path,
    *,
    roadmap: str = BACKLOG,
    changelog: str = LEDGER,
    deferred: str | None = None,
) -> Config:
    store = f'deferred = "{STORE}"\n' if deferred is not None else ""
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
        + store,
        encoding="utf-8",
    )
    files = {ROADMAP: roadmap, CHANGELOG: changelog}
    if deferred is not None:
        files[STORE] = deferred
    for name, body in files.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def annotated(
    tmp_path: Path,
    *deps: str | Dep,
    roadmap: str = BACKLOG,
    changelog: str = LEDGER,
    deferred: str | None = None,
) -> list[str | None]:
    """The markers derivation produces for these deps, in order."""
    backlog = Backlog.load(
        project(tmp_path, roadmap=roadmap, changelog=changelog, deferred=deferred)
    )
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


def test_a_finished_block_and_an_empty_range_are_the_same_answer(tmp_path):
    # Three kinds, one meaning: waiting on this is over. What makes the block one of them
    # is the ledger filing an entry under the label and never the heading (RK432).
    assert annotated(
        tmp_path,
        "Block B",
        "RK1–RK2",
        roadmap="## Block B — Authoring\n",
        changelog=LEDGER + "\n## Block B — Authoring\n\n- ✅ **RK5** **A symptom** — Done.\n",
    ) == ["✅", "✅"]


def test_a_block_declared_before_its_first_line_is_not_annotated_shipped(tmp_path):
    # The checkmark §RK432 is about: the heading was written, nothing was ever filed under
    # it, and the annotation said waiting was over. Neither invented onto the bare token
    # nor left standing where an author typed one — a collective marker is derived by
    # construction, so there is no reading of one line for the preserve rule to protect.
    assert annotated(
        tmp_path, "Block B", Dep("Block B", "✅"), roadmap="## Block B — Authoring\n"
    ) == [None, None]


def test_a_block_with_nothing_open_and_work_in_the_store_is_annotated_paused(tmp_path):
    # RK92's marker at the level `Standing` says the block is at (RK432): not "every line
    # was set aside" but "nothing open, and something a `resume` brings back" — the one
    # state a dependent's own line cannot show.
    assert annotated(
        tmp_path,
        "Block B",
        roadmap="## Block B — Authoring\n",
        deferred="## Block B — Authoring\n"
        "- ⏸ **RK6** (deps: —) **A symptom** — set aside: waiting. → §RK6\n",
    ) == ["⏸"]


def test_a_marker_on_a_block_nothing_declares_is_not_the_authors_to_keep(tmp_path):
    # The other half of the branch `test_work_outside_the_backlog_is_left_exactly_as_written`
    # pins: the preserve rule is about a dep naming one line, and `Block Z` names many.
    assert annotated(tmp_path, Dep("Block Z", "✅")) == [None]


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
        f"[limits]\nline = {width(long)}\n",
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
    assert f"limit of {width(long)}" in violation.message
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
        f"[limits]\nline = {width(long)}\n",
        encoding="utf-8",
    )
    with pytest.raises(SchemaError) as raised:
        refresh(Backlog.load(Config.discover(tmp_path)))
    (violation,) = raised.value.violations
    assert f"RK1's line ({ROADMAP}:3)" in violation.message
    assert "dep annotation" in violation.message
    # **Leading** since RK1152: RK348 appended this clause, so the sentence still opened with a
    # count about the string the caller had just typed and the redirection arrived after the
    # remedy — read in order, it says shorten the wrong prose. The rule and its number survive
    # after the address, because a refusal that only says what to type teaches nobody why.
    assert violation.message.startswith(f"on RK1's line ({ROADMAP}:3), not on the text passed")
    assert "40 characters, limit is 38" in violation.message
    assert "amend RK1 --why" in violation.message


def test_every_line_the_write_would_overflow_is_named_in_one_refusal(tmp_path):
    """RK1152's second half, and the one that cost the rounds.

    `ship DD34` was refused three times in Shio: each refusal named one dependent, the author
    amended it, and the next was found only by re-running the command. Three lines whose
    annotation this write ticks are three violations of one refusal — the scan does not stop at
    the first, because `derive` reads the backlog rather than the document being rebuilt, so the
    third overflow is as true as the first before anything is written.
    """
    lines = [
        f"- 📋 **RK{n}** (deps: RK4) **A symptom that is quite long** — "
        f"Because of a reason that fills the line. → §RK{n}"
        for n in (1, 2, 3)
    ]
    project(tmp_path, roadmap="## Block A — The model\n\n" + "\n".join(lines) + "\n")
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
        f"[limits]\nline = {width(lines[0])}\n",
        encoding="utf-8",
    )
    with pytest.raises(SchemaError) as raised:
        refresh(Backlog.load(Config.discover(tmp_path)))
    named = {
        one.message.split("'s line", 1)[0].removeprefix("on ")
        for one in raised.value.violations
    }
    assert named == {"RK1", "RK2", "RK3"}, named
    # And each one carries the edit that closes it, so one round of amends is enough.
    assert all(f"amend {who} --why" in " ".join(
        one.message for one in raised.value.violations
    ) for who in named)
