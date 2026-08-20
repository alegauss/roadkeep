"""The questions this project has written down, as the one set L5 quantifies over (RK1021).

L5 says *query instead of read*: every question a maintainer asks a governed file is a
command, so answering costs no context. The register recorded it as **stated and unheld**,
and said why — a property over "the questions somebody asks" has nothing to sweep until
those questions are written down, which is a task and not a test. This is that inventory.

What existed before was the converse. RK167 holds that every command the MCP surface
publishes is one the CLI parses; nothing held that a question somebody has is answered by
one. A tool can publish forty verbs and still send its reader to an editor for the one
thing they wanted, and no test here would have noticed.

**The bound is honest and that is what makes it checkable**: not every conceivable
question, but every question this project has written down — which is the same bound
`test_invariants` already accepts about the six laws, stated rather than pretended away.
A question nobody has written is not a hole in the property; a verb that answers one and
appears nowhere in the skill *is*, and so is a question whose command writes.

Two halves, and neither works alone. :data:`QUESTIONS` says what is asked and which argv
answers it — the join to the parser that the half-written inventory in
`skills/roadkeep/SKILL.md` never had. :data:`ANSWERS_NO_QUESTION` says which read-only
verbs answer none and why, because a verb quietly left out of the first table is how an
inventory stops covering a surface while still looking total.

Addressed as `asking.QUESTIONS` from L5's row, which is what `test_invariants` reads back
against the holder: a property that stopped naming this set is one whose row describes a
rule it no longer sweeps.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from roadkeep.cli import build_parser


@dataclass(frozen=True, slots=True)
class Question:
    """One question this project has written down, and the argv that answers it."""

    #: In a maintainer's words rather than the verb's — the whole point is that the two are
    #: not the same string. A row whose question is its command spelled as a sentence proves
    #: nothing: it asserts the surface against itself.
    asked: str
    #: The argv, complete enough to parse. Positionals are placeholders and are never run:
    #: what is held is that the question **has** a command and that the command only reads,
    #: which is decidable from the parser and needs no repository to point at.
    answered_by: tuple[str, ...]


#: Every question this project has written down about a governed file, and the command that
#: answers it. One row per read-only verb that answers one: a verb answering two questions
#: would be two rows, and a question with no command is the state this whole file exists to
#: make visible.
QUESTIONS: tuple[Question, ...] = (
    Question("what should I work on next", ("pick",)),
    Question("what do I need to know before starting this task", ("brief", "RK1")),
    Question("what is this task, across the files that hold a piece of it", ("show", "RK1")),
    Question("what is this task waiting on, and what waits on it", ("deps", "RK1")),
    Question("which lines carry this marker", ("list",)),
    Question("how much is in this file", ("stats",)),
    Question("which marker lines did the grammar fail to read", ("audit",)),
    Question("does this backlog still conform to its own rules", ("lint",)),
    Question("what does this finding's code mean, as a class rather than a line", ("explain", "line.too-long")),
    Question("how much room does this line's prose have before I write a word", ("budget", "--block", "A")),
    Question("what did a comparable task cost, so this is one line or two", ("weight",)),
    Question("how much of this migration is left", ("remaining", "RK1")),
    Question("what would show me this task is finished", ("evidence", "RK1")),
    Question("has this work already shipped under another id", ("delivered", "A")),
    Question("which shipped entries were later undone", ("reversals",)),
    Question("what has this project decided not to do", ("non-goal", "list")),
    Question("what would finish this block", ("criterion", "list")),
    Question("what are the blocks called, so I know where this task goes", ("block", "list")),
    Question("in what order does this project want its open work", ("priority", "list")),
    Question("what id does the next task take", ("next-id",)),
    Question("which id below the highest does no line carry, and where did it go", ("gaps",)),
    Question("which commit wrote this task, and which one took it", ("origin", "RK1")),
    Question(
        "which of my open lines did somebody already write the code for",
        ("unclosed",),
    ),
    Question("which rationale addresses are spent, and what is the next free one", ("anchors",)),
    Question("what does this rationale section say, and what does it cost", ("section", "show", "RK1")),
    Question("who is holding a line right now", ("claims",)),
    Question("which paths does this task own, and does the tree still agree", ("claim", "RK1")),
    Question("which governed files did a verb write, and which did something else", ("writes",)),
    Question("do the three copies of this tool agree", ("engines",)),
    Question("what do two branches make of one governed file", ("merge", "base.md", "ours.md", "theirs.md")),
)

#: The read-only verbs that answer no question in the sense above, and why each. Declared
#: rather than filtered out silently: the exemption is where an inventory rots, and a verb
#: added here has to be a sentence somebody wrote instead of a name somebody skipped.
ANSWERS_NO_QUESTION: dict[str, str] = {
    # Two transports. Neither has a maintainer at the other end of it: the caller is a hook
    # runner and an MCP client, and every question they carry is one of the rows above.
    "guard": "a hook payload arrives on stdin and is answered on stdout; nobody types it",
    "mcp": "a protocol, not a question — what it dispatches is this same parser",
    # Two about a defect in *this tool*, which is not a governed file. RK85's capture is a
    # different subject from the backlog, and L5 is a law about the backlog.
    "report": "the subject is a defect in roadkeep, filed as facts a replay re-runs",
    "replay": "the subject is that capture, and the answer is whether it still reproduces",
    # And one whose subject is a file **no project governs yet** (RK1147). L5 is a law about
    # a backlog this tool owns the writes to; `adopt` measures somebody else's file before any
    # of that exists, so the question it answers is asked once and never again.
    "adopt": "the subject is a foreign file, measured before this tool owns any write to it",
}


def verbs() -> dict[str, argparse.ArgumentParser]:
    """Every subcommand this CLI parses, by its full path — `show`, `non-goal list`.

    Derived from the parser and never listed, for the reason `surface.py` gives about the
    package's modules: a second view of the surface agrees with the first right up until
    somebody adds a verb, which is the single moment either of them matters.
    """
    found: dict[str, argparse.ArgumentParser] = {}

    def walk(parser: argparse.ArgumentParser, prefix: tuple[str, ...]) -> None:
        for action in parser._actions:
            if not isinstance(action, argparse._SubParsersAction):
                continue
            for name, sub in action.choices.items():
                found[" ".join((*prefix, name))] = sub
                walk(sub, (*prefix, name))

    walk(build_parser(), ())
    return found


def read_only() -> set[str]:
    """The verbs that declare they only read, which is `reads_only` and nothing else.

    The declaration is the CLI's own — it is what keeps a command out of the write lock
    (RK117) — so reading it here means this inventory and the lock can never disagree about
    which verbs are reads.
    """
    return {name for name, parser in verbs().items() if parser.get_default("reads_only") is True}


def verb_of(question: Question) -> str:
    """Which verb a row's argv reaches, as `verbs()` spells one.

    The longest declared path the argv starts with, so `non-goal list` is one verb and
    `section show RK1` does not read as `section`. Derived from the parser for the same
    reason `read_only` is: a row cannot name a verb this CLI stopped having.
    """
    declared = verbs()
    for width in range(len(question.answered_by), 0, -1):
        path = " ".join(question.answered_by[:width])
        if path in declared:
            return path
    return question.answered_by[0]
