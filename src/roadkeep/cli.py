"""The command surface (opened by RK4, extended one subcommand per task).

Design rules for everything added here, so that later commands do not each invent
their own:

* **Plain stdout is composable, `--json` is for reasoning.** `roadkeep next-id` prints
  `RK32` and nothing else, so it can be substituted into another command; `--json`
  carries the provenance — which file and line the answer came from — because an
  answer an agent cannot audit gets verified by reading the file, which is the cost
  the command existed to remove (L5).
* **Exit codes are the contract.** 0 success, 1 the gate says no (`lint`, from RK14),
  2 usage or configuration error. A gate that reports in prose is advice.
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
from collections.abc import Sequence
from pathlib import Path

from roadkeep import __version__
from roadkeep.backlog import Backlog
from roadkeep.config import Config, ConfigError
from roadkeep.history import Commit, HistoryUnavailable, Origin, origin_of
from roadkeep.ids import highest, next_id

EXIT_OK = 0
EXIT_GATE = 1
EXIT_USAGE = 2


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
    deps_parser.add_argument("--json", action="store_true", help="machine-readable form")
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
    origin_parser.add_argument("--json", action="store_true", help="machine-readable form")
    origin_parser.set_defaults(handler=_origin)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
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
                    "file": _relative(top.path, config.root),
                    "line": top.lineno,
                },
                "sources": [
                    _relative(path, config.root)
                    for path in config.id_sources()
                    if path.is_file()
                ],
            },
            indent=2,
        )
    )
    return EXIT_OK


def _deps(config: Config, args: argparse.Namespace) -> int:
    backlog = Backlog.load(config)
    entry = backlog.entry(args.id)
    if entry is None:
        print(
            f"roadkeep: no open task {args.id} in {_relative(config.path('roadmap'), config.root)}"
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


def _relative(path: Path, root: Path) -> str:
    """Paths are reported relative to the project, so output is machine-independent."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _force_utf8(stream: object) -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors="backslashreplace")


if __name__ == "__main__":  # pragma: no cover - exercised via the console script
    raise SystemExit(main())
