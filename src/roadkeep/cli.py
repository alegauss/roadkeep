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
* **Errors name the fix, and a failure names one more move.** A `ConfigError` prints every
  problem it found, once — and every non-zero exit closes with the `report` command that
  captures it, argv already substituted (RK86). Held here rather than at each of the twenty
  refusals, because the exit code is the contract they all already leave through.
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
import tempfile
import tomllib
import traceback
from collections.abc import Mapping, Sequence
from pathlib import Path

from roadkeep.adopting import Estimate, adopt, init
from roadkeep.authoring import add, amend, set_status
from roadkeep.backlog import Backlog
from roadkeep.briefing import Brief, brief, non_goals
from roadkeep.capturing import PARTS, body, capture, check, handoff, keep, offer, replay
from roadkeep.config import Config, ConfigError
from roadkeep.counting import Census
from roadkeep.document import Document, Entry, Reject, RoundTripError
from roadkeep.exporting import Projection, project, splice
from roadkeep.fixing import Fix, fix
from roadkeep.graph import Graph, Leverage
from roadkeep.guarding import START_EVENTS, STOP_EVENTS, announce, guard, review
from roadkeep.history import Commit, HistoryUnavailable, Origin, gaps, origin_of
from roadkeep.ids import highest, next_id
from roadkeep.linting import Finding, Report, lint
from roadkeep.picking import Choice, pick
from roadkeep.provenance import engine
from roadkeep.schema import SchemaError
from roadkeep.scoping import add as add_non_goal
from roadkeep.scoping import drop as drop_non_goal
from roadkeep.sections import Section, heading_of
from roadkeep.sections import add as add_section
from roadkeep.sections import drop as drop_section
from roadkeep.sections import find as find_section
from roadkeep.sections import nested as nested_sections
from roadkeep.sections import pointers
from roadkeep.serving import serve
from roadkeep.shipping import Closure, record, retire, ship
from roadkeep.weighing import Spread, Weights, weigh
from roadkeep.shipping import drop as drop_record
from roadkeep.showing import View, show

EXIT_OK = 0
EXIT_GATE = 1
EXIT_USAGE = 2

