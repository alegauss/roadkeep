"""The verdict a person leaves on a shipped entry, and the one door to it (RK1690).

Done when an entry carries a verdict, a second `validate` replaces it rather than adding one,
and a token outside the set is refused — each held below against a throwaway project, and the
line the write composes held against the reader beside it.
"""

from __future__ import annotations

import contextlib
import io
import json
from pathlib import Path

import pytest

from composing import runs
from conftest import git_commit, git_init

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError
from roadkeep.kernel.schema import SchemaError
from roadkeep.linting import lint
from roadkeep.validating import (
    VERDICT,
    VERDICTS,
    NoStart,
    Unshipped,
    is_verdict_line,
    looked,
    read_verdict,
    unvalidated,
    validate,
    verdict_line,
)

ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK3** (deps: —) **An open symptom** — Because it is still open. → §RK3
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK1** **A first symptom** — It works.
  checked **It opens** Because it does.
- ✅ **RK2** **A second symptom** — It works too.
- 🗑 **RK4** **A retired symptom** — abandoned: The work is not coming back.
"""

IMPROVEMENTS = """# Improvements

## Block A — The model

### §RK3 An open design

The reasoning.
"""


def project(tmp_path: Path, *, ledger: str = LEDGER) -> Config:
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "docs/ROADMAP.md"\n'
        'changelog = "docs/CHANGELOG.md"\nimprovements = "docs/IMPROVEMENTS.md"\n',
        encoding="utf-8",
    )
    for name, body in (
        ("ROADMAP.md", ROADMAP),
        ("CHANGELOG.md", ledger),
        ("IMPROVEMENTS.md", IMPROVEMENTS),
    ):
        with (tmp_path / "docs" / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


def ledger_of(config: Config) -> str:
    with (config.root / "docs" / "CHANGELOG.md").open(encoding="utf-8", newline="") as handle:
        return handle.read()


# -- the line, and its reader ------------------------------------------------


def test_the_line_the_writer_composes_is_the_line_the_reader_recognises():
    """RK1507's pairing, for the second derived word: a change to either is a red here."""
    for verdict in VERDICTS:
        line = verdict_line(verdict, "Opened it and\n  it was there.")
        assert is_verdict_line(line)
        read = read_verdict(line)
        assert read is not None
        assert (read.verdict, read.saw) == (verdict, "Opened it and it was there.")
    assert not is_verdict_line("  checked **It opens** Because it does.")
    assert read_verdict("- ✅ **RK1** **A symptom** — It works.") is None


# -- done when ---------------------------------------------------------------


def test_an_entry_carries_the_verdict_as_its_last_line(tmp_path):
    config = project(tmp_path)
    written = validate(config, "RK1", "worked", saw="Opened it and it was there.")
    assert written.save()
    text = ledger_of(config)
    assert (
        "- ✅ **RK1** **A first symptom** — It works.\n"
        "  checked **It opens** Because it does.\n"
        "  validated **worked** Opened it and it was there.\n"
        "- ✅ **RK2**"
    ) in text
    # Owned by the entry, not by the one after it, and a file the gate still reads clean.
    entry = config.document("changelog").by_id()["RK1"]
    assert entry.stop - entry.index == 3
    assert lint(config).clean


def test_a_second_verdict_replaces_the_first_rather_than_adding_one(tmp_path):
    config = project(tmp_path)
    validate(config, "RK2", "worked", saw="It looked right.").save()
    second = validate(config, "RK2", "failed", saw="The second open came back empty.")
    second.save()
    text = ledger_of(config)
    assert text.count("validated **") == 1
    assert "  validated **failed** The second open came back empty.\n" in text
    assert second.replaced == "worked"
    assert second.lineno == 8


def test_the_same_verdict_twice_writes_nothing(tmp_path):
    config = project(tmp_path)
    validate(config, "RK2", "nothing to see", saw="A refactor.").save()
    before = ledger_of(config)
    again = validate(config, "RK2", "nothing to see", saw="A refactor.")
    assert not again.changed
    assert again.save() == ()
    assert ledger_of(config) == before


def test_a_token_outside_the_set_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError) as refused:
        validate(config, "RK1", "great", saw="It was great.")
    assert [one.code for one in refused.value.violations] == [VERDICT]
    # And at the parser, which reads the same set rather than a copy of it.
    with contextlib.redirect_stderr(io.StringIO()):
        with pytest.raises(SystemExit) as parsed:
            main(["-C", str(tmp_path), "validate", "RK1", "great", "--saw", "It was."])
    assert parsed.value.code == EXIT_USAGE
    assert "validated" not in ledger_of(config)


# -- the refusals ------------------------------------------------------------


