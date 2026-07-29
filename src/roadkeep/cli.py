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
* **Errors name the fix.** A `ConfigError` prints every problem it found, once.
* **stdout is forced to UTF-8.** The markers are emoji and the default Windows console
  encoding is cp1252, which raises `UnicodeEncodeError` mid-write and leaves a
  half-printed report. That cost three interrupted runs while this file's own package
  was being written.

`argparse`, not `click`: a tool meant to run as `uvx roadkeep` in someone else's CI
pays for every dependency, and the whole command surface is argument parsing.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping, Sequence

from roadkeep import __version__
from roadkeep.authoring import add, set_status
from roadkeep.backlog import Backlog
from roadkeep.config import Config, ConfigError
from roadkeep.counting import Census
from roadkeep.document import Document, Entry, Reject, RoundTripError
from roadkeep.history import Commit, HistoryUnavailable, Origin, origin_of
from roadkeep.ids import highest, next_id
from roadkeep.picking import Choice, pick
from roadkeep.schema import SchemaError
from roadkeep.sections import Section
from roadkeep.sections import add as add_section
from roadkeep.sections import drop as drop_section
from roadkeep.sections import find as find_section
from roadkeep.shipping import ship

EXIT_OK = 0
EXIT_GATE = 1
EXIT_USAGE = 2

