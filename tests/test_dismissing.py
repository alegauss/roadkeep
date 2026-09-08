"""What was traced and deliberately not filed, as a record (RK1618).

`delivered` says what a block shipped and `reversals` what it undid. Neither answers the third
question a proposal meets — *was this looked at already and left?* — so the reading that ruled
a finding out is paid again by whoever proposes it next, and the tests here are about the
seventh governed file that stops that.

Four claims, and the second is the one the whole role exists for:

* the store reads the **same grammar**, in the configuration `as_dismissed` returns — one
  marker, and the two slots a finding nobody filed has nothing to put in dropped;
* the **premise is required**, refused at the door before a reason is composed and reported by
  the gate on an entry that arrived any other way — *checked, fine* is unfalsifiable, and an
  entry with no falsifiable claim is the note this store replaces;
* 🚫 is **legal there and nowhere else**, the rule ✅, 🗑 and ⏸ already obey, in both
  directions;
* an id in the store is **taken**, so nothing mints it twice — and `reopen` is what takes it
  back out, which is what separates a record from a deletion.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.backlog import Where, Whereabouts
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError
from roadkeep.dismissing import (
    AlreadyDismissed,
    NoStore,
    NotDismissed,
    UnrecoverablePremise,
    dismiss,
    reopen,
)
from roadkeep.ids import carried
from roadkeep.kernel.document import Document
from roadkeep.linting import lint
from roadkeep.kernel.schema import (
    DESIGNED,
    DISMISSED,
    DISMISSED_OPEN,
    Schema,
    SchemaError,
    Task,
    authored_why,
    dismissal_premise,
)

ROADMAP = f"""# Roadmap

## Block A — The model

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
"""

LEDGER = """# Shipped

## Block A — The model
"""

PROSE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.
"""

STORE = f"""# Ruled out

## Block A — The model

- {DISMISSED} **RK7** **A finding traced and left alone** — \
holds while (the caller validates first): the path is unreachable.
"""

CONFIG = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    'improvements = "IMPROVEMENTS.md"\ndismissed = "DISMISSED.md"\n'
)


