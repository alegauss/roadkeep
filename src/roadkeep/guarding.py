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
  `Stop` hook still runs `lint` behind it — and, since RK175, :func:`attested`, because a
  `sed` the user approves leaves a *conforming* line `lint` has no quarrel with.
* **The decision travels in the payload, never in the exit code.** The harness reads a
  non-zero exit as *the hook itself failed*, so this is the one command in the package that
  always exits 0 (see :func:`roadkeep.cli._guard`) and says everything in its output.

The same process answers `SessionStart` (RK82), because the barrier only ever spoke to a
session that had already decided to write: :class:`Notice` states which files are governed
here, once, before the first read. The other candidate — a `PreToolUse` matcher on the
reading tools — is not taken, on the argument `Bash` gets above: paying on every read to
catch what one resident line already said is a tax, and reading is never refused anyway.

That start is also where a **drifted vendored copy** is named (RK234). `install --check` was
the gate holding the copy in step and no adopting project ran it, so a session read a skill
78 lines behind the file it came from with the trust of the original. Asked here because this
process *is* the wired checkout and the copy is what the session is about to load, and cheap
enough to ask unconditionally: :func:`~roadkeep.installing.stale` costs one `is_file` where
there is no copy at all.

**One module, three events, and each event's imports are its own** (RK260). What the three need
is disjoint: `PreToolUse` wants the config, the tool names and the invocation; `SessionStart`
wants :func:`~roadkeep.installing.stale`; `Stop` wants `linting`, `attesting` and `history`.
Imported at module level, that made the hook the harness waits for on *every* Edit, Write and
Bash pay for the linter it will not run — measured at **84.5 ms and 25 modules**, against 50.1
and 7 once each import moved into the branch that uses it, and 44.6 and 5 once `Document` and
`LockBusy` followed (RK261). Interleaved, warm, minimum of nine rounds per tree: the first pass
at this reported 141 against 66 from one sample each, and single-shot import timings on this
machine drift far enough that a tree with *five* modules measured slower than one with seven.
The module count is the exact half of the claim and the milliseconds are one machine's.

This is the opposite trade from RK202,
and for the opposite reason: the MCP server is one process answering many messages, so a lookup
it repeats is worth hoisting, while the guard is a **fresh process per hook call**, so every
import it holds is paid again. RK176 bought the floor below this with
:mod:`roadkeep.screening`, which answers "there is certainly nothing here" out of the standard
library; this is the same argument for the payloads that get past it.

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
from typing import TYPE_CHECKING

from roadkeep.config import Config, ConfigError, find_config
from roadkeep.provenance import WIRED, invocation, served_by
from roadkeep.remedying import Door, alongside, offered

