"""The barrier at the agent boundary: a governed write refused before it happens (RK22).

L1 puts the schema where the text is created, and every command in this package honours it
— but only for text that arrives *through* a command. With Markdown as the store (L2), an
agent can bypass the entire format with one `Edit`, and will, because `Edit` is cheaper than
reading a `--help`. `lint` catches it at the commit, which is a whole turn of prose too late:
by then the tokens are spent and what the report asks for is a deletion. So this is the one
enforcement point an agent cannot route around — a `PreToolUse` hook, run by the harness
*before* the tool call, answering one question: **is this path a file that some project's
`roadkeep.toml` says is governed?**

If it is, the write is denied and the reason *is the command to call instead*, with its
flags. That second half is the whole value: a refusal that names no alternative is a refusal
an agent works around, and one that names the command makes the denial the cheapest path
forward rather than an obstacle.

Five decisions, each because the opposite breaks a session rather than a rule:

* **The config is discovered from the file, not from the working directory.** A harness
  edits across repositories, and a hook installed in `~/.claude/settings.json` sees all of
  them. Walking up from the path being written is the one rule that answers correctly for a
  monorepo, a worktree and a global install, with a single implementation.
* **Silence is the allow.** Nothing is ever returned for a file this does not govern.
  ``allow`` in this protocol *is* an approval, and emitting it would bypass the permission
  rules the user set for every unrelated file in the repository — a guard that widens what
  an agent may write is worse than no guard.
* **Every failure allows.** A malformed payload, an unreadable `roadkeep.toml`, a tool
  input carrying no path: all allow. A guard that denies on its own errors turns one typo
  in a config file into a repository nobody can edit, and RK14 still refuses the file at
  the commit — the gate is the backstop for the barrier, not the other way round.
* **`Bash` is not matched.** `sed -i` on the roadmap is a real bypass, and matching every
  shell command in order to catch one is not a barrier, it is a tax on every command. The
  `Stop` hook runs `lint` instead, so the bypass is caught before the turn ends — which is
  the difference between a report somebody reads and a report nobody was sent.
* **The decision travels in the payload, never in the exit code.** The harness reads a
  non-zero exit as *the hook itself failed*, so this is the one command in the package that
  always exits 0 (see :func:`roadkeep.cli._guard`) and says everything in its output.

What is deliberately absent: any judgement about the *content* of the write. This module
never reads what the agent was about to insert, only where it was going. Deciding whether a
sentence fits is :meth:`Schema.validate`'s job, and it gets to make it when the author calls
`add` — which is the entire point of refusing here.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from roadkeep.config import Config, ConfigError, find_config
from roadkeep.linting import Report, lint

#: The tools that put bytes in a file. Listed by what reaches the disk and not by what the
#: harness happens to call it this month: a writing tool that is missing here is the hole
#: the whole hook exists to close, so the set is wider than the two RK22 names.
WRITE_TOOLS = ("Edit", "MultiEdit", "NotebookEdit", "Write")

#: The events that mean the turn is trying to end, and `lint` is the last thing to say.
STOP_EVENTS = ("Stop", "SubagentStop")

#: Where a tool's input spells the file. Every key any writer uses, rather than the key
#: each one uses: reading all three costs three dict lookups and survives a renamed field.
_PATH_KEYS = ("file_path", "notebook_path", "path")

#: A `Stop` reason is context the next turn pays for, so the report is truncated — and the
#: truncation is *stated*, because a capped list that does not say so reads as a complete one.
_MOST_FINDINGS = 12

#: What to call instead, per role: the command, and what it is for. A denial is only as
#: useful as this table — the flags are the part that otherwise gets guessed (RK24), and
#: `<x>`/`<id>`/`…` are placeholders on purpose, since the tool never writes the prose (L4).
_INSTEAD: Mapping[str, tuple[tuple[str, str], ...]] = {
    "roadmap": (
        ('add --block <x> --symptom "…" --why "…"', "a new task line, fields refused at input"),
        ("status <id> <marker>", "a marker, and only in this file"),
        ("ship <id>", "shipped: ledger entry, line gone, section dropped"),
        ('retire <id> --reason "…"', "gone without shipping"),
    ),
    "changelog": (
        ("ship <id>", "the entry a planned task earns, in one transaction"),
        ('record --block <x> --symptom "…" --why "…"', "work that was never planned"),
        ('retire <id> --reason "…"', "a line that left without shipping"),
    ),
    "improvements": (
        ('section add <id> --title "…"', "the prose on stdin, within the word budget"),
        ("section drop <id>", "delete one section whole, subsections included"),
    ),
    "strategy": (
        ('section add <id> --title "…" --role strategy', "the prose on stdin, filled"),
        ("section drop <id> --role strategy", "delete one section whole"),
    ),
}

#: What a file that is governed but absent needs, which is not an edit.
_SCAFFOLD = (("init", "create the governed files and the config this project declares"),)


@dataclass(frozen=True, slots=True)
class Refusal:
    """One write denied, and the commands that do it properly."""

    #: The tool the harness was about to run, named back so the reason reads as an answer.
    tool: str
    #: As the project spells it — a reason quoting an absolute path is a reason that is
    #: about one machine.
    path: str
    role: str
    #: On disk already. A governed file that is *not* there yet is `init`'s, not `add`'s.
    exists: bool = True

    @property
    def commands(self) -> tuple[tuple[str, str], ...]:
        return _INSTEAD.get(self.role, ()) if self.exists else _SCAFFOLD

    def __str__(self) -> str:
        """The reason, as the agent reads it: what was refused, why, and what to run."""
        lines = [
            f"{self.tool} refused: {self.path} is this project's {self.role}, and "
            f"roadkeep owns its writes.",
            "",
            "The id, the pointer and every (deps: … ✅) annotation are derived on render, "
            "so a hand-edit is the one path that can leave a line the format rejects — "
            "and a limit discovered after the sentence exists is a limit that costs a "
            "deletion instead of a refusal.",
            "",
            "Call instead, from the project root:",
        ]
        width = max((len(command) for command, _ in self.commands), default=0)
        for command, purpose in self.commands:
            lines.append(f"  roadkeep {command:<{width}}  {purpose}")
        lines += [
            f"  {'roadkeep <command> --help':<{width + 9}}  every flag, so none is guessed",
            "",
            "Reading is never refused: `roadkeep brief <id>` starts a task in one call, "
            "`show <id>` joins the line to its rationale, `list --block <x>` prints them "
            "verbatim.",
        ]
        return "\n".join(lines)


@dataclass(frozen=True, slots=True)
class Review:
    """What `lint` found when the turn tried to end (RK14 as the backstop for RK22).

    Only the failing tier: a :class:`~roadkeep.linting.Note` is something the gate says at
    exit 0, and a turn is not worth blocking over a sentence.
    """

    report: Report

    def __str__(self) -> str:
        findings = self.report.findings
        lines = [
            f"roadkeep lint refuses {len(findings)} line(s) in "
            f"{', '.join(self.report.checked)}: a governed file was changed by something "
            f"other than roadkeep, and the format is what the next reader trusts.",
            "",
        ]
        lines += [f"  {finding}" for finding in findings[:_MOST_FINDINGS]]
        if len(findings) > _MOST_FINDINGS:
            lines.append(
                f"  … and {len(findings) - _MOST_FINDINGS} more — `roadkeep lint` prints "
                f"all of them"
            )
        lines += [
            "",
            "`roadkeep lint --fix` repairs what is derived (annotation, pointer, dep "
            "order, marker codepoint, whitespace); everything left is editorial and "
            "wants a command, not an edit.",
        ]
        return "\n".join(lines)


def guard(payload: Mapping[str, object], root: str | Path = ".") -> Refusal | None:
    """Decide one `PreToolUse` call: ``None`` allows, a :class:`Refusal` denies.

    ``root`` is only the fallback for a payload with no ``cwd`` — the paths in the tool
    input decide which project's configuration applies, because one hook process serves
    every repository the session touches.
    """
    tool = payload.get("tool_name")
    if not isinstance(tool, str) or tool not in WRITE_TOOLS:
        return None
    for path in _targets(payload.get("tool_input"), _cwd(payload, root)):
        found = governed(path)
        if found is None:
            continue
        config, role = found
        return Refusal(
            tool=tool, path=config.relative(path), role=role, exists=path.is_file()
        )
    return None


def review(payload: Mapping[str, object], root: str | Path = ".") -> Review | None:
    """Judge the files as the turn ends: ``None`` lets it end, a :class:`Review` blocks.

    The one check `Bash` cannot dodge, and the reason `PreToolUse` does not need to match
    every shell command. ``stop_hook_active`` is honoured before anything is read: blocking
    a second time on a file the agent has already failed to repair is a loop, and a loop
    costs more than the drift it was trying to stop.
    """
    if payload.get("stop_hook_active") is True:
        return None
    if not isinstance(payload.get("hook_event_name", "Stop"), str):
        return None
    try:
        config = Config.discover(_cwd(payload, root))
    except ConfigError:
        # The same failure rule as the barrier: a broken config must not pin a session
        # open. `lint` refuses to run and says why, where somebody can act on it.
        return None
    if config.source is None:
        return None  # not a roadkeep project: there is nothing here this may judge
    try:
        report = lint(config)
    except (KeyError, OSError):
        return None
    return None if report.clean else Review(report=report)


def governed(path: str | Path) -> tuple[Config, str] | None:
    """The project that owns ``path`` and the role it holds there, or ``None``.

    Discovery walks up from the file itself, so the answer does not depend on where the
    hook process happened to be started. `roadkeep.toml` is *not* governed: it is the
    per-project declaration (L6), which a human edits by hand on purpose.
    """
    target = Path(path)
    found = find_config(target.parent)
    if found is None:
        return None
    try:
        config = Config.load(found)
    except (ConfigError, OSError, tomllib.TOMLDecodeError):
        return None
    wanted = _comparable(target)
    for role, declared in config.paths.items():
        if _comparable(declared) == wanted:
            return config, role
    return None


def _comparable(path: Path) -> str:
    """A path as this filesystem compares them.

    `normcase` and not `str`: on Windows `docs/ROADMAP.md` and `docs/roadmap.md` are one
    file, and a comparison that misses that allows the write it exists to refuse.
    """
    return os.path.normcase(str(path.resolve()))


def _targets(raw: object, base: Path) -> tuple[Path, ...]:
    """Every path the tool input names, resolved against the session's directory."""
    if not isinstance(raw, Mapping):
        return ()
    out: list[Path] = []
    for key in _PATH_KEYS:
        value = raw.get(key)
        if isinstance(value, str) and value:
            candidate = Path(value)
            out.append(candidate if candidate.is_absolute() else base / candidate)
    return tuple(out)


def _cwd(payload: Mapping[str, object], root: str | Path) -> Path:
    value = payload.get("cwd")
    return Path(value if isinstance(value, str) and value else root)
