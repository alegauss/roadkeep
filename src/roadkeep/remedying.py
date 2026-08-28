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
* ``decide`` — more than one door, and which one is right is editorial. Both are rendered,
  and :attr:`Remedy.decision` states what distinguishes them, so the choice is made from the
  report instead of by running one and reading its refusal. `repair` executes none of them,
  which is what lets one carry L4's blank where the choice is between an editorial write and
  a write only the author can compose — `deps.unknown` and `priority.block-unstarted`
  (RK435). "Both are rendered complete" is what this said, and two rows already refuted it.

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

**And it is the one place a command becomes text** (RK488). :class:`Door` was already the
shape — an argv and what it does, spelled as a shell line or as a tool call by whoever prints
it — but only findings went through it. Everything else composed its own: the guard's two
tables and its three sentences, the gate's, the attestation's, and a third copy of the whole
mechanism inside `serving`, each branching on the served prefix for itself. So a surface that
never learned to ask printed the shell form to a session holding the tools, and RK444, RK447,
RK448, RK475, RK477 and RK479 each taught one more site to ask without anything being able to
say how many were left. :meth:`Door.named`, :meth:`Door.mention`, :func:`offered` and
:func:`alongside` are the four renderings a message actually wants, and
`tests/test_remedying.py` holds the property that nothing outside this module spells one —
the same total-domain assertion the table above gets, about spellings instead of codes.

The prefix still arrives as a **field** and is not read here: which engine answers is a fact
about the project, and this module reads no project. What changed is that it is now handed to
a renderer instead of interpolated at forty call sites.