def test_a_sentence_nobody_wrote_or_one_past_the_limit_is_refused(tmp_path):
    config = project(tmp_path)
    with pytest.raises(SchemaError):
        validate(config, "RK1", "worked", saw="   ")
    with pytest.raises(SchemaError) as long:
        validate(config, "RK1", "worked", saw="word " * 60)
    assert "limit is 200" in str(long.value.violations[0])


@pytest.mark.parametrize(
    ("task_id", "because"),
    [
        ("RK3", "is still open"),
        ("RK4", "was retired"),
        ("RK9", "is not in docs/CHANGELOG.md"),
    ],
)
def test_work_nothing_shipped_is_refused(tmp_path, task_id, because):
    config = project(tmp_path)
    with pytest.raises(Unshipped) as refused:
        validate(config, task_id, "worked", saw="It worked.")
    assert because in str(refused.value)


DOUBLED = LEDGER.replace(
    "- ✅ **RK2** **A second symptom** — It works too.\n",
    "- ✅ **RK2** **A second symptom** — It works too.\n"
    "  validated **worked** Once.\n"
    "  validated **failed** Twice.\n",
)


def test_an_entry_already_holding_two_verdicts_collapses_to_the_one_written(tmp_path):
    """RK1693. Which of the two was the last is not a fact the file holds, and it need not be:
    the call being made now is the latest verdict, so it is written over both."""
    config = project(tmp_path, ledger=DOUBLED)
    written = validate(config, "RK2", "worked", saw="A third time.")
    written.save()
    text = ledger_of(config)
    assert text.count("validated **") == 1
    assert (
        "- ✅ **RK2** **A second symptom** — It works too.\n"
        "  validated **worked** A third time.\n- 🗑 **RK4**"
    ) in text
    assert written.lineno == 8


def test_a_hand_wrapped_entry_keeps_its_prose_and_gains_the_verdict_under_it(tmp_path):
    wrapped = LEDGER.replace(
        "- ✅ **RK2** **A second symptom** — It works too.\n",
        "- ✅ **RK2** **A second symptom** — It works too.\n  A paragraph somebody wrote.\n",
    )
    config = project(tmp_path, ledger=wrapped)
    validate(config, "RK2", "worked", saw="It did.").save()
    assert (
        "  A paragraph somebody wrote.\n  validated **worked** It did.\n- 🗑 **RK4**"
        in ledger_of(config)
    )


# -- the verb ----------------------------------------------------------------


def test_the_served_schema_publishes_the_set_and_the_ledger_s_limit(tmp_path):
    """The set is the one thing an agent would otherwise guess, so the client gets it whole."""
    from roadkeep.serving import TOOLS, descriptor

    tool = next(one for one in TOOLS if one.name == "validate")
    properties = descriptor(tool, project(tmp_path))["inputSchema"]["properties"]
    assert properties["verdict"]["enum"] == list(VERDICTS)
    assert properties["saw"]["maxLength"] == 200


def test_the_verb_answers_in_both_registers(tmp_path):
    project(tmp_path)
    said = io.StringIO()
    with contextlib.redirect_stdout(said):
        assert main(["-C", str(tmp_path), "validate", "RK1", "worked", "--saw", "It did."]) == EXIT_OK
    assert "RK1 validated  docs/CHANGELOG.md:7  worked" in said.getvalue()
    assert "git add -- docs/CHANGELOG.md" in said.getvalue()

    payload = io.StringIO()
    with contextlib.redirect_stdout(payload):
        argv = ["validate", "RK1", "nothing to see", "--saw", "No surface.", "--json"]
        assert main(["-C", str(tmp_path), *argv]) == EXIT_OK
    answer = json.loads(payload.getvalue())
    assert answer["verdict"] == "nothing to see"
    assert answer["replaced"] == "worked"
    assert answer["line"] == 7
    assert answer["wrote"] == ["docs/CHANGELOG.md"]


# -- the read: what nobody has looked at (RK1691) -----------------------------


def asking(tmp_path: Path, *, ledger: str = LEDGER, start: str | None = "RK1") -> Config:
    """A project that asks the question from `start`, committed so the start can be placed."""
    project(tmp_path, ledger=ledger)
    declared = "[validation]\n" + ("" if start is None else f'from = "{start}"\n')
    with (tmp_path / "roadkeep.toml").open("a", encoding="utf-8", newline="") as handle:
        handle.write(declared)
    git_init(tmp_path)
    git_commit(tmp_path, "the project, asking")
    return Config.discover(tmp_path)


