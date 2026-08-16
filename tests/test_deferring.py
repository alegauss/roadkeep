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

import json
from dataclasses import replace
from pathlib import Path

import pytest

from roadkeep.authoring import IdInUse, StatusElsewhere, refuse_reuse, set_status
from roadkeep.backlog import Backlog, DepStatus, NotOpen, Readiness, Whereabouts
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError
from roadkeep.deferring import (
    Carried,
    NoStore,
    NotSetAside,
    SetAside,
    UnrecoverableReason,
    defer,
    resume,
)
from roadkeep.kernel.document import Document
from roadkeep.linting import lint
from roadkeep.picking import pick
from roadkeep.kernel.schema import (
    DEFERRED,
    DESIGNED,
    IDEA,
    PARTIAL,
    SHIPPED,
    Dep,
    Schema,
    SchemaError,
    Task,
)
from roadkeep.shipping import AlreadyRecorded

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


def test_a_dep_on_paused_work_resolves_as_paused_and_not_as_a_gap(tmp_path):
    # The fifth outcome (RK92). Read as unknown — which is what it was before the resolver
    # had an answer — the gate failed a file stating a legitimate wait, and told the reader
    # to go looking for a typo that is not there.
    config = project(tmp_path)
    assert lint(config).findings == ()
    backlog = Backlog.load(config)
    (resolution,) = backlog.resolve(backlog.entry("RK4").task)
    assert resolution.status is DepStatus.DEFERRED
    assert "set aside" in resolution.detail and "a decision" in resolution.detail


def test_a_task_waiting_on_paused_work_is_neither_ready_nor_blocked_forever(tmp_path):
    # The two wrong collapses, both named in §RK92: read as open, `pick` offers a task
    # whose blocker nobody is working; read as unresolvable, it buries one that unblocks.
    backlog = Backlog.load(project(tmp_path))
    assert backlog.readiness(backlog.entry("RK4").task) is Readiness.PAUSED
    assert backlog.readiness(backlog.entry("RK1").task) is Readiness.READY


def test_the_pick_does_not_offer_it_and_counts_it_apart(tmp_path):
    choice = pick(project(tmp_path))
    assert choice.entry.task.id == "RK1"
    assert (choice.ready, choice.blocked, choice.paused) == (1, 0, 1)
    assert "1 blocked on paused work" in choice.counts


def test_an_unresolvable_dep_still_outranks_a_paused_one(tmp_path):
    # Ordered by how permanent the answer is: a resume would leave the external dep, so
    # "blocked outside" is the honest word for a line carrying both.
    roadmap = ROADMAP.replace(
        "(deps: RK2 ⏸)", "(deps: RK2 ⏸, real design partners)"
    ).replace("⏸", DEFERRED)
    backlog = Backlog.load(project(tmp_path, {"ROADMAP.md": roadmap}))
    assert backlog.readiness(backlog.entry("RK4").task) is Readiness.OUTSIDE


def test_a_resumed_dep_stops_reading_as_paused(tmp_path):
    # The block lifts on a decision, which is the whole difference from `retire`'s never.
    config = project(tmp_path)
    resume(config, "RK2").save()
    backlog = Backlog.load(Config.discover(config.root))
    assert backlog.readiness(backlog.entry("RK4").task) is Readiness.BLOCKED
    (resolution,) = backlog.resolve(backlog.entry("RK4").task)
    assert resolution.status is DepStatus.OPEN


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


# -- the two doors, one of them the way back (RK91) ---------------------------


def read(config: Config, name: str) -> str:
    with (config.root / name).open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def files(config: Config) -> tuple[str, ...]:
    return tuple(
        read(config, name)
        for name in ("ROADMAP.md", "CHANGELOG.md", "IMPROVEMENTS.md", "DEFERRED.md")
    )


