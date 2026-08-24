"""Every pair of boolean flags a read can be given, and what it may not answer (RK467).

RK465 found `cost --tools --role` by probing refusal paths; RK466 found `anchors --claims
--next` and `export --readme --json` the same way, and one of the three it first claimed
turned out to be the transaction working. Three probes, two defects, one false positive —
which is what finding a class by hand looks like, and the read-only surface has more pairs
than anybody is going to try.

**The signature is mechanical and exact.** A swallowed flag leaves output *byte-identical to
one half alone* and different from the other: `anchors --claims --next` printed what `--next`
prints, to the character. So every pair is one of three things, and the fourth is the defect:

* **refused** — exit 2, which is two subjects saying so (`budget`'s five, RK465);
* **composed** — exit 0 and an answer that is neither half's, which is `list --block --json`
  and every ordinary combination;
* **idempotent** — exit 0 and an answer identical to *both* halves, which is a flag that
  changed nothing for a reason of its own and is stated below rather than guessed at;
* and **swallowed** — exit 0, identical to one half and not the other. That one is the bug.

An inventory rather than a call site, which is this project's answer to a class: `VOLATILE`
names the caches an autouse fixture clears and says why the rest are cleared for nothing
(RK268), and `remedying`'s table is asserted total over every code the gate can emit (RK421).

**And since RK489 it is a property rather than a search.** The refusal used to be twenty-five
hand-written lines inside `budget` and four smaller copies elsewhere, so this file was the
only thing that could say which verb had them — it reported the next defect *after* a flag
nothing reads had been written. Now every verb that takes more than one answer declares its
subjects at `add_parser` and one dispatcher enforces them, so each pair below is predicted
before it is run: a pair the declaration separates must exit 2, and one it does not must
compose. What this sweep now measures is whether the declaration is **complete**, which is a
question about a table rather than a hunt through eighty verbs.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import itertools
from pathlib import Path

import pytest

from roadkeep.cli import _one_answer, build_parser, main

ROADMAP = """# Roadmap

## Block A — The model

- 💭 **RK1** (deps: —) **A first symptom** — Because of a reason. → §I.1
- 🛠 **RK2** (deps: RK1) **A second symptom** — Because of another. → §I.2

## Non-goals

- **No web UI.** Files and a CLI.
"""

LEDGER = """# Shipped

## Block A — The model

- ✅ **RK9** **A shipped symptom** — It works now.
"""

PROSE = """# Improvements

## Block A — The model

## I A family

The prose a family opens with.

### I.1 The first design (RK1)

The reasoning the line has no room for.

### I.2 The second design

