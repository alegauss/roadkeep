"""Every write emits the event, and the tool's part ends there (RK38).

One shape from three commands, because a payload a hook has to special-case per command
is a payload nobody parses. The fact worth emitting is the one nothing else can derive
after the write: **whether that block still holds an open line** — which is how "Block B
is finished" reaches a `PostToolUse` hook (RK22) or the Action (RK17) without the tool
learning what to do next.

What is deliberately absent is a listener. A `[hooks]` table that ran commands after a
write would make `uvx roadkeep` in someone else's CI an executor of whatever their repo
declares, and one that called a model would make the tool a prose writer by proxy (L4).
"""

from __future__ import annotations

import json
from pathlib import Path

from roadkeep.cli import EXIT_OK, EXIT_USAGE, main
from roadkeep.config import Config
from roadkeep.provenance import invocation

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"

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
    assert capsys.readouterr().out.splitlines()[-1] == "event    RK3  Block A  open"


def test_status_emits_the_event(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK1", "🛠"]) == EXIT_OK
    assert capsys.readouterr().out.splitlines()[-1] == "  event    RK1  Block A  open"


def test_ship_emits_the_event(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "RK1", "--why", "It works now."]) == EXIT_OK
    out = capsys.readouterr().out.splitlines()
    assert out[-2] == "  event    RK1  Block A  empty"
    # And the verb that state makes available (RK408): `empty` is the one moment a heading
    # becomes droppable, and the answer used to stop one word short of saying so.
    assert f"{invocation()} block drop A" in out[-1]


# -- the fact that is worth emitting -----------------------------------------


def test_the_block_reads_empty_only_when_its_last_line_goes(tmp_path, capsys):
    # Two lines in Block B: the first ship leaves it open, the second finishes it. This
    # is the whole reason the payload exists — nothing else can tell the two apart
    # without re-reading the file the command just wrote.
    project(tmp_path, roadmap=BACKLOG + f"{SECOND.replace('RK2', 'RK4')}\n")
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "It works now."]) == EXIT_OK
    assert capsys.readouterr().out.splitlines()[-1] == "  event    RK2  Block B  open"
    assert main(["-C", str(tmp_path), "ship", "RK4", "--why", "It works now."]) == EXIT_OK
    assert capsys.readouterr().out.splitlines()[-2] == "  event    RK4  Block B  empty"


def test_a_status_write_never_empties_a_block(tmp_path, capsys):
    project(tmp_path)
    assert main(["-C", str(tmp_path), "status", "RK1", "⏳"]) == EXIT_OK
    assert "Block A  open" in capsys.readouterr().out


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
    assert json.loads(capsys.readouterr().out)["event"] == {
        "id": "RK3",
        "block": "A",
        "block_empty": False,
    }

    assert main(["-C", str(tmp_path), "status", "RK1", "🛠", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["event"] == {
        "id": "RK1",
        "block": "A",
        "block_empty": False,
    }

    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "It works now.", "--json"]) == EXIT_OK
    assert json.loads(capsys.readouterr().out)["event"] == {
        "id": "RK2",
        "block": "B",
        "block_empty": True,
    }


def test_an_open_block_is_offered_no_verb_it_would_be_refused(tmp_path, capsys):
    # The suggestion is bounded to the state that makes it available (RK408): a block still
    # holding a line is one `block drop` refuses by name, and offering it there would teach
    # a command that answers with a refusal — which is how a guardrail becomes a detour.
    project(tmp_path, roadmap=BACKLOG + f"{SECOND.replace('RK2', 'RK4')}\n")
    assert main(["-C", str(tmp_path), "ship", "RK2", "--why", "It works now."]) == EXIT_OK
    out = capsys.readouterr().out
    assert out.splitlines()[-1] == "  event    RK2  Block B  open"
    assert "block drop" not in out


def test_the_payload_is_unchanged_by_the_sentence(tmp_path, capsys):
    # `--json` carries `block_empty` and nothing else new: the suggestion is a sentence for
    # a reader, and a consumer that already derives the next command from the boolean would
    # be handed a second spelling of the same fact (RK38's three facts and no more).
    project(tmp_path)
    assert main(["-C", str(tmp_path), "ship", "--json", "RK1", "--why", "Works."]) == EXIT_OK
    payload = json.loads(capsys.readouterr().out)
    assert payload["event"] == {"id": "RK1", "block": "A", "block_empty": True}
