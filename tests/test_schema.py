"""The schema, checked against its own repository's backlog.

`docs/ROADMAP.md` is the conformance fixture (see agents.md): the corpus tests
below fail if the schema stops being able to express the 26 lines it was measured
from, which is the difference between a format proven by an artefact and one
asserted in a README.

Reaching the fields is `Document`'s job (RK2); these tests are about what the
schema says once they are read.
"""

from __future__ import annotations

import re
from dataclasses import replace
from pathlib import Path

import pytest

from roadkeep.document import Document
from roadkeep import (
    DESIGNED,
    IDEA,
    PARTIAL,
    SHIPPED,
    Dep,
    Id,
    Schema,
    SchemaError,
    Task,
)
from roadkeep.schema import RETIRED, over_by, width, words, words_over

ROADMAP = Path(__file__).resolve().parents[1] / "docs" / "ROADMAP.md"
CHANGELOG = Path(__file__).resolve().parents[1] / "docs" / "CHANGELOG.md"

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
    # A corpus test over zero lines passes for the wrong reason, and that is the whole claim
    # this makes. The floor is now the *ledger's*, which is where this comment was already
    # heading: the roadmap's finished state is empty, so every floor above zero is a count
    # waiting to fail on progress — 10 fell when RK41 left 9, 5 fell when RK23 left 4, and 1
    # fell when RK21 shipped the last line there is. The shipped lines are the corpus that
    # only grows, so the tests below read both halves, each under its own schema.
    assert read_ledger()


def test_every_corpus_line_conforms():
    offenders = {
        t.id: schema.validate(t)
        for schema, corpus in ((SCHEMA, read_corpus()), (LEDGER, read_ledger()))
        for t in corpus
        if schema.validate(t)
    }
    assert offenders == {}


def test_every_corpus_line_renders_back_to_itself():
    # A weaker statement than L3's round-trip (RK2), but it is the part that is
    # about the schema: the canonical form is the form already in the file.
    for schema, lines, corpus in (
        (SCHEMA, read_corpus_lines(), read_corpus()),
        (LEDGER, read_ledger_lines(), read_ledger()),
    ):
        for line, parsed in zip(lines, corpus, strict=True):
            assert schema.render(parsed) == line


def test_corpus_stays_inside_the_limits_it_was_measured_from():
    lines = [SCHEMA.render(t) for t in read_corpus()]
    lines += [LEDGER.render(t) for t in read_ledger()]
    assert max(len(line) for line in lines) <= SCHEMA.line_max


# -- lengths ---------------------------------------------------------------


def test_over_length_symptom_is_refused_with_limit_and_actual():
    (violation,) = SCHEMA.validate(task(symptom="x" * 121))
    assert violation.code == "symptom.too-long"
    assert "121" in violation.message and "120" in violation.message
    assert "improvements" in violation.message


def test_a_length_refusal_names_the_surplus_and_asks_for_a_deletion():
    # RK184: both numbers were already there and the surplus was left to be derived, so
    # the message asked for a rewrite — 327, then 303, then 300. It states the subtraction.
    (violation,) = SCHEMA.validate(task(symptom="x" * 127))
    assert "delete 7 characters" in violation.message
    # And the advice about where the text goes survives, after the arithmetic rather
    # than in place of it: it answers where, not how much.
    assert violation.message.index("delete 7") < violation.message.index("improvements")


def test_a_surplus_of_one_is_singular():
    (violation,) = SCHEMA.validate(task(symptom="x" * 121))
    assert "delete 1 character — about 1 word;" in violation.message


def test_the_arithmetic_is_spelled_in_one_place():
    # Five refusals count a length and one function writes all of them, so a message that
    # improves improves everywhere rather than in the one the author happened to hit.
    assert over_by(327, 320) == (
        "327 characters, limit is 320: delete 7 characters — about 2 words"
    )
    assert over_by(253, 250, unit="word") == "253 words, limit is 250: delete 3 words"


def test_a_character_surplus_is_restated_in_the_unit_the_retry_is_composed_in():
    # RK201: RK185 published every aim in words and left this surface — the one an author
    # reaches after the overrun — in characters alone, so the retry was a re-guess.
    assert over_by(309, 280).endswith("delete 29 characters — about 5 words")


