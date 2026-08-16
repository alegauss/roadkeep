"""The verbs whose subject is a heading or a list, and never a task line (RK494).

The rationale sections a pointer resolves to, the block headings every governed file is
organised by, and the roadmap's two other lists — the non-goals a proposal is checked
against before it is written, and the queue that reorders what `pick` offers.

One module because they share a shape none of the task-line verbs has: each addresses a
place rather than a task, and each writes the same heading into every file that declares one.

**Every write here renders both registers off its own record** (RK1170), so this module no
longer imports `rendering` at all. What is left composing an answer in a door is the three
reads — `section show`, `non-goal list` and `priority list` — which is the rest of that task.
"""

from __future__ import annotations

import argparse
import json
import sys

from roadkeep.blocking import (
    amend_block,
    catalogue,
    drop_block,
    merge_block,
    open_block,
)
from roadkeep.briefing import non_goals
from roadkeep.config import Config
from roadkeep.queueing import (
    add as add_priority,
    declared as declared_queue,
    drop as drop_priority,
    migrate as migrate_priority,
)
from roadkeep.scoping import add as add_non_goal, amend as amend_non_goal, drop as drop_non_goal
from roadkeep.sections import (
    namespaced,
    AmbiguousTitle,
    NoSuchSection,
    Shown,
    add as add_section,
    amend as amend_section,
    amend_untitled,
    drop as drop_section,
    find as find_section,
    move as move_section,
    pointers,
    titled,
)
from roadkeep.serving import Prose
from roadkeep.verbs.declaring import (
    _BODY_FILE,
    _JSON_HELP,
    _PIPE,
    withheld,
)
from roadkeep.verbs.reading import _body_reader, _one_body, _piped
from roadkeep.verbs.refusing import EXIT_OK, EXIT_USAGE, REFUSALS, _refused


def _block_add(config: Config, args: argparse.Namespace) -> int:
    try:
        opened = open_block(
            config, args.label, args.title, after=args.after, organise=args.organise
        )
        wrote = opened.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(opened.payload(config, wrote), indent=2))
    else:
        print(opened.stated(config, wrote))
    return EXIT_OK


def _block_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        closed = drop_block(config, args.label, prose=args.prose)
        wrote = closed.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(closed.payload(config, wrote), indent=2))
    else:
        print(closed.stated(config, wrote))
    return EXIT_OK


def _block_amend(config: Config, args: argparse.Namespace) -> int:
    try:
        retitled = amend_block(config, args.label, args.title)
        wrote = retitled.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(retitled.payload(config, wrote), indent=2))
    else:
        print(retitled.stated(config, wrote))
    return EXIT_OK


def _block_merge(config: Config, args: argparse.Namespace) -> int:
    try:
        merged = merge_block(config, args.label, prose=args.prose)
        wrote = merged.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(merged.payload(config, wrote), indent=2))
    else:
        print(merged.stated(config, wrote))
    return EXIT_OK


def _block_list(config: Config, args: argparse.Namespace) -> int:
    """Print where a task may go, at the moment one is placed (RK1188).

    `non-goal list`'s sibling, and answered the same way: no argument, never refused, and
    the counts are the reader every other query about a block already uses.
    """
    try:
        declared = catalogue(config)
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(declared.payload(config), indent=2))
    else:
        print(declared.stated(config))
    return EXIT_OK


def _section_add(config: Config, args: argparse.Namespace) -> int:
    # stdin by default: a paragraph does not fit comfortably in a shell argument, and a
    # heredoc is how the caller of this tool already passes prose. `--body-file` is the third
    # source (RK381), and the one whose retry costs the corrected field alone.
    clash = _one_body("--body", args.body, args.body_file)
    if clash is not None:
        print(f"roadkeep: {clash}", file=sys.stderr)
        return EXIT_USAGE
    try:
        # Inside the try: a paragraph that is not UTF-8 raises UnicodeDecodeError, which
        # is a ValueError, so it is refused with the exit code every other bad input gets.
        body = _body_reader(args.body, args.body_file)()
        written = add_section(
            config, args.role, args.anchor, args.title, body, level=args.level
        )
        wrote = written.document.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(written.payload(config, wrote), indent=2))
    else:
        print(written.stated(config, wrote))
    return EXIT_OK


def _refs(config: Config, args: argparse.Namespace) -> int:
    """Declare a prose file's namespace and carry its own citations into it (RK1168).

    The transaction the first half of this task made visible: `[refs]` re-addresses every heading
    in a file at once and carried none of the prose citing them, so declaring it created seven
    dangling citations and twenty-one that resolved into the other file — the second population
    being the one nothing reported until `ref.crossed`.

    **The config last.** A prose file this cannot rewrite leaves the key undeclared, which is the
    state the project was already in; a key declared over a file that was not carried is the
    defect. So the order makes the failure land on the side that changes nothing, which is the
    rule `init` keeps one module over about a scaffold's directories.
    """
    try:
        found = namespaced(config, args.role, args.namespace)
        wrote = found.document.save()
        config.source.write_text(found.config_text, encoding="utf-8", newline="")
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(found.payload(config, wrote), indent=2))
    else:
        print(found.stated(config, wrote))
    return EXIT_OK


