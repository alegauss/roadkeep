"""The command surface (opened by RK4, extended one subcommand per task).

Design rules for everything added here, so that later commands do not each invent
their own:

* **Plain stdout is composable, `--json` is for reasoning.** `roadkeep next-id` prints
  `RK32` and nothing else, so it can be substituted into another command; `--json`
  carries the provenance — which file and line the answer came from — because an
  answer an agent cannot audit gets verified by reading the file, which is the cost
  the command existed to remove (L5).
* **Exit codes are the contract.** 0 success, 1 the gate says no (`lint`, from RK14),
  2 usage or configuration error. A gate that reports in prose is advice. A refused
  `add` (RK5) exits 2 and not 1: what has to change is the caller's input, not the
  file — 1 is reserved for a file that is already wrong.
* **Every mutator emits the event and stops there (RK38).** A write already succeeds or
  refuses with an exit code, so what a hook is missing is not a listener but a payload:
  the id, the block, and whether that block still holds an open line. Deciding what to do
  next belongs to the `PostToolUse` hook (RK22) or the Action (RK17) — a `[hooks]` table
  running commands would make `uvx roadkeep` an executor of whatever a repo declares.
* **Errors name the fix, and a fault names one more move.** A `ConfigError` prints every
  problem it found, once — and a non-zero exit closes with the `report` command that
  captures it, argv already substituted (RK86). Held here rather than at each of the twenty
  refusals, because the exit code is the contract they all already leave through. Not on a
  **verdict**, which is a read-only command's own 1 (RK271): `lint` naming a finding has
  answered the question it was asked, and doubting itself afterwards is the tool's
  highest-traffic output saying nothing.
* **stdout is forced to UTF-8.** The markers are emoji and the default Windows console
  encoding is cp1252, which raises `UnicodeEncodeError` mid-write and leaves a
  half-printed report. That cost three interrupted runs while this file's own package
  was being written.

`argparse`, not `click`: a tool meant to run as `uvx roadkeep` in someone else's CI
pays for every dependency, and the whole command surface is argument parsing.
"""

from __future__ import annotations

import argparse
import difflib
import sys
import tomllib
import traceback
from collections.abc import Sequence

from roadkeep.attesting import attest
from roadkeep.capturing import PARTS, offer
from roadkeep.config import Config, ConfigError, PROSE_ROLES
from roadkeep.exporting import DEFAULTS
from roadkeep.locking import LockBusy, exclusive
from roadkeep.provenance import engine, invocation, invoked, read_by
from roadkeep.ranking import NEAREST
from roadkeep.serving import Prose, spelled
from roadkeep.remaining import declared
from roadkeep.verbs.adopting import (
    _adopt,
    _engines,
    _init,
    _install,
    _mcp,
    _capture_filed,
    _replay,
    _report,
    _uninstall,
)
from roadkeep.verbs.authoring import declare_lines
from roadkeep.verbs.linting import declare_gate
from roadkeep.verbs.querying import (
    _anchors,
    _audit,
    _brief,
    _budget,
    _claim,
    _claims,
    _deps,
    _export,
    _gaps,
    _list,
    _origin,
    _pick,
    _remaining,
    _show,
    _stats,
    _weight,
    _writes,
)
from roadkeep.verbs.declaring import (
    Answer,
    _A_TYPO,
    _BODY_FILE,
    _DESIGNED_HELP,
    _JSON_HELP,
    _PIPE,
    _VALUED,
    _counting_flags,
    _marker_flag,
    _reason_flag,
    _Verb,
    answers,
    narrows,
    withheld,
    writes_when,
)
from roadkeep.verbs.reading import _one_pipe, _piped, harden
from roadkeep.verbs.refusing import EXIT_GATE, EXIT_OK, EXIT_USAGE
from roadkeep.verbs.sections import (
    _refs,
    _block_add,
    _block_drop,
    _block_merge,
    _non_goal_add,
    _non_goal_amend,
    _non_goal_drop,
    _non_goal_list,
    _priority_add,
    _priority_drop,
    _priority_list,
    _priority_migrate,
    _section_add,
    _section_amend,
    _section_drop,
    _section_move,
    _section_show,
)
from roadkeep.verbs.shipping import (
    _delivered,
    _record,
    _record_amend,
    _record_drop,
    _record_move,
    _record_renumber,
    _retire,
    _reversals,
    _ship,
)




