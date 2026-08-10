"""The backlog projected onto another file, without a second author (RK39).

Two properties carry this task, and both are the kind that rot quietly:

* **Idempotence.** The same input must yield the same bytes, or every refresh is a diff and
  the diff stops being readable exactly when it matters. That is also why no timestamp is
  emitted — the test that would catch a regression is the one that runs it twice.
* **No new sentence.** Task lines appear verbatim and block titles come from the headings,
  so `lint` still proves the artefact and L4 holds. A projection that summarised would be
  a generator, and a generator would reintroduce the drift the tool exists to stop.

The third is structural: the block is replaced *between markers the author put there*, and
everything outside them survives byte for byte, endings included.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep import cli, document, exporting
from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.document import Document
from roadkeep.exporting import BEGIN, END, NoMarkers, project, splice
from roadkeep.linting import lint
from roadkeep.picking import take
from roadkeep.schema import DESIGNED, IN_PROGRESS, RETIRED, SHIPPED
from roadkeep.shipping import retire

HERE = Path(__file__).resolve().parents[1]

ROADMAP = f"""# Roadmap

## Block A — The model (a task is data first)

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- {DESIGNED} **RK4** (deps: RK1) **A fourth symptom** — Because of another. → §RK4

## Block B — Authoring
"""

LEDGER = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK2** **A shipped symptom** — it was done.

## Block B — Authoring
"""

README = f"""# A project

Prose the author owns.

{BEGIN}
stale text nobody re-derived
{END}

More prose the author owns.
"""


def project_files(tmp_path: Path, roadmap: str = ROADMAP, readme: str = README) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    for name, body in {
        "ROADMAP.md": roadmap,
        "CHANGELOG.md": LEDGER,
        "README.md": readme,
    }.items():
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


# -- the projection -----------------------------------------------------------


def test_the_counts_are_per_block_and_from_both_files(tmp_path):
    projection = project(project_files(tmp_path))
    assert [(row.label, row.open, row.shipped) for row in projection.rows] == [
        ("A", 2, 1),
        ("B", 0, 0),
    ]
    assert (projection.totals.open, projection.totals.shipped) == (2, 1)


def test_a_block_title_comes_from_the_heading_that_declares_it(tmp_path):
    # Verbatim, and the roadmap's wording wins: the ledger's heading for the same block is
    # often the shorter one, and inventing a third would be authoring.
    projection = project(project_files(tmp_path))
    assert projection.rows[0].title == "A — The model (a task is data first)"


def test_the_next_ready_line_is_the_file_s_own_bytes(tmp_path):
    config = project_files(tmp_path)
    projection = project(config)
    assert projection.next_ready.task.id == "RK1"
    assert projection.next_ready.raw in projection.markdown()


def test_nothing_ready_projects_no_next(tmp_path):
    roadmap = ROADMAP.replace("(deps: —)", "(deps: RK9)")
    projection = project(project_files(tmp_path, roadmap=roadmap))
    assert projection.next_ready is None
    assert "Next ready" not in projection.markdown()
    assert projection.payload()["next"] is None


def test_the_retired_column_appears_only_once_something_is_retired(tmp_path):
    config = project_files(tmp_path)
    assert "Retired" not in project(config).markdown()

    retire(config, "RK4", reason="the premise stopped being true.").save()
    reopened = Config.discover(tmp_path)
    markdown = project(reopened).markdown()
    assert "Retired" in markdown
    # The count is per block and per marker, so a retirement is not counted as shipped.
    assert project(reopened).rows[0].retired == 1
    assert project(reopened).rows[0].shipped == 1


# -- a function of the governed files, and of nothing else (RK104) -------------