_JSON_HELP = "machine-readable form"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="roadkeep",
        description="Own the writes to a project's roadmap, changelog and rationale.",
    )
    parser.add_argument("--version", action="version", version=f"roadkeep {__version__}")
    parser.add_argument(
        "-C",
        "--directory",
        default=".",
        metavar="PATH",
        help="where to start looking for roadkeep.toml (default: the current directory)",
    )
    subcommands = parser.add_subparsers(dest="command", required=True)

    next_id_parser = subcommands.add_parser(
        "next-id",
        help="the next unused task id, one past the highest anywhere",
        description=(
            "Print the next id. Never the first unused number: a retired id is never "
            "reused, so filling its hole would make two tasks share it in the history."
        ),
    )
    next_id_parser.add_argument(
        "--json",
        action="store_true",
        help="include where the highest id was found, so the answer can be audited",
    )
    next_id_parser.set_defaults(handler=_next_id)

    add_parser = subcommands.add_parser(
        "add",
        help="insert a task line under its block, refusing the fields at input",
        description=(
            "Compose, validate and insert one task line. Nothing is written unless "
            "every field passes: a limit reported after the prose exists is a limit "
            "discovered too late to save the tokens it was meant to save."
        ),
    )
    add_parser.add_argument("--block", required=True, help="the block label, e.g. B")
    add_parser.add_argument(
        "--symptom", required=True, help="what does not work — a phrase, never a fix"
    )
    add_parser.add_argument("--why", required=True, help="one sentence, ending in a stop")
    add_parser.add_argument(
        "--dep",
        action="append",
        default=[],
        dest="deps",
        metavar="DEP",
        help="a dep, repeatable: an id, 'Block X', a range, or work outside the backlog",
    )
    add_parser.add_argument(
        "--status",
        help="the status marker (default: the first marker roadkeep.toml declares)",
    )
    add_parser.add_argument(
        "--id",
        dest="task_id",
        help="the id (default: derived, one past the highest anywhere)",
    )
    add_parser.add_argument(
        "--ref",
        help="the rationale anchor, for ref_scheme = 'outline' only; otherwise derived",
    )
    add_parser.add_argument(
        "--json", action="store_true", help="the line, with the file and line it landed on"
    )
    add_parser.set_defaults(handler=_add)

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
        "add", help="write a new section under its block, reflowed to the prose width"
    )
    section_add.add_argument("anchor", help="the anchor, e.g. RK9 (no §)")
    section_add.add_argument("--title", required=True, help="the heading text")
    section_add.add_argument(
        "--body",
        help="the prose; omitted or '-' reads stdin, which is how a paragraph gets in",
    )
    section_add.add_argument(
        "--role",
        default="improvements",
        help="which prose file (default: improvements)",
    )
    section_add.add_argument(
        "--level", type=int, default=3, help="heading depth (default: 3)"
    )
    section_add.add_argument("--json", action="store_true", help=_JSON_HELP)
    section_add.set_defaults(handler=_section_add)

    section_show = actions.add_parser("show", help="print one section and its word count")
    section_show.add_argument("anchor", help="the anchor, e.g. RK9")
    section_show.add_argument("--role", default="improvements", help="which prose file")
    section_show.add_argument("--json", action="store_true", help=_JSON_HELP)
    section_show.set_defaults(handler=_section_show)

    section_drop = actions.add_parser(
        "drop", help="delete one section whole, subsections included"
    )
    section_drop.add_argument("anchor", help="the anchor, e.g. RK9")
    section_drop.add_argument("--role", default="improvements", help="which prose file")
    section_drop.add_argument("--json", action="store_true", help=_JSON_HELP)
    section_drop.set_defaults(handler=_section_drop)

    status_parser = subcommands.add_parser(
        "status",
        help="set a task's marker in the roadmap, and nowhere else",
        description=(
            "Write one task's status marker. Refused if a sibling file already carries "
            "one for that id: two files that both express status will eventually "
            "express different status, and nothing says which is right."
        ),
    )
    status_parser.add_argument("id", help="the task, e.g. RK7")
    status_parser.add_argument(
        "marker", help="the new marker, from the open set this project declares"
    )
    status_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    status_parser.set_defaults(handler=_status)

    ship_parser = subcommands.add_parser(
        "ship",
        help="move a task to the ledger, drop its rationale, clear the roadmap line",
        description=(
            "Ship one task in three edits across three files. Everything is validated "
            "before anything is written, because whichever of the three is done by hand "
            "last is the one that gets forgotten."
        ),
    )
    ship_parser.add_argument("id", help="the task to ship, e.g. RK5")
    ship_parser.add_argument(
        "--why",
        help=(
            "restate the sentence as an outcome; the design's own sentence is kept "
            "verbatim by default and the tool never rewrites either"
        ),
    )
    ship_parser.add_argument("--json", action="store_true", help="every edit, as data")
    ship_parser.set_defaults(handler=_ship)

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
    list_parser.add_argument("--marker", help="only this status marker")
    list_parser.add_argument(
        "--ids", action="store_true", help="print ids alone, one per line"
    )
    list_parser.set_defaults(handler=_list)

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
    stats_parser.set_defaults(handler=_stats)

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
    audit_parser.set_defaults(handler=_audit)

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
        "--json", action="store_true", help="the pick, the tier and the counts"
    )
    pick_parser.set_defaults(handler=_pick)

    deps_parser = subcommands.add_parser(
        "deps",
        help="resolve one task's deps, naming the ones nothing can resolve",
        description=(
            "Resolve each dep against the roadmap and the changelog. A dep on work "
            "outside the backlog is reported as unresolvable rather than open, "
            "because waiting will never satisfy it."
        ),
    )
    deps_parser.add_argument("id", help="the task to resolve, e.g. RK5")
    deps_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    deps_parser.set_defaults(handler=_deps)

    origin_parser = subcommands.add_parser(
        "origin",
        help="the commits that proposed and shipped a task, with the reasoning",
        description=(
            "Resolve a task's history from git. The pointer is derived, never stored: "
            "a hash written into the ledger would be rewritten by the first squash or "
            "amend, and a dead hash reads exactly like a live one."
        ),
    )
    origin_parser.add_argument("id", help="the task to look up, e.g. RK1")
    origin_parser.add_argument(
        "--why",
        action="store_true",
        help="print the shipping commit's full message — the rationale the ledger drops",
    )
    origin_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    origin_parser.set_defaults(handler=_origin)

    return parser


def _counting_flags(parser: argparse.ArgumentParser) -> None:
    """The three flags every counting command shares (RK10), declared once."""
    parser.add_argument("--block", help="only this block, e.g. C")
    parser.add_argument(
        "--role", default="roadmap", help="which governed file (default: roadmap)"
    )
    parser.add_argument("--json", action="store_true", help=_JSON_HELP)


def main(argv: Sequence[str] | None = None) -> int:
    # stdin too, and for the same reason as the two below: a section's prose arrives on
    # a pipe (RK9), the governed files are UTF-8, and the default Windows console
    # encoding is cp1252 — which turned every em dash in a piped paragraph into three
    # mojibake characters the round-trip then preserved forever.
    # strict on the way in: input that is not UTF-8 is refused, never repaired, because
    # a substituted character round-trips out of the file it lands in (L3).
    _force_utf8(sys.stdin, errors="strict")
    _force_utf8(sys.stdout)
    _force_utf8(sys.stderr)
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = Config.discover(args.directory)
    except ConfigError as error:
        print(f"roadkeep: {error}", file=sys.stderr)
        return EXIT_USAGE
    return args.handler(config, args)