class _Version(argparse.Action):
    """Print which engine answered, not just its number (RK79).

    An `action="version"` string is built with the parser, on every run — and naming the
    tree costs a git call. This defers it to the flag being passed, so the answer a plugin
    cache and a checkout disagree on costs nothing on the commands that do the work.
    """

    def __init__(self, option_strings: Sequence[str], dest: str, **kwargs: object) -> None:
        super().__init__(option_strings, dest, nargs=0, default=argparse.SUPPRESS, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None) -> None:  # type: ignore[no-untyped-def]
        print(engine())
        parser.exit(EXIT_OK)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roadkeep",
        description="Own the writes to a project's roadmap, changelog and rationale.",
        # The top level too (RK1032): `-C` and `--version` are the only options here, and
        # `--vers` reaching the second is the same class as `--f` reaching `--fix` — one
        # rule for the whole surface, so no parser is the one that kept the affordance.
        allow_abbrev=False,
    )
    parser.add_argument(
        "--version",
        action=_Version,
        help="the version, the commit it is at and the directory it ran from",
    )
    parser.add_argument(
        "-C",
        "--directory",
        default=".",
        metavar="PATH",
        help="where to start looking for roadkeep.toml (default: the current directory)",
    )
    # Every subcommand is a `_Verb` (RK339), and a nested one inherits the class from its
    # parent, so `section add` is one too — a pair of near-twins one level down declares
    # itself the same way.
    subcommands = parser.add_subparsers(
        dest="command", required=True, parser_class=_Verb
    )

    declare_lines(subcommands)
    declare_gate(subcommands)

    section_parser = subcommands.add_parser(
        "section",
        help="add, show or drop a section in a prose file",
        description=(
            "The prose files are paragraphs, not lines, so their unit is a section: an "
            "anchor a pointer can resolve, a word budget, and a place derived from the "
            "task's block. `ship` calls `drop` for the first of its three edits."
        ),
    )
    actions = section_parser.add_subparsers(dest="action", required=True)

    section_add = actions.add_parser(
        "add",
        help="write a new section under its block, reflowed to the prose width",
        description=(
            "Write one rationale section: the prose on stdin or `--body`, within the word "
            "budget, filled to the configured width, and placed under the task's own block "
            "or beneath the section it extends. A table or a list is inserted as written."
        ),
    )
    section_add.add_argument(
        "anchor", help="the anchor, e.g. RK9 or S:VIII.2 (no §)"
    )
    section_add.add_argument("--title", required=True, help="the heading text")
    section_add.add_argument(
        "--body",
        help="the prose; omitted or '-' reads stdin, which is how a paragraph gets in",
    )
    section_add.add_argument(
        "--body-file", dest="body_file", metavar="PATH", help=_BODY_FILE.format(what="prose")
    )
    section_add.add_argument(
        "--role",
        default="improvements",
        help="which prose file (default: improvements)",
    )
    section_add.add_argument(
        "--level",
        type=int,
        help=(
            "heading depth; derived where omitted — a subsection at 3, and a new top level "
            "at the depth this file already writes one at"
        ),
    )
    section_add.add_argument("--json", action="store_true", help=_JSON_HELP)
    # Ungated and reached by omission: this command's whole input is a paragraph, so `--body`
    # left out *is* the pipe, which the help above states and RK171 makes readable by a surface.
    withheld(
        section_add,
        body_file="`add`'s reason: a path this transport does not share",
        level="the heading depth is the file's shape and the writer derives it, so a caller setting one is a caller writing a heading the renderer would not",
    )
    section_add.set_defaults(
        handler=_section_add, reads_stdin=(Prose(dest="body", unless="body_file"),)
    )

    section_amend = actions.add_parser(
        "amend",
        help="correct a live section's prose or its heading text, in place",
        description=(
            "Rewrite one section's own prose, or its heading text, without deleting it. "
            "The door that was missing: `drop` refuses while an open line points at the "
            "anchor, `add` refuses the duplicate and the guard denies the hand edit, so a "
            "design was write-once until it shipped — which is the opposite of when it "
            "changes. The subtree is not touched: a subsection is amended by its own "
            "anchor. Neither is the anchor itself: that is `section move` under an outline, "
            "and `renumber` where the address is the task's id. Nor is the heading line, "
            "unless --title asks for it: a body-only amend leaves those bytes alone. An "
            "address that is not an anchor is read as a heading text, which is how the two "
            "regions carrying no anchor — the file's opening, and a table of contents — are "
            "reached; neither is charged the section word limit, which is a rationale's."
        ),
    )
    section_amend.add_argument(
        "anchor", help="the anchor, e.g. RK9 (no §), or an unanchored heading's own text"
    )
    section_amend.add_argument("--title", help="replace the heading text")
    section_amend.add_argument(
        "--body",
        help=(
            "the replacement prose; '-' reads stdin, and stdin is the default unless "
            "--title is the only thing being changed"
        ),
    )
    section_amend.add_argument(
        "--body-file",
        dest="body_file",
        metavar="PATH",
        help=_BODY_FILE.format(what="replacement prose"),
    )
    section_amend.add_argument(
        "--role", default="improvements", help="which prose file (default: improvements)"
    )
    section_amend.add_argument("--json", action="store_true", help=_JSON_HELP)
    # `omitted=False` and not an oversight: an amend with neither field is refused below rather
    # than defaulted to the pipe, so only the documented `-` reaches the read here.
    withheld(
        section_amend,
        body_file="`section add`'s reason, which the verb correcting a body does not change: the text crosses as text",
    )
    section_amend.set_defaults(
        handler=_section_amend,
        reads_stdin=(Prose(dest="body", omitted=False, unless="body_file"),),
    )

    section_move = actions.add_parser(
        "move",
        help="re-address a section, its subtree and every pointer at it",
        description=(
            "Move one section to a free address, keeping its prose exactly where it is. The "
            "verb an outline had none of: `renumber` moves an id and leaves the pointer as "
            "typed under any other scheme, so a doubled address — what `lint` calls "
            "`section.ambiguous` and `add` refuses to create — was repairable only by the "
            "hand edit the guard denies. The heading, every nested anchor that extends it "
            "and the `→ §<anchor>` on every line naming one of them move together, or none "
            "of them do. The destination takes every refusal `add` computes, and stays under "
            "the parent the address already had: this write changes the address, not the "
            "place."
        ),
    )
    section_move.add_argument("anchor", help="the anchor to move, e.g. I.2 (no §)")
    section_move.add_argument(
        "--to", required=True, help="the free address to move it to — `anchors` names one"
    )
    section_move.add_argument(
        "--role", default="improvements", help="which prose file (default: improvements)"
    )
    section_move.add_argument("--json", action="store_true", help=_JSON_HELP)
    section_move.set_defaults(handler=_section_move)

    section_show = actions.add_parser(
        "show",
        help="print one section and its word count",
        description=(
            "Print one section whole, with the word count the budget is measured in. An "
            "address that is not an anchor is read as a heading text, so the file's opening "
            "and a table of contents answer too. `--own` prints what `section amend --body` "
            "takes, so the two extents are one on the section that has children. Reads; "
            "never writes."
        ),
    )
    section_show.add_argument(
        "anchor", help="the anchor, e.g. RK9, or an unanchored heading's own text"
    )
    section_show.add_argument(
        "--own",
        action="store_true",
        help=(
            "print this section's own prose alone, which is the extent `section amend "
            "--body` replaces — the round-trip on a section that has subsections"
        ),
    )
    section_show.add_argument("--role", default="improvements", help="which prose file")
    section_show.add_argument("--json", action="store_true", help=_JSON_HELP)
    section_show.set_defaults(handler=_section_show, reads_only=True)

    section_drop = actions.add_parser(
        "drop",
        help="delete one section whole, subsections included",
        description=(
            "Delete one section and everything under it. Subsections included, because one "
            "left behind is orphaned prose under the next task's heading — which reads as "
            "that task's design and is the outcome worse than deleting too much. Refused "
            "when an open line points at the anchor or at anything under it: the section a "
            "live pointer names is `ship`'s to remove, and this verb's job is the orphan."
        ),
    )
    section_drop.add_argument("anchor", help="the anchor, e.g. RK9")
    section_drop.add_argument("--role", default="improvements", help="which prose file")
    section_drop.add_argument("--json", action="store_true", help=_JSON_HELP)
    section_drop.set_defaults(handler=_section_drop)

    block_parser = subcommands.add_parser(
        "block",
        help="declare a block, which no other write will invent for you",
        description=(
            "A block is declared by a heading and by nothing else, so every write refuses "
            "an undeclared one — and the guard denies the hand-edit that would declare it. "
            "Both refusals are right and the pair is a deadlock; this is the key."
        ),
    )
    block_actions = block_parser.add_subparsers(dest="action", required=True)

    block_add = block_actions.add_parser(
        "add",
        help="write the heading into every governed file already organised by blocks",
        description=(
            "The label and the title are yours; everything else is derived per file. It "
            "goes after the last block's subtree — never at the end, where the roadmap's "
            "Non-goals live — or after the block `--after` names, which is a neighbour and "
            "not an index, so each file places it after its own copy of that heading. It is "
            "spelled at the level and with the separator that file's own first block heading "
            "uses. All of the files, or none of them."
        ),
    )
    block_add.add_argument("label", help="the block label, e.g. G")
    block_add.add_argument("--title", required=True, help="what the block is for")
    block_add.add_argument(
        "--after",
        help=(
            "open it after this block instead of last, e.g. C; refused where a file that "
            "wants the heading declares no such neighbour"
        ),
    )
    block_add.add_argument(
        "--organise",
        action="append",
        default=[],
        metavar="ROLE",
        help=(
            "also write the first block heading into this file, e.g. changelog; a file "
            "organised by nothing is skipped without it, and every ship there refuses"
        ),
    )
    block_add.add_argument("--json", action="store_true", help=_JSON_HELP)
    block_add.set_defaults(handler=_block_add)

    block_drop = block_actions.add_parser(
        "drop",
        help="remove the heading from every file where it stands over nothing",
        description=(
            "The inverse, and narrow in the one way that matters: a heading over work is "
            "not an empty heading. It is removed only where its whole subtree is blank, "
            "and refused by name where anything is filed under the label — open lines, "
            "paused ones, rationale sections. The ledger is the exception, left alone and "
            "said so, because history keeps the heading it was filed under."
        ),
    )
    block_drop.add_argument("label", help="the block label, e.g. G")
    block_drop.add_argument(
        "--prose",
        action="store_true",
        help="take the heading's note with it — loose prose only, never work",
    )
    block_drop.add_argument("--json", action="store_true", help=_JSON_HELP)
    block_drop.set_defaults(handler=_block_drop)

    block_merge = block_actions.add_parser(
        "merge",
        help="fold a label's duplicate headings into the first, moving the entries",
        description=(
            "The key RK391 named. Two headings under one label is a state the gate reports "
            "and every write refuses with `merge the two regions by hand` — which the guard "
            "denies. This is that merge, done by the tool: the first heading stays, every "
            "later one's entries move under it, and the emptied duplicates go. The ledger is "
            "included, not skipped, because history stays under a heading of the same label. "
            "All of the files, or none of them. A nested section is `section move`'s to place "
            "and refused here; loose prose is dropped only under --prose."
        ),
    )
    block_merge.add_argument("label", help="the block label, e.g. B")
    block_merge.add_argument(
        "--prose",
        action="store_true",
        help="drop a duplicate heading's loose prose as it is folded — never an entry",
    )
    block_merge.add_argument("--json", action="store_true", help=_JSON_HELP)
    block_merge.set_defaults(handler=_block_merge)

    ship_parser = subcommands.add_parser(
        "ship",
        help="move a task to the ledger, drop its rationale, clear the roadmap line",
        description=(
            "Ship one task in three edits across three files. Everything is validated "
            "before anything is written, because whichever of the three is done by hand "
            "last is the one that gets forgotten. `--why` is the outcome and is required: "
            "the roadmap's sentence states the problem, and inheriting it files a defect "
            "report under a heading that means done."
        ),
    )
    ship_parser.add_argument("id", help="the task to ship, e.g. RK5")
    ship_parser.add_argument(
        "--why",
        help=(
            "the outcome this shipped — required where an entry is written, because the "
            "roadmap's sentence states a problem and is not inherited; refused where the "
            "ledger already holds the id and this call only closes the line. Completing a "
            "wrapped partial with --lines above one, it is the whole span: the first line "
            "is the outcome and the rest is written back as the tail" + _PIPE
        ),
    )
    ship_parser.add_argument(
        "--part",
        help=(
            "record only the half that landed and leave the line open, e.g. 'local "
            "half'; a later ship with no --part completes it and removes the qualifier"
        ),
    )
    ship_parser.add_argument(
        "--lines",
        type=int,
        help=(
            "how many lines the completion replaces; required where the partial entry it "
            "completes wraps, and refused where this call replaces no entry — above one it "
            "is also what lets --why carry that span back instead of collapsing it"
        ),
    )
    ship_parser.add_argument(
        "--superseded-design",
        help=(
            "what the design this deletes turned out to be wrong about, e.g. 'the resize "
            "endpoint it called a new subsystem had shipped two blocks earlier'; appended "
            "to the ledger's sentence with the section's address, since the entry is the "
            "one place both survive the deletion"
        ),
    )
    ship_parser.add_argument("--json", action="store_true", help="every edit, as data")
    ship_parser.set_defaults(
        handler=_ship,
        reads_stdin=(
            Prose(dest="why", omitted=False),
            # The argument RK1176 was filed about: the pipe is documented on every prose
            # argument, and this one reached the ledger as a literal `-` because the handler
            # resolved `--why` by hand and this was added after that line was written.
            Prose(dest="superseded_design", omitted=False),
        ),
    )

    record_parser = subcommands.add_parser(
        "record",
        help="write, correct, re-file, renumber or drop a ledger entry directly",
        description=(
            "The ledger's own doors, the ones the roadmap's are not: every other command "
            "starts from a task line, and these start from the entry."
        ),
    )
    entries = record_parser.add_subparsers(dest="action", required=True)

    record_add = entries.add_parser(
        "add",
        help="write a ledger entry directly, for shipped work no open line can carry",
        description=(
            "The fourth door, and the only one that starts nowhere: `ship` and both "
            "retirements begin from an open roadmap line, so this is how the ledger records "
            "work that has none. Never planned is one case and not the definition — a task "
            "that was planned and shipped inside another's sentence needs its own entry too, "
            "and so does a revert (--supersedes). What it does is write the entry and touch "
            "nothing else; without it the only route in was a fictitious line shipped in the "
            "same breath, which teaches that the format can be gamed."
        ),
    )
    record_add.add_argument("--block", required=True, help="the block label, e.g. B")
    record_add.add_argument(
        "--symptom",
        required=True,
        help="what did not work — a phrase, never the name of the patch that closed it",
    )
    record_add.add_argument(
        "--why",
        required=True,
        help="one sentence, ending in a stop: the outcome" + _PIPE,
    )
    record_add.add_argument(
        "--id",
        dest="task_id",
        help=(
            "the id (default: derived, one past the highest anywhere); refused where a "
            "line already holds it, allowed where only a sentence names it — which is how "
            "an id cited but never recorded gets the entry it is missing"
        ),
    )
    record_add.add_argument(
        "--supersedes",
        metavar="ID",
        help=(
            "the entry this one reverts: its sentence gains `(superseded by <id>)` in the "
            "same write, so the ledger's two records of one decision know about each other"
        ),
    )
    record_add.add_argument(
        "--lines",
        type=int,
        # Declared only so a script that spells it gets `NoSpan` rather than argparse's
        # `declares no --lines` (RK1056): the count authorised a span rewrite the pointer
        # stopped making, and the refusal is the one answer that says which of the two
        # changed. Withdrawn from the served tool, which has no script to keep working.
        help=(
            "refused, and kept only to say so: the --supersedes pointer is appended to the "
            "sentence on the entry's first line and replaces no span, so a wrapped bullet "
            "needs no count and keeps the lines under it"
        ),
    )
    record_add.add_argument(
        "--json", action="store_true", help="the entry, with the file and line it landed on"
    )
    withheld(
        record_add,
        task_id="the ledger's id is the roadmap line's, and `ship` is what carries it across; typing one here is inventing an id the backlog never issued",
        lines="the entry's shape is derived from what it records, and a count set by hand is the arrangement the schema replaced",
    )
    record_add.set_defaults(
        handler=_record, reads_stdin=(Prose(dest="why", omitted=False),)
    )

    record_amend = entries.add_parser(
        "amend",
        help="correct a ledger entry's sentence where it stands",
        description=(
            "Rewrite one entry's `why`, or a partial's qualifier, without moving the line. "
            "`drop` and `add` are not equivalent to this: they would remove the entry and "
            "append a new one under its block, so a ledger read in the order work landed "
            "stops being one and a reviewer sees a deletion where a word changed. The "
            "`symptom` is the claim and is not a field, the id is `renumber`'s, and the "
            "block is not offered because filing an entry elsewhere is a move."
        ),
    )
    record_amend.add_argument("id", help="the recorded id, e.g. RK41")
    record_amend.add_argument(
        "--why",
        help=(
            "the corrected sentence, one stop — or, with --lines above one, the whole span: "
            "the first line is the sentence and the rest is written back as the tail" + _PIPE
        ),
    )
    record_amend.add_argument(
        "--part",
        help="correct a partial's qualifier; refused where the entry carries none",
    )
    record_amend.add_argument(
        "--lines",
        type=int,
        help=(
            "how many lines this correction replaces; required where the entry wraps, "
            "because there the sentence runs past the line the parse holds — and above "
            "one it is also what lets --why carry that span back"
        ),
    )
    record_amend.add_argument("--json", action="store_true", help=_JSON_HELP)
    record_amend.set_defaults(
        handler=_record_amend, reads_stdin=(Prose(dest="why", omitted=False),)
    )

    record_move = entries.add_parser(
        "move",
        help="re-file a ledger entry under another block heading",
        description=(
            "The move `amend` deliberately does not pretend is a correction. `ship` files an "
            "entry under the block its roadmap line sat in, so a line filed under the wrong "
            "one ships to the wrong one — and no other verb reaches it: `record add` refuses "
            "an id that exists, `drop` wants the id stated twice, `renumber` changes the "
            "address and not the heading. This removes the line and re-places it under the "
            "named heading, reporting both positions, and refuses a heading the ledger does "
            "not declare — `block add` is what writes one."
        ),
    )
    record_move.add_argument("id", help="the recorded id, e.g. RK41")
    record_move.add_argument(
        "--to-block",
        required=True,
        dest="to_block",
        help="the block label to file it under, e.g. B; refused unless a heading declares it",
    )
    record_move.add_argument(
        "--json", action="store_true", help="both positions, and the blocks they are under"
    )
    record_move.set_defaults(handler=_record_move)

    record_drop = entries.add_parser(
        "drop",
        help="remove the later of two ledger entries for one id",
        description=(
            "Delete a duplicate entry, and only a duplicate: refused unless the ledger states "
            "the id twice, because removing the only record of a decision is deleting history "
            "rather than de-duplicating it. The first entry stays, since that is where a "
            "reader already found the decision, and no other file is opened."
        ),
    )
    record_drop.add_argument("id", help="the id the ledger carries twice, e.g. RK41")
    record_drop.add_argument(
        "--line",
        type=int,
        help=(
            "which of the two entries goes; required when they do not say the same thing, "
            "because then they are two deliveries and not one recorded twice"
        ),
    )
    record_drop.add_argument(
        "--json", action="store_true", help="which line went, and which one answers now"
    )
    record_drop.set_defaults(handler=_record_drop)

    record_renumber = entries.add_parser(
        "renumber",
        help="give one of two entries for an id an address of its own",
        description=(
            "The counterpart of `renumber` for the file that verb never opens. Renumbering "
            "a record is normally how a `git log -S` starts returning two unrelated "
            "designs — and that argument inverts on a collision, where the shared id is "
            "already what makes the history unreadable. Refused on anything but an id the "
            "ledger states twice, and which of the entries moves is yours to name: the one "
            "that earned the id from a roadmap line is the one to leave alone."
        ),
    )
    record_renumber.add_argument("id", help="the id the ledger carries twice, e.g. RK41")
    record_renumber.add_argument(
        "--line", type=int, help="the entry that moves; named, never defaulted"
    )
    record_renumber.add_argument(
        "--to", help="the new id (default: derived, one past the highest in its family)"
    )
    record_renumber.add_argument("--json", action="store_true", help=_JSON_HELP)
    record_renumber.set_defaults(handler=_record_renumber)

    scope_parser = subcommands.add_parser(
        "non-goal",
        help="write the roadmap's other bullet: a constraint, not a task",
        description=(
            "The one content of the roadmap that is not a task line, and until RK70 the one "
            "thing nothing governed: `Edit` denied and offered five commands that all write "
            "task lines, `lint` said nothing because a bullet with no marker is prose, and "
            "`sed` through `Bash` was the route left. Opt in with `[non_goals]`."
        ),
    )
    # Three actions, two of which write. `list` is here rather than as the top-level
    # `non-goals` its design named (RK69): one noun with three verbs, because `non-goal` and
    # `non-goals` are two addresses for one list and a near-twin is a command typed wrong.
    constraints = scope_parser.add_subparsers(dest="action", required=True)

    scope_add = constraints.add_parser(
        "add",
        help="insert one non-goal under the heading, filled to the prose width",
        description=(
            "Compose, validate and insert one non-goal. Addressed by its lead — unique and "
            "checked — because an id would buy a lifecycle for a list of eight lines that "
            "changes once a year. No marker, no dep and no pointer: a constraint has no "
            "status to state."
        ),
    )
    scope_add.add_argument(
        "--lead",
        required=True,
        help="what is not built — the bolded head a brief prints and a duplicate is judged on",
    )
    scope_add.add_argument(
        "--why",
        required=True,
        help="the reason it is not, in this file's own limit" + _PIPE,
    )
    scope_add.add_argument(
        "--json", action="store_true", help="the bullet, with the file and line it landed on"
    )
    scope_add.set_defaults(
        handler=_non_goal_add, reads_stdin=(Prose(dest="why", omitted=False),)
    )

    scope_amend = constraints.add_parser(
        "amend",
        help="rewrite one non-goal's reason where it already sits",
        description=(
            "Correct a constraint's reason in place, keeping the bullet's position. The door "
            "`record amend` and `section amend` already are one grammar over: without it the "
            "only route was drop-and-re-add, and `add` inserts after the last bullet — so a "
            "constraint that sat fifth of eight moved to eighth, and a reviewer read a "
            "deletion where a word changed. The lead is not a field: it is the address, so a "
            "changed one is a `drop` and an `add`."
        ),
    )
    scope_amend.add_argument(
        "lead", help="the lead, as the file reads it; the trailing stop and case do not matter"
    )
    scope_amend.add_argument(
        "--why", required=True, help="the corrected reason, in this file's own limit" + _PIPE
    )
    scope_amend.add_argument("--json", action="store_true", help=_JSON_HELP)
    scope_amend.set_defaults(
        handler=_non_goal_amend, reads_stdin=(Prose(dest="why", omitted=False),)
    )

    scope_list = constraints.add_parser(
        "list",
        help="print what may not be proposed at all — call it before `add`",
        description=(
            "The list that binds an `add`, at the moment one is *proposed* rather than the "
            "moment a task starts: until RK69 only `brief <id>` printed it, so the rule was "
            "carried by a sentence in a file. Presence, not enforcement — whether a proposal "
            "violates a constraint is a judgement about meaning, and this tool has no model "
            "(L4). Reading is never refused, so an ungoverned list prints and says so."
        ),
    )
    scope_list.add_argument(
        "--json", action="store_true", help="the leads, with the file and what was left"
    )
    scope_list.set_defaults(handler=_non_goal_list, reads_only=True)

    scope_drop = constraints.add_parser(
        "drop",
        help="remove the non-goal a lead addresses, wrapped lines included",
        description=(
            "Delete one non-goal whole. The half a correction needs: a lead is the address, "
            "so a constraint whose lead changes is one retired and one written rather than an "
            "edit to an address. Where two bullets carry one lead the later goes, which makes "
            "this the door for `lint`'s non-goal.duplicate as well."
        ),
    )
    scope_drop.add_argument(
        "lead", help="the lead, as the file reads it; the trailing stop and case do not matter"
    )
    scope_drop.add_argument("--json", action="store_true", help=_JSON_HELP)
    scope_drop.set_defaults(handler=_non_goal_drop)

    queue_parser = subcommands.add_parser(
        "priority",
        help="the order that outranks the id order, in the file the plan lives in",
        description=(
            "The one tier of `pick` a project declares rather than derives, moved out of "
            "`roadkeep.toml` and into a `## Priority` section of the roadmap (RK325). Every "
            "token in it names work, and work leaves — so unlike the prefix, the paths and "
            "the limits, the queue stops being true by itself, and the config was the one "
            "file nothing governs. The section wins wherever both are declared."
        ),
    )
    # Three verbs under one noun, for the reason `non-goal` has three (RK69): `priority` and
    # `priorities` are two addresses for one list, and a near-twin is a command typed wrong.
    ordering = queue_parser.add_subparsers(dest="action", required=True)

    queue_add = ordering.add_parser(
        "add",
        help="put a token in the queue — an id, or 'Block X'",
        description=(
            "Insert one entry under the priority heading. Appended by default, because a "
            "queue grows at the end and 'everything new is most urgent' is the order nobody "
            "meant; --first and --after are the two places that are not the end, and moving "
            "work up the order is the act the config file made unavailable."
        ),
    )
    queue_add.add_argument("token", help="an id of this project, or 'Block X'")
    placement = queue_add.add_mutually_exclusive_group()
    placement.add_argument(
        "--first", action="store_true", help="ahead of everything already queued"
    )
    placement.add_argument(
        "--after", metavar="TOKEN", help="directly after this entry, which must be queued"
    )
    queue_add.add_argument(
        "--json", action="store_true", help="the entry, its place in the order, and the line"
    )
    queue_add.set_defaults(handler=_priority_add)

    queue_list = ordering.add_parser(
        "list",
        help="the order as it stands, and which file declared it",
        description=(
            "The queue `pick` applies, in order, with the file it came from — because a "
            "project that wrote a section and is still being ordered by its config has a "
            "fact to learn and no other way to learn it. Reading is never refused."
        ),
    )
    queue_list.add_argument("--json", action="store_true", help=_JSON_HELP)
    queue_list.set_defaults(handler=_priority_list, reads_only=True)

    queue_drop = ordering.add_parser(
        "drop",
        help="take a token out of the queue",
        description=(
            "Delete one entry. There is no correction verb between the two: an entry carries "
            "a token and nothing else, so a token that changed is a different entry and a "
            "move is a drop and an insert."
        ),
    )
    queue_drop.add_argument("token", help="the entry to remove, as the file spells it")
    queue_drop.add_argument("--json", action="store_true", help=_JSON_HELP)
    queue_drop.set_defaults(handler=_priority_drop)

    # The third verb, and the one that exists because the other two could not be reached
    # (RK427): a project whose queue is still `roadkeep.toml`'s was reported a defect by the
    # gate and refused by both doors, which had never opened that file.
    queue_migrate = ordering.add_parser(
        "migrate",
        help="move roadkeep.toml's queue into the roadmap, where every queue verb reaches it",
        description=(
            "RK325 moved the queue into the roadmap and the gate still reads the old "
            "declaration, which is right — a project that has not migrated has a real "
            "order. This is the door between them. The config line is left alone, because "
            "nothing here writes `roadkeep.toml`: the section wins from the moment this "
            "returns, and `lint` names the leftover as `priority.config`."
        ),
    )
    queue_migrate.add_argument("--json", action="store_true", help=_JSON_HELP)
    queue_migrate.set_defaults(handler=_priority_migrate)

    list_parser = subcommands.add_parser(
        "list",
        help="the task lines, filtered, printed verbatim",
        description=(
            "Print the lines a filter selects, exactly as the file spells them. A "
            "marker-bearing line the grammar did not accept is reported on stderr with "
            "the count, so a filtered listing can never look complete when it is not."
        ),
    )
    _counting_flags(list_parser)
    _marker_flag(list_parser, "only this status marker", dest="marker")
    list_parser.add_argument(
        "--ids", action="store_true", help="print ids alone, one per line"
    )
    withheld(
        list_parser,
        ids='how a terminal prints: the payload carries every id in `tasks`, so a caller over this transport already has what the flag composes',
    )
    list_parser.set_defaults(handler=_list, reads_only=True)
    # Two output *forms* of one read are two answers, exactly as `budget`'s subjects are
    # (RK465's rule, RK467's find): the payload came back whole with nothing said about the
    # flag that shaped nothing.
    answers(list_parser, ("ids", "the listing as bare ids"), ("json", "the payload"))

    stats_parser = subcommands.add_parser(
        "stats",
        help="counts per block and per marker, with what was not counted",
        description=(
            "Count the file. Every count carries the number of marker-bearing lines it "
            "could *not* read, printed even when it is zero: a grep reports the "
            "remainder with no indication that anything is missing."
        ),
    )
    _counting_flags(stats_parser)
    stats_parser.set_defaults(handler=_stats, reads_only=True)

    audit_parser = subcommands.add_parser(
        "audit",
        help="every marker-bearing line the count did not count, and why",
        description=(
            "Print the misses. This is what makes a count trustable rather than an "
            "extra: exit stays 0, because reporting is not the gate (`lint`, RK14) — "
            "an audit that failed a build would be a gate nobody could adopt first."
        ),
    )
    _counting_flags(audit_parser)
    audit_parser.set_defaults(handler=_audit, reads_only=True)

    claims_parser = subcommands.add_parser(
        "claims",
        help="which lines a worker is holding, oldest first, and where that is recorded",
        description=(
            "List the claim registry against the roadmap: held, expired — stepped over, so "
            "the line is offered again — or stale, meaning the marker moved and nothing "
            "reads the entry. Ranks nothing and offers nothing: `pick` decides what to work "
            "on, and the release is a marker."
        ),
    )
    claims_parser.add_argument(
        "--prune",
        action="store_true",
        help=(
            "drop the rows that are not claims and keep the ones that are, which is the "
            "reconciliation a marker write performs and the only other remedy is the file"
        ),
    )
    claims_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # A read that can write, so it declares which flag makes it one (RK167): `dispatch` keeps
    # deciding the lock, and reading the registry never waits on one.
    withheld(
        claims_parser,
        prune='it writes the registry, exactly as `lint --fix` writes the files (RK16)',
    )
    claims_parser.set_defaults(handler=_claims, reads_only=True, writes_when="prune")

    claim_parser = subcommands.add_parser(
        "claim",
        help="the paths one held line's commit owns, declared once and answered on demand",
        description=(
            "Say which paths this task will touch, and read them back at the moment of "
            "committing. Without --path it answers what was declared, plus what the tree "
            "holds that another live claim says is its own — the analysis `git add -A` "
            "cannot make. Declared verbatim: nothing here reads the disk or the task's "
            "prose to guess a path, and nothing here dates a claim."
        ),
    )
    claim_parser.add_argument("id", help="the task id, which a live claim must already hold")
    claim_parser.add_argument(
        "--path",
        action="append",
        default=[],
        metavar="PATH",
        help=(
            "a path this task's commit owns, repeatable; replaces the whole scope, so a "
            "correction is one call and not a file to edit"
        ),
    )
    claim_parser.add_argument(
        "--add-path",
        action="append",
        default=[],
        metavar="PATH",
        dest="add_path",
        help=(
            "a path this task's commit *also* owns, repeatable; keeps what was declared, so "
            "a file the work turned up is one argument and not the whole scope again"
        ),
    )
    claim_parser.add_argument(
        "--porcelain",
        action="store_true",
        help="the paths alone, one per line — what a commit script feeds to `git add --`",
    )
    claim_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # A read that can write, declared the way `claims --prune` declares it (RK167) — and by
    # two arguments (RK307), because either of them is the write.
    withheld(
        claim_parser,
        porcelain='how a terminal prints, for a caller that is already reading JSON',
    )
    claim_parser.set_defaults(
        handler=_claim,
        reads_only=True,
        writes_when=("path", "add_path"),
        # The second pair, found by the read RK339 asked for: same one-edit distance, same
        # asymmetry, and the same verb typed wanting the listing.
        twin=(
            "claim reads one line's scope back and needs it: `claim <id>`, or "
            "`claim <id> --path …` to declare what this commit owns. The registry "
            "listing is `claims`, which needs no id"
        ),
    )
    # The sixth pair, and the first one the *declaration* found rather than a sweep (RK489):
    # `--porcelain` returned before `--json` was read, so a caller asking for the payload got
    # the paths, byte for byte. RK467's sweep could never see it — it runs against a fixture
    # with no live claim, where every `claim` pair exits 2 for want of one — which is the
    # limit of finding a class by probing, one probe away from the class being declarable.
    answers(
        claim_parser,
        ("porcelain", "the paths alone, for `git add --`"),
        ("json", "the payload"),
    )

    writes_parser = subcommands.add_parser(
        "writes",
        help="which governed files a verb wrote, which nothing did, and where that is recorded",
        description=(
            "Read the write record against the files: attested — the bytes a verb left — "
            "unattested, meaning something else produced them, or unrecorded, meaning no "
            "verb has run here yet. Moves no baseline, so asking twice answers twice; the "
            "`Stop` hook states it once and consumes it (RK175)."
        ),
    )
    writes_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # Never a write, not even behind a flag: re-baselining is what the `Stop` block does, and a
    # query offering it would be the laundering `dispatch` refuses queries in the first place.
    writes_parser.set_defaults(handler=_writes, reads_only=True)

    delivered_parser = subcommands.add_parser(
        "delivered",
        help="what a block has already shipped, as claims — the read before an `add`",
        description=(
            "The other list to consult before proposing work, beside `non-goal list` "
            "(RK69). A duplicate is not refused and could not be: RK378 restated RK340 the "
            "day after it shipped and RK382 restated RK178 a day later, and a lexical match "
            "cannot be gated: measured over this ledger it ranks the true pair in the top "
            "three and still scores below what an entry with no duplicate scores against "
            "its own nearest neighbour, so no threshold separates them. Two people "
            "describing one problem use disjoint words, and recognising that takes meaning "
            "this tool has none of (L4). So it states what "
            "the block delivered and you read it. Symptoms alone: the claim is what a "
            "duplicate collides with, and the outcome sentence doubles the length. A letter "
            "no heading declares is refused rather than answered as empty — that answer is "
            "read as evidence — and where the label is declared the reply says which of "
            "live, paused, finished or empty the block is. `--near` is the same read "
            f"bounded by the question (RK442): the {NEAREST} entries nearest the sentence "
            "you are about to propose, in order, instead of the whole block. The order is "
            "the answer and there is no score — RK441 measured that the absolute one "
            "separates nothing, so publishing it would invite a threshold that cannot exist."
        ),
    )
    delivered_parser.add_argument("block", help="the block label, e.g. B")
    delivered_parser.add_argument(
        "--near",
        metavar="SYMPTOM",
        help=(
            f"the symptom about to be proposed: print the {NEAREST} entries nearest it "
            "rather than the block, ranked by word overlap and never refused or warned about"
        ),
    )
    delivered_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    delivered_parser.set_defaults(handler=_delivered, reads_only=True)

    reversals_parser = subcommands.add_parser(
        "reversals",
        help="the decisions this ledger already made and undid, with the argument",
        description=(
            "A revert is filed as a delivery, so a duplicate check answers `yes, shipped` "
            "about the entry that says the work did not hold. This reads the forward "
            "pointer back: every id the ledger marks superseded, the entry that superseded "
            "it, and that entry's sentence — which is the argument a fresh proposal is "
            "against. Read it before an `add`, not after. It refuses nothing: re-proposing "
            "reverted work is sometimes right, and which is a judgement the tool never makes."
        ),
    )
    reversals_parser.add_argument(
        "--id",
        dest="task_id",
        help="ask about one id: exits 1 where that id's decision was reversed",
    )
    reversals_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    reversals_parser.set_defaults(handler=_reversals, reads_only=True)


    brief_parser = subcommands.add_parser(
        "brief",
        help="everything it costs to start one task, in one call",
        description=(
            "Compose the line, its rationale, its resolved deps, the blocker chain, what "
            "shipping it unblocks and the non-goals that bind it. With no id, briefs "
            "whatever `pick` would choose, which makes the first call the only one."
        ),
    )
    brief_parser.add_argument(
        "id", nargs="?", help="the task; omitted, `pick` chooses it"
    )
    brief_parser.add_argument(
        "--block", help="scope the pick to one block, e.g. C (only without an id)"
    )
    brief_parser.add_argument(
        "--designed",
        action="store_true",
        help=_DESIGNED_HELP,
    )
    brief_parser.add_argument(
        "--claim",
        action="store_true",
        help=(
            "take the line as well as describing it: the marker moves to in-progress in the "
            "same transaction, and a named id another worker holds is refused"
        ),
    )
    brief_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    withheld(
        brief_parser,
        claim='it writes, and a read that writes is a read a caller stops making freely (L5) — so the writing door is a tool of its own with its own hint',
    )
    brief_parser.set_defaults(handler=_brief, reads_only=True, writes_when="claim")

    budget_parser = subcommands.add_parser(
        "budget",
        help="how many characters a line has left for prose, before one is written",
        description=(
            "Report what a line leaves its prose fields. Every number is derived from "
            "the id, the marker, the deps and the pointer — all of which are known before "
            "the first word exists — so the budget is a fact about the line you are about "
            "to write rather than a verdict on one you already wrote. With an id that the "
            "roadmap holds, it is that line's own, which is what an amend has."
        ),
    )
    budget_parser.add_argument(
        "id",
        nargs="?",
        help="an existing line, e.g. RK12 — omitted, the line `add` would write next",
    )
    budget_parser.add_argument(
        "--block", default="", help="the block the line would be filed under, e.g. B"
    )
    budget_parser.add_argument(
        "--dep",
        action="append",
        default=[],
        dest="deps",
        metavar="DEP",
        help="a dep the line would carry, repeatable: the group is what moves the budget",
    )
    _marker_flag(
        budget_parser, "the marker the line would carry (default: the first declared)"
    )
    budget_parser.add_argument(
        "--symptom",
        default="",
        help="the symptom, where it is written: what it takes is what the why loses",
    )
    budget_parser.add_argument(
        "--prefix",
        dest="family",
        help="count the derived id in this track (default: the first declared)",
    )
    budget_parser.add_argument(
        "--ref",
        help=(
            "the anchor the line would point at, for ref_scheme = 'outline' only: the "
            "pointer is structure, so unnamed the budget assumes the widest on file"
        ),
    )
    # The other two prose limits, at the same door and never as a `--dry-run` (RK283): both
    # are facts about the file and the role, so both are answerable with no prose in hand.
    budget_parser.add_argument(
        "--anchor",
        metavar="ANCHOR",
        help="a section, e.g. RK12: what its body may say in words, and what it has spent",
    )
    budget_parser.add_argument(
        "--role",
        choices=PROSE_ROLES,
        help="which prose file --anchor is measured against (default: the one holding it)",
    )
    budget_parser.add_argument(
        "--non-goal",
        dest="non_goal",
        action="store_true",
        help="the two limits `non-goal add` enforces, which are the list's own",
    )
    # The fifth subject, and the one context nothing counted (RK464). Every other budget here
    # is about prose a *write* is measured against; this one is about what the surface itself
    # costs a session, which is the same argument RK30 makes about a resident file and had
    # never been made about the schema this server publishes.
    budget_parser.add_argument(
        "--tools",
        action="store_true",
        help=(
            "what this project's tool list costs a session that connects the server: the "
            "count, the characters, and which tools they are — the read RK30 makes about "
            "an every-turn file, about the surface"
        ),
    )
    budget_parser.add_argument(
        "--lead",
        help="a non-goal that exists, with --non-goal: what its argument has left",
    )
    # The fourth subject, and the one limit this format holds that had no pre-write read
    # (RK345): every other budget is derived from a line, and this one from the file on disk.
    budget_parser.add_argument(
        "--file",
        nargs="?",
        const="",
        metavar="PATH",
        help=(
            "an every-turn file `[budgets]` declares, e.g. agents.md: what it costs in "
            "lines and bytes and what is left — bare, every declared budget"
        ),
    )
    # The sixth, and the one neither of the two above could be asked about (RK1095): what a
    # session pays is the tool list once and every resident file on each turn, and deciding
    # between cutting a description and cutting a paragraph meant two commands and a
    # subtraction. Two figures against their cadences rather than one that hides a multiplier.
    budget_parser.add_argument(
        "--session",
        action="store_true",
        help=(
            "what one session pays: the served schema once at the handshake and every "
            "`[budgets]` file on each turn, named against the cadence each is paid at"
        ),
    )
    budget_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    withheld(
        budget_parser,
        family="`add`'s reason read back: the answer is about the id this project would issue next, and a prefix typed here asks about one it would not",
    )
    budget_parser.set_defaults(handler=_budget, reads_only=True)
    # Four subjects and one verb (RK283/RK345), declared rather than checked by hand (RK489).
    # Named rather than inferred from the positional: under the id scheme `RK12` is both a
    # line and an anchor, and a command that guessed which one was meant would be a budget
    # the caller has to check before trusting.
    answers(
        budget_parser,
        ("anchor", "one section's prose"),
        ("non_goal", "the roadmap's other bullet"),
        ("file", "an every-turn file"),
        ("tools", "what this tool surface costs a session"),
        ("session", "both halves of what a session pays, against their cadences"),
    )
    narrows(budget_parser, "role", "anchor")
    narrows(budget_parser, "lead", "non_goal")

    show_parser = subcommands.add_parser(
        "show",
        help="one task: its line, its rationale section and the paths it names",
        description=(
            "Join what a task is out of the files that hold a piece of it. Nothing is "
            "stored to make this possible: the section is found by the pointer, and a "
            "pointer that resolves to nothing is reported as the absence it is."
        ),
    )
    show_parser.add_argument("id", help="the task, e.g. RK12")
    show_parser.add_argument(
        "--no-body",
        dest="no_body",
        action="store_true",
        help="omit the section's prose, keeping the line and where the prose is",
    )
    show_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    show_parser.set_defaults(handler=_show, reads_only=True)

    pick_parser = subcommands.add_parser(
        "pick",
        help="the next task to work on, and the reason it was chosen",
        description=(
            "Apply three tiers — work already in progress, the declared priority, then "
            "the lowest ready id — and print which one answered. A task blocked outside "
            "the backlog is never offered: shipping cannot unblock it."
        ),
    )
    pick_parser.add_argument(
        "--block",
        help=(
            "scope every part of the answer to one block, so 'nothing to pick' is a "
            "statement about that block and not about a lower id somewhere else"
        ),
    )
    pick_parser.add_argument(
        "--designed",
        action="store_true",
        help=_DESIGNED_HELP,
    )
    pick_parser.add_argument(
        "--claim",
        action="store_true",
        help=(
            "take the line as well as read it: the marker moves to in-progress in the same "
            "transaction, so the next caller is answered with something else"
        ),
    )
    pick_parser.add_argument(
        "--json", action="store_true", help="the pick, the tier and the counts"
    )
    # The query it is without `--claim`, and the write it is with one (RK167). `take` still
    # holds a lock of its own over the answer *and* the marker, that pair being what has to be
    # indivisible for every caller — re-entrant, so declaring it here costs nothing twice.
    withheld(
        pick_parser,
        claim="`brief`'s reason, and its answer too: the writing door is already served as the `claim` tool, so a second flag here would be a second spelling of it",
    )
    pick_parser.set_defaults(handler=_pick, reads_only=True, writes_when="claim")

    retire_parser = subcommands.add_parser(
        "retire",
        help="record a line leaving without shipping: replaced by another, or abandoned",
        description=(
            "The two departures that are not a ship: the work moved to another id "
            "(--superseded-by), or it is not being done. Both write one ledger line under "
            "the block it belonged to, with the forward pointer where there is one, and no "
            "design — which is what a gap here otherwise reads as, a botched hand-edit."
        ),
    )
    retire_parser.add_argument("id", help="the task leaving, e.g. RK33")
    retire_parser.add_argument(
        "--superseded-by",
        dest="superseded_by",
        metavar="ID",
        help=(
            "the id that takes the work over, which is a replacement and not an "
            "abandonment; omitted, the line is recorded as abandoned"
        ),
    )
    _reason_flag(
        retire_parser, "one sentence, the author's own: the tool never writes it" + _PIPE
    )
    retire_parser.add_argument("--json", action="store_true", help="every edit, as data")
    retire_parser.set_defaults(
        handler=_retire, reads_stdin=(Prose(dest="reason", omitted=False),)
    )

    export_parser = subcommands.add_parser(
        "export",
        help="project the backlog onto a README block, a page, or a JSON payload",
        description=(
            "Derive what another file would restate: counts per block and the next ready "
            "line. Idempotent and stamped with nothing, so a refresh with nothing to say "
            "makes no diff — and every character of content already passed `add`."
        ),
    )
    export_parser.add_argument(
        "--readme",
        nargs="?",
        const=DEFAULTS["readme"].name,
        metavar="PATH",
        help=(
            f"write the block between the roadkeep markers in this file "
            f"(default {DEFAULTS['readme'].name})"
        ),
    )
    export_parser.add_argument(
        "--site",
        nargs="?",
        const=DEFAULTS["site"].name,
        metavar="PATH",
        help=(
            f"the same projection as HTML, between the same two markers "
            f"(default {DEFAULTS['site'].name})"
        ),
    )
    export_parser.add_argument(
        "--contents",
        action="store_true",
        help=(
            "refresh the table of contents inside this project's rationale file, between the "
            "same two markers: every row is a heading that file already carries, so a `ship` "
            "that drops a section leaves the list wrong until this runs. Takes no path — the "
            "target is `[files]`' own"
        ),
    )
    export_parser.add_argument(
        "--json", action="store_true", help="the payload a site build reads"
    )
    export_parser.set_defaults(handler=_export)
    # `--json` is a subject and a destination is a write, so asking for both asks two
    # questions (RK466). `--readme` and `--site` are not that shape — they are two
    # destinations of one projection and compose, which RK39 asked for, so they are one
    # group: the whole reason :class:`Answer` holds a group rather than a flag.
    answers(
        export_parser,
        ("json", "the projection printed"),
        (("readme", "site"), "the projection written into a file"),
    )

    gaps_parser = subcommands.add_parser(
        "gaps",
        help="ids in neither file, resolved against the commit that removed them",
        description=(
            "Every id below the highest that no line carries. Each resolves to the commit "
            "whose message holds the decision, to 'never carried' when a complete history "
            "mentions it nowhere, or to 'unresolvable' when there is no history to search "
            "— three different answers from 'retired', none of them a weaker one."
        ),
    )
    gaps_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    gaps_parser.set_defaults(handler=_gaps, reads_only=True)

    anchors_parser = subcommands.add_parser(
        "anchors",
        help="which outline addresses this project has ever declared, live or retired",
        description=(
            "Read the anchors out of every declared prose file and out of its diffs: live "
            "ones a heading declares now, and retired ones a ship deleted while every entry "
            "citing them stayed. An address is spent once a heading used it (RK4's rule for "
            "ids), so this is the read that says which number a reopened family may take — "
            "and which top-level is free, which is what a reused block needs."
        ),
    )
    anchors_parser.add_argument(
        "--family",
        default="",
        metavar="ANCHOR",
        help="only this subtree, e.g. XXXVII — omitted, one row per top-level family",
    )
    anchors_parser.add_argument(
        "--block",
        default="",
        metavar="LABEL",
        help=(
            "the subtree this block's prose already lives under, e.g. Q — the address a "
            "caller knows, since a prose file under an outline declares no block heading; "
            "refused with --family, and names both where a block spans two families"
        ),
    )
    anchors_parser.add_argument(
        "--role",
        default="",
        help=(
            "list only this prose file's addresses (default: every declared one) — the "
            "free top-level is per namespace, so it stays the project's where no [refs] "
            "declares one and is that file's own where one does"
        ),
    )
    anchors_parser.add_argument(
        "--next",
        dest="only_next",
        action="store_true",
        help=(
            "the free address alone, without the listing of spent ones — the `next-id` of "
            "anchors, and the read an `add --ref` makes every time"
        ),
    )
    anchors_parser.add_argument(
        "--claims",
        action="store_true",
        help=(
            "only the addresses whose ownership is not the ordinary one: a heading binding "
            "nobody, and one binding a task no open line claims — the audit, over every "
            "family at once, since the rows it leaves out are the ones nobody reads"
        ),
    )
    anchors_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    anchors_parser.set_defaults(handler=_anchors, reads_only=True)
    # Two subjects, as `budget`'s four are (RK466): `--next` returned before the `--claims`
    # branch was reached, so a caller asking for the audit and the free address read the
    # address alone with nothing said about the other.
    answers(
        anchors_parser, ("only_next", "the free address"), ("claims", "the ownership audit")
    )

    deps_parser = subcommands.add_parser(
        "deps",
        help="resolve one task's deps, naming the ones nothing can resolve",
        description=(
            "Resolve each dep against the roadmap and the changelog. A dep nothing now "
            "open will satisfy is reported as unresolvable rather than open — work "
            "outside the backlog, a task that retired, and a block label with nothing "
            "filed under it."
        ),
    )
    deps_parser.add_argument("id", help="the task to resolve, e.g. RK5")
    deps_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    deps_parser.set_defaults(handler=_deps, reads_only=True)

    origin_parser = subcommands.add_parser(
        "origin",
        help="the commits that proposed and shipped a task, with the reasoning",
        description=(
            "Resolve a task's history from git. The pointer is derived, never stored: "
            "a hash written into the ledger would be rewritten by the first squash or "
            "amend, and a dead hash reads exactly like a live one. A leading § asks the "
            "same question of a rationale anchor instead — the dangling cross-reference a "
            "ship leaves in somebody else's prose, which no file records the answer to."
        ),
    )
    origin_parser.add_argument(
        "id", help="the task to look up, e.g. RK1 — or §<anchor>, as the prose spells it"
    )
    origin_parser.add_argument(
        "--why",
        action="store_true",
        help="print the shipping commit's full message — the rationale the ledger drops",
    )
    origin_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    origin_parser.set_defaults(handler=_origin, reads_only=True)

    weight_parser = subcommands.add_parser(
        "weight",
        help="what comparable tasks cost, derived from the commits that shipped them",
        description=(
            "What a comparable task cost, so granularity is a query instead of a feel: a "
            "block whose last comparables shipped at 800+ lines is a block where the next "
            "line is probably two lines. Derived from the commit that wrote each ledger "
            "entry, so nothing stores it and `git show` refutes it. Two axes and no score — "
            "median to p90 lines vary 2.7× here and files, which is what an agent holds in "
            "context, 1.4×. An entry whose commit wrote several is named and left out "
            "rather than given a share of it, a divided cost being one no commit contains. "
            "This ranks nothing: every tier of `pick` is a fact, and a cheapness tier would "
            "defer the architectural tasks, which is where the leverage is."
        ),
    )
    weight_parser.add_argument("--block", help="only this block's comparables, e.g. C")
    weight_parser.add_argument(
        "--records",
        action="store_true",
        help=(
            "every weighed entry, which the percentiles summarise: the evidence for the "
            "figure, wanted when you dispute it and not when you are sizing a line (RK264)"
        ),
    )
    weight_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    weight_parser.set_defaults(handler=_weight, reads_only=True)

    remaining_parser = subcommands.add_parser(
        "remaining",
        help="how many sites a task's own declared query still matches",
        description=(
            "The mirror of `weight`, and derived the same way (RK492): that one says what a "
            "comparable task cost, from the commits that shipped it, and this says what one "
            "has left, from the repository as it is now. A migration declares the query in "
            "its rationale section — a fenced `roadkeep-remaining` block, one `<pathspec> :: "
            "<regex>` per line — and this runs it. Nothing is stored, so nothing goes stale: "
            "the first commit that closes a site changes the answer, which a number written "
            "onto a line could not. It is a count and never a verdict — the pattern is the "
            "author's, so a query answering 0 says the pattern stopped matching, and whether "
            "that is the work being done is a judgement this tool does not make."
        ),
    )
    remaining_parser.add_argument("id", help="the task whose design declares the query, e.g. RK12")
    remaining_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    remaining_parser.set_defaults(handler=_remaining, reads_only=True)

    report_parser = subcommands.add_parser(
        "report",
        help="capture a defect in this tool, with what the failing session knew",
        description=(
            "Re-run the command that failed, in this process, and emit what identifies the "
            "defect: the argv, the exit code, the engine that answered, this project's "
            "roadkeep.toml, the line the engine objected to and any traceback. The two "
            "facts a machine cannot supply are arguments and are refused here against this "
            "tool's own schema, so a report arrives inside the limits the backlog it is "
            "destined for enforces. Nothing is sent: the capture is printed, and delivery "
            "is a separate decision."
        ),
    )
    report_parser.add_argument(
        "--symptom", required=True, help="what does not work — a phrase, never a fix"
    )
    report_parser.add_argument(
        "--why", required=True, help="one sentence, ending in a stop: why it matters"
    )
    report_parser.add_argument(
        "--block",
        default="F",
        help="the block of roadkeep's own backlog this belongs under (default: F)",
    )
    report_parser.add_argument(
        "--without",
        dest="without",
        action="append",
        default=[],
        metavar="PART",
        choices=PARTS,
        help=(
            "drop one part of the capture, repeatable: what a private repository must not "
            "publish is deleted by name, never scrubbed by a filter"
        ),
    )
    report_parser.add_argument(
        "--issue",
        action="store_true",
        help=(
            "print the tracker body on stdout and the command that files it on stderr; "
            "nothing is sent, and the destination is [report] upstream"
        ),
    )
    report_parser.add_argument(
        "--to",
        metavar="OWNER/REPO",
        help="file against this repository instead of the configured upstream",
    )
    report_parser.add_argument(
        "--embed",
        action="store_true",
        help=(
            "carry the governed files this project declares, so the capture can be replayed "
            "without this repository — a test somewhere else, and files leaving here"
        ),
    )
    report_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    report_parser.add_argument(
        "command_argv",
        nargs=argparse.REMAINDER,
        metavar="-- COMMAND",
        help="the roadkeep command that failed, after a bare --, without the program name",
    )
    report_parser.set_defaults(handler=_report, tolerates_config_error=True, reads_only=True)

    replay_parser = subcommands.add_parser(
        "replay",
        help="re-run a stored capture against the tree that is here now",
        description=(
            "Stage the capture's own configuration and file in a scratch directory, run "
            "the argv it recorded, and answer whether the defect still reproduces. Nothing "
            "from the reporting project is needed: a capture that was never made replayable "
            "says which part it lacks instead of being staged from a guess. Exits 1 when "
            "the answer differs from the `reproduces` the file records — which is what "
            "makes a corpus of field reports a gate rather than a folder."
        ),
    )
    replay_parser.add_argument("path", help="a capture written by `report --json`")
    replay_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    replay_parser.set_defaults(handler=_replay, tolerates_config_error=True, reads_only=True)

    capture_parser = subcommands.add_parser(
        "capture",
        help="what became of a capture already on disk",
        description=(
            "The third of the capture pair's family (RK1142). `report` writes one and "
            "`replay` re-runs it; this says what happened to one that is already there. A "
            "group with one action because it is where the retention `keep` leaves "
            "deliberately unsolved goes next — rotation, an age limit, a dedup by argv."
        ),
    )
    capture_actions = capture_parser.add_subparsers(dest="action", required=True)
    capture_filed = capture_actions.add_parser(
        "filed",
        help="record which task a kept capture was filed as",
        description=(
            "Write into the capture the id it was filed as, so the row `stats` counts is "
            "cleared by a fact in the artefact rather than by a symptom that matches "
            "(RK1141). `add --capture` does this for a capture being filed now; this is the "
            "door for one already on disk, and it is the whole of what RK1142 was: clearing "
            "this repository's own row took a `python -c`, which is what L5 exists against. "
            "Refused where no governed file holds the id — a stamp naming nothing is a link "
            "to nothing — and where the path is not a capture this tool wrote. An id "
            "**qualified by a repository** is the exception (RK1160): a defect in roadkeep is "
            "filed in roadkeep's backlog, so no local file will ever hold that id, and both "
            "readers left a row nothing could clear."
        ),
    )
    capture_filed.add_argument("path", help="a capture under .roadkeep/reports/")
    capture_filed.add_argument(
        "--as",
        dest="task_id",
        required=True,
        metavar="ID",
        help=(
            "the task it was filed as, e.g. RK1138 — refused unless a governed file holds it, "
            "or `owner/repo#ID` for one filed in another backlog this project cannot read"
        ),
    )
    capture_filed.add_argument("--json", action="store_true", help=_JSON_HELP)
    capture_filed.set_defaults(handler=_capture_filed)

    refs_parser = subcommands.add_parser(
        "refs",
        help="declare the namespace a prose file's outline lives in, carrying its citations",
        description=(
            "Write `[refs] <role>` and re-address that file's own citations in the same "
            "transaction (RK1168). Declaring the key alone re-addresses every heading at once "
            "and carries none of the prose citing them: measured on one adoption, 7 citations "
            "dangled and 21 kept resolving into the other prose file's section of the same "
            "address, where nothing reports them. Both writes land or neither does. Only a "
            "declaration: a role that already has a namespace is a re-addressing, whose "
            "citations carry the old prefix and whose answer is a different transaction."
        ),
    )
    refs_parser.add_argument("role", help="the prose role, e.g. strategy")
    refs_parser.add_argument(
        "--as",
        dest="namespace",
        required=True,
        metavar="NS",
        help="the namespace, e.g. S — the letters before the colon of an address like S:I.2",
    )
    refs_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    refs_parser.set_defaults(handler=_refs)

    init_parser = subcommands.add_parser(
        "init",
        help="scaffold roadkeep.toml and the files it declares",
        description=(
            "Write the configuration and the three governed files, or write nothing. The "
            "config is rendered from the schema's own defaults, so a scaffold cannot "
            "declare a format the tool does not implement. No starter task and no prose: "
            "a title, the blocks you name, and where the non-goals go."
        ),
    )
    init_parser.add_argument(
        "--prefix",
        action="append",
        help=(
            "the id prefix, uppercase alphanumeric (default: RK). Repeatable for a "
            "backlog numbered by track; the first is what `add` mints under"
        ),
    )
    init_parser.add_argument(
        "--block",
        action="append",
        dest="blocks",
        metavar="LABEL",
        help=(
            "a block heading, repeatable: 'A' or 'A — The model'. A task is filed "
            "under a heading and a write never invents one (default: A)"
        ),
    )
    init_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    init_parser.set_defaults(handler=_init)

    adopt_parser = subcommands.add_parser(
        "adopt",
        help="what an existing backlog would have to change to pass",
        description=(
            "Run the schema over a backlog this tool does not own yet and report the "
            "delta: what parses, what conforms, the longest field against its limit, the "
            "markers to declare. Writes nothing and never fails — an estimate that "
            "exits 1 is a gate, and the point is to take it before the commitment."
        ),
    )
    adopt_parser.add_argument("path", help="the file to measure, e.g. docs/ROADMAP.md")
    adopt_parser.add_argument(
        "--prefix",
        action="append",
        help=(
            "read the ids under this prefix, repeatable for a backlog numbered by "
            "track; without it the project's own is used, or the one the file's ids "
            "already spell — never all of them, which is a judgement and not a count"
        ),
    )
    adopt_parser.add_argument(
        "--ref-scheme",
        dest="ref_scheme",
        choices=("id", "outline"),
        help=(
            "measure the pointers under this scheme: 'outline' asks what adopting the "
            "tool costs, 'id' what adopting it and renumbering the outline costs"
        ),
    )
    adopt_parser.add_argument(
        "--ledger",
        action="store_true",
        help="measure it as a changelog: shipped marker, no deps field, no pointer",
    )
    adopt_parser.add_argument(
        "--sections",
        action="store_true",
        help=(
            "measure it as a rationale file: sections against `section`, and the width "
            "its prose is already wrapped to — the two limits an adopter has to declare"
        ),
    )
    adopt_parser.add_argument(
        "--with",
        dest="alongside",
        metavar="PATH",
        action="append",
        default=[],
        help=(
            "another prose file an address could be doubled across, repeatable — the one "
            "measure here that is about a set of files rather than this one; requires "
            "--sections, and never inferred from the directory"
        ),
    )
    adopt_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # Read-only, which RK18 has been true of since this verb existed and nothing declared:
    # `adopt` measures a file and exits 0, writing nothing anywhere. Undeclared it took the
    # write lock for a run that cannot conflict with one, and — since RK1147 published a door
    # that reruns it — said `writes: true` in a payload about a command that writes nothing.
    adopt_parser.set_defaults(handler=_adopt, reads_only=True)

    install_parser = subcommands.add_parser(
        "install",
        help="wire this project to the checkout answering, the way the plugin would",
        description=(
            "Write the surfaces the plugin ships, for a project that runs roadkeep from a "
            "checkout instead: the server, the guard on its three hook events, and the "
            "skill that says which command to call — plus the CI workflow when the "
            "repository already has one. Every byte is translated from what the plugin "
            "carries, the launcher's path being the only substituted fact, so the skill "
            "cannot drift from the file it was copied from. The skill is refreshed on "
            "every run; the declarations keep everything they hold that is not this "
            "project's entry; the workflow is written once and then yours."
        ),
    )
    install_parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "write nothing and exit 1 on anything that would change: the gate that keeps "
            "the copied skill in step, for a CI job or a pre-commit hook"
        ),
    )
    install_parser.add_argument(
        "--source",
        metavar="PATH",
        help=(
            "the roadkeep checkout to wire in (default: the one this command is running "
            "from, which is the one whose hook and tools the project would get)"
        ),
    )
    install_parser.add_argument(
        "--register-merge",
        action="store_true",
        help=(
            "wire the merge driver too — the `.gitattributes` half of `merge --register`, "
            "with the `git config` line printed for you to run: a flag and not a default, "
            "because it is configuration and the other half is outside these files"
        ),
    )
    install_parser.add_argument(
        "--committed",
        action="store_true",
        help=(
            "wire a launcher committed to this repository instead of a path to the checkout, "
            "so the guard reaches an environment that installs no plugin and clones no "
            "checkout — Claude Code on the web. It defers where the harness has the plugin "
            "wired for this project, and never blocks a turn"
        ),
    )
    install_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    install_parser.set_defaults(handler=_install)

    engines_parser = subcommands.add_parser(
        "engines",
        help="which copies of roadkeep write, judge and gate this project",
        description=(
            "An adopting project wires three: the plugin its hook and skill run, the action "
            "its workflow gates on, and whatever `roadkeep` the caller invokes. They are "
            "allowed to differ — a cache may lag a checkout — and what is not survivable is "
            "not being able to say which one answered. Exits 1 where the two that state a "
            "version state different ones, so a session can ask this and act on it."
        ),
    )
    engines_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    # A read, and the exit code is its verdict rather than a fault (RK271): the three lines
    # above it have already said everything, and `/plugin update` is the move.
    engines_parser.set_defaults(handler=_engines, reads_only=True)

    uninstall_parser = subcommands.add_parser(
        "uninstall",
        help="take this project's entries back out of the four surfaces install wrote",
        description=(
            "Un-wire a project that ran roadkeep from a checkout — moving to the plugin, or "
            "off the tool entirely (RK138). The inverse of `install` under the same two "
            "rules: the declarations keep every entry that is not this project's, and a "
            "file that is not a JSON object is refused rather than rewritten. A file left "
            "holding nothing but what `install` wrote is deleted, because that is the state "
            "it was created from. It reads no checkout — the wiring is recognised by the "
            "server's name and the launcher a hook runs — so a project can be un-wired "
            "after the tree it pointed at is gone. The CI workflow stays: that gate calls "
            "the published action and not the checkout."
        ),
    )
    uninstall_parser.add_argument(
        "--check",
        action="store_true",
        help=(
            "take nothing out and exit 1 while anything is still wired: the same tense "
            "`install --check` reports in, on the other direction"
        ),
    )
    uninstall_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    uninstall_parser.set_defaults(handler=_uninstall)

    mcp_parser = subcommands.add_parser(
        "mcp",
        help="serve add, ship, pick and lint as MCP tools over stdio",
        description=(
            "Speak JSON-RPC on stdin and stdout so the fields arrive as a schema the "
            "client validates instead of flag names an agent types from memory (RK24). "
            "Every tool is dispatched through this same parser, so the refusal is the one "
            "a terminal prints. Not for a human to call: a session's client starts it."
        ),
    )
    # Same reason as `guard`: the process is started once for a whole session, so refusing
    # to start on a broken `roadkeep.toml` would take the tools away exactly when the gate
    # is what the project needs. `tools/list` describes the defaults and the first call
    # reports the error.
    mcp_parser.set_defaults(handler=_mcp, tolerates_config_error=True, reads_only=True)

    return parser






