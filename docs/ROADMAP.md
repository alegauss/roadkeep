# roadkeep — Roadmap (active backlog)

> **Single source of truth for task status.** Flat, one line per task.
> Only **unshipped** work lives here (📋 designed · 💭 idea · ⏳ partial · 🛠 in-progress).
> Shipped work moves to [CHANGELOG.md](CHANGELOG.md); design rationale lives in
> [IMPROVEMENTS.md](IMPROVEMENTS.md).
>
> **What this is.** A CLI that owns writes to a project's roadmap, changelog,
> improvements and strategy files, so the format is a schema at the point of
> insertion instead of a convention an author is asked to remember — shipped as a
> Claude Code plugin, because the author to constrain is usually an agent.
>
> **The one law.** *A field limit enforced only by a reviewer is a limit discovered
> after the prose is written.* `add` refuses an over-length field; `lint` refuses a
> file that drifted anyway. The tool validates — it never writes prose.
>
> **An entry here is one sentence: what + why + `→` pointer** — ≤320 characters,
> symptom in bold (what does not work), never a solution name. This file is the
> tool's own conformance fixture: if `lint` cannot pass it, `lint` is wrong.
>
> **How to pick work:** the lowest-numbered task whose `deps` are all shipped.

## Block A — The model (a task is data before it is a line)

## Block B — Authoring (insert, never hand-edit)

## Block C — Query (consult without reading the file)

- 📋 **RK303** (deps: —) **The section budget picks the first of two prose files declaring one anchor, where every other reader refuses** — It answered improvements about an address strategy declares too, and show calls that state a pointer resolving to neither — so a limit is priced for an unreachable section. → §RK303
- 📋 **RK324** (deps: —) **brief calls a shipped task ready, so the one command meant to start work invites redoing it** — show reads the same id and answers shipped; brief prints ready beside the checkmark and an unblocks count, which is a startable task described to whoever asked what starting it costs. → §RK324
- 📋 **RK336** (deps: RK312 ✅) **anchors prices every family that exists and never says which one is free next** — The address a new section needs is one no family has ever declared, and the report is a per-family table of live, retired and next subsection, so the new-family question is answered by guessing. → §RK336
- 📋 **RK345** (deps: —) **The budget every other field is read before is the one an every-turn file has no door for** — Its limit is held only by lint, so the room left in agents.md is measured with wc and a subtraction at the moment a module has to be named in it. → §RK345
- 📋 **RK346** (deps: —) **One question is answered by two fields, and the older one names one namespace of several** — anchors --json carries next_family beside next_families, so a client reading the field it always read is handed the unprefixed namespace's address on a project whose roles each have one. → §RK346

## Block D — The gate

- 📋 **RK320** (deps: —) **The version bump stages two whole files, so an unrelated edit to either rides into the next commit** — Measured once: another agent's manifest change was in the tree, the hook staged plugin.json to bump it, and the edit landed under a commit message about something else. → §RK320
- 📋 **RK326** (deps: RK325 ✅) **The gate passes a priority entry naming a shipped id, an unknown id or a block nothing declares** — Measured after a ship: all three pass at exit 0, where the same three tokens written as deps are two findings and a resolution the annotation carries. → §RK326
- 📋 **RK328** (deps: RK325 ✅, RK326) **The one queue repair that is fully derived has no fixer, so a clean tree still costs a hand edit** — Dropping the entry whose task shipped chooses nothing and writes no prose, which is the half --fix exists for, and after RK325 it is a governed file the fixer rewrites. → §RK328
- 📋 **RK333** (deps: —) **The refusal offers mcp__roadkeep__add, which is not the name a plugin-provided server gives it** — Measured in an adopting project: the tools arrive as mcp__plugin_roadkeep_roadkeep__add, so the route the guard names first is one that session cannot call. → §RK333
- 📋 **RK335** (deps: —) **The job that gates a release pipes an unpinned remote script into bash, under the workflow's default token** — RK334 bought the loader's own reader with a curl into bash and a workflow declaring no permissions, so the gate now runs code nobody pinned with whatever the token grants. → §RK335

## Block E — Adoption

- 📋 **RK305** (deps: —) **The scheme suggestion is suppressed by a majority that shipping erodes** — adopt hides it only while the declared scheme out-counts the other, and this repo's id-anchored sections are deleted at every ship, so a conforming file is told to switch once enough work lands. → §RK305
- 📋 **RK315** (deps: —) **A test asserting on this repository's own docs fails when another session writes them mid-run** — It read docs/IMPROVEMENTS.md live and failed once in three identical runs while a second session shipped into that file, so the red said nothing about the code under test. → §RK315
- 📋 **RK347** (deps: —) **The estimate reads one prose file at a time, so the state two of them are in is the one it cannot report** — adopt --sections never sees the sibling, and an address both files declare is met on the first lint rather than in the estimate taken to price adoption. → §RK347

## Block F — The Claude Code plugin (the guardrail at the agent boundary)

## Non-goals

Deliberately **not** built — check this list before proposing work:

- **No web UI and no server.** Files and a CLI. The store is the repository.
- **No model and no prompts.** The tool validates and renders; it never writes the
  symptom or the rationale. A generator would reintroduce exactly the prose drift
  this exists to stop.
- **No enforced id scheme beyond `<prefix><n>`.** Non-contiguous, retired-never-reused
  is a property of real backlogs, not a defect to normalize.
- **No dates or quarters.** A marker is maturity, not a schedule.
- **No effort or size field.** Nothing can verify a letter, `pick`'s every tier is a
  fact, and what an agent pays is context: 4 to 14 files a task, against lines that vary
  27-fold, so the letter prices the axis nobody pays.
- **No backlog in an issue tracker** (Jira, Linear, GitHub Issues.) A backlog that lives
  in a service is one an agent cannot `Grep`; a one-way report about this tool, sent
  explicitly, moves nothing out of the files.
- **No multi-line task line.** A task whose text wraps across paragraphs, with its deps
  on a `↳` line of their own, is a second grammar; reading only the first line would
  ship a truncated why and orphan the rest.
- **No supported Python API.** The CLI, the MCP tools and the plugin are the surface;
  `from roadkeep import Schema` is how the tests reach the vocabulary, so no `py.typed`
  ships and a rename inside the package breaks nobody.
