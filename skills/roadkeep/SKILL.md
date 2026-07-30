---
name: roadkeep
description: Call the roadkeep CLI instead of editing a project's governed ROADMAP.md, CHANGELOG.md, IMPROVEMENTS.md or STRATEGY.md. Use when adding, shipping, retiring or recording a task, changing a marker, writing a rationale section, picking what to work on next, or reading a backlog, ledger or dependency graph — and whenever an edit to one of those files was denied or `roadkeep lint` reported a violation. Trigger words: roadmap, backlog, changelog, task line, block, ship, retire, next task, roadkeep.
---

# roadkeep — call the command, never type the format

The line format is a schema at the point of insertion, not a convention to remember. Every
field is validated before a sentence exists, so a refusal costs a retry and never a deletion.
Read `roadkeep.toml` for this project's prefix, paths, markers and limits (L6); nothing below
hardcodes them. `roadkeep` is the installed entry point — `python -m roadkeep.cli` when it is
not on PATH.

## Writing and shipping

When the `mcp__roadkeep__*` tools are available, **prefer them**: the whole write path and
the reads a task needs are there — `add`, `status`, `ship`, `retire`, `record`, `section_add`,
`section_drop`, `brief`, `pick`, `list`, `deps`, `lint` — same engine and same refusals, with
the fields arriving as a schema instead of flag names typed from memory. `init` and `adopt`
run once per project and want the CLI. Every guarantee below holds either way.

`roadkeep <add|status|ship|retire|record|section> --help` has the flags. What they guarantee,
so it costs you no thought: the id, the `→ §<id>` pointer, the status default and every
`(deps: … ✅)` annotation are **derived, never typed**; a refusal exits 2 naming the length and
the limit and writes nothing; the shipped marker never reaches the roadmap; `ship <id>` makes
its three edits (ledger entry, roadmap line gone, `§<id>` deleted) plus the dependents'
annotations, or none, and `retire <id> [--superseded-by <id>] --reason "…"` is the same
transaction, two more doors. `record --block <x> --symptom "…" --why "…"` is the fourth — never
planned, so the ledger entry alone and the roadmap untouched. `section add <id> --title "…"`
takes prose on **stdin**, within the word budget, filled to the configured width, under the
task's block — a table or list is inserted exactly as written. No write invents a block
heading. Every write prints one `event <id> Block <x> open|empty` line, the whole payload a
hook gets. There is no second route: `Edit` on a governed file is denied, naming the command,
and `lint` gates the turn's end.

That leaves the two rules a schema cannot check:

1. **`symptom` states what does not work** — never a solution name: a line named after its fix
   cannot be falsified, so it never gets closed, only abandoned.
2. **`why` is one sentence.** A second sentence is the signal the content belongs in the
   rationale file, which is what the pointer addresses.

Markers are `[markers]` in `roadkeep.toml`: the open set is the roadmap's, and the shipped and
retired ones are the ledger's alone — neither is legal in a roadmap. Limits are `[limits]`:
`roadkeep lint` names the file, line and column of anything over, and `--fix` repairs only
what is **derived** (annotation, pointer, dep order, marker codepoint, whitespace).

## Ask, don't count

Every query takes `--json`. **`roadkeep brief [<id>]` starts a task in one call** — the line,
its rationale, deps resolved, the blocker chain, what it unblocks and the non-goals, bounded
to a tool result; with no id, `pick`'s own choice. Narrower: `next-id` never fills a gap;
`list|stats|audit [--block <x>]` counts and lists, naming every marker line neither could
read; `show <id>` joins one line, its section and its paths; `deps <id>` walks the graph both
ways; `gaps` resolves an id in neither file against the commit that removed it; `origin <id>
--why` reads it out of history. And **never restate a count in prose**: `export
[--readme|--site|--json]` projects it.

## Picking work

`roadkeep brief [--block <x>]` picks and briefs in one call, printing why: in-progress first,
then `priority` in `roadkeep.toml`, then the lowest ready id, never one blocked outside.
**Scope it to finish a block**: only "nothing is open in Block <x>" means finished — unscoped,
the answer may be another block's, and the block order is the headings' own (`list`).

## One task, one commit

What `ship` wrote goes in the *same* commit as the code, so the docs never describe a state
that did not ship — and a batch of ready tasks is not permission to batch the commits.