def _verb_reached(parser: argparse.ArgumentParser, argv: Sequence[str]):
    """The deepest subparser this argv named, and its path — `('ship',)`, `('non-goal',
    'list')` (RK1026).

    Read by walking the tree the way argparse does rather than by re-listing the verbs: the
    parser is the authority on what a command is, and a second table would answer about a
    surface that has moved. `-C <path>` is the one option before the verb that consumes what
    follows it, in both spellings, which is `_crossed`'s rule and the same reason for it.
    """
    reached, path, skipping, opened = parser, [], False, len(argv)
    for index, token in enumerate(argv):
        if skipping:
            skipping = False
            continue
        if token.startswith("-"):
            skipping = token in _VALUED
            continue
        choices = next(
            (
                action.choices
                for action in reached._actions
                if isinstance(action, argparse._SubParsersAction)
            ),
            None,
        )
        if not choices or token not in choices:
            break
        opened = min(opened, index)
        reached, _ = choices[token], path.append(token)
    return reached, tuple(path), opened


def _options(parser: argparse.ArgumentParser) -> tuple[str, ...]:
    """Every long option one verb declares, in the order its parser does — `--help` aside."""
    return tuple(
        option
        for action in parser._actions
        for option in action.option_strings
        if option.startswith("--") and option != "--help"
    )


