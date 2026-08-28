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
import subprocess
from pathlib import Path

import pytest

import corpora
from composing import runs
from conftest import git
from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.kernel.schema import DESIGNED, SHIPPED
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
        ("see `src/roadkeep/nope.md`", ["src/roadkeep/nope.md"]),
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
        ("a [link](src/roadkeep/linked.md) counts", ["src/roadkeep/linked.md"]),
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
        ("`src/roadkeep/@kept.md`", ["src/roadkeep/@kept.md"]),
    ],
)
def test_what_counts_as_a_path(text, expected):
    assert [p.path for p in paths_in(text, HERE)] == expected


# -- this repository ---------------------------------------------------------


def test_every_open_task_here_shows_its_own_section(governed):
    config = Config.discover(governed)
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


# -- the free address alone (RK410) ------------------------------------------


def _outline(tmp_path):
    """A project numbering its prose by outline, with one family several children deep."""
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\nref_scheme = "outline"\n[files]\nroadmap = "ROADMAP.md"\n'
        'changelog = "CHANGELOG.md"\nimprovements = "IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    for name, body in (
        (
            "ROADMAP.md",
            "# Roadmap\n\n## Block A — The model\n\n"
            "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §I.1\n",
        ),
        ("CHANGELOG.md", "# Shipped\n\n## Block A — The model\n"),
        (
            "IMPROVEMENTS.md",
            "# Improvements\n\n## I A first family\n\n### §I.1 RK1 A first design\n\n"
            "The reasoning.\n\n### §I.2 A second design\n\nThe reasoning.\n\n"
            "## II A second family\n\n### §II.1 Another design\n\nThe reasoning.\n",
        ),
    ):
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


def test_the_next_child_is_the_whole_answer(tmp_path, capsys):
    """Under a 27-anchor family the free address was the 28th row, and on a tool result the
    rows are what gets truncated first — so the one line that mattered was the likeliest cut."""
    root = _outline(tmp_path)
    assert main(["-C", str(root), "anchors", "--family", "I", "--next"]) == EXIT_OK
    assert capsys.readouterr().out == "§I.3\n"


def test_the_next_family_is_the_whole_answer_when_none_is_named(tmp_path, capsys):
    root = _outline(tmp_path)
    assert main(["-C", str(root), "anchors", "--next"]) == EXIT_OK
    assert capsys.readouterr().out == "§III\n"


def test_the_narrow_read_answers_what_the_wide_one_does(tmp_path, capsys):
    # A filter over a list already computed: the flag leaves the listing out and must never
    # answer differently, or it becomes a second derivation of the same address.
    root = _outline(tmp_path)
    assert main(["-C", str(root), "anchors", "--family", "I"]) == EXIT_OK
    wide = capsys.readouterr().out
    assert main(["-C", str(root), "anchors", "--family", "I", "--next"]) == EXIT_OK
    narrow = capsys.readouterr().out.strip()
    assert f"next     {narrow} — nothing ever used it" in wide