def test_the_exact_figure_comes_first_and_the_approximation_is_hedged():
    # The character count is what refuses; the word one is derived from it. An author told
    # only "about 5 words" against a 29-character overrun has a smaller number to guess at.
    message = over_by(309, 280)
    assert message.index("29 characters") < message.index("about 5 words")
    assert "about" in message


def test_a_surplus_in_words_rounds_up_where_an_aim_rounds_down():
    # Opposite directions, one constant: an aim that rounds up overshoots the gate, and a
    # cut that rounds down stops short of it and earns the same refusal a second time.
    assert words(13) == 2 and words_over(13) == 2
    assert words(14) == 2 and words_over(14) == 3
    assert words(6) == 0 and words_over(6) == 1


def test_a_refusal_already_counted_in_words_gets_no_second_copy_of_itself():
    assert "about" not in over_by(253, 250, unit="word")


# -- one limit, and the counter the consumer uses (RK430) --------------------


def test_a_character_outside_the_basic_plane_costs_what_the_consumer_charges():
    # Java's `String.length`, C#'s and JavaScript's `.length` all count UTF-16 code
    # units. Four of this project's five default markers are astral and three are not,
    # which is why the exposure is invisible until a line lands on the limit exactly.
    assert (width("📋"), len("📋")) == (2, 1)
    assert (width("💭"), width("🛠"), width("🗑")) == (2, 2, 2)
    # The three that cost the same in both, and the reason the ledger never met this:
    # every shipped entry carries ✅, which is inside the Basic Multilingual Plane.
    assert (width("✅"), width("⏳"), width("⏸")) == (1, 1, 1)
    assert width("plain ascii") == len("plain ascii")


def test_a_line_at_the_limit_in_code_points_is_over_it_here():
    """Shio's ratchet, reproduced: `stats` said 320 of 320 and the Java gate said 321.

    Neither was wrong, and the character between them was the marker roadkeep itself
    wrote — so the tool certified a line its consumer rejects, and the failure landed on
    the next person to run the suite, in a build they did not break.
    """
    padded = task(why="x" * 40 + ".")
    at_limit = replace(SCHEMA, line_max=len(SCHEMA.render(padded)))
    assert at_limit.validate(padded) != ()
    # And exactly one unit over, which is the whole defect: one marker, one surrogate pair.
    assert width(SCHEMA.render(padded)) == len(SCHEMA.render(padded)) + 1


def test_the_refusal_names_both_numbers_only_where_they_disagree():
    # The cost of the defect was that both figures look right and the difference is one,
    # so the refusal says which it counted — and only then, because a parenthesis about
    # UTF-16 on every ASCII overrun is noise on the overwhelming majority of them.
    astral = "📋" + "x" * 130
    message = over_by(width(astral), 120, measured=astral)
    assert "132 characters (UTF-16 code units, 131 code points" in message
    assert "the gates that read this file use it" in message
    assert "(UTF-16" not in over_by(width("x" * 130), 120, measured="x" * 130)


def test_symptom_at_the_limit_is_accepted():
    assert SCHEMA.validate(task(symptom="x" * 120)) == ()


def test_over_length_why_is_refused():
    (violation,) = SCHEMA.validate(task(why="x " * 100 + "y."))
    assert violation.code == "why.too-long"


def test_the_lines_own_limit_is_what_bounds_the_why():
    # RK183: 120 + 200 is exactly 320 and the structure costs 38 more, so a line obeying
    # both published limits was refused by a third one measured on a string the author
    # never writes. The line's limit is carried into the field instead, and it is the
    # `why` that carries it — the field whose remainder has a section to go to.
    over = task(symptom="x" * 120, why="y " * 99 + "z.")
    (violation,) = SCHEMA.validate(over)
    assert violation.code == "why.too-long"
    assert violation.field == "why"
    # The number that refused, the number it came from, and what took the difference.
    assert f"limit is {SCHEMA.why_budget(over)}" in violation.message
    assert f"limit of {SCHEMA.line_max}" in violation.message
    assert "the symptom takes 120" in violation.message