if TYPE_CHECKING:  # annotations only, and already strings — see the docstring's sixth decision
    from roadkeep.attesting import Unattested
    from roadkeep.linting import Finding, Report

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
#: a number a test holds, exactly as `[budgets]` holds `agents.md` (RK30). It prices the line
#: every session gets; the drift sentence (RK234) is over it deliberately and is not resident
#: — it appears only while a copy has drifted and goes away with one `install`.
#:
#: Raised from 260 by RK1242, which is the deliberate act a counted limit exists to make
#: visible. What it bought is the fallback clause on a project that declares the server: a
#: line naming an interface that never arrives sends a session to re-derive by hand
#: everything this line exists to stop it re-deriving, which is worth more than the sixty
#: characters. Sized for the longest invocation a wired project has — the committed launcher,
#: `python .roadkeep/scripts/roadkeep.py` — rather than for the console script.
#:
#: Counted in **UTF-16 code units** since RK1243, which is how every other length in this
#: package is counted (RK430) and how `cost --session` now reports this one: a read and a
#: gate that measured the same line two ways would disagree on exactly the line carrying a
#: character outside the BMP, which is the marker this tool writes.
_NOTICE_BUDGET = 320

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
        # And the words on it (RK1204): the drop above is refused the moment a line is filed
        # under the label, so a heading's title was correctable only while nobody read it.
        ('block amend <x> --title "…"', "correct a heading's words; the label and work stay"),
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
        # The second read before a proposal (RK385), and beside the first for the same
        # reason: a duplicate is not refusable, and the measurement that says so is the
        # *score* and not the rank (RK441). BM25 over the 426 shipped symptoms this ledger
        # held when it was taken ranks the true partner of all four `superseded by` pairs at
        # #1 to #3 across the file — the ranking is fine. Two of those four score below the
        # 13th percentile of the top-1 score a proposal with **no** duplicate produces, so a
        # threshold catching all four flags 419 of the 426. Relative order inside one query
        # carries signal and the absolute score carries none, which makes a gate impossible
        # rather than merely unreliable — and it holds however good the ranking gets, where
        # the rank this replaced argued the same right decision from a figure the ledger
        # contradicts. Two people describing one problem use disjoint words. So the block
        # states what it delivered and the author reads it, which costs one call against a
        # claim and a retirement.
        ("delivered <x>", "what this block already shipped, as claims — also before `add`"),
        # The other list this file holds that is not task lines (RK325), and the reason it
        # arrived: the queue used to live in the config, which nothing governs — right for
        # the prefix and the limits, wrong for a list whose every token names work that leaves.
        ("priority add <token>", "an id or 'Block X' jumps the id order; --first, --after"),
        ("priority drop <token>", "an entry that has shipped, or stopped being urgent"),
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
        # Which is why the retitle reaches it at all (RK1204): a heading standing over history
        # is one that can never be dropped, so its words were correctable by nothing.
        ('block amend <x> --title "…"', "correct a heading's words over entries it keeps"),
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

