"""The barrier at the agent boundary: a governed write refused before it happens (RK22).

L1 puts the schema where the text is created, and every command in this package honours it
— but only for text that arrives *through* a command. With Markdown as the store (L2), an
agent can bypass the entire format with one `Edit`, and will, because `Edit` is cheaper than
reading a `--help`. `lint` catches it at the commit, which is a whole turn of prose too late:
by then the tokens are spent and what the report asks for is a deletion. So this is the one
enforcement point an agent cannot route around — a `PreToolUse` hook, run by the harness
*before* the tool call, answering one question: **is this path a file that some project's
`roadkeep.toml` says is governed?** For a `Bash` payload, which names no path, it is the same
question asked of the command's characters, and the answer is `ask` rather than `deny` (RK128).

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
* **`Bash` is matched, and answered with `ask` rather than `deny`** (RK128). It used not to be
  matched at all, on the argument that parsing shell to catch one `sed -i` is a tax on every
  command — but the refusal above says *roadkeep owns its writes*, and an agent told that will
  believe it, so silence there was the barrier claiming a side it did not hold. Nothing parses
  shell: the one decidable question is whether a path this project declares appears in the
  command at all, and where it does, what the command *does* to it is the harness's user to
  answer. `deny` would refuse `git add docs/ROADMAP.md` and every `git log --` of a governed
  file; `allow` is not this hook's to give. So the third answer is the honest one, and the
  `Stop` hook still runs `lint` behind it.
* **The decision travels in the payload, never in the exit code.** The harness reads a
  non-zero exit as *the hook itself failed*, so this is the one command in the package that
  always exits 0 (see :func:`roadkeep.cli._guard`) and says everything in its output.

The same process answers `SessionStart` (RK82), because the barrier only ever spoke to a
session that had already decided to write: :class:`Notice` states which files are governed
here, once, before the first read. The other candidate — a `PreToolUse` matcher on the
reading tools — is not taken, on the argument `Bash` gets above: paying on every read to
catch what one resident line already said is a tax, and reading is never refused anyway.

What is deliberately absent: any judgement about the *content* of the write. This module
never reads what the agent was about to insert, only where it was going. Deciding whether a
sentence fits is :meth:`Schema.validate`'s job, and it gets to make it when the author calls
`add` — which is the entire point of refusing here.
"""

from __future__ import annotations

import os
import tomllib
from collections.abc import Mapping
from dataclasses import dataclass, replace
from pathlib import Path

from roadkeep.config import Config, ConfigError, find_config
from roadkeep.history import changed_lines
from roadkeep.linting import Report, lint
from roadkeep.serving import TOOLS

#: The tools that put bytes in a file. Listed by what reaches the disk and not by what the
#: harness happens to call it this month: a writing tool that is missing here is the hole
#: the whole hook exists to close, so the set is wider than the two RK22 names.
WRITE_TOOLS = ("Edit", "MultiEdit", "NotebookEdit", "Write")

#: The tools that put bytes in a file the payload does not name (RK128). One, and it is the
#: hole every other measure in this module was arranged around: a `command` is a string the
#: harness never resolves into a path, so the only thing knowable without parsing shell is
#: whether a governed path is *mentioned* — which is why these are asked about, not denied.
ASK_TOOLS = ("Bash",)

#: Both, in the order the plugin's `PreToolUse` matcher lists them. Kept as one name because
#: the matcher and this module have to agree or the hook never sees the payload it decides.
GUARDED_TOOLS = (*WRITE_TOOLS, *ASK_TOOLS)

#: The events that mean the turn is trying to end, and `lint` is the last thing to say.
STOP_EVENTS = ("Stop", "SubagentStop")

#: The event that arrives before the session's first tool call — the one moment an
#: announcement is cheaper than the mistake it prevents (RK82).
START_EVENTS = ("SessionStart",)

