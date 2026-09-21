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

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.kernel.schema import SchemaError
from roadkeep.linting import lint
from roadkeep.validating import (
    VERDICT,
    VERDICTS,
    Repeated,
    Unshipped,
    is_verdict_line,
    read_verdict,
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


def test_an_entry_already_holding_two_verdicts_is_refused_and_named(tmp_path):
    doubled = LEDGER.replace(
        "- ✅ **RK2** **A second symptom** — It works too.\n",
        "- ✅ **RK2** **A second symptom** — It works too.\n"
        "  validated **worked** Once.\n"
        "  validated **failed** Twice.\n",
    )
    config = project(tmp_path, ledger=doubled)
    with pytest.raises(Repeated) as refused:
        validate(config, "RK2", "worked", saw="A third time.")
    assert "lines 8, 9" in str(refused.value)


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