def _doors(rows: tuple[tuple[str, str], ...]) -> tuple[Door, ...]:
    """One table's rows as doors, which is what a spelling is decided from (RK488).

    The tables above stay strings — they are read by people as much as rendered — and the
    split is `Door`'s own: an argv joined by single spaces renders back to the line it was
    written as, which is the round-trip L3 asks of a task line, one file over.

    This module composed both spellings itself until RK488, and `_tool_for` was the half that
    made it look cheap: it matched the subcommand path and never asked whether the tool takes
    the flags beside it, so `lint --fix` was offered as `mcp__roadkeep__lint` — RK16 keeps
    `--fix` where a human is standing, so the row named a call the session cannot make. That
    question is `serving.serves`' now, asked once for every surface.
    """
    return tuple(Door(tuple(command.split()), purpose) for command, purpose in rows)


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
    #: The prefix this session's tools arrive under (RK333) — the bare `mcp__roadkeep__`
    #: where a project declares the server, and `mcp__plugin_<plugin>_roadkeep__` where a
    #: plugin provides it. A field and not a call, because it is a fact about the *project*
    #: being refused and one hook process serves every repository the session touches.
    #:
    #: `""` is the third state and not a missing value (RK447): this session has no server
    #: for them, so there is no tool table to print.
    #:
    #: And it is the **default** since RK1247, where it used to be the bare prefix on the
    #: argument that this is what every wired project has. That argument is RK333's, from
    #: when the choice was *between two prefixes*; RK447 ended it. A project that
    #: pip-installed roadkeep and never ran `install` has neither scope and no tools at all,
    #: and naming a route it cannot call spends a turn being told the tool does not exist
    #: before it reaches the command that works — worse than naming none. Unreachable through
    #: the hook, where both doors pass `served_by` and `tests/carrying.py` holds them to it;
    #: what the default reaches is every caller building one without the field, and each of
    #: those was getting the answer RK447 argued against. The four carriers now say one thing.
    served: str = ""

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
    def commands(self) -> tuple[Door, ...]:
        return _doors(_INSTEAD.get(self.role, ()) if self.exists else _SCAFFOLD)

    @property
    def tools(self) -> tuple[Door, ...]:
        """The commands above that the same plugin also serves as MCP tools (RK58).

        Named first, because since RK57 the plugin installs with no `pip install` and no
        PATH entry: on that machine the tool is the route that is certainly there and
        `roadkeep add` is a `command not found` waiting to teach that the advice is wrong.

        **Empty where this session has no server for them** (RK447), which is the same
        argument read backwards. A project that pip-installed roadkeep and never ran
        `install` has neither scope, and led with a prefix it cannot call the agent spends a
        turn being told the tool does not exist before it reaches the command that works —
        naming an edit that cannot be made, which is worse than naming none (RK16). The
        `else` branch below is then the whole answer, and it was already there: this is a
        denial, and the one thing it owes is the command that closes it. That `install`
        would give this project the tools is true and is the notice's to say (RK444); a
        refusal is a bad place to advertise.
        """
        if not self.served:
            return ()
        # A door whose served spelling is its shell one is a command this session does not
        # serve, which is the renderer's answer rather than a second lookup here (RK488).
        return tuple(
            door for door in self.commands if door.named(self.served) != door.command
        )

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

    @property
    def _repairing(self) -> list[str]:
        """The shorter route, for the write that is a repair (RK424).

        This table is keyed by **role**, deliberately: the hook never reads what the agent
        was about to write — the module's last paragraph is about exactly that — so it
        cannot narrow fourteen commands to one, and a table keyed by intent would be a table
        keyed by a guess.

        But since RK420 the guard is no longer the only thing that speaks. A finding carries
        the command that closes it, so an agent repairing a *reported* line has a route that
        is one call rather than a read of this list — and this refusal is the one place it
        will certainly look, because it is what stopped the `Edit`. So the route is named
        first and the fourteen stay beneath it, for the write that is not a repair.

        What this deliberately does **not** do is run `lint` here. `PreToolUse` is a fresh
        process the harness waits on before every `Edit`, `Write` and `Bash`, held at 44.6 ms
        and five modules by RK261, and loading the linter would spend that budget on every
        write in the repository to answer a question about a few of them. Naming the command
        costs three lines of a string already being composed, and the caller who needs the
        answer is one call away from it.
        """
        # RK448: this paragraph is read *first* — RK424 put it above the tool table — and it
        # spelled all three with the invocation whatever the session had. So on a wired
        # project the line an agent acts on recommended the shell for exactly the verbs the
        # table under it would have served, which is RK58's own argument arriving one
        # paragraph too late. Where the tools are here, this is where they are named.
        #
        # A flag is not a word over that transport: `repair --dry-run` is the `repair` tool
        # carrying `dry_run`. Which spelling, and where a dropped flag is named, is
        # `remedying.offered`'s since RK488 — this states the three doors and nothing else.
        doors = (
            Door(("repair",), "every finding whose remedy is one command, applied in one call"),
            Door(("repair", "--dry-run"), "the same list, printed and not run"),
            Door(("explain", "<code>"), "what one code means, and which doors close it"),
        )
        return [
            "If this edit was repairing something `lint` reported, it already named the "
            "command that closes each finding — so none of them has to be inferred:",
            *offered(doors, self.served),
            "",
        ]

    def __str__(self) -> str:
        """The reason, as the agent reads it: what was refused, why, and what to run."""
        lines = [
            self._opening,
            "",
            "The id, the pointer and every (deps: …) annotation are derived on render, "
            "so a hand-edit is the one path that can leave a line the format rejects — "
            "and a limit discovered after the sentence exists is a limit that costs a "
            "deletion instead of a refusal.",
            "",
        ]
        lines += self._repairing
        if self.tools:
            lines.append("Call instead — this session's tools, where the fields are a schema:")
            lines += offered(self.tools, self.served)
            lines += ["", "Or the same engine in a shell, from the project root:"]
        else:
            lines.append("Call instead, from the project root:")
        # The shell table, rendered by the same function and therefore with the invocation
        # this machine actually has (RK254): since RK57 the plugin installs with no `pip
        # install` and no PATH entry, so `roadkeep add` was advice that answers `command not
        # found` on the machine most likely to read it. `--help` closes the table rather than
        # sitting in it — it is not a role's command, it is what makes the rest readable.
        helped = Door(("<command>", "--help"), "every flag, so none is guessed")
        lines += offered((*self.commands, helped))
        lines += ["", self._reading]
        return "\n".join(lines)

    @property
    def _reading(self) -> str:
        """The three reads, in the spelling the session that will make them has (RK477).

        RK254 gave this sentence `invocation()` for the console script RK57 removed, which is
        right for a shell and was all it got: RK24 split the *writes* into a tools table and a
        shell table, and the closing line stayed below both, composed once. So the message
        offered fifteen writes as tools and then said reading is never refused in a shell the
        reader may not have — measured on a scaffolded project as 15 rendered twice, 3 once.

        Per table, like `_repairing` above it, and a sentence rather than a fourth table: what
        makes these three read as *not* the refused act is that they are not in one. And the
        served form names fields, because `<id>` is an argv and a caller here passes arguments.

        The **spelling** is `remedying.alongside`'s since RK488, and the two sentences stay:
        a served name drops the arguments a shell line shows, so what each verb takes has to
        be said in words there and is already visible here. That difference is prose, which
        is the one thing a renderer may not decide.
        """
        brief, show, listing = alongside(
            (
                Door(("brief", "<id>"), ""),
                Door(("show", "<id>"), ""),
                Door(("list", "--block", "<x>"), ""),
            ),
            self.served,
        )
        if self.served:
            return (
                f"Reading is never refused: `{brief}` starts a task in one call and "
                f"`{show}` joins the line to its rationale, both taking the id; "
                f"`{listing}` prints them verbatim, and takes a block."
            )
        return (
            f"Reading is never refused: `{brief}` starts a task in one call, "
            f"`{show}` joins the line to its rationale, `{listing}` prints them "
            f"verbatim."
        )


