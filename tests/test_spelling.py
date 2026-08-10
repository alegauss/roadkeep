"""Every message that blocks a turn, in both spellings, held against each other (RK480).

RK444 and RK447 moved two routes, RK448 a third, RK477 the reads a deny closes on, RK478 the
doors the gate prints, RK479 the attestation. Six tasks, one shape, and every one was found
the same way — somebody rendered the message and read it. The seventh is found that way or
not at all, which is what `tests/test_pairs.py` said about flag pairs before it swept them.

**The assertion reads no prose.** Each message is rendered twice, with a tool prefix and
without; the verbs named in each are taken off the text, and every verb the shell form offers
the served form must offer as a call. What a message *says* is not the subject — only that it
hands no session a verb withheld from that session's own surface.

An inventory rather than a call site, which is this project's answer to a class: `VOLATILE`
names the caches an autouse fixture clears (RK268), `remedying`'s table is asserted total over
every code the gate can emit (RK421), and `_IDEMPOTENT` states the flag pairs that change
nothing and why (RK467).
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from roadkeep.attesting import Unattested
from roadkeep.config import Config
from roadkeep.guarding import Notice, Refusal, Review
from roadkeep.linting import lint
from roadkeep.provenance import invocation

ROADMAP = "docs/ROADMAP.md"
CHANGELOG = "docs/CHANGELOG.md"
IMPROVEMENTS = "docs/IMPROVEMENTS.md"

CLEAN = """# Roadmap

## Block A — The model

- 📋 **RK1** (deps: —) **A first symptom** — Because of a reason. → §RK1
- 📋 **RK2** (deps: RK99) **A second symptom** — Because of another. → §RK2
"""

LEDGER = """# Shipped

## Block A — The model
"""

DESIGN = """# Improvements

## Block A — The model

### §RK1 The first design