def test_the_files_may_be_handed_over_instead_of_read(tmp_path):
    """The seam a gate at a revision needs: count what you were given, open nothing.

    Given documents, the projection is derived from those alone — a table derived from this
    working tree and compared against a README at a revision would charge the current commit
    for every ship since.
    """
    config = project_files(tmp_path)
    roadmap = Document.parse(ROADMAP, schema=config.schema_for("roadmap"))
    thinner = Document.parse(
        ROADMAP.replace(f"- {DESIGNED} **RK4**", f"- {DESIGNED} **RK9**"),
        schema=config.schema_for("roadmap"),
    )
    assert project(config, {"roadmap": roadmap}).totals.open == 2
    # The ledger is absent from what was handed over, so its column is zero rather than
    # whatever the file on disk happens to say.
    assert project(config, {"roadmap": thinner}).totals.shipped == 0
    ids = [task["id"] for task in project(config, {"roadmap": thinner}).payload()["open"]]
    assert ids == ["RK1", "RK9"]


def test_a_projection_of_nothing_is_refused_rather_than_empty(tmp_path):
    config = project_files(tmp_path)
    with pytest.raises(KeyError, match="no roadmap to project"):
        project(config, {})


def test_a_live_claim_moves_no_byte_of_the_projection(tmp_path):
    """Claim-blind on purpose: a claim is dated outside the repository and expires on a clock.

    Read through one, the next-ready line would change with no commit to explain it — and a
    README that goes stale by itself is one the gate over it (RK104) reports for nothing.
    """
    started = ROADMAP.replace(f"- {DESIGNED} **RK1**", f"- {IN_PROGRESS} **RK1**")
    config = project_files(tmp_path, roadmap=started)
    before = project(config).markdown()
    take(config, None)
    assert project(Config.discover(tmp_path)).markdown() == before


# -- idempotence --------------------------------------------------------------


def test_the_same_input_yields_the_same_bytes(tmp_path):
    config = project_files(tmp_path)
    assert project(config).markdown() == project(config).markdown()
    assert project(config).json() == project(config).json()


def test_the_payload_carries_no_stamp_that_would_diff_every_run(tmp_path):
    payload = project(project_files(tmp_path)).payload()
    assert not [key for key in payload if "date" in key or "time" in key]
    assert "generated" not in json.dumps(payload)


def test_splicing_twice_changes_nothing_the_second_time(tmp_path):
    config = project_files(tmp_path)
    body = project(config).markdown()
    once = splice(README, body, "README.md")
    assert splice(once, body, "README.md") == once


def test_the_command_writes_once_and_then_says_it_is_current(tmp_path, capsys):
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    assert "refreshed" in capsys.readouterr().out
    written = (tmp_path / "README.md").read_text(encoding="utf-8")

    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    assert "already current" in capsys.readouterr().out
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == written


def test_a_readme_that_moved_between_the_read_and_the_write_is_refused(
    tmp_path, capsys, monkeypatch
):
    # RK132: the one write this tool makes outside a governed file was the one skipping the
    # question every `save` asks (RK116) — and a README is the file most likely to be open
    # in an editor while a command runs. `splice` is where the other writer lands here.
    project_files(tmp_path)
    readme = tmp_path / "README.md"
    theirs = readme.read_text(encoding="utf-8") + "\nA paragraph somebody else wrote.\n"
    spliced = exporting.splice

    def landing(text, body, where):
        readme.write_text(theirs, encoding="utf-8")
        return spliced(text, body, where)

    monkeypatch.setattr(exporting, "splice", landing)
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_GATE
    assert "changed since it was read" in capsys.readouterr().err
    assert readme.read_text(encoding="utf-8") == theirs  # their paragraph is still there


def test_a_readme_that_is_already_current_asks_nothing(tmp_path, capsys):
    # Idempotence comes first: nothing is written, so there is no write to refuse, and a
    # file deleted after the read is not a failure of a command that changes nothing.
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    capsys.readouterr()
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    assert "already current" in capsys.readouterr().out


# -- what is outside the markers is the author's ------------------------------


def test_everything_outside_the_markers_survives(tmp_path):
    config = project_files(tmp_path)
    spliced = splice(README, project(config).markdown(), "README.md")
    assert spliced.startswith("# A project\n\nProse the author owns.\n")
    assert spliced.endswith("More prose the author owns.\n")
    assert "stale text nobody re-derived" not in spliced


