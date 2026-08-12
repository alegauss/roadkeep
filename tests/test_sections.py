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
from roadkeep.authoring import IdInUse, refuse_reuse
from roadkeep.backlog import Where, Whereabouts
from roadkeep.cli import EXIT_OK, EXIT_USAGE, build_parser, main
from roadkeep.config import Config
from roadkeep.kernel.document import Document, UnknownBlock
from roadkeep.kernel.schema import Schema, SchemaError
from roadkeep.linting import lint
from roadkeep.sections import (
    AmbiguousTitle,
    AnchorClaimed,
    AnchorIsId,
    _elsewhere,
    NoSuchSection,
    NotASibling,
    SameAnchor,
    SectionClaimed,
    SectionExists,
    SectionError,
    SectionOccupied,
    UnknownParent,
    add,
    amend,
    amend_untitled,
    anchored,
    citing,
    drop,
    find,
    move,
    nested,
    paragraphs,
    pointers,
    structural,
    titled,
    untitled,
    words,
)

#: This repository, whose `docs/` are the conformance fixture — read, never written.
HERE = Path(__file__).resolve().parents[1]
ROADMAP = "docs/ROADMAP.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"
STRATEGY = "docs/STRATEGY.md"

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
    document, section, _ = drop(config.document("improvements"), "RK1")
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
    document, _, _ = drop(config.document("improvements"), "RK2")
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
    document, _, _ = drop(
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
    document, _, _ = drop(config.document("improvements"), "RK1", claimed=pointers(config))
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
    assert "Block A" in str(raised.value) and IMPROVEMENTS in str(raised.value)


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


def test_the_repository_s_own_preface_files_itself_before_the_first_block(governed):
    # The reading that opened RK45: writing §0.4 with `section add` put it under Block F,
    # 50 lines and five headings away from the §0.3 it continues. Unsaved — this file is
    # the conformance fixture, and a test that rewrote it would be measuring itself.
    config = Config.discover(governed)
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


#: The seam RK147 closed, and the fixture that had been missing: a project whose *prose
#: file* declares limits of its own, so `config.schema` and `config.schema_for(role)` stop
#: returning the same number. Without one, both readings agree and neither door is proven.
PER_ROLE = "[limits]\nsection = 10\n[limits.improvements]\nsection = 30\n"


def test_the_writing_door_reads_the_limit_the_file_declares(tmp_path):
    # L1: the schema is enforced where the text is created. `_check` read the project's
    # top-level numbers while the gate charged `schema_for(role)`, so a *looser* rationale
    # budget had `section add` refusing prose `lint` would accept — and a refusal on legal
    # text is a refusal an author routes around.
    config = project(tmp_path, extra=PER_ROLE)
    document, section = add(config, "improvements", "RK2", "A design", "word " * 20)
    document.save()
    assert section.words == 20
    assert "section.too-long" not in {
        f.code for f in lint(Config.discover(tmp_path)).findings
    }


def test_the_tighter_declaration_is_refused_before_the_paragraph_exists(tmp_path):
    # The other direction, and the one L1 is actually about: a project that declares a
    # tighter rationale budget used to get it only from the backstop, after the prose was
    # written — which is the analysis this tool exists to spend nobody's tokens on.
    config = project(tmp_path, extra="[limits]\nsection = 30\n[limits.improvements]\nsection = 10\n")
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK2", "A design", "word " * 20)
    assert [v.code for v in raised.value.violations] == ["body.too-long"]
    assert "limit is 10" in raised.value.violations[0].message


def test_an_amend_is_held_to_the_same_number_as_the_add(tmp_path):
    # Both doors, one reading: `amend`'s subtree check was the one place already calling
    # `schema_for`, so a project with a per-role limit had `add` and `amend` disagreeing.
    config = project(tmp_path, extra=PER_ROLE)
    add(config, "improvements", "RK2", "A design", "word " * 20)[0].save()
    document, amended, changed = amend(
        Config.discover(tmp_path), "improvements", "RK2", body="word " * 25
    )
    document.save()
    assert changed == ("body",) and amended.words == 25
    assert "section.too-long" not in {
        f.code for f in lint(Config.discover(tmp_path)).findings
    }


def test_an_id_anchor_that_names_no_open_task_is_refused(tmp_path):
    # The pointer is the id (RK27), so this section is an orphan the moment it exists.
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK9", "A design", "Prose.")
    assert [v.code for v in raised.value.violations] == ["anchor.unknown"]
    assert read(config) == RATIONALE


def ledgered(tmp_path: Path, *, marker: str = "✅", design: bool = False) -> Config:
    """A project whose ledger holds RK9 — the state `add the line first` cannot be taken in."""
    improvements = RATIONALE
    if design:
        improvements += "\n### §RK9 A design that outlived its line\n\nProse.\n"
    config = project(
        tmp_path, improvements=improvements, extra='changelog = "docs/CHANGELOG.md"\n'
    )
    with (config.root / "docs" / "CHANGELOG.md").open("w", encoding="utf-8", newline="") as h:
        h.write(
            f"# Shipped\n\n## Block A — The model\n\n"
            f"- {marker} **RK9** **A ninth symptom** — It left, one way or the other.\n"
        )
    return Config.discover(tmp_path)


def test_an_id_that_never_existed_is_still_told_to_add_the_line(tmp_path):
    # The one state that advice fits, and it keeps it: nothing anywhere carries RK9, so the
    # line is the thing missing and `add` is the door.
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK9", "A design", "Prose.")
    assert "add the line first" in str(raised.value)


def test_a_shipped_id_is_offered_the_doors_that_open(tmp_path):
    # RK238: `add the line first` is what `refuse_reuse` refuses — the id is in the ledger, so
    # that `add` is `IdInUse` and retired-never-reused is the rule saying so. The author was
    # handed the single door RK4 closes, and spent the attempt before learning it.
    config = ledgered(tmp_path)
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK9", "A design", "Prose.")
    message = str(raised.value)
    assert "add the line first" not in message
    assert "the changelog records it as ✅" in message
    assert "`record amend`" in message and "outline anchor" in message
    # And the advice is followable: the door it names is the one that is not refused.
    with pytest.raises(IdInUse):
        refuse_reuse(config, "RK9")


def test_a_retired_id_is_named_by_the_marker_the_ledger_holds(tmp_path):
    # Three states, one sentence, and only the last is a typo — the split `NotSetAside`
    # already makes: which of them it was is the whole of what the author needs.
    # `amend` is the door that reaches it: the section is still in the file, so the earlier
    # `NoSuchSection` does not fire and `_check` is what answers — one composer, so the two
    # doors cannot describe one entry differently.
    config = ledgered(tmp_path, marker="🗑", design=True)
    with pytest.raises(SchemaError) as raised:
        amend(config, "improvements", "RK9", body="Prose that outlived the line.")
    assert "the changelog records it as 🗑" in str(raised.value)
    assert "add the line first" not in str(raised.value)


def test_the_sentence_naming_where_an_id_is_comes_from_one_composer(tmp_path):
    # RK240: `deferring` and `sections` both wrote `the changelog records it as X` from the
    # same read of the same file, so the refusal an author is handed was two strings. It is
    # one type now, and this asserts the identity rather than the spelling — a test quoting
    # the words a second time would be the third copy.
    config = ledgered(tmp_path)
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK9", "A design", "Prose.")
    assert Whereabouts.of(config, "RK9").sentence in str(raised.value)


def test_the_record_amend_door_is_chosen_from_the_state_and_not_from_a_sentence(tmp_path):
    # The one caller that acts on the fact rather than printing it: `record amend` is the
    # remedy for an id the ledger holds, and the branch reads the marker (RK240).
    config = ledgered(tmp_path)
    assert Whereabouts.of(config, "RK9").recorded
    assert Whereabouts.of(config, "RK99").where is Where.NOWHERE
    assert Whereabouts.of(config, "RK1").where is Where.OPEN


def test_an_outline_anchor_reads_no_file_to_be_told_where_no_id_is(tmp_path, monkeypatch):
    # An outline anchor named a section and never a task, so no file can answer a question
    # `_unknown` will not ask (RK240) — the ledger parse this used to spend anyway.
    config = ledgered(tmp_path)
    reads: list[str] = []
    original = Config.document
    monkeypatch.setattr(
        Config, "document", lambda self, role: (reads.append(role), original(self, role))[1]
    )
    assert _elsewhere(config, config.schema, "IV.2", None) is None
    assert reads == []
    # And an id-shaped one still reads them, that being the branch with a door to hand over.
    assert _elsewhere(config, config.schema, "RK9", None) is not None
    assert "changelog" in reads


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


#: Claude Code Tray's `§XXII`, minimised: a container whose own prose is two sentences and
#: whose three live subsections are the rest. Every piece is inside a 40-word budget and the
#: subtree is not, which is the state `lint` calls clean and the writer refused.
CONTAINED = """# Improvements

## §XXII The container

Two sentences of intro. It describes a budget as full.

### §RK1 A first design

The reasoning the first line has no room for, at some length.

### §RK2 A second design

The reasoning the second line has no room for, at some length.

### §RK3 A third design

The reasoning the third line has no room for, at some length.
"""

OUTLINED_BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 📋 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2
- 📋 **RK3** (deps: —) **A third symptom** — Because of a third reason. → §RK3
"""


def contained(tmp_path: Path, *, limit: int = 40) -> Config:
    return project(
        tmp_path,
        roadmap=OUTLINED_BACKLOG,
        improvements=CONTAINED,
        extra=f"[limits]\nsection = {limit}\n",
    )


def test_a_container_nothing_points_at_is_charged_its_own_prose(tmp_path):
    # The defect: the subtree was charged unconditionally, so a nine-word correction to a
    # two-sentence intro was refused for the 900 words of three live subsections — on a file
    # that passes the gate. `drop` refuses by those same pointers and the guard denies the
    # hand edit, so every door was closed and the file left saying something untrue.
    config = contained(tmp_path)
    assert lint(config).clean  # the gate's own verdict on this file, before and after
    whole = find(config.document("improvements"), "XXII")
    assert whole.words > 40  # the number that used to refuse
    (own,) = [s for s in anchored(config.document("improvements")) if s.anchor == "XXII"]
    assert own.words <= 40  # the number the gate actually charges it

    document, amended, changed = amend(
        config, "improvements", "XXII", body="A shorter intro that is now true."
    )
    document.save()
    assert changed == ("body",)
    body = read(config)
    assert "A shorter intro that is now true." in body
    assert "It describes a budget as full." not in body
    # The subsections are untouched: an intro is its own section, and correcting one is not
    # a deletion of what sits under it.
    for anchor in ("RK1", "RK2", "RK3"):
        assert f"§{anchor}" in body
    assert lint(Config.discover(tmp_path)).clean


def test_a_pointed_at_section_is_still_charged_its_subtree(tmp_path):
    # The other half, and the reason this is a split rather than a removal: a pointer hands
    # a reader the whole subtree, so that is what the gate charges — and a writer that let
    # the subtree over the limit would be an amend that passes and a `lint` that refuses.
    config = project(tmp_path, extra="[limits]\nsection = 12\n")
    with pytest.raises(SectionError) as raised:
        amend(config, "improvements", "RK1", body="Six words, which is under twelve.")
    assert "with its subsections" in str(raised.value)
    assert read(config) == RATIONALE


def test_an_anchor_two_prose_files_declare_is_charged_what_the_gate_charges_it(tmp_path):
    # RK232, and the state is measured rather than imagined: Turing at f08304fcb1 declares 13
    # anchors in both prose files, one of them pointed at — so the writer charged 365 words of
    # somebody else's subtree while the gate charged 73 and called that check clean.
    both = "# Strategy\n\n## Block A — The model\n\n### §RK1 The same anchor\n\nElsewhere.\n"
    config = project(
        tmp_path,
        roadmap=f"# Roadmap\n\n## Block A — The model\n\n{RK1_LINE}\n",
        extra='strategy = "docs/STRATEGY.md"\n[limits]\nsection = 12\n',
    )
    with (config.root / "docs" / "STRATEGY.md").open("w", encoding="utf-8", newline="") as h:
        h.write(both)
    config = Config.discover(tmp_path)

    # The gate's own reading first, so the claim is agreement and not a second opinion. Both
    # ends of the one defect since RK239: the pointer's, and each of the two headings'.
    doubled = ["ref.ambiguous", "section.ambiguous", "section.ambiguous"]
    assert sorted(f.code for f in lint(config).findings) == doubled
    document, amended, changed = amend(
        config, "improvements", "RK1", body="Six words, which is under twelve."
    )
    assert changed == ("body",)
    document.save()
    assert "Six words, which is under twelve." in read(config)
    # And the ambiguity is still the finding, which is the one this door must not answer.
    assert sorted(f.code for f in lint(Config.discover(tmp_path)).findings) == doubled


def test_an_anchor_the_sibling_prose_file_declares_is_refused_at_the_door(tmp_path):
    # RK302, reproduced: `SectionExists` asked the document it was writing into and nobody
    # else, so the second `section add` reported success and `lint` then named the state its
    # own message calls unresolvable — out of which `drop` was the only exit.
    both = "# Strategy\n\n## Block A — The model\n\n### §RK1 The same anchor\n\nElsewhere.\n"
    config = project(
        tmp_path,
        roadmap=f"# Roadmap\n\n## Block A — The model\n\n{RK1_LINE}\n",
        extra='strategy = "docs/STRATEGY.md"\n',
        improvements="# Improvements\n\n## Block A — The model\n",
    )
    with (config.root / "docs" / "STRATEGY.md").open("w", encoding="utf-8", newline="") as h:
        h.write(both)
    config = Config.discover(tmp_path)

    with pytest.raises(SectionExists) as raised:
        add(config, "improvements", "RK1", "A design", "Prose.")
    message = str(raised.value)
    assert "docs/STRATEGY.md:5" in message
    assert "across every prose file this project declares" in message
    # Refused before the write, so the file the caller named still holds every byte it held.
    assert "RK1" not in read(config)
    assert lint(config).findings == ()


def test_the_outline_repro_that_filed_it_is_refused_on_both_calls(tmp_path):
    # The reproduction verbatim: `IX` and `IX.1` into improvements, then the same two into
    # strategy. All four used to succeed and print their line counts.
    config = project(
        tmp_path,
        top='ref_scheme = "outline"\n',
        extra='strategy = "docs/STRATEGY.md"\n',
        improvements="# Improvements\n\n## Block A — The model\n",
    )
    with (config.root / "docs" / "STRATEGY.md").open("w", encoding="utf-8", newline="") as h:
        h.write("# Strategy\n\n## Block A — The model\n")
    config = Config.discover(tmp_path)
    for anchor, title in (("IX", "A design"), ("IX.1", "A child")):
        document, _ = add(config, "improvements", anchor, title, "Prose here.")
        document.save()
    config = Config.discover(tmp_path)
    for anchor, title in (("IX", "A design"), ("IX.1", "A child")):
        with pytest.raises(SectionExists) as raised:
            add(config, "strategy", anchor, title, "Prose here.")
        assert IMPROVEMENTS in str(raised.value)


def test_the_same_anchor_in_the_file_being_written_still_names_that_file(tmp_path):
    # The local refusal is unchanged and is the one that runs first: an author writing into
    # IMPROVEMENTS.md is told about IMPROVEMENTS.md, not about a file they did not mention.
    config = project(tmp_path, roadmap=f"# Roadmap\n\n## Block A — The model\n\n{RK1_LINE}\n")
    with pytest.raises(SectionExists) as raised:
        add(config, "improvements", "RK1", "A second design", "Prose.")
    assert IMPROVEMENTS in str(raised.value)
    assert "across every prose file" not in str(raised.value)


def test_the_state_this_condition_is_for_is_one_a_live_corpus_carries():
    """The count RK232 was filed to get, and it is what decided the condition over a retire.

    The idea's own argument against itself was that `lint` reports `ref.ambiguous` there, so
    no tree somebody works in reaches the disagreement. Turing does. At `f08304fcb1` thirteen
    anchors are declared by both the improvements and the strategy file, and `X.1` is pointed
    at by T354 — where the gate charges the section's own 73 words and the writer charged the
    365 of a subtree, so correcting the intro was refused for 292 words that are somebody
    else's subsections. RK215's finding, in the one state RK215's fix did not cover.

    The ambiguity is a finding either way, and that is the point: it is the author's edit and
    a larger one, while the paragraph in front of them is a correction this door was refusing.
    """
    corpora.require(corpora.TURING)
    settings = corpora.config(corpora.TURING)
    roles = [r for r in ("improvements", "strategy") if corpora.has(corpora.TURING, r)]
    if len(roles) < 2:
        pytest.skip(f"{corpora.TURING} no longer declares two prose files")
    documents = {role: corpora.document(corpora.TURING, role) for role in roles}
    declared: dict[str, list[str]] = {}
    for role, document in documents.items():
        for anchor in dict.fromkeys(s.anchor for s in anchored(document)):
            declared.setdefault(anchor, []).append(role)
    assert len([a for a, rs in declared.items() if len(rs) > 1]) == 13

    pointed = {
        e.task.ref
        for e in corpora.document(corpora.TURING, "roadmap").entries
        if e.task.ref and len(declared.get(e.task.ref, ())) > 1
    }
    assert pointed == {"X.1"}
    improvements = documents["improvements"]
    (own,) = [s for s in anchored(improvements) if s.anchor == "X.1"]
    subtree = find(improvements, "X.1")
    limit = settings.schema_for("improvements").section_max
    assert own.words == 73 and subtree.words == 365 and limit == 250


def test_a_container_is_still_held_to_the_limit_by_its_own_prose(tmp_path):
    # Unpointed does not mean unbudgeted: `_check` charges the body before the write, which
    # is the same number `lint` charges the section — so the door is open and not unguarded.
    config = contained(tmp_path)
    with pytest.raises(SectionError) as raised:
        amend(config, "improvements", "XXII", body=" ".join(f"word{n}" for n in range(50)))
    assert "50 words, limit is 40" in str(raised.value)
    assert "with its subsections" not in str(raised.value)
    assert read(config) == CONTAINED


def test_a_deferred_line_still_claims_the_subtree(tmp_path):
    # Both live roles, as the gate reads them: work set aside keeps its pointer and its
    # section (RK96), so a deferred line is a claim and not an absence. The roadmap is empty
    # here, so a reader of it alone would charge this container its own prose and let a
    # subtree the gate refuses through.
    config = project(
        tmp_path,
        roadmap="# Roadmap\n\n## Block A — The model\n",
        improvements=CONTAINED,
        extra='deferred = "docs/DEFERRED.md"\n[limits]\nsection = 40\n',
    )
    store = config.root / "docs" / "DEFERRED.md"
    with store.open("w", encoding="utf-8", newline="") as handle:
        handle.write(
            "# Deferred\n\n## Block A — The model\n\n"
            "- ⏸ **RK9** (deps: —) **A paused symptom** — paused: later. → §XXII\n"
        )
    config = Config.discover(tmp_path)
    with pytest.raises(SectionError) as raised:
        amend(config, "improvements", "XXII", body="A shorter intro that is now true.")
    assert "with its subsections" in str(raised.value)
    assert read(config) == CONTAINED


def paused(tmp_path: Path, *, roadmap: str = "# Roadmap\n\n## Block A — The model\n") -> Config:
    """RK1's line set aside, with the §RK1 design RK96 keeps for the return trip."""
    config = project(tmp_path, roadmap=roadmap, extra='deferred = "docs/DEFERRED.md"\n')
    with (config.root / "docs" / "DEFERRED.md").open("w", encoding="utf-8", newline="") as h:
        h.write(
            "# Deferred\n\n## Block A — The model\n\n"
            "- ⏸ **RK1** (deps: —) **A first symptom** — set aside (later): "
            "Because of a reason. → §RK1\n"
        )
    return Config.discover(tmp_path)


def test_a_paused_tasks_rationale_can_be_corrected(tmp_path):
    # RK231, and RK123's deadlock displaced: `drop` refuses while the store's pointer claims
    # the anchor, the guard denies the `Edit`, and `amend` read the roadmap alone — so the
    # design of a line the tool itself set aside was the one nobody could correct.
    config = paused(tmp_path)
    document, section, _ = amend(config, "improvements", "RK1", body="The reasoning, corrected.")
    assert section.body.startswith("The reasoning, corrected.")
    document.save()
    assert "The reasoning, corrected." in read(config)


def test_a_section_can_be_written_for_a_line_that_is_set_aside(tmp_path):
    # The other door `_task_for` gates. A pause keeps the block, so the placement a section
    # derives from the line is still there to derive from.
    config = paused(tmp_path, roadmap="# Roadmap\n\n## Block A — The model\n")
    document, written = add(
        config, "improvements", "RK1.2", "A later subsection", "Written while paused."
    )
    assert written.anchor == "RK1.2"
    document.save()
    assert "#### §RK1.2 A later subsection" in read(config)


def test_an_anchor_no_live_line_names_is_still_refused(tmp_path):
    # What the refusal is left with, and it is the whole of it: an id the ledger holds is
    # unknown here too, because a departure deletes the design in the same transaction.
    config = paused(tmp_path)
    with pytest.raises(SectionError) as raised:
        add(config, "improvements", "RK9", "A design", "For a line nothing carries.")
    assert [v.code for v in raised.value.violations] == ["anchor.unknown"]
    assert "no live task RK9" in str(raised.value)


def test_the_command_amends_the_container(tmp_path, capsys, monkeypatch):
    config = contained(tmp_path)
    monkeypatch.setattr(sys, "stdin", io.StringIO("A shorter intro that is now true."))
    argv = ["-C", str(tmp_path), "section", "amend", "XXII", "--body", "-"]
    assert main(argv) == EXIT_OK
    assert "XXII" in capsys.readouterr().out
    assert "A shorter intro that is now true." in read(config)


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


# -- one address for a file (RK181) -------------------------------------------


def refused(config: Config, capsys, *argv: str) -> str:
    """The refusal alone, with the whole filesystem path it must not contain checked here.

    `str(config.path(...))` and not `str(tmp_path)`: the harness echoes the `-C` it was
    invoked with, so the root is in every stderr — what RK181 is about is the *file's*
    absolute path, which is what a reader has to read past to reach the anchor.
    """
    assert main(["-C", str(config.root), *argv]) == EXIT_USAGE
    message = capsys.readouterr().err
    assert str(config.path("improvements")) not in message
    return message


def test_a_refused_drop_names_the_file_the_way_the_gate_names_it(tmp_path, capsys):
    # RK14 fixed the form of a report: the reader acts on the address, and it is the same
    # string `lint` will print for the same file a moment later. These were absolute.
    config = project(tmp_path)
    assert f"§RK1 in {IMPROVEMENTS} is pointed at" in refused(
        config, capsys, "section", "drop", "RK1"
    )


def test_a_claim_on_a_name_under_the_anchor_names_it_the_same_way(tmp_path, capsys):
    # `AnchorClaimed`, the widest of the four: measured while shipping RK169, where the
    # refusal ran past the terminal width on the path alone. `§RK1` itself is unclaimed
    # here, so the check that fires is the one reading the *name* and not the headings.
    config = project(tmp_path, roadmap=BACKLOG.replace(RK1_LINE, "").replace("§RK3", "§RK1.2"))
    assert f"§RK1 in {IMPROVEMENTS} is above" in refused(
        config, capsys, "section", "drop", "RK1"
    )


def test_an_anchor_the_file_does_not_declare_names_it_the_same_way(tmp_path, capsys):
    config = project(tmp_path)
    assert f"no §RK9 section in {IMPROVEMENTS}" in refused(
        config, capsys, "section", "drop", "RK9"
    )


def test_a_missing_parent_names_the_directory_it_is_in(tmp_path, capsys):
    # The other of the three spellings: `UnknownParent` and `UnknownBlock` were handed
    # `document.path.name`, which is not absolute and is not an address either — two files
    # of the same name in one project are named identically by it.
    config = project(tmp_path, top='ref_scheme = "outline"\n')
    assert f"({IMPROVEMENTS} declares:" in refused(
        config, capsys, "section", "add", "IX.4", "--title", "A design", "--body", "Prose."
    )


def test_an_undeclared_block_names_the_directory_it_is_in(tmp_path, capsys):
    config = project(tmp_path, improvements="# Improvements\n\n## Block A — The model\n")
    # The file is the address and not `document.path.name` — two files of one name in one
    # project are named identically by that. The labels it declares are not listed (RK296).
    assert f"Block B in {IMPROVEMENTS}:" in refused(
        config, capsys, "section", "add", "RK2", "--title", "A design", "--body", "Prose."
    )


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


#: The shape a project gets by nesting its rationale under a `##` part heading: the outline's
#: own top level is `###` and its designs are `####`. Nothing about it is exotic — it is
#: OUTLINE_RATIONALE one `#` deeper — and it is the file the fixed depth was wrong in.
DEEPER_RATIONALE = """# Improvements

## Part two — the designs

### XXI A theme

The part that is not numbered by anybody.

#### XXI.1 A first design

The reasoning the line has no room for.
"""


def deeper(tmp_path: Path) -> Config:
    return project(
        tmp_path,
        improvements=DEEPER_RATIONALE,
        top='ref_scheme = "outline"\n',
        roadmap=BACKLOG.replace("§RK1", "§XXI.1"),
    )


def test_a_subsection_takes_the_depth_of_the_section_it_extends(tmp_path):
    # RK180: the level was 3 flat, so here `XXI.6` was written as a *sibling* of `### XXI` —
    # which ends the subtree it was meant to be inside, nothing refusing it.
    config = deeper(tmp_path)
    document, section = add(config, "improvements", "XXI.6", "A sixth design", "Prose.")
    assert section.level == 4
    document.save()
    assert "#### XXI.6 A sixth design" in read(config)


def test_the_subsection_stays_inside_the_subtree_its_anchor_names(tmp_path):
    # The consequence, and the reason a depth is not cosmetic (RK115): depth is what says
    # where a section ends, so a sibling would leave `drop XXI` taking the parent alone.
    config = deeper(tmp_path)
    document, _ = add(config, "improvements", "XXI.6", "A sixth design", "Prose.")
    document.save()
    config = Config.discover(config.root)
    assert find(config.document("improvements"), "XXI").body.count("XXI.6") == 1


def test_a_subsection_in_a_shallower_file_is_written_exactly_where_it_was(tmp_path):
    # The other direction, which is what keeps this a fix rather than a move: in a file whose
    # top level is `##`, one under the parent is the 3 the constant always gave.
    config = outline(tmp_path)
    document, section = add(config, "improvements", "VIII.2", "A second design", "Prose.")
    assert section.level == 3
    document.save()
    assert "### VIII.2 A second design" in read(config)


def test_a_task_s_own_design_still_takes_the_nested_depth(tmp_path):
    # Under the id scheme a one-segment anchor is a task's design and has no parent by
    # construction — reading a depth off the file's other one-segment sections would find
    # this repository's own `§0` container and write every design a level too shallow.
    config = project(tmp_path)
    document, section = add(config, "improvements", "RK3", "A third design", "Prose.")
    assert section.level == 3
    document.save()
    assert "### §RK3 A third design" in read(config)


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
    # Bound to the line it was written for (RK262): the section a task ships is the one whose
    # heading names it, and this title was composed before the author could know the id.
    assert "### XXII.1 A design (CT1)" in prose


# -- a heading that binds to the line it was written for (RK262) ---------------


def test_a_section_written_for_a_task_names_it_even_when_the_title_does_not(tmp_path):
    # The defect: `add --section` derives the id, so a title composed by hand cannot carry
    # one — and the heading it wrote belonged to nobody from the moment it reached the file.
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
    assert insertion.section is not None
    assert insertion.section.title == f"A second design ({insertion.entry.task.id})"


def test_a_title_that_already_names_the_task_is_written_exactly_as_given(tmp_path):
    # An author who knows the id and typed it gets their sentence back, not a second copy
    # of the binding — `owners` is the reading, so what satisfies the gate satisfies this.
    from roadkeep.authoring import add as add_task

    config = outline(tmp_path)
    insertion = add_task(
        config,
        block="B",
        symptom="A fourth symptom",
        why="Because of a fourth reason.",
        ref="VIII.2",
        section=("A second design (RK4)", "The reasoning for it."),
    )
    assert insertion.entry.task.id == "RK4"
    assert insertion.section is not None
    assert insertion.section.title == "A second design (RK4)"


def test_a_section_belonging_to_no_task_keeps_the_title_it_was_given(tmp_path):
    # The standing memo the outline scheme exists for: no line points at §IX.5, so there is
    # no id to bind and appending one would invent an owner.
    config = outline(tmp_path)
    _, written = add(
        config, "improvements", "VIII.11", "A standing memo", "Prose belonging to no task."
    )
    assert written.title == "A standing memo"


def test_under_the_id_scheme_the_anchor_is_the_binding_and_nothing_is_appended(tmp_path):
    # `§RK1 A first design` already belongs to RK1 — the anchor says so — so a title that
    # repeated the id would be the tool writing what the format already states.
    from roadkeep.authoring import add as add_task

    config = project(tmp_path)
    insertion = add_task(
        config,
        block="A",
        symptom="A fourth symptom",
        why="Because of a fourth reason.",
        section=("A fourth design", "The reasoning for it."),
    )
    assert insertion.section is not None
    assert insertion.section.title == "A fourth design"


def test_an_amended_title_that_drops_the_id_gets_it_back(tmp_path):
    # `section amend --title` is the other door onto the same state: a correction to the
    # wording is not a decision to unbind the section from its line.
    config = outline(tmp_path)
    # RK1 points at §VIII.1 here, and the heading names SH75 — a prefix this project does
    # not use, so the section was already nobody's under its own schema.
    _, amended, _ = amend(
        config, "improvements", "VIII.1", title="MCP server host, rewritten"
    )
    assert amended.title == "MCP server host, rewritten (RK1)"


def test_an_amended_body_leaves_a_heading_that_names_no_task_alone(tmp_path):
    # Correcting a paragraph is not the call in which a heading silently changes, and the
    # file this arrives on is one no write of this tool's created.
    config = outline(tmp_path)
    before = find(config.document("improvements"), "IX.4.d")
    _, amended, _ = amend(config, "improvements", "IX.4.d", body="A corrected paragraph.")
    assert amended.title == before.title


def test_an_anchor_two_lines_point_at_binds_to_neither(tmp_path):
    # RK64's rule, read here: four of Shio's lines point at one epic design, and a writer
    # that picked one of them would answer by guessing a question the format leaves open.
    config = project(
        tmp_path,
        improvements=OUTLINE_RATIONALE,
        top='ref_scheme = "outline"\n',
        roadmap=BACKLOG.replace("§RK1", "§VIII.10")
        .replace("§RK2", "§XIV.8.7")
        .replace("§RK3", "§VIII.10"),
    )
    _, amended, _ = amend(
        config, "improvements", "VIII.10", title="Batch and apply, rewritten"
    )
    assert amended.title == "Batch and apply, rewritten"


def test_the_section_a_bound_heading_owns_is_the_one_its_ship_deletes(tmp_path):
    # The whole finding, end to end: before this, `ship` reported the section *kept* as prose
    # belonging to none, and the rationale for shipped work stayed in the prose file.
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "CT"\nref_scheme = "outline"\n[files]\n'
        'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
        'improvements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    for name, body in {
        "ROADMAP.md": "# Roadmap\n\n## Block A — Themes\n",
        "CHANGELOG.md": "# Shipped\n\n## Block A — Themes\n",
        "IMPROVEMENTS.md": "# Rationale\n\n## XXI A theme\n\nProse.\n",
    }.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)

    at = ["-C", str(tmp_path)]
    assert main([*at, "add", "--block", "A", "--ref", "XXI.1", "--symptom", "A symptom",
                 "--why", "Because of a reason.", "--section", "A design",
                 "--section-body", "The reasoning."]) == EXIT_OK
    assert main([*at, "ship", "CT1", "--why", "Because it works."]) == EXIT_OK

    prose = (tmp_path / "IMPROVEMENTS.md").read_text(encoding="utf-8")
    assert "XXI.1" not in prose  # deleted, not "kept as prose belonging to none"
    assert "CT1" in (tmp_path / "CHANGELOG.md").read_text(encoding="utf-8")
    assert main([*at, "lint"]) == EXIT_OK


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
    document, section, _ = drop(
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
    document, section, _ = drop(
        config.document("improvements"), "XIV", claimed=pointers(config, leaving="RK373")
    )
    document.save()
    assert section.anchor == "XIV" and read(config) == "# Turing — Design rationale\n"


# -- the pointer read from the other end (RK206) ------------------------------


CITING = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.

#### §RK1.1 A subsection

Which belongs to the section above.

### §RK3 A third design

This extends §RK1, and the argument in §RK1.1 is why.

## Block B — Authoring

### §RK2 A second design

`§RK1` is what this quotes, and → §RK1 is how the line spells it.

> Somebody else's mail said §RK1 was wrong.

```
a fence naming §RK1
```
"""


def shippable(tmp_path: Path, improvements: str) -> Config:
    """The same project with a ledger, so a departure has somewhere to file its entry."""
    project(
        tmp_path,
        improvements=improvements,
        extra='changelog = "docs/CHANGELOG.md"\n',
    )
    ledger = "# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n"
    with (tmp_path / "docs" / "CHANGELOG.md").open(
        "w", encoding="utf-8", newline=""
    ) as handle:
        handle.write(ledger)
    return Config.discover(tmp_path)


def test_the_sections_citing_a_dropped_anchor_are_named(tmp_path, capsys):
    """The other end of the pointer, and the one nothing read (RK206).

    `ref.unresolved` resolves the ref a task line carries, `section.orphan` reads what
    points at a section, and a design citing another design is neither — so `ship` deleted
    §XVIII.12 out of claude-tray and `lint` answered `clean` for a day.
    """
    shippable(tmp_path, CITING)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    out = capsys.readouterr().out
    assert "cited    §RK3 cites it in prose — now resolving to nothing" in out
    # The subtree went too, so a citation of §RK1.1 is the same dangling reference.
    assert "nested   §RK1.1 went with it" in out


def test_a_quotation_is_not_a_citation(tmp_path, capsys):
    """The three exclusions, each measured rather than guessed.

    §RK2 names §RK1 four times — in a code span, after a `→` that reproduces a task line,
    inside a blockquote and inside a fence — and none of them is a reference this drop
    breaks. A false positive here fails a file whose prose is correct, which is the one
    thing a gate over prose cannot afford; the same reasoning §RK15 made about scanning a
    raw task line, one file down.
    """
    shippable(tmp_path, CITING)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    cited = [line for line in capsys.readouterr().out.splitlines() if "cited" in line]
    assert cited and "RK2" not in cited[0]


def test_a_ship_with_nobody_citing_it_says_nothing(tmp_path, capsys):
    """Silence is the common case, so it has to stay silent: a line per ship about nobody
    is the noise that makes the line about somebody unread."""
    shippable(tmp_path, RATIONALE)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    assert "cited" not in capsys.readouterr().out


def test_the_citation_is_reported_and_never_refused(tmp_path):
    """The ship is correct — the design shipped and its section is supposed to go — so the
    citing prose is the author's next edit and not a reason to refuse a right transaction.
    `section drop`'s refusals (RK78, RK112) are the other case: there an *open line* points
    at the anchor, which is a pointer the format promises resolves."""
    config = shippable(tmp_path, CITING)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    assert find(config.document("improvements"), "RK1") is None
    assert "RK1" in config.document("changelog").by_id()


def test_the_json_carries_the_same_list(tmp_path, capsys):
    shippable(tmp_path, CITING)
    main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now.", "--json"])
    payload = json.loads(capsys.readouterr().out)
    assert payload["improvements"]["cited"] == ["RK3"]


@pytest.mark.parametrize("corpus", corpora.BOTH, ids=lambda c: c.name)
def test_a_live_corpus_carries_cross_references_a_ship_would_break(corpus):
    """The exposure, counted at the pin: this is not a defect one project happened to hit.

    Read over every declared anchor at once, so the number is "how many citations exist"
    rather than "how many a particular ship breaks" — which is what makes it a floor. It
    also fixes the shape of the answer: these resolve today, so nothing here is a finding
    and none of these files is failing anything.
    """
    corpora.require(corpus)
    settings = corpora.config(corpus)
    found = []
    for role in ("improvements", "strategy"):
        if not corpora.has(corpus, role):
            continue
        document = settings.document(role)
        found += list(citing(document, [s.anchor for s in anchored(document)]))
    assert found
    for cited, by in found:
        assert cited and by and cited != by or cited == by


# -- the third door says it too (RK209) ---------------------------------------


#: A section no task line owns — so `section drop` is not refused — that another design
#: cites, plus the four quotations of it that are not citations.
DROPPABLE = """# Improvements

## §0 — Why this exists

### §0.2 A shared reading

The argument two designs lean on.

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.

#### §RK1.1 A subsection

Which belongs to the section above.

### §RK3 A third design

This extends §0.2, and the argument in §0.2.1 is why.

## Block B — Authoring

### §RK2 A second design

`§0.2` is what this quotes, and → §0.2 is how the line spells it.

> Somebody else's mail said §0.2 was wrong.

```
a fence naming §0.2
```
"""


def test_section_drop_names_who_was_left_citing_it(tmp_path, capsys):
    """The door RK206 did not reach, and the one an author reaches for on purpose.

    `ship` and `retire` go through `_drop_section` and named it; the verb whose whole job is
    deleting a section inherited nothing — the same shape RK112 already fixed once here, one
    end of the reference along.
    """
    project(tmp_path, improvements=DROPPABLE)
    assert main(["-C", str(tmp_path), "section", "drop", "0.2"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "cited    §RK3 cites it in prose — now resolving to nothing" in out
    assert "§RK2" not in out  # its four mentions are quotations, not citations


def test_the_answer_is_the_deletion_s_own_and_not_a_second_reading(tmp_path):
    """One statement of the question (§RK209's first option), which is why it is a return
    value: what a deletion breaks is a fact about this file's grammar — the same argument
    that puts `drop` in this module rather than in `shipping` — so both callers are handed
    it instead of each asking the file again."""
    config = project(tmp_path, improvements=DROPPABLE)
    document = config.document("improvements")
    _, section, cited = drop(document, "0.2", where=IMPROVEMENTS)
    assert section.anchor == "0.2" and cited == ("RK3",)
    # Computed before the removal: afterwards the prose is the only end still in the file.
    assert find(document, "0.2") is not None


def test_a_pointer_still_refuses_where_a_citation_only_reports(tmp_path, capsys):
    """The line between the two, said in one test.

    A pointer is a promise the format makes — a line spells `→ §<anchor>` and the anchor has
    to be there — so `SectionClaimed` refuses and writes nothing (RK112). A citation is a
    sentence, and a sentence that needs re-wording is an edit rather than a transaction to
    abandon. Same file, same deletion, two answers on purpose.
    """
    config = project(tmp_path, improvements=DROPPABLE)
    before = read(config)
    # RK3's own line points at §RK3, so dropping that section is the refusal.
    assert main(["-C", str(tmp_path), "section", "drop", "RK3"]) == EXIT_USAGE
    assert "pointed at by RK3" in capsys.readouterr().err
    assert read(config) == before
    # §0.2 is nobody's pointer and somebody's citation, so it goes and is reported.
    assert main(["-C", str(tmp_path), "section", "drop", "0.2"]) == EXIT_OK
    assert "cited" in capsys.readouterr().out


def test_the_json_form_carries_it_too(tmp_path, capsys):
    project(tmp_path, improvements=DROPPABLE)
    main(["-C", str(tmp_path), "section", "drop", "0.2", "--json"])
    assert json.loads(capsys.readouterr().out)["cited"] == ["RK3"]


# -- two numbers, one of them printed (RK287) ---------------------------------


def test_a_section_carries_both_its_own_count_and_its_subtrees(tmp_path):
    # The defect: `310 words` on a section whose own prose is 48 invites cutting prose that
    # was never over. Both are wanted — the subtree is what a reader pays, the argument is
    # what an amend can shorten — so both are carried and neither is the only one.
    config = project(tmp_path)
    section = find(config.document("improvements"), "RK1")
    assert section.words == 18 and section.own_words < section.words
    assert section.own_words == len("The reasoning the line has no room for.".split())
    assert section.nests


def test_a_leaf_says_the_same_number_twice_and_never_claims_two(tmp_path):
    # Where there is nothing nested, there is one number — and a printer that always said
    # "N words, N with subsections" would be noise on the common case.
    leaf = find(project(tmp_path).document("improvements"), "0.1")
    assert leaf.own_words == leaf.words and not leaf.nests


def test_a_container_with_no_prose_of_its_own_is_charged_none_of_its_children(tmp_path):
    # `§0` here is this repository's own shape: a heading that holds sections and no
    # paragraph. Counting its children against it measures the file, not anyone's argument.
    section = find(project(tmp_path).document("improvements"), "0")
    assert section.own_words == 0 and section.words > 0 and section.nests


def test_the_own_count_agrees_with_the_reading_the_gate_uses(tmp_path):
    # `anchored` already carried own prose and `find` carried the subtree, which is the split
    # that let two readers of one file disagree. They are one number now.
    document = project(tmp_path).document("improvements")
    by_anchor = {section.anchor: section for section in anchored(document)}
    for anchor, own in by_anchor.items():
        assert find(document, anchor).own_words == own.words


def test_the_verbs_that_print_a_count_print_the_limit_beside_it(tmp_path, capsys):
    # The rule underneath: a verb printing a number beside a limit is claiming the two are
    # the same number. Here the limit is stated, so the figure acts on something.
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "section", "amend", "RK1", "--body", "Rewritten."]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "with subsections" in printed and f"limit {config.schema.section_max}" in printed


def test_a_leaf_prints_one_figure_rather_than_the_same_one_twice(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "section", "amend", "0.1", "--body", "Rewritten."]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "with subsections" not in printed and f"limit {config.schema.section_max}" in printed


def test_the_json_carries_both_counts_so_a_client_never_has_to_choose(tmp_path, capsys):
    project(tmp_path)
    assert main(
        ["-C", str(tmp_path), "section", "amend", "RK1", "--body", "Rewritten.", "--json"]
    ) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["own_words"] < payload["words"]


def test_show_states_the_same_pair_as_the_section_verbs(tmp_path, capsys):
    # `show` and `brief` are what start a task, so a figure they state wrongly is the one
    # an author acts on first.
    config = project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK1", "--no-body"]) == EXIT_OK
    printed = capsys.readouterr().out
    assert "with subsections" in printed and f"limit {config.schema.section_max}" in printed


def test_the_limit_printed_is_the_roles_own_and_not_the_projects(tmp_path, capsys):
    # `[limits.improvements]` is the same declaration `[limits.changelog]` is (RK50), so a
    # printer reading the project's number would state one this file is not held to.
    config = project(tmp_path, extra="\n[limits.improvements]\nsection = 7\n")
    assert config.schema_for("improvements").section_max == 7
    assert main(["-C", str(tmp_path), "show", "RK1", "--no-body"]) == EXIT_OK
    assert "limit 7" in capsys.readouterr().out


# -- where the words are, on the refusal that discards them (RK311) -----------


def test_the_refusal_says_which_paragraph_the_cut_is_available_in(tmp_path):
    # Fifteen `body.too-long` refusals in one session, three of them over one or two words.
    # The overage says a cut is needed; without this the author counts by hand for somewhere
    # to make it, against a number this module has already computed exactly.
    config = project(tmp_path, extra="[limits]\nsection = 10\n")
    body = "one two three\n\n" + "word " * 8 + "\n\nlast bit here"
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK2", "A design", body)

    message = raised.value.violations[0].message
    assert "by paragraph ¶1 3, ¶2 8, ¶3 3" in message
    assert "¶2 is the longest" in message
    assert read(config) == RATIONALE


def test_a_body_of_one_paragraph_is_not_told_its_own_total_twice(tmp_path):
    # "¶1 335" restates the number the same sentence just gave, and a refusal that repeats
    # itself is one an author stops reading.
    config = project(tmp_path, extra="[limits]\nsection = 10\n")
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK2", "A design", "word " * 11)

    assert "by paragraph" not in raised.value.violations[0].message


def test_a_paragraph_the_limit_does_not_charge_is_reported_as_nothing_to_cut(tmp_path):
    # The other half of the question. A section over the limit whose longest paragraph is a
    # table is not one to split, and the `0` says so — the same reading `words` already makes
    # for the three shapes that are data rather than argument (RK136).
    config = project(tmp_path, extra="[limits]\nsection = 10\n")
    body = "| a | b |\n| - | - |\n| 1 | 2 |\n\n" + "word " * 11
    with pytest.raises(SchemaError) as raised:
        add(config, "improvements", "RK2", "A design", body)

    assert "by paragraph ¶1 0, ¶2 11" in raised.value.violations[0].message


def test_a_fenced_block_is_one_paragraph_however_many_blanks_are_inside_it(tmp_path):
    # A fence opens inside whatever paragraph is being read, and the blank lines in the block
    # are not paragraph breaks — a count that split there would number paragraphs the author
    # cannot see.
    body = "Intro line.\n```\ncode\n\nmore code\n```\n\nA second paragraph of four words."
    assert paragraphs(body) == (2, 6)


def test_the_counts_add_up_to_the_number_the_limit_charges():
    # One reading, not two: a breakdown that did not sum to the total would send the author
    # cutting in a paragraph the limit was never charging them for.
    body = (
        "A first paragraph here.\n\n> a quotation nobody is charged for\n\n"
        "| a | b |\n\nA third paragraph with several words in it.\n\n```\nfenced\n```"
    )
    assert sum(paragraphs(body)) == words(body)


# -- moving an address (RK377) -----------------------------------------------

#: Two prose files whose outlines collide, which is the state Turing adopted the tool in:
#: 13 addresses declared by both, `lint` reporting `section.ambiguous` at every one of them,
#: and no verb that changes a section's address. The roadmap points into the file that names
#: its task in the heading, which is what `owners` reads and what decides the pointer below.
DOUBLED_BACKLOG = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §I.2

- 📋 **RK2** (deps: —) **A second symptom** — Because of another reason. → §I.2.1
"""

DOUBLED_IMPROVEMENTS = """# Improvements

## I The first family

Prose that is not numbered by anybody.

### I.1 An earlier design

The reasoning the line has no room for.

### I.2 A doubled design (RK1)

The reasoning the other file also claims.

#### I.2.1 A subsection (RK2)

Which belongs to the section above.

### I.9 A later design

This one names §I.2 in its own prose.
"""

DOUBLED_STRATEGY = """# Strategy

## I The first family

A second file that numbered its own outline from the same place.

### I.2 The other one at this address

The collision the corpus arrived with.
"""


def doubled(tmp_path: Path, *, refs: str = "") -> Config:
    """An outline project whose two prose files both declare `§I` and `§I.2`."""
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\nref_scheme = "outline"\n{refs}[files]\n'
        f'roadmap = "{ROADMAP}"\nimprovements = "{IMPROVEMENTS}"\nstrategy = "{STRATEGY}"\n',
        encoding="utf-8",
    )
    for name, body in {
        ROADMAP: DOUBLED_BACKLOG,
        IMPROVEMENTS: DOUBLED_IMPROVEMENTS,
        STRATEGY: DOUBLED_STRATEGY,
    }.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def test_the_doubled_address_the_gate_reports_now_has_a_verb(tmp_path):
    # The whole task in one assertion. `lint` named this state on every run and the write path
    # refuses to create it, and between the two there was nothing to call: `renumber` moves an
    # id and keeps the pointer as typed under any scheme but `id`, `section amend` says the
    # anchor is not one of its fields, and `drop` is refused while a line points at it.
    config = doubled(tmp_path)
    assert "section.ambiguous" in {f.code for f in lint(config).findings}

    move(config, "strategy", "I.2", "I.10").save()
    move(Config.discover(tmp_path), "strategy", "I", "II").save()

    assert [f.code for f in lint(Config.discover(tmp_path)).findings] == []


def test_the_pointer_stays_with_the_file_whose_heading_names_the_task(tmp_path):
    # The half that must not be a guess. Both files declared §I.2 and RK1 pointed at it; the
    # repair moves the copy in `strategy`, whose heading names nobody, so following the move
    # would take RK1 away from the design that is actually its own — the state `lint` then
    # reports as `section.unreachable`, one defect traded for another.
    config = doubled(tmp_path)
    moved = move(config, "strategy", "I.2", "I.10")
    moved.save()

    assert moved.repointed == ()
    assert moved.kept == (("RK1", "I.2"),)
    assert "Because of a reason. → §I.2" in read(Config.discover(tmp_path), ROADMAP)


def test_a_pointer_nothing_else_answers_follows_the_heading(tmp_path):
    # The ordinary re-address, and the reason the rule above is two clauses rather than one:
    # here nothing else declares §I.2, so a pointer left behind resolves to nothing — which is
    # the dangling reference this module refuses a file over.
    config = doubled(tmp_path)
    move(config, "strategy", "I.2", "I.10").save()  # the doubling out of the way first
    moved = move(Config.discover(tmp_path), "improvements", "I.2", "I.11")
    moved.save()

    # Each to its **own** address: the subsection's pointer follows to §I.11.1 and not to the
    # address this call was about, which is what a report checked against the file needs.
    assert moved.repointed == (("RK1", "I.11"), ("RK2", "I.11.1"))
    assert "ref.unresolved" not in {f.code for f in lint(Config.discover(tmp_path)).findings}


def test_the_subtree_moves_with_the_address_and_a_stranger_does_not(tmp_path):
    # RK113's rule at the other end: a half-renamed subtree leaves a §I.2.1 claiming an
    # address the file no longer has, under a heading naming §I.11 — and the gate calls it
    # clean. Segment by segment, so `descending` is the one reader of "whose numbering is this".
    config = doubled(tmp_path)
    moved = move(config, "improvements", "I.2", "I.11")
    moved.save()

    assert moved.subsections == (("I.2.1", "I.11.1"),)
    body = read(Config.discover(tmp_path))
    assert "#### I.11.1 A subsection (RK2)" in body
    # The sibling at §I.1 is not `I.2`'s numbering and stays exactly where it was.
    assert "### I.1 An earlier design" in body


def test_the_prose_that_still_cites_the_old_address_is_named(tmp_path):
    # Reported and never rewritten, for the reason `drop` reports the same thing (RK206): a
    # pointer is a promise the format makes and a citation is a sentence, which is the author's.
    config = doubled(tmp_path)
    moved = move(config, "improvements", "I.2", "I.11")

    assert moved.cited == (("I.2", "I.9"),)
    assert "names §I.2 in its own prose" in read(config)


def test_a_destination_under_another_parent_is_refused(tmp_path):
    # The bound that keeps the verb honest: this write changes the address and moves no prose,
    # so a §XIV.5 re-addressed in place still sits inside §I's subtree — where `_span` ends it
    # and the next `drop I` takes it, with nothing in the file saying so.
    config = doubled(tmp_path)
    with pytest.raises(NotASibling) as raised:
        move(config, "improvements", "I.2", "XIV.5")

    assert raised.value.parent == "I"
    assert "name an address under §I" in str(raised.value)
    assert read(config) == DOUBLED_IMPROVEMENTS


def test_a_destination_the_sibling_file_declares_is_refused(tmp_path):
    # The refusal `add` computes about a destination, asked by this verb too (RK302): a repair
    # that could land on the address the other file holds would recreate the doubling it was
    # called to remove.
    config = doubled(tmp_path)
    with pytest.raises(SectionExists) as raised:
        move(config, "improvements", "I.1", "I.2")

    assert raised.value.anchor == "I.2"


def test_a_subsection_s_derived_destination_is_asked_too(tmp_path):
    # Every **new** address and not only the named one: a subsection's is derived from its
    # parent's, so a collision one segment down is a collision this transaction would write.
    doubled(tmp_path)
    (tmp_path / STRATEGY).write_text(
        DOUBLED_STRATEGY.replace("### I.2 The other one", "### I.11.1 The other one"),
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    with pytest.raises(SectionExists) as raised:
        move(config, "improvements", "I.2", "I.11")

    assert raised.value.anchor == "I.11.1" and raised.value.elsewhere


def test_moving_to_the_address_it_already_has_is_refused(tmp_path):
    # `renumber`'s argument one file over: the write would rewrite the file to the bytes it
    # already holds, and an untouched file with a moved mtime reads as an edit.
    config = doubled(tmp_path)
    with pytest.raises(SameAnchor):
        move(config, "improvements", "I.2", "I.2")


def test_an_address_that_is_not_one_is_refused_before_anything_moves(tmp_path):
    config = doubled(tmp_path)
    with pytest.raises(SectionError) as raised:
        move(config, "improvements", "I.2", "§I.11")

    assert [v.code for v in raised.value.violations] == ["anchor.sigil"]


def test_the_id_scheme_sends_the_caller_to_the_verb_that_moves_both_ends(tmp_path):
    # The one scheme this verb has nothing to do: there the anchor *is* the id, so a section
    # re-addressed alone is one its own task no longer points at — and moving both is
    # `renumber`, in one transaction with every dep.
    config = project(tmp_path)
    with pytest.raises(AnchorIsId) as raised:
        move(config, "improvements", "RK1", "RK9")

    assert "`renumber RK1 --to <id>`" in str(raised.value)
    assert "`section drop`" in str(raised.value)
    assert read(config) == RATIONALE


def test_a_namespaced_role_is_moved_by_the_address_it_answers(tmp_path):
    # The prefix is part of the address and not a spelling (RK340): the role answers only its
    # own, and the heading keeps writing the bare number because the file is the answer to
    # "which file".
    config = doubled(tmp_path, refs='[refs]\nstrategy = "S"\n')
    with pytest.raises(NoSuchSection):
        move(config, "strategy", "I.2", "I.10")

    move(config, "strategy", "S:I.2", "S:I.10").save()
    assert "### I.10 The other one at this address" in read(Config.discover(tmp_path), STRATEGY)


def test_a_destination_in_another_file_s_namespace_is_refused(tmp_path):
    config = doubled(tmp_path, refs='[refs]\nstrategy = "S"\n')
    with pytest.raises(SectionError) as raised:
        move(config, "strategy", "S:I.2", "I.10")

    assert [v.code for v in raised.value.violations] == ["anchor.namespace"]


def test_a_paused_line_s_pointer_moves_with_the_heading(tmp_path):
    # The deferred store is a pointing file too (RK96): pausing a line keeps its section, so
    # its pointer is as live as the roadmap's and the gate reads both.
    doubled(tmp_path)
    with (tmp_path / "roadkeep.toml").open("a", encoding="utf-8") as handle:
        handle.write('deferred = "docs/DEFERRED.md"\n')
    (tmp_path / "docs" / "DEFERRED.md").write_text(
        "# Deferred\n\n## Block A — The model\n\n"
        "- ⏸ **RK3** (deps: —) **A paused symptom** — Paused: because of a reason. → §I.1\n",
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)

    moved = move(config, "improvements", "I.1", "I.10")
    moved.save()

    assert moved.repointed == (("RK3", "I.10"),)
    assert "→ §I.10" in read(Config.discover(tmp_path), "docs/DEFERRED.md")


def test_the_command_reports_every_end_of_the_move(tmp_path, capsys):
    config = doubled(tmp_path)
    assert main(["-C", str(config.root), "section", "move", "I.2", "--to", "I.11"]) == EXIT_OK

    out = capsys.readouterr().out
    assert "§I.2 → §I.11" in out
    assert "nested   §I.2.1 → §I.11.1" in out
    assert "pointer  RK2 follows it to §I.11.1" in out
    assert "cited    §I.9 names §I.2 in its prose" in out


def test_the_command_answers_in_json_too(tmp_path, capsys):
    config = doubled(tmp_path)
    argv = ["-C", str(config.root), "section", "move", "I.2", "--to", "I.10"]
    assert main([*argv, "--role", "strategy", "--json"]) == EXIT_OK

    answer = json.loads(capsys.readouterr().out)
    assert (answer["from"], answer["anchor"]) == ("I.2", "I.10")
    assert answer["kept"] == [{"id": "RK1", "address": "I.2"}]


def test_a_refusal_writes_nothing_and_exits_two(tmp_path, capsys):
    config = doubled(tmp_path)
    argv = ["-C", str(config.root), "section", "move", "I.2", "--to", "XIV.5"]
    assert main(argv) == EXIT_USAGE

    assert read(config) == DOUBLED_IMPROVEMENTS


# -- the paragraph named by path (RK381) --------------------------------------


class _Unread:
    """A pipe that fails the test if anything drains it — see the same class one file over."""

    def read(self) -> str:
        raise AssertionError("a body named by path must not reach the pipe (RK381)")


def test_a_section_body_can_be_named_by_path(tmp_path, capsys, monkeypatch):
    # The affordance is the retry: `anchor.unknown` and every title rule are checked with the
    # body, so a refusal on either spends a paragraph the pipe cannot hand over twice.
    config = project(tmp_path)
    body = tmp_path / "body.md"
    body.write_text("The reasoning, drafted before it was filed.\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", _Unread())

    argv = ["-C", str(tmp_path), "section", "add", "--title", "A design", "--body-file", str(body)]
    assert main([*argv, "RK99"]) == EXIT_USAGE
    capsys.readouterr()

    assert main([*argv, "RK2"]) == EXIT_OK
    assert "The reasoning, drafted before it was filed." in read(config)


def test_an_amend_can_name_the_replacement_by_path(tmp_path, capsys, monkeypatch):
    config = project(tmp_path)
    body = tmp_path / "body.md"
    body.write_text("The corrected reasoning, from a file.\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", _Unread())

    argv = ["-C", str(tmp_path), "section", "amend", "RK1", "--body-file", str(body)]
    assert main(argv) == EXIT_OK
    assert "(body)" in capsys.readouterr().out
    assert "The corrected reasoning, from a file." in read(config)


def test_an_amend_naming_the_prose_twice_is_refused(tmp_path, capsys):
    config = project(tmp_path)
    argv = ["-C", str(config.root), "section", "amend", "RK1", "--body", "x", "--body-file", "y"]
    assert main(argv) == EXIT_USAGE

    assert "two answers to one question" in capsys.readouterr().err
    assert read(config) == RATIONALE


def test_the_dash_on_the_path_flag_is_refused_by_name(tmp_path, capsys, monkeypatch):
    # RK406, measured filing a task in this repository: it opened a file called `-` and
    # answered `[Errno 2] No such file or directory`, from a door whose body already comes
    # from stdin. The pipe is not opened either — the refusal is about argv.
    config = project(tmp_path)
    monkeypatch.setattr("sys.stdin", _Unread())
    argv = ["-C", str(config.root), "section", "amend", "RK1", "--body-file", "-"]
    assert main(argv) == EXIT_USAGE

    error = capsys.readouterr().err
    assert "already comes from stdin unless a path is given" in error
    # And the spelling that does mean stdin, so the refusal is not a dead end.
    assert "--body -" in error
    assert read(config) == RATIONALE


def test_a_title_only_amend_still_never_opens_the_pipe(tmp_path, capsys, monkeypatch):
    # The third source must not become a fourth default: `--body-file` absent leaves a
    # title-only amend exactly as it was, which is the prose untouched and no pipe opened.
    config = project(tmp_path)
    monkeypatch.setattr("sys.stdin", _Unread())
    argv = ["-C", str(tmp_path), "section", "amend", "RK1", "--title", "A better name"]

    assert main(argv) == EXIT_OK
    assert "(title)" in capsys.readouterr().out
    assert "The reasoning the line has no room for." in read(config)


def test_an_amend_with_none_of_the_three_names_all_three(tmp_path, capsys):
    config = project(tmp_path)
    assert main(["-C", str(config.root), "section", "amend", "RK1"]) == EXIT_USAGE

    assert "--body-file" in capsys.readouterr().err


# -- the heading nobody named (RK388) -----------------------------------------

#: An outline file whose headings carry a sigil the reader accepts and the writer would not
#: reproduce (RK44), plus one with spacing nobody would write twice. Both parse; neither is
#: what `anchor_text` renders, which is the whole of the defect.
SIGILLED = """# Improvements

## §I The first family

Prose that is not numbered by anybody.

### §I.1  A design

The reasoning the line has no room for.
"""


def sigilled(tmp_path: Path) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\nref_scheme = "outline"\n[files]\n'
        f'roadmap = "{ROADMAP}"\nimprovements = "{IMPROVEMENTS}"\n',
        encoding="utf-8",
    )
    for name, body in {ROADMAP: "# Roadmap\n\n## Block A — The model\n", IMPROVEMENTS: SIGILLED}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def test_a_body_amend_leaves_the_heading_byte_identical(tmp_path):
    # The measured defect: `--body` re-rendered the heading above the prose it was passed, so
    # a file that opened with `§` lost it on the first write to any section in it — and `lint`
    # called the result clean, L3 being held over task lines and a prose file having none.
    config = sigilled(tmp_path)
    document, section, changed = amend(
        config, "improvements", "I.1", body="The corrected reasoning."
    )
    document.save()

    assert changed == ("body",)
    written = read(Config.discover(tmp_path))
    assert "### §I.1  A design" in written
    assert "The corrected reasoning." in written


def test_the_sibling_headings_are_untouched_too(tmp_path):
    config = sigilled(tmp_path)
    document, _, _ = amend(config, "improvements", "I.1", body="The corrected reasoning.")
    document.save()

    assert "## §I The first family" in read(Config.discover(tmp_path))


def test_a_title_amend_is_the_caller_asking_for_the_heading_to_change(tmp_path):
    # The other half, and why this is a fourth answer rather than a refusal: passing `--title`
    # *is* the request to rewrite that line, so there the canonical spelling is right.
    config = sigilled(tmp_path)
    document, section, changed = amend(config, "improvements", "I.1", title="A better name")
    document.save()

    assert changed == ("title",)
    written = read(Config.discover(tmp_path))
    assert "### I.1 A better name" in written
    assert "§I.1" not in written


def test_the_prose_under_an_untouched_heading_is_still_reflowed(tmp_path):
    # Not touching the heading is not leaving the section alone: the body is filled to the
    # declared width exactly as before, which is the half `--body` was passed for.
    config = sigilled(tmp_path)
    document, _, _ = amend(
        config, "improvements", "I.1", body="one two three four five six seven " * 6
    )
    document.save()

    written = read(Config.discover(tmp_path)).splitlines()
    filled = [line for line in written if line.startswith("one two")]
    assert filled and all(len(line) <= 88 for line in filled)


def test_the_id_scheme_keeps_its_heading_too(tmp_path):
    # The sigil is required under `id`, so the canonical form and the file already agree —
    # what this holds is that the *rule* is the same one, not a branch on the scheme.
    config = project(tmp_path)
    document, _, changed = amend(config, "improvements", "RK1", body="The corrected reasoning.")
    document.save()

    assert changed == ("body",)
    assert "### §RK1 A first design" in read(Config.discover(tmp_path))


# -- a marker is the character and the space after it (RK397) -----------------


def test_a_paragraph_that_breaks_before_a_bold_span_is_still_prose(tmp_path):
    # The measured defect, found writing §RK385: one line of an ordinary paragraph happened to
    # begin `**does not separate them**`, `*` is a bullet character, and the whole paragraph was
    # inserted verbatim — the author's incidental breaks kept, none of them filled.
    config = project(tmp_path)
    body = (
        "A first line of an ordinary paragraph.\n"
        "**does not separate them** is how the second one opens, and it is not a list."
    )
    document, section = add(config, "improvements", "RK2", "A design", body)
    document.save()

    written = read(Config.discover(tmp_path))
    assert "A first line of an ordinary paragraph. **does not separate them** is how the" in written


def test_every_marker_still_reads_as_the_shape_it_is(tmp_path):
    # The rule is the space, not a shorter alphabet: each of these is a structure and each is
    # inserted exactly as written, which is what `_reflow` has always promised (L4).
    assert structural(["- one", "- two"])
    assert structural(["* one"]) and structural(["+ one"])
    assert structural(["1. one"]) and structural(["1) one"])
    assert structural(["### A heading inside a body"])
    # No space is required of these three, `|a|b|` and `>quoted` both being legal.
    assert structural(["|a|b|"]) and structural([">quoted"]) and structural(["```"])
    # A run of three is a thematic break, which is the same prefix with the opposite reading.
    assert structural(["---"]) and structural(["***"]) and structural(["___"])
    assert structural(["    indented code"])


def test_what_is_no_longer_read_as_a_marker(tmp_path):
    assert not structural(["**bold** opens this line."])
    assert not structural(["*emphasis* opens this one."])
    # `1.5 seconds` fell to the `1.` prefix for the same reason, and is a sentence.
    assert not structural(["1.5 seconds is the budget this line is about."])
    assert not structural(["A sentence carrying **bold** and *emphasis* mid-line."])


def test_the_estimate_measures_the_width_the_writer_would_fill(tmp_path):
    # One predicate on purpose (RK99): `adopt --sections` reads the width a file is already
    # wrapped to over the paragraphs `_reflow` would touch, so a corpus with bold-led lines
    # used to report a width nobody wrote. The two readers move together or not at all.
    from roadkeep.sections import _shape

    assert _shape("- a bullet") and not _shape("**not a bullet**")


# -- an id in a design is a citation, never a promise (RK1002) ----------------


def test_a_design_naming_an_id_no_line_carries_is_refused(tmp_path):
    """RK1002. §RK498 was composed with an unclaimed id in it as an example, `section add`
    validated the body and said nothing, and the next task filed was RK1000 — the cost
    arriving two sessions later inside another command's output, as a warning nobody has to
    act on and which the gate has no code for."""
    config = project(tmp_path)
    with pytest.raises(SectionError) as refused:
        add(
            config,
            "improvements",
            "RK3",
            "A design",
            "A paragraph naming RK999 as an example of the shape.",
        )
    (violation,) = [one for one in refused.value.violations if one.code == "body.promise"]
    assert "names RK999" in violation.message
    # Both ways out, because which one is meant is the author's to know (L4).
    assert "spell the example outside RK" in violation.message
    assert "name the id actually meant" in violation.message


def test_an_example_outside_this_project_s_prefix_is_prose_and_not_an_address(tmp_path):
    # The door the refusal names: an id-shaped token nothing here numbers cannot be spent,
    # so it costs no address and reads as the illustration it is.
    config = project(tmp_path)
    _, section = add(
        config,
        "improvements",
        "RK3",
        "A design",
        "A paragraph naming XX999 as an example of the shape.",
    )
    assert "XX999" in section.body


def test_a_design_may_name_any_task_a_file_carries_as_a_line(tmp_path):
    """A rationale cites the work it builds on, and `carried` reads every role that holds an
    id as a line rather than the roadmap alone — so a shipped dep, a paused one and the task
    across the block are all citations and none of them is a promise."""
    config = project(tmp_path)
    _, section = add(
        config,
        "improvements",
        "RK3",
        "A design",
        "A paragraph about RK3 itself, building on RK1 and beside RK2.",
    )
    assert "RK1" in section.body and "RK2" in section.body


def test_the_gate_reports_a_design_a_hand_edit_gave_an_unclaimed_id(tmp_path):
    """RK1003, and :func:`~roadkeep.linting._query`'s shape: `section add` refuses the body
    and this reads what is already on disk. The three ways one gets there without passing a
    door are the three a backstop exists for — an adopted backlog, a hand edit, a merge."""
    from roadkeep.linting import lint

    config = project(
        tmp_path,
        improvements=RATIONALE.replace(
            "The reasoning the line has no room for.",
            "The reasoning the line has no room for, filed as RK999.",
        ),
    )
    finding = next(one for one in lint(config).findings if one.code == "body.promise")
    assert finding.id == "RK1" and "names RK999" in finding.message
    # The same two ways out the refusal names, because neither surface may repair prose (L4).
    assert "spell the example outside RK" in finding.message


def test_the_gate_is_silent_where_every_id_a_design_names_is_a_line(tmp_path):
    from roadkeep.linting import lint

    config = project(
        tmp_path,
        improvements=RATIONALE.replace(
            "The reasoning the line has no room for.",
            "The reasoning the line has no room for, beside RK2 and XX999.",
        ),
    )
    assert not [one for one in lint(config).findings if one.code == "body.promise"]


def test_the_gate_reports_a_pointer_that_resolves_to_nothing(tmp_path):
    """RK1012, and the two rows RK1004's register measured as reported by nothing. Neither is
    cosmetic and the pointer is why: the gate holds that `→ §<id>` resolves, so a heading with
    nothing under it satisfies that check while giving the reader none of what it promised."""
    from roadkeep.linting import lint

    # The subsection goes too: §RK1's argument is its subtree, so a parent left with a child
    # is not hollow — the same reading `_budget` makes, and the reason `§0` here stays silent.
    # What is under test is a pointer resolving to nothing at all.
    hollow = RATIONALE[: RATIONALE.index("### §RK1 A first design")] + "### §RK1 A first design\n"
    config = project(tmp_path, improvements=hollow)
    found = [one for one in lint(config).findings if one.code == "body.empty"]
    assert found and found[0].id == "RK1"
    assert "promised a rationale" in found[0].message


def test_the_gate_reports_a_section_addressed_and_unnamed(tmp_path):
    from roadkeep.linting import lint

    config = project(
        tmp_path, improvements=RATIONALE.replace("### §RK1 A first design", "### §RK1")
    )
    found = [one for one in lint(config).findings if one.code == "title.empty"]
    assert found and found[0].id == "RK1"


def test_a_container_with_no_prose_of_its_own_is_not_hollow(tmp_path):
    """The boundary, and the reason the reading is the subtree: this repository's own `§0` is
    a heading whose children are the rationale. A parent left with none is `ship`'s to report
    (RK377), and reporting it here too would be one state named twice."""
    from roadkeep.linting import lint

    config = project(tmp_path)
    assert not [one for one in lint(config).findings if one.code in ("body.empty", "title.empty")]


# -- a child is charged to the address that owns it (RK1024) -----------------


def _budgeted(tmp_path: Path, parent_words: int, limit: int = 30):
    """An outline project whose §IX is a live design already near its own limit."""
    return project(
        tmp_path,
        top='ref_scheme = "outline"\n',
        extra=f"\n[limits]\nsection = {limit}\n",
        roadmap=f"# Roadmap\n\n## Block A — The model\n\n{RK1_LINE.replace('§RK1', '§IX')}\n",
        improvements=(
            "# Improvements\n\n## Block A — The model\n\n"
            "### IX A design already spending its budget\n\n"
            + " ".join(["word"] * parent_words)
            + "\n"
        ),
    )


def test_a_subsection_that_puts_its_parent_over_is_refused_before_the_write(tmp_path):
    """The reproduction. `add` promises nothing is written unless every field passes, and a
    child charged on its own words alone made that promise false for every nested address:
    the parent was 299 of its own 300, so an empty subsection was already over."""
    config = _budgeted(tmp_path, parent_words=29)
    before = read(config)
    with pytest.raises(SectionError) as raised:
        add(config, "improvements", "IX.1", "A child", "Six more words than there is room.")
    message = str(raised.value)
    assert "§IX" in message and "anchors --next" in message
    assert read(config) == before


def test_the_child_s_own_words_are_still_what_a_top_level_is_charged(tmp_path):
    """The half that must not move: a top level has no ancestor to overflow, so it is
    charged its own prose exactly as it was, and prose the gate calls clean is accepted."""
    config = _budgeted(tmp_path, parent_words=29)
    document, section = add(config, "improvements", "X", "A sibling", "Four short words.")
    assert section.anchor == "X"
    document.save()
    assert lint(Config.discover(tmp_path)).findings == ()


def test_a_parent_with_room_takes_the_child(tmp_path):
    """The refusal is about the total and not about nesting: where the subtree still fits,
    the write lands and the gate agrees."""
    config = _budgeted(tmp_path, parent_words=5)
    document, _ = add(config, "improvements", "IX.1", "A child", "Four short words.")
    document.save()
    assert lint(Config.discover(tmp_path)).findings == ()


def test_a_container_nothing_points_at_is_not_charged_its_children(tmp_path):
    """The gate's own rule, asked the same way (RK215): a parent no line points at is a
    container, and charging its children here would refuse prose `lint` calls clean."""
    config = project(
        tmp_path,
        top='ref_scheme = "outline"\n',
        extra="\n[limits]\nsection = 30\n",
        roadmap="# Roadmap\n\n## Block A — The model\n",
        improvements=(
            "# Improvements\n\n## Block A — The model\n\n"
            "### IX A container nobody addresses\n\n" + " ".join(["word"] * 29) + "\n"
        ),
    )
    document, _ = add(config, "improvements", "IX.1", "A child", "Four short words.")
    document.save()
    assert lint(Config.discover(tmp_path)).findings == ()


# -- three zones and not two (RK1027) ----------------------------------------


def test_an_id_just_past_the_highest_is_a_sibling_not_yet_filed(tmp_path):
    """The case both remedies missed. A caller authoring two tasks that cite each other has
    to write one of them first, which is the only order a shell allows — and was told to
    rename or delete the cross-reference the backlog wanted."""
    config = project(tmp_path)
    with pytest.raises(SectionError) as refused:
        add(
            config,
            "improvements",
            "RK3",
            "A design",
            "A paragraph naming RK4, the sibling task this one is filed beside.",
        )
    (violation,) = [one for one in refused.value.violations if one.code == "body.promise"]
    assert "past every id a line carries" in violation.message
    assert "file that task first and write this section after" in violation.message
    # The advice the other two rows give is about a mistake, and this is not one.
    assert "name the id actually meant" not in violation.message


def test_an_id_far_past_the_highest_is_still_an_illustration(tmp_path):
    """The bound, and it is what RK1002 bought: §RK498 named `RK999` against a backlog whose
    next id was RK1000. Reading that as work in flight would take a refusal that was right
    and blunt it — nobody is filing eight hundred tasks in the sitting."""
    config = project(tmp_path)
    with pytest.raises(SectionError) as refused:
        add(config, "improvements", "RK3", "A design", "A paragraph naming RK999.")
    (violation,) = [one for one in refused.value.violations if one.code == "body.promise"]
    assert "spell the example outside RK" in violation.message
    assert "past every id a line carries" not in violation.message


def test_an_id_below_the_highest_is_a_hole_and_is_sent_to_gaps(tmp_path):
    """The third zone, unchanged in kind and now named: below the maximum there was
    something to retire, so where the id went is a question one verb already answers."""
    config = project(tmp_path, roadmap=BACKLOG.replace(f"{RK1_LINE}\n", ""))
    with pytest.raises(SectionError) as refused:
        add(config, "improvements", "RK3", "A design", "A paragraph naming RK1.")
    (violation,) = [one for one in refused.value.violations if one.code == "body.promise"]
    assert "read `gaps` for where it went" in violation.message
    assert "past every id a line carries" not in violation.message


def test_a_mixed_body_is_answered_as_the_mistake_it_may_be(tmp_path):
    """One violation and one sentence, so a body naming both is not two refusals. The
    conservative reading wins: an author told to check a spelling loses a moment, and one
    told to go and file a task that was a typo loses the turn."""
    config = project(tmp_path, roadmap=BACKLOG.replace(f"{RK1_LINE}\n", ""))
    with pytest.raises(SectionError) as refused:
        add(config, "improvements", "RK3", "A design", "A paragraph naming RK1 and RK4.")
    (violation,) = [one for one in refused.value.violations if one.code == "body.promise"]
    assert "names RK1, RK4" in violation.message
    assert "past every id a line carries" not in violation.message


# -- the door the ancestor check did not reach (RK1033) ----------------------


def _nested(tmp_path: Path, parent_words: int, child_words: int, limit: int = 30):
    """An outline project whose live §IX already owns a child, both spending its budget."""
    return project(
        tmp_path,
        top='ref_scheme = "outline"\n',
        extra=f"\n[limits]\nsection = {limit}\n",
        roadmap=f"# Roadmap\n\n## Block A — The model\n\n{RK1_LINE.replace('§RK1', '§IX')}\n",
        improvements=(
            "# Improvements\n\n## Block A — The model\n\n"
            "### IX A design\n\n" + " ".join(["word"] * parent_words) + "\n\n"
            "#### IX.1 A child\n\n" + " ".join(["word"] * child_words) + "\n"
        ),
    )


def test_an_amend_that_pushes_its_parent_over_is_refused(tmp_path):
    """The write RK1024 and RK1029 left open, and the one an author reaches more often: a
    design is amended more than once and written once, and an amend is where the prose
    already exists — so the refusal costs a draft rather than a retry."""
    config = _nested(tmp_path, parent_words=10, child_words=5)
    before = read(config)
    with pytest.raises(SectionError) as raised:
        amend(config, "improvements", "IX.1", body=" ".join(["word"] * 25))
    assert "§IX" in str(raised.value)
    assert read(config) == before


def test_an_amend_that_shortens_an_already_over_parent_lands(tmp_path):
    """The delta, and it is what keeps this from being RK215's deadlock: a file somebody
    else left over is one an author can only correct by writing into it, and a refusal there
    closes every door and leaves the prose saying something untrue."""
    config = _nested(tmp_path, parent_words=25, child_words=25)
    document, section, _ = amend(config, "improvements", "IX.1", body="Four short words.")
    document.save()
    assert section.own_words == 3
    # Still over — the parent alone is 25 of 30 — and the write was right anyway.
    assert find(Config.discover(tmp_path).document("improvements"), "IX").words > 30


def test_an_amend_that_leaves_the_total_where_it_was_lands(tmp_path):
    """The boundary between the two above: equal is not worse, so a rewrite that trades one
    sentence for another of the same length is a correction and not an overrun."""
    config = _nested(tmp_path, parent_words=25, child_words=10)
    document, _, _ = amend(config, "improvements", "IX.1", body=" ".join(["term"] * 10))
    document.save()
    assert "term" in read(Config.discover(tmp_path))


def test_a_container_nothing_points_at_still_binds_nothing_at_an_amend(tmp_path):
    """The gate's rule, asked the same way at this door too (RK215): an ancestor no line
    points at is charged its own prose, and charging its children here would refuse prose
    `lint` calls clean."""
    config = project(
        tmp_path,
        top='ref_scheme = "outline"\n',
        extra="\n[limits]\nsection = 30\n",
        roadmap="# Roadmap\n\n## Block A — The model\n",
        improvements=(
            "# Improvements\n\n## Block A — The model\n\n"
            "### IX A container nobody addresses\n\n" + " ".join(["word"] * 25) + "\n\n"
            "#### IX.1 A child\n\nFour short words.\n"
        ),
    )
    document, _, _ = amend(config, "improvements", "IX.1", body=" ".join(["word"] * 25))
    document.save()
    assert lint(Config.discover(tmp_path)).findings == ()


def test_the_two_doors_say_different_ways_out(tmp_path):
    """RK1034. The arithmetic is one number and is shared; what changes is the list of ways
    out, which is what a refusal is for. At an `add` the address has not been chosen, so
    `anchors --next` is one flag away; at an `amend` the section is already there and that
    door opens nothing."""
    config = _nested(tmp_path, parent_words=10, child_words=5)
    with pytest.raises(SectionError) as amended:
        amend(config, "improvements", "IX.1", body=" ".join(["word"] * 25))
    with pytest.raises(SectionError) as added:
        add(config, "improvements", "IX.2", "A second child", " ".join(["word"] * 25))
    said, wrote = str(amended.value), str(added.value)
    # The overage is the same sentence at both, because it is the same number.
    assert "limit is 30 with this section under it" in said
    assert "limit is 30 with this section under it" in wrote
    assert "anchors --next" in wrote and "anchors --next" not in said
    assert "`section move IX.1 --to <free anchor>`" in said
    assert "amending §IX's own prose" in said


def test_every_way_out_the_refusal_names_is_a_command_this_cli_parses(tmp_path):
    """The property `tests/test_hinting.py` holds over the package, asked here because both
    sentences are composed rather than declared: a refusal that hands over an argv hands over
    one that runs, and `anchors --next` was a real flag spelled at the wrong door."""
    parser = build_parser()
    for argv in (["anchors", "--next"], ["section", "move", "IX.1", "--to", "IX.9"]):
        assert parser.parse_args(argv) is not None


# -- the two regions that carry no anchor (RK1107) -----------------------------

#: A prose file with both of them: an opening that says what the file is, and a contents
#: listing its families. Shio's shape, which is where the defect was reported from — there
#: the two occupy lines 1–27 and 28–49, and neither had a door.
UNANCHORED = """# Improvements

The file's own opening, which says what this document is for.

## Table of contents

- [§RK1 A first design](#rk1-a-first-design)

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for.
"""


def test_the_unanchored_headings_are_the_ones_no_verb_could_reach(tmp_path):
    config = project(tmp_path, improvements=UNANCHORED)
    found = {one.title: one for one in untitled(config.document("improvements"))}
    assert set(found) == {"Improvements", "Table of contents", "Block A — The model"}
    # Own prose and never the subtree, `anchored`'s rule: the `#`'s body stops at the first
    # `##`, so amending the opening can never reach a section that has an address of its own.
    assert "says what this document is for" in found["Improvements"].body
    assert "Table of contents" not in found["Improvements"].body
    assert found["Improvements"].anchor == ""


def test_an_unanchored_section_is_addressed_by_its_heading(tmp_path):
    # The call the defect was reported from: `section show 'Table of contents'` answered *no
    # §Table of contents section*, which was true and left the caller the hand edit alone.
    config = project(tmp_path, improvements=UNANCHORED)
    document = config.document("improvements")
    assert titled(document, "Table of contents").lineno == 5
    assert titled(document, "Improvements").level == 1
    # An anchored heading is *not* reachable this way: one address per addressable thing.
    assert titled(document, "A first design") is None


def test_amending_the_contents_leaves_every_other_line_alone(tmp_path):
    config = project(tmp_path, improvements=UNANCHORED)
    document, section, changed = amend_untitled(
        config, "improvements", "Table of contents", body="- [§RK1 A first design](#rk1)"
    )
    document.save()
    body = read(config)
    assert changed == ("body",) and section.level == 2
    assert "- [§RK1 A first design](#rk1)\n" in body
    # Neither neighbour moved: the opening above it and the anchored section below.
    assert "The file's own opening, which says what this document is for." in body
    assert "The reasoning the line has no room for." in body
    # On this file and not on the report: the shared roadmap fixture points at sections this
    # prose does not carry, which is another test's subject. What matters here is that a write
    # into an unanchored region leaves the prose file itself gating clean.
    report = lint(Config.discover(tmp_path))
    assert [one.code for one in report.findings if one.file.endswith(IMPROVEMENTS)] == []


def test_the_opening_is_the_file_s_own_title_and_needs_no_new_word(tmp_path):
    # §RK1107 assumed a positional name (`preamble`) declared per project. The `#` heading is
    # already an unanchored heading and `prose_end` already delimits its body, so the file's
    # title is its address and no second addressing scheme is invented anywhere.
    config = project(tmp_path, improvements=UNANCHORED)
    document, _, changed = amend_untitled(
        config, "improvements", "Improvements", body="A rewritten opening."
    )
    document.save()
    body = read(config)
    assert changed == ("body",)
    assert "A rewritten opening.\n" in body and "## Table of contents\n" in body
    assert "The file's own opening" not in body


def test_a_retitled_unanchored_heading_gets_no_bare_sigil(tmp_path):
    # `heading_of` renders `§` + anchor, so an empty anchor wrote `## § Contents` — caught
    # here because the one writer of that spelling is the one place to answer it.
    config = project(tmp_path, improvements=UNANCHORED)
    document, _, changed = amend_untitled(
        config, "improvements", "Table of contents", retitle="Contents"
    )
    document.save()
    assert changed == ("title",)
    assert "\n## Contents\n" in read(config) and "§ Contents" not in read(config)


def test_two_headings_with_one_text_have_no_address_between_them(tmp_path):
    # Refused rather than guessed: the first match would make *which one did I edit* a
    # question, and a file with two identical headings has two regions and one name.
    doubled = UNANCHORED.replace(
        "## Block A — The model", "## Table of contents\n\nA second one.\n\n## Block A — The model"
    )
    config = project(tmp_path, improvements=doubled)
    with pytest.raises(AmbiguousTitle) as refusal:
        amend_untitled(config, "improvements", "Table of contents", body="Which one?")
    assert "2 headings read 'Table of contents'" in str(refusal.value)
    assert read(config) == doubled


def test_an_amend_of_a_heading_no_file_carries_is_refused(tmp_path):
    config = project(tmp_path, improvements=UNANCHORED)
    with pytest.raises(NoSuchSection):
        amend_untitled(config, "improvements", "Nothing writes this", body="x")


def test_the_command_reads_and_writes_an_unanchored_section(tmp_path, capsys, monkeypatch):
    config = project(tmp_path, improvements=UNANCHORED)
    assert main(["-C", str(tmp_path), "section", "show", "Table of contents"]) == EXIT_OK
    assert "## Table of contents" in capsys.readouterr().out
    monkeypatch.setattr("sys.stdin", _Stdin("The corrected contents."))
    assert (
        main(["-C", str(tmp_path), "section", "amend", "Table of contents", "--body", "-"])
        == EXIT_OK
    )
    printed = capsys.readouterr().out
    # Named by its heading and carrying no word count: `section = <n>` is what a rationale
    # may spend, and these two were never measured against it.
    assert "'Table of contents' amended" in printed and "§ amended" not in printed
    assert "limit" not in printed
    assert "The corrected contents." in read(config)


def test_an_address_that_is_neither_says_so_in_both_vocabularies(tmp_path, capsys):
    project(tmp_path, improvements=UNANCHORED)
    assert main(["-C", str(tmp_path), "section", "show", "Nothing"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "no §Nothing section" in said and "no heading reading 'Nothing'" in said


# -- the answer with nothing in it to read (RK1109) ---------------------------


def test_an_unchanged_amend_says_the_prose_was_never_read(tmp_path, capsys, monkeypatch):
    """The defect, from a field report: a caller piped the replacement prose *and* passed
    `--title`, the title already read that way, and the answer was `unchanged: it already reads
    that way` at exit 0 — a success-shaped message over a paragraph nothing had looked at.

    The changed path lists its fields, so `(title)` already says the prose was left alone; this
    one listed nothing at all, which is where the silence was.
    """
    config = project(tmp_path)
    monkeypatch.setattr("sys.stdin", _Unread())
    argv = ["-C", str(tmp_path), "section", "amend", "RK1", "--title", "A first design"]

    assert main(argv) == EXIT_OK
    said = capsys.readouterr().out
    assert "unchanged: it already reads that way" in said
    assert "the prose was not read; pass --body - to replace it" in said
    # And the pipe stayed shut, which is the rule this keeps rather than changes: `_Unread`
    # fails the test if anything drains it.
    assert read(config) == RATIONALE


def test_an_unchanged_amend_that_did_read_the_prose_says_nothing_extra(tmp_path, capsys):
    # The clause is about what the call did not do, so a call that read the body and found it
    # identical is simply unchanged — adding the sentence there would be false.
    config = project(tmp_path)
    argv = [
        "-C", str(tmp_path), "section", "amend", "RK1",
        "--body", "The reasoning the line has no room for.",
    ]
    assert main(argv) == EXIT_OK
    said = capsys.readouterr().out
    assert "unchanged" in said and "the prose was not read" not in said
    assert read(config) == RATIONALE


def test_the_json_answer_carries_whether_the_prose_was_looked_at(tmp_path, capsys, monkeypatch):
    # `changed: []` says nothing moved and cannot say why, which is the ambiguity a piped body
    # and a `--title` land in together — so the same fact is a field.
    project(tmp_path)
    monkeypatch.setattr("sys.stdin", _Unread())
    argv = [
        "-C", str(tmp_path), "section", "amend", "RK1", "--title", "A first design", "--json",
    ]
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["changed"] == [] and payload["read_body"] is False


def test_the_clause_names_the_path_where_this_process_cannot_read_a_pipe(monkeypatch):
    # Over MCP the server owns stdin for the protocol, so the pipe is not available at all and
    # naming it would send the caller at the transport. `--body-file` is the door there, and
    # this is also why the fix is a sentence and not a *detection*: "stdin is not a tty" is true
    # of every served call, so refusing on it would refuse the whole surface.
    from roadkeep.verbs import reading

    monkeypatch.setattr(reading, "_STDIN_HARDENED", False)
    assert "--body-file <path> is the door" in reading.unread_prose()
    monkeypatch.setattr(reading, "_STDIN_HARDENED", True)
    assert "pass --body - to replace it" in reading.unread_prose()
