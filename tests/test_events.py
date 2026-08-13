"""Every write emits the event, and the tool's part ends there (RK38).

One shape from three commands, because a payload a hook has to special-case per command
is a payload nobody parses. The fact worth emitting is the one nothing else can derive
after the write: **what became of that block** — which is how "Block B is finished"
reaches a `PostToolUse` hook (RK22) or the Action (RK17) without the tool learning what to
do next. A boolean about the roadmap alone since RK438: `finished`, `paused` and `empty`
are three different answers to "nothing is open here", and the one word they shared sent a
paused block at a `block drop` that refuses it.

What is deliberately absent is a listener. A `[hooks]` table that ran commands after a
write would make `uvx roadkeep` in someone else's CI an executor of whatever their repo
declares, and one that called a model would make the tool a prose writer by proxy (L4).
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config, ConfigError
from roadkeep.provenance import invocation

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
#: Declared only by the one test that needs a block to reach `paused` (RK438) — the state
#: the old boolean could not tell from `finished`, both leaving the roadmap holding nothing.
DEFERRED = "docs/DEFERRED.md"

ONLY = "- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1"
SECOND = "- 📋 **RK2** (deps: —) **A second symptom** — Because of another reason. → §RK2"

BACKLOG = f"""# Roadmap

## Block A — The model

{ONLY}

## Block B — Authoring

{SECOND}
"""

LEDGER = """# Shipped

## Block A — The model

