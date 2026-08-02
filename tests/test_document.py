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
from roadkeep.schema import RETIRED

HERE = Path(__file__).resolve().parents[1]

# Shio and Turing number their sections by hand; this repository derives the anchor
# from the id (RK27). Both are configurations of one format (L6).
OUTLINE = Schema(ref_scheme="outline")
OUTLINE_SH = Schema(prefixes=("SH",), ref_scheme="outline")
OUTLINE_T = Schema(prefixes=("T",), ref_scheme="outline")
ROADMAP = HERE / "docs" / "ROADMAP.md"
CHANGELOG = HERE / "docs" / "CHANGELOG.md"

#: Real backlogs that predate the tool, with their own prefixes (L6). Absent on
#: any machine but the author's, so every use is guarded.
#: The bound is 1 for the same reason `OWN`'s roadmap is: these files belong to other
#: projects and empty as those projects ship, so any floor above one is a count that
#: somebody else's progress crosses — 90, then 80, which fell the day Shio shipped SH270,
#: and a comment calling it slack does not make it slack (RK102). What the corpus is read
#: for is round-trip at a scale nothing here authored, and that needs no magnitude: the
#: floor's whole job is to fail when a parse silently read nothing.
FOREIGN = [
    (Path("D:/Git/viglet/shio/latest/docs/ROADMAP.md"), OUTLINE_SH, 1),
    (Path("D:/Git/viglet/turing/latest/docs/ROADMAP.md"), OUTLINE_T, 1),
]

# Lower bounds, not counts: shipping a task moves a line between these two files every
# commit, and a test that has to be edited by every commit gets edited without being read.
# The roadmap's floor is **zero**, which is the end of a sequence this comment recorded twice
# before it arrived: 10 fell to RK41, 5 fell to RK23, and 1 fell to RK21, which shipped the
# last open line there is. A backlog's finished state is empty, so any floor at all is a count
# progress crosses. The ledger's is the bound worth raising, because that file only grows —
# and with the roadmap empty it is the only half of this corpus that proves anything.
OWN = [(ROADMAP, Schema(), 0), (CHANGELOG, Schema().as_ledger(), 40)]

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
    # The two halves are independent, and conflating them is what makes a formatter
    # destructive: Shio's lines are over the limits *and* every one of them renders back
    # unchanged. Not a floor on how many offend — Shio rewrites those lines, and a suite
    # that counted them would go red for somebody else's progress (RK102). The magnitude
    # is owned by the fixture below; what the corpus adds is scale nothing here authored.
    path, schema, _ = FOREIGN[0]
    if not path.exists():
        pytest.skip(f"{path} is not on this machine")
    document = Document.load(path, schema)
    offenders = [e for e in document.entries if schema.validate(e.task)]
    if not offenders:
        pytest.skip(f"{path} no longer has a line to disagree with: nothing to prove here")
    assert document.non_canonical == ()


#: The two live ledgers, and a floor on what the parser must *say* about them. Lower
#: bounds like every other one here, and safe ones: a ledger only grows. Before RK43 both
#: numbers were 0 — 920 bullets in Shio read as prose, and the reject list that exists to
#: make a miss impossible was empty because nothing wore the marker slot wrongly.
FOREIGN_LEDGERS = [
    (Path("D:/Git/viglet/shio/latest/docs/CHANGELOG.md"), OUTLINE_SH, 150),
    (Path("D:/Git/viglet/turing/latest/docs/CHANGELOG.md"), OUTLINE_T, 500),
]


@pytest.mark.parametrize(
    "case", FOREIGN_LEDGERS, ids=lambda c: c[0].parent.parent.name
)
def test_a_live_ledger_that_carries_no_marker_is_reported_line_by_line(case):
    path, schema, minimum = case
    if not path.exists():
        pytest.skip(f"{path} is not on this machine")
    document = Document.load(path, schema.as_ledger())
    assert len(document.rejects) >= minimum
    assert all(reject.reason for reject in document.rejects)
    with path.open("r", encoding="utf-8", newline="") as handle:
        assert document.render() == handle.read()  # reported, and still not rewritten


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


def test_a_line_far_over_the_limits_still_renders_back_unchanged():
    # What the foreign backlog above is read for, at a magnitude this file owns: a
    # symptom many times the limit and a why of three sentences is rejected by
    # `validate` and untouched by `render`, which is the independence that keeps a
    # formatter from being destructive.
    over = (
        f"- {IDEA} **RK9** (deps: —) **{'A symptom that runs on ' * 8}and on** "
        f"— A reason. And a second sentence. And a third. → §RK9"
    )
    (entry,) = parse_in_block(over).entries
    assert {v.field for v in Schema().validate(entry.task)} == {"symptom", "why"}
    assert Schema().render(entry.task) == over


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