#: What the notice may cost, in characters. A budget and not a style rule: this is resident
#: for the whole session in every governed project, so the thing that keeps it one line is
#: a number a test holds, exactly as `[budgets]` holds `agents.md` (RK30).
_NOTICE_BUDGET = 260

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
        # First, because it is the one the agent meets first (RK141): every write above
        # refuses an undeclared block, and until this verb existed the only key to that
        # door was the edit this refusal denies.
        ('block add <x> --title "…"', "declare a block, in every file organised by them"),
        # And the inverse (RK144), because the key that only opens is the same asymmetry: a
        # label typed wrongly was a heading in three files that only this denial's edit removed.
        ("block drop <x>", "withdraw a label: refused by name over any line under it"),
        ("status <id> <marker>", "a marker, and only in this file"),
        ('amend <id> --why "…"', "correct the why, the deps or the pointer of a line"),
        # The field that one excludes, which is the whole reason it is a second row (RK178): a
        # denial naming only `amend` sends a reader to the verb that refuses this field.
        ('restate <id> --symptom "…"', "a symptom whose premise turned out to be false"),
        ("ship <id>", "shipped: ledger entry, line gone, section dropped"),
        ('retire <id> --reason "…"', "gone without shipping"),
        # The one bullet in this file that is not a task line, and the reason the five above
        # were not enough: a denial that named only them left `sed` as the route (RK70).
        ('non-goal add --lead "…" --why "…"', "a constraint on what may be proposed at all"),
        ("non-goal drop <lead>", "a constraint that is gone, or whose lead is being corrected"),
        # The one read in a table of writes (RK69), and here rather than in the closing
        # sentence because this is the file whose first bullet decides whether `add` may be
        # called at all: a denial that teaches the write and not the check teaches half.
        ("non-goal list", "what may not be proposed at all — before `add`, not after"),
        # The repair for damage smaller than a line (RK126). Listed on both line files,
        # because a control character is the one defect no verb above reaches.
        ("lint --fix", "a derived field or a character that is not text, repaired"),
    ),
    "changelog": (
        ("ship <id>", "the entry a planned task earns, in one transaction"),
        ('record add --block <x> --symptom "…" --why "…"', "work that was never planned"),
        ('block add <x> --title "…"', "declare a block: `ship` refuses one this file lacks"),
        # Its inverse reaches this file too, but only for a label with nothing under it: an
        # entry is history, and history keeps the heading it was filed under (RK144).
        ("block drop <x>", "withdraw a label opened by mistake; entries keep theirs"),
        # The ledger's update (RK124), without which the honest answer to "a word is wrong
        # here" was drop-and-re-add, which moves the entry to the end of its block.
        ('record amend <id> --why "…"', "correct an entry's sentence where it already is"),
        # The field that update deliberately withheld (RK143): filing an entry elsewhere is a
        # move, so it is a verb that says so rather than a flag inside a correction.
        ("record move <id> --to-block <x>", "an entry filed under the wrong block heading"),
        ("record drop <id>", "one of two entries for one id, when they say the same thing"),
        # And when they do not (RK127): two deliveries under one id, which the drop above
        # refuses rather than resolving by picking the entry that earned the id. Offered
        # without its `--line`, because the refusal names the two real line numbers and a
        # placeholder here would be the guess this whole table exists to remove.
        ("record renumber <id>", "two deliveries sharing an id; it names both, you pick --line"),
        ('retire <id> --reason "…"', "a line that left without shipping"),
        ("lint --fix", "a character that is not text, removed wherever it is"),
    ),
    "improvements": (
        ('section add <id> --title "…"', "the prose on stdin, within the word budget"),
        # The correction an open task's design needs (RK123): `drop` is refused while a live
        # pointer names the anchor, so without this the table named nothing that applied.
        ("section amend <id> --body -", "correct a live section's prose, or its --title"),
        ("section drop <id>", "delete one section whole, subsections included"),
    ),
    "strategy": (
        ('section add <id> --title "…" --role strategy', "the prose on stdin, filled"),
        ("section amend <id> --body - --role strategy", "correct a live section's prose"),
        ("section drop <id> --role strategy", "delete one section whole"),
    ),
}