Because a pointer resolving to nothing reads exactly like a design that does.
"""

CONFIG = (
    f'prefix = "RK"\n[files]\nroadmap = "{ROADMAP}"\nchangelog = "{CHANGELOG}"\n'
    f'improvements = "{IMPROVEMENTS}"\n'
)

#: The prefix a served session's tools arrive under. Any string ending in the separator the
#: real one uses: what is under test is the *branch*, not the harness's naming scheme.
SERVED = "mcp__roadkeep__"

#: A vendored surface `install` refreshes — what makes `Notice` grow its second clause.
VENDORED = ".claude/skills/roadkeep/SKILL.md"

#: Verbs a message may offer in a shell and not as a call, each with the reason it is not an
#: oversight. Stated here rather than filtered in silence, so a third one is a decision:
#:
#: * ``lint --fix`` **writes**, and RK16 keeps a repair where a human is standing — so the
#:   surface exposes `lint` without it and a prefix glued to this line would name no tool.
#: * ``<command> --help`` is argparse's own screen, and nothing serves one.
_SHELL_ONLY = {
    "lint --fix": "`--fix` writes, so the tool surface withholds it by derivation (RK16)",
    "<command> --help": "argparse's screen; no tool serves a help page",
}

#: Verbs **no tool serves at all**, each with why the surface has none — kept apart from
#: `_SHELL_ONLY` because the two are different facts (RK486): that one is a flag a served
#: command withholds, and these are commands the surface never had. Folding them together
#: would let a served read fall into the list on the strength of the wrong reason, which is
#: the RK463 defect. Asserted against `TOOLS` below, so an entry cannot go stale.
_UNSERVED = {
    "init": "scaffolds a project that has no config yet, so there is no server to call",
    "install": "wires the harness itself, which is what a session would be calling through",
}


def project(tmp_path: Path) -> Path:
    for name, body in (
        ("roadkeep.toml", CONFIG),
        (ROADMAP, CLEAN),
        (CHANGELOG, LEDGER),
        (IMPROVEMENTS, DESIGN),
    ):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


def shapes(root: Path) -> dict[str, tuple[object, object]]:
    """Every **rendering** these messages reach, in both spellings, one entry per shape.

    Per shape and not per message (RK486). RK480 built one of each and called that coverage;
    driving `install` end to end showed the gap — drift a vendored `SKILL.md` and the
    `SessionStart` notice grows a clause naming `install`, and the plain `Notice` this
    fixture built names no route at all. `Refusal` is the same: `exists` renders two files.

    Constructed rather than driven through the hooks: what is under test is the rendering,
    and a fixture that had to *provoke* four different events would exercise the triggers
    instead. That each is wired to read `serving(root)` is asserted where it is wired —
    `tests/test_attesting.py` holds the one that was not (RK479).
    """
    config = Config.discover(root)
    report = lint(config)

    def both(build) -> tuple[object, object]:
        return build(SERVED), build("")

    return {
        "Refusal": both(
            lambda served: Refusal(tool="Edit", path=ROADMAP, role="roadmap", served=served)
        ),
        "Refusal.absent": both(
            lambda served: Refusal(
                tool="Edit", path=ROADMAP, role="roadmap", served=served, exists=False
            )
        ),
        "Review": both(
            lambda served: Review(report=report, served=served, config=config)
        ),
        "Notice": both(lambda served: Notice(files=(ROADMAP, CHANGELOG), served=served)),
        "Notice.drifted": both(
            lambda served: Notice(
                files=(ROADMAP, CHANGELOG), served=served, stale=(VENDORED,)
            )
        ),
        "Unattested": both(
            lambda served: Unattested(files=(("roadmap", ROADMAP),), served=served)
        ),
    }


def commands() -> set[str]:
    """Every command path the CLI registers — `add`, and `section add` for the nested ones.

    Off the real parser, so a verb this sweep looks for is one that exists: matching bare
    words instead read `lint refuses …` as the command `lint refuses`, which is a sentence.
    """
    from roadkeep.cli import build_parser

    top = [one for one in build_parser()._actions if getattr(one, "choices", None)][0].choices
    found = set()
    for name, parser in top.items():
        found.add(name)
        nested = [one for one in parser._actions if getattr(one, "choices", None)]
        found |= {f"{name} {sub}" for one in nested for sub in one.choices}
    return found


def offered(text: str) -> set[str]:
    """The verbs a shell rendering offers, as `verb` or `verb sub` — never a whole argv.

    The head only, because a flag is not a word over the other transport (RK449): what is
    being compared is which *command* each spelling puts within reach, and `add --block <x>`
    and `add --id RK1` are the same answer to that question. Two words before one, for
    `Door.call`'s reason: `section add` is a command and `section` alone is not.
    """
    known = commands()
    reached = re.escape(invocation())
    found = set()
    for tail in re.findall(rf"{reached} ([a-z][a-z-]*(?: [a-z][a-z-]*)?)", text):
        words = tail.split()
        for length in (2, 1):
            if " ".join(words[:length]) in known:
                found.add(" ".join(words[:length]))
                break
    return found


def spelled(text: str) -> set[str]:
    """The commands a served rendering names, read back through `TOOLS`.

    Through the table and not by replacing `_` with a space: `non_goal_add` is the command
    `non-goal add`, and a reverse mapping that guessed would report three tools missing that
    the deny has named since RK24 — measured, while writing this.
    """
    from roadkeep.serving import TOOLS

    named = set(re.findall(rf"{re.escape(SERVED)}([a-z_]+)", text))
    return {tool.command for tool in TOOLS if tool.name in named}


@pytest.mark.parametrize(
    "name",
    ["Refusal", "Refusal.absent", "Review", "Notice", "Notice.drifted", "Unattested"],
)
def test_every_verb_a_message_offers_in_a_shell_it_offers_as_a_call(tmp_path, name):
    """The defect six tasks closed by hand, stated as the shape it leaves: a session with
    tools reads a route only its shell half names, on a machine RK57 may have left without
    one. The two exceptions are named in `_SHELL_ONLY` and asserted to be the whole list."""
    served, shell = shapes(project(tmp_path))[name]
    # The exception is taken **per line and not per verb**: `lint --fix` is excused and
    # `lint` is not, so excusing the head would have excused the one RK448 moved. Measured —
    # reverting RK448 with the verb-wide form left this sweep green.
    kept = "\n".join(
        line
        for line in str(shell).splitlines()
        if not any(one in line for one in _SHELL_ONLY)
    )
    withheld = offered(kept) - spelled(str(served)) - set(_UNSERVED)
    assert not withheld, (
        f"{name} offers {sorted(withheld)} in a shell and names no tool for them: either the "
        f"served rendering has to spell them, or the reason belongs in _SHELL_ONLY"
    )


def test_the_sweep_reaches_every_message_that_blocks_a_turn(tmp_path):
    """The count is the claim: a fifth message added without a `served` field silently leaves
    this sweep, and a sweep nobody can size is one that can go empty without saying so."""
    import dataclasses

    from roadkeep import attesting, guarding

    carrying = {
        f"{module.__name__}.{name}"
        for module in (guarding, attesting)
        for name, obj in vars(module).items()
        if dataclasses.is_dataclass(obj)
        and isinstance(obj, type)
        and obj.__module__ == module.__name__
        and any(one.name == "served" for one in dataclasses.fields(obj))
    }
    assert len(carrying) == 4, sorted(carrying)
    built = shapes(project(tmp_path))
    reached = {one.split(".")[0] for one in built}
    assert {one.rsplit(".", 1)[1] for one in carrying} == reached


def test_every_field_that_changes_what_a_message_says_has_a_shape(tmp_path):
    """RK486's own mechanism: a message is not one rendering, and counting it as one is how
    `Notice`'s drift clause — which names `install` — stayed outside a sweep whose whole
    claim is coverage.

    So the optional fields are the inventory. One that never takes a non-default value in
    any shape is a rendering nobody sweeps, and it leaves silently unless this fails."""
    import dataclasses

    from roadkeep import attesting, guarding

    built = shapes(project(tmp_path))
    for module in (guarding, attesting):
        for name, obj in vars(module).items():
            if not (dataclasses.is_dataclass(obj) and isinstance(obj, type)):
                continue
            if obj.__module__ != module.__name__:
                continue
            if not any(one.name == "served" for one in dataclasses.fields(obj)):
                continue
            mine = [one for key, one in built.items() if key.split(".")[0] == name]
            for field in dataclasses.fields(obj):
                if field.name == "served" or field.default is dataclasses.MISSING:
                    continue
                moved = any(getattr(shape, field.name) != field.default for shape, _ in mine)
                assert moved, (
                    f"{name}.{field.name} never leaves its default in any shape: add one to "
                    f"`shapes`, or this field's rendering is outside the sweep"
                )


def test_what_the_sweep_lets_through_says_why(tmp_path):
    """Both exceptions carry a reason and both are still real: `--fix` is a flag `lint` takes
    and the tool surface does not expose, which is the derivation RK449 relies on."""
    from roadkeep.serving import TOOLS

    assert all(reason for reason in _SHELL_ONLY.values())
    assert all(reason for reason in _UNSERVED.values())
    # And they really are unserved: an entry that became a tool is an exception hiding a
    # route the sweep exists to find.
    served_now = {tool.command for tool in TOOLS}
    assert served_now.isdisjoint(_UNSERVED), sorted(served_now & set(_UNSERVED))
    lint_ = next(tool for tool in TOOLS if tool.command == "lint")
    assert "fix" not in lint_.exposes, "the surface exposes --fix; the exception is stale"
    # And the sweep sees them: both appear in the shell rendering it compares against.
    shell = str(shapes(project(tmp_path))["Refusal"][1])
    assert all(one in shell for one in _SHELL_ONLY)
