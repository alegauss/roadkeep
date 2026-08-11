"""Round-trip as the ownership test (RK2).

The property under test is one sentence: **for every real file, parse → render is
byte-identical, and every line the parser claims to understand renders back to
exactly what was written.** It is a property test over a corpus of real backlogs
rather than an example test, because the corruption it guards against is precisely
the case nobody thought to write an example for.

The corpus is this repository's `docs/` plus **both governed line files** of Shio and
Turing when they are on this machine — six files, three prefixes and two projects that
never heard of this tool. The foreign halves skip cleanly elsewhere, so CI tests what it
has, and they are read at a pin (RK105) so somebody else's afternoon cannot turn this red.

The ledgers were added last and for a measured reason (RK182): RK157 was a silent
misfiling of an entry whose bullet **wraps**, 146 of Shio's 290 entries do and 3 of
Turing's 801, and a governed roadmap has none by construction — so the property read every
file except the kind the defect was in, and passed throughout.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

import corpora
from surface import address, modules
from roadkeep import DESIGNED, IDEA, PARTIAL, SHIPPED, Dep, Schema, Task
from roadkeep.kernel.document import (
    Document,
    RoundTripError,
    StaleFile,
    UnknownBlock,
    _parsed,
    declares,
    shading,
    write_atomically,
)
from roadkeep.kernel.schema import RETIRED

HERE = Path(__file__).resolve().parents[1]

# Shio and Turing number their sections by hand; this repository derives the anchor
# from the id (RK27). Both are configurations of one format (L6).
OUTLINE = Schema(ref_scheme="outline")
OUTLINE_SH = Schema(prefixes=("SH",), ref_scheme="outline")
OUTLINE_T = Schema(prefixes=("T",), ref_scheme="outline")
ROADMAP = HERE / "docs" / "ROADMAP.md"
CHANGELOG = HERE / "docs" / "CHANGELOG.md"

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


@dataclass(frozen=True, slots=True)
class Case:
    """One file in the corpus: its bytes, the schema that reads them, and what it holds.

    Bytes and not a path, because the foreign half is read **at a pinned revision** and a
    revision has no file (RK105) — which is also why ``path`` is None there: file ownership
    is a fact about this disk, and a blob has none. ``entries`` is a floor for this
    repository's own files, whose count moves with every commit, and an exact number for a
    pinned one, whose count cannot move at all.
    """

    name: str
    source: str
    schema: Schema
    entries: int
    path: Path | None = None
    #: Whether ``entries`` is the number or the floor.
    exact: bool = False


def _read(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


#: What each pinned corpus holds at its pin, per role. Exact, because that is the whole of
#: RK105: at a revision these are measurements rather than floors somebody else's progress
#: crosses — 90, then 80, which fell the day Shio shipped SH270, then 1, which is a number
#: that proves only that the parse read *something*. Re-measured when a pin moves, on
#: purpose and in that commit.
#:
#: **The ledgers are here because the wrapped shape lives in them** (RK182). RK157 was a
#: silent misfiling of an entry whose bullet wraps, and a governed roadmap has none by
#: construction — the format has no multi-line task line. Counted while fixing it: 146 of
#: Shio's 290 entries wrap and 3 of Turing's 801, so the one place the shape occurs at scale
#: was the one kind of file this property did not read, and it passed on every file for as
#: long as the defect existed. What made two more files affordable is RK105: they are read
#: at a pin, so they cannot turn this suite red for somebody else's afternoon.
PINNED = {
    ("shio", "roadmap"): 48,
    ("shio", "changelog"): 290,
    ("turing", "roadmap"): 37,
    ("turing", "changelog"): 801,
}


def corpus() -> list[Case]:
    """This repository's own files, plus each pinned corpus that is here to be read."""
    cases = [
        Case(path.name, _read(path), schema, floor, path)
        for path, schema, floor in OWN
    ]
    for (name, role), count in PINNED.items():
        found = next(c for c in corpora.BOTH if c.name == name)
        if not corpora.present(found) or not corpora.has(found, role):
            continue
        cases.append(
            Case(
                name=f"{name}-{role}",
                source=corpora.text(found, role),
                schema=corpora.config(found).schema_for(role),
                entries=count,
                exact=True,
            )
        )
    return cases


# -- the property ----------------------------------------------------------


@pytest.mark.parametrize("case", corpus(), ids=lambda c: c.name)
def test_a_file_renders_back_byte_for_byte(case):
    assert Document.parse(case.source, schema=case.schema).render() == case.source