**A row states what is per-code and derives the rest** (RK490). Totality over the codes says
every finding has a door; it says nothing about whether the door is about that finding. Three
rows failed on exactly that and each was found by example — RK468 named one verb and
dispatched another, RK470 omitted which prose file the finding was in, RK472 dispatched a door
the verb refuses — and what bound them is that a row *repeated* the finding's subject, file or
verb instead of reading it. :func:`_values` is the one place any of them is derived and
:data:`FIELDS` is the declared domain of what a row may name, so the agreement is a property
over the whole table rather than a defect discovered one row at a time.
"""

from __future__ import annotations

import shlex
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import lru_cache

from .config import PROSE_ROLES, ROLES, Config
from roadkeep.kernel.schema import Dep

#: The six kinds, in the order a caller pays for them: nothing, one write, one read then a
#: judgement, one sentence, one choice, and one command that is not this tool's at all.
#: `repair` runs the first two and prints the rest.
KINDS = ("fix", "run", "read", "compose", "decide", "restore")

#: Marks the one field of a ``compose`` argv that the tool may not write (L4). Kept as a
#: distinct token rather than an empty string so a caller can find it without parsing prose.
BLANK = "…"


def _spelled_word(word: str) -> str:
    """One argv token as a line a shell reads back as that token (RK1265).

    **Whitespace and nothing else**, which is narrower than `shlex.quote`'s own rule and
    deliberately so: what this fixes is a token that would run as several arguments, and the
    other characters that reader quotes are already in doors that print correctly today —
    `<command> --help` is one of them, and `'<command>' --help` reads as a literal somebody
    typed. The :data:`BLANK` is never quoted either, for :attr:`Door.quoted`'s reason: it
    marks a field the author fills, and `'…'` reads as a value already chosen.
    """
    if BLANK in word or not word or not any(c.isspace() for c in word):
        return word
    return shlex.quote(word)


@lru_cache(maxsize=1)
def _reading() -> Mapping[str, frozenset[str]]:
    """Every verb this CLI declares read-only, and the flags that turn each into a write.

    Both halves come from the parser that declares them, because both are already there:
    `reads_only` is what keeps a command out of the write lock (RK117) and `writes_when`
    names the flag that makes one a write anyway (RK167) — `lint` is read-only and `lint
    --fix` is not, which is the case this mapping exists for and the one a set alone gets
    backwards.

    Deferred and cached: `cli` imports this module to build a report, so the edge back runs
    at call time (RK260), and the parser is built once — a remedy is rendered per finding
    and a report can carry hundreds.
    """
    from roadkeep.cli import build_parser  # noqa: PLC0415 - RK1015
    from roadkeep.verbs.declaring import writes_when  # noqa: PLC0415 - RK1171

    verbs = next(
        action
        for action in build_parser()._actions
        if getattr(action, "choices", None) and action.dest == "command"
    )
    out: dict[str, frozenset[str]] = {}
    for verb, parser in verbs.choices.items():
        if not parser.get_default("reads_only"):
            continue
        turns = set(writes_when(parser))
        out[verb] = frozenset(
            option
            for action in parser._actions
            if action.dest in turns
            for option in action.option_strings
        )
    return out


@dataclass(frozen=True, slots=True)
class Door:
    """One command that could close a finding, and what choosing it means.

    ``what`` is only load-bearing on a ``decide``, where it is the difference between the
    doors — but it is carried on every kind, because a caller printing a remedy has one
    shape to render and `explain` (RK423) has one field to quote.
    """

    argv: tuple[str, ...]
    what: str
    #: Whether this argv is somebody else's command (RK451). False for every door but the
    #: ``restore`` kind's: there the content of a governed file is gone, no verb of this tool
    #: brings it back, and the store is the repository (L2) — so the command is git's, and
    #: prefixing it with this engine would name a subcommand roadkeep does not have.
    foreign: bool = False

    @property
    def writes(self) -> bool:
        """Does running this door change the files (RK1015)?

        **Per door and not per remedy**, which is the whole of it: `deps.unknown` is one
        `decide` holding `gaps`, which answers a question and changes nothing, and `amend
        <id> --dep …`, which writes. The kind is the remedy's, so it says `decide` about
        both, and a caller that has to know which it just pressed — a quick-fix menu, a
        repair loop — could not ask.

        Derived from the verb and never declared twice: the CLI already states which
        commands only read, because that is what keeps one out of the write lock (RK117), and
        a second list here would be the drift this package exists to stop. A foreign door is
        somebody else's command and this tool has no opinion about it — `git checkout` writes
        and says so in its own name.
        """
        reading = _reading()
        if self.foreign or self.argv[0] not in reading:
            return True
        # A read-only verb with the flag that makes it a write: `lint --fix` is the case,
        # and the parser is where both facts are already declared.
        return any(flag in self.argv for flag in reading[self.argv[0]])

    @property
    def command(self) -> str:
        """The argv as a line to run, reaching this engine the way this machine can (RK254).

        Derived and never the literal console script: it exists only after a `pip install`
        that put the scripts directory on PATH, so on a plugin-installed machine — and in
        this repository — a remedy spelling it names a command that answers `command not
        found`. A remedy a caller cannot run is the defect this task was about, one step
        further along.

        A :attr:`foreign` door is already whole: it names another tool, so there is no
        invocation of this one to put in front of it.

        **A token carrying a space is quoted, and only such a token** (RK1265). Every door
        before the criteria carried argv of single words — an id, a code, a flag, or a
        :data:`BLANK` the author fills — so joining on spaces was the whole of it; the lead of
        a criterion is the caller's own prose and is what a remedy substitutes, so an unquoted
        line runs as eight arguments. The blank is left bare for :attr:`quoted`'s reason: a
        `'…'` reads as a value somebody chose, and it is the one token that is not one.
        """
        words = tuple(_spelled_word(word) for word in self.argv)
        if self.foreign:
            return " ".join(words)
        from .provenance import invocation

        return " ".join((invocation(), *words))

    @property
    def quoted(self) -> str:
        """:attr:`command`, spelled for the shell that will run it verbatim (RK1149).

        Every door before this one carried argv of single tokens — an id, a code, a flag — or a
        `BLANK` the author fills, so joining on spaces was the whole of it. A retry offered on a
        refusal carries the caller's **prose**: a symptom and a why, with spaces and apostrophes
        in them, and a command printed unquoted is one that runs as eight arguments or not at all.

        Beside :attr:`command` rather than replacing it: what a table prints and what a caller
        pastes are two readings, and quoting a `…` placeholder would spell it `'…'`, which reads
        as a value somebody chose.
        """
        if self.foreign:
            return shlex.join(self.argv)
        from .provenance import invocation

        return f"{invocation()} {shlex.join(self.argv)}"

    @property
    def complete(self) -> bool:
        """Whether every field is filled — false where L4 left one to the author."""
        return not any(BLANK in word for word in self.argv)

    def call(self) -> tuple[str, dict[str, object]] | None:
        """The same door as a **tool call**: the name and its fields, or ``None`` (RK449).

        `lint` and `explain` are both served, and what they handed a caller there was this
        argv — a list of shell words, to the one surface RK57 left with no console script and
        no PATH entry. So the door is published in both spellings and the caller takes the one
        its session can make.

        Derived from the argv and never tabled beside it. The mapping is the subcommand's
        **own parser**, which is what `serving` already reads to publish the schema, so a
        renamed flag moves both ends at once and there is no third declaration to fall behind.
        Two things fall out of that rather than being decided:

        * A door setting a field the tool surface withholds has **no call**, and `lint --fix`
          is exactly that — `--fix` writes, and RK16 keeps it where a human is standing, so
          `lint` is served without it. The one remedy that must stay a shell command stays one
          by derivation instead of by exception.
        * :attr:`argv` remains the fact. `repair` (RK422) dispatches it untouched, and this is
          computed beside it — which is what keeps the second spelling from becoming a second
          grammar.

        The :data:`BLANK` survives into the field it lands in, because it means the same thing
        there: L4 left that one to the author, and a call with the marker in it is a call to
        finish rather than one to make.
        """
        if self.foreign:
            return None  # somebody else's command; this surface serves none of it (RK451)
        from .serving import TOOLS, _fields_of, _subparser, serves  # noqa: PLC0415 - RK260

        # **Which** tool, asked once and in one place (RK488): `serves` reads `TOOLS` alone,
        # so the guard can afford the same question inside a hook budget a parser build would
        # spend four times over. What is left here is the tail as *values*, which is the one
        # half that genuinely needs the parser.
        name = serves(self.argv)
        if name is None:
            return None
        tool = next(one for one in TOOLS if one.name == name)
        rest = list(self.argv)[len(tool.argv_head) :]
        # The unconditional half, which is what this reader can ask: a door is composed
        # without a project (RK1157), and whether one opens a conditional field is that
        # project's answer — so a field only some projects offer has no call here.
        fields = _fields_of(_subparser(tool.command), rest, tool.unconditional)
        return None if fields is None else (name, fields)

    def payload(self, served: str = "") -> dict[str, object]:
        """This door as JSON — one writer, because two answers publish one now (RK1147).

        `Remedy.payload` built this row inline, and then `adopt` needed the same shape: its
        printed report has named the flag that reads a file the other way since RK285, and its
        payload published the count beside it and nothing else — the asymmetry `lint` has not
        had since RK15, on the one command whose whole output is a decision. An estimate's
        unread reading is not a finding and has no code, so what it carries is a door and not a
        `Remedy`, which is exactly why the row had to stop being a `Remedy` local.

        ``served`` is the prefix this session's tools arrive under, and where it is given the
        door carries its **call** beside its argv (RK449). Absent — or where nothing serves the
        door, which is every `adopt` door, that verb being deliberately unserved — only the
        argv is published, which is what every consumer written before RK449 already reads.
        """
        row: dict[str, object] = {
            "argv": list(self.argv),
            "what": self.what,
            "complete": self.complete,
            # Whether pressing it changes the files (RK1015): the kind is the remedy's, and one
            # `decide` holds a read and a write.
            "writes": self.writes,
        }
        call = self.call() if served else None
        if call is not None:
            name, fields = call
            row["call"] = {"tool": f"{served}{name}", "arguments": fields}
        return row

    def named(self, served: str = "") -> str:
        """This door's **command alone**, in the spelling ``served`` has (RK488).

        The third of the three renderings, and the one a *table* prints: :attr:`command` is
        the shell line unconditionally, :meth:`spoken` is a spelling plus what it does, and
        this is the column the rows are padded to, with the purpose in a column of its own.

        Cheap by construction — it asks `serving.serves` and never the parser — because the
        guard composes one of these per row inside a `PreToolUse` the harness waits on. The
        arguments the served name drops are :meth:`passing`'s to state.
        """
        if self.foreign or not served:
            return self.command
        from .serving import serves  # noqa: PLC0415 - RK260, the printing path only

        name = serves(self.argv)
        return self.command if name is None else f"{served}{name}"

    def passing(self, served: str = "") -> str:
        """The arguments the served spelling moved out of the command, or ``""`` (RK488).

        A flag is not a word over that transport: `repair --dry-run` is the `repair` tool
        carrying `dry_run`, so :meth:`named` drops the flag and this is where it goes. Spelled
        as the dests, which is what a caller passes and what the tool's own schema names.

        The flags and not the positionals. `explain <code>` reaches its tool as `code` too,
        and a placeholder is not a dest — `delivered <x>` would read as *pass x* where the
        field is `block` — so what cannot be derived is left to the purpose beside it rather
        than guessed, which is :func:`_substitute`'s rule about a blank one layer up.
        """
        if not served or self.foreign:
            return ""
        from .serving import TOOLS, dest_of, serves  # noqa: PLC0415 - RK260, printing only

        name = serves(self.argv)
        if name is None:
            return ""  # a shell line, where the argv already shows them
        # The tool's own command, because a dest is declared per subcommand and two of them
        # cross: `--marker` sets `status` on `add` and `--status` sets `marker` on `resume`.
        command = next(one for one in TOOLS if one.name == name).command
        return ", ".join(dest_of(word, command) for word in self.argv if word.startswith("--"))

    def mention(self, served: str = "", *, quote: str = "") -> str:
        """This door as a **sentence** names it: the spelling, and the fields it carries.

        :meth:`named` with the values filled in, for prose rather than for a table — the form
        `serving` rewrites a printed backtick into (RK449) and the head of :meth:`spoken`.
        Falls back to :meth:`named` and never straight to the shell, so one door cannot answer
        *tool* to a table and *shell* to a sentence in the same message.

        ``quote`` wraps the **command** and not the fields it carries, which is the one thing a
        caller cannot add afterwards: `` `tool` with anchor: RK1 `` reads as one call and a
        backtick around the whole of it reads as one command line to paste.
        """
        call = self.call() if served else None
        if call is None:
            return f"{quote}{self.named(served)}{quote}"
        name, fields = call
        named = "  ".join(f"{key}: {value}" for key, value in fields.items())
        return f"{quote}{served}{name}{quote}" + (f" with {named}" if named else "")

    def spoken(self, served: str = "") -> str:
        """This door in the spelling ``served`` has, falling back to the shell one (RK478).

        The sentence form of :meth:`call`, for the surfaces that print a door instead of
        publishing it: `payload` hands a consumer both and lets it pick, and a message an
        agent reads has room for exactly one. Nothing new is decided here — a door with no
        call, which is `lint --fix` and every foreign one, is a shell command wherever it is
        shown, because that is what it is.
        """
        return f"{self.mention(served)}  — {self.what}"

    def __str__(self) -> str:
        return f"{self.command}  — {self.what}"


def offered(doors: Sequence[Door], served: str = "", indent: str = "  ") -> list[str]:
    """A table of doors, each in this session's spelling, padded to the widest (RK488).

    The one renderer for *here are the commands*, and the reason it is a function rather than
    six copies of a `max(len(...))`: every surface that offers a table used to compose the
    served branch and the shell branch itself, so a module that never learned to ask printed
    the shell form to a session holding the tools — which RK444, RK447, RK448, RK475, RK477
    and RK479 each fixed at one more site, none of them able to say how many were left.

    The **width is per rendering**, not per table: a tool name is longer than a verb, so a
    column measured on the shell spelling and printed in the served one is a column that does
    not line up. That is the whole reason a caller cannot pad these itself and hand them over.

    :meth:`Door.passing` is appended where the served name dropped arguments, because a tool
    row that named neither the flags nor the fields is the shell row's information without its
    precision. Empty on the shell spelling, where the argv already shows them.
    """
    rows = [(door.named(served), door.passing(served), door.what) for door in doors]
    width = max((len(name) for name, _, _ in rows), default=0)
    return [
        f"{indent}{name:<{width}}  {what}" + (f" — pass {fields}" if fields else "")
        for name, fields, what in rows
    ]


def alongside(doors: Sequence[Door], served: str = "") -> tuple[str, ...]:
    """Several doors in one **sentence**, with the engine named once (RK488).

    :func:`offered` is the table and this is the prose beside it, holding the one rule both
    surfaces that write such a sentence had found for themselves: a served name is
    self-contained, so each carries its prefix, while a shell line repeats the invocation per
    verb — three times inside a notice whose whole budget is 260 characters. So the engine
    leads and the rest are the argv alone, which is how a reader writes the second command of
    a pair anyway.

    What it does **not** decide is the sentence around them. A served spelling drops the
    arguments a shell spelling shows, so the two say different things about what a verb takes,
    and that difference is prose the author writes — this owns which spelling, and never which
    words.
    """
    spelled = [door.named(served) for door in doors]
    if served:
        return tuple(spelled)
    return (*spelled[:1], *(" ".join(door.argv) for door in doors[1:]))


@dataclass(frozen=True, slots=True)
class Remedy:
    """What closes one finding: a command to run, or a decision to take."""

    code: str
    kind: str
    doors: tuple[Door, ...]
    #: What has to be chosen between the doors. Non-empty exactly when ``kind`` is
    #: ``decide``, because a single door has nothing to decide between.
    decision: str = ""
    #: Whether several doors are **ordered** rather than alternative (RK1336). Until this
    #: existed, more than one door meant one thing — a choice — and a row whose doors are
    #: steps had nowhere to say so: `budget.session` needs the read that ranks the
    #: descriptions before the read that prices the whole, and neither is an alternative to
    #: the other. Named rather than inferred from the count, because a rule that spelled
    #: *choose one of these* and *do these in turn* the same way would hide the difference
    #: the reader most needs — which is the argument the doors table already makes about
    #: naming why a site is not executed instead of writing "no".
    sequence: bool = False

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

        **Still the kind, and RK1015 measured why.** That task proposed reading
        :attr:`Door.writes` instead — the door now carries it, which is what a caller outside
        this process needed — and the substitution does not hold: `section.too-long` closes
        with `section amend <id> --body -`, a door that writes, is complete and is one, and a
        repair loop running it would read a paragraph off a stdin it does not have. What the
        kind carries and no door field does is *who supplies the prose*, so `compose` is a
        word about the author and not about the command.
        """
        return self.kind in ("fix", "run") and all(d.complete for d in self.doors)

    def payload(self, served: str = "") -> dict[str, object]:
        """The `--json` form: argv as a list, because a consumer runs it rather than reads it.

        ``served`` is the prefix this session's tools arrive under, and where it is given each
        door carries its **call** beside its argv (RK449): the same door, named as the surface
        the caller is already on. Passed in rather than read here for the reason `Notice` and
        `Refusal` take theirs — which engine answers is a fact about the project, and this
        module reads no project. Absent, or where nothing serves the door, only the argv is
        published, which is what every consumer written before this already reads.
        """
        return {
            "kind": self.kind,
            "decision": self.decision,
            # Both registers say which kind of several these are (RK1336): a consumer looking
            # at two doors and a blank decision would otherwise have to guess whether to offer
            # a choice or a sequence, which is the guess the stated register no longer makes.
            "sequence": self.sequence,
            "doors": [door.payload(served) for door in self.doors],
        }

    def spoken(self, served: str = "") -> str:
        """The same text :meth:`__str__` renders, in the spelling this session has (RK478)."""
        if self.kind == "decide":
            return f"{self.decision}\n" + "\n".join(
                f"    {door.spoken(served)}" for door in self.doors
            )
        if self.sequence:
            # Every door and not the first (RK1336): a row carrying more than one names a
            # sequence, and printing the head of it silently drops the step that says what to
            # do with what the first one shows. `decide` already rendered its several because
            # choosing between them is its whole content — this is the same rendering for a
            # row whose several are ordered rather than alternative.
            return "\n    ".join(door.spoken(served) for door in self.doors)
        return self.doors[0].spoken(served)

    def __str__(self) -> str:
        return self.spoken()


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
    #: Whether several doors are ordered rather than alternative (RK1336). See
    #: :attr:`Remedy.sequence`, which this fills in.
    sequence: bool = False
    #: Whether this row's doors name another tool's command (RK451). On the row and not on
    #: each door, because it is a property of the *kind*: `restore` is the one that leaves
    #: this tool's vocabulary, and a door-by-door flag would let a row be half foreign.
    foreign: bool = False