def test_the_prose_budget_is_the_line_minus_what_it_renders_around_it():
    # Measured by rendering, never by a second copy of the format: the structure is the
    # dash, the marker, the bold id, the deps group, the em dash and the pointer.
    bare = task(symptom="", why="")
    assert SCHEMA.prose_budget(bare) == SCHEMA.line_max - width(SCHEMA.render(bare))
    # And `width`, not `len` (RK430): the structure carries the 📋 this tool wrote, which
    # is one code point and two UTF-16 units — so a budget measured in code points hands
    # the author a character the consumer's gate then refuses.
    assert width(SCHEMA.render(bare)) == len(SCHEMA.render(bare)) + 1
    # A dep costs the line, so it costs the prose: the budget is this line's, not the
    # project's, which is the whole reason a static number could not be right.
    assert SCHEMA.prose_budget(task(deps=(Dep("RK9"),))) < SCHEMA.prose_budget(task())


def test_a_symptom_over_its_own_limit_takes_nothing_from_the_why():
    # Otherwise one overrun is reported as two, and the author cuts a sentence that was
    # never over: the symptom is refused as itself and the why keeps its own limit.
    codes = {v.code for v in SCHEMA.validate(task(symptom="x" * 200, why="y" * 150 + "."))}
    assert codes == {"symptom.too-long"}


def test_a_why_inside_its_derived_budget_always_fits_the_line():
    # The property the derivation buys, and the whole of RK183: the rendered length is the
    # structure plus the two fields, so a `why` written to the number it was given cannot
    # be refused by the line. Across symptom lengths, dep counts and a narrower line —
    # the three things that move the structure — there is no pair that obeys and fails.
    for schema in (SCHEMA, replace(SCHEMA, line_max=200)):
        for symptom_len in (1, 60, 120):
            for deps in ((), (Dep("RK9"),), (Dep("RK9"), Dep("RK8"))):
                probe = task(symptom="x" * symptom_len, deps=deps)
                filled = replace(probe, why="y" * (schema.why_budget(probe) - 1) + ".")
                assert len(schema.render(filled)) <= schema.line_max
                assert schema.validate(filled) == ()


def test_a_line_with_no_prose_to_blame_is_still_the_lines_own_refusal():
    # What `line.too-long` is left to catch, and it is not a limit an author can fail: a
    # line whose structure alone is over, with no sentence the surplus could come out of.
    narrow = replace(SCHEMA, line_max=20)
    codes = {v.code for v in narrow.validate(task(why=""))}
    assert codes == {"why.empty", "line.too-long"}


def test_the_refusal_no_sentence_answers_asks_for_no_word_deletion():
    # RK243: RK201's hint is aimed at prose, and this is the one refusal whose own next
    # clause says prose is not what is over — an edit named beside the reason it cannot work.
    narrow = replace(SCHEMA, line_max=20)
    (violation,) = [v for v in narrow.validate(task(why="")) if v.code == "line.too-long"]
    assert "about" not in violation.message
    assert "delete" in violation.message and "the structure" in violation.message


def test_the_field_refusals_a_sentence_does_answer_keep_it():
    # The other side of the same switch: cutting words is exactly the remedy here, and the
    # neighbour `part.too-long` is prose too.
    (symptom,) = SCHEMA.validate(task(symptom="x" * 127))
    assert "about 2 words" in symptom.message
    (part,) = SCHEMA.as_ledger().validate(
        replace(task(), status=SHIPPED, part="p" * 60, ref="", deps=())
    )
    assert part.code == "part.too-long" and "about" in part.message


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


def test_a_block_letter_first_segment_is_an_anchor_and_a_bare_one_is_not():
    # commitclerk numbers its rationale §B.2 to §J.9 (RK101), of which only C and D parsed
    # — they happen to be roman numerals — so the same file was half-read under the scheme
    # it was written for. A bare `§B` stays refused: there it names a block, not a section.
    assert OUTLINE.validate(task(ref="B.2")) == ()
    assert OUTLINE.validate(task(ref="J.9")) == ()
    assert {v.code for v in OUTLINE.validate(task(ref="B"))} == {"ref.format"}


@pytest.mark.parametrize("ref", ["VII.2.beta", "VII.2.A", "VII.a.2", "III.2–III.5", "AB.2"])
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
    # Not `line.too-long`: the symptom is what is over, and the same overrun reported
    # twice is one defect with two numbers (RK183).
    assert codes == {"id.format", "status.shipped", "symptom.too-long"}


def test_check_returns_the_task_when_it_conforms():
    conforming = task()
    assert SCHEMA.check(conforming) is conforming


# -- the schema is configuration, not convention ---------------------------