def _first(argv: Sequence[str], token: str) -> int | None:
    """Where a token was typed, or None — `--flag=value` included, which argv splits."""
    for index, one in enumerate(argv):
        if one == token or one.startswith(f"{token}="):
            return index
    return None


def _unrecognised(
    parser: argparse.ArgumentParser, argv: Sequence[str], extra: Sequence[str]
) -> str:
    """The refusal this tool writes for a flag its own parser does not declare (RK1026).

    `ship RK1 --note "…"` used to print argparse's usage line, the full list of thirty-odd
    verbs, `unrecognized arguments:` and then **the entire rejected value** — often a
    paragraph meant for `--why`, burying the one line that matters under text the caller had
    just typed. The verb was right; the flag was wrong; nothing on screen said so.

    So the answer is the verb's **own** surface, which is short, rather than the tool's,
    which is not, and the option token alone, never its value. A near miss is named first
    where `difflib` finds one — and where it does not, which is the common case (`--note`
    against `--why` is no edit-distance hit), the list is the whole answer.

    A stray positional keeps its own sentence: `show RK1 RK2` is one argument too many, and
    naming the flags of a verb that takes an id would be advice about a mistake nobody made.

    **Which surface answers is decided by where the flag was typed** (RK1032). A flag before
    the verb is the top level's — `roadkeep --vers lint` is somebody reaching for
    `--version`, and answering with `lint`'s options would send them to a `--help` that has
    none of what they wanted.
    """
    reached, path, opened = _verb_reached(parser, argv)
    flags = [token for token in extra if token.startswith("-")]
    if flags and (found := _first(argv, flags[0])) is not None and found < opened:
        reached, path = parser, ()
    # The name and the command are two things: the top level is called `roadkeep` in a
    # sentence and reached as no word at all, so one string for both would print
    # `roadkeep roadkeep --help` — a door that opens nothing.
    verb = " ".join(path) or "roadkeep"
    door = f"{invocation()} {' '.join(path)}".rstrip()
    if not flags:
        loose = ", ".join(repr(token) for token in extra)
        return (
            f"roadkeep: `{verb}` takes no further argument, and got {loose}: "
            f"`{door} --help` is what it does take"
        )
    declared = _options(reached)
    near = difflib.get_close_matches(flags[0], declared, n=1, cutoff=_A_TYPO)
    guess = f" — did you mean `{near[0]}`?" if near else ""
    takes = ", ".join(declared) or "no options of its own"
    return (
        f"roadkeep: `{verb}` declares no {flags[0]}{guess}\n"
        f"  takes    {takes}\n"
        f"  see      `{door} --help`"
    )


