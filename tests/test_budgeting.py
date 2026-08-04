"""What a line has left for prose, asked before a word of it exists (RK190).

RK183 derived the number and RK184 spelled it, and both act only inside a refusal — after
a sentence has been composed. Everything the budget needs is known before that, so the
tests here are about the number arriving *early*: as an answer to a question, not as the
verdict on a draft.

Nothing here asserts a limit. The numbers are the schema's, so a test that spelled 320
would be the second statement of it this module exists not to be.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.budgeting import CHARS_PER_WORD, budget, budget_of, words
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.schema import DESIGNED

BACKLOG = f"""# Roadmap

## Block A — The model

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- {DESIGNED} **RK2** (deps: RK1) **A second symptom** — Because of another one. → §RK2
"""

LEDGER = """# Shipped

## Block A — The model
"""


def project(tmp_path: Path, roadmap: str = BACKLOG) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return Config.discover(tmp_path)


# -- the number before the sentence ------------------------------------------


def test_the_budget_is_answerable_with_no_prose_at_all(tmp_path):
    config = project(tmp_path)
    answer = budget(config, block="A")
    schema = config.schema
    # Not a constant: the structure is what the line costs before a word, and the prose is
    # what is left — both read off `prose_budget`, which is the only place that measures it.
    assert answer.prose == schema.prose_budget(answer.task)
    assert answer.structure == schema.line_max - answer.prose
    assert answer.line_max == schema.line_max
    assert not answer.open_line and answer.task.id == "RK3"


def test_deps_move_the_budget_and_the_answer_says_so(tmp_path):
    config = project(tmp_path)
    bare = budget(config, block="A")
    carried = budget(config, block="A", deps=["RK1", "RK2"])
    # The whole reason a static `maxLength` cannot state it: the group is part of the line.
    assert carried.prose < bare.prose
    assert carried.structure > bare.structure


def test_a_symptom_takes_its_room_from_the_why(tmp_path):
    config = project(tmp_path)
    empty = budget(config, block="A")
    written = budget(config, block="A", symptom="x" * config.schema.symptom_max)
    assert written.share("why").allowed < empty.share("why").allowed
    assert written.share("why").allowed == config.schema.why_budget(written.task)


def test_the_line_binding_rather_than_the_field_is_named(tmp_path):
    config = project(tmp_path)
    # An author writing to the two published numbers is refused by a third, measured on a
    # string they never write — so which of the two binds is the finding, not a footnote.
    written = budget(config, block="A", symptom="x" * config.schema.symptom_max)
    why = written.share("why")
    assert why.bound_by_line and why.allowed < why.limit
    assert not budget(config, block="A").share("why").bound_by_line


# -- the line already on the desk --------------------------------------------


def test_an_id_the_roadmap_holds_is_that_line_and_not_a_hypothetical(tmp_path):
    config = project(tmp_path)
    answer = budget(config, "RK2")
    assert answer.open_line and answer.task.id == "RK2"
    # Its own fields, off the file: the marker, the deps and the symptom the line carries.
    assert [dep.id for dep in answer.task.deps] == ["RK1"]
    assert answer.share("symptom").taken == len("A second symptom")
    assert answer.share("why").left == answer.share("why").allowed - len(answer.task.why)


def test_an_id_no_file_holds_is_the_line_that_id_would_have(tmp_path):
    # The third question, and not an error: a caller checking what a split (`RK9b`) would
    # leave is asking about an id that is deliberately not there yet.
    answer = budget(project(tmp_path), "RK9")
    assert not answer.open_line and answer.task.id == "RK9"


def test_budget_of_takes_a_task_the_caller_already_holds(tmp_path):
    config = project(tmp_path)
    task = config.document("roadmap").by_id()["RK2"].task
    assert budget_of(config, task, open_line=True) == budget(config, "RK2")


# -- the two doors -----------------------------------------------------------


def test_the_command_prints_each_field_and_which_limit_binds(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK2", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK2" and payload["open_line"] is True
    fields = {one["field"]: one for one in payload["fields"]}
    assert fields["why"]["limit"] == config.schema.why_max
    assert fields["why"]["allowed"] == config.schema.why_budget(
        config.document("roadmap").by_id()["RK2"].task
    )
    assert set(fields) == {"symptom", "why"}


def test_the_command_answers_with_no_id_at_all(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--block", "A", "--dep", "RK1"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "RK3" in printed and "for prose" not in printed
    assert "symptom" in printed and "why" in printed


def test_a_brief_carries_the_budget_of_the_line_it_hands_over(tmp_path, capsys):
    # The second shape (RK190): the call that starts a task anyway, so the number the next
    # `amend` is measured on is already on the desk rather than one refusal away.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK2", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["budget"]["id"] == "RK2"
    assert payload["budget"]["prose"] > 0


def test_a_shipped_task_has_no_line_to_budget(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "it works now."]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "brief", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    # The ledger is a different grammar and holds no line an `amend` would rewrite.
    assert payload["budget"] is None
    assert config.document("changelog").by_id()["RK1"] is not None


def test_an_unspellable_family_is_refused_rather_than_guessed(tmp_path, capsys):
    assert main(["-C", str(tmp_path), "budget", "--prefix", "ZZ"]) == EXIT_USAGE
    assert "ZZ" in capsys.readouterr().err


# -- the aim, beside the gate (RK185) ----------------------------------------


def test_the_conversion_is_the_corpus_and_not_a_comment():
    """`CHARS_PER_WORD` is a measurement, so it is re-measured rather than asserted.

    A model has no characters: publishing a ceiling only in them makes the first attempt a
    guess. The figure that turns one into an aim is a property of the prose these files are
    written in, so it is derived from the prose these files are written in — and a corpus
    that drifted past it should fail here rather than quietly make every aim optimistic.
    """
    config = Config.discover(Path(__file__).parents[1])
    ratios = sorted(
        len(text) / len(text.split())
        for role in ("roadmap", "changelog")
        for entry in config.document(role).entries
        for text in (entry.task.symptom or "", entry.task.why or "")
        if text
    )
    assert len(ratios) > 100, "too small a corpus to fix a constant from"
    p95 = ratios[int(len(ratios) * 0.95)]
    # Above the 95th percentile, so an aim that is hit lands inside the gate about nineteen
    # times in twenty; and not far above it, or the aim is tighter than the format allows.
    assert p95 <= CHARS_PER_WORD <= p95 + 0.75


def test_an_aim_that_is_hit_clears_the_gate_on_this_repositorys_own_lines():
    # The claim the constant makes, on the artefact the format is proven by: no line whose
    # word count is at or under its field's aim is over that field's character limit.
    config = Config.discover(Path(__file__).parents[1])
    schema = config.schema
    for role in ("roadmap", "changelog"):
        for entry in config.document(role).entries:
            for text, limit in (
                (entry.task.symptom or "", schema.symptom_max),
                (entry.task.why or "", schema.why_max),
            ):
                if text and len(text.split()) <= words(limit):
                    assert len(text) <= limit, text


def test_the_aim_is_derived_from_what_the_line_allows_not_from_the_ceiling(tmp_path):
    # Why this waited on RK183: an aim computed from the published `why` limit would send
    # the author at prose the line has no room for, which is the overrun it inherits.
    config = project(tmp_path)
    answer = budget(config, block="A", symptom="x" * config.schema.symptom_max)
    why = answer.share("why")
    assert why.bound_by_line
    assert why.aim == words(why.allowed) < words(why.limit)


def test_the_command_states_both_units(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "budget"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "aim" in printed and "words" in printed


def test_the_json_carries_the_aim_per_field(tmp_path):
    project(tmp_path)
    answer = budget(Config.discover(tmp_path))
    for share in answer.shares:
        assert share.aim == words(share.allowed)


def test_a_zero_budget_aims_at_nothing_rather_than_at_a_negative():
    assert words(0) == 0
    assert words(1) == 0


# -- the remainder, in the unit the aim is stated in (RK245) -----------------


def test_the_remainder_has_a_word_figure_of_its_own(tmp_path):
    # The one number RK185 skipped, and the one an `amend` is bounded by: `aim` describes
    # the whole field, so beside a written one it answers a question nobody asked.
    config = project(tmp_path)
    why = budget(config, "RK1").share("why")
    assert why.taken
    assert why.room == words(why.left) < why.aim


def test_the_remainder_floors_because_it_is_an_allowance(tmp_path):
    # The opposite rounding from `words_over` (RK201) and the same argument from the other
    # side: an allowance that rounds up sends the author back to the refusal.
    config = project(tmp_path)
    task = config.document("roadmap").by_id()["RK1"].task
    for share in budget_of(config, task, open_line=True).shares:
        assert share.room <= share.left / CHARS_PER_WORD


def test_a_field_with_nothing_written_states_the_whole_aim(tmp_path):
    # Nothing to be misread here: what is left *is* what the field allows, so the two
    # figures agree and the pre-`add` read is unchanged.
    config = project(tmp_path)
    share = budget(config, block="A").share("why")
    assert not share.taken and share.room == share.aim


def test_the_command_aims_at_what_is_left_and_never_at_the_whole_field(tmp_path, capsys):
    # The misreading in the symptom: `18 left  aim 30 words` invites the reading that thirty
    # words are available when about three are, so the two are never printed together.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK1"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "more words" in printed
    assert "aim 30 words" not in printed


def test_the_json_carries_the_remainder_beside_the_characters(tmp_path, capsys):
    # Beside `left` and not instead of it: the characters are still what refuses.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    field = next(one for one in payload["fields"] if one["field"] == "why")
    assert field["room"] == words(field["left"]) and field["left"] < field["allowed"]


def test_the_brief_states_the_same_figure_as_the_budget(tmp_path, capsys):
    # `brief` prints the `why`'s share of the line it hands over, so whatever `Share` grows
    # is what a task started through it is told — and the two cannot state it differently.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    briefed = capsys.readouterr().out
    assert main(["-C", str(tmp_path), "budget", "RK1"]) == EXIT_OK
    room = budget(Config.discover(tmp_path), "RK1").share("why").room
    assert f"aim {room} more words" in briefed
    assert f"aim {room} more words" in capsys.readouterr().out


# -- the pointer the budget could not be told about (RK265) --------------------

#: Long enough that the *line* binds the `why` rather than the `why`'s own limit, which is
#: the only condition under which an eight-character pointer can be the whole difference.
WIDE = "A symptom written to the length the corpus writes them, so the line is what binds"


OUTLINED = f"""# Roadmap

