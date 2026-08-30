"""The vocabulary a verb declares itself in (RK1171).

`cli.py` held these beside `build_parser`, which was fine for as long as every parser lived
there too. It cannot stay: a verb's parser belongs with its handler, `cli` already imports
those handlers, and a `verbs/` module reaching back for `withheld` would close the cycle —
so the words a declaration is made of move to where both ends can say them.

Nothing here decides anything. Each function writes one fact onto a parser and something
else reads it back: :func:`~roadkeep.cli.dispatch` takes the write lock off `writes_when`,
:func:`roadkeep.serving.withheld` composes a refusal off the reasons, and `_one_answer`
refuses two subjects off what :func:`answers` declared. That is the whole shape RK1171 is
about — one declaration, and three surfaces interpreting it.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import NoReturn

from roadkeep.verbs.refusing import EXIT_USAGE

#: Appended to every prose argument that reads the pipe (RK329), so the convention is one
#: sentence in nine help strings rather than nine sentences that drift.
_PIPE = "; '-' reads stdin, which is how an apostrophe or a backtick survives a shell"
#: Every spelling a prose argument gives that clause, longest first (RK1260). Held here
#: because the surface that has to **unsay** it is not the one that wrote it: over MCP there
#: is no stdin and no shell, so this sentence described a channel the caller loading it cannot
#: use — token per tool per session, spent on advice addressed to somebody else. Matching a
#: sentence written four ways in three modules is what a list replaces, and
#: `tests/test_serving.py` holds it against the declarations rather than against these bytes:
#: a prose argument whose help stops carrying exactly one of these is red here, not silently
#: unrewritten there.
PIPE_CLAUSES = (
    "; '-' reads stdin, and stdin is the default unless --title is the only thing being changed",
    "; omitted or '-' reads stdin, which is how a paragraph gets in",
    "; omitted or '-' reads stdin",
    _PIPE,
)
#: And nothing stands in its place, which is the second half of the same argument. A clause
#: saying *there is no pipe here* describes an absence to a caller who was never going to
#: reach for one — and it would be paid per tool per session, which is the cost this removes.
#: What the field is instead, the schema already says: `"type": "string"`. A caller that sends
#: `-` anyway, copying a CLI example, is answered by `serving._companioned`, which names the
#: argument — a refusal at the one moment it is about something, rather than a sentence in
#: every session that connects.
SERVED_PIPE = ""
#: Appended to every prose argument that also answers to a path (RK381), so the convention is
#: one sentence in three help strings rather than three that drift. What it buys is the
#: **retry**: a refusal on a short field re-reads the file and costs that field alone.
#:
#: Said without naming the pipe, because the sentence is now published on both surfaces
#: (RK1260): a pipe not rewinding is why the terminal retry is expensive and re-sending the
#: payload is why the served one is, so the *cost* is the fact both callers share and the
#: channel is the half only one of them has. One sentence, and no substitution to keep in step.
_BODY_FILE = (
    "read the {what} from this file instead — a refusal on a short field then costs the "
    "corrected field alone and never the paragraph again"
)
#: One sentence, on both `pick` and `brief`, because it is one flag (RK83): a caller asking
#: to execute a block wants work whose design is written, and the markers already say which.
_DESIGNED_HELP = (
    "offer only work whose design is written, setting aside the markers "
    "`[markers] undesigned` names (only without an id)"
)
#: One sentence, on both `pick` and `brief`, for `_DESIGNED_HELP`'s reason — and repeatable
#: because a caller has a set and not a switch (RK1297). What it does not say is "declare what
#: you have": the default is nothing, and the flag is the exception a person at the desk types.
_HAVE_HELP = (
    "declare a requirement this caller has, repeatable: a ready line whose `(needs: …)` "
    "names anything undeclared is set aside and named, never offered (only without an id)"
)
#: The same flag on `stats`, where the axis is **counted** rather than chosen from (RK1432).
#: Its own sentence and not `_HAVE_HELP`: that one's "never offered" and "(only without an
#: id)" are facts about a verb that picks a line, and this verb picks none — one sentence
#: covering both would have to drop the half each caller reads it for.
_HAVE_COUNTING_HELP = (
    "declare a requirement this caller has, repeatable: an open line naming anything "
    "undeclared counts as waiting rather than as startable"
)
#: Top-level options that take a value, so the token after one is not the verb. Two, because
#: `--version` is an action and every other flag belongs to a subcommand that was never reached.
_VALUED = ("-C", "--directory")
#: How close a rejected flag has to be before it is named as a typo of a real one. High,
#: because the failure this replaced was advice nobody could act on: at `difflib`'s own 0.6
#: default, `--note` is offered `--lines`, which is a worse answer than the list — a caller
#: who wanted `--why` is now weighing a flag that has nothing to do with what they meant.
#: `--seciton` for `--section` is the case worth catching, and it scores far above this.
_A_TYPO = 0.8

#: What every `--json` flag this CLI declares says it is for.
_JSON_HELP = "machine-readable form"


class _Verb(argparse.ArgumentParser):
    """A subcommand whose missing-argument refusal can name its near-twin (RK339).

    Two pairs in a list of forty-one differ by one edit *and* differ in whether they need a
    positional: `status <id> <marker>` writes and `stats` reports, `claim <id>` writes and
    `claims` reports. In both, the mutator is the one carrying the name every other tool
    spends on a read-only summary — `git status`, `systemctl status` — so the verb typed
    wanting a report is the verb that takes arguments, and what comes back is `error: the
    following arguments are required`.

    Nothing is written and nothing is at risk: the required positionals are what make it fail
    safe, and the twin needs none, so the mistake the other way is a harmless report. The cost
    is the confusion and the round trip, and it recurs for as long as the names do.

    **A rename is the wrong fix**, worth saying because it is the first idea. Other projects
    have adopted this tool, these verbs are in their skills and their hooks, and breaking one
    to improve a name spends their turn to save this one. So the fix is the refusal, which is
    already the only thing a caller sees when they get this wrong — one message, no schema
    change, landing exactly where the mistake is made.

    Keyed on a `twin` default rather than a table here, for :class:`~roadkeep.serving.Prose`'s
    reason (RK171): it is a claim about one command, so its own parser is where it belongs and
    a third pair declares itself instead of being found by the session that meets it. Which
    verbs owe one is read off these parsers rather than remembered (RK350) —
    `test_every_verb_that_shadows_a_report_declares_the_sentence` is the survey RK339 ran once
    by hand, so a verb added tomorrow is measured by a test and not by whoever types it wrong.

    That the sentence is *delivered* is a second property over the same list (RK362), because
    the condition below is a substring of what argparse composes, in argparse's English: a
    Python release wording it differently would turn every twin off at once and leave a suite
    of tests asserting the defaults are still declared.
    """

    def __init__(self, *args: object, **kwargs: object) -> None:
        # Declared here and not on forty `add_parser` calls (RK1032): argparse resolves any
        # unambiguous prefix by default, so `lint --f` **wrote files** — and the four flags
        # it handed over that way are exactly the ones this CLI declares as `writes_when`,
        # which is to say the ones `dispatch` takes the write lock for. A miss is the refusal
        # RK1026 composes; a hit was a write nobody typed, reported as a success.
        #
        # What this removes is an affordance nobody documented: no help string, no sentence
        # of the shipped skill and no message in this tree spells a flag short.
        kwargs.setdefault("allow_abbrev", False)
        super().__init__(*args, **kwargs)  # type: ignore[arg-type]

    def error(self, message: str) -> NoReturn:
        twin = self.get_default("twin")
        if twin is None or "required" not in message:
            super().error(message)
        self.exit(EXIT_USAGE, f"roadkeep: {twin}\n")


def _reason_flag(parser: argparse.ArgumentParser, help_text: str) -> None:
    """The prose field on the two verbs that call it `--reason`, under `--why` too (RK1038).

    RK399's repair, one field over. Nine verbs spell this `--why` — `add`, `amend`, `ship`,
    `restate`, `origin`, `report` and both the `record` and `non-goal` pairs — and `defer`
    and `retire` spell it `--reason`, which are the two doors a caller reaches least often
    and so the two names they are least likely to have kept. Because the field is *required*,
    a caller who typed `--why` got `error: the following arguments are required: --reason`:
    argparse naming what is missing and never what was typed, so the correction is a guess.

    Both accepted and neither removed, for the reason RK399 gives about `--status`: other
    projects have adopted this tool, these verbs are in their skills and their hooks, and a
    rename that breaks them to win a synonym is a cost paid by everyone to fix nobody's
    defect. `--reason` stays first, so it is what the usage line and the shipped skill spell
    and what :class:`~roadkeep.serving.Prose` keeps naming; `dest` does not move.
    """
    parser.add_argument("--reason", "--why", dest="reason", required=True, help=help_text)


def _marker_flag(
    parser: argparse.ArgumentParser, help_text: str, *, dest: str = "status"
) -> None:
    """The open marker, under both names four verbs had spelled it (RK399).

    `add --status` and `resume --marker` write the same field, read from the same
    `[markers] open` list, and disagreed about what it is called — so a caller who learned
    the name on one verb got `unrecognized arguments` from the other, which is argparse
    saying the field does not exist rather than that this verb calls it something else.

    The skill says *marker* throughout, `roadkeep.toml` says `[markers]`, and `status <id>`
    is a verb rather than a flag because moving one is an act. So `--marker` is the name and
    `--status` is kept accepted rather than removed: every adopting project's scripts, hooks
    and half-remembered invocations spell it, and a rename that breaks them to win a synonym
    is a cost paid by everyone to fix nobody's defect.

    ``dest`` stays whatever each verb already handed its handler. Which of the two argparse
    treats as canonical is decided by option order alone, so this takes the destination
    explicitly instead: a helper that silently renamed a field on two of four verbs would be
    the same defect, arriving through its own repair.
    """
    names = ("--marker", "--status") if dest == "marker" else ("--status", "--marker")
    parser.add_argument(*names, dest=dest, help=help_text)


def _counting_flags(parser: argparse.ArgumentParser) -> None:
    """The three flags every counting command shares (RK10), declared once."""
    parser.add_argument("--block", help="only this block, e.g. C")
    parser.add_argument(
        "--role", default="roadmap", help="which governed file (default: roadmap)"
    )
    parser.add_argument("--json", action="store_true", help=_JSON_HELP)


def json_needs(source: argparse.Namespace | argparse.ArgumentParser) -> str:
    """The argument this command's `--json` is the form *of*, or `""` where it is the command's.

    Declared beside :func:`writes_when` and read the same way, because it is the same kind of
    claim: a fact about the command that a surface serving it has to know (RK167). One command
    makes it — `merge`, where `--json` is the form of `--check` and the driver's own answer is an
    exit code and the bytes git reads out of `%A` (RK317).

    It has to be **declared** rather than left as an `if` in the handler (RK319), because
    :func:`~roadkeep.serving.argv` ends every tool's command line with `--json` and never exposes
    it: so a command with a branch that refuses the flag is servable only through a tool whose
    `always` carries the argument named here, and nothing said so. Held by a test over the two
    halves (`tests/test_serving.py`), which is this project's answer to a declaration that can
    stop matching — the alternative being a served tool refusing every call it receives, over a
    flag the caller never passed and cannot remove.
    """
    declared = (
        source.get_default("json_needs")
        if isinstance(source, argparse.ArgumentParser)
        else getattr(source, "json_needs", "")
    )
    return declared or ""


def withheld(parser: argparse.ArgumentParser, **reasons: str) -> None:
    """Say why this verb's tool surface does not offer these arguments (RK1169).

    A fact about an argument, declared where the argument is. `serving.WITHHELD` was a table of
    the same rows keyed by verb, held true against these parsers by a test asserting the two
    agreed — which is the shape this task is about: not a defect waiting to happen, but a test
    written to prove that two places say one thing.

    Merged rather than replaced, so a verb may declare its reasons beside the flags they are
    about instead of in one call at the end — the point being that the sentence sits next to
    what it explains.
    """
    parser.set_defaults(withheld={**(parser.get_default("withheld") or {}), **reasons})


def writes_when(source: argparse.Namespace | argparse.ArgumentParser) -> tuple[str, ...]:
    """The argument(s) that turn a declared read into a write, however it declared them.

    A bare string is one of them, which is what every other parser passes and what this keeps
    accepting: the plural is the general shape and not a migration (RK307).
    """
    declared = (
        source.get_default("writes_when")
        if isinstance(source, argparse.ArgumentParser)
        else getattr(source, "writes_when", "")
    )
    if not declared:
        return ()
    return (declared,) if isinstance(declared, str) else tuple(declared)


@dataclass(frozen=True, slots=True)
class Answer:
    """One question a verb can be asked, as its own parser declares it (RK489).

    A **group** of flags rather than one, because two of them can be one question: `export
    --readme --site` writes the same projection to two destinations and composes, which is
    what RK39 asked for, while either of them beside `--json` is two answers. One flag is the
    ordinary case and reads as a group of one.
    """

    #: `(dest, option string, the parser's own default)` per flag, resolved at declaration
    #: time so nothing here has to derive an option from a dest or a dest from an option.
    flags: tuple[tuple[str, str, object], ...]
    #: What this question answers, as a **noun phrase**: it is rendered inside `<what>
    #: (--flag)`, so a verb here would have to agree with a list whose length is the caller's.
    what: str

    def given(self, args: argparse.Namespace) -> tuple[str, ...]:
        """The option strings of this group the caller actually passed."""
        return tuple(
            option
            for dest, option, default in self.flags
            if getattr(args, dest, default) != default
        )

    def holds(self, dest: str) -> bool:
        return any(one == dest for one, _, _ in self.flags)

    def asked(self, args: argparse.Namespace) -> str:
        return f"{self.what} ({', '.join(self.given(args))})"


def _declared(parser: argparse.ArgumentParser, dest: str) -> tuple[str, str, object]:
    """One argument this parser declares, or a `KeyError` naming the verb (RK489).

    Raised at **build time**, which is the whole point: a declaration naming a flag the
    subparser does not have is a mistake that fails when the parser is constructed — before
    any argv reaches it — rather than a refusal that silently never fires. That is the same
    trade `writes_when` makes one function up, and the reason this takes dests: an option
    string is spelled per flag and a dest is what every other declaration here is keyed by.
    """
    for action in parser._actions:  # noqa: SLF001 - argparse exposes no public reader
        if action.dest == dest and action.option_strings:
            return dest, action.option_strings[0], action.default
    raise KeyError(f"{parser.prog} declares no --{dest.replace('_', '-')}")


def answers(parser: argparse.ArgumentParser, *groups: tuple[str | tuple[str, ...], str]) -> None:
    """Declare which of a verb's flags are **answers**, so two of them are refused (RK489).

    `budget` wrote this by hand for its four subjects — a list of flags, a refusal when two
    arrive, and a check of each narrowing flag against the one that answered — and it was
    twenty-five lines for one verb out of eighty. Every other multi-subject verb either
    repeated the shape or did not have it: RK465 found `--role` swallowed beside three
    subjects, RK466 found two commands taking two answers and printing one, and RK467 added a
    sweep that finds the next one *after* it has been written.

    Declared here, :func:`_one_answer` enforces it for every verb before the handler runs, on
    both surfaces, because `dispatch` is the door the MCP server comes through too. Which is
    this tool's own thesis turned on itself: the saving is the analysis, not the characters —
    a sweep reports after a flag nothing reads has been added, and a declaration refuses
    before a subparser exists that can swallow one.
    """
    parser.set_defaults(
        subjects=tuple(
            Answer(
                tuple(
                    _declared(parser, one)
                    for one in ((dests,) if isinstance(dests, str) else dests)
                ),
                what,
            )
            for dests, what in groups
        )
    )


def narrows(parser: argparse.ArgumentParser, flag: str, subject: str) -> None:
    """Declare that ``flag`` shapes ``subject`` and may not arrive without it (RK489).

    Checked against the subject that **answered** and not against the absence of one, which
    is RK465's finding: the refusal `budget` wrote sat after every dispatch, so it fired only
    where nothing else had, and `--role` beside `--file` changed nothing and said nothing. A
    caller reading a number it believes it narrowed is worse off than one refused.
    """
    declared = parser.get_default("narrowing") or ()
    parser.set_defaults(
        narrowing=(*declared, (_declared(parser, flag), _declared(parser, subject)))
    )