## Block B — Authoring
"""


def project(tmp_path: Path, *, roadmap: str = BACKLOG) -> Config:
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n',
        encoding="utf-8",
    )
    for name, body in {ROADMAP: roadmap, CHANGELOG: LEDGER}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return Config.discover(tmp_path)


# -- the same three facts, from every mutator --------------------------------


def test_add_emits_the_event(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "A",
                "--symptom",
                "A third symptom",
                "--why",
                "Because of a third reason.",
            ]
        )
        == EXIT_OK
    )
    assert capsys.readouterr().out.splitlines()[-1] == "event    RK3  Block A  live"


def test_status_emits_the_event(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK1", "🛠"]) == EXIT_OK
    assert capsys.readouterr().out.splitlines()[-1] == "  event    RK1  Block A  live"


def test_ship_emits_the_event(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert out[-3] == "  event    RK1  Block A  finished"
    # What is left, on the line under it (RK1164): this is the verb a caller drives a block
    # with, and the `list` that used to follow every ship asked what this line answers.
    assert out[-2] == "           Block A is finished: nothing open, and the ledger records 1 filed under it"
    # And the verb that state makes available (RK408): a block that stopped holding work is
    # the one moment a heading becomes droppable, and the answer used to stop one word short
    # of saying so. `finished` and not `empty` (RK438): the ledger now records the line.
    assert f"{invocation()} block drop A" in out[-1]


# -- the fact that is worth emitting -----------------------------------------


def test_the_block_settles_only_when_its_last_line_goes(tmp_path, capsys):
    # Two lines in Block B: the first ship leaves it open, the second finishes it. This
    # is the whole reason the payload exists — nothing else can tell the two apart
    # without re-reading the file the command just wrote.
    project(tmp_path, roadmap=BACKLOG + f"{SECOND.replace('RK2', 'RK4')}\n")
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "It works now."]) == EXIT_OK
    said = capsys.readouterr().out.splitlines()
    assert said[-2] == "  event    RK2  Block B  live"
    # The live count, which is the case that cost the second call (RK1164).
    assert said[-1] == "           Block B has 1 open"
    assert main(["-C", str(tmp_path), "ship", "RK4", "--why", "It works now."]) == EXIT_OK
    assert capsys.readouterr().out.splitlines()[-3] == "  event    RK4  Block B  finished"


def test_a_status_write_never_settles_a_block(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK1", "⏳"]) == EXIT_OK
    assert "Block A  live" in capsys.readouterr().out


def test_a_refusal_emits_nothing(tmp_path, capsys):
    # The event describes a write. A refusal changed nothing, so there is nothing to
    # react to, and an event on stderr would be a write a hook then looked for in vain.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK9", "🛠"]) == EXIT_USAGE
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "event" not in captured.err


# -- the machine-readable form -----------------------------------------------


def test_json_carries_the_event_from_every_mutator(tmp_path, capsys):
    project(tmp_path)
    assert (
        main(
            [
                "-C",
                str(tmp_path),
                "add",
                "--block",
                "A",
                "--symptom",
                "A third symptom",
                "--why",
                "Because of a third reason.",
                "--json",
            ]
        )
        == EXIT_OK
    )
    event = json.loads(capsys.readouterr().out)["event"]
    assert (event["id"], event["block"], event["stage"]) == ("RK3", "A", "live")
    # Every mutator's event carries the standing since RK1164, printed by the two a caller
    # drives a block with: a key costs a client nothing to skip, where a line costs a reader.
    assert event["standing"]["open"] == 2

    assert main(["-C", str(tmp_path), "status", "RK1", "🛠", "--json"]) == EXIT_OK
    moved = json.loads(capsys.readouterr().out)["event"]
    assert (moved["id"], moved["block"], moved["stage"]) == ("RK1", "A", "live")
    assert moved["standing"]["open"] == 2

    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "It works now.", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["event"] == {
        "id": "RK2",
        "block": "B",
        "stage": "finished",
        "standing": {
            "block": "B",
            "state": "finished",
            "sentence": "Block B is finished: nothing open, and the ledger records 1 filed under it",
            "open": 0,
            "recorded": 1,
            "paused": 0,
        },
    }


def test_an_open_block_is_offered_no_verb_it_would_be_refused(tmp_path, capsys):
    # The suggestion is bounded to the state that makes it available (RK408): a block still
    # holding a line is one `block drop` refuses by name, and offering it there would teach
    # a command that answers with a refusal — which is how a guardrail becomes a detour.
    project(tmp_path, roadmap=BACKLOG + f"{SECOND.replace('RK2', 'RK4')}\n")
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "It works now."]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.splitlines()[-2] == "  event    RK2  Block B  live"
    assert "block drop" not in out


# -- the word the two questions were sharing (RK438) -------------------------


def test_a_finished_block_is_not_called_the_word_an_unfilled_one_answers_to(tmp_path, capsys):
    """The defect: shipping the last line of a block printed `empty` beside an offer to
    withdraw the heading, while `pick --block` on the same label answered `is finished: the
    ledger records N filed under it`. Both were right about their own question, and one word
    was carrying two of them — so the event asks for the state the tool already computes."""
    project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Block A  finished" in out and "Block A  empty" not in out
    assert f"{invocation()} block drop A" in out
    # And the other reader says the same word about the same label.
    assert main(["-C", str(tmp_path), "pick", "--block", "A"]) == EXIT_OK
    assert "Block A is finished" in capsys.readouterr().out


def test_a_paused_block_is_offered_no_verb_that_would_refuse_it(tmp_path, capsys):
    """The boolean could not tell this apart from `finished`: both leave the roadmap holding
    no line under the label. The deferred store still files one there, so `block drop` refuses
    — and naming an edit that cannot work is worse than naming no edit at all (RK16)."""
    project(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
        f'deferred = "{DEFERRED}"\n',
        encoding="utf-8",
    )
    with (tmp_path / DEFERRED).open("w", encoding="utf-8", newline="") as handle:
        handle.write(LEDGER.replace("# Shipped", "# Deferred"))
    assert main(["-C", str(tmp_path), "defer", "RK1", "--reason", "Waiting on a decision."]) == EXIT_OK
    out = capsys.readouterr().out
    assert "Block A  paused" in out
    assert "block drop" not in out


def test_the_payload_is_unchanged_by_the_sentence(tmp_path, capsys):
    # `--json` carries no spelling of the **suggestion**: that is a sentence for a reader, and a
    # consumer deriving the next command from the stage would be handed it twice (RK38's three
    # facts and no more). What it does carry since RK1164 is the standing — the counts a caller
    # asked `list` for after every ship, which is a fact about the files and not a suggestion.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "--json", "RK1", "--why", "Works."]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert set(payload["event"]) == {"id", "block", "stage", "standing"}
    assert payload["event"]["stage"] == "finished"
    assert "block drop" not in json.dumps(payload)


# -- the offer a project may answer once (RK1121) ------------------------------


def permanent(tmp_path: Path) -> None:
    """`[headings] permanent` on the fixture above, declared after the files are written."""
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
        "[headings]\npermanent = true\n",
        encoding="utf-8",
    )


def test_a_project_whose_headings_are_permanent_is_offered_no_door(tmp_path, capsys):
    """RK1121. Measured in this repository: nine ships in one session printed the offer six
    times — D, B, F, B, C, E — and no block has ever been dropped. The offer's own clause said
    `where this project drops one`, which is the sentence knowing the answer it cannot read."""
    project(tmp_path)
    permanent(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    out = capsys.readouterr().out
    # The state is still stated: what emptied is a fact, and only the suggestion was a question.
    assert "Block A  finished" in out
    assert "block drop" not in out and "withdraws the heading" not in out


def test_the_declaration_changes_no_payload(tmp_path, capsys):
    # Three facts and no more (RK38): the flag decides whether a sentence is printed, so a
    # consumer that derives its own next command from the stage reads the same event either way.
    project(tmp_path)
    permanent(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "--json", "RK1", "--why", "Works."]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert (payload["event"]["stage"], payload["event"]["block"]) == ("finished", "A")
    assert "block drop" not in json.dumps(payload)


def test_a_project_that_says_nothing_is_still_offered_the_door(tmp_path, capsys):
    # Off by default, so nothing changes for a backlog whose headings group live work.
    project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    assert f"{invocation()} block drop A" in capsys.readouterr().out


def test_the_flag_has_to_be_a_flag(tmp_path):
    # Refused where it is typed, like every other value in this table.
    project(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\n[headings]\npermanent = "yes"\n',
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="headings.permanent must be true or false"):
        Config.discover(tmp_path)


def test_the_word_and_the_flag_live_in_one_table(tmp_path):
    # `[headings]` is the table about the heading a project files work under (RK75), and
    # whether that heading outlives the work is the same subject.
    project(tmp_path)
    (tmp_path / "roadkeep.toml").write_text(
        f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\n'
        '[headings]\nword = "Track"\npermanent = true\n',
        encoding="utf-8",
    )
    config = Config.discover(tmp_path)
    assert config.schema.heading_word == "Track" and config.permanent_headings


def test_this_repository_declares_its_own_headings_permanent():
    # The conformance fixture again: the seven blocks here are the shape of the backlog, and
    # the measurement that produced the flag was taken on this file's own ships.
    root = Path(__file__).resolve().parents[1]
    assert Config.discover(root).permanent_headings