def _section_amend(config: Config, args: argparse.Namespace) -> int:
    if args.title is None and args.body is None and args.body_file is None:
        # Refused rather than defaulted to stdin: an `amend` with neither field is a
        # command that would block on a pipe nobody meant to open.
        print(
            "roadkeep: nothing to amend: pass --body (or '-' for stdin), --body-file or --title",
            file=sys.stderr,
        )
        return EXIT_USAGE
    clash = _one_body("--body", args.body, args.body_file)
    if clash is not None:
        print(f"roadkeep: {clash}", file=sys.stderr)
        return EXIT_USAGE
    try:
        # Inside the try for `section add`'s reason: prose that is not UTF-8 raises
        # UnicodeDecodeError, which is a ValueError, and is refused with the same code.
        # `None` stays None here and does not become the pipe: a title-only amend leaves
        # the prose alone, which is what `omitted=False` says one file over.
        body = (
            None
            if args.body is None and args.body_file is None
            else _body_reader(args.body, args.body_file)()
        )
        # An anchor first and the heading text second, the order `show` reads in (RK1107): an
        # address the project chose wins, and a `## Table of contents` is reachable by the one
        # name it has. The branch is here rather than inside `amend` because the two writes
        # differ in what they may do — an unanchored section has no owner to bind into its
        # heading, no pointer to move and no word budget measured against it.
        if find_section(config.document(args.role), args.anchor) is None and (
            titled(config.document(args.role), args.anchor) is not None
        ):
            rewritten = amend_untitled(
                config, args.role, args.anchor, body=body, retitle=args.title
            )
        else:
            rewritten = amend_section(
                config, args.role, args.anchor, title=args.title, body=body
            )
        wrote = rewritten.document.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(rewritten.payload(config, wrote, body is not None), indent=2))
    else:
        print(rewritten.stated(config, wrote, body is not None))
    return EXIT_OK


def _section_move(config: Config, args: argparse.Namespace) -> int:
    try:
        moved = move_section(config, args.role, args.anchor, args.to)
        wrote = moved.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(moved.payload(config, wrote), indent=2))
    else:
        print(moved.stated(config, wrote))
    return EXIT_OK


def _section_show(config: Config, args: argparse.Namespace) -> int:
    """One section, at the extent the caller asked for (RK1107, RK1112, RK1118).

    Both registers come off the record (RK1170), and the third stream with them: the prose is
    stdout because an `amend --body-file` is composed from it, so the note saying *why* a body
    came back empty goes to stderr or it ends up in the file.
    """
    try:
        shown = Shown.of(config, args.role, args.anchor, args.own)
    except (KeyError, OSError, AmbiguousTitle) as error:
        return _refused(error)
    except NoSuchSection as error:
        print(f"roadkeep: {error}", file=sys.stderr)
        return EXIT_USAGE

    if args.json:
        print(json.dumps(shown.payload(), indent=2))
        return EXIT_OK
    print(shown.stated(config.schema))
    for note in shown.silence():
        print(note, file=sys.stderr)
    return EXIT_OK


def _section_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        deleted = drop_section(
            config.document(args.role),
            args.anchor,
            claimed=pointers(config),
            where=config.relative(config.path(args.role)),
        )
        wrote = deleted.document.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(deleted.payload(config, wrote), indent=2))
    else:
        print(deleted.stated(config, wrote))
    return EXIT_OK


def _non_goal_add(config: Config, args: argparse.Namespace) -> int:
    try:
        written = add_non_goal(config, lead=args.lead, why=_piped(args.why))
        wrote = written.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(written.payload(config, wrote), indent=2))
    else:
        print(written.stated(config, wrote))
    return EXIT_OK


def _non_goal_amend(config: Config, args: argparse.Namespace) -> int:
    try:
        amended = amend_non_goal(config, args.lead, _piped(args.why))
        wrote = amended.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(amended.payload(config, wrote), indent=2))
    else:
        print(amended.stated(config, wrote))
    return EXIT_OK


def _non_goal_list(config: Config, args: argparse.Namespace) -> int:
    """Print the list at the moment a task is proposed (RK69).

    The same leads `brief` carries, from the same reader and under the same bound (RK68): a
    second projection of the list is a second answer about scope, and the whole point is that
    the constraint an `add` is checked against is the constraint the file states.
    """
    try:
        gathered = non_goals(config, config.document("roadmap"))
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(gathered.payload(config), indent=2))
    else:
        print(gathered.stated(config))
    return EXIT_OK


