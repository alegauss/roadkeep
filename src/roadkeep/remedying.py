"""What closes one finding, as a command rather than a sentence (RK420).

`lint` and the guard are the two halves of one contract. The barrier states the rule
outright — a refusal that names no alternative is a refusal an agent works around — and
:data:`~roadkeep.guarding._INSTEAD` keeps it, carrying the command *and its flags* for
every governed role. The gate made the same promise in :class:`~roadkeep.linting.Finding`'s
docstring and did not keep it: counted over the emission sites, 25 of 37 codes named no
verb at all, and the twelve that did named it inside a sentence, as prose to re-type.

The cost of that is paid in **turns**, which is why it went unmeasured. A report arrives,
the caller infers a door per code, and the guard denies the `Edit` that would have been the
shortcut — so the loop is *retry a verb until one is not refused*, against a file whose
repair was one command the whole time. `id.duplicate` is the case that proves it: `record
drop` and `record renumber` both exist, the refusal on each names the other, and the
finding names neither.

So the remedy is a field, and this module is the one table it comes from. Four kinds,
because four is what a caller actually does next:

* ``fix`` — `lint --fix` takes it. No decision, no prose, nothing to read.
* ``run`` — one command that **writes**, complete, with the id and the line already
  substituted. A placeholder here would be the guess this module exists to remove.
* ``read`` — one command answers the question and closes nothing: which of two sections is
  history, what a block dep expands to, which file claims an anchor. Split out from ``run``
  because `repair` executes that one, and a read it executed would spend a step, change no
  byte and report the finding still standing — a repair that repairs nothing.
* ``compose`` — one command, one field that is **prose only the author can write**. L4 is
  not a gap in the table, it is the table being honest: nothing here composes a title, a
  reason or a shorter sentence, so the blank is marked and left.
* ``decide`` — more than one door, and which one is right is editorial. Both are rendered
  complete, and :attr:`Remedy.decision` states what distinguishes them, so the choice is
  made from the report instead of by running one and reading its refusal.

**The table is keyed by code and nothing else.** A remedy computed at the emission site
would be 70 remedies to keep in step with 70 messages, and the one that fell behind would
be invisible — the report still prints, the exit is still 1, and only the sentence that
would have saved the turn is missing. Keyed centrally, `tests/test_remedying.py` can assert
the domain is *total* over every code the package can emit (RK421), which turns adding a
check without stating its repair into a red rather than a discovery on somebody else's
backlog six months later.

**Two things are read from the config rather than fixed** (L6): whether the pointer is
derived (`ref_scheme = "id"` makes `ref.mismatch` mechanical; an outline anchor is the
author's, so it is `compose`), and which role a file plays, since `id.duplicate` is
`renumber` in the roadmap and `record renumber` in the ledger. Everything else is one
lookup.

What this module does **not** do is run anything. `repair` (RK422) is the verb that reads
these back and executes them; keeping the table pure is what lets `lint --json`, `explain`
and the guard's denial all quote the same answer without any of them growing a side effect.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from .config import ROLES, Config

#: The five kinds, in the order a caller pays for them: nothing, one write, one read then a
#: judgement, one sentence, one choice. `repair` runs the first two and prints the rest.
KINDS = ("fix", "run", "read", "compose", "decide")

#: Marks the one field of a ``compose`` argv that the tool may not write (L4). Kept as a
#: distinct token rather than an empty string so a caller can find it without parsing prose.
BLANK = "…"


@dataclass(frozen=True, slots=True)
class Door:
    """One command that could close a finding, and what choosing it means.

    ``what`` is only load-bearing on a ``decide``, where it is the difference between the
    doors — but it is carried on every kind, because a caller printing a remedy has one
    shape to render and `explain` (RK423) has one field to quote.
    """

    argv: tuple[str, ...]
    what: str

    @property
    def command(self) -> str:
        """The argv as a line to run, reaching this engine the way this machine can (RK254).

        Derived and never the literal console script: it exists only after a `pip install`
        that put the scripts directory on PATH, so on a plugin-installed machine — and in
        this repository — a remedy spelling it names a command that answers `command not
        found`. A remedy a caller cannot run is the defect this task was about, one step
        further along.
        """
        from .provenance import invocation

        return " ".join((invocation(), *self.argv))

    @property
    def complete(self) -> bool:
        """Whether every field is filled — false where L4 left one to the author."""
        return not any(BLANK in word for word in self.argv)

    def __str__(self) -> str:
        return f"{self.command}  — {self.what}"


@dataclass(frozen=True, slots=True)
class Remedy:
    """What closes one finding: a command to run, or a decision to take."""

    code: str
    kind: str
    doors: tuple[Door, ...]
    #: What has to be chosen between the doors. Non-empty exactly when ``kind`` is
    #: ``decide``, because a single door has nothing to decide between.
    decision: str = ""

    @property
    def door(self) -> Door | None:
        """The one door, where there is one. ``None`` on a ``decide``."""
        return self.doors[0] if len(self.doors) == 1 else None

    @property
    def runnable(self) -> bool:
        """Whether `repair` may execute this without asking anybody anything (RK422).

        ``read`` is deliberately not runnable. Its command is safe to run and useless to
        run *here*: it answers a question for the caller, and executing it inside a repair
        loop would leave the finding exactly where it was.
        """
        return self.kind in ("fix", "run") and all(d.complete for d in self.doors)

    def payload(self) -> dict[str, object]:
        """The `--json` form: argv as a list, because a consumer runs it rather than reads it."""
        return {
            "kind": self.kind,
            "decision": self.decision,
            "doors": [
                {"argv": list(d.argv), "what": d.what, "complete": d.complete}
                for d in self.doors
            ],
        }

    def __str__(self) -> str:
        if self.kind == "decide":
            return f"{self.decision}\n" + "\n".join(f"    {d}" for d in self.doors)
        return str(self.doors[0])


@dataclass(frozen=True, slots=True)
class _Rule:
    """One row of the table: how to close this code, before the finding fills it in."""

    kind: str
    #: ``(argv template, what)``. Every ``{}`` field is substituted from the finding.
    doors: tuple[tuple[tuple[str, ...], str], ...]
    decision: str = ""
    #: A rule that reads the config instead of the table — the two cases L6 makes
    #: per-project. Named, so the totality test can see it is deliberate.
    varies: str = ""
    #: What *produces* the defect, for `explain` (RK423). Required on a ``fix`` row and
    #: absent everywhere else, which is not an oversight but the rule: a `run`, `compose`
    #: or `decide` door already states the defect in order to say what choosing it means,
    #: and a second sentence saying the same thing is the drift this package exists to
    #: stop. A ``fix`` door cannot — its `what` describes the *repair* — so the cause is
    #: written there and only there. `tests/test_remedying.py` holds both directions.
    cause: str = ""


def _fix(cause: str, what: str) -> _Rule:
    return _Rule("fix", ((("lint", "--fix"), what),), cause=cause)


def _run(argv: tuple[str, ...], what: str) -> _Rule:
    return _Rule("run", ((argv, what),))


def _read(argv: tuple[str, ...], what: str) -> _Rule:
    """One command that answers the finding and writes nothing. See :data:`KINDS`."""
    return _Rule("read", ((argv, what),))


def _compose(argv: tuple[str, ...], what: str) -> _Rule:
    return _Rule("compose", ((argv, what),))


def _decide(decision: str, *doors: tuple[tuple[str, ...], str]) -> _Rule:
    return _Rule("decide", tuple(doors), decision)


#: Every code the package can emit, and what closes it. The domain is asserted total in
#: `tests/test_remedying.py` against the codes scraped from `linting` and `schema` — a code
#: added without a row here fails the suite (RK421).
#:
#: `{id}` is the finding's subject: a task id on most codes, and on the rest whatever the
#: emission site put in that slot — a block label, a section anchor, a queue token. `{line}`
#: is the line it was read at, `{first}` the earlier of two positions where the message
#: carries one, and `{role}` the file's role.
_TABLE: Mapping[str, _Rule] = {
    # ------------------------------------------------------------------ the character pass
    # RK126's repair: not a re-render, and the one that reaches a line no parse touches.
    "char.bom": _fix(
        "a byte-order mark at the start of the file: not text, and a byte the round-trip "
        "compares, so the file stops matching what the schema renders",
        "the mark is deleted, and no other byte moves",
    ),
    "char.tab": _fix(
        "a tab past the indentation, where this format separates fields with a space — so "
        "the grammar reads the separator as part of the field beside it",
        "the tab becomes the one space this format writes",
    ),
    "char.space": _fix(
        "a codepoint that renders as a space and is not one, so the grammar reads a word "
        "where a separator was meant and the line parses as something else",
        "the codepoint is replaced by an ordinary space",
    ),
    "char.invisible": _fix(
        "a codepoint invisible in an editor — a zero-width space, a variation selector, a "
        "control character — so every other diagnosis of the line names a consequence",
        "the codepoint is deleted wherever it sits, inside a line no parse reaches",
    ),
    # Not the character pass's: it works on the body and puts the ending back exactly as it
    # was read, deliberately, so a fixer for this would be the pass that joins the file.
    "char.mixed-endings": _compose(
        ("lint",),
        "no verb writes an ending: normalize the file with git's own `text` attribute, "
        "then re-run the gate",
    ),
    # ------------------------------------------------------------------------ derived data
    "deps.stale": _fix(
        "the `(deps: … ✅)` annotation caches another line's status and that line moved: "
        "derived data written once and read as current",
        "the annotation is recomputed from the files it caches",
    ),
    "deps.duplicate": _fix(
        "one dep stated twice in a field where an entry is an address, usually a merge "
        "that resolved into both sides' tokens",
        "the repeated dep is dropped and the order is re-derived",
    ),
    "deps.marker": _fix(
        "a dep carrying a marker the annotation does not derive, so the line states a "
        "status the files do not agree with",
        "the annotation is derived, so the marker it caches is rewritten",
    ),
    "ref.mismatch": _Rule(
        "fix",
        ((("lint", "--fix"), "the pointer is derived from the id, so it is recomputed"),),
        varies="ref_scheme",
        cause=(
            "the pointer names an anchor other than the one the scheme derives, so the "
            "line addresses a section chosen by hand"
        ),
    ),
    "line.non-canonical": _fix(
        "the line parses, and rendering the task back produces different bytes: a field "
        "spelled by hand where the schema has one spelling for it",
        "the line is re-rendered from the task the parser read out of it",
    ),
    # --------------------------------------------------------------------- the three lists
    "priority.shipped": _fix(
        "the queue names work that has shipped: every token in an order names work, and "
        "work leaves — the one list a departure does not reach",
        "the entry is dropped, named in the report and never in silence",
    ),
    "priority.retired": _fix(
        "the queue names work that was retired, which is the same departure by the other "
        "door and leaves the same dead entry",
        "the entry is dropped, named in the report and never in silence",
    ),
    "priority.deferred": _decide(
        "a paused line's place in the order is the one thing the store could not keep, "
        "so restoring it and dropping it are both real answers:",
        (("resume", "{id}"), "the work is coming back, and keeps the place it held"),
        (("priority", "drop", "{id}"), "the order should not name it while it is paused"),
    ),
    "priority.unknown": _decide(
        "an id no file carries is as likely a typo as a deletion, which is why the fixer "
        "leaves it:",
        (("priority", "drop", "{id}"), "the work is gone and the queue outlived it"),
        (("priority", "add", "{id}"), "the token was mistyped — drop it, then add the right one"),
    ),
    "priority.duplicate": _run(
        ("priority", "drop", "{id}"),
        "one of the two entries goes; the queue is re-added at the place you meant",
    ),
    "priority.shape": _compose(
        ("priority", "add", BLANK),
        "the bullet addresses no work: drop it by hand-free re-add — `priority add <id>` "
        "or `priority add 'Block X'`",
    ),
    "priority.config": _read(
        ("priority", "list"),
        "the section wins over the config: read the queue that is live, then take the "
        "`priority = [...]` line out of roadkeep.toml",
    ),
    "priority.block": _decide(
        "a block with no open line under it cannot be first, and whether that is a "
        "finished block or one nothing has been added to yet is not the queue's to say:",
        (("priority", "drop", "{id}"), "the block is finished and the order outlived it"),
        (("list", "--block", "{id}"), "read what is under it before deciding"),
    ),
    "priority.block-empty": _run(
        ("priority", "drop", "{id}"),
        "the block holds no open line, so nothing in it can be first",
    ),
    "priority.block-unstarted": _run(
        ("priority", "drop", "{id}"),
        "the block was never declared, so the token addresses nothing",
    ),
    # ------------------------------------------------------------------------ the headings
    "block.repeated": _run(
        ("block", "merge", "{id}"),
        "the label's later headings fold into the first, entries and all",
    ),
    "block.unrecorded": _compose(
        ("block", "add", "{id}", "--title", BLANK),
        "the ledger declares no heading for a block the roadmap plans work under; the "
        "title is yours to write",
    ),
    "block.unorganised": _compose(
        ("block", "add", "{id}", "--title", BLANK, "--organise", "changelog"),
        "the ledger is organised by nothing, so the first heading opens it",
    ),
    "block.missing": _compose(
        ("block", "add", "{id}", "--title", BLANK),
        "the line's block is declared nowhere; declare it, or re-file the line under one "
        "that exists",
    ),
    "block.format": _compose(
        ("block", "add", BLANK, "--title", BLANK),
        "the label is not one this project's heading word can render; re-declare it and "
        "move the lines",
    ),
    "block.emptied": _read(
        ("stats",),
        "the block held open lines and holds none: read the counts before a projection "
        "that names active blocks is republished",
    ),
    "block.reopened": _read(
        ("stats",),
        "the same row, in the other direction",
    ),
    # ------------------------------------------------------------------------------ the ids
    "id.duplicate": _Rule(
        "decide",
        (
            (
                ("record", "drop", "{id}", "--line", "{line}"),
                "one delivery recorded twice — the later entry goes",
            ),
            (
                ("record", "renumber", "{id}", "--line", "{line}"),
                "two deliveries sharing an id — this one gets an address of its own",
            ),
        ),
        "two lines carry one id, and whether that is one thing written twice or two "
        "things colliding is the only thing the tool cannot read off the file:",
        varies="role",
    ),
    "id.format": _run(
        ("renumber", "{id}"),
        "the id does not match this project's shape; renumber moves the line and its "
        "dependents to one that does",
    ),
    "id.two-files": _run(
        ("ship", "{id}"),
        "a ship stopped between its two writes: re-running closes the line without "
        "writing a second entry",
    ),
    # ------------------------------------------------------------------------- the pointers
    "ref.unresolved": _compose(
        ("section", "add", "{id}", "--title", BLANK),
        "the line points at a section that does not exist; the prose arrives on stdin",
    ),
    "ref.ambiguous": _read(
        ("anchors",),
        "one anchor is declared in two places: read which files claim it, then move one "
        "with `section move`",
    ),
    "ref.missing": _compose(
        ("amend", "{id}", "--ref", BLANK),
        "the scheme cannot derive this pointer, so the anchor is the field you name",
    ),
    "ref.format": _compose(
        ("amend", "{id}", "--ref", BLANK),
        "the anchor is not an address this project's scheme reads",
    ),
    "ref.sigil": _fix(
        "the pointer carries a sigil the renderer writes, so the field holds a character "
        "the schema would add again",
        "the sigil is derived, so the pointer is re-rendered without it",
    ),
    # ------------------------------------------------------------------------- the sections
    "section.stale": _run(
        ("section", "drop", "{id}"),
        "the task is in the ledger and `ship` deletes the section, so this survived a "
        "hand edit",
    ),
    "section.orphan": _decide(
        "nothing points at this section, which is either a design that outlived its line "
        "or a line that was lost:",
        (("section", "drop", "{id}"), "the work is gone and the rationale went with it"),
        (("show", "{id}"), "read it first — a lost line is re-filed with `add`, not deleted"),
    ),
    "section.duplicate": _run(
        ("section", "move", "{id}"),
        "one anchor is at two places in one file; move the later under an address of its own",
    ),
    "section.ambiguous": _read(
        ("anchors",),
        "two files declare the anchor: read both, then give one file a `[refs]` namespace",
    ),
    "section.unreachable": _read(
        ("show", "{id}"),
        "the task is alive and its design is somewhere else: read both before one becomes "
        "history",
    ),
    "section.unpaired": _read(
        ("show", "{id}"),
        "the section was edited and its line was not — `pick` reads only the line, so read "
        "what moved and put it there with `restate` or `amend`",
    ),
    "section.too-long": _compose(
        ("section", "amend", "{id}", "--body", "-"),
        "past the word budget; the shorter prose is yours and arrives on stdin",
    ),
    # ---------------------------------------------------------------------------- the deps
    "deps.unknown": _decide(
        "the dep is in neither file, so nothing can say whether it is done — and a token "
        "nothing carries is as likely a typo as a deletion:",
        (("amend", "{id}", "--dep", BLANK), "the dep was mistyped; state the right one"),
        (("gaps",), "read where the id went before deciding it is gone"),
    ),
    "deps.retired": _compose(
        ("amend", "{id}", "--dep", BLANK),
        "the dep left without shipping, so the line waits on nothing; restate the deps "
        "it actually has",
    ),
    "deps.block": _read(
        ("deps", "{id}"),
        "read what the block dep expands to before the line is picked",
    ),
    "deps.cycle": _compose(
        ("amend", "{id}", "--dep", BLANK),
        "the deps close a loop, so no order starts it; one of them is the edge to cut",
    ),
    "deps.collective": _read(
        ("deps", "{id}"),
        "one token names many open tasks: read the expansion, which is the whole finding",
    ),
    "deps.self": _compose(
        ("amend", "{id}", "--dep", BLANK),
        "a line waiting on itself can never start; state the deps it meant",
    ),
    "deps.compound": _compose(
        ("amend", "{id}", "--dep", BLANK),
        "one token holds several deps; `--dep` is repeatable, so state them one each",
    ),
    "deps.format": _compose(
        ("amend", "{id}", "--dep", BLANK),
        "the token is not a dep this grammar reads: an id, a `Block X`, a range, or work "
        "outside the backlog",
    ),
    "deps.range": _compose(
        ("amend", "{id}", "--dep", BLANK),
        "the range names no line this backlog carries",
    ),
    "deps.unexpected": _run(
        ("lint", "--fix"),
        "this file's rules declare no deps field, so the annotation is dropped",
    ),
    # --------------------------------------------------------------------- the prose fields
    # Every one of these is `compose`, and that is L4 rather than a gap: there is no shorter
    # sentence the tool may write, so the blank is marked and the author fills it.
    "why.too-long": _compose(
        ("amend", "{id}", "--why", BLANK),
        "past the limit; `budget` says how many characters the field has before you write",
    ),
    "why.sentences": _compose(
        ("amend", "{id}", "--why", BLANK),
        "the why is one sentence — the second belongs in the section the line points at",
    ),
    # The six the schema composes from a field name, invisible to the totality read until
    # RK428 taught it to look. Each is one door away and always was — the reason none had a
    # row is that nothing ever asked.
    "why.empty": _compose(
        ("amend", "{id}", "--why", BLANK),
        "the field is blank; a line with no why states a problem and no reason for it",
    ),
    "symptom.empty": _compose(
        ("restate", "{id}", "--symptom", BLANK),
        "the field is blank; the symptom is the falsifiable claim the line *is*",
    ),
    # `-` and not a blank: a newline in a one-line field is almost always what a shell put
    # there, and stdin is the route where nothing expands anything (RK407 is the other half).
    "why.newline": _compose(
        ("amend", "{id}", "--why", "-"),
        "a task is one line; re-send the field on stdin, which no shell rewrites",
    ),
    "symptom.newline": _compose(
        ("restate", "{id}", "--symptom", "-"),
        "a task is one line; re-send the field on stdin, which no shell rewrites",
    ),
    # Mechanical, and the one pair here that is: the trim is refused at the *door* on
    # purpose — the tool does not silently rewrite text it did not author — but on a line
    # already in the file `--fix` normalizes it, which is derived data by any other name.
    "why.whitespace": _fix(
        "leading or trailing whitespace around the field, which the door refuses rather "
        "than trimming: nothing here silently rewrites text it did not author",
        "the field is trimmed where it already sits, and no other byte moves",
    ),
    "symptom.whitespace": _fix(
        "leading or trailing whitespace around the field, which the door refuses rather "
        "than trimming: nothing here silently rewrites text it did not author",
        "the field is trimmed where it already sits, and no other byte moves",
    ),
    # The character the author did not type (RK407). `compose` and not `fix`: the codepoint
    # is inside prose, so removing it is a rewrite of somebody's sentence — and the shell
    # that wrote it will write it again unless the *quoting* changes, which is why the door
    # is the field's own and the dash is what the remedy actually turns on.
    "why.control": _compose(
        ("amend", "{id}", "--why", "-"),
        "a control character a shell's escape wrote: re-send the field on stdin, where "
        "nothing expands a backtick",
    ),
    "symptom.control": _compose(
        ("restate", "{id}", "--symptom", "-"),
        "a control character a shell's escape wrote: re-send the field on stdin, where "
        "nothing expands a backtick",
    ),
    "why.no-terminator": _compose(
        ("amend", "{id}", "--why", BLANK),
        "the why ends in a stop; nothing here adds one, because where it goes is the "
        "sentence's",
    ),
    "symptom.too-long": _compose(
        ("restate", "{id}", "--symptom", BLANK),
        "past the limit; the symptom is the falsifiable claim, so shortening it is `restate`",
    ),
    "symptom.sentence": _compose(
        ("restate", "{id}", "--symptom", BLANK),
        "the symptom is a phrase naming what does not work, never a sentence",
    ),
    "symptom.markup": _compose(
        ("restate", "{id}", "--symptom", BLANK),
        "the symptom carries markup the renderer writes; state the claim alone",
    ),
    "line.too-long": _compose(
        ("amend", "{id}", "--why", BLANK),
        "the rendered line is past the limit; `budget` prices both fields before you write",
    ),
    "part.too-long": _compose(
        ("record", "amend", "{id}", "--part", BLANK),
        "the partial's qualifier is past the limit",
    ),
    "part.blank": _compose(
        ("record", "amend", "{id}", "--part", BLANK),
        "a partial names which half shipped; an empty qualifier names none",
    ),
    "part.unexpected": _run(
        ("ship", "{id}"),
        "a partial qualifier where the files say the work is whole: the completion "
        "replaces the entry and drops it",
    ),
    # -------------------------------------------------------------------------- the markers
    # `compose` and not `run`: the marker is a choice from a declared set, so the tool could
    # list the candidates and still may not pick one — maturity is the author's claim about
    # the work, which is the same reason `resume` asks for it rather than restoring a default.
    "status.unknown": _compose(
        ("status", "{id}", BLANK),
        "the marker is not one this project declares; `[markers]` in roadkeep.toml lists them",
    ),
    "status.shipped": _run(
        ("ship", "{id}"),
        "the shipped marker never belongs in the roadmap — `ship` is the transaction that "
        "moves the line",
    ),
    "status.unrepresentable": _fix(
        "the marker carries a codepoint that is not part of it — a variation selector an "
        "editor added — so the status matches nothing this project declares",
        "the codepoint is deleted, which is the whole of what made it unreadable",
    ),
    # ---------------------------------------------------------------------------- the files
    "file.missing": _compose(
        ("init",),
        "a declared file is not on disk: scaffold it, or take the entry out of "
        "`[files]` in roadkeep.toml",
    ),
    "path.missing": _compose(
        ("amend", "{id}", "--why", BLANK),
        "the line names a path the repository does not have; the path is prose, so the "
        "correction is the sentence",
    ),
    "budget.absent": _compose(
        ("budget",),
        "a `[budgets]` entry names a file that is not there; read what is budgeted, then "
        "correct the entry in roadkeep.toml",
    ),
    "export.stale": _run(
        ("export", "--readme"),
        "every character between the markers is derived, so it is rewritten and never edited",
    ),
    "export.unmarked": _run(
        ("export", "--readme"),
        "the target carries no roadkeep markers, so nothing there is governed yet",
    ),
    "engine.disagreement": _read(
        ("engines",),
        "three copies of this tool can be in play and they may differ; this reads all "
        "three and names which one refused",
    ),
    # ------------------------------------------------------------------- the unreadable line
    # The one row that names no verb reaching it, and says so. Every write above starts from
    # a parsed line, and there is no parse here — so the honest answer is the two things that
    # *can* be tried and the statement that neither is guaranteed.
    "line.unparsed": _decide(
        "the grammar could not read this line at all, so no verb starting from a task "
        "reaches it; a control character is the one cause with a repair:",
        (("lint", "--fix"), "a codepoint that is not text can be the whole reason"),
        (("audit",), "read every marker-bearing line the count missed, and why"),
    ),
}

#: What each varying row reads, spelled for a reader rather than as a field name: one is a
#: key in `roadkeep.toml` and the other is not a setting at all (RK423).
_VARIES_READS = {
    "ref_scheme": "with `ref_scheme` in roadkeep.toml",
    "role": "with which governed file it is reported about",
}

#: The codes whose row is decided per project rather than per code (L6), and what each
#: reads. **Derived** from the table rather than restated beside it: a second list of the
#: same two names is the drift this package exists to stop, one layer down.
VARIES: Mapping[str, str] = {
    code: rule.varies for code, rule in _TABLE.items() if rule.varies
}


def codes() -> tuple[str, ...]:
    """Every code this table answers, sorted — the vocabulary `explain` lists (RK423)."""
    return tuple(sorted(_TABLE))


@dataclass(frozen=True, slots=True)
class Explained:
    """One code as a class rather than as an occurrence (RK423).

    A finding is about one line; a code is about a kind of defect, and until this there was
    nowhere to look the second one up — so a caller meeting `section.unpaired` for the first
    time grepped the package and reconstructed from an implementer's docstring what one
    screen would have said.

    Three fields and no more. The worked example is the argv the finding already carries,
    and a page long enough to scroll is a page an agent pays for in context to learn what it
    could have run.
    """

    code: str
    kind: str
    #: What produces this defect. Read off the ``fix`` row where it is written and off the
    #: doors otherwise, so the explanation and the remedy cannot drift the way a README and
    #: a checker do — there is only ever one sentence, in one place.
    cause: str
    remedy: Remedy
    #: What changes the answer on this row, where anything does (L6). Empty otherwise.
    varies: str = ""

    def __str__(self) -> str:
        lines = [f"{self.code}  [{self.kind}]", f"  cause    {self.cause}"]
        for door in self.remedy.doors:
            # The command, and its `what` only where that is not the cause already printed:
            # on a single-door row the two are the same sentence by :func:`_cause`, and
            # repeating it spends two thirds of the one screen this answers on restatement.
            # Never suppressed on a `decide`, where the `what` is not a description of the
            # defect at all — it is what distinguishes this door from the other one, which
            # is the entire content of the decision.
            lines.append(f"  remedy   {door.command if door.what == self.cause else door}")
        if self.varies:
            lines.append(f"  varies   {_VARIES_READS[self.varies]}")
        return "\n".join(lines)

    def payload(self) -> dict[str, object]:
        return {
            "code": self.code,
            "kind": self.kind,
            "cause": self.cause,
            "varies": self.varies or None,
            **self.remedy.payload(),
        }


def explain(code: str, config: Config | None = None) -> Explained | None:
    """The class behind one code. ``None`` for a code this tool cannot report."""
    rule = _TABLE.get(code)
    if rule is None:
        return None
    # A finding with no line and no subject: the templates render their blanks, which is
    # right here — an explanation is about the class, and a substituted id would be one
    # occurrence's, presented as if it were the rule's.
    found = remedy(_Class(code), config)
    assert found is not None  # `rule` is not None, so neither is this
    return Explained(code, found.kind, _cause(rule, found), found, rule.varies)


def _cause(rule: _Rule, found: Remedy) -> str:
    """Where the cause is written for this kind. One sentence, never two.

    A ``fix`` row states it outright, because its door describes the repair. Every other
    kind already had to say what the defect is in order to say what choosing a door means —
    so that sentence is the cause, and writing a second one beside it is the drift this
    package exists to stop, one layer down.
    """
    if rule.cause:
        return rule.cause
    return found.decision or found.doors[0].what


@dataclass(frozen=True, slots=True)
class _Class:
    """A finding about no line: what an explanation of the class is derived from."""

    code: str
    file: str = ""
    id: str = ""
    subject: str = ""
    lineno: int | None = None


def remedy(finding: object, config: Config | None = None) -> Remedy | None:
    """What closes ``finding``. ``None`` only for a code the table does not carry.

    Takes anything with ``code``, ``id``, ``lineno`` and ``file`` — a
    :class:`~roadkeep.linting.Finding`, a :class:`~roadkeep.linting.Note`, or a
    :class:`~roadkeep.schema.Violation` wrapped in one — because the caller repairing a
    line does not care which of the three reported it.
    """
    code = getattr(finding, "code", "")
    rule = _TABLE.get(code)
    if rule is None:
        return None
    if rule.varies and config is not None:
        rule = _varied(code, rule, finding, config)
    subject = getattr(finding, "subject", "") or getattr(finding, "id", "")
    lineno = getattr(finding, "lineno", None)
    doors = tuple(
        Door(_substitute(argv, subject, lineno), what) for argv, what in rule.doors
    )
    return Remedy(code, rule.kind, doors, rule.decision)


def _varied(code: str, rule: _Rule, finding: object, config: Config) -> _Rule:
    """The two rows a project's own configuration decides (L6)."""
    if code == "ref.mismatch" and config.schema.ref_scheme != "id":
        # An outline anchor is not derivable, so there is nothing mechanical to recompute:
        # the field is the author's and the fixer would be guessing an address.
        return _compose(
            ("amend", "{id}", "--ref", BLANK),
            "the anchor is not derived under this project's scheme, so it is yours to state",
        )
    if code == "id.duplicate" and _role_of(finding, config) == "roadmap":
        # `record renumber` opens the ledger and this is the other file: two *open* lines
        # sharing an id are two tasks, and one of them takes a free address.
        return _decide(
            "two open lines carry one id, which is two tasks sharing an address:",
            (("renumber", "{id}"), "move the later line, with its section and its dependents"),
            (("show", "{id}"), "read both first — they may be one line written twice"),
        )
    return rule


def _role_of(finding: object, config: Config) -> str:
    """Which governed file this finding is about, by the path the report printed."""
    where = getattr(finding, "file", "")
    for role in ROLES:
        if config.has(role) and config.relative(config.path(role)) == where:
            return role
    return ""


def _substitute(argv: Sequence[str], subject: str, lineno: int | None) -> tuple[str, ...]:
    """Fill a template. A field with no value keeps its blank rather than rendering `None`.

    That fallback is the module's own rule applied to itself: an argv reading
    ``--line None`` is worse than one reading ``--line …``, because the first looks
    runnable and the second says which word is missing.
    """
    values = {"id": subject, "line": "" if lineno is None else str(lineno)}
    out: list[str] = []
    for word in argv:
        for name, value in values.items():
            token = "{" + name + "}"
            if token in word:
                word = word.replace(token, value or BLANK)
        out.append(word)
    return tuple(out)