The reasoning the other line has no room for.
"""

#: Flags that **write**, inside commands whose parser is declared read-only. Each is the
#: RK16 exception — the repair belongs where a human is standing — and none of them belongs
#: in a sweep that runs every pair against one fixture: a `--fix` in the middle of it would
#: change what every later pair is measured against.
_WRITES = {
    ("lint", "--fix"),
    ("claims", "--prune"),
    ("merge", "--register"),
    ("brief", "--claim"),
    ("pick", "--claim"),
}

#: Commands this sweep does not reach, and why — stated rather than filtered in silence, for
#: the reason a truncated listing states its own truncation.
_UNREACHED = {
    "report": "it re-runs a named command and writes a capture, so it is not one read",
    "replay": "it needs a stored capture, which is a fixture and not a flag",
}

#: Pairs that answer identically to *both* halves, with the reason each does. A flag that
#: changes nothing here is not a swallowed flag — it is one whose effect this fixture does
#: not exhibit — and saying which is what keeps the sweep from being loosened to admit one.
#:
#: Empty, and that is the finding rather than the absence of one: every pair this reaches
#: either composes or is refused. It stays because the alternative to a named exception is
#: an unnamed one, and the assertion below is what makes adding a row a decision.
_IDEMPOTENT: dict[tuple[str, str, str], str] = {}


def project(tmp_path: Path) -> Path:
    for name, body in (
        (
            "roadkeep.toml",
            # An **outline** project (RK467): under `ref_scheme = "id"` the anchor is the id,
            # so `anchors` refuses for want of a family and every pair on it exits 2 — which
            # a sweep reads as "refused, nothing to check" and learns nothing from. The
            # commands this exists to watch have to answer here.
            'prefix = "RK"\nref_scheme = "outline"\n[files]\n'
            'roadmap = "ROADMAP.md"\nchangelog = "CHANGELOG.md"\n'
            'improvements = "IMPROVEMENTS.md"\n',
        ),
        ("ROADMAP.md", ROADMAP),
        ("CHANGELOG.md", LEDGER),
        ("IMPROVEMENTS.md", PROSE),
    ):
        with (tmp_path / name).open("w", encoding="utf-8", newline="") as handle:
            handle.write(body)
    return tmp_path


#: What a verb needs before its flags mean anything: the positional it declares required. One
#: table for both halves of the sweep (RK1147) — they read it for different reasons, one to
#: parse and one to run, and two copies is how a verb ends up covered by only one of them.
#: `adopt` arrived here by being declared `reads_only`, which it always was, and its file is
#: the project's own roadmap: a real corpus this fixture already writes, so the pair runs
#: against an answer rather than against argparse's missing-argument exit.
NEEDS = {
    "claim": ["RK2"],
    "show": ["RK1"],
    "origin": ["RK1"],
    "adopt": ["docs/ROADMAP.md"],
}


def run(root: Path, command: str, *flags: str) -> tuple[int, str]:
    """One call, with its stdout — which is the thing a swallowed flag leaves identical."""
    out = io.StringIO()
    argv = ["-C", str(root), command, *NEEDS.get(command, []), *flags]
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
        try:
            code = main(argv)
        except SystemExit as leaving:  # argparse refuses before a handler exists
            code = leaving.code if isinstance(leaving.code, int) else 2
    return code, out.getvalue()


def subcommands() -> dict[str, argparse.ArgumentParser]:
    """Every verb, off the real parser — the one reader this file has of what is declared."""
    return [one for one in build_parser()._actions if getattr(one, "choices", None)][0].choices  # noqa: SLF001


def separated(command: str, first: str, second: str) -> bool:
    """Whether this verb's own declaration says these two flags are two answers (RK489).

    Read off `subjects`, which is what `dispatch` reads: a prediction taken from anywhere else
    would be this file holding a second opinion about the rule it is checking.
    """
    parser = subcommands()[command]
    groups = parser.get_default("subjects") or ()
    held = [
        {option for _, option, _ in group.flags}
        for group in groups
    ]
    return any(
        first in one and second in other
        for one in held
        for other in held
        if one is not other
    )


def pairs() -> list[tuple[str, str, str]]:
    """Every two boolean flags one read-only command takes, off the real parser."""
    found = []
    for name, parser in sorted(subcommands().items()):
        if not parser.get_default("reads_only") or name in _UNREACHED:
            continue
        flags = [
            one.option_strings[0]
            for one in parser._actions  # noqa: SLF001
            if isinstance(one, argparse._StoreTrueAction)  # noqa: SLF001
            and (name, one.option_strings[0]) not in _WRITES
        ]
        found += [(name, first, second) for first, second in itertools.combinations(flags, 2)]
    return found


@pytest.mark.parametrize("command, first, second", pairs())
def test_a_pair_is_refused_or_answers_as_neither_half(tmp_path, command, first, second):
    """The defect this catches, stated as the shape it leaves: exit 0, and an answer that is
    one half's to the character. Both halves are run against the same fixture, so what
    separates a composed pair from a swallowed one is only whether the output moved."""
    root = project(tmp_path)
    code, both = run(root, command, first, second)
    if code != 0:
        return  # refused, which is two subjects saying so
    _, alone_first = run(root, command, first)
    _, alone_second = run(root, command, second)
    if alone_first == alone_second == both:
        assert (command, first, second) in _IDEMPOTENT, (
            f"`{command} {first} {second}` answers as both halves and no reason is stated: "
            f"add it to _IDEMPOTENT with why, or the pair is doing nothing"
        )
        return
    dropped = first if both == alone_second else second if both == alone_first else ""
    assert not dropped, (
        f"`{command} {first} {second}` answered exactly as `{command} "
        f"{second if dropped == first else first}` alone: {dropped} was swallowed"
    )


@pytest.mark.parametrize("command, first, second", pairs())
def test_the_dispatcher_refuses_exactly_the_pairs_a_verb_declares(command, first, second):
    """The property RK489 turned this sweep into, asked of the dispatcher and not of a run.

    An exit code cannot answer it: five of these pairs exit 2 for reasons that are nothing to
    do with the flags — no `[non_goals]` table, no git history, no live claim — so a test
    reading the code alone would call each of those a declared refusal. `_one_answer` is the
    whole rule and takes a parsed namespace, so this asks it directly: refused **iff** the
    verb's own `answers(...)` puts the two flags in different groups.

    Which is what makes the declaration complete rather than merely present. A verb that grows
    a sixth subject and forgets to declare it fails here on the pair it swallows, in the file
    that has always been the one able to see the class."""
    parser = build_parser()
    args = parser.parse_args([command, *NEEDS.get(command, []), first, second])
    refused = _one_answer(args) is not None
    assert refused == separated(command, first, second), (
        f"`{command} {first} {second}`: the dispatcher "
        f"{'refuses' if refused else 'allows'} a pair the declaration "
        f"{'does not separate' if refused else 'separates'}"
    )


def test_the_sweep_reaches_every_read_that_takes_two(tmp_path):
    """The count is the claim: a command that stops being read-only, or a flag that stops
    being boolean, silently leaves this sweep — and a sweep nobody can size is one that can
    go empty without saying so."""
    found = pairs()
    assert len(found) >= 12, f"only {len(found)} pairs reached: {found}"
    covered = {command for command, _, _ in found}
    assert {"anchors", "budget", "list", "show", "brief"} <= covered
    assert covered.isdisjoint(_UNREACHED)
    # And at least one of them is a pair a declaration separates, so the prediction above is
    # exercised rather than being an `if` nothing enters (RK489).
    assert any(separated(*one) for one in found), found


def test_what_the_sweep_does_not_run_says_why(tmp_path):
    """Both exclusions are named with a reason, so widening either is a decision somebody
    writes down rather than a filter that quietly grew."""
    assert all(reason for reason in _UNREACHED.values())
    assert all(reason for reason in _IDEMPOTENT.values())
    # And the sweep's own finding: nothing needed an exception. `lint --quiet --json` and
    # `list --ids --json` were the two it caught, and both are refused now rather than listed
    # here — a flag shaping one form beside another form is RK465's rule, not an exemption.
    assert _IDEMPOTENT == {}
    declared = subcommands()
    for command, flag in _WRITES:
        assert command in declared, command
        assert flag in {
            one for action in declared[command]._actions for one in action.option_strings
        }, f"{command} no longer takes {flag}"


def test_every_declared_answer_names_a_flag_its_verb_actually_has():
    """RK489's build-time half, stated as a test as well: `answers` and `narrows` resolve a
    dest through the subparser and raise where it has none, so a declaration naming a flag
    that was renamed fails when the parser is *constructed*. This asserts what that buys —
    every group is non-empty, every subject says what it answers, and every narrowing flag
    names a subject the same verb declares."""
    seen = 0
    for name, parser in sorted(subcommands().items()):
        options = {
            one for action in parser._actions for one in action.option_strings  # noqa: SLF001
        }
        for group in parser.get_default("subjects") or ():
            seen += 1
            assert group.flags, name
            assert group.what, (name, group.flags)
            for _, option, _ in group.flags:
                assert option in options, (name, option)
        subjects = {
            option
            for group in parser.get_default("subjects") or ()
            for _, option, _ in group.flags
        }
        for (_, flag, _), (_, subject, _) in parser.get_default("narrowing") or ():
            assert flag in options, (name, flag)
            assert subject in subjects, (name, flag, subject)
    # Five verbs declare between them, and the count is the claim: a declaration deleted with
    # the branch it replaced would leave this file measuring nothing.
    assert seen >= 12, seen
