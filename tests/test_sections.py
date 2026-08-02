"""A section is the unit of a prose file (RK9).

Four claims, and the last two are the ones that make this a schema rather than an append:

* a section is **found and deleted whole**, subsections included, because prose left
  under the next task's heading reads as that task's design;
* it has a **word budget**, refused before the paragraph is written, which is `add`'s
  argument (L1) applied to the unit prose actually has;
* its **anchor must resolve** — an id-shaped anchor naming no open task is an orphan the
  moment it is written, and the pointer that was supposed to reach it never will;
* its **place is derived** — from the task's block, or from the anchor itself when it
  belongs to no task (RK45) — so the prose file's order is a consequence of the backlog's
  and of the outline's, and nobody chooses where to type.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.document import Document, UnknownBlock
from roadkeep.schema import Schema, SchemaError
from roadkeep.sections import (
    NoSuchSection,
    SectionClaimed,
    SectionExists,
    SectionOccupied,
    UnknownParent,
    add,
    anchored,
    drop,
    find,
    nested,
    pointers,
)

#: This repository, whose `docs/` are the conformance fixture — read, never written.
HERE = Path(__file__).resolve().parents[1]
ROADMAP = "docs/ROADMAP.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"

RK1_LINE = "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1"

BACKLOG = f"""# Roadmap

## Block A — The model

{RK1_LINE}

- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason. → §RK3

## Block B — Authoring

- 📋 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2
"""

RATIONALE = """# Improvements

## §0 — Why this exists

### §0.1 The measured problem

The reading that started it.

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.

#### §RK1.1 A subsection

Which belongs to the section above.

## Block B — Authoring
"""


def project(
    tmp_path: Path,
    *,
    roadmap: str = BACKLOG,
    improvements: str = RATIONALE,
    extra: str = "",
    top: str = "",
) -> Config:
    """A project on disk. ``extra`` follows `[files]`; ``top`` precedes it (a bare key)."""
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n{top}[files]\nroadmap = "{ROADMAP}"\n'
        f'improvements = "{IMPROVEMENTS}"\n{extra}',
        encoding="utf-8",
    )
    for name, body in {ROADMAP: roadmap, IMPROVEMENTS: improvements}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def read(config: Config, name: str = IMPROVEMENTS) -> str:
    with (config.root / name).open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


# -- finding -----------------------------------------------------------------


def test_a_section_owns_its_subsections(tmp_path):
    config = project(tmp_path)
    section = find(config.document("improvements"), "RK1")
    assert (section.title, section.level) == ("A first design", 3)
    assert (section.first, section.last) == (11, 18)
    assert "A subsection" in section.body
    # The budget counts the subsection's words too: the unit is the section, and prose
    # that escapes the count by gaining a heading is the drift the budget exists to stop.
    assert section.words == 18


def test_every_anchor_is_enumerable_with_its_own_prose(tmp_path):
    # What the gate reads from the other direction (RK15): a pointer resolves one anchor,
    # and a section nothing points at is only visible from the set. Own prose, because
    # `find` returns the subtree and §0 is a container with no paragraph of its own.
    sections = {s.anchor: s for s in anchored(project(tmp_path).document("improvements"))}
    assert list(sections) == ["0", "0.1", "RK1", "RK1.1"]
    assert sections["0"].words == 0 and sections["0.1"].words == 5
    assert sections["RK1"].words == 8  # 18 with the subsection `find` also returns


def test_an_outline_anchor_is_a_section_like_any_other(tmp_path):
    config = project(tmp_path)
    assert find(config.document("improvements"), "0.1").title == "The measured problem"
    # §0 owns §0.1, because a section ends at the next same-or-higher heading.
    assert find(config.document("improvements"), "0").level == 2


def test_an_anchor_that_is_a_prefix_of_another_is_not_a_match(tmp_path):
    config = project(tmp_path)
    assert find(config.document("improvements"), "RK1").anchor == "RK1"
    assert find(config.document("improvements"), "RK") is None


# -- the anchor is read per scheme (RK44) ------------------------------------

#: An outline document numbers its own headings and puts the § on the pointer alone. The
#: shapes are the live ones: Shio's terminating period, Turing's depth, a container with
#: no number at all, a `.10` that must not be claimed by `.1`, and commitclerk's block
#: letters (RK101), measured on that file before it moved to the `id` scheme.
OUTLINE_RATIONALE = """# Improvements

