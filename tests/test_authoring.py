"""Refusing at input, and writing without disturbing the file (RK5).

Two claims carry the task and neither is about convenience:

* **A refusal costs nothing and teaches the fix.** The over-length field is named with
  its length and its limit, every violation is reported at once, and the file is
  byte-identical afterwards — a partial write to a governed file is the failure this
  tool exists to remove.
* **An accepted line changes exactly one line.** Placement is asserted against the
  whole file text rather than against the inserted line, because "inserted correctly"
  and "did not touch anything else" are the same property (L3).
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from roadkeep.authoring import (
    DerivedPointer,
    IdInUse,
    NoAnchor,
    NoProseFile,
    RepeatedHeading,
    UnknownBlock,
    add,
    amend,
    restate,
)
from roadkeep.cli import EXIT_GATE, EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.backlog import NotOpen
from roadkeep.document import RoundTripError, Wrapped
from roadkeep.schema import SchemaError

ROADMAP = "docs/ROADMAP.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"
CHANGELOG = "docs/CHANGELOG.md"

FIRST = "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1"
BODY = f"""# Roadmap

## Block A — The model

{FIRST}

## Block B — Authoring

## Non-goals

- not a task line, and never reported as one
"""

DESIGN = """# Improvements

## Block A — The model

## Block B — Authoring
"""


def project(
    tmp_path: Path,
    body: str = BODY,
    *,
    declares: tuple[str, ...] = (),
    files: dict[str, str] | None = None,
    prose: str | None = None,
    ledger: str | None = None,
) -> Config:
    """A throwaway project: a config, its roadmap, and whatever else it declares.

    `prose` declares *and* writes the improvements file, which is the only state in
    which a pointer resolves to anything at all (RK93). A project that declares none
    is the third case those tests care about, and it stays this helper's default.

    `ledger` does the same for the changelog, which is what makes `add`'s second heading
    refusal reachable (RK380): a project declaring no ledger has nothing for it to read,
    and that is this helper's default for the same reason `prose` is.
    """
    lines = ['prefix = "RK"', *declares, "[files]", f'roadmap = "{ROADMAP}"']
    if prose is not None:
        lines.append(f'improvements = "{IMPROVEMENTS}"')
    if ledger is not None:
        lines.append(f'changelog = "{CHANGELOG}"')
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    written = {
        ROADMAP: body,
        **({IMPROVEMENTS: prose} if prose is not None else {}),
        **({CHANGELOG: ledger} if ledger is not None else {}),
        **(files or {}),
    }
    for name, text in written.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        # newline="" so a CRLF fixture stays CRLF on disk, which is the point of one
        # of these tests and would otherwise be silently translated by the write.
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    return Config.discover(tmp_path)


def source(config: Config) -> str:
    with config.path("roadmap").open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def task(config: Config, **overrides: object) -> object:
    fields: dict[str, object] = {
        "block": "B",
        "symptom": "A second symptom",
        "why": "Because of another reason.",
    }
    fields.update(overrides)
    return add(config, **fields)  # type: ignore[arg-type]


# -- where the line lands ----------------------------------------------------


def test_the_line_lands_after_the_last_task_in_its_block(tmp_path):
    config = project(tmp_path)
    added = task(config, block="A")
    assert added.rendered == (
        "- 📋 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2"
    )
    assert source(config) == BODY.replace(FIRST, f"{FIRST}\n{added.rendered}")
    assert added.lineno == 6


def test_an_empty_block_keeps_the_blank_line_before_the_next_heading(tmp_path):
    # A task glued to a heading reads as belonging to the wrong block, and the diff
    # that introduces it looks identical to the correct one.
    config = project(tmp_path)
    added = task(config)
    assert source(config) == BODY.replace(
        "## Block B — Authoring\n\n", f"## Block B — Authoring\n\n{added.rendered}\n\n"
    )


def test_an_empty_block_keeps_the_paragraph_that_introduces_it_above_the_task(tmp_path):
    # RK108: five of commitclerk's nine blocks open with a paragraph saying what the
    # block is for. It only ever shows once a block empties and refills, and the wrong
    # answer is legal, round-trips and lints clean — so nothing but this asserts it.
    preamble = "*Where a task line is created, and what is refused there.*"
    config = project(
        tmp_path, BODY.replace("## Block B — Authoring\n", f"## Block B — Authoring\n\n{preamble}\n")
    )
    added = task(config)
    assert source(config) == BODY.replace(
        "## Block B — Authoring\n\n",
        f"## Block B — Authoring\n\n{preamble}\n\n{added.rendered}\n\n",
    )


def test_prose_under_a_nested_heading_is_not_the_blocks_own_preamble(tmp_path):
    # The boundary `section add` draws: a task placed after the nested heading's prose
    # would read as belonging to that heading, which is the mistake one level down.
    config = project(
        tmp_path,
        "## Block B — Authoring\n\n*What this block is for.*\n\n### A note\n\nProse.\n",
    )
    added = task(config)
    assert source(config) == (
        "## Block B — Authoring\n\n*What this block is for.*\n\n"
        f"{added.rendered}\n\n### A note\n\nProse.\n"
    )


def test_a_block_whose_preamble_is_its_last_line_gains_the_task_after_it(tmp_path):
    config = project(tmp_path, "# Roadmap\n\n## Block B — Authoring\n\n*What this is for.*\n")
    added = task(config)
    assert source(config) == (
        f"# Roadmap\n\n## Block B — Authoring\n\n*What this is for.*\n\n{added.rendered}\n"
    )


def test_a_block_heading_on_the_last_line_gains_no_trailing_blank(tmp_path):
    config = project(tmp_path, "# Roadmap\n\n## Block B — Authoring\n")
    added = task(config)
    assert source(config) == f"# Roadmap\n\n## Block B — Authoring\n\n{added.rendered}\n"


def test_a_heading_followed_immediately_by_another_is_separated(tmp_path):
    config = project(tmp_path, "## Block B — Authoring\n## Block C — Query\n")
    added = task(config)
    assert source(config) == f"## Block B — Authoring\n\n{added.rendered}\n\n## Block C — Query\n"


def test_the_file_keeps_its_line_endings(tmp_path):
    config = project(tmp_path, BODY.replace("\n", "\r\n"))
    added = task(config)
    written = source(config)
    assert f"{added.rendered}\r\n" in written
    assert "\n" not in written.replace("\r\n", "")


def test_a_block_no_heading_declares_is_refused_and_the_file_is_untouched(tmp_path):
    config = project(tmp_path)
    with pytest.raises(UnknownBlock) as raised:
        task(config, block="Z")
    # The file and the verb are named: the fix is a heading or a different label, and
    # inventing the heading would file the task where nothing looks for it. The labels the
    # file *does* declare are not (RK296) — they are a set the caller is not choosing from.
    message = str(raised.value)
    assert "Block Z" in message and "block add Z" in message
    assert "A, B" not in message
    assert raised.value.declared == ("A", "B")  # still carried, for a caller that wants them
    assert source(config) == BODY


# -- one label, two headings, and no write that picks (RK391) ----------------

TWICE = BODY.replace(
    "## Non-goals", "## Block B — Authoring again\n\n## Non-goals"
)


def test_a_label_two_headings_declare_is_refused_rather_than_resolved(tmp_path):
    config = project(tmp_path, TWICE)
    with pytest.raises(RepeatedHeading) as raised:
        task(config, block="B")
    # Both addresses, because the fix is an editorial merge and nothing else locates it —
    # and the file is untouched, which is what "refused rather than resolved" means.
    message = str(raised.value)
    assert f"{ROADMAP}:7" in message and f"{ROADMAP}:9" in message
    assert raised.value.linenos == (7, 9)
    assert source(config) == TWICE


def test_the_other_block_is_still_writable(tmp_path):
    # Narrow: one broken label does not close the file. A is declared once and takes lines.
    config = project(tmp_path, TWICE)
    assert task(config, block="A").rendered.startswith("- 📋 **RK2**")


# -- the other heading, asked one task before the ship needs it (RK380) ------

LEDGER = """# Changelog

