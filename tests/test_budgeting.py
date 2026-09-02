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
    conversion,
    budget,
    budget_of,
    file_budget,
    non_goal_budget,
    words,
)
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.verbs.refusing import EXIT_GATE
from roadkeep.linting import lint
from roadkeep.config import Config
from roadkeep.authoring import amend as amend_line
from roadkeep.sections import SectionError, amend
from roadkeep.kernel.schema import DESIGNED, SchemaError, body_aim

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
    why = answer.share("why")
    # What the line holds, and — since RK1366 — the whole allowance beside it: `amend --why`
    # replaces that sentence, so the room for the next one is not the room beside this one.
    assert why.taken == len(answer.task.why)
    assert why.replaced and why.left == why.allowed


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
    # Off the command since RK1381, which is the whole of that task: the measurement was
    # written here and in a comment in source, and a corpus that grew past the constant could
    # only speak through this test failing — with the new figure taking a throwaway script to
    # get. Read from `conversion` rather than recomputed, so what this asserts is the *rule*
    # and the reading is one answer a caller can also ask for.
    found = conversion(Config.discover(Path(__file__).parents[1]))
    assert found.sample > 100, "too small a corpus to fix a constant from"
    assert found.at == CHARS_PER_WORD, "the read and the constant came apart"
    # Above the 95th percentile, so an aim that is hit lands inside the gate about nineteen
    # times in twenty; and not far above it, or the aim is tighter than the format allows.
    assert found.reading <= CHARS_PER_WORD <= found.reading + 0.75


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
    # The one number RK185 skipped, and the one a *draft* is bounded by: `aim` describes the
    # whole field, so beside prose the caller has already composed it overstates the room.
    # Asked of a draft since RK1366 — on the line as it stands nothing is partly written,
    # `amend` replacing the field rather than adding to it.
    config = project(tmp_path)
    why = budget(config, "RK1", why="Because of a reason drafted at some length.").share("why")
    assert why.taken and why.drafted and not why.replaced
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
    draft = "Because of a reason drafted at some length."
    assert main(["-C", str(tmp_path), "budget", "RK1", "--why", draft]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "more words" in printed
    assert "aim 30 words" not in printed


def test_the_aim_beside_a_field_the_write_replaces_is_the_whole_of_it(tmp_path, capsys):
    """RK1366. The rule above, at the one shape it does not describe: nothing is *partly*
    written on a line an `amend` rewrites, so `aim 5 more words` beside a sentence about to be
    deleted is the misreading it exists to prevent, pointed the other way."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK1"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "more words" not in printed
    # And the row that says why the two figures below it do not add up.
    assert "replacing  what is written below" in printed


def test_the_remainder_is_the_longest_why_the_amend_accepts(tmp_path):
    """RK1366's falsification, held against the write and never against a number remembered
    here: what `budget <id>` publishes is composed as a `--why` and amended in, and one code
    unit more than it is refused. The defect it closes was the same arithmetic RK1365 found a
    file over — `allowed - taken` on a field the next write deletes, which on one line here
    read 55 where 200 was true, and the word aim beside it 8 against 31."""
    for where, spare in (("exact", 0), ("over", 1)):
        root = tmp_path / where
        root.mkdir()
        config = project(root)
        allowed = budget(config, "RK1").share("why")
        # One sentence ending in a stop, so nothing but the width is under test.
        outcome = "W" * (allowed.left - 1 + spare) + "."
        if not spare:
            assert amend_line(config, "RK1", why=outcome).changed == ("why",)
            assert outcome in config.path("roadmap").read_text(encoding="utf-8")
            continue
        with pytest.raises(SchemaError) as refused:
            amend_line(config, "RK1", why=outcome)
        assert "why.too-long" in [one.code for one in refused.value.violations]


def test_the_json_carries_the_remainder_beside_the_characters(tmp_path, capsys):
    # Beside `left` and not instead of it: the characters are still what refuses.
    project(tmp_path)
    draft = "Because of a reason drafted at some length."
    assert main(["-C", str(tmp_path), "budget", "RK1", "--why", draft, "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    field = next(one for one in payload["fields"] if one["field"] == "why")
    assert field["room"] == words(field["left"]) and field["left"] < field["allowed"]
    # Which of the two arithmetics produced it, for `drafted`'s own reason (RK1366).
    assert field["drafted"] and not field["replaced"]


def test_the_brief_states_the_same_figure_as_the_budget(tmp_path, capsys):
    # `brief` prints the `why`'s share of the line it hands over, so whatever `Share` grows
    # is what a task started through it is told — and the two cannot state it differently.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "brief", "RK1"]) == EXIT_OK
    briefed = capsys.readouterr().out
    assert main(["-C", str(tmp_path), "budget", "RK1"]) == EXIT_OK
    # Off the share and never spelled here: the claim is that one figure reaches both doors,
    # and a test naming the arithmetic would be the second statement of it (RK1366).
    aimed = budget(Config.discover(tmp_path), "RK1").share("why").aimed
    assert aimed in briefed
    assert aimed in capsys.readouterr().out


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


def test_a_lead_that_exists_reports_what_the_rewrite_of_it_has(tmp_path):
    # What the bullet holds, and the whole limit beside it: `non-goal amend --why` replaces
    # that argument and a changed lead is a drop and an add, so neither field is extended
    # (RK1366) — the same correction the task line's two fields took.
    shares = {one.field: one for one in non_goal_budget(scoped(tmp_path), "No web UI")}
    assert shares["lead"].taken == len("No web UI.")
    assert shares["why"].taken > 0
    assert shares["why"].replaced
    assert shares["why"].left == shares["why"].limit


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
    # `taken` is still what an amend can shorten, and RK1036 is about a different number:
    # what is *left* is the declared limit less what the subsections already spend, because
    # a write here replaces this paragraph and leaves them where they are.
    assert answer.allowed == answer.limit - (answer.subtree - answer.taken)
    assert answer.left == answer.allowed - answer.taken
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
    # Off the string this test wrote and not off the bytes on disk (RK1105). This assertion
    # was the other way round, on the ground that a line ending translated on the way out is
    # part of what a loader pays — and it was the defect: the fixture writes through Python's
    # own translation, so it asserted 35 here and 32 on a posix runner for one source string.
    # A budget is a fact about the commit, so `\r\n` counts as the `\n` the repository stores.
    assert costs["bytes"].taken == len(AGENTS.encode()) and costs["bytes"].limit == 100
    written = (tmp_path / "agents.md").read_bytes()
    assert load.translated == written.count(b"\r\n")  # named, and never charged


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


def test_the_read_names_what_this_checkout_pays_over_the_ceiling(tmp_path, capsys):
    # RK1105's other half. The normalised number is the one that decides, and the bytes a
    # loader on this machine really reads are stated under it rather than dropped — otherwise
    # the tool answers a smaller number than the file and never says which question it took.
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_bytes(b"# Agents\r\n\r\nOne line.\r\n")
    assert main(["-C", str(tmp_path), "budget", "--file"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "bytes      20 of 100" in printed
    assert "checkout   3 more, this tree's lines ending CRLF" in printed
    assert main(["-C", str(tmp_path), "budget", "--file", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["files"][0]["translated"] == 3


def test_a_section_breakdown_counts_the_bytes_the_total_counted(tmp_path):
    # The parts have to sum inside the total (RK1092 under RK1105): measured off the checkout
    # while the total was normalised, a breakdown adds up past the number printed above it,
    # and a reader deciding what to cut is comparing the two.
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_bytes(b"## One\r\nbody\r\n## Two\r\nbody\r\n")
    (load,) = file_budget(Config.discover(tmp_path))
    assert sum(part.bytes for part in load.parts) == load.bytes


def test_an_lf_checkout_says_nothing_about_a_translation_it_did_not_make(tmp_path, capsys):
    # 0 is not a fact worth a line: on a posix checkout the two numbers are one number, and a
    # note about the difference would be a reader's cue to look for one that is not there.
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_bytes(b"# Agents\n\nOne line.\n")
    assert main(["-C", str(tmp_path), "budget", "--file"]) == EXIT_OK
    assert "checkout" not in capsys.readouterr().out
    assert [one for one in lint(Config.discover(tmp_path)).notes
            if one.code.startswith("budget.")] == []


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


# -- where the number came from, on the earlier path (RK1071) ------------------


def _priced(tmp_path: Path, limits: str = "") -> Path:
    """A project whose `[limits]` are its own, which is what makes an origin worth printing."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        + limits,
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return tmp_path


def _lines_of(tmp_path: Path, *needles: str) -> list[int]:
    """Which line of the written config each of these is on, 1-based as an editor counts."""
    body = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8").splitlines()
    return [next(n for n, line in enumerate(body, 1) if line == needle) for needle in needles]


def test_the_read_says_which_of_the_numbers_the_project_chose(tmp_path, capsys):
    # RK1067 put the citation on the refusal; this is the same author one moment earlier —
    # the moment the whole tool is built on, the number arriving before the prose does.
    _priced(tmp_path, "\n[limits]\nsymptom = 100\nwhy = 180\n")
    assert main(["-C", str(tmp_path), "budget", "--block", "A", "--symptom", "x"]) == EXIT_OK
    said = next(line for line in capsys.readouterr().out.splitlines() if "declared" in line)
    # Grouped by the table, because that is what a reader opens: one file and one heading,
    # then the line each field is on — not an address after every figure in the column.
    assert "roadkeep.toml [limits]" in said
    # The line numbers are read back off the file rather than spelled here: a fixture that
    # grows a line would otherwise make this test assert an address nobody can click.
    at = _lines_of(tmp_path, "symptom = 100", "why = 180")
    assert f"symptom:{at[0]}" in said and f"why:{at[1]}" in said


def test_a_limit_left_to_the_tool_is_named_beside_the_ones_that_were_chosen(tmp_path, capsys):
    # The split is the live question: *which of these did I choose* only arises where some
    # were and some were not, and that is exactly when the answer is worth the line.
    _priced(tmp_path, "\n[limits]\nwhy = 180\n")
    main(["-C", str(tmp_path), "budget", "--block", "A", "--symptom", "x"])
    said = next(line for line in capsys.readouterr().out.splitlines() if "declared" in line)
    (line,) = _lines_of(tmp_path, "why = 180")
    assert f"why:{line}" in said and "symptom is this tool's default" in said


def test_a_project_that_declared_no_limit_is_told_nothing_rather_than_five_defaults(
    tmp_path, capsys
):
    # `this tool's default` on every row is the noise the one line exists to avoid, and a
    # project that declared none has no line for anybody to go and look at.
    _priced(tmp_path)
    main(["-C", str(tmp_path), "budget", "--block", "A", "--symptom", "x"])
    assert "declared" not in capsys.readouterr().out


def test_the_payload_carries_the_origin_beside_each_number(tmp_path, capsys):
    # The half that is not a layout question: a surface serving this over MCP can answer
    # *why is it 200* without a second call, which is the read that otherwise costs a turn.
    _priced(tmp_path, "\n[limits]\nwhy = 180\n")
    main(["-C", str(tmp_path), "budget", "--block", "A", "--symptom", "x", "--json"])
    payload = json.loads(capsys.readouterr().out)
    sources = {field["field"]: field["source"] for field in payload["fields"]}
    (line,) = _lines_of(tmp_path, "why = 180")
    assert sources["why"] == f"roadkeep.toml:{line} [limits].why"
    # And the default says so rather than being absent, which a consumer cannot tell from
    # a field this surface forgot to answer about.
    assert sources["symptom"] == "this tool's default"


# -- the fifth subject: what the surface costs (RK464) ------------------------


def test_the_tool_list_states_what_it_costs_a_session(tmp_path, capsys):
    """RK30 put `[budgets]` on the files a session loads every turn, because resident prose
    has no natural ceiling, and `lint` refuses one over. The schema this server publishes was
    counted nowhere: measured on a three-file project, 51 tools and 52,892 characters, six
    times the budget the resident file is held to.

    Not a claim the list is too long — a claim that the number was not stated, and RK30's own
    argument is that a limit nobody counts is a limit that moves."""
    from roadkeep.serving import published

    config = budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools"]) == EXIT_OK
    printed = capsys.readouterr().out
    # Both messages a session is handed before its first call (RK1062), because reporting
    # one of them made the other a place an author could move text into and measure a win.
    # Counted against what *this* project is published (RK1360) — which is the whole point of
    # the verb: a figure derived from the package would be one no checkout ever pays.
    assert f"session    {len(published(config))} tool(s) and the handshake" in printed
    assert "handshake" in printed and "sent once" in printed
    assert "utf-16-code-units" in printed
    # The largest few, because a reader deciding what to cut wants where the size went.
    assert "add " in printed and "… and" in printed


def test_the_payload_carries_every_tool_and_the_terminal_the_largest(tmp_path, capsys):
    from roadkeep.serving import published

    config = budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["tools"] == len(published(config)) == len(payload["by_tool"])
    assert payload["tool_list"] == sum(row["characters"] for row in payload["by_tool"])
    # The total is the session's and the two halves are named beside it (RK1062): a caller
    # left to add them is a caller who can be told a saving that only moved.
    assert payload["characters"] == payload["tool_list"] + payload["handshake"]
    # Largest first, which is the order the terminal truncates from.
    sizes = [row["characters"] for row in payload["by_tool"]]
    assert sizes == sorted(sizes, reverse=True)


def test_the_handshake_is_counted_as_what_it_actually_carries(tmp_path, capsys):
    # Derived from `instructions()` for `descriptors`' reason: a second estimate of a payload
    # is a number that stops moving when the payload does, which is the whole failure RK1062
    # names — the read that could not see where RK1060's 3,159 characters went.
    from roadkeep.serving import instructions
    from roadkeep.kernel.schema import width

    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["handshake"] == width(instructions())


def test_the_figure_moves_with_what_the_surface_actually_publishes(tmp_path, capsys):
    """Derived from `descriptors` and not a second estimate: a description reworded in
    `cli.py` moves this number, which is the whole reason it is worth reading."""
    from roadkeep.serving import descriptors

    config = budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    described = {one["name"] for one in descriptors(config)}
    assert {row["name"] for row in payload["by_tool"]} == described


def test_the_fifth_subject_is_named_and_never_combined(tmp_path, capsys):
    # Within one verb, which is what the rule is about (RK489). Since RK1321 the surface
    # subjects live on `cost` and the prose ones on `budget`, so a pair across the two is two
    # commands and not two answers — the refusal that matters is each verb's own.
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "--brief"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "one answer per call" in said
    assert "(--tools)" in said and "(--brief)" in said

    assert main(["-C", str(tmp_path), "budget", "--file", "--non-goal"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "one answer per call" in said
    assert "(--file)" in said and "(--non-goal)" in said


def test_a_project_declaring_no_budgets_is_still_told_what_the_surface_costs(tmp_path, capsys):
    """The one subject here that is not about a declaration: the surface costs what it costs
    whether or not `[budgets]` exists, and a project that declared none is exactly the one
    that has never been told."""
    budgeted(tmp_path, declared=False)
    assert main(["-C", str(tmp_path), "cost", "--tools"]) == EXIT_OK
    assert "tool(s)" in capsys.readouterr().out


# -- a narrowing flag belongs to its subject (RK465) --------------------------


def test_a_narrowing_flag_is_refused_beside_a_subject_it_does_not_narrow(tmp_path, capsys):
    """The refusal existed and was right, and it sat after every dispatch — so it fired only
    where nothing else had. Measured: `--role improvements` exits 2 alone and exit 0 beside
    `--tools`, `--file` or `--non-goal`, changing nothing. A caller reading a number it
    believes it narrowed is worse off than one refused (RK16's argument)."""
    budgeted(tmp_path)
    # `--tools` left with `cost` (RK1321), and `--role` never narrowed it: what is held here
    # is this verb's own subjects against this verb's own narrowing flag.
    for subject in (["--file"], ["--non-goal"]):
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


# -- the read RK1024 did not reach (RK1029) ----------------------------------


def crowded(tmp_path: Path, spent: int, limit: int = 30, pointed: bool = True) -> Config:
    """An outline project whose §IX is a design already spending most of its budget."""
    line = (
        "- 📋 **RK1** (deps: —) **A symptom** — Because of a reason. → §IX\n"
        if pointed
        else ""
    )
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\nref_scheme = "outline"\n[files]\nroadmap = "ROADMAP.md"\n'
        f'changelog = "CHANGELOG.md"\nimprovements = "IMPROVEMENTS.md"\n'
        f"\n[limits]\nsection = {limit}\n",
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(
        f"# Roadmap\n\n## Block A — The model\n\n{line}", encoding="utf-8"
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## Block A — The model\n", encoding="utf-8"
    )
    (tmp_path / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A — The model\n\n### IX A design\n\n"
        + " ".join(["word"] * spent)
        + "\n",
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_a_child_of_a_full_parent_is_answered_with_the_room_it_has(tmp_path):
    """The reproduction. `budget --anchor IX.1` answered `30 words, aim 28` about a parent
    with one word of room — the pre-`add` read, wrong in the generous direction, on the one
    question this tool is built to answer before the prose exists."""
    answer = body_budget(crowded(tmp_path, spent=29), "IX.1")
    # A row and not a substitution: the declared limit is still the first number a reader is
    # shown. What RK1036 changed is the aim beside it, which no longer promises room the
    # write refuses — the ancestor leaves one word, so that is what may be composed.
    assert (answer.limit, answer.allowed, answer.aim) == (30, 1, body_aim(1))
    assert (answer.under, answer.under_taken, answer.under_left) == ("IX", 29, 1)


def test_a_container_nothing_points_at_never_binds_a_child(tmp_path):
    """The gate's own rule, asked the same way (RK215): a parent no line points at is
    charged its own prose, so reporting it here would price a body against a heading nobody
    bills — and refuse prose `lint` calls clean."""
    answer = body_budget(crowded(tmp_path, spent=29, pointed=False), "IX.1")
    assert answer.under == "" and answer.under_left == 30


def test_a_top_level_has_no_ancestor_to_be_bound_by(tmp_path):
    answer = body_budget(crowded(tmp_path, spent=29), "XII")
    assert answer.under == "" and answer.under_taken == 0


def test_the_tightest_ancestor_is_the_one_reported(tmp_path):
    """Every ancestor and not the immediate one: a parent with room under a grandparent with
    none is still a write the gate fails, and the number that matters is the one an `add`
    will actually be refused by."""
    config = crowded(tmp_path, spent=29)
    path = config.root / "IMPROVEMENTS.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n#### IX.1 A child\n\nFour short words.\n",
        encoding="utf-8",
    )
    answer = body_budget(Config.discover(tmp_path), "IX.1.1")
    assert answer.under == "IX"


def test_a_written_child_is_answered_with_what_a_replacement_body_may_say(tmp_path):
    """RK1035. The ancestor's total is billed with everything under it, this section
    included, so quoting it raw answered a written child with the room an *insert* would
    have — two figures and the subtraction between them, which is the analysis this door
    exists to remove rather than move."""
    config = crowded(tmp_path, spent=10)
    path = config.root / "IMPROVEMENTS.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n#### IX.1 A child\n\n" + "word " * 5 + "\n",
        encoding="utf-8",
    )
    answer = body_budget(Config.discover(tmp_path), "IX.1")
    assert answer.written and answer.under == "IX"
    # The parent's 19 include this child's 5, so a replacement body may be 30 - (19 - 5).
    assert (answer.under_taken, answer.under_left) == (19, 16)


def test_the_figure_is_what_the_write_after_it_accepts(tmp_path):
    """The property the number is worth anything for: a budget the next call disagrees with
    is the retry this whole door exists to save."""
    config = crowded(tmp_path, spent=10)
    path = config.root / "IMPROVEMENTS.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n#### IX.1 A child\n\n" + "word " * 5 + "\n",
        encoding="utf-8",
    )
    room = body_budget(Config.discover(tmp_path), "IX.1").under_left
    out = amend(
        Config.discover(tmp_path), "improvements", "IX.1", body=" ".join(["term"] * room)
    )
    document = out.document
    document.save()
    with pytest.raises(SectionError):
        amend(
            Config.discover(tmp_path),
            "improvements",
            "IX.1",
            body=" ".join(["term"] * (room + 1)),
        )


def test_an_unwritten_child_answers_exactly_what_it_answered(tmp_path):
    """The half that must not move: on an unwritten anchor this section contributes nothing,
    so the discount is zero and the row is the one RK1029 shipped."""
    config = crowded(tmp_path, spent=29)
    answer = body_budget(config, "IX.1")
    assert not answer.written
    assert (answer.under_taken, answer.under_left) == (29, 1)


def test_the_aim_is_what_the_write_after_it_accepts_on_a_full_parent(tmp_path):
    """RK1036. `Share.allowed` has reported the binding figure since RK183, and this was the
    one budget here that reported the larger: `30 words, 10 written, 20 left … aim 18 more
    words` on a parent whose subtree sat at its limit, an eighteen-word body refused, and
    ten what landed — both figures on the line and the subtraction the reader's."""
    config = crowded(tmp_path, spent=10)
    path = config.root / "IMPROVEMENTS.md"
    path.write_text(
        path.read_text(encoding="utf-8") + "\n#### IX.1 A child\n\n" + "word " * 15 + "\n",
        encoding="utf-8",
    )
    answer = body_budget(Config.discover(tmp_path), "IX")
    # The declared limit is unchanged and still shown; what binds is the subsections' share.
    assert answer.limit == 30 and answer.subtree > answer.taken
    assert answer.allowed == answer.limit - (answer.subtree - answer.taken)
    out = amend(
        Config.discover(tmp_path), "improvements", "IX", body=" ".join(["term"] * answer.allowed)
    )
    document = out.document
    document.save()
    with pytest.raises(SectionError):
        amend(
            Config.discover(tmp_path),
            "improvements",
            "IX",
            body=" ".join(["term"] * (answer.allowed + 1)),
        )


def test_a_leaf_with_no_ancestor_answers_its_declared_limit(tmp_path):
    """The half that must not move, and it is every section in a flat file — which is why
    this was invisible for so long: with no subsections and no binding ancestor, both claims
    are the declared limit and the answer is the one this door always gave."""
    config = crowded(tmp_path, spent=10, pointed=False)
    answer = body_budget(config, "IX")
    assert (answer.allowed, answer.aim) == (answer.limit, body_aim(answer.limit))
    assert answer.left == answer.limit - answer.taken


# -- the section a new task will not write into (RK1041) ---------------------


def outlined_with_a_full_section(tmp_path: Path, spent: int = 29, limit: int = 30) -> Config:
    """An outline project whose one live design is the widest pointer its roadmap carries."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\nref_scheme = "outline"\n[files]\nroadmap = "ROADMAP.md"\n'
        f'changelog = "CHANGELOG.md"\nimprovements = "IMPROVEMENTS.md"\n'
        f"\n[limits]\nsection = {limit}\n",
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(
        "# Roadmap\n\n## Block A — The model\n\n"
        "- 📋 **RK1** (deps: —) **A symptom** — Because of a reason. → §IX\n",
        encoding="utf-8",
    )
    (tmp_path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## Block A — The model\n", encoding="utf-8"
    )
    (tmp_path / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A — The model\n\n### IX A design\n\n"
        + " ".join(["word"] * spent)
        + "\n",
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_a_new_task_is_budgeted_for_the_section_it_will_create(tmp_path):
    """The defect. RK265's stand-in for an unnamed pointer is the **widest anchor the roadmap
    already carries**, so the structure of an unwritten line is never under-measured — and
    reporting that anchor's *occupancy* answered about a section belonging to another task.
    A new task gets a fresh anchor and the whole limit."""
    config = outlined_with_a_full_section(tmp_path)
    answer = budget(config, block="A")
    assert answer.ref_assumed and answer.section is not None
    assert not answer.section.written
    assert (answer.section.taken, answer.section.allowed) == (0, answer.section.limit)
    assert answer.section.under == ""


def test_the_line_s_own_fields_still_take_the_wider_structure(tmp_path):
    """The half that must not move: the guess is kept where it is honest. RK265's whole point
    is that a pointer the caller did not name is assumed *wide*, so the `why` is never offered
    room the `add` would refuse — and that is about the line, not about the section."""
    config = outlined_with_a_full_section(tmp_path)
    assumed = budget(config, block="A")
    assert assumed.ref == "IX" and assumed.ref_assumed


def test_a_named_ref_is_the_caller_s_and_is_answered_as_it_is(tmp_path):
    """Naming a `--ref` makes the anchor a fact rather than a stand-in, which is the read a
    child address wants (RK1029): there the ancestor's occupancy is exactly what binds."""
    config = outlined_with_a_full_section(tmp_path)
    answer = budget(config, block="A", ref="IX.5")
    assert not answer.ref_assumed
    assert answer.section is not None and answer.section.under == "IX"
    assert answer.section.under_taken == 29


# -- where the size is, not only how much of it there is (RK1092) --------------


def test_the_file_budget_says_where_the_size_went(tmp_path, capsys):
    """`cost --tools` ranks tools so an author cutting the schema knows where to cut, and
    the resident file had only a total — so `agents.md` reaching eight bytes of room turned
    *compress the prose rather than the index* into a preference nothing had re-measured.

    Sections and not paragraphs: a `##` is what the file declares, and a paragraph is where
    a reader happened to stop.
    """
    (tmp_path / "agents.md").write_text(
        "intro\n\n## Big\n\n" + "x" * 400 + "\n\n## Small\n\nshort\n", encoding="utf-8"
    )
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[budgets]\n"agents.md" = { bytes = 900 }\n', encoding="utf-8"
    )
    (load,) = file_budget(Config.discover(tmp_path))
    # Largest first, which is the order a reader deciding what to cut reads in.
    assert [part.heading for part in load.parts][:2] == ["## Big", "## Small"]
    assert sum(part.bytes for part in load.parts) == load.costs[0].taken
    assert load.parts[0].bytes > load.parts[1].bytes