## Table of contents

## VIII. The Agent Gateway

The part that is not numbered by anybody.

### VIII.1 MCP server host (SH75)

The reasoning the line has no room for.

### VIII.10 Batch and apply

A tenth one, which §VIII.1 must not claim.

#### XIV.8.7 The deepest one

Three segments, which Turing writes.

#### IX.4.d The pivot

A fourth level spelled with a letter, which Turing writes twenty times.

#### IX.4.beta Not a segment

A word after the dot, which nothing writes and which no anchor claims.

## B — Context beyond the diff

A block letter on its own, which names a block and so claims no section.

### B.2 Ticket trailers

A rationale numbered by the roadmap's own block letters, which commitclerk writes.
"""


def outline(tmp_path: Path) -> Config:
    return project(
        tmp_path,
        improvements=OUTLINE_RATIONALE,
        top='ref_scheme = "outline"\n',
        roadmap=BACKLOG.replace("§RK1", "§VIII.1")
        .replace("§RK2", "§XIV.8.7")
        .replace("§RK3", "§VIII.10"),
    )


def test_an_outline_document_numbers_its_headings_and_they_are_still_sections(tmp_path):
    # Measured on Shio: 151 headings, 0 sections, and 74 pointers reported as resolving to
    # nothing against a file that answers every one of them — RK15's argument inverted.
    sections = {s.anchor: s for s in anchored(outline(tmp_path).document("improvements"))}
    assert list(sections) == ["VIII", "VIII.1", "VIII.10", "XIV.8.7", "IX.4.d", "B.2"]
    assert sections["VIII"].title == "The Agent Gateway"  # the period is not the anchor
    assert sections["VIII.1"].title == "MCP server host (SH75)"


def test_an_outline_heading_with_no_number_is_prose_and_not_a_section(tmp_path):
    config = outline(tmp_path)
    assert find(config.document("improvements"), "Table") is None
    # `IX.4.beta` is here too: a segment no corpus writes stays prose, which is what keeps
    # `§IX.4` from having to tell an anchor from a title's first word (RK47). `## B —` is
    # the same rule one level up (RK101): the dot is what makes a letter an anchor, so a
    # block heading stays a block heading even where `### B.2` under it is a section.
    assert find(config.document("improvements"), "B") is None
    assert {s.anchor for s in anchored(config.document("improvements"))} == {
        "VIII",
        "VIII.1",
        "VIII.10",
        "XIV.8.7",
        "IX.4.d",
        "B.2",
    }


def test_an_outline_anchor_does_not_claim_the_one_it_prefixes(tmp_path):
    config = outline(tmp_path)
    assert find(config.document("improvements"), "VIII.1").title.startswith("MCP")
    assert find(config.document("improvements"), "VIII").level == 2


def test_the_sigil_is_still_required_on_a_heading_under_the_id_scheme(tmp_path):
    # The two schemes are read differently and neither is read into the other: under `id`
    # the anchor is a task id, so the § is what tells `RK1` from a word.
    config = project(tmp_path, improvements=RATIONALE.replace("### §RK1", "### RK1"))
    assert find(config.document("improvements"), "RK1") is None


def test_a_section_written_under_the_outline_scheme_is_read_back(tmp_path):
    config = outline(tmp_path)
    document, section = add(
        config, "improvements", "VIII.2", "Agent manifest", "The reasoning, written once."
    )
    document.save()
    # Written bare, because that is how the scheme spells a heading — and a heading this
    # tool writes that it cannot read back is the defect RK44 closes, not a new one.
    assert "### VIII.2 Agent manifest" in read(config)
    assert section.anchor == "VIII.2"
    assert find(config.document("improvements"), "VIII.2") is not None


def test_an_anchor_the_outline_scheme_cannot_number_is_refused(tmp_path):
    config = outline(tmp_path)
    with pytest.raises(SchemaError, match="outline anchor"):
        add(config, "improvements", "RK9", "A design", "The reasoning.")


#: Shio, whose 151 headings and 74 unresolved pointers are the measurement RK44 names.
#: Absent on any machine but the author's, so the use is guarded (as in `test_document`).
SHIO_PROSE = Path("D:/Git/viglet/shio/latest/docs/IMPROVEMENTS.md")
SHIO_BACKLOG = Path("D:/Git/viglet/shio/latest/docs/ROADMAP.md")
#: Turing, the only corpus that spells a fourth level with a letter (RK47).
TURING_PROSE = Path("D:/Git/viglet/turing/latest/docs/IMPROVEMENTS.md")


def test_a_live_outline_file_yields_its_sections_and_answers_its_pointers():
    if not SHIO_PROSE.exists():
        pytest.skip(f"{SHIO_PROSE} is not on this machine")
    schema = Schema(prefixes=("SH",), ref_scheme="outline")
    sections = anchored(Document.load(SHIO_PROSE, schema))
    # A lower bound, like every other foreign one here: the file only grows.
    assert len(sections) >= 120
    declared = {s.anchor for s in sections}
    pointers = [e.task.ref for e in Document.load(SHIO_BACKLOG, schema).entries if e.task.ref]
    # Every one of them, and not a slack count: an unresolved pointer here is a defect in
    # *that* backlog for `lint` to report, which is the whole point — before RK44 the
    # answer was 74 of them, and the gate was reporting the file rather than reading it.
    assert pointers and [p for p in pointers if p not in declared] == []


def test_a_lettered_heading_in_the_live_corpus_becomes_a_section_the_budget_charges():
    if not TURING_PROSE.exists():
        pytest.skip(f"{TURING_PROSE} is not on this machine")
    sections = anchored(Document.load(TURING_PROSE, Schema(prefixes=("T",), ref_scheme="outline")))
    lettered = [s for s in sections if s.anchor[-2:-1] == "." and s.anchor[-1].isalpha()]
    # Twenty, and one of them is 779 words: prose that had escaped the section budget
    # entirely by gaining a lettered heading, which is the drift RK47 measured.
    assert len(lettered) >= 20
    assert max(s.words for s in lettered) > 250


# -- dropping ----------------------------------------------------------------


def test_dropping_takes_the_subsections_and_leaves_the_shape(tmp_path):
    config = project(tmp_path)
    document, section = drop(config.document("improvements"), "RK1")
    document.save()
    assert section.first == 11
    assert read(config) == RATIONALE.replace(
        """### §RK1 A first design