@pytest.mark.parametrize("case", corpus(), ids=lambda c: c.name)
def test_every_understood_line_renders_back_to_what_was_written(case):
    document = Document.parse(case.source, schema=case.schema)
    if case.exact:
        assert len(document.entries) == case.entries
    else:
        assert len(document.entries) >= case.entries
    assert document.non_canonical == ()
    if case.path is not None:
        Document.load(case.path, case.schema).ensure_writable()  # the file may be owned


@pytest.mark.parametrize("case", corpus(), ids=lambda c: c.name)
def test_no_two_entries_claim_the_same_line(case):
    # The span RK157 gave every entry, as a property: an entry ends before the next one
    # starts, so no write can insert into one or remove part of another. The shape that
    # motivated it — a bullet that wraps — lived in a *ledger* this corpus did not read,
    # which is exactly why the property test did not catch it (RK182).
    document = Document.parse(case.source, schema=case.schema)
    for earlier, later in zip(document.entries, document.entries[1:]):
        assert earlier.stop < later.lineno, (earlier.task.id, later.task.id)
    assert all(entry.stop <= len(document.lines) for entry in document.entries)


#: How many entries wrap in each pinned ledger. Counted while fixing RK157 and asserted
#: here, because the widening above is only worth what the corpus actually carries: a pin
#: that moved to a ledger with no wrapped bullet would leave the property reading four files
#: and testing the same three shapes, which is the failure this task was filed about.
WRAPPING = {"shio": 146, "turing": 3}


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_the_pinned_ledgers_carry_the_shape_this_property_is_read_for(corpus):
    corpora.require(corpus)
    document = corpora.document(corpus, "changelog")
    wrapped = [entry for entry in document.entries if entry.stop > entry.lineno]
    assert len(wrapped) == WRAPPING[corpus.name]
    # And the roadmaps have none, by construction: "no multi-line task line" is a non-goal,
    # so the one file kind the corpus already read could never have contained the shape.
    roadmap = corpora.document(corpus, "roadmap")
    assert [e for e in roadmap.entries if e.stop > e.lineno] == []


@pytest.mark.parametrize("case", corpus(), ids=lambda c: c.name)
def test_no_marker_bearing_line_is_silently_dropped(case):
    document = Document.parse(case.source, schema=case.schema)
    # Every reject carries a reason; a line understood by nobody and reported by
    # nobody is the failure mode of the grep this replaces.
    assert all(reject.reason for reject in document.rejects)


def test_a_foreign_backlog_round_trips_while_failing_validation():
    # The two halves are independent, and conflating them is what makes a formatter
    # destructive: a line over the limits still renders back unchanged. What the pin buys
    # here is that the *absence* of offenders is a fact rather than a flake (RK105): Shio
    # rewrote those lines, so at this revision there are none, and the skip below says so
    # once instead of appearing and disappearing with somebody else's afternoon.
    corpora.require(corpora.SHIO)
    schema = corpora.config(corpora.SHIO).schema_for("roadmap")
    document = corpora.document(corpora.SHIO, "roadmap")
    offenders = [e for e in document.entries if schema.validate(e.task)]
    assert document.non_canonical == ()
    if not offenders:
        pytest.skip(f"{corpora.SHIO} conforms: it has no line left to disagree with")
    assert document.render() == corpora.text(corpora.SHIO, "roadmap")


#: What each pinned ledger yields when it is read under a schema that **expects** the marker
#: slot it does not carry: every line a reject, each with a reason. A deliberate
#: misconfiguration, which is why the corpus's own `[ledger] marker = false` is not used here
#: — before RK43 these numbers were 0, and 920 bullets in Shio read as prose because nothing
#: wore the slot wrongly. Exact at the pin (RK105); the ledgers grow between pins.
UNMARKED_LEDGERS = {"shio": 290, "turing": 801}


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_a_live_ledger_that_carries_no_marker_is_reported_line_by_line(corpus):
    corpora.require(corpus)
    source = corpora.text(corpus, "changelog")
    schema = replace(
        corpora.config(corpus).schema_for("changelog"), marker_field=True
    )
    document = Document.parse(source, schema=schema)
    assert len(document.rejects) == UNMARKED_LEDGERS[corpus.name]
    assert all(reject.reason for reject in document.rejects)
    assert document.render() == source  # reported, and still not rewritten


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


