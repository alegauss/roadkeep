"""The commands as MCP tools, so the field schema *is* the tool's input schema (RK24, RK59).

A CLI reached through `Bash` puts the field names in prose. `--symptom` is typed from memory,
`--dep` is guessed as `--deps`, and the answer is a usage string the caller pays for after the
sentence was already composed. Over MCP the same fields arrive as a JSON Schema the client
validates *before* the call, which is L1 moved one layer further out: not the write path
refusing bad prose, but the protocol refusing a wrong argument name.

What that costs, and how each cost is avoided here:

* **No second implementation.** A tool call is translated into the argv the CLI accepts and
  dispatched through :func:`~roadkeep.cli.build_parser`'s own handler, in-process. The exit
  code becomes `isError`, and the refusal an agent reads over MCP is byte-identical to the one
  it reads in a terminal. Two code paths that both "add a task" is the drift this repo exists
  to remove, so there is one.
* **No duplicated schema.** Every property is derived: its type and description come from the
  argparse action, its bounds from `roadkeep.toml` — `maxLength` is this project's `symptom`
  and `why` limits, `enum` is its declared markers, `pattern` is its id shape, and a prose
  body's budget is said in words because that is the unit it is declared in (L6). A tool
  description is the subcommand's own `description`, so a flag renamed in `cli.py` cannot
  leave the schema describing something that is gone.
* **stdio, and no listener.** "No server" is a non-goal about *the store*: this speaks
  JSON-RPC on stdin and stdout, binds no port and caches no file. The config is re-read per
  message, so a `roadkeep.toml` edited mid-session is the one the next `tools/list`
  describes — and because the *code* reading it is not, a refusal says so when this package's
  own modules moved after they were imported (RK155). The one thing held between messages is
  :class:`Watch`, and it holds no fact about the project: only a digest of the tool list this
  connection was **sent**, so `notifications/tools/list_changed` can be sent when it ages
  (RK177). A stateless server cannot derive what it already told somebody.
* **stdin is the transport, so a handler never gets it.** `call` dispatches in-process through
  the CLI's own parser, and three handlers read a paragraph from a pipe (RK9). Given the
  client's pipe, one of them waits for an EOF no live client sends and eats every message queued
  behind it — 18 minutes, holding the lock (RK170). :func:`_spent_stdin` substitutes a stream
  already at EOF, which turns the deadlock into the refusal the format already owns. *Which*
  three is :class:`Prose` on their own parsers rather than a comment in one handler (RK171), so
  the argv is refused before it gets there and a fourth is named by a test and not by a session.
* **A broken config still starts.** `mcp` tolerates a `ConfigError` for the reason `guard`
  does: the process is launched once for the whole session, and refusing to start would take
  the tools away exactly when a typo in the config most needs the gate. `tools/list` then
  describes the defaults, and the error is what the first `tools/call` returns.

The surface is what a task needs end to end, which RK24 got wrong by half. It exposed four
because one roadmap line named four, on the argument that the reads were "one `Bash` call
away" — and RK57 then made a plugin install with no console script at all, so on that machine
there is no shell command to fall back to. Starting a task needs `brief`, writing a rationale
needs `section add`, a line that leaves without shipping needs `retire`.

What stays out is what a tool cannot be: `init` and `adopt` run once, before the project is
governed, and `guard` and `mcp` are the harness's own entry points. `lint` exposes one argument
and deliberately not `--fix` — that one writes, and RK16 belongs where a human is standing (the
pre-commit hook), which is what keeps this tool honestly read-only.

`repair` (RK422) is not that decision reversed, and the distinction is worth stating because it
looks like one. Withholding `--fix` is a claim about **`lint`**: a tool a caller reaches for to
*read* a report must not write while answering. It was never a claim that the agent may not
repair — the agent already writes through twenty tools here, and what `repair` runs is those
same verbs, chosen from a table (RK420) instead of from a caller's reading of an English
message. So it grants no capability this surface did not have; it removes the turn spent
composing each command, which is the entire cost RK420 measured. Declared a writer, so the
read-only hint stays true of both, and `dry_run` is the read.

A nested subcommand is one tool: `section add` is `section_add` to the protocol, which has no
space in a name, and two argv words here. One :class:`Tool` holds both spellings rather than a
table mapping between them.
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import io
import json
import re
import sys
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, TextIO

from roadkeep import __version__
from roadkeep.config import PROSE_ROLES, ROLES, Config, ConfigError, Scope
from roadkeep import provenance
from roadkeep.provenance import engine, invocation, serving
# `words` from where it is *defined* and not from `budgeting`, which re-exports it (RK260):
# `config` already loads `schema`, and reaching the name through `budgeting` cost the guard
# 30 ms and eight modules — `authoring`, `sections`, `claiming`, `ids`, `markers` and the
# rest of the write path — on every denied edit, for one character-to-word division.
from roadkeep.kernel.schema import body_aim, width, words

#: The protocol revision this server answers with when the client asks for one it does not
#: know. Negotiation is "echo what the client asked for if we understand it": a server that
#: always answers with its own newest version fails clients that pinned an older one.
PROTOCOL = "2025-06-18"
KNOWN_PROTOCOLS = (PROTOCOL, "2025-03-26", "2024-11-05")

#: JSON-RPC's own codes. Only these three are reachable: a tool that fails is *not* a
#: protocol error — it answers with `isError`, so the model reads the refusal and retries,
#: instead of the client reporting a transport failure it cannot act on.
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601


@dataclass(frozen=True, slots=True)
class Prose:
    """A command that takes a paragraph off a pipe, declared beside the argument (RK171).

    Three exposed tools reach `sys.stdin.read()` and neither `TOOLS` nor `cli.py` said which:
    `add` on a section named with no body, `section add` on a body omitted, `section amend` on
    the `-` its own help documents. `record add` cannot, exposing no body at all — and that
    asymmetry is the point, because it is a property of the two files together and a comment in
    one handler was the whole of it. So the parser declares it, the way :attr:`Tool.writes` made
    `reads_only`/`writes_when` the parser's claim rather than a table beside it (RK167).

    What it buys is not the deadlock — :func:`_spent_stdin` closed that whatever this says — but
    that every one of the three refuses by *naming the argument*, and that a fourth exposed
    tomorrow is named by a test rather than by the session that meets it.
    """

    #: The argument carrying the prose. Omitting it or setting it to :attr:`sentinel` is what
    #: sends the handler to the pipe.
    dest: str
    #: The spelling the CLI documents for "read it from stdin". One string, because a second
    #: sentinel would be a second thing a caller has to know.
    sentinel: str = "-"
    #: Whether *omitting* the argument reads the pipe too, or only the sentinel does. False for
    #: `section amend`, which refuses an amend with neither field rather than defaulting to it.
    omitted: bool = True
    #: The argument whose presence makes the read happen at all, where one does. `add` reads
    #: only when a section was named: an `add` with no rationale must never block on a pipe,
    #: which used to be a comment and is now the thing that says so.
    gated_by: str = ""

    def reached_by(self, arguments: Mapping[str, Any]) -> bool:
        """Whether this argv sends the handler to the pipe."""
        if self.gated_by and self.gated_by not in arguments:
            return False
        if self.dest not in arguments:
            return self.omitted
        return arguments[self.dest] == self.sentinel


@dataclass(frozen=True, slots=True)
class Tool:
    """One subcommand, and which of its arguments an agent is allowed to set.

    :attr:`unconditional` is a whitelist and not a filter: `add --ref` exists for adoption
    (RK18) and would let a caller choose a pointer the tool derives, which is the one thing a
    schema cannot then check.

    :attr:`conditional` is the exception that proves the rule (RK111): where a project declares
    a shape the deriver cannot spell, withholding the field leaves that surface unable to write
    a legal id at all.

    **The answer is :meth:`exposed`, and the two declarations are its halves** (RK1157). That
    field was called `exposes` — one letter from `exposed(config)`, and the shorter of the two —
    so a reader asking what a tool offers got the half that is true on every project and reads
    as total. Two tasks were filed against that reading in three iterations and one was shipped
    before it surfaced: `add exposes: (block, symptom, why, …)` says an outline project cannot
    name its anchor, and `exposed(config)` on that project ends in `ref`. Named for the
    condition it is one side of, so the half is visible as a half.
    """

    #: The subcommand path, space-separated where it is nested (`"section add"`). The argv
    #: is this split; the tool's name is the same with `_`, because a protocol name may not
    #: carry a space and a client shows what it is given.
    command: str
    unconditional: tuple[str, ...] = ()
    #: Arguments this tool always passes, by dest — never exposed, so a caller cannot unset
    #: one. This is how a **flag becomes a tool** (RK150): `readOnlyHint` is one boolean per
    #: tool and `brief --claim` writes while `brief` does not, so the two are two tools over
    #: one command, and the query keeps the hint that makes it free to ask (L5). By dest and
    #: not as literal argv, so the flag is resolved through the same parser every exposed
    #: argument is and a rename cannot leave a tool passing something that is gone.
    always: tuple[str, ...] = ()
    #: The protocol name where it is not the command path. Needed only where :attr:`always`
    #: has put two tools on one command, and it names the **act** rather than the command,
    #: because two names for one path is what a client would otherwise have to tell apart.
    named: str = ""
    #: Arguments exposed only where this project's config makes them the **one** way to spell
    #: a legal value, by dest — the predicate is :data:`_CONDITIONAL` and the bound that then
    #: narrows them to exactly that value is :data:`_BOUNDS` (RK111). By dest and by config,
    #: never by hand: a field a caller may set on one project and not another is a difference
    #: `roadkeep.toml` states (L6), so the tool schema varying is the config being read rather
    #: than this surface holding a second opinion about it.
    conditional: tuple[str, ...] = ()

    def exposed(self, config: Config) -> tuple[str, ...]:
        """Every argument a caller may set on *this* project, in declaration order.

        The conditional ones come last, so the argv stays stable and diffable when a project
        turns one on — a field that reordered the others would make the same call render two
        command lines.
        """
        opened = tuple(dest for dest in self.conditional if _CONDITIONAL[dest].opens(config))
        return (*self.unconditional, *opened)

    @property
    def name(self) -> str:
        """The protocol name: the command path with `_` where its space is (RK59).

        A tool name may not carry a space, and a client shows the name it is given — so
        `section add` is `section_add` there and stays two argv words here. A hyphen goes the
        same way (RK70): `non-goal add` is one command spelled in two conventions, and the
        name a client renders should not be where that shows.
        """
        return self.named or self.command.replace(" ", "_").replace("-", "_")

    @property
    def argv_head(self) -> list[str]:
        return self.command.split()

    @property
    def writes(self) -> bool:
        """Whether a successful call changes a governed file — `readOnlyHint`, derived (RK168).

        Stated per tool until now, and the reason given was `lint`: it writes when `--fix` is
        passed and is read-only *here* only because that flag is not exposed. RK167 gave a
        parser the way to say which flag makes a read a write, and RK168 put it on `lint` — so
        the answer is derivable and stops being a boolean two places could disagree about.

        Two clauses and no table: a command whose parser does not call itself a read writes, and
        a read writes exactly when this tool passes the flag its parser names — exposed, so a
        caller may, or in :attr:`always`, so it always does.

        :attr:`conditional` counts as exposed without asking the config, which is the safe
        direction: a hint that flipped to read-only on some projects would be a client caching
        "free to ask" for a tool that writes, and `readOnlyHint` is a promise or it is noise.
        """
        return self.writes_of(_subparser(self.command))

    def writes_of(self, parser: argparse.ArgumentParser) -> bool:
        """:attr:`writes`, read off a parser the caller already resolved (RK174).

        The same two clauses, against a parser passed in rather than looked up: `descriptor`
        holds this tool's own parser by the time it needs the hint, and resolving it a second
        time was half of what `tools/list` spent.
        """
        if not parser.get_default("reads_only"):
            return True
        # One argument or several (RK307), read through the CLI's own accessor rather than
        # off the default: a tuple compared as a string is a tool whose `readOnlyHint` says
        # free-to-ask about an argv that writes.
        from roadkeep.cli import writes_when  # noqa: PLC0415 - RK260

        settable = (*self.unconditional, *self.conditional, *self.always)
        return any(flag in settable for flag in writes_when(parser))


#: What a task needs end to end (RK24's four, extended by RK59). Order is the order
#: `tools/list` reports: the write path first, then the reads, because that is the order a
#: session uses them in and a client renders the list as given.
#:
#: `init` and `adopt` are deliberately absent — they run once, before the project is
#: governed — and so are `guard` and `mcp`, which are the harness's own entry points.
TOOLS: tuple[Tool, ...] = (
    # `section` and `section_body` are exposed for the reason `section add`'s body is: the
    # rationale is the second half of one write (RK93), and a client that cannot pass it
    # here is one whose every `add` leaves a pointer for the gate to refuse.
    # `task_id` is conditional and every other id on the write path is derived (RK111): a
    # project that declares `[ids] suffix` has a legal shape `spell_id` never produces, so the
    # split the skill prescribes was an invocation only the CLI could make. Opened only there,
    # and bounded to *require* the letter — so what the field buys is the id the counter cannot
    # reach, and never the number it would have handed out.
    # `ref` is conditional for the same reason, one field over (RK241): under `ref_scheme =
    # "outline"` the anchor is the caller's to name and nothing derives it, so withholding it
    # made every `add` on such a project refuse `ref.missing` — the RK141/RK144 deadlock again,
    # with a source checkout as the only remaining door. Closed where the scheme derives the
    # pointer, which is where offering it would be choosing what the tool computes.
    Tool(
        "add",
        ("block", "symptom", "why", "deps", "status", "section", "section_body"),
        conditional=("task_id", "ref"),
    ),
    # The key to a deadlock the agent meets first (RK141): `ship` refuses an undeclared
    # block, the guard denies the edit that would declare it, and no other verb writes a
    # heading — so a correctly wired project could not open a block at all.
    # `after` rides with it (RK145): block order is what `list` reports and what a reader takes
    # for the shape of the plan, and without it a phase belonging between two existing ones was
    # appended after both — repaired only by reordering three files by hand.
    # `organise` rides with them (RK405): a ledger organised by nothing is a project every
    # `ship` refuses and no bare `block add` repairs, and the agent that meets that refusal
    # is the one the guard denies the hand-edit to — a flag only the CLI can reach would
    # leave this surface holding the deadlock the two above exist to break.
    Tool("block add", ("label", "title", "after", "organise")),
    # And the key that could not close the door (RK144). Exposed for the same reason: the
    # caller that opened a label by mistake is the one the guard denies the hand-edit to, and
    # the removal is refused by name over anything filed under it.
    # `prose` rides with it (RK237): the agent that finds a block whose every line shipped is
    # the one the guard denies the `Edit` to, and the note under that heading was the whole
    # obstacle — a flag only a human can pass is no door on the surface this ships for.
    Tool("block drop", ("label", "prose")),
    # The key RK141/RK144's pair never cut (RK403): a doubled heading is the state every write
    # refuses with `merge the two regions by hand`, and the guard denies exactly that edit — so
    # an agent that reaches it over MCP, where there is no hand-edit at all, had no door out.
    # `prose` rides with it (RK237) for the same reason it rides with `block drop`.
    Tool("block merge", ("label", "prose")),
    # The write a session makes first, and the one flag that became a tool (RK149, RK150): it
    # is `brief --claim`, so the answer is everything needed to start the task *and* the
    # marker that stops the next agent being handed it — while `brief` and `pick` below stay
    # honestly read-only, which is what keeps consulting the backlog free.
    Tool(
        "brief",
        ("id", "block", "designed"),
        always=("claim",),
        named="claim",
    ),
    # The *other* verb with that word on it, which the tool above is why nobody noticed was
    # missing (RK308). RK150's own sentence is the finding — a flag only the CLI can reach is a
    # flag the agent this ships for cannot pass — and it applies unchanged to the whole of RK280:
    # an agent driving this over the protocol declared no scope, so every changed path came back
    # `loose` and the analysis `git add -A` cannot make was the one it could not ask for.
    #
    # `named` for the act, which is what the collision argues for rather than against: the tool
    # above *takes a line* and this one *says what the commit owns*. The read half stays at the
    # terminal — `theirs` and `loose` are `git status` in the answering process's checkout, and
    # `ship` already prints the scope it releases at the one moment it is wanted (RK298), so
    # exposing it would add a second answer to a question that is already answered.
    Tool("claim", ("id", "path", "add_path"), named="scope"),
    Tool("status", ("id", "marker")),
    # `lines` for `record amend`'s reason one file over (RK195): this is the door an adopting
    # project reaches for, and an adopted roadmap is the only place a wrapped line comes from.
    Tool("amend", ("id", "why", "deps", "ref", "lines")),
    # The field `amend` excludes, at its own door (RK178). Exposed beside it because the agent
    # that discovers a premise is false is the one executing the line, and the exit designed
    # for it — retire plus add — spends an id and deletes a section that was already right.
    # `typo` rides with it (RK414): which of the two acts a rewording is cannot be inferred
    # from the strings, so it is the caller's declaration — and the caller this surface is
    # for is the one whose every restatement would otherwise read as a premise turning false.
    Tool("restate", ("id", "symptom", "lines", "typo")),
    # The repair a merge needs, exposed for the reason it exists at all (RK97): the agent
    # that hits a doubled id is the one the hook denies a hand-edit to, so a door only a
    # human can reach is no door. `to` is offered because the derived answer is not always
    # the wanted one — it is refused against every source either way.
    Tool("renumber", ("id", "to")),
    # `part` is exposed because the agent shipping half of something is the one that needs
    # it (RK121): without it the only honest options are a ledger entry that overstates and
    # a hand-edited qualifier the grammar reads and no verb maintains.
    # `why` is required on the write path and not merely offered (RK142): the roadmap's
    # sentence is a problem statement, and the entry that inherited it read as a defect
    # report filed under a heading meaning "done".
    # `lines` for `record amend`'s reason (RK193): the ship that completes a partial rewrites
    # that entry's span, and where the ledger arrived wrapped the count is the same door.
    # `superseded_design` because the agent that finds the design stale is this one (RK310):
    # it claimed the line, read the section, and is the only reader who will ever know — and
    # the trace it would otherwise leave is a hand-edit to the file the guard denies.
    Tool("ship", ("id", "why", "part", "lines", "superseded_design")),
    Tool("retire", ("id", "reason", "superseded_by")),
    Tool("defer", ("id", "reason")),
    Tool("resume", ("id", "marker")),
    # `supersedes` rides with it because the revert is one transaction (RK395): the entry that
    # says the work did not hold and the pointer on the entry that says it shipped are two
    # edits an agent cannot make separately — the second one is a hand edit the guard denies.
    #
    # `lines` rode with it until RK1053 narrowed that pointer to the entry's first line, and
    # is withdrawn here (RK1056): the write it authorised no longer exists, so every call it
    # can appear in is refused. The CLI keeps declaring it — a flag somebody's script spells
    # is answered better by `NoSpan` than by argparse — and this surface is re-derived every
    # session, so it has no legacy to keep and pays the cost of one: a published property
    # whose whole description is *refused* is bytes an agent reads before every call it makes.
    Tool("record add", ("block", "symptom", "why", "supersedes")),
    # The ledger's update (RK124). `part` rides with it because a qualifier that stopped
    # being true is the commonest correction an entry needs, and the agent that wrote it is
    # the one the hook denies a hand-edit to.
    # `lines` rides with it for `record drop --line`'s reason (RK179): on a ledger whose
    # bullets wrap, the correction replaces text the parse never held, and the count is the
    # caller saying they read it — a door the agent this ships for has to be able to reach.
    Tool("record amend", ("id", "why", "part", "lines")),
    # The move `record amend` refuses to spell as a correction (RK143). Exposed beside it
    # because an entry filed under the wrong block is what `ship` writes from a line filed
    # under the wrong block — an agent's own slip, and the hand-edit that repaired it is the
    # one the guard denies that agent.
    Tool("record move", ("id", "to_block")),
    # `line` rides with both because the choice is the fix (RK127): two entries for one id
    # can be one slip or two deliveries, and the default picked the entry that earned the id.
    Tool("record drop", ("id", "line")),
    Tool("record renumber", ("id", "line", "to")),
    Tool("non-goal add", ("lead", "why")),
    # The correction the other two bullet grammars had and this one did not (RK368). Exposed
    # beside them for `record amend`'s reason: without it a reworded constraint is a drop and
    # an append, which moves the bullet to the end of a list a reader takes for the plan's shape.
    Tool("non-goal amend", ("lead", "why")),
    Tool("non-goal drop", ("lead",)),
    # The other list this file holds that is not task lines (RK325). Exposed for the reason
    # the non-goals are: the agent that ships a queued id is the one that has to take it out,
    # and the file it now lives in is the one the guard denies an edit to.
    Tool("priority add", ("token", "first", "after")),
    Tool("priority drop", ("token",)),
    # The door the other two could not be reached without (RK427). Exposed because the caller
    # that meets the deadlock is this one: the gate names a defect in `roadkeep.toml`, both
    # verbs above refuse having never opened it, and the hand edit is what the guard denies.
    Tool("priority migrate", ()),
    Tool("section add", ("anchor", "title", "body", "role")),
    # The correction an open task's design needs (RK123). Exposed for the reason the whole
    # write path is: the agent that narrowed a hypothesis is the one the hook denies a hand
    # edit to, and until this verb existed the only way through was shipping the task.
    Tool("section amend", ("anchor", "title", "body", "role")),
    # The address `section amend` refuses to spell as a correction (RK377), and `renumber`
    # cannot reach under an outline. Exposed beside them because the state it repairs is one
    # an adopting corpus arrives with — 13 doubled addresses in Turing — and the only other
    # way through is the hand edit this server's own guard denies the agent making it.
    Tool("section move", ("anchor", "to", "role")),
    Tool("section drop", ("anchor", "role")),
    Tool("non-goal list"),
    Tool("priority list"),
    # `records` is exposed because the caller paying for them is this one (RK264): the
    # percentiles are the answer and the sample was 95% of the payload, so the evidence is
    # a flag an agent disputing the figure can still pass rather than a read it cannot make.
    Tool("weight", ("block", "records")),
    # That read's mirror (RK492), and served for the same reason it is: an agent about to
    # continue a migration asks how many sites are left, and the alternative to a command is
    # a grep whose pattern it composed itself and whose misses are silent (L5).
    Tool("remaining", ("id",)),
    # The other pre-`add` read, and the one this transport needs most (RK190): `maxLength`
    # publishes the field's own ceiling and cannot publish the line's, so without this the
    # binding number reaches the author only as a refusal — a linter, one layer in.
    # `ref` rides with it for the reason the budget exists (RK265): under the outline scheme
    # the pointer is the caller's, and a budget that did not count it approved a why the
    # `add` one call later refused — the verdict-after-the-prose, from the verb that
    # replaces it. Conditional, because under the id scheme there is nothing to name.
    # `anchor`, `role`, `non_goal` and `lead` ride with it because they are the *other two*
    # prose limits (RK283), and both are larger than the line's: a section body is the longest
    # thing an author writes and its ceiling reached them only as a refusal, at 366 words
    # against 300. Over this transport most of all — `maxLength` cannot publish a word count.
    # `file` is the fourth subject (RK345) and the one this transport cannot answer any other
    # way: an agent editing an every-turn file has no `wc` here, so the room it is composing
    # against would otherwise arrive as a gate at the end of the turn.
    # `tools` is the fifth (RK464), and the one subject on this list that is about *this
    # list*: what the schema published here costs a session, which is the read RK30 makes
    # about an every-turn file and nobody had made about the surface. Exposed for `file`'s
    # reason read back — the caller paying it is the one connected to this server.
    Tool(
        "budget",
        # `session` joins them for `tools`' reason and one more (RK1097): it is the read the
        # gate's own message sends a caller to, and a door this surface serves whose call it
        # withholds is the shape `Door.call` returns None for.
        ("id", "block", "deps", "status", "symptom", "anchor", "role", "non_goal", "lead",
         "file", "tools", "session"),
        conditional=("ref",),
    ),
    # `designed` is exposed on both for the reason it exists (RK83): the caller that asks
    # to execute a block over MCP is the one that was handed a design session, and a flag
    # only the CLI can reach is a flag the agent this ships for cannot pass.
    Tool("brief", ("id", "block", "designed")),
    Tool("pick", ("block", "designed")),
    Tool("list", ("block", "role", "marker")),
    Tool("deps", ("id",)),
    # `baseline` and nothing else (RK84): it is the flag that makes the answer readable on a
    # project with standing debt — "did what I just wrote add anything" rather than a count
    # of 317 the caller cannot attribute — and it reads a revision without writing one.
    Tool("lint", ("baseline",)),
    # The verb this whole surface exists for (RK422). `lint` says what drifted and now says
    # what closes each one; this spends that in a single call, which is the difference
    # between a caller that fixes a file and a caller that spends a turn per finding
    # composing the command from a sentence. `dry_run` is the flag that makes it readable
    # before it is trusted — the same argument `install --check` and `adopt` are built on,
    # and the one flag here that changes whether anything is written at all.
    Tool("repair", ("dry_run",)),
    # And the read beside the pair (RK423). A code is the only stable name a defect has, and
    # a caller meeting one first had nowhere to look it up — so the alternative to this tool
    # is grepping the package, which is the context cost L5 exists to remove. `code` is
    # optional here for the reason it is on the CLI: with none, the answer is the vocabulary.
    Tool("explain", ("code",)),
    # The read before a proposal that `non_goal_list` is the other half of (RK385). Exposed
    # because the caller filing the duplicate is this one: RK378 restated RK340 the day after
    # it shipped, and the collision surfaced only once a worker claimed the line.
    # `near` is exposed for the reason the whitelist exists at all, read the other way: it
    # is the caller's sentence and nothing derives it (RK442). This is the read an agent
    # makes immediately before an `add`, over a transport where the whole block arriving as
    # a tool result is the cost L5 is about — so withholding it here would leave the one
    # surface that most needs the narrow answer asking for the file.
    Tool("delivered", ("block", "near")),
    # The eight reads the shipped skill names and this surface withheld (RK463). `serving`'s
    # own opening records that argument being had and settled once: RK24 exposed four tools
    # because one roadmap line named four, on the ground that the reads were "one `Bash` call
    # away" — and RK57 then made a plugin install with no console script at all, so on that
    # machine there is no shell command to fall back to. Counted by the spelling the skill
    # uses for a command: `anchors` five times, `origin` and `reversals` twice, the rest once.
    #
    # `anchors` is the sharpest of them. Under `ref_scheme = "outline"` the pointer is the
    # caller's to name, and the skill says `--next` "is the read an `add --ref` makes every
    # time" — so on a plugin-installed outline project an agent was told to derive an address
    # by a command it had no way to run, while the tool that refuses a wrong one was served.
    #
    # None of the eight writes, so each keeps the read-only hint that makes asking free (L5).
    # What is *not* added is every remaining read: `guard` and `mcp` are the harness's own
    # entry points, `report`, `replay` and `capture filed` are the capture family a person runs
    # against paths on their own disk (RK87, RK1142), and a
    # tool list is context an agent pays for on every turn — so the line is the skill, which
    # is the same authority that decides which command to call in the first place.
    Tool("anchors", ("family", "block", "role", "only_next", "claims")),
    Tool("origin", ("id", "why")),
    Tool("reversals", ("task_id",)),
    # `--prune` writes the registry, so it is withheld exactly as `lint --fix` is (RK16).
    Tool("claims", ()),
    Tool("gaps", ()),
    Tool("next-id", ("family",)),
    Tool("show", ("id", "no_body")),
    Tool("writes", ()),
    # Which copies of this tool write, judge and gate the project (RK415). Exposed because
    # the agent is the one it happens to: its writes go through whatever `roadkeep` the
    # session reaches and its hand edits are denied by whatever the harness installed, and
    # measured live those were 133 versions apart with nothing anywhere saying so.
    Tool("engines", ()),
    # The one query on this list that is not its own subcommand (RK275). `merge` is git's driver
    # contract — three positional paths and an exit code git reads — and none of that belongs in
    # a tool an agent calls, so the verb stays unexposed. `--check` is not that verb sharing a
    # name: it writes nothing, reads the wiring back out of git config, and answers in three
    # lines. RK150's mechanism is what makes that expressible without renaming a flag five
    # decisions now sit behind — `always` puts the act on the surface and `named` calls it what
    # it is, exactly as `claim` is `brief --claim`. Last, because an unwired driver is silent
    # until the merge it was registered for, which is a thing to ask once and never in a loop.
    Tool("merge", always=("check",), named="merge_check"),
)

#: The subcommands above by their first word. Kept because a caller asking "is this command
#: served as a tool" asks about `section`, not `section add`; the refusal that names one
#: (RK58) resolves the full path itself.
TOOL_NAMES = frozenset(tool.argv_head[0] for tool in TOOLS)


#: The long options this CLI declares a dest for, rather than letting argparse derive one,
#: **by subcommand**. Not a flat table and it cannot be one: `--marker` sets `status` on `add`
#: and `--status` sets `marker` on `resume`, so the two spellings cross and a global mapping
#: would answer one of them backwards.
#:
#: Held here so :func:`serves` can answer without building a parser, and asserted **total** in
#: `tests/test_serving.py` against every option every subcommand declares (RK488): the cheap
#: reader and the parser are allowed to differ in cost and not in answer, and a flag renamed
#: in `cli.py` fails there rather than silently costing a door its served spelling.
_DESTS: Mapping[str, Mapping[str, str]] = {
    "add": {"--dep": "deps", "--marker": "status", "--id": "task_id", "--prefix": "family"},
    "amend": {"--dep": "deps"},
    "anchors": {"--next": "only_next"},
    "budget": {"--dep": "deps", "--marker": "status", "--prefix": "family"},
    # The two that call the one sentence `--reason` and accept `--why` beside it (RK1038):
    # the same crossing `--marker` and `--status` make, so the same rows.
    "defer": {"--why": "reason"},
    "list": {"--status": "marker"},
    "next-id": {"--prefix": "family"},
    "record add": {"--id": "task_id"},
    "resume": {"--status": "marker"},
    "retire": {"--why": "reason"},
    "reversals": {"--id": "task_id"},
}


def dest_of(option: str, command: str = "") -> str:
    """The dest this long option sets on ``command`` — `--to-block` is `to_block` (RK488).

    Argparse's own rule where the CLI leaves the dest to argparse, and :data:`_DESTS` where it
    does not. Restated here rather than read off the parser because :func:`serves` is asked
    this inside a hook the harness waits on, and building the parser index costs 117 ms.
    """
    return _DESTS.get(command, {}).get(option) or option.lstrip("-").replace("-", "_")


def serves(argv: Sequence[str]) -> str | None:
    """The tool this session offers for ``argv``, or ``None`` where it offers none (RK488).

    The **cheap** half of what :meth:`~roadkeep.remedying.Door.call` answers, and the half
    the guard can afford: a denial is composed inside a `PreToolUse` the harness waits on,
    held at 44.6 ms by RK261, and building the CLI's parser index to name one tool costs 117
    ms of that. So this reads :data:`TOOLS` and nothing else — the subcommand path answers
    *which* tool, and :attr:`Tool.unconditional` answers whether the flags in the argv are ones
    a caller may pass on **every** project — the half this reader can afford (RK1157). The parser is then only ever asked for the field **values**.

    That second question is the one `guarding._tool_for` did not ask, and `lint --fix` is the
    row that proves it has to be: RK16 keeps the writing flag where a human is standing, so
    the served `lint` has no `--fix` — and the denial's own table offered it as a tool call,
    which is naming a route the session cannot take, on the surface that just stopped an edit.

    Conservative on the two edges, because both fall back to a shell line that is right
    wherever a shell exists: a tool whose :attr:`Tool.always` names a flag serves a narrower
    command than the argv asks about (RK150) and is never the answer to *what runs this*, and
    a :attr:`Tool.conditional` argument is read as withheld, since whether a project opens one
    is a fact about that project (L6) and this reader is given none.
    """
    words = list(argv)
    for length in (2, 1):
        for tool in TOOLS:
            if tool.always or tool.argv_head != words[:length]:
                continue
            passed = (
                dest_of(word, tool.command) for word in words[length:] if word.startswith("--")
            )
            return (
                tool.name
                if all(dest in tool.unconditional for dest in passed)
                else None
            )
    return None


#: Structural, and the reason it is not in the table below: every tool answers as JSON, so
#: `--json` is not a field a caller could set — it is what the transport already is.
STRUCTURAL = "json"

def withheld() -> Mapping[str, Mapping[str, str]]:
    """Every argument a served verb has and does not offer, with the reason it does not (RK1099).

    `unconditional` is a whitelist, which makes withholding the default: a flag added to `cli.py`
    and not listed there is unreachable over MCP and nothing says so. Measured, that is not
    hypothetical — RK1095 added `budget --session` and left it off, and it stayed CLI-only through
    two more tasks. What caught it was a *remedy door* naming the flag; a flag no door names would
    still be missing. :data:`STRUCTURAL` is excluded, being the transport rather than a decision.

    **Read from the parsers and no longer restated here** (RK1169). This was a table of the same
    rows keyed by verb, held true by a test asserting that it and the parsers agreed — which is
    the shape that task is about: not a defect waiting to happen, but a test written to prove two
    places say one thing. `cli.withheld` declares each reason beside the argument it explains, so
    the two cannot disagree and the assertion that held them apart is gone.

    Three kinds of reason, and they are worth telling apart when reading them: **it writes** (RK16
    keeps those where a human is standing), **the tool derives it** (exposing it would let a
    caller choose what the schema then cannot check), and **the shape does not cross** — a path on
    this machine, or a flag whose whole purpose is to change how a terminal prints.

    Not on the hook path: `serves` answers *which tool* from :data:`_DESTS` alone, which is the
    budget RK261 bought, and this builds the parser index that reader deliberately avoids. Every
    caller here is composing a description or a refusal, where that cost is already paid.
    """
    from roadkeep.cli import build_parser  # noqa: PLC0415 - RK260

    out: dict[str, dict[str, str]] = {}

    def walk(parser: argparse.ArgumentParser, path: tuple[str, ...] = ()) -> None:
        for action in parser._actions:  # noqa: SLF001 - argparse exposes no public reader
            if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
                for name, sub in action.choices.items():
                    walk(sub, (*path, name))
        rows = parser.get_default("withheld")
        if rows:
            out[" ".join(path)] = dict(rows)

    walk(build_parser())
    return out


def _markers(config: Config) -> dict[str, Any]:
    """The open markers a caller may write, wherever the field means that set (RK314).

    Above the table rather than beside the other bound functions, because the table names it
    directly and not through a lambda: two dests share one bound here, and a wrapper per dest
    would be the second spelling this exists to prevent.

    The **roadmap's** set, which is what every dest reaching this writes into: `status` refuses
    `✅` as `status.shipped`, so the shipped marker is not a value any of them may carry. The
    changelog's own set is a different question and `list` is the only tool that asks it.
    """
    return {"enum": list(config.schema.markers)}


#: What the config knows about a field that argparse does not: the limit, the marker set, the
#: id shape. This is the whole of RK24 — the bound that refuses the prose and the bound the
#: client validates against are read from the same `roadkeep.toml` (L6).
_BOUNDS = {
    # `maxLength` is what refuses; the word figure is what an author can aim at (RK185). A
    # model has no characters, so a ceiling published only in them is a target reached by
    # trial — and the aim is stated in the sentence rather than as a second keyword, because
    # a client validating word counts would refuse prose this server accepts.
    "symptom": lambda config: {
        "maxLength": config.schema.symptom_max,
        "note": _aimed(config.schema.symptom_max),
    },
    # `maxLength` is the field's own ceiling and not the one that binds (RK183): the line
    # is, and how much of it this field has left depends on the symptom and the deps of the
    # call being composed, which no static number can state. So the ceiling is published as
    # what it is, and the joint rule is said in words beside it — a lower number here would
    # refuse on the client a line the server accepts, which is a bound on the client.
    "why": lambda config: {
        "maxLength": config.schema.why_max,
        "note": (
            f"{_aimed(config.schema.why_max)} The binding limit is the rendered line "
            f"({config.schema.line_max}), which this sentence shares with the symptom and "
            f"with the line's own structure, so the usable maximum is lower than "
            f"{config.schema.why_max} and lower again where the line carries deps. "
            f"`budget` answers it in both units before a word is written (RK190); the "
            f"refusal names what was left, in both units too (RK201)."
        ),
    },
    # The one field whose limit needs no translation, and the one that published none (RK258).
    # `symptom` and `why` get a ceiling and a word aim; the three prose bodies said what the
    # field was and never that a bound existed, so `section = 250` reached an author only as a
    # refusal — measured at two of them in one task, each costing a re-send of the paragraph.
    # No `maxLength`: JSON Schema counts characters, and a character bound derived from a word
    # count would refuse prose this tool accepts, which is a bound on the client (RK183's rule).
    "body": lambda config: {"note": _paragraphed(config)},
    "section_body": lambda config: {"note": _paragraphed(config)},
    # One bound and two dests, because the dest is a spelling and the set is the fact (RK314).
    # `budget --status` is dest `status` and the `status` command's own positional is dest
    # `marker` — the same closed set, and keying by dest published it to the tool that *prices*
    # a line while missing the tool that writes one, which is the call an agent makes on every
    # task it starts. `resume --marker` is the third and was missing for the same reason.
    "status": _markers,
    "marker": _markers,
    # The remaining closed set, and the one that published a sentence (RK304). `section_add`,
    # `section_amend`, `section_drop` and `budget` each describe this as *"which prose file"* and
    # gave the client nothing to validate, so `role = "notes"` was a well-formed call the server
    # refused after it was made. The set is the project's declared prose files — `config.has` over
    # `PROSE_ROLES`, the same narrowing `_paragraphed` makes to decide which limits to publish
    # (RK259), because a role a project declares no file for is one every reader here refuses.
    "role": lambda config: _roles(config, PROSE_ROLES),
    "id": lambda config: {"pattern": config.schema.id_pattern().pattern},
    # Not `id_pattern` (RK111): this is the *chosen* id, and the shape that admits a bare
    # number would admit exactly the choice deriving already makes. The narrower pattern is
    # what keeps the field from being a way around the counter, so it is also checked here and
    # not only published — a bound a client may skip is a bound on the client.
    "task_id": lambda config: {"pattern": config.schema.split_id_pattern().pattern},
}

@dataclass(frozen=True, slots=True)
class Conditional:
    """What opens a :attr:`Tool.conditional` argument, and what a refusal says when it is shut.

    One record and not two tables agreeing (RK252). RK111 wrote the predicate, RK241 wrote the
    sentence beside it, and they are one fact — `ref` is open where `ref_scheme = "outline"`, and
    the refusal says exactly that — so held apart, opening a dest on a second declaration grew
    the predicate a clause while the sentence went on naming only the first. That is the
    arrangement this tool exists to remove, one layer out. Held together, a dest has both halves
    or is not a dest: :func:`_withheld` indexes without a guard, and the failure lands on the
    edit rather than on the caller who passed the closed field (RK251).

    What this cannot do is derive the prose from the predicate. A lambda over `Config` names no
    table, and writing the sentence is what L4 rules out — so the available half is making them
    one object, and it is the half that fails early.
    """

    #: Whether *this* project's config makes the field the only way to write something legal.
    #: A predicate and not a config key, because the question is re-asked per call: a
    #: `roadkeep.toml` edited mid-session is the one this server answers with (RK155's neighbour).
    opens: Callable[[Config], bool]
    #: The clause a refusal adds when it is closed — which declaration would have opened it, and
    #: what the project derives instead. Read as prose after `<dest>: `, so it starts lowercase
    #: and carries no full stop.
    because: str


#: Every conditional argument this surface has, by dest (RK111, RK241, RK252).
_CONDITIONAL: Mapping[str, Conditional] = {
    "task_id": Conditional(
        opens=lambda config: config.schema.id_suffix,
        because=(
            "offered only where `roadkeep.toml` declares an id shape the counter cannot spell "
            "(`[ids] suffix`), and this project declares none — so every legal id here is the "
            "one `add` derives"
        ),
    ),
    "ref": Conditional(
        opens=lambda config: config.schema.ref_scheme == "outline",
        because=(
            'offered only where `roadkeep.toml` sets `ref_scheme = "outline"`, which makes the '
            "anchor the caller's to name; this project derives the pointer from the id, and one "
            "chosen by hand is what `ref.mismatch` refuses"
        ),
    ),
}

#: `list --role` is *which governed file*, not which prose file (RK304) — its universe is every
#: role this project declares, `roadmap` included, and that is the default. Published through the
#: same table with the one key overridden, so a bound added to `_BOUNDS` tomorrow reaches this
#: tool too: an enum of the prose files here would refuse the most common call this surface makes.
#: — and its `marker` is every marker any of those files can carry (RK314), because the set is
#: read per role: the changelog declares `✅ 🗑` where the roadmap declares the open four, so a
#: filter is checked against `schema_for(--role)`. A schema cannot make one enum depend on
#: another field, so this is the union — over-permissive by exactly the markers legal on a role
#: the call did not name, which the read beneath refuses, where the narrow answer would refuse
#: `--role changelog --marker ✅` on the client and never reach it.
_FILE_BOUNDS = {
    **_BOUNDS,
    "role": lambda config: _roles(config, ROLES),
    "marker": lambda config: _listed_markers(config),
}

#: The non-goals are their own two limits (RK70), so the same `why` means a different number
#: here — a client validating a bullet against the *task* limit would refuse prose the tool
#: accepts, which is the one way this derivation can be wrong while looking right.
_SCOPE_BOUNDS = {
    "lead": lambda config: {
        "maxLength": (config.non_goals or Scope()).lead,
        "note": _aimed((config.non_goals or Scope()).lead),
    },
    "why": lambda config: {
        "maxLength": (config.non_goals or Scope()).why,
        "note": _aimed((config.non_goals or Scope()).why),
    },
}


#: The two verbs whose `why` has a **second shape** (RK1049, RK1053, RK1055). With `--lines`
#: above one the field carries a wrapped ledger entry whole, and only its first line is measured
#: against `limits.<role>.why` — so no character ceiling describes both calls, and publishing the
#: single-line one refuses a span this server takes. That is RK183's rule, and the answer is the
#: one `body` and `section_body` already give for the same shape: no `maxLength`, and the bound
#: said in the note. The affordance is said there too, because a schema is the whole of what an
#: agent has: unsaid, it composes the `<br>`-joined line RK1049 exists to remove.
_SPAN_BOUNDS = {
    **_BOUNDS,
    "why": lambda config: {
        "note": (
            f"Aim for {words(config.schema.why_max)} words. **No `maxLength` here, and the "
            f"limit is per line**: {config.schema.why_max} characters is what refuses a "
            f"one-line field, counted in UTF-16 code units, and the rendered line "
            f"({config.schema.line_max}) is what binds — `budget` answers both before a word "
            f"is written (RK190). Passing `--lines` above one on an entry that wraps, this "
            f"field is the **whole span**: the first line is the sentence and is measured, "
            f"and the lines after it are written back under the bullet verbatim, unmeasured "
            f"because no field holds them. So the total has no ceiling and one published "
            f"here would refuse a call this tool accepts."
        )
    },
}


#: The verbs that mean something of their own by a field name every other verb shares, and the
#: table that says what (RK316). By the **full command** and then by its first word, which is
#: the order the divergences now need: `non-goal add` and `non-goal drop` share `[non_goals]`'
#: limits, while `record amend` takes a span and `record add` — placing a new entry — does not,
#: so a first-word key would publish the loose bound to the one door that still has the tight
#: one. Every key is asserted to name a subcommand this CLI accepts, so the one way this can
#: be wrong — a rename leaving nothing matched and the defaults silently published — is a test
#: failure and not a client refusing a call the tool would have taken.
_DIVERGENT: Mapping[str, Mapping[str, Any]] = {
    "non-goal": _SCOPE_BOUNDS,
    "list": _FILE_BOUNDS,
    "ship": _SPAN_BOUNDS,
    "record amend": _SPAN_BOUNDS,
}


def _aimed(limit: int) -> str:
    """The character ceiling restated as the word count a model can count towards (RK185).

    **And in the unit it is counted in** (RK436). `maxLength` is the one figure this tool
    publishes and does not own: the keyword is defined over the string's *characters* —
    code points — and RK430 made every gate here count UTF-16 code units, which is the
    stricter of the two. So the number is right and its unit is the client's, and a field
    carrying an astral character validates locally, passes, and is refused by a bound it
    was told it had met.

    Three answers existed and this is the one the surface already ruled the other two out
    of. Publishing the stricter figure is what the `why` bound refuses to do for the line
    limit and what `body` refuses to do for the word one: a lower `maxLength` refuses on
    the client prose this server accepts, which is a bound on the client (RK183) — and it
    would cost that room on every ASCII field to buy it on the rare astral one. Leaving it
    unsaid is the state the defect describes. What is left is naming the residual in the
    one place a client author reading the field is already looking, beside the aim.

    Said on every field rather than only where the counters disagree, which is where
    :func:`~roadkeep.kernel.schema._counted` says it: a refusal has the string in hand and can
    compare, and a schema is composed before any string exists.

    **Said once, and not per field** (RK1060). The residual belongs here and the paragraph
    stating it did not: identical on 13 properties, 322 characters each, 4,186 of the tool
    list — one sentence in every twelve a session read before its first call. What varies is
    the number and the aim, and that is what stays; the caveat is a fact about every bound
    this surface publishes, so it moved to :data:`INSTRUCTIONS`, which a client is given once
    at the handshake. Not `$ref`: a model is handed the tool list as text, so a definition it
    has to resolve is worse for the reader than a repeated sentence — the saving has to come
    from saying it somewhere a reader already is, which the handshake is and a sibling
    property is not.
    """
    return (
        f"Aim for {words(limit)} words; {limit} characters is what refuses, counted in "
        f"UTF-16 code units."
    )


#: The residual :func:`_aimed` used to repeat on every prose field, said once (RK1060). A
#: client is given this at the handshake and the tool list on every session that connects,
#: so a fact true of *every* published bound belongs in the one of them that is delivered
#: once. Beside the engine line RK79 put there for the same reason — which tree answered is
#: also a fact about the whole surface rather than about any tool on it.
_COUNTING = (
    "Every `maxLength` here is its field's ceiling under JSON Schema's own count, which "
    "is code points; this tool counts UTF-16 code units, the stricter of the two. So a "
    "field carrying an emoji or other astral character can validate on the client and "
    "still be refused — the published number is the looser one on purpose, a stricter "
    "bound being one that would refuse prose this server accepts."
)


@dataclass(frozen=True, slots=True)
class Surface:
    """What a session is sent, measured once (RK1096).

    Two reads answer this and each did its own arithmetic: `budget --tools` summed the
    descriptors and the handshake, and `budget --session` summed the same two under a
    different heading. They agreed, which is the property a duplicate has right up to the
    edit that moves one — the shape RK1073 closed for the provenance note and RK1080 for the
    partial predicate, both found the same way.

    Here rather than in `budgeting`, and that is the import direction rather than a
    preference: `serving` reaches `cli`, `cli` reaches the verbs, and a verb reaches
    `budgeting` — so a measurement of the surface placed there would close the cycle. The
    module that composes the payload is the module that can say what it costs.
    """

    #: Every tool and what it costs, largest first — the ranking `--tools` prints.
    tools: tuple[tuple[str, int], ...]
    #: The handshake, which is sent once beside the list and counted with it (RK1078/RK1062).
    handshake: int

    @property
    def listed(self) -> int:
        """The tool list alone, which is the half `[tools] characters` is a ceiling on."""
        return sum(cost for _name, cost in self.tools)

    @property
    def characters(self) -> int:
        """Everything a client is sent before its first call."""
        return self.listed + self.handshake


def surface(config: Config) -> Surface:
    """What connecting to this server costs, as both reads of it ask (RK1096).

    Derived from :func:`descriptors` and :func:`instructions` — the payloads themselves and
    never a second estimate of them — so a description reworded in `cli.py` moves this
    figure, which is the whole reason the number is worth reading.
    """
    sizes = {
        one["name"]: width(json.dumps(one, ensure_ascii=False)) for one in descriptors(config)
    }
    return Surface(
        tools=tuple(sorted(sizes.items(), key=lambda row: (-row[1], row[0]))),
        handshake=width(instructions()),
    )


def instructions() -> str:
    """What a client is told once, at the handshake (RK79, RK1060).

    Two facts, and both are about the whole surface rather than about any tool on it: which
    copy of this package answered, and how every bound in the schema is counted. The second
    was published 13 times over instead, once per prose field, which is 4,186 characters a
    session read before making a call — the cost RK464 measured and `[tools] characters` now
    holds one tool of.
    """
    return f"{engine()}\n\n{_COUNTING}"


def _roles(config: Config, universe: Sequence[str]) -> dict[str, Any]:
    """The roles a caller may name, as the enum a client validates against (RK304).

    ``universe`` is what the *command* means by a role and the config is what this project has,
    and the answer is the intersection: `section add` writes into a prose file and `list` prints
    any governed one, so one enum over both would refuse `roadmap` on the read or offer it on the
    write. Passed in rather than inferred, because it is a fact about the verb.

    Not argparse `choices`, for the reason §RK304 gives: `--role` accepts what the *project*
    declares, and a parser built once per process cannot say so without being rebuilt per project.
    Nothing is checked here either — unlike a conditional field's `pattern` (:func:`_bounded`),
    every role this narrows is one the write path beneath already refuses by name, so a check
    here would be a second spelling of a refusal `Config.path` owns.

    **Empty publishes nothing.** A project that declares no file of this kind has no legal value
    to offer, and `"enum": []` is a keyword no value satisfies — a client holding it could not make
    the call that earns the refusal explaining why, which is the one useful thing left to say.
    """
    declared = [role for role in universe if config.has(role)]
    return {"enum": declared} if declared else {}


def _listed_markers(config: Config) -> dict[str, Any]:
    """Every marker a declared file can carry, for the one filter that reads any of them (RK314).

    `list --marker` is checked against `schema_for(--role)` — the changelog declares `✅ 🗑`, the
    roadmap the open four — and JSON Schema cannot make one field's enum depend on another's
    value. So the union, in the order `ROLES` declares the files, first occurrence winning: it is
    over-permissive by the markers legal on some *other* role, and every one of those is refused
    by the read beneath with the set that role does declare.

    The direction matters and is the one rule this whole derivation keeps: a bound that refuses
    what the tool accepts is a bound on the client (RK183), and a per-role enum would refuse
    `--role changelog --marker ✅` before the call was ever made.
    """
    seen: list[str] = []
    for role in ROLES:
        if not config.has(role):
            continue
        schema = config.schema_for(role)
        for marker in (*schema.markers, schema.shipped_marker):
            if marker not in seen:
                seen.append(marker)
    return {"enum": seen} if seen else {}


def _paragraphed(config: Config) -> str:
    """A ceiling already stated in words, published as one (RK258).

    :func:`_aimed`'s inverse and the easier half: RK185 translates characters into words because
    a model cannot count the former, and a section's budget is *declared* in words (RK9), so it
    needs no translation at all — which is why it publishing nothing was the odd case.

    Per role, because `[limits.<role>]` can give one prose file its own number (RK50) and this one
    field reaches two: the default `role` is named with its figure, and a role that differs is
    named beside it rather than averaged into a number true of neither.

    The roles it may name are the ones the project **declares** (RK259). `schema_for` answers for
    any role, composing `[limits.<role>]` over the base and having no reason to check for a file —
    so walking `PROSE_ROLES` published a figure for `strategy` on a project carrying
    `[limits.strategy]` and no `[files] strategy`, naming a role `section add --role` would refuse.
    `config.has` and :func:`~roadkeep.authoring.prose_role` are the same narrowing every other
    reader of this question already makes, on the argument that a command naming a file nobody
    created cannot run — and with nothing declared at all the base number is still the honest
    answer, the field existing on the tool whatever this project's `[files]` says.
    """
    from roadkeep.authoring import prose_role  # noqa: PLC0415 - `authoring` reaches `sections`

    limits = {
        role: config.schema_for(role).section_max for role in PROSE_ROLES if config.has(role)
    }
    binding = limits.get(prose_role(config) or "", config.schema.section_max)
    # The aim beside the gate, as every other bound here publishes one (RK301): a ceiling
    # published as its own target is a target hit from above, measured at thirteen refusals
    # in one session — and over this transport the retry re-sends the whole body.
    said = (
        f"Aim for {body_aim(binding)} words; {binding} is what refuses, counted as words "
        f"rather than characters. `budget` states it per call, before the body exists."
    )
    differing = sorted(
        f"{role} {limit}" for role, limit in limits.items() if limit != binding
    )
    if differing:
        said += f" Where `role` names {', '.join(differing)}, that file's own number binds."
    return said


class ToolError(Exception):
    """An argument name or shape the schema already rules out — refused before dispatch."""


# -- describing the tools ----------------------------------------------------


def _action(parser: argparse.ArgumentParser, dest: str) -> argparse.Action:
    for candidate in parser._actions:  # noqa: SLF001 - argparse exposes no public reader
        if candidate.dest == dest:
            return candidate
    raise KeyError(f"{parser.prog} declares no {dest!r}")


@lru_cache(maxsize=1)
def _root() -> argparse.ArgumentParser:
    """The CLI parser, built once for the life of this process (RK202).

    RK174 and RK198 each removed a rebuild and left the last one on an argument: that a
    parser held across messages would stop a `roadkeep.toml` edited mid-session from being
    described. Counted, that is false. `build_parser` reads no configuration at all — two
    builds under two different configs on disk are identical action for action — and every
    configured value reaches a descriptor through `_BOUNDS`, off a config this server
    re-reads per message. A parser is a pure function of `cli.py`.

    Nor is it staler than what is already here: `cli.py` is imported once, so a parser built
    from the loaded module cannot describe a file edited after that import whether it is
    cached or not. RK155 reports that, and reports it the same either way.

    What the cache does assume is that nobody mutates the parser it hands out. Nothing in
    this package does — `parse_args` builds a Namespace, `descriptor` and `argv` read
    actions — and `tests/test_serving.py` holds it rather than this sentence.

    **The second build is real and is left alone** (RK1061). `main` builds a tree to
    dispatch the verb and this builds another to describe the surface, so a `lint` holding
    `[tools] characters` builds two — and `remedying._reading` is a third caller caching its
    own derivation of the same uncached object (RK1015). Caching `build_parser` removes the
    duplicate and was tried and reverted: measured at **6.3 ms once per process**, against a
    `lint` process of ~460 ms, and it is bought by freezing every `handler=` the parser
    holds at first build. A `monkeypatch` on one then silently does nothing — which is not a
    hypothetical, it is what the revert was written from. 1.4% is not worth a change that
    makes a patch fail by having no effect.
    """
    from roadkeep.cli import build_parser

    return build_parser()


def _parsers(
    root: argparse.ArgumentParser | None = None,
) -> Mapping[str, argparse.ArgumentParser]:
    """Every subcommand path in the CLI, indexed by it, off **one** parser (RK174).

    Reaching one subcommand means building the whole CLI, so a caller with more than one to
    resolve pays that per lookup — 58 builds and 195 ms for the `tools/list` a client sends
    first. The walk is the same descent :func:`_subparser` makes, done once and kept.

    ``root`` is the parser to index, for the caller that has to keep it anyway (RK198):
    :func:`call` parses the argv it built through the root, so building a second one to
    index was a third of what a `tools/call` spent. Defaulted to :func:`_root`, so the
    index is walked per call and the parser under it is built per process.
    """
    if root is None:
        root = _root()
    index: dict[str, argparse.ArgumentParser] = {}

    def walk(parser: argparse.ArgumentParser, path: str) -> None:
        for action in parser._actions:  # noqa: SLF001 - argparse exposes no public reader
            if not isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
                continue
            for step, sub in action.choices.items():
                index[f"{path} {step}".strip()] = sub
                walk(sub, f"{path} {step}".strip())

    walk(root, "")
    return index


def _subparser(
    command: str, parsers: Mapping[str, argparse.ArgumentParser] | None = None
) -> argparse.ArgumentParser:
    """The parser for a subcommand path, descending where it is nested (`section add`).

    Takes an index where the caller has one, and builds itself one where it does not — so
    `descriptor(tool, config)` stays callable with a single tool, which is how the tests ask
    what one schema is.
    """
    return (_parsers() if parsers is None else parsers)[command]


def _property(
    action: argparse.Action, config: Config, bounds_for: Mapping[str, Any] = _BOUNDS
) -> dict[str, Any]:
    """One argparse argument, as the JSON Schema a client validates before calling."""
    bounds = dict(bounds_for.get(action.dest, lambda _: {})(config))
    # A bound the schema has no keyword for. `maxLength` says how long the field may be and
    # cannot say what else the length depends on, so the part that is a *joint* rule is
    # appended to the sentence the CLI already prints for the flag rather than dropped.
    note = bounds.pop("note", "")
    described = {"description": _joined((action.help or "").strip(), note)}
    if isinstance(action, argparse._StoreTrueAction):  # noqa: SLF001
        return {"type": "boolean", **described}
    if isinstance(action, argparse._AppendAction):  # noqa: SLF001
        return {"type": "array", "items": {"type": "string", **bounds}, **described}
    return {"type": "string", **bounds, **described}


def _required(action: argparse.Action) -> bool:
    # A positional is required by being one; `nargs="?"` is the exception, and `ship id` is
    # not one. Reading it off the action keeps the two lists from disagreeing.
    return bool(action.required) or (not action.option_strings and action.nargs != "?")


def _joined(help_: str, note: str) -> str:
    """The flag's own sentence and what the config adds to it, as one readable string.

    The CLI's `help` is a fragment with no full stop — it is read under a column heading —
    so a note appended with a space ran the two together into "never a fix Aim for 18
    words". Ending the first is the whole fix, and it is here rather than in each note
    because the notes are composed by the config and the fragment by argparse.
    """
    if not note:
        return help_
    if help_ and help_[-1] not in ".!?:;":
        help_ += "."
    return " ".join(part for part in (help_, note) if part)


def _description(tool: Tool, parser: argparse.ArgumentParser) -> str:
    """The subcommand's own description, plus what an always-passed flag adds to it (RK150).

    Derived and never written here: the flag's help is the sentence the CLI prints for it, so
    two tools over one command cannot come to describe that difference in two ways — and a
    tool whose whole point is a flag it never mentioned would be a tool a client mistakes for
    the read it was split off from.
    """
    described = (parser.description or "").strip()
    for dest in tool.always:
        action = _action(parser, dest)
        flag, help_ = action.option_strings[0], (action.help or "").strip()
        described = f"{described} This tool always passes {flag}, which is to {help_}."
    return described


def _bounds_for(tool: Tool) -> Mapping[str, Any]:
    """Which bounds table describes this tool's fields, by the verb and never by the dest.

    Commands mean something of their own by a name every other command shares: `non-goal`'s
    `why` is `[non_goals]`' limit and not `[limits]`' (RK70), `list`'s `role` is any governed
    file and its `marker` any marker one can carry (RK304, RK314), and `ship`'s and `record
    amend`'s `why` has a shape no ceiling describes (RK1055). All are properties of the verb
    rather than of the dest, so all are read off it, here and in one place: a second `if` at the
    caller is how two tools over one dest come to publish two answers.

    **The full command first, then its first word** (RK1055). `record amend` takes a span and
    `record add` does not, so the two doors under one head need different answers — and the
    fallback is what keeps `non-goal add` and `non-goal drop` one entry rather than two.

    Read from :data:`_DIVERGENT` and no longer from an `if` chain (RK316). The chain's failure was
    silent and in the forbidden direction: a command renamed in `cli.py` left every `Tool` correct
    and no branch matching, so the fields fell back to `_BOUNDS` — narrower than the verb accepts,
    which is a bound on the client (RK183). A table has the same words in it and is *checkable*,
    which is RK167's own answer to a declaration that can stop matching: a key naming no command
    is a test failure (`tests/test_serving.py`) rather than a schema quietly refusing a legal call.
    Not moved onto :class:`Tool` — the tables are composed from the config below this line, and
    two divergent verbs out of thirty-odd is a fact about those two rather than a field for all.
    """
    if tool.command in _DIVERGENT:
        return _DIVERGENT[tool.command]
    return _DIVERGENT.get(tool.argv_head[0], _BOUNDS)


def descriptor(
    tool: Tool, config: Config, parsers: Mapping[str, argparse.ArgumentParser] | None = None
) -> dict[str, Any]:
    parser = _subparser(tool.command, parsers)
    # Which table holds this tool's numbers: the non-goals are governed by `[non_goals]` and
    # every other command by `[limits]`, and `why` is a field both of them name (RK70) — plus the
    # one command whose `role` means *which governed file* rather than which prose file (RK304).
    bounds_for = _bounds_for(tool)
    properties: dict[str, Any] = {}
    required: list[str] = []
    for dest in tool.exposed(config):
        action = _action(parser, dest)
        properties[dest] = _property(action, config, bounds_for)
        if _required(action):
            required.append(dest)
    payload: dict[str, Any] = {
        "name": tool.name,
        "description": _description(tool, parser),
        "inputSchema": {
            "type": "object",
            "properties": properties,
            # Closed on purpose: a misspelt argument is the failure RK24 names, and an open
            # object would forward it to a parser that answers with a usage string.
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": not tool.writes_of(parser)},
    }
    if required:
        payload["inputSchema"]["required"] = required
    return payload


def descriptors(config: Config) -> list[dict[str, Any]]:
    parsers = _parsers()
    return [descriptor(tool, config, parsers) for tool in TOOLS]


# -- calling one ------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Answer:
    """What one `tools/call` returns: the CLI's own output, and its exit code as a flag."""

    text: str
    is_error: bool

    def content(self) -> dict[str, Any]:
        return {"content": [{"type": "text", "text": self.text}], "isError": self.is_error}


def argv(
    tool: Tool,
    arguments: Mapping[str, Any],
    config: Config,
    parsers: Mapping[str, argparse.ArgumentParser] | None = None,
) -> list[str]:
    """The command line the CLI accepts, or `ToolError` naming what may be set instead.

    Takes the config because what may be set is a question about the project (RK111), and
    because a bound the descriptor published is a bound this has to hold: a client that
    validated is not the same as a call that was checked.

    ``parsers`` is the index the caller already built (RK198). Optional, and defaulted the
    same way :func:`descriptor`'s is: a test asking what one tool's argv is has one lookup
    and nothing to amortise it over.
    """
    parser = _subparser(tool.command, parsers)
    exposed = tool.exposed(config)
    unknown = [name for name in arguments if name not in exposed]
    if unknown:
        raise ToolError(_unrecognised(tool, unknown, exposed))
    _companioned(tool, arguments, parsers)
    positional: list[str] = []
    optional: list[str] = []
    for dest in exposed:  # declaration order, so the argv is stable and diffable
        if dest not in arguments:
            continue
        action = _action(parser, dest)
        fragment = _rendered(action, dest, arguments[dest])
        _bounded(dest, arguments[dest], config)
        (optional if action.option_strings else positional).extend(fragment)
    # What makes this tool the act it is named for (RK150), resolved through the parser like
    # every exposed argument: a client cannot pass these and cannot unset them.
    always = [_action(parser, dest).option_strings[0] for dest in tool.always]
    # `--json` is never exposed and always passed: the provenance is the difference between
    # an answer an agent can audit and one it re-reads the file to check (L5).
    return [*tool.argv_head, *positional, *optional, *always, "--json"]


def prose_of(
    command: str, parsers: Mapping[str, argparse.ArgumentParser] | None = None
) -> tuple[Prose, ...]:
    """What this subcommand takes off a pipe, as its own parser declares it (RK171).

    The inventory neither `TOOLS` nor `cli.py` stated. Read from the parser rather than held
    here, so exposing a fourth command that reads a paragraph declares itself instead of being
    found by the session that hangs on it — and so `tests/test_serving.py` can ask the question
    over every tool at once, which is the instrument RK170 was fixed without.

    ``parsers`` stays optional because that test asks one command at a time (RK198); the call
    path threads its index through, this lookup having been the second build of every call.

    **A tuple, because one command can have two** (RK329). `--why` reads the pipe wherever it
    appears, and on `add` that is beside `--section-body` — the field whose sentence carries
    an apostrophe, a backtick and a `§` being the one a shell reads first. A single answer here
    would have named one of the two and left the other to be found by the session that meets it,
    which is the state RK171 exists to have ended.
    """
    declared = _subparser(command, parsers).get_default("reads_stdin")
    return () if declared is None else tuple(declared)


def _companioned(
    tool: Tool,
    arguments: Mapping[str, Any],
    parsers: Mapping[str, argparse.ArgumentParser] | None = None,
) -> None:
    """Refuse an argv that would have gone to the pipe, naming the argument (RK170, RK171).

    The deadlock is closed by :func:`_spent_stdin` whatever this says, so what is bought here is
    only *which* refusal the caller reads: without it, `add` with a section title and no body
    answers `body.empty` — true, and about the prose, when the fact is that the argument carrying
    it did not arrive. Derived from :func:`prose_of` and not a table beside it, so all three
    declared paths answer the same way and a fourth cannot be the one that was forgotten.
    """
    for prose in prose_of(tool.command, parsers):
        if prose.dest not in tool.unconditional or not prose.reached_by(arguments):
            continue
        raise ToolError(
            f"{tool.name}: {prose.dest} is the prose itself, and over this transport there "
            f"is no pipe to read it from — pass it as a string. Omitted, or "
            f"{prose.sentinel!r}, it is nothing, and this format has no slot that may be "
            f"empty"
        )


def _unrecognised(tool: Tool, unknown: Sequence[str], exposed: Sequence[str]) -> str:
    """Why these names did not reach the argv, told apart from each other (RK253).

    An argument this project *closed* is not one that does not exist. `--ref` and `--id` are
    declared by the CLI, printed by its `--help` and reachable at a terminal; what is true over
    this transport is that `roadkeep.toml` shut them here (RK111). Led with "no such argument"
    they read as a misspelling, and the caller looks for a typo in a name spelled correctly —
    RK111 saw that reading and answered it by appending :func:`_withheld` rather than by
    correcting the claim, which leaves the correction arriving after the sentence that is wrong.

    So the two are stated separately, over their own names, and a call that guessed both ways
    earns both. The partition is free: :attr:`Tool.conditional` is exactly the names that exist
    and are shut, and every other unknown one is a name nothing declares.
    """
    closed = sorted(set(unknown) & set(tool.conditional))
    absent = sorted(set(unknown) - set(closed))
    stated = []
    if absent:
        stated.append(f"no such argument {', '.join(absent)}")
    if closed:
        stated.append(
            f"{', '.join(closed)} {'is' if len(closed) == 1 else 'are'} declared by the CLI "
            f"and closed by this project's config"
        )
    return (
        f"{tool.name}: {'; '.join(stated)} — this tool takes "
        f"{', '.join(exposed) or 'no arguments'}{_withheld(closed)}"
    )


def _withheld(closed: Sequence[str]) -> str:
    """Which declaration would have opened each closed field (RK111).

    Which arguments a tool takes is a fact about `roadkeep.toml` (L6), so the refusal names the
    declaration to edit rather than only that the field is absent — and one clause per field
    (RK241), because two joined into one sentence named one table for both, and a caller told to
    declare an id shape to name an anchor is a caller sent to edit the wrong table.

    Indexed and not guarded, which is what :class:`Conditional` buys (RK252): the reason travels
    with the predicate that opens the field, so a dest reaching one and not the other is not a
    state the record admits. RK251 needed a fallback here because two tables could disagree, and
    this ran on exactly one path — a caller passing a field this project closed — so the miss
    surfaced as a `KeyError` composing the refusal, for the caller who most needed the sentence.

    Takes the partition :func:`_unrecognised` already made rather than making it again (RK253):
    the lead clause and these depend on the same split, and computing it twice is how the two
    come to disagree about which names are which.
    """
    return "".join(f". {dest}: {_CONDITIONAL[dest].because}" for dest in closed)


def _spelled(tool: Tool, parsers: Mapping[str, argparse.ArgumentParser] | None = None) -> str:
    """This tool's **act** as a command line: the verb, and the flags that make it that one (RK318).

    `tool.command` alone is a different act wherever :attr:`Tool.always` is what names the tool,
    which is RK150's whole mechanism — and a note advising it sends the reader somewhere else.
    Measured on all three tools that have one: `claim` is `brief --claim`, and `brief` *succeeds*,
    prints a briefing and takes no line, so the write the caller asked for silently does not
    happen; `merge_check` is `merge --check`, and `merge` exits 2 on its own usage string; `scope`
    is the real `claim` command and was right only by having no always flag.

    Resolved through the parser and by dest, exactly as :func:`argv` resolves the same flags, so a
    rename in `cli.py` cannot leave this sentence naming something that is gone.

    The always flags and no arguments. Those are the caller's — they were just sent — and every
    `always` dest is a `store_true` by construction, because `argv` renders it as the option
    string alone: so there is no value here to quote, which is the second grammar §RK313 declined.
    """
    if not tool.always:
        return tool.command
    parser = _subparser(tool.command, parsers)
    flags = (_action(parser, dest).option_strings[0] for dest in tool.always)
    return " ".join((tool.command, *flags))


def spelled(name: str) -> str | None:
    """The command line for a name this tool publishes **over MCP**, or None (RK353).

    Two surfaces name one act differently on purpose — `scope` is the tool for declaring what
    a commit owns, and at the CLI that act is `claim <id> --path …`, because there `claim`
    without a path is the other act — and the skill teaches the tool name. What a session that
    reads it and types `roadkeep scope RK345 --path …` gets is argparse's `invalid choice`
    followed by forty verbs, none of which is the one it was sent for.

    The **tool table is the authority on a name**, which is the question §RK353 left open: it
    is what publishes the other spelling, it already carries the flags that make an act that
    one (:func:`_spelled`, RK318), and a second mapping in `cli.py` would be a second thing to
    keep in step with this one. So the parser asks here rather than answering itself.

    A qualified name is taken too — `mcp__roadkeep__scope`, and the longer
    `mcp__plugin_roadkeep_roadkeep__scope` a plugin-provided server gives it (RK333) — because
    a name pasted out of a tool list arrives with its prefix, and the refusal that only knew
    the bare form would be the same defect one surface along.
    """
    tool = next((one for one in TOOLS if one.name == name.rpartition("__")[2]), None)
    return None if tool is None else _spelled(tool)


def _bounded(dest: str, value: Any, config: Config) -> None:
    """Hold a conditional argument to the bound that opened it (RK111).

    Only the conditional ones, and only their `pattern`: every other bound in :data:`_BOUNDS`
    is the schema's, so the write path beneath refuses a violation whatever a client sent. A
    conditional field's is this surface's alone — `add --id T24` stays legal at a terminal,
    where `adopt` writes ids a corpus already spent — so unchecked here is unchecked.

    Conditional and still the schema's is the third case, and `ref` is it (RK241): an anchor
    that is not `<x.y>` is `ref.format` from `validate`, and where the pointer is derived the
    field is not exposed at all — so there is nothing this surface would be the only checker
    of, and a bound published here would be a second spelling of one the schema already holds.
    """
    if dest not in _CONDITIONAL or dest not in _BOUNDS:
        return
    pattern = _BOUNDS[dest](config).get("pattern")
    if pattern and not re.match(pattern, _one(dest, value)):
        raise ToolError(
            f"{dest} must match {pattern}, got {_one(dest, value)!r} — the id you may "
            f"choose is the split of one that already exists, and a number without the "
            f"letter is one the counter derives: leave the field out and it is derived"
        )


def _rendered(action: argparse.Action, dest: str, value: Any) -> list[str]:
    """One JSON value as the argv fragment its own argparse action reads."""
    if not action.option_strings:
        return [_one(dest, value)]
    flag = action.option_strings[0]
    if isinstance(action, argparse._StoreTrueAction):  # noqa: SLF001
        return [flag] if value else []
    if isinstance(action, argparse._AppendAction):  # noqa: SLF001
        return [part for item in _many(dest, value) for part in (flag, item)]
    return [flag, _one(dest, value)]


def _one(dest: str, value: Any) -> str:
    if isinstance(value, str):
        return value
    raise ToolError(f"{dest} must be a string, got {type(value).__name__}")


def _many(dest: str, value: Any) -> list[str]:
    if isinstance(value, str) or not isinstance(value, Sequence):
        raise ToolError(f"{dest} must be an array of strings")
    return [_one(dest, item) for item in value]


def call(tool: Tool, arguments: Mapping[str, Any], directory: str = ".") -> Answer:
    """Dispatch through the real parser and handler, with stdout and stderr captured.

    In-process rather than a subprocess: the tool is already running in one, and a second
    interpreter per call would make an `add` cost more over MCP than over `Bash`.
    """
    from roadkeep.cli import dispatch

    # Beside `dispatch`, and for the reason it is here rather than at the top (RK261): the guard
    # imports this module for `TOOLS` and never dispatches anything, so a module-level
    # `LockBusy` cost every denied edit 12 ms for an `except` only this function reaches.
    from roadkeep.locking import LockBusy  # noqa: PLC0415 - RK261

    # Discovered before the argv is built, because which arguments this tool takes is read
    # from it (RK111) — and discovered once, so the call cannot be checked against one config
    # and dispatched against another.
    # Before anything that could refuse, so the note can never be composed from an earlier call's
    # refusal (RK267): the slot is one call's out-parameter and this is where the call begins.
    provenance.witness(None)
    # And the argv beside it, for the same reason and under the same rule (RK1149): this surface
    # dispatches a parsed namespace and has no argv at all, so anything left in that slot is the
    # last *terminal* call this process served — and a retry spelled from it would offer a caller
    # here a command about somebody else's invocation. One call, one out-parameter, cleared where
    # the call begins.
    provenance.invoked(())
    try:
        config = Config.discover(directory)
    except ConfigError as error:
        # The engine is named on this one refusal unconditionally (RK155): a key the file
        # declares and the code does not know is the shape stale code produces, and which
        # build read the config is the fact that turns the puzzle into an instruction.
        # The one refusal with no root to name, the config that would have stated it being the
        # thing that failed (RK248). The launch path is what is left, and it is the safe half.
        provenance.witness(error)
        return _answered(
            f"roadkeep: {error}{provenance.read_by()}",
            Path(directory),
            is_error=True,
            served=_spelled(tool),
        )
    # One build for the whole call (RK198), and then one for the whole process (RK202). The
    # argv is rendered through the subcommands and parsed through the root they belong to,
    # and until this was threaded each of those three lookups built the entire CLI — 10.2 ms
    # of a 12.7 ms call, on the path every write takes.
    root = _root()
    parsers = _parsers(root)
    try:
        line = argv(tool, arguments, config, parsers)
    except ToolError as error:
        # The three refusals this function raises or catches itself still have the exception, so
        # they witness here rather than leave the note with nothing to intersect (RK267).
        provenance.witness(error)
        return _answered(str(error), config.root, is_error=True, served=_spelled(tool, parsers))
    out, err = io.StringIO(), io.StringIO()
    try:
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err), _spent_stdin():
            args = root.parse_args(["-C", directory, *line])
            # Through the CLI's own dispatch and not straight to the handler, so a write
            # over MCP takes the same lock a write over `Bash` does (RK117) — this is the
            # path an agent uses, so it is the path the duplicate id was minted on.
            code = dispatch(config, args)
    except SystemExit as exit_:  # argparse refused the argv: a missing required argument
        code = exit_.code if isinstance(exit_.code, int) else 2
    except LockBusy as busy:
        provenance.witness(busy)
        return _answered(
            f"roadkeep: {busy}", config.root, is_error=True, served=_spelled(tool, parsers)
        )
    reported = "\n".join(part for part in (err.getvalue().strip(), out.getvalue().strip()) if part)
    return _answered(
        reported or f"{tool.name}: exit {code}",
        config.root,
        is_error=bool(code),
        served=_spelled(tool, parsers),
    )


@contextlib.contextmanager
def _spent_stdin() -> Iterator[None]:
    """Hand the handler a stream already at EOF, for the length of one call (RK170).

    stdout and stderr are redirected because their output *is* the answer. stdin is redirected
    because it is the **transport**: `_add --section` with no `--section-body` reads
    `sys.stdin.read()`, and the only guard against that was a comment true of the `add` that
    names no section at all. Over `Bash` the read sees EOF and the call refuses. Over MCP it
    waits for an EOF no live client sends, and swallows every message queued behind it —
    measured in Shio at 18 minutes, 0% CPU, still holding the lock it claimed (RK117), with the
    `add` unanswered and a `status` sent after it unanswered too.

    Exhausted and not closed: `read()` on a closed stream raises `ValueError`, which
    :data:`~roadkeep.cli.REFUSALS` reports as bad input, and the honest answer is the refusal
    the format already owns for prose that is not there — `body.empty`, *a section with no prose
    is a heading*. So every handler that reads the pipe answers the same way instead of hanging,
    whether or not this surface knew it could.
    """
    saved = sys.stdin
    sys.stdin = io.StringIO("")
    try:
        yield
    finally:
        sys.stdin = saved


def _rerouted(text: str, root: Path) -> str:
    """Spell any command this answer names as the tool that serves it (RK475).

    RK444, RK447 and RK448 moved the four routes `guarding` composes. The **write path**
    raises its own refusals, and those were not in that count: an `add` on an outline project
    answers `ref.missing` and names `<invocation> anchors --block A`, handed to a caller on
    the surface where `anchors` has been a tool since RK463 — and to a machine that, since
    RK57, may have no console script at all.

    **At the print and not at the raise**, which is the question §RK475 left open. A
    `SchemaError` raised in `sections` knows nothing about the transport it will be shown on,
    and giving it one would be the write path importing the surface; this function is the one
    place that holds the message and the transport at once, so the substitution is made once
    here rather than at the twenty-nine sites that compose an invocation.

    Narrow on purpose: only `<invocation> <verb>` where the verb is one this surface serves,
    and only the two-word nested spelling where that is the tool. Everything else — a verb
    withheld here, a flag, a sentence that happens to contain the word — is left exactly as
    the CLI wrote it, because a rewrite that guessed would be this transport editing prose it
    did not compose (L4).
    """
    prefix = serving(root)
    if prefix is None:
        return text
    text = re.sub(
        r'("needs": )("(?:[^"\\]|\\.)*")', lambda found: _as_field(found, prefix), text
    )
    reached = invocation()
    if reached not in text:
        return text
    return re.sub(
        r"`" + re.escape(reached) + r" ([^`]*)`",
        lambda found: _as_call(found.group(1), prefix) or found.group(0),
        text,
    )


def _as_field(found: re.Match[str], prefix: str) -> str:
    """`add`'s `needs` as the call that closes it, or the argv the CLI wrote (RK476).

    The **one** JSON value this pass touches, and named rather than matched by shape: `needs`
    is documented as a command, so it is the field that is known argv and not prose. A pass
    over every string would meet a `why` that opens with a verb, and rewriting that would be
    this transport editing text it did not compose — the line `_rerouted` already holds.

    Backtick-free, because a field is read by a caller and not printed to one. Left exactly as
    it is wherever `_as_call` declines, which includes `null`: the regex reaches quoted values
    only, so a pointer that already resolves is never seen here.

    The value is **decoded before it is read and re-encoded after** — `json.dumps` escapes the
    ellipsis `--title …` ends on, and matching the raw span cost this its first measurement.
    """
    call = _as_call(json.loads(found.group(2)), prefix, plain=True)
    return found.group(1) + json.dumps(call) if call else found.group(0)


def _as_call(argv: str, prefix: str, *, plain: bool = False) -> str:
    """One backticked command as the call that serves it, or `""` to leave it alone.

    A flag is not a word over this transport (RK449's finding, RK475's case): rewriting the
    head and keeping `--block A` would name the right tool and an argument nobody can pass.
    So the tail goes through the **subcommand's own parser** — the same reader `_property`
    uses to publish the schema — and comes back as the fields a call carries.

    Empty on anything this surface cannot answer for: a verb it withholds, an argv the parser
    refuses, a field outside the tool's `unconditional`. There the shell spelling stays, which is
    what the CLI wrote and what is at least right where a shell exists.

    Composed by :meth:`~roadkeep.remedying.Door.mention` and no longer here (RK488). This was
    the third module holding its own copy of *a command in the spelling this session has*, and
    the copy was honest about it — the docstring under :func:`_fields_of` said the two were
    kept apart on purpose. What that bought is a transport whose rewriting rule can drift from
    the report's own composition, silently, because both keep printing.
    """
    from roadkeep.remedying import Door  # noqa: PLC0415 - RK260, the rewriting path only

    door = Door(tuple(argv.split()), "")
    if door.call() is None:
        return ""
    # No backtick where this lands in a *field* rather than in a sentence printed to somebody
    # (RK476) — which is the only thing this transport still decides about the spelling.
    return door.mention(prefix, quote="" if plain else "`")


def _fields_of(
    parser: argparse.ArgumentParser, rest: Sequence[str], exposes: Sequence[str]
) -> dict[str, object] | None:
    """The tail of a command as the fields a call carries, or ``None`` where it has none.

    The one reader of a command's **values**, for both halves of the problem (RK488): this
    read prose the CLI printed and `remedying._fields` read a table's argv, kept apart on the
    argument that a shared helper would tie the report's composition to this transport — and
    what it tied instead was two rules about `exposes` that had to stay equal by hand.
    :meth:`~roadkeep.remedying.Door.call` asks :func:`serves` *which* tool and asks this one
    what the tail says; nothing else parses a door.

    ``None`` on three states, and each is a command that genuinely has no call: an argv the
    parser refuses, a word it does not recognise arriving as a leftover, and a field outside
    ``exposes`` — `lint --fix`, since RK16 keeps the writing half where a human is standing.
    """
    with contextlib.redirect_stderr(io.StringIO()):
        try:
            parsed, unknown = parser.parse_known_args(list(rest))
        except SystemExit:
            return None
    if unknown:
        return None
    fields: dict[str, object] = {}
    for dest, value in vars(parsed).items():
        if value == parser.get_default(dest) or value is None or value is False:
            continue
        if dest not in exposes:
            return None
        fields[dest] = value
    return fields


def _answered(text: str, root: Path, *, is_error: bool, served: str = "") -> Answer:
    """One tool's answer, plus the note a **refusal** needs when the code answering moved.

    RK155, measured twice in one session: the config is re-read per message on purpose, so a
    `roadkeep.toml` edited mid-session is the one the next `tools/list` describes — but the code
    reading it was imported once at session start. `[claims] held` added to the file and to
    `config.py` in one commit made every MCP write refuse `unknown key 'claims'` while the CLI
    in a terminal accepted it, and the fallback was to stop using the write path this project
    ships. The refusal was correct about the code and wrong about the project.

    Only on a refusal, and only when something actually moved: a successful call has nothing to
    explain, and a note on every answer is a note that stops being read. Nothing reloads — see
    :attr:`~roadkeep.provenance.Engine.stale` for why that is the harness's job and not this
    server's.

    What it may not do is argue with the refusal it rides on (RK242). The sentence here said the
    refusal "may be a build behind rather than a fact about this project", attached to every
    refusal alike — and mtimes cannot know whether the files that moved reach the verb that
    refused, so a correct `ref.missing` arrived pre-doubted. Measured, that costs calls: the
    caller re-ran the command, tried a second spelling of the flag, then imported the CLI from a
    source checkout to obtain the answer it already had. So the drift is stated as what it is, a
    fact about this process, beside a refusal that stands as the answer the running code gave.

    And the remedy is the one that applies to the server reading it (RK246): a patch bump reloads
    a *plugin*, so on a project running the tool from its own checkout the note's first clause
    named a mechanism never in play — measured here at five bumps in one session, with the note
    still naming seven changed files. Which wiring answered is
    :meth:`~roadkeep.provenance.Engine.carried_by`, so it is read and not guessed. What stays
    untouched is the decision above it: nothing reloads itself (RK155).

    ``root`` is the **project** root and not the path the server was launched from (RK248):
    `Config.discover` walks up for a `roadkeep.toml`, so a server started in any subdirectory of
    a governed checkout has a root above its `-C` — and there `<root>/src/roadkeep` is not under
    the launch path, `carried_by` answers False, and the note names the bump on exactly the tree
    RK246 measured the bump never reaching. Every caller past discovery passes `config.root`; the
    `ConfigError` above it has no config to read one from and passes the launch path, which is
    the safe direction because that branch ends in restarting the session either way.

    **And it may not hand the relevance question back** (RK267). The note used to list every
    module :attr:`~roadkeep.provenance.Engine.stale` found and close with "re-run only where the
    changed files are the ones that would decide this", which is the reader being asked to know
    the call graph of a refusal they did not raise. Measured while shipping RK255: a
    `why.too-long` decided by `schema.py`, unchanged, arrived naming `cli.py`, `merging.py` and
    `provenance.py` — 450 characters of correct and irrelevant text on a refusal that had already
    said everything actionable in one line, fired on every error in every session that edits this
    package.

    Which modules decided it is knowable, so it is answered rather than delegated:
    :func:`~roadkeep.provenance.raised_in` reads them off the traceback and
    :func:`~roadkeep.provenance.witness` carries them across the exit code, and the note turns on
    the **intersection**. Disjoint sets say nothing at all — that is the RK255 case, and a note
    that fires there is the one nobody reads by the third time. An overlap names the module both
    sets hold and keeps the rest behind it, because a helper whose frame has already returned is
    the miss §RK267 accepts, and dropping the others would hide it.

    A refusal this process never witnessed is neither case: nothing decided it *here* — argparse
    refusing an argv, a handler exiting non-zero without raising — and the honest answer is then
    the inventory RK155 shipped, because suppressing on no evidence is the opposite mistake.

    **And whatever it says, it closes with something the reader can do** (RK313). Every remedy
    this note had named was a patch bump or a session restart, and the agent it is written for can
    perform neither — measured as one session abandoning the protocol surface and driving the CLI
    for all thirteen of its filings, which worked and left the served path untested for a session
    of real use. ``served`` is what makes the alternative nameable: the command this call would
    have run, so :func:`_now` says it.
    """
    text = _rerouted(text, root)
    if not is_error:
        return Answer(text, is_error=False)
    changed = engine().stale
    if not changed:
        return Answer(text, is_error=True)
    decided = provenance.witnessed()
    if decided is None:
        # Relevance is genuinely unknown, so the full list is what there is to say.
        return Answer(f"{text}\n\n{_inventory(changed, root, served)}", is_error=True)
    both = tuple(one for one in changed if one in decided)
    if not both:
        return Answer(text, is_error=True)
    rest = tuple(one for one in changed if one not in decided)
    behind = f" ({', '.join(rest)} also changed and did not.)" if rest else ""
    return Answer(
        f"{text}\n\n"
        f"Separately, about this process and not about the refusal above: "
        f"{', '.join(both)} decided this refusal and changed on disk after this server imported "
        f"roadkeep, so the answer above is what the code it did import said — read it first, "
        f"then re-run.{behind} {_remedy(root)}{_now(served)}",
        is_error=True,
    )


def _inventory(changed: Sequence[str], root: Path, served: str = "") -> str:
    """The note on a refusal nothing witnessed, which is RK155's and claims no relevance (RK267).

    It cannot ask the reader to establish one either, so it does not close with the sentence that
    did: what is left is the fact, the remedy, and the one thing available now (RK313).
    """
    return (
        f"Separately, about this process and not about the refusal above: this server "
        f"imported roadkeep before {', '.join(changed)} changed on disk, and the refusal is "
        f"what the code it did import answered — read it first. {_remedy(root)}{_now(served)}"
    )


def _now(served: str) -> str:
    """The remedy available **inside** the session that reads this, or nothing (RK313).

    Every other sentence in this note is about a process the reader cannot address: a patch bump
    is the harness's and a restart is the user's, both correct about the cause and empty as an
    instruction. The one action that exists is the one the measured session found by itself — the
    same verb through the CLI, which loads the changed files on the spot.

    Not circular, which is RK272's bar for advice: this note fires only where the drift is a fact
    about *this process*, so a run that imports fresh is the one place a different answer can come
    from. And spelled through :func:`~roadkeep.provenance.invocation`, because a command named
    literally is one that answers `command not found` on a plugin-installed machine (RK254).

    The verb and never the arguments. The reader has those — they just sent them — and a rendered
    argv would have to quote a `--why` sentence to be correct, which is a second grammar for
    stating a call this surface already accepts as JSON.
    """
    from roadkeep.remedying import Door  # noqa: PLC0415 - RK260, this note's path only

    if not served:
        # Nothing to name, so nothing is claimed. Every branch in :func:`call` passes the command
        # — the tool was resolved before dispatch — and this is the guard that keeps a caller
        # composing a note by hand from getting a sentence about a verb it never named.
        return ""
    return (
        f" Available now, in this session: `{Door(tuple(served.split()), '').command}` runs "
        f"the changed files, the CLI importing them per process."
    )


def _remedy(root: Path) -> str:
    """What actually restarts *this* server, which of the two wirings decides (RK246).

    Resolved here and not asked of the caller: a `Config.root` already is, and the launch path the
    `ConfigError` branch passes is the one that is not (RK248).

    What it says is bounded by what :meth:`~roadkeep.provenance.Engine.carried_by` establishes,
    which is a directory relation and not a launcher (RK250). It used to name `.mcp.json` and
    `scripts/roadkeep.py` — true of this repository and of nothing else that satisfies the same
    relation: a `pip install -e .` into a `.venv` inside the governed tree, or a marketplace
    pointing at a local path, would read two files they have not got. That is the very defect
    RK242 and RK246 each removed one instance of, so the sentence states the fact the relation
    gives and the remedy that follows from it, and names no mechanism it did not observe.
    """
    try:
        root = root.resolve()
    except OSError:  # a path that cannot be resolved is not evidence about either wiring
        return "Restart the session to run the changed files."
    if engine().carried_by(root):
        return (
            "The code answering lives inside the tree it is governing, so nothing the harness "
            "versions addresses this process and restarting the session is the only remedy."
        )
    return (
        "Every commit bumps the patch version so the harness reloads the plugin (RK153); "
        "restart the session if it has not."
    )


def tool_named(name: str) -> Tool:
    for tool in TOOLS:
        if tool.name == name:
            return tool
    raise ToolError(
        f"no such tool {name!r} — this server offers "
        f"{', '.join(tool.name for tool in TOOLS)}"
    )


# -- the protocol -----------------------------------------------------------


@dataclass
class Watch:
    """What this connection was told the tool list is — the one thing held between messages.

    The schema *varies by config* (RK111): `[ids] suffix` decides whether `add` accepts a
    `task_id` at all, and `[limits]`, `[markers]` and the id shape decide the bounds on
    every field. The server already re-reads `roadkeep.toml` per message, so a `tools/list`
    always describes the file as it is now — but a client asks once, at the handshake, and
    then validates every call against what it cached. Edit the config mid-session and the
    call it refuses is one this server would have accepted, with a message the *client*
    composed from a schema nobody told it was out of date.

    The protocol's answer is `notifications/tools/list_changed`, and sending it costs the
    claim that this holds no state between messages. That claim is kept where it means
    something: nothing here is a fact about the project, about a task or about a file's
    contents — it is a memory of *what this connection was sent*, which is the one thing a
    stateless server cannot derive and the one thing the notification is about. The
    alternative considered was to leave it and say "restart the session" in the refusal,
    which is a workaround for a message this server is able to send.

    Two costs kept small on purpose. Nothing is computed until the client has actually asked
    for a list, so a session that never lists pays nothing; and after that the per-message
    cost is one `stat` of the config file, with the descriptors rebuilt only when its bytes
    moved — the build is what RK174 and RK198 are about, and doing it per message to detect
    a change nobody made would cost more than the staleness it fixes.
    """

    #: The digest of the descriptors last handed to this client, or ``None`` before it asked.
    described: str | None = None
    #: The config file as it was when that answer was composed: path, mtime and size. Not the
    #: digest of its bytes — this is read on every message and the point is that it is a stat.
    stamp: tuple[str, int, int] | None = None
    #: Whether a list has ever been sent. Distinct from :attr:`stamp`, which is ``None`` both
    #: before the first list and on a project that declares no config at all.
    told: bool = field(default=False)

    def describing(self, config: Config, described: list[dict[str, Any]]) -> None:
        """Remember the answer being sent, so a later message can tell that it aged."""
        self.described = _digest(described)
        self.stamp = _stamp(config)
        self.told = True

    def moved(self, directory: str) -> dict[str, Any] | None:
        """The notification this connection is owed, or ``None`` — and never twice for one edit.

        The new digest is kept rather than cleared: a client that ignores the notification
        is not told again about the same edit, and a *second* edit still reaches it.
        """
        if not self.told:
            return None
        try:
            config = _config(directory)
        except OSError:
            return None
        stamp = _stamp(config)
        if stamp == self.stamp:
            return None
        self.stamp = stamp
        digest = _digest(descriptors(config))
        if digest == self.described:
            # The file moved and the schema did not — a comment edited, a `[report]` line
            # added. Nothing to tell the client, and the new stamp above means nothing to
            # rebuild until it moves again.
            return None
        self.described = digest
        return {"jsonrpc": "2.0", "method": "notifications/tools/list_changed"}


def handle(message: Any, directory: str = ".", watch: Watch | None = None) -> dict[str, Any] | None:
    """One JSON-RPC message in, one response out — or `None`, which is a notification.

    A notification answered is a protocol violation, and `notifications/initialized` is the
    first thing every client sends, so the `None` here is load-bearing rather than tidy.

    ``watch`` is the connection's memory of what it was last told (RK177), optional because
    a caller answering one message in isolation has no connection to keep one for.
    """
    if not isinstance(message, Mapping) or message.get("jsonrpc") != "2.0":
        return _error(None, INVALID_REQUEST, "expected a JSON-RPC 2.0 object")
    identifier = message.get("id")
    method = message.get("method")
    params = message.get("params") if isinstance(message.get("params"), Mapping) else {}
    if identifier is None:
        return None  # every notification, including the ones a later spec adds
    if method == "initialize":
        return _result(identifier, _handshake(params))
    if method == "ping":
        return _result(identifier, {})
    if method == "tools/list":
        config = _config(directory)
        described = descriptors(config)
        if watch is not None:
            watch.describing(config, described)
        return _result(identifier, {"tools": described})
    if method == "tools/call":
        return _result(identifier, _called(params, directory))
    return _error(identifier, METHOD_NOT_FOUND, f"unsupported method {method!r}")


def _digest(described: list[dict[str, Any]]) -> str:
    """The tool list as one comparable string, ordered so equal lists compare equal."""
    return hashlib.sha256(
        json.dumps(described, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _stamp(config: Config) -> tuple[str, int, int] | None:
    """The config file as a stat, or ``None`` where this project declares none."""
    source = config.source
    if source is None:
        return None
    try:
        info = Path(source).stat()
    except OSError:
        return None
    return (str(source), info.st_mtime_ns, info.st_size)


def _handshake(params: Mapping[str, Any]) -> dict[str, Any]:
    asked = params.get("protocolVersion")
    return {
        "protocolVersion": asked if asked in KNOWN_PROTOCOLS else PROTOCOL,
        # `listChanged` is what makes the notification above mean anything: a client that was
        # never told the list can change is entitled to ignore one that says it did (RK177).
        "capabilities": {"tools": {"listChanged": True}},
        "serverInfo": {"name": "roadkeep", "version": __version__},
        # The startup line RK79 asks for, and what every published bound is counted in
        # (RK1060). `serverInfo.version` stays the release number a client may have pinned
        # against, so which tree answered goes here — the one field of the handshake that
        # reaches a session, and the only moment this server has one.
        "instructions": instructions(),
    }


def _called(params: Mapping[str, Any], directory: str) -> dict[str, Any]:
    arguments = params.get("arguments") if isinstance(params.get("arguments"), Mapping) else {}
    try:
        tool = tool_named(str(params.get("name")))
    except ToolError as error:
        # `isError` and not a JSON-RPC error, so the allowed set reaches the model that
        # guessed the name rather than the client that forwarded it.
        return Answer(str(error), is_error=True).content()
    return call(tool, arguments, directory).content()


def _config(directory: str) -> Config:
    try:
        return Config.discover(directory)
    except ConfigError:
        # The limits are then the defaults, which is a schema that is wrong about this
        # project rather than no schema at all — and `lint` is the tool that says why.
        return Config.default(directory)


def _result(identifier: Any, result: Mapping[str, Any]) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": identifier, "result": dict(result)}


def _error(identifier: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": identifier, "error": {"code": code, "message": message}}


def serve(reader: TextIO, writer: TextIO, directory: str = ".") -> int:
    """Read line-delimited JSON-RPC until the client closes stdin.

    The loop never raises: a malformed line is a parse error the client can read, and a
    server that dies on one takes every tool in the session with it.

    The :class:`Watch` is the connection, and lives exactly as long as it (RK177): a second
    message may find `roadkeep.toml` describing different tools than the first one answered
    with, and the client is told so rather than left validating against what it cached.
    """
    watch = Watch()
    for line in reader:
        if not line.strip():
            continue
        try:
            message = json.loads(line)
        except ValueError:
            response: dict[str, Any] | None = _error(None, PARSE_ERROR, "invalid JSON")
        else:
            response = handle(message, directory, watch)
        if response is not None:
            _send(writer, response)
        # After the answer, never instead of it: the response is what the client is waiting
        # on, and a notification that arrived first would sit in front of it in the pipe.
        notice = watch.moved(directory)
        if notice is not None:
            _send(writer, notice)
    return 0


def _send(writer: TextIO, message: Mapping[str, Any]) -> None:
    writer.write(json.dumps(message) + "\n")
    writer.flush()
