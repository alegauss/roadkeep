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
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_GATE, EXIT_OK, main
from roadkeep.config import Config
from roadkeep.linting import lint

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

CONFIG = 'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'


def project(
    tmp_path: Path,
    roadmap: str = CLEAN,
    changelog: str | None = LEDGER,
    config: str = CONFIG,
) -> Config:
    (tmp_path / "roadkeep.toml").write_text(config, encoding="utf-8")
    files = {"ROADMAP.md": roadmap}
    if changelog is not None:
        files["CHANGELOG.md"] = changelog
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
    assert report.lines > 30
    assert report.checked == ("docs/ROADMAP.md", "docs/CHANGELOG.md")


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