def _fix(cause: str, what: str) -> _Rule:
    return _Rule("fix", ((("lint", "--fix"), what),), cause=cause)


def _run(argv: tuple[str, ...], what: str) -> _Rule:
    return _Rule("run", ((argv, what),))


def _restore(argv: tuple[str, ...], what: str) -> _Rule:
    """One command **another tool** owns, for a finding no verb here can close (RK451).

    The one kind whose door is not a roadkeep argv. A governed file whose content a crash
    took is not malformed and cannot be repaired: there is nothing left to render from. What
    closes it is the store, and the store is the repository (L2) — so the command is git's,
    marked :attr:`Door.foreign` so nothing prefixes it with this engine, offers it as a tool
    call or hands it to `repair`.
    """
    return _Rule("restore", ((argv, what),), foreign=True)


def _read(argv: tuple[str, ...], what: str) -> _Rule:
    """One command that answers the finding and writes nothing. See :data:`KINDS`."""
    return _Rule("read", ((argv, what),))


def _reads(*steps: tuple[tuple[str, ...], str]) -> _Rule:
    """Two or more reads that answer one finding, in the order the work goes (RK1336).

    :func:`_read`'s plural, and the reason it exists rather than a second single door: a
    finding whose remedy is *pick something and cut it* needs the read that ranks the
    candidates before the read that prices the whole, and one door can only be one of those.
    The sequence is the claim, as it already is for a `run` row — a second step is not an
    alternative to the first.
    """
    return _Rule("read", steps, sequence=True)


def _compose(argv: tuple[str, ...], what: str) -> _Rule:
    return _Rule("compose", ((argv, what),))


def _varies_on_queue(cause: str, what: str) -> _Rule:
    """A dead queue entry: mechanical where the section holds the order, `migrate` where the
    config still does (RK427). `--fix` reads the roadmap and only the roadmap, so on a project
    that never migrated it repairs nothing and the caller is left holding a finding whose
    named door does not open that file."""
    return _Rule("fix", ((("lint", "--fix"), what),), varies="queue", cause=cause)


def _decide(decision: str, *doors: tuple[tuple[str, ...], str]) -> _Rule:
    return _Rule("decide", tuple(doors), decision)