def _crossed(argv: Sequence[str]) -> str | None:
    """The other surface's name for the verb this argv asked for, if that is what it is (RK353).

    Read from :func:`~roadkeep.serving.spelled`, which is the tool table's answer: the parser is
    the authority on what a *command* is and the table is the authority on what a **tool** is
    called, so this asks rather than carrying a second mapping that could disagree with either.

    The first token that is not an option, and nothing after it: the verb is the first positional
    argument, and scanning further would read a `--why` somebody wrote about `scope` as the
    command they typed. `-C <path>` is the one option before the verb that consumes what follows
    it, in both spellings and in the `=` form, which needs no skip at all.
    """
    skipping = False
    for token in argv:
        if skipping:
            skipping = False
            continue
        if token.startswith("-"):
            skipping = token in _VALUED
            continue
        line = spelled(token)
        if line is None or line == token:
            # Silent where the two surfaces agree, which is most of them: `add` is `add`, so a
            # refusal about a missing `--block` would otherwise be told the verb it already used.
            return None
        return (
            f"roadkeep: `{token}` is what this tool publishes that verb as over MCP; at this "
            f"CLI the same act is `{invocation()} {line}`, which takes the arguments you typed."
        )
    return None


def main(argv: Sequence[str] | None = None) -> int:
    # Before anything is parsed, and in the module that owns the flag: a section's prose
    # arrives on a pipe (RK9), the governed files are UTF-8, and every reader of what stdin
    # allowed is four frames down a handler. See :func:`~roadkeep.verbs.reading.harden`.
    harden()
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    try:
        # `parse_known_args` and not `parse_args`, so the one refusal argparse used to write
        # is one this tool writes (RK1026). Every other parse failure — a missing required
        # argument, a verb that is not a verb — still raises below, where argparse's message
        # is about the thing the caller got wrong and not about thirty verbs they did not.
        args, extra = parser.parse_known_args(argv)
        if extra:
            print(_unrecognised(parser, argv, extra), file=sys.stderr)
            print(offer(argv), file=sys.stderr)
            return EXIT_USAGE
    except SystemExit as exit_:
        # argparse refuses before a handler exists, and its exit 2 is one of the three
        # places RK86 names. The argv is all this knows, and all the offer needs.
        if exit_.code:
            crossed = _crossed(argv)
            if crossed is not None:
                print(crossed, file=sys.stderr)
            print(offer(argv), file=sys.stderr)
        raise
    try:
        config = Config.discover(args.directory)
    except (ConfigError, tomllib.TOMLDecodeError, OSError) as error:
        # A TOML *syntax* error never reached `ConfigError`, so the commands declared to
        # survive a broken config did not survive the way it is most often broken — and
        # `report`, whose whole purpose is the session where something is wrong, crashed
        # on the file it was about to carry as evidence.
        if not getattr(args, "tolerates_config_error", False):
            # And which build read it (RK1150): over MCP that clause has been on this refusal
            # since RK155, and at a terminal the same message named the file, the key and an
            # allowed set that is *this* version's — with no way to tell a typo from a config a
            # newer roadkeep wrote. One spelling for both surfaces, so they cannot drift.
            print(f"roadkeep: {error}{read_by()}", file=sys.stderr)
            return EXIT_USAGE
        # `guard` (RK22) is the one command that has to survive a broken config: it runs
        # before every write in the session, so failing here would turn one typo in
        # `roadkeep.toml` into a repository nobody can edit. It resolves its own config
        # from the payload anyway — one hook process serves every project a session sees.
        config = Config.default(args.directory)
    # Recorded here because this is the one surface that has one: a refusal that computed the
    # address the caller was missing can then offer the same call with it filled in, instead of a
    # sentence to read, extract and retype (RK1149). After `discover`, so a run that never reached
    # a project leaves the slot as the served path expects to find it — empty.
    invoked(argv)
    faulted = False
    try:
        code = dispatch(config, args)
    except LockBusy as busy:
        print(f"roadkeep: {busy}", file=sys.stderr)
        code = EXIT_GATE
    except Exception:
        # A traceback that reaches a terminal raw is a session that ends, and RK86's whole
        # subject is what an agent does next. Printed, then closed with the offer, then
        # answered with an exit code — 1 and not 2, because nothing about the caller's
        # input is what has to change.
        traceback.print_exc()
        code = EXIT_GATE
        # The one thing the exit code cannot say afterwards: this 1 is the tool falling over
        # and not the verdict a read was asked for, which is the difference RK271 turns on.
        faulted = True
    if code != EXIT_OK:
        _may_offer(argv, args, code, faulted=faulted)
    return code


