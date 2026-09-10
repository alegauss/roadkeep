"""Every field a caller composes, and what stands between it and a governed file (RK1627).

RK1570 found the block title by being told where to look: `block add J --title "…"` writes a
heading into the roadmap, the ledger and every prose role at once, and nothing validated it —
not even the codec rule. What that task could not have found is the next one, because nothing
enumerated the fields a caller composes, so *which of them has a validator* was a question
answered by remembering.

**The population is the parsers', which is what makes it total.** Every value-taking argument
of a write verb is a string somebody types and this tool does something with, and
`add_argument` is where each one enters. A dest that appears tomorrow has no row and fails
here — which is the property the two registers this is modelled on already have:
`tests/composing.py` enumerates every site that composes a command, `test_backstop.py` every
code a write refuses. Both are totals over a population read from the source, and both caught
something the first time they ran.

**What each row says is the kind**, and the kinds are the decision this file *is*:

* ``schema`` — the value is written into a governed file verbatim, and a validator refuses it
  first. The row names the code family, and :data:`test_backstop.BACKSTOP` is what already
  proves that family is refused at the door and reported by the gate, so *has a validator* is
  answered by a join rather than by a claim here.
* ``round-trip`` — the value is written verbatim and nothing reads the **field**: what refuses
  it is the composed file being parsed back before the bytes land (L3, RK1533/RK1576). Weaker
  on purpose and said out loud, because it is the state RK1570 was about.
* ``address`` — it names *where* the write goes and is resolved rather than written: an id, a
  label, an anchor, a marker, a role. A wrong one is a refusal about a thing that does not
  exist, which is a different question from a field that is malformed.
* ``path`` — a file, resolved against the caller's directory or the project's root, and
  classified per argument by `config.PATH_ARGUMENTS` rather than here.

Keyed by **dest** and not by `(command, dest)`, with :data:`ELSEWHERE` for the few a second
verb means something else by: `why` is a task's sentence on `add` and a non-goal's on `non-goal
add`, and both are prose refused under different codes. A dest reused for the same thing needs
no second row, which is what keeps this a page and not a transcript.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass

from roadkeep.cli import build_parser


@dataclass(frozen=True, slots=True)
class Composed:
    """One argument a write verb takes, and what stands between it and a governed file."""

    #: One of `schema`, `round-trip`, `address`, `path` — the four above.
    kind: str
    #: What it is, in one clause. Read after the dest, so it starts lowercase.
    why: str
    #: The code family a `schema` field is refused under, and empty on every other kind.
    #: Held against `test_backstop.BACKSTOP`, which is where door and gate are already joined.
    codes: tuple[str, ...] = ()


def _schema(why: str, *codes: str) -> Composed:
    return Composed("schema", why, tuple(codes))


def _address(why: str) -> Composed:
    return Composed("address", why)


def _path(why: str) -> Composed:
    return Composed("path", why)


#: Every dest a write verb takes, by what it is. Total against :func:`fields`, so an argument
#: added tomorrow is a red here with one question in it: what checks this before it lands?
FIELDS: dict[str, Composed] = {
    # -- prose a validator refuses ------------------------------------------------
    "symptom": _schema(
        "the falsifiable claim a line is, written into the roadmap or the ledger",
        "symptom.empty", "symptom.too-long", "symptom.markup", "symptom.sentence",
        "symptom.newline", "symptom.control", "symptom.whitespace",
    ),
    "why": _schema(
        "the one sentence a line carries, written into the roadmap or the ledger",
        "why.empty", "why.too-long", "why.no-terminator", "why.sentences",
        "why.newline", "why.control", "why.whitespace",
    ),
    "reason": _schema(
        "a departure's or a pause's sentence, which lands in the entry's or the line's `why`",
        "why.empty", "why.too-long", "why.no-terminator", "why.sentences",
    ),
    "premise": _schema(
        "the claim a dismissal holds while, wrapped around its reason (RK1618)",
        "premise.missing",
    ),
    "part": _schema(
        "which half a partial entry delivered, inside the ledger line's bold head",
        "part.blank", "part.too-long",
    ),
    "remainder": _schema(
        "what is left after a `--part`, which becomes the open line's own `why`",
        "why.empty", "why.too-long", "why.no-terminator", "why.sentences",
    ),
    "superseded_design": _schema(
        "what a deleted design turned out to be wrong about, appended to the ledger sentence",
        "why.too-long",
    ),
    "decides": _schema(
        "the constraint a ship leaves behind, filed as one line in the decisions role",
        "symptom.too-long", "why.too-long", "why.no-terminator",
    ),
    "title": _schema(
        "a heading, written into every file that declares the label or the anchor (RK1570)",
        "title.empty", "title.newline", "title.markup", "char.mangled",
    ),
    "section": _schema(
        "the heading an `add` writes its rationale under, which is a section title",
        "title.empty", "title.newline", "title.markup", "char.mangled",
    ),
    "body": _schema(
        "a rationale paragraph, written into a prose role under its heading",
        "body.empty", "body.promise", "char.mangled",
    ),
    "section_body": _schema(
        "the same paragraph on `add`, written in the transaction that files the line",
        "body.empty", "body.promise", "char.mangled",
    ),
    "replacement": _schema(
        "what a narrow `section amend` puts in place of the clause it names, inside the body",
        "body.empty", "char.mangled",
    ),
    "lead": _schema(
        "the bolded head of a non-goal or a criterion, which is also its address",
        "non-goal.lead", "non-goal.shape", "criterion.lead", "criterion.shape",
    ),
    # -- prose held to the two character rules and nothing else -------------------
    # RK1627's own finding, and the row this register exists to be able to make: `govern`
    # wraps the sentence into comment lines above the key and re-parses the whole file before
    # the bytes land, which refuses a value TOML cannot carry and saw nothing about the prose
    # — so a mangled run landed, in a file `lint` reads for budgets and not for characters.
    #
    # `schema` since RK1666, and the codes are the shared `char.*` family with the field
    # naming the argument: what a comment cannot be held to is a length, a sentence count or
    # a line to fit — there is no line, the wrap makes one — and what it can be held to is the
    # two rules every other composed field takes. `characters()` is that pair, named once.
    "because": _schema(
        "your argument for a number, wrapped into comments above the key in roadkeep.toml",
        "char.mangled", "char.invisible", "char.tab", "char.space",
    ),
    "instead": _schema(
        "the same sentence, replacing the run above the key rather than stacking on it",
        "char.mangled", "char.invisible", "char.tab", "char.space",
    ),
    # -- addresses: what is named, not what is written ----------------------------
    "id": _address("the task this write is about, resolved against the files that hold one"),
    "task_id": _address("the id to mint under, refused against every id any file carries"),
    "family": _address("which track a derived id counts in, from `[ids]`' declared prefixes"),
    "to": _address("the id or anchor a renumber or a move sends this to, refused if taken"),
    "to_block": _address("the label a ledger entry moves under, which a heading must declare"),
    "block": _address("the label this is filed under, which a heading must declare"),
    "label": _address("the block a heading write is about, refused against `[ids]`' shape"),
    "after": _address("the neighbour a new heading or queue entry goes after, resolved"),
    "organise": _address("which role a first heading is written into, from the declared set"),
    "anchor": _address("the section address, refused against this project's `ref_scheme`"),
    "ref": _address("the pointer a line carries, derived under the id scheme and named here"),
    "decides_ref": _address("where a decision's body goes, on a project numbering its own"),
    "role": _address("which governed file, narrowed to the roles this project declares"),
    "namespace": _address("the prefix a prose role's addresses live under, `[refs]`' own"),
    "marker": _address("the open marker a line comes back at, from `[markers] open`"),
    "status": _address("the same field under `add`'s spelling, from `[markers] open`"),
    "deps": _address("what this line waits on, parsed and resolved against the backlog"),
    "add_deps": _address("one dep to add, read by the same parser the group is"),
    "drop_deps": _address("one dep to remove, matched against the group already there"),
    "requires": _address("a requirement word, refused unless `[requirements]` declares it"),
    "token": _address("a queue entry, which is an id or a `Block X` and nothing else"),
    "task": _address("the line a criterion is scoped to, resolved against the roadmap"),
    "checked": _address("a criterion of this task by its lead — its own sentence is what lands"),
    "by": _address("the decision that supersedes this one, resolved in the decisions role"),
    "superseded_by": _address("the id a retirement points forward to, which must exist"),
    "folds_into": _address("the task this work went inside, resolved the same way"),
    "supersedes": _address("the shipped entry a revert undoes, resolved in the ledger"),
    "key": _address("which `roadkeep.toml` key `govern` writes, from the declared tables"),
    # What `declare --move` takes (RK1652). An address and not a value: the key is resolved
    # against `describing.TABLES` and the line that moves is the caller's own bytes, so what
    # this write can get wrong is a placement and never a field — and the file is read back
    # before it lands, which is the `round-trip` half every writer here keeps. Its `--to` is
    # in `ELSEWHERE`, that dest already meaning an anchor on the two verbs that move a section.
    "move": _address("the misplaced key, resolved against the tables this build declares"),
    "at": _address("the number that key takes, refused by the parser that reads the file"),
    "level": _address("the heading depth a section is written at, a small integer"),
    "line": _address("which of two entries under one id, by its line number in the file"),
    "lines": _address("how many lines a wrapped entry spans, so a rewrite replaces them all"),
    "replace": _address("the clause a narrow amend finds, matched against the body verbatim"),
    "spec": _address("which export shape is written, from a closed set of names"),
    # -- paths: a file, resolved and never written as prose -----------------------
    "path": _path("where a declared role's file goes, resolved against the project root"),
    "file": _path("the `[budgets]` entry `govern` is about, addressed as the config spells it"),
    "body_file": _path("a paragraph read from disk instead of the argument, the caller's own"),
    "section_body_file": _path("the same door on `add`, and the caller's file either way"),
    "capture": _path("the kept capture this line files, stamped with the id it mints"),
    "recorded_in": _path("the file a deleted design's durable half moved to; must resolve"),
    "readme": _path("where the projected block is written, a file of the project"),
    "site": _path("the second projection target, resolved the same way"),
}

#: The few a second verb means something else by. Keyed by `(command, dest)`, and the reason
#: each is here rather than a second dest name is that the CLI's own vocabulary is the
#: caller's: `--why` is one flag a caller learns once, and which list it lands in is the verb.
ELSEWHERE: dict[tuple[str, str], Composed] = {
    ("non-goal add", "why"): _schema(
        "a non-goal's reason, held to `[non_goals]`' own two numbers",
        "non-goal.why", "non-goal.shape",
    ),
    ("non-goal amend", "why"): _schema(
        "the same field corrected in place, held to the same two numbers",
        "non-goal.why", "non-goal.shape",
    ),
    ("criterion add", "why"): _schema(
        "a criterion's reason, held to `[criteria]`' own two numbers",
        "criterion.why", "criterion.shape",
    ),
    ("criterion amend", "why"): _schema(
        "the same field corrected in place, held to the same two numbers",
        "criterion.why", "criterion.shape",
    ),
    # `--to` is an anchor on the two verbs that move a section and a **table** here (RK1652):
    # the same word about two vocabularies, which is exactly what this list is for.
    ("declare", "to"): _address(
        "which table a misplaced key goes under, from the ones this build declares it in"
    ),
    # The one dest that is an address on one verb and prose on another: `non-goal drop` and
    # `criterion drop` take the lead to *find* the bullet, and the two `add` verbs write it.
    ("non-goal drop", "lead"): _address("the bullet to withdraw, matched against the list"),
    ("criterion drop", "lead"): _address(
        "the same lookup one list over, matched against the roadmap's third list"
    ),
}


def _walk(parser, path=()):
    for action in parser._actions:
        choices = getattr(action, "choices", None)
        if isinstance(choices, dict):
            for name, sub in choices.items():
                yield from _walk(sub, (*path, name))
    if path and parser.get_default("handler") is not None:
        yield " ".join(path), parser


def fields() -> dict[tuple[str, str], str]:
    """Every value-taking argument a **write** verb declares, as `(command, dest)` → dest.

    The population, read off the real parsers and never listed: an argument added tomorrow is
    in it by being declared, which is the whole difference between a census and a list.

    Booleans are out because there is nothing composed — a switch carries no text — and so are
    `--json` and `--help`, which every verb has and none writes. `reads_only` and `wiring` are
    the parsers' own declarations of what does not write (RK167), so what is left is exactly
    the arguments whose values this tool does something with in a governed file.
    """
    found: dict[tuple[str, str], str] = {}
    for command, parser in _walk(build_parser()):
        if parser.get_default("reads_only") or parser.get_default("wiring"):
            continue
        for action in parser._actions:
            if action.dest in ("help", "json"):
                continue
            if isinstance(action, argparse._SubParsersAction):  # noqa: SLF001
                continue
            if isinstance(
                action,
                (
                    argparse._StoreTrueAction,  # noqa: SLF001
                    argparse._StoreFalseAction,  # noqa: SLF001
                    argparse._CountAction,  # noqa: SLF001
                ),
            ):
                continue
            found[(command, action.dest)] = action.dest
    return found


def classify(command: str, dest: str) -> Composed | None:
    """What this argument is, or `None` where nothing accounts for it."""
    return ELSEWHERE.get((command, dest)) or FIELDS.get(dest)


def rows() -> dict[str, Composed]:
    """Every row this register holds, named the way a failure should print it.

    One spelling, because four assertions want the same walk and a comprehension repeated at
    each of them is the drift a register exists to remove — one layer in from what it is a
    register of.
    """
    return {
        **FIELDS,
        **{f"{command} --{dest}": row for (command, dest), row in ELSEWHERE.items()},
    }


KINDS = ("schema", "round-trip", "address", "path")