#: Every code the package can emit, and what closes it. The domain is asserted total in
#: `tests/test_remedying.py` against the codes scraped from `linting` and `schema` — a code
#: added without a row here fails the suite (RK421).
#:
#: `{id}` is the finding's subject: a task id on most codes, and on the rest whatever the
#: emission site put in that slot — a block label, a section anchor, a queue token. `{line}`
#: is the line it was read at, and `{label}` is the block **inside** a queue token, for the
#: one door that takes `--block` rather than the token itself (RK435). Those three and no
#: others: `{first}` and `{role}` were named here for years and substituted nowhere, so a
#: door using either would have rendered its own braces — which the suite now refuses.
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
        "the `(deps: …)` annotation caches another line's status and that line moved: "
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
    "priority.shipped": _varies_on_queue(
        "the queue names work that has shipped: every token in an order names work, and "
        "work leaves — the one list a departure does not reach",
        "the entry is dropped, named in the report and never in silence",
    ),
    "priority.retired": _varies_on_queue(
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
    # ------------------------------------------------------------------ the roadmap's other bullet
    # RK1266, and the rows are RK1265's read across: the two lists are one grammar, so what
    # closes a criterion closes a constraint with the verb's name changed. Missing until now
    # because the scrape could not see a code with a hyphen in its head — the gate reported all
    # four and the suite was green, which is the state a totality test exists to make impossible.
    #
    # `--lead` is not passed on any of them: the lead **is** the address, so the verb takes it
    # as its one positional and the finding supplies it as the subject.
    "non-goal.duplicate": _run(
        ("non-goal", "drop", "{id}"),
        "two bullets lead the same way: the later goes and the first stays, which is where "
        "the reader already found it",
    ),
    # The pair, for the reason `scoping.Unshaped` refuses an amend on one: the render would
    # impose the shape and move the address while doing it.
    "non-goal.shape": _decide(
        "the bullet carries no bold lead, so it has no address this format can write around",
        (
            ("non-goal", "drop", "{id}"),
            "take the bullet out, then `non-goal add --lead … --why …` writes it in the "
            "shape — honest about the lead changing",
        ),
        (
            ("non-goal", "list"),
            "read the list first where the lead as this file reads it is not obvious",
        ),
    ),
    "non-goal.why": _compose(
        ("non-goal", "amend", "{id}", "--why", "-"),
        "past the limit for a constraint's reason; the shorter sentence is yours and arrives "
        "on stdin",
    ),
    "non-goal.lead": _decide(
        "the lead is the address, so shortening it is a different constraint and not an edit",
        (
            ("non-goal", "drop", "{id}"),
            "remove it, then `non-goal add --lead … --why …` with the shorter head",
        ),
        (
            ("non-goal", "list"),
            "read what this project already refuses before rewriting one of it",
        ),
    ),
    # ------------------------------------------------------------------ the roadmap's third list
    # RK1265. The lead is the address, so the three that are about one bullet all reach it by
    # that lead — which the emission site passes as the finding's subject. `--block` is left off
    # every door on purpose: the verb resolves it from the one list carrying the lead, and a
    # remedy that had to spell a block it cannot read would be the blank RK420 exists to remove.
    # The address stopped existing, so the **bare** drop is the door (RK1318): the addressed
    # form takes a `--block` or a `--task` naming exactly what is gone, which would be a
    # command that cannot run. A region the last drop leaves empty carries no lead, and a
    # remedy with a blank subject answers nothing here — that one is `--fix`'s, a heading
    # addressed to nothing with nothing under it being derived dead.
    "criterion.orphan": _run(
        ("criterion", "drop", "{id}"),
        "the list is addressed to a block or an id no file answers, so what it asks about "
        "cannot be finished — the bullets go, and the heading with the last of them",
    ),
    "criterion.duplicate": _run(
        ("criterion", "drop", "{id}"),
        "two bullets in one block lead the same way: the later goes and the first stays, "
        "which is where the reader already found it",
    ),
    # The shape, and the one pair that cannot be a single door: the lead is the address, so a
    # bullet whose head is its first sentence is repaired by removing it and writing one — an
    # `amend` would impose the shape and move the address while doing it.
    "criterion.shape": _decide(
        "the bullet carries no bold lead, so it has no address this format can write around",
        (
            ("criterion", "drop", "{id}"),
            "take the bullet out, then `criterion add --block … --lead … --why …` writes it "
            "in the shape — honest about the lead changing",
        ),
        (
            ("criterion", "list"),
            "read the list first where the lead as this file reads it is not obvious",
        ),
    ),
    "criterion.why": _compose(
        ("criterion", "amend", "{id}", "--why", "-"),
        "past the limit for a criterion's reason; the shorter sentence is yours and arrives "
        "on stdin",
    ),
    # The lead and not the reason, so `amend` is the wrong door: that verb refuses to touch an
    # address, and a shorter lead is a different criterion.
    "criterion.lead": _decide(
        "the lead is the address, so shortening it is a different criterion and not an edit",
        (
            ("criterion", "drop", "{id}"),
            "remove it, then `criterion add --block … --lead … --why …` with the shorter head",
        ),
        (
            ("criterion", "list"),
            "read what the block already claims before rewriting one of it",
        ),
    ),
    "priority.config": _read(
        ("priority", "list"),
        "the section wins over the config: read the queue that is live, then take the "
        "`priority = [...]` line out of roadkeep.toml",
    ),
    # Not a finding of its own — the row the two above become on a project that never
    # migrated (RK427). `--fix` reads the roadmap's section, so on a config-declared queue
    # it repairs nothing and the caller is left with a defect the gate names in a file no
    # verb opens. `_varied` swaps this in when `lint` read the order out of the config.
    "priority.unmigrated": _run(
        ("priority", "migrate"),
        "this queue is still roadkeep.toml's, which no verb writes: move it into the "
        "roadmap and every queue verb reaches it",
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
    # The coming-back door first, as `priority.deferred`'s is: what the order names is work
    # a decision would restore, so dropping it is the one move that guarantees it never
    # fires. `--block` is deliberately absent from the read — it takes a bare label and the
    # only value this table can substitute is the queue token — and `resume` is absent for
    # the same reason: it takes an id, and which line comes back is what the read answers.
    "priority.block-paused": _decide(
        "every line filed under this block is in the store, so the tier can only fire once "
        "one comes back — and where in the order it sat is what the store did not keep:",
        (
            ("list", "--role", "deferred"),
            "read what is set aside: the address is an id, so `resume <id>` is what makes "
            "this tier fire again",
        ),
        (
            ("priority", "drop", "{id}"),
            "the order should not name a block whose lines are all paused",
        ),
    ),
    # This read *the block was never declared, so the token addresses nothing* —
    # `priority.block`'s condition, printed under the one code that fires only where a
    # heading **does** declare the label (RK435). Three codes share one shape and their
    # remedies were written together; the one that drifted was invisible, because a note
    # still prints and the exit is still 0. A reason contradicting the line above it is
    # worse than none: it is the half a reader trusts.
    #
    # The kind moves with the sentence. A heading before its lines is the order `block add`
    # prescribes — which is why `_dead_block` makes this a note and not a finding — so the
    # entry is *early* rather than dead, and `priority drop` is the one move that guarantees
    # the tier never fires. It is lossy in the bargain: the queue keeps no place to put a
    # token back into, which is the fact `priority.deferred` is a `decide` for. So the drop
    # stays as one of two answers and never as the only one, and the other door is the
    # continuation the prescribed order already started.
    #
    # A `read` was the third candidate and is the one this task may not take: `list --block
    # <label>` does answer here (exit 0, `Block B is empty: …`), but it answers in
    # `Stage`'s words — so the door would print a second classification of the same block
    # beside the gate's, which is the reader RK434 has just finished removing.
    "priority.block-unstarted": _decide(
        "the heading declares the label and no file files a line under it, which is the "
        "order `block add` prescribes — so this entry is early rather than dead, and which "
        "of the two it is only the author knows:",
        (
            ("add", "--block", "{label}", "--symptom", BLANK, "--why", BLANK),
            "the work is still coming: the tier fires on the first line filed under it",
        ),
        (
            ("priority", "drop", "{id}"),
            "the plan moved: the entry goes, and the place it held in the order with it",
        ),
    ),
    # ------------------------------------------------------------------------ the headings
    # RK451: no verb here closes it — the content is gone rather than malformed, and there
    # is nothing left to render from. `--` before the path, because a file named like a flag
    # is a path git would otherwise read as one.
    "file.not-text": _restore(
        ("git", "checkout", "--", "{file}"),
        "the file's content did not reach the disk; the store is the repository, and this "
        "puts back what it last committed",
    ),
    # Varies with the **files**, which is the third thing a row is decided by (RK468). The
    # finding's own sentence has branched on whether the later region is empty since RK425 —
    # the caller's next question is whether their lines survive it — and this row could not
    # ask, so on a droppable one the message said `block drop` and the remedy said `block
    # merge`. `repair` dispatches the remedy, so it ran the verb the sentence above it did
    # not name; both leave a legal file, which is why nothing caught it.
    "block.repeated": _Rule(
        "run",
        ((("block", "merge", "{id}"), "the label's later headings fold into the first, "
          "entries and all"),),
        varies="region",
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
    "id.reserved": _decide(
        "`reserved_ids` says this address is spoken for and never written as a line, and a "
        "line carries it — so the declaration and the file disagree, and which of them is "
        "right is the author's to say:",
        (
            ("renumber", "{id}"),
            "the reservation stands; the line and its dependents move to an address of "
            "their own",
        ),
        (
            ("next-id",),
            "the reservation is stale; drop the token from `reserved_ids`, and this says "
            "what the deriver answers once it is gone",
        ),
    ),
    "id.format": _run(
        ("renumber", "{id}"),
        "the id does not match this project's shape; renumber moves the line and its "
        "dependents to one that does",
    ),
    # The pair no live project can reach yet (RK1084): neither adopting corpus declares a
    # store, and a departure that stopped between its two writes is what leaves it. No verb
    # takes it — `resume` would place an open line for work the ledger records as gone —
    # so the door is the two reads that say which file is right, and the repair is a
    # decision this tool may not make for somebody's history (L4).
    "id.paused-and-gone": _decide(
        "the ledger records this id as gone and the store still says it is paused; which "
        "of the two is the leftover is a fact about what actually happened:",
        # `{id}` and no longer a blank (RK1340): the walk over `PAIRS` passes the task id as
        # this finding's own, so printing `…` asked the reader to type the one value the tool
        # had just held — on a finding whose whole content is that this id is in two files.
        # And the sentence says what `show` does: it joins a task out of the files holding a
        # piece of it and reports the ledger's, the store's pause appearing in neither
        # register — so *side by side* was a promise the door could not keep.
        (("show", "{id}"), "the entry as the ledger holds it, which is the side claiming the "
                           "work is done"),
        (("origin", "{id}"), "which commit wrote each, which is what dates the pair"),
    ),
    # The store's own pair (RK1081). `resume` and not `defer`: the roadmap already says the
    # work is open, which is what a resume produces, so the store entry is the stale half.
    "id.paused-and-open": _run(
        ("resume", "{id}"),
        "the deferred store and the roadmap both carry this id — a pause that stopped "
        "between its two writes, or a resume that did; either way the open line is what "
        "the files should say, so this removes the store's copy and places nothing",
    ),
    "id.two-files": _run(
        ("ship", "{id}"),
        "the ledger already records this id and the roadmap still carries a line for it — "
        "a ship stopped between its two writes, or a partial marker left beside an entry "
        "recording the whole; either way, re-running closes the line and writes no second "
        "entry",
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
    # Varies with the file for `block.repeated`'s reason, one code over (RK472): the drop
    # this names refuses while a **nested** section is claimed by an open line, so on Turing
    # it was dispatched and refused on every `repair`, forever. `runnable` asks whether the
    # argv's fields are filled and never whether the command would run.
    "section.stale": _Rule(
        "run",
        ((("section", "drop", "{id}"),
          "the task is in the ledger and `ship` deletes the section, so this survived a "
          "hand edit"),),
        varies="nested",
    ),
    "section.orphan": _decide(
        "nothing points at this section, which is either a design that outlived its line "
        "or a line that was lost:",
        (("section", "drop", "{id}"), "the work is gone and the rationale went with it"),
        (("show", "{id}"), "read it first — a lost line is re-filed with `add`, not deleted"),
    ),
    # `--to` is **required** on `section move`, and this row omitted it — so the door was a
    # complete argv the CLI refuses, and `repair` would have dispatched it (RK474). Neither
    # corpus carries this code, which is why RK473's sweep could not see it and the parser
    # check could. A `compose` and not a `run`: the free address is the author's to pick, and
    # naming which one would be this tool choosing where somebody's design lives.
    # Outline-only as written, and offered under both schemes until RK1337. Reproduced on a
    # scratch project at `ref_scheme = "id"`: `anchors --next` exits 2 there, having no
    # numbering to take the next of, and `section move` refuses an id-addressed section by
    # design — *the address is not this verb's to move*. So the door named a command the verb
    # it names rejects. `varies` because what closes this genuinely differs by scheme, which
    # is what that field is for.
    "section.duplicate": _Rule(
        "compose",
        (
            (
                ("section", "move", "{id}", "--to", BLANK),
                "one anchor is at two places in one file; move the later under an address "
                "of its own, which `anchors --next` names",
            ),
        ),
        varies="ref_scheme",
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
    # RK1106. Not a `--fix`: a citation is prose, and repointing it at a different anchor or
    # rewriting the sentence that argued from it are different edits with different meanings,
    # which is exactly the statement about the work L4 keeps out of this tool. Two doors and
    # the read second, because the anchor may never have existed — a typo has no design to go
    # and read, and `origin` is what tells the two apart (RK212).
    "ref.dangling": _decide(
        "this section's prose cites an anchor no prose file declares, and whether the design "
        "moved or was never there decides which edit it is:",
        (
            ("section", "amend", "{id}", "--body", "-"),
            "the sentence is this section's, so repointing the citation or rewriting the "
            "argument that leant on it arrives on stdin",
        ),
        (
            ("origin", BLANK),
            "the cited anchor, if it ever was one: this answers which commit wrote that "
            "design and which took it, so a sentence can be corrected instead of deleted",
        ),
    ),
    # RK1168. `compose` and one door: the citation is this section's own sentence, and which
    # address it meant — the local `S:I.2` or the other file's `I.2` — is a claim about the
    # argument that only its author can make. What the finding supplies is that the two exist;
    # writing the corrected sentence is the half L4 keeps out of the tool.
    "ref.crossed": _compose(
        ("section", "amend", "{id}", "--body", "-"),
        "the citation resolves into the other prose file while this one declares the same "
        "address; the sentence naming which it meant arrives on stdin",
    ),
    # RK1380. Two doors and a decision, because the sentence is in whichever file cites the law
    # and the verb follows the file: a design is `section amend`, a ledger entry is `record
    # amend`, and both take the prose on stdin. Which of the two — and whether the citation was
    # mistyped or the argument leant on a law this project does not hold — is the author's, so
    # no `{id}` is substituted here: this finding names a line and not a task.
    "law.unknown": _decide(
        "a sentence cites a law the table does not declare, and where it sits decides the "
        "verb that corrects it:",
        (
            ("amend", "{id}", "--why", "-"),
            "where the citation is in a roadmap line's why, and `restate` where it is in the "
            "claim, that being what the line is rather than a field on it",
        ),
        (
            ("section", "amend", "{id}", "--body", "-"),
            "where it is in a design, the corrected sentence arriving on stdin",
        ),
        (
            ("record", "amend", "{id}", "--why", "-"),
            "where it is in a ledger entry, which is the third prose a law is cited from",
        ),
    ),
    "section.too-long": _compose(
        ("section", "amend", "{id}", "--body", "-"),
        "past the word budget; the shorter prose is yours and arrives on stdin",
    ),
    # RK492. `compose` and not `run`: the pathspec and the pattern are the author's claim
    # about what this migration is, and a fixer guessing either would be composing the one
    # thing L4 forbids — a statement about the work rather than a rendering of one.
    "body.empty": _compose(
        ("section", "amend", "{id}", "--body", "-"),
        "the pointer resolves to a heading with no prose; the rationale is yours and "
        "arrives on stdin",
    ),
    "title.empty": _compose(
        ("section", "amend", "{id}", "--title", BLANK),
        "the section is addressed and unnamed; a heading is what a reader sees before the "
        "prose, and naming it is not the tool's",
    ),
    "body.promise": _decide(
        "the design names an id no line carries, which the deriver reads as spent and the "
        "next `add` steps past (RK431) — and whether it was an illustration, the id this "
        "task should have had, work not filed yet, or an address this project reserved "
        "and will never write as a line is the sentence's meaning, not the tool's:",
        (
            ("next-id",),
            # The door RK1027 found missing. Both rows below assume the id was an error, so
            # a caller authoring two tasks that cite each other was told to rename or delete
            # a cross-reference the backlog wanted — the outcome that costs something. The
            # read and not the `add`, because the ordering is the whole advice: what the
            # sibling's id will be, filed first, and this section written after.
            "the id is a sibling not filed yet; this says what it will be — `add` it "
            "first, and the section then names a line that exists",
        ),
        (
            ("section", "amend", "{id}", "--body", "-"),
            "it was an example; spell it outside this project's prefix, where nothing "
            "numbers it",
        ),
        (("gaps",), "read where the id went before deciding it was never a line"),
        (
            ("lint",),
            # The fourth reading, and the one the mechanism was built for (RK1047): an id
            # this project spoke for and will never write as a line. Shio declared four
            # epics and six retired ranges and went from twelve findings to one — where the
            # rewording above would have made its non-goals stop naming what they refuse.
            "the id is reserved: add it to `reserved_ids` in roadkeep.toml, where the "
            "deriver skips it because it IS taken — then this re-reads clean",
        ),
    ),
    "remaining.format": _compose(
        ("section", "amend", "{id}", "--body", "-"),
        "the declared query is not `<pathspec> :: <regex>` per line; the corrected block "
        "is yours and arrives on stdin",
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
        "read what the block dep resolves to — its members, or the standing that says "
        "nothing is filed under the label — before the line is picked",
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
    # RK1297. All four are `--requires`, which replaces the whole group, and that is the
    # honest door even for `requires.unknown` — where the other repair is to declare the word
    # in `[requirements]`. Naming a config edit here would be this table offering a hand edit
    # to the one file the guard denies, and the choice between the two is the author's: a
    # misspelt requirement is a line to correct, and a real one is a vocabulary to widen.
    "requires.format": _compose(
        ("amend", "{id}", "--requires", BLANK),
        "the token is not a requirement this grammar reads: one word, no padding",
    ),
    "requires.unrenderable": _compose(
        ("amend", "{id}", "--requires", BLANK),
        "the token carries a bracket, a comma or an arrow, so the line it is written into "
        "stops parsing; a requirement is one word",
    ),
    "requires.unknown": _compose(
        ("amend", "{id}", "--requires", BLANK),
        "`[requirements] declared` does not name it, so `pick` matches it against nothing "
        "and the line is offered to nobody — restate it, or declare the word",
    ),
    "requires.duplicate": _compose(
        ("amend", "{id}", "--requires", BLANK),
        "one requirement stated twice; `--requires` is repeatable, so state each once",
    ),
    # RK1229. A `compose`, because what the dep should say instead is the caller's: the
    # parenthetical they wrote is usually a sentence about *why* the dependency exists, which
    # belongs in the section the line points at and not inside a rendered group.
    "deps.unrenderable": _compose(
        ("amend", "{id}", "--dep", BLANK),
        "a dep carrying `)` or the pointer arrow stops the line parsing, and then no verb "
        "reaches it; the parenthetical belongs in the section, not in the dep",
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
    # `record amend` and never `amend` (RK1203). This finding fires on the **ledger alone** —
    # `_paths` reads `documents["changelog"]` and nothing else, a roadmap naming an artefact
    # its task exists to write being the opposite claim — so the door named here was not merely
    # wrong for one role, it was wrong on every finding this code can produce. `amend` loads
    # the roadmap, looks the id up in `roadmap.by_id()` and raises `NotOpen` for anything the
    # ledger holds; it was built to correct an open line and says so. Found adopting Turing,
    # where T759 names a script that moved to its own repository: the one remedy offered was
    # the one verb that structurally cannot perform it, and following it spends a call to learn
    # the door is shut.
    #
    # `--lines` is named in the sentence rather than put in the argv, because how many lines an
    # entry spans is a fact about that entry and not a constant this table could carry — and on
    # the corpus that found this the entry was 1,600 characters across several of them.
    "path.missing": _compose(
        ("record", "amend", "{id}", "--why", BLANK),
        "a shipped entry names a path the repository no longer has; the path is prose, so "
        "the correction is the sentence — add `--lines <n>` where the entry wraps",
    ),
    "budget.absent": _compose(
        ("budget",),
        "a `[budgets]` entry names a file that is not there; read what is budgeted, then "
        "correct the entry in roadkeep.toml",
    ),
    # The read is the door and there is no `--fix` for it (RK1059): what a tool costs is
    # its own `help=` and its exposed arguments, so the shorter description is the author's
    # and the only mechanical part is finding which tool grew.
    # The one finding whose subject is a rule rather than a record (RK1068), so the door is
    # the read that shows what the rule produces — and the edit is a config line, which no
    # verb of this tool writes: `[grammar.<role>]` is the author's declaration (L6).
    "grammar.unreadable": _compose(
        ("show", BLANK),
        "a declared grammar cannot read back what it writes; read any one line, compare it "
        "with the rendering the report carries, then correct `[grammar.<role>]` — the id is "
        "the author's because every line in the file is equally evidence",
    ),
    # A note and not a finding, so the door is a read and there is nothing to repair: the
    # ceiling held (RK1105). What it reports is that the declared number was measured on a
    # working tree and this count is the commit's, so the file has room its author never
    # voted for — and bringing a ceiling down is an argument about what may be loaded every
    # turn, which is the one edit in `roadkeep.toml` no verb of this tool makes for you.
    "budget.translated": _read(
        ("budget", "--file", "{id}"),
        "the counted bytes are the commit's and this checkout pays more; this prints both "
        "beside the ceiling, and lowering it is a line in roadkeep.toml",
    ),
    # RK1288. `{id}` is the line the ranking could not measure, and the door is the read that
    # tries it alone: the whole answer is what refused it, which that call prints beside the
    # ranking rather than as one row inside a report about eight other things.
    "read.unpriced": _read(
        ("cost", "--brief", "{id}"),
        "the ranking could not compose this brief, so the widest is unaccounted for; this "
        "asks for that one and prints what refused it",
    ),
    # RK1287. A note and not a defect: the gate priced what a session is about to brief and
    # says how many it left out, which is `deps.collective`'s shape — the door is the read
    # that answers the whole question, and there is nothing here to repair.
    "read.priced": _read(
        ("cost", "--brief"),
        "the gate prices the briefs `pick` offers next, so a backlog's length never reaches "
        "it; this ranks every open line and names what each costs",
    ),
    # RK1286. `{id}` is the task whose brief is over, which this finding carries as its
    # subject: the ranking answers *which one*, and the finding already said that — what the
    # reader needs next is what that one brief costs and where the size went.
    "read.over": _read(
        ("cost", "--brief", "{id}"),
        "this is the read that replaces reading the file, so one that does not fit a tool "
        "result is a task a session opens the roadmap for; what closes it is a shorter "
        "design, a narrower field, or a ceiling re-argued in `roadkeep.toml`",
    ),
    # Two reads and the ranking first (RK1336). The finding says no single tool is at fault,
    # then had to send the reader somewhere no tool was named at all — when what they do next
    # is pick one. Measured on this corpus: the ceiling has been re-argued six times and a
    # served flag withdrawn once, and a whole verb never, so the ranking is not the detour the
    # single door assumed. It could not have been offered before RK1335, which is what taught
    # `--tools` to carry this ceiling rather than only the per-tool one.
    "budget.session": _reads(
        (
            ("cost", "--tools"),
            "the whole served surface is past what `[tools] session` allows and no single "
            "tool is; this ranks every description against that ceiling and prints the room "
            "each has, which is what picking one to cut needs",
        ),
        (
            ("cost", "--session"),
            "and this prices the surface beside what the resident files cost each turn, "
            "which is what decides whether it is the surface to cut at all; what closes it "
            "is descriptions shortened or a ceiling re-argued in `roadkeep.toml`",
        ),
    ),
    # `{id}` is the tool, which this finding carries as its subject (RK1236). The ranking over
    # every tool answers *which one is over* and the finding already said that; what the reader
    # needs next is which of this tool's fields spent the bytes, and the file it is written in.
    "budget.tool": _read(
        ("cost", "--tools", "{id}"),
        "one served tool is past what `[tools] characters` allows; this ranks that tool's "
        "own fields and names the module each is written in",
    ),
    # `--readme` is the row and the *target's* flag is what `_varied` swaps in (RK1110). With a
    # third projection the literal became a remedy contradicting the message above it — the
    # finding named `export --contents` and the door under it said `--readme` — which is the
    # worse half of the two, being the one a reader trusts. Varied rather than templated,
    # because `{id}` means a task id everywhere else and a row spelling `--{id}` renders
    # `export --RK1` under the sweep that holds every door runnable.
    "export.stale": _Rule(
        "run",
        (
            (
                ("export", "--readme"),
                "every character between the markers is derived, so it is rewritten and "
                "never edited",
            ),
        ),
        varies="target",
    ),
    "export.unmarked": _run(
        ("export", "--readme"),
        "the target carries no roadkeep markers, so nothing there is governed yet",
    ),
    # A `run` and not a `read`, which is the whole point of putting this at the gate (RK1192):
    # `install --check` reported it and nobody ran that, so the finding names the command that
    # closes it and `repair` closes it. The plain verb, because the surfaces are written
    # together or not at all and the variant is read off the disk rather than off a flag.
    "install.stale": _run(
        ("install",),
        "the wired launcher, hook and skill are rewritten from the checkout answering here; "
        "`[install] pinned` in roadkeep.toml is how a project that chose this version says so",
    ),
    # A `compose` and not a `fix` (RK1222): what the pattern under that directory should be is
    # the author's — which files a migration is about is the claim the query makes, and `**/*`
    # is this tool guessing at it. The suffix is the part only they know.
    "remaining.unmatched": _compose(
        ("section", "amend", "{id}", "--body", "-"),
        "the clause names a directory where `Path.glob` wants a pattern, so it reads no file "
        "at all; `<that path>/**/*` is the shape, and which files it should reach is yours",
    ),
    # A `decide` and not a `run` (RK1228): whether the work this change carries *is* the task
    # is the one judgement nothing here can make — a path a section names changes for a
    # rename, a neighbouring fix, a refactor that crossed it. So the two readings are named
    # and the caller picks, which is why this is a note and not a finding in the first place.
    "task.worked": _decide(
        "source under this open task moved and the line did not, which is either the work "
        "landing or a path it merely names changing:",
        (("ship", "{id}", "--why", BLANK), "this is what landed, and the entry is owed"),
        (("show", "{id}"), "read what the section claims before deciding it was that"),
    ),
    # The same judgement one level up (RK1234), so the same shape — but the first reading is
    # no longer `ship` on a line: a whole block whose every line moved is either work that
    # landed under all of them, or one commit that crossed the area they all name.
    "block.worked": _decide(
        "source under every open line of this block moved and none of them shipped, which is "
        "either a block finished and not closed or one change crossing what they all name:",
        (("list", "--block", "{id}"), "read the lines this is about before shipping any"),
        (("unclosed",), "which of them commits already name, which is the other half"),
    ),
    # RK1238. `engines` and not `/plugin update`: which copy is right is a decision about a
    # setup this tool can read and never make, and the one command that names all three is
    # the whole of what a reader needs before taking it.
    "gate.behind": _read(
        ("engines",),
        "the copy that judged this tree is older than the one `[install] pinned` names, so "
        "a clean verdict here is that copy's; this reads all three and says which answered",
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
    "region": "with whether the label's later region holds anything",
    "nested": "with whether an open line claims a section nested under this one",
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

    def payload(self, served: str = "") -> dict[str, object]:
        """The `--json` form, and the one place ``decision`` is **not** published (RK1416).

        :func:`_cause` derives the cause of a non-``fix`` row *from* the decision, so on
        every code that carries one the two keys were byte-identical — which a consumer
        rendering both prints as one sentence under two headings, and a reader takes the
        second for an answer to something the first did not cover. ``cause`` is the key
        every code has, so it is the one that stays; ``kind`` already says the doors are
        alternatives, which is what the second name was carrying.

        Dropped here and not from :meth:`Remedy.payload`, which `repair --json` publishes
        beside no cause at all: there the sentence is the only statement of what to weigh,
        and taking it out would lose it rather than stop repeating it.
        """
        remedy = self.remedy.payload(served)
        del remedy["decision"]
        return {
            "code": self.code,
            "kind": self.kind,
            "cause": self.cause,
            "varies": self.varies or None,
            **remedy,
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


#: Every name a row may write between braces, and the whole of what a door can be told about
#: the finding it closes (RK490). **Declared**, rather than being whatever :func:`_values`
#: happens to compute: `{first}` and `{role}` sat named in this table for years and
#: substituted nowhere, so those doors rendered their own braces — a command line no shell
#: repairs (RK435) — and nothing anywhere could say so. `tests/test_remedying.py` holds both
#: directions: every `{name}` the source writes is one of these, and every one of these is a
#: key :func:`_values` answers.
FIELDS = ("id", "line", "label", "file", "role")


def _values(finding: object, config: Config | None) -> dict[str, str]:
    """What this finding tells a door about itself, by the names a row uses (RK490).

    The one place any of them is derived. Three rows' worth of defects — RK468, RK470, RK472
    — were each a row repeating what the finding already knew instead of reading it, and each
    was found by example because there was nowhere for the agreement to be checked. Computed
    here, per finding and once, the table states only what is genuinely per-code and the
    agreement is a property over the whole of it.

    Read by ``getattr`` on purpose: this takes a :class:`~roadkeep.linting.Finding`, a
    :class:`~roadkeep.linting.Note`, a :class:`~roadkeep.kernel.schema.Violation` wrapped in one, or
    the :class:`_Class` an explanation is composed from — the caller repairing a line does
    not care which of the four reported it, and neither does a door.

    ``id`` is the finding's **own** :attr:`~roadkeep.linting.Finding.token`, which already
    means *what a remedy substitutes*: the explicit subject, or the id it usually is. Reading
    it here rather than recomposing the `subject or id` fallback is the smallest instance of
    this task's whole rule, and it is the one that was written twice.
    """
    lineno = getattr(finding, "lineno", None)
    subject = getattr(finding, "token", "") or getattr(finding, "subject", "") or getattr(
        finding, "id", ""
    )
    return {
        "id": subject,
        "line": "" if lineno is None else str(lineno),
        "label": _label(subject, config),
        "file": getattr(finding, "file", ""),
        # Which governed file this finding is about, which is a fact the *report* already
        # printed and a door had to be told separately until RK470 derived it by hand.
        "role": "" if config is None else _role_of(finding, config),
    }


def remedy(finding: object, config: Config | None = None) -> Remedy | None:
    """What closes ``finding``. ``None`` only for a code the table does not carry.

    Takes anything with ``code``, ``id``, ``lineno`` and ``file`` — a
    :class:`~roadkeep.linting.Finding`, a :class:`~roadkeep.linting.Note`, or a
    :class:`~roadkeep.kernel.schema.Violation` wrapped in one — because the caller repairing a
    line does not care which of the three reported it.
    """
    code = getattr(finding, "code", "")
    rule = _TABLE.get(code)
    if rule is None:
        return None
    values = _values(finding, config)
    if rule.varies and config is not None:
        rule = _varied(code, rule, finding, values, config)
    doors = tuple(
        Door(_scoped(_substitute(argv, values), values, config), what, foreign=rule.foreign)
        for argv, what in rule.doors
    )
    return Remedy(code, rule.kind, doors, rule.decision, rule.sequence)


def _varied(
    code: str, rule: _Rule, finding: object, values: Mapping[str, str], config: Config
) -> _Rule:
    """The two rows a project's own configuration decides (L6)."""
    if code == "ref.mismatch" and config.schema.ref_scheme != "id":
        # An outline anchor is not derivable, so there is nothing mechanical to recompute:
        # the field is the author's and the fixer would be guessing an address.
        return _compose(
            ("amend", "{id}", "--ref", BLANK),
            "the anchor is not derived under this project's scheme, so it is yours to state",
        )
    if code == "section.duplicate" and config.schema.ref_scheme == "id":
        # Under an id scheme both headings claim one line's address, and no verb re-addresses
        # one of them: `section move` refuses an id-addressed section outright and
        # `anchors --next` has no numbering to derive from. The two doors that are real are
        # the ones `section move`'s own refusal names, and choosing between them is reading
        # which heading is the stray — so a decision and not a command (RK1337).
        return _decide(
            "two headings claim one line's address and nothing derives a free one here: "
            "either the later design belongs to a line of its own, or it is a copy",
            (
                ("renumber", "{id}", "--to", BLANK),
                "the line, its heading, its subtree and every dep move together, which is "
                "what re-addressing an id-addressed design means",
            ),
            (
                ("section", "drop", "{id}"),
                "or take the copy out — refused while a line still points at it, so the "
                "pointer is repointed or that line ships first",
            ),
        )
    if rule.varies == "queue" and _queue_in_config(config):
        # The order lives where no verb writes, so the mechanical pass cannot reach it and
        # the honest remedy is the one door between the two declarations.
        return _TABLE["priority.unmigrated"]
    if rule.varies == "target":
        # Which projection went stale, read off the finding's own subject (RK1110). The domain
        # is `DEFAULTS`' keys, so a fourth target is covered by arithmetic rather than by
        # somebody remembering — and a subject that is not one of them keeps the row, which is
        # what `explain` gets, having no finding to ask.
        from roadkeep.exporting import DEFAULTS  # noqa: PLC0415 - RK260's edge back

        flag = values.get("id", "")
        if flag in DEFAULTS:
            argv, what = rule.doors[0]
            return _Rule("run", (((*argv[:-1], f"--{flag}"), what),))
        return rule
    if rule.varies == "nested":
        blockers = _claimed_below(finding, config)
        if blockers:
            # Not a door this tool can open: the drop is right and cannot happen until the
            # nested design moves or the line claiming it ships, and neither is a mechanical
            # write. Naming an edit that cannot work is worse than naming none (RK16), so
            # what is named is the blocker and the two ways it goes.
            named = ", ".join(f"§{anchor} ({', '.join(who)})" for anchor, who in blockers)
            return _decide(
                f"the drop is blocked: {named} nests under this one and an open line points "
                f"there, so it goes when that design moves or that task ships:",
                (("show", "{id}"), "read what still claims the prose under this section"),
                (("section", "move", BLANK), "move the nested design out, then drop this one"),
            )
        return rule
    if rule.varies == "region":
        loose = _loose_below(finding, config)
        if loose:
            # `block merge` refuses while the later heading stands over a note, and `--prose`
            # is what drops it — a decision RK237 put at the door on purpose, because the
            # note is somebody's prose and this tool does not delete prose to close a finding
            # (L4). Found by RK473's own sweep on Shio's pinned ledger, where two merges were
            # dispatched and refused on every run.
            where = ", ".join(f"line {one}" for one in loose)
            return _decide(
                f"the fold is blocked: the later heading stands over a note ({where}), which "
                f"the merge would take with it:",
                (("block", "merge", "{id}", "--prose"), "fold, dropping that note with it"),
                (("show", "{id}"), "read the note first — moving it is the other answer"),
            )
    if rule.varies == "region" and _empty_region(finding, config):
        # The verb the finding's own sentence names on this branch (RK425): a region holding
        # nothing is removed rather than folded, and `block drop` is what removes it.
        return _run(
            ("block", "drop", "{id}"),
            "the later heading stands over nothing, so it is taken out rather than folded",
        )
    if code == "id.duplicate" and values["role"] == "roadmap":
        # `record renumber` opens the ledger and this is the other file: two *open* lines
        # sharing an id are two tasks, and one of them takes a free address.
        return _decide(
            "two open lines carry one id, which is two tasks sharing an address:",
            (("renumber", "{id}"), "move the later line, with its section and its dependents"),
            (("show", "{id}"), "read both first — they may be one line written twice"),
        )
    return rule


def _queue_in_config(config: Config) -> bool:
    """Whether this project's order is still `roadkeep.toml`'s (RK427).

    Asked of :func:`~roadkeep.queueing.declared`, which is the one reader that can see both
    declarations — a second rule here about which file wins is the disagreement RK427 is.
    """
    from .queueing import declared  # noqa: PLC0415 - one branch, and never on a clean run

    return declared(config).declared_in == "config"


def _loose_below(finding: object, config: Config) -> tuple[int, ...]:
    """The lines of prose the later heading stands over, which the fold would take (RK473).

    Asked of `blocking._held`, which is the reader `block merge` refuses from, so the remedy
    and the verb answer one question. Empty where the fold would run.
    """
    from .blocking import _held  # noqa: PLC0415 - one branch, never on a clean run

    label = getattr(finding, "subject", "") or getattr(finding, "id", "")
    where, lineno = getattr(finding, "file", ""), getattr(finding, "lineno", None)
    if not label or not where or lineno is None:
        return ()
    document = next(
        (
            config.document(role)
            for role in ROLES
            if config.has(role) and config.relative(config.path(role)) == where
        ),
        None,
    )
    if document is None:
        return ()
    later = next((one for one in document.headings if one.lineno == lineno), None)
    return () if later is None else _held(document, later).prose


def _empty_region(finding: object, config: Config) -> bool:
    """Whether `block drop` would remove this label's heading rather than refuse (RK468).

    Asked of `linting.closes_by_drop`, which is the reader the finding's own sentence uses,
    so the message and the remedy answer one question rather than two that agree until they
    do not. Imported inside the branch for :func:`_queue_in_config`'s reason: this module is
    on the report's own import path and the question is asked on one code out of seventy.

    Two things off the finding and not one. The subject is the **label** — every other row
    here is keyed by a task id, and this is the one whose id is a heading — and the line is
    which repeat it is about, because `block drop` closes this finding only where *this*
    region is the empty one and not merely where the verb would run somewhere.
    """
    from .linting import closes_by_drop  # noqa: PLC0415 - one branch, never on a clean run

    label = getattr(finding, "subject", "") or getattr(finding, "id", "")
    where, lineno = getattr(finding, "file", ""), getattr(finding, "lineno", None)
    if not label or not where or lineno is None:
        return False
    files = {
        role: config.document(role)
        for role in ROLES
        if config.has(role) and config.path(role).is_file()
    }
    document = next(
        (one for role, one in files.items() if config.relative(config.path(role)) == where),
        None,
    )
    if document is None:
        return False
    later = next((one for one in document.headings if one.lineno == lineno), None)
    return later is not None and closes_by_drop(document, later, files, label)


def _claimed_below(finding: object, config: Config) -> tuple[tuple[str, tuple[str, ...]], ...]:
    """The sections nested under this one that an open line still points at (RK472).

    The same question `section drop` refuses on, asked of the readers it uses — `pointers`
    for the claims and `nested` for the containment — so the remedy and the verb answer one
    thing rather than two that agree until they do not. Empty where the drop would run.

    Imported inside the branch for :func:`_queue_in_config`'s reason, and asked on one code.
    """
    from .sections import find, nested, pointers  # noqa: PLC0415 - one branch

    anchor = getattr(finding, "subject", "") or getattr(finding, "id", "")
    role = _role_of(finding, config)
    if not anchor or role not in PROSE_ROLES or not config.has(role):
        return ()
    document = config.document(role)
    if find(document, anchor) is None:
        return ()
    claimed = pointers(config)
    return tuple(
        (child.anchor, claimed[child.anchor])
        for child in nested(document, anchor)
        if child.anchor in claimed
    )


def _scoped(
    argv: tuple[str, ...], values: Mapping[str, str], config: Config | None
) -> tuple[str, ...]:
    """Name which prose file a `section` verb is about, where the project has two (RK470).

    RK420 promises a complete argv, and on a project declaring one prose file it was: every
    `section` verb defaults to that file. On one declaring two it was not. Measured by
    running `repair` over a copy of Turing:

        docs/STRATEGY.md:683  section.stale  XIV.2 …
        FAILED  section drop XIV.2
        roadkeep: no §XIV.2 section in docs/IMPROVEMENTS.md

    The finding names one file and the remedy opened the other. `--role` is a flag all four
    verbs already take, and the finding already says which file it is about — so nothing new
    is read, and the completion is derived here rather than written into five rows that would
    each carry a word most projects do not need.

    **Only where the project declares more than one**, which is the question §RK470 left open:
    on a single-file project the flag names the default and is a word that changes nothing,
    and these argvs are read by people as well as run by `repair`.
    """
    if config is None or argv[:1] != ("section",) or "--role" in argv:
        return argv
    declared = [role for role in PROSE_ROLES if config.has(role)]
    role = values["role"]
    if len(declared) < 2 or role not in declared:
        return argv
    return (*argv, "--role", role)


def _role_of(finding: object, config: Config) -> str:
    """Which governed file this finding is about, by the path the report printed."""
    where = getattr(finding, "file", "")
    for role in ROLES:
        if config.has(role) and config.relative(config.path(role)) == where:
            return role
    return ""


def _label(subject: str, config: Config | None) -> str:
    """The block label inside a queue token, for the door that takes one (RK435).

    Two spellings of one thing, and mixing them is not cosmetic: the queue holds `Block D`
    and `priority drop` takes exactly that, while `--block` takes `D` and answers `Block D`
    by looking for a heading named `Block Block D` — exit 2, on the remedy RK420 added so a
    caller would not have to compose one.

    Asked of :meth:`~roadkeep.kernel.schema.Schema.block_of_dep`, which is where a token's label is
    read everywhere else, including at the emission site this row answers. A second reader
    of that spelling would be the drift this package exists to stop, and it would be the one
    that has to remember `heading_word` is per project (L6).

    Empty where there is nothing to ask — a token naming no block, or a `remedy` called with
    no config, which `explain` is — and the blank then renders for :func:`_substitute`'s own
    reason: the field is unknown to *this call* rather than withheld from the author, and
    `add --block …` says which word is missing where `add --block None` does not.
    """
    return "" if config is None else (config.schema.block_of_dep(Dep(subject)) or "")


def _substitute(argv: Sequence[str], values: Mapping[str, str]) -> tuple[str, ...]:
    """Fill a template from :func:`_values`. A field with no value keeps its blank.

    That fallback is the module's own rule applied to itself: an argv reading ``--line None``
    is worse than one reading ``--line …``, because the first looks runnable and the second
    says which word is missing.

    The domain is :data:`FIELDS` and this reads it whole, so a row naming a fifth field is a
    row this fills rather than one that renders its own braces (RK490) — and the suite holds
    the other end, that no row names something :func:`_values` does not answer.
    """
    out: list[str] = []
    for word in argv:
        for name, value in values.items():
            token = "{" + name + "}"
            if token in word:
                word = word.replace(token, value or BLANK)
        out.append(word)
    return tuple(out)