def dispatch(config: Config, args: argparse.Namespace) -> int:
    """Run one command's handler, under the write lock unless its parser only reads (RK117).

    Here and not inside :func:`main`, because the MCP server dispatches the same parsed
    args in-process and never goes through `main` (RK24) — which is the write path an agent
    actually uses, so a lock only `main` took would be a lock the defect walks around.

    Every command writes unless its parser said otherwise. The default is the locked one
    because that is the safe way to be wrong: a query serialised against a write costs
    milliseconds, and a write that is not serialised is two lines with one id.

    A read that *can* write says which flag makes it one (RK167). Three commands do —
    `pick --claim`, `brief --claim`, `claims --prune` — and until they declared it, each
    arranged its own lock somewhere else while `reads_only=True` described their default flags
    rather than the command. The decision stays here, where the one rule is; what the flag's
    own writer still keeps is a re-entrant lock of its own, because indivisibility is a promise
    to *every* caller and not only to this dispatcher (RK117).
    """
    # One question per call, before either branch (RK489): a verb asked two answers one of
    # them for, and the write lock is the wrong place to discover it.
    refused = _one_answer(args)
    if refused is not None:
        return refused
    # Which arguments read a pipe is the parser's claim, resolved once (RK1176). Here for
    # `_one_answer`'s reason: a handler resolving its own is a handler that can be written
    # without one, which is exactly what happened — `ship --superseded-design -` published the
    # dash, and `--why - --superseded-design -` was not refused although the refusal existed.
    refused = _read_prose(args)
    if refused is not None:
        return refused
    if _only_reads(args):
        return args.handler(config, args)
    with exclusive(config.root):
        code = args.handler(config, args)
        # Still under the lock, and after the handler rather than before: what is recorded
        # is the bytes a verb left, so a later turn can say that bytes which are not these
        # arrived some other way (RK175). A refusal wrote nothing and re-records the same
        # digests, which is the right answer and not a special case.
        attest(config)
        return code