def test_the_files_line_endings_are_kept(tmp_path):
    crlf = README.replace("\n", "\r\n")
    spliced = splice(crlf, "one line", "README.md")
    assert "\n" not in spliced.replace("\r\n", "")


def test_a_file_with_no_markers_is_refused_with_the_lines_to_paste(tmp_path):
    with pytest.raises(NoMarkers) as caught:
        splice("# A project\n\nNo markers here.\n", "body", "README.md")
    message = caught.value.args[0]
    assert BEGIN in message and END in message and "no begin marker" in message


def test_markers_in_the_wrong_order_are_refused():
    with pytest.raises(NoMarkers):
        splice(f"{END}\n{BEGIN}\n", "body", "README.md")


def test_the_command_refuses_a_readme_without_markers(tmp_path, capsys):
    project_files(tmp_path, readme="# A project\n\nNo markers.\n")
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_USAGE
    assert BEGIN in capsys.readouterr().err
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == "# A project\n\nNo markers.\n"


# -- the two shapes on the command line --------------------------------------


def test_the_default_prints_the_markdown_and_writes_nothing(tmp_path, capsys):
    project_files(tmp_path)
    before = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert main(["-C", str(tmp_path), "export"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("<!-- generated by")
    assert "| Block | Open | Shipped |" in out
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == before


def test_json_carries_the_lines_and_the_totals(tmp_path, capsys):
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["totals"] == {"open": 2, "shipped": 1, "retired": 0}
    assert [task["id"] for task in payload["open"]] == ["RK1", "RK4"]
    assert payload["ledger"][0] == {
        "id": "RK2",
        "status": SHIPPED,
        "block": "A",
        "symptom": "A shipped symptom",
        "why": "it was done.",
        "deps": [],
        "ref": None,
        "line": 5,
    }
    assert payload["next"] == "RK1"


# -- this repository ----------------------------------------------------------


def test_this_repositorys_projection_matches_its_own_files(governed):
    config = Config.discover(governed)
    projection = project(config)
    census_open = len(config.document("roadmap").entries)
    assert projection.totals.open == census_open
    # Every open line appears in the payload exactly as the file spells it.
    payload_ids = [task["id"] for task in projection.payload()["open"]]
    assert payload_ids == [e.task.id for e in config.document("roadmap").entries]


def test_this_repositorys_readme_is_current(governed):
    # The artefact proves the format: if this fails, run `roadkeep export --readme`.
    config = Config.discover(governed)
    readme = (governed / "README.md").read_text(encoding="utf-8", errors="strict")
    assert splice(readme, project(config).markdown(), "README.md") == readme


def test_the_landing_page_carries_no_projection_to_go_stale():
    """`docs/index.html` is a pitch, so it restates no count — and holds no markers.

    The page used to carry the derived strip, which is why the README half of RK39 has a
    currency test and this one does not: a page that says nothing about the backlog cannot
    say it wrongly. `--site` is still the supported shape, asserted below against a
    scaffolded page; what is asserted here is that this file is not one of its targets.
    """
    page = (HERE / "docs" / "index.html").read_text(encoding="utf-8", errors="strict")
    assert BEGIN not in page
    assert "tasks shipped" not in page


# -- the page shape (RK39's other half) ---------------------------------------

PAGE = f"""<!DOCTYPE html>
<html><body>
<p>Markup the author owns.</p>
{BEGIN}
<p>stale markup nobody re-derived</p>
{END}
<footer>More markup the author owns.</footer>
</body></html>
"""


def test_the_page_body_is_derived_from_the_same_projection(tmp_path):
    projection = project(project_files(tmp_path))
    body = projection.html()
    assert "roadkeep export --site" in body
    # The same two numbers the Markdown table carries, in the shape a page reads.
    assert f"<b>{projection.totals.shipped}</b>" in body
    assert f'width:{projection.progress}%' in body
    assert "A — The model" in body


def test_a_symptom_that_would_break_the_markup_is_escaped(tmp_path):
    """A line that passed `add` must not be able to emit markup a browser mis-parses."""
    roadmap = ROADMAP.replace(
        "**A first symptom**", "**Tags <b> & quotes are not stripped**"
    )
    body = project(project_files(tmp_path, roadmap=roadmap)).html()
    assert "&lt;b&gt; &amp; quotes" in body
    assert "<b> & quotes" not in body


def test_the_meter_never_reads_full_while_something_is_open(tmp_path):
    """Floored, not rounded: 100% with one line still open is the one wrong number."""
    projection = project(project_files(tmp_path))
    assert projection.totals.open > 0
    assert projection.progress < 100


def test_the_page_refresh_is_idempotent(tmp_path):
    config = project_files(tmp_path)
    (tmp_path / "index.html").write_text(PAGE, encoding="utf-8", newline="")
    where = ["-C", str(tmp_path), "export", "--site", "index.html"]
    assert main(where) == EXIT_OK
    once = (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "stale markup" not in once
    assert "<footer>More markup the author owns.</footer>" in once
    assert main(where) == EXIT_OK
    assert (tmp_path / "index.html").read_text(encoding="utf-8") == once
    assert config is not None


def test_both_destinations_refresh_in_one_call(tmp_path, capsys):
    """A README and a page that restate one backlog cannot be refreshed by two commands:
    the one nobody remembered is the stale one, which is the symptom RK39 names."""
    project_files(tmp_path)
    (tmp_path / "index.html").write_text(PAGE, encoding="utf-8", newline="")
    assert (
        main(["-C", str(tmp_path), "export", "--readme", "--site", "index.html"])
        == EXIT_OK
    )
    out = capsys.readouterr().out
    assert "README.md refreshed" in out
    assert "index.html refreshed" in out
    assert "stale text" not in (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "stale markup" not in (tmp_path / "index.html").read_text(encoding="utf-8")


def test_a_site_that_moved_under_the_command_leaves_the_readme_alone(tmp_path, capsys):
    """Both targets or neither (RK187): the README is spliced first, so a refusal on the
    site used to exit at the gate with one projection refreshed and one stale — and the
    re-run it advises met a tree the failed command had already half-written."""
    project_files(tmp_path)
    (tmp_path / "index.html").write_text(PAGE, encoding="utf-8", newline="")
    readme_before = (tmp_path / "README.md").read_text(encoding="utf-8")

    # The other writer lands in the window the command actually occupies: after both
    # files were read, before either is renamed into place.
    real = document.stage

    def racing(target: Path, text: str) -> Path:
        staged = real(target, text)
        if target.name == "README.md":
            with (tmp_path / "index.html").open("a", encoding="utf-8", newline="") as f:
                f.write("<!-- somebody else -->\n")
        return staged

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("roadkeep.document.stage", racing)
        assert (
            main(["-C", str(tmp_path), "export", "--readme", "--site", "index.html"])
            == EXIT_GATE
        )
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == readme_before
    assert "stale markup" in (tmp_path / "index.html").read_text(encoding="utf-8")
    assert "re-run the command" in capsys.readouterr().err


def test_a_page_with_no_markers_is_refused_with_the_lines_to_paste(tmp_path, capsys):
    project_files(tmp_path)
    (tmp_path / "index.html").write_text("<html></html>\n", encoding="utf-8")
    assert main(["-C", str(tmp_path), "export", "--site", "index.html"]) == EXIT_USAGE
    assert BEGIN in capsys.readouterr().err


# -- the write that stales the block is the write that owes it (RK188) --------


def test_a_status_change_refreshes_the_block_without_a_second_command(tmp_path, capsys):
    """The symptom: RK104 gated the block and gave no verb the job of writing it, so ten
    claims and ten ships each left this repository failing its own conformance run on a
    file the task never touched. Every character of the block is derived from files the
    write already holds open, which makes it the same kind of thing as a dep annotation."""
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    capsys.readouterr()

    assert main(["-C", str(tmp_path), "status", "RK1", IN_PROGRESS]) == EXIT_OK
    readme = (tmp_path / "README.md").read_text(encoding="utf-8")
    assert f"{IN_PROGRESS} **RK1**" in readme  # the next-ready line moved with the marker
    assert "export.stale" not in [f.code for f in lint(Config.discover(tmp_path)).findings]


def test_the_refresh_reads_the_state_the_write_is_creating(tmp_path):
    """Derived from the edited documents and not from what is on disk: a projection taken
    before the rename would restate the backlog the command is replacing, which is the one
    thing worse than a stale block — a fresh one that is wrong."""
    config = project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    assert "| **Total** | 2 | 1 |" in (tmp_path / "README.md").read_text(encoding="utf-8")

    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    assert "| **Total** | 1 | 2 |" in (tmp_path / "README.md").read_text(encoding="utf-8")
    assert "export.stale" not in [f.code for f in lint(config).findings]


def test_a_write_that_moves_no_count_writes_no_readme(tmp_path):
    """Idempotence survives being called on every write: a command that changes nothing the
    block states leaves the file's bytes and its mtime alone, so the diff a refresh produces
    still means something."""
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    readme = tmp_path / "README.md"
    stamp = readme.stat().st_mtime_ns

    assert main(["-C", str(tmp_path), "amend", "RK4", "--why", "Because of a third."]) == EXIT_OK
    assert readme.stat().st_mtime_ns == stamp


def test_a_readme_that_moved_under_a_ship_refuses_the_whole_transaction(tmp_path, capsys):
    """The refresh is *inside* the transaction (RK187), not a step after it: the README is
    the file most likely to be open in an editor while a command runs, and a governed write
    that landed beside a refused refresh would be the half-applied state write_all exists
    to prevent — the roadmap saying shipped and the block still counting it open."""
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--readme"]) == EXIT_OK
    capsys.readouterr()
    readme = tmp_path / "README.md"
    roadmap_before = (tmp_path / "ROADMAP.md").read_text(encoding="utf-8")

    real = document.stage

    def racing(target: Path, text: str) -> Path:
        staged = real(target, text)
        if target.name == "ROADMAP.md":
            with readme.open("a", encoding="utf-8", newline="") as handle:
                handle.write("A paragraph somebody else wrote.\n")
        return staged

    with pytest.MonkeyPatch.context() as patch:
        patch.setattr("roadkeep.document.stage", racing)
        assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_GATE
    assert (tmp_path / "ROADMAP.md").read_text(encoding="utf-8") == roadmap_before
    assert "somebody else wrote" in readme.read_text(encoding="utf-8")


def test_a_readme_carrying_no_markers_is_not_a_target_of_a_write_either(tmp_path):
    """The markers are the declaration (RK37), the same reading the gate makes: a project
    that never asked for a projection does not get one opened by a `ship`."""
    project_files(tmp_path, readme="# A project\n\nNo projection here.\n")
    before = (tmp_path / "README.md").read_bytes()
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    assert (tmp_path / "README.md").read_bytes() == before


# -- one answer per call (RK466) ----------------------------------------------


def test_the_projection_and_a_destination_are_two_answers(tmp_path, capsys):
    """RK465's shape one command over: the branch that spliced returned before the `--json`
    read was reached, so a caller asking for both got the write and nothing about the read.
    Two answers asked for and one given, with no exit code separating that from the one it
    wanted."""
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--readme", "--json"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "--json prints the projection and --readme writes it into a file" in said
    assert "one answer per call" in said


def test_two_destinations_are_not_two_answers(tmp_path, capsys):
    """`--readme` and `--site` compose and always did: `_export` plans a splice per
    destination and writes them together or not at all (RK187), which is what RK39 asked for
    — a README and a page restating one backlog refreshed by the same call."""
    config = project_files(tmp_path)
    page = tmp_path / "index.html"
    page.write_text(
        "<html>\n<!-- roadkeep:begin -->\n<!-- roadkeep:end -->\n</html>\n", encoding="utf-8"
    )
    code = main(["-C", str(tmp_path), "export", "--readme", "--site", str(page)])
    assert code == EXIT_OK
    printed = capsys.readouterr().out
    assert "README.md" in printed and "index.html" in printed
    assert config is not None


def test_the_projection_alone_is_still_the_projection(tmp_path, capsys):
    project_files(tmp_path)
    assert main(["-C", str(tmp_path), "export", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)
