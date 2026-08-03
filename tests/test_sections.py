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

The fourth claim is where RK166 lands: under an outline the **anchor** is that derivation
even for a task, no outline project's prose file declaring a block heading at all — and a
top-level anchor is placed after the last top-level section rather than refused, because "a
heading they can add" was an argument about an edit the guard denies.

And the first is where RK169 does. "Deleted whole" is only safe while the guard sees
everything the deletion would take, and it saw **headings**: a corpus addressing a design as
`- **XIV.8.7 — …**` had that design deleted with its shipped parent, because a bullet is not a
section. So ownership is decided from the *name* as well — an address under the anchor is
claimed prose whatever shape the file writes it in.
"""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

import corpora
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.document import Document, UnknownBlock
from roadkeep.schema import Schema, SchemaError
from roadkeep.linting import lint
from roadkeep.sections import (
    AnchorClaimed,
    NoSuchSection,
    SectionClaimed,
    SectionExists,
    SectionError,
    SectionOccupied,
    UnknownParent,
    add,
    amend,
    anchored,
    drop,
    find,
    nested,
    pointers,
    words,
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


def test_a_table_a_fence_and_a_quote_cost_the_budget_nothing(tmp_path):
    # RK136: Claude Tray's `III` is 269 words of which 230 are the measured-baseline table
    # the file keeps *because it is data, not design*. Charged as prose, the only remedies
    # on offer were splitting a six-row measurement in half or declaring `section = 300`.
    body = (
        "One two three four five.\n\n"
        "| a header | and another |\n| --- | --- |\n| twelve words | that are not prose |\n\n"
        "```\nnine ten eleven twelve thirteen fourteen\n```\n\n"
        "> Somebody else's fifteen sixteen seventeen words.\n"
    )
    assert words(body) == 5
    assert len(body.split()) == 41  # what the same section used to be charged


def test_a_list_is_argument_and_is_charged(tmp_path):
    # Deliberately not exempt: a bullet is how an argument is written in these files, and a
    # budget a reformat reopens is not one. `structural` reads them as shapes for *width*,
    # which is a different question with a different answer (RK99).
    assert words("- One two three.\n- Four five six.\n") == 8  # the markers included


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


#: What Shio's rationale file yields at its pin — 79 anchored sections, and every pointer
#: in its roadmap resolving to one of them. Exact rather than a floor because the read is
#: pinned (RK105): 120 was a floor this file fell through as Shio shipped, and a number that
#: somebody else's progress crosses is a red about their afternoon.
SHIO_SECTIONS = 79


def test_a_live_outline_file_yields_its_sections_and_answers_its_pointers():
    corpora.require(corpora.SHIO)
    sections = anchored(corpora.document(corpora.SHIO, "improvements"))
    assert len(sections) == SHIO_SECTIONS
    declared = {s.anchor for s in sections}
    pointers = [
        e.task.ref for e in corpora.document(corpora.SHIO, "roadmap").entries if e.task.ref
    ]
    # Every one of them, and not a slack count: an unresolved pointer here is a defect in
    # *that* backlog for `lint` to report, which is the whole point — before RK44 the
    # answer was 74 of them, and the gate was reporting the file rather than reading it.
    assert pointers and [p for p in pointers if p not in declared] == []


def test_a_lettered_heading_in_the_live_corpus_becomes_a_section_the_budget_charges():
    """The shape RK47 measured — a fourth level spelled with a letter, escaping the budget.

    The parser's side of it is the local fixture above (`§IX.2a`); what the corpus added was
    that twenty of them existed and one ran to 779 words. Turing has since renumbered them
    to `III.1.1`, so at this pin the shape is not there to read — which the pin turns into
    one stable skip instead of a test that goes red the day somebody else renames a heading.
    """
    corpora.require(corpora.TURING)
    sections = anchored(corpora.document(corpora.TURING, "improvements"))
    lettered = [s for s in sections if s.anchor[-2:-1] == "." and s.anchor[-1].isalpha()]
    if not lettered:
        pytest.skip(f"{corpora.TURING} spells no fourth level with a letter any more")
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


# -- amending a live section (RK123) ------------------------------------------


def test_the_rationale_of_an_open_task_can_be_corrected(tmp_path):
    # The gap, stated as its two halves: the drop is refused — correctly, RK1 is open and
    # points here — and the same anchor is amendable, which is what was missing.
    config = project(tmp_path)
    with pytest.raises(SectionClaimed):
        drop(config.document("improvements"), "RK1", claimed=pointers(config))

    document, section, changed = amend(
        config, "improvements", "RK1", body="One hypothesis is eliminated."
    )
    document.save()

    assert changed == ("body",)
    assert "One hypothesis is eliminated." in read(config)
    assert "The reasoning the line has no room for." not in read(config)


def test_the_subtree_survives_an_amend_of_its_root(tmp_path):
    # Its own prose and never the subtree: a subsection has an anchor to be named by, and
    # deleting one as a side effect of correcting a paragraph is `drop`'s job, with
    # `drop`'s refusals.
    config = project(tmp_path)
    document, _, _ = amend(config, "improvements", "RK1", body="A shorter reasoning.")
    document.save()

    body = read(config)
    assert "#### §RK1.1 A subsection" in body
    assert "Which belongs to the section above." in body
    assert "## Block B — Authoring" in body


def test_a_subsection_is_amended_by_its_own_anchor(tmp_path):
    config = project(tmp_path)
    document, section, changed = amend(
        config, "improvements", "RK1.1", body="Corrected in place."
    )
    document.save()

    assert (section.anchor, changed) == ("RK1.1", ("body",))
    assert "Corrected in place." in read(config)
    assert "The reasoning the line has no room for." in read(config)


def test_the_heading_text_moves_without_the_prose(tmp_path):
    config = project(tmp_path)
    document, section, changed = amend(
        config, "improvements", "RK1", title="A first design, restated"
    )
    document.save()

    assert changed == ("title",) and section.title == "A first design, restated"
    assert "### §RK1 A first design, restated" in read(config)
    assert "The reasoning the line has no room for." in read(config)


def test_an_amend_that_changes_nothing_writes_nothing(tmp_path):
    config = project(tmp_path)
    document, _, changed = amend(
        config, "improvements", "RK1", body="The reasoning the line has no room for."
    )
    document.save()
    assert changed == () and read(config) == RATIONALE


def test_the_replacement_is_reflowed_and_a_table_is_not(tmp_path):
    # The same narrow rule `add` writes under, because it is the same function: prose is
    # filled to the width and a shape the tool did not author is inserted as written.
    config = project(tmp_path, extra="[limits]\nprose = 40\n")
    document, _, _ = amend(
        config,
        "improvements",
        "RK1",
        body="A paragraph long enough that the configured width has to break it somewhere.\n\n| a | b |\n|---|---|\n| 1 | 2 |",
    )
    document.save()

    body = read(config)
    assert "| a | b |\n" in body and "|---|---|\n" in body
    assert max(len(line) for line in body.splitlines() if not line.startswith("|")) <= 40


def test_the_budget_is_charged_what_the_gate_charges(tmp_path):
    # The subtree, not the paragraph: a body that clears the limit alone and puts the
    # section over it with its subsections is an amend that passes and a `lint` that
    # refuses — which is the one way this write can be wrong while looking right.
    config = project(tmp_path, extra="[limits]\nsection = 12\n")
    with pytest.raises(SectionError) as raised:
        amend(config, "improvements", "RK1", body="Six words, which is under twelve.")
    assert "with its subsections" in str(raised.value)
    assert read(config) == RATIONALE


def test_an_anchor_this_file_does_not_declare_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NoSuchSection):
        amend(config, "improvements", "RK9", body="Prose for nobody.")
    assert read(config) == RATIONALE


def test_an_empty_body_is_refused_rather_than_written(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SectionError):
        amend(config, "improvements", "RK1", body="   ")
    assert read(config) == RATIONALE


def test_the_command_reads_the_replacement_from_stdin(tmp_path, capsys, monkeypatch):
    config = project(tmp_path)
    monkeypatch.setattr("sys.stdin", _Stdin("The corrected reasoning, by pipe."))
    assert (
        main(["-C", str(tmp_path), "section", "amend", "RK1", "--body", "-"]) == EXIT_OK
    )
    assert "(body)" in capsys.readouterr().out
    assert "The corrected reasoning, by pipe." in read(config)


def test_an_amend_with_neither_field_never_opens_the_pipe(tmp_path, capsys):
    # Refused rather than defaulted to stdin: a command with nothing to amend that blocks
    # on a pipe nobody opened is a session that stops.
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "section", "amend", "RK1"]) == EXIT_USAGE
    assert "nothing to amend" in capsys.readouterr().err
    assert read(config) == RATIONALE


def test_json_says_which_fields_changed(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "section",
                "amend",
                "RK1",
                "--title",
                "Restated",
                "--body",
                "And rewritten.",
                "--json",
            ]
        )
        == EXIT_OK
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["changed"] == ["title", "body"]
    assert payload["anchor"] == "RK1" and payload["title"] == "Restated"


class _Stdin:
    """The one thing a pipe has to do, without a real pipe."""

    def __init__(self, text: str) -> None:
        self._text = text

    def read(self) -> str:
        return self._text


# -- the first section of a new block (RK166) ----------------------------------


def test_a_new_top_level_section_lands_after_the_last_one(tmp_path):
    # The deadlock RK141 closed, one file over: `block add` skips a prose file organised by
    # an outline rather than by blocks, `section add` refused an anchor extending nothing,
    # and the guard denies the edit that would declare it — so a newly declared block's
    # first design was reachable by no verb at all.
    config = outline(tmp_path)
    document, section = add(config, "improvements", "IX", "A ninth theme", "What it is for.")
    document.save()

    body = read(config)
    assert body.index("A fourth level spelled with a letter") < body.index("IX A ninth theme")
    assert body.index("IX A ninth theme") < body.index("## B — Context")
    assert section.anchor == "IX"


def test_a_new_top_level_section_takes_the_depth_this_file_writes_one_at(tmp_path):
    # Not optional and not cosmetic: a top level written at a subsection's depth is not a
    # top level at all — it lands inside the previous one's subtree, where every reader that
    # asks a heading where it ends would find it.
    config = outline(tmp_path)
    document, section = add(config, "improvements", "IX", "A ninth theme", "Prose.")
    assert section.level == 2  # `## VIII.`, read off the file rather than defaulted to 3
    document.save()
    assert "## IX A ninth theme" in read(config)


def test_a_named_level_still_wins_over_the_derived_one(tmp_path):
    # A project whose outline nests four deep has a depth no rule here knows.
    config = outline(tmp_path)
    document, section = add(config, "improvements", "IX", "A ninth theme", "Prose.", level=3)
    assert section.level == 3
    document.save()


def test_a_nested_anchor_whose_parent_is_missing_is_still_refused(tmp_path):
    # The half of the old refusal that was right: this is a typo in an address, and
    # appending it would file somebody's paragraph under a design it does not extend.
    config = outline(tmp_path)
    with pytest.raises(UnknownParent) as raised:
        add(config, "improvements", "IX.4", "A reading nothing precedes", "Prose.")
    assert "no section §IX.4 extends" in str(raised.value)
    assert read(config) == OUTLINE_RATIONALE


def test_the_id_scheme_refuses_a_top_level_anchor_as_it_always_did(tmp_path):
    # Under `id` the anchor *is* the id, so it carries no place and no level: reaching the
    # top level with one means the id names no open line, which stays a refusal.
    config = project(tmp_path)
    with pytest.raises(UnknownParent):
        add(config, "improvements", "9", "A reading nothing precedes", "Prose.")
    assert read(config) == RATIONALE


def test_a_new_top_level_section_in_a_file_with_none_goes_last(tmp_path):
    config = project(
        tmp_path,
        improvements="# Improvements\n\nA preface nobody numbered.\n",
        top='ref_scheme = "outline"\n',
    )
    document, section = add(config, "improvements", "I", "A first theme", "Prose.")
    document.save()
    # One level under the file's shallowest heading, which is its title in every corpus.
    assert section.level == 2
    assert read(config).endswith("## I A first theme\n\nProse.\n")


def test_a_task_s_section_under_an_outline_is_placed_by_its_anchor(tmp_path):
    # `add --section` passes the task, which forced the block branch — and no outline
    # project's prose file declares a block heading at all, so that branch could only ever
    # refuse. Under an outline the author chose the anchor, and it states the place.
    from roadkeep.authoring import add as add_task

    config = outline(tmp_path)
    insertion = add_task(
        config,
        block="B",
        symptom="A fourth symptom",
        why="Because of a fourth reason.",
        ref="VIII.2",
        section=("A second design", "The reasoning for it."),
    )
    assert insertion.section is not None and insertion.section.level == 3
    body = read(config)
    # The end of §VIII's subtree, which is where every anchor that extends one goes — not
    # under the roadmap's Block B, a heading this file does not declare and never will.
    assert body.index("#### XIV.8.7") < body.index("VIII.2")
    assert body.index("VIII.2") < body.index("## B — Context")


def test_the_whole_deadlock_ends_with_a_clean_gate(tmp_path):
    # Every step the report walked, in one test: the block, its first top-level section, a
    # task whose pointer resolves, and the gate that used to be red at step three.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "CT"\nref_scheme = "outline"\n[files]\n'
        'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    for name, body in {
        "ROADMAP.md": "# Roadmap\n\n## Block AG — Themes\n",
        "CHANGELOG.md": "# Shipped\n\n## Block AG — Themes\n",
        "IMPROVEMENTS.md": "# Tray — Design rationale\n\n## XXI — A theme (Block AG)\n\nProse.\n",
    }.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)

    at = ["-C", str(tmp_path)]
    assert main([*at, "block", "add", "AI", "--title", "A new theme"]) == EXIT_OK
    assert main([*at, "section", "add", "XXII", "--title", "A new theme (Block AI)",
                 "--body", "What this theme is for."]) == EXIT_OK
    assert main([*at, "add", "--block", "AI", "--ref", "XXII.1", "--symptom", "A symptom",
                 "--why", "Because of a reason.", "--section", "A design",
                 "--section-body", "The reasoning."]) == EXIT_OK
    assert main([*at, "lint"]) == EXIT_OK

    prose = (tmp_path / "IMPROVEMENTS.md").read_text(encoding="utf-8")
    assert "## XXII A new theme (Block AI)" in prose
    assert "### XXII.1 A design" in prose


# -- the guard reads the name, not the shape (RK169) ---------------------------

#: Turing's shape, verbatim from the adoption that measured it: a design addressed as a
#: bullet under the heading a drop was aimed at, which is not a section and so was invisible
#: to the guard that walks the sections.
BULLETED = """# Turing — Design rationale