def test_a_retirement_is_the_one_line_a_markerless_ledger_marks():
    # What the declaration no longer costs (RK125 against RK32): the file says every entry
    # in it shipped, so the one that did not is the one line that has to carry a marker —
    # and it round-trips, which is what makes it a line this tool may write.
    task = Task(id="RK1", status=RETIRED, block="A", symptom="A symptom", why="a reason.")
    line = MARKERLESS.render(task)
    assert line == f"- {RETIRED} **RK1** **A symptom** — a reason."
    assert MARKERLESS.validate(task) == ()
    (entry,) = parse_in_block(line, schema=MARKERLESS).entries
    assert entry.task.status == RETIRED  # not the file's ✅, which is the whole point
    assert MARKERLESS.render(entry.task) == line


def test_every_other_marker_is_still_unwritable_there():
    # The declaration still means what it says: an open line in a file whose status is the
    # file's would read as shipped, and 🗑 is the exception the file's own claim creates.
    task = Task(id="RK1", status=DESIGNED, block="A", symptom="A symptom", why="a reason.")
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


@pytest.mark.parametrize(
    ("line", "box"),
    [
        ("- [ ] **C40** · a task in somebody else's convention", "[ ]"),
        ("- [x] **C40** · the same convention, checked", "[x]"),
        ("- [X] **C40** · and shouted", "[X]"),
        ("- [] **C40** · and written without the space", "[]"),
    ],
)
def test_a_task_list_checkbox_is_rejected_rather_than_read_as_prose(line, box):
    # Measured on cursarei: 16 of these, 0 entries *and* 0 rejects (RK103). `[ ]` is two
    # tokens where a marker is one, so nothing that catches a wrong or missing marker fired.
    document = parse_in_block(line)
    assert document.entries == ()
    (reject,) = document.rejects
    assert box in reject.reason and "task-list checkbox" in reject.reason


def test_a_checkbox_is_a_reject_in_a_markerless_ledger_too():
    # The slot the file declares does not decide this one: a checkbox is another
    # convention's whole line whether this file's marker slot holds a marker or nothing.
    document = parse_in_block("- [ ] **SH134** — the seventh op.", schema=MARKERLESS)
    assert document.entries == ()
    assert "task-list checkbox" in document.rejects[0].reason


@pytest.mark.parametrize(
    "line",
    [
        "- [ ] write the migration script",  # a prose checklist: no bold id
        "- [ ] **Delete** the 3 old files",  # bold, and no digit
        "- [Website](https://example.com/): the landing page",  # a link, not a box
    ],
)
def test_a_checklist_that_is_not_a_backlog_stays_prose(line):
    # The bold id after the box is the whole difference: without it every checklist in
    # every rationale file would arrive as work somebody has to migrate.
    document = parse_in_block(line)
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


# -- the file that moved under the writer (RK116) ---------------------------


def loaded(tmp_path: Path, *lines: str) -> Document:
    target = tmp_path / "ROADMAP.md"
    target.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="")
    return Document.load(target)


def test_a_write_onto_a_file_that_changed_since_it_was_read_is_refused(tmp_path):
    # The defect, staged: two processes read the same file, each removes its own line, and
    # the second write used to land on top of the first — the loser's line gone, exit 0.
    first = loaded(tmp_path, "## Block A — The model", LINE, LINE.replace("RK9", "RK1"))
    second = Document.load(first.path)
    first.remove_line(1).save()
    losing = second.remove_line(2)
    with pytest.raises(StaleFile, match="changed since it was read"):
        losing.save()
    # And the first writer's edit is still on disk, which is the whole claim.
    assert "RK9" not in first.path.read_text(encoding="utf-8")
    assert "RK1" in first.path.read_text(encoding="utf-8")


def test_an_unchanged_file_is_written_without_complaint(tmp_path):
    document = loaded(tmp_path, "## Block A — The model", LINE)
    after = document.insert_line(len(document.lines), LINE.replace("RK9", "RK1"))
    after.save()
    assert "RK1" in document.path.read_text(encoding="utf-8")


def test_a_write_repeated_on_the_same_document_is_refused_the_second_time(tmp_path):
    # `save` does not re-baseline: the document still remembers the read, and its own
    # first write is a change like any other. A caller that means to write twice re-reads.
    document = loaded(tmp_path, "## Block A — The model", LINE)
    after = document.remove_line(1)
    after.save()
    with pytest.raises(StaleFile):
        after.save()


def test_a_file_deleted_under_the_writer_is_named_as_gone_and_not_recreated(tmp_path):
    document = loaded(tmp_path, "## Block A — The model", LINE)
    after = document.remove_line(1)
    document.path.unlink()
    with pytest.raises(StaleFile, match="no longer exists"):
        after.save()
    assert not document.path.exists()