def test_another_projects_prefix_is_a_configuration():
    shio = Schema(prefixes=("SH",))
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


#: The ledger's own schema, and the lines it holds. This half of the corpus is the one that
#: only grows: a task leaves the roadmap the moment it ships, and this repository's roadmap
#: is empty since RK21, so a corpus claim asked of the roadmap alone is now asked of nothing.
LEDGER = SCHEMA.as_ledger()


def read_ledger_lines() -> list[str]:
    return [e.raw for e in Document.load(CHANGELOG, LEDGER).entries]


def read_ledger() -> list[Task]:
    return [e.task for e in Document.load(CHANGELOG, LEDGER).entries]


# -- a backlog numbered by track (RK74) -------------------------------------

TRACKS = Schema(prefixes=("C", "L", "V"), ref_scheme="outline")


def test_every_declared_family_is_an_id_of_the_project():
    # One backlog, six numbering tracks: the letter is which track the work belongs to,
    # so `C14` and `V5` are both ids here and a dep from one to the other is ordinary.
    for identifier in ("C14", "L4", "V5"):
        assert TRACKS.id_pattern().match(identifier)
    assert not TRACKS.id_pattern().match("G11")


def test_a_dep_across_two_tracks_is_an_ordinary_dep():
    crossing = task(id="V5", deps=("C14", "L4"), ref="1.2")
    assert TRACKS.validate(crossing) == ()


def test_a_refusal_names_every_family_and_not_just_the_first():
    codes = {v.code: v.message for v in TRACKS.validate(task(id="G11", ref="1.2"))}
    assert "C/L/V" in codes["id.format"]


def test_a_range_counts_in_one_track():
    # `C14–C20` is a range; `C14–V5` names two tracks that number independently, so the
    # pair it names is not a range of anything and falls through to be reported.
    assert TRACKS.range_of_dep(Dep("C14–C20")) == (14, 20)
    assert TRACKS.family_of_dep(Dep("C14–C20")) == "C"
    assert TRACKS.range_of_dep(Dep("C14–V20")) is None
    assert TRACKS.family_of_dep(Dep("C14–20")) == "C"


def test_two_families_that_read_one_id_two_ways_are_refused():
    # `C` beside `C1` makes `C12` two ids, and which one it is would depend on the order
    # the alternation happens to be written in.
    with pytest.raises(ValueError, match="no rule breaks the tie"):
        Schema(prefixes=("C", "C1"))


def test_a_family_declared_twice_is_refused():
    with pytest.raises(ValueError, match="names a family twice"):
        Schema(prefixes=("C", "L", "C"))


def test_a_project_that_numbers_one_family_reads_the_pattern_it_always_did():
    # An MCP client shows this string, and a group nothing alternates over is punctuation
    # a reader has to look past.
    assert Schema().id_pattern().pattern == "^RK[1-9][0-9]*$"


# -- the id shape a live corpus already spells (RK106) ----------------------

PADDED = Schema(prefixes=("D",), id_pad=2, heading_word="Track")
SPLIT = Schema(prefixes=("T",), id_suffix=True, ref_scheme="outline")


def test_a_declared_width_admits_the_padding_and_still_refuses_the_second_spelling():
    # Dumont writes D01 through D09 on every line. The hazard the tool refuses padding for
    # is a backlog that pads *sometimes*, and a declared width is the project answering it:
    # every number has exactly one spelling again.
    for identifier in ("D01", "D09", "D10", "D99", "D100"):
        assert PADDED.id_pattern().match(identifier)
    for identifier in ("D1", "D001", "D0", "D00"):
        assert not PADDED.id_pattern().match(identifier)


def test_an_undeclared_width_is_still_refused():
    assert not Schema(prefixes=("D",)).id_pattern().match("D01")


def test_the_number_the_counter_mints_is_spelled_at_the_declared_width():
    # `D10` and never the `D1` this project's own gate would refuse a moment later.
    assert PADDED.spell_id("D", 1) == "D01"
    assert PADDED.spell_id("D", 100) == "D100"
    assert Schema().spell_id("RK", 7) == "RK7"


def test_a_padded_range_dep_is_the_range_it_reads_as():
    # Without the width the ends would not parse, and `D01–D09` would be reported as a
    # token that reads like a range instead of resolved as one.
    assert PADDED.range_of_dep(Dep("D01–D09")) == (1, 9)
    assert PADDED.family_of_dep(Dep("D01–D09")) == "D"