def _only_reads(args: argparse.Namespace) -> bool:
    """Whether this argv is the query its parser declared, or the write a flag turned it into.

    Read off `args` and not from a list here, so the answer comes from the parser that already
    declares it — and a `writes_when` naming an argument that parser does not accept is a test
    failure rather than a lock silently not taken (`tests/test_locking.py`).

    One argument or several (RK307): `claim` writes on either of two, and a declaration that
    could only name one would have left the second taking no lock at all — the failure this
    mechanism exists to make impossible, arriving through the one shape it could not state.
    """
    if not getattr(args, "reads_only", False):
        return False
    return not any(getattr(args, flag, False) for flag in writes_when(args))


def _reaches(args: argparse.Namespace, one: Prose) -> bool:
    """Whether this argv sends that argument to the pipe (RK1176).

    :meth:`Prose.reached_by` asks the same question of a tool's arguments mapping, where an
    argument nobody set is *absent*; on a namespace every dest exists and `None` is how absence
    arrives, so the reading is spelled here rather than bent into that one.
    """
    if one.gated_by and getattr(args, one.gated_by, None) is None:
        return False
    if one.unless and getattr(args, one.unless, None) is not None:
        return False
    value = getattr(args, one.dest, None)
    return one.omitted if value is None else value == one.sentinel