@dataclass(frozen=True, slots=True)
class Review:
    """What `lint` found when the turn tried to end (RK14 as the backstop for RK22).

    Only the failing tier: a :class:`~roadkeep.linting.Note` is something the gate says at
    exit 0, and a turn is not worth blocking over a sentence.
    """

    report: Report
    #: The prefix this session's tools arrive under, or `""` where it has none (RK448). The
    #: same field :class:`Refusal` carries and for the same reason: this message is what an
    #: agent acts on to unblock itself, and it named the shell on projects whose `lint` is
    #: pre-approved. A field rather than a call, because one hook process serves every
    #: repository the session touches and the answer is a fact about this one.
    served: str = ""
    #: This project, for the doors below (RK478). Optional because `Review` is constructed
    #: in tests from a report alone, and a rule the table does not vary by needs none — but
    #: `remedy` reads `ref_scheme`, `role` and the queue for the five that do, so the gate
    #: gets it wherever a caller has one.
    config: Config | None = None

    def __str__(self) -> str:
        findings = self.report.findings
        # Both spellings from one renderer (RK488). The engine is the one this machine has,
        # for `Denial`'s reason (RK254) — a gate naming a repair the reader cannot run blocks
        # the turn and withholds the way out of it — and where the session has the tool, that
        # is the route (RK448). `lint --fix` answers the shell on every project without being
        # asked to: `--fix` writes, RK16 keeps it where a human is standing, so the served
        # `lint` does not expose it and `Door.named` declines the prefix by derivation.
        lint_ = Door(("lint",), "").named(self.served)
        fixing = Door(("lint", "--fix"), "").named(self.served)
        lines = [
            f"{lint_} refuses {len(findings)} line(s) this turn changed in "
            f"{', '.join(self.report.checked)}: a governed file was changed by something "
            f"other than roadkeep, and the format is what the next reader trusts.",
            "",
        ]
        lines += self._findings(findings, lint_)
        lines += [
            "",
            # Six repairs, held against `fixing.REPAIRS` by a test and not imported (RK355):
            # this module stays out of that import path, which is what RK260 bought.
            #
            # The one route here that keeps the invocation on every project (RK448), and it
            # says so: `--fix` writes, and RK16 puts it where a human is standing — so the
            # served surface withholds it deliberately (`lint` is exposed there without it),
            # and a prefix glued to this line would name a tool that does not exist.
            f"`{fixing}` repairs what is derived (annotation, pointer, dep "
            f"order, marker codepoint, whitespace, dead queue entry, orphaned criteria "
            f"heading); everything left is "
            f"editorial and wants a command, not an edit."
            + (
                " That one is the shell whatever this session serves: `--fix` writes, so "
                "the tool surface withholds it."
                if self.served
                else ""
            ),
        ]
        return "\n".join(lines)

    def _findings(self, findings: tuple[Finding, ...], lint_: str) -> list[str]:
        """Each finding, and under it the door RK420 gave it (RK478).

        The gate was the one surface that withheld it: it printed the address and the
        sentence and closed on *everything left is editorial and wants a command*, which
        says one exists and not which — so a turn stopped here called `lint` again to read a
        report already composed. Measured on a copy of Shio, three `path.missing` with three
        doors and none of them shown.

        Grouped exactly as `cli._print_findings` groups (RK469), by `(code, file, shared)`
        and printed at the first member, and the **cap counts groups** — it exists for
        length, and a group is what costs lines. That is what makes the doors affordable:
        on Turing, 35 findings reach 11 groups and all of them are shown, where the same cap
        ungrouped prints 12 and hides 23. Shio's three fold to nothing because they declare
        no shared fact, which is the emitter's answer and the right one.

        The mechanical class stays counted and not printed: the `lint --fix` sentence below
        is already that remedy, said once for all of them, which is RK420's own rule.
        """
        # RK260: this module's imports are per event, and a door is only ever printed here.
        from roadkeep.remedying import remedy  # noqa: PLC0415

        runs: dict[tuple[str, str, str], list[Finding]] = {}
        for finding in findings:
            if finding.shared:
                runs.setdefault((finding.code, finding.file, finding.shared), []).append(finding)
        lines: list[str] = []
        seen: set[tuple[str, str, str]] = set()
        shown = covered = 0
        for finding in findings:
            key = (finding.code, finding.file, finding.shared)
            run = runs.get(key, []) if finding.shared else []
            if len(run) > 1 and key in seen:
                continue
            if shown == _MOST_FINDINGS:
                break
            seen.add(key)
            shown += 1
            covered += max(len(run), 1)
            lines += self._group(finding, run)
            found = remedy(finding, self.config)
            if found is not None and found.kind != "fix":
                lines += [f"    {one.lstrip()}" for one in found.spoken(self.served).splitlines()]
        if covered < len(findings):
            left = len(findings) - covered
            lines.append(f"  … and {left} more — `{lint_}` prints all of them")
        return lines

    @staticmethod
    def _group(finding: Finding, run: list[Finding]) -> list[str]:
        """One row, or the pair a run of two or more folds to — `cli._print_findings`' shape."""
        if len(run) < 2:
            return [f"  {finding}"]
        return [
            f"  {finding.file}  {finding.code}  {len(run)} addresses {finding.shared}",
            f"    {'  '.join(f'{one.token}:{one.lineno}' for one in run)}",
        ]


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
    #: The vendored surfaces that have drifted from the checkout answering (RK234). Said in
    #: this line and nowhere else because this is the one moment it is both cheap to ask and
    #: early enough to act on — the copy the session is about to trust is the skill.
    stale: tuple[str, ...] = ()
    #: The prefix this session's roadkeep tools arrive under, or `""` where there are none
    #: (RK444). The route this line names, and the reason it is a field rather than a call
    #: inside `__str__`: which engine answers is a fact about the project, decided where the
    #: project is read, and a `Notice` built by a test says which case it is testing.
    served: str = ""

    def __str__(self) -> str:
        # And the first message of the session is the first place the invocation has to be one
        # this machine has (RK254) — it is the line teaching that reading is a command.
        #
        # Where the tools are served, that is the route (RK444). This is the only message
        # every adopting session gets, and it named the shell on exactly the projects whose
        # tools are pre-approved: the deny lists them correctly and fires only on a hand-edit,
        # which the agent that behaves never makes, and the skill's copy waits on a trigger,
        # one sentence among two hundred and fifty. What is stated is which engine answers —
        # the same kind of fact as which files are governed — and never the write path, which
        # stays the skill's, a rule in two places being two places that can disagree.
        #
        # One renderer for the three spellings since RK488, and `alongside` is the half this
        # line paid for: a served name is self-contained, and three shell lines each carrying
        # the invocation is 46 characters of repetition inside a 260-character budget.
        brief, show, listing = alongside(
            (
                Door(("brief",), ""),
                Door(("show", "<id>"), ""),
                Door(("list", "--block", "<x>"), ""),
            ),
            self.served,
        )
        asks = f"`{brief}` starts a task, `{show}` and `{listing}` answer the rest"
        said = (
            f"roadkeep governs {', '.join(self.files)} — ask, never read them whole: "
            f"{asks}, and a hand-edit is refused."
        )
        # And what to do when they do not arrive (RK1242). Measured over one long session on a
        # project that vendors roadkeep: this line named the tools, the harness reported the
        # server as still connecting, and they never appeared — two searches minutes apart
        # found none, and every call for the rest of the session went through the launcher.
        # Nothing was lost, which is why it is worth saying: the CLI answered everything, so
        # the only cost was a paragraph about an interface that was not there, and an agent
        # that trusted it would have waited or reported the capability as unavailable.
        #
        # Where the project **declares** the server and not where a plugin provides it: the
        # connection that can fail this way is the launcher this repository wrote, spawned by
        # the harness, and a plugin's server is the harness's own machinery. So this appears on
        # the projects the failure was measured on and stays off the rest.
        #
        # Read off `served` and never carried beside it (RK1244). RK1242 added a second field
        # for this, which was a three-way answer stored as two — and the pair `mcp__plugin_…`
        # with `declared = True` is a project whose server is both, which `serving` cannot
        # produce and a caller could construct without noticing. `WIRED` **is** the declared
        # case, by that function's own first branch, so there was never a second fact to hold.
        if self.served == WIRED:
            said += f" `{invocation()}` is the same engine if they never arrive."
        # The invocation stays here whatever the clause above chose (RK444): `install` runs
        # once per project and is deliberately not on the served surface — so it is one more
        # door through the same renderer, and the shell form is what comes back because
        # nothing serves the verb, rather than because this line remembered not to ask.
        if self.stale:
            installing = Door(("install",), "").named(self.served)
            said += (
                f" This project's copy of {', '.join(self.stale)} has drifted from the "
                f"checkout answering here: `{installing}` refreshes it, and until then "
                f"the copy is not what this session is running."
            )
        return said


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
    if not files:
        return None
    # Asked here and not on a `PreToolUse`, for the reason the notice itself is: the copy a
    # session trusts is the skill it loads, and by the first write it has been read (RK234).
    from roadkeep.installing import stale  # noqa: PLC0415 - RK260 the SessionStart path only

    # `serving` and not `served_as` (RK444): a refusal has to recommend something and the
    # bare prefix is the right guess wherever nothing says otherwise, but this line is read
    # by every adopting session including the ones with no tools at all, and there naming a
    # prefix nobody can call is worse than naming the shell.
    return Notice(files=files, stale=stale(config.root), served=served_by(config.root))