#: The ledger both live projects actually write: no marker, because every entry in it
#: shipped (RK43). Declared once in `[ledger] marker`, not repeated on 920 lines.
MARKERLESS = replace(Schema(), ledger_marker=False).as_ledger()


def test_a_ledger_that_declares_no_marker_reads_its_lines_and_renders_them_back():
    line = "- **RK1** **A symptom** — a reason."
    (entry,) = parse_in_block(line, schema=MARKERLESS).entries
    # The status is the file's, not the line's: a ledger carrying no marker is a ledger
    # where everything in it shipped, which is the whole content of the declaration.
    assert entry.task.status == SHIPPED
    assert MARKERLESS.render(entry.task) == line
    assert MARKERLESS.validate(entry.task) == ()


def test_a_marker_in_a_ledger_that_declares_none_is_reported_not_read():
    document = parse_in_block(
        f"- {SHIPPED} **RK1** **A symptom** — a reason.", schema=MARKERLESS
    )
    assert document.entries == ()
    (reject,) = document.rejects
    assert "carry none" in reject.reason


def test_a_retired_line_cannot_be_written_to_a_ledger_that_declares_no_marker():
    # The one thing the declaration costs (RK32): with no slot to carry 🗑, a retired
    # line would read as shipped, so it is refused rather than recorded as a lie.
    task = Task(id="RK1", status=RETIRED, block="A", symptom="A symptom", why="a reason.")
    assert {v.code for v in MARKERLESS.validate(task)} == {"status.unrepresentable"}


#: The other slot both live ledgers lack (RK48): `- **SH134** — <prose>`, with no bold
#: symptom before the em dash — 234 lines in Shio and 761 in Turing.
NO_SLOTS = replace(Schema(), ledger_marker=False, ledger_symptom=False).as_ledger()


def test_a_ledger_with_no_symptom_slot_reads_the_tail_as_the_why_and_renders_it_back():
    line = "- **RK1** — **`post.move`**, the seventh op, moves an address in place."
    (entry,) = parse_in_block(line, schema=NO_SLOTS).entries
    assert entry.task.id == "RK1"
    assert entry.task.symptom == ""  # the slot does not exist, so the field is empty
    assert entry.task.why.startswith("**`post.move`**")
    # L3 is not relaxed for a file whose history nobody will rewrite: the line comes back.
    assert NO_SLOTS.render(entry.task) == line
    assert NO_SLOTS.validate(entry.task) == ()


def test_an_absent_symptom_slot_is_not_an_empty_one():
    # `- **SH1** ****  — …` would be the shape a blank field renders as, and no ledger
    # writes it. The bold is omitted entirely, which is what makes the round-trip hold.
    task = Task(id="SH1", status=SHIPPED, block="A", symptom="", why="a reason.")
    assert NO_SLOTS.render(task) == "- **SH1** — a reason."
    assert "****" not in NO_SLOTS.render(task)


def test_the_symptom_slot_is_only_droppable_in_the_ledger():
    # The roadmap keeps both slots whatever the ledger declares: a backlog of reasons with
    # no faults could not say what does not work, which is the one field that must exist.
    roadmap = replace(Schema(), ledger_marker=False, ledger_symptom=False)
    assert roadmap.symptom_field and roadmap.marker_field


def test_a_bullet_leading_with_a_bold_id_is_rejected_rather_than_read_as_prose():
    # Measured on Shio: 920 changelog lines, 0 entries *and* 0 rejects. The marker slot
    # is not wrong here, it is empty, which is what made the miss silent twice (RK43).
    document = parse_in_block(
        "- **SH134** — **`post.move`**, the seventh op.", schema=Schema().as_ledger()
    )
    assert document.entries == ()
    (reject,) = document.rejects
    assert "no marker where the status goes" in reject.reason
    # And it names the declaration that turns those lines into entries.
    assert "[ledger] marker = false" in reject.reason


@pytest.mark.parametrize(
    "line",
    [
        "- **Delete** the 3 old files after migration",  # bold, and no digit: prose
        "- **SH239**: a benchmark pair wrote into the folder another pair measured",
        "- See **RK5** for the design.",
        "- **No web UI and no server.** Files and a CLI.",
    ],
)
def test_prose_that_also_leads_with_bold_stays_prose(line):
    # The widened test is the one that could make the report noise, and a noisy report
    # is an ignored one: it takes an id-shaped token and nothing else in the slot.
    document = parse_in_block(line, schema=Schema().as_ledger())
    assert document.entries == () and document.rejects == ()


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


# -- a nested task, and a quoted one (RK49, RK53) ---------------------------


