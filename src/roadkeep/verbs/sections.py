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

from roadkeep.blocking import drop_block, merge_block, open_block
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

