"""A door the text names is a door the payload carries (RK1307).

Measured on quickshell, after QS12 shipped and took its own criteria with it. `criterion
list --task QS12` printed the whole answer to a person — which empty, and the command that
fills it — and the same call with `--json` returned `{"criteria": [], "blocks": [...]}` and
nothing else. The MCP tools serve the JSON, so every agent got strictly less than the
person at the terminal, and lost exactly the two things that verb is documented for.

RK1306 is the same shape one verb over: the shipping budget stated the ledger allowance and
not what the two clauses spend from it, which the refusal names perfectly once the write has
failed. Two occurrences is a class, and a class needs a gate rather than a third fix.

**What this holds is the asymmetry and never a list of verbs.** A test naming the four
calls that were wrong the day it was written is a test that passes while the fifth is being
added. So it walks the calls below in both registers, reads the commands out of the text,
and asserts each is reachable in the payload — and a verb added later joins by being added
to `CALLS`, which is the one line a reviewer can ask for.

Not every command in a sentence is a door. `anchors` says *765 addresses are task ids,
which `add` already refuses to reuse*, which names a verb and offers nothing to run. So a
door here is a command **with an argument**: an invocation-prefixed line, or a backticked
one carrying a space. That rule is what keeps this from demanding a payload key for every
verb this tool mentions in prose.
"""

from __future__ import annotations

import contextlib
import io
import json
import re
from pathlib import Path

import pytest

from roadkeep.cli import EXIT_OK, main
from roadkeep.provenance import invocation

#: Verbs this tool has, so a backticked fragment of prose is not read as a command. Read off
#: the parser rather than spelled, because a list written here is one that stops matching.
VERBS = frozenset(
    {
        "add", "amend", "anchors", "audit", "block", "brief", "budget", "claim", "claims",
        "config", "criterion", "declare", "defer", "delivered", "deps", "evidence",
        "explain", "export", "gaps", "govern", "guard", "install", "lint", "list", "merge",
        "non-goal", "origin", "pick", "priority", "record", "refs", "remaining", "renumber",
        "repair", "replay", "restate", "resume", "retire", "reversals", "section", "ship",
        "show", "stats", "status", "supersede", "unclosed", "weight", "writes",
    }
)

#: A door named the way the printers spell one. Two spellings and both take an argument: a
#: bare verb inside backticks is prose about a command, not an offer to run it.
_INVOKED = re.compile(rf"{re.escape(invocation())} ([a-z][a-z-]*(?: [^\s`]+)+)")
_BACKTICKED = re.compile(r"`([a-z][a-z-]*(?: [^`]+)+)`")

ROADMAP = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1

## Block B — Authoring

- 📋 **RK2** (deps: —) **A second symptom** — Because of another. → §RK2

## Non-goals

- **No web UI.** Files and a CLI.
"""

IMPROVEMENTS = """# Improvements

## Block A — The model

### §RK1 A design

Because the prose has to live somewhere.

### §RK2 A design

Because it points somewhere too.
"""

#: Every call whose text names a door. Each is `(argv, what it is about)`, and the second
#: half is what a failure prints: an id is not enough to find the sentence again.
CALLS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("criterion", "list", "--task", "RK1"), "which empty, and the command that fills it"),
    (("criterion", "list", "--block", "B"), "the same, addressed to a block"),
    (
        ("section", "find", "a sentence this corpus does not hold"),
        "the read that resolves a sentence to an anchor, when it resolves to none",
    ),
    (
        ("ship", "RK2", "--why", "It works now.", "--part", "local half"),
        "what to do with the half that is still open, and what closes the line",
    ),
)


def project(tmp_path: Path) -> Path:
    (tmp_path / "docs").mkdir(parents=True, exist_ok=True)
    (tmp_path / "roadkeep.toml").write_text(
        'prefix = "RK"\n[files]\nroadmap = "docs/ROADMAP.md"\n'
        'changelog = "docs/CHANGELOG.md"\nimprovements = "docs/IMPROVEMENTS.md"\n[criteria]\n',
        encoding="utf-8",
    )
    (tmp_path / "docs/ROADMAP.md").write_text(ROADMAP, encoding="utf-8")
    (tmp_path / "docs/CHANGELOG.md").write_text(
        "# Shipped\n\n## Block A — The model\n\n## Block B — Authoring\n", encoding="utf-8"
    )
    (tmp_path / "docs/IMPROVEMENTS.md").write_text(IMPROVEMENTS, encoding="utf-8")
    return tmp_path


def _spoken(root: Path, argv: tuple[str, ...], *, served: bool) -> str:
    buffer = io.StringIO()
    with contextlib.redirect_stdout(buffer), contextlib.redirect_stderr(io.StringIO()):
        assert main(["-C", str(root), *argv, *(["--json"] if served else [])]) == EXIT_OK
    return buffer.getvalue()


def _doors(text: str) -> set[str]:
    """Every command the text offers, in the two spellings the printers use."""
    found = set()
    for pattern in (_INVOKED, _BACKTICKED):
        for match in pattern.finditer(text):
            command = match.group(1).strip()
            if command.split()[0] in VERBS:
                found.add(command)
    return found


@pytest.mark.parametrize(
    ("argv", "about"), CALLS, ids=[" ".join(one[0][:3]) for one in CALLS]
)
def test_every_door_the_text_names_is_in_the_payload(tmp_path, argv, about):
    text = _spoken(project(tmp_path), argv, served=False)
    payload = _spoken(project(tmp_path / "again"), argv, served=True)
    parsed = json.loads(payload)
    assert _doors(text), f"the fixture stopped producing a door for {about}"

    for door in _doors(text):
        # By verb and by every argument that is not a placeholder: a payload spelling the
        # same call as an MCP tool name and a field map (RK449) carries the parts and not the
        # line, so matching the rendered string would fail on the surface this is *for*.
        for word in door.split():
            # Placeholders are not payload content: `…` is the blank a remedy renders for a
            # field the author fills, and `<anchor>` is the same thing spelled for a reader.
            # Demanding either would be demanding the *rendering*, which is the one thing a
            # served call deliberately does not carry (RK449).
            if word in {"…", "-"} or (word.startswith("<") and word.endswith(">")):
                continue
            assert word in payload, (
                f"`{door}` is offered by `{' '.join(argv)}` and `{word}` is nowhere in its "
                f"payload — {about}"
            )
    assert parsed  # the payload parsed, which is what makes the search above meaningful


def test_a_verb_named_in_prose_is_not_read_as_a_door(tmp_path):
    """The rule that keeps this gate from demanding a key for every verb this tool mentions.

    `anchors` says *765 addresses are task ids, which `add` already refuses to reuse* — a
    sentence about a command, not an offer to run one. A door takes an argument, which is
    also what makes it runnable: a bare verb is never the whole of a next step here.
    """
    assert _doors("which `add` already refuses to reuse") == set()
    assert _doors("`criterion add --task RK1 --lead … --why …` opens the list") == {
        "criterion add --task RK1 --lead … --why …"
    }
