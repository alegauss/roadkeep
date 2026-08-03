"""The gate, and the one property that makes it one (RK14).

Every assertion here is about a file that got past `add` — hand-edited, merged badly,
or written before a limit moved — because that is the only population `lint` exists for.
Two claims are load-bearing and the rest are the codes:

* **A defect exits 1.** A report at exit 0 is advice, and advice is what the 92 lines
  measured in Shio already had.
* **A defect is never repaired.** The file is compared byte-for-byte after the run:
  normalizing a line the parser may have misread is the corruption L3 forbids, so the
  report carries the canonical rendering and the edit stays a human's.

And the fixture that proves the format rather than asserting it: this repository's own
`docs/` must come back clean under its own `roadkeep.toml`.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_GATE, EXIT_OK, main
from roadkeep.config import Config
from roadkeep.exporting import BEGIN, END
from roadkeep.exporting import project as exported
from roadkeep.linting import lint
from roadkeep.picking import take

HERE = Path(__file__).resolve().parents[1]
#: A backlog that never heard of this tool, read where it lives and never written to.
#: Absent on any machine but the author's, so the test skips rather than fails.
SHIO = Path("D:/Git/viglet/shio/latest")

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 💭 **RK2** (deps: RK1) **A second symptom** — Because of another reason. → §RK2
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK5** **An earlier symptom** — Because it was done.
"""

PROSE = """# Design rationale

## Block A — The model

### §RK1 The first design

The reasoning the first line has no room for.

### §RK2 The second design

The reasoning the second line has no room for.
"""

CONFIG = (
    'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    'improvements = "IMPROVEMENTS.md"\n'
)


def project(
    tmp_path: Path,
    roadmap: str = CLEAN,
    changelog: str | None = LEDGER,
    improvements: str | None = PROSE,
    config: str = CONFIG,
) -> Config:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    files = {"ROADMAP.md": roadmap}
    if changelog is not None:
        files["CHANGELOG.md"] = changelog
    if improvements is not None:
        files["IMPROVEMENTS.md"] = improvements
    for name, body in files.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def codes(report) -> list[str]:
    return [finding.code for finding in report.findings]


# -- the fixture, and the pass -----------------------------------------------


def test_this_repository_passes_its_own_gate():
    # The format is proven by the artefact: a limit that cannot express these lines is
    # the wrong limit rather than a set of wrong lines.
    report = lint(Config.discover(HERE))
    assert report.clean, [str(f) for f in report.findings]
    # A floor and not a count: the lines only grow, but `ship` deletes the rationale
    # section, so the number of sections falls as the backlog empties (10 as RK22 landed).
    assert report.lines > 30 and report.sections > 3
    assert report.checked == (
        "docs/ROADMAP.md",
        "docs/CHANGELOG.md",
        "docs/IMPROVEMENTS.md",
        # The one file here the tool does not own, read because it carries the markers that
        # say it restates the backlog (RK104). `docs/index.html` carries none, so it is not
        # in this tuple — a pitch that states no count cannot state one wrongly.
        "README.md",
        "agents.md",
        "CLAUDE.md",
    )
    # The instruction files are inside the budget they declare, which is the reading that
    # matters: this repository is the file that reached 186 KB in the project next door.
    assert report.budgets == 2


