"""The verbs whose subject is a heading or a list, and never a task line (RK494).

The rationale sections a pointer resolves to, the block headings every governed file is
organised by, and the roadmap's two other lists — the non-goals a proposal is checked
against before it is written, and the queue that reorders what `pick` offers.

One module because they share a shape none of the task-line verbs has: each addresses a
place rather than a task, and each writes the same heading into every file that declares one.
"""

from __future__ import annotations

import argparse
import json
import sys

from roadkeep.blocking import drop_block, merge_block, open_block
from roadkeep.briefing import non_goals
from roadkeep.capturing import body
from roadkeep.config import Config
from roadkeep.queueing import (
    add as add_priority,
    declared as declared_queue,
    drop as drop_priority,
    migrate as migrate_priority,
)
from roadkeep.rendering import _counted, _print_cited, _section_json
from roadkeep.scoping import add as add_non_goal, amend as amend_non_goal, drop as drop_non_goal
from roadkeep.sections import (
    AmbiguousTitle,
    add as add_section,
    amend as amend_section,
    amend_untitled,
    drop as drop_section,
    find as find_section,
    heading_of,
    move as move_section,
    nested as nested_sections,
    pointers,
    titled,
    untitled,
)
from roadkeep.verbs.reading import _body_reader, _one_body, _piped, unread_prose
from roadkeep.verbs.refusing import EXIT_OK, EXIT_USAGE, REFUSALS, _refused


def _block_add(config: Config, args: argparse.Namespace) -> int:
    try:
        opened = open_block(
            config, args.label, args.title, after=args.after, organise=args.organise
        )
        opened.save()
    except REFUSALS as error:
        return _refused(error)

    files = {
        role: config.relative(config.path(role)) for role in opened.documents
    }
    if args.json:
        print(
            json.dumps(
                {
                    "label": opened.label,
                    "title": opened.title,
                    # The neighbour as it was asked for, null where it was derived: "after
                    # the last block" and "appended" are the same placement said twice.
                    "after": opened.after,
                    "written": [
                        {
                            "role": role,
                            "file": files[role],
                            "line": opened.placed[role],
                            "rendered": opened.rendered[role],
                        }
                        for role in opened.documents
                    ],
                    # Named, never silent: a file skipped in silence is one the author
                    # discovers was skipped by the next command that refuses on it.
                    "skipped": [
                        {"file": where, "reason": reason}
                        for where, reason in opened.skipped
                    ],
                },
                indent=2,
            )
        )
        return EXIT_OK

    beside = (
        f" (after {config.schema.block_named(opened.after)})" if opened.after else ""
    )
    print(f"{config.schema.block_named(opened.label)} declared{beside}: {opened.title}")
    width = max((len(files[role]) for role in opened.documents), default=0)
    for role in opened.documents:
        print(f"  {files[role]:<{width}}:{opened.placed[role]}  {opened.rendered[role]}")
    for where, reason in opened.skipped:
        print(f"  not      {where}: {reason}")
    return EXIT_OK