def project(root: Path, *, store: str | None = STORE, config: str = CONFIG) -> Config:
    """A governed project, with the dismissed store unless a test asks for none."""
    written = {
        "roadkeep.toml": config,
        "ROADMAP.md": ROADMAP,
        "CHANGELOG.md": LEDGER,
        "IMPROVEMENTS.md": PROSE,
    }
    if store is not None:
        written["DISMISSED.md"] = store
    for name, body in written.items():
        with (root / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(root)


# -- the grammar, before any command writes to it -----------------------------


def test_the_store_is_the_same_format_in_its_own_configuration():
    """One schema in a seventh configuration, never a second grammar: the file a line sits in
    is what states what was decided about it, and two grammars drift."""
    schema = Schema().as_dismissed()
    assert schema.is_dismissed
    assert schema.markers == (DISMISSED,)
    # The two slots a finding nobody filed has nothing to put in: no design section for a
    # pointer to reach, and nothing waiting on a decision to rule something out.
    assert not schema.deps_field
    assert not schema.ref_required


def test_the_marker_is_legal_in_the_store_and_nowhere_else():
    # The rule ✅, 🗑 and ⏸ already obey, in both directions.
    assert DISMISSED not in Schema().markers
    with pytest.raises(ValueError, match="dismissed marker"):
        Schema(markers=(DESIGNED, DISMISSED))
    entry = Task(id="RK7", status=DISMISSED, block="A", symptom="A symptom", why="Because.")
    assert any(one.code == "status.unknown" for one in Schema().validate(entry))


def test_a_project_may_spell_the_marker_its_own_way_and_not_two_at_once(tmp_path):
    """L6, and the cross-key check that goes with it: a glyph the package chose would be this
    tool declaring a state in somebody else's file, and two states reading alike is a store
    that cannot say which of them a line is in."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[markers]\ndismissed = "🔕"\n', encoding="utf-8"
    )
    assert Config.discover(tmp_path).schema.dismissed_marker == "🔕"
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[markers]\ndismissed = "🗑"\n', encoding="utf-8"
    )
    with pytest.raises(ConfigError, match="markers.dismissed must differ"):
        Config.discover(tmp_path)


# -- the premise, which is what the role exists for ---------------------------


def test_the_premise_is_wrapped_around_the_reason_and_read_back_off_it(tmp_path):
    config = project(tmp_path)
    filed = dismiss(
        config,
        block="A",
        symptom="A second finding traced and left",
        reason="The other path is unreachable.",
        premise="the guard runs first",
    )
    task = filed.store.entry.task
    assert task.why.startswith(DISMISSED_OPEN)
    assert dismissal_premise(task.why) == "the guard runs first"
    # The author's sentence comes back exactly as written, which is what makes the reopen a
    # restoration rather than a rewrite (L4).
    assert authored_why(task.why) == "The other path is unreachable."


def test_a_blank_premise_is_refused_before_anything_is_written(tmp_path):
    """The one field this format requires and composes the frame of. Blank counts as absent:
    `holds while (): …` reads as a premise to every eye and falsifies nothing."""
    config = project(tmp_path)
    before = (tmp_path / "DISMISSED.md").read_text(encoding="utf-8")
    with pytest.raises(SchemaError) as refused:
        dismiss(
            config,
            block="A",
            symptom="A second finding traced and left",
            reason="The other path is unreachable.",
            premise="   ",
        )
    assert any(one.code == "premise.missing" for one in refused.value.violations)
    assert (tmp_path / "DISMISSED.md").read_text(encoding="utf-8") == before


def test_the_gate_reports_an_entry_that_reached_the_file_any_other_way(tmp_path):
    """L1's backstop, and the reason the rule is in the schema and not only in the verb: an
    entry hand-edited past `dismiss` is one nothing can ever reopen, because nothing says which
    commit makes the finding real again."""
    config = project(
        tmp_path,
        store=(
            f"# Ruled out\n\n## Block A — The model\n\n"
            f"- {DISMISSED} **RK7** **A finding traced and left alone** — "
            f"The path is unreachable.\n"
        ),
    )
    found = [one for one in lint(config).findings if one.code == "premise.missing"]
    assert [one.id for one in found] == ["RK7"]


def test_a_premise_that_closes_the_prefix_is_refused_rather_than_stored(tmp_path):
    # The damage is invisible until the reopen: the unwrap stops at the first `): `, so the
    # author's own reason would come back with the tail of the premise glued to its front.
    config = project(tmp_path)
    with pytest.raises(UnrecoverablePremise):
        dismiss(
            config,
            block="A",
            symptom="A second finding traced and left",
            reason="The other path is unreachable.",
            premise="a guard (of a kind): it runs first",
        )


def test_the_reason_is_measured_against_the_line_and_not_the_field(tmp_path):
    """RK1479's rule at this door: the wrapper widens the rendered line, so a reason that fits
    its own limit and pushes the line past its own is refused before it lands."""
    config = project(
        tmp_path,
        config=CONFIG + "[limits]\nline = 120\nsymptom = 40\nwhy = 200\n",
    )
    reason = ("a word that is plainly long " * 3).strip() + "."
    # Inside the field's own limit, and past what the line leaves it.
    assert len(reason) < 200
    with pytest.raises(SchemaError) as refused:
        dismiss(
            config,
            block="A",
            symptom="A second finding traced",
            reason=reason,
            premise="the guard runs first",
        )
    assert [one.code for one in refused.value.violations] == ["why.too-long"]
    assert "the line is full" in refused.value.violations[0].message


def test_a_premise_the_author_is_charged_for_nowhere_still_bounds_the_line(tmp_path):
    """The other half, and the one only this door has: the premise is derived, so `[limits] why`
    is not what it is charged to — and a wrapper nothing measured would land as a line the gate
    then refuses, which is L1 inverted on the one write here that composes prose."""
    config = project(
        tmp_path,
        config=CONFIG + "[limits]\nline = 140\nsymptom = 40\nwhy = 200\n",
    )
    with pytest.raises(SchemaError) as refused:
        dismiss(
            config,
            block="A",
            symptom="A second finding traced",
            reason="It is unreachable.",
            premise="a guard that is stated at very considerable and quite unnecessary length",
        )
    assert [one.code for one in refused.value.violations] == ["line.too-long"]


# -- the id, which is what makes a reopen possible ----------------------------


def test_an_id_in_the_store_is_taken_and_nothing_mints_it_twice(tmp_path):
    config = project(tmp_path)
    assert "RK7" in carried(config)
    assert main(
        [
            "-C", str(tmp_path), "add", "--block", "A", "--symptom", "A second symptom",
            "--why", "Because of another.", "--id", "RK7",
        ]
    ) == EXIT_USAGE


def test_the_id_is_derived_past_everything_the_store_holds(tmp_path):
    config = project(tmp_path)
    filed = dismiss(
        config,
        block="A",
        symptom="A second finding traced and left",
        reason="The other path is unreachable.",
        premise="the guard runs first",
    )
    assert filed.task_id == "RK8"


def test_a_ruled_out_id_is_a_state_and_not_an_absence(tmp_path):
    """`Where.DISMISSED` for `PAUSED`'s reason: reading it as *no file mentions it* loses the
    fact a `reopen` would change, and sends a reader looking for work never filed."""
    config = project(tmp_path)
    found = Whereabouts.of(config, "RK7")
    assert found.where is Where.DISMISSED
    assert found.dismissed
    assert "reopen" in found.sentence


# -- the way back -------------------------------------------------------------


def test_reopen_files_the_entry_as_work_and_leaves_the_premise_behind(tmp_path):
    config = project(tmp_path)
    filed = reopen(config, "RK7")
    filed.save()
    assert filed.was == "the caller validates first"
    line = Config.discover(tmp_path).document("roadmap").by_id()["RK7"]
    assert line.task.why == "the path is unreachable."
    assert line.task.status == config.schema.markers[0]
    # The store let it go in the same transaction, which is what makes this a move.
    assert "RK7" not in Config.discover(tmp_path).document("dismissed").by_id()


def test_reopen_reconciles_where_the_roadmap_already_carries_the_id(tmp_path):
    """RK1081's resolution one store over: two governed files disagreeing about one id, settled
    towards the one that already states the outcome, so the state a write stopping between its
    two saves leaves has a verb rather than only a finding."""
    config = project(tmp_path)
    reopen(config, "RK7").save()
    # The store's copy put back, which is what a crash between the two writes leaves.
    with (tmp_path / "DISMISSED.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write(STORE)
    config = Config.discover(tmp_path)
    assert any(one.code == "id.dismissed-and-open" for one in lint(config).findings)
    second = reopen(config, "RK7")
    second.save()
    assert second.reconciled
    assert second.placed is None
    # The contradiction is gone and the roadmap was not touched: what is left is the pointer
    # a reopened line owes, which is the state a fresh `add` with no `--section` leaves too.
    left = {one.code for one in lint(Config.discover(tmp_path)).findings}
    assert left == {"ref.unresolved"}


def test_a_marker_on_a_call_that_places_nothing_is_refused(tmp_path):
    # A flag accepted where it can take no effect is a flag the caller believes took one.
    config = project(tmp_path)
    reopen(config, "RK7").save()
    with (tmp_path / "DISMISSED.md").open("w", encoding="utf-8", newline="") as handle:
        handle.write(STORE)
    with pytest.raises(ValueError, match="places none"):
        reopen(Config.discover(tmp_path), "RK7", marker="🛠")


def test_reopen_names_where_an_id_it_does_not_hold_actually_is(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotDismissed, match="open in the roadmap"):
        reopen(config, "RK1")


# -- the store a project has not got ------------------------------------------


def test_both_doors_refuse_where_no_store_is_declared_and_name_the_one_that_opens_it(tmp_path):
    config = project(tmp_path, store=None, config=CONFIG.replace(
        'dismissed = "DISMISSED.md"\n', ""
    ))
    with pytest.raises(NoStore, match="declare dismissed"):
        dismiss(
            config,
            block="A",
            symptom="A finding traced and left alone",
            reason="The path is unreachable.",
            premise="the caller validates first",
        )
    with pytest.raises(NoStore, match="declare dismissed"):
        reopen(config, "RK7")


def test_a_second_entry_for_one_id_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(AlreadyDismissed, match="two premises"):
        dismiss(
            config,
            block="A",
            symptom="A finding traced and left alone",
            reason="The path is unreachable.",
            premise="the caller validates first",
            task_id="RK7",
        )


# -- both registers -----------------------------------------------------------


def test_the_answer_says_what_the_entry_holds_while_in_both_registers(tmp_path, capsys):
    project(tmp_path)
    assert main([
        "-C", str(tmp_path), "dismiss", "--block", "A",
        "--symptom", "A second finding traced and left",
        "--why", "The other path is unreachable.",
        "--premise", "the guard runs first", "--json",
    ]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["premise"] == "the guard runs first"
    assert payload["dismissed"]["limit"] == Config.discover(tmp_path).schema.line_max
    assert payload["id"] == "RK8"


def test_the_file_still_round_trips_after_both_writes(tmp_path):
    """L3, over the one file this task adds: every line the store holds renders back to the
    bytes it was read as, or the whole file is refused."""
    config = project(tmp_path)
    dismiss(
        config,
        block="A",
        symptom="A second finding traced and left",
        reason="The other path is unreachable.",
        premise="the guard runs first",
    ).save()
    document = Document.load(tmp_path / "DISMISSED.md", config.schema_for("dismissed"))
    assert document.render() == (tmp_path / "DISMISSED.md").read_text(encoding="utf-8")
    assert len(document.entries) == 2