def test_the_narrow_payload_keeps_what_makes_the_answer_readable(tmp_path, capsys):
    root = _outline(tmp_path)
    assert main(["-C", str(root), "anchors", "--next", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    # The address is meaningless without which numbering it continues; the listing is what
    # this flag exists to leave out, so those keys are gone rather than empty.
    # `opens` joined with RK1140: the address alone sent a client at `add --ref III.1`, which
    # refuses until a heading declares `III` — so the row names the command that makes it one.
    assert payload["next_families"] == [
        {"namespace": None, "next": "III", "opens": "section add III --title …"}
    ]
    assert "anchors" not in payload and "retired" not in payload


def test_a_project_with_no_family_yet_says_so_rather_than_printing_nothing(tmp_path, capsys):
    root = _outline(tmp_path)
    (root / "IMPROVEMENTS.md").write_text("# Improvements\n", encoding="utf-8")
    assert main(["-C", str(root), "anchors", "--next"]) == EXIT_USAGE
    out = capsys.readouterr()
    assert out.out == ""
    assert "no outline family exists yet" in out.err


def test_the_first_address_names_both_systems_because_it_chooses_one(tmp_path, capsys):
    """RK1211. This sentence spelled `I.1` by hand, on the one file with no family to read a
    system off — which is why `next_family` answers None here at all. One half of the command
    declined to guess and the other half guessed, and taking the guess on a project numbering
    `1`, `1.1` made its top levels `1` and `I`: two systems tying at 1, which is RK1210's
    nondeterminism entered through a message that never mentions it."""
    root = _outline(tmp_path)
    (root / "IMPROVEMENTS.md").write_text("# Improvements\n", encoding="utf-8")
    assert main(["-C", str(root), "anchors", "--next"]) == EXIT_USAGE
    said = capsys.readouterr().err
    # Both, and the reason: a first address chooses the system for every address after it,
    # and which system a project numbers in is the project's (L4, L6).
    assert "--ref I.1" in said and "--ref 1.1" in said
    assert "whichever this project numbers in" in said


# -- the neighbour a refusal never named (RK1025) ----------------------------


OUTLINED = """# Improvements

## Block A — The model

### IX A design the outline numbers

The reasoning the line has no room for.
"""


def outlined(tmp_path: Path) -> Config:
    """A project addressing its prose by an outline, where an anchor is not an id."""
    config = project(tmp_path, improvements=OUTLINED)
    path = config.root / "roadkeep.toml"
    path.write_text(
        path.read_text(encoding="utf-8").replace(
            'prefix = "RK"', 'prefix = "RK"\nref_scheme = "outline"'
        ),
        encoding="utf-8",
    )
    return Config.discover(tmp_path)


def test_an_address_a_prose_file_declares_names_the_verb_that_prints_it(tmp_path):
    """The reproduction. `§IX` is the shape this tool writes in every pointer, and the
    refusal used to answer that no such **task** was ever written — accurate, in a
    vocabulary the caller was not using, leaving a grep of the file the guard exists to
    keep them out of as the next move."""
    with pytest.raises(NoSuchTask) as caught:
        show(outlined(tmp_path), "IX")
    said = caught.value.args[0]
    assert "§IX is a section in IMPROVEMENTS.md" in said
    assert "section show IX" in said
    # The absence is *replaced* and not appended to: "never written" and "it is over there"
    # are two answers, and a refusal printing both argues with itself.
    assert NoSuchTask.ABSENT not in said


def test_an_address_the_outline_could_number_is_said_as_a_shape_and_not_a_fact(tmp_path):
    """A pointer the caller holds for a section nobody has written yet is still worth
    answering — but as a reading of the argument, beside the absence, rather than as a claim
    that the section is there."""
    with pytest.raises(NoSuchTask) as caught:
        show(outlined(tmp_path), "XII.4")
    said = caught.value.args[0]
    assert NoSuchTask.ABSENT in said
    assert "§XII.4 is a section address rather than an id" in said


def test_a_sigil_the_caller_typed_is_the_argument_answering_for_itself(tmp_path):
    """Nobody writes a `§` in front of a task id, so the token names what it names whatever
    the scheme reads — and the verb is offered with the sigil stripped, because that is how
    the command takes one."""
    with pytest.raises(NoSuchTask) as caught:
        show(outlined(tmp_path), "§IX")
    assert "section show IX" in caught.value.args[0]


def test_an_id_scheme_offers_the_verb_only_where_the_section_is_really_there(tmp_path):
    """Under `id` an anchor *is* an id, so a token that is not a task is a typo and not an
    address — offering a section verb for one would be advice about a file the caller never
    mentioned. The declared section is the case that still answers, because it is a fact."""
    config = project(tmp_path)
    with pytest.raises(NoSuchTask) as caught:
        show(config, "RK99")
    assert caught.value.instead == ""
    assert NoSuchTask.ABSENT in caught.value.args[0]


def test_the_ordinary_refusal_is_unchanged(tmp_path):
    """The whole point of the condition: a missing id is the common case, and a sentence
    printed on every refusal is one nobody reads on the refusal that needed it."""
    with pytest.raises(NoSuchTask) as caught:
        show(outlined(tmp_path), "RK99")
    assert caught.value.instead == ""
    assert caught.value.args[0].endswith(NoSuchTask.ABSENT)


# -- the id the parse could not see (RK1048) ---------------------------------


def _repo(tmp_path: Path) -> Config:
    """A ledger entry that delivers two ids and leads with one — Shio's shape (RK1048)."""
    config = project(
        tmp_path,
        changelog=LEDGER
        + "\n- ✅ **RK7** **A first symptom** — it was done, and so was **RK8**.\n",
    )
    for argv in (
        ("init", "-q"),
        ("add", "-A"),
        # No `-c user.email=…` here: `conftest.git` carries the identity for every fixture
        # repository, which is what made three call sites around it a red gate (RK1153).
        ("commit", "-qm", "feat: two at once"),
    ):
        git(tmp_path, *argv)
    return Config.discover(tmp_path)


def test_an_id_no_entry_leads_with_is_answered_from_history(tmp_path):
    """`Document.by_id()` keys an entry by the id it **leads with**, so an entry delivering
    two things is visible under one of them. Measured in Shio: `show SH169` answered *never
    written* about a task in the file, while `gaps` resolved it to the commit that shipped
    SH154 and SH169 together — two readers of one file, disagreeing."""
    config = _repo(tmp_path)
    # RK7 leads the entry and resolves; RK8 is in the same sentence and does not.
    assert show(config, "RK7").task.id == "RK7"
    with pytest.raises(NoSuchTask) as caught:
        show(config, "RK8")
    said = caught.value.args[0]
    assert "wrote it" in said and "feat: two at once" in said
    assert "gaps` resolves which" in said


def test_an_id_history_never_wrote_keeps_the_plain_refusal(tmp_path):
    """The bound: a commit is evidence the id was written, and where there is none the
    sentence says only what it always said. Inventing a whereabouts from a failed search
    would be the worse half of the defect this closes."""
    config = _repo(tmp_path)
    with pytest.raises(NoSuchTask) as caught:
        show(config, "RK99")
    assert caught.value.args[0].endswith(NoSuchTask.ABSENT)


def test_a_tree_git_cannot_answer_for_is_silent(tmp_path):
    """A shallow clone, a tarball, an unindexed tree: the absence is the refusal's own."""
    with pytest.raises(NoSuchTask) as caught:
        show(project(tmp_path), "RK8")  # no `git init`, so there is no history to ask
    assert caught.value.args[0].endswith(NoSuchTask.ABSENT)


def test_the_join_prints_what_the_line_is_waiting_for(tmp_path, capsys):
    """RK1311's third surface. This read joins a task out of every file holding a piece of it,
    and a line carrying `(requires: console)` showed the marker, the deps, the section and the
    budget — and nothing about the thing it is actually waiting for."""
    project(tmp_path, roadmap=BACKLOG.replace(
        "(deps: —) **A first symptom**", "(deps: —) (requires: console) **A first symptom**"
    ))
    # The vocabulary this line's group is drawn from, appended: `project` writes `[files]` last,
    # so a table after it would be read as one of its keys.
    written = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    vocabulary = '[requirements]\ndeclared = ["console"]\n\n[files]'
    (tmp_path / "roadkeep.toml").write_text(
        written.replace("[files]", vocabulary), encoding="utf-8"
    )
    assert main(["-C", str(tmp_path), "show", "RK1"]) == EXIT_OK
    assert "  requires console" in capsys.readouterr().out

    assert main(["-C", str(tmp_path), "show", "RK1", "--json"]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["requires"] == ["console"]


def test_a_line_requiring_nothing_says_so_with_an_empty_list(tmp_path, capsys):
    # `[]` and never omitted, for `deps`' reason: a key that appears only when it is set is one
    # a reader learns to stop looking for. Silent in the printed register, as the deps row is.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "show", "RK1", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["requires"] == []


def test_a_paused_id_is_told_where_it_went_and_not_that_it_never_was(tmp_path):
    """RK1341. `defer` moves a line out of the backlog on purpose, so a task-addressed read
    declining it is right — `pick` skips it and `list` omits it, which is the verb's whole
    content. What none of them said is *where it went*: `show` answered `an id in neither file
    was never written or was retired`, and both of those are false about a line sitting in
    `DEFERRED.md` with a reason beside it.

    The store was never unreadable — `list --role deferred` prints it — so the refusal was
    standing in front of the answer offering two guesses, which is RK16's rule broken one
    surface over: a finding names the command that closes it, and so does a refusal."""
    # The section too, because `resume` puts the line back where a pointer is required: a
    # fixture whose stored line could not return would fail the door for its own reason.
    project(tmp_path, improvements=RATIONALE + "\n### §RK9 A parked design\n\nThe reasoning.\n")
    (tmp_path / "roadkeep.toml").write_text(
        (tmp_path / "roadkeep.toml").read_text(encoding="utf-8").rstrip("\n")
        + '\ndeferred = "DEFERRED.md"\n',
        encoding="utf-8",
    )
    (tmp_path / "DEFERRED.md").write_text(
        "# Deferred\n\n## Block A — The model\n\n"
        "- ⏸ **RK9** (deps: —) **A symptom plainly long enough to read** — "
        "set aside (Waiting on a decision.): Because of a reason. → §RK9\n",
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    with pytest.raises(NoSuchTask) as caught:
        show(config, "RK9")
    said = caught.value.args[0]
    # The claim that was false, gone; the file that holds it, named.
    assert NoSuchTask.ABSENT not in said
    assert "paused in DEFERRED.md" in said
    # Both doors: the read that prints it, and the write that undoes the pause.
    assert "list --role deferred" in said and "resume RK9" in said
    # Executed and not only quoted, which is what a `run` row in the composing table claims
    # (RK1209): a door is worth its characters only if what it prints lands, in the order
    # printed — the read first, then the write that empties the store it read.
    assert runs(tmp_path, said) == (["list", "--role", "deferred"], ["resume", "RK9"])

    # And an id that really is absent keeps the answer it had, which is the condition's point.
    with pytest.raises(NoSuchTask) as absent:
        show(config, "RK99")
    assert NoSuchTask.ABSENT in absent.value.args[0]