def test_a_sub_letter_is_an_id_only_where_the_project_declares_one():
    # T24b is a task split after its number was cited in commits and issues, which is the
    # thing an id is for; renumbering it would break the citations.
    assert SPLIT.id_pattern().match("T24b")
    assert SPLIT.id_pattern().match("T24")
    assert not SPLIT.id_pattern().match("T24beta")
    assert not SPLIT.id_pattern().match("T24B")
    assert not Schema(prefixes=("T",)).id_pattern().match("T24b")


def test_a_split_task_and_its_parent_are_two_lines_that_both_validate():
    parent = task(id="T24", ref="1.2")
    split = task(id="T24b", deps=("T24",), ref="1.3")
    assert SPLIT.validate(parent) == ()
    assert SPLIT.validate(split) == ()


def test_a_refusal_spells_the_shape_this_project_declared():
    # A message naming the built-in shape at a project whose config legalised another
    # reads as a bug in the tool, and gets the config edited back.
    padded = {v.code: v.message for v in PADDED.validate(task(id="D1", block="A", ref="D1"))}
    assert "zero-filled to 2 digits" in padded["id.format"]
    split = {v.code: v.message for v in SPLIT.validate(task(id="T24beta", ref="1.2"))}
    assert "one lowercase letter" in split["id.format"]


def test_a_width_below_one_is_not_a_width():
    with pytest.raises(ValueError, match="id_pad must be at least 1"):
        Schema(id_pad=0)


# -- one parse, so the pattern and the ordering cannot disagree (RK109) -----


def test_the_parse_takes_an_id_apart_into_the_three_things_declared():
    assert Schema().parse_id("RK9") == Id("RK", 9, "")
    assert PADDED.parse_id("D01") == Id("D", 1, "")
    assert SPLIT.parse_id("T24b") == Id("T", 24, "b")
    assert TRACKS.parse_id("V05") is None  # TRACKS declares no width
    assert TRACKS.parse_id("C14") == Id("C", 14, "")


def test_what_the_gate_refuses_the_parse_refuses():
    # The defect: `id_pattern` refused the `D1` the ordering read as 1, so a line the file
    # could not legally carry still got a number, and a number is a place in the queue.
    for schema in (Schema(), PADDED, SPLIT, TRACKS):
        for text in ("RK9", "D1", "D01", "D001", "T24", "T24b", "T24B", "C14", "V05", ""):
            assert (schema.parse_id(text) is not None) == bool(
                schema.id_pattern().match(text)
            )


def test_the_plain_fragment_stays_embeddable_twice_and_the_named_one_is_the_same_shape():
    # `lint` and `origin` wrap the plain fragment in a group of their own and read group 1,
    # and a range dep embeds it at both ends — neither survives a named group, which is why
    # there are two forms of one join rather than one form everybody works around.
    for schema in (Schema(), PADDED, SPLIT, TRACKS):
        assert "(?P<" not in schema.id_fragment
        both = re.compile(rf"^{schema.id_fragment}–{schema.id_fragment}$")
        assert both.groups == 0
        for text in ("RK9", "D1", "D01", "T24b", "C14", "V05"):
            assert bool(re.fullmatch(schema.id_groups, text)) == bool(
                re.fullmatch(schema.id_fragment, text)
            )


# -- the word a project files work under (RK75) -----------------------------

TRACKS_WORD = Schema(heading_word="Track", ref_scheme="outline")


def test_the_heading_and_the_dep_read_the_same_word_and_the_same_label():
    # One list, or `pick --block D.1` answers about a block nothing declares while both
    # halves parse. The label shape is the format's; only the word is the project's.
    assert TRACKS_WORD.heading_pattern().match("Track A — Structured sources")["label"] == "A"
    assert TRACKS_WORD.heading_pattern().match("Block A — nope") is None
    assert TRACKS_WORD.block_of_dep(Dep("Track A")) == "A"
    assert TRACKS_WORD.block_of_dep(Dep("Block A")) is None


def test_a_dotted_label_is_one_label_on_both_sides():
    # It was not: the heading captured `D` where the dep captured `D.1`, so two headings
    # `Block D.1` and `Block D.2` both declared `D` and a dep on either resolved wrong.
    plain = Schema(ref_scheme="outline")
    assert plain.heading_pattern().match("Block D.1 — sub-block")["label"] == "D.1"
    assert plain.block_of_dep(Dep("Block D.1")) == "D.1"


