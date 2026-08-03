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