def test_a_ledger_with_one_verdict_and_two_without_answers_with_the_two(tmp_path):
    """RK1691's done-when, and the two it leaves out are the ones `validate` refuses."""
    ledger = LEDGER + "- ✅ **RK5** **A fifth symptom** — It works as well.\n"
    config = asking(tmp_path, ledger=ledger)
    validate(config, "RK1", "worked", saw="It did.").save()
    answer = unvalidated(config)
    assert [one.task_id for one in answer.rows] == ["RK2", "RK5"]
    assert answer.validated == 1
    # The counts `stats` carries are the list's own, never a second walk that could disagree.
    counts = looked(config)
    assert counts is not None
    assert (counts.validated, counts.unvalidated) == (1, len(answer.rows))
    assert "2 of 3 entr(ies) shipped from RK1 carry no verdict" in answer.stated()


def test_the_list_narrows_to_a_block_and_refuses_one_the_ledger_lacks(tmp_path):
    config = asking(tmp_path)
    assert [one.task_id for one in unvalidated(config, "A").rows] == ["RK1", "RK2"]
    with pytest.raises(KeyError, match="no heading declares Block ZZ"):
        unvalidated(config, "ZZ")


def test_the_verb_and_stats_answer_in_both_registers(tmp_path):
    asking(tmp_path)
    payload = io.StringIO()
    with contextlib.redirect_stdout(payload):
        assert main(["-C", str(tmp_path), "unvalidated", "--json"]) == EXIT_OK
    answer = json.loads(payload.getvalue())
    assert [one["id"] for one in answer["unvalidated"]] == ["RK1", "RK2"]
    assert (answer["governed"], answer["placed"], answer["from"]) == (True, True, "RK1")
    # The commit that first wrote the entry, which is what `origin` answers as where it shipped.
    assert len(answer["unvalidated"][0]["commit"]) == 40

    counted = io.StringIO()
    with contextlib.redirect_stdout(counted):
        assert main(["-C", str(tmp_path), "stats", "--json"]) == EXIT_OK
    assert json.loads(counted.getvalue())["validation"] == {"validated": 0, "unvalidated": 2}
    said = io.StringIO()
    with contextlib.redirect_stdout(said):
        assert main(["-C", str(tmp_path), "stats"]) == EXIT_OK
    rows = {line.split()[0]: line.split()[1:] for line in said.getvalue().splitlines()[1:]}
    assert rows["verdicts"] == ["0", "2", "without", "one"]


def test_the_door_under_the_list_runs_as_printed(tmp_path, capsys):
    """The one command `unvalidated` composes, executed rather than matched (RK1209): the id is
    the row's own and the verdict is the person's, so the harness supplies both and what proves
    the door is the line the write puts under the entry."""
    from composing import commands, filled, supplied

    config = asking(tmp_path)
    assert main(["-C", str(tmp_path), "unvalidated"]) == EXIT_OK
    said = capsys.readouterr().out
    (argv,) = [one for one in commands(said) if one[:1] == ["validate"]]
    chosen = {"<id>": "RK2", "<verdict>": "worked"}
    taken = supplied(filled([chosen.get(one, one) for one in argv]))
    assert main(["-C", str(tmp_path), *taken]) == EXIT_OK
    assert "  validated **worked** It was there when I looked.\n" in ledger_of(config)


# -- where looking starts (RK1692) ----------------------------------------------