def _next_id(config: Config, args: argparse.Namespace) -> int:
    identifier = next_id(config)
    if not args.json:
        print(identifier)
        return EXIT_OK
    top = highest(config)
    print(
        json.dumps(
            {
                "next": identifier,
                "prefix": config.schema.prefix,
                "highest": None
                if top is None
                else {
                    "id": top.id,
                    "file": config.relative(top.path),
                    "line": top.lineno,
                },
                "sources": [
                    config.relative(path) for path in config.id_sources() if path.is_file()
                ],
            },
            indent=2,
        )
    )
    return EXIT_OK


def _add(config: Config, args: argparse.Namespace) -> int:
    try:
        insertion = add(
            config,
            block=args.block,
            symptom=args.symptom,
            why=args.why,
            status=args.status,
            deps=args.deps,
            ref=args.ref,
            task_id=args.task_id,
        )
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)  # a SchemaError arrives here as the ValueError it is

    event = _event(
        insertion.entry.task.id, insertion.entry.task.block, insertion.document
    )
    if args.json:
        print(
            json.dumps(
                {
                    "id": insertion.entry.task.id,
                    "file": config.relative(config.path("roadmap")),
                    "line": insertion.lineno,
                    "rendered": insertion.rendered,
                    "length": len(insertion.rendered),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK
    print(insertion.rendered)
    _print_event(event)
    return EXIT_OK


def _section_add(config: Config, args: argparse.Namespace) -> int:
    # stdin by default: a paragraph does not fit comfortably in a shell argument, and a
    # heredoc is how the caller of this tool already passes prose.
    try:
        # Inside the try: a paragraph that is not UTF-8 raises UnicodeDecodeError, which
        # is a ValueError, so it is refused with the exit code every other bad input gets.
        body = sys.stdin.read() if args.body in (None, "-") else args.body
        document, section = add_section(
            config, args.role, args.anchor, args.title, body, level=args.level
        )
        document.save()
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    where = config.relative(config.path(args.role))
    if args.json:
        print(json.dumps(_section_json(section, where), indent=2))
        return EXIT_OK
    print(f"§{section.anchor} → {where}:{section.first}  {section.words} words")
    return EXIT_OK


def _section_show(config: Config, args: argparse.Namespace) -> int:
    try:
        section = find_section(config.document(args.role), args.anchor)
    except (KeyError, OSError) as error:
        return _refused(error)
    where = config.relative(config.path(args.role))
    if section is None:
        print(f"roadkeep: no §{args.anchor} section in {where}", file=sys.stderr)
        return EXIT_USAGE

    if args.json:
        print(json.dumps({**_section_json(section, where), "body": section.body}, indent=2))
        return EXIT_OK
    print(f"{'#' * section.level} §{section.anchor} {section.title}")
    print()
    print(section.body)
    return EXIT_OK


def _section_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        document, section = drop_section(config.document(args.role), args.anchor)
        document.save()
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    where = config.relative(config.path(args.role))
    if args.json:
        print(json.dumps(_section_json(section, where), indent=2))
        return EXIT_OK
    print(f"dropped {section} from {where}")
    return EXIT_OK


def _section_json(section: Section, where: str) -> dict[str, object]:
    return {
        "anchor": section.anchor,
        "title": section.title,
        "level": section.level,
        "file": where,
        "first": section.first,
        "last": section.last,
        "words": section.words,
    }


def _status(config: Config, args: argparse.Namespace) -> int:
    try:
        change = set_status(config, args.id, args.marker)
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    where = f"{config.relative(config.path('roadmap'))}:{change.lineno}"
    event = _event(args.id, change.entry.task.block, change.document)
    if args.json:
        print(
            json.dumps(
                {
                    "id": args.id,
                    "from": change.before,
                    "to": change.after,
                    "changed": change.changed,
                    "file": config.relative(config.path("roadmap")),
                    "line": change.lineno,
                    "rendered": change.rendered,
                    "refreshed": list(change.refreshed),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK
    if not change.changed:
        print(f"{args.id} is already {change.after}  {where}")
        _print_event(event, "  ")
        return EXIT_OK
    print(f"{args.id} {change.before} → {change.after}  {where}")
    if change.refreshed:
        print(f"  derived  {', '.join(change.refreshed)} (dep annotations re-derived)")
    _print_event(event, "  ")
    return EXIT_OK


def _event(task_id: str, block: str, roadmap: Document) -> dict[str, object]:
    """What changed, where, and whether that place is finished (RK38).

    Three facts and no more. "This block is done" stays a *derived* fact about the file
    every mutator just wrote, so it cannot go stale the way a queued message can, and the
    tool never learns what happens next.
    """
    return {"id": task_id, "block": block, "block_empty": not roadmap.block(block)}


def _print_event(event: dict[str, object], indent: str = "") -> None:
    state = "empty" if event["block_empty"] else "open"
    print(f"{indent}event    {event['id']}  Block {event['block']}  {state}")


def _refused(error: Exception) -> int:
    """One error path for every command that writes. The exit code is the contract."""
    if isinstance(error, SchemaError):
        # Every violation at once, each naming its limit: a refusal that reports one
        # problem per run turns a single fix into a conversation.
        print("roadkeep: refused, nothing written:", file=sys.stderr)
        for violation in error.violations:
            print(f"  {violation}", file=sys.stderr)
        return EXIT_USAGE
    if isinstance(error, RoundTripError):
        # The file drifted before this command ran, so the gate says no: normalizing a
        # line the parser may have misread is the corruption L3 forbids.
        print(f"roadkeep: {error}", file=sys.stderr)
        return EXIT_GATE
    # KeyError renders its message in quotes, which reads as a stray token in a report.
    message = error.args[0] if isinstance(error, KeyError) else error
    print(f"roadkeep: {message}", file=sys.stderr)
    return EXIT_USAGE


def _ship(config: Config, args: argparse.Namespace) -> int:
    try:
        shipment = ship(config, args.id, why=args.why)
        shipment.save()
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    roadmap = config.relative(config.path("roadmap"))
    ledger = config.relative(config.path("changelog"))
    block = shipment.ledger.entry.task.block
    event = _event(shipment.task_id, block, shipment.roadmap)
    if args.json:
        print(
            json.dumps(
                {
                    "id": shipment.task_id,
                    "changelog": {
                        "file": ledger,
                        "line": shipment.ledger.lineno,
                        "rendered": shipment.ledger.rendered,
                    },
                    "roadmap": {"file": roadmap, "removed": shipment.removed_from},
                    "improvements": {
                        "dropped": None
                        if shipment.dropped is None
                        else {
                            "anchor": shipment.dropped.anchor,
                            "title": shipment.dropped.title,
                            "first": shipment.dropped.first,
                            "last": shipment.dropped.last,
                        },
                        "kept": shipment.kept,
                    },
                    "refreshed": list(shipment.refreshed),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(f"{shipment.task_id} → {ledger}:{shipment.ledger.lineno} under Block {block}")
    print(f"  removed  {roadmap}:{shipment.removed_from}")
    if shipment.dropped is not None:
        print(
            f"  dropped  {shipment.dropped} from "
            f"{config.relative(config.path('improvements'))}"
        )
    else:
        print(f"  kept     nothing dropped: {shipment.kept}")
    if shipment.refreshed:
        print(f"  derived  {', '.join(shipment.refreshed)} (dep annotations re-derived)")
    _print_event(event, "  ")
    return EXIT_OK


def _census(config: Config, args: argparse.Namespace) -> Census:
    return Census.read(config, args.role).select(
        block=args.block, marker=getattr(args, "marker", None)
    )


def _list(config: Config, args: argparse.Namespace) -> int:
    try:
        census = _census(config, args)
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(
            json.dumps(
                {
                    "file": census.file,
                    "total": census.total,
                    "uncounted": [_miss_json(m) for m in census.missed],
                    "tasks": [_row_json(entry) for entry in census.counted],
                },
                indent=2,
            )
        )
        return EXIT_OK

    for entry in census.counted:
        print(entry.task.id if args.ids else entry.raw)
    # stdout stays exactly what the file says, so `list` substitutes for the grep it
    # replaces; the miss goes to stderr, where it cannot be silent and cannot corrupt
    # a pipe either. A listing that looked complete is the whole symptom (RK10).
    if census.missed:
        print(
            f"roadkeep: {census.uncounted} marker-bearing line(s) in {census.file} "
            f"were not counted; run 'roadkeep audit' to see them",
            file=sys.stderr,
        )
    return EXIT_OK


def _stats(config: Config, args: argparse.Namespace) -> int:
    try:
        census = _census(config, args)
    except (KeyError, OSError) as error:
        return _refused(error)

    longest = census.longest()
    if args.json:
        print(
            json.dumps(
                {
                    "file": census.file,
                    "total": census.total,
                    "uncounted": census.uncounted,
                    "markers": census.markers(),
                    "blocks": [
                        {
                            "block": tally.label,
                            "counted": tally.counted,
                            "uncounted": tally.missed,
                            "markers": dict(tally.markers),
                        }
                        for tally in census.tallies()
                    ],
                    "longest": None
                    if longest is None
                    else {
                        "id": longest.task.id,
                        "length": len(longest.raw),
                        "limit": census.schema.line_max,
                    },
                },
                indent=2,
            )
        )
        return EXIT_OK

    tallies = census.tallies()
    names = [tally.name for tally in tallies] + ["total", "uncounted"]
    width = max(len(name) for name in names)
    print(census.file)
    for tally in tallies:
        print(
            f"  {tally.name:<{width}}  {tally.counted:>4}  "
            f"{_markers(tally.markers)}".rstrip()
        )
    print(
        f"  {'total':<{width}}  {census.total:>4}  {_markers(census.markers())}".rstrip()
    )
    # Printed at zero too: a field that appears only when it is non-zero is a field a
    # reader learns to stop looking for, which is how the miss became invisible.
    print(f"  {'uncounted':<{width}}  {census.uncounted:>4}")
    if longest is not None:
        print(
            f"  {'longest':<{width}}  {longest.task.id} at {len(longest.raw)} "
            f"of {census.schema.line_max}"
        )
    return EXIT_OK


def _audit(config: Config, args: argparse.Namespace) -> int:
    try:
        census = _census(config, args)
    except (KeyError, OSError) as error:
        return _refused(error)

    if args.json:
        print(
            json.dumps(
                {
                    "file": census.file,
                    "counted": census.total,
                    "uncounted": [_miss_json(m) for m in census.missed],
                },
                indent=2,
            )
        )
        return EXIT_OK

    if not census.missed:
        print(f"{census.file}: {census.total} counted, none uncounted")
        return EXIT_OK
    for miss in census.missed:
        where = f"Block {miss.block}" if miss.block else "no block"
        print(f"{census.file}:{miss.lineno}  ({where})  {miss.reason}")
        print(f"    {miss.raw.strip()}")
    print(f"{census.file}: {census.total} counted, {census.uncounted} uncounted")
    return EXIT_OK


def _markers(markers: Mapping[str, int]) -> str:
    return "  ".join(f"{marker} {count}" for marker, count in markers.items())


def _row_json(entry: Entry) -> dict[str, object]:
    task = entry.task
    return {
        "id": task.id,
        "status": task.status,
        "block": task.block,
        "symptom": task.symptom,
        "why": task.why,
        "deps": [dep.render() for dep in task.deps],
        "ref": task.ref,
        "line": entry.lineno,
        "length": len(entry.raw),
    }


def _miss_json(miss: Reject) -> dict[str, object]:
    return {
        "line": miss.lineno,
        "block": miss.block,
        "reason": miss.reason,
        "raw": miss.raw,
    }


def _pick(config: Config, args: argparse.Namespace) -> int:
    try:
        choice = pick(config)
    except (KeyError, OSError) as error:
        return _refused(error)
    stalled = [{"id": s.id, "blockers": list(s.blockers)} for s in choice.stalled]
    if args.json:
        entry = choice.entry
        print(
            json.dumps(
                {
                    "pick": None
                    if entry is None
                    else {
                        "id": entry.task.id,
                        "block": entry.task.block,
                        "status": entry.task.status,
                        "file": config.relative(config.path("roadmap")),
                        "line": entry.lineno,
                        "symptom": entry.task.symptom,
                        "ref": entry.task.ref,
                    },
                    "tier": None if choice.tier is None else str(choice.tier),
                    "reason": choice.reason,
                    "alternatives": list(choice.alternatives),
                    "ready": choice.ready,
                    "blocked": choice.blocked,
                    "outside": choice.outside,
                    "stalled": stalled,
                },
                indent=2,
            )
        )
        return EXIT_OK

    # Nothing ready is an answer, not a failure: exit stays 0 and the reason carries the
    # counts, so a caller can tell "backlog finished" from "everything is blocked".
    if choice.entry is None:
        print(f"nothing to pick: {choice.reason}")
        print(f"  backlog  {choice.counts}")
        _print_stalled(choice)
        return EXIT_OK

    entry = choice.entry
    where = f"{config.relative(config.path('roadmap'))}:{entry.lineno}"
    print(f"{entry.task.id}  Block {entry.task.block}  {entry.task.status}  {where}")
    print(f"  because  {choice.reason}")
    print(f"  backlog  {choice.counts}")
    print(f"  symptom  {entry.task.symptom}")
    if choice.alternatives:
        print(f"  or       {', '.join(choice.alternatives)}")
    _print_stalled(choice)
    return EXIT_OK


def _print_stalled(choice: Choice) -> None:
    """A started task that cannot be continued is the one thing a pick must not hide."""
    for stalled in choice.stalled:
        print(f"  stalled  {stalled.id} is in progress, waiting on "
              f"{', '.join(stalled.blockers) or 'nothing this backlog names'}")


def _deps(config: Config, args: argparse.Namespace) -> int:
    try:
        backlog = Backlog.load(config)
    except (KeyError, OSError) as error:
        return _refused(error)  # a declared file that is not there yet: `init` (RK18)
    entry = backlog.entry(args.id)
    if entry is None:
        print(
            f"roadkeep: no open task {args.id} in {config.relative(config.path('roadmap'))}"
            + (" (it is in the changelog)" if args.id in backlog.shipped() else ""),
            file=sys.stderr,
        )
        return EXIT_USAGE

    resolutions = backlog.resolve(entry.task)
    readiness = backlog.readiness(entry.task)
    if args.json:
        print(
            json.dumps(
                {
                    "id": entry.task.id,
                    "readiness": str(readiness),
                    "deps": [
                        {
                            "dep": r.dep.id,
                            "kind": str(r.kind),
                            "status": str(r.status),
                            "detail": r.detail,
                        }
                        for r in resolutions
                    ],
                },
                indent=2,
            )
        )
        return EXIT_OK

    if not resolutions:
        print(f"{entry.task.id}: {readiness} (no deps)")
        return EXIT_OK
    width = max(len(r.dep.id) for r in resolutions)
    for resolution in resolutions:
        print(
            f"  {resolution.dep.id:<{width}}  {resolution.status:<13}"
            f"{resolution.kind:<9}{resolution.detail}"
        )
    print(f"{entry.task.id}: {readiness}")
    return EXIT_OK


def _origin(config: Config, args: argparse.Namespace) -> int:
    try:
        origin = origin_of(config, args.id)
    except HistoryUnavailable as error:
        print(f"roadkeep: no history to resolve against ({error})", file=sys.stderr)
        return EXIT_USAGE

    if args.json:
        print(json.dumps({"id": origin.task_id, **_commits_json(origin)}, indent=2))
        return EXIT_OK

    if origin.proposed_in is None and origin.shipped_in is None:
        print(f"{args.id}: nothing in history mentions it yet")
        return EXIT_OK
    for label, commit in (("proposed", origin.proposed_in), ("shipped", origin.shipped_in)):
        if commit is None:
            print(f"  {label:<9} —")
            continue
        print(f"  {label:<9} {commit.short}  {commit.date[:10]}  {commit.subject}")
    if args.why and origin.shipped_in is not None:
        print()
        print(origin.shipped_in.reasoning)
    return EXIT_OK


def _commits_json(origin: Origin) -> dict[str, object]:
    def one(commit: Commit | None) -> dict[str, object] | None:
        if commit is None:
            return None
        return {
            "sha": commit.sha,
            "short": commit.short,
            "date": commit.date,
            "author": commit.author,
            "subject": commit.subject,
            "reasoning": commit.reasoning,
        }

    return {
        "proposed_in": one(origin.proposed_in),
        "shipped_in": one(origin.shipped_in),
    }


def _force_utf8(stream: object, errors: str = "backslashreplace") -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors=errors)


if __name__ == "__main__":  # pragma: no cover - exercised via the console script
    raise SystemExit(main())