def test_a_report_names_a_block_in_the_projects_own_word():
    assert TRACKS_WORD.block_named("C") == "Track C"


def test_a_heading_word_that_is_not_one_bare_word_is_refused():
    # It is joined to the label by exactly one space, on the heading and on the dep alike.
    with pytest.raises(ValueError, match="one bare word"):
        Schema(heading_word=" Track")
    with pytest.raises(ValueError, match="one bare word"):
        Schema(heading_word="")


# -- the qualifier a partial entry carries (RK121) ---------------------------

LEDGER = Schema().as_ledger()


def test_a_partial_entry_renders_the_qualifier_inside_the_bold():
    # Inside the bold because that is where the corpus writes it — a second spelling would
    # be a line the tool renders differently from the one it read.
    entry = Task(id="RK9", status=SHIPPED, block="A", symptom="A symptom", why="Landed.")
    assert LEDGER.render(entry) == "- ✅ **RK9** **A symptom** — Landed."
    half = replace(entry, part="local half")
    assert LEDGER.render(half) == "- ✅ **RK9 (local half)** **A symptom** — Landed."


def test_a_qualifier_on_a_roadmap_line_is_refused():
    # The roadmap already has a word for work in halves: ⏳, an open marker. A line saying
    # it twice would be two places to read one claim.
    line = task(id="RK9", ref="RK9")
    codes = {v.code for v in SCHEMA.validate(replace(line, part="half"))}
    assert "part.unexpected" in codes


def test_a_qualifier_that_is_a_second_summary_is_refused():
    entry = Task(
        id="RK9",
        status=SHIPPED,
        block="A",
        symptom="A symptom",
        why="Landed.",
        part="the half that does the thing the other half does not do yet at all",
    )
    codes = {v.code: v.message for v in LEDGER.validate(entry)}
    assert "it names which half" in codes["part.too-long"]


def test_an_ordinary_entry_carries_no_qualifier_and_is_not_asked_for_one():
    entry = Task(id="RK9", status=SHIPPED, block="A", symptom="A symptom", why="Landed.")
    assert entry.part is None
    assert LEDGER.validate(entry) == ()


# -- the character the author did not type (RK407) ----------------------------


def test_a_lone_carriage_return_names_the_shell_that_wrote_it():
    """PowerShell reads a backtick as its escape character, so a `why` quoting an identifier
    like `renderItem` arrives carrying a CR nobody typed. Reported as `newline` the answer was
    accurate about the value and wrong about the cause — and the cause is the half to fix."""
    found = _codes(why="Because \rof a reason.")
    assert "why.control" in found
    assert "why.newline" not in found
    message = _message("why.control", why="Because \rof a reason.")
    assert "U+000D CARRIAGE RETURN" in message
    assert "`r" in message and "PowerShell" in message


def test_the_codepoint_is_named_and_not_only_numbered():
    # Unicode gives a C0 control no `name`, so `unicodedata` answers "" for every one of
    # them — and `U+0007` alone names the value without naming anything a caller recognises.
    for char, named, escape in (
        ("\a", "BELL", "`a"),
        ("\f", "FORM FEED", "`f"),
        ("\x1b", "ESCAPE", "`e"),
        ("\0", "NUL", "`0"),
    ):
        message = _message("why.control", why=f"Because {char}of a reason.")
        assert named in message and escape in message, char


def test_a_real_newline_is_still_a_newline():
    # A pasted paragraph produces one honestly, so the code stays and only the sentence
    # grows the clause about the shell — the two causes are both real and only one is a slip.
    for value in ("Because\nof a reason.", "Because\r\nof a reason."):
        found = _codes(why=value)
        assert "why.newline" in found, value
        assert "why.control" not in found, value


def test_a_tab_is_left_to_the_fixer_that_normalizes_it():
    # `char.tab` is `--fix`'s (RK126): refusing at the door what the gate one file over
    # repairs would be two rules about one character, disagreeing.
    assert "why.control" not in _codes(why="Because \tof a reason.")


def test_the_symptom_is_answered_the_same_way():
    assert "symptom.control" in _codes(symptom="A \asymptom")


