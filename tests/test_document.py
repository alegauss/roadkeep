"""Round-trip as the ownership test (RK2).

The property under test is one sentence: **for every real file, parse → render is
byte-identical, and every line the parser claims to understand renders back to
exactly what was written.** It is a property test over a corpus of real backlogs
rather than an example test, because the corruption it guards against is precisely
the case nobody thought to write an example for.

The corpus is this repository's `docs/` plus Shio's and Turing's roadmaps when
they are on this machine — 144 task lines across four files, three prefixes and
two projects that never heard of this tool. Those two skip cleanly elsewhere, so
CI tests what it has.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from roadkeep import DESIGNED, IDEA, PARTIAL, SHIPPED, Dep, Schema, Task
from roadkeep.document import Document, RoundTripError

HERE = Path(__file__).resolve().parents[1]

# Shio and Turing number their sections by hand; this repository derives the anchor
# from the id (RK27). Both are configurations of one format (L6).
OUTLINE = Schema(ref_scheme="outline")
OUTLINE_SH = Schema(prefix="SH", ref_scheme="outline")
OUTLINE_T = Schema(prefix="T", ref_scheme="outline")
ROADMAP = HERE / "docs" / "ROADMAP.md"
CHANGELOG = HERE / "docs" / "CHANGELOG.md"

#: Real backlogs that predate the tool, with their own prefixes (L6). Absent on
#: any machine but the author's, so every use is guarded.
FOREIGN = [
    (Path("D:/Git/viglet/shio/latest/docs/ROADMAP.md"), OUTLINE_SH, 90),
    (Path("D:/Git/viglet/turing/latest/docs/ROADMAP.md"), OUTLINE_T, 25),
]

# Lower bounds, not counts: shipping a task moves a line between these two files
# every commit, and a test that has to be edited by every commit gets edited without
# being read.
OWN = [(ROADMAP, Schema(), 20), (CHANGELOG, Schema().as_ledger(), 1)]

LINE = (
    f"- {DESIGNED} **RK9** (deps: RK5 {SHIPPED}) **A symptom** "
    f"— a reason. → §RK9"
)


def corpus() -> list[tuple[Path, Schema, int]]:
    return OWN + [c for c in FOREIGN if c[0].exists()]


# -- the property ----------------------------------------------------------


@pytest.mark.parametrize("case", corpus(), ids=lambda c: c[0].parent.parent.name)
def test_a_file_renders_back_byte_for_byte(case):
    path, schema, _ = case
    with path.open("r", encoding="utf-8", newline="") as handle:
        source = handle.read()
    assert Document.load(path, schema).render() == source


@pytest.mark.parametrize("case", corpus(), ids=lambda c: c[0].parent.parent.name)
def test_every_understood_line_renders_back_to_what_was_written(case):
    path, schema, minimum = case
    document = Document.load(path, schema)
    assert len(document.entries) >= minimum
    assert document.non_canonical == ()
    document.ensure_writable()  # the file may be owned


@pytest.mark.parametrize("case", corpus(), ids=lambda c: c[0].parent.parent.name)
def test_no_marker_bearing_line_is_silently_dropped(case):
    path, schema, _ = case
    document = Document.load(path, schema)
    # Every reject carries a reason; a line understood by nobody and reported by
    # nobody is the failure mode of the grep this replaces.
    assert all(reject.reason for reject in document.rejects)


def test_a_foreign_backlog_round_trips_while_failing_validation():
    # The two halves are independent, and conflating them is what makes a
    # formatter destructive: Shio's lines are far over the limits *and* every one
    # of them renders back unchanged.
    path, schema, _ = FOREIGN[0]
    if not path.exists():
        pytest.skip(f"{path} is not on this machine")
    document = Document.load(path, schema)
    assert document.non_canonical == ()
    offenders = [e for e in document.entries if schema.validate(e.task)]
    assert len(offenders) > 50


def test_our_own_roadmap_has_no_rejects():
    # The non-goals are prose bullets, not malformed tasks: reporting them would
    # make the reject list noise, and a noisy report is an ignored one.
    assert Document.load(ROADMAP, Schema()).rejects == ()


# -- parsing ---------------------------------------------------------------


def parse(*body: str, schema: Schema | None = None) -> Document:
    return Document.parse("".join(f"{line}\n" for line in body), schema=schema)


def parse_in_block(*body: str, schema: Schema | None = None) -> Document:
    """As `parse`, under a block heading — a task outside one has no block (RK14)."""
    return parse("## Block A — The model", *body, schema=schema)


def test_fields_survive_the_round_trip_through_data():
    (entry,) = parse("## Block B — Authoring", LINE).entries
    assert entry.task == Task(
        id="RK9",
        status=DESIGNED,
        block="B",
        symptom="A symptom",
        why="a reason.",
        deps=(Dep("RK5", SHIPPED),),
        ref="RK9",
    )
    assert entry.lineno == 2


def test_the_pointer_is_taken_from_the_end_not_the_first_match():
    # RK15's own line quotes "→ §x.y" inside its why as an example; a scan from
    # the left truncates the sentence there and the line stops round-tripping.
    quoted = (
        f"- {DESIGNED} **RK15** (deps: RK14) **A pointer that does not resolve** "
        f"— resolve every `→ §x.y` against the file. → §IV.2"
    )
    (entry,) = parse(quoted, schema=OUTLINE).entries
    assert entry.task.ref == "IV.2"
    assert entry.task.why == "resolve every `→ §x.y` against the file."
    assert OUTLINE.render(entry.task) == quoted


def test_a_dep_the_parser_does_not_understand_is_still_counted():
    # Shio has "(deps: Block P)"; both parse, and since RK28 both also validate — a
    # block is a legitimate thing to wait on. What must not happen either way is the
    # line dropping out of the count.
    line = f"- {IDEA} **RK9** (deps: Block P, RK5 {PARTIAL}) **A symptom** — a reason. → §RK9"
    document = parse_in_block(line)
    (entry,) = document.entries
    assert entry.task.deps == (Dep("Block P"), Dep("RK5", PARTIAL))
    assert document.non_canonical == ()  # it round-trips
    assert Schema().validate(entry.task) == ()


def test_an_id_shaped_dep_from_another_backlog_is_still_reported():
    line = f"- {IDEA} **RK9** (deps: SH341) **A symptom** — a reason. → §RK9"
    (entry,) = parse_in_block(line).entries
    assert {v.code for v in Schema().validate(entry.task)} == {"deps.format"}


def test_no_deps_parses_as_none_and_renders_back():
    line = f"- {IDEA} **RK1** (deps: —) **A symptom** — a reason. → §RK1"
    (entry,) = parse_in_block(line).entries
    assert entry.task.deps == ()
    assert Schema().render(entry.task) == line


def test_the_ledger_shape_is_a_configuration_of_the_same_grammar():
    ledger = Schema().as_ledger()
    line = f"- {SHIPPED} **RK1** **A symptom** — a reason."
    (entry,) = parse_in_block(line, schema=ledger).entries
    assert entry.task.deps == ()
    assert entry.task.ref is None
    assert ledger.render(entry.task) == line
    assert ledger.validate(entry.task) == ()


def test_a_roadmap_line_without_its_deps_field_is_reported():
    document = parse_in_block(f"- {IDEA} **RK1** **A symptom** — a reason. → §RK1")
    (reject,) = document.rejects
    assert "(deps: …)" in reject.reason


def test_a_block_heading_sets_the_block_and_a_plain_heading_clears_it():
    document = parse(
        "## Block A — The model",
        LINE.replace("RK9", "RK1"),
        "## Priority queue",
        LINE.replace("RK9", "RK2"),
    )
    assert [e.task.block for e in document.entries] == ["A", ""]


def test_a_multi_letter_block_label_is_read():
    # Turing's blocks reach BJ, and one heading is "Block J follow-ups".
    document = parse("## Block BJ — Lexicon", "## Block J follow-ups — Cloud")
    assert [h.label for h in document.headings] == ["BJ", "J"]


def test_prose_bullets_are_not_tasks_and_not_rejects():
    document = parse("- **No web UI and no server.** Files and a CLI.", "- plain text")
    assert document.entries == () and document.rejects == ()


# -- rejects name their reason ---------------------------------------------


@pytest.mark.parametrize(
    ("line", "expected"),
    [
        (f"  - {IDEA} **RK9** (deps: —) **A symptom** — a reason. → §RK9", "indented"),
        (f"- {IDEA} RK9 (deps: —) **A symptom** — a reason.", "bold"),
        (f"- {IDEA} **RK9** (deps: —) **A symptom** - a reason.", "between the symptom"),
        (f"* {IDEA} **RK9** (deps: —) **A symptom** — a reason.", "one dash"),
    ],
)
def test_a_marker_bearing_line_that_fails_the_grammar_says_why(line, expected):
    document = parse(line)
    assert document.entries == ()
    (reject,) = document.rejects
    assert expected in reject.reason


def test_a_deps_field_in_the_ledger_is_reported_as_one():
    document = parse(
        f"- {SHIPPED} **RK1** (deps: —) **A symptom** — a reason.",
        schema=Schema().as_ledger(),
    )
    (reject,) = document.rejects
    assert "carries none" in reject.reason


def test_extra_whitespace_after_the_bullet_is_reported_not_skipped():
    document = parse(f"-  {IDEA} **RK9** (deps: —) **A symptom** — a reason. → §RK9")
    assert document.entries == ()
    assert len(document.rejects) == 1


# -- refusing to write -----------------------------------------------------

#: A marker with a variation selector appended: identical on screen, a different
#: string to every tool. This is the drift a byte comparison exists to catch —
#: and the reason the parser reads such a line at all instead of skipping it.
INVISIBLE = f"- {DESIGNED}\ufe0f **RK9** (deps: —) **A symptom** — a reason. → §RK9"


def broken() -> Document:
    """A document whose lines were written under a different configuration.

    The parser is lossless by construction — every branch either keeps the text in
    a field or rejects the line — so a file it reads round-trips. What does not is
    a file read under one config and rendered under another: change `deps_field` or
    the marker set in `roadkeep.toml` (RK3) and every existing line would come back
    reformatted. That is the case the guard is for: **a configuration change is not
    a licence to rewrite files written before it.**
    """
    return replace(parse_in_block(LINE), schema=Schema().as_ledger())


def test_an_invisible_marker_is_read_and_reported_rather_than_skipped():
    # 📋 followed by U+FE0F is a different string and the same picture. Reading it
    # is what lets lint say so; skipping it would leave the drift uncounted.
    (entry,) = parse_in_block(INVISIBLE).entries
    assert entry.task.status != DESIGNED
    assert {v.code for v in Schema().validate(entry.task)} == {"status.unknown"}


def test_a_line_that_does_not_round_trip_blocks_every_write(tmp_path):
    document = broken()
    assert len(document.non_canonical) == 1
    for attempt in (
        lambda d: d.replace_line(0, "x"),
        lambda d: d.insert_line(0, "x"),
        lambda d: d.remove_line(0),
        lambda d: d.save(tmp_path / "out.md"),
    ):
        with pytest.raises(RoundTripError, match="will not be rewritten"):
            attempt(document)


def test_the_refusal_names_the_line_a_human_has_to_look_at():
    with pytest.raises(RoundTripError) as caught:
        broken().ensure_writable()
    assert "RK9" in str(caught.value) and "line 2" in str(caught.value)


# -- writing ---------------------------------------------------------------


def test_replacing_a_task_rewrites_only_its_line():
    document = parse("## Block B — Authoring", LINE, "trailing prose")
    (entry,) = document.entries
    after = document.replace_task(entry, Task(**{**vars_of(entry.task), "status": IDEA}))
    assert after.lines[0] == "## Block B — Authoring\n"
    assert after.lines[2] == "trailing prose\n"
    assert after.entries[0].task.status == IDEA
    assert after.render() == document.render().replace(DESIGNED, IDEA)


def test_an_inserted_line_takes_the_files_own_ending():
    document = Document.parse("## Block A — The model\r\nprose\r\n")
    after = document.insert_line(1, LINE)
    assert after.render() == f"## Block A — The model\r\n{LINE}\r\nprose\r\n"
    assert after.entries[0].task.id == "RK9"


def test_appending_to_a_file_without_a_final_newline_does_not_glue_the_lines():
    document = Document.parse("## Block A — The model\nprose")
    after = document.insert_line(len(document.lines), LINE)
    assert after.render() == f"## Block A — The model\nprose\n{LINE}\n"


def test_a_file_without_a_final_newline_keeps_it_that_way():
    source = "## Block A — The model\nprose"
    assert Document.parse(source).render() == source


def test_removing_a_line_leaves_the_rest_verbatim():
    document = parse("## Block A — The model", LINE, "prose")
    after = document.remove_line(1)
    assert after.render() == "## Block A — The model\nprose\n"
    assert after.entries == ()


def test_line_numbers_are_recomputed_after_an_edit():
    document = parse(LINE)
    after = document.insert_line(0, "## Block B — Authoring")
    assert after.entries[0].lineno == 2
    assert after.entries[0].task.block == "B"


def test_save_writes_what_render_says_and_nothing_else(tmp_path):
    target = tmp_path / "ROADMAP.md"
    document = parse("## Block A — The model", LINE)
    document.save(target)
    with target.open("r", encoding="utf-8", newline="") as handle:
        assert handle.read() == document.render()


def test_a_document_parsed_from_text_has_nowhere_to_save_to():
    with pytest.raises(ValueError, match="no path"):
        parse(LINE).save()


# -- lookups ---------------------------------------------------------------


def test_entries_are_reachable_by_id_and_by_block():
    document = parse(
        "## Block A — The model",
        LINE.replace("RK9", "RK1"),
        "## Block B — Authoring",
        LINE,
    )
    assert document.by_id()["RK9"].task.block == "B"
    assert [e.task.id for e in document.block("A")] == ["RK1"]
    assert document.heading("B").text.startswith("Block B")


def test_the_live_roadmap_files_every_task_under_a_block():
    document = Document.load(ROADMAP, Schema())
    assert document.entries
    assert all(entry.task.block for entry in document.entries)


def vars_of(task: Task) -> dict:
    return {
        "id": task.id,
        "status": task.status,
        "block": task.block,
        "symptom": task.symptom,
        "why": task.why,
        "deps": task.deps,
        "ref": task.ref,
    }