## Block A — The model
"""


def test_a_block_the_ledger_does_not_declare_is_refused_at_the_add(tmp_path):
    config = project(tmp_path, ledger=LEDGER)
    with pytest.raises(UnknownBlock) as raised:
        task(config, block="B")
    # The roadmap declares B, so this is the half only the ledger knows — and the sentence
    # is the one the first ship in this block would have given, at the end of the task.
    message = str(raised.value)
    assert CHANGELOG in message and 'block add B --title "<its title>"' in message
    # And the file the line was going into (RK404), because the roadmap's own `## Block B`
    # is on the author's screen and a refusal naming only the ledger reads as a bad label.
    assert f"though {ROADMAP} (where this line goes) declares it" in message
    assert raised.value.into == ROADMAP
    assert source(config) == BODY


def test_the_roadmap_answers_first_when_neither_file_declares_the_block(tmp_path):
    config = project(tmp_path, ledger=LEDGER)
    with pytest.raises(UnknownBlock) as raised:
        task(config, block="Z")
    # One mistake, named against the file the line was going into: `block add Z` opens the
    # heading in both, so a second sentence about the ledger would be the same remedy twice.
    message = str(raised.value)
    assert ROADMAP in message
    # And no clause about a second file (RK404): the two ends are one file here, so saying
    # it would repeat what the sentence has already said.
    assert "where this line goes" not in message


def test_a_block_both_files_declare_is_written(tmp_path):
    config = project(tmp_path, ledger=LEDGER)
    added = task(config, block="A")
    assert added.rendered.startswith("- 📋 **RK2**")


def test_a_project_that_declares_no_ledger_is_not_asked_about_one(tmp_path):
    # The refusal has to be about a file `ship` would read. Nothing declares a changelog
    # here, so there is no heading to be missing and no command that would add one.
    added = project(tmp_path)
    assert task(added, block="B").rendered.startswith("- 📋 **RK2**")


def test_a_declared_ledger_that_is_not_on_disk_yet_is_not_asked_about(tmp_path):
    config = project(tmp_path, ledger=LEDGER)
    config.path("changelog").unlink()
    assert task(config, block="B").rendered.startswith("- 📋 **RK2**")


def test_a_ledger_organised_by_nothing_is_asked_too_and_names_the_argument(tmp_path):
    # RK403 silenced this door, because the `block add` it named answered "already declared
    # in the roadmap: nothing to open". RK405 gave that verb `--organise`, so the remedy is
    # real and the narrowing's whole reason went with it (RK411).
    flat = "# Changelog\n\nProse, and no block heading anywhere in it.\n"
    config = project(tmp_path, ledger=flat)
    with pytest.raises(UnknownBlock) as raised:
        task(config, block="B")
    assert 'block add B --title "<its title>" --organise changelog' in str(raised.value)
    assert source(config) == BODY


# -- refusing before the prose exists ----------------------------------------


def test_an_over_length_why_is_refused_with_its_length_and_its_limit(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        task(config, why="Because " + "of a reason " * 20 + "indeed.")
    codes = [v.code for v in raised.value.violations]
    assert "why.too-long" in codes
    assert "255 characters, limit is 200" in str(raised.value)
    assert "improvements" in str(raised.value)
    assert source(config) == BODY


def test_every_violation_is_reported_not_the_first(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        task(config, symptom="Ends in a stop.", why="One sentence. And a second.")
    assert {v.code for v in raised.value.violations} == {
        "symptom.sentence",
        "why.sentences",
    }
    assert source(config) == BODY


def test_a_status_outside_the_declared_set_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        task(config, status="✅")
    assert [v.code for v in raised.value.violations] == ["status.shipped"]
    assert source(config) == BODY


def test_a_file_that_already_drifted_is_not_rewritten(tmp_path):
    # The pointer is derived here, so a hand-numbered anchor is a line the schema would
    # render differently: the write is refused rather than normalizing what it may have
    # misread.
    drifted = BODY.replace("→ §RK1", "→ §2.1")
    config = project(tmp_path, drifted)
    with pytest.raises(RoundTripError) as raised:
        task(config)
    assert "RK1" in str(raised.value)
    assert source(config) == drifted


# -- the id and the pointer --------------------------------------------------


def test_the_id_is_derived_one_past_the_highest(tmp_path):
    config = project(tmp_path, BODY.replace("RK1", "RK41"))
    assert task(config).entry.task.id == "RK42"


def test_an_id_already_used_is_refused_even_where_it_is_only_prose(tmp_path):
    config = project(
        tmp_path, declares=['id_sources = ["agents.md"]'], files={"agents.md": "RK9 is retired.\n"}
    )
    with pytest.raises(IdInUse) as raised:
        task(config, task_id="RK9")
    assert "agents.md:1" in str(raised.value)
    assert source(config) == BODY


def test_the_pointer_is_derived_and_cannot_be_chosen(tmp_path):
    config = project(tmp_path)
    with pytest.raises(DerivedPointer):
        task(config, ref="4.2")
    assert task(config, ref="RK2").entry.task.ref == "RK2"


def test_an_outline_project_supplies_its_own_anchor(tmp_path):
    config = project(tmp_path, declares=['ref_scheme = "outline"'])
    assert task(config, ref="4.2").rendered.endswith("→ §4.2")
    with pytest.raises(SchemaError) as raised:
        task(config)
    assert [v.code for v in raised.value.violations] == ["ref.missing"]


def test_the_default_status_is_the_first_marker_the_project_declares(tmp_path):
    config = project(tmp_path, declares=['[markers]', 'open = ["💭", "📋"]'])
    assert task(config).entry.task.status == "💭"


# -- deps --------------------------------------------------------------------


def test_a_dep_is_read_by_the_same_code_that_reads_the_file(tmp_path):
    config = project(tmp_path)
    added = task(config, deps=["RK1", "Block A", "real design partners"])
    assert added.rendered.startswith(
        "- 📋 **RK2** (deps: RK1, Block A, real design partners)"
    )
    assert [dep.id for dep in added.entry.task.deps] == [
        "RK1",
        "Block A",
        "real design partners",
    ]


def test_a_typed_marker_is_corrected_rather_than_trusted(tmp_path):
    # The annotation is a cache of another line's status (RK8), so what the author typed
    # about RK1 loses to what RK1's own line says.
    config = project(tmp_path)
    assert task(config, deps=["RK1 ✅"]).rendered.startswith("- 📋 **RK2** (deps: RK1 📋)")


def test_a_task_cannot_depend_on_itself(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as raised:
        task(config, task_id="RK7", deps=["RK7"])
    assert [v.code for v in raised.value.violations] == ["deps.self"]


# -- the command -------------------------------------------------------------


def test_the_command_prints_the_line_it_wrote(tmp_path, capsys):
    config = project(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
                "--dep",
                "RK1",
            ]
        )
        == EXIT_OK
    )
    printed, event = capsys.readouterr().out.splitlines()
    assert printed == "- 📋 **RK2** (deps: RK1) **A second symptom** — Because of another reason. → §RK2"
    assert printed in source(config)
    # A block that just gained a line is never empty, and the event says so anyway: one
    # shape from every mutator is what makes it parseable at all (RK38).
    assert event == "event    RK2  Block B  open"


def test_json_says_where_the_line_landed(tmp_path, capsys):
    project(tmp_path)
    assert main(
        [
            "-C",
            str(tmp_path),
            "add",
            "--block",
            "A",
            "--symptom",
            "A second symptom",
            "--why",
            "Because of another reason.",
            "--json",
        ]
    ) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["id"] == "RK2"
    assert payload["file"] == ROADMAP
    assert payload["line"] == 6
    assert payload["length"] == len(payload["rendered"]) <= 320


def test_a_refusal_exits_two_and_names_every_violation(tmp_path, capsys):
    config = project(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A symptom that ends in a stop.",
                "--why",
                "No terminator",
            ]
        )
        == EXIT_USAGE
    )
    err = capsys.readouterr().err
    assert "nothing written" in err
    assert "symptom.sentence" in err and "why.no-terminator" in err
    assert source(config) == BODY


def test_a_drifted_file_exits_one_because_the_gate_says_no(tmp_path, capsys):
    project(tmp_path, BODY.replace("→ §RK1", "→ §2.1"))
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
            ]
        )
        == EXIT_GATE
    )
    assert "will not be rewritten" in capsys.readouterr().err


# -- correcting a line that already exists (RK65) ------------------------------


def test_amend_rewrites_the_why_and_re_validates_it(tmp_path):
    # The work Shio's adoption is: 70 lines whose `why` is a paragraph, and §0.4 measured that
    # 67 of them point at a section that already makes the argument. Compression against a text
    # already written had no command until this one.
    config = project(tmp_path)
    amended = amend(config, "RK1", why="A shorter sentence.")
    assert amended.changed == ("why",)
    assert amended.rendered.endswith("— A shorter sentence. → §RK1")
    assert "A shorter sentence." in source(config)


def test_amend_refuses_a_why_over_the_limit_and_writes_nothing(tmp_path):
    config = project(tmp_path)
    before = source(config)
    with pytest.raises(SchemaError, match="why"):
        amend(config, "RK1", why="Because of " + "a long reason " * 30)
    assert source(config) == before


def test_amend_replaces_the_whole_dep_group(tmp_path):
    # Given at all, `--dep` replaces: a flag that appended could not remove the dep naming an
    # id in neither file, which is 4 of Shio's findings.
    second = "- 💭 **RK2** (deps: RK1) **A second symptom** — Because of another. → §RK2"
    config = project(tmp_path, BODY.replace(FIRST, FIRST + "\n" + second))
    amended = amend(config, "RK2", deps=["RK1"])
    assert amended.changed == ()  # already exactly that
    amended = amend(config, "RK2", deps=[])
    assert amended.changed == ("deps",) and "(deps: —)" in amended.rendered


def test_amend_writes_nothing_when_every_field_already_reads_that_way(tmp_path):
    config = project(tmp_path)
    before = source(config)
    amended = amend(config, "RK1", why=config.document("roadmap").by_id()["RK1"].task.why)
    assert amended.changed == ()
    assert source(config) == before


def test_amend_refuses_an_id_that_is_not_open(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotOpen):
        amend(config, "RK404", why="A sentence.")


def test_the_symptom_is_not_amendable():
    """It is the falsifiable claim the line *is*, so a different one is a different task — and
    the corpus agrees it is not the problem: 0 of Shio's 78 over the limit, against 70 whys.

    Not unreachable, though (RK178): `restate` is its door, and the separation is the answer —
    a flag here would have shown a reviewer a word changing where a claim was replaced."""
    import inspect

    assert "symptom" not in inspect.signature(amend).parameters
    assert "symptom" in inspect.signature(restate).parameters


# -- the one field a correction could not reach (RK178) ------------------------


def test_restate_replaces_the_claim_and_keeps_everything_it_is_keyed_on(tmp_path):
    # Measured in claude-tray: a line written from a list of response headers, whose premise
    # turned out false. The `why` was corrected, the marker dropped, the rationale rewritten to
    # refute itself — and the roadmap went on asserting the false claim in bold.
    config = project(tmp_path)
    restated = restate(config, "RK1", "A premise that turned out to be false")

    assert restated.changed
    assert restated.before.symptom == "A first symptom"
    assert "**A premise that turned out to be false**" in restated.rendered
    # The whole argument for the verb: the work never changed, so nothing the history is keyed
    # on moves — not the id, not the deps, not the pointer, not the marker.
    task = config.document("roadmap").by_id()["RK1"].task
    assert (task.id, task.deps, task.ref, task.status) == (
        restated.before.id,
        restated.before.deps,
        restated.before.ref,
        restated.before.status,
    )
    assert "A premise that turned out to be false" in source(config)


def test_restate_re_validates_the_symptom_and_writes_nothing_when_it_refuses(tmp_path):
    # L1 at this door as at every other: the limit is met before the sentence exists, and a
    # symptom is a phrase naming what does not work rather than a sentence.
    config = project(tmp_path)
    before = source(config)
    with pytest.raises(SchemaError, match="symptom"):
        restate(config, "RK1", "A claim " + "that is far too long " * 12)
    with pytest.raises(SchemaError, match="symptom"):
        restate(config, "RK1", "This one is written as a sentence.")
    assert source(config) == before


def test_restate_writes_nothing_when_the_line_already_states_it(tmp_path):
    config = project(tmp_path)
    before = source(config)
    restated = restate(config, "RK1", "A first symptom")
    assert not restated.changed and source(config) == before


def test_restate_refuses_an_id_that_is_not_open(tmp_path):
    config = project(tmp_path)
    with pytest.raises(NotOpen):
        restate(config, "RK404", "A claim about nothing")


def test_the_restate_command_prints_both_readings(tmp_path, capsys):
    # What makes it *recorded* rather than hidden: a reviewer sees a claim replaced, where a
    # `--symptom` inside `amend` would have shown a word changing.
    project(tmp_path)
    code = main(
        ["-C", str(tmp_path), "restate", "RK1", "--symptom", "A premise that was false"]
    )
    assert code == EXIT_OK
    out = capsys.readouterr().out
    assert out.startswith("RK1 restated  docs/ROADMAP.md:5")
    assert "was      A first symptom" in out
    assert "now      A premise that was false" in out
    assert "kept     the id, the deps and the section" in out


def test_the_restate_json_carries_both_readings(tmp_path, capsys):
    project(tmp_path)
    assert main(
        ["-C", str(tmp_path), "restate", "RK1", "--symptom", "A premise that was false", "--json"]
    ) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["was"] == "A first symptom"
    assert payload["now"] == "A premise that was false"
    assert payload["changed"] is True and payload["line"] == 5


def test_restate_takes_no_reason_because_the_format_has_nowhere_to_put_one(tmp_path):
    # An argument the tool cannot store is an argument it must not pretend to take (L4). The
    # commit that removes the false claim is where the reason belongs.
    import inspect

    taken = list(inspect.signature(restate).parameters)
    # Named rather than counted (RK195): the claim is that no argument *carries a reason*,
    # and a whole-signature equality also refused `lines`, which stores nothing and says
    # how many lines the write replaces.
    assert not {"reason", "why", "because", "rationale"} & set(taken)
    assert taken[:3] == ["config", "task_id", "symptom"]


# -- the same door, on the file the corpus said was clean (RK195) --------------

#: The shape adoption produces on a *roadmap*: a first line that satisfies every rule, and
#: a hand-written note under it that the parse reads nothing from. `RK2` is the neighbour a
#: span that overran would take. This lints clean, which is why nobody had counted it.
WRAPPED = f"""# Roadmap