def _spelled(one: Prose) -> str:
    """A declared prose argument as the CLI documents it — a refusal names what was typed."""
    return f"--{one.dest.replace('_', '-')}"


def _read_prose(args: argparse.Namespace) -> int | None:
    """Resolve every prose argument this argv sent to the pipe, or refuse (RK1176).

    ``None`` where nothing asked for stdin, which is every call to a verb that declares no
    prose. Run from :func:`dispatch`, so one pass answers for both surfaces and no handler
    carries a copy — the shape `_one_answer` and `_only_reads` already have.

    **The refusal is asked here and can no longer be skipped.** `_one_pipe` existed and was
    consulted in one handler, so `ship --why - --superseded-design -` sent two arguments to one
    stream and the second kept its dash: a refusal that is documented and not asked is worse
    than none, because the documentation promises it.

    Only the sentinel, and never the *omitted* argument. Whether a verb with no value at all
    should block on a pipe is that verb's own question — `section add` reads, `section amend`
    refuses — and answering it here would turn `Prose.omitted` into a rule about arguments the
    caller never mentioned.
    """
    declared: tuple[Prose, ...] = getattr(args, "reads_stdin", ()) or ()
    # The clash first and over *every* argument that reaches the pipe, including one reaching it
    # by being omitted: resolving the sentinel first is what made `add --why - --section X` stop
    # being refused, because by the time the handler looked, `--why` no longer held a dash.
    reaching = [one for one in declared if _reaches(args, one)]
    if len(reaching) > 1:
        clash = _one_pipe(*[(_spelled(one), True) for one in reaching])
        print(f"roadkeep: {clash}", file=sys.stderr)
        return EXIT_USAGE
    asked = [one for one in declared if getattr(args, one.dest, None) == one.sentinel]
    if not asked:
        return None
    if len(asked) > 1:
        # Spelled as the CLI documents them, because that is what the caller typed: a refusal
        # naming `superseded_design` is about a flag nobody passed.
        clash = _one_pipe(*[(_spelled(one), True) for one in asked])
        print(f"roadkeep: {clash}", file=sys.stderr)
        return EXIT_USAGE
    (one,) = asked
    try:
        setattr(args, one.dest, _piped(getattr(args, one.dest)))
    except (OSError, UnicodeDecodeError, ValueError) as error:
        # The same codes the handlers gave this read: prose that is not UTF-8 is bad input, and
        # a stream this tool could not harden says so in the words RK455 composed for it.
        print(f"roadkeep: {error}", file=sys.stderr)
        return EXIT_USAGE
    return None


def _one_answer(args: argparse.Namespace) -> int | None:
    """Refuse a call that asked two questions, out of what its parser declared (RK489).

    ``None`` where the call is one question, which is every call to a verb that declares
    nothing. Run from :func:`dispatch`, so the refusal is the same on both surfaces and no
    handler carries a copy of it.
    """
    subjects: tuple[Answer, ...] = getattr(args, "subjects", ())
    given = [one for one in subjects if one.given(args)]
    if len(given) > 1:
        print(
            f"roadkeep: one answer per call: {given[0].asked(args)} or "
            f"{given[1].asked(args)}, not both",
            file=sys.stderr,
        )
        return EXIT_USAGE
    asked = given[0] if given else None
    for (flag, option, default), (subject, names, _) in getattr(args, "narrowing", ()):
        if getattr(args, flag, default) == default:
            continue
        if asked is None or not asked.holds(subject):
            # Both halves, because the two states are different mistakes: a subject was named
            # and it is not this flag's, or none was and the flag cannot stand alone.
            beside = (
                f"and {asked.given(args)[0]} is a different subject"
                if asked is not None
                else "so pass it too"
            )
            print(f"roadkeep: {option} narrows {names}, {beside}", file=sys.stderr)
            return EXIT_USAGE
    return None


def _may_offer(
    argv: Sequence[str], args: argparse.Namespace, code: int, *, faulted: bool = False
) -> None:
    """Close a **fault** with the capture command, and a verdict with nothing (RK86, RK271).

    One place and not twenty: every refusal in this file already leaves through an exit
    code, so the affordance rides the contract instead of being remembered at each of them.

    Which is also what made it unable to tell the two apart. `lint` exiting 1 with
    `ref.unresolved 1` has already said everything — the finding names the file, the line and
    the rule, and the next move is `--fix` or an edit — so two further lines saying roadkeep
    itself may be wrong ride the tool's highest-traffic output, where the action and the
    pre-commit hook both live and where there is no session to capture before the end of.

    The split needs no new judgement, which is why it is this one and not a longer exemption
    list: a **verdict** is what a read-only command returns when it found something, and a
    fault is everything else. `_only_reads` is the parsers' own declaration (RK167), so
    `pick --claim` refusing a held line is a write refusal and keeps the offer, and a `lint`
    that *crashed* keeps it too — `faulted` is how that 1 says it was not a verdict.

    A validation refusal keeps the offer either way: that is the case RK86 measured, and the
    one where the limit really might be wrong.
    """
    if args.command in ("report", "guard", "mcp"):
        # `report` offering to report itself is a regress; `guard` and `mcp` answer a
        # protocol, and a sentence on their stderr is read by no agent at all.
        return
    if not faulted and code == EXIT_GATE and _only_reads(args):
        return
    # The report this closes went to stdout and this goes to stderr: unflushed, the offer
    # lands above the findings it is about, and a line out of order is a line misread.
    sys.stdout.flush()
    print(offer(argv), file=sys.stderr)


if __name__ == "__main__":  # pragma: no cover - exercised via the console script
    raise SystemExit(main())