def test_the_line_leaves_the_roadmap_and_arrives_in_the_store(tmp_path):
    config = project(tmp_path)
    pause = defer(config, "RK1", reason="the decision it waits on is somebody else's")
    pause.save()
    assert pause.store.rendered == (
        f"- {DEFERRED} **RK1** (deps: —) **A first symptom** — set aside (the decision it "
        f"waits on is somebody else's): Because of a reason. → §RK1"
    )
    assert "RK1" not in config.document("roadmap").by_id()
    # Every slot the ledger would have dropped is still there, which is what a return needs.
    (held,) = [e for e in config.document("deferred").entries if e.task.id == "RK1"]
    assert (held.task.symptom, held.task.ref) == ("A first symptom", "RK1")


def test_the_rationale_is_carried_and_not_deleted(tmp_path):
    # The one edit a departure makes that this one must not: `ship` deletes the design
    # because a shipped line has none left to state, and a paused line has all of it.
    config = project(tmp_path)
    pause = defer(config, "RK1", reason="it waits on a decision")
    pause.save()
    assert pause.carried == Carried(anchor="§RK1", role="improvements")
    assert "### §RK1 A first design" in read(config, "IMPROVEMENTS.md")
    # And the gate agrees it is not an orphan, which is the half RK96 already built.
    assert not [f for f in lint(config).findings if f.id == "RK1"]