def test_only_the_first_is_reported():
    # A sentence carrying six is six symptoms of one quoting mistake, and the first already
    # sends the reader to it.
    mangled = "Because \aof \aa \areason."
    assert sum(1 for code in _codes(why=mangled) if code == "why.control") == 1


def _task(**fields):
    from roadkeep.schema import Task

    base = {
        "id": "RK1",
        "status": "📋",
        "block": "A",
        "symptom": "A symptom",
        "why": "Because of a reason.",
        "ref": "RK1",
    }
    return Task(**{**base, **fields})


# -- one template, read in two directions (RK1063) ----------------------------


@pytest.mark.parametrize("symptom", [True, False])
@pytest.mark.parametrize("deps", [True, False])
def test_what_the_writer_renders_is_what_the_grammar_reads(symptom, deps):
    """The guarantee RK1063 makes structural: every shape a project can declare renders a
    line the parser accepts, and the fields come back as they went in.

    Not the round-trip property test one file over — that reads three corpora and answers
    *did this parser misread somebody's line*, which is L3's own question and stays. This
    one takes no corpus and asks whether the two faces of `TEMPLATE` still describe one
    line, which is the question that used to have no asker: a renderer emitting what the
    grammar refuses was a thing a test could catch and not a thing that was impossible.

    The marker arm is `schema.marks(task.status)` and not the `[ledger]` declaration,
    because that is the answer `_read_bullet` chooses the grammar from — whether *this
    line* fills the slot is a question per line and not per file (RK43, RK125), and a test
    that asked the file would be checking a pairing the parser never makes.
    """
    from roadkeep.document import _split_ref, _task_re

    schema = Schema(symptom_field=symptom, deps_field=deps)
    task = _task(deps=(Dep("RK7"),) if deps else (), part="local half")
    marked = schema.marks(task.status)
    line = schema.render(task)

    head, ref = _split_ref(line)
    found = _task_re(marked, symptom).match(head)
    assert found is not None, f"render wrote a line the grammar refuses: {line!r}"
    assert found.group("id") == task.id
    assert found.group("part") == task.part
    assert found.group("why") == task.why
    assert ref == task.ref
    if marked:
        assert found.group("status") == task.status
    if symptom:
        assert found.group("symptom") == task.symptom
    if deps:
        assert found.group("deps") == "RK7"


def test_the_markerless_ledger_line_renders_and_reads_without_the_slot():
    # The other half of the pairing above, and the one the parametrisation cannot reach: a
    # ledger declared markerless writes no marker and no symptom, so both faces have to drop
    # each slot together — and the em dash has to survive both drops (RK43, RK48).
    from roadkeep.document import _split_ref, _task_re

    schema = Schema(ledger_marker=False, ledger_symptom=False).as_ledger()
    task = _task(status=SHIPPED, ref=None, part=None)
    line = schema.render(task)
    assert line == "- **RK1** — Because of a reason."

    head, ref = _split_ref(line)
    found = _task_re(schema.marks(task.status), schema.symptom_field).match(head)
    assert found is not None and found.group("id") == "RK1" and ref is None

    # And the retirement that file still writes with one, which is the exception `marks`
    # carries and the reason it is asked per line (RK125): both faces move together there.
    retired = _task(status=RETIRED, ref=None, part=None)
    assert schema.render(retired).startswith(f"- {RETIRED} **RK1**")
    assert _task_re(schema.marks(RETIRED), schema.symptom_field).match(
        _split_ref(schema.render(retired))[0]
    )


def test_the_two_faces_are_the_same_sequence_of_slots():
    # The claim the parametrisation above cannot make: that there is one statement rather
    # than two that happen to agree. A slot added with only one face is a template that has
    # started being two again, which is the state RK1063 was filed from.
    from roadkeep.schema import TEMPLATE, grammar

    assert [slot.name for slot in TEMPLATE] == ["status", "head", "deps", "symptom", "why"]
    for slot in TEMPLATE:
        assert callable(slot.reads) and callable(slot.writes), slot.name
    # And the pattern really is the concatenation, so a slot cannot be read out of order.
    assert grammar(True, True) == "".join(
        slot.reads(True) for slot in TEMPLATE
    )


def _codes(**fields):
    return [v.code for v in SCHEMA.validate(_task(**fields))]


def _message(code, **fields):
    return next(
        v.message for v in SCHEMA.validate(_task(**fields)) if v.code == code
    )