def test_a_project_with_no_table_has_no_list(tmp_path, capsys):
    """Not an empty list: the question is not asked, and the answer names what asks it."""
    config = project(tmp_path)
    git_init(tmp_path)
    git_commit(tmp_path, "the project, not asking")
    answer = unvalidated(config)
    assert (answer.governed, answer.rows) == (False, ())
    assert looked(config) is None
    assert main(["-C", str(tmp_path), "stats", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["validation"] is None
    # And the door it names opens the question, from the next ship on.
    runs(tmp_path, answer.stated())
    assert "[validation]" in (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")


def test_a_declared_start_lists_only_what_followed_it(tmp_path):
    """Placed on the history and not on the file: RK5 ships into Block A, above RK2 in the
    file, and is still after it — and RK1, written in the same commit as RK2 but above it, is
    history the declaration named as such."""
    config = asking(tmp_path, start="RK2")
    ledger = ledger_of(config).replace(
        "- 🗑 **RK4**", "- ✅ **RK5** **A fifth symptom** — It works as well.\n- 🗑 **RK4**"
    )
    (tmp_path / "docs" / "CHANGELOG.md").write_text(ledger, encoding="utf-8", newline="")
    git_commit(tmp_path, "ship RK5")
    assert [one.task_id for one in unvalidated(Config.discover(tmp_path)).rows] == ["RK2", "RK5"]


def test_with_no_start_looking_begins_at_the_ship_after_the_table(tmp_path):
    project(tmp_path)
    git_init(tmp_path)
    git_commit(tmp_path, "the history")
    assert main(["-C", str(tmp_path), "declare", "validation"]) == EXIT_OK
    git_commit(tmp_path, "asking from here")
    config = Config.discover(tmp_path)
    assert unvalidated(config).rows == ()
    assert "nothing has shipped since [validation] was declared" in unvalidated(config).stated()
    # The next ship is in the question the moment it lands, committed or not.
    main(["-C", str(tmp_path), "record", "add", "--block", "A", "--symptom", "A later one",
          "--why", "It works."])
    assert [one.task_id for one in unvalidated(Config.discover(tmp_path)).rows] == ["RK5"]


def test_a_start_the_ledger_lacks_is_refused_and_one_that_is_no_id_at_config_read(tmp_path):
    asking(tmp_path, start="RK9")
    with pytest.raises(NoStart, match="validation.from names RK9"):
        unvalidated(Config.discover(tmp_path))
    text = (tmp_path / "roadkeep.toml").read_text(encoding="utf-8")
    (tmp_path / "roadkeep.toml").write_text(text.replace('"RK9"', '"banana"'), encoding="utf-8")
    with pytest.raises(ConfigError, match="validation.from: not an id"):
        Config.discover(tmp_path)


def test_with_no_history_the_start_is_not_placed_and_nothing_is_listed(tmp_path):
    project(tmp_path)
    with (tmp_path / "roadkeep.toml").open("a", encoding="utf-8") as handle:
        handle.write('[validation]\nfrom = "RK1"\n')
    answer = unvalidated(Config.discover(tmp_path))
    assert (answer.governed, answer.placed, answer.rows) == (True, False, ())
    assert "no history to read" in answer.stated()


def test_the_table_declared_twice_names_the_read_and_not_a_key_it_lacks(tmp_path, capsys):
    """The door `declare` prints for an open table was `govern <table>.lead`, which this table
    has no such key for — so it is the read of what the table carries, and it runs."""
    asking(tmp_path)
    assert main(["-C", str(tmp_path), "declare", "validation"]) == EXIT_USAGE
    said = capsys.readouterr().err
    assert "govern" not in said
    runs(tmp_path, said)




# -- the recogniser and the gate (RK1693) -------------------------------------


def test_an_entry_holding_a_verdict_is_corrected_with_no_span(tmp_path):
    """RK1693's done-when, the half about the recogniser: a verdict is this tool's line, so
    `record amend` keeps it and the `checked` line beside it without asking for `--lines`."""
    config = project(tmp_path)
    validate(config, "RK1", "worked", saw="It did.").save()
    assert main(["-C", str(tmp_path), "record", "amend", "RK1", "--why", "It works, now."]) == EXIT_OK
    # Written once each, with the next entry straight under them: the tail was handed back with
    # its endings on and written with a second one, which split an entry holding two.
    assert (
        "- ✅ **RK1** **A first symptom** — It works, now.\n"
        "  checked **It opens** Because it does.\n"
        "  validated **worked** It did.\n"
        "- ✅ **RK2**"
    ) in ledger_of(config)


def _reported(config: Config) -> dict[str, list[int | None]]:
    out: dict[str, list[int | None]] = {}
    for finding in lint(Config.discover(config.root)).findings:
        if finding.code.startswith("validation."):
            out.setdefault(finding.code, []).append(finding.lineno)
    return out


@pytest.mark.parametrize(
    ("typed", "code"),
    [
        ("  validated **great** It was great.\n", "validation.verdict"),
        ("  validated **worked**\n", "validation.saw"),
        ("  validated **worked** " + "word " * 60 + "\n", "validation.saw"),
    ],
    ids=["a-word-outside-the-set", "no-sentence", "a-sentence-past-the-limit"],
)
def test_a_hand_written_verdict_of_each_shape_is_reported_with_its_code(tmp_path, typed, code):
    ledger = LEDGER.replace("- 🗑 **RK4**", typed + "- 🗑 **RK4**")
    config = project(tmp_path, ledger=ledger)
    assert _reported(config) == {code: [8]}


def test_two_verdicts_and_one_under_an_open_line_are_reported(tmp_path):
    assert _reported(project(tmp_path, ledger=DOUBLED)) == {"validation.repeated": [9]}
    opened = LEDGER + "- ✅ **RK3** **An open symptom** — Half of it works.\n  validated **worked** It did.\n"
    assert _reported(project(tmp_path / "open", ledger=opened)) == {"validation.open": [10]}


def test_a_legal_verdict_is_not_a_finding_and_an_absent_one_never_is(tmp_path):
    """Unvalidated is a state and not a violation (RK1691): an entry shipped an hour ago is in
    it as its ordinary condition, so the gate has nothing to say about an entry with none."""
    config = project(tmp_path)
    assert _reported(config) == {}
    validate(config, "RK2", "nothing to see", saw="A refactor.").save()
    assert _reported(config) == {}
