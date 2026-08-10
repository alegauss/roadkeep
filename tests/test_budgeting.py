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

from roadkeep.budgeting import (
    CHARS_PER_WORD,
    AmbiguousAnchor,
    body_budget,
    budget,
    budget_of,
    file_budget,
    non_goal_budget,
    words,
)
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.linting import lint
from roadkeep.config import Config
from roadkeep.schema import DESIGNED, body_aim

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


# -- the two larger limits, met only at the door until now (RK283) -------------

IMPROVEMENTS = """# Improvements

## Block A — The model

### §RK1 A design

One sentence of prose, and no subsection under it.
"""

GOALS = f"""{BACKLOG}
## Non-goals

Deliberately **not** built — check this list before proposing work:

- **No web UI.** Files and a CLI, because the store is the repository.
"""


def scoped(tmp_path: Path, *, governed: bool = True, prose: bool = True) -> Config:
    """A project whose non-goals are governed and whose prose file holds one section."""
    lines = ['prefix = "RK"', "[files]", 'roadmap = "ROADMAP.md"', 'changelog = "CHANGELOG.md"']
    if prose:
        lines.append('improvements = "IMPROVEMENTS.md"')
        (tmp_path / "IMPROVEMENTS.md").write_text(IMPROVEMENTS, encoding="utf-8")
    if governed:
        lines += ["[non_goals]", "lead = 40", "why = 120"]
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text(GOALS, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return Config.discover(tmp_path)


def test_a_section_body_states_its_limit_before_a_word_of_it_exists(tmp_path):
    # The largest of the three and the one that cost the most to meet at the door: 366 words
    # written, then refused against 300. Nothing here waited on the paragraph.
    config = scoped(tmp_path)
    answer = body_budget(config, "RK9")
    assert answer.limit == config.schema.section_max and answer.taken == 0
    assert not answer.written and answer.role == "improvements"
    assert answer.left == answer.limit


def test_an_amend_is_told_what_the_section_already_spends(tmp_path):
    # Where it matters: there the author holds a body and the number nobody stated is what
    # it has to fit inside.
    answer = body_budget(scoped(tmp_path), "RK1")
    assert answer.written and answer.taken > 0
    assert answer.left == answer.limit - answer.taken


def test_the_section_limit_is_the_roles_and_not_the_first_files(tmp_path):
    # `section = <n>` is per role (L6), so an answer that always read `improvements` would
    # state a limit the write into the other file is not held to.
    (tmp_path / "STRATEGY.md").write_text(
        "# Strategy\n\n## Block A — The model\n\n### §RK2 A plan\n\nProse.\n", encoding="utf-8"
    )
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\nstrategy = "STRATEGY.md"\n'
        "[limits.strategy]\nsection = 40\n",
        encoding="utf-8",
    )
    (tmp_path / "IMPROVEMENTS.md").write_text(IMPROVEMENTS, encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text(GOALS, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    config = Config.discover(tmp_path)
    # Resolved by which file holds it, the way every other reader resolves a role (RK196).
    assert body_budget(config, "RK2").role == "strategy"
    assert body_budget(config, "RK2").limit == config.schema_for("strategy").section_max
    assert body_budget(config, "RK1").role == "improvements"
    # And named outright where the caller has a file in mind that does not hold it yet.
    assert body_budget(config, "RK9", "strategy").limit == 40


def test_a_project_with_no_prose_file_is_refused_rather_than_given_a_number(tmp_path):
    # A limit is a fact about a role, so a project declaring none has no answer to give.
    with pytest.raises(KeyError):
        body_budget(scoped(tmp_path, prose=False), "RK9")


def test_the_non_goals_two_limits_are_the_lists_own_and_not_the_lines(tmp_path):
    # Measured at two refusals, 286 then 234, against 200 — and the number that refuses is
    # `[non_goals]`, which is not the `why` a task line is held to.
    config = scoped(tmp_path)
    shares = {one.field: one for one in non_goal_budget(config)}
    assert set(shares) == {"lead", "why"}
    assert shares["why"].limit == config.non_goals.why != config.schema.why_max
    assert shares["lead"].limit == config.non_goals.lead
    # No third limit measured across them: a non-goal is two fields and no shared line.
    assert not any(one.bound_by_line for one in shares.values())


def test_a_lead_that_exists_reports_what_its_argument_has_left(tmp_path):
    shares = {one.field: one for one in non_goal_budget(scoped(tmp_path), "No web UI")}
    assert shares["lead"].taken == len("No web UI.")
    assert shares["why"].taken > 0 and shares["why"].left == shares["why"].limit - shares["why"].taken


def test_an_ungoverned_list_is_refused_rather_than_given_an_invented_limit(tmp_path):
    # The write refuses it for the same reason: a limit for a list nobody governs would read
    # as one the file is already held to.
    with pytest.raises(KeyError):
        non_goal_budget(scoped(tmp_path, governed=False))


def test_a_lead_that_addresses_nothing_names_the_ones_that_do(tmp_path):
    with pytest.raises(KeyError):
        non_goal_budget(scoped(tmp_path), "no such constraint")


def test_the_command_answers_for_a_section_in_words_and_never_in_characters(tmp_path, capsys):
    # This limit is declared in words (RK258), so translating it would publish a second
    # number the config never stated.
    config = scoped(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--anchor", "RK1"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert f"{config.schema.section_max} words" in printed and "characters" not in printed
    assert main(["-C", str(tmp_path), "budget", "--anchor", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["unit"] == "words" and payload["subject"] == "section"
    assert payload["left"] == payload["limit"] - payload["taken"]


def test_the_command_answers_for_the_non_goal_bullet_in_both_units(tmp_path, capsys):
    config = scoped(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--non-goal"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert str(config.non_goals.why) in printed and "aim" in printed
    assert main(["-C", str(tmp_path), "budget", "--non-goal", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["subject"] == "non-goal"
    assert {one["field"] for one in payload["fields"]} == {"lead", "why"}


def test_one_subject_per_answer_rather_than_a_guess_at_which_was_meant(tmp_path, capsys):
    # Under the id scheme `RK1` is both a line and an anchor, so the subject is named and
    # never inferred: a budget the caller has to check before trusting saves nothing.
    scoped(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--anchor", "RK1", "--non-goal"]) == EXIT_USAGE
    assert main(["-C", str(tmp_path), "budget", "--lead", "No web UI"]) == EXIT_USAGE
    assert main(["-C", str(tmp_path), "budget", "--role", "improvements"]) == EXIT_USAGE


def test_the_task_line_answer_is_unchanged_by_the_other_two_subjects(tmp_path, capsys):
    # The three are one verb and not one answer: a line budget that grew a section's figure
    # would be the unbounded read L5 exists to avoid.
    scoped(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK1" and "unit" not in payload and "subject" not in payload


def test_the_section_budget_charges_the_argument_and_reports_the_subtree(tmp_path):
    # RK287 at this door: `taken` is what an amend can shorten, and a container charged for
    # its children names a figure no edit to its own paragraph can move.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A — The model\n\n### §RK1 A design\n\nEight words of "
        "prose, and one subsection under it.\n\n#### §RK1.1 A subsection\n\n"
        "Which belongs to the section above and is longer than it is.\n",
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    config = Config.discover(tmp_path)
    answer = body_budget(config, "RK1")
    assert answer.nests and answer.subtree > answer.taken
    assert answer.left == answer.limit - answer.taken
    # And the leaf says one number, because there is one.
    assert not body_budget(config, "RK1.1").nests


# -- the other half of the same transaction (RK301) ----------------------------


def sectioned(tmp_path: Path, *, prose: bool = True) -> Config:
    """A project whose `add --section` has somewhere to write, which is the transaction."""
    lines = ['prefix = "RK"', "[files]", 'roadmap = "ROADMAP.md"', 'changelog = "CHANGELOG.md"']
    if prose:
        lines.append('improvements = "IMPROVEMENTS.md"')
        (tmp_path / "IMPROVEMENTS.md").write_text(
            "# Improvements\n\n## Block A — The model\n\n### §RK1 A design\n\n"
            "Eight words of prose, and nothing nested under it.\n",
            encoding="utf-8",
        )
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return Config.discover(tmp_path)


def test_the_line_budget_carries_the_body_that_refuses_the_same_add(tmp_path):
    # The defect: `add --section` writes two things in one transaction, the second has its own
    # limit, it refuses the whole `add`, and this read named only the first.
    config = sectioned(tmp_path)
    answer = budget(config, block="A")
    assert answer.section is not None
    assert answer.section.limit == config.schema.section_max
    assert answer.section.role == "improvements" and not answer.section.written


def test_an_open_lines_budget_reports_what_that_section_has_left(tmp_path):
    # The asymmetry `budget` already carries between an add and an amend, at the second field.
    answer = budget(sectioned(tmp_path), "RK1")
    assert answer.section is not None and answer.section.written
    assert answer.section.taken > 0
    assert answer.section.left == answer.section.limit - answer.section.taken


def test_the_body_aim_sits_under_the_limit_and_never_on_it(tmp_path):
    # Composing to exactly 250 produced four refusals on its own: an author counts sentences
    # and `words` counts what the markup between them leaves, so a ceiling published as its
    # own target is a target hit from above.
    config = sectioned(tmp_path)
    section = budget(config, block="A").section
    assert section.aim < section.limit
    # And the measured worst case clears it: 266 against 250 is a 6.4% overshoot, and an
    # author making the same error from the aim lands under the gate.
    assert section.aim * 1.064 <= section.limit


def test_the_aim_for_a_written_body_is_about_what_is_left(tmp_path):
    # RK245's rule at this field: beside a partly written body the whole-field aim answers a
    # question nobody asked, and read next to a remainder it overstates the room.
    section = budget(sectioned(tmp_path), "RK1").section
    assert section.room == body_aim(section.left) < section.aim


def test_a_project_with_no_prose_file_has_no_second_half_to_budget(tmp_path):
    # The only state in which `add --section` does not exist, and a refusal here would refuse
    # the read every other project makes.
    assert budget(sectioned(tmp_path, prose=False), block="A").section is None


def test_the_command_prints_the_body_beside_the_two_fields_of_the_line(tmp_path, capsys):
    config = sectioned(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--block", "A"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert f"section    {config.schema.section_max} words (improvements)" in printed
    assert f"aim {body_aim(config.schema.section_max)} words" in printed


def test_the_json_carries_the_body_beside_the_fields(tmp_path, capsys):
    sectioned(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--block", "A", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["section"]["unit"] == "words"
    assert payload["section"]["aim"] < payload["section"]["limit"]
    # And the brief hands over the same object, since it prints this budget (RK190).
    assert main(["-C", str(tmp_path), "brief", "RK1", "--json"]) == EXIT_OK
    briefed = json.loads(capsys.readouterr().out)
    assert briefed["budget"]["section"]["anchor"] == "RK1"


def test_the_standalone_read_and_the_field_state_the_same_thing(tmp_path):
    # One shape at both doors: a second spelling of a body's budget would be a second answer.
    config = sectioned(tmp_path)
    assert budget(config, "RK1").section == body_budget(config, "RK1")


# -- the one budget with no pre-write read (RK345) -----------------------------

AGENTS = "# Agents\n\nOne line of guidance.\n"


def budgeted(tmp_path: Path, *, declared: bool = True, on_disk: bool = True) -> Config:
    """A project with an always-loaded file, which is the limit `[budgets]` holds."""
    lines = ['prefix = "RK"', "[files]", 'roadmap = "ROADMAP.md"', 'changelog = "CHANGELOG.md"']
    if declared:
        lines += ["[budgets]", '"agents.md" = { lines = 5, bytes = 100 }']
    if on_disk:
        (tmp_path / "agents.md").write_text(AGENTS, encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return Config.discover(tmp_path)


def test_an_every_turn_file_states_what_it_costs_before_the_edit(tmp_path):
    # The defect: every other limit here is answered before the text exists, and this one was
    # measured with two `wc` reads and a subtraction — at the moment a module had to be named.
    (load,) = file_budget(budgeted(tmp_path))
    costs = {one.unit: one for one in load.costs}
    assert load.path == "agents.md" and load.present and not load.over
    assert costs["lines"].taken == 3 and costs["lines"].left == 2
    # Off the bytes on disk and not off the string this test wrote: a budget is what the
    # loader pays, and a line ending translated on the way out is part of what it pays.
    written = (tmp_path / "agents.md").read_bytes()
    assert costs["bytes"].taken == len(written) and costs["bytes"].limit == 100


def test_the_gate_and_the_read_count_the_same_file_the_same_way(tmp_path):
    # One measurement and not two (RK50): a read that composed the edit and a gate that
    # refused it would be the disagreement this door exists to remove.
    config = budgeted(tmp_path)
    (tmp_path / "agents.md").write_text("# Agents\n" + "A line.\n" * 9, encoding="utf-8")
    (load,) = file_budget(config)
    costs = {one.unit: one for one in load.costs}
    assert costs["lines"].over == 5 and costs["lines"].left == 0
    # And `lint` refuses it, naming the same figure — the read reports, the gate holds.
    findings = [one for one in lint(config).findings if one.code == "budget.lines"]
    assert findings and f"{costs['lines'].taken} lines" in findings[0].message


def test_a_declared_file_that_is_not_there_is_said_and_never_read_as_room(tmp_path):
    # The state `lint` reports as `budget.absent`: the whole limit free is exactly what a
    # missing file looks like, so the answer says which of the two it is.
    (load,) = file_budget(budgeted(tmp_path, on_disk=False))
    assert not load.present and all(one.taken == 0 for one in load.costs)


def test_a_path_no_budget_declares_is_refused_with_the_ones_that_do(tmp_path):
    with pytest.raises(KeyError) as refusal:
        file_budget(budgeted(tmp_path), "README.md")
    assert "agents.md" in str(refusal.value)
    # And the file's own spelling reaches it, because the caller has the file open and not
    # `roadkeep.toml`: an absolute path resolving to the same file is the same subject.
    assert file_budget(budgeted(tmp_path), str(tmp_path / "agents.md"))[0].path == "agents.md"


def test_a_project_declaring_no_budgets_is_refused_rather_than_given_a_number(tmp_path):
    # The reason the non-goal read is: a limit for a file nobody declared is one invented
    # here, and it would read as one the project is already held to.
    with pytest.raises(KeyError):
        file_budget(budgeted(tmp_path, declared=False))


def test_the_command_answers_in_the_units_the_loader_pays(tmp_path, capsys):
    # No aim and no word figure (RK258): `[budgets]` is declared in lines and bytes.
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--file"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "agents.md  budgeted" in printed and "3 of 5, 2 left" in printed
    assert "aim" not in printed and "words" not in printed
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["subject"] == "file" and len(payload["files"]) == 1
    assert {one["unit"] for one in payload["files"][0]["units"]} == {"lines", "bytes"}


def test_the_fourth_subject_is_named_and_never_combined(tmp_path, capsys):
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--file", "--non-goal"]) == EXIT_USAGE
    # One grammar for every verb that takes more than one answer (RK489): what each subject
    # answers is a noun phrase its own `add_parser` declares, and the refusal is composed.
    said = capsys.readouterr().err
    assert "one answer per call" in said
    assert "an every-turn file (--file)" in said and "(--non-goal)" in said


# -- one anchor, two files, and no first match (RK303) -------------------------


def doubled(tmp_path: Path) -> Config:
    """A project where §RK1 is declared by both prose files, which is the ambiguity."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\nstrategy = "STRATEGY.md"\n'
        "[limits.strategy]\nsection = 40\n",
        encoding="utf-8",
    )
    (tmp_path / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A — The model\n\n### §RK1 A design\n\n"
        "Eight words of prose, and nothing nested under it.\n",
        encoding="utf-8",
    )
    (tmp_path / "STRATEGY.md").write_text(
        "# Strategy\n\n## Block A — The model\n\n### §RK1 A position\n\nProse.\n",
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return Config.discover(tmp_path)


def test_two_files_declaring_one_anchor_are_refused_and_never_the_first_of_them(tmp_path):
    # The direction every other reader already took: `show` answers that the pointer resolves
    # to neither and `ship` leaves the section rather than choosing. A number about the first
    # is right about a file that was picked rather than named.
    config = doubled(tmp_path)
    with pytest.raises(AmbiguousAnchor) as refusal:
        body_budget(config, "RK1")
    assert refusal.value.files == ("IMPROVEMENTS.md", "STRATEGY.md")
    assert "IMPROVEMENTS.md and STRATEGY.md" in str(refusal.value)
    # And the unambiguous anchor in the same project is untouched by the rule.
    assert body_budget(config, "RK2").role == "improvements"


def test_the_named_role_is_what_resolves_it_and_the_only_thing_that_can(tmp_path):
    # The caller saying which of the two they mean, which is the one resolution that is not
    # this verb choosing (L4) — and the limit that comes back is that role's own.
    config = doubled(tmp_path)
    assert body_budget(config, "RK1", "strategy").limit == 40
    assert body_budget(config, "RK1", "improvements").role == "improvements"


def test_the_lines_own_two_fields_survive_an_anchor_nobody_can_price(tmp_path):
    # The ambiguity is about the body, not about the sentence: refusing the whole read would
    # cost the author a `why` budget that is still exactly right.
    answer = budget(doubled(tmp_path), "RK1")
    assert answer.share("why").allowed > 0 and answer.section is None
    # And the absence says which of the two nulls this is, because a project declaring no
    # prose file at all reads identically otherwise.
    assert "§RK1 is declared by" in answer.section_absence
    plain = tmp_path / "plain"
    plain.mkdir()
    assert budget(sectioned(plain, prose=False), "RK1").section_absence == ""


def test_the_command_refuses_the_anchor_and_names_the_flag_that_resolves_it(tmp_path, capsys):
    config = doubled(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--anchor", "RK1"]) == EXIT_USAGE
    assert "--role" in capsys.readouterr().err
    assert main(["-C", str(tmp_path), "budget", "--anchor", "RK1", "--role", "strategy"]) == EXIT_OK
    assert f"{config.schema_for('strategy').section_max} words" in capsys.readouterr().out


def test_the_json_says_why_the_section_is_null_rather_than_only_that_it_is(tmp_path, capsys):
    doubled(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["section"] is None and payload["section_absence"]
    assert payload["fields"], "the line's own fields are unaffected by the anchor"


# -- the fifth subject: what the surface costs (RK464) ------------------------


def test_the_tool_list_states_what_it_costs_a_session(tmp_path, capsys):
    """RK30 put `[budgets]` on the files a session loads every turn, because resident prose
    has no natural ceiling, and `lint` refuses one over. The schema this server publishes was
    counted nowhere: measured on a three-file project, 51 tools and 52,892 characters, six
    times the budget the resident file is held to.

    Not a claim the list is too long — a claim that the number was not stated, and RK30's own
    argument is that a limit nobody counts is a limit that moves."""
    from roadkeep.serving import TOOLS

    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--tools"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert f"tool list  {len(TOOLS)} tool(s)" in printed
    assert "utf-16-code-units" in printed
    # The largest few, because a reader deciding what to cut wants where the size went.
    assert "add " in printed and "… and" in printed


def test_the_payload_carries_every_tool_and_the_terminal_the_largest(tmp_path, capsys):
    from roadkeep.serving import TOOLS

    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--tools", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["tools"] == len(TOOLS) == len(payload["by_tool"])
    assert payload["characters"] == sum(row["characters"] for row in payload["by_tool"])
    # Largest first, which is the order the terminal truncates from.
    sizes = [row["characters"] for row in payload["by_tool"]]
    assert sizes == sorted(sizes, reverse=True)


def test_the_figure_moves_with_what_the_surface_actually_publishes(tmp_path, capsys):
    """Derived from `descriptors` and not a second estimate: a description reworded in
    `cli.py` moves this number, which is the whole reason it is worth reading."""
    from roadkeep.serving import descriptors

    config = budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--tools", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    described = {one["name"] for one in descriptors(config)}
    assert {row["name"] for row in payload["by_tool"]} == described


def test_the_fifth_subject_is_named_and_never_combined(tmp_path, capsys):
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--tools", "--file"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "one answer per call" in said
    assert "(--tools)" in said and "(--file)" in said


def test_a_project_declaring_no_budgets_is_still_told_what_the_surface_costs(tmp_path, capsys):
    """The one subject here that is not about a declaration: the surface costs what it costs
    whether or not `[budgets]` exists, and a project that declared none is exactly the one
    that has never been told."""
    budgeted(tmp_path, declared=False)
    assert main(["-C", str(tmp_path), "budget", "--tools"]) == EXIT_OK
    assert "tool(s)" in capsys.readouterr().out


# -- a narrowing flag belongs to its subject (RK465) --------------------------


def test_a_narrowing_flag_is_refused_beside_a_subject_it_does_not_narrow(tmp_path, capsys):
    """The refusal existed and was right, and it sat after every dispatch — so it fired only
    where nothing else had. Measured: `--role improvements` exits 2 alone and exit 0 beside
    `--tools`, `--file` or `--non-goal`, changing nothing. A caller reading a number it
    believes it narrowed is worse off than one refused (RK16's argument)."""
    budgeted(tmp_path)
    for subject in (["--tools"], ["--file"], ["--non-goal"]):
        assert main(["-C", str(tmp_path), "budget", *subject, "--role", "improvements"]) == EXIT_USAGE
        said = capsys.readouterr().err
        assert "--role narrows --anchor" in said and f"{subject[0]} is a different subject" in said


def test_the_flag_that_cannot_stand_alone_still_says_so(tmp_path, capsys):
    """Two states and two mistakes: a subject was named and it is not this flag's, or none
    was and the flag has nothing to narrow."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--role", "improvements"]) == EXIT_USAGE
    assert "--role narrows --anchor, so pass it too" in capsys.readouterr().err
    assert main(["-C", str(tmp_path), "budget", "--lead", "x"]) == EXIT_USAGE
    assert "--lead narrows --non-goal, so pass it too" in capsys.readouterr().err


def test_each_flag_beside_the_subject_it_narrows_is_never_refused_for_it(tmp_path, capsys):
    """The rule narrows nothing that worked: `--role` is `--anchor`'s and `--lead` is
    `--non-goal`'s. Asserted on the refusal and not on the answer, because what each subject
    then says about an unknown anchor or an absent lead is that subject's own business."""
    budgeted(tmp_path)
    main(["-C", str(tmp_path), "budget", "--anchor", "RK1", "--role", "improvements"])
    assert "--role narrows" not in capsys.readouterr().err
    main(["-C", str(tmp_path), "budget", "--non-goal", "--lead", "a lead"])
    assert "--lead narrows" not in capsys.readouterr().err