def test_the_carried_design_names_the_file_that_declares_it(tmp_path, capsys):
    # RK229. The assumption RK196 removed from the ship, made one door over: the pause
    # carried the anchor alone, so the CLI supplied `improvements` — and against a project
    # that declares strategy alone the answer was not merely the wrong path, it was a
    # KeyError raised *after* both files were written.
    config = project(
        tmp_path,
        {"STRATEGY.md": RATIONALE},
        declare=(
            'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
            'strategy = "STRATEGY.md"\ndeferred = "DEFERRED.md"\n'
        ),
    )
    pause = defer(config, "RK1", reason="it waits on a decision")
    assert pause.carried == Carried(anchor="§RK1", role="strategy")
    assert main(["-C", str(tmp_path), "defer", "RK1", "--reason", "it waits"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "carried  §RK1 kept in STRATEGY.md" in out and "IMPROVEMENTS" not in out
    # And the design is where the answer says, which is the claim a reader acts on (RK96).
    assert "### §RK1 A first design" in read(config, "STRATEGY.md")
    # Fields and not a sentence, so the caller reads the file rather than parsing "kept in".
    assert main(["-C", str(tmp_path), "defer", "RK4", "--reason", "it waits", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)["carried"]
    assert payload == {
        "anchor": "§RK4",
        "role": "strategy",
        "file": "STRATEGY.md",
        "absence": None,
    }


def test_a_pointer_resolving_to_nothing_is_said_and_not_dressed_as_a_location(tmp_path, capsys):
    # The absence spells itself, because "kept in IMPROVEMENTS.md" about a section that is
    # not there sends a reader looking for prose no file holds. The pause is right either
    # way — a dangling pointer is `lint`'s finding and never this door's refusal.
    config = project(tmp_path, {"IMPROVEMENTS.md": "# Improvements\n\n## Block A — The model\n"})
    pause = defer(config, "RK1", reason="it waits")
    assert pause.carried == Carried(
        anchor="§RK1", absence="not in IMPROVEMENTS.md, so nothing was carried"
    )
    assert main(["-C", str(tmp_path), "defer", "RK4", "--reason", "it waits"]) == EXIT_OK
    assert "carried  §RK4 — not in IMPROVEMENTS.md" in capsys.readouterr().out


def test_two_prose_files_declaring_one_anchor_are_reported_and_not_picked(tmp_path):
    # `ship` refuses to choose which of two a line meant (RK196), and a report that named
    # one of them would be this door answering the question `ref.ambiguous` asks the author.
    config = project(
        tmp_path,
        {"STRATEGY.md": RATIONALE},
        declare=DECLARE + 'strategy = "STRATEGY.md"\n',
    )
    pause = defer(config, "RK1", reason="it waits")
    assert pause.carried is not None and pause.carried.role is None
    assert "IMPROVEMENTS.md and STRATEGY.md" in pause.carried.absence


def test_the_return_restores_the_line_the_pause_wrapped(tmp_path):
    config = project(tmp_path)
    defer(config, "RK1", reason="it waits on a decision").save()
    resumption = resume(Config.discover(tmp_path), "RK1")
    resumption.save()
    # The author's own sentence, unwrapped: what came back is the line that left, and the
    # reason is reported once rather than left in a design it was never part of.
    assert resumption.placed.raw == (
        f"- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1"
    )
    assert resumption.was == "it waits on a decision"
    assert "RK1" not in config.document("deferred").by_id()


def test_the_id_is_the_same_one_and_never_a_reuse(tmp_path):
    # The whole difference from a retirement: retired-never-reused is not crossed, because
    # a deferred id was never retired — the same work comes back under its own number.
    config = project(tmp_path)
    defer(config, "RK1", reason="it waits").save()
    resume(Config.discover(tmp_path), "RK1").save()
    (entry,) = [e for e in config.document("roadmap").entries if e.task.id == "RK1"]
    assert entry.task.ref == "RK1"


def test_the_marker_the_store_could_not_keep_is_the_authors_to_state(tmp_path):
    config = project(tmp_path, {"ROADMAP.md": ROADMAP.replace(DESIGNED, "⏳", 1)})
    defer(config, "RK1", reason="it waits").save()
    resumption = resume(Config.discover(tmp_path), "RK1", marker="⏳")
    resumption.save()
    assert resumption.placed.task.status == "⏳"


def test_the_dependents_are_re_derived_on_the_way_back(tmp_path):
    # RK4 caches ⏸ for RK2 while it is paused; the moment RK2 is open again the annotation
    # is false, and nothing else would ever revisit it (RK8).
    config = project(tmp_path)
    resumption = resume(config, "RK2")
    resumption.save()
    assert resumption.refreshed == ("RK4",)
    (entry,) = [e for e in config.document("roadmap").entries if e.task.id == "RK4"]
    assert entry.task.deps == (Dep("RK2", marker=DESIGNED),)


def test_a_reason_that_would_not_survive_the_return_is_refused(tmp_path):
    # Invisible until the return trip: the unwrap stops at the first `): `, so the design
    # sentence would come back with the tail of the reason glued to its front.
    config = project(tmp_path)
    before = files(config)
    with pytest.raises(UnrecoverableReason):
        defer(config, "RK1", reason="waiting (on RK9): which never shipped")
    assert files(config) == before


def test_a_pause_with_nowhere_to_go_is_refused_and_not_scaffolded(tmp_path):
    # A store a `defer` invented on its way past would be a format decided by a verb.
    declare = DECLARE.replace('deferred = "DEFERRED.md"\n', "")
    config = project(tmp_path, declare=declare)
    with pytest.raises(NoStore, match="no deferred store is declared"):
        defer(config, "RK1", reason="it waits")


def test_a_line_the_ledger_already_recorded_has_neither_door(tmp_path):
    shipped = LEDGER + (
        f"\n- {SHIPPED} **RK1** **A first symptom** — Because of a reason.\n"
    )
    config = project(tmp_path, {"CHANGELOG.md": shipped})
    before = files(config)
    with pytest.raises(AlreadyRecorded):
        defer(config, "RK1", reason="it waits")
    assert files(config) == before


def test_pausing_what_is_not_open_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotOpen):
        defer(config, "RK9", reason="it waits")


def test_pausing_what_the_store_already_holds_is_refused(tmp_path):
    # RK2 is in the store and not in the roadmap, so this is NotOpen — the case the store's
    # own refusal answers is a hand-edit that left the id in both files.
    both = ROADMAP + (
        f"- {DESIGNED} **RK2** (deps: RK1) **A paused symptom** — Because it waits. → §RK2\n"
    )
    config = project(tmp_path, {"ROADMAP.md": both})
    with pytest.raises(SetAside, match="already set aside"):
        defer(config, "RK2", reason="it waits")


def test_resuming_what_never_paused_names_where_it_is(tmp_path):
    # "Not in the store" is the same sentence for an open task, a shipped one and a typo,
    # and only the last is a mistake about the id.
    config = project(tmp_path)
    with pytest.raises(NotSetAside, match="it is open in the roadmap"):
        resume(config, "RK1")


def test_the_sentence_it_names_it_with_is_the_one_the_section_refusals_use(tmp_path):
    # RK240: this refusal and `anchor.unknown` composed the same clause in two modules, and
    # a resolution copied rather than called is what goes stale when the other is corrected.
    config = project(tmp_path)
    with pytest.raises(NotSetAside) as raised:
        resume(config, "RK1")
    assert Whereabouts.of(config, "RK1").sentence in str(raised.value)


def test_the_gate_passes_over_both_files_after_a_pause(tmp_path):
    config = project(tmp_path)
    defer(config, "RK1", reason="it waits on a decision").save()
    # Clean on both sides now (RK92): RK4's wait on paused RK2 is a state the resolver has
    # a word for, and RK2's own wait on the freshly paused RK1 is the same word again.
    assert [f.code for f in lint(Config.discover(tmp_path)).findings] == []


def test_a_pause_annotates_the_lines_waiting_on_it_in_the_same_write(tmp_path):
    # The dependents `defer` already reported (RK96) get the marker in the transaction that
    # paused the target, for RK8's reason: an annotation derived by one door and not another
    # is a cache the gate refuses on the next run.
    waiting = ROADMAP + (
        f"- {DESIGNED} **RK7** (deps: RK1 {DESIGNED}) **A seventh symptom** — Because of a "
        f"third. → §RK7\n"
    )
    design = RATIONALE + "\n### §RK7 A seventh design\n\nThe reasoning it waits for.\n"
    config = project(tmp_path, {"ROADMAP.md": waiting, "IMPROVEMENTS.md": design})
    paused = defer(config, "RK1", reason="it waits on a decision")
    assert paused.dependents == ("RK7",)
    paused.save()
    returned = Config.discover(tmp_path).document("roadmap").by_id()
    assert returned["RK7"].task.deps == (Dep("RK1", marker=DEFERRED),)
    assert lint(Config.discover(tmp_path)).findings == ()


def test_a_resume_takes_the_annotation_back_off(tmp_path):
    config = project(tmp_path)
    resume(config, "RK2").save()
    returned = Config.discover(tmp_path).document("roadmap").by_id()
    # RK4 waited on RK2 ⏸ and now waits on an open line, so the cached marker follows.
    assert returned["RK4"].task.deps == (Dep("RK2", marker=DESIGNED),)


def test_defer_reports_every_edit_and_resume_reports_the_reason(tmp_path, capsys):
    tmp = str(tmp_path)
    project(tmp_path)
    assert main(["-C", tmp, "defer", "RK1", "--reason", "it waits on a decision"]) == EXIT_OK
    out = capsys.readouterr().out
    assert f"RK1 {DEFERRED} DEFERRED.md:" in out
    assert "carried  §RK1 kept in IMPROVEMENTS.md" in out
    assert main(["-C", tmp, "resume", "RK1"]) == EXIT_OK
    assert "was      set aside: it waits on a decision" in capsys.readouterr().out


def test_a_refused_pause_exits_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    before = files(config)
    assert main(["-C", str(tmp_path), "defer", "RK9", "--reason", "it waits"]) == EXIT_USAGE
    assert "RK9" in capsys.readouterr().err
    assert files(config) == before


# -- the contradiction the store and the roadmap can both hold (RK1081) --------


def paused_project(tmp_path: Path) -> Config:
    """A project whose roadmap and store both carry RK1 — the state RK1079 measured."""
    return project(
        tmp_path,
        {
            "DEFERRED.md": DEFERRED_STORE
            + f"- {DEFERRED} **RK1** (deps: —) **A first symptom** "
            f"— Because of a reason. → §RK1\n"
        },
    )


def test_a_resume_reconciles_an_id_both_files_carry(tmp_path):
    """Found by RK1079's sweep and closed here. `defer` refused because the store held it,
    `resume` refused because the roadmap did, and `ship` and `retire` both **succeeded** —
    recording the work as gone while the store still said it was paused, with the gate
    calling that tree clean.

    The roadmap already says what a resume would write, so the store's copy is the stale
    half: this removes it and places nothing, which is the mirror of RK1075 one file over.
    """
    config = paused_project(tmp_path)
    roadmap = read(config, "ROADMAP.md")
    returned = resume(config, "RK1")
    returned.save()

    assert returned.reconciled
    # No line placed: the roadmap is byte for byte what it was.
    assert read(Config.discover(config.root), "ROADMAP.md") == roadmap
    assert "**RK1**" not in read(Config.discover(config.root), "DEFERRED.md")


def test_a_departure_is_refused_while_the_store_still_carries_it(tmp_path):
    # Refused rather than made to remove the store entry, which is `ship`'s own choice about
    # a second ledger entry: a departure writes the files its transaction is about, and
    # reconciling a contradiction is a decision with its own verb — named in the refusal.
    from roadkeep.shipping import AlsoPaused, ship

    config = paused_project(tmp_path)
    with pytest.raises(AlsoPaused) as refused:
        ship(config, "RK1", why="It landed.")
    assert "resume RK1" in str(refused.value)
    assert "still says it is paused" in str(refused.value)


def test_the_two_acts_resume_answers_are_said_apart(tmp_path, capsys):
    # RK1083: the reconciling call places no line, and `Resumption.roadmap` wraps the entry
    # it left alone — so the output said "returned" over a write nobody made. `ship` answers
    # the same shape the same way (`RK1 closed` against `RK1 →`): one verb, two sentences.
    from roadkeep.cli import EXIT_OK, main

    root = paused_project(tmp_path).root
    assert main(["-C", str(root), "resume", "RK1"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "RK1 reconciled" in said and "roadmap  untouched" in said

    # And the ordinary return keeps its own sentence, which is what makes the pair legible.
    assert main(["-C", str(root), "resume", "RK2"]) == EXIT_OK
    assert "under Block A" in capsys.readouterr().out


def test_a_marker_is_refused_where_the_call_places_no_line(tmp_path):
    # `--marker` names the marker a returned line comes back at, and here there is no line
    # to mark: a flag accepted where it can take no effect is one the caller believes took
    # one, which is the rule `NoCompletion` and `NoSpan` already hold.
    from roadkeep.deferring import NoPlacement

    config = paused_project(tmp_path)
    with pytest.raises(NoPlacement) as refused:
        resume(config, "RK1", marker=DESIGNED)
    assert "status RK1" in str(refused.value)
    # The ordinary path still takes it, or the refusal would be about the flag rather than
    # about the act.
    assert resume(config, "RK2", marker=DESIGNED).marker == DESIGNED


def test_the_result_carries_no_line_it_did_not_place(tmp_path):
    """RK1086. `Resumption.roadmap` was an `Insertion` — a line and the file that now holds
    it — which is right for the act this verb was built for and wrong for the one RK1081
    added: a reconciling call places nothing and had to point the field at the entry it left
    alone. RK1084 then met the act with no entry *anywhere* to point at, and the shape did
    not refuse it — it parsed, and the printer read `.entry.task.block` two lines later.

    Two fields now, and they answer two questions: the document this write leaves, and the
    line it put there or `None`.
    """
    config = paused_project(tmp_path)
    reconciled = resume(config, "RK1")
    assert reconciled.reconciled and reconciled.placed is None
    reconciled.save()

    returned = resume(Config.discover(config.root), "RK2")
    assert not returned.reconciled and returned.placed is not None
    assert returned.placed.task.id == "RK2"


def test_a_reconciling_call_reports_no_address_for_a_line_it_never_wrote(tmp_path, capsys):
    # The `--json` half: a `line` under `roadmap` would be an address for a write nobody
    # made, so the object is null and a consumer can tell the two acts apart without prose.
    from roadkeep.cli import EXIT_OK, main

    root = paused_project(tmp_path).root
    assert main(["-C", str(root), "resume", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["reconciled"] is True and payload["roadmap"] is None
    assert payload["deferred"]["removed"] > 0


# -- the pause a budget forbade (RK1115) --------------------------------------

#: A `why` written to exactly the limit below, which is what `brief` invites: it prints the
#: headroom left on the field as room to fill, and a line that took the invitation could then
#: never be paused — the 14-character derived prefix overflowed before a reason was written.
AT_BUDGET = "Because a reason fills exactly the limit this project declares for a why, leaving no room."
NARROW = DECLARE + "[limits]\nwhy = 90\n"


def written(tmp_path: Path, why: str = AT_BUDGET) -> Config:
    return project(
        tmp_path,
        files={
            "ROADMAP.md": (
                "# Roadmap\n\n## Block A — The model\n\n"
                f"- {DESIGNED} **RK1** (deps: —) **A first symptom** — {why} → §RK1\n"
            ),
            "DEFERRED.md": "# Set aside\n\n## Block A — The model\n",
            "IMPROVEMENTS.md": (
                "# Improvements\n\n## Block A — The model\n\n### §RK1 A first design\n\n"
                "The reasoning the line has no room for.\n"
            ),
        },
        declare=NARROW,
    )


def test_a_line_written_to_its_why_budget_can_still_be_paused(tmp_path):
    # pportal's PP55: 165 characters against a limit of 169, so `set aside (): ` alone was 10
    # over before a reason existed. A reason of zero characters still failed, which left the
    # two terminal doors as the only ones — for a line that was neither shipped nor abandoned.
    config = written(tmp_path)
    assert len(AT_BUDGET) == 90  # the limit exactly, so the prefix is the whole overflow
    paused = defer(config, "RK1", reason="no instrument here")
    paused.store.document.save()
    paused.roadmap.save()
    stored = (tmp_path / "DEFERRED.md").read_text(encoding="utf-8")
    assert f"set aside (no instrument here): {AT_BUDGET}" in stored


def test_the_stored_line_the_pause_wrote_passes_the_gate(tmp_path):
    # The half that makes it a fix and not a hole: the door and the gate read one rule, so a
    # file `defer` wrote is a file `lint` calls clean.
    config = written(tmp_path)
    paused = defer(config, "RK1", reason="no instrument here")
    paused.store.document.save()
    paused.roadmap.save()
    assert [f.code for f in lint(Config.discover(tmp_path)).findings] == []


def test_the_author_s_own_sentence_is_still_charged(tmp_path):
    # Only the derived half rides free. A `why` one character over its limit is still over it,
    # in the store as in the roadmap — the relaxation is about who wrote the characters.
    config = written(tmp_path, why=AT_BUDGET.replace("no room.", "no room at all."))
    with pytest.raises(Exception) as raised:
        defer(config, "RK1", reason="no instrument here")
    assert "why" in str(raised.value)


def test_the_reason_may_not_smuggle_in_what_an_author_is_refused_for(tmp_path):
    # The limit is the one thing `charged` relaxes: a control character in the wrapper is as
    # unrenderable as one in the sentence, so every other check still reads the whole field.
    config = written(tmp_path)
    with pytest.raises(Exception) as raised:
        defer(config, "RK1", reason="no\tinstrument")
    assert "char.tab" in str(raised.value) or "tab" in str(raised.value)


def test_a_roadmap_line_gets_no_free_prefix_for_writing_the_same_words(tmp_path):
    # Guarded on the store's own configuration and never on the text: a roadmap line whose
    # author happens to open with those words is prose, and prose is charged.
    schema = Schema(why_max=90)
    task = Task(
        status=DESIGNED,
        id="RK1",
        block="A",
        symptom="A symptom",
        why=f"set aside (a reason): {AT_BUDGET}",
        ref="RK1",
    )
    assert "why.too-long" in {v.code for v in schema.validate(task)}
    assert "why.too-long" not in {
        v.code for v in schema.as_deferred().validate(replace(task, status=DEFERRED))
    }


# -- what to stage, from the two doors that are not terminal (RK1130) -----------


def test_a_pause_says_what_to_stage(tmp_path, capsys):
    # Two governed files move in one transaction here, and the projection with them: a commit
    # that took the roadmap alone would leave the store's new line uncommitted.
    project(tmp_path)
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "defer", "RK1", "--reason", "waiting on a decision"]) == EXIT_OK
    staging = next(
        line for line in capsys.readouterr().out.splitlines() if "stage    " in line
    )
    assert "ROADMAP.md" in staging and "DEFERRED.md" in staging


def test_a_resume_says_the_same(tmp_path, capsys):
    project(tmp_path)
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "resume", "RK2"]) == EXIT_OK
    staging = next(
        line for line in capsys.readouterr().out.splitlines() if "stage    " in line
    )
    assert "ROADMAP.md" in staging and "DEFERRED.md" in staging


def test_the_pause_payload_carries_the_list(tmp_path, capsys):
    project(tmp_path)
    argv = ["-C", str(tmp_path), "defer", "RK1", "--reason", "waiting", "--json"]
    capsys.readouterr()
    assert main(argv) == EXIT_OK
    wrote = json.loads(capsys.readouterr().out)["wrote"]
    assert "ROADMAP.md" in wrote and "DEFERRED.md" in wrote


# -- the absence with a door, told apart from the one with none (RK1213) ------


def test_a_paused_id_is_not_the_absence_a_typo_is(tmp_path):
    """RK1213. `Where` had three members and the store was a fourth, so `amend`, `restate`
    and `status` refused a paused line word for word as they refuse an id nobody wrote —
    while `Whereabouts` said *no file mentions it* about a line the store carries verbatim.

    `Stage.PAUSED` made this argument one level up (RK92, RK429): a block whose every line
    was deferred is not finished and not empty, and reading it as either loses the one fact
    a `resume` would change. An id is the same claim with a door of its own.
    """
    config = project(tmp_path)
    defer(config, "RK1", reason="it waits on a decision").save()
    config = Config.discover(tmp_path)

    found = Whereabouts.of(config, "RK1")
    assert found.paused and not found.recorded
    assert found.sentence == "the deferred store holds it — `resume` brings it back"
    # And the one it must not be confused with, unchanged.
    assert Whereabouts.of(config, "RK404").sentence == "no file mentions it"


def test_the_doors_that_refuse_a_paused_line_name_the_one_that_takes_it(tmp_path):
    # The three writes that reach a line by id. Each answered "nothing there carries that
    # id", which is true of the roadmap and false about the project.
    config = project(tmp_path)
    defer(config, "RK1", reason="it waits on a decision").save()
    root = str(tmp_path)
    for argv in (
        ["amend", "RK1", "--why", "A corrected reason."],
        ["restate", "RK1", "--symptom", "A premise that was false"],
        ["status", "RK1", DESIGNED],
    ):
        assert main(["-C", root, *argv]) == EXIT_USAGE, argv


def test_a_shipped_id_keeps_the_reading_it_had(tmp_path):
    # The state that was already told apart: what changed is the two that were not.
    from roadkeep.shipping import ship

    config = project(tmp_path)
    ship(config, "RK1", why="It works now.").save()
    config = Config.discover(tmp_path)
    found = Whereabouts.of(config, "RK1")
    assert found.recorded and not found.paused
    assert main(["-C", str(tmp_path), "amend", "RK1", "--why", "A reason."]) == EXIT_USAGE


# -- the one pair this tool writes on purpose, at the two doors that refused it (RK1215) --


def test_a_partially_shipped_line_can_still_be_paused(tmp_path):
    """RK1215. `ship --part` records a qualified half and leaves the line open at ⏳, which
    is the one shape this tool creates on purpose — and `defer` answered with the *ledger's*
    refusal, about a second entry it would never write. `_refuse_recorded` asked whether the
    ledger holds the id and never whether that entry is a half, which is the pair
    `_refuse_sibling_status` and the gate both skip on `Task.in_halves` (RK1080, RK1114).

    The state it locked out is the case the store exists for: a half that landed and a
    remainder waiting on a decision. The only exit left was `retire`, which deletes the
    design and records a departure that did not happen.
    """
    from roadkeep.shipping import ship

    config = project(tmp_path)
    ship(config, "RK1", why="The local half works now.", part="local half").save()
    config = Config.discover(tmp_path)
    assert config.document("roadmap").by_id()["RK1"].task.status == PARTIAL

    paused = defer(config, "RK1", reason="the rest waits on a decision")
    paused.save()
    config = Config.discover(tmp_path)
    assert config.document("deferred").by_id()["RK1"] is not None
    # And the gate agrees, which is the half opening the door alone would have broken.
    assert [f.code for f in lint(config).findings] == []


def test_the_pause_a_partial_allows_comes_back(tmp_path):
    # `resume` reads the same function, so it had the same refusal about an id the store
    # already held — and the qualifier the roadmap lost is `--marker`'s to restore.
    from roadkeep.shipping import ship

    config = project(tmp_path)
    ship(config, "RK1", why="The local half works now.", part="local half").save()
    config = Config.discover(tmp_path)
    defer(config, "RK1", reason="the rest waits on a decision").save()
    config = Config.discover(tmp_path)

    resume(config, "RK1", marker=PARTIAL).save()
    config = Config.discover(tmp_path)
    assert config.document("roadmap").by_id()["RK1"].task.status == PARTIAL
    assert "RK1" not in config.document("deferred").by_id()
    assert [f.code for f in lint(config).findings] == []


def test_a_whole_shipment_is_still_refused_at_both_doors(tmp_path):
    # The rule the exception is carved out of, unchanged: an id the ledger holds *whole* has
    # neither door, and a pause beside it is the contradiction `id.paused-and-gone` reports.
    from roadkeep.shipping import ship

    config = project(tmp_path)
    ship(config, "RK1", why="It works now.").save()
    config = Config.discover(tmp_path)
    # The line is gone from the roadmap, so `defer` refuses one step earlier — and says so
    # in the words RK1213 gave that reading rather than the ledger's.
    assert main(["-C", str(tmp_path), "defer", "RK1", "--reason", "set aside"]) == EXIT_USAGE
    assert main(["-C", str(tmp_path), "resume", "RK1"]) == EXIT_USAGE


def test_the_gate_reads_the_qualifier_off_the_ledger_and_not_off_the_second_file(tmp_path):
    """The gate half (RK1215). `_carried` walks three pairs and read `in_halves` off `held`,
    the pair's *second* file — but the changelog is second in two of them and first in the
    third, so `id.paused-and-gone` looked for the qualifier on the store's line, where it
    never appears. A tolerance applied to a position rather than to the file carrying the
    fact works by coincidence."""
    store = DEFERRED_STORE + (
        f"- {DEFERRED} **RK7** (deps: —) **A half-shipped symptom** — "
        f"set aside (the rest waits): Because of a reason. → §RK7\n"
    )
    whole = LEDGER + f"- {SHIPPED} **RK7** **A half-shipped symptom** — It works now.\n"
    halved = LEDGER + (
        f"- {SHIPPED} **RK7 (local half)** **A half-shipped symptom** — The half works.\n"
    )
    # Whole: the contradiction the rule is for, still reported.
    config = project(tmp_path, {"DEFERRED.md": store, "CHANGELOG.md": whole})
    assert "id.paused-and-gone" in [f.code for f in lint(config).findings]
    # A half: the two files agreeing that work arrived in halves, and the store holds the rest.
    config = project(tmp_path, {"DEFERRED.md": store, "CHANGELOG.md": halved})
    assert "id.paused-and-gone" not in [f.code for f in lint(config).findings]