def test_an_indented_task_line_is_a_task_and_keeps_its_indentation():
    # Shio nests four live tasks under the line that shipped their parent, so rejecting an
    # indented line made SH44–SH47 invisible to every count, to `pick`, and to `next-id`.
    line = f"  - {IDEA} **RK9** (deps: —) **A symptom** — a reason. → §RK9"
    (entry,) = parse_in_block(line).entries
    assert entry.task.id == "RK9" and entry.task.indent == "  "
    # The indentation is part of the line, so `render` puts it back byte for byte (L3).
    assert Schema().render(entry.task) == line


def test_the_ledger_entry_a_nested_line_ships_into_starts_at_column_zero():
    from roadkeep.shipping import _as_recorded

    nested = Task(id="RK9", status=IDEA, block="A", symptom="A symptom", why="a reason.", indent="  ")
    assert _as_recorded(nested, SHIPPED, None).indent == ""


@pytest.mark.parametrize("fence", ["```", "~~~", "```toml", "   ```"])
def test_a_task_line_inside_a_fence_is_quoted_text_and_not_a_task(fence):
    document = parse_in_block(
        fence,
        f"- {IDEA} **RK9** (deps: —) **A symptom** — a reason. → §RK9",
        fence.strip()[:3],
    )
    assert document.entries == () and document.rejects == ()


def test_a_fence_is_closed_only_by_its_own_kind():
    # ``` inside a ~~~ block is text, which is what a renderer does with it — and the only
    # way a section quoting one fence inside another can be read at all.
    document = parse_in_block(
        "~~~",
        "```",
        f"- {IDEA} **RK9** (deps: —) **A symptom** — a reason. → §RK9",
        "```",
        "~~~",
    )
    assert document.entries == ()


def test_a_line_after_the_fence_closes_is_read_again():
    document = parse_in_block(
        "```",
        f"- {IDEA} **RK1** (deps: —) **Quoted** — a reason. → §RK1",
        "```",
        f"- {IDEA} **RK9** (deps: —) **Real** — a reason. → §RK9",
    )
    assert [e.task.id for e in document.entries] == ["RK9"]


def test_a_heading_inside_a_fence_does_not_close_the_block():
    # Otherwise a `## Block` in a quoted example would file every following task under it.
    document = parse_in_block(
        "```",
        "## Block Z — quoted, not declared",
        "```",
        f"- {IDEA} **RK9** (deps: —) **A symptom** — a reason. → §RK9",
    )
    (entry,) = document.entries
    assert entry.task.block == "A"


# -- rejects name their reason ---------------------------------------------


@pytest.mark.parametrize(
    ("line", "expected"),
    [
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


# -- what a heading owns, asked of the document (RK115) ---------------------


def nested_file() -> Document:
    return parse(
        "# Title",
        "intro",
        "## Block A — The model",
        "preamble",
        "### A nested heading",
        "nested prose",
        "## Block B — Authoring",
        "b prose",
    )


def test_the_subtree_reaches_past_a_nested_heading_and_stops_at_the_next_peer():
    document = nested_file()
    # `## Block A` is line 3 (1-based); `## Block B` is line 7, so the subtree it owns is
    # everything up to index 6 — the nested `###` included, because a drop takes it.
    assert document.subtree_end(document.heading("A")) == 6
    assert document.subtree_end(document.heading("B")) == len(document.lines)


def test_the_prose_a_heading_owns_stops_at_the_nested_heading():
    document = nested_file()
    # The narrower answer: `### A nested heading` is line 5, so Block A's own prose is
    # the one line at index 3. A budget charging Block A may not count the subsection.
    assert document.prose_end(document.heading("A")) == 4


def test_the_two_answers_are_the_same_where_nothing_is_nested():
    document = parse("## Block A — The model", "a", "## Block B — Authoring", "b")
    for label in ("A", "B"):
        heading = document.heading(label)
        assert document.subtree_end(heading) == document.prose_end(heading)


def test_a_heading_at_the_end_of_the_file_owns_the_rest_of_it():
    document = nested_file()
    last = document.headings[-1]
    assert document.subtree_end(last) == document.prose_end(last) == len(document.lines)


def test_the_live_roadmap_files_every_task_under_a_block():
    # Both governed files, because the claim is about the parser and not about the backlog:
    # this repository's roadmap is empty (RK21 shipped its last line), so asked of that file
    # alone the assertion would hold over nothing. The ledger carries the same 100 lines, each
    # filed under the block it belonged to.
    for path, schema in ((ROADMAP, Schema()), (CHANGELOG, Schema().as_ledger())):
        document = Document.load(path, schema)
        assert all(entry.task.block for entry in document.entries)
    assert Document.load(CHANGELOG, Schema().as_ledger()).entries


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