def _non_goal_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        dropped = drop_non_goal(config, args.lead)
        wrote = dropped.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(dropped.payload(config, wrote), indent=2))
    else:
        print(dropped.stated(config, wrote))
    return EXIT_OK


def _priority_add(config: Config, args: argparse.Namespace) -> int:
    try:
        written = add_priority(config, args.token, after=args.after, first=args.first)
        wrote = written.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(written.payload(config, wrote), indent=2))
    else:
        print(written.stated(config, wrote))
    return EXIT_OK


def _priority_list(config: Config, args: argparse.Namespace) -> int:
    """The order, and which file declared it (RK325).

    Both, always. A project that wrote a section and is still being ordered by its config is
    the state this move exists to make visible, and it is invisible from the tokens alone.
    """
    try:
        queue = declared_queue(config)
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(queue.payload(config), indent=2))
    else:
        print(queue.stated(config))
    return EXIT_OK


def _priority_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        dropped = drop_priority(config, args.token)
        wrote = dropped.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(dropped.payload(config, wrote), indent=2))
    else:
        print(dropped.stated(config, wrote))
    return EXIT_OK


def _priority_migrate(config: Config, args: argparse.Namespace) -> int:
    """Move the config's queue into the roadmap, which is the only door between them (RK427).

    Prints what `lint` will now say, because that is the half a caller would otherwise learn
    from a red run: the section wins from here, so the `priority` line left in `roadkeep.toml`
    becomes `priority.config` — a finding whose remedy is a one-line edit the guard does not
    deny, that file being one this tool does not govern and deliberately does not write.
    """
    try:
        migrated = migrate_priority(config)
        wrote = migrated.save()
    except REFUSALS as error:
        return _refused(error)

    if args.json:
        print(json.dumps(migrated.payload(config, wrote), indent=2))
    else:
        print(migrated.stated(config, wrote))
    return EXIT_OK


def declare_places(subcommands: argparse._SubParsersAction) -> None:
    """This module's verbs, declared where their handlers are (RK1171).

    `build_parser` called forty-nine blocks like these in a row; what it calls now is an index
    over the modules that own them. The move is what RK1169 and RK1170 bought: the flags a verb
    declares, the reasons it withholds and the record it answers with are one file's, so a
    change to any of them is one file's too.

    The order inside is `build_parser`'s own, which is where these blocks sat.
    """
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
        help="say what the blocks are, and declare one no other write will invent for you",
        description=(
            "A block is declared by a heading and by nothing else, so every write refuses "
            "an undeclared one — and the guard denies the hand-edit that would declare it. "
            "Both refusals are right and the pair is a deadlock; this is the key. `list` is "
            "the read the other four assume has happened: which labels exist to file under."
        ),
    )
    block_actions = block_parser.add_subparsers(dest="action", required=True)

    # First of the five, because it is the one called before the other four (RK1188): the
    # question `add --block <x>` asks and nothing answered, which sent the author to grep the
    # file the hook exists to keep hands off.
    block_list = block_actions.add_parser(
        "list",
        help="print every declared block with its title and open count — call it before `add`",
        description=(
            "Where a task may go, at the moment one is placed. `add --block <x>` is the "
            "first flag on the first write of any new task and nothing said what `<x>` "
            "could be: `stats` prints letters and counts and never a title, `list --block` "
            "and `delivered <block>` both demand the letter they cannot enumerate. In file "
            "order, because a reader takes the sequence for the shape of the plan. A label "
            "the roadmap has lost keeps its ledger heading and is named as such — that is "
            "the row an `add` still refuses, and `block add` re-declares it."
        ),
    )
    block_list.add_argument(
        "--json", action="store_true", help="the rows, with every file each label is in"
    )
    block_list.set_defaults(handler=_block_list, reads_only=True)

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

    block_amend = block_actions.add_parser(
        "amend",
        help="give a declared block's heading new words, keeping its label and its work",
        description=(
            "The words on a heading the other three cannot change. `drop` plus `add` was the "
            "repair and it is refused the moment anything is filed under the label, so a "
            "title was write-once from the first `add` on. Narrow: the label is the identity "
            "and does not move, the subtree is untouched, and each file keeps its own level "
            "and separator. Every file that declares the label or none — a title corrected "
            "in one and left in another is the defect this closes."
        ),
    )
    block_amend.add_argument("label", help="the block label, e.g. G")
    block_amend.add_argument("--title", required=True, help="the words it should read")
    block_amend.add_argument("--json", action="store_true", help=_JSON_HELP)
    block_amend.set_defaults(handler=_block_amend)

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