_JSON_HELP = "machine-readable form"


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
        "--prefix",
        dest="family",
        help=(
            "count in this track (default: the first declared) — two tracks sharing a "
            "counter are two tracks that renumber each other"
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
        "--prefix",
        dest="family",
        help=(
            "which track the derived id counts in (default: the first declared); only "
            "a backlog that numbers by track has a second one to name"
        ),
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
        "add",
        help="write a new section under its block, reflowed to the prose width",
        description=(
            "Write one rationale section: the prose on stdin or `--body`, within the word "
            "budget, filled to the configured width, and placed under the task's own block "
            "or beneath the section it extends. A table or a list is inserted as written."
        ),
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

    section_show = actions.add_parser(
        "show",
        help="print one section and its word count",
        description=(
            "Print one section whole, with the word count the budget is measured in. Reads; "
            "never writes."
        ),
    )
    section_show.add_argument("anchor", help="the anchor, e.g. RK9")
    section_show.add_argument("--role", default="improvements", help="which prose file")
    section_show.add_argument("--json", action="store_true", help=_JSON_HELP)
    section_show.set_defaults(handler=_section_show)

    section_drop = actions.add_parser(
        "drop",
        help="delete one section whole, subsections included",
        description=(
            "Delete one section and everything under it. Subsections included, because one "
            "left behind is orphaned prose under the next task's heading — which reads as "
            "that task's design and is the outcome worse than deleting too much."
        ),
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

    amend_parser = subcommands.add_parser(
        "amend",
        help="correct one open line's why, deps or pointer",
        description=(
            "Correct the three fields a project that adopted the tool has to be able to fix: "
            "a pointer it never had, a dep naming an id in neither file, and the compression "
            "of a `why` that was a paragraph before the limit existed. Validated at input "
            "exactly as `add` validates it, or nothing is written. The `symptom` is not "
            "amendable — it is the claim the line is, so a different one is a different task."
        ),
    )
    amend_parser.add_argument("id", help="the task, e.g. RK7")
    amend_parser.add_argument("--why", help="the sentence, re-validated against the limit")
    amend_parser.add_argument(
        "--dep",
        action="append",
        dest="deps",
        metavar="DEP",
        help="a dep, repeatable: given at all, it replaces the whole group",
    )
    amend_parser.add_argument(
        "--ref", help="the rationale anchor, for ref_scheme = 'outline'"
    )
    amend_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    amend_parser.set_defaults(handler=_amend)

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

    record_parser = subcommands.add_parser(
        "record",
        help="write a ledger entry for unplanned work, or drop a duplicate of one",
        description=(
            "The ledger's own two doors, the pair the roadmap's four are not: every other "
            "command starts from a task line, and these start from the entry."
        ),
    )
    entries = record_parser.add_subparsers(dest="action", required=True)

    record_add = entries.add_parser(
        "add",
        help="write a ledger entry for work that shipped without ever being planned",
        description=(
            "The fourth door, and the only one that starts nowhere. `ship` and both "
            "retirements begin from an open roadmap line, so a fix nobody planned had one "
            "route in: a fictitious roadmap line shipped in the same breath, which teaches "
            "that the format can be gamed. This writes the entry and touches nothing else."
        ),
    )
    record_add.add_argument("--block", required=True, help="the block label, e.g. B")
    record_add.add_argument(
        "--symptom",
        required=True,
        help="what did not work — a phrase, never the name of the patch that closed it",
    )
    record_add.add_argument(
        "--why", required=True, help="one sentence, ending in a stop: the outcome"
    )
    record_add.add_argument(
        "--id",
        dest="task_id",
        help="the id (default: derived, one past the highest anywhere)",
    )
    record_add.add_argument(
        "--json", action="store_true", help="the entry, with the file and line it landed on"
    )
    record_add.set_defaults(handler=_record)

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
        "--json", action="store_true", help="which line went, and which one answers now"
    )
    record_drop.set_defaults(handler=_record_drop)

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
        "--why", required=True, help="the reason it is not, in this file's own limit"
    )
    scope_add.add_argument(
        "--json", action="store_true", help="the bullet, with the file and line it landed on"
    )
    scope_add.set_defaults(handler=_non_goal_add)

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
    scope_list.set_defaults(handler=_non_goal_list)

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

    lint_parser = subcommands.add_parser(
        "lint",
        help="validate every governed line; exit 1 when anything drifted",
        description=(
            "The backstop for what bypassed `add`. Reports every violation, every line "
            "that does not round-trip and every dep nothing can satisfy — and exits "
            "non-zero, which is the entire difference between a gate and advice."
        ),
    )
    lint_parser.add_argument(
        "--fix",
        action="store_true",
        help="normalize what is mechanical first, then report what needs a decision",
    )
    lint_parser.add_argument(
        "--since",
        metavar="REV",
        help=(
            "also report a rationale section edited since REV whose task line was not "
            "(RK36): HEAD in a commit hook, the base branch in CI"
        ),
    )
    lint_parser.add_argument(
        "--quiet",
        action="store_true",
        help="print only the summary line, for a hook that wants the exit code",
    )
    lint_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    lint_parser.set_defaults(handler=_lint)

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
    brief_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    brief_parser.set_defaults(handler=_brief)

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
    show_parser.set_defaults(handler=_show)

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
        "--json", action="store_true", help="the pick, the tier and the counts"
    )
    pick_parser.set_defaults(handler=_pick)

    retire_parser = subcommands.add_parser(
        "retire",
        help="record a line leaving without shipping: superseded, or abandoned",
        description=(
            "A line leaves the roadmap by three doors and only shipping was recorded, so "
            "a gap read as a botched hand-edit. This writes the other two: one ledger "
            "line under the block it belonged to, with the forward pointer, and no design."
        ),
    )
    retire_parser.add_argument("id", help="the task leaving, e.g. RK33")
    retire_parser.add_argument(
        "--superseded-by",
        dest="superseded_by",
        metavar="ID",
        help="the id that replaces it; omitted, the line is recorded as abandoned",
    )
    retire_parser.add_argument(
        "--reason",
        required=True,
        help="one sentence, the author's own: the tool never writes it",
    )
    retire_parser.add_argument("--json", action="store_true", help="every edit, as data")
    retire_parser.set_defaults(handler=_retire)

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
        const="README.md",
        metavar="PATH",
        help="write the block between the roadkeep markers in this file (default README.md)",
    )
    export_parser.add_argument(
        "--site",
        nargs="?",
        const="docs/index.html",
        metavar="PATH",
        help=(
            "the same projection as HTML, between the same two markers "
            "(default docs/index.html)"
        ),
    )
    export_parser.add_argument(
        "--json", action="store_true", help="the payload a site build reads"
    )
    export_parser.set_defaults(handler=_export)

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
    gaps_parser.set_defaults(handler=_gaps)

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

    weight_parser = subcommands.add_parser(
        "weight",
        help="what comparable tasks cost, derived from the commits that shipped them",
        description=(
            "What a comparable task cost, so granularity is a query instead of a feel: a "
            "block whose last comparables shipped at 800+ lines is a block where the next "
            "line is probably two lines. Derived from the commit that wrote each ledger "
            "entry, so nothing stores it and `git show` refutes it. Two axes and no score — "
            "lines vary 27-fold here and files, which is what an agent holds in context, do "
            "not. This ranks nothing: every tier of `pick` is a fact, and a cheapness tier "
            "would defer the architectural tasks, which is where the leverage is."
        ),
    )
    weight_parser.add_argument("--block", help="only this block's comparables, e.g. C")
    weight_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    weight_parser.set_defaults(handler=_weight)

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
            "carry the file the finding named, so the capture can be replayed without this "
            "repository — a test somewhere else, and a file leaving here"
        ),
    )
    report_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    report_parser.add_argument(
        "command_argv",
        nargs=argparse.REMAINDER,
        metavar="-- COMMAND",
        help="the roadkeep command that failed, after a bare --, without the program name",
    )
    report_parser.set_defaults(handler=_report, tolerates_config_error=True)

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
    replay_parser.set_defaults(handler=_replay, tolerates_config_error=True)

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
    adopt_parser.add_argument("--json", action="store_true", help=_JSON_HELP)
    adopt_parser.set_defaults(handler=_adopt)

    guard_parser = subcommands.add_parser(
        "guard",
        help="answer a Claude Code hook: deny a hand-edit, or lint as the turn ends",
        description=(
            "Read one hook payload on stdin and answer it on stdout (RK22). A "
            "`PreToolUse` payload naming a governed file is denied with the command to "
            "call instead; a `Stop` payload runs `lint` and blocks on what it refuses. "
            "Everything else is answered with silence. Not for a human to call: the "
            "harness runs it before every write, so it always exits 0 — a non-zero exit "
            "is read as the hook itself having failed, which would deny nothing and "
            "report a broken hook on every edit in the session."
        ),
    )
    guard_parser.set_defaults(handler=_guard, tolerates_config_error=True)

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
    mcp_parser.set_defaults(handler=_mcp, tolerates_config_error=True)

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
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exit_:
        # argparse refuses before a handler exists, and its exit 2 is one of the three
        # places RK86 names. The argv is all this knows, and all the offer needs.
        if exit_.code:
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
            print(f"roadkeep: {error}", file=sys.stderr)
            return EXIT_USAGE
        # `guard` (RK22) is the one command that has to survive a broken config: it runs
        # before every write in the session, so failing here would turn one typo in
        # `roadkeep.toml` into a repository nobody can edit. It resolves its own config
        # from the payload anyway — one hook process serves every project a session sees.
        config = Config.default(args.directory)
    try:
        code = args.handler(config, args)
    except Exception:
        # A traceback that reaches a terminal raw is a session that ends, and RK86's whole
        # subject is what an agent does next. Printed, then closed with the offer, then
        # answered with an exit code — 1 and not 2, because nothing about the caller's
        # input is what has to change.
        traceback.print_exc()
        code = EXIT_GATE
    if code != EXIT_OK:
        _may_offer(argv, args)
    return code