def test_the_breakdown_is_silent_where_it_would_be_the_total_twice(tmp_path):
    # One section is the whole file, so naming it is the number printed again.
    (tmp_path / "agents.md").write_text("just prose\n", encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[budgets]\n"agents.md" = { bytes = 900 }\n', encoding="utf-8"
    )
    (load,) = file_budget(Config.discover(tmp_path))
    assert len(load.parts) == 1


def test_a_file_that_is_not_there_has_nothing_to_attribute(tmp_path):
    # The state `lint` calls `budget.absent`: no content, so no breakdown — and never zeroes,
    # which would read as a file whose every section is empty.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[budgets]\n"gone.md" = { bytes = 900 }\n', encoding="utf-8"
    )
    (load,) = file_budget(Config.discover(tmp_path))
    assert not load.present and load.parts == ()


# -- both halves of what a session pays (RK1095) -------------------------------


def test_the_session_read_names_two_cadences_and_never_adds_them(tmp_path, capsys):
    """`--tools` totals the served schema and `--file` totals a resident file, and neither
    knew the other existed — so deciding between cutting a description and cutting a
    paragraph was two commands and a subtraction by hand.

    Two figures and never a sum: the schema is sent once at the handshake and a file is read
    on every turn, so adding them is a number wrong for every session with more than one
    turn, which is all of them.
    """
    _priced(tmp_path)
    (tmp_path / "agents.md").write_text("x" * 300 + "\n", encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        '[budgets]\n"agents.md" = { bytes = 900 }\n',
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["once"]["characters"] > 0
    assert payload["each_turn"]["files"][0]["path"] == "agents.md"
    # No total: a key holding the sum is the multiplier this read exists not to hide.
    assert "total" not in payload


def test_the_session_read_answers_a_project_with_no_budgeted_file(tmp_path, capsys):
    # `--file` raises here; this says the real answer, which is that the schema is the whole
    # of what such a session pays.
    _priced(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "declares no [budgets] file" in said and "once" in said


def test_the_session_read_is_a_subject_and_not_a_narrowing(tmp_path, capsys):
    # One answer per call (RK489): asked beside another subject it is refused, which is what
    # makes it a sixth subject rather than a flag on one of the two it reads.
    _priced(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session", "--tools"]) == EXIT_USAGE
    assert "one answer per call" in capsys.readouterr().err


# -- the fourth cadence: the write path, on the turns that load it (RK1424) --


def test_the_skill_is_priced_beside_the_surface_it_is_larger_than(tmp_path, capsys):
    """The largest single thing a session is handed was the one thing no read named.
    `[budgets]` prices what loads every turn and excludes this on purpose — pricing a
    trigger-loaded file as resident is the third figure `--session` exists to avoid inventing
    (RK23) — which settles the table it is not in and never said the number was not worth
    having. RK464's argument a third time, and RK30's before it: a file nobody counts is the
    one that reached 186 KB in the repository this tool was written after.

    Beside the served figure, because the comparison is the whole point: a reader handed
    65,180 alone has to run a second command to learn whether that is large.
    """
    from roadkeep.serving import surface

    _priced(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--skill", "--json"]) == EXIT_OK
    found = json.loads(capsys.readouterr().out)
    assert found["present"] and found["origin"] == "checkout"
    assert found["characters"] > 0
    # One measurement and two readers (RK1096), as `--session` totals what `--tools` ranks.
    assert found["schema"] == surface(Config.discover(tmp_path)).characters
    # And never a sum: two cadences, which is the arithmetic `--session` already refuses.
    assert "total" not in found


def test_the_skill_read_declares_no_ceiling(tmp_path, capsys):
    """`govern` refuses a limit this corpus already breaks, so declaring one here would be a
    number chosen before the reading that decides it. A `null` limit key would read as a
    ceiling this build failed to find rather than as one nobody has argued for, so there is
    no key: what this reports is what `weight` and `adopt` report."""
    _priced(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--skill", "--json"]) == EXIT_OK
    found = json.loads(capsys.readouterr().out)
    assert "limit" not in found
    assert not any("limit" in key for key in found)


def test_the_skill_read_says_where_the_size_went(tmp_path, capsys):
    """A total alone is a number with nowhere to act on it (RK1092), which is the argument
    `Part` already makes about a resident file. Measured on this checkout: one `##` section
    is two thirds of the file, which is the whole of what an author cutting it needs."""
    _priced(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--skill", "--json"]) == EXIT_OK
    found = json.loads(capsys.readouterr().out)
    assert len(found["sections"]) > 1
    counted = [one["characters"] for one in found["sections"]]
    assert counted == sorted(counted, reverse=True), "the largest section is not first"
    assert sum(one["bytes"] for one in found["sections"]) == found["bytes"]


def test_the_vendored_copy_is_the_one_a_session_loads(tmp_path, capsys):
    """Two copies can answer and the order is what a session actually reads: a project that
    ran `install` has the skill under `.claude/`, and that copy is the one its sessions get —
    stale or not, which is `install.stale`'s business and not this read's."""
    root = _priced(tmp_path)
    vendored = tmp_path / ".claude" / "skills" / "roadkeep" / "SKILL.md"
    vendored.parent.mkdir(parents=True, exist_ok=True)
    vendored.write_text("# roadkeep\n\n## A section\n\nProse.\n", encoding="utf-8")
    del root
    assert main(["-C", str(tmp_path), "cost", "--skill", "--json"]) == EXIT_OK
    found = json.loads(capsys.readouterr().out)
    assert found["origin"] == "project"
    assert found["path"] == ".claude/skills/roadkeep/SKILL.md"
    assert found["lines"] == 5


def test_a_project_with_neither_copy_says_so_and_names_the_read_that_answers(
    tmp_path, capsys, monkeypatch
):
    """A project using the plugin without vendoring has the file inside a cache this read does
    not resolve. Reported rather than guessed at: `engines` is the verb that reads the copies,
    and a number taken from the wrong one is worse than no number.

    The command it names is **run** and not matched, which is `tests/composing.py`'s whole
    reading: a message composing an argv nobody executes is a message that can name a verb
    this CLI does not parse.
    """
    import re
    import shlex

    from roadkeep import budgeting

    _priced(tmp_path)
    monkeypatch.setattr(
        budgeting, "skill_cost", lambda config: budgeting.Skilled(path="x", origin="")
    )
    assert main(["-C", str(tmp_path), "cost", "--skill"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "absent" in printed
    named = re.search(r"`([^`]+)`", printed)
    assert named, printed
    argv = shlex.split(named.group(1))[1:]  # the invocation is how it is reached, not a verb
    assert argv == ["engines"]
    assert main(["-C", str(tmp_path), *argv]) in (EXIT_OK, 1)
    assert "capture it before the session ends" not in capsys.readouterr().err


def test_the_skill_is_a_subject_and_not_a_narrowing(tmp_path, capsys):
    # One answer per call (RK489), as every other subject of this verb is: asked beside one
    # of them it is refused, and the bare form names all four cadences.
    _priced(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--skill", "--session"]) == EXIT_USAGE
    assert "one answer per call" in capsys.readouterr().err
    assert main(["-C", str(tmp_path), "cost"]) == EXIT_USAGE
    said = capsys.readouterr().err
    for subject in ("--tools", "--brief", "--session", "--skill"):
        assert subject in said, subject


# -- the fifth cadence: one refused write (RK1428) ----------------------------


def test_the_denial_is_priced_beside_the_notice_that_already_was(tmp_path, capsys):
    """`guarding.py` hands a session two texts and only the small one was measured. The
    notice is 305 against a declared 320 and `--session` prints it beside that ceiling; the
    denial — thirteen times larger on this repository — was priced by nothing, and it is the
    one paid per denial by a plugin whose whole purpose is to produce them.

    Both figures in one answer, because the finding *is* the pair: a reading that gave the
    denial alone would be the same number with the argument taken out of it.
    """
    _priced(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--deny", "--json"]) == EXIT_OK
    found = json.loads(capsys.readouterr().out)
    assert found["characters"] > found["notice"] > 0
    assert found["notice_limit"] == 320
    # No ceiling of its own, for `--skill`'s reason: `govern` refuses a limit this corpus
    # breaks, so one declared before the reading would be a number nobody argued for.
    assert "limit" not in found


def test_the_denial_is_measured_off_the_refusal_and_not_a_fixture(tmp_path, capsys):
    """`notice_budget`'s rule one message over: it is composed from `announce` so a sentence
    reworded there moves the figure. A fixture pasted into the reader would agree until
    somebody edits a door, which is the drift this package exists to refuse."""
    from roadkeep.budgeting import deny_cost
    from roadkeep.guarding import Refusal
    from roadkeep.kernel.schema import width

    _priced(tmp_path)
    config = Config.discover(tmp_path)
    found = deny_cost(config)
    composed = Refusal(
        tool="Edit",
        path=config.relative(config.path("roadmap")),
        role="roadmap",
    )
    assert found.bare == width(str(composed))
    # This fixture declares no server, so the two figures are one and the split is 0 — the
    # answer and not an absence: with no tool table above it the shell one is the only one.
    assert found.here == found.bare
    assert found.shell == 0

    # And the served branch, on the one project at hand that declares the server. The half a
    # caller addressed by its MCP names has already been given is reported and never judged
    # (RK447, RK448): it is inside the served figure, so it cannot exceed it.
    here = deny_cost(Config.discover(Path(__file__).resolve().parents[1]))
    assert here.here > here.bare
    assert 0 < here.shell < here.here


def test_the_denial_read_is_the_one_subject_the_surface_withholds(tmp_path, capsys):
    """Exposing it costs 102 characters against 19 of room under `[tools] session`, and a
    ceiling raised to admit the next subject is the reviewer's limit RK30 replaced. So it is
    withheld with `list --ids`' reason: the caller over that transport is handed the denial
    itself and can count what is in front of it."""
    from roadkeep import serving

    assert "deny" in serving.withheld()["cost"]
    assert "handed the denial itself" in serving.withheld()["cost"]["deny"]
    # And it is still a subject, so asking for it beside another is refused like the rest.
    _priced(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--deny", "--skill"]) == EXIT_USAGE
    assert "one answer per call" in capsys.readouterr().err


def test_the_two_surface_reads_share_one_measurement(tmp_path, capsys):
    """RK1096. `--tools` summed the descriptors and the handshake, `--session` summed the
    same two, and neither called the other — one arithmetic written twice, which agrees right
    up to the edit that moves one. The shape RK1073 closed for the provenance note and RK1080
    for the partial predicate, both found the same way.

    Asked of the two answers rather than of the function, because agreeing is what the
    duplicate did: what this holds is that they cannot come apart.
    """
    from roadkeep.serving import surface

    _priced(tmp_path)
    sent = surface(Config.discover(tmp_path))

    main(["-C", str(tmp_path), "cost", "--tools", "--json"])
    tools = json.loads(capsys.readouterr().out)
    main(["-C", str(tmp_path), "cost", "--session", "--json"])
    session = json.loads(capsys.readouterr().out)

    # The **schema** and not the cadence total: since RK1243 the once-per-session figure also
    # carries the `SessionStart` notice, which is a second thing paid at the same cadence and
    # not a second measurement of this one. What may not come apart is the shared half.
    assert tools["characters"] == session["once"]["schema"] == sent.characters
    assert sum(row["characters"] for row in tools["by_tool"]) == sent.listed
    assert tools["handshake"] == sent.handshake
    # And the total is the two, stated: a reader choosing what to cut is inside one budget.
    assert (
        session["once"]["characters"]
        == session["once"]["schema"] + session["once"]["notice"]
    )


def test_a_loads_bytes_are_its_own_arithmetic_and_not_a_readers(tmp_path):
    # `--session` walked `costs` for the unit it wanted, which is this record's arithmetic
    # performed by a reader — the shape RK345 removed from the two that count the file.
    (tmp_path / "agents.md").write_text("x" * 300 + "\n", encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[budgets]\n"agents.md" = { bytes = 900 }\n', encoding="utf-8"
    )
    (load,) = file_budget(Config.discover(tmp_path))
    assert load.bytes == next(c.taken for c in load.costs if c.unit == "bytes")

    # And zero rather than a raise where only lines were declared: a file with no byte
    # budget still costs bytes, and this answers what the *budget* holds.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[budgets]\n"agents.md" = { lines = 9 }\n', encoding="utf-8"
    )
    (lines_only,) = file_budget(Config.discover(tmp_path))
    assert lines_only.bytes == 0


# -- the draft, measured rather than refused (RK1190) --------------------------


def test_a_why_draft_is_measured_against_the_allowance_it_will_be_refused_by(tmp_path):
    """The defect. RK190 made the allowance knowable before the first word and left the draft
    unmeasurable, so the only thing that ever compared prose against its limit was the write
    that refused it — one retry per guess, each costing the whole field again."""
    config = project(tmp_path)
    allowed = budget(config, block="A").share("why").allowed

    fits = budget(config, block="A", why="x" * (allowed - 1))
    assert (fits.share("why").over, fits.share("why").left) == (0, 1)

    over = budget(config, block="A", why="x" * (allowed + 12))
    assert over.share("why").over == 12
    # And `left` still floors at zero, which is exactly why `over` had to exist: the deficit
    # was a subtraction between two numbers on one row.
    assert over.share("why").left == 0


def test_a_draft_is_named_as_one_and_never_as_prose_a_file_holds(tmp_path):
    """The same count means two things and only this says which: `153 written` about a
    paragraph that exists nowhere is a report about the wrong file."""
    config = project(tmp_path)
    assert budget(config, block="A", why="a draft").share("why").drafted
    assert not budget(config, "RK1").share("why").drafted
    # The symptom is the caller's on a line the roadmap does not hold, and the file's on one
    # it does — read off `open_line`, because that is the whole difference.
    assert budget(config, block="A", symptom="drafted").share("symptom").drafted
    assert not budget(config, "RK1").share("symptom").drafted


def test_nothing_is_composed_so_a_draft_twice_its_limit_is_a_number(tmp_path):
    """The whole verb, in one assertion. An `add` carrying this refuses; this answers."""
    config = project(tmp_path)
    answer = budget(config, block="A", why="word " * 400)
    assert answer.share("why").over > 0
    assert answer.task.why == ""


def test_an_empty_draft_is_not_the_absence_of_one(tmp_path):
    """`--why ""` asks what an empty field costs, which is a question; `None` is no question."""
    config = project(tmp_path)
    assert budget(config, block="A", why="").share("why").drafted
    assert not budget(config, block="A").share("why").drafted


def test_a_body_draft_is_measured_by_the_reader_that_measures_the_written_one(tmp_path):
    """A second counter that disagreed with the door by one would be worse than no read
    (RK136): a table row costs nothing here exactly as it costs nothing when it is written."""
    config = outlined_with_a_full_section(tmp_path)
    prose = "One two three four five."
    assert body_budget(config, "IX", body=prose).draft == 5
    # A table row is data and costs nothing here, exactly as it costs nothing written.
    assert body_budget(config, "IX", body=f"{prose}\n\n| a | b |\n").draft == 5


def test_a_body_draft_is_priced_against_what_a_replacement_may_say(tmp_path):
    """`allowed` and never `left` (RK1036): a written section's draft replaces its own prose,
    so pricing it against the room for *more* would refuse an amend as though it were an
    insert."""
    config = outlined_with_a_full_section(tmp_path)
    answer = body_budget(config, "IX", body="word " * 30)
    assert answer.written and answer.allowed == 30
    assert (answer.draft, answer.over) == (30, 0)

    tight = body_budget(config, "IX", body="word " * 33)
    assert tight.over == 3


def test_no_draft_leaves_every_answer_exactly_as_it_was(tmp_path):
    """The argument is additive or it is a second reading of a number four verbs already
    print: `brief` hands over this record and asked for no draft."""
    config = project(tmp_path)
    assert budget(config, "RK1").payload() == budget(config, "RK1", why=None).payload()
    (tmp_path / "outline").mkdir()
    outlined = outlined_with_a_full_section(tmp_path / "outline")
    assert body_budget(outlined, "IX").draft is None
    assert body_budget(outlined, "IX").over == 0


def test_the_call_exits_non_zero_where_the_draft_does_not_fit(tmp_path, capsys):
    """The one bit the caller asked for, as an exit code rather than as prose to parse — and
    `isError` over MCP, where the refusal it replaces costs the whole payload again.

    And it closes on that (RK1422). `cli.GATE_VERDICTS` names this exit as an answer, and its
    own comment says the behaviour is held per verb rather than by the census — so the
    address it names is here, and until now the claim was the only thing at it.
    """
    root = str(tmp_path)
    project(tmp_path)
    assert main(["-C", root, "budget", "--block", "A", "--why", "short"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", root, "budget", "--block", "A", "--why", "x" * 400]) == EXIT_GATE
    printed = capsys.readouterr()
    assert "over" in printed.out
    assert "capture it before the session ends" not in printed.err

    (tmp_path / "outline").mkdir()
    outlined_with_a_full_section(tmp_path / "outline")
    where = str(tmp_path / "outline")
    assert main(["-C", where, "budget", "--anchor", "IX", "--body", "w " * 400]) == EXIT_GATE
    printed = capsys.readouterr()
    assert "over" in printed.out
    assert "capture it before the session ends" not in printed.err


def test_a_line_the_file_holds_over_its_own_limit_is_the_gate_s_and_not_this_verb_s(tmp_path):
    """The narrowing that keeps this a read: exit 1 is about a draft this call was handed, so
    `budget <id>` still describes a file rather than passing a verdict on it."""
    config = project(tmp_path)
    long_why = "x" * (budget(config, "RK1").share("why").allowed + 40)
    roadmap = config.path("roadmap")
    roadmap.write_text(
        roadmap.read_text(encoding="utf-8").replace("Because of a reason.", long_why),
        encoding="utf-8",
    )
    assert budget(Config.discover(tmp_path), "RK1").share("why").over == 40
    assert main(["-C", str(tmp_path), "budget", "RK1"]) == EXIT_OK


def test_the_served_draft_publishes_no_ceiling_that_would_refuse_it(tmp_path):
    """The defect this task would otherwise have shipped: naming the dest `why` inherited
    `maxLength`, so the client would refuse exactly the overrun the read exists to report —
    the refusal-before-the-answer arriving one layer out, from this server's own schema."""
    from roadkeep.serving import TOOLS, descriptor

    config = project(tmp_path)
    (tool,) = [one for one in TOOLS if one.name == "budget"]
    fields = descriptor(tool, config)["inputSchema"]["properties"]
    assert "maxLength" not in fields["why"]
    assert "maxLength" not in fields["symptom"]
    # And the write still publishes one, which is what makes the absence a decision.
    (writing,) = [one for one in TOOLS if one.name == "add"]
    assert "maxLength" in descriptor(writing, config)["inputSchema"]["properties"]["why"]


# -- the flags one arm of a two-arm read never looked at (RK1221) --------------


def test_a_field_the_caller_states_wins_over_the_line_on_file(tmp_path):
    """`_subject` has two arms. With an id the roadmap holds it returned that entry's task, so
    `--block`, `--dep`, `--marker` and `--symptom` were read and discarded: `budget RK1
    --symptom "<a rewrite I am weighing>"` answered about the symptom already on the line and
    said so nowhere.

    RK465 named the shape — a narrowing flag nobody reads is worse than a refused one, because
    the caller reads a number believing it narrowed it — and RK1190 sharpened it: `--symptom`
    is a draft to *measure*, which is exactly what an author weighing an `amend` passes.
    """
    config = project(tmp_path)
    held = budget(config, "RK1")
    # A symptom of the caller's, and the `why` allowance moves with it: what the symptom takes
    # is what the why loses, which is the whole reason the flag is worth honouring here.
    # Long enough that the *line* binds the why rather than its own maximum, which is the
    # interaction being asserted: a short symptom moves `taken` and leaves `allowed` at 200.
    theirs = budget(config, "RK1", symptom="A" * config.schema.symptom_max)
    assert theirs.share("symptom").taken > held.share("symptom").taken
    # And the `why` allowance moves with it, which is the whole reason the flag is worth
    # honouring here rather than merely refusing: what the symptom takes is what the why loses.
    assert theirs.share("why").allowed < held.share("why").allowed


def test_all_four_are_honoured_because_all_four_move_the_number(tmp_path):
    """One flag taken and the others ignored would make four flags mean two things — which is
    the caveat this task's own design ends on."""
    config = project(tmp_path)
    held = budget(config, "RK1")
    # The deps group is part of the line, so it moves what the prose has between the two of
    # them, exactly as it does on the arm that composes a new line.
    assert budget(config, "RK1", deps=["RK2", "RK4"]).prose < held.prose


def test_what_came_from_the_caller_is_named_and_what_matched_the_file_is_not(tmp_path):
    """The half a silent override would still be missing: a caller who passed `--symptom` and
    reads an allowance has to see that it was theirs, and one whose flag matched the file
    changed nothing and should not be told they did."""
    config = project(tmp_path)
    assert budget(config, "RK1").stated == ()
    assert budget(config, "RK1", symptom="A different one").stated == ("--symptom",)

    # Identical to what the line already says: nothing was overridden, so nothing is claimed.
    same = config.document("roadmap").by_id()["RK1"].task.symptom
    assert budget(config, "RK1", symptom=same).stated == ()


def test_a_read_of_the_line_as_it_stands_is_untouched(tmp_path):
    """Every call before this one, and the one `brief` makes: no field of the caller's, so the
    entry's own task comes back uncomposed and the answer is what it always was."""
    config = project(tmp_path)
    plain = budget(config, "RK1")
    assert plain.stated == ()
    assert plain.task == config.document("roadmap").by_id()["RK1"].task


def test_the_row_says_which_line_the_number_is_about(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK1", "--symptom", "Short"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "yours      --symptom" in out
    assert "an `amend` carrying them would write" in out

    assert main(["-C", str(tmp_path), "budget", "RK1", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["stated"] == []


# -- one call for a transaction that is validated as one (RK1224) --------------


def with_prose(tmp_path: Path) -> Config:
    """A project that declares a prose file, which is what makes a section row exist at all.

    `project` above declares a roadmap and a ledger, so `Budget.section` is `None` there and a
    draft body has nothing to be measured against — the state RK303 reports as an absence
    rather than a zero.
    """
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    (tmp_path / "IMPROVEMENTS.md").write_text(
        "# Improvements\n\n## Block A — The model\n", encoding="utf-8"
    )
    return Config.discover(tmp_path)


def test_one_call_prices_the_line_and_the_body_add_writes_together(tmp_path):
    """Filing one Shio task took four calls: one refused for a missing `ref`, then three for
    `why` — 176, 171 and 170 characters against 167. Each refusal was correct, each named the
    exact overflow, and each threw away the 250-word `--section-body` beside it.

    The field that failed was **three characters** too long and the payload re-sent to fix it
    was two orders of magnitude larger. The all-or-nothing transaction is right and is not what
    changes; what was missing is a way to price both halves at once.
    """
    config = with_prose(tmp_path)
    answer = budget(
        config, block="A", symptom="A symptom", why="Because.", body="word " * 300
    )
    # The line's own fields, and the body of the section its pointer names (RK301).
    assert answer.share("why").drafted
    assert answer.section is not None and answer.section.draft == 300
    assert answer.section.over > 0


def test_the_exit_speaks_for_both_halves(tmp_path, capsys):
    """A body three words over is a call the `add` refuses whole, so an exit that spoke only
    for the line would answer a question narrower than the one being asked."""
    root = str(tmp_path)
    with_prose(tmp_path)
    fits = ["-C", root, "budget", "--block", "A", "--why", "Short.", "--body", "A body."]
    assert main(fits) == EXIT_OK
    capsys.readouterr()

    over = [*fits[:-1], " ".join(["word"] * 400)]
    assert main(over) == EXIT_GATE
    assert "over" in capsys.readouterr().out


def test_the_body_no_longer_needs_an_anchor_to_be_measured_against(tmp_path, capsys):
    """The last thing standing between this verb and one call for a whole `add --section`: the
    line subject already reports the section its pointer names, so a draft handed to it has
    somewhere to be measured."""
    root = str(tmp_path)
    with_prose(tmp_path)
    assert main(["-C", root, "budget", "--block", "A", "--body", "A body."]) == EXIT_OK
    assert "draft" in capsys.readouterr().out


def test_a_subject_with_no_section_still_refuses_a_draft_body(tmp_path, capsys):
    """RK465's rule kept where it applies: a draft measured against nothing is a number the
    caller misreads, and `--file` prices an every-turn file rather than any prose."""
    root = str(tmp_path)
    with_prose(tmp_path)
    (tmp_path / "agents.md").write_text("x\n", encoding="utf-8")
    assert main(["-C", root, "budget", "--file", "agents.md", "--body", "A body."]) != EXIT_OK


def test_a_body_and_a_path_are_still_two_answers_to_one_question(tmp_path, capsys):
    """Unchanged by the widening: `--body` and `--body-file` are two sources for one draft, and
    honouring either silently is how a caller comes to believe the file is what was measured."""
    root = str(tmp_path)
    with_prose(tmp_path)
    argv = ["-C", root, "budget", "--block", "A", "--body", "A body.", "--body-file", "x.md"]
    assert main(argv) == EXIT_USAGE
    assert "two answers to one question" in capsys.readouterr().err


# -- the group the price was never told about (RK1461) -------------------------


#: The vocabulary a `(requires: …)` group may quote from — declared, because a requirement
#: nothing states is a word the write refuses (RK1297).
REQUIRING = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    '[requirements]\ndeclared = ["upstream", "sandbox"]\n'
)


def _requiring(tmp_path: Path) -> Config:
    (tmp_path / "roadkeep.toml").write_text(REQUIRING, encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    return Config.discover(tmp_path)


def test_the_group_the_write_adds_is_taken_off_the_price(tmp_path):
    """RK1461. `add --requires <word>` puts `(requires: <word>)` on the line and this read had
    no way to be told it was coming. The gap is exact: a sentence priced at `165 of 200` was
    refused at `158 characters, limit is 144` by the `add` that carried one — 21 apart, which
    is the width of `(requires: upstream) `."""
    config = _requiring(tmp_path)
    bare = budget(config, block="A")
    carried = budget(config, block="A", requires=["upstream"])

    assert bare.prose - carried.prose == len("(requires: upstream) ")
    # And the structure is what moved, not the field: the limit is untouched and the room is not.
    assert carried.share("why").allowed <= bare.share("why").allowed


def test_the_number_is_the_one_the_add_then_enforces(tmp_path, capsys):
    # The prediction and the refusal, asked of one line with nothing between them changing it,
    # which is the only thing that can hold a pre-write number honest (RK1199's shape).
    from roadkeep.verbs.refusing import EXIT_USAGE as REFUSED

    config = _requiring(tmp_path)
    root = str(tmp_path)
    left = budget(config, block="A", requires=["upstream"]).share("why").left
    common = [
        "-C", root, "add", "--block", "A", "--requires", "upstream",
        "--symptom", "A third symptom",
    ]
    assert main([*common, "--why", "x" * (left + 1) + "."]) == REFUSED
    capsys.readouterr()
    assert main([*common, "--why", "x" * (left - 1) + "."]) == EXIT_OK


def test_two_requirements_cost_more_than_one(tmp_path):
    """Repeatable for `--dep`'s reason: two of them cost two words and a separator, so a flag
    taking one would answer the common case and quietly mis-price the rest — which is the
    failure being removed rather than a smaller version of it."""
    config = _requiring(tmp_path)

    one = budget(config, block="A", requires=["upstream"]).prose
    two = budget(config, block="A", requires=["upstream", "sandbox"]).prose
    assert two < one


def test_the_flag_is_named_where_it_was_the_caller_s(tmp_path, capsys):
    # `--dep`'s rule, one group over (RK1221): a caller who passed it and reads a number has to
    # see that the number was theirs, and one whose flag matched the file changed nothing.
    config = _requiring(tmp_path)
    assert budget(config, "RK1", requires=["upstream"]).stated == ("--requires",)
    assert budget(config, "RK1").stated == ()


# -- the argument that did not survive into the write (RK1459) -----------------


def test_the_price_and_the_write_take_the_same_argument(tmp_path, capsys):
    """RK1459. `budget` is the read this tool asks callers to make before a write, and the
    write it prices did not take the argument it took: pricing a design is `budget <id>
    --body-file <p>` and filing it with the line is `add … --section-body-file <p>`. Same path,
    same content, and a caller moving from the price to the write in one step was refused by
    the parser for the name it had been told to use one call earlier.

    An alias and not a rename: both names are right where they are — `section add` writes only
    a body, and `add` writes a body as one of two — and this verb is the one asked about both
    subjects."""
    root = str(tmp_path)
    with_prose(tmp_path)
    draft = tmp_path / "draft.md"
    draft.write_text("The reasoning the line has no room for.\n", encoding="utf-8")

    assert main(["-C", root, "budget", "--block", "A", "--section-body", "A body."]) == EXIT_OK
    took = capsys.readouterr().out
    assert main(["-C", root, "budget", "--block", "A", "--body", "A body."]) == EXIT_OK
    assert capsys.readouterr().out == took, "one argument, two spellings, one answer"

    assert main([
        "-C", root, "budget", "--block", "A", "--section-body-file", str(draft)
    ]) == EXIT_OK
    by_path = capsys.readouterr().out
    assert main(["-C", root, "budget", "--block", "A", "--body-file", str(draft)]) == EXIT_OK
    assert capsys.readouterr().out == by_path


def test_the_alias_is_printed_where_a_caller_would_look(tmp_path, capsys):
    # An alias that is never printed is one nobody finds. argparse lists both spellings on the
    # option itself, so neither `help` restates it and neither pays for it over a transport
    # where no flag is ever typed.
    with_prose(tmp_path)
    with pytest.raises(SystemExit):
        main(["-C", str(tmp_path), "budget", "--help"])
    said = capsys.readouterr().out
    assert "--body, --section-body" in said
    assert "--body-file, --section-body-file" in said


def test_the_served_surface_publishes_one_spelling(tmp_path):
    # The first option string is what the schema names, so an alias costs the session nothing:
    # a caller on that transport passes a property and never a flag.
    from roadkeep.serving import handle

    with_prose(tmp_path)
    answered = handle(
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"}, str(tmp_path)
    )
    (priced,) = [
        one for one in answered["result"]["tools"] if one["name"] == "budget"
    ]
    fields = priced["inputSchema"]["properties"]
    assert "body" in fields and "section_body" not in fields


# -- the rules that are not widths (RK1225) ------------------------------------


def test_the_rule_the_gate_enforces_is_published_with_the_widths(tmp_path):
    """`budget` answered width — characters left in a field, room on the line, words under an
    anchor — and said nothing about how many sentences the field accepts. `why` accepts one.

    So a caller could compose a `why` that fits every number published and still be refused by
    `why.sentences`, which is the verb whose entire purpose is to say so costing a composition
    anyway. Observed shipping a partial whose outcome needed two clauses.
    """
    config = project(tmp_path)
    share = budget(config, block="A").share("why")
    assert share.sentences == 1
    assert share.terminated
    assert share.bounded == "1 sentence, ending in a stop"


def test_the_rule_is_read_off_the_schema_and_not_stated_here(tmp_path):
    """Per role, because `[rules.<role>]` switches both — a ledger written before the tool is
    history, and a rule cannot be obeyed retroactively. `0` is *unbounded* and not *one*."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        "[rules.roadmap]\none_sentence = false\nterminator = false\n",
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(LEDGER, encoding="utf-8")
    share = budget(Config.discover(tmp_path), block="A").share("why")
    assert share.sentences == 0 and not share.terminated
    assert share.bounded == ""


def test_what_the_budget_publishes_is_what_the_write_refuses(tmp_path, capsys):
    """The claim worth holding: the published rule and the enforced one are one rule. A `why`
    of two sentences that fits every width is refused, and the read said so first."""
    root = str(tmp_path)
    project(tmp_path)
    assert main(["-C", root, "budget", "--block", "A"]) == EXIT_OK
    assert "1 sentence, ending in a stop" in capsys.readouterr().out

    # Two sentences, comfortably inside every number that read published.
    assert main([
        "-C", root, "add", "--block", "A",
        "--symptom", "A symptom plainly long enough to read",
        "--why", "One thing. And another.",
    ]) == EXIT_USAGE
    assert "why.sentences" in capsys.readouterr().err


def test_the_payload_carries_the_rules_beside_the_numbers(tmp_path, capsys):
    root = str(tmp_path)
    project(tmp_path)
    assert main(["-C", root, "budget", "--block", "A", "--json"]) == EXIT_OK
    fields = {one["field"]: one for one in json.loads(capsys.readouterr().out)["fields"]}
    assert fields["why"]["sentences"] == 1
    assert fields["why"]["terminated"] is True


# -- and which of that tool's fields spent it (RK1236) ------------------------


def test_the_tool_that_is_over_names_the_field_that_spent_the_bytes(tmp_path, capsys):
    """The ranking answers *which tool is over*, which is never the question a caller has at
    that moment — `lint` already named the tool.

    Measured twice in one block: RK1190 put `budget` at 2637 against 2600 and RK1233 put
    `ship` at 2659, and both times the answer came from a throwaway script that serialised
    each property and sorted by length. The first repair guessed the argument just added,
    which was the smallest of six, and the ceiling was still crossed.
    """
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "ship"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert printed.startswith("ship ")
    # Every field it publishes has a row, and the description has one too — a cost with no
    # argument to name it is still a cost.
    assert "why" in printed and "(description)" in printed


def test_the_rows_are_largest_first_and_in_the_units_the_gate_counts(tmp_path, capsys):
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "ship", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    sizes = [row["characters"] for row in payload["by_field"]]
    assert sizes == sorted(sizes, reverse=True)
    assert payload["unit"] == "utf-16-code-units"
    # The same number the ranking prints for this tool, because both come off `descriptor`.
    assert main(["-C", str(tmp_path), "cost", "--tools", "--json"]) == EXIT_OK
    ranked = json.loads(capsys.readouterr().out)
    (row,) = [one for one in ranked["by_tool"] if one["name"] == "ship"]
    assert row["characters"] == payload["characters"]


def test_the_parts_do_not_sum_to_the_total_and_the_difference_is_named(tmp_path, capsys):
    """Deliberate and visible: a descriptor is JSON, so its name, its keys, its `required`
    list and its brackets are bytes no argument spent. A breakdown that quietly balanced
    would have assigned structure to whichever field rounded best."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "ship", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    fields = sum(row["characters"] for row in payload["by_field"])
    assert payload["envelope"] == payload["characters"] - fields
    assert payload["envelope"] > 0


def test_the_row_names_the_file_the_help_string_is_edited_in(tmp_path, capsys):
    """The address RK1192 found actionable, and the one argparse cannot give: an action
    records no source location, so what is resolvable is the module the handler was defined
    in — which is the module its parser is built in."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "ship", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["declared_in"].endswith("verbs/shipping.py")


def test_the_room_is_stated_against_the_ceiling_that_refuses(tmp_path, capsys):
    """`[tools] characters` is what `lint` holds a tool to, so the read that aims the next
    cut states the same number — the pairing RK345 makes everywhere else."""
    budgeted(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
        + "\n[tools]\ncharacters = 4000\n",
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "cost", "--tools", "ship"]) == EXIT_OK
    assert "of 4000" in capsys.readouterr().out


def test_a_name_no_tool_answers_to_is_refused_and_says_where_the_names_are(tmp_path, capsys):
    from composing import runs

    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "shipp"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "not a tool this project serves" in said
    # Executed as printed (RK1209): the ranking it sends the caller to is accepted, which is
    # what makes it a door rather than a sentence.
    assert runs(tmp_path, said) == (["cost", "--tools"],)


def test_bare_is_still_the_ranking_over_every_tool(tmp_path, capsys):
    """The empty string is what a value-taking flag makes of a bare one, and it is a subject
    that was asked for — the reading `--file` already has one subject over."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools"]) == EXIT_OK
    assert "tool(s) and the handshake" in capsys.readouterr().out


# -- and the seam inside the largest row (RK1239) -----------------------------


def test_the_description_row_says_which_of_its_parts_to_shorten(tmp_path, capsys):
    """A tool's description is not one string: `_description` takes the subparser's own
    sentence and appends one per always-passed flag, built from that flag's `help`. So an
    author shortening the `description=` in front of them cuts a fraction of what the row
    measured, because the rest is written in another file.

    Measured here: 725 of `merge_check`'s 871, and 427 of `claim`'s 949 — the largest row
    either tool has, and the one a reader could not act on."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "merge_check"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "(description)" in printed
    # Named by the flag: what a caller needs is which text to open, and `--check`'s sentence
    # is edited where `--check` is declared.
    assert "from description" in printed and "from --check" in printed


def test_the_parts_sum_to_the_sentence_and_not_to_the_serialised_row(tmp_path, capsys):
    """The row measures the property as it is sent — key, quotes and escaping — and the parts
    measure the clauses as they are written. Stated rather than reconciled, because a
    breakdown that quietly balanced would be one that had assigned punctuation to a clause."""
    from roadkeep.kernel.schema import width
    from roadkeep.serving import TOOLS, _described, _parsers, _subparser

    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "merge_check", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    parsers = _parsers()
    (tool,) = [one for one in TOOLS if one.name == "merge_check"]
    written = _described(tool, _subparser(tool.command, parsers))
    assert [one["source"] for one in payload["description_from"]] == [
        source for source, _text in written
    ]
    assert sum(one["characters"] for one in payload["description_from"]) == sum(
        width(text) for _source, text in written
    )


def test_a_description_that_is_one_sentence_has_nothing_to_split(tmp_path, capsys):
    """The rule `_print_parts` already keeps one read over: a single-part breakdown is the
    row's own total printed twice."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "ship", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["description_from"] == []
    assert main(["-C", str(tmp_path), "cost", "--tools", "ship"]) == EXIT_OK
    assert "from description" not in capsys.readouterr().out


def test_the_split_is_what_the_client_is_actually_sent(tmp_path, capsys):
    """Derived and never a second estimate, which is `descriptors`' own rule: the join of the
    parts *is* the description a client receives, so a clause reworded moves both."""
    from roadkeep.config import Config
    from roadkeep.serving import TOOLS, _description, _parsers, _subparser, descriptor

    config = budgeted(tmp_path)
    parsers = _parsers()
    (tool,) = [one for one in TOOLS if one.name == "merge_check"]
    parser = _subparser(tool.command, parsers)
    assert descriptor(tool, config, parsers)["description"] == _description(tool, parser)


# -- the envelope inside the envelope (RK1241) --------------------------------


def test_the_split_names_what_its_clauses_do_not_account_for(tmp_path, capsys):
    """RK1236 named the difference between a tool's total and the sum of its fields, on the
    argument that a breakdown which quietly balanced would have assigned structure to
    whichever field rounded best. RK1239 then split the description and left 725 over 576 and
    129 for the reader to notice — the docstring said so, and the report is what a reader is
    looking at while subtracting."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "merge_check"]) == EXIT_OK
    assert "its key, quoting, and the space between" in capsys.readouterr().out


def test_both_levels_balance_exactly(tmp_path, capsys):
    """Which is the whole claim: an accounting honest at the top and silent underneath
    teaches a reader to distrust both."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "merge_check", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    fields = sum(one["characters"] for one in payload["by_field"])
    assert fields + payload["envelope"] == payload["characters"]
    (row,) = [one for one in payload["by_field"] if one["field"] == "(description)"]
    clauses = sum(one["characters"] for one in payload["description_from"])
    assert clauses + payload["description_quoting"] == row["characters"]


def test_a_row_with_nothing_to_split_reports_no_inner_envelope(tmp_path, capsys):
    """Zero where `description_from` is empty, and no row: a description that is the parser's
    own sentence has no seam, so naming what it does not account for would be naming the
    serialisation of a row already printed."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--tools", "ship", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["description_quoting"] == 0
    assert main(["-C", str(tmp_path), "cost", "--tools", "ship"]) == EXIT_OK
    assert "its key, quoting" not in capsys.readouterr().out


# -- the third thing a session pays for (RK1243) ------------------------------


def test_the_session_start_line_is_priced_beside_the_schema(tmp_path, capsys):
    """`--tools` prices the schema and `--file` the resident files. The notice is resident
    too — one line handed to every session in every governed project — and had a ceiling no
    command could ask about: a constant in `guarding.py` a test asserted a fixture against.

    RK1242 raised that constant by 23% to fit a clause, which is a change to what every
    adopting session pays, made by editing a literal. RK30's own argument one surface over:
    a limit nobody counts is a limit that moves."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "the session-start notice" in printed
    # Beside the room, which is RK345's pairing everywhere else: a limit that reaches an
    # author only as a refusal is the verdict-after-the-prose this project exists to replace.
    assert "of 320" in printed


def test_the_schema_row_names_the_ceiling_the_gate_refuses_it_against(tmp_path, capsys):
    """RK1333. The two rows print at one cadence and only one of them was measured: the
    notice derived `+15 of 320` while the schema printed 64679 and stopped, though
    `[tools] session` declares the ceiling and `budget.session` is the single finding that
    refuses the total against it. Measured at 21 characters of room — the next sentence added
    to any one of 66 tool descriptions — so the reader most likely to run this verb was the
    one it answered least.

    Both registers, because a consumer reading `schema` to decide whether a description may
    grow had the same nothing to measure it against."""
    budgeted(tmp_path)
    toml = tmp_path / "roadkeep.toml"
    toml.write_text(
        # Both keys, the table refusing to hold nobody to anything.
        toml.read_text(encoding="utf-8") + "[tools]\ncharacters = 3000\nsession = 9000\n",
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "of 9000" in printed
    # The pairing is one spelling and not two, which is the shape of the defect: a second
    # copy is what let one row keep a pairing the other never grew.
    assert printed.count(" of ") >= 2

    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    once = json.loads(capsys.readouterr().out)["once"]
    assert once["schema_limit"] == 9000
    # A project declaring no ceiling stays silent rather than inventing one.
    (tmp_path / "bare").mkdir()
    budgeted(tmp_path / "bare")
    assert main(["-C", str(tmp_path / "bare"), "cost", "--session", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["once"]["schema_limit"] is None


def test_the_schema_row_reconciles_without_the_row_under_it(tmp_path, capsys):
    """RK1423. The row printed `64249 … +116 of 64300` on this repository, and those three
    numbers are about two totals: 65 of the 64249 names the checkout, no ceiling is about it,
    and the room is 64300 less the 64184 held. A reader subtracting the two numbers on the
    line got 51 — under half the truth, on the read whose whole purpose is deciding whether
    another tool fits.

    Held as arithmetic on the row itself rather than as a phrase, which is what makes it a
    property and not a spelling: the room is the ceiling less a figure the line names, and
    that stays true through any rewording of it.
    """
    import re

    budgeted(tmp_path)
    toml = tmp_path / "roadkeep.toml"
    toml.write_text(
        toml.read_text(encoding="utf-8") + "[tools]\ncharacters = 3000\nsession = 9000\n",
        encoding="utf-8",
    )
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    printed = capsys.readouterr().out
    row = next(line for line in printed.splitlines() if "tool(s) and the handshake" in line)
    numbers = [int(one) for one in re.findall(r"-?\d+", row)]
    room = next(int(one) for one in re.findall(r"([+-]\d+) of ", row))
    assert 9000 - room in numbers, f"the room is measured on a figure this row never names: {row}"

    # And the row below still says where the rest of the total went, which is the half that
    # was already right: the two figures differ by exactly what names the checkout.
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    once = json.loads(capsys.readouterr().out)["once"]
    assert once["schema"] - once["schema_provenance"] == once["schema_held"] == 9000 - room


def test_the_notice_shares_the_cadence_and_so_is_added(tmp_path, capsys):
    """The rule this record keeps is that two *cadences* may not be summed. The schema and
    the notice share one, so a reader deciding whether to cut a tool description or a
    sentence of the notice is deciding inside one budget."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    once = json.loads(capsys.readouterr().out)["once"]
    assert once["characters"] == once["schema"] + once["notice"]
    assert once["notice"] > 0 and once["notice_limit"] == 320
    # And never added to the other cadence, which is what RK1095 refused.
    assert "total" not in once


def test_it_is_the_line_this_project_actually_gets(tmp_path, capsys):
    """Measured off `announce` and never re-composed, which is `surface`'s rule: a sentence
    reworded in `guarding.py` moves the figure, and this project's own paths are in it."""
    from dataclasses import replace as _replace

    from roadkeep.guarding import announce
    from roadkeep.kernel.schema import width

    config = budgeted(tmp_path)
    said = announce({"cwd": str(config.root)}, config.root)
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["once"]["notice"] == width(
        str(_replace(said, stale=()))
    )


def test_the_drift_sentence_is_not_priced_as_resident(tmp_path, capsys):
    """RK234's sentence is deliberately over the ceiling and is not resident: it appears only
    while a vendored copy has drifted and goes away with one `install`. What is priced is
    what every session pays."""
    from roadkeep.guarding import Notice
    from roadkeep.kernel.schema import width

    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    priced = json.loads(capsys.readouterr().out)["once"]["notice"]
    drifted = width(str(Notice(files=("ROADMAP.md",), stale=(".claude/skills/roadkeep",))))
    assert priced < drifted


def test_the_ceiling_and_the_read_count_the_same_way(tmp_path):
    """A read and a gate measuring one line two ways disagree on exactly the line carrying a
    character outside the BMP — which is the marker this tool writes (RK430)."""
    from roadkeep.budgeting import notice_budget
    from roadkeep.guarding import _NOTICE_BUDGET

    config = budgeted(tmp_path)
    measured, limit = notice_budget(config)
    assert limit == _NOTICE_BUDGET
    assert measured <= limit


def test_a_project_this_cannot_announce_for_pays_nothing(tmp_path):
    """A real answer rather than a missing row, which is the same choice `--session` makes
    about a project declaring no `[budgets]` file."""
    from roadkeep.budgeting import notice_budget
    from roadkeep.config import Config

    assert notice_budget(Config.default(tmp_path)) == (0, None)


# -- one comparison, one unit (RK1245) ----------------------------------------


#: The same, in two `##` sections — what the per-section breakdown needs, since a file with
#: one section has its total printed twice and no breakdown at all.
SECTIONED = (
    "# Guide\n\n## First\n\n"
    + "📋 designed, 💭 idea, ⏳ partial\n" * 3
    + "\n## Second\n\n"
    + "🛠 in progress, ✅ shipped\n" * 2
)

#: A paragraph carrying the status markers this tool writes, which is where the two units
#: come apart: each marker is one code point outside the BMP — four bytes, two code units.
MARKED = "# Guide\n\n" + ("📋 designed, 💭 idea, ⏳ partial, 🛠 in progress, ✅ shipped\n" * 4)


def test_both_cadences_are_reported_in_one_unit(tmp_path, capsys):
    """The whole purpose of this read is a comparison — cut a tool description, or cut a
    paragraph — and until now it asked the reader to make it across two units.

    The split was defensible while the two cadences were also two kinds of thing: a JSON
    payload a client validates, and a file on disk. RK1243's notice broke that, being a
    message handed to a session exactly as `agents.md` is."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["once"]["unit"] == payload["each_turn"]["unit"] == "utf-16-code-units"


def test_the_gate_still_reads_bytes_and_the_report_says_so(tmp_path, capsys):
    """Stated and never converted: `[budgets]` declares bytes and `lint` refuses on them, for
    the reason `spent` gives — a budget is what a *loader* pays, and an instruction file is
    not a format this tool decodes (L4). Two honest readings of one set of files, so the
    report can be compared without the gate being moved."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text(MARKED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)["each_turn"]
    # On this prose they differ, which is the case the whole task is about.
    assert payload["bytes"] > payload["characters"]
    assert payload["bytes"] == sum(one["bytes"] for one in payload["files"])
    assert payload["characters"] == sum(one["characters"] for one in payload["files"])


def test_the_loaders_unit_is_named_once_and_not_per_row(tmp_path, capsys):
    """One fact about the set. Repeating it beside each file would spend the report on the
    difference rather than on the comparison the reader came for."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text(MARKED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert printed.count("the unit `[budgets]` counts") == 1


def test_it_says_nothing_where_the_two_agree(tmp_path, capsys):
    """Which is every ASCII project, and is where there is nothing to say."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text("# Guide\n\nPlain prose, no markers.\n", encoding="utf-8")
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    assert "the unit `[budgets]` counts" not in capsys.readouterr().out


def test_a_file_that_does_not_decode_falls_back_to_its_bytes(tmp_path, capsys):
    """`None` and never a guess: a file this cannot decode is one where *what does a reader
    pay for it* has no answer here, and its bytes alone are the honest row. Nothing is
    refused either way — the gate reads bytes and is untouched."""
    from roadkeep.budgeting import file_budget

    config = budgeted(tmp_path)
    (tmp_path / "agents.md").write_bytes(b"# Guide\n\n\xff\xfe not utf-8 at all\n")
    (load,) = [one for one in file_budget(config) if one.path == "agents.md"]
    assert load.characters is None
    assert load.bytes > 0
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    assert "this file is not UTF-8" in capsys.readouterr().out


def test_the_reading_is_of_the_same_normalised_bytes_the_total_is(tmp_path):
    """RK1105's convention, kept: a figure counted off the checkout's own terminator would
    disagree with the number printed beside it on exactly the machines a budget is about."""
    from roadkeep.budgeting import file_budget

    config = budgeted(tmp_path)
    (tmp_path / "agents.md").write_bytes(b"# Guide\r\n\r\nTwo lines.\r\n")
    (load,) = [one for one in file_budget(config) if one.path == "agents.md"]
    assert load.characters == len("# Guide\n\nTwo lines.\n")
    assert load.translated == 3


# -- and the room the project's own line declares (RK1248) --------------------


def test_a_resident_file_states_what_its_own_budget_has_left(tmp_path, capsys):
    """RK1243 gave the notice row a room clause because it had one number to compare against,
    and nobody looked up: the rows above it are the ones whose ceiling the *project* wrote and
    `lint` refuses on, and they printed a bare figure.

    RK345's argument runs the other way — a limit that reaches an author only as a refusal is
    the verdict-after-the-prose this project exists to replace."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "agents.md" in printed
    assert "left of" in printed


def test_the_unit_of_the_room_is_named_because_the_figure_is_not_in_it(tmp_path, capsys):
    """RK1245's lesson kept: the row's number is code units and the limit is the project's own
    unit, so the clause says which — mixing them silently is what that task removed."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    (row,) = [
        one for one in capsys.readouterr().out.splitlines() if "agents.md" in one
    ]
    assert "lines left of" in row or "bytes left of" in row


def test_the_tightest_limit_is_the_one_named(tmp_path, capsys):
    """Tightest measured as the share taken, not the count left: a file 21 lines and 1494
    bytes from its ceilings is nearer the first, and the one that refuses is the one to name.
    """
    from roadkeep.budgeting import file_budget

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
        '[budgets]\n"agents.md" = { lines = 10, bytes = 100000 }\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "agents.md").write_text("x\n" * 9, encoding="utf-8")
    config = Config.discover(tmp_path)
    (load,) = file_budget(config)
    # 9 of 10 lines against 18 of 100000 bytes: lines is what refuses, and it is what is said.
    assert load.tightest.unit == "lines"
    assert load.room == "1 lines left of 10"


def test_a_file_over_its_budget_says_so_rather_than_reporting_no_room(tmp_path):
    """`left` clamps at zero, so an overrun and a file exactly at its ceiling would read the
    same — which is the one state a reader has to act on."""
    from roadkeep.budgeting import file_budget

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
        '[budgets]\n"agents.md" = { lines = 2 }\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "agents.md").write_text("x\n" * 5, encoding="utf-8")
    (load,) = file_budget(Config.discover(tmp_path))
    assert load.room == "over by 3 lines of 2"


def test_the_payload_names_the_limit_a_caller_would_act_on(tmp_path, capsys):
    """A consumer gating on this reads the payload, and the field it needs is which limit is
    about to refuse — not the first one the config happened to declare."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    (found,) = [
        one
        for one in json.loads(capsys.readouterr().out)["each_turn"]["files"]
        if one["path"] == "agents.md"
    ]
    assert found["limit"]["unit"] in ("lines", "bytes")
    assert found["limit"]["declared"] > 0
    assert found["limit"]["left"] >= 0 and found["limit"]["over"] == 0


def test_the_room_is_this_records_arithmetic_and_not_a_readers(tmp_path):
    """RK1096's rule, which is why `Session` now carries the records rather than a widening
    tuple of their fields: this read wanted a third and then a fourth, and a projection is
    what RK1244 had just finished removing one surface over."""
    from dataclasses import fields

    from roadkeep.budgeting import Load, Session

    (one,) = [field for field in fields(Session) if field.name == "resident"]
    assert "Load" in str(one.type)
    assert {"room", "tightest"} <= {name for name in dir(Load)}


# -- and it stops at the conversion (RK1249) ----------------------------------


def test_the_summary_row_does_not_say_which_unit_refuses(tmp_path, capsys):
    """It used to. `[budgets]` declares two units and `lint` emits `budget.lines` and
    `budget.bytes`, each naming its own — so *bytes is what `lint` refuses on* was a third
    statement of the gate that neither the gate nor the rows above agreed with.

    A summary takes the last word and reads as the general rule, which is what made two true
    sentences mislead together."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text(MARKED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "the unit `[budgets]` counts" in printed
    assert "refuses on" not in printed


def test_the_row_that_does_say_which_unit_refuses_is_the_per_file_one(tmp_path, capsys):
    """Which is where the fact lives: it is per file, because the tightest of two declared
    limits is a property of that file's own content (RK1248)."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text(MARKED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    (row,) = [one for one in capsys.readouterr().out.splitlines() if "agents.md" in one]
    assert "left of" in row or "over by" in row


def test_the_gate_still_names_the_unit_it_refused_on(tmp_path):
    """The statement the summary was competing with, asserted where it is actually made: one
    finding per declared unit, each carrying its own name."""
    from roadkeep.linting import lint

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
        '[budgets]\n"agents.md" = { lines = 2, bytes = 100000 }\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "agents.md").write_text("x\n" * 5, encoding="utf-8")
    codes = [one.code for one in lint(Config.discover(tmp_path)).findings]
    assert "budget.lines" in codes
    assert "budget.bytes" not in codes


# -- the reading the read before an edit was missing (RK1250) -----------------


def test_the_read_before_an_edit_states_what_a_model_is_charged(tmp_path, capsys):
    """RK345 built `--file` for one moment — an author about to edit an always-loaded file,
    asked before the paragraph exists. RK1245 gave `--session` the figure that moment needs
    and this read, the more likely to be open, threw it away."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text(MARKED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "reader" in printed
    assert "utf-16-code-units" in printed


def test_it_is_a_reading_and_says_so_rather_than_reading_as_a_third_limit(tmp_path, capsys):
    """RK258's line kept rather than crossed: that task refused a word figure *beside a
    declared unit*, because `[budgets]` is stated in what the loader pays and an aim next to
    it would be a number this project never wrote.

    This is not beside a cost and is not an aim — it is the same shape as the `checkout` row
    RK1105 added, and its clause says outright that nothing limits it."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md"]) == EXIT_OK
    (row,) = [one for one in capsys.readouterr().out.splitlines() if "reader" in one]
    assert "nothing here limits it" in row
    # And never spelled like the rows above it, which are `<taken> of <limit>`.
    assert " of " not in row


def test_the_payload_keeps_it_out_of_the_declared_units(tmp_path, capsys):
    """A caller iterating `units` is iterating limits, and a reading among them is one it
    would compare against a ceiling that does not exist."""
    budgeted(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md", "--json"]) == EXIT_OK
    (found,) = json.loads(capsys.readouterr().out)["files"]
    assert found["characters"] > 0
    assert {one["unit"] for one in found["units"]} == {"lines", "bytes"}


def test_it_is_the_same_number_the_session_read_reports(tmp_path, capsys):
    """One measurement and two readers (RK1096), which is the property this task is about:
    the figure was already on the record and only one of the two printed it."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text(SECTIONED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md", "--json"]) == EXIT_OK
    (one,) = json.loads(capsys.readouterr().out)["files"]
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    (other,) = [
        row
        for row in json.loads(capsys.readouterr().out)["each_turn"]["files"]
        if row["path"] == "agents.md"
    ]
    assert one["characters"] == other["characters"]


def test_a_file_that_does_not_decode_prints_no_reading(tmp_path, capsys):
    """`None` is the answer where the question has none, and a row saying so would be a row
    about this tool rather than about the file."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_bytes(b"# Guide\n\n\xff\xfe not utf-8\n")
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md"]) == EXIT_OK
    assert "reader" not in capsys.readouterr().out


# -- two absences, one None (RK1251) ------------------------------------------


def _declared_but(tmp_path: Path, **files: bytes) -> Config:
    """A project budgeting `agents.md` and whatever else, with only what is passed on disk."""
    declared = dict.fromkeys(("agents.md", *files))
    entries = "\n".join(f'"{name}" = {{ lines = 10, bytes = 8000 }}' for name in declared)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n[budgets]\n' + entries + "\n",
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    for name, body in files.items():
        (tmp_path / name).write_bytes(body)
    return Config.discover(tmp_path)


def test_a_file_that_is_not_on_disk_is_not_called_undecodable(tmp_path, capsys):
    """The defect. `Load.characters` is `None` for a file that does not decode *and* for one
    that is not there, and the row read that `None` as the first — so a project whose declared
    `agents.md` is missing was told this tool could not read it.

    Both other surfaces already say it plainly: `--file` prints `not on disk`, and `lint`
    reports `budget.absent`."""
    _declared_but(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    (row,) = [one for one in capsys.readouterr().out.splitlines() if "agents.md" in one]
    assert "not on disk" in row
    assert "UTF-8" not in row


def test_the_absent_row_states_no_room_either(tmp_path, capsys):
    """The other half. `10 lines left of 10` is arithmetically true and is the sentence
    `budget.absent` exists to contradict: a budget with nothing under it is the one reading
    that makes a missing file look like room."""
    _declared_but(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    (row,) = [one for one in capsys.readouterr().out.splitlines() if "agents.md" in one]
    assert "left of" not in row


def test_a_file_that_is_there_and_does_not_decode_still_says_which(tmp_path, capsys):
    """The state RK1245 was about, unchanged: it is on disk, its bytes are what a loader pays,
    and the row says so rather than reporting a code-unit figure it does not have."""
    _declared_but(tmp_path, **{"agents.md": b"# x\n\n\xff\xfe not utf-8\n"})
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    (row,) = [one for one in capsys.readouterr().out.splitlines() if "agents.md" in one]
    assert "not UTF-8" in row
    assert "not on disk" not in row
    # And its room stands, because there is a file under the budget.
    assert "left of" in row


def test_the_payload_says_which_absence_a_null_is(tmp_path, capsys):
    """A caller reading only the null cannot tell the two apart, which is the defect one
    surface in."""
    _declared_but(tmp_path)
    assert main(["-C", str(tmp_path), "cost", "--session", "--json"]) == EXIT_OK
    (found,) = json.loads(capsys.readouterr().out)["each_turn"]["files"]
    assert found["characters"] is None
    assert found["present"] is False


def test_the_three_surfaces_agree_about_an_absent_file(tmp_path, capsys):
    """The property this restores: `--file`, `--session` and the gate are three readings of
    one state, and two of them were right."""
    from roadkeep.linting import lint

    config = _declared_but(tmp_path)
    assert "budget.absent" in {one.code for one in lint(config).findings}
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md"]) == EXIT_OK
    assert "not on disk" in capsys.readouterr().out
    assert main(["-C", str(tmp_path), "cost", "--session"]) == EXIT_OK
    assert "not on disk" in capsys.readouterr().out


# -- the ranking under the total (RK1252) -------------------------------------


def _sectioned(tmp_path: Path, config: str) -> Config:
    """Two sections where the byte order and the line order disagree — a short section of
    long lines against a long section of short ones, which is the case the sort key decides.
    """
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "agents.md").write_text(
        "# Guide\n\n"
        "## Wide\n\n" + ("x" * 200 + "\n") * 3 + "\n"
        "## Tall\n\n" + "y\n" * 20,
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


BYTES_TIGHT = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
    '[budgets]\n"agents.md" = { lines = 10000, bytes = 700 }\n'
)
LINES_TIGHT = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
    '[budgets]\n"agents.md" = { lines = 30, bytes = 1000000 }\n'
)


def test_the_ranking_follows_the_limit_about_to_refuse(tmp_path):
    """RK1092 built this list for an author at the ceiling, and it sorted by bytes always.
    RK1248 made the cost visible: the limit about to refuse may be `lines`, and a breakdown
    ranked by bytes then names a section that is not the one to cut."""
    from roadkeep.budgeting import file_budget

    (wide,) = file_budget(_sectioned(tmp_path, BYTES_TIGHT))
    assert wide.tightest.unit == "bytes"
    assert [one.heading for one in wide.ranked][:1] == ["## Wide"]


def test_the_same_file_ranks_the_other_way_where_lines_are_the_ceiling(tmp_path):
    """The same sections, the other declared limit, the other answer — which is the whole
    point of keying the order on `tightest` rather than on a preference."""
    from roadkeep.budgeting import file_budget

    (tall,) = file_budget(_sectioned(tmp_path, LINES_TIGHT))
    assert tall.tightest.unit == "lines"
    assert [one.heading for one in tall.ranked][:1] == ["## Tall"]


def test_the_ranking_and_the_room_are_one_decision(tmp_path):
    """Keyed on the same property, so the report cannot advise against the ceiling it just
    stated: `room` names the unit and `ranked` orders by it."""
    from roadkeep.budgeting import file_budget

    (load,) = file_budget(_sectioned(tmp_path, LINES_TIGHT))
    assert "lines left of" in load.room
    assert load.ranked[0].lines >= load.ranked[-1].lines


def test_the_column_a_reader_scans_is_the_one_it_is_sorted_on(tmp_path, capsys):
    """The ranking unit leads the row, because a list ordered by a column that is not the
    first reads as unordered."""
    _sectioned(tmp_path, LINES_TIGHT)
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md"]) == EXIT_OK
    rows = [one for one in capsys.readouterr().out.splitlines() if one.startswith("    ")]
    leading = [int(one.split()[0]) for one in rows if one.split()[0].isdigit()]
    assert leading == sorted(leading, reverse=True), rows


def test_the_reading_is_printed_under_the_breakdown_and_not_over_it(tmp_path, capsys):
    """Between the limits and the sections it was the total a reader met immediately before a
    list ranked in another unit, so the adjacency said *this is what those are of*. The
    breakdown belongs to the ceiling above it; the reading belongs to neither."""
    _sectioned(tmp_path, LINES_TIGHT)
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md"]) == EXIT_OK
    printed = capsys.readouterr().out.splitlines()
    # The reading's own row and not the breakdown's column header, which also says `reader`
    # since RK1253 — the two are different statements and only one of them is a total.
    total = [one for one in printed if "utf-16-code-units" in one][0]
    assert printed.index(total) > printed.index(
        [one for one in printed if "## Tall" in one][0]
    )


def test_the_payload_lists_them_in_the_order_the_report_shows(tmp_path, capsys):
    """A consumer acting on the first row should act on the section a reader would."""
    _sectioned(tmp_path, LINES_TIGHT)
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md", "--json"]) == EXIT_OK
    (found,) = json.loads(capsys.readouterr().out)["files"]
    assert [one["heading"] for one in found["parts"]][:1] == ["## Tall"]


def test_a_file_declaring_no_limit_keeps_the_order_it_always_had(tmp_path):
    """Bytes where nothing is declared, which is what `_parts` sorted by from the start."""
    from roadkeep.budgeting import Load, _parts

    load = Load(path="x", costs=(), parts=_parts(b"## A\nyyyy\n## B\nz\n"))
    assert load.tightest is None
    assert [one.heading for one in load.ranked] == ["## A", "## B"]


# -- the reading, per section (RK1253) ----------------------------------------


def test_each_section_carries_what_a_model_is_charged_for_it(tmp_path, capsys):
    """RK1252 ranked the breakdown by the ceiling, which is right, and left the reading with
    no per-section figure at all — so the one total whose purpose is comparison against the
    served schema was the one total with no breakdown."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text(SECTIONED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md", "--json"]) == EXIT_OK
    (found,) = json.loads(capsys.readouterr().out)["files"]
    assert all(one["characters"] is not None for one in found["parts"])
    # And it is the reading and not a second byte count: markers are two code units and four
    # bytes each, which is the whole reason the two columns are not one.
    assert any(one["characters"] < one["bytes"] for one in found["parts"])


def test_the_sections_sum_to_the_file(tmp_path):
    """One measurement at two levels (RK1096), which is what makes the column subtractable:
    a breakdown that did not sum to the total above it would be a second estimate of it."""
    from roadkeep.budgeting import file_budget

    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text(SECTIONED, encoding="utf-8")
    (load,) = [one for one in file_budget(Config.discover(tmp_path)) if one.path == "agents.md"]
    assert sum(one.characters for one in load.parts) == load.characters


def test_the_reading_is_a_column_and_never_the_sort_key(tmp_path):
    """The decision RK1253 left open, taken the way RK1252 took its own: the order belongs to
    the limit about to refuse, and a list sorted by a figure nothing refuses would answer a
    question the gate never asks while looking like the one that does."""
    from roadkeep.budgeting import file_budget

    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\n'
        '[budgets]\n"agents.md" = { lines = 30, bytes = 1000000 }\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    # `Wide` is the largest in bytes and in code units; `Tall` is the largest in lines, which
    # is the declared ceiling — so an order following the reading would name the other one.
    (tmp_path / "agents.md").write_text(
        "# Guide\n\n## Wide\n\n" + ("x" * 200 + "\n") * 3 + "\n## Tall\n\n" + "y\n" * 20,
        encoding="utf-8",
    )
    (load,) = file_budget(Config.discover(tmp_path))
    assert load.tightest.unit == "lines"
    assert load.ranked[0].heading == "## Tall"
    assert load.ranked[0].characters < load.ranked[1].characters


def test_three_figures_are_given_a_header(tmp_path, capsys):
    """Two columns of bare numbers said which was which by position and by width; three do
    not, and the leading one now varies with the ceiling."""
    budgeted(tmp_path)
    (tmp_path / "agents.md").write_text(SECTIONED, encoding="utf-8")
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md"]) == EXIT_OK
    printed = capsys.readouterr().out.splitlines()
    (header,) = [one for one in printed if one.strip().startswith(("lines", "bytes"))
                 and "reader" in one]
    # Named in the order printed, ranking unit first (RK1252).
    assert header.split() == ["lines", "bytes", "reader"] or header.split() == [
        "bytes", "lines", "reader"
    ]


def test_a_file_that_does_not_decode_has_no_column_at_all(tmp_path, capsys):
    """`None` for the whole file or for none of it: a UTF-8 continuation byte is never a
    newline, so splitting on line boundaries cannot break a sequence — if the file decodes
    every section does, and the two absences are one fact."""
    from roadkeep.budgeting import file_budget

    budgeted(tmp_path)
    (tmp_path / "agents.md").write_bytes(b"## A\n\xff\xfe\n## B\nz\n")
    (load,) = [one for one in file_budget(Config.discover(tmp_path)) if one.path == "agents.md"]
    assert load.characters is None
    assert all(one.characters is None for one in load.parts)
    assert main(["-C", str(tmp_path), "budget", "--file", "agents.md"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "reader" not in printed


# -- what a brief costs a tool result (RK1286) --------------------------------


def _reading(tmp_path: Path, *, ceiling: int | None = None) -> Config:
    """The fixture, optionally declaring what one brief may cost."""
    config = project(tmp_path)
    if ceiling is not None:
        (tmp_path / "roadkeep.toml").write_text(
            (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
            + f"\n[reads]\nbrief = {ceiling}\n",
            encoding="utf-8",
        )
    return Config.discover(config.root)


def test_the_read_that_replaces_reading_the_file_is_priced(tmp_path):
    """RK1286. Every resident file has a budget and the served surface has two, on RK30's
    argument that a limit nobody counts is a limit that moves — and the one answer this
    project recommends *over* reading the file had no figure at all."""
    from roadkeep.budgeting import brief_budget

    found = brief_budget(_reading(tmp_path))

    assert {one.id for one in found.briefs} == {"RK1", "RK2"}
    assert all(one.characters > 0 for one in found.briefs)
    # Widest first, because a brief that fits on the average task and not on the hardest one
    # is a brief a session replaces exactly when the file is longest.
    assert found.briefs == tuple(sorted(found.briefs, key=lambda o: -o.characters))
    assert found.widest is found.briefs[0]
    # Opt-in: absent means ungoverned and never zero, which is every other table's rule.
    assert found.limit is None and found.over == ()


def test_the_figure_is_the_answer_itself_and_never_re_composed(tmp_path):
    # `surface`'s rule one read over: a row added to a brief moves this number, which is the
    # whole reason it is worth reading.
    from roadkeep.briefing import brief
    from roadkeep.budgeting import brief_budget
    from roadkeep.kernel.schema import width

    config = _reading(tmp_path)
    (one,) = [each for each in brief_budget(config, "RK1").briefs if each.id == "RK1"]
    assert one.characters == width(brief(config, "RK1").stated(config))


def test_a_brief_over_the_declared_ceiling_is_a_finding(tmp_path):
    config = _reading(tmp_path, ceiling=1)
    report = lint(config)

    assert not report.clean
    over = [one for one in report.findings if one.code == "read.over"]
    assert over, [str(one) for one in report.findings]
    # Filed against the file that declared it: a brief is composed per call and there is no
    # path a reader could open to see it, which is `budget.tool`'s own reason.
    assert all(one.file == "roadkeep.toml" for one in over)
    # The ones `pick` offers next, which on this fixture is the whole ready tier (RK1287).
    assert {one.subject for one in over} <= {"RK1", "RK2"}


def test_the_gate_prices_what_a_session_is_about_to_ask_for(tmp_path):
    """RK1287. A brief costs tens of milliseconds, so pricing every open line put a project
    that declared a ceiling at O(open) of them on every commit. What is left out is what
    nobody is about to brief — and the next run prices whatever the answer has become."""
    from roadkeep.budgeting import brief_budget

    config = _reading(tmp_path, ceiling=9000)
    bounded = brief_budget(config, offered=True)
    whole = brief_budget(config)

    assert {one.id for one in bounded.briefs} <= {one.id for one in whole.briefs}
    assert bounded.elided == len(whole.briefs) - len(bounded.briefs)
    # And the deliberate read is still every one: a person who asked for the ranking gets it.
    assert whole.elided == 0


def test_what_the_gate_left_out_is_a_note_and_never_a_silence(tmp_path):
    """No silent caps: a report that omits without saying so reads as one that covered
    everything, and `read.over` is derived from this ranking — so a project can be over its
    ceiling on a line nothing reports unless the count is stated."""
    config = _reading(tmp_path, ceiling=9000)
    (config.root / "ROADMAP.md").write_text(
        BACKLOG + "".join(
            f"- {DESIGNED} **RK{n}** (deps: —) **A symptom numbered {n}** — Because.\n"
            for n in range(3, 15)
        ),
        encoding="utf-8",
    )
    report = lint(Config.discover(config.root))
    priced = [one for one in report.notes if one.code == "read.priced"]

    # Fourteen open lines and four priced, so the ceiling is held against a minority — which
    # is the shortfall the threshold exists to name (RK1290).
    assert priced, [str(one) for one in report.notes]
    assert "open line(s) priced" in priced[0].message
    assert "cost --brief" in priced[0].message


def test_the_note_is_quiet_where_the_gate_saw_the_majority(tmp_path):
    """RK1290. `_collective`'s shape and not a tuned ratio: below the threshold this gate saw
    most of the backlog and there is no surprise to report. Without one it fired on every
    clean run of any real backlog, and a reader who meets the same sentence every time stops
    reading the notes — so the next one that matters arrives under a heading they skip."""
    config = _reading(tmp_path, ceiling=9000)
    report = lint(config)

    assert report.clean
    # Two open lines and the gate priced one of them: left out is not *more* than priced.
    assert [one for one in report.notes if one.code == "read.priced"] == []


def test_the_finding_names_the_read_that_prices_the_one_over(tmp_path):
    # RK420: every code resolves to a door, and this one carries the id already substituted.
    from roadkeep.remedying import remedy

    config = _reading(tmp_path, ceiling=1)
    found = next(one for one in lint(config).findings if one.code == "read.over")
    door = remedy(found, config)

    assert door is not None
    assert ["cost", "--brief", found.subject] in [list(one.argv) for one in door.doors]


def test_the_gate_composes_nothing_where_no_ceiling_is_declared(tmp_path, monkeypatch):
    """Pricing a brief per open line on a project that asked for no ceiling is work the gate
    has no question to spend it on — which is why the check is opt-in and not merely silent."""
    from roadkeep import linting

    asked = []
    monkeypatch.setattr(
        linting, "_reads", lambda config: (asked.append(config), ([], []))[1]
    )
    assert lint(_reading(tmp_path)).clean
    # The function is reached and answers empty; what it must not do is compose a brief.
    from roadkeep.budgeting import brief_budget

    assert brief_budget(_reading(tmp_path)).limit is None


def test_the_verb_ranks_every_open_line_and_narrows_to_one(tmp_path, capsys):
    _reading(tmp_path, ceiling=9000)
    assert main(["-C", str(tmp_path), "cost", "--brief"]) == EXIT_OK
    every = capsys.readouterr().out
    assert "RK1" in every and "RK2" in every and "9000 allowed, 0 over" in every

    assert main(["-C", str(tmp_path), "cost", "--brief", "RK1"]) == EXIT_OK
    one = capsys.readouterr().out
    assert "RK1" in one and "RK2" not in one


def test_a_backlog_with_nothing_open_is_answered_and_not_refused(tmp_path, capsys):
    # The caller who most needs the figure is the one about to file the first task.
    project(tmp_path, roadmap="# Roadmap\n\n## Block A — The model\n")
    assert main(["-C", str(tmp_path), "cost", "--brief"]) == EXIT_OK
    assert "nothing to price" in capsys.readouterr().out


def test_a_brief_the_read_cannot_compose_is_named_and_never_dropped(tmp_path, monkeypatch):
    """RK1288. A bare `continue` made the one number this read exists for wrong in the
    direction that matters: the widest is the bound, and a line that could not be composed is
    exactly the shape most likely to be it — so the ranking named the top of the rest."""
    import roadkeep.briefing as briefing
    from roadkeep.budgeting import brief_budget

    config = _reading(tmp_path)
    assert brief_budget(config).unpriced == (), "the fixture composes both"

    # Provoked at the composer, which is the seam a real refusal arrives through: a pointer
    # into prose this project does not have, or a graph the resolver declines.
    real = briefing.brief

    def refusing(config, task_id=None, **rest):
        if task_id == "RK2":
            raise KeyError("RK2 points at prose this project does not have")
        return real(config, task_id, **rest)

    monkeypatch.setattr(briefing, "brief", refusing)
    found = brief_budget(config)

    assert {one.id for one in found.briefs} == {"RK1"}
    assert [one.id for one in found.unpriced] == ["RK2"]
    # The tool's own sentence and not one composed here: naming it costs a row, not a decision.
    assert "prose this project does not have" in found.unpriced[0].because


def test_the_gate_reports_the_line_it_could_not_measure(tmp_path, monkeypatch):
    # `read.over` is derived from this ranking, so a project can be over its ceiling on a line
    # nothing reports — which makes the absence a finding rather than a note.
    import roadkeep.briefing as briefing

    config = _reading(tmp_path, ceiling=9000)
    monkeypatch.setattr(
        briefing,
        "brief",
        lambda *a, **k: (_ for _ in ()).throw(KeyError("nothing composes")),
    )
    report = lint(config)

    unpriced = [one for one in report.findings if one.code == "read.unpriced"]
    assert unpriced, [str(one) for one in report.findings]
    assert "would not compose" in unpriced[0].message
    assert "nothing composes" in unpriced[0].message


def test_the_total_is_carried_and_never_reconstructed(tmp_path, monkeypatch):
    """RK1289. The note added `elided` to what it priced and called that the backlog, which is
    the backlog only while every line it asked for answered: a line that refused leaves the
    ranking without ever being elided, so the denominator lost exactly the lines the report is
    most concerned about."""
    import roadkeep.briefing as briefing
    from roadkeep.budgeting import brief_budget

    config = _reading(tmp_path, ceiling=9000)
    real = briefing.brief

    def refusing(config, task_id=None, **rest):
        if task_id == "RK1":
            raise KeyError("nothing composes")
        return real(config, task_id, **rest)

    monkeypatch.setattr(briefing, "brief", refusing)
    found = brief_budget(config, offered=True)

    # Three numbers that add up, where two arranged so the sum is wrong was the defect.
    assert len(found.briefs) + len(found.unpriced) + found.elided == found.open_lines
    assert found.open_lines == 2
    assert len(found.unpriced) == 1


def test_the_note_says_priced_refused_and_not_asked_for(tmp_path, monkeypatch):
    import roadkeep.briefing as briefing

    config = _reading(tmp_path, ceiling=9000)
    real = briefing.brief
    monkeypatch.setattr(
        briefing,
        "brief",
        lambda cfg, task_id=None, **rest: (_ for _ in ()).throw(KeyError("nothing composes"))
        if task_id == "RK1"
        else real(cfg, task_id, **rest),
    )
    (note,) = [one for one in lint(config).notes if one.code == "read.priced"]

    assert "of 2 open line(s)" in note.message
    assert "1 refused" in note.message


def test_the_named_read_keeps_the_rule_the_unnamed_one_states(tmp_path):
    """RK1291. Asked for every line this walks the open ones, on the argument that a shipped id
    has no brief left to start work from — and named, it priced whatever it was handed. A
    shipped brief carries no allowances, no deps and no design, because the ship deleted them:
    the figure is comparable to nothing and is printed under a header saying what room is
    left."""
    from roadkeep.budgeting import brief_budget
    from roadkeep.shipping import ship

    config = _reading(tmp_path, ceiling=9000)
    ship(config, "RK1", why="It works now.").save()
    config = Config.discover(config.root)

    found = brief_budget(config, "RK1")
    assert found.briefs == ()
    assert [one.id for one in found.unpriced] == ["RK1"]
    # `Whereabouts`' own sentence, which every other refusal about a missing id already asks.
    assert "the changelog records it as" in found.unpriced[0].because


def test_an_id_no_file_mentions_is_the_same_absence(tmp_path):
    from roadkeep.budgeting import brief_budget

    found = brief_budget(_reading(tmp_path), "RK9999")
    assert [one.id for one in found.unpriced] == ["RK9999"]
    assert "no file mentions it" in found.unpriced[0].because


def test_an_open_line_named_is_still_priced(tmp_path):
    # The other half: a caller naming an id is usually naming one they are about to work on.
    from roadkeep.budgeting import brief_budget

    found = brief_budget(_reading(tmp_path), "RK1")
    assert [one.id for one in found.briefs] == ["RK1"]
    assert found.unpriced == ()


def test_the_verdict_says_what_it_was_taken_over(tmp_path, capsys):
    """RK1292. `0 over` beside a listing naming a line nobody could measure is a claim the
    ranking is not entitled to — the widest is the bound, and an unmeasured line is the shape
    most likely to be it. RK1288's finding at the printer: the reading learnt to name what it
    could not compose and the sentence above the listing kept counting as if it had not."""
    from roadkeep.shipping import ship

    config = _reading(tmp_path, ceiling=9000)
    ship(config, "RK1", why="It works now.").save()
    assert main(["-C", str(config.root), "cost", "--brief", "RK1"]) == EXIT_OK
    said = capsys.readouterr().out

    assert "0 over, 1 unpriced" in said


def test_an_answer_that_measured_everything_reads_as_it_always_did(tmp_path, capsys):
    # Silent where nothing went unmeasured, which is what keeps the ordinary answer short.
    _reading(tmp_path, ceiling=9000)
    assert main(["-C", str(tmp_path), "cost", "--brief"]) == EXIT_OK
    said = capsys.readouterr().out

    assert "0 over" in said and "unpriced" not in said


# -- and the third write off the same line (RK1305) ---------------------------


def test_the_retirement_reason_is_priced_before_it_is_written(tmp_path):
    """Measured while retiring a task in an adopting project: the reason was refused three
    times running — 250 characters, then 212, then 205, against a limit of 200 — and each
    rewrite cut a clause out of the one field whose whole job is to carry evidence. The
    sentence that finally landed says less about the measurement that settled the decision
    than the first draft did.

    Every refusal did its job. What none of them could do is what this read already did before
    a line was added or a completion written: answer, before a word exists, how much room
    *this* retirement has.
    """
    config = project(tmp_path)
    abandoned = budget(config, "RK2", retire="")
    superseded = budget(config, "RK2", retire="RK1")

    # The ledger's line, not the roadmap's: no deps and no pointer in the structure.
    assert abandoned.task.deps == () and abandoned.task.ref is None
    assert abandoned.task.status == config.schema.retired_marker
    # And the prefix `retire` writes, counted against the same limit the reason is refused by
    # — which is why the usable maximum is neither the published one nor a ship's.
    assert abandoned.derived == "abandoned: "
    assert superseded.derived == "superseded by RK1: "
    assert superseded.share("why").left < abandoned.share("why").left


def test_the_figure_is_the_reason_retire_actually_accepts(tmp_path, capsys):
    # The prediction and the refusal, asked of one line with nothing between them changing it
    # — which is the only thing that can hold a pre-write number honest (RK1199's shape).
    from roadkeep.verbs.refusing import EXIT_USAGE as REFUSED

    config = project(tmp_path)
    root = str(tmp_path)
    left = budget(config, "RK2", retire="RK1").share("why").left

    assert main(["-C", root, "retire", "RK2", "--superseded-by", "RK1",
                 "--reason", "x" * (left + 1) + "."]) == REFUSED
    capsys.readouterr()
    # And exactly what it promised lands, which is the half an under-report hides.
    assert main(["-C", root, "retire", "RK2", "--superseded-by", "RK1",
                 "--reason", "x" * (left - 1) + "."]) == EXIT_OK


def test_the_derived_prefix_is_named_rather_than_left_as_a_number(tmp_path, capsys):
    # `11 written` on a field nobody has drafted reads as the caller's prose and is the tool's,
    # and the remainder underneath is the one that binds either way.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK2", "--retire", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["derived"] == "abandoned: "
    # Published on every budget and never omitted, so a client can tell a write that derives
    # nothing from a build that did not know the field existed.
    assert json.loads(
        json.dumps(budget(Config.discover(tmp_path), "RK2").payload())
    )["derived"] == ""


def test_the_state_word_says_which_write_the_figures_are_about(tmp_path, capsys):
    # Three states and not two: `open_line=False` meant *the line add would write next*, and
    # a retirement's figures under that sentence describe the wrong write entirely.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK2", "--retire"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "(the ledger line retire writes)" in said
    assert "derived    `abandoned: `" in said


# -- the fourth write, and the one two limits made necessary (RK1458) ----------


def test_the_ship_sentence_is_priced_against_the_ledger_and_not_the_line(tmp_path):
    """RK1458. Two limits govern one sentence: the `why` on an open roadmap line and the `why`
    a `ship` writes to the ledger are different numbers, because the two lines carry different
    structure. `brief` says both — it quoted `why 171 on this line` and `why 190 on the ledger
    line a ship writes` — and this read knew only the first, so a caller either read the number
    out of an earlier brief, or wrote to the stricter of the two and spent characters that were
    there, or to the looser and spent a refusal."""
    # A line wide enough that the *line* limit binds and not the field's, which is the state
    # the two numbers differ in — and the state every real line of a mature backlog is in.
    wide = BACKLOG.replace("**A second symptom**", f"**{'A wide symptom ' * 7}**")
    config = project(tmp_path, roadmap=wide)
    line = budget(config, "RK2").share("why").allowed
    shipping = budget(config, "RK2", ship=True).share("why").allowed

    # The ledger drops the deps and the pointer, so its line has more room for prose.
    assert shipping > line, "the two limits are the whole subject"
    shaped = budget(config, "RK2", ship=True)
    assert shaped.task.deps == () and shaped.task.ref is None
    assert shaped.task.status == config.schema.shipped_marker
    # Nothing derived, which is the difference from a retirement: a ship writes no prefix.
    assert shaped.derived == ""


def test_it_answers_the_number_brief_already_quoted(tmp_path):
    # One reader for one figure: `brief` composes its shipping row through `as_recorded` under
    # the ledger's schema, and a second computation here is how the two come apart (RK1199).
    from roadkeep.briefing import brief

    config = project(tmp_path)
    view = brief(config, "RK2")
    assert view.shipping is not None
    assert budget(config, "RK2", ship=True).share("why").allowed == view.shipping.share("why").allowed


def test_the_figure_is_the_sentence_ship_actually_accepts(tmp_path, capsys):
    # The prediction and the write, with nothing between them changing the line — the only
    # thing that can hold a pre-write number honest (RK1199's shape).
    from roadkeep.verbs.refusing import EXIT_USAGE as REFUSED

    config = project(tmp_path)
    root = str(tmp_path)
    left = budget(config, "RK2", ship=True).share("why").left

    assert main(["-C", root, "ship", "RK2", "--why", "x" * (left + 1) + "."]) == REFUSED
    capsys.readouterr()
    assert main(["-C", root, "ship", "RK2", "--why", "x" * (left - 1) + "."]) == EXIT_OK


def test_the_state_word_is_read_off_the_departure_and_not_off_a_prefix(tmp_path, capsys):
    """RK1305 discriminated on `derived`, which worked while a retirement was the only
    departure priced here. A ship writes no prefix, so the second one arrived reporting itself
    as *the line add would write next* — the wrong write, said in the row that exists to say
    which write it is."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "budget", "RK2", "--ship"]) == EXIT_OK
    said = capsys.readouterr().out
    assert "(the ledger line ship writes)" in said
    assert "derived" not in said

    assert main(["-C", str(tmp_path), "budget", "RK2", "--ship", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert (payload["departure"], payload["derived"]) == ("ship", "")
    # Empty and never omitted on a line as it stands, for `derived`'s reason.
    assert json.loads(
        json.dumps(budget(Config.discover(tmp_path), "RK2").payload())
    )["departure"] == ""


def test_a_draft_over_the_ledger_s_allowance_exits_one(tmp_path, capsys):
    # The whole point of the subject: a refusal, without the write (RK1190).
    project(tmp_path)
    root = str(tmp_path)
    left = budget(Config.discover(tmp_path), "RK2", ship=True).share("why").left
    assert main(["-C", root, "budget", "RK2", "--ship", "--why", "x" * (left + 1) + "."]) == 1
    capsys.readouterr()
    assert main(["-C", root, "budget", "RK2", "--ship", "--why", "x" * (left - 1) + "."]) == EXIT_OK


# -- whose prose a number is about, said and not derived (RK1320) --------------


def test_one_flag_no_longer_answers_two_ways_about_one_sentence(tmp_path, capsys):
    """Measured on this repository, one call: `brief RK1311 --json` answered
    `budget.fields.symptom.drafted = false` and `shipping.changed.fields.symptom.drafted =
    true` about the same 93 characters, read off the same roadmap line, in the same payload.

    `Share.drafted` says whether `taken` is prose the caller handed over rather than prose the
    file holds (RK1190). It changes no arithmetic and every word of the answer: *93 drafted*
    about a symptom nobody typed is a report about the wrong file.
    """
    config = project(tmp_path)
    line = budget(config, "RK1")
    shipped = budget_of(
        config,
        line.task,
        open_line=False,
        schema=config.schema_for("changelog"),
    )
    # Same sentence, same file, one answer. `open_line` was a proxy for *the caller composed
    # this* and stopped being one the moment a second reason to pass False existed.
    assert line.share("symptom").taken == shipped.share("symptom").taken
    assert line.share("symptom").drafted is False
    assert shipped.share("symptom").drafted is False


def test_a_symptom_the_caller_typed_is_still_theirs(tmp_path):
    # The half this must not cost: the pre-`add` read the flag was written for, where there is
    # no file the prose could have come from and `_subject` composed the task out of it.
    config = project(tmp_path)
    drafted = budget(config, block="A", symptom="A drafted symptom")
    assert drafted.share("symptom").drafted is True
    assert drafted.share("symptom").taken == len("A drafted symptom")

    # And an empty flag is the absence of a draft rather than one: `--symptom ""` asks what an
    # empty field costs, and nothing was handed over to be called the caller's.
    assert budget(config, block="A").share("symptom").drafted is False


# -- two tenses, two verbs (RK1321) --------------------------------------------


def test_the_surface_subjects_left_the_verb_about_prose(tmp_path, capsys):
    """Measured twice in one session: RK1305 added a seventh subject and `budget` reached
    2,741 against a per-tool ceiling of 2,600 — overtaking `ship` at 2,466, the tool that
    number was calibrated against — and RK1310 then added a 65th verb and the whole surface
    reached 64,190 against 63,500. Both ceilings were re-argued rather than met, and both
    arguments were about the same tool.

    What the ceiling found is not a description that grew. `budget` answered about a line, a
    section body, a non-goal, an every-turn file, the tool list, a session, a brief and a
    retirement — eight questions under one name, where every other served tool answers one.
    """
    budgeted(tmp_path)
    where = ["-C", str(tmp_path)]
    # The seam is the tense: what a write **may** spend, against what a surface **does**.
    for subject in ("--tools", "--brief", "--session"):
        assert main([*where, "cost", subject]) == EXIT_OK
        capsys.readouterr()
        assert main([*where, "budget", subject]) == EXIT_USAGE
        assert "declares no" in capsys.readouterr().err

    for subject in ("--file", "--non-goal"):
        # Whether each answers is its own test's; what is held here is which verb *has* it.
        capsys.readouterr()
        assert main([*where, "cost", subject]) == EXIT_USAGE
        assert "declares no" in capsys.readouterr().err


def test_neither_half_is_the_largest_served_tool():
    """The design's own falsification: splitting is a name and not a bundle if either half is
    still the largest. Measured after the split — `budget` is third, behind two write verbs
    that answer one question each, which is what a per-tool ceiling is calibrated against."""
    import json

    from roadkeep import serving

    config = Config.discover(Path(__file__).resolve().parents[1])
    ranked = sorted(
        ((len(json.dumps(one, ensure_ascii=False)), one["name"]) for one in serving.descriptors(config)),
        reverse=True,
    )
    largest = ranked[0][1]
    assert largest not in {"budget", "cost"}, f"{largest} is still the largest"
    # And the half that kept the subjects is well under it, which is the room the split bought.
    sized = dict((name, n) for n, name in ranked)
    assert sized["budget"] < sized[largest]
    assert sized["cost"] < sized["budget"]