## Block A — The model

{FIRST}
  Noted by hand when this backlog was somebody else's convention.
- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2

## Block B — Authoring
"""

WRAPPED_DESIGN = """# Improvements

## Block A — The model

### §RK1 A first design

Some prose.

### §RK2 A second design

Some other prose.

## Block B — Authoring
"""


def wrapped_project(tmp_path: Path) -> Config:
    return project(tmp_path, WRAPPED, prose=WRAPPED_DESIGN)


def test_a_wrapped_roadmap_line_parses_and_lints_clean(tmp_path):
    # The premise RK195 was filed to check. Both pinned roadmaps carry zero of these, and
    # the reason is not that the format prevents one: `add` refuses to write one, and
    # nothing refuses to read one. So the gate says nothing and the shape is reachable.
    from roadkeep.linting import lint

    config = wrapped_project(tmp_path)
    document = config.document("roadmap")
    first = document.by_id()["RK1"]
    assert first.wrapped and (first.lineno, first.stop) == (5, 6)
    assert not document.rejects
    assert lint(config).clean


def test_amending_a_wrapped_line_is_refused_until_the_count_is_given(tmp_path):
    # The defect: `replace_task` reproduces the first line, so the note stayed underneath a
    # sentence that had been replaced, and the command reported an amend.
    config = wrapped_project(tmp_path)
    with pytest.raises(Wrapped) as raised:
        amend(config, "RK1", why="Because the reason changed entirely.")
    message = str(raised.value)
    assert "ROADMAP.md:5" in message and "lines 5-6" in message
    assert "correcting it replaces all 2" in message and "--lines 2" in message
    assert source(config) == WRAPPED


def test_the_count_replaces_the_span_and_stops_at_the_next_line(tmp_path):
    config = wrapped_project(tmp_path)
    amend(config, "RK1", why="Because the reason changed entirely.", lines=2)

    body = source(config)
    assert "Because the reason changed entirely." in body
    assert "somebody else's convention" not in body
    # The neighbour is exactly where it was: a span that overran by one would have taken it.
    assert "- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2" in body


def test_restating_a_wrapped_line_is_refused_by_the_same_rule(tmp_path):
    # A restatement rewrites the line's prose too, so it strands the same tail — and the
    # verb in the refusal is the caller's own.
    config = wrapped_project(tmp_path)
    with pytest.raises(Wrapped) as raised:
        restate(config, "RK1", "A symptom that was never true")
    assert "restating it replaces all 2" in str(raised.value)
    assert source(config) == WRAPPED


def test_a_restatement_with_the_count_collapses_the_wrap(tmp_path):
    config = wrapped_project(tmp_path)
    restate(config, "RK1", "A symptom that was never true", lines=2)
    body = source(config)
    assert "**A symptom that was never true**" in body
    assert "somebody else's convention" not in body


def test_a_count_that_is_not_the_span_is_refused_rather_than_trusted(tmp_path):
    config = wrapped_project(tmp_path)
    with pytest.raises(Wrapped) as raised:
        amend(config, "RK1", why="Because the reason changed entirely.", lines=3)
    assert "--lines 3 is not that count" in str(raised.value)
    assert source(config) == WRAPPED


def test_a_line_that_does_not_wrap_needs_no_count(tmp_path):
    # The count is the door out of a refusal, not a new field on every correction: every
    # governed roadmap reads as zero wrapped lines, so nothing changes for one.
    config = wrapped_project(tmp_path)
    amend(config, "RK2", why="Because the second reason changed.")
    assert "Because the second reason changed." in source(config)


def test_an_amend_that_changes_nothing_is_never_asked_for_a_count(tmp_path):
    config = wrapped_project(tmp_path)
    amended = amend(config, "RK1", why="Because of a reason.")
    assert amended.changed == () and source(config) == WRAPPED


def test_both_flags_reach_the_command_line(tmp_path, capsys):
    config = wrapped_project(tmp_path)
    argv = ["-C", str(tmp_path), "amend", "RK1", "--why", "Because it changed.", "--lines", "2"]
    assert main(argv) == EXIT_OK
    assert "somebody else's convention" not in source(config)

    argv = ["-C", str(tmp_path), "restate", "RK2", "--symptom", "A restated symptom"]
    assert main(argv) == EXIT_OK  # RK2 does not wrap, so no count is asked for
    capsys.readouterr()

    argv = ["-C", str(tmp_path), "restate", "RK1", "--symptom", "Another restated symptom"]
    assert main(argv) == EXIT_OK  # RK1 no longer wraps either, the amend having collapsed it

# -- the rationale the pointer needs (RK93) ------------------------------------


def design(config: Config) -> str:
    with config.path("improvements").open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def test_the_line_and_the_design_it_points_at_are_one_write(tmp_path):
    # The pointer is derived on every line and `lint` requires it resolve, so an `add`
    # whose rationale is a second command can never leave a gate-clean tree.
    config = project(tmp_path, prose=DESIGN)
    added = task(config, section=("A design", "Because the gate said so."))
    assert added.needs is None
    assert added.section is not None and added.section.anchor == "RK2"
    written = design(config)
    assert "### §RK2 A design\n\nBecause the gate said so.\n" in written
    # Under its own block in the prose file, which is a consequence of the backlog's
    # order rather than a decision made per insertion (RK9).
    assert written.index("§RK2") > written.index("## Block B")
    assert added.rendered.endswith("→ §RK2")
    assert added.rendered in source(config)


def test_a_rationale_the_prose_file_refuses_leaves_no_line_either(tmp_path):
    # The whole point of one transaction: a roadmap written before the section was
    # validated is the dangling pointer this closes, arrived at by a refusal instead.
    config = project(tmp_path, declares=("[limits]", "section = 3"), prose=DESIGN)
    with pytest.raises(SchemaError) as raised:
        task(config, section=("A design", "Five words is already too many."))
    assert "body.too-long" in str(raised.value.violations[0])
    assert source(config) == BODY
    assert design(config) == DESIGN


def test_an_undeclared_block_in_the_prose_file_refuses_the_whole_add(tmp_path):
    # RK37 one file over: the section has nowhere to go, and the line would point at it.
    config = project(tmp_path, prose="# Improvements\n\n## Block A — The model\n")
    with pytest.raises(UnknownBlock):
        task(config, block="B", section=("A design", "Because of a reason."))
    assert source(config) == BODY


def test_an_add_with_no_rationale_names_the_command_that_answers_its_pointer(tmp_path):
    config = project(tmp_path, prose=DESIGN)
    added = task(config)
    assert added.needs == "RK2"
    assert added.section is None and added.prose is None
    assert design(config) == DESIGN  # named, never written: the tool has no prose (L4)


def test_a_pointer_that_already_resolves_asks_for_nothing(tmp_path):
    # Only an outline project reaches this state: under the id scheme the anchor is the
    # id, and an id the prose file already mentions is one `add` refuses to mint (RK4).
    config = project(
        tmp_path,
        declares=('ref_scheme = "outline"',),
        prose=(
            "# Improvements\n\n## Block B — Authoring\n\n"
            "### VIII.1 A design\n\nPre-existing.\n"
        ),
    )
    added = task(config, ref="VIII.1")
    assert added.needs is None and added.section is None


def test_a_project_with_no_prose_file_is_asked_for_nothing_it_cannot_do(tmp_path):
    # A follow-up naming a command that cannot run is worse than the silence it replaces.
    assert task(project(tmp_path)).needs is None
    config = project(tmp_path)
    with pytest.raises(NoProseFile):
        task(config, section=("A design", "Because of a reason."))
    assert source(config) == BODY


# -- the follow-up that names work already done (RK197) ------------------------

STRATEGY = "docs/STRATEGY.md"

PLAN = """# Strategy