The reasoning the line has no room for.

#### §RK1.1 A subsection

Which belongs to the section above.

""",
        "",
    )


def test_dropping_the_last_section_leaves_no_trailing_blank(tmp_path):
    config = project(tmp_path, improvements=RATIONALE + "\n### §RK2 A last design\n\nProse.\n")
    document, _ = drop(config.document("improvements"), "RK2")
    document.save()
    assert read(config) == RATIONALE


def test_dropping_what_is_not_there_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NoSuchSection):
        drop(config.document("improvements"), "RK9")
    assert read(config) == RATIONALE


# -- a subtree that is not all one section's (RK78) ---------------------------


#: A level-2 section with a level-3 child that belongs to another line, which is the shape
#: `find` reads as one body and a drop would delete as one deletion.
NESTING = RATIONALE.replace("### §RK1 A first design", "## §RK1 An epic design").replace(
    "#### §RK1.1 A subsection", "### §RK2 A design under it"
)


def test_a_subtree_is_enumerable_as_the_headings_it_is(tmp_path):
    config = project(tmp_path, improvements=NESTING)
    assert [s.anchor for s in nested(config.document("improvements"), "RK1")] == ["RK2"]
    # And nothing is nested under a section that is not there — the same answer the drop
    # gives, so a reader of this question is not the one told about the missing heading.
    assert nested(config.document("improvements"), "RK9") == ()


def test_what_the_open_lines_point_at_is_read_from_the_roadmap(tmp_path):
    config = project(tmp_path, improvements=NESTING)
    assert pointers(config) == {"RK1": ("RK1",), "RK2": ("RK2",), "RK3": ("RK3",)}
    # The departing line's own claim is the reason the drop is happening, so it is not one.
    assert pointers(config, leaving="RK1") == {"RK2": ("RK2",), "RK3": ("RK3",)}


def test_a_subtree_another_line_points_at_is_refused_before_the_write(tmp_path):
    config = project(tmp_path, improvements=NESTING)
    with pytest.raises(SectionOccupied) as raised:
        drop(config.document("improvements"), "RK1", claimed=pointers(config, leaving="RK1"))
    assert "§RK2 (RK2)" in str(raised.value)
    assert read(config) == NESTING


def test_a_subtree_nobody_else_claims_still_goes_whole(tmp_path):
    # Ownership bounds the deletion and not depth: §RK1.1 carries no pointer of its own, so
    # it is RK1's prose and leaves with it — which is what keeps the refusal above narrow.
    config = project(tmp_path)
    document, _ = drop(
        config.document("improvements"), "RK1", claimed=pointers(config, leaving="RK1")
    )
    document.save()
    assert "§RK1.1" not in read(config)


# -- the anchor that was named, and who points at it (RK112) ------------------


#: RK3's line pointing at RK1's design: two open owners for one anchor, which is the shape
#: an outline gives a project by default and a hand-written `→ §…` gives any of them.
CO_OWNED = BACKLOG.replace("→ §RK3", "→ §RK1")


def test_the_named_anchor_is_refused_when_an_open_line_points_at_it(tmp_path):
    # Found in Shio: `section drop VIII.11` succeeded and the next `lint` reported
    # `ref.unresolved` for the open line that owned it. RK78 asked this about the subtree
    # and `ship` about the anchor; the standalone verb asked neither.
    config = project(tmp_path)
    with pytest.raises(SectionClaimed) as raised:
        drop(config.document("improvements"), "RK1", claimed=pointers(config))
    assert "is pointed at by RK1" in str(raised.value)
    assert "repoint the line, or ship the one that claims it" in str(raised.value)
    assert read(config) == RATIONALE


def test_every_owner_is_named_so_the_remedy_is_the_whole_list(tmp_path):
    config = project(tmp_path, roadmap=CO_OWNED)
    with pytest.raises(SectionClaimed) as raised:
        drop(config.document("improvements"), "RK1", claimed=pointers(config))
    assert raised.value.owners == ("RK1", "RK3")
    assert "pointed at by RK1, RK3" in str(raised.value)
    # One remedy per pointer, so the sentence counts them rather than assuming one.
    assert "those pointers" in str(raised.value)


def test_the_departing_line_s_own_claim_is_not_one_of_them(tmp_path):
    # `ship` passes `leaving`, so the claim that is the *reason* for the drop is excluded
    # and shipping still takes its own task's section — the case that is always right.
    config = project(tmp_path, roadmap=CO_OWNED)
    with pytest.raises(SectionClaimed) as raised:
        drop(config.document("improvements"), "RK1", claimed=pointers(config, leaving="RK1"))
    assert raised.value.owners == ("RK3",) and "that pointer" in str(raised.value)


def test_a_section_no_open_line_claims_is_the_one_this_verb_drops(tmp_path):
    # The orphan `lint` already reports: RK1 is gone from the roadmap and its design is
    # what is left. Nothing points at it, so nothing is stranded by removing it.
    config = project(tmp_path, roadmap=BACKLOG.replace(f"{RK1_LINE}\n\n", ""))
    document, _ = drop(config.document("improvements"), "RK1", claimed=pointers(config))
    document.save()
    assert "§RK1" not in read(config)


# -- adding ------------------------------------------------------------------


def test_the_section_lands_under_its_task_s_block(tmp_path):
    # RK2 is in Block B, so its rationale goes under Block B — the prose file's order is
    # a consequence of the backlog's.
    config = project(tmp_path)
    document, section = add(config, "improvements", "RK2", "A second design", "Prose.")
    document.save()
    assert read(config) == RATIONALE + "\n### §RK2 A second design\n\nProse.\n"
    assert (section.anchor, section.title, section.words) == ("RK2", "A second design", 1)


def test_a_second_section_follows_the_first_in_its_block(tmp_path):
    # RK3 is in Block A, so its section lands after §RK1's subsections and *before* the
    # Block B heading — appended to its block, not to the file.
    config = project(tmp_path)
    document, _ = add(config, "improvements", "RK3", "A third design", "More prose.")
    document.save()
    body = read(config)
    assert body.index("A third design") < body.index("## Block B")
    assert body.index("Which belongs to the section above.") < body.index("A third design")


def test_a_block_the_prose_file_does_not_declare_is_refused(tmp_path):
    # Block A's sections all shipped and its heading went with them, so appending at the
    # end would file this section under Block B for every reader.
    config = project(
        tmp_path, improvements="# Improvements\n\n## Block B — Authoring\n\nProse.\n"
    )
    with pytest.raises(UnknownBlock) as raised:
        add(config, "improvements", "RK1", "A first design", "Prose.")
    assert "Block A" in str(raised.value) and "declares: B" in str(raised.value)


def test_a_task_less_anchor_lands_after_the_section_it_extends(tmp_path):
    # §0.2 continues §0, so it goes at the end of §0's subtree — *before* Block A, not at
    # the end of the file, where the only signal that it is not Block B's rationale would
    # be the anchor itself (RK45).
    config = project(tmp_path)
    document, _ = add(config, "improvements", "0.2", "A second reading", "Prose.", level=3)
    document.save()
    body = read(config)
    assert body.index("The reading that started it.") < body.index("§0.2 A second reading")
    assert body.index("§0.2 A second reading") < body.index("## Block A")


def test_a_subsection_of_a_task_lands_inside_that_task_s_section(tmp_path):
    # §RK1.1 belongs inside §RK1, and this one goes after the subsection already there:
    # the place is the end of the subtree, so a third one follows the second.
    config = project(tmp_path)
    document, _ = add(config, "improvements", "RK1.2", "A second subsection", "Prose.", level=4)
    document.save()
    body = read(config)
    assert body.index("Which belongs to the section above.") < body.index("§RK1.2")
    assert body.index("§RK1.2") < body.index("## Block B")


def test_an_anchor_extending_nothing_this_file_declares_is_refused(tmp_path):
    # The refusal `_placement` already makes for an undeclared block, from the other side:
    # appending is the one answer that is always plausible and frequently wrong, so the
    # file's top level stays the author's to declare.
    config = project(tmp_path)
    with pytest.raises(UnknownParent) as raised:
        add(config, "improvements", "9.1", "A reading nothing precedes", "Prose.")
    assert "no section §9.1 extends" in str(raised.value)
    assert "§0.1" in str(raised.value)  # what the file does declare, so the fix is visible
    assert read(config) == RATIONALE


def test_an_anchor_is_not_the_parent_of_the_one_it_prefixes_as_a_string(tmp_path):
    # `§0.1` is not what `§0.10` extends — read segment by segment, the same care `find`
    # takes about where an anchor ends. §0 is, so §0.10 lands at the end of §0's subtree.
    config = project(tmp_path, improvements=RATIONALE.replace("§0.1 The", "§0.9 The"))
    document, _ = add(config, "improvements", "0.10", "A tenth reading", "Prose.", level=3)
    document.save()
    body = read(config)
    assert body.index("The reading that started it.") < body.index("§0.10")
    assert body.index("§0.10") < body.index("## Block A")


def test_the_repository_s_own_preface_files_itself_before_the_first_block():
    # The reading that opened RK45: writing §0.4 with `section add` put it under Block F,
    # 50 lines and five headings away from the §0.3 it continues. Unsaved — this file is
    # the conformance fixture, and a test that rewrote it would be measuring itself.
    config = Config.discover(HERE)
    document, section = add(config, "improvements", "0.9", "A ninth reading", "Prose.")
    body = "".join(document.lines)
    assert body.index("### §0.4") < body.index("### §0.9") < body.index("## Block A")
    # And nowhere near last, which is where the reading found §0.4: five headings further
    # down, under the block whose rationale it then read as.
    assert section.first < max(heading.lineno for heading in document.headings)


def test_prose_is_reflowed_and_structure_is_not(tmp_path):
    config = project(tmp_path, extra="[limits]\nprose = 40\n")
    body = (
        "One sentence that is definitely longer than forty characters in total.\n\n"
        "| a | b |\n|---|---|\n| 1 | 2 |"
    )
    document, _ = add(config, "improvements", "RK2", "A design", body)
    document.save()
    written = read(config)
    assert "One sentence that is definitely longer\nthan forty characters in total.\n" in written
    # The table is inserted exactly as written: the tool re-flows prose and never
    # reformats a shape it did not author.
    assert "| a | b |\n|---|---|\n| 1 | 2 |\n" in written


def test_the_file_keeps_its_line_endings(tmp_path):
    config = project(tmp_path, improvements=RATIONALE.replace("\n", "\r\n"))
    document, _ = add(config, "improvements", "RK2", "A design", "Prose.")
    document.save()
    assert "\n" not in read(config).replace("\r\n", "")


# -- refusing ----------------------------------------------------------------


def test_a_section_over_its_word_budget_is_refused(tmp_path):
    config = project(tmp_path, extra="[limits]\nsection = 10\n")
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK2", "A design", "word " * 11)
    assert [v.code for v in raised.value.violations] == ["body.too-long"]
    assert "11 words, limit is 10" in str(raised.value)
    assert read(config) == RATIONALE


def test_an_id_anchor_that_names_no_open_task_is_refused(tmp_path):
    # The pointer is the id (RK27), so this section is an orphan the moment it exists.
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK9", "A design", "Prose.")
    assert [v.code for v in raised.value.violations] == ["anchor.unknown"]
    assert read(config) == RATIONALE


def test_every_violation_is_reported_not_the_first(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "§RK2", "", "")
    assert {v.code for v in raised.value.violations} == {
        "anchor.sigil",
        "title.empty",
        "body.empty",
    }


def test_one_anchor_names_one_section(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SectionExists) as raised:
        add(config, "improvements", "RK1", "A duplicate", "Prose.")
    assert "resolves to neither" in str(raised.value)
    assert read(config) == RATIONALE


# -- the command -------------------------------------------------------------


def test_the_command_reads_the_body_from_stdin(tmp_path, capsys, monkeypatch):
    config = project(tmp_path)
    monkeypatch.setattr("sys.stdin", _Stdin("A paragraph that arrived by pipe."))
    assert (
        main(["-C", str(tmp_path), "section", "add", "RK2", "--title", "A design"])
        == EXIT_OK
    )
    assert "§RK2 → docs/IMPROVEMENTS.md:21  6 words" in capsys.readouterr().out
    assert "A paragraph that arrived by pipe." in read(config)


def test_a_pipe_the_console_would_decode_as_cp1252_still_carries_an_em_dash(
    tmp_path, capsys, monkeypatch
):
    # The defect this closes: stdout was forced to UTF-8 and stdin was not, so on a
    # Windows console every em dash in a piped paragraph arrived as three mojibake
    # characters — and the round-trip then preserved them in the file forever.
    config = project(tmp_path)
    prose = "A paragraph — piped, and the dash has to survive it."
    monkeypatch.setattr(
        "sys.stdin", io.TextIOWrapper(io.BytesIO(prose.encode()), encoding="cp1252")
    )
    assert (
        main(["-C", str(tmp_path), "section", "add", "RK2", "--title", "A design"])
        == EXIT_OK
    )
    assert prose in read(config)


def test_a_pipe_that_is_not_utf8_is_refused_rather_than_repaired(tmp_path, capsys):
    # Strict on the way in: a substituted character would round-trip out of the file it
    # landed in, so the input is refused and the file is left exactly as it was (L3).
    config = project(tmp_path)
    sys.stdin = io.TextIOWrapper(io.BytesIO(b"A paragraph, \xe9 alone."), encoding="cp1252")
    try:
        assert (
            main(["-C", str(tmp_path), "section", "add", "RK2", "--title", "A design"])
            == EXIT_USAGE
        )
    finally:
        sys.stdin = sys.__stdin__
    assert "utf-8" in capsys.readouterr().err
    assert read(config) == RATIONALE


def test_show_prints_the_section_as_the_file_has_it(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "section", "show", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("### §RK1 A first design\n\n")
    assert "#### §RK1.1 A subsection" in out


def test_show_json_carries_the_body_and_the_count(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "section", "show", "0.1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["anchor"] == "0.1" and payload["words"] == 5
    assert payload["body"] == "The reading that started it."


def test_show_of_nothing_exits_two(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "section", "show", "RK9"]) == EXIT_USAGE
    assert "no §RK9 section" in capsys.readouterr().err


def test_drop_reports_what_it_removed(tmp_path, capsys):
    # RK1's line is gone from the roadmap, which is the state this verb is for: a section
    # an open line still points at is refused one test down (RK112).
    config = project(tmp_path, roadmap=BACKLOG.replace(f"{RK1_LINE}\n\n", ""))
    assert main(["-C", str(tmp_path), "section", "drop", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert f"dropped §RK1 (11-18) from {IMPROVEMENTS}" in out
    # And the size the anchor does not state: one command, two headings (RK78).
    assert "nested   §RK1.1 went with it" in out
    assert "§RK1" not in read(config)


def test_drop_of_a_claimed_anchor_exits_two_and_writes_nothing(tmp_path, capsys):
    # The verb reads the roadmap for itself: no `leaving` to pass, because nothing is
    # departing — which is exactly why this call had no owner check at all (RK112).
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "section", "drop", "RK1"]) == EXIT_USAGE
    assert "is pointed at by RK1" in capsys.readouterr().err
    assert read(config) == RATIONALE


def test_drop_of_an_occupied_subtree_exits_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path, improvements=NESTING)
    assert main(["-C", str(tmp_path), "section", "drop", "RK1"]) == EXIT_USAGE
    assert "resolving to nothing" in capsys.readouterr().err
    assert read(config) == NESTING


def test_a_refusal_exits_two_and_writes_nothing(tmp_path, capsys):
    config = project(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "section",
                "add",
                "RK9",
                "--title",
                "A design",
                "--body",
                "Prose.",
            ]
        )
        == EXIT_USAGE
    )
    assert "anchor.unknown" in capsys.readouterr().err
    assert read(config) == RATIONALE


class _Stdin:
    """The one thing a pipe has to do, without a real pipe."""

    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text
