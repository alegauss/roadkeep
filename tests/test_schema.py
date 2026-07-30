"""The schema, checked against its own repository's backlog.

`docs/ROADMAP.md` is the conformance fixture (see agents.md): the corpus tests
below fail if the schema stops being able to express the 26 lines it was measured
from, which is the difference between a format proven by an artefact and one
asserted in a README.

Reaching the fields is `Document`'s job (RK2); these tests are about what the
schema says once they are read.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from roadkeep.document import Document
from roadkeep import (
    DESIGNED,
    IDEA,
    PARTIAL,
    SHIPPED,
    Dep,
    Schema,
    SchemaError,
    Task,
)

ROADMAP = Path(__file__).resolve().parents[1] / "docs" / "ROADMAP.md"

SCHEMA = Schema()
OUTLINE = Schema(ref_scheme="outline")


def task(**over) -> Task:
    """A conforming task, with the field under test overridden."""
    fields = dict(
        id="RK1",
        status=DESIGNED,
        block="A",
        symptom="Nothing knows what a task line is, so every check is a regex over prose",
        why=(
            "a schema over the six fields is the only thing that can refuse an "
            "over-length line at write time."
        ),
        deps=(),
    )
    fields.update(over)
    # In the id scheme the pointer is the id, so a helper that pinned it would be
    # testing a line no `add` could produce.
    fields.setdefault("ref", fields["id"])
    return Task(**fields)


# -- rendering -------------------------------------------------------------


def test_render_is_the_canonical_line():
    assert SCHEMA.render(task(symptom="Nothing knows what a task line is", why="a schema refuses.")) == (
        "- \U0001f4cb **RK1** (deps: —) **Nothing knows what a task line is** "
        "— a schema refuses. → §RK1"
    )


def test_empty_deps_render_as_an_em_dash():
    assert "(deps: —)" in SCHEMA.render(task(deps=()))


def test_deps_render_the_markers_they_carry():
    line = SCHEMA.render(task(id="RK5", deps=(Dep("RK1", SHIPPED), Dep("RK2"))))
    assert f"(deps: RK1 {SHIPPED}, RK2)" in line


def test_a_dep_marker_is_any_status_not_only_shipped():
    # Shio annotates ⏳ and 📋 deps: the marker caches the target's status (RK8),
    # so every status it can hold is representable.
    assert SCHEMA.validate(task(id="RK5", deps=(Dep("RK1", PARTIAL),))) == ()
    assert f"(deps: RK1 {PARTIAL})" in SCHEMA.render(task(id="RK5", deps=(Dep("RK1", PARTIAL),)))


def test_a_dep_marker_that_is_not_a_status_is_refused():
    codes = {v.code for v in SCHEMA.validate(task(id="RK5", deps=(Dep("RK1", "soon"),)))}
    assert codes == {"deps.marker"}


def test_plain_string_deps_are_coerced():
    assert task(id="RK5", deps=("RK1",)).deps == (Dep("RK1", marker=None),)


def test_a_task_without_a_ref_renders_without_the_arrow():
    assert "→" not in SCHEMA.render(task(ref=None))


# -- the corpus is the fixture ---------------------------------------------


def test_corpus_is_not_empty():
    # A corpus test over zero lines passes for the wrong reason. A floor and not a count:
    # this corpus is the *roadmap*, which shrinks by one every time a task ships, so a
    # tight number here would fail on progress — as 10 did the moment RK41 left 9 behind.
    # The shipped lines are a corpus too, under the ledger's own schema, and test_document.py
    # holds that half.
    assert len(read_corpus()) >= 5


def test_every_corpus_line_conforms():
    offenders = {
        t.id: SCHEMA.validate(t) for t in read_corpus() if SCHEMA.validate(t)
    }
    assert offenders == {}


def test_every_corpus_line_renders_back_to_itself():
    # A weaker statement than L3's round-trip (RK2), but it is the part that is
    # about the schema: the canonical form is the form already in the file.
    for line, parsed in zip(read_corpus_lines(), read_corpus(), strict=True):
        assert SCHEMA.render(parsed) == line


def test_corpus_stays_inside_the_limits_it_was_measured_from():
    lines = [SCHEMA.render(t) for t in read_corpus()]
    assert max(len(line) for line in lines) <= SCHEMA.line_max


# -- lengths ---------------------------------------------------------------


def test_over_length_symptom_is_refused_with_limit_and_actual():
    (violation,) = SCHEMA.validate(task(symptom="x" * 121))
    assert violation.code == "symptom.too-long"
    assert "121" in violation.message and "120" in violation.message
    assert "improvements" in violation.message


def test_symptom_at_the_limit_is_accepted():
    assert SCHEMA.validate(task(symptom="x" * 120)) == ()


def test_over_length_why_is_refused():
    (violation,) = SCHEMA.validate(task(why="x " * 100 + "y."))
    assert violation.code == "why.too-long"


def test_rendered_line_limit_catches_fields_that_are_each_legal():
    over = task(symptom="x" * 120, why="y " * 99 + "z.")
    codes = {v.code for v in SCHEMA.validate(over)}
    assert codes == {"line.too-long"}


# -- one sentence ----------------------------------------------------------


def test_a_second_sentence_in_why_is_refused():
    (violation,) = SCHEMA.validate(task(why="a schema refuses. It also renders."))
    assert violation.code == "why.sentences"
    assert "improvements" in violation.message


def test_an_abbreviation_is_not_a_sentence_boundary():
    assert SCHEMA.validate(task(why="limits are per project, e.g. the prefix.")) == ()


def test_a_decimal_is_not_a_sentence_boundary():
    assert SCHEMA.validate(task(why="tomllib is stdlib from 3.11 onward.")) == ()


def test_why_without_a_terminator_is_refused():
    (violation,) = SCHEMA.validate(task(why="a schema refuses"))
    assert violation.code == "why.no-terminator"


def test_symptom_with_a_terminator_is_refused():
    (violation,) = SCHEMA.validate(task(symptom="Nothing knows what a task line is."))
    assert violation.code == "symptom.sentence"


# -- shape -----------------------------------------------------------------


def test_shipped_marker_is_refused_in_the_roadmap():
    (violation,) = SCHEMA.validate(task(status=SHIPPED))
    assert violation.code == "status.shipped"
    assert "changelog" in violation.message


def test_unknown_marker_is_refused_and_names_the_allowed_set():
    (violation,) = SCHEMA.validate(task(status="⭐"))
    assert violation.code == "status.unknown"
    assert IDEA in violation.message


def test_ids_are_prefix_and_unpadded_number():
    assert {v.code for v in SCHEMA.validate(task(id="SH1"))} == {"id.format"}
    assert {v.code for v in SCHEMA.validate(task(id="RK01"))} == {"id.format"}
    assert {v.code for v in SCHEMA.validate(task(id="RK"))} == {"id.format"}


def test_a_self_dependency_is_refused():
    codes = {v.code for v in SCHEMA.validate(task(id="RK5", deps=("RK5",)))}
    assert codes == {"deps.self"}


def test_a_duplicated_dependency_is_refused():
    codes = {v.code for v in SCHEMA.validate(task(id="RK5", deps=("RK1", "RK1")))}
    assert codes == {"deps.duplicate"}


def test_a_dependency_of_another_project_is_refused():
    codes = {v.code for v in SCHEMA.validate(task(id="RK5", deps=("SH341",)))}
    assert codes == {"deps.format"}


def test_a_missing_ref_is_refused_by_default_and_optional_by_configuration():
    assert {v.code for v in SCHEMA.validate(task(ref=None))} == {"ref.missing"}
    assert Schema(ref_required=False).validate(task(ref=None)) == ()


def test_a_ref_carrying_its_sigil_is_refused():
    (violation,) = SCHEMA.validate(task(ref="§I.1"))
    assert violation.code == "ref.sigil"
    assert "I.1" in violation.message


def test_a_pointer_at_a_whole_section_is_accepted_where_sections_are_numbered():
    # Turing has nine of these. Under the outline scheme the rule is that a pointer
    # resolves, not that it carries a dot.
    assert OUTLINE.validate(task(ref="XLV")) == ()
    assert OUTLINE.validate(task(ref="XIV.8.7")) == ()


def test_a_lettered_final_segment_is_an_anchor_at_both_ends_of_the_pointer():
    # Turing spells a fourth level with a letter (RK47), 20 headings across two files,
    # and the heading and the pointer read the same pattern — so a `§VII.2.a` the file
    # declares had to be a pointer the schema accepts, or the two ends would disagree
    # about which sections exist.
    assert OUTLINE.validate(task(ref="VII.2.a")) == ()
    assert OUTLINE.validate(task(ref="IX.4.d")) == ()


@pytest.mark.parametrize("ref", ["VII.2.beta", "VII.2.A", "VII.a.2", "III.2–III.5"])
def test_a_segment_no_corpus_writes_is_still_refused(ref):
    # One lowercase letter, last: measured, not guessed. A general alphanumeric segment
    # admits nothing more across either corpus and costs `§VII.2` its ability to tell an
    # anchor from a title's first word; a range names no single anchor at all.
    assert {v.code for v in OUTLINE.validate(task(ref=ref))} == {"ref.format"}


def test_a_ref_that_is_not_an_anchor_is_refused():
    assert {v.code for v in OUTLINE.validate(task(ref="Block A"))} == {"ref.format"}


def test_the_pointer_is_the_id_and_a_chosen_one_is_refused():
    # The whole point of RK27: there is nothing to choose, so choosing is an error.
    (violation,) = SCHEMA.validate(task(id="RK27", ref="I.5"))
    assert violation.code == "ref.mismatch"
    assert "RK27" in violation.message


def test_the_pointer_is_derived_on_render_not_echoed():
    # A line carrying the wrong anchor stops round-tripping instead of being
    # preserved, which is what makes the anchor impossible to get wrong.
    assert SCHEMA.render(task(id="RK27", ref="I.5")).endswith("§RK27")
    assert OUTLINE.render(task(id="RK27", ref="I.5")).endswith("§I.5")


def test_the_scheme_itself_is_checked_at_construction():
    with pytest.raises(ValueError, match="ref_scheme"):
        Schema(ref_scheme="roman")


# -- round-trip safety (refused, not repaired) -----------------------------


def test_a_newline_in_a_field_is_refused():
    codes = {v.code for v in SCHEMA.validate(task(symptom="two\nlines"))}
    assert codes == {"symptom.newline"}


def test_padding_is_refused_rather_than_trimmed():
    (violation,) = SCHEMA.validate(task(symptom=" padded "))
    assert violation.code == "symptom.whitespace"


def test_the_delimiter_cannot_appear_inside_the_symptom_it_closes():
    codes = {v.code for v in SCHEMA.validate(task(symptom="a **bold** claim"))}
    assert codes == {"symptom.markup"}


def test_bold_inside_a_why_is_not_the_tools_business():
    # 25 of Shio's lines do this and every one round-trips.
    assert SCHEMA.validate(task(why="`HELP` is a **template literal**.")) == ()


def test_an_empty_field_is_refused_once():
    assert {v.code for v in SCHEMA.validate(task(why=""))} == {"why.empty"}


# -- the batch refusal -----------------------------------------------------


def test_check_raises_with_every_violation_not_the_first():
    broken = task(id="rk1", status=SHIPPED, symptom="x" * 200)
    with pytest.raises(SchemaError) as caught:
        SCHEMA.check(broken)
    codes = {v.code for v in caught.value.violations}
    assert codes == {"id.format", "status.shipped", "symptom.too-long", "line.too-long"}


def test_check_returns_the_task_when_it_conforms():
    conforming = task()
    assert SCHEMA.check(conforming) is conforming


# -- the schema is configuration, not convention ---------------------------


def test_another_projects_prefix_is_a_configuration():
    shio = Schema(prefix="SH")
    assert shio.validate(task(id="SH341", deps=("SH1",), symptom="A", why="b.")) == ()


def test_a_schema_that_can_say_done_is_refused_at_construction():
    with pytest.raises(ValueError, match="shipped marker"):
        Schema(markers=(DESIGNED, SHIPPED))


def test_limits_must_be_positive():
    with pytest.raises(ValueError, match="why_max"):
        Schema(why_max=0)


# -- reaching the corpus ---------------------------------------------------


def read_corpus_lines() -> list[str]:
    return [e.raw for e in Document.load(ROADMAP, SCHEMA).entries]


def read_corpus() -> list[Task]:
    return [e.task for e in Document.load(ROADMAP, SCHEMA).entries]