## Block A — The model

### §X.1 The first design

Prose the project already has, and that the tool cannot write again (L4).

## Block B — Authoring
"""


def outlined(tmp_path: Path, *, improvements: str | None = None) -> Config:
    """An outline project whose prose lives in the strategy file, and maybe in both."""
    lines = ['prefix = "RK"', 'ref_scheme = "outline"', "[files]", f'roadmap = "{ROADMAP}"']
    written = {ROADMAP: BODY, STRATEGY: PLAN}
    if improvements is not None:
        lines.append(f'improvements = "{IMPROVEMENTS}"')
        written[IMPROVEMENTS] = improvements
    lines.append(f'strategy = "{STRATEGY}"')
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name, text in written.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    return Config.discover(tmp_path)


def test_a_pointer_another_prose_role_answers_asks_for_nothing(tmp_path):
    # The defect: reading the improvements file alone told this project its pointer
    # resolved to nothing, for an anchor STRATEGY.md holds and `lint` resolves — and the
    # `section add` it named would have written the second copy that is `ref.ambiguous`.
    config = outlined(tmp_path)
    added = task(config, ref="X.1")
    assert added.needs is None and added.needs_role is None
    with (tmp_path / STRATEGY).open("r", encoding="utf-8", newline="") as handle:
        assert handle.read() == PLAN  # named nothing, wrote nothing


def test_a_pointer_no_prose_role_answers_names_the_role_it_means(tmp_path):
    # The decision beside the fix: a project declaring only a strategy file would be handed
    # `section add`'s default, which is a role it does not declare — a follow-up that
    # cannot run, which is the silence this whole report replaced.
    config = outlined(tmp_path)
    added = task(config, ref="X.9")
    assert added.needs == "X.9" and added.needs_role == "strategy"


def test_the_default_role_is_left_unspoken_where_it_is_the_default(tmp_path):
    # Declaring both, the sentence every project already saw is the sentence it still sees:
    # improvements is `section add`'s default and where `add --section` writes.
    config = outlined(tmp_path, improvements="# Improvements\n\n## Block A — The model\n")
    added = task(config, ref="X.9")
    assert added.needs == "X.9" and added.needs_role == "improvements"


def test_either_declared_role_answering_is_enough(tmp_path):
    # The anchor decides, not the order of declaration: improvements is declared and empty,
    # and the strategy file is what resolves it.
    config = outlined(tmp_path, improvements="# Improvements\n\n## Block A — The model\n")
    assert task(config, ref="X.1").needs is None


def test_the_command_offers_a_follow_up_that_runs(tmp_path, capsys):
    outlined(tmp_path)
    argv = [
        "-C", str(tmp_path), "add", "--block", "A",
        "--symptom", "A second symptom", "--why", "Because of another.", "--ref", "X.9",
    ]
    assert main(argv) == EXIT_OK
    assert "needs    section add X.9 --title … --role strategy" in capsys.readouterr().out


def test_the_json_carries_the_same_follow_up(tmp_path, capsys):
    outlined(tmp_path)
    argv = [
        "-C", str(tmp_path), "add", "--block", "A",
        "--symptom", "A second symptom", "--why", "Because of another.", "--ref", "X.9",
        "--json",
    ]
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["needs"] == "section add X.9 --title … --role strategy"


def test_the_json_names_the_pointer_beside_the_id(tmp_path, capsys):
    # Both derived addresses read the same way (RK249). Under this scheme the anchor is
    # not the id, so recomputing it from `id` is not open to the caller either.
    outlined(tmp_path)
    assert (
        main(
            [
                "-C", str(tmp_path), "add", "--block", "A",
                "--symptom", "A second symptom", "--why", "Because of another.",
                "--ref", "X.9", "--json",
            ]
        )
        == EXIT_OK
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["ref"] == "X.9" and payload["id"] == "RK2"


def test_the_pointer_is_reported_where_the_section_was_written_in_the_same_call(
    tmp_path, capsys
):
    # The case that reported the anchor nowhere: `needs` is null exactly when `--section`
    # answered the pointer here, which is the composition RK93 recommends.
    outlined(tmp_path)
    assert (
        main(
            [
                "-C", str(tmp_path), "add", "--block", "A",
                "--symptom", "A second symptom", "--why", "Because of another.",
                "--ref", "X.1.1", "--section", "A design", "--section-body", "A reason.",
                "--json",
            ]
        )
        == EXIT_OK
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["needs"] is None
    assert payload["ref"] == "X.1.1"


def test_a_pointer_the_strategy_file_answers_reports_no_follow_up_on_the_command_line(
    tmp_path, capsys
):
    outlined(tmp_path)
    argv = [
        "-C", str(tmp_path), "add", "--block", "A",
        "--symptom", "A second symptom", "--why", "Because of another.", "--ref", "X.1",
    ]
    assert main(argv) == EXIT_OK
    assert "needs" not in capsys.readouterr().out


# -- the write that could not reach the file it was told about (RK230) --------

PLANNED = """# Strategy