## Block A — The model

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §IV.2
- {DESIGNED} **RK2** (deps: —) **{WIDE}** — Because of another one. → §XXXVII.11
"""


def outlined(tmp_path: Path) -> Config:
    """A project where the anchor is the caller's to name, which is where the defect is."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\nref_scheme = "outline"\n'
        '[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(OUTLINED, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return Config.discover(tmp_path)


def test_the_anchor_the_caller_names_is_counted_as_the_structure_it_is(tmp_path):
    # The measured defect: `budget` answered a why 182 characters and the `add` that followed
    # — identical but for `--ref` — refused at 174, the eight being ` → §XX.2`.
    config = outlined(tmp_path)
    answer = budget(config, block="A", symptom=WIDE, ref="XX.2")
    assert answer.task.ref == "XX.2" and not answer.ref_assumed
    # Not a constant: what the pointer costs is the difference between the two structures,
    # and `render` is the only place either is measured (L3).
    assert answer.structure == config.schema.line_max - config.schema.prose_budget(answer.task)
    assert answer.share("why").allowed == config.schema.why_budget(answer.task)


def test_an_unnamed_anchor_is_assumed_at_the_widest_the_file_carries(tmp_path):
    # The honest direction: an assumption that can be wrong is made wrong towards a sentence
    # with characters to spare, never towards the second composition of it this verb prevents.
    answer = budget(outlined(tmp_path), block="A", symptom=WIDE)
    assert answer.ref == "XXXVII.11" and answer.ref_assumed
    named = budget(outlined(tmp_path), block="A", symptom=WIDE, ref="IV.2")
    assert answer.share("why").allowed < named.share("why").allowed