@dataclass(frozen=True, slots=True)
class Advice:
    """A hand edit that is allowed, and the door four of its tables now have (RK1280).

    The guard does not govern `roadkeep.toml` — "which a human edits by hand on purpose" —
    and half of that stopped being true: `[limits]`, `[budgets]`, `[tools]` and `[claims]`
    have a verb that takes the reading first and refuses a number this corpus already breaks.
    So the two writers disagree about what is checkable, and the unchecked one is the default.

    **Denying it is the wrong answer**, and the reason is the shape of the file: a hook sees a
    path and not a table. `[files]`, `[markers]`, `[refs]` and `[grammar]` have no verb and
    are not going to get one, so a denial would make the config unwritable in the sessions
    that need it most — including the one where `install` has not run yet.

    What this is instead is the register the barrier deliberately has no other use for: it
    **decides nothing**. `permissionDecision: "allow"` would grant the write and wave through
    the permission rules the user set for every other file (RK1202), so this carries no
    decision at all — only the sentence, on the one path a session touches twice a year.
    """

    #: As the project spells it, for :class:`Refusal`'s reason: a message quoting an absolute
    #: path is a message about one machine.
    path: str
    #: The prefix this session's tools arrive under, or `""` — :class:`Refusal`'s field and
    #: its argument exactly, so the door named is one this session can actually call.
    served: str = ""

    def __str__(self) -> str:
        from roadkeep.governing import GOVERNED  # noqa: PLC0415 - RK260

        tables = ", ".join(f"[{one.split('.')[0]}]" for one in GOVERNED)
        governing = Door(("govern", "<key>", "<n>"), "").named(self.served)
        listing = Door(("config",), "").named(self.served)
        return (
            f"{self.path} is yours to edit and this is not a refusal — but {tables} are "
            f"numbers a reading decides, and `{governing}` takes that reading and refuses "
            f"one this project already breaks, where a hand edit lands it and the gate "
            f"reports it on the next run. `{listing}` says what may be declared here."
        )