## Block A — The model

## Block B — Authoring
"""


def planning(tmp_path: Path, *, improvements: str | None = None) -> Config:
    """A project whose prose is the strategy file — legal under L6, and refused until RK230."""
    lines = ['prefix = "RK"', "[files]", f'roadmap = "{ROADMAP}"']
    written = {ROADMAP: BODY, STRATEGY: PLANNED}
    if improvements is not None:
        lines.append(f'improvements = "{IMPROVEMENTS}"')
        written[IMPROVEMENTS] = improvements
    lines.append(f'strategy = "{STRATEGY}"')
    (tmp_path / "roadkeep.toml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    for name, text in written.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(text)
    return Config.discover(tmp_path)


def plan(config: Config) -> str:
    with config.path("strategy").open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def test_a_section_lands_in_the_only_prose_file_a_project_declares(tmp_path):
    # The follow-up already named `--role strategy` (RK197) for a write that then refused to
    # make it: `NoProseFile`, on a project whose one prose file was sitting right there. So
    # the door RK93 built existed and the projects that most needed it could not reach it.
    config = planning(tmp_path)
    added = task(config, section=("A design", "Because the gate said so."))
    assert added.needs is None and added.section is not None
    written = plan(config)
    assert "### §RK2 A design\n\nBecause the gate said so.\n" in written
    assert written.index("§RK2") > written.index("## Block B")
    assert added.rendered in source(config)  # one transaction, both files


def test_declaring_both_roles_still_writes_where_the_default_points(tmp_path):
    # Derived and never a flag on `add`: the role is already said in `section add --role`,
    # and a project declaring both has a choice its author makes by taking that route.
    config = planning(tmp_path, improvements=DESIGN)
    assert task(config, section=("A design", "Because the gate said so.")).section is not None
    assert "### §RK2 A design" in design(config)
    assert plan(config) == PLANNED  # untouched, and never a second copy of one anchor


def test_the_report_names_the_file_the_write_chose(tmp_path, capsys):
    # A report composed from the improvements default is a second answer to a question the
    # write already resolved, and on this project it is the wrong one (RK196).
    planning(tmp_path)
    argv = [
        "-C", str(tmp_path), "add", "--block", "B",
        "--symptom", "A second symptom", "--why", "Because of another.",
        "--section", "A design", "--section-body", "Because the gate said so.",
    ]
    assert main(argv) == EXIT_OK
    out = capsys.readouterr().out
    assert "design   §RK2 → docs/STRATEGY.md:" in out and "IMPROVEMENTS" not in out
    assert main([*argv, "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["section"]["file"] == "docs/STRATEGY.md"


def test_a_project_declaring_no_prose_file_is_told_about_every_role(tmp_path):
    # The refusal that remains, and it no longer asks for the second prose file a project
    # declaring one has no use for.
    config = project(tmp_path)
    with pytest.raises(NoProseFile, match="'improvements' or 'strategy'"):
        task(config, section=("A design", "Because of a reason."))
    assert source(config) == BODY


def test_a_section_on_a_line_with_no_pointer_is_refused(tmp_path):
    # A project that made the pointer optional (RK66) and wrote a line without one: the
    # prose would be reachable from nothing, so there is no section to write.
    config = project(
        tmp_path,
        declares=('ref_scheme = "outline"', "[rules.roadmap]", "ref = false"),
        prose=DESIGN,
    )
    with pytest.raises(NoAnchor):
        task(config, section=("A design", "Because of a reason."))
    assert source(config) == BODY


def test_the_command_writes_both_files_and_reports_both(tmp_path, capsys):
    config = project(tmp_path, prose=DESIGN)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
                "--section",
                "A design",
                "--section-body",
                "Because the gate said so.",
            ]
        )
        == EXIT_OK
    )
    line, reported, event = capsys.readouterr().out.splitlines()
    assert line.endswith("→ §RK2")
    assert reported.startswith(f"design   §RK2 → {IMPROVEMENTS}:")
    assert reported.endswith("5 words")
    assert "Because the gate said so." in design(config)
    assert event == "event    RK2  Block B  open"


def test_the_command_names_the_follow_up_it_leaves_behind(tmp_path, capsys):
    project(tmp_path, prose=DESIGN)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
            ]
        )
        == EXIT_OK
    )
    _, follow, event = capsys.readouterr().out.splitlines()
    assert follow.startswith("needs    section add RK2 --title")
    assert event == "event    RK2  Block B  open"


def test_json_carries_the_section_and_the_follow_up_as_fields(tmp_path, capsys):
    project(tmp_path, prose=DESIGN)
    argv = [
        "-C",
        str(tmp_path),
        "add",
        "--block",
        "B",
        "--symptom",
        "A second symptom",
        "--why",
        "Because of another reason.",
        "--json",
    ]
    assert main(argv) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["section"] is None
    assert payload["needs"].startswith("section add RK2 --title")

    assert main([*argv, "--section", "A design", "--section-body", "A reason."]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["needs"] is None
    assert payload["section"]["anchor"] == "RK3"
    assert payload["section"]["file"] == IMPROVEMENTS


def test_the_prose_arrives_on_stdin_when_only_a_title_is_given(tmp_path, capsys, monkeypatch):
    config = project(tmp_path, prose=DESIGN)
    monkeypatch.setattr("sys.stdin", io.StringIO("Because the gate said so."))
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
                "--section",
                "A design",
            ]
        )
        == EXIT_OK
    )
    assert "Because the gate said so." in design(config)


# -- the paragraph a refusal must not spend (RK381) ---------------------------


class _Unread:
    """A pipe that fails the test if anything drains it.

    The assertion cannot be made after the fact — a drained pipe and an unread one leave the
    same files behind, which is exactly why this was invisible until it was measured against a
    real corpus. So the pipe itself is what reports it.
    """

    def __init__(self) -> None:
        self.text = "A paragraph that costs real tokens to compose, and to send again."

    def read(self) -> str:
        raise AssertionError(
            "the body was read off stdin before the line's own fields had passed: a pipe "
            "does not rewind, so this refusal costs the paragraph a second time (RK381)"
        )


def test_a_refusal_on_a_short_field_never_reaches_the_pipe(tmp_path, capsys, monkeypatch):
    # Measured against Turing: `--why` 15 characters over a limit of 200, and acting on the
    # refusal meant resending a 184-word heredoc unchanged to correct three words in a
    # different argument. Every refusal the line can raise happens above the read now.
    project(tmp_path, prose=DESIGN)
    monkeypatch.setattr("sys.stdin", _Unread())
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of a reason that runs on well past the two hundred characters this "
                "field is allowed, which is the ordinary way to trip it: one clause too many "
                "in a sentence that was otherwise saying the right thing about the defect.",
                "--section",
                "A design",
            ]
        )
        == EXIT_USAGE
    )
    assert "why.too-long" in capsys.readouterr().err


def test_a_block_nothing_declares_is_the_same_refusal_one_field_over(tmp_path, monkeypatch):
    # Not only the length rules: the id, the block and the rendered line are all decided
    # above the read, so the property is the ordering rather than a list of codes.
    project(tmp_path, prose=DESIGN)
    monkeypatch.setattr("sys.stdin", _Unread())
    with pytest.raises(UnknownBlock):
        add(
            Config.discover(tmp_path),
            block="Z",
            symptom="A second symptom",
            why="Because of another reason.",
            section=("A design", _Unread().read),
        )


def test_the_pipe_is_still_what_an_omitted_body_reaches(tmp_path, capsys, monkeypatch):
    # The ordering changes when the paragraph is fetched and nothing else: an `add` whose
    # fields pass still reads the pipe, which is the affordance every heredoc caller uses.
    config = project(tmp_path, prose=DESIGN)
    monkeypatch.setattr("sys.stdin", io.StringIO("Because the gate said so, by pipe."))
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
                "--section",
                "A design",
            ]
        )
        == EXIT_OK
    )
    assert "Because the gate said so, by pipe." in design(config)


def test_a_body_named_by_path_survives_the_retry(tmp_path, capsys, monkeypatch):
    # The half the ordering cannot reach: `sections.add` reports every violation at once, so
    # its anchor and title checks cannot be split from the body's — and there a path is what
    # makes the second attempt cost the corrected field alone.
    config = project(tmp_path, prose=DESIGN)
    body = tmp_path / "body.md"
    body.write_text("The rationale, drafted before it was filed.\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", _Unread())
    argv = [
        "-C",
        str(tmp_path),
        "add",
        "--block",
        "B",
        "--symptom",
        "A second symptom",
        "--section",
        "A design",
        "--section-body-file",
        str(body),
        "--why",
    ]
    assert main([*argv, "A why with no full stop"]) == EXIT_USAGE
    capsys.readouterr()

    # The same argv with the sentence corrected, and the file re-read: nothing about the
    # paragraph was resent, which is the whole saving.
    assert main([*argv, "Because of another reason."]) == EXIT_OK
    assert "The rationale, drafted before it was filed." in design(config)


def test_naming_the_prose_and_the_path_it_is_in_is_refused(tmp_path, capsys):
    # Two answers to one question. Honouring either silently is how a caller comes to believe
    # the file is what landed, which is worse than the refusal: the wrong prose is in the file
    # and the command said it worked.
    project(tmp_path, prose=DESIGN)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
                "--section",
                "A design",
                "--section-body",
                "Inline prose.",
                "--section-body-file",
                str(tmp_path / "body.md"),
            ]
        )
        == EXIT_USAGE
    )
    assert "two answers to one question" in capsys.readouterr().err


def test_the_dash_is_refused_at_this_door_too(tmp_path, capsys, monkeypatch):
    # RK406: the same rule at the other pair, and the refusal is about argv — the pipe this
    # command would otherwise have read is never opened.
    config = project(tmp_path, prose=DESIGN)
    monkeypatch.setattr("sys.stdin", _Unread())
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
                "--section",
                "A design",
                "--section-body-file",
                "-",
            ]
        )
        == EXIT_USAGE
    )
    assert "already comes from stdin unless a path is given" in capsys.readouterr().err
    assert source(config) == BODY


def test_a_path_that_is_not_there_is_refused_like_any_other_bad_input(tmp_path, capsys):
    project(tmp_path, prose=DESIGN)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "Because of another reason.",
                "--section",
                "A design",
                "--section-body-file",
                str(tmp_path / "nothing-here.md"),
            ]
        )
        == EXIT_USAGE
    )
    assert "nothing-here.md" in capsys.readouterr().err


def test_a_file_and_the_why_on_the_pipe_are_not_a_clash(tmp_path, capsys, monkeypatch):
    # `--why -` and an omitted `--section-body` are two arguments reaching one pipe and are
    # refused (RK329). A body named by path is not on the pipe at all, so the sentence may be.
    config = project(tmp_path, prose=DESIGN)
    body = tmp_path / "body.md"
    body.write_text("The rationale, from a file.\n", encoding="utf-8")
    monkeypatch.setattr("sys.stdin", io.StringIO("Because a shell would eat the backtick.\n"))
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "B",
                "--symptom",
                "A second symptom",
                "--why",
                "-",
                "--section",
                "A design",
                "--section-body-file",
                str(body),
            ]
        )
        == EXIT_OK
    )
    assert "Because a shell would eat the backtick." in source(config)
    assert "The rationale, from a file." in design(config)


# -- the field's two names (RK399) -------------------------------------------


def test_the_open_marker_answers_to_both_names_on_every_verb_that_takes_it():
    """One declared field, spelled `--status` on two verbs and `--marker` on two others.

    A caller who learned the name on one got `unrecognized arguments` from the other, which
    is argparse saying the field does not exist rather than that this verb has a synonym for
    it — and the skill, `[markers]` and every refusal say *marker*, so the guess that fails
    is the informed one.
    """
    from roadkeep.cli import build_parser

    parser = build_parser()
    for command, dest in (
        ("add", "status"),
        ("budget", "status"),
        ("list", "marker"),
        ("resume", "marker"),
    ):
        flags = {
            option
            for action in _subparser(parser, command)._actions  # noqa: SLF001
            for option in action.option_strings
            if option in ("--status", "--marker")
        }
        assert flags == {"--status", "--marker"}, command
        # And both write the destination that verb's handler already reads: a helper that
        # renamed the field on two of the four would be this defect through its own repair.
        for spelled in ("--status", "--marker"):
            args = _parse(parser, command, spelled)
            assert getattr(args, dest) == "💭", (command, spelled)


def _subparser(parser, command):
    for action in parser._subparsers._group_actions:  # noqa: SLF001
        if command in action.choices:
            return action.choices[command]
    raise AssertionError(f"no subcommand {command}")


def _parse(parser, command, spelled):
    #: The positional each verb needs before its flags are legal.
    required = {
        "add": ["--block", "A", "--symptom", "s", "--why", "w."],
        "budget": ["--block", "A"],
        "list": [],
        "resume": ["RK1"],
    }[command]
    return parser.parse_args([command, *required, spelled, "💭"])