def _tool_for(command: str) -> str | None:
    """The tool that serves this command line, matching the longest subcommand path first.

    Two words before one, because `section add` is a tool and `section` is not — a lookup on
    the first word alone would name `mcp__roadkeep__section`, which nothing answers (RK59).
    """
    words = command.split()
    for length in (2, 1):
        for tool in TOOLS:
            # A tool that always passes a flag serves a *narrower* command than the one asked
            # about (RK150), so `claim` is not the answer to "which tool runs `brief`".
            if not tool.always and tool.argv_head == words[:length]:
                return tool.name
    return None


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
    def decision(self) -> str:
        """What the harness is told: `deny`, or `ask` where the target was only mentioned.

        Derived from the tool and not stated, so the two cannot disagree (RK128). A tool that
        *names* the file it writes is certain, and the command table below is then the cheaper
        path forward. A shell command only mentions the path — `sed -i` and `git log --` are
        one payload shape — so the answer belongs to whoever owns the repository, which is the
        one response that is neither a lie about the boundary nor a hole in it.
        """
        return "ask" if self.tool in ASK_TOOLS else "deny"

    @property
    def commands(self) -> tuple[tuple[str, str], ...]:
        return _INSTEAD.get(self.role, ()) if self.exists else _SCAFFOLD

    @property
    def tools(self) -> tuple[tuple[str, str], ...]:
        """The commands above that the same plugin also serves as MCP tools (RK58).

        Named first, because since RK57 the plugin installs with no `pip install` and no
        PATH entry: on that machine the tool is the route that is certainly there and
        `roadkeep add` is a `command not found` waiting to teach that the advice is wrong.
        """
        found = []
        for command, purpose in self.commands:
            name = _tool_for(command)
            if name is not None:
                found.append((f"mcp__roadkeep__{name}", purpose))
        return tuple(found)

    @property
    def _opening(self) -> str:
        """The one sentence the two decisions do not share (RK128).

        Everything under it is the same text, because the value of a denial is the command
        table and a project that printed two of those would have two that could drift. What
        differs is only the claim being made: one states that the write was refused, the other
        that this hook cannot tell a read from a write and is not going to pretend.
        """
        if self.decision == "ask":
            return (
                f"{self.tool} names {self.path}, this project's {self.role}, and roadkeep "
                f"owns its writes. A shell command is not read to see which it does, so the "
                f"decision is yours: reading it is fine, and writing it wants a verb below."
            )
        return (
            f"{self.tool} refused: {self.path} is this project's {self.role}, and "
            f"roadkeep owns its writes."
        )

    def __str__(self) -> str:
        """The reason, as the agent reads it: what was refused, why, and what to run."""
        lines = [
            self._opening,
            "",
            "The id, the pointer and every (deps: … ✅) annotation are derived on render, "
            "so a hand-edit is the one path that can leave a line the format rejects — "
            "and a limit discovered after the sentence exists is a limit that costs a "
            "deletion instead of a refusal.",
            "",
        ]
        if self.tools:
            width = max(len(name) for name, _ in self.tools)
            lines.append("Call instead — this session's tools, where the fields are a schema:")
            lines += [f"  {name:<{width}}  {purpose}" for name, purpose in self.tools]
            lines += ["", "Or the same engine in a shell, from the project root:"]
        else:
            lines.append("Call instead, from the project root:")
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
            f"roadkeep lint refuses {len(findings)} line(s) this turn changed in "
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


@dataclass(frozen=True, slots=True)
class Notice:
    """The one line a session is given before it reads anything (RK82).

    The write side had an instrument and the read side had prose: a hook refuses a
    hand-edit, and the rule that these files are *queried* rather than read lives in a
    skill that loads once a governed file is already in play. Measured, that is too late —
    a session opened with a `grep` of the roadmap and the skill in the same batch, so the
    instruction not to read the file arrived with the file's contents.

    So this states the two facts nothing resident carried: **which** files are governed
    here, and that reading them is a command too. It never repeats the write path — that
    is the skill's, and a rule in two places is two places that can disagree.
    """

    #: As this project spells them, in the order `[files]` declares: the whole point is
    #: that a session learns these paths before it greps for one (L6).
    files: tuple[str, ...]

    def __str__(self) -> str:
        return (
            f"roadkeep governs {', '.join(self.files)} — ask, never read them whole: "
            "`roadkeep brief` starts a task, `show <id>` and `list --block <x>` answer "
            "the rest, and a hand-edit is refused."
        )