## XIV — Cloud

### XIV.8 The seed config

- **XIV.8.7 — ship Cloud default config as a GLOBAL seed ZIP (T373).**
"""

BULLET_BACKLOG = """# Roadmap

## Block A — Themes

- 📋 **RK373** (deps: —) **A symptom** — Because of a reason. → §XIV.8.7
"""


def bulleted(tmp_path: Path) -> Config:
    return project(
        tmp_path,
        improvements=BULLETED,
        roadmap=BULLET_BACKLOG,
        top='ref_scheme = "outline"\n',
    )


def test_a_bullet_an_open_line_points_at_is_not_deleted_with_its_parent(tmp_path):
    # `section drop XIV` was accepted and took §XIV.8 with it, and the design of an open task
    # went with it without a word: a bullet is not a section, so the subtree looked unowned.
    config = bulleted(tmp_path)
    with pytest.raises(AnchorClaimed) as raised:
        drop(config.document("improvements"), "XIV", claimed=pointers(config))
    assert "§XIV.8.7 (RK373)" in str(raised.value)
    assert read(config) == BULLETED


def test_the_two_findings_stay_two_reports_instead_of_becoming_data_loss(tmp_path):
    # That the pointer does not resolve is the project's, and `lint` says so. That the verb
    # whose whole job is the orphan deleted a live design *because* the pointer was already
    # broken was this tool's — the finding made the content invisible to its own guard.
    config = bulleted(tmp_path)
    codes = [finding.code for finding in lint(config).findings]
    assert "ref.unresolved" in codes
    with pytest.raises(AnchorClaimed):
        drop(config.document("improvements"), "XIV", claimed=pointers(config))
    assert read(config) == BULLETED


def test_the_immediate_parent_is_refused_the_same_way(tmp_path):
    # Not only the grandparent: the check is every claimed pointer below the anchor.
    config = bulleted(tmp_path)
    with pytest.raises(AnchorClaimed):
        drop(config.document("improvements"), "XIV.8", claimed=pointers(config))
    assert read(config) == BULLETED


def test_the_name_is_read_segment_by_segment(tmp_path):
    # `§XIV.8.7` does not descend from `§XIV.8.70`, and a guard that compared strings would
    # refuse a drop nobody claimed — the care `_extends` already takes about where one ends.
    config = project(
        tmp_path,
        improvements=BULLETED.replace("### XIV.8 The", "### XIV.80 The"),
        roadmap=BULLET_BACKLOG,
        top='ref_scheme = "outline"\n',
    )
    document, section = drop(
        config.document("improvements"), "XIV.80", claimed=pointers(config)
    )
    document.save()
    assert section.anchor == "XIV.80" and "XIV.80" not in read(config)


def test_the_anchor_itself_is_still_the_other_refusal(tmp_path):
    # Asked first, because its message names the pointer that claims this exact section
    # rather than one under it — the same remedy, a more precise sentence.
    config = outline(tmp_path)  # here §XIV.8.7 is a heading, and RK2 points at it
    with pytest.raises(SectionClaimed):
        drop(config.document("improvements"), "XIV.8.7", claimed=pointers(config))
    assert read(config) == OUTLINE_RATIONALE


def test_the_line_that_is_leaving_does_not_claim_its_own_subtree(tmp_path):
    # `ship` passes `leaving`, so the claim that is the *reason* for the drop is not one of
    # these — otherwise a task pointing at a descendant could never ship at all.
    config = bulleted(tmp_path)
    document, section = drop(
        config.document("improvements"), "XIV", claimed=pointers(config, leaving="RK373")
    )
    document.save()
    assert section.anchor == "XIV" and read(config) == "# Turing — Design rationale\n"