@dataclass(frozen=True, slots=True)
class Barrier:
    """What one `PreToolUse` call answers: a refusal, a sentence, or neither (RK1283).

    One record because it is **one walk**. `guard` resolved the config per target and threw it
    away on the way to `None`, and `advise` then discovered the same file again — one
    `find_config` walk and one `tomllib` parse per *allowed* write, on the path every `Edit` a
    session makes goes down. What the barrier has always been careful about is what an allowed
    call costs; this is that care, kept while the sentence was added.

    The order is a rule and not an ordering (RK1280): the advice is held rather than returned
    while any target may still be governed, because a call producing both would be two
    messages about one write.
    """

    refusal: Refusal | None = None
    advice: Advice | None = None


def decide(payload: Mapping[str, object], root: str | Path = ".") -> Barrier:
    """Both answers, from one reading of the project (RK22, RK1280, RK1283).

    ``root`` is only the fallback for a payload with no ``cwd`` — the paths in the tool input
    decide which project's configuration applies, because one hook process serves every
    repository the session touches.
    """
    tool = payload.get("tool_name")
    if not isinstance(tool, str) or tool not in GUARDED_TOOLS:
        return Barrier()
    base = _cwd(payload, root)
    if tool in ASK_TOOLS:
        # A command only *mentions* a path, so there is nothing here to advise about either:
        # a sentence about four tables attached to a call that may be reading the file is
        # prose about a write nobody made.
        return Barrier(refusal=_mentioned(payload.get("tool_input"), base, tool))
    advice: Advice | None = None
    for path in _targets(payload.get("tool_input"), base):
        config = owning(path)
        if config is None:
            continue
        role = role_at(config, path)
        if role is not None:
            return Barrier(
                refusal=Refusal(
                    tool=tool,
                    path=config.relative(path),
                    role=role,
                    exists=path.is_file(),
                    served=served_by(config.root),
                )
            )
        if config.source is not None and _comparable(path) == _comparable(config.source):
            advice = Advice(
                path=config.relative(config.source), served=served_by(config.root)
            )
    return Barrier(advice=advice)