def test_a_document_parsed_from_a_string_has_no_disk_state_to_have_moved(tmp_path):
    # `save(path)` to a file this document was never read from is a write, not an overwrite
    # of something it misremembers — `init` and every test above depend on it.
    target = tmp_path / "ROADMAP.md"
    target.write_text("something else\n", encoding="utf-8", newline="")
    parse("## Block A — The model", LINE).save(target)
    assert "RK9" in target.read_text(encoding="utf-8")


def test_saving_a_loaded_document_elsewhere_is_a_different_file_and_not_a_changed_one(
    tmp_path,
):
    document = loaded(tmp_path, "## Block A — The model", LINE)
    document.path.write_text("moved on\n", encoding="utf-8", newline="")
    document.save(tmp_path / "COPY.md")  # the target it names is untouched by that
    assert "RK9" in (tmp_path / "COPY.md").read_text(encoding="utf-8")


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


# -- is that block still occupied (RK300) -----------------------------------


def test_a_block_with_a_line_is_held_and_one_without_is_not():
    document = parse(
        "## Block A — The model",
        LINE.replace("RK9", "RK1"),
        "## Block B — Authoring",
    )
    assert document.holds("A") and not document.holds("B")
    # A label no heading declares is not held either, which is the answer a caller iterating
    # over one tree's headings against another's needs (RK269).
    assert not document.holds("Z")


def test_the_predicate_agrees_with_the_tuple_it_replaces_reading():
    # The whole point of one reader: `holds` is `any` and `block` builds a tuple, so the two
    # must not be able to disagree about a label — this is the equivalence, per block.
    document = parse(
        "## Block A — The model",
        LINE.replace("RK9", "RK1"),
        "## Block B — Authoring",
        LINE,
        "## Block C — Query",
    )
    for label in ("A", "B", "C", "Z"):
        assert document.holds(label) == bool(document.block(label)), label


def test_the_two_readers_of_it_are_the_only_two():
    """The guarantee the rationale asked for, and a test is how it stays one: RK269's note and
    RK38's event line both answer "is that block empty", and nothing else may spell it again.

    Source, not behaviour, because behaviour is what a third spelling would agree with right
    up until it did not — which is the argument `_only_reads` and `GUARDED_TOOLS` are built on.
    """
    # `document.py` is where both are defined and where each one's docstring names the other,
    # so it is the one module that is not a caller. The set is `surface.modules` and not a
    # glob of this file's own (RK496), addressed by path: `verbs/` holds a module per verb
    # family named after the domain module it calls, so a bare filename lets
    # `verbs/shipping.py` answer under `shipping.py` — one file counted as another.
    callers = {module.where: module.text for module in modules()}
    callers.pop(address("document"))
    spellings = {name for name, text in callers.items() if ".block(" in text}
    # Every remaining caller wants the entries themselves: `backlog.py` expands a `Block X`
    # dep into member ids, `authoring.py` finds where to insert, `linting.py` counts how
    # many lines a block *held* for the note's own sentence — which the event line never
    # computes, so it is a second fact rather than a second answer to the first one — and
    # `verbs/shipping.py` lists what a block delivered (RK433), which is the same call
    # `Standing.of` makes and is why that listing and `standing.recorded` are one number.
    assert spellings == {"backlog.py", "authoring.py", "linting.py", "verbs/shipping.py"}
    # `rendering.py` is the third name and not a third spelling (RK493): the event line moved
    # there with every other printer, and what it carries is the *word* — `Backlog.during`,
    # not this call. Its `.holds(` is the docstring saying which one it stopped being.
    assert {name for name, text in callers.items() if ".holds(" in text} == {
        "cli.py",
        "linting.py",
        "rendering.py",
    }


# -- the write a reader can catch halfway (RK118) ---------------------------


