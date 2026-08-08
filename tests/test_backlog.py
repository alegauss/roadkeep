"""Resolving deps, and the four answers to "is it done?" (RK28).

The claim under test is that **unresolvable is not the same as open**. Every other
assertion here exists to keep that one honest: a block dep resolves, a range dep
resolves, an id-shaped mistake is reported, and only genuine outside work is called
unresolvable — otherwise the distinction would just be a label on everything the
parser found difficult.

The dep kinds are the ones the live backlogs write. `Block P` is Shio's, `T451–T457`
and `real design partners` are Turing's; none of the three was invented here.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import corpora
from roadkeep.backlog import Backlog, DepStatus, Readiness, Stage, id_order, number_of
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.document import Document
from roadkeep.schema import DESIGNED, SHIPPED, Dep, DepKind, Schema

HERE = Path(__file__).resolve().parents[1]


def write_project(tmp_path: Path, roadmap: str, changelog: str = "") -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    return Config.discover(tmp_path)


def line(task_id: str, deps: str, block: str = "A") -> str:
    return (
        f"- {DESIGNED} **{task_id}** (deps: {deps}) **A symptom** "
        f"— a reason. → §{task_id}\n"
    )


def shipped(task_id: str) -> str:
    return f"- {SHIPPED} **{task_id}** **A symptom** — a reason.\n"


# -- classification ----------------------------------------------------------


@pytest.mark.parametrize(
    ("token", "kind"),
    [
        ("RK5", DepKind.TASK),
        ("Block P", DepKind.BLOCK),
        ("Block BJ", DepKind.BLOCK),
        ("RK451–RK457", DepKind.RANGE),
        ("RK451–457", DepKind.RANGE),
        ("RK451-457", DepKind.RANGE),
        ("real design partners", DepKind.EXTERNAL),
        ("upstream review", DepKind.EXTERNAL),
        # Mistakes must not hide as external work, or a typo becomes a permanent
        # blocker nobody can see.
        ("RK007", DepKind.TASK),
        ("RK9x", DepKind.TASK),
        ("SH341", DepKind.TASK),
        # A descending range is not a range; it falls through to external, so the
        # schema reports it (see the next test) instead of the resolver claiming
        # nothing here can ever satisfy it.
        ("RK457–RK451", DepKind.EXTERNAL),
    ],
)
def test_a_dep_is_classified_by_what_it_names(token, kind):
    assert Schema().classify_dep(Dep(token)) == kind


def test_only_an_id_shaped_mistake_is_a_format_violation():
    schema = Schema()
    assert schema.validate(_task(deps=("Block P", "real design partners"))) == ()
    codes = {v.code for v in schema.validate(_task(deps=("RK007",)))}
    assert codes == {"deps.format"}


def test_a_range_that_does_not_ascend_is_reported_rather_than_called_external():
    codes = {v.code for v in Schema().validate(_task(deps=("RK457–RK451",)))}
    assert codes == {"deps.range"}


def test_free_text_naming_this_projects_ids_is_reported_rather_than_called_external():
    # The measured case (RK389): `--dep "RK5 + RK7"` matched no arm but the last, so a line
    # blocked on two real ids — one of them already shipped — read as blocked forever on work
    # that does not exist, and only a separate `deps` call ever said so.
    found = Schema().validate(_task(deps=("RK5 + RK7",)))
    assert {v.code for v in found} == {"deps.compound"}
    assert "RK5 and RK7" in found[0].message


def test_one_id_buried_in_prose_is_the_same_mistake_told_in_the_singular():
    found = Schema().validate(_task(deps=("the rewrite after RK5",)))
    assert {v.code for v in found} == {"deps.compound"}
    assert "names RK5 of this project" in found[0].message
    assert "its own dep" in found[0].message


def test_external_work_that_names_no_id_of_this_project_stays_external():
    # The arm this must not close. Turing's T902 waits on `roadkeep RK378 + RK377`, which is
    # another project's backlog — ids, but not *these* ids, and the whole point of free text.
    schema = Schema()
    assert schema.validate(_task(deps=("roadkeep T378 + T377",))) == ()
    assert schema.validate(_task(deps=("upstream review",))) == ()
    # And an id is bounded on both sides: `RK55` is one id, not `RK5` inside a longer word.
    assert schema.ids_named("RK55") == ("RK55",)


def _task(**over):
    from roadkeep.schema import Task

    fields = dict(
        id="RK9",
        status=DESIGNED,
        block="A",
        symptom="A symptom",
        why="a reason.",
        deps=(),
        ref="RK9",
    )
    fields.update(over)
    return Task(**fields)


# -- resolution --------------------------------------------------------------


def test_a_task_dep_resolves_against_both_files(tmp_path):
    config = write_project(
        tmp_path,
        "## Block A — The model\n" + line("RK9", "RK1 ✅, RK5") + line("RK5", "—"),
        "## Block A — The model\n" + shipped("RK1"),
    )
    backlog = Backlog.load(config)
    statuses = {r.dep.id: r.status for r in backlog.resolve(backlog.entry("RK9").task)}
    assert statuses == {"RK1": DepStatus.SHIPPED, "RK5": DepStatus.OPEN}


def test_an_id_that_exists_in_neither_file_is_unknown_not_open(tmp_path):
    config = write_project(tmp_path, "## Block A — The model\n" + line("RK9", "RK77"))
    backlog = Backlog.load(config)
    (resolution,) = backlog.resolve(backlog.entry("RK9").task)
    assert resolution.status is DepStatus.UNKNOWN
    assert "neither" in resolution.detail


def test_a_block_dep_resolves_against_that_blocks_open_tasks(tmp_path):
    config = write_project(
        tmp_path,
        "## Block A — The model\n"
        + line("RK9", "Block B")
        + "## Block B — Authoring\n"
        + line("RK5", "—", block="B"),
    )
    backlog = Backlog.load(config)
    (resolution,) = backlog.resolve(backlog.entry("RK9").task)
    assert resolution.kind is DepKind.BLOCK
    assert resolution.status is DepStatus.OPEN
    assert "RK5" in resolution.detail


def test_a_collective_dep_expands_to_the_open_tasks_it_names(tmp_path):
    # One answer, two callers (RK35): the graph would otherwise walk into a dep it treats
    # as opaque, and the gate says out loud what one token costs a reader counting deps.
    config = write_project(
        tmp_path,
        "## Block A — The model\n"
        + line("RK9", "Block B")
        + line("RK10", "RK20–RK30")
        + line("RK25", "—")
        + "## Block B — Authoring\n"
        + line("RK5", "—", block="B")
        + line("RK6", "—", block="B"),
    )
    backlog = Backlog.load(config)
    assert backlog.expand(Dep("Block B")) == ("RK5", "RK6")
    assert backlog.expand(Dep("RK20–RK30")) == ("RK25",)
    # A task and something outside the backlog name no members, rather than themselves.
    assert backlog.expand(Dep("RK5")) == ()
    assert backlog.expand(Dep("real design partners")) == ()


def test_a_declared_block_with_nothing_open_satisfies_the_dep(tmp_path):
    config = write_project(
        tmp_path, "## Block A — The model\n" + line("RK9", "Block B") + "## Block B — Authoring\n"
    )
    backlog = Backlog.load(config)
    (resolution,) = backlog.resolve(backlog.entry("RK9").task)
    assert resolution.status is DepStatus.SHIPPED


def test_a_block_declared_only_by_the_ledger_still_resolves(tmp_path):
    # The last task of a block ships, its roadmap heading goes, and the dep must not
    # flip from satisfied to unresolvable because the file it emptied stopped saying
    # the block ever existed.
    config = write_project(
        tmp_path,
        "## Block A — The model\n" + line("RK9", "Block B"),
        "## Block B — Authoring\n" + shipped("RK5"),
    )
    backlog = Backlog.load(config)
    (resolution,) = backlog.resolve(backlog.entry("RK9").task)
    assert resolution.status is DepStatus.SHIPPED
    assert backlog.declared_blocks() == {"A", "B"}


def test_a_range_dep_resolves_against_the_ids_inside_it(tmp_path):
    config = write_project(
        tmp_path,
        "## Block A — The model\n"
        + line("RK9", "RK20–RK30")
        + line("RK25", "—")
        + line("RK40", "—"),
    )
    backlog = Backlog.load(config)
    (resolution,) = backlog.resolve(backlog.entry("RK9").task)
    assert resolution.kind is DepKind.RANGE
    assert resolution.status is DepStatus.OPEN
    assert "RK25" in resolution.detail and "RK40" not in resolution.detail


def test_a_range_with_no_open_members_is_satisfied_not_unknown(tmp_path):
    # Ids are non-contiguous by design, so "nothing open in RK20–RK30" is an answer
    # and not a gap: Turing's T477 waits on T451–T457, all of which have shipped.
    config = write_project(tmp_path, "## Block A — The model\n" + line("RK9", "RK20–RK30"))
    backlog = Backlog.load(config)
    (resolution,) = backlog.resolve(backlog.entry("RK9").task)
    assert resolution.status is DepStatus.SHIPPED


# -- what became of a label (RK429) ------------------------------------------


def test_the_four_states_a_label_can_be_in(tmp_path):
    """One reader, because three commands were about to compose this three times.

    The discriminator between `finished` and `empty` is **entries under the label**, not
    the heading: `block add` writes the heading into every organised file the moment the
    label is declared, so a heading in the ledger proves only that somebody declared it.
    """
    config = write_project(
        tmp_path,
        "## Block A — The model\n"
        + line("RK9", "—")
        + "\n## Block B — Authoring\n"
        + "\n## Block C — Query\n",
        "## Block B — Authoring\n" + shipped("RK1") + "\n## Block C — Query\n",
    )
    backlog = Backlog.load(config)
    states = {label: backlog.standing(label).stage for label in "ABCZ"}
    assert states == {
        "A": Stage.LIVE,
        # Declared in both files and filed under in the ledger: done.
        "B": Stage.FINISHED,
        # Declared in both files and filed under in neither — the heading is what
        # `block add` wrote, and it is the fact this must not read as completion.
        "C": Stage.EMPTY,
        "Z": Stage.UNKNOWN,
    }
    assert backlog.standing("B").recorded == 1
    assert backlog.standing("A").open == 1


def test_every_count_is_taken_whatever_the_state_turned_out_to_be(tmp_path):
    # An early return once made `recorded` read 0 for a live block the ledger files
    # entries under — a field only true in the branch that needed it, which is a payload
    # a caller reads wrongly exactly once.
    config = write_project(
        tmp_path,
        "## Block A — The model\n" + line("RK9", "—"),
        "## Block A — The model\n" + shipped("RK1") + shipped("RK2"),
    )
    standing = Backlog.load(config).standing("A")
    assert standing.stage is Stage.LIVE
    assert (standing.open, standing.recorded, standing.paused) == (1, 2, 0)


def test_a_ledger_that_only_retired_work_still_had_the_last_word(tmp_path):
    # `recorded` and not `shipped`: a retirement is filed in the ledger too, so the claim
    # `finished` makes is that the ledger has the last word — not that anything shipped.
    config = write_project(
        tmp_path,
        "## Block A — The model\n",
        f"## Block A — The model\n- 🗑 **RK1** **A symptom** — nobody will do it.\n",
    )
    standing = Backlog.load(config).standing("A")
    assert (standing.stage, standing.recorded) == (Stage.FINISHED, 1)


def test_a_block_whose_lines_were_all_set_aside_is_neither_of_the_two(tmp_path):
    """The state the first cut of this read as `empty`, in a sentence that was false.

    A deferred line is work: it keeps its id, its deps and its design, and a `resume`
    brings it back (RK92). Calling that block empty says nothing was ever filed under it,
    which the store on disk contradicts — and calling it finished is worse.
    """
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
        'changelog = "CHANGELOG.md"\ndeferred = "DEFERRED.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text("## Block A — The model\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(
        "## Block A — The model\n" + shipped("RK1"), encoding="utf-8"
    )
    (tmp_path / "DEFERRED.md").write_text(
        "## Block A — The model\n"
        "- ⏸ **RK2** (deps: —) **A symptom** — set aside: waiting. → §RK2\n",
        encoding="utf-8",
    )
    standing = Backlog.load(Config.discover(tmp_path)).standing("A")
    # Paused outranks the ledger: a block that shipped one line and set the other aside
    # is not finished, and that is the fact a `resume` would change.
    assert standing.stage is Stage.PAUSED
    assert (standing.paused, standing.recorded) == (1, 1)
    assert "1 set aside" in standing.sentence


def test_the_sentence_each_state_answers_with(tmp_path):
    # Spelled verbatim once, here, where it is written. Every other test asserts the word
    # or the distinguishing prefix, so a reword is one edit rather than four.
    config = write_project(
        tmp_path,
        "## Block A — The model\n" + line("RK9", "—") + "\n## Block C — Query\n",
        "## Block A — The model\n" + shipped("RK1") + "\n## Block B — Authoring\n"
        + shipped("RK2"),
    )
    backlog = Backlog.load(config)
    said = {label: backlog.standing(label).sentence for label in "ABCZ"}
    assert said == {
        "A": "Block A has 1 open",
        "B": "Block B is finished: nothing open, and the ledger records 1 filed under it",
        "C": "Block C is empty: the heading is declared and no task line is filed under it",
        "Z": "no heading declares Block Z",
    }
    # Only three of them explain an empty answer: `live` was emptied by a filter and
    # `unknown` is already refused in every surface's own words.
    settled = {label: backlog.standing(label).settled for label in "ABCZ"}
    assert settled == {"A": False, "B": True, "C": True, "Z": False}


def test_the_sentence_is_spelled_once_and_names_the_project_word(tmp_path):
    # `heading_word` is configurable (RK75), so a report saying "Block G" on a project
    # whose headings all say "Track" names nothing its author wrote.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[headings]\nword = "Track"\n[files]\n'
        'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text("## Track A — The model\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("", encoding="utf-8")
    standing = Backlog.load(Config.discover(tmp_path)).standing("A")
    assert standing.sentence.startswith("Track A is empty")


# -- the distinction that matters -------------------------------------------


def test_work_outside_the_backlog_is_unresolvable_not_open(tmp_path):
    config = write_project(
        tmp_path, "## Block A — The model\n" + line("RK9", "real design partners")
    )
    backlog = Backlog.load(config)
    (resolution,) = backlog.resolve(backlog.entry("RK9").task)
    assert resolution.status is DepStatus.UNRESOLVABLE
    assert not resolution.satisfied
    assert "nothing here will ever" in resolution.detail


def test_a_task_blocked_outside_the_backlog_is_not_merely_blocked(tmp_path):
    config = write_project(
        tmp_path,
        "## Block A — The model\n"
        + line("RK9", "real design partners")
        + line("RK10", "RK5")
        + line("RK11", "RK1 ✅"),
        "## Block A — The model\n" + shipped("RK1"),
    )
    backlog = Backlog.load(config)
    readiness = {e.task.id: backlog.readiness(e.task) for e in backlog.roadmap.entries}
    # Three different answers, where before there were two: RK9 never becomes ready
    # by shipping anything in this backlog, and `pick` must not offer it.
    assert readiness == {
        "RK9": Readiness.OUTSIDE,
        "RK10": Readiness.BLOCKED,
        "RK11": Readiness.READY,
    }


def test_a_block_no_heading_declares_is_unresolvable_not_satisfied(tmp_path):
    # RK37: emptiness is not completion. `Block Z` has nothing open for the same
    # reason a mistyped or renamed block has nothing open — it does not exist.
    config = write_project(tmp_path, "## Block A — The model\n" + line("RK9", "Block Z"))
    backlog = Backlog.load(config)
    (resolution,) = backlog.resolve(backlog.entry("RK9").task)
    assert resolution.kind is DepKind.BLOCK
    assert resolution.status is DepStatus.UNRESOLVABLE
    assert not resolution.satisfied
    assert "nothing declares" in resolution.detail


def test_an_undeclared_block_never_reads_as_ready(tmp_path):
    # The failure this closes: RK9 waited on a block nothing ever built, and `pick`
    # would have offered it as the next task to start.
    config = write_project(
        tmp_path,
        "## Block A — The model\n"
        + line("RK9", "Block Z")
        + line("RK10", "Block A")
        + "## Block B — Authoring\n",
    )
    backlog = Backlog.load(config)
    readiness = {e.task.id: backlog.readiness(e.task) for e in backlog.roadmap.entries}
    assert readiness == {"RK9": Readiness.OUTSIDE, "RK10": Readiness.BLOCKED}


def test_a_task_with_no_deps_is_ready(tmp_path):
    config = write_project(tmp_path, "## Block A — The model\n" + line("RK9", "—"))
    backlog = Backlog.load(config)
    assert backlog.readiness(backlog.entry("RK9").task) is Readiness.READY


# -- the live corpora --------------------------------------------------------


def test_this_repository_resolves_every_dep(governed):
    backlog = Backlog.load(Config.discover(governed))
    unresolved = [
        (e.task.id, r.dep.id, str(r.status))
        for e in backlog.roadmap.entries
        for r in backlog.resolve(e.task)
        if r.status is DepStatus.UNKNOWN
    ]
    assert unresolved == []


def test_shios_block_deps_all_name_a_block_it_declares():
    # The counter-check on RK37: the new answer must be reachable only by a mistake.
    # Shio writes the only block deps in any corpus here, and all of them resolve.
    corpora.require(corpora.SHIO)
    schema = corpora.config(corpora.SHIO).schema_for("roadmap")
    document = corpora.document(corpora.SHIO, "roadmap")
    declared = {h.label for h in document.headings if h.label}
    named = {
        schema.block_of_dep(dep)
        for e in document.entries
        for dep in e.task.deps
        if schema.classify_dep(dep) is DepKind.BLOCK
    }
    assert named and named <= declared


@pytest.mark.parametrize(
    ("corpus", "expected"),
    [
        (corpora.SHIO, {DepKind.BLOCK}),
        (corpora.TURING, {DepKind.RANGE, DepKind.EXTERNAL}),
    ],
    ids=lambda value: value.name if isinstance(value, corpora.Corpus) else "",
)
def test_the_live_backlogs_use_the_kinds_this_model_has(corpus, expected):
    corpora.require(corpus)
    schema = corpora.config(corpus).schema_for("roadmap")
    document = corpora.document(corpus, "roadmap")
    kinds = {
        schema.classify_dep(dep) for e in document.entries for dep in e.task.deps
    }
    assert expected <= kinds
    # And none of them is a format violation any more: they were never mistakes.
    assert not [
        v
        for e in document.entries
        for v in schema.validate(e.task)
        if v.code.startswith("deps")
    ]


# -- the command -------------------------------------------------------------


def test_the_command_reports_each_dep_and_the_verdict(tmp_path, capsys):
    write_project(
        tmp_path,
        "## Block A — The model\n" + line("RK9", "RK1 ✅, real design partners"),
        "## Block A — The model\n" + shipped("RK1"),
    )
    assert main(["-C", str(tmp_path), "deps", "RK9"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "unresolvable" in out and "shipped" in out
    # The verdict is a line of its own; RK13 appends the graph after it, so it is no
    # longer the last word.
    assert "RK9: blocked-outside" in out.splitlines()


def test_json_carries_the_kind_and_the_status(tmp_path, capsys):
    write_project(
        tmp_path,
        "## Block A — The model\n" + line("RK9", "Block B") + "## Block B — Authoring\n",
    )
    assert main(["-C", str(tmp_path), "deps", "RK9", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["readiness"] == "ready"  # Block B is declared and has nothing open
    assert payload["deps"] == [
        {
            "dep": "Block B",
            "kind": "block",
            "status": "shipped",
            "detail": "Block B has nothing open",
        }
    ]


def test_asking_about_a_shipped_task_says_where_it_went(tmp_path, capsys):
    write_project(
        tmp_path,
        "## Block A — The model\n",
        "## Block A — The model\n" + shipped("RK1"),
    )
    assert main(["-C", str(tmp_path), "deps", "RK1"]) == EXIT_USAGE
    assert "in the changelog" in capsys.readouterr().err


# -- one ordering, so a fifth caller cannot write a fourth one (RK109) -------

SPLIT = Schema(prefixes=("T",), id_suffix=True, ref_scheme="outline")
PADDED = Schema(prefixes=("D",), id_pad=2, heading_word="Track")


def test_the_ordering_is_numeric_and_not_lexical():
    ids = ["RK10", "RK9", "RK100", "RK1"]
    assert sorted(ids, key=lambda i: id_order(i, Schema())) == [
        "RK1",
        "RK9",
        "RK10",
        "RK100",
    ]


def test_a_split_task_sorts_directly_after_the_number_it_split():
    # `T24b` is the task Turing numbered *after* T24 on purpose. Read as no id it counted
    # as zero, and zero is first — so `pick` offered it ahead of T1.
    ids = ["T25", "T24b", "T1", "T24"]
    assert sorted(ids, key=lambda i: id_order(i, SPLIT)) == ["T1", "T24", "T24b", "T25"]


def test_an_id_this_project_cannot_read_sorts_last_and_never_first():
    # `D1` is a spelling this project's own gate refuses; the ordering used to read it as
    # 1 and put it ahead of D02. A string the gate will not admit is not a claim on the
    # front of the queue, so it goes to the end, by its own text.
    ids = ["D02", "D1", "D01", "nonsense"]
    assert sorted(ids, key=lambda i: id_order(i, PADDED)) == [
        "D01",
        "D02",
        "D1",
        "nonsense",
    ]


def test_the_number_is_read_within_one_family_when_a_range_asks_for_one():
    tracks = Schema(prefixes=("C", "V"), ref_scheme="outline")
    assert number_of("C14", tracks) == 14
    assert number_of("C14", tracks, "C") == 14
    assert number_of("V15", tracks, "C") is None
    assert number_of("D1", PADDED) is None


# -- the read before a proposal (RK385) ---------------------------------------


def test_a_block_states_what_it_delivered(tmp_path, capsys):
    """RK378 restated RK340 the day after it shipped; `add` accepted it, `lint` passed it,
    `pick` offered it, and the duplication surfaced only when a worker claimed the line."""
    from roadkeep.cli import EXIT_OK, main

    root = _shipped(tmp_path)
    assert main(["-C", str(root), "delivered", "A"]) == EXIT_OK
    out = capsys.readouterr().out
    # Three, because the retired one is a claim too — see below.
    assert "Block A, 3 delivered" in out
    assert "A first symptom" in out and "A second symptom" in out


def test_the_outcome_sentence_is_left_out(tmp_path, capsys):
    # A duplicate collides with the *claim*; the outcome is written in the vocabulary of the
    # fix and never matches, so printing it doubles a read made before every proposal.
    from roadkeep.cli import EXIT_OK, main

    root = _shipped(tmp_path)
    assert main(["-C", str(root), "delivered", "A"]) == EXIT_OK
    assert "it was done" not in capsys.readouterr().out


def test_a_retired_claim_is_in_it_and_says_which_it_is(tmp_path, capsys):
    # A claim that was abandoned is still one somebody argued about, and a proposal restating
    # it wants the argument more than the outcome — so the marker says which.
    from roadkeep.cli import EXIT_OK, main

    root = _shipped(tmp_path)
    assert main(["-C", str(root), "delivered", "A"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "🗑 DX3" in out


def test_a_block_that_delivered_nothing_says_so(tmp_path, capsys):
    # Never an empty stdout: "this block has delivered nothing" and "this command found
    # nothing to read" look the same to a caller, and only one of them is an answer.
    from roadkeep.cli import EXIT_OK, main

    root = _shipped(tmp_path)
    assert main(["-C", str(root), "delivered", "Z"]) == EXIT_OK
    assert "has delivered nothing yet" in capsys.readouterr().out


def test_the_payload_carries_the_claim_and_the_marker(tmp_path, capsys):
    import json

    from roadkeep.cli import EXIT_OK, main

    root = _shipped(tmp_path)
    assert main(["-C", str(root), "delivered", "A", "--json"]) == EXIT_OK
    rows = json.loads(capsys.readouterr().out)["delivered"]
    assert [row["id"] for row in rows] == ["DX1", "DX2", "DX3"]
    assert all("symptom" in row and "marker" in row for row in rows)
    assert "why" not in rows[0]


def test_the_guard_names_it_beside_the_other_read():
    # Both reads before a proposal, in the table an agent meets when its `Edit` is denied:
    # `non-goal list` says what may not be proposed, and this says what already was.
    from roadkeep.guarding import _INSTEAD

    offered = dict(_INSTEAD["roadmap"])
    assert "delivered <x>" in offered
    assert "before `add`" in offered["delivered <x>"]


def _shipped(tmp_path):
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "DX"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    for name, body in (
        ("ROADMAP.md", "# Roadmap\n\n## Block A — The model\n"),
        (
            "CHANGELOG.md",
            "# Shipped\n\n## Block A — The model\n\n"
            "- ✅ **DX1** **A first symptom** — it was done.\n"
            "- ✅ **DX2** **A second symptom** — it was done.\n"
            "- 🗑 **DX3** **A third symptom** — superseded by DX1: it was the same thing.\n",
        ),
    ):
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path