def advise(payload: Mapping[str, object], root: str | Path = ".") -> Advice | None:
    """The one thing to say about a write this gate allows, or ``None`` (RK1280).

    Narrow twice over. Only the project's **own declaration** — the config this path resolves
    to, so a `pyproject.toml` that configures nothing here says nothing — and only where
    nothing was refused, which :func:`decide` establishes in one pass.

    Kept as its own name for :func:`guard`'s reason: it is the question a reader outside this
    module asks, and the tests that hold this boundary are written against it.
    """
    return decide(payload, root).advice


def guard(payload: Mapping[str, object], root: str | Path = ".") -> Refusal | None:
    """Decide one `PreToolUse` call: ``None`` allows, a :class:`Refusal` denies.

    :func:`decide`'s refusal half, kept as its own name because that is the question every
    caller outside this module asks and the one the tests are written against.
    """
    return decide(payload, root).refusal


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
                tool=tool,
                path=relative,
                role=role,
                exists=declared.is_file(),
                served=served_by(config.root),
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
        from roadkeep.linting import lint  # noqa: PLC0415 - RK260 the Stop path only

        report = lint(config)
    except (KeyError, OSError):
        return None
    if report.clean:
        return None
    narrowed = _this_turn(config, report)
    if not narrowed.findings:
        return None
    return Review(report=narrowed, served=served_by(config.root), config=config)