def announce(payload: Mapping[str, object], root: str | Path = ".") -> Notice | None:
    """Compose what a starting session is told, or ``None`` where there is nothing to say.

    Silence outside a roadkeep project, on the same argument the barrier makes about
    `allow`: a hook that speaks in every repository is a hook every repository pays for.
    Failure is silence too — a session that cannot start because a `roadkeep.toml` has a
    typo in it is a worse outcome than one told nothing, and `lint` still refuses the file.
    """
    try:
        config = Config.discover(_cwd(payload, root))
    except (ConfigError, OSError, tomllib.TOMLDecodeError):
        return None
    if config.source is None:
        return None
    files = tuple(config.relative(path) for path in config.paths.values())
    return Notice(files=files) if files else None


def guard(payload: Mapping[str, object], root: str | Path = ".") -> Refusal | None:
    """Decide one `PreToolUse` call: ``None`` allows, a :class:`Refusal` denies.

    ``root`` is only the fallback for a payload with no ``cwd`` — the paths in the tool
    input decide which project's configuration applies, because one hook process serves
    every repository the session touches.
    """
    tool = payload.get("tool_name")
    if not isinstance(tool, str) or tool not in GUARDED_TOOLS:
        return None
    base = _cwd(payload, root)
    if tool in ASK_TOOLS:
        return _mentioned(payload.get("tool_input"), base, tool)
    for path in _targets(payload.get("tool_input"), base):
        found = governed(path)
        if found is None:
            continue
        config, role = found
        return Refusal(
            tool=tool, path=config.relative(path), role=role, exists=path.is_file()
        )
    return None


def _mentioned(raw: object, base: Path, tool: str) -> Refusal | None:
    """The governed path a shell command spells, or ``None`` (RK128).

    Not a parse and not a heuristic about what the command *is*: the question is only whether
    one of the handful of paths this project declares occurs in the string at all, which is the
    single thing decidable without knowing what `sed`, a heredoc or a `python -c` would do with
    it. A command naming none of them is the overwhelming majority and costs one config read.

    Nothing is allowlisted, because nothing needs to be: roadkeep's own commands address a
    task by **id and role**, never by path, so the verbs this refusal recommends do not
    trip it — which is a fact `tests/test_guarding.py` holds rather than a hope.
    """
    if not isinstance(raw, Mapping):
        return None
    command = raw.get("command")
    if not isinstance(command, str) or not command:
        return None
    try:
        config = Config.discover(base)
    except (ConfigError, OSError, tomllib.TOMLDecodeError):
        return None
    if config.source is None:
        return None
    spelled = _comparable_text(command)
    for role, declared in config.paths.items():
        relative = config.relative(declared)
        # Both spellings, because a command may name the file either way and the substring is
        # the whole test: `./docs/ROADMAP.md` and a quoted absolute path both contain one.
        if any(_comparable_text(form) in spelled for form in (relative, str(declared))):
            return Refusal(
                tool=tool, path=relative, role=role, exists=declared.is_file()
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
    if report.clean:
        return None
    narrowed = _this_turn(config, report)
    return Review(report=narrowed) if narrowed.findings else None


def _this_turn(config: Config, report: Report) -> Report:
    """The same report, keeping only findings on lines the working tree changed (RK60).

    The hook answers "did this turn leave the file in a state the format rejects", and a
    project that adopted the tool with drift already in it would otherwise have every turn
    blocked by history — 278 findings in Shio, none of them the session's. `roadkeep lint`,
    the pre-commit hook and the Action are unchanged: they answer "is this file correct".
    """
    per_file: dict[str, frozenset[int] | None] = {}
    kept = []
    for finding in report.findings:
        if finding.file not in per_file:
            per_file[finding.file] = changed_lines(config, "HEAD", config.root / finding.file)
        changed = per_file[finding.file]
        # `None` is git declining to say, and a finding about the file itself (a budget) has
        # no line to compare — both are judged, because neither can be excused.
        if changed is None or finding.lineno is None or finding.lineno in changed:
            kept.append(finding)
    return replace(report, findings=tuple(kept))


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


def _comparable_text(text: str) -> str:
    """A path *inside* a longer string, as this filesystem compares them (RK128).

    The same `normcase` rule as above and for the same reason — on Windows it also settles the
    separator, so a command written with `/` and a declaration held as `\\` are one string. Not
    `resolve`: there is no path here to resolve, only characters that may contain one.
    """
    return os.path.normcase(text)


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
