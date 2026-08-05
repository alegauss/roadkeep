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

- 📋 **RK362** (deps: —) **The gate over near-twin verbs proves the sentence is declared and never that it reaches a caller** — RK350 reads twin off the parsers, while whether it prints turns on a substring of argparse own English that no test holds for a pair added later. → §RK362

## Block C — Query (consult without reading the file)

## Block D — The gate

- 📋 **RK354** (deps: —) **The report names a file it does not list among the ones it checked, so a count and a finding disagree** — RK326 resolves a queue the config declares and files findings against roadkeep.toml, which `checked` never carried: the summary reads 1 problem across 2 files and names a third. → §RK354
- 📋 **RK355** (deps: —) **What `--fix` repairs is enumerated in four places and none of them is derived from the fixer** — RK328 added the sixth repair and the `Stop` hook's sentence still names five, so the message an agent reads at the moment of the drift is the one place the list went stale. → §RK355
- 💭 **RK356** (deps: —) **Nothing says when the version this gate pins stopped being the one an installing user gets** — RK335 named the reader so a merge is gated by a fact somebody can read, and the cost it bought is a number that ages silently until a payload defect the newer validator sees ships. → §RK356
- 📋 **RK357** (deps: —) **A repair that removed a line reports the line number of whatever moved up into its place** — RK328's drop is the one repair that is not a rewrite, and it is reported as `file:line` like the others, so following the address lands on the entry that took the removed one's place. → §RK357

## Block E — Adoption

- 📋 **RK358** (deps: —) **The pick over this repository's own backlog is asserted lowest-ready, so a run made while a line is claimed is red** — `pick` answers STARTED for a 🛠 line and the test names LOWEST, so the suite is red for the length of every task the one-task-one-commit rule creates. → §RK358
- 📋 **RK359** (deps: —) **The doubled address the estimate reports is reachable only where the file is already one this project declares** — Two unadopted prose files are the case adopt exists for and it takes one path, so the collision an adopter meets first stays invisible until after the commitment. → §RK359

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
