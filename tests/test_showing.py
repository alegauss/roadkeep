"""One task, joined from the files that hold a piece of it (RK12).

The join is the feature, so the tests are about what the join must not do: invent a
field, hide the absence of a section, or turn a dotted name in prose into a missing file.

The three absences are the interesting part. A section can be gone because the task
shipped (correct), because nobody wrote it (a defect `lint` will gate: RK15), or because
the project declares no prose file at all (a configuration, not a fault) — and a report
that spelled all three "none" would be the same as not asking.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import corpora
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.schema import DESIGNED, SHIPPED
from roadkeep.showing import NoSuchTask, paths_in, show

HERE = Path(__file__).resolve().parents[1]

BACKLOG = f"""# Roadmap

## Block A — The model

- {DESIGNED} **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- {DESIGNED} **RK4** (deps: RK1) **A fourth symptom** — Because of another. → §RK4
"""

LEDGER = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK2** **A shipped symptom** — it was done.
"""

RATIONALE = """# Improvements

## Block A — The model

### §RK1 A first design

The reasoning the line has no room for, which cites `docs/specs/first.md` and
`roadkeep.toml`.
"""


def project(
    tmp_path: Path,
    roadmap: str = BACKLOG,
    changelog: str = LEDGER,
    improvements: str | None = RATIONALE,
    strategy: str | None = None,
) -> Config:
    files = 'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
    if improvements is not None:
        files += 'improvements = "IMPROVEMENTS.md"\n'
        (tmp_path / "IMPROVEMENTS.md").write_text(improvements, encoding="utf-8")
    if strategy is not None:
        files += 'strategy = "STRATEGY.md"\n'
        (tmp_path / "STRATEGY.md").write_text(strategy, encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\n{files}', encoding="utf-8"
    )
    (tmp_path / "ROADMAP.md").write_text(roadmap, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(changelog, encoding="utf-8")
    # The directory the rationale's path claim sits in, and not the file: a claim is only
    # decidable where its directory exists (RK55), and what is being tested is a claim the
    # repository fails.
    (tmp_path / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    return Config.discover(tmp_path)


# -- the join ----------------------------------------------------------------


def test_the_line_and_its_section_arrive_together(tmp_path):
    view = show(project(tmp_path), "RK1")
    assert view.entry.lineno == 5 and not view.shipped
    assert view.task.symptom == "A first symptom"
    assert view.section is not None and view.section.title == "A first design"
    assert view.section_absence == ""


def test_a_shipped_task_is_found_in_the_ledger(tmp_path):
    # "RK2 shipped" is an answer, and a different one from "no such task".
    view = show(project(tmp_path), "RK2")
    assert view.shipped and view.role == "changelog"
    assert view.task.status == SHIPPED and view.task.deps == ()


def test_the_roadmap_is_asked_before_the_ledger(tmp_path):
    # An id in both files is a lint error; until the gate lands, the open line wins,
    # because that is the one a reader can still act on.
    config = project(
        tmp_path,
        roadmap=BACKLOG + f"- {DESIGNED} **RK2** (deps: —) **Twice over** — a reason. → §RK2\n",
    )
    assert show(config, "RK2").role == "roadmap"


def test_an_id_in_neither_file_names_both_files(tmp_path):
    with pytest.raises(NoSuchTask) as caught:
        show(project(tmp_path), "RK99")
    assert "ROADMAP.md" in caught.value.args[0] and "CHANGELOG.md" in caught.value.args[0]


# -- the three absences ------------------------------------------------------


def test_a_section_deleted_on_ship_is_not_reported_as_a_defect(tmp_path):
    view = show(project(tmp_path), "RK2")
    assert view.section is None
    assert "deleted on ship" in view.section_absence


def test_a_pointer_that_resolves_to_nothing_says_so(tmp_path):
    view = show(project(tmp_path), "RK4")
    assert view.section is None
    assert "§RK4 is not in IMPROVEMENTS.md" in view.section_absence
    assert "resolves to nothing" in view.section_absence


def test_a_project_with_no_prose_file_is_a_configuration_not_a_fault(tmp_path):
    view = show(project(tmp_path, improvements=None), "RK1")
    assert view.section is None and view.section_file is None
    # Both roles named, because both are roles a pointer may address (RK172): a message
    # naming one would describe a project that declares the other as declaring nothing.
    assert view.section_absence == "this project declares no improvements or strategy file"


# -- the pointer addresses every prose file, not the first one ---------------

POSITIONING = """# Strategy

## Block A — The model

### §RK4 Where this sits

The positioning prose, which `[files]` declares a governed role for.
"""


def test_a_pointer_into_the_strategy_file_resolves(tmp_path):
    # RK186: RK172 taught the gate that a pointer addresses every governed prose role and
    # left this reader asking the improvements file alone — so `brief` denied a design the
    # config declares, on the call that *starts* a task.
    view = show(project(tmp_path, strategy=POSITIONING), "RK4")
    assert view.section is not None and view.section.title == "Where this sits"
    assert view.section_file == "STRATEGY.md" and view.section_absence == ""


def test_an_anchor_two_prose_files_declare_resolves_to_neither(tmp_path):
    # The gate's own answer, in the reader's words: reading the first is what bills a task
    # somebody else's subtree without saying so, so the ambiguity is stated.
    config = project(
        tmp_path,
        improvements=RATIONALE + "\n### §RK4 A fourth design\n\nWritten here too.\n",
        strategy=POSITIONING,
    )
    view = show(config, "RK4")
    assert view.section is None and view.section_file is None
    assert "IMPROVEMENTS.md and STRATEGY.md" in view.section_absence
    assert "resolves to neither" in view.section_absence


def test_an_unresolved_pointer_names_every_file_it_was_looked_for_in(tmp_path):
    view = show(project(tmp_path, strategy=POSITIONING.replace("RK4", "RK9")), "RK4")
    assert view.section is None
    assert "§RK4 is not in IMPROVEMENTS.md or STRATEGY.md" in view.section_absence
    # And where a design would go is still named: the first declared role.
    assert view.section_file == "IMPROVEMENTS.md"


# -- the lines an entry owns -------------------------------------------------

WRAPPED = f"""# Shipped

## Block A — The model

- {SHIPPED} **RK5** **A hand-written entry** — the first half of a sentence that
  runs on past the line the parse could read, citing `docs/specs/tail.md`
  before it finally stops.
- {SHIPPED} **RK6** **A one-line entry** — this one fits.
"""

LOOSE = 'prefix = "RK"\n[rules.changelog]\none_sentence = false\nterminator = false\n'


def wrapping(tmp_path: Path) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        LOOSE + '[files]\nroadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "ROADMAP.md").write_text(BACKLOG, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text(WRAPPED, encoding="utf-8")
    (tmp_path / "docs" / "specs").mkdir(parents=True, exist_ok=True)
    return Config.discover(tmp_path)


def test_a_wrapped_entry_reports_every_line_it_owns(tmp_path):
    # RK194: the span has been a fact since RK157 and every writer uses it — this is the
    # reader, so what `record amend --lines` replaces is an answer and not a file to open.
    view = show(wrapping(tmp_path), "RK5")
    assert view.wrapped and len(view.lines) == 3
    # Verbatim, endings and all: these are the file's lines and not a rendering of them (L3).
    assert view.lines[0].rstrip("\r\n") == view.entry.raw
    assert view.lines[-1].strip() == "before it finally stops."
    # The count the refusal asks for, derivable from the answer rather than from the file.
    assert len(view.lines) == view.entry.stop - view.entry.index


def test_an_unwrapped_entry_owns_exactly_its_own_line(tmp_path):
    view = show(wrapping(tmp_path), "RK6")
    assert not view.wrapped
    assert [raw.rstrip("\r\n") for raw in view.lines] == [view.entry.raw]


def test_the_tail_of_a_wrapped_entry_is_text_the_task_names(tmp_path):
    # The fields hold only the first line, so a path quoted below it was invisible — and
    # `show`'s promise is the paths *this task* names, not the paths the parse reached.
    view = show(wrapping(tmp_path), "RK5")
    assert [referenced.path for referenced in view.paths] == ["docs/specs/tail.md"]


def test_the_lines_reach_the_json_and_carry_the_count(tmp_path, capsys):
    config = wrapping(tmp_path)
    assert main(["-C", str(config.root), "show", "RK5", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["wrapped"] is True and len(payload["lines"]) == 3
    assert payload["rendered"] == payload["lines"][0]


def test_the_refusal_that_asks_for_the_count_names_the_command_that_prints_them(
    tmp_path, capsys
):
    config = wrapping(tmp_path)
    assert main(["-C", str(config.root), "record", "amend", "RK5", "--why", "done."]) != EXIT_OK
    refused = capsys.readouterr().err
    assert "--lines 3" in refused and "show RK5" in refused


def test_a_live_ledger_hands_over_the_lines_its_wrapped_entries_own(tmp_path):
    """The shape this exists for, on the file it was measured on (RK194).

    Shio's ledger is 290 entries of which about half wrap, and the only route to the two
    lines a correction replaces was opening it. Materialised at the pin rather than read
    from the checkout, so a corpus somebody edits this afternoon is not this verdict.
    """
    corpora.require(corpora.SHIO)
    settings = corpora.config(corpora.SHIO)
    (tmp_path / "roadkeep.toml").write_text(
        corpora.raw(corpora.SHIO, "roadkeep.toml") or "", encoding="utf-8", newline=""
    )
    for role in ("roadmap", "changelog"):
        # At the paths that config declares, because `show` asks the config where they are.
        target = tmp_path / settings.relative(settings.path(role))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(corpora.text(corpora.SHIO, role), encoding="utf-8", newline="")
    config = Config.discover(tmp_path)
    wrapped = [entry for entry in config.document("changelog").entries if entry.wrapped]
    assert wrapped, "the corpus this was measured on carries wrapped entries"
    view = show(config, wrapped[0].task.id)
    assert len(view.lines) == wrapped[0].stop - wrapped[0].index > 1
    assert "".join(view.lines) in corpora.text(corpora.SHIO, "changelog")


# -- the paths its text names ------------------------------------------------


def test_the_paths_come_from_the_line_and_the_section(tmp_path):
    config = project(tmp_path)
    (config.root / "roadkeep.toml").exists()
    named = {p.path: p.exists for p in show(config, "RK1").paths}
    assert named == {"docs/specs/first.md": False, "roadkeep.toml": True}


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # Really there, so worth reporting even without a slash.
        ("see `roadkeep.toml`", ["roadkeep.toml"]),
        # A filename under a directory that exists: a claim the repository fails (RK55).
        ("see `docs/assets/nope.md`", ["docs/assets/nope.md"]),
        # The same name where no such directory exists — undecidable from prose, and 60 of
        # Shio's 61 findings. `app/api/route.ts` is a path in a template, not in the repo.
        ("see `nowhere/at/all/nope.md`", []),
        # An extension is what tells a filename from two method names sharing a prefix.
        ("`ShPostUnifiedWriteService.update/publish` is a pair", []),
        ("`application/zip` is a media type", []),
        # A dotted name in prose is not a broken file, and reporting it would make the
        # list noise — which is the failure mode of every report nobody reads.
        ("`Config.load` and `Schema.render`", []),
        # A URL is not a path in this repository.
        ("`https://example.com/a.md` and [x](https://example.com/b.md)", []),
        ("a [link](docs/assets/linked.md) counts", ["docs/assets/linked.md"]),
        # Slash-shaped and not this repository: a slash command, and an absolute path
        # that `roadkeep.toml` refuses for the same reason. RK25's line names four.
        ("`/roadkeep:add` and `/etc/hosts`", []),
        ("bare docs/specs/unquoted.md does not", []),
        # Quoted twice, reported once, in order of appearance.
        ("`docs/b.md` then `docs/b.md`", ["docs/b.md"]),
        # Slash-shaped and still not one file: a class of them. Disk cannot settle any of
        # these, so there is no question to ask — four of RK46's eight false findings.
        ("`blueprints/*/files/package.json` is a glob", []),
        ("`monaco-editor/esm/vs/…` is elided", []),
        ("`template/widget/<name>.html` is a placeholder", []),
        ("`@graphiql/react` is an npm package", []),
        # A leading `@` only: `node_modules/@types/node` names a directory, not a scope.
        ("`docs/assets/@kept.md`", ["docs/assets/@kept.md"]),
    ],
)
def test_what_counts_as_a_path(text, expected):
    assert [p.path for p in paths_in(text, HERE)] == expected


# -- this repository ---------------------------------------------------------


def test_every_open_task_here_shows_its_own_section():
    config = Config.discover(HERE)
    absent = [
        entry.task.id
        for entry in config.document("roadmap").entries
        if show(config, entry.task.id).section is None
    ]
    # RK15 will make this a gate; until then it is the hand-verification agents.md names.
    assert absent == []


# -- the command -------------------------------------------------------------


def test_the_command_prints_the_line_then_the_prose(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK1"]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("RK1  Block A  📋  open  ROADMAP.md:5")
    assert "  section  IMPROVEMENTS.md:5  §RK1, 13 words" in out
    assert "path     docs/specs/first.md  (missing)" in out
    assert out.rstrip().endswith("`roadkeep.toml`.")


def test_no_body_keeps_the_pointer_and_drops_the_prose(tmp_path, capsys):
    # `--no-body`, not `--brief`: `brief` is the command that starts a task (RK29), and
    # one word meaning two things is a word an agent guesses wrong.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK1", "--no-body"]) == EXIT_OK
    out = capsys.readouterr().out
    assert "IMPROVEMENTS.md:5" in out
    assert "The reasoning the line has no room for" not in out


def test_json_carries_the_section_the_absence_and_the_paths(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK4", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["section"] is None
    assert "resolves to nothing" in payload["section_absence"]
    assert payload["deps"] == ["RK1"] and payload["ref"] == "RK4"
    assert payload["paths"] == []

    assert main(["-C", str(tmp_path), "show", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["section"]["words"] == 13
    assert payload["section"]["body"].startswith("The reasoning")


def test_json_no_body_drops_the_body_and_keeps_the_count(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK1", "--no-body", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["section"]["body"] is None and payload["section"]["words"] == 13


def test_an_unknown_id_exits_two(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK99"]) == EXIT_USAGE
    assert "no task RK99" in capsys.readouterr().err
