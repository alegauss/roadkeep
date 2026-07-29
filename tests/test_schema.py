"""The schema, checked against its own repository's backlog.

`docs/ROADMAP.md` is the conformance fixture (see agents.md): the corpus tests
below fail if the schema stops being able to express the 26 lines it was measured
from, which is the difference between a format proven by an artefact and one
asserted in a README.

The line reader at the bottom of this file is deliberately test-local and
throwaway — RK2 owns parsing, and until it lands the corpus tests need *some* way
to reach the fields. It is not imported from `roadkeep`.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from roadkeep import (
    DESIGNED,
    IDEA,
    SHIPPED,
    Dep,
    Schema,
    SchemaError,
    Task,
)

ROADMAP = Path(__file__).resolve().parents[1] / "docs" / "ROADMAP.md"

SCHEMA = Schema()


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
        ref="I.1",
    )
    fields.update(over)
    return Task(**fields)


# -- rendering -------------------------------------------------------------


def test_render_is_the_canonical_line():
    assert SCHEMA.render(task(symptom="Nothing knows what a task line is", why="a schema refuses.")) == (
        "- \U0001f4cb **RK1** (deps: —) **Nothing knows what a task line is** "
        "— a schema refuses. → §I.1"
    )


def test_empty_deps_render_as_an_em_dash():
    assert "(deps: —)" in SCHEMA.render(task(deps=()))


def test_deps_render_with_the_shipped_marker_only_when_shipped():
    line = SCHEMA.render(task(id="RK5", deps=(Dep("RK1", shipped=True), Dep("RK2"))))
    assert f"(deps: RK1 {SHIPPED}, RK2)" in line


def test_plain_string_deps_are_coerced():
    assert task(id="RK5", deps=("RK1",)).deps == (Dep("RK1", shipped=False),)


def test_a_task_without_a_ref_renders_without_the_arrow():
    assert "→" not in SCHEMA.render(task(ref=None))


# -- the corpus is the fixture ---------------------------------------------


def test_corpus_is_not_empty():
    # A corpus test over zero lines passes for the wrong reason.
    assert len(read_corpus()) >= 20


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


def test_a_ref_that_is_not_an_anchor_is_refused():
    assert {v.code for v in SCHEMA.validate(task(ref="I"))} == {"ref.format"}


# -- round-trip safety (refused, not repaired) -----------------------------


def test_a_newline_in_a_field_is_refused():
    codes = {v.code for v in SCHEMA.validate(task(symptom="two\nlines"))}
    assert codes == {"symptom.newline"}


def test_padding_is_refused_rather_than_trimmed():
    (violation,) = SCHEMA.validate(task(symptom=" padded "))
    assert violation.code == "symptom.whitespace"


def test_the_field_delimiter_cannot_appear_inside_a_field():
    codes = {v.code for v in SCHEMA.validate(task(symptom="a **bold** claim"))}
    assert codes == {"symptom.markup"}


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


# -- test-local line reader (RK2 replaces this) ----------------------------

_LINE = re.compile(
    r"^- (?P<status>\S+) \*\*(?P<id>[A-Z]+[0-9]+)\*\* \(deps: (?P<deps>[^)]*)\) "
    r"\*\*(?P<symptom>.+?)\*\* — (?P<why>.+?)"
    r"(?: → §(?P<ref>\S+))?$"
)
_BLOCK = re.compile(r"^## Block (?P<block>\S+)")


def read_corpus_lines() -> list[str]:
    return [line for line, _ in _read()]


def read_corpus() -> list[Task]:
    return [t for _, t in _read()]


def _read() -> list[tuple[str, Task]]:
    out: list[tuple[str, Task]] = []
    block = "?"
    for raw in ROADMAP.read_text(encoding="utf-8").splitlines():
        heading = _BLOCK.match(raw)
        if heading:
            block = heading.group("block")
            continue
        match = _LINE.match(raw)
        if not match:
            continue  # prose bullets (the non-goals) are not task lines
        deps = ()
        if match.group("deps") != "—":
            deps = tuple(
                Dep(d.split()[0], shipped=SHIPPED in d)
                for d in match.group("deps").split(", ")
            )
        out.append(
            (
                raw,
                Task(
                    id=match.group("id"),
                    status=match.group("status"),
                    block=block,
                    symptom=match.group("symptom"),
                    why=match.group("why"),
                    deps=deps,
                    ref=match.group("ref"),
                ),
            )
        )
    return out