def test_the_assumption_is_never_more_room_than_the_add_will_allow(tmp_path):
    # What the defect cost: the budget promised room the `add` then refused. Against every
    # anchor the file holds, the assumed answer is at or under what naming it would give.
    config = outlined(tmp_path)
    assumed = budget(config, block="A", symptom=WIDE).share("why").allowed
    for anchor in ("IV.2", "XXXVII.11"):
        assert assumed <= budget(config, block="A", symptom=WIDE, ref=anchor).share("why").allowed


def test_a_roadmap_carrying_no_pointer_says_so_instead_of_guessing_one(tmp_path, capsys):
    # The one case with no evidence to reason from, stated rather than reported silently.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\nref_scheme = "outline"\n'
        '[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text("# Roadmap\n\n## Block A — The model\n", encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    answer = budget(Config.discover(tmp_path), block="A")
    assert answer.ref is None and answer.ref_assumed
    assert main(["-C", str(tmp_path), "budget", "--block", "A"]) == EXIT_OK
    assert "counts no pointer" in capsys.readouterr().out


def test_the_derived_scheme_has_no_anchor_to_name_and_refuses_one(tmp_path, capsys):
    # The same rule `add` applies, from the same function: a pointer chosen by hand under the
    # id scheme is what `ref.mismatch` refuses, and a budget that took it would price a line
    # the tool will not write.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--block", "A", "--ref", "IV.2"]) != EXIT_OK
    assert not budget(project(tmp_path), block="A").ref_assumed


def test_an_open_line_keeps_its_own_anchor_and_takes_a_new_one_on_request(tmp_path):
    # The `amend` that moves the pointer and rewrites the why in one call: the room the why
    # has depends on which of the two anchors the line ends up carrying.
    config = outlined(tmp_path)
    assert budget(config, "RK2").ref == "XXXVII.11"
    assert not budget(config, "RK2").ref_assumed
    moved = budget(config, "RK2", ref="IV.2")
    assert moved.open_line and moved.ref == "IV.2"
    assert moved.share("why").allowed > budget(config, "RK2").share("why").allowed


def test_the_command_names_the_anchor_it_assumed_and_the_flag_that_corrects_it(tmp_path, capsys):
    outlined(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--block", "A"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "§XXXVII.11 assumed" in printed and "--ref" in printed
    assert main(["-C", str(tmp_path), "budget", "--block", "A", "--ref", "XX.2", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["ref"] == "XX.2" and payload["ref_assumed"] is False


def test_a_named_anchor_is_not_reported_as_an_assumption(tmp_path, capsys):
    # The two answers read identically without this, and only one of them an `add` can correct.
    outlined(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--block", "A", "--ref", "XX.2"]) == EXIT_OK
    assert "assumed" not in capsys.readouterr().out