def _block_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        closed = drop_block(config, args.label, prose=args.prose)
        closed.save()
    except REFUSALS as error:
        return _refused(error)

    files = {role: config.relative(config.path(role)) for role in closed.documents}
    if args.json:
        print(
            json.dumps(
                {
                    "label": closed.label,
                    "removed": [
                        {
                            "role": role,
                            "file": files[role],
                            # The line it was on and the heading it was, because after this
                            # write no file holds either and the answer is the only record.
                            "line": closed.removed[role],
                            "rendered": closed.rendered[role],
                            # Null where the heading stood over nothing, so a caller reads
                            # "the note went too" off a field rather than off a count (RK237).
                            "note": closed.notes.get(role),
                        }
                        for role in closed.documents
                    ],
                    "skipped": [
                        {"file": where, "reason": reason} for where, reason in closed.skipped
                    ],
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{config.schema.block_named(closed.label)} withdrawn")
    width = max((len(files[role]) for role in closed.documents), default=0)
    for role in closed.documents:
        print(f"  {files[role]:<{width}}:{closed.removed[role]}  {closed.rendered[role]}")
        if role in closed.notes:
            # Said, because this is the one line of the removal that took prose with it and
            # the file no longer holds it to be compared against (RK237).
            print(f"  note     {closed.notes[role]} line(s) of prose taken with the heading")
    for where, reason in closed.skipped:
        print(f"  kept     {where}: {reason}")
    return EXIT_OK


def _block_merge(config: Config, args: argparse.Namespace) -> int:
    try:
        merged = merge_block(config, args.label, prose=args.prose)
        merged.save()
    except REFUSALS as error:
        return _refused(error)

    files = {role: config.relative(config.path(role)) for role in merged.documents}
    if args.json:
        print(
            json.dumps(
                {
                    "label": merged.label,
                    "merged": [
                        {
                            "role": role,
                            "file": files[role],
                            # Where the surviving heading is, the ids that moved under it,
                            # and the headings folded — verbatim, since the file no longer
                            # holds them and this answer is their only record.
                            "kept": merged.kept[role],
                            "moved": list(merged.moved[role]),
                            "folded": list(merged.folded[role]),
                            # Null where a folded heading stood over entries alone (RK237).
                            "note": merged.notes.get(role),
                        }
                        for role in merged.documents
                    ],
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{config.schema.block_named(merged.label)} consolidated")
    width = max((len(files[role]) for role in merged.documents), default=0)
    for role in merged.documents:
        moved = ", ".join(merged.moved[role]) or "nothing"
        print(
            f"  {files[role]:<{width}}:{merged.kept[role]}  "
            f"folded {len(merged.folded[role])}, moved {moved}"
        )
        if role in merged.notes:
            print(f"  note     {merged.notes[role]} line(s) of prose dropped with a heading")
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
        document, section = add_section(
            config, args.role, args.anchor, args.title, body, level=args.level
        )
        document.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path(args.role))
    if args.json:
        print(json.dumps(_section_json(section, where), indent=2))
        return EXIT_OK
    print(
        f"§{section.anchor} → {where}:{section.first}  "
        f"{_counted(section, config.schema_for(args.role).section_max)}"
    )
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
            document, section, changed = amend_untitled(
                config, args.role, args.anchor, body=body, retitle=args.title
            )
        else:
            document, section, changed = amend_section(
                config, args.role, args.anchor, title=args.title, body=body
            )
        document.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path(args.role))
    if args.json:
        print(
            json.dumps(
                {
                    **_section_json(section, where),
                    "changed": list(changed),
                    # The same fact as a field (RK1109): whether this call looked at the prose
                    # at all. `changed: []` says nothing moved and cannot say why, which is the
                    # ambiguity a piped body and a `--title` land in together.
                    "read_body": body is not None,
                },
                indent=2,
            )
        )
        return EXIT_OK
    # An unanchored section is named by its heading and never by a bare sigil (RK1107), and it
    # carries no word count: `section = <n>` is what a *rationale* may spend, and printing a
    # figure beside a limit is claiming the two are the same number — which the file's opening
    # paragraph and its contents table are not measured by. `[budgets]` counts their bytes.
    named = f"§{section.anchor}" if section.anchor else f"'{section.title}'"
    if not changed:
        # RK1109. `unchanged` at exit 0 is the one answer here with nothing in it to read: the
        # changed path lists its fields, so a caller sees `(title)` and knows the prose was left
        # alone, and this path listed nothing at all. A caller who piped the replacement and
        # passed `--title` got a success-shaped message over a paragraph never read.
        aside = "" if body is not None else f" — {unread_prose()}"
        print(f"{named} unchanged: it already reads that way{aside}")
        return EXIT_OK
    counted = (
        f"  {_counted(section, config.schema_for(args.role).section_max)}"
        if section.anchor
        else ""
    )
    print(f"{named} amended  {where}:{section.first}  ({', '.join(changed)}){counted}")
    return EXIT_OK


def _section_move(config: Config, args: argparse.Namespace) -> int:
    try:
        moved = move_section(config, args.role, args.anchor, args.to)
        moved.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path(args.role))
    if args.json:
        print(
            json.dumps(
                {
                    **_section_json(moved.section, where),
                    "from": moved.anchor,
                    "subsections": [
                        {"from": before, "to": after} for before, after in moved.subsections
                    ],
                    "repointed": [{"id": one, "to": a} for one, a in moved.repointed],
                    "kept": [{"id": one, "address": a} for one, a in moved.kept],
                    "cited": [{"address": a, "by": by} for a, by in moved.cited],
                },
                indent=2,
            )
        )
        return EXIT_OK
    print(f"§{moved.anchor} → §{moved.to}  {where}:{moved.section.first}")
    for before, after in moved.subsections:
        print(f"  nested   §{before} → §{after}")
    # Named for `renumber`'s reason (RK97): a pointer is the other end of the address that
    # moved, and the line that changed is the one whose author has to agree it should have.
    for one, address in moved.repointed:
        print(f"  pointer  {one} follows it to §{address}")
    for one, address in moved.kept:
        # The doubling this verb is usually called for: the address still resolves, to the
        # section that stayed, and that is the answer rather than a thing left half done.
        print(f"  kept     {one} still points at §{address}, which the other file declares")
    for address, by in moved.cited:
        print(f"  cited    §{by} names §{address} in its prose — that address has moved")
    return EXIT_OK


def _by_title(document, title: str):
    """The unanchored section this heading text names, or None (RK1107).

    A lookup and not a second reader: :func:`~roadkeep.sections.titled` decides what matches
    and :func:`~roadkeep.sections.untitled` builds the record, so this only joins the two —
    which is what keeps `show` and `amend` reading one answer.
    """
    heading = titled(document, title)
    if heading is None:
        return None
    return next(
        (one for one in untitled(document) if one.first == heading.lineno),
        None,
    )


def _section_show(config: Config, args: argparse.Namespace) -> int:
    try:
        document = config.document(args.role)
        section = find_section(document, args.anchor)
        if section is None:
            # The address is a heading text where it is not an anchor (RK1107), which is the
            # order every reader here needs: an anchor is the project's chosen name and wins,
            # and the fall-through is what makes `section show 'Table of contents'` — the call
            # this task was reported from — an answer instead of a refusal.
            section = _by_title(document, args.anchor)
    except (KeyError, OSError, AmbiguousTitle) as error:
        return _refused(error)
    where = config.relative(config.path(args.role))
    if section is None:
        print(
            f"roadkeep: no §{args.anchor} section in {where}, and no heading reading "
            f"'{args.anchor}' either",
            file=sys.stderr,
        )
        return EXIT_USAGE

    if args.json:
        print(json.dumps({**_section_json(section, where), "body": section.body}, indent=2))
        return EXIT_OK
    print(heading_of(config.schema, section))
    print()
    print(section.body)
    return EXIT_OK


def _section_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        document = config.document(args.role)
        # Read before the drop, because afterwards the headings are gone: what a subtree
        # took is the part of this command's size that the anchor does not state (RK78).
        taken = tuple(child.anchor for child in nested_sections(document, args.anchor))
        document, section, cited = drop_section(
            document,
            args.anchor,
            claimed=pointers(config),
            where=config.relative(config.path(args.role)),
        )
        document.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path(args.role))
    if args.json:
        print(
            json.dumps(
                {**_section_json(section, where), "nested": list(taken), "cited": list(cited)},
                indent=2,
            )
        )
        return EXIT_OK
    print(f"dropped {section} from {where}")
    if taken:
        print(f"  nested   {', '.join(f'§{a}' for a in taken)} went with it")
    _print_cited(cited)
    return EXIT_OK


def _non_goal_add(config: Config, args: argparse.Namespace) -> int:
    try:
        written = add_non_goal(config, lead=args.lead, why=_piped(args.why))
        written.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path("roadmap"))
    if args.json:
        print(
            json.dumps(
                {
                    "lead": written.non_goal.lead,
                    "why": written.non_goal.why,
                    "file": where,
                    "line": written.lineno,
                    "rendered": list(written.rendered),
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{where}:{written.lineno}  {len(written.rendered)} line(s)")
    for line in written.rendered:
        print(f"  {line}")
    # No event line (RK38): the payload a hook reads is an id and its block's open state, and
    # a non-goal has neither — it is the constraint on what a block may hold, not a member.
    return EXIT_OK


def _non_goal_amend(config: Config, args: argparse.Namespace) -> int:
    try:
        amended = amend_non_goal(config, args.lead, _piped(args.why))
        amended.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path("roadmap"))
    if args.json:
        print(
            json.dumps(
                {
                    "lead": amended.non_goal.lead,
                    # Both readings, which is what makes this reviewable as a correction
                    # rather than as a move: the word changed and the bullet did not.
                    "was": amended.before,
                    "now": amended.non_goal.why,
                    "changed": amended.changed,
                    "file": where,
                    "line": amended.lineno,
                    "rendered": list(amended.rendered),
                },
                indent=2,
            )
        )
        return EXIT_OK

    if not amended.changed:
        print(f"{amended.non_goal.lead} unchanged: the bullet already reads that way")
        return EXIT_OK
    print(f"{where}:{amended.lineno}  amended  {len(amended.rendered)} line(s)")
    for line in amended.rendered:
        print(f"  {line}")
    return EXIT_OK


def _non_goal_list(config: Config, args: argparse.Namespace) -> int:
    """Print the list at the moment a task is proposed (RK69).

    The same leads `brief` carries, from the same reader and under the same bound (RK68): a
    second projection of the list is a second answer about scope, and the whole point is that
    the constraint an `add` is checked against is the constraint the file states.
    """
    try:
        document = config.document("roadmap")
    except (KeyError, OSError) as error:
        return _refused(error)

    where = config.relative(config.path("roadmap"))
    gathered = non_goals(config, document)
    if args.json:
        print(
            json.dumps(
                {
                    "file": where,
                    # A project that has not opted in can still be read — `add` is what
                    # `[non_goals]` gates (RK70), and refusing the read too would leave the
                    # scope of two live corpora unaskable.
                    "governed": config.non_goals is not None,
                    "non_goals": list(gathered.leads),
                    "non_goals_elided": gathered.elided,
                },
                indent=2,
            )
        )
        return EXIT_OK

    if not gathered.leads:
        print(f"{where}: no non-goals — nothing here says what may not be proposed")
        return EXIT_OK

    ungoverned = "" if config.non_goals is not None else "  read-only: no [non_goals]"
    print(f"{where}  {len(gathered.leads)} non-goal(s){ungoverned}")
    for lead in gathered.leads:
        # The shape `brief` prints, so the list is recognisable as the same list and not as
        # a second one that happens to agree today.
        print(f"  not      {lead}")
    if gathered.elided:
        print(f"  not      … and {gathered.elided} more under Non-goals")
    return EXIT_OK


def _non_goal_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        dropped = drop_non_goal(config, args.lead)
        dropped.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path("roadmap"))
    span = dropped.non_goal
    if args.json:
        print(
            json.dumps(
                {
                    "lead": span.lead,
                    "why": span.why,
                    "file": where,
                    "removed": [span.first, span.last],
                    "carried": dropped.carried,
                    "rendered": list(dropped.lines),
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{where}:{span.first}-{span.last}  dropped  **{span.lead}**")
    if dropped.carried > 1:
        # Two bullets for one address is `lint`'s non-goal.duplicate, and this call repaired
        # it rather than removing the list's only statement of a constraint.
        print(
            f"  duplicate {dropped.carried} bullets carried this lead: the later one went, "
            f"the first is where the reader already found it"
        )
    return EXIT_OK


def _priority_add(config: Config, args: argparse.Namespace) -> int:
    try:
        written = add_priority(config, args.token, after=args.after, first=args.first)
        written.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path("roadmap"))
    if args.json:
        print(
            json.dumps(
                {
                    "token": written.entry.token,
                    "file": where,
                    "line": written.lineno,
                    # The two a caller cannot read off a line number, and the whole content
                    # of a list whose order is what it says (RK325).
                    "position": written.position,
                    "length": written.length,
                    "rendered": written.entry.raw,
                    # Whether this call also opened the section (RK1014): a caller who asked
                    # to queue a token has had a heading written into a governed file.
                    "opened": written.opened,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{where}:{written.lineno}  queued {written.entry.token}")
    if written.opened:
        # Said, because the caller asked for an entry and got a heading too (RK1014) — the
        # same reason every write here prints what it changed rather than only that it did.
        print(f"  opened   the priority section, above the blocks — the queue is declared now")
    print(f"  order    {written.position} of {written.length}")
    # No event line (RK38): the payload a hook reads is an id and its block's open state, and
    # an entry states neither — the token names work whose line is somewhere else.
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

    where = config.relative(config.path("roadmap"))
    source = config.relative(config.source or config.root)
    if args.json:
        print(
            json.dumps(
                {
                    "declared_in": queue.declared_in or None,
                    "file": where if queue.declared_in == "roadmap" else source,
                    "priority": list(queue.tokens),
                    # Bullets under the heading the format could not read — counted apart
                    # for `non-goal`'s reason: unreadable is not absent.
                    "unread": [
                        {"line": lineno, "raw": raw} for lineno, raw in queue.rejects
                    ],
                },
                indent=2,
            )
        )
        return EXIT_OK

    if not queue.declared_in:
        print(
            f"{where}: no priority queue — add a `## Priority` heading, or declare "
            f"`priority` in {source}; the id order stands either way"
        )
        return EXIT_OK
    named = where if queue.declared_in == "roadmap" else source
    empty = "  empty: the tier is declared and off" if not queue.tokens else ""
    print(f"{named}  {len(queue.tokens)} entr(ies){empty}")
    for place, token in enumerate(queue.tokens, 1):
        print(f"  {place:<8} {token}")
    for lineno, raw in queue.rejects:
        print(f"  unread   {where}:{lineno}  {raw}")
    return EXIT_OK


def _priority_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        dropped = drop_priority(config, args.token)
        dropped.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path("roadmap"))
    if args.json:
        print(
            json.dumps(
                {
                    "token": dropped.entry.token,
                    "file": where,
                    "removed": dropped.entry.lineno,
                    "length": dropped.length,
                    "rendered": dropped.entry.raw,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{where}:{dropped.entry.lineno}  dropped  {dropped.entry.token}")
    print(f"  order    {dropped.length} left")
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
        migrated.save()
    except REFUSALS as error:
        return _refused(error)

    where = config.relative(config.path("roadmap"))
    if args.json:
        print(
            json.dumps(
                {
                    "file": where,
                    "line": migrated.lineno,
                    "tokens": list(migrated.tokens),
                    "configured": _configured_source(config),
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{where}:{migrated.lineno}  priority section written")
    for position, token in enumerate(migrated.tokens, start=1):
        print(f"  {position:<8} {token}")
    print(
        f"  left     `priority` is still in {_configured_source(config)} and is now read by "
        f"nothing — take the line out; `lint` reports it as `priority.config` until you do"
    )
    return EXIT_OK


def _configured_source(config: Config) -> str:
    return config.relative(config.source) if config.source else "roadkeep.toml"