def test_a_clean_project_exits_zero(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "clean" in out and "ROADMAP.md" in out and "CHANGELOG.md" in out


def test_a_foreign_backlog_is_reported_at_length_and_left_untouched():
    # The population the tool was measured against: 90-odd lines averaging 142 words
    # against a one-sentence rule. What matters here is that the gate produces a report
    # instead of an exception, and that the file it read is byte-identical afterwards.
    roadmap = SHIO / "docs" / "ROADMAP.md"
    if not roadmap.is_file():
        pytest.skip(f"{roadmap} is not on this machine")
    config = Config.parse(
        {"prefix": "SH", "ref_scheme": "outline", "files": {"roadmap": "docs/ROADMAP.md"}},
        root=SHIO,
    )
    before = roadmap.read_bytes()
    report = lint(config)
    assert report.problems > 20 and report.lines > 50
    assert roadmap.read_bytes() == before


# -- the schema, re-read where nothing was watching --------------------------


def test_a_second_sentence_is_found_in_a_file_add_never_saw(tmp_path):
    # The rule `add` refuses at input, on a line that arrived by hand.
    drifted = CLEAN.replace(
        "Because of a reason.", "Because of a reason. And then a second sentence."
    )
    report = lint(project(tmp_path, roadmap=drifted))
    assert "why.sentences" in codes(report)
    assert report.findings[0].id == "RK1"
    assert report.findings[0].lineno == 5


def test_an_over_length_line_names_the_limit(tmp_path):
    padded = CLEAN.replace("Because of a reason.", "Because of " + "a long reason " * 20)
    report = lint(project(tmp_path, roadmap=padded))
    assert {"why.too-long", "line.too-long"} <= set(codes(report))


def test_a_shipped_marker_in_the_roadmap_fails(tmp_path):
    report = lint(project(tmp_path, roadmap=CLEAN.replace("📋", "✅", 1)))
    assert "status.shipped" in codes(report)


def test_a_task_under_no_block_heading_is_a_finding(tmp_path):
    # `stats` calls it "(no block)" and counts it; here it is the defect it is.
    homeless = CLEAN.replace("## Block A — The model", "## Priority queue")
    report = lint(project(tmp_path, roadmap=homeless))
    assert codes(report).count("block.missing") == 2


# -- the line the parser could not read at all -------------------------------


def test_a_marker_bearing_line_the_grammar_rejected_fails_the_gate(tmp_path):
    # `audit` (RK10) prints this at exit 0 because reporting is not the gate. This is.
    broken = CLEAN + "- 📋 **RK3** **No deps field** — Because it was hand-written.\n"
    report = lint(project(tmp_path, roadmap=broken))
    assert "line.unparsed" in codes(report)
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_GATE


# -- L3: reported, never repaired --------------------------------------------


def test_a_line_that_does_not_round_trip_is_named_and_left_alone(tmp_path):
    # The pointer is derived from the id (RK27), so a hand-chosen anchor both violates
    # the schema and stops round-tripping — two findings on one line, and no rewrite.
    wrong_anchor = CLEAN.replace("→ §RK1", "→ §RK9")
    config = project(tmp_path, roadmap=wrong_anchor)
    before = (tmp_path / "ROADMAP.md").read_bytes()
    report = lint(config)
    assert {"ref.mismatch", "line.non-canonical"} <= set(codes(report))
    assert (tmp_path / "ROADMAP.md").read_bytes() == before
    canonical = next(f for f in report.findings if f.code == "line.non-canonical")
    assert "§RK1" in canonical.message


# -- one id, two answers ------------------------------------------------------


def test_one_id_twice_in_one_file_is_a_finding(tmp_path):
    twice = CLEAN + "- 📋 **RK1** (deps: —) **A repeat** — Because it was pasted. → §RK1\n"
    report = lint(project(tmp_path, roadmap=twice))
    duplicate = next(f for f in report.findings if f.code == "id.duplicate")
    assert duplicate.id == "RK1" and "line 5" in duplicate.message


def test_an_id_in_both_files_is_a_finding(tmp_path):
    both = LEDGER + "- ✅ **RK1** **The same task** — Because it shipped.\n"
    report = lint(project(tmp_path, changelog=both))
    assert "id.two-files" in codes(report)


# -- deps nothing will satisfy ------------------------------------------------


def test_a_dep_in_neither_file_is_a_finding(tmp_path):
    report = lint(project(tmp_path, roadmap=CLEAN.replace("(deps: RK1)", "(deps: RK9)")))
    unknown = next(f for f in report.findings if f.code == "deps.unknown")
    assert unknown.id == "RK2" and "RK9" in unknown.message


def test_a_dep_on_a_retired_task_is_a_finding(tmp_path):
    # RK32's other door: the record says the work will not happen, so the dependent
    # line is the author's next edit — reported at `retire`, gated here.
    gone = LEDGER + "- 🗑 **RK7** **A dropped symptom** — abandoned: the premise went.\n"
    report = lint(
        project(tmp_path, roadmap=CLEAN.replace("(deps: RK1)", "(deps: RK7)"), changelog=gone)
    )
    assert "deps.retired" in codes(report)


def test_a_dep_on_a_block_no_heading_declares_is_a_finding(tmp_path):
    report = lint(
        project(tmp_path, roadmap=CLEAN.replace("(deps: RK1)", "(deps: Block Z)"))
    )
    assert "deps.block" in codes(report)


def test_a_dep_outside_the_backlog_is_not_a_finding(tmp_path):
    # Turing writes `(deps: real design partners)` and means it: failing every file that
    # states an honest external dep would make the gate unadoptable.
    outside = CLEAN.replace("(deps: RK1)", "(deps: real design partners)")
    assert lint(project(tmp_path, roadmap=outside)).clean


def test_a_dep_on_another_declared_block_is_not_a_finding(tmp_path):
    # Shio's `(deps: Block P)` is legitimate: a block with open work is a dep that is
    # merely unsatisfied, which is what `deps` answers and not what the gate refuses.
    two_blocks = CLEAN.replace(
        "- 💭 **RK2** (deps: RK1)",
        "\n## Block B — Authoring\n\n- 💭 **RK2** (deps: Block A)",
    )
    assert lint(project(tmp_path, roadmap=two_blocks)).clean


def test_a_block_dep_the_task_is_itself_inside_is_a_cycle(tmp_path):
    # Block A cannot empty until RK2 ships, so RK2 waits on itself — one member, and a
    # sentence that says so instead of "wait on each other".
    inside = CLEAN.replace("(deps: RK1)", "(deps: Block A)")
    report = lint(project(tmp_path, roadmap=inside))
    (cycle,) = [f for f in report.findings if f.code == "deps.cycle"]
    assert cycle.id == "RK2" and "its own blocker set" in cycle.message


# -- the annotation that goes stale by itself (RK8) --------------------------


def test_an_annotation_that_no_longer_matches_its_target_is_a_finding(tmp_path):
    stale = CLEAN.replace("(deps: RK1)", "(deps: RK1 ✅)")
    report = lint(project(tmp_path, roadmap=stale))
    finding = next(f for f in report.findings if f.code == "deps.stale")
    assert "RK1 📋" in finding.message


# -- the defect the graph finds ----------------------------------------------


def test_a_cycle_is_reported_once_for_the_group(tmp_path):
    looping = CLEAN.replace("(deps: —)", "(deps: RK2)")
    report = lint(project(tmp_path, roadmap=looping))
    cycles = [f for f in report.findings if f.code == "deps.cycle"]
    assert len(cycles) == 1 and cycles[0].id == "RK1"
    assert "RK1 ↔ RK2" in cycles[0].message


# -- the file that is not there ----------------------------------------------


def test_a_declared_file_that_is_absent_is_reported_not_crashed(tmp_path):
    report = lint(project(tmp_path, changelog=None))
    missing = next(f for f in report.findings if f.code == "file.missing")
    assert missing.file == "CHANGELOG.md" and missing.lineno is None
    assert report.lines == 2  # the roadmap was still read


# -- the pointer, resolved in both directions (RK15) -------------------------


def test_a_pointer_to_a_section_that_does_not_exist_fails(tmp_path):
    # Worse than no pointer: it makes a reader stop looking.
    report = lint(project(tmp_path, improvements=PROSE.replace("§RK2", "§RK7")))
    unresolved = next(f for f in report.findings if f.code == "ref.unresolved")
    assert unresolved.id == "RK2" and "IMPROVEMENTS.md" in unresolved.message
    assert unresolved.file == "ROADMAP.md"  # where the broken pointer is written


def test_a_pointer_quoted_inside_a_sentence_is_not_scanned(tmp_path):
    # §RK15's own trap: the `why` quotes a pointer as an example of one, and a scan over
    # the raw line would report that quotation as the design that does not exist. The
    # rendered `ref` field is the only pointer, and here it resolves.
    quoting = CLEAN.replace(
        "Because of another reason.", "Because a `→ §RK9` in prose is not a pointer."
    )
    assert lint(project(tmp_path, roadmap=quoting)).clean


def test_a_section_whose_task_shipped_and_was_not_dropped_fails(tmp_path):
    # `ship` deletes the section as one of its three edits, so this is a hand edit.
    survived = PROSE + "\n### §RK5 The shipped design\n\nStill here after the ship.\n"
    report = lint(project(tmp_path, improvements=survived))
    stale = next(f for f in report.findings if f.code == "section.stale")
    assert stale.id == "RK5" and stale.file == "IMPROVEMENTS.md"


def test_a_section_no_line_points_at_is_an_orphan(tmp_path):
    orphaned = PROSE + "\n### §RK7 A design for nothing\n\nProse nothing points at.\n"
    report = lint(project(tmp_path, improvements=orphaned))
    assert [f.id for f in report.findings if f.code == "section.orphan"] == ["RK7"]


#: A project that numbers its rationale by hand, which is what both live corpora do (RK44).
#: The id is in the heading, not the anchor: `§XIV.15 A design (RK5)`.
OUTLINE_CONFIG = CONFIG.replace('prefix = "RK"', 'prefix = "RK"\nref_scheme = "outline"')
OUTLINE_CLEAN = CLEAN.replace("→ §RK1", "→ §I.1").replace("→ §RK2", "→ §I.2")
OUTLINE_PROSE = """# Design rationale

## Block A — The model

### §I.1 The first design (RK1)

The reasoning the first line has no room for.

### §I.2 The second design (RK2)

The reasoning the second line has no room for.
"""


def outline(tmp_path, improvements=OUTLINE_PROSE):
    return project(
        tmp_path, roadmap=OUTLINE_CLEAN, improvements=improvements, config=OUTLINE_CONFIG
    )


def test_an_outline_project_passes_when_every_section_names_a_live_task(tmp_path):
    assert lint(outline(tmp_path)).clean


def test_a_shipped_task_named_in_an_outline_heading_is_stale_too(tmp_path):
    # RK61: both checks were guarded by an id-shaped anchor, so under the scheme Shio and
    # Turing use they fired for nobody — 39 stale sections and 9 orphans in Shio, unseen.
    survived = OUTLINE_PROSE + "\n### §I.9 The shipped design (RK5)\n\nStill here.\n"
    report = lint(outline(tmp_path, improvements=survived))
    stale = next(f for f in report.findings if f.code == "section.stale")
    assert stale.id == "I.9" and "RK5" in stale.message


def test_an_outline_heading_naming_no_live_task_is_an_orphan(tmp_path):
    orphaned = OUTLINE_PROSE + "\n### §I.9 A design for nothing (RK7)\n\nProse.\n"
    report = lint(outline(tmp_path, improvements=orphaned))
    assert [f.id for f in report.findings if f.code == "section.orphan"] == ["I.9"]


def test_an_outline_heading_that_names_no_task_owns_nothing(tmp_path):
    # Naming no id is how a section says it belongs to no task, under either scheme.
    unowned = OUTLINE_PROSE + "\n### §I.9 A shape of the file\n\nProse.\n"
    assert lint(outline(tmp_path, improvements=unowned)).clean


def test_naming_a_task_in_a_heading_is_the_claim_to_be_its_rationale(tmp_path):
    # No exemption for where the section sits. The first attempt made one — "a task's section
    # is under a `Block X` heading", read off this repository's own file — and it disabled the
    # check on the corpus it was for: Shio files rationale under `## VIII. … (Block H)`, so all
    # 146 of its sections looked unowned. This repository's own §0.4 lost `(RK20)` from its
    # heading instead, because citing the task that took a measurement is not owning it.
    outside = OUTLINE_PROSE.replace(
        "## Block A — The model",
        "### §0.9 A reading (RK5)\n\nProse.\n\n## Block A — The model",
    )
    report = lint(outline(tmp_path, improvements=outside))
    assert [f.code for f in report.findings] == ["section.stale"]


def test_prose_that_belongs_to_no_task_is_nobody_s_orphan(tmp_path):
    # `§0.1` is this repository's own preface: an anchor no line owns, which is legal —
    # the same rule `section add` applies to an anchor that is not id-shaped (RK9).
    preface = PROSE + "\n## §0 — Why this exists\n\n### §0.1 The measured problem\n\nProse.\n"
    assert lint(project(tmp_path, improvements=preface)).clean


def test_two_sections_with_one_anchor_fail(tmp_path):
    twice = PROSE + "\n### §RK1 The first design again\n\nA pasted duplicate.\n"
    report = lint(project(tmp_path, improvements=twice))
    duplicate = next(f for f in report.findings if f.code == "section.duplicate")
    assert duplicate.id == "RK1" and "resolves to neither" in duplicate.message


def test_a_section_over_its_word_budget_fails(tmp_path):
    tight = CONFIG + "\n[limits]\nsection = 5\n"
    report = lint(project(tmp_path, config=tight))
    over = [f for f in report.findings if f.code == "section.too-long"]
    assert len(over) == 2 and "limit is 5" in over[0].message


def test_a_section_a_line_points_at_is_charged_for_its_subsection(tmp_path):
    # RK9's rule, at the gate: prose that escapes the budget by gaining a heading is the
    # drift the budget exists to stop, and following §RK1 is what hands it to a reader.
    grown = PROSE.replace(
        "### §RK2 The second design",
        "#### §RK1.1 A subsection\n\nWhich doubles what the pointer hands a reader.\n"
        "\n### §RK2 The second design",
    )
    # 10 words clears every section's own prose here and not §RK1 plus its subsection.
    report = lint(project(tmp_path, improvements=grown, config=CONFIG + "\n[limits]\nsection = 10\n"))
    assert [f.id for f in report.findings if f.code == "section.too-long"] == ["RK1"]


def test_a_container_nothing_points_at_is_measured_on_its_own_prose(tmp_path):
    # The other half: §0 has no prose of its own and three anchored children that are each
    # inside the budget, so charging it their words would fail a file with no long
    # paragraph in it — and this repository's own file is the fixture.
    nested = """# Design rationale

## Block A — The model

### §RK1 The first design

Three words here.

### §RK2 The second design

Three words here.

## §0 — Why this exists

Short.

### §0.1 The measured problem

This subsection is comfortably over any budget of five words.
"""
    report = lint(project(tmp_path, improvements=nested, config=CONFIG + "\n[limits]\nsection = 5\n"))
    assert [f.id for f in report.findings if f.code == "section.too-long"] == ["0.1"]


def test_no_prose_file_means_no_pointer_to_resolve(tmp_path):
    # Shio declares no improvements file. That is not a pointer defect, and a gate that
    # said so would fail every project that keeps its rationale somewhere else.
    bare = 'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    assert lint(project(tmp_path, improvements=None, config=bare)).clean


# -- the paths a line claims (RK15, narrowed to the ledger by RK46) ----------


def test_a_path_a_shipped_line_names_and_the_repository_lacks_fails(tmp_path):
    claiming = LEDGER.replace(
        "Because it was done.", "Because `docs/specs/absent.md` says so."
    )
    # The directory and not the file: a claim is decidable where its directory exists, and
    # undecidable prose is what RK55 stopped reporting.
    (tmp_path / "docs" / "specs").mkdir(parents=True)
    report = lint(project(tmp_path, changelog=claiming))
    missing = next(f for f in report.findings if f.code == "path.missing")
    assert missing.id == "RK5" and "docs/specs/absent.md" in missing.message
    assert missing.file == "CHANGELOG.md"


def in_docs(tmp_path: Path, ledger: str) -> Config:
    """A project whose ledger sits one directory down, which is where `..` starts to mean
    something: at the root the two bases RK51 compares are the same directory."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "docs/CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "docs").mkdir()
    for name, body in {"ROADMAP.md": CLEAN, "docs/CHANGELOG.md": ledger}.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def test_a_link_relative_to_the_ledgers_own_directory_resolves(tmp_path):
    # 886 of Shio's ledger links are written the way Markdown reads them — from the file —
    # and every one of them was reported missing (RK51). The question is whether the
    # repository has the artefact, not whether the link renders from the root.
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "Service.java").write_text("//", encoding="utf-8")
    config = in_docs(
        tmp_path,
        LEDGER.replace("Because it was done.", "Because [S](../src/Service.java) does it."),
    )
    assert config.document("changelog").entries, "the fixture has to have a ledger to read"
    assert [f for f in lint(config).findings if f.code == "path.missing"] == []


def test_a_relative_link_that_resolves_under_no_base_is_still_reported(tmp_path):
    (tmp_path / "src").mkdir()  # the directory exists; the file it claims does not (RK55)
    config = in_docs(
        tmp_path,
        LEDGER.replace("Because it was done.", "Because [g](../src/Gone.java) did it."),
    )
    missing = next(f for f in lint(config).findings if f.code == "path.missing")
    assert "../src/Gone.java" in missing.message


def test_a_path_the_roadmap_names_is_the_file_the_task_will_write(tmp_path):
    # Shio: 8 findings, 8 false — every one an artefact its task exists to create. A
    # roadmap describes work that has not happened, so absence there is not a defect.
    claiming = CLEAN.replace(
        "Because of a reason.", "Because it will write `import/post-types.json`."
    )
    assert lint(project(tmp_path, roadmap=claiming)).clean


def test_a_slash_command_is_not_a_missing_path(tmp_path):
    # RK25's line names four of them; each is slash-shaped and none is a file here.
    commands = LEDGER.replace("Because it was done.", "Because `/roadkeep:add` exists.")
    assert lint(project(tmp_path, changelog=commands)).clean


@pytest.mark.parametrize(
    "token",
    [
        "blueprints/*/files/package.json",
        "monaco-editor/esm/vs/…",
        "template/widget/<name>.html",
        "@graphiql/react",
    ],
)
def test_a_token_naming_a_class_of_file_is_not_a_claim_even_when_shipped(tmp_path, token):
    # The ledger is the file where absence *is* a defect, and these still are not: no
    # state of the repository makes any of them resolve, so none of them is falsifiable.
    claiming = LEDGER.replace("Because it was done.", f"Because `{token}` says so.")
    assert lint(project(tmp_path, changelog=claiming)).clean


def test_a_section_may_name_a_file_that_does_not_exist_yet(tmp_path):
    # A design's whole job: §RK26 names `.claude-plugin/marketplace.json` before there is
    # one. Resolving a section's prose would fail every honest forward reference.
    forward = PROSE.replace(
        "The reasoning the first line has no room for.",
        "It will write `.claude-plugin/marketplace.json` and nothing else.",
    )
    assert lint(project(tmp_path, improvements=forward)).clean


# -- the dep that names more work than it looks like (RK35) -------------------

COLLECTIVE = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 💭 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2

## Block B — Authoring

- 📋 **RK3** (deps: Block A) **A third symptom** — Because of a third reason. → §RK3
"""

WITH_RK3 = PROSE + "\n### §RK3 The third design\n\nThe reasoning the third line lacks.\n"


#: Eight open tasks behind one token — the magnitude in a fixture that owns its numbers,
#: so no assertion about it depends on another repository still having a full backlog.
CROWDED = (
    "# Roadmap\n\n## Block A — The model\n"
    + "".join(
        f"- 📋 **RK{n}** (deps: —) **A symptom** — Because of a reason. → §RK{n}\n"
        for n in range(11, 19)
    )
    + "\n## Block B — Authoring\n\n"
    "- 📋 **RK19** (deps: Block A) **A ninth symptom** — Because of a reason. → §RK19\n"
)
CROWDED_PROSE = "# Design rationale\n\n## Block A — The model\n" + "".join(
    f"\n### §RK{n} The design\n\nThe reasoning the line has no room for.\n"
    for n in (*range(11, 19), 19)
)


def test_a_block_dep_says_what_it_expands_to_without_failing(tmp_path):
    # `Block P` resolved to forty-one open tasks in Shio and is one token on the page.
    # Legitimate (RK28), so the exit code cannot move — but a reader counting deps to
    # judge how blocked a line is has no way to see it from the line.
    report = lint(project(tmp_path, roadmap=COLLECTIVE, improvements=WITH_RK3))
    assert report.clean and report.problems == 0
    (note,) = report.notes
    assert note.code == "deps.collective" and note.id == "RK3"
    assert "Block A is one token naming 2 open tasks: RK1, RK2" in note.message
    assert str(note).startswith("ROADMAP.md:10  deps.collective  RK3:")


def test_the_note_does_not_move_the_exit_code(tmp_path, capsys):
    project(tmp_path, roadmap=COLLECTIVE, improvements=WITH_RK3)
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "deps.collective" in out and "clean" in out


def test_a_range_dep_is_expanded_too(tmp_path):
    # Turing's `(deps: T451–T457)` is one token naming seven.
    ranged = COLLECTIVE.replace("(deps: Block A)", "(deps: RK1–RK2)")
    report = lint(project(tmp_path, roadmap=ranged, improvements=WITH_RK3))
    assert report.clean
    assert "RK1–RK2 is one token naming 2 open tasks" in report.notes[0].message


def test_the_listing_stops_at_six_and_the_count_still_names_them_all(tmp_path):
    # Where the count and the listing part company, which is the whole point of printing
    # the number: past six the reader is told how much the token hides, not which ids.
    report = lint(project(tmp_path, roadmap=CROWDED, improvements=CROWDED_PROSE))
    assert report.clean
    (note,) = report.notes
    assert "Block A is one token naming 8 open tasks: " in note.message
    assert note.message.endswith("RK11, RK12, RK13, RK14, RK15, RK16 …")


def test_a_collective_dep_naming_one_task_says_nothing(tmp_path):
    # There is no surprise at one, and at zero the annotation already reads ✅ because the
    # dep is satisfied (RK8). A note per token below that is output nobody reads.
    single = COLLECTIVE.replace(
        "- 💭 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2\n",
        "",
    )
    # The section goes with the line, or §RK2 is an orphan and the file is not clean.
    prose = WITH_RK3.replace(
        "### §RK2 The second design\n\nThe reasoning the second line has no room for.\n", ""
    )
    report = lint(project(tmp_path, roadmap=single, improvements=prose))
    assert report.notes == () and report.clean


def test_quiet_drops_the_notes_with_everything_else(tmp_path, capsys):
    project(tmp_path, roadmap=COLLECTIVE, improvements=WITH_RK3)
    assert main(["-C", str(tmp_path), "lint", "--quiet"]) == EXIT_OK
    assert "deps.collective" not in capsys.readouterr().out


def test_json_carries_the_notes_beside_the_findings(tmp_path, capsys):
    project(tmp_path, roadmap=COLLECTIVE, improvements=WITH_RK3)
    assert main(["-C", str(tmp_path), "lint", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is True and payload["findings"] == []
    (note,) = payload["notes"]
    assert note["code"] == "deps.collective" and note["id"] == "RK3"


def _open_in_shio_block(roadmap: Path, label: str) -> list[str]:
    """Block `label`'s open ids, read out of the raw text by nothing this suite tests.

    The point of the assertion below is that `expand` names *exactly* the set the file
    spells, so the expected side of it has to be counted independently — a second call
    into `Backlog` would only prove the parser agrees with itself.
    """
    ids: list[str] = []
    within = False
    for line in roadmap.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            within = line.startswith(f"## {label} ")
        elif within and (match := re.match(r"- \S+ \*\*(SH[1-9][0-9]*)\*\*", line)):
            ids.append(match.group(1))
    return ids


def test_a_live_backlog_shows_where_the_abbreviation_hides_work():
    roadmap = SHIO / "docs" / "ROADMAP.md"
    if not roadmap.is_file():
        pytest.skip(f"{roadmap} is not on this machine")
    config = Config.parse(
        {
            "prefix": "SH",
            "ref_scheme": "outline",
            "files": {"roadmap": "docs/ROADMAP.md", "changelog": "docs/CHANGELOG.md"},
        },
        root=SHIO,
    )
    # Not a floor: Shio empties Block P, and 48 when this was measured is 12 today. What
    # holds at every one of those is the note naming the count the file itself spells.
    expected = _open_in_shio_block(roadmap, "Block P")
    notes = [n for n in lint(config).notes if "Block P is one token" in n.message]
    if len(expected) < 2:
        # The block emptied to one: RK35 suppresses the note there, and that is the
        # assertion, not a reason to go red.
        assert notes == []
        return
    (note,) = notes
    assert f"naming {len(expected)} open tasks: {expected[0]}" in note.message


# -- the byte nobody can see (RK34) -------------------------------------------


def test_a_variation_selector_is_named_instead_of_its_consequence(tmp_path):
    # Measured against this parser: 📋 + U+FE0F is reported as `status.unknown`, which
    # prints as "'📋️' is not one of 📋" — correct, and unusable.
    report = lint(project(tmp_path, roadmap=CLEAN.replace("📋", "📋️", 1)))
    assert [f.code for f in report.findings] == ["char.invisible"]
    (finding,) = report.findings
    assert "U+FE0F" in finding.message and "variation selector-16" in finding.message
    # Column 4: "- " then the marker at 3, and the selector riding on it at 4.
    assert (finding.lineno, finding.column) == (5, 4)
    assert str(finding).startswith("ROADMAP.md:5:4  char.invisible  RK1:")


def test_a_no_break_space_is_named_instead_of_the_terminator_it_broke(tmp_path):
    # The other measured case: a NBSP before the pointer is reported as
    # `why.no-terminator`, naming the one thing the line does not lack.
    nbsp = CLEAN.replace("reason. → §RK1", "reason. → §RK1")
    report = lint(project(tmp_path, roadmap=nbsp))
    assert [f.code for f in report.findings] == ["char.space"]
    assert "U+00A0 no-break space" in report.findings[0].message


def test_the_codepoint_replaces_every_other_finding_on_that_line(tmp_path):
    # A line the author cannot read as written is not a line the format can judge, so the
    # rest is left for the run after the byte is gone — and the run after says so.
    tainted = CLEAN.replace("📋", "📋️", 1)
    config = project(tmp_path, roadmap=tainted)
    assert [f.code for f in lint(config).findings] == ["char.invisible"]
    (tmp_path / "ROADMAP.md").write_text(tainted.replace("️", ""), encoding="utf-8")
    assert lint(config).clean


def test_a_second_line_keeps_its_own_findings(tmp_path):
    # Suppression is per line, not per file: RK2's real problem still has to be reported.
    both = CLEAN.replace("📋", "📋️", 1).replace(
        "Because of another reason.", "Because of another reason. And a second."
    )
    report = lint(project(tmp_path, roadmap=both))
    assert [f.code for f in report.findings] == ["char.invisible", "why.sentences"]


def test_a_byte_order_mark_answers_for_itself(tmp_path):
    report = lint(project(tmp_path, roadmap="﻿" + CLEAN))
    assert [f.code for f in report.findings] == ["char.bom"]
    assert "not text" in report.findings[0].message


def test_a_tab_inside_a_line_is_a_control_character(tmp_path):
    # Category `Cc`, caught by the same rule and with no entry in any list: the definition
    # is Unicode's, so a control nobody has met yet is reported too.
    report = lint(project(tmp_path, roadmap=CLEAN.replace("A first symptom", "A first\tsymptom")))
    assert [f.code for f in report.findings] == ["char.invisible"]


def test_two_kinds_of_line_ending_in_one_file_are_reported(tmp_path):
    mixed = CLEAN.replace("- 📋 **RK1**", "- 📋 **RK1**").replace("\n", "\r\n", 3)
    report = lint(project(tmp_path, roadmap=mixed))
    assert [f.code for f in report.findings] == ["char.mixed-endings"]
    assert "CRLF" in report.findings[0].message and "LF" in report.findings[0].message


def test_a_file_that_is_uniformly_crlf_is_not_a_defect(tmp_path):
    # It round-trips, and a repository that checks out CRLF is a configuration and not a
    # mistake (L6). Reporting it would fail every Windows clone of an adopting project.
    assert lint(project(tmp_path, roadmap=CLEAN.replace("\n", "\r\n"))).clean


def test_prose_is_not_scanned_for_invisible_characters(tmp_path):
    # §RK34 had to quote a variation selector to explain the defect. A scan over prose
    # would have reported that quotation as the defect — RK15's trap, one file over.
    quoting = PROSE.replace(
        "The reasoning the first line has no room for.",
        "Measured: `📋️` is refused as `status.unknown`, naming the wrong thing.",
    )
    assert lint(project(tmp_path, improvements=quoting)).clean


# -- the file that is loaded every turn (RK30) --------------------------------


def budgeted(tmp_path: Path, body: str, declaration: str) -> Config:
    (tmp_path / "agents.md").write_text(body, encoding="utf-8", newline="")
    return project(tmp_path, config=CONFIG + f"\n[budgets]\n{declaration}\n")


def test_a_file_over_its_line_budget_fails(tmp_path):
    # Shio's `agents.md` reached 186 KB while stating a 150-line rule about itself, which
    # is the whole argument: a budget nothing reads is a budget nothing enforces.
    report = lint(budgeted(tmp_path, "a\nb\nc\nd\n", '"agents.md" = { lines = 3 }'))
    over = next(f for f in report.findings if f.code == "budget.lines")
    assert "4 lines, budget is 3" in over.message and over.file == "agents.md"
    assert "every turn" in over.message


def test_a_file_inside_its_budget_passes(tmp_path):
    assert lint(budgeted(tmp_path, "a\nb\n", '"agents.md" = { lines = 2 }')).clean


def test_a_last_line_without_a_terminator_still_counts(tmp_path):
    # Otherwise a file could sit one line over the budget by not ending with a newline.
    report = lint(budgeted(tmp_path, "a\nb\nc", '"agents.md" = { lines = 2 }'))
    assert "3 lines" in next(f for f in report.findings if f.code == "budget.lines").message


def test_the_byte_budget_catches_what_the_line_budget_cannot(tmp_path):
    # A line budget alone is met by writing longer lines, which is why RK30 names both.
    long_lines = "x" * 400 + "\n" + "y" * 400 + "\n"
    report = lint(budgeted(tmp_path, long_lines, '"agents.md" = { lines = 9, bytes = 500 }'))
    assert [f.code for f in report.findings] == ["budget.bytes"]
    assert "802 bytes, budget is 500" in report.findings[0].message


def test_a_budgeted_file_that_is_absent_is_reported(tmp_path):
    report = lint(project(tmp_path, config=CONFIG + '\n[budgets]\n"gone.md" = { lines = 5 }\n'))
    absent = next(f for f in report.findings if f.code == "budget.absent")
    assert absent.file == "gone.md" and absent.lineno is None


def test_a_budget_is_read_from_the_configuration_and_not_from_the_file(tmp_path):
    # L6: the number is per project, and the file it governs is not one the tool writes —
    # so nothing here parses `agents.md`, it only measures what a loader pays for it.
    config = budgeted(tmp_path, "a\n" * 40, '"agents.md" = { lines = 40 }')
    assert lint(config).clean
    (tmp_path / "roadkeep.toml").write_text(
        CONFIG + '\n[budgets]\n"agents.md" = { lines = 39 }\n', encoding="utf-8"
    )
    assert not lint(Config.discover(tmp_path)).clean


# -- the block the tool writes outside a governed file (RK104) -----------------


def readme(tmp_path: Path, body: str, name: str = "README.md") -> Config:
    """A project whose README carries a projection — current, stale, or malformed."""
    config = project(tmp_path)
    (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
    with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
        handle.write(body)
    return config


def marked(inside: str) -> str:
    return f"# A project\n\nProse the author owns.\n\n{BEGIN}\n{inside}\n{END}\n"


def derived(config: Config, shape: str = "markdown") -> str:
    return exported(config).body(shape)


def test_a_file_with_no_markers_is_not_a_target(tmp_path):
    # The markers are the author's declaration (RK37): a README that restates nothing cannot
    # restate it wrongly, and inventing the container is the one thing a gate may not do.
    config = readme(tmp_path, "# A project\n\nNo projection here.\n")
    report = lint(config)
    assert report.clean and "README.md" not in report.checked


def test_a_current_block_is_silence(tmp_path):
    config = project(tmp_path)
    (tmp_path / "README.md").write_text(marked("stale"), encoding="utf-8", newline="")
    config = Config.discover(tmp_path)
    (tmp_path / "README.md").write_text(
        marked(derived(config)), encoding="utf-8", newline=""
    )
    report = lint(config)
    assert report.clean and "README.md" in report.checked


def test_a_stale_block_fails_and_names_the_command(tmp_path):
    # The symptom: a commit ships a task, forgets `export`, and the table now contradicts
    # the ledger it was derived from — which every gate passed before this check existed.
    config = readme(tmp_path, marked("| Block | Open | Shipped |\n| --- | --- | --- |\n"))
    report = lint(config)
    stale = next(f for f in report.findings if f.code == "export.stale")
    assert stale.file == "README.md" and "export --readme" in stale.message
    # On the begin marker, not on the file: the block has a place, and a reader sent to the
    # file is sent to look for it (RK34's reading of a column).
    assert stale.lineno == 5


def test_the_stale_block_is_reported_and_never_rewritten(tmp_path):
    config = readme(tmp_path, marked("nothing derived this"))
    before = (tmp_path / "README.md").read_bytes()
    assert not lint(config).clean
    assert (tmp_path / "README.md").read_bytes() == before


def test_a_begin_with_no_end_has_no_block_to_compare(tmp_path):
    config = readme(tmp_path, f"# A project\n\n{BEGIN}\nhalf a container\n")
    report = lint(config)
    unmarked = next(f for f in report.findings if f.code == "export.unmarked")
    assert "no end marker" in unmarked.message and BEGIN in unmarked.message


def test_the_page_shape_is_gated_where_the_page_is(tmp_path):
    # The same check for `--site`, addressed by the flag that writes it: HTML between the
    # same two markers is the other half of RK39, and a stale meter is a stale count.
    config = readme(tmp_path, marked("<p>nobody re-derived this</p>"), "docs/index.html")
    stale = next(f for f in lint(config).findings if f.code == "export.stale")
    assert stale.file == "docs/index.html" and "export --site" in stale.message


def test_a_page_carrying_its_own_derived_html_is_clean(tmp_path):
    config = project(tmp_path)
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "index.html").write_text(
        marked(derived(config, "html")), encoding="utf-8", newline=""
    )
    assert lint(Config.discover(tmp_path)).clean


def test_the_gate_reads_the_same_bytes_the_write_produces(tmp_path):
    """`export` then `lint` is silence, which is the only property that makes this a gate.

    Asserted through the command rather than through the function: the two would agree on
    any pair of renderers, and what is being held is that they agree on *the* pair.
    """
    config = readme(tmp_path, marked("stale"))
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_OK


def test_a_claim_that_expires_moves_no_byte(tmp_path, monkeypatch):
    """The projection is claim-blind, so nothing outside the repository can make it stale.

    A claim is dated in a temp file and expires on a clock. A README derived through one
    would change bytes with no commit to explain the change, and a gate over those bytes
    would be red for a reason nobody can look up.
    """
    config = project(tmp_path, roadmap=CLEAN.replace("📋 **RK1**", "🛠 **RK1**"))
    (tmp_path / "README.md").write_text(
        marked(derived(config)), encoding="utf-8", newline=""
    )
    config = Config.discover(tmp_path)
    assert lint(config).clean
    take(config, None)  # RK1 is in progress, so tier 1 claims exactly that line
    assert lint(config).clean


# -- the id shape a project declares (RK106) ----------------------------------

PADDED = """# Roadmap

## Track A — Structured sources

- 📋 **D01** (deps: —) **A first symptom** — Because of a reason. → §D01
- 📋 **D09** (deps: D01) **A ninth symptom** — Because of another reason. → §D09
"""

PADDED_PROSE = """# Design rationale

## Track A — Structured sources

### §D01 The first design

The reasoning the first line has no room for.

### §D09 The ninth design

The reasoning the ninth line has no room for.
"""

PADDED_CONFIG = (
    'prefix = "D"\n[ids]\npad = 2\n[headings]\nword = "Track"\n'
    '[files]\nroadmap = "ROADMAP.md"\nimprovements = "IMPROVEMENTS.md"\n'
)


def test_a_backlog_that_pads_every_line_passes_once_it_declares_the_width(tmp_path):
    # The nine findings that were the whole of Dumont's lint output, and the reason a
    # fourth corpus could not wire the gate at all: one question about the id's spelling,
    # answered by the project rather than by the format.
    config = project(
        tmp_path,
        roadmap=PADDED,
        changelog=None,
        improvements=PADDED_PROSE,
        config=PADDED_CONFIG,
    )
    assert lint(config).clean, [str(f) for f in lint(config).findings]


def test_the_same_file_without_the_declaration_is_a_finding_per_line(tmp_path):
    config = project(
        tmp_path,
        roadmap=PADDED,
        changelog=None,
        improvements=PADDED_PROSE,
        config=PADDED_CONFIG.replace("[ids]\npad = 2\n", ""),
    )
    assert codes(lint(config)).count("id.format") == 2


# -- the contract -------------------------------------------------------------


def test_the_exit_code_is_the_report(tmp_path, capsys):
    project(tmp_path, roadmap=CLEAN.replace("Because of a reason.", "no terminator"))
    assert main(["-C", str(tmp_path), "lint"]) == EXIT_GATE
    out = capsys.readouterr().out
    assert "why.no-terminator" in out and "1 problem(s)" in out


def test_quiet_keeps_the_summary_and_drops_the_lines(tmp_path, capsys):
    project(tmp_path, roadmap=CLEAN.replace("Because of a reason.", "no terminator"))
    assert main(["-C", str(tmp_path), "lint", "--quiet"]) == EXIT_GATE
    out = capsys.readouterr().out
    assert "ROADMAP.md:5" not in out and "why.no-terminator 1" in out


def test_json_carries_every_finding_and_still_exits_one(tmp_path, capsys):
    project(tmp_path, roadmap=CLEAN.replace("Because of a reason.", "no terminator"))
    assert main(["-C", str(tmp_path), "lint", "--json"]) == EXIT_GATE
    payload = json.loads(capsys.readouterr().out)
    assert payload["clean"] is False and payload["problems"] == 1
    assert payload["codes"] == {"why.no-terminator": 1}
    (finding,) = payload["findings"]
    assert finding["file"] == "ROADMAP.md" and finding["line"] == 5
    assert finding["id"] == "RK1"