def attested(payload: Mapping[str, object], root: str | Path = ".") -> Unattested | None:
    """The other half of the same `Stop`: bytes no verb wrote, stated once (RK175).

    Beside :func:`review` rather than inside it, because the two answer different questions
    and only one of them is about the format: `lint` asks whether the file is correct, and
    this asks whether roadkeep put it there. A conforming hand-edit passes the first and is
    the entire subject of the second, so folding them would hide it behind a clean report.

    Silence on every failure and on `stop_hook_active`, on the rules the rest of this module
    keeps: a broken config must not pin a session open, and blocking twice on one fact is a
    loop. :mod:`roadkeep.attesting` re-baselines as it reports, so the second pass is silent
    even where the harness never sets the flag.
    """
    if payload.get("stop_hook_active") is True:
        return None
    try:
        config = Config.discover(_cwd(payload, root))
    except (ConfigError, OSError, tomllib.TOMLDecodeError):
        return None
    if config.source is None:
        return None
    from roadkeep.attesting import unattested  # noqa: PLC0415 - RK260

    return unattested(config)


def _this_turn(config: Config, report: Report) -> Report:
    """The same report, keeping only findings on lines the working tree changed (RK60).

    The hook answers "did this turn leave the file in a state the format rejects", and a
    project that adopted the tool with drift already in it would otherwise have every turn
    blocked by history — 278 findings in Shio, none of them the session's. `roadkeep lint`,
    the pre-commit hook and the Action are unchanged: they answer "is this file correct".
    """
    from roadkeep.history import changed_lines  # noqa: PLC0415 - RK260 the Stop path only

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


def owning(path: str | Path) -> Config | None:
    """The project whose declaration covers ``path``, or ``None`` (RK1283).

    The half :func:`governed` and :func:`advise` share, split out because both of them wanted
    it on the same call: the barrier resolved the config per target, threw it away on the way
    to `None`, and the advice then discovered the same file again — one `find_config` walk and
    one `tomllib` parse per **allowed** write, which is the path every `Edit` a session makes
    goes down.

    Discovery walks up from the file itself, so the answer does not depend on where the hook
    process happened to be started.
    """
    found = find_config(Path(path).parent)
    if found is None:
        return None
    try:
        return Config.load(found)
    except (ConfigError, OSError, tomllib.TOMLDecodeError):
        return None


def role_at(config: Config, path: str | Path) -> str | None:
    """Which governed role this path holds in that project, or ``None``.

    `roadkeep.toml` is *not* governed: it is the per-project declaration (L6), which a human
    edits by hand on purpose — and since RK1280 is told what four of its tables now have.
    """
    wanted = _comparable(Path(path))
    for role, declared in config.paths.items():
        if _comparable(declared) == wanted:
            return role
    return None


def governed(path: str | Path) -> tuple[Config, str] | None:
    """The project that owns ``path`` and the role it holds there, or ``None``.

    The pair the two readers above compose, kept because it is the question every caller
    outside this module asks — one path, one answer — and because the tests that hold this
    boundary are written against it.
    """
    config = owning(path)
    if config is None:
        return None
    role = role_at(config, path)
    return None if role is None else (config, role)


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