def _may_offer(argv: Sequence[str], args: argparse.Namespace) -> None:
    """Close a failure with the capture command, except where that would be a loop.

    One place and not twenty: every refusal in this file already leaves through an exit
    code, so the affordance rides the contract instead of being remembered at each of them.
    """
    if args.command in ("report", "guard", "mcp"):
        # `report` offering to report itself is a regress; `guard` and `mcp` answer a
        # protocol, and a sentence on their stderr is read by no agent at all.
        return
    # The report this closes went to stdout and this goes to stderr: unflushed, the offer
    # lands above the findings it is about, and a line out of order is a line misread.
    sys.stdout.flush()
    print(offer(argv), file=sys.stderr)


def _next_id(config: Config, args: argparse.Namespace) -> int:
    try:
        identifier = next_id(config, args.family)
    except ValueError as error:
        return _refused(error)
    family = args.family or config.schema.prefix
    if not args.json:
        print(identifier)
        return EXIT_OK
    top = highest(config, family)
    print(
        json.dumps(
            {
                "next": identifier,
                "prefix": family,
                "prefixes": list(config.schema.prefixes),
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
            family=args.family,
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
        document, section = drop_section(document, args.anchor, claimed=pointers(config))
        document.save()
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    where = config.relative(config.path(args.role))
    if args.json:
        print(json.dumps({**_section_json(section, where), "nested": list(taken)}, indent=2))
        return EXIT_OK
    print(f"dropped {section} from {where}")
    if taken:
        print(f"  nested   {', '.join(f'§{a}' for a in taken)} went with it")
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


def _amend(config: Config, args: argparse.Namespace) -> int:
    if args.why is None and args.deps is None and args.ref is None:
        print(
            "roadkeep: nothing to amend: pass --why, --dep or --ref",
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        amended = amend(config, args.id, why=args.why, deps=args.deps, ref=args.ref)
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    where = config.relative(config.path("roadmap"))
    if args.json:
        print(
            json.dumps(
                {
                    "id": args.id,
                    "file": where,
                    "line": amended.entry.lineno,
                    "changed": list(amended.changed),
                    "rendered": amended.rendered,
                    "refreshed": list(amended.refreshed),
                },
                indent=2,
            )
        )
        return EXIT_OK

    if not amended.changed:
        print(f"{args.id} unchanged: every field already reads that way")
        return EXIT_OK
    print(f"{args.id} amended  {where}:{amended.entry.lineno}  ({', '.join(amended.changed)})")
    print(f"  {amended.rendered}")
    if amended.refreshed:
        print(f"  derived  {', '.join(amended.refreshed)} (dep annotations re-derived)")
    return EXIT_OK


def _ship(config: Config, args: argparse.Namespace) -> int:
    try:
        shipment = ship(config, args.id, why=args.why)
        shipment.save()
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    if isinstance(shipment, Closure):
        # The ledger already holds the entry, so there is none to report (RK62): what this
        # call did is remove the line that was left behind, and the evidence is where the
        # entry already was.
        return _closed(config, shipment, args)

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
                        "nested": list(shipment.nested),
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
        if shipment.nested:
            print(
                f"  nested   {', '.join(f'§{a}' for a in shipment.nested)} went with it"
            )
    else:
        print(f"  kept     nothing dropped: {shipment.kept}")
    if shipment.refreshed:
        print(f"  derived  {', '.join(shipment.refreshed)} (dep annotations re-derived)")
    _print_event(event, "  ")
    return EXIT_OK


def _closed(config: Config, closure: Closure, args: argparse.Namespace) -> int:
    """A roadmap line closed against an entry the ledger already had (RK62)."""
    roadmap = config.relative(config.path("roadmap"))
    ledger = config.relative(config.path("changelog"))
    event = _event(closure.task_id, closure.recorded.task.block, closure.roadmap)
    if args.json:
        print(
            json.dumps(
                {
                    "id": closure.task_id,
                    "closed": {"file": roadmap, "removed": closure.removed_from},
                    "recorded": {
                        "file": ledger,
                        "line": closure.recorded.lineno,
                        "marker": closure.marker,
                        "written": False,
                    },
                    "improvements": {
                        "dropped": None
                        if closure.dropped is None
                        else {"anchor": closure.dropped.anchor, "title": closure.dropped.title},
                        "nested": list(closure.nested),
                        "kept": closure.kept,
                    },
                    "refreshed": list(closure.refreshed),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"{closure.task_id} closed  {roadmap}:{closure.removed_from} removed, "
        f"already {closure.marker} in {ledger}:{closure.recorded.lineno}"
    )
    print("  ledger   untouched: the entry was already there")
    if closure.dropped is not None:
        print(
            f"  dropped  {closure.dropped} from "
            f"{config.relative(config.path('improvements'))}"
        )
        if closure.nested:
            print(f"  nested   {', '.join(f'§{a}' for a in closure.nested)} went with it")
    if closure.refreshed:
        print(f"  derived  {', '.join(closure.refreshed)} (dep annotations re-derived)")
    _print_event(event, "  ")
    return EXIT_OK


def _record(config: Config, args: argparse.Namespace) -> int:
    try:
        entry = record(
            config,
            block=args.block,
            symptom=args.symptom,
            why=args.why,
            task_id=args.task_id,
        )
        entry.save()
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    ledger = config.relative(config.path("changelog"))
    block = entry.ledger.entry.task.block  # as the file reads it back, not as it was typed
    # The event's block state is the *roadmap's*, as it is for every other mutator: a hook
    # asking "is Block B finished" is asking about open work, and a record adds none.
    event = _event(entry.task_id, block, entry.roadmap)
    if args.json:
        print(
            json.dumps(
                {
                    "id": entry.task_id,
                    "marker": entry.marker,
                    "changelog": {
                        "file": ledger,
                        "line": entry.ledger.lineno,
                        "rendered": entry.ledger.rendered,
                    },
                    "roadmap": {"touched": bool(entry.refreshed)},
                    "refreshed": list(entry.refreshed),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"{entry.task_id} {entry.marker} {ledger}:{entry.ledger.lineno} "
        f"under Block {block}"
    )
    # Said out loud, because the absence is the whole point: a reader of this output has to
    # be able to tell "nothing was planned" from "the roadmap edit was forgotten".
    print("  planned  never: straight to the ledger, so there was no roadmap line to remove")
    if entry.refreshed:
        print(f"  derived  {', '.join(entry.refreshed)} (dep annotations re-derived)")
    _print_event(event, "  ")
    return EXIT_OK


def _non_goal_add(config: Config, args: argparse.Namespace) -> int:
    try:
        written = add_non_goal(config, lead=args.lead, why=args.why)
        written.save()
    except (RoundTripError, KeyError, ValueError, OSError) as error:
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
    except (RoundTripError, KeyError, ValueError, OSError) as error:
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


def _record_drop(config: Config, args: argparse.Namespace) -> int:
    try:
        dropped = drop_record(config, args.id)
        dropped.save()
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    ledger = config.relative(config.path("changelog"))
    # The roadmap is read, never written (RK67): the event's block state is the *roadmap's*
    # for every mutator, and a duplicate entry removed leaves open work exactly as it was.
    event = _event(dropped.task_id, dropped.block, config.document("roadmap"))
    if args.json:
        print(
            json.dumps(
                {
                    "id": dropped.task_id,
                    "changelog": {
                        "file": ledger,
                        "removed": dropped.removed_from,
                        "marker": dropped.marker,
                    },
                    "kept": {"line": dropped.kept, "marker": dropped.kept_marker},
                    "roadmap": {"touched": False},
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"{dropped.task_id} {dropped.marker} {ledger}:{dropped.removed_from} removed, "
        f"duplicate of {ledger}:{dropped.kept}"
    )
    print(f"  kept     {dropped.kept_marker} line {dropped.kept}: where the decision was found")
    if dropped.kept_marker != dropped.marker:
        # Two entries that disagree about the door are not one decision written twice, and
        # the later one is gone: which marker the ledger now states has to be said out loud.
        print(
            f"  differed the entry removed said {dropped.marker}, so the ledger now states "
            f"{dropped.kept_marker}"
        )
    print("  roadmap  untouched: an id the ledger still records changes no annotation")
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


def _lint(config: Config, args: argparse.Namespace) -> int:
    try:
        # The mechanical pass runs first and the report is taken afterwards, so what is
        # printed is what is left — the whole point of RK16.
        applied = fix(config) if args.fix else Fix()
        report = lint(config, since=args.since)
    except HistoryUnavailable as error:
        print(f"roadkeep: no history to resolve against ({error})", file=sys.stderr)
        return EXIT_USAGE
    except (KeyError, OSError) as error:
        return _refused(error)

    passed = report.clean and not applied.refused
    if args.json:
        print(json.dumps(_lint_json(report, applied), indent=2))
    else:
        _print_report(report, applied, quiet=args.quiet)
    return EXIT_OK if passed else EXIT_GATE


def _print_report(report: Report, applied: Fix, quiet: bool) -> None:
    if not quiet:
        _print_fix(applied)
        # Notes before the findings and the summary: a note is what the gate says about a
        # file it is passing, and after an exit-1 report nobody would read it (RK35).
        for note in report.notes:
            print(str(note))
    _print_refusals(applied)
    if report.clean:
        # The files are named on the way out even when there is nothing to say: a gate
        # that passed by reading nothing looks exactly like a gate that passed.
        print(f"{', '.join(report.checked) or 'nothing'}: {_scope(report)}, clean")
        return
    if not quiet:
        for finding in report.findings:
            print(str(finding))
    print(
        f"{report.problems} problem(s) in {_scope(report)} across "
        f"{len(report.checked)} file(s): {_codes(report)}"
    )


def _print_fix(applied: Fix) -> None:
    for repair in applied.repairs:
        print(str(repair))
    for kept in applied.skipped:
        print(str(kept))
    if applied.repairs:
        print(f"{applied.changed} line(s) normalized in {', '.join(applied.files)}")


def _print_refusals(applied: Fix) -> None:
    """Printed even under `--quiet`: a pass that could not prove its own output wrote
    nothing, and silence about that is the difference between "clean" and "unexamined"."""
    for message in applied.refused:
        print(f"roadkeep: refused, nothing written: {message}", file=sys.stderr)


def _lint_json(report: Report, applied: Fix) -> dict[str, object]:
    return {
        "clean": report.clean and not applied.refused,
        "fixed": [
            {
                "file": repair.file,
                "line": repair.lineno,
                "id": repair.id,
                "reasons": list(repair.reasons),
                "before": repair.before,
                "after": repair.after,
            }
            for repair in applied.repairs
        ],
        "kept": [
            {"file": s.file, "line": s.lineno, "id": s.id, "reason": s.reason}
            for s in applied.skipped
        ],
        "refused": list(applied.refused),
        "checked": list(report.checked),
        "lines": report.lines,
        "sections": report.sections,
        "budgets": report.budgets,
        "problems": report.problems,
        "codes": report.codes(),
        "findings": [_finding_json(f) for f in report.findings],
        "notes": [
            {
                "code": note.code,
                "file": note.file,
                "line": note.lineno,
                "id": note.id or None,
                "message": note.message,
            }
            for note in report.notes
        ],
    }


def _scope(report: Report) -> str:
    """What was read, in its own units: task lines, sections, and budgeted files."""
    scope = f"{report.lines} line(s), {report.sections} section(s)"
    return scope if not report.budgets else f"{scope}, {report.budgets} budget(s)"


def _codes(report: Report) -> str:
    return "  ".join(f"{code} {count}" for code, count in report.codes().items())


def _finding_json(finding: Finding) -> dict[str, object]:
    return {
        "code": finding.code,
        "file": finding.file,
        "line": finding.lineno,
        # Only a character finding has one (RK34), and it is what makes an invisible
        # codepoint findable: `file:line:column` is what an editor jumps to.
        "column": finding.column,
        "id": finding.id or None,
        "message": finding.message,
    }


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


def _brief(config: Config, args: argparse.Namespace) -> int:
    if args.id is not None and args.block is not None:
        # Two answers to one question: the id names a task and the block names a search.
        print(
            "roadkeep: give an id or --block, not both: an id is already the answer "
            "--block would look for",
            file=sys.stderr,
        )
        return EXIT_USAGE
    try:
        gathered = brief(config, args.id, args.block)
    except (KeyError, OSError) as error:
        return _refused(error)

    view, task = gathered.view, gathered.task
    if args.json:
        print(json.dumps(_brief_json(gathered), indent=2))
        return EXIT_OK

    print(f"{task.id}  Block {task.block}  {task.status}  {gathered.readiness}  "
          f"{view.file}:{view.entry.lineno}")
    if gathered.picked:
        print(f"  picked   {gathered.picked}")
    print(f"  symptom  {task.symptom}")
    print(f"  why      {task.why}")
    for resolution in gathered.deps:
        print(f"  dep      {resolution.dep.id}  {resolution.status}  {resolution.detail}")
    for chain in gathered.chains:
        print(f"  chain    {chain.render(task.id)}  — {chain.detail}")
    _print_leverage(gathered.leverage)
    for referenced in view.paths:
        print(f"  path     {referenced.path}{'' if referenced.exists else '  (missing)'}")
    for non_goal in gathered.non_goals.leads:
        print(f"  not      {non_goal}")
    if gathered.non_goals.elided:
        # Where the list was cut, and not silently: a bounded list that reads as the whole
        # one is a proposal made against a scope it never saw (RK68).
        print(f"  not      … and {gathered.non_goals.elided} more under Non-goals")
    if view.section is not None:
        print()
        print(heading_of(config.schema, view.section))
        print()
        print(view.section.body)
    else:
        print(f"  section  none — {view.section_absence}")
    return EXIT_OK


def _brief_json(gathered: Brief) -> dict[str, object]:
    return {
        **_view_json(gathered.view, no_body=False),
        "readiness": str(gathered.readiness),
        "picked": gathered.picked or None,
        "deps_resolved": [
            {
                "dep": r.dep.id,
                "kind": str(r.kind),
                "status": str(r.status),
                "detail": r.detail,
            }
            for r in gathered.deps
        ],
        "chains": [
            {
                "path": [gathered.task.id, *(hop.target for hop in c.hops)],
                "end": str(c.end),
                "detail": c.detail,
            }
            for c in gathered.chains
        ],
        "unblocks": {
            "count": gathered.leverage.count,
            "of": gathered.leverage.of,
            "transitive": list(gathered.leverage.transitive),
        },
        "non_goals": list(gathered.non_goals.leads),
        "non_goals_elided": gathered.non_goals.elided,
    }


def _show(config: Config, args: argparse.Namespace) -> int:
    try:
        view = show(config, args.id)
    except (KeyError, OSError) as error:
        return _refused(error)

    task = view.task
    section = view.section
    if args.json:
        print(json.dumps(_view_json(view, no_body=args.no_body), indent=2))
        return EXIT_OK

    state = "shipped" if view.shipped else "open"
    print(f"{task.id}  Block {task.block}  {task.status}  {state}  "
          f"{view.file}:{view.entry.lineno}")
    print(f"  symptom  {task.symptom}")
    print(f"  why      {task.why}")
    if task.deps:
        print(f"  deps     {', '.join(dep.render() for dep in task.deps)}")
    if section is not None:
        print(
            f"  section  {view.section_file}:{section.first}  "
            f"§{section.anchor}, {section.words} words"
        )
    else:
        # The absence carries its reason: deleted on ship, never written, or no prose
        # file at all are three states, and only one of them is a defect (RK15).
        print(f"  section  none — {view.section_absence}")
    for referenced in view.paths:
        print(f"  path     {referenced.path}{'' if referenced.exists else '  (missing)'}")
    if section is not None and not args.no_body:
        print()
        print(heading_of(config.schema, section))
        print()
        print(section.body)
    return EXIT_OK


def _view_json(view: View, no_body: bool) -> dict[str, object]:
    task, section = view.task, view.section
    body = None if no_body or section is None else section.body
    return {
        "id": task.id,
        "status": task.status,
        "block": task.block,
        "shipped": view.shipped,
        "file": view.file,
        "line": view.entry.lineno,
        "rendered": view.entry.raw,
        "symptom": task.symptom,
        "why": task.why,
        "deps": [dep.render() for dep in task.deps],
        "ref": task.ref,
        "section": None
        if section is None
        else {**_section_json(section, view.section_file or ""), "body": body},
        "section_absence": view.section_absence,
        "paths": [{"path": p.path, "exists": p.exists} for p in view.paths],
    }


def _pick(config: Config, args: argparse.Namespace) -> int:
    try:
        choice = pick(config, args.block)
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
                    "scope": choice.block,
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


def _retire(config: Config, args: argparse.Namespace) -> int:
    try:
        departure = retire(
            config,
            args.id,
            reason=args.reason,
            superseded_by=args.superseded_by,
        )
        departure.save()
    except (RoundTripError, KeyError, ValueError, OSError) as error:
        return _refused(error)

    ledger = config.relative(config.path("changelog"))
    roadmap = config.relative(config.path("roadmap"))
    block = departure.ledger.entry.task.block
    event = _event(departure.task_id, block, departure.roadmap)
    if args.json:
        print(
            json.dumps(
                {
                    "id": departure.task_id,
                    "marker": departure.marker,
                    "superseded_by": args.superseded_by,
                    "changelog": {
                        "file": ledger,
                        "line": departure.ledger.lineno,
                        "rendered": departure.ledger.rendered,
                    },
                    "roadmap": {"file": roadmap, "removed": departure.removed_from},
                    "dropped": None
                    if departure.dropped is None
                    else departure.dropped.anchor,
                    "dependents": list(departure.dependents),
                    "refreshed": list(departure.refreshed),
                    "event": event,
                },
                indent=2,
            )
        )
        return EXIT_OK

    print(
        f"{departure.task_id} {departure.marker} {ledger}:{departure.ledger.lineno} "
        f"under Block {block}"
    )
    print(f"  removed  {roadmap}:{departure.removed_from}")
    if departure.dropped is not None:
        print(f"  dropped  {departure.dropped} from "
              f"{config.relative(config.path('improvements'))}")
    if departure.dependents:
        # Reported, not refused: a supersession is legitimate and these lines are the
        # author's next edit. `deps` now resolves them as unresolvable, not as satisfied.
        print(f"  still    {', '.join(departure.dependents)} name {departure.task_id}")
    _print_event(event, "  ")
    return EXIT_OK


def _export(config: Config, args: argparse.Namespace) -> int:
    # Both destinations in one run: a README and a page that restate the same backlog have
    # to be refreshed by the same call, or the one nobody remembered is the stale one —
    # which is the whole symptom RK39 names, and it named the site too.
    targets = [
        (args.readme, "markdown"),
        (args.site, "html"),
    ]
    chosen = [(name, shape) for name, shape in targets if name is not None]
    try:
        projection = project(config)
        if not chosen:
            print(projection.json() if args.json else projection.markdown())
            return EXIT_OK
        written = [_splice_into(config, projection, name, shape) for name, shape in chosen]
    except (KeyError, ValueError, OSError) as error:
        return _refused(error)

    for line in written:
        print(line)
    return EXIT_OK


def _splice_into(
    config: Config, projection: Projection, name: str, shape: str
) -> str:
    """Replace one file's marked block, and report which of the two things happened."""
    target = config.root / name
    with target.open("r", encoding="utf-8", newline="") as handle:
        before = handle.read()
    body = projection.html() if shape == "html" else projection.markdown()
    after = splice(before, body, config.relative(target))
    if after == before:
        # The point of idempotence, said out loud: nothing changed, so nothing is written
        # and the file's mtime does not move either.
        return f"{config.relative(target)} is already current"
    target.write_text(after, encoding="utf-8", newline="")
    return f"{config.relative(target)} refreshed between the roadkeep markers"
    return EXIT_OK


def _gaps(config: Config, args: argparse.Namespace) -> int:
    found = gaps(config)
    if args.json:
        print(
            json.dumps(
                [
                    {
                        "id": gap.id,
                        "resolved": gap.resolved,
                        "never_carried": gap.never_carried,
                        "removed_in": None
                        if gap.removed_in is None
                        else {
                            "sha": gap.removed_in.sha,
                            "short": gap.removed_in.short,
                            "date": gap.removed_in.date,
                            "subject": gap.removed_in.subject,
                        },
                    }
                    for gap in found
                ],
                indent=2,
            )
        )
        return EXIT_OK

    if not found:
        print("no gaps: every id below the highest is in one of the files")
        return EXIT_OK
    for gap in found:
        if gap.never_carried:
            print(f"  {gap.id:<6} never carried  the whole history mentions it nowhere")
            continue
        if gap.removed_in is None:
            print(f"  {gap.id:<6} unresolvable  no history here to search")
            continue
        commit = gap.removed_in
        print(f"  {gap.id:<6} {commit.short}  {commit.date[:10]}  {commit.subject}")
    resolved = sum(1 for gap in found if gap.resolved)
    skipped = sum(1 for gap in found if gap.never_carried)
    tail = f", {skipped} never carried" if skipped else ""
    print(f"{len(found)} gap(s), {resolved} resolved against history{tail}")
    return EXIT_OK


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
    graph = Graph.of(backlog)
    chains = graph.chains(args.id)
    leverage = graph.leverage(args.id)
    cycle = graph.cycle_of(args.id)
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
                    "blockers": sorted(graph.blockers(args.id)),
                    "chains": [
                        {
                            "path": [entry.task.id, *(hop.target for hop in c.hops)],
                            "via": [hop.via for hop in c.hops],
                            "end": str(c.end),
                            "detail": c.detail,
                        }
                        for c in chains
                    ],
                    "unblocks": {
                        "direct": list(leverage.direct),
                        "transitive": list(leverage.transitive),
                        "count": leverage.count,
                        "of": leverage.of,
                    },
                    "cycle": list(cycle),
                },
                indent=2,
            )
        )
        return EXIT_OK

    if not resolutions:
        print(f"{entry.task.id}: {readiness} (no deps)")
        _print_leverage(leverage)
        return EXIT_OK
    width = max(len(r.dep.id) for r in resolutions)
    for resolution in resolutions:
        print(
            f"  {resolution.dep.id:<{width}}  {resolution.status:<13}"
            f"{resolution.kind:<9}{resolution.detail}"
        )
    print(f"{entry.task.id}: {readiness}")
    for chain in chains:
        print(f"  chain    {chain.render(entry.task.id)}  — {chain.detail}")
    if cycle:
        # A defect, not a shape: printed here, failed by `lint` (RK14).
        print(f"  cycle    {' ↔ '.join(cycle)}: nothing in this group can be started")
    _print_leverage(leverage)
    return EXIT_OK


def _print_leverage(leverage: Leverage) -> None:
    """The reverse direction, which is the half of prioritisation a tool may supply."""
    shown = ", ".join(leverage.transitive[:4])
    tail = " …" if leverage.count > 4 else ""
    detail = f": {shown}{tail}" if shown else ""
    print(f"  unblocks {leverage.count} of {leverage.of} open{detail}")


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


def _weight(config: Config, args: argparse.Namespace) -> int:
    """Print what comparable tasks cost (RK71). Numbers only — the judgement is the author's.

    No advice line: what a spread means for the line being written is an editorial call, and
    a tool that phrased it would be writing the reasoning it exists not to write (L4).
    """
    try:
        weights = weigh(config, args.block)
    except HistoryUnavailable as error:
        print(f"roadkeep: no history to weigh against ({error})", file=sys.stderr)
        return EXIT_USAGE
    except (KeyError, OSError) as error:
        return _refused(error)

    where = config.relative(config.path("changelog"))
    if args.json:
        print(json.dumps(_weight_json(where, weights), indent=2))
        return EXIT_OK

    scope = f"  Block {weights.block}" if weights.block else ""
    print(f"{where}{scope}  {weights.lines.count} weighed")
    print(f"  lines    {weights.lines}")
    print(f"  files    {weights.files}")
    if weights.block:
        # The number the block is being compared against, without a second command.
        print(f"  ledger   {weights.everywhere}")
        for weight in weights.recent:
            print(
                f"  last     {weight.task_id:<6} {weight.lines:>5} lines  "
                f"{weight.files:>3} files  {weight.commit}"
            )
    else:
        for label, spread in weights.by_block().items():
            print(f"  block {label:<3} {spread}")
    if weights.unresolved:
        # An absent answer is not a cheap task (RK28): a squash or a shallow clone leaves an
        # entry no commit accounts for, and a count that hid them would read as complete.
        print(
            f"  missing  {len(weights.unresolved)} entr(ies) no commit accounts for: "
            f"{', '.join(weights.unresolved)}"
        )
    return EXIT_OK


def _weight_json(where: str, weights: Weights) -> dict[str, object]:
    def spread(one: Spread) -> dict[str, int]:
        return {
            "count": one.count,
            "low": one.low,
            "high": one.high,
            "p25": one.p25,
            "median": one.median,
            "p75": one.p75,
            "p90": one.p90,
        }

    return {
        "file": where,
        "block": weights.block,
        "lines": spread(weights.lines),
        "files": spread(weights.files),
        "ledger": spread(weights.everywhere),
        "blocks": {
            label: spread(one) for label, one in weights.by_block().items()
        },
        "weighed": [
            {
                "id": weight.task_id,
                "block": weight.block,
                "lines": weight.lines,
                "files": weight.files,
                "commit": weight.commit,
            }
            for weight in weights.weighed
        ],
        "unresolved": list(weights.unresolved),
    }


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


def _init(config: Config, args: argparse.Namespace) -> int:
    # `config` is deliberately unused: `init` is the one command that runs *before* a
    # project is configured, so it takes the directory it was pointed at. A discovered
    # config would be an ancestor's, and scaffolding under someone else's paths is how a
    # subproject ends up writing into its parent's roadmap.
    del config
    families = tuple(args.prefix or ("RK",))
    try:
        created = init(args.directory, prefix=families, blocks=args.blocks or ("A",))
    except (ValueError, OSError) as error:
        return _refused(error)

    files = [created.config, *created.files]
    if args.json:
        print(
            json.dumps(
                {
                    "root": Path(args.directory).resolve().as_posix(),
                    "created": [path.as_posix() for path in files],
                    "prefix": families[0],
                    "prefixes": list(families),
                    "blocks": list(created.blocks),
                },
                indent=2,
            )
        )
        return EXIT_OK
    for path in files:
        print(f"created  {path.as_posix()}")
    print(
        f"{len(files)} file(s), blocks {', '.join(created.blocks)}: "
        f"`roadkeep add --block {created.blocks[0]} …` writes the first line"
    )
    return EXIT_OK


def _adopt(config: Config, args: argparse.Namespace) -> int:
    try:
        estimate = adopt(
            config,
            args.path,
            prefix=args.prefix,
            ref_scheme=args.ref_scheme,
            ledger=args.ledger,
        )
    except (ValueError, OSError) as error:
        return _refused(error)

    if args.json:
        print(json.dumps(_estimate_json(estimate), indent=2))
        return EXIT_OK
    _print_estimate(estimate)
    # Always 0: this reports on a file the project has not adopted, so there is no
    # contract for it to have broken. `lint` is the command with an exit code.
    return EXIT_OK


def _print_estimate(estimate: Estimate) -> None:
    where = estimate.path.as_posix()
    source = " (inferred from the ids)" if estimate.inferred else ""
    print(f"{where}  prefix {'/'.join(estimate.families)}{source}")
    print(
        f"  read     {estimate.parsed} line(s), {estimate.conforming} conform, "
        f"{estimate.changing} would change"
    )
    if estimate.blocks:
        print(f"  blocks   {', '.join(estimate.blocks)}")
    for prefix, count in estimate.prefixes:
        # Only the ones the chosen families do not cover. `prefix` takes a list now
        # (RK74), so this names the flag instead of the limitation: whether the spelling
        # is a second track or a paste from another backlog is the reader's call.
        if prefix not in estimate.families:
            print(
                f"  also     {count} id(s) spell {prefix}, unread here: "
                f"--prefix {prefix} if it is a track of this backlog"
            )
    for measure in estimate.measures:
        if measure.over:
            print(
                f"  {measure.field:<8} {measure.over} over {measure.limit}, "
                f"longest {measure.longest}"
            )
    for marker, count in estimate.undeclared:
        print(f"  marker   {marker} on {count} line(s), declared by nothing in [markers]")
    for code, count in estimate.codes:
        print(f"  {code:<8} {count}")
    for reason, count in estimate.rejects:
        print(f"  unparsed {count}: {reason}")
    if estimate.non_canonical:
        print(
            f"  {estimate.non_canonical} line(s) do not round-trip: the tool would "
            f"refuse to write this file until they are rewritten by hand"
        )


def _estimate_json(estimate: Estimate) -> dict[str, object]:
    return {
        "file": estimate.path.as_posix(),
        "prefix": estimate.prefix,
        "families": list(estimate.families),
        "inferred": estimate.inferred,
        "parsed": estimate.parsed,
        "conforming": estimate.conforming,
        "changing": estimate.changing,
        "blocks": list(estimate.blocks),
        "prefixes": [{"prefix": p, "count": n} for p, n in estimate.prefixes],
        "measures": [
            {
                "field": m.field,
                "limit": m.limit,
                "longest": m.longest,
                "over": m.over,
            }
            for m in estimate.measures
        ],
        "undeclared": [{"marker": m, "count": n} for m, n in estimate.undeclared],
        "codes": [{"code": c, "count": n} for c, n in estimate.codes],
        "rejects": [{"reason": r, "count": n} for r, n in estimate.rejects],
        "non_canonical": estimate.non_canonical,
    }


def _report(config: Config, args: argparse.Namespace) -> int:
    """Capture one defect in this tool (RK85). Exit 2 refuses the claim, never the capture.

    The refusal is the point: a report is a task line for a backlog that holds a limit, so
    the sentence is judged in the session that made the claim rather than in the review of
    an issue. What the observed command exits with is a *fact of the capture* and never this
    command's own code — the whole reason to run it is that it failed.
    """
    argv = list(args.command_argv)
    if argv and argv[0] == "--":
        argv = argv[1:]
    if not argv:
        print("roadkeep: name the command that failed, after a bare --", file=sys.stderr)
        return EXIT_USAGE
    violations = check(args.symptom, args.why, args.block)
    if violations:
        print("roadkeep: refused, nothing captured:", file=sys.stderr)
        for violation in violations:
            print(f"  {violation}", file=sys.stderr)
        return EXIT_USAGE
    found = capture(
        args.symptom, args.why, args.block, argv, config.root, embed=args.embed
    ).without(*args.without)
    # Written before it is printed (RK89): what only exists on a stdout depends on the
    # caller taking a second step, and this block's own RK86 is the record of second steps
    # not being taken. On stderr, so `--json` and `--issue` stay pipeable.
    kept = keep(found, config.root)
    print(f"kept  {kept.path}", file=sys.stderr)
    if kept.complaint:
        print(f"roadkeep: {kept.complaint}", file=sys.stderr)
    if args.json:
        print(json.dumps(found.as_dict(), indent=2, ensure_ascii=False))
        return EXIT_OK
    if not args.issue:
        print(found)
        return EXIT_OK
    upstream = args.to or config.upstream
    if upstream is None:
        # Guessed, this publishes a private repository's contents in a stranger's tracker.
        print(
            "roadkeep: no upstream to file against: declare [report] upstream = "
            "'owner/repo' in roadkeep.toml, or pass --to",
            file=sys.stderr,
        )
        return EXIT_USAGE
    print(body(found))
    sys.stdout.flush()
    print(handoff(found, upstream), file=sys.stderr)
    return EXIT_OK


def _replay(config: Config, args: argparse.Namespace) -> int:
    """Re-run one stored capture (RK88). Exit 1 when the verdict is not the recorded one.

    A scratch directory and never the working tree: the capture carries a `roadkeep.toml`
    and a governed file, and staging those over somebody's project would be the one write
    this tool makes that nobody asked for.
    """
    try:
        recorded = json.loads(Path(args.path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"roadkeep: {error}", file=sys.stderr)
        return EXIT_USAGE
    with tempfile.TemporaryDirectory(prefix="roadkeep-replay-") as scratch:
        outcome = replay(recorded, scratch)
    expected = bool(recorded.get("reproduces", True))
    agrees = outcome.ran and outcome.reproduces == expected
    if args.json:
        print(
            json.dumps(
                {
                    "path": args.path,
                    "ran": outcome.ran,
                    "missing": list(outcome.missing),
                    "reproduces": outcome.reproduces,
                    "expected": expected,
                    "recorded_exit": outcome.recorded_exit,
                    "exit": outcome.exit_code,
                },
                indent=2,
            )
        )
    else:
        print(f"{args.path}  {outcome}")
        if outcome.ran and not agrees:
            # The whole point of the corpus: a verdict that moved is either a fix to record
            # or a regression to answer, and both want the file updated in the same commit.
            print(
                f"  recorded reproduces = {str(expected).lower()}: "
                f"update the capture, or the tree stopped agreeing with it"
            )
    return EXIT_OK if agrees else EXIT_GATE


def _guard(config: Config, args: argparse.Namespace) -> int:
    """One command for every hook: the event is in the payload, not in the flags (RK22).

    Three shapes of answer, because the harness reads three: a `SessionStart` line of
    context, a `PreToolUse` decision, and a `Stop` block. None of them is ever an
    *approval* — a governed file is denied and everything else is answered with an empty
    stdout, since `permissionDecision: "allow"` would grant the write rather than decline
    to judge it, waving through the permission rules the user set for every other file in
    the repository.

    The config discovered from `-C` is only this command's fallback: the payload names the
    directory, and the paths in it may belong to another project entirely.
    """
    payload = _payload()
    root = config.root
    if payload.get("hook_event_name") in START_EVENTS:
        notice = announce(payload, root)
        if notice is not None:
            print(
                json.dumps(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "SessionStart",
                            "additionalContext": str(notice),
                        }
                    },
                    indent=2,
                )
            )
        return EXIT_OK
    if payload.get("hook_event_name") in STOP_EVENTS:
        found = review(payload, root)
        if found is not None:
            print(json.dumps({"decision": "block", "reason": str(found)}, indent=2))
        return EXIT_OK
    refusal = guard(payload, root)
    if refusal is not None:
        print(
            json.dumps(
                {
                    "hookSpecificOutput": {
                        "hookEventName": "PreToolUse",
                        "permissionDecision": "deny",
                        "permissionDecisionReason": str(refusal),
                    }
                },
                indent=2,
            )
        )
    return EXIT_OK


def _mcp(config: Config, args: argparse.Namespace) -> int:
    """Hand stdin and stdout to the protocol loop (RK24).

    The directory and not the `Config`: the server re-discovers it per message, so a
    `roadkeep.toml` edited during the session is the one the next `tools/list` describes.
    """
    return serve(sys.stdin, sys.stdout, args.directory)


def _payload() -> Mapping[str, object]:
    """The hook payload, or nothing at all — a guard that raises denies every write."""
    try:
        data = json.loads(sys.stdin.read() or "{}")
    except (ValueError, OSError):
        # `ValueError` covers both halves: a payload that is not JSON, and one that is not
        # UTF-8 — stdin is strict on the way in (see `main`), and neither is worth a crash.
        return {}
    return data if isinstance(data, Mapping) else {}


def _force_utf8(stream: object, errors: str = "backslashreplace") -> None:
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None:
        reconfigure(encoding="utf-8", errors=errors)


if __name__ == "__main__":  # pragma: no cover - exercised via the console script
    raise SystemExit(main())