def test_the_target_is_replaced_and_never_truncated_in_place(tmp_path):
    # The defect is not that a write can fail — it is that a reader arriving mid-write gets
    # a *shorter* file that parses, because every line left in it is one the schema accepts.
    # So the assertion is about the file the reader would open: it is never opened for
    # writing at all, it is renamed over.
    target = tmp_path / "ROADMAP.md"
    target.write_text("## Block A — The model\n" + LINE + "\n", encoding="utf-8")
    opened: list[str] = []
    real = Path.open

    def watched(self, mode="r", *args, **kwargs):
        # Only the writing opens: `Document.load` reads the target, and this is a claim
        # about what is opened *for writing* (RK450 moved the write off `write_text`).
        if "r" not in mode:
            opened.append(self.name)
        return real(self, mode, *args, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(Path, "open", watched)
        write_atomically(target, "## Block B — Authoring\n")
    assert opened == [f".{target.name}.roadkeep-{os.getpid()}.tmp"]
    assert target.read_text(encoding="utf-8") == "## Block B — Authoring\n"


def test_the_staged_bytes_are_on_the_device_before_the_rename(tmp_path):
    """RK450, and the one test here written from a data loss rather than from a design.

    `write_text` returns once the bytes are in the page cache and `commit` renames straight
    after, so a crash between them leaves the target at its **new size and entirely NUL** —
    not a whole file, and not the old one either, which is the single state RK118 claims a
    reader cannot catch. Measured on this repository from a hard reboot mid-session: four
    governed files at 2,980, 121,337, 4,333 and 24,068 bytes, every byte NUL.

    Asserted as an ordering, because that is the whole of it: a rename that reaches the disk
    before the bytes it renames is what produces the corrupt file, and the fsync is what
    makes that impossible.
    """
    target = tmp_path / "ROADMAP.md"
    target.write_text("before\n", encoding="utf-8")
    order: list[str] = []
    real_fsync, real_replace = os.fsync, os.replace

    def watched_fsync(fd):
        order.append("fsync")
        return real_fsync(fd)

    def watched_replace(src, dst, **kwargs):
        order.append("replace")
        return real_replace(src, dst, **kwargs)

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(os, "fsync", watched_fsync)
        patch.setattr(os, "replace", watched_replace)
        write_atomically(target, "after\n")
    assert order == ["fsync", "replace"]
    assert target.read_text(encoding="utf-8") == "after\n"


def test_every_file_of_a_transaction_is_synced_before_any_of_them_is_placed(tmp_path):
    """The same ordering across the three files a `ship` writes: `write_all` stages them all
    and then commits them all, so the sync belongs to the staging half or the last file
    renamed is the one that can be NUL."""
    from roadkeep.kernel.document import Write, write_all

    writes = []
    for name in ("ROADMAP.md", "CHANGELOG.md", "IMPROVEMENTS.md"):
        path = tmp_path / name
        path.write_text("before\n", encoding="utf-8")
        writes.append(Write(target=path, text="after\n", assert_current=lambda: None))
    order: list[str] = []
    real_fsync, real_replace = os.fsync, os.replace

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(os, "fsync", lambda fd: (order.append("fsync"), real_fsync(fd))[1])
        patch.setattr(
            os,
            "replace",
            lambda src, dst, **kw: (order.append("replace"), real_replace(src, dst, **kw))[1],
        )
        write_all(*writes)
    assert order == ["fsync"] * 3 + ["replace"] * 3
    assert all(one.target.read_text(encoding="utf-8") == "after\n" for one in writes)


def test_the_scratch_file_is_in_the_targets_own_directory_and_does_not_survive(tmp_path):
    # Its own directory, or the rename would be a copy across filesystems and stop being
    # one step. And gone afterwards, in a directory the tool asked to be trusted with.
    target = tmp_path / "docs" / "ROADMAP.md"
    target.parent.mkdir()
    target.write_text("before\n", encoding="utf-8")
    write_atomically(target, "after\n")
    assert list(target.parent.iterdir()) == [target]
    assert target.read_text(encoding="utf-8") == "after\n"


def test_a_write_that_fails_leaves_neither_a_scratch_file_nor_a_damaged_target(tmp_path):
    target = tmp_path / "ROADMAP.md"
    target.write_text("the file as it was\n", encoding="utf-8")
    def refusing(*args, **kwargs):
        raise PermissionError("something holds the target")

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("roadkeep.kernel.document.os.replace", refusing)
        patch.setattr("roadkeep.kernel.document._REPLACE_PAUSE", 0.0)
        with pytest.raises(PermissionError):
            write_atomically(target, "the file as it would have been\n")
    assert target.read_text(encoding="utf-8") == "the file as it was\n"
    assert list(tmp_path.iterdir()) == [target]


def test_a_saved_document_lands_whole(tmp_path):
    target = tmp_path / "ROADMAP.md"
    document = parse("## Block A — The model", LINE)
    document.save(target)
    with target.open("r", encoding="utf-8", newline="") as handle:
        assert handle.read() == document.render()


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


# -- the qualifier a partial entry carries (RK121) ---------------------------


LEDGER = Schema().as_ledger()
PARTIAL_LINE = "- ✅ **RK9 (local half)** **A symptom** — a reason."


def test_a_partial_entry_round_trips():
    document = Document.parse(f"## Block A — The model\n{PARTIAL_LINE}\n", LEDGER)
    assert document.entries[0].task.part == "local half"
    assert document.entries[0].task.id == "RK9"
    assert document.render() == f"## Block A — The model\n{PARTIAL_LINE}\n"
    assert document.non_canonical == ()


def test_a_partial_entry_is_found_by_its_id_and_not_by_the_whole_bold():
    # The defect: the parser saw no id at all, so two Shio deps reported `SH96` as being in
    # neither file while the roadmap annotated it shipped.
    document = Document.parse(f"## Block A — The model\n{PARTIAL_LINE}\n", LEDGER)
    assert "RK9" in document.by_id()
    assert "RK9 (local half)" not in document.by_id()


def test_a_markerless_ledger_reads_the_qualifier_too():
    # Both live ledgers write `- **T1** — …`, and Shio's thirteen partials are all in one.
    schema = replace(LEDGER, marker_field=False, symptom_field=False)
    line = "- **SH96 (local half)** — What landed."
    document = Document.parse(f"## Block A — The model\n{line}\n", schema)
    assert (document.entries[0].task.id, document.entries[0].task.part) == (
        "SH96",
        "local half",
    )
    assert document.render() == f"## Block A — The model\n{line}\n"


def test_prose_that_puts_a_parenthetical_in_bold_is_still_prose():
    # The shape tests decide whether a bullet *claims* a task line, and widening them is
    # what let the corpus's partials be read at all — so the other side has to hold.
    schema = replace(LEDGER, marker_field=False, symptom_field=False)
    for line in ("- **Delete (soon)** the 3 old files", "- **Notes (draft)** on the plan"):
        document = Document.parse(f"## Block A — The model\n{line}\n", schema)
        assert document.entries == () and document.rejects == (), line


# -- where an entry ends (RK157) ----------------------------------------------

#: A ledger written before this tool existed, at the shape Shio's is: the rules that hold a
#: `why` to one sentence ending in a stop are off for the role, so the bullet wraps and the
#: lines under it parse as nothing at all.
WRAPPED = replace(LEDGER, one_sentence=False, terminator=False)
WRAPPED_LEDGER = (
    "## Block A — The model\n"
    "\n"
    "- ✅ **RK1** **A first symptom** — Because of a reason that continues\n"
    "  on a second line, and finishes\n"
    "  on a third one.\n"
)


def test_an_entry_that_wraps_knows_where_it_ends():
    # The fact no reader held: `place` answered "after the last entry" with the line after
    # that entry's *first* line, so a new bullet landed inside the previous entry.
    document = Document.parse(WRAPPED_LEDGER, WRAPPED)
    entry = document.entries[0]
    assert (entry.lineno, entry.last, entry.stop) == (3, 5, 5)
    assert entry.wrapped


def test_an_entry_that_does_not_wrap_owns_one_line():
    # Every line of a governed roadmap: the format has no multi-line task line.
    document = Document.parse(f"## Block A — The model\n{PARTIAL_LINE}\n", LEDGER)
    entry = document.entries[0]
    assert (entry.lineno, entry.stop) == (2, 2) and not entry.wrapped


def test_a_blank_line_ends_an_entry_and_a_paragraph_below_belongs_to_the_block():
    # A block's own introduction (RK108) is not the last entry of the block above it.
    document = Document.parse(WRAPPED_LEDGER + "\nWhat this block is for.\n", WRAPPED)
    assert document.entries[0].stop == 5


def test_a_following_bullet_ends_an_entry_even_with_no_blank_between():
    document = Document.parse(
        WRAPPED_LEDGER + "- ✅ **RK2** **A second symptom** — It works now.\n", WRAPPED
    )
    assert [(e.task.id, e.stop) for e in document.entries] == [("RK1", 5), ("RK2", 6)]


def test_a_fence_below_an_entry_is_not_its_continuation():
    # Nothing inside a fence is a line this parser claims, so nothing inside one is a line
    # an entry owns either — a quoted example would otherwise be swallowed by the bullet.
    document = Document.parse(
        "## Block A — The model\n"
        "- ✅ **RK1** **A first symptom** — It works now.\n"
        "```\n- not a bullet\n```\n",
        LEDGER,
    )
    assert document.entries[0].stop == 2


def test_a_rewrite_keeps_the_lines_it_cannot_reproduce():
    # `replace_task` is deliberately not span-aware: every field the schema renders was read
    # off the first line, so replacing the whole span with one rendered line would delete
    # somebody's paragraph in the name of changing an id.
    document = Document.parse(WRAPPED_LEDGER, WRAPPED)
    entry = document.entries[0]
    updated = document.replace_task(entry, replace(entry.task, id="RK9"))
    assert "**RK9**" in updated.lines[2]
    assert updated.lines[3:5] == ("  on a second line, and finishes\n", "  on a third one.\n")


# -- one parse per distinct read (RK211) --------------------------------------

#: One open line, which is all these need: the subject is the parse, not the grammar.
LEDGER_TEXT = "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1\n"


def test_the_same_bytes_are_parsed_once_however_many_times_they_are_read(tmp_path):
    """The cost RK188 added, measured and then removed where it was duplication.

    A `status` change parses the three counted roles through `Backlog.load`, and the
    projection in the same transaction parses them again — 9.1 ms of Turing's 17.1 ms
    refresh, on a file the command had read a millisecond earlier. Nothing about the
    projection was wrong; the second parse was.
    """
    path = tmp_path / "ROADMAP.md"
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(LEDGER_TEXT)
    _parsed.cache_clear()
    first = Document.load(path)
    misses = _parsed.cache_info().misses
    again = Document.load(path)
    assert _parsed.cache_info().misses == misses  # the second read parsed nothing
    assert again.entries == first.entries


def test_the_bytes_are_read_from_disk_every_time_so_there_is_nothing_to_invalidate(tmp_path):
    """What makes it a memo and not a cache, and the reason it needs no invalidation.

    The key *is* the text, so a file somebody changed produces a different key. There is no
    window in which this answers about a file that has moved — which is the property RK116
    spends a re-read on, and it would be undone by a cache keyed on the path.
    """
    path = tmp_path / "ROADMAP.md"
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(LEDGER_TEXT)
    assert len(Document.load(path).entries) == 1
    with path.open("a", encoding="utf-8", newline="") as handle:
        handle.write("- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2\n")
    assert len(Document.load(path).entries) == 2


def test_two_schemas_over_one_file_are_two_parses(tmp_path):
    """The schema is half the key, because the same bytes are two different documents under
    two grammars — which is how the reject list is proved (a ledger read under a schema that
    expects the marker it does not carry), and a memo keyed on text alone would hand the
    second reader the first one's answer."""
    ledger = Schema(markers=("📋",)).as_ledger()
    text = "- ✅ **RK1** **A symptom** — it was done.\n"
    assert len(Document.parse(text, schema=ledger).entries) == 1
    marked = Document.load if False else Document.parse
    assert len(marked(text, schema=Schema()).entries) == 0  # a ✅ no open set declares


def test_a_cached_document_is_never_the_one_a_caller_mutates(tmp_path):
    """Entries are shared between readers, which is only safe because every mutator returns
    a new document (L3). Held as a test rather than as a comment: the day something edits a
    document in place, this is the reader that finds out."""
    path = tmp_path / "ROADMAP.md"
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write(LEDGER_TEXT)
    first = Document.load(path)
    entry = first.entries[0]
    first.remove_lines(entry.index, entry.stop)
    assert len(Document.load(path).entries) == 1
    assert first.path == path and Document.load(path).path == path


# -- a diagnosis that sends the caller to the wrong file (RK216) ---------------

#: Claude Code Tray's own list, at the incident. `AJ` is in it and `A` is not, and `A` is a
#: prefix of six of them — which is what made the refusal impossible to act on.
TRAY_BLOCKS = ("AG", "AE", "AB", "AC", "AI", "AJ", "G", "D", "N", "E", "S", "Q")


def test_a_label_that_shades_into_a_declared_one_is_named_as_such():
    # The finding: `ship` on a task in AJ refused with "no heading declares Block A" from a
    # list containing AJ, so the only thing the sentence asked for was a heading already
    # there under a letter the caller never typed.
    error = UnknownBlock("A", TRAY_BLOCKS, where="ROADMAP.md")
    message = str(error)
    assert "no heading declares Block A" in message  # the fact, unchanged
    assert "shares a prefix with A" not in message  # six of them, so the plural
    assert "AG, AE, AB, AC, AI, AJ share a prefix with A" in message
    assert "check that the label reached this command whole" in message
    # And the advice the base sentence gives is the one that is now unsafe to follow.
    assert "before declaring a second heading over the first one's work" in message


def test_the_confusion_is_reported_from_either_end():
    # `A` against a declared `AJ` and `AJ` against a declared `A` are one mistake seen from
    # two ends, and only one of them is the direction the incident arrived from.
    assert "AJ shares a prefix with A" in str(UnknownBlock("A", ("AJ", "G")))
    assert "A shares a prefix with AJ" in str(UnknownBlock("AJ", ("A", "G")))


def test_a_label_that_shades_into_nothing_says_nothing_extra():
    # The sentence every project already saw stays what it was: a hint on every refusal is
    # output nobody reads, and `Z` against A and B is already actionable.
    message = str(UnknownBlock("Z", ("A", "B"), where="ROADMAP.md"))
    assert "no heading declares Block Z" in message
    assert "prefix" not in message and "reached this command whole" not in message


def test_the_declared_label_itself_is_never_reported_as_shading_into_itself():
    # Every label is a prefix of itself, so the check has to exclude the equal case or a
    # refusal that cannot happen would carry a hint about the block it is refusing.
    assert shading("AJ", ("AJ",)) == ""


def test_the_diagnosis_is_written_once_and_used_by_the_reads_too(tmp_path):
    # Three places compose this refusal — the write, `Census.select` and `pick` — and a fix
    # in one that left two copies unactionable would be a half-fix of the finding itself.
    assert "AJ shares a prefix with A" in shading("A", ("AJ", "G"))
    assert shading("A", ()) == ""


# -- and the verb that repairs it (RK257) -------------------------------------


def test_the_refusal_ends_in_the_command_that_declares_the_heading():
    # Naming the block was three quarters of the answer: the fourth is that `block add` is
    # the verb, and it is one the author would otherwise have to go and find.
    message = str(UnknownBlock("Z", ("A", "B"), where="docs/CHANGELOG.md"))
    assert message.endswith('`block add Z --title "<its title>"`')
    assert "the verb that opens it wherever it is missing is" in message


def test_the_shaded_refusal_makes_the_command_conditional_on_the_label():
    # Where the label shades into a declared one the advice is *check the label first* — so
    # the verb arrives after that check and not as a second instruction competing with it.
    message = str(UnknownBlock("A", TRAY_BLOCKS, where="docs/CHANGELOG.md"))
    verb = message.index("`block add A")
    assert message.index("check that the label reached this command whole") < verb
    assert "over the first one's work — and if it did, the verb is" in message


def test_the_command_carries_the_label_that_was_asked_for():
    # Not a declared one and not a placeholder: the argument the author retypes is the label
    # the refused write already named, which is the whole reason it can be spelled here.
    assert "`block add BU " in str(UnknownBlock("BU", ("A", "B")))
    assert "`block add BU " in str(UnknownBlock("BU", ("B", "C")))  # shaded by B


# -- and not the eighty-nine labels beside it (RK296) -------------------------


def test_the_labels_the_file_declares_are_not_listed():
    # The half of RK257 that was left: a project with 90 blocks answered a question nobody
    # asked, and the two clauses that are the remedy arrived after a line of labels.
    message = str(UnknownBlock("Z", TRAY_BLOCKS, where="docs/CHANGELOG.md"))
    assert "no heading declares Block Z in docs/CHANGELOG.md:" in message
    assert "declares:" not in message
    for label in TRAY_BLOCKS:
        assert f" {label}," not in message


def test_the_labels_are_still_carried_for_a_caller_that_wants_them():
    # Dropped from the sentence and not from the exception: what changed is what a reader is
    # made to scan past, not what the refusal knows.
    assert UnknownBlock("Z", TRAY_BLOCKS).declared == TRAY_BLOCKS


def test_the_one_case_the_list_was_load_bearing_for_is_still_answered():
    # `shading` names the labels that share a prefix, which is the subset a confused author
    # needs — so removing the rest takes nothing away from the incident RK216 was filed from.
    message = str(UnknownBlock("A", TRAY_BLOCKS, where="docs/CHANGELOG.md"))
    assert "AG, AE, AB, AC, AI, AJ share a prefix with A" in message
    assert "declares:" not in message


def test_a_file_declaring_no_block_at_all_says_that_much():
    # A different diagnosis rather than a shorter list: there is no label to have mistyped,
    # and `block add` is the whole answer.
    assert " (it declares none)" in str(UnknownBlock("Z", (), where="docs/CHANGELOG.md"))
    assert " (nothing declares any block)" in str(UnknownBlock("Z", ()))
    assert declares(("A",)) == "" and declares(("A",), named=True) == ""
